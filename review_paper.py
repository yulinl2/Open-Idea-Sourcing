#!/usr/bin/env python3
"""review_paper.py — CLI for evaluating academic paper novelty.

Usage
-----
    python review_paper.py paper.pdf [options]
    python review_paper.py paper.txt [options]
    python review_paper.py https://arxiv.org/abs/2006.06138 [options]
    python review_paper.py https://arxiv.org/pdf/2006.06138 [options]
    python review_paper.py --papers-file data/test_papers.ndjson [options]

Environment variables
---------------------
OPENAI_API_KEY
    Required when using the default OpenAI backend.
OPENAI_MODEL
    OpenAI model name (default: gpt-4o).

Examples
--------
    # Review a PDF — produces a PDF report in the reports/ directory by default:
    python review_paper.py my_paper.pdf --references refs.json

    # Review a plain-text paper:
    python review_paper.py my_paper.txt

    # Review directly from an arXiv URL (downloads to temp directory automatically):
    python review_paper.py https://arxiv.org/abs/2006.06138

    # Save a Markdown report to a custom location instead of the reports/ directory:
    python review_paper.py my_paper.pdf --format markdown --output report.md

    # Output JSON for downstream processing:
    python review_paper.py my_paper.pdf --format json > report.json

    # Use a custom report store directory:
    python review_paper.py my_paper.pdf --reports-dir /path/to/my_reports

    # Review a batch of papers from an NDJSON file (one JSON object per line,
    # each with a "url" or "path" key):
    python review_paper.py --papers-file data/test_papers.ndjson

    # Batch review with a specific output format:
    python review_paper.py --papers-file data/test_papers.ndjson --format markdown
"""

from __future__ import annotations

import argparse
import datetime
import os
import re
import shutil
import sys
import tempfile
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlparse
import ipaddress
import socket

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dependency is declared in requirements
    load_dotenv = None

MAX_DOWNLOAD_BYTES = 100 * 1024 * 1024  # 100 MiB safety limit for downloads

# Path to the bundled default reference store shipped with the repository.
_BUNDLED_REFERENCES = Path(__file__).resolve().parent / "data" / "references.json"

from open_idea_sourcing import __version__
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


def _read_papers_file(path: Path) -> list[str]:
    """Read an NDJSON file and return a list of paper sources (URLs or paths).

    Each non-empty, non-comment line must be a JSON object with a ``"url"``
    key (for remote papers) or a ``"path"`` key (for local file paths).

    Raises :class:`SystemExit` with a descriptive message on any error so
    that callers can surface the problem without a traceback.
    """
    import json as _json

    try:
        fh = path.open(encoding="utf-8")
    except (FileNotFoundError, PermissionError) as exc:
        raise SystemExit(
            f"Error: could not read papers file {path}: {exc}"
        ) from exc

    sources: list[str] = []
    with fh:
        for line_no, raw_line in enumerate(fh, 1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                entry = _json.loads(line)
            except _json.JSONDecodeError as exc:
                raise SystemExit(
                    f"Error: invalid JSON in {path} at line {line_no}: {exc}"
                ) from exc
            if "url" in entry:
                sources.append(entry["url"])
            elif "path" in entry:
                sources.append(entry["path"])
            else:
                raise SystemExit(
                    f"Error: entry at {path}:{line_no} must have a 'url' or "
                    f"'path' key; got: {list(entry.keys())}"
                )

    if not sources:
        raise SystemExit(f"Error: no papers found in {path}")
    return sources


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="review_paper",
        description="Evaluate the genuine novelty of an academic paper using AI.",
    )
    parser.add_argument(
        "paper",
        nargs="?",
        default=None,
        help=(
            "Path to the paper file (.pdf or .txt), "
            "or a URL (e.g. https://arxiv.org/abs/2006.06138). "
            "Mutually exclusive with --papers-file."
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
        choices=["text", "markdown", "json", "pdf"],
        default="pdf",
        help="Output format for the report (default: pdf).",
    )
    parser.add_argument(
        "--output",
        metavar="FILE",
        default=None,
        help=(
            "Write the report to this exact file path instead of the reports "
            "directory.  Overrides --reports-dir."
        ),
    )
    parser.add_argument(
        "--reports-dir",
        metavar="DIR",
        default="reports",
        help=(
            "Directory where reports are stored when --output is not given "
            "(default: reports).  Created automatically if it does not exist."
        ),
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
    parser.add_argument(
        "--papers-file",
        metavar="FILE",
        default=None,
        help=(
            "Path to an NDJSON file listing papers to review in batch. "
            "Each line must be a JSON object with a 'url' or 'path' key. "
            "Mutually exclusive with the positional paper argument."
        ),
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


def _review_one(paper_source: str, args: argparse.Namespace) -> int:
    """Evaluate a single paper and write its report.

    Parameters
    ----------
    paper_source:
        A local file path or a URL.
    args:
        Parsed CLI arguments (format, model, references, reports_dir, etc.).

    Returns
    -------
    int
        0 on success, 1 on failure.
    """
    run_start = time.monotonic()
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    stage_runtimes: dict[str, float] = {}

    # --- Resolve paper source (file path or URL) ---
    tmp_dir: str | None = None
    try:
        if paper_source.startswith(("http://", "https://")):
            tmp_dir = tempfile.mkdtemp()
            try:
                paper_path = _download_paper(paper_source, tmp_dir)
            except SystemExit as exc:
                return _fail(str(exc.code), args.format)
        else:
            paper_path = Path(paper_source)
            if not paper_path.exists():
                return _fail(f"file not found: {paper_path}", args.format)

        # --- Parse the submitted paper ---
        parser = PaperParser()
        print(f"Parsing paper: {paper_path.name} ...", file=sys.stderr)
        t0 = time.monotonic()
        try:
            paper = parser.parse_file(paper_path)
        except Exception as exc:
            return _fail(f"could not parse paper: {exc}", args.format)
        parse_duration = round(time.monotonic() - t0, 2)
        stage_runtimes["parsing"] = parse_duration
        if not paper.full_text.strip():
            return _fail("no text could be extracted from the paper.", args.format)

        # --- Load reference store ---
        # Always start with the bundled default references so that every run
        # benefits from the curated baseline corpus.  Any user-supplied store
        # (via --references) is merged on top.
        store = ReferenceStore()
        if _BUNDLED_REFERENCES.exists():
            store.load(_BUNDLED_REFERENCES)
            print(
                f"Loaded {len(store)} bundled reference(s) from {_BUNDLED_REFERENCES.name}",
                file=sys.stderr,
            )
        if args.references:
            ref_path = Path(args.references)
            if ref_path.exists():
                print(f"Loading reference store: {ref_path} ...", file=sys.stderr)
                store.load(ref_path)
            else:
                print(
                    f"Warning: reference file not found: {ref_path}", file=sys.stderr
                )

        # --- Similarity search ---
        t0 = time.monotonic()
        searcher = SimilaritySearch(store)
        similar = searcher.search(paper.key_content(), top_k=args.top_k)
        sim_duration = round(time.monotonic() - t0, 2)
        stage_runtimes["similarity"] = sim_duration

        # Build early pipeline job records for pre-LLM stages
        early_jobs = [
            PipelineJob(
                name="Parse paper",
                agent="PaperParser",
                offset_s=0.0,
                duration_s=parse_duration,
                input_summary=paper_path.name,
                output_summary=f'"{paper.title}", {len(paper.full_text)} chars',
            ),
            PipelineJob(
                name="Similarity search",
                agent="SimilaritySearch",
                offset_s=round(stage_runtimes["parsing"], 3),
                duration_s=sim_duration,
                input_summary="paper key content",
                output_summary=f"top-{len(similar)} match(es)",
            ),
        ]

        # --- LLM evaluation ---
        try:
            llm = _build_llm(args.model)
        except SystemExit as exc:
            return _fail(str(exc.code), args.format)
        evaluator = NoveltyEvaluator(llm=llm, top_k_similar=args.top_k)
        print("Running novelty evaluation ...", file=sys.stderr)
        t0 = time.monotonic()

        # Collect git/CI context from GitHub Actions environment variables.
        # These are empty strings when running locally.
        _gh_server = os.environ.get("GITHUB_SERVER_URL", "").rstrip("/")
        _gh_repo = os.environ.get("GITHUB_REPOSITORY", "")
        _gh_sha = os.environ.get("GITHUB_SHA", "")
        _gh_run_id = os.environ.get("GITHUB_RUN_ID", "")
        _gh_ref = os.environ.get("GITHUB_REF", "")
        git_commit = _gh_sha[:7] if _gh_sha else ""
        git_commit_url = (
            f"{_gh_server}/{_gh_repo}/commit/{_gh_sha}"
            if (_gh_server and _gh_repo and _gh_sha)
            else ""
        )
        ci_run_url = (
            f"{_gh_server}/{_gh_repo}/actions/runs/{_gh_run_id}"
            if (_gh_server and _gh_repo and _gh_run_id)
            else ""
        )
        # Derive PR number from refs/pull/<NUMBER>/merge (pull_request events)
        # or from the PR_NUMBER env var (set explicitly in CI for other triggers).
        _pr_match = re.match(r"refs/pull/(\d+)/", _gh_ref)
        pr_number = (
            _pr_match.group(1)
            if _pr_match
            else os.environ.get("PR_NUMBER", "")
        )

        # Pre-build the metadata object so per-job timings can be appended
        # inside evaluate() as each LLM call completes.
        run_metadata = RunMetadata(
            model=args.model,
            input_source=paper_source,
            timestamp=timestamp,
            stage_runtimes=stage_runtimes,
            code_version=__version__,
            git_branch=os.environ.get("GITHUB_REF_NAME", ""),
            git_commit=git_commit,
            git_commit_url=git_commit_url,
            ci_run_url=ci_run_url,
            pr_number=pr_number,
            jobs=early_jobs,
        )
        try:
            report = evaluator.evaluate(
                paper,
                similar_papers=similar,
                metadata=run_metadata,
                _run_start=run_start,
            )
        except RuntimeError as exc:
            return _fail(f"novelty evaluation failed: {exc}", args.format)
        stage_runtimes["evaluation"] = round(time.monotonic() - t0, 2)

        # --- Attach run metadata ---
        total_runtime = round(time.monotonic() - run_start, 2)
        run_metadata.total_runtime_seconds = total_runtime
        run_metadata.stage_runtimes = stage_runtimes
        report.metadata = run_metadata

        # --- Optionally save updated store ---
        if args.save_references:
            store.save(args.save_references)
            print(
                f"Reference store saved to: {args.save_references}", file=sys.stderr
            )

        # --- Render and output report ---
        generator = ReportGenerator()

        # Determine the output path: explicit --output takes priority;
        # otherwise auto-generate an informative filename in --reports-dir.
        if args.output:
            output_path = Path(args.output)
            auto_save = False
        else:
            reports_dir = Path(args.reports_dir)
            reports_dir.mkdir(parents=True, exist_ok=True)
            output_path = reports_dir / suggest_filename(report, args.format)
            auto_save = True

        if args.format == "pdf":
            try:
                generator.generate_pdf(report, output_path)
            except RuntimeError as exc:
                return _fail(str(exc), args.format)
            print(f"PDF report written to: {output_path}", file=sys.stderr)
            return 0

        content = generator.generate(report, fmt=args.format)

        try:
            output_path.write_text(content, encoding="utf-8")
        except OSError as exc:
            return _fail(f"could not write output file: {exc}", args.format)
        print(f"Report written to: {output_path}", file=sys.stderr)
        # When auto-saving to the reports directory, also echo to stdout so
        # that piping (e.g. ``| tee``) and CI log capture still work.
        # When the caller specified an explicit --output path, suppress stdout
        # to match the original behaviour.
        if auto_save:
            print(content)

        return 0

    finally:
        if tmp_dir:
            shutil.rmtree(tmp_dir, ignore_errors=True)


def main(argv: list[str] | None = None) -> int:
    _load_environment()

    args = _parse_args(argv)

    # --- Validate mutual exclusivity of paper and --papers-file ---
    if args.paper is None and args.papers_file is None:
        print(
            "Error: provide a paper path/URL as a positional argument, "
            "or use --papers-file for batch mode.",
            file=sys.stderr,
        )
        return 1
    if args.paper is not None and args.papers_file is not None:
        print(
            "Error: provide either a paper path/URL or --papers-file, not both.",
            file=sys.stderr,
        )
        return 1
    if args.papers_file is not None and args.output:
        print(
            "Error: --output cannot be used with --papers-file; "
            "use --reports-dir instead.",
            file=sys.stderr,
        )
        return 1

    # --- Batch mode ---
    if args.papers_file is not None:
        try:
            sources = _read_papers_file(Path(args.papers_file))
        except SystemExit as exc:
            print(str(exc.code), file=sys.stderr)
            return 1
        failed = 0
        for source in sources:
            print(f"\n--- Reviewing: {source} ---", file=sys.stderr)
            rc = _review_one(source, args)
            if rc != 0:
                failed += 1
                print(f"Warning: review failed for: {source}", file=sys.stderr)
        return 0 if failed == 0 else 1

    # --- Single paper mode ---
    return _review_one(args.paper, args)


if __name__ == "__main__":
    sys.exit(main())
