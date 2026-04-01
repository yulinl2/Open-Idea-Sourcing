# agent-reconstruct

Minimal teacher-student reconstruction track.

The teacher agent extracts a domain problem statement from the paper (no solution
revealed). The student agent independently develops a methodology using only the
hint and an allowed reference set -- no external search.

See AGENT_TRACK_ROADMAP.md section 5 for the full build sequence.

## Quickstart

    python agent.py --paper-url https://arxiv.org/abs/2006.06138 \\
                    --refs 1706.03762 1409.0473 \\
                    --model gpt-4o

## Inputs

- `--paper-url` : arXiv URL or local PDF path for the paper to reconstruct
- `--refs`      : space-separated arXiv IDs that the student may use
- `--model`     : LLM model identifier (default: gpt-4o)
- `--output`    : output path for report.md (default: reports/report.md)
