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
from open_idea_sourcing.online_search import OnlineReferenceSearch, generate_search_queries
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


def _extract_arxiv_id(source: str) -> str:
    """Return the arXiv paper ID from an arXiv URL, or an empty string.

    Supports both ``/abs/`` and ``/pdf/`` URL forms, with or without a
    version suffix, and with or without a trailing ``.pdf`` extension.

    Examples
    --------
    >>> _extract_arxiv_id("https://arxiv.org/abs/2006.06138")
    '2006.06138'
    >>> _extract_arxiv_id("https://arxiv.org/abs/2006.06138v2")
    '2006.06138v2'
    >>> _extract_arxiv_id("https://arxiv.org/pdf/1706.03762")
    '1706.03762'
    >>> _extract_arxiv_id("https://arxiv.org/pdf/1706.03762.pdf")
    '1706.03762'
    >>> _extract_arxiv_id("/path/to/paper.pdf")
    ''
    """
    m = re.match(
        r"https?://arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5}(?:v\d+)?)(?:\.pdf)?",
        source,
    )
    return m.group(1) if m else ""


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
    """Create a simple OpenAI chat-completion callable.

    Reasoning models (o1, o3, o4 series) do not accept a ``temperature``
    parameter; this function auto-detects them and omits it so that
    requests to those models succeed without caller changes.
    """
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

    # Reasoning models (o1-*, o3-*, o4-*) do not support `temperature`.
    _is_reasoning = model.startswith(("o1", "o3", "o4"))

    def call_llm(prompt: str) -> str:
        try:
            kwargs: dict = dict(
                model=model,
                messages=[{"role": "user", "content": prompt}],
            )
            if not _is_reasoning:
                kwargs["temperature"] = 0.2
            response = client.chat.completions.create(**kwargs)
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
        default=str(_BUNDLED_REFERENCES),
        help=(
            "Path to a JSON file containing reference papers to compare against. "
            "Defaults to the bundled baseline corpus (data/references.json). "
            "Pass an empty string ('') to disable reference comparison."
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
        "--decomposition-model",
        default=os.environ.get("OPENAI_DECOMPOSITION_MODEL", ""),
        metavar="MODEL",
        help=(
            "OpenAI model to use specifically for the idea decomposition / "
            "concept-tree step (default: same as --model). "
            "Use a stronger reasoning model here, e.g. o3-mini or o4-mini, "
            "to produce deeper and more technically precise concept trees "
            "without increasing cost for the rest of the pipeline. "
            "The OPENAI_DECOMPOSITION_MODEL environment variable is also "
            "honoured."
        ),
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
    parser.add_argument(
        "--no-online-search",
        action="store_true",
        default=False,
        help=(
            "Disable automatic online reference search via the Semantic "
            "Scholar API (enabled by default).  Use this flag when working "
            "offline or when you want to rely solely on a local --references "
            "file."
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
        # By default --references points to the bundled baseline corpus
        # (data/references.json).  Pass an empty string ('') to skip ALL
        # reference loading (bundled corpus + any user-supplied file).
        # Any user-supplied store that differs from the bundled path is
        # loaded and merged on top so that the full combined corpus is
        # available to the similarity search.
        store = ReferenceStore()
        if args.references != "":
            if _BUNDLED_REFERENCES.exists():
                store.load(_BUNDLED_REFERENCES)
                print(
                    f"Loaded {len(store)} bundled reference(s) from"
                    f" {_BUNDLED_REFERENCES.name}",
                    file=sys.stderr,
                )
        if args.references != "" and args.references != str(_BUNDLED_REFERENCES):
            ref_path = Path(args.references)
            if ref_path.exists():
                print(f"Loading reference store: {ref_path} ...", file=sys.stderr)
                store.load(ref_path)
            else:
                print(
                    f"Warning: reference file not found: {ref_path}", file=sys.stderr
                )

        # --- Build LLM (needed for query generation and novelty evaluation) ---
        try:
            llm = _build_llm(args.model)
        except SystemExit as exc:
            return _fail(str(exc.code), args.format)

        # --- Build optional decomposition LLM ---
        # When --decomposition-model (or OPENAI_DECOMPOSITION_MODEL) is set to
        # a value different from --model, build a separate callable so the
        # concept-tree step can use a stronger reasoning model (e.g. o3-mini)
        # without increasing cost for the rest of the pipeline.
        decomposition_model: str = (getattr(args, "decomposition_model", "") or "").strip()
        decomposition_llm = None
        if decomposition_model and decomposition_model != args.model:
            print(
                f"Using decomposition model: {decomposition_model} "
                f"(main model: {args.model})",
                file=sys.stderr,
            )
            try:
                decomposition_llm = _build_llm(decomposition_model)
            except SystemExit as exc:
                return _fail(str(exc.code), args.format)

        # Build evaluator before Stage 3 so it is available for Stage 2 and Stage 3d.
        evaluator = NoveltyEvaluator(
            llm=llm,
            top_k_similar=args.top_k,
            decomposition_llm=decomposition_llm,
            decomposition_model=decomposition_model if decomposition_llm else "",
        )

        # --- Stage 2 — Idea decomposition (Understand) ---
        # Running decomposition before retrieval means the structured concept
        # tree is available to inform Stage 3c LLM query generation, which
        # surfaces conceptually equivalent prior art more reliably.
        print("Decomposing paper idea ...", file=sys.stderr)
        t0_decomp = time.monotonic()
        _decomp_raw: dict[str, str] = {}
        try:
            idea_decomp = evaluator.decompose_idea(content=paper.key_content(), raw=_decomp_raw)
        except RuntimeError as exc:
            return _fail(f"idea decomposition failed: {exc}", args.format)
        decomp_duration = round(time.monotonic() - t0_decomp, 2)
        stage_runtimes["decomposition"] = decomp_duration

        # --- Stage 3 — Online reference search (Retrieve) ---
        # This stage runs after Stage 2 (idea decomposition) and is positioned
        # at the retrieval layer so that online results augment the reference
        # store before TF-IDF similarity search.  LLM-generated conceptual
        # queries are derived from the pre-computed idea decomposition so that
        # conceptually equivalent prior art is surfaced more reliably.
        online_papers_count = 0
        online_duration = 0.0
        online_papers: list = []
        search_queries: list[str] = []
        arxiv_id = _extract_arxiv_id(paper_source)
        if not args.no_online_search:
            print(
                "Generating conceptual search queries ...",
                file=sys.stderr,
            )
            t0 = time.monotonic()
            search_queries = generate_search_queries(paper.key_content(), llm, decomposition=idea_decomp)
            if search_queries:
                print(
                    f"  Generated {len(search_queries)} quer"
                    f"{'y' if len(search_queries) == 1 else 'ies'}: "
                    + ", ".join(f'"{q}"' for q in search_queries),
                    file=sys.stderr,
                )
            else:
                print(
                    "  Query generation failed or returned no queries; "
                    "falling back to title-based search.",
                    file=sys.stderr,
                )

            print(
                "Searching for related papers online (Semantic Scholar) ...",
                file=sys.stderr,
            )
            online_searcher = OnlineReferenceSearch(max_results=args.top_k * 2)
            online_papers = online_searcher.search(
                paper.title,
                paper.abstract,
                arxiv_id=arxiv_id,
                queries=search_queries or None,
            )
            for ref_paper in online_papers:
                store.add(ref_paper)
            online_papers_count = len(online_papers)
            online_duration = round(time.monotonic() - t0, 2)
            stage_runtimes["online_search"] = online_duration
            print(
                f"  Found {online_papers_count} related paper(s) online.",
                file=sys.stderr,
            )

        # --- Similarity search ---
        query = paper.key_content()
        t0 = time.monotonic()
        searcher = SimilaritySearch(store)
        similar = searcher.search(query, top_k=args.top_k)
        sim_duration = round(time.monotonic() - t0, 2)
        stage_runtimes["similarity"] = sim_duration

        # Build descriptive output summary: list top matched titles with scores.
        if similar:
            matched_items = [
                f"{r.score:.2f}×{r.paper.title[:35]}{'…' if len(r.paper.title) > 35 else ''}"
                for r in similar[:3]
            ]
            sim_output = f"top-{len(similar)}: {'; '.join(matched_items)}"
            if len(similar) > 3:
                sim_output += f"; +{len(similar) - 3} more"
        else:
            sim_output = "no matches"

        # First 15 words of key content as a readable query preview.
        query_words = query.split()
        query_preview = " ".join(query_words[:15])
        if len(query_words) > 15:
            query_preview += "…"

        # --- Stage 3d — Domain reference finder (Retrieve) ---
        # Domain reference finding is a *retrieval* task: it contextualises
        # the paper in its field using the top-matched references as context.
        # Per the ideal architecture it belongs at Stage 3 (Retrieve), not
        # Stage 5 (Evaluate), because it enriches the retrieval context rather
        # than producing a novelty verdict.  Running it here means all five
        # evaluation passes (5a–5c + synthesis) receive the domain context.
        print("Finding domain references ...", file=sys.stderr)
        t0 = time.monotonic()
        _dr_raw: dict[str, str] = {}
        try:
            domain_refs = evaluator.find_domain_references(
                paper.key_content(),
                NoveltyEvaluator.format_references(similar),
                _dr_raw,
            )
        except RuntimeError as exc:
            return _fail(f"domain reference finding failed: {exc}", args.format)
        dr_duration = round(time.monotonic() - t0, 2)
        stage_runtimes["domain_references"] = dr_duration
        print(
            f"  Found {len(domain_refs)} domain reference(s).",
            file=sys.stderr,
        )

        # Build early pipeline job records for pre-LLM stages
        # --- PaperParser job detail (title, abstract, authors, section list) ---
        _abstract_preview = (
            (paper.abstract[:500] + "…") if len(paper.abstract) > 500 else paper.abstract
        ) or "*(not extracted)*"
        _authors_line = ", ".join(paper.authors) if paper.authors else "*(not extracted)*"
        _sections_list = "\n".join(
            f"- {s.title}" for s in paper.sections[:20]
        ) or "*(no sections detected)*"
        _parse_detail_parts = [
            f"**Title:** {paper.title}",
            "",
            f"**Authors:** {_authors_line}",
            "",
            f"**Abstract:** {_abstract_preview}",
            "",
            f"**Sections ({len(paper.sections)}):**",
            _sections_list,
        ]
        _parse_detail = "\n".join(_parse_detail_parts)

        early_jobs: list[PipelineJob] = [
            PipelineJob(
                name="Parse paper",
                agent="PaperParser",
                offset_s=0.0,
                duration_s=parse_duration,
                input_summary=paper_path.name,
                output_summary=f'"{paper.title}", {len(paper.full_text)} chars',
                detail=_parse_detail,
            ),
        ]
        decomp_agent_label = f"LLM ({decomposition_model or args.model})"
        early_jobs.append(
            PipelineJob(
                name="Idea decomposition",
                agent=decomp_agent_label,
                offset_s=round(parse_duration, 3),
                duration_s=decomp_duration,
                input_summary="paper content",
                output_summary=f"{len(idea_decomp.sub_ideas)} sub-idea(s)",
            )
        )
        if not args.no_online_search:
            # Short table cell summary (queries in detail section below).
            _qword = "query" if len(search_queries) == 1 else "queries"
            if arxiv_id and search_queries:
                _search_input = f"arXiv:{arxiv_id} + {len(search_queries)} LLM {_qword}"
            elif search_queries:
                _search_input = f"{len(search_queries)} LLM {_qword}"
            elif arxiv_id:
                _search_input = f"arXiv:{arxiv_id}"
            else:
                _search_input = f'title="{paper.title}"'

            # Detail section: full query list + fetched paper titles.
            _q_lines = "\n".join(
                f"{i + 1}. {q}" for i, q in enumerate(search_queries)
            ) if search_queries else "*(none generated)*"
            _fetched_lines = "\n".join(
                f"{i + 1}. **{p.title}** ({p.year or '—'})"
                for i, p in enumerate(online_papers)
            ) if online_papers else "*(none fetched)*"
            _online_detail_parts = [
                "**Queries used:**",
                _q_lines,
                "",
                f"**Fetched papers ({online_papers_count}):**",
                _fetched_lines,
            ]
            # Surface any HTTP / network errors so the user can tell why 0 papers
            # were returned (e.g. rate limiting, network unavailable).
            _search_errors = online_searcher.last_errors if not args.no_online_search else []
            if _search_errors:
                _error_lines = "\n".join(f"- ⚠️ {e}" for e in _search_errors)
                _online_detail_parts += ["", "**Errors encountered:**", _error_lines]
            _online_detail = "\n".join(_online_detail_parts)

            early_jobs.append(
                PipelineJob(
                    name="Online reference search",
                    agent="SemanticScholar API",
                    offset_s=round(stage_runtimes["parsing"] + decomp_duration, 3),
                    duration_s=online_duration,
                    input_summary=_search_input,
                    output_summary=f"{online_papers_count} paper(s) fetched",
                    detail=_online_detail,
                )
            )
        sim_offset = round(
            stage_runtimes["parsing"] + decomp_duration + online_duration,
            3,
        )

        # Similarity search detail: full list of matched papers with scores.
        def _esc(text: str) -> str:
            """Escape text for a Markdown table cell."""
            return str(text).replace("|", r"\|").replace("\n", " ")

        _sim_rows = "\n".join(
            f"| {r.score:.3f} | {_esc(r.paper.title)} | {r.paper.year or '—'} |"
            for r in similar
        ) if similar else "| — | *(no matches)* | — |"
        _sim_detail = "\n".join([
            f"**Query (key content excerpt):**",
            "```",
            query[:300] + ("…" if len(query) > 300 else ""),
            "```",
            "",
            f"**All matches ({len(similar)}):**",
            "| Score | Title | Year |",
            "|------:|-------|------|",
            _sim_rows,
        ])

        early_jobs.append(
            PipelineJob(
                name="Similarity search",
                agent="SimilaritySearch",
                offset_s=sim_offset,
                duration_s=sim_duration,
                input_summary=f"TF-IDF cosine on {len(store)} ref(s)",
                output_summary=sim_output,
                detail=_sim_detail,
            )
        )
        # Domain references PipelineJob is recorded here at Stage 3d
        # (not inside evaluate() where it used to sit at Stage 5d).
        dr_offset = round(sim_offset + stage_runtimes["similarity"], 3)
        early_jobs.append(
            PipelineJob(
                name="Domain references",
                agent=f"LLM ({args.model})",
                offset_s=dr_offset,
                duration_s=dr_duration,
                input_summary=f"paper content + {len(similar)} similar paper(s)",
                output_summary=f"{len(domain_refs)} domain reference(s)",
            )
        )

        # --- LLM evaluation ---
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
                domain_references=domain_refs,
                _domain_references_raw=_dr_raw,
                idea_decomposition=idea_decomp,
                _idea_decomposition_raw=_decomp_raw,
            )
        except RuntimeError as exc:
            return _fail(f"novelty evaluation failed: {exc}", args.format)
        stage_runtimes["evaluation"] = round(time.monotonic() - t0, 2)

        # --- Attach run metadata ---
        total_runtime = round(time.monotonic() - run_start, 2)
        run_metadata.total_runtime_seconds = total_runtime
        run_metadata.stage_runtimes = stage_runtimes
        report.metadata = run_metadata

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
