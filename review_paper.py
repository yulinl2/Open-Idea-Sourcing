#!/usr/bin/env python3
"""review_paper.py — CLI for evaluating academic paper novelty.

Usage
-----
    python review_paper.py paper.pdf [options]
    python review_paper.py paper.txt [options]
    python review_paper.py https://arxiv.org/abs/2006.06138 [options]
    python review_paper.py https://arxiv.org/pdf/2006.06138 [options]

Environment variables
---------------------
OPENAI_API_KEY
    Required when using the default OpenAI backend.
OPENAI_MODEL
    OpenAI model name (default: gpt-4o).

Examples
--------
    # Review a PDF against a local reference store (markdown by default):
    python review_paper.py my_paper.pdf --references refs.json

    # Review a plain-text paper:
    python review_paper.py my_paper.txt

    # Review directly from an arXiv URL (downloads to temp directory automatically):
    python review_paper.py https://arxiv.org/abs/2006.06138

    # Output JSON for downstream processing:
    python review_paper.py my_paper.pdf --format json > report.json
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
import tempfile
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
import ipaddress
import socket

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dependency is declared in requirements
    load_dotenv = None

MAX_DOWNLOAD_BYTES = 100 * 1024 * 1024  # 100 MiB safety limit for downloads

from open_idea_sourcing.novelty_evaluator import NoveltyEvaluator, PipelineJob, RunMetadata
from open_idea_sourcing.paper_parser import PaperParser
from open_idea_sourcing.reference_store import ReferenceStore
from open_idea_sourcing.report_generator import ReportGenerator, suggest_filename
from open_idea_sourcing.similarity_search import SimilaritySearch


def _load_environment() -> None:
    """Load environment variables from .env without overriding existing env vars.

    Load order is deterministic:
    1. ``.env`` in the current working directory
    2. ``.env`` next to this script (repo root in normal usage)
    """
    if load_dotenv is None:
        if not os.environ.get("OPENAI_API_KEY"):
            print(
                "Warning: python-dotenv is not installed; .env will not be auto-loaded. "
                "Run 'make install' or export OPENAI_API_KEY in your shell.",
                file=sys.stderr,
            )
        return

    cwd_env = Path.cwd() / ".env"
    script_env = Path(__file__).resolve().parent / ".env"
    seen: set[Path] = set()

    for env_path in (cwd_env, script_env):
        resolved = env_path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        if resolved.is_file():
            load_dotenv(dotenv_path=resolved, override=False)
            return

    # Fall back to default discovery (cwd -> parents) while preserving env precedence.
    load_dotenv(override=False)


def _normalise_arxiv_url(url: str) -> str:
    """Convert an arXiv abstract page URL to a direct PDF URL.

    Examples
    --------
    >>> _normalise_arxiv_url("https://arxiv.org/abs/2006.06138")
    'https://arxiv.org/pdf/2006.06138'
    >>> _normalise_arxiv_url("https://arxiv.org/abs/2006.06138v2")
    'https://arxiv.org/pdf/2006.06138v2'
    >>> _normalise_arxiv_url("https://arxiv.org/pdf/2006.06138")
    'https://arxiv.org/pdf/2006.06138'
    """
    m = re.match(r"(https?://arxiv\.org)/abs/(.+)", url)
    if m:
        return f"{m.group(1)}/pdf/{m.group(2)}"
    return url


def _download_paper(url: str, dest_dir: str) -> Path:
    """Download a paper PDF from *url* into *dest_dir* and return the path.

    Handles arXiv abstract URLs by rewriting them to the PDF endpoint.
    Only ``https://`` URLs are accepted to prevent unintended plain-HTTP
    requests or other scheme abuse.
    Raises :class:`SystemExit` with a user-friendly message on failure.
    """
    if not url.startswith("https://"):
        raise SystemExit(
            f"Error: only https:// URLs are supported, got: {url!r}"
        )
    pdf_url = _normalise_arxiv_url(url)
    parsed = urlparse(pdf_url)
    filename = Path(parsed.path).name or "paper"
    if not filename.lower().endswith(".pdf"):
        filename += ".pdf"
    dest = Path(dest_dir) / filename
    print(f"Downloading paper from: {pdf_url} ...", file=sys.stderr)
    req = urllib.request.Request(
        pdf_url,
        headers={"User-Agent": "review_paper/1.0 (https://github.com/yulinl2/Open-Idea-Sourcing)"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310
            # Re-validate the final response URL after redirects.
            final_url = resp.geturl()
            final_parsed = urlparse(final_url)
            if final_parsed.scheme != "https":
                raise SystemExit(
                    f"Error: redirect to non-HTTPS URL is not allowed: {final_url!r}"
                )
            host = final_parsed.hostname
            if not host:
                raise SystemExit(
                    f"Error: redirect to URL with no valid hostname is not allowed: {final_url!r}"
                )
            try:
                addr_infos = socket.getaddrinfo(host, None)
            except socket.gaierror as exc:
                raise SystemExit(
                    f"Error: could not resolve host for URL {final_url!r}: {exc}"
                ) from exc
            addresses = {info[4][0] for info in addr_infos}
            for addr in addresses:
                ip_obj = ipaddress.ip_address(addr)
                if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local:
                    raise SystemExit(
                        f"Error: redirect to disallowed IP address range ({addr}) from {final_url!r}"
                    )

            content_length = resp.getheader("Content-Length")
            if content_length is not None:
                try:
                    length_val = int(content_length)
                except ValueError:
                    length_val = None
                else:
                    if length_val > MAX_DOWNLOAD_BYTES:
                        raise SystemExit(
                            f"Error: remote file is too large ({length_val} bytes); "
                            "refusing to download."
                        )

            # Read at most MAX_DOWNLOAD_BYTES + 1 so we can detect oversize
            # payloads without risking unbounded downloads.
            payload = resp.read(MAX_DOWNLOAD_BYTES + 1)
            if len(payload) > MAX_DOWNLOAD_BYTES:
                raise SystemExit(
                    "Error: download exceeded maximum allowed size; "
                    "aborting."
                )
            with dest.open("wb") as out_f:
                out_f.write(payload)
    except Exception as exc:
        raise SystemExit(f"Error: failed to download paper from {pdf_url!r}: {exc}") from exc
    return dest


def _build_llm(model: str):
    """Create a simple OpenAI chat-completion callable."""
    try:
        import openai
    except ImportError as exc:
        raise SystemExit(
            "openai package is required. Install it with: pip install openai"
        ) from exc

    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise SystemExit(
            "OPENAI_API_KEY environment variable is not set.\n"
            "Set OPENAI_API_KEY in .env (recommended) or export it in your shell."
        )

    client = openai.OpenAI(api_key=api_key)

    def call_llm(prompt: str) -> str:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
            return response.choices[0].message.content or ""
        except openai.OpenAIError as exc:
            raise RuntimeError(str(exc)) from exc

    return call_llm


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="review_paper",
        description="Evaluate the genuine novelty of an academic paper using AI.",
    )
    parser.add_argument(
        "paper",
        help=(
            "Path to the paper file (.pdf or .txt), "
            "or a URL (e.g. https://arxiv.org/abs/2006.06138)."
        ),
    )
    parser.add_argument(
        "--references",
        metavar="FILE",
        default=None,
        help="Path to a JSON file containing reference papers to compare against.",
    )
    parser.add_argument(
        "--save-references",
        metavar="FILE",
        default=None,
        help=(
            "Save the loaded reference store to this JSON file. "
            "This does not modify or update any references."
        ),
    )
    parser.add_argument(
        "--format",
        choices=["text", "markdown", "json"],
        default="markdown",
        help="Output format for the report (default: markdown).",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("OPENAI_MODEL", "gpt-4o"),
        help="OpenAI model name (default: gpt-4o or OPENAI_MODEL env var).",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of similar reference papers to surface (default: 5).",
    )
    return parser.parse_args(argv)


def _fail(message: str, fmt: str = "markdown") -> int:
    """Print a minimal formatted error report to *stdout* and return 1.

    Writing to stdout ensures the message is captured by the workflow's
    ``| tee report.md`` pipe, so the report artifact is never silently empty.
    The same message is also sent to stderr so it appears in the CI job log.
    """
    print(f"Error: {message}", file=sys.stderr)  # also visible in raw CI logs
    if fmt == "json":
        import json

        print(json.dumps({"error": message}, indent=2))
    elif fmt == "text":
        print(f"ERROR: {message}")
    else:  # markdown (default)
        print(f"# Novelty Report\n\n> **Error:** {message}")
    return 1


def main(argv: list[str] | None = None) -> int:
    _load_environment()

    args = _parse_args(argv)

    # --- Resolve paper source (file path or URL) ---
    tmp_dir: str | None = None
    try:
        run_start = datetime.now(timezone.utc)
        metadata = RunMetadata(
            started_at=run_start,
            model_name=args.model,
            paper_source=args.paper,
        )

        if args.paper.startswith(("http://", "https://")):
            tmp_dir = tempfile.mkdtemp()
            try:
                paper_path = _download_paper(args.paper, tmp_dir)
            except SystemExit as exc:
                return _fail(str(exc.code), args.format)
        else:
            paper_path = Path(args.paper)
            if not paper_path.exists():
                return _fail(f"file not found: {paper_path}", args.format)

        # --- Parse the submitted paper ---
        parser = PaperParser()
        print(f"Parsing paper: {paper_path.name} ...", file=sys.stderr)
        t0 = datetime.now(timezone.utc)
        try:
            paper = parser.parse_file(paper_path)
        except Exception as exc:
            return _fail(f"could not parse paper: {exc}", args.format)
        t1 = datetime.now(timezone.utc)
        if not paper.full_text.strip():
            return _fail("no text could be extracted from the paper.", args.format)
        metadata.jobs.append(PipelineJob(
            name="Parse paper",
            agent="PaperParser",
            started_at=t0,
            finished_at=t1,
            input_summary=paper_path.name,
            output_summary=f'"{paper.title}", {len(paper.full_text)} chars',
        ))

        # --- Load reference store ---
        store = ReferenceStore()
        t2 = datetime.now(timezone.utc)
        ref_source = "none"
        if args.references:
            ref_path = Path(args.references)
            if ref_path.exists():
                print(f"Loading reference store: {ref_path} ...", file=sys.stderr)
                store.load(ref_path)
                ref_source = ref_path.name
            else:
                print(
                    f"Warning: reference file not found: {ref_path}", file=sys.stderr
                )
        t3 = datetime.now(timezone.utc)
        metadata.jobs.append(PipelineJob(
            name="Load references",
            agent="ReferenceStore",
            started_at=t2,
            finished_at=t3,
            input_summary=ref_source,
            output_summary=f"{len(store)} paper(s)",
        ))

        # --- Similarity search ---
        searcher = SimilaritySearch(store)
        t4 = datetime.now(timezone.utc)
        similar = searcher.search(paper.key_content(), top_k=args.top_k)
        t5 = datetime.now(timezone.utc)
        metadata.jobs.append(PipelineJob(
            name="Similarity search",
            agent="SimilaritySearch",
            started_at=t4,
            finished_at=t5,
            input_summary="paper key content",
            output_summary=f"top-{len(similar)} match(es)",
        ))

        # --- LLM evaluation ---
        try:
            llm = _build_llm(args.model)
        except SystemExit as exc:
            return _fail(str(exc.code), args.format)
        evaluator = NoveltyEvaluator(llm=llm, top_k_similar=args.top_k)
        print("Running novelty evaluation ...", file=sys.stderr)
        try:
            report = evaluator.evaluate(paper, similar_papers=similar, metadata=metadata)
        except RuntimeError as exc:
            return _fail(f"novelty evaluation failed: {exc}", args.format)

        metadata.finished_at = datetime.now(timezone.utc)

        # --- Optionally save updated store ---
        if args.save_references:
            store.save(args.save_references)
            print(
                f"Reference store saved to: {args.save_references}", file=sys.stderr
            )

        # --- Render report ---
        generator = ReportGenerator()
        print(generator.generate(report, fmt=args.format))

        # --- Emit suggested filename for CI / downstream tooling ---
        suggested = suggest_filename(report.paper_title, args.format)
        github_output = os.environ.get("GITHUB_OUTPUT", "")
        if github_output:
            with open(github_output, "a", encoding="utf-8") as fh:
                fh.write(f"report_file={suggested}\n")

        return 0

    finally:
        if tmp_dir:
            shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
