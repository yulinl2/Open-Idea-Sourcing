# agent-linear

6-stage checkpointed pipeline with full I/O specs per stage.
Supports --from-stage N for resuming interrupted runs.

See AGENT_TRACK_ROADMAP.md section 4 for the full build sequence.

## Quickstart

    python agent.py --paper-url https://arxiv.org/abs/2006.06138 --model gpt-4o
    # Resume from stage 3:
    python agent.py --paper-url https://arxiv.org/abs/2006.06138 --from-stage 3
