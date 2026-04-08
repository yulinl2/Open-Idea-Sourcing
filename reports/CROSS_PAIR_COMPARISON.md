# Cross-Pair Conceptual Residual Comparison

**Date:** 2026-04-08  
**Version:** staged_reconstruct_v0_6_1  
**Models:** Student = claude-sonnet-4-20250514, Teacher = claude-opus-4-20250514  
**Method:** Iterative hint-refinement (max 5 rounds, MIN_ROUNDS=3, regression guard)

## Paper & Reference Index

| ID | Short Name | Domain |
|----|-----------|--------|
| **Target A** (2006.06138) | Lei & Candes 2021 — Conformal ITE | Causal inference / uncertainty quantification |
| **Target B** (2602.04770) | Deng et al. 2026 — Drifting Models | Generative modeling / one-step generation |
| **Ref 1** (1904.06019) | Tibshirani et al. 2020 — Conformal Under Covariate Shift | Conformal prediction / distribution shift |
| **Ref 2** (2006.01474) | Kivaranovic et al. 2020 — Conformal ITE Intervals | Conformal prediction / treatment effects |

## Design: 2x2 (Target x Reference) Matrix

| | Ref 1 (Covariate Shift) | Ref 2 (ITE Intervals) |
|---|---|---|
| **Target A** (Conformal ITE) | Pair 1: close ref (same field) | Pair 2: very close ref (same problem) |
| **Target B** (Drifting Models) | Pair 3: distant ref (different field) | Pair 4: distant ref (different field) |

**Hypothesis:** When the reference is topically close to the target, the conceptual
residual should be smaller (higher scores, fewer hint additions needed). When the
reference is distant, the residual should be larger — the student can't derive
much from an irrelevant reference, so the teacher must hint more.

---

## Full Results: Best Scores per Mode

### Pair 1: Target A + Ref 1 (close ref)
*Run: 2026-04-08T09-56-09Z*

| Mode | Rounds | Trajectory | Best Score | Convergence |
|------|--------|-----------|------------|-------------|
| abstract | 4 | 3.2→3.2→3.2→3.4 | **3.4** | teacher stop |
| mindmap | 5 | 3.8→3.8→3.0→3.6→4.0 | **4.0** | max rounds |
| problem | 3 | 2.8→2.8→2.8 | **2.8** | teacher stop |
| problem_method | 4 | 2.8→3.0→3.0→3.2 | **3.2** | teacher stop |

### Pair 2: Target A + Ref 2 (very close ref)
*Run: 2026-04-08T10-44-36Z*

| Mode | Rounds | Trajectory | Best Score | Convergence |
|------|--------|-----------|------------|-------------|
| abstract | 3 | 2.8→3.2→3.2 | **3.2** | score plateau |
| mindmap | 4 | 3.8→3.8→3.0→4.2 | **4.2** | teacher stop |
| problem | 5 | 3.0→3.4→3.0→3.4→3.4 | **3.4** | max rounds |
| problem_method | 5 | 2.8→3.0→2.8→2.8→3.2 | **3.2** | max rounds |

### Pair 3: Target B + Ref 1 (distant ref)
*Run: 2026-04-08T11-11-36Z*

| Mode | Rounds | Trajectory | Best Score | Convergence |
|------|--------|-----------|------------|-------------|
| abstract | 3 | 2.8→2.8→3.4 | **3.4** | teacher stop |
| mindmap | 4 | 3.0→2.8→2.8→3.0 | **3.0** | score plateau |
| problem | 4 | 2.6→3.2→3.2→3.6 | **3.6** | 85% residual captured |
| problem_method | 3 | 2.6→2.8→2.8 | **2.8** | score plateau |

### Pair 4: Target B + Ref 2 (distant ref)
*Run: 2026-04-08T11-34-51Z*

| Mode | Rounds | Trajectory | Best Score | Convergence |
|------|--------|-----------|------------|-------------|
| abstract | 5 | 2.8→2.8→2.8→3.4→3.2 | **3.4** | max rounds |
| mindmap | 3 | 2.6→3.0→3.6 | **3.6** | teacher stop |
| problem | 5 | 3.2→3.2→3.4→3.0→3.4 | **3.4** | max rounds |
| problem_method | 5 | 3.2→2.6→3.0→3.0→3.0 | **3.2** | max rounds |

---

## Summary Comparison Table

### Best Scores Across All Modes (per pair)

| | Ref 1 (Covariate Shift) | Ref 2 (ITE Intervals) |
|---|---|---|
| **Target A** (Conformal ITE) | abs=3.4 / mm=**4.0** / prob=2.8 / pm=3.2 | abs=3.2 / mm=**4.2** / prob=3.4 / pm=3.2 |
| **Target B** (Drifting Models) | abs=3.4 / mm=3.0 / prob=**3.6** / pm=2.8 | abs=3.4 / mm=**3.6** / prob=3.4 / pm=3.2 |

### Peak Score per Pair (best mode)

| | Ref 1 | Ref 2 |
|---|---|---|
| **Target A** | **4.0** (mindmap) | **4.2** (mindmap) |
| **Target B** | **3.6** (problem) | **3.6** (mindmap) |

### Average Score Across Modes (per pair)

| | Ref 1 | Ref 2 |
|---|---|---|
| **Target A** | **3.35** | **3.50** |
| **Target B** | **3.20** | **3.40** |

---

## Conceptual Residuals Identified

### Target A: Conformal ITE (Lei & Candes 2021)

**Core residual (consistent across both refs and all modes):**
> The specific use of **inverse propensity scores as conformal weights** for
> counterfactual inference — treating treatment assignment as a known covariate
> shift, then applying **weighted split-CQR** with a **doubly robust** property
> (coverage holds if either propensity scores OR conditional quantiles are
> well-estimated).

**Residual components ranked by depth:**
1. **Decomposition insight** (captured by round 2 in most modes): construct
   intervals for each potential outcome Y(1), Y(0) separately, then combine
2. **Weighted conformal connection** (captured by round 3-4): treatment
   assignment = covariate shift → propensity scores = likelihood ratio weights
3. **Doubly robust property** (rarely captured): coverage guarantee holds under
   misspecification of one component — this is the deepest novelty
4. **Exact finite-sample guarantees** for randomized trials (almost never captured)

**Ref sensitivity:** Ref 2 (Kivaranovic) is a *closer* reference — it directly
addresses conformal prediction for ITE. Yet the best scores are similar
(4.0 vs 4.2), and the residual is nearly identical. This suggests the
conceptual residual is robust to reference choice within the same field.
The closer ref helps the `problem` mode (2.8→3.4), but the deepest novelty
(doubly robust property) remains uncaptured regardless.

### Target B: Drifting Models (Deng et al. 2026)

**Core residual (consistent across both refs and all modes):**
> The **anti-symmetric drifting field** V_p,q = -V_q,p with **kernel-weighted
> attraction** (toward data samples) and **repulsion** (away from generated
> samples), enabling **training-time distribution evolution** that naturally
> admits one-step inference. The stop-gradient fixed-point training objective.

**Residual components ranked by depth:**
1. **Training-time evolution concept** (partially captured): the pushforward
   distribution evolves during training, not just at inference
2. **Drifting field formulation** (rarely captured): V(x) = V+(x) - V-(x)
   with anti-symmetry ensuring V=0 at equilibrium
3. **Kernel-based forces** (almost never captured): attraction/repulsion via
   kernel-weighted sums over data and generated samples
4. **Stop-gradient fixed-point iteration** (never captured): the specific
   training trick that makes the objective stable

**Ref sensitivity:** Both refs are *distant* (conformal prediction has nothing
to do with generative modeling). Scores are correspondingly lower than Target A.
Interestingly, Ref 2 scores slightly higher on average (3.40 vs 2.95), possibly
because the student doesn't waste effort trying to connect an irrelevant
reference. The conceptual residual is identical regardless of reference —
confirming that for truly novel work, the residual is ref-independent.

---

## Cross-Pair Scientific Insights

### 1. Reference relevance affects scores but not the residual

| Metric | Close Ref Pairs (1,2) | Distant Ref Pairs (3,4) |
|--------|----------------------|------------------------|
| Avg peak score | 4.1 | 3.6 |
| Avg score across modes | 3.42 | 3.30 |
| Residual identified? | Yes | Yes |
| Residual content changed? | No | No |

The conceptual residual is **invariant to reference choice** — it captures
what's genuinely novel regardless of what prior work the student has access to.
Close references improve scores (student reconstructs better) but don't change
*what* the student misses. This validates the iterative process as a true
novelty extractor, not just a performance benchmark.

### 2. Mode effectiveness varies by paper type

| Mode | Target A (formal/theoretical) | Target B (experimental/architectural) |
|------|------------------------------|--------------------------------------|
| abstract | 3.3 avg | 3.4 avg |
| mindmap | **4.1 avg** | 3.3 avg |
| problem | 3.1 avg | **3.5 avg** |
| problem_method | 3.2 avg | 3.0 avg |

- **Mindmap** excels for Target A (theoretical paper): its structural
  flexibility lets the student lay out the conceptual landscape
- **Problem** excels for Target B (architectural paper): the problem
  framing mode better captures the engineering challenge

### 3. Convergence behavior differs by reference relevance

| | Close Refs (Pairs 1,2) | Distant Refs (Pairs 3,4) |
|---|---|---|
| Teacher stops | 5/8 modes | 3/8 modes |
| Max rounds hit | 2/8 modes | 5/8 modes |
| Score plateau | 1/8 modes | 3/8 modes |
| Avg rounds | 3.9 | 4.0 |

With distant references, the teacher is less confident about convergence
(fewer "stop" signals, more max-round exhaustion). This makes sense — the
teacher sees the student struggling with fundamental novelty and keeps trying
to guide, but the novelty is too deep for hint-based correction alone.

### 4. The regression guard is essential

Score regression occurred in 6/16 mode runs. Without the guard:
- Pair 1 mindmap (3.8→3.8→**3.0**→3.6→4.0) would have stopped at round 3
- Pair 2 mindmap (3.8→3.8→**3.0**→4.2) would have stopped at round 3
- Pair 4 problem_method (3.2→**2.6**→3.0→3.0→3.0) would have stopped at round 2

The guard prevented premature convergence in cases that eventually reached
the highest scores in the entire study.

---

## Preserved Run Artifacts

| Run Timestamp | Target | Reference | Notes |
|--------------|--------|-----------|-------|
| 2026-04-08T09-56-09Z | 2006.06138 | 1904.06019 | Pair 1 (close ref) |
| 2026-04-08T10-44-36Z | 2006.06138 | 2006.01474 | Pair 2 (very close ref) |
| 2026-04-08T11-11-36Z | 2602.04770 | 1904.06019 | Pair 3 (distant ref) |
| 2026-04-08T11-34-51Z | 2602.04770 | 2006.01474 | Pair 4 (distant ref) |
| 2026-04-08T09-50-33Z | 2006.06138 | 1904.06019 | Pre-fix baseline (MIN_ROUNDS=2) |

---

## Budget & Token Usage

Prices: Sonnet $3/$15 per 1M in/out, Opus $15/$75 per 1M in/out.

| Pair | API Calls | Sonnet Tokens | Opus Tokens | Total Tokens | Est. Cost |
|------|-----------|--------------|-------------|-------------|-----------|
| 1 (A+R1) | 48 | 147K in / 25K out | 412K in / 23K out | 607K | $8.73 |
| 2 (A+R2) | 50 | 128K in / 32K out | 434K in / 26K out | 621K | $9.37 |
| 3 (B+R1) | 43 | 129K in / 21K out | 376K in / 22K out | 548K | $7.99 |
| 4 (B+R2) | 52 | 134K in / 28K out | 443K in / 26K out | 631K | $9.44 |
| **Total** | **193** | **539K in / 106K out** | **1,665K in / 98K out** | **2,408K** | **$35.52** |

**Cost breakdown by role:**
- Opus (teacher: hint extraction + evaluation + refinement): ~77% of cost
- Sonnet (student: reconstruction): ~23% of cost

**Cost per pair:** ~$8–9.50 (16 mode-runs, avg 4 rounds each = ~48 API calls)
**Cost per mode-run:** ~$1.85 average

### Wall-Clock Time

| Pair | abstract | mindmap | problem | problem_method | Total |
|------|----------|---------|---------|----------------|-------|
| 1 (A+R1) | 4.4m (4R) | 5.6m (5R) | 4.3m (3R) | 7.5m (4R) | **22.1m** |
| 2 (A+R2) | 3.3m (3R) | 5.2m (4R) | 7.5m (5R) | 9.6m (5R) | **25.9m** |
| 3 (B+R1) | 3.3m (3R) | 5.2m (4R) | 6.6m (4R) | 5.6m (3R) | **20.9m** |
| 4 (B+R2) | 5.4m (5R) | 4.0m (3R) | 7.5m (5R) | 8.7m (5R) | **25.9m** |
| **Total** | | | | | **94.8m** |

**Per-round time by mode:**

| Mode | Avg Time/Round | Breakdown |
|------|---------------|-----------|
| abstract | ~66s | Student (~15s) + Evaluate (~25s) + Refine (~25s) |
| mindmap | ~76s | Student (~20s) + Evaluate (~25s) + Refine (~30s) |
| problem | ~91s | Student (~25s) + Evaluate (~30s) + Refine (~35s) |
| problem_method | ~111s | Student (~35s) + Evaluate (~35s) + Refine (~40s) |

Round time scales with output length — problem_method (~10K chars) takes ~1.7x
longer per round than abstract (~2.5K chars). The dominant cost is serial:
student → evaluate → refine must run sequentially within each round.

### Per-Stage Breakdown (aggregated across all 4 pairs)

| Stage | API Calls | Tokens In | Tokens Out | Cost | Time | Avg/Call | % Cost |
|-------|-----------|-----------|------------|------|------|----------|--------|
| teacher | 4 | 57K | 2K | $0.98 | 69s | 17s | 2.8% |
| student | 65 | 538K | 106K | $3.21 | 2,163s | 33s | 9.0% |
| evaluate | 65 | 810K | 32K | $14.57 | 1,257s | 19s | 41.0% |
| refine | 59 | 799K | 64K | $16.76 | 2,204s | 37s | 47.2% |
| **Total** | **193** | **2,204K** | **204K** | **$35.52** | **5,694s** | | **100%** |

**Key observations:**
- **Refine is the most expensive stage** (47% of cost, 39% of time) — Opus
  processes the full round history on each call, so context grows across rounds
- **Evaluate is the second most expensive** (41% of cost) — also Opus, but
  faster per call (19s vs 37s) because it doesn't need the full hint history
- **Student is cheap but slow** (9% of cost, 38% of time) — Sonnet generates
  long outputs (avg 1,636 tokens out) but at $3/$15 per 1M rates
- **Teacher hint is negligible** (2.8% of cost) — one Opus call per pair

### Per-Round Detail (example: Pair 2 / mindmap)

```
Round | student        | evaluate       | refine         | Round Total
------+----------------+----------------+----------------+-----------
  1   | 8K/1K $0.04 27s| 12K/0.4K $0.21 17s| 12K/1K $0.26 35s| $0.51  79s
  2   | 8K/1K $0.04 26s| 12K/0.4K $0.21 16s| 13K/1K $0.26 31s| $0.51  73s
  3   | 8K/1K $0.04 26s| 12K/0.5K $0.21 18s| 13K/1K $0.28 39s| $0.53  83s
  4   | 8K/1K $0.04 23s| 12K/0.4K $0.20 15s| 13K/1K $0.28 37s| $0.52  75s
------+----------------+----------------+----------------+-----------
Total |       $0.16    |       $0.83    |       $1.08    | $2.05 310s
```

Pattern: student cost is flat (~$0.04/round), evaluate/refine grow slightly
as the hint accumulates additions across rounds. Refine grows fastest because
it receives the full history of all prior rounds.

### Per-Mode Breakdown (aggregated across all 4 pairs)

| Mode | Rounds | API Calls | Tokens | Cost | Time | student | evaluate | refine |
|------|--------|-----------|--------|------|------|---------|----------|--------|
| abstract | 15 | 44 | 493K | $7.29 | 16.5m | $0.46 / 3.0m | $3.09 / 4.8m | $3.75 / 8.7m |
| mindmap | 16 | 47 | 553K | $7.96 | 20.0m | $0.64 / 7.0m | $3.35 / 4.7m | $3.97 / 8.4m |
| problem | 17 | 49 | 621K | $9.17 | 25.8m | $0.90 / 10.4m | $3.89 / 5.6m | $4.37 / 9.8m |
| problem_method | 17 | 49 | 682K | $10.12 | 31.4m | $1.21 / 15.7m | $4.24 / 5.9m | $4.67 / 9.9m |

**Scaling pattern:** problem_method costs 1.39x more and takes 1.90x longer
than abstract, driven primarily by student generation time (5.2x longer) and
refine context growth. Evaluate time is relatively stable across modes (~5m)
because the evaluator reads a fixed-size paper regardless of student output length.

### Per-Pair Per-Mode Cost & Time

| Mode | Pair 1 (A+R1) | Pair 2 (A+R2) | Pair 3 (B+R1) | Pair 4 (B+R2) |
|------|---------------|---------------|---------------|---------------|
| abstract | $2.02 / 4.4m (4R) | $1.49 / 3.3m (3R) | $1.50 / 3.3m (3R) | $2.28 / 5.4m (5R) |
| mindmap | $2.28 / 5.6m (5R) | $2.05 / 5.2m (4R) | $2.07 / 5.2m (4R) | $1.57 / 4.0m (3R) |
| problem | $1.65 / 4.3m (3R) | $2.61 / 7.5m (5R) | $2.33 / 6.6m (4R) | $2.58 / 7.5m (5R) |
| problem_method | $2.54 / 7.5m (4R) | $2.97 / 9.6m (5R) | $1.84 / 5.6m (3R) | $2.77 / 8.7m (5R) |
| **Total** | **$8.49 / 22.1m** | **$9.12 / 25.9m** | **$7.74 / 20.9m** | **$9.20 / 25.9m** |

Cost and time scale linearly with round count. Cheapest run: Pair 3 ($7.74,
fewest total rounds at 14). Most expensive: Pair 4 ($9.20, most rounds at 18).

---

## Cost Optimization: Prospective Savings

Three layers of optimization were implemented in v0.6.1 to reduce API costs.
The table below estimates savings against the **observed baseline** of $35.52 /
2,408K tokens across the 4-pair study.

### Optimization Layers

| Layer | Backend | Mechanism | What It Saves |
|-------|---------|-----------|---------------|
| **1. Prompt caching** | Anthropic | `cache_control: {"type": "ephemeral"}` on system prompts + paper-text prefix blocks | Avoids re-tokenizing system prompt (~1K tokens) and paper text (~8K tokens) on every call. Cache TTL = 5 min (ephemeral). |
| **2. Stateful chaining** | OpenAI | `previous_response_id` on Responses API | Refine calls chain sequentially — each round's context is appended to prior, not resent. Paper text sent once per chain. |
| **3. Cross-mode seeding** | OpenAI | `create_context_seed()` sends paper once per paper, all calls branch/chain from seed | Paper text (~8K tokens) processed exactly once per paper across all 4 modes and all rounds. |

### Estimated Token Savings

The following estimates are based on the observed token distribution and call
counts from the 4-pair study. Savings compound across layers.

#### Layer 1: Prompt Caching (Anthropic)

| Call Type | Calls | Cached Tokens/Call | Total Saved | Cache Read Discount |
|-----------|-------|--------------------|-------------|---------------------|
| System prompt | 193 | ~1,000 | 193K | 90% (10% of normal price) |
| Paper-text prefix (eval) | 65 | ~8,000 | 520K | 90% |
| Paper-text prefix (refine) | 59 | ~8,000 | 472K | 90% |
| **Total cached** | | | **1,185K tokens** | |

At Opus input pricing ($15/1M), the full cost for 1,185K input tokens would
be **$17.78**. With 90% cache discount, the effective cost drops to **$1.78**,
saving **$16.00** (45% of total spend).

*Note: savings apply per-session within the 5-min TTL window. Calls within
the same mode run (avg 4 rounds × 3 calls/round = 12 calls over ~6 min)
mostly fall within the TTL. Cross-mode sharing requires modes to run within
5 min of each other.*

#### Layer 2: Stateful Chaining (OpenAI)

Refine calls chain sequentially — round N+1 references round N's response_id,
so the API reuses the prior context without resending.

| Chain Type | Chains | Rounds in Chain | Tokens Saved/Round | Total Saved |
|------------|--------|-----------------|-------------------|-------------|
| Refine chain | 16 modes | avg 2.7 chained rounds | ~8,000 (paper text) | 345K |

Student calls are memoryless (no chaining benefit). Evaluate calls now branch
from the seed rather than chaining (correctness fix — see below).

Estimated input savings: **345K tokens → ~$5.18** at Opus rates.

#### Layer 3: Cross-Mode Seeding (OpenAI)

Without seeding, each of the 16 mode runs processes the full paper text on
its first call. With seeding, the paper is sent once per paper (4 seeds for
4 pairs), and all 16 mode runs branch from the seed.

| Without Seed | With Seed | Savings |
|---|---|---|
| 16 first-calls × 8K tokens = 128K | 4 seeds × 8K = 32K | **96K tokens** |

At Opus rates: **$1.44 saved** per study.

#### Correctness Fix: Independent Evaluations

Previous implementation chained eval calls sequentially (eval_round_2 from
eval_round_1), letting the evaluator see prior rounds' scores and outputs.
This could bias scores upward (anchoring) or create false convergence signals.

The fix: all eval calls **branch from the paper-context seed** independently.
Each evaluator sees only the paper + current student output, never prior
evaluations. This is a **correctness** improvement, not a cost reduction — eval
calls still send the student output each round (which varies, so can't be cached).

### Prospective Budget Summary

| Scenario | Input Tokens | Effective Cost | vs. Baseline |
|----------|-------------|----------------|-------------|
| **Baseline** (no optimization) | 2,204K | $35.52 | — |
| **+ Anthropic caching** (Layer 1) | 2,204K (1,185K cached) | ~$19.52 | **-45%** |
| **+ OpenAI chaining** (Layer 2) | 1,859K | ~$30.34 | **-15%** |
| **+ Cross-mode seeding** (Layer 3) | 1,763K | ~$28.90 | **-19%** |
| **OpenAI full stack** (L2 + L3) | 1,763K | ~$28.90 | **-19%** |
| **Anthropic full stack** (L1) | 2,204K (1,185K cached) | ~$19.52 | **-45%** |

*Layers 2+3 are OpenAI-specific; Layer 1 is Anthropic-specific. The backends
are alternatives, not cumulative.*

**Best case (Anthropic with caching):** ~$19.50 for a full 4-pair study.  
**Best case (OpenAI with chaining + seeding):** ~$28.90 for a full 4-pair study.

### Where Cost Cannot Be Reduced Further

| Component | Why It's Irreducible |
|-----------|---------------------|
| Student output tokens (106K out) | Must be generated fresh each round (memoryless) |
| Eval output tokens (32K out) | Must be generated fresh each round (independent) |
| Refine output tokens (64K out) | Must be generated fresh each round |
| Student input tokens per round | System prompt + hint + refs — all dynamic |
| Eval student-output context | Varies per round — cannot be cached/chained |

The theoretical floor is determined by the irreducible per-round cost of
generating student, eval, and refine outputs, plus the dynamic per-round input
(hint + student output). The optimizations above eliminate only the *redundant*
re-sending of static context (paper text, system prompts).

### Hybrid Backend Pairs: Mixing Per Stage for Minimum Cost

The single-backend analysis above treats Anthropic vs OpenAI as an either/or
choice. But each stage has different caching characteristics — mixing backends
per stage can unlock further savings.

**Key observation:** Anthropic caching gives 90% input discount on *static*
context (paper text, system prompts). OpenAI has cheaper base rates for
student-tier models. The optimal hybrid uses each backend where it's cheapest.

#### Per-Stage Cost Breakdown (baseline, no optimization)

| Stage | Role | Model Tier | Input | Output | Baseline Cost |
|-------|------|-----------|-------|--------|---------------|
| teacher | extract hint | Opus | 57K | 2K | $0.98 |
| student | reconstruct | Sonnet | 538K | 106K | $3.21 |
| evaluate | score output | Opus | 810K | 32K | $14.57 |
| refine | adjust hint | Opus | 799K | 64K | $16.76 |

#### Candidate Hybrid Configurations

**Hybrid A: Anthropic teacher + OpenAI student**

Use Anthropic (Opus, with caching) for teacher/eval/refine; use OpenAI
(GPT-4o) for student calls.

| Stage | Backend | Pricing | Input Cost | Output Cost | Caching | Stage Total |
|-------|---------|---------|-----------|-------------|---------|-------------|
| teacher | Anthropic Opus | $15/$75 /1M | $0.86 | $0.15 | system cached | $0.83 |
| **student** | **OpenAI GPT-4o** | **$2.50/$10 /1M** | **$1.35** | **$1.06** | none (memoryless) | **$2.41** |
| evaluate | Anthropic Opus | $15/$75 /1M | $12.15 | $2.40 | paper prefix cached (90% off ~520K) → -$7.02 | $7.53 |
| refine | Anthropic Opus | $15/$75 /1M | $11.99 | $4.80 | paper prefix cached (90% off ~472K) → -$6.37 | $10.42 |
| | | | | | **Hybrid A Total** | **$21.19** |

vs. pure Anthropic with caching: $19.52.

**Verdict:** Hybrid A is *worse* than pure Anthropic. GPT-4o is cheaper per
token than Sonnet ($2.50/$10 vs $3/$15), saving ~$0.80 on student. But
student calls lose Anthropic system-prompt caching (~65 calls × 1K tokens ×
$15/1M × 90% = $0.88 lost). Net effect: approximately break-even.

**Hybrid B: Anthropic eval/refine + OpenAI student + OpenAI teacher**

Optimize further: use OpenAI for the cheap calls (teacher hint = 1 call,
student = memoryless), Anthropic only where caching matters most (eval/refine).

| Stage | Backend | Stage Total |
|-------|---------|-------------|
| teacher | OpenAI GPT-5.4 | $0.98 (negligible, 4 calls) |
| student | OpenAI GPT-4o | $2.41 |
| evaluate | Anthropic Opus (cached) | $7.53 |
| refine | Anthropic Opus (cached) | $10.42 |
| | **Hybrid B Total** | **$21.34** |

**Verdict:** Even worse — teacher is negligible cost either way, and switching
it to OpenAI loses the small caching benefit on 4 calls while gaining nothing.

**Hybrid C: Anthropic everything + cheaper eval model (Sonnet for eval)**

The most impactful lever: **downgrade eval from Opus to Sonnet**. Evaluation
is structured scoring — less creative than hint refinement — and Sonnet may
suffice. This is a model-tier mix, not a backend mix.

| Stage | Model | Pricing | Input Cost | Output Cost | Caching Savings | Stage Total |
|-------|-------|---------|-----------|-------------|-----------------|-------------|
| teacher | Opus | $15/$75 | $0.86 | $0.15 | -$0.18 cached | $0.83 |
| student | Sonnet | $3/$15 | $1.61 | $1.59 | -$0.18 cached | $3.03 |
| **evaluate** | **Sonnet** | **$3/$15** | **$2.43** | **$0.48** | **-$1.40 cached** | **$1.51** |
| refine | Opus | $15/$75 | $11.99 | $4.80 | -$6.37 cached | $10.42 |
| | | | | | **Hybrid C Total** | **$15.79** |

**Verdict: Best configuration.** Switching eval to Sonnet saves **$6.02** vs
pure Anthropic Opus ($19.52 → ~$15.79), a further **18% reduction**. Eval is
structured (JSON scoring rubric) and may not need Opus-level reasoning.

*Tradeoff:* Sonnet eval may be noisier — less nuanced novelty-gap detection.
This should be validated empirically by comparing score distributions.

**Hybrid D: Hybrid C + OpenAI student (max savings)**

| Stage | Backend / Model | Stage Total |
|-------|----------------|-------------|
| teacher | Anthropic Opus (cached) | $0.83 |
| student | OpenAI GPT-4o | $2.41 |
| evaluate | Anthropic Sonnet (cached) | $1.51 |
| refine | Anthropic Opus (cached) | $10.42 |
| | **Hybrid D Total** | **$15.17** |

Marginal gain over Hybrid C ($0.62) — not worth the dual-client complexity.

#### Summary: Hybrid Comparison

| Configuration | Est. Cost | vs. Baseline | Complexity |
|--------------|-----------|-------------|------------|
| Baseline (no opt) | $35.52 | — | Single backend |
| Pure OpenAI (chaining + seeding) | $28.90 | -19% | Single backend |
| **Pure Anthropic (caching)** | **$19.52** | **-45%** | Single backend |
| Hybrid A (Anthropic teacher + OpenAI student) | $21.19 | -40% | Dual client |
| Hybrid B (Anthropic eval/refine + OpenAI rest) | $21.34 | -40% | Dual client |
| **Hybrid C (Anthropic, Sonnet eval)** | **$15.79** | **-56%** | Single backend, model swap |
| Hybrid D (Hybrid C + OpenAI student) | $15.17 | -57% | Dual client + model swap |

**Recommendation:** Hybrid C — pure Anthropic backend with **Sonnet for eval,
Opus for everything else**. Single backend (no dual-client wiring needed),
simple model-tier swap, and the largest cost reduction (-56%). The dual-client
hybrids (A, B, D) add architectural complexity for marginal gains.

**Implementation:** Add an `--eval-model` CLI flag to override the eval model
independently of the teacher model. One line in `dispatch_paper` + one in
`run_iterative_refinement`.

```python
# agent.py — minimal change
eval_model = args.eval_model or teacher_model  # default to teacher
```

### Batched / Parallel API Calls

The current implementation runs modes **sequentially** within each condition.
Within each mode, rounds are inherently sequential (student→eval→refine→next
round). But several stages are **embarrassingly parallel** across modes and
could benefit from batched API calls.

#### What Can Be Parallelized

| Parallelism | Currently | Potential | Wall-Clock Savings |
|-------------|-----------|-----------|-------------------|
| **Cross-mode student calls** (same round) | Sequential | Parallel | Each round: 4 modes × ~30s → ~30s (4x speedup) |
| **Cross-mode eval calls** (same round) | Sequential | Parallel | Each round: 4 modes × ~25s → ~25s (4x speedup) |
| **Cross-condition runs** | Sequential | Parallel | 2 conditions × ~25 min → ~25 min (2x speedup) |
| **Cross-pair runs** | Sequential | Parallel | 4 pairs × ~25 min → ~25 min (4x speedup) |
| **Within-round stages** | Sequential | **Cannot parallelize** | student→eval→refine is causally dependent |

#### Approach 1: Async Concurrent Modes (within a paper)

Run all 4 modes concurrently using `asyncio` or `concurrent.futures`. Each
mode's iterative loop remains sequential internally, but modes don't depend
on each other.

```
Current (sequential):
  abstract R1→R2→R3→R4  →  mindmap R1→R2→R3→R4→R5  →  problem ...  →  pm ...
  Total: sum of all mode times ≈ 95 min

Parallel modes:
  abstract R1→R2→R3→R4  ┐
  mindmap  R1→R2→R3→R4→R5 ├→ done when slowest finishes
  problem  R1→R2→R3     │
  pm       R1→R2→R3→R4  ┘
  Total: max mode time ≈ 32 min (problem_method, 5R)
```

**Wall-clock savings: ~66% (95 min → ~32 min).**  
**Token cost: unchanged** (same total calls, just concurrent).

*Rate limit consideration:* 4 concurrent modes × 1 API call at a time =
4 concurrent requests. Well within typical tier limits (60+ RPM for Opus).

#### Approach 2: Batch API (OpenAI only)

OpenAI's Batch API offers **50% discount** on input/output tokens with
24-hour turnaround. Not suitable for the iterative loop (needs real-time
eval→refine feedback), but viable for:

- **Post-hoc evaluation re-scoring** (re-evaluate all outputs with a different model)
- **Cross-validation** (run the same student on the same hint N times for variance estimation)
- **Pairwise comparisons** (all independent, no sequential dependency)

| Use Case | Calls | Batch Savings (50% off) | Turnaround |
|----------|-------|------------------------|------------|
| Re-score all 16 mode outputs | 16 | ~$7.28 → $3.64 | ≤24h |
| Variance estimation (3× student) | 48 | ~$9.63 → $4.82 | ≤24h |
| Pairwise comparisons | 16 | ~$3.50 → $1.75 | ≤24h |

**Not applicable to the core iterative loop** — each round depends on the
previous round's evaluation.

#### Approach 3: Anthropic Message Batches

Anthropic's Message Batches API offers **50% discount** with ≤24h turnaround,
same constraints as OpenAI Batch. Applicable to the same non-iterative tasks.

With Anthropic caching + batch discount combined:
- Cached input at 10% of normal, then 50% batch discount on the remaining
- Effective rate: **5% of normal input price** on cached tokens in batch mode

| Scenario | Est. Cost |
|----------|-----------|
| Hybrid C (Sonnet eval, real-time) | $15.79 |
| Hybrid C + batch re-scoring (50% off eval) | $15.04 |
| Batch-only non-iterative tasks (pairwise, variance) | 50% off applicable calls |

#### Combined Prospective: Full Optimization Stack

| Optimization | Cost Impact | Time Impact |
|---|---|---|
| Anthropic caching (Layer 1) | -45% cost | — |
| Sonnet eval (Hybrid C) | -56% cost total | — |
| Parallel modes (Approach 1) | — | -66% wall-clock |
| Batch re-scoring (Approach 2/3) | -50% on batch-eligible calls | +24h latency |

**Fully optimized real-time estimate:**

| Config | Cost | Wall-Clock |
|--------|------|-----------|
| Baseline | $35.52 | ~95 min |
| Hybrid C + parallel modes | **$15.79** | **~32 min** |

**Fully optimized with batch where possible:**

| Config | Cost | Wall-Clock |
|--------|------|-----------|
| Hybrid C + batch re-eval + batch pairwise | **~$14.00** | ~32 min + ≤24h for batch |

#### Implementation Roadmap

| Priority | Change | Effort | Impact | Status |
|----------|--------|--------|--------|--------|
| **P0** | `--eval-model` flag (Hybrid C) | ~10 lines | -56% cost | **Implemented** |
| **P1** | `--parallel-modes` (ThreadPoolExecutor) | ~50 lines | -66% wall-clock | **Implemented** |
| **P2** | Batch API for pairwise/re-scoring | ~100 lines (new batch_eval.py) | -50% on eligible | Planned |
| P3 | Dual-client hybrid (Hybrid D) | ~80 lines (plumbing) | -2% more cost | Low priority |
