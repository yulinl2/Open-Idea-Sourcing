# Iterative Hint-Refinement for Conceptual Residual Extraction

**Version:** v0.6.1  
**Status:** Implemented, tested (76 unit tests), and validated on real paper

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
| `tests/test_iterative.py` | 43 unit tests covering all components |

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
5. **Minimum 3 rounds** always enforced (raised from 2 after premature convergence in first real run)
6. **Score regression guard** — blocks convergence when latest score drops below best previous score (regression = noise from memoryless student, not convergence)

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
| v0.6 | Iterative refinement | Conceptual residual extraction, hint convergence |
| **v0.6.1** | **Convergence hardening** | **Regression guard, MIN_ROUNDS=3, best-round selection, neutral ref guidance** |

### v0.6.1: Real Run Validation & Convergence Fixes

**Approach:** Run iterative refinement on a real paper (arxiv:2006.06138) across
all 4 modes with `with_refs` condition. Validate convergence behavior, analyze
cross-mode patterns, and fix issues discovered in production.

**First real run (pre-fix):** Converged after just 2 rounds on abstract mode
with score dropping 3.4→3.2, teacher recommending stop. Root causes:
- `MIN_ROUNDS=2` was too low — the teacher stopped before the system could
  explore the hint space
- No guard against score regression — the system treated a downward score
  trajectory as convergence
- Teacher conflated "hint is stable" with "should stop"

**Lesson 8: Score regression is noise, not convergence.** A memoryless student
can have a bad roll — if the latest score drops below the best previous score,
that's not convergence, it's variance. Added a regression guard:
```python
if scores[-1] < best_score - 0.1:
    return False, "score regressed"
```

**Lesson 9: Best-round selection > last-round selection.** Since the student is
memoryless, the last round's output may not be the best. Use `best_round()` to
select the highest-scoring round's output as the final result.

**Lesson 10: Neutral reference guidance for iterative mode.** Forcing students to
engage with references ("you MUST use these references") is counterproductive
in iterative mode — it prevents the teacher from cleanly observing what the
student naturally derives vs. what needs hinting. Implemented dual guidance:
- **Directive** (single-shot): "You MUST engage substantively with references"
- **Neutral** (iterative): "Use them if and as you see fit"

This supports the two-fold optimization: minimizing teacher hint beyond
(refs + problem context) while maximizing reconstruction quality.

## Real Run Results (arxiv:2006.06138)

Paper: "Conformal Inference of Counterfactuals and Individual Treatment Effects"
(Lei & Candès, 2021)

### Cross-Mode Score Trajectories

| Mode | Rounds | Trajectory | Best | Convergence |
|------|--------|-----------|------|-------------|
| abstract | 4 | 3.2→3.2→3.2→3.4 | 3.4 | teacher stop |
| mindmap | 5 | 3.8→3.8→3.0→3.6→4.0 | 4.0 | max rounds |
| problem | 3 | 2.8→2.8→2.8 | 2.8 | teacher stop |
| problem_method | 4 | 2.8→3.0→3.0→3.2 | 3.2 | teacher stop |

### Key Findings

**1. Mindmap mode benefits most from iteration.** Its trajectory
(3.8→3.8→3.0→3.6→4.0) shows the regression guard working perfectly — the
round 3 score dip to 3.0 didn't trigger premature convergence, and the system
recovered to its best score of 4.0 by round 5. The mindmap format's structural
flexibility gives the student more room to integrate new hint information.

**2. Problem mode plateaus at 2.8.** Despite 3 rounds of refinement, the
teacher couldn't improve the student's reconstruction. The evaluator notes the
student consistently proposes intervals for CATE (conditional averages) rather
than individual counterfactuals — a fundamental framing error that hints alone
couldn't correct. This suggests some novelty is too deep for hint-based guidance.

**3. Problem_method shows steady improvement.** 2.8→3.0→3.0→3.2 over 4 rounds
with the teacher progressively adding guidance about (a) separate treatment of
potential outcomes, (b) quantile-based approaches, (c) doubly robust properties.
Each addition nudged the student closer without revealing the answer.

**4. Abstract mode is constrained by format.** At ~150 words, the abstract
format limits how much technical detail the student can include, capping the
achievable score. The 3.2→3.4 improvement came from the teacher adding a single
key insight about decomposing ITE into separate potential outcome predictions.

**5. Novelty gap reveals the conceptual residual.** Across all modes, the
persistent novelty gap centers on: *the specific use of inverse propensity
scores as conformal weights for counterfactual inference* — this IS the paper's
conceptual residual. The iterative process successfully identified it.

### Hint Evolution Analysis

The teacher's refinement trajectory across modes reveals a consistent pattern:

1. **Round 1→2:** Add "construct intervals for each potential outcome separately"
   (the decomposition insight)
2. **Round 2→3:** Add "treatment assignment creates a known covariate shift"
   (the connection to weighted conformal methods)
3. **Round 3→4:** Add "quantile-based vs mean-based approaches" and "doubly
   robust property" (technical depth)

These additions, accumulated across rounds, represent increasing levels of
the conceptual residual — from high-level framing to specific technical insights.

## Test Coverage

43 tests in `tests/test_iterative.py` (76 total across both test files):

- **Data structures** (8): RoundRecord, IterativeResult creation/serialization
- **Convergence** (7): max rounds, min rounds, teacher stop, score plateau, hint stability, residual captured
- **Parsing** (4): JSON block, bare JSON, fallback, nested structures
- **Full loop** (6): basic flow, max rounds cap, student failure, no output dir, hint evolution, serialization roundtrip
- **Mode-specific** (3): abstract structure, problem_method long outputs, mode acceptance
- **Prompt validation** (3): file exists, content markers, no student placeholders
- **Edge cases** (3): single round, empty hint, no mutation
- **Dispatch integration** (6): iterative abstract/problem_method, both conditions, summary, non-iterative unchanged, CLI flags
- **Regression guard** (2): score regression blocks convergence, regression recovery
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

## Two-Fold Optimization & Reference Guidance

The iterative process implements a **two-fold optimization**:

1. **Minimize** the teacher's hint beyond what references + problem context
   already provide
2. **Maximize** the student's reconstruction quality across scientific,
   conceptual, logical, and methodological dimensions

These two objectives are in tension: a larger hint makes reconstruction easier
but inflates the measured conceptual residual. The iterative refinement
naturally resolves this by converging to the minimal hint that achieves
maximal reconstruction — the true conceptual residual.

### Why neutral reference guidance matters

In single-shot mode, forcing the student to engage with references
("you MUST use these references substantively") ensures reference impact is
measurable. But in iterative mode, forced engagement is counterproductive:

- It **biases the teacher's signal**: if the student uses references because
  it was forced to, the teacher can't distinguish "student derived this from
  refs naturally" from "student mentioned refs because instructed to."
- It **undermines the two-fold optimization**: the teacher needs to observe
  what the student does *naturally* with refs + hint to calibrate whether
  the hint is too large (student already gets it from refs) or too small
  (student misses key ideas).

The neutral guidance ("Use them if and as you see fit") lets the teacher get
a clean signal, enabling the hint to converge to its true minimal form.

## Limitations & Open Questions

### Known Limitations

1. **Evaluator variance.** The teacher-evaluator uses a single LLM call per
   round. Score variance across rounds (e.g., mindmap's 3.0 dip) is partly
   evaluator noise, not just student variance. Best-round selection mitigates
   this but doesn't eliminate it.

2. **Problem mode plateau.** The `problem` mode plateaued at 2.8 across all
   3 rounds — the student consistently proposed CATE-based intervals instead
   of counterfactual inference. Some novelty may be too fundamental to guide
   via hints without effectively revealing the answer.

3. **Single paper validation.** Results are from one paper (arxiv:2006.06138).
   Cross-paper validation is needed to confirm the convergence patterns
   generalize.

4. **Cost.** Each iterative run costs 3-5x a single-shot run (multiple
   student + evaluate + refine calls per mode). The 4-mode run used ~16
   rounds total across modes.

5. **Teacher self-assessment bias.** The teacher's `estimated_residual_captured`
   and `recommendation` may be overconfident. The teacher recommended stop
   for `problem` at 2.8 — a low score — suggesting it may underestimate
   remaining gaps.

### Open Questions

1. **Should the conceptual residual include format-specific findings?**
   The mindmap residual differs from the problem_method residual in
   granularity. Should we aggregate across modes for a unified residual?

2. **What's the right max_rounds?** 5 rounds was sufficient for most modes,
   but mindmap hit the cap without the teacher recommending stop. Would
   7-10 rounds yield further improvement?

3. **Can the regression guard be smarter?** Currently uses a fixed 0.1
   threshold. An adaptive threshold based on observed score variance
   across rounds could be more principled.

4. **How does `no_refs` iterative compare?** All runs used `with_refs`.
   Running `no_refs` iterative would show how much of the conceptual
   residual is ref-dependent vs. inherent to the paper's contribution.

## Preserved Run Artifacts

| Directory | Description |
|-----------|-------------|
| `reports/2026-04-08T09-50-33Z/` | Pre-fix run (MIN_ROUNDS=2, premature convergence after 2 rounds) |
| `reports/2026-04-08T09-56-09Z/` | Post-fix run (MIN_ROUNDS=3, regression guard, 4 modes complete) |

Both runs are preserved for comparative analysis of the convergence fix impact.
The pre-fix run demonstrates the premature convergence problem; the post-fix
run demonstrates the corrected behavior.
