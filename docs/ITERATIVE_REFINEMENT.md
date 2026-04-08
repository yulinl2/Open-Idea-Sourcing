# Iterative Hint-Refinement for Conceptual Residual Extraction

**Version:** v0.6.0  
**Status:** Implemented and tested (75 unit tests pass)

## Scientific Motivation

The single-shot teacher-student pipeline (v0.1–v0.5) answers: "How well can a
student reconstruct paper B given only a problem hint and references A?" But a
single evaluation gives only a coarse signal. The **iterative** approach asks a
sharper question:

> **What is the minimal set of ideas the student needs, beyond the references,
> to reconstruct the paper's contribution?**

This minimal set is the paper's **conceptual residual** — its genuine
intellectual contribution beyond prior work.

### The Iterative Workflow

```
Round 1: Teacher hint₀ → Student generates₁ → Teacher evaluates₁
Round 2: Teacher refines hint₁ (based on eval₁) → Fresh student generates₂ → Teacher evaluates₂
Round 3: Teacher refines hint₂ → Fresh student generates₃ → Teacher evaluates₃
...
Round N: Hint stabilizes → The final hint IS the conceptual residual
```

**Key design principles** (from the original concept):

1. **Iteration modifies the hint, NOT the student output.** The teacher
   observes what the student is missing and adjusts the hint; where the
   student over-delivers, the teacher removes over-specification.

2. **Each student is memoryless.** Every round starts a fresh student with no
   memory of previous attempts. This ensures the hint alone accounts for
   guidance — not accumulated context.

3. **The teacher retains full history.** The teacher sees all prior rounds
   (hints, outputs, evaluations) and uses them to make informed refinements.

4. **Convergence = conceptual residual found.** When the hint stops changing
   meaningfully and the student's quality plateaus, the remaining hint
   content represents what's genuinely novel in the paper.

## Architecture

### New Components

| File | Purpose |
|------|---------|
| `infra/iterative.py` | Core iterative engine: loop, convergence, data structures |
| `prompts/teacher_refine_hint.txt` | Teacher prompt for hint refinement |
| `tests/test_iterative.py` | 42 unit tests covering all components |

### Data Structures

```python
RoundRecord:
  round_number: int
  hint: dict              # hint given to student this round
  student_output: str     # student's reconstruction
  evaluation: dict        # teacher's scoring (5 dimensions + composite)
  refined_hint: dict      # hint after refinement (None for last round)
  refinement_rationale: dict  # what was added/removed and why
  convergence_signal: dict    # teacher's assessment of convergence

IterativeResult:
  paper_id, mode, condition
  initial_hint: dict
  rounds: list[RoundRecord]
  converged: bool
  convergence_reason: str
  final_hint: dict        # THE CONCEPTUAL RESIDUAL
  total_rounds: int
  score_trajectory() → list[float]
  hint_trajectory() → list[dict]
```

### Convergence Criteria (checked after each round)

1. **Max rounds** (hard cap, default 5)
2. **Teacher recommends stop** (`convergence_signal.recommendation == "stop"`)
3. **Score plateau** (composite score delta < 0.3) AND hint stable
4. **High residual captured** (teacher estimates ≥ 85% captured)
5. **Minimum 2 rounds** always enforced

### CLI Usage

```bash
# Iterative refinement on abstract mode
python agent.py --iterative --modes abstract --conditions with_refs

# Custom max rounds
python agent.py --iterative --max-rounds 3 --modes abstract problem_method

# Full iterative run (all modes, both conditions)
python agent.py --iterative --max-rounds 5
```

### Output Structure

```
reports/<timestamp>/<paper_id>/
  _teacher/hint.json                    # initial teacher hint
  with_refs/abstract/
    output.md                           # final round's output (with metadata)
    eval.json                           # final round's evaluation
    _iterative/
      iterative_result.json             # complete trajectory data
      round_1/
        hint.json                       # hint for this round
        output.md                       # student output
        eval.json                       # evaluation scores
        student_audit.json              # LLM call audit
        eval_audit.json                 # evaluation audit
        refined_hint.json               # refined hint for next round
        refinement.json                 # rationale + convergence signal
        refine_audit.json               # refinement audit
      round_2/
        ...
      round_N/
        hint.json
        output.md
        eval.json
        # (no refined_hint — this was the last round)
```

## Development Process & Lessons Learned

### v0.6.0-alpha: Abstract Mode First

**Approach:** Implement and perfect the iterative engine on the simplest mode
(abstract, 150–300 words) before scaling up.

**Lesson 1: Mock routing matters.** The first test run had 2/35 failures
because the mock LLM client routed `refine_hint` calls to the `evaluate`
handler — both prompts contained the word "evaluate". Fix: check for the
refine prompt's unique markers ("conceptual residual", "iterative
reconstruction") **before** checking for eval markers.

**Lesson 2: Convergence needs both signals.** Score plateau alone is
insufficient — the hint might still be changing substantially. We require
BOTH score plateau AND hint stability for convergence. This prevents
premature stopping when the teacher is still making large hint adjustments
that happen to not change scores yet.

**Lesson 3: Deep copy discipline.** The iterative loop modifies hints across
rounds. Without `copy.deepcopy()`, the initial_hint dict would be mutated
in place. Added an explicit test (`test_initial_hint_not_mutated`) to guard
against this.

### v0.6.0-beta: Scale to Problem-Method

**Approach:** After abstract mode was stable (35/35 tests), extended tests
to `problem_method` mode with longer outputs (~6K tokens).

**Lesson 4: Output truncation in refinement prompts.** The `refine_hint`
function caps student output at 15K chars in the user message. This is
important for problem_method mode where outputs can be very long. Without
truncation, the refinement prompt would exceed token limits.

**Lesson 5: The student function is injected.** Making `run_student_fn` a
parameter (rather than importing it directly) enables clean mocking and
ensures the iterative engine doesn't depend on the student implementation.

### v0.6.0: Integration & Final Polish

**Approach:** Wire iterative mode into `dispatch_paper` via `--iterative`
flag, then test end-to-end with dispatch integration tests.

**Lesson 6: Iterative implies evaluate.** Setting `--iterative` automatically
enables evaluation. This is a hard requirement — the iterative loop cannot
refine hints without evaluation scores and novelty gap analysis.

**Lesson 7: Separate iterative and single-shot paths.** Rather than adding
conditionals throughout the existing dispatch code, the iterative path is a
clean `if iterative: ... continue` block that falls through to the original
single-shot code. This keeps the v0.5 behavior completely unchanged when
`--iterative` is not set.

## Version Trajectory

| Version | Focus | Key Addition |
|---------|-------|-------------|
| v0.1 | One-shot generation | 6 modes, audit trail |
| v0.2 | Dual backend | OpenAI + Anthropic, with_refs/no_refs |
| v0.3 | Teacher evaluation | 5-dimension scoring, PDF extraction |
| v0.4 | Anti-leakage | Redesigned teacher prompt, reconstruction difficulty |
| v0.5 | Pairwise comparison | Side-by-side with_refs vs no_refs, 1-7 scale |
| **v0.6** | **Iterative refinement** | **Conceptual residual extraction, hint convergence** |

## Test Coverage

42 tests in `tests/test_iterative.py`:

- **Data structures** (8): RoundRecord, IterativeResult creation/serialization
- **Convergence** (7): max rounds, min rounds, teacher stop, score plateau, hint stability, residual captured
- **Parsing** (4): JSON block, bare JSON, fallback, nested structures
- **Full loop** (6): basic flow, max rounds cap, student failure, no output dir, hint evolution, serialization roundtrip
- **Mode-specific** (3): abstract structure, problem_method long outputs, mode acceptance
- **Prompt validation** (3): file exists, content markers, no student placeholders
- **Edge cases** (3): single round, empty hint, no mutation
- **Dispatch integration** (6): iterative abstract/problem_method, both conditions, summary, non-iterative unchanged, CLI flags
- **Imports** (2): module imports, infra init exports

## Scientific Interpretation

When the iterative process converges:

- **Small final hint + high scores** → Paper's contribution is highly
  derivable from references. The conceptual residual is small.
- **Large final hint + improving scores** → Paper contains genuine novelty
  that cannot be derived from references. The hint additions across rounds
  reveal specifically WHAT is novel.
- **Hint trajectory** → Shows the discovery process: what the teacher
  needed to add (genuinely novel ideas) and remove (derivable from refs).
- **Score trajectory** → Shows how reconstruction quality improves as the
  hint approaches the conceptual residual.

The `refinement_rationale.additions` across all rounds collectively describe
the paper's novel contributions at a conceptual level, without revealing
the specific mechanism — a unique form of novelty characterization.
