#!/usr/bin/env python3
"""agent-linear: 6-stage checkpointed pipeline.

Implementation guide: AGENT_TRACK_ROADMAP.md section 4
Supports --from-stage N for resuming interrupted runs.
"""
import argparse
import sys

AGENT_IMPL_ID = "linear_v0_0_0"


def main() -> None:
    parser = argparse.ArgumentParser(description="agent-linear: staged pipeline")
    parser.add_argument("--paper-url", required=True)
    parser.add_argument("--model", default="gpt-4o")
    parser.add_argument("--output", default="reports/report.md")
    parser.add_argument("--from-stage", type=int, default=1,
                        help="Resume from stage N (1-6)")
    args = parser.parse_args()
    print(f"[agent-linear] impl_id={AGENT_IMPL_ID} paper_url={args.paper_url} model={args.model} "
          f"from_stage={args.from_stage}")
    print("[agent-linear] Not yet implemented -- see AGENT_TRACK_ROADMAP.md section 4")
    sys.exit(1)


if __name__ == "__main__":
    main()
