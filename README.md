# agent-staged-reconstruct

**Multi-mode teacher-student paper reconstruction pipeline.**

Given a research paper and its cited references, this pipeline measures how much
of the paper's intellectual contribution a capable LLM can reconstruct from
references alone — across 6 levels of reconstruction granularity.

## Scientific Goal

If a student model, given only the problem statement and cited references, can
closely reconstruct a paper's methodology, that suggests the contribution was
*highly derivable* from prior work. Conversely, large divergence signals
genuine novelty. By running 6 reconstruction modes (from abstract to full
paper), we get a granular signal about *which aspects* of a paper are novel.

## Architecture

```
Teacher (gpt-5.4)          Student (gpt-4o)
──────────────────         ─────────────────
Reads full paper  ──┐     Has NO paper access
                    │     Has NO web search
                    ▼     Has NO tools
            Problem hint
            (no solution   ───► Reconstructs from:
             leakage)           - Problem hint
                                - Reference abstracts
                                ─────────────────────
                                6 reconstruction modes:
                                1. Abstract
                                2. Idea mindmap
                                3. Problem formulation
                                4. Problem + methodology
                                5. Full paper (guided)
                                6. Full paper (freestyle)
```

## Output Structure

```
reports/
  2026-04-04T12-00-00Z/          # timestamped dispatch
    SUMMARY.md                    # human-readable summary table
    results.json                  # machine-readable results
    2006.06138/                   # paper ID
      _teacher/
        hint.json                 # teacher's problem-context extraction
        audit.json                # full LLM call audit trail
      abstract/
        output.md                 # student reconstruction
        audit.json                # full audit trail
      mindmap/
        output.md
        audit.json
      ...
    2602.04770/
      ...
```

## Usage

```bash
# Run all modes on all test papers
python agent.py

# Single paper, specific modes
python agent.py --paper-url https://arxiv.org/abs/2006.06138 --modes abstract mindmap

# Override models
python agent.py --student-model gpt-4o --teacher-model gpt-5.4
```

Requires `OPENAI_API_KEY` environment variable.

## Design Decisions

- **Student has no web search**: prevents knowledge leakage from the student
  retrieving the actual paper or its derivatives.
- **Teacher has web search available** (future): can enrich problem context
  with broader field awareness, improving prompt quality.
- **Output in Markdown**: avoids typesetting noise; LaTeX math in `$...$`
  renders in most viewers. Can be upgraded to PDF later with generic tooling.
- **Audit-first**: every LLM call is recorded with full prompts, responses,
  token counts, and timing for scientific reproducibility.

## Development Roadmap

1. **v0.1** (current): One-off generation, 6 modes, full audit trail
2. **v0.2**: Teacher evaluation of reconstruction quality (scoring rubric)
3. **v0.3**: Iterative teacher-student game with feedback loops
4. **v0.4**: Loop termination criteria (convergence detection, max rounds)
5. **v0.5**: Cross-paper comparison and novelty ranking
