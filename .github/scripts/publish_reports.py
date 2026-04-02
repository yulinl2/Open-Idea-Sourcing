"""publish_reports.py — copy baseline reports into <slug>/v<version>/ subdirs.

Usage:
    python .github/scripts/publish_reports.py <src_dir> <dst_dir>

For each .md file in <src_dir>:
  - Strip the trailing _YYYY-MM-DDTHHMMSS timestamp to derive the paper slug.
  - Parse "| Code version | <ver> |" from the file body.
  - Copy to <dst_dir>/<slug>/v<version>/<filename>.

Non-.md files and .md files without a Code version field are copied flat to
<dst_dir> (safe fallback; the retroactive reorganize_reports.py can tidy them).
"""

import re
import shutil
import sys
from pathlib import Path

TIMESTAMP_RE = re.compile(r"^(.+?)_(\d{4}-\d{2}-\d{2}T\d{6})$")


def paper_slug(stem: str) -> str:
    m = TIMESTAMP_RE.match(stem)
    return m.group(1) if m else stem


def parse_version(text: str) -> str:
    m = re.search(r"\|\s*Code version\s*\|\s*([^|\n]+?)\s*\|", text)
    return m.group(1).strip() if m else ""


def main(src_dir: str, dst_dir: str) -> None:
    src = Path(src_dir)
    dst = Path(dst_dir)
    for report in sorted(src.iterdir()):
        if report.suffix == ".md":
            content = report.read_text(encoding="utf-8", errors="replace")
            slug = paper_slug(report.stem)
            version = parse_version(content)
            dest = (
                dst / slug / f"v{version}" / report.name
                if version
                else dst / report.name
            )
        else:
            dest = dst / report.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(report, dest)
        print(f"  copied {report.name} → {dest.relative_to(dst)}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <src_dir> <dst_dir>", file=sys.stderr)
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
