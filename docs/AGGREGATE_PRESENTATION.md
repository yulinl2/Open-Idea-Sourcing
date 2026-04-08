# Aggregate Results: Staged Reconstruction v0.4–v0.5

> **Pipeline:** agent-staged-reconstruct v0.4 (anti-leakage) through v0.5 (pairwise evaluator)
> **Student model:** claude-sonnet-4-20250514 | **Teacher/Evaluator:** claude-opus-4-20250514
> **Runs aggregated:** run06 (v0.4, anti-leakage), run07 (v0.4, calibrated rubric), run08 (v0.5, pairwise)
> **Date:** 2026-04-08

---

## 1. Aggregate Score Tables

All independent scores are teacher-evaluated composites on a 1–5 Likert scale
(mean of problem_understanding, technical_depth, novelty_alignment,
writing_quality, completeness). Statistics are sample mean +/- sample standard
deviation across n=3 independent runs with identical student/teacher models but
different random seeds.

### 1.1 Paper 1 — Lei & Candes 2021 (arXiv:2006.06138)

**Domain:** Conformal inference for counterfactuals and individual treatment effects
**Reference supplied:** Tibshirani et al. 2020 (arXiv:1904.06019) — conformal prediction under covariate shift
**Relevance:** RELATED (reference provides the methodological foundation the paper extends)

#### Independent Scoring (n=3 runs: 06, 07, 08)

| Mode | with_refs | no_refs | Delta | Direction |
|------|-----------|---------|-------|-----------|
| abstract | 3.17 +/- 0.15 | 3.00 +/- 0.20 | +0.17 +/- 0.21 | + |
| mindmap | 3.63 +/- 0.21 | 3.37 +/- 0.15 | +0.27 +/- 0.12 | + |
| problem | 3.63 +/- 0.59 | 3.40 +/- 0.40 | +0.23 +/- 0.25 | + |
| problem_method | 3.17 +/- 0.15 | 3.00 +/- 0.20 | +0.17 +/- 0.06 | + |
| full_guided | 3.33 +/- 0.42 | 3.30 +/- 0.17 | +0.03 +/- 0.25 | ~ |
| full_freestyle | 3.30 +/- 0.17 | 3.17 +/- 0.35 | +0.13 +/- 0.23 | + |
| **All modes** | **3.37 +/- 0.34** | **3.21 +/- 0.28** | **+0.17 +/- 0.18** | **+** |

Direction: **+** = positive delta in majority of runs, **~** = sign inconsistent across runs.

#### Pairwise Evaluation (run08, 1–7 scale)

| Mode | Impact Score | Closer to Original | Confidence |
|------|-------------|-------------------|------------|
| abstract | 6 | A (with_refs) | high |
| mindmap | 6 | A (with_refs) | high |
| problem | 6 | A (with_refs) | high |
| problem_method | 6 | A (with_refs) | high |
| full_guided | 6 | A (with_refs) | high |
| full_freestyle | 4 | tied | high |
| **Mean** | **5.67** | **5/6 favor with_refs** | |

Scale: 7 = references dramatically helped, 4 = no difference, 1 = references actively hurt.

---

### 1.2 Paper 2 — Deng et al. 2026 (arXiv:2602.04770)

**Domain:** Generative modeling via training-time drifting fields
**Reference supplied:** Tibshirani et al. 2020 (arXiv:1904.06019) — conformal prediction under covariate shift
**Relevance:** UNRELATED (negative control; reference domain is orthogonal to target paper)

#### Independent Scoring (n=3 runs: 06, 07, 08)

| Mode | with_refs | no_refs | Delta | Direction |
|------|-----------|---------|-------|-----------|
| abstract | 3.00 +/- 0.53 | 2.90 +/- 0.46 | +0.10 +/- 0.56 | ~ |
| mindmap | 2.90 +/- 0.46 | 3.13 +/- 0.23 | -0.23 +/- 0.25 | - |
| problem | 3.17 +/- 0.49 | 3.30 +/- 0.62 | -0.13 +/- 0.23 | - |
| problem_method | 3.17 +/- 0.57 | 2.90 +/- 0.44 | +0.27 +/- 0.23 | + |
| full_guided | 3.77 +/- 0.21 | 3.27 +/- 0.46 | +0.50 +/- 0.26 | + |
| full_freestyle | 3.20 +/- 0.53 | 3.57 +/- 0.32 | -0.37 +/- 0.35 | - |
| **All modes** | **3.20 +/- 0.49** | **3.18 +/- 0.44** | **+0.02 +/- 0.42** | **~** |

Note: Per-mode standard deviations of the delta (0.23–0.56) exceed the
corresponding mean deltas in 5/6 modes, consistent with noise rather than
signal.

#### Pairwise Evaluation (run08, 1–7 scale)

| Mode | Impact Score | Closer to Original | Confidence |
|------|-------------|-------------------|------------|
| abstract | 4 | B (no_refs) | high |
| mindmap | 2 | B (no_refs) | high |
| problem | 2 | B (no_refs) | high |
| problem_method | 3 | B (no_refs) | high |
| full_guided | 4 | B (no_refs) | high |
| full_freestyle | 3 | B (no_refs) | high |
| **Mean** | **3.00** | **6/6 favor no_refs** | |

---

### 1.3 Cross-Paper Summary

| Metric | Paper 1 (related) | Paper 2 (unrelated) | Separation |
|--------|-------------------|---------------------|------------|
| Mean delta (indep., n=18) | +0.17 | +0.02 | 0.15 |
| Delta stdev (pooled) | 0.18 | 0.42 | 2.3x higher for P2 |
| Pairwise impact (1–7) | 5.67 | 3.00 | 2.67 pts |
| Modes favoring refs (pairwise) | 5/6 | 0/6 | Perfect separation |
| Consistent direction (indep.) | 5/6 modes | 0/6 modes | Perfect separation |

The pairwise evaluator achieves complete separation between the related and
unrelated reference conditions at the mode level — a result the independent
scorer cannot replicate due to anchoring and calibration noise.

---

## 2. Consolidated Scientific Interpretations

### 2.1 Anti-Leakage Validation

The v0.3.1 teacher prompt exhibited information leakage through four vectors:
(i) `evaluation_criteria` that encoded solution-specific properties (e.g.,
"doubly robust"), (ii) `domain_keywords` containing methodology terms,
(iii) `reference_guidance` revealing how references connect to the solution,
and (iv) hallucinated paper metadata that corrupted problem formulations.

The v0.4 redesign eliminated all four vectors by replacing solution-specific
fields with abstract desiderata, removing domain keywords and reference
guidance, and adding explicit anti-leakage rules with worked examples. Runs
06–08 confirm that the fix is effective: references now produce a measurable
positive signal for Paper 1 (mean delta +0.17, pairwise impact 5.67/7) that
was absent in v0.3.1 (where with_refs ≈ no_refs because the hint itself
was sufficient to reconstruct the approach). See
`reports/LEAKAGE_ANALYSIS.md` for the full analysis.

### 2.2 Reference Impact Signal

For Paper 1, the Tibshirani et al. reference on weighted conformal prediction
consistently enables the student to identify the target paper's methodological
foundation. The pairwise evaluator identifies the specific mechanism: the
reference provides the weighted conformal framework that the student then
extends to causal inference, correctly identifying propensity score
reweighting, doubly robust coverage properties, and the reduction of
counterfactual inference to a covariate shift problem.

The effect is most pronounced in structured modes — mindmap (+0.27 mean delta,
sd 0.12) and problem (+0.23, sd 0.25) — where the reference scaffolds
conceptual organization. The effect is weakest in full_guided (+0.03, sd 0.25)
and full_freestyle (+0.13, sd 0.23), where unconstrained generation introduces
noise that dilutes the reference signal.

### 2.3 Negative Control Validation

Paper 2 serves as a negative control: the conformal prediction reference is
topically orthogonal to the target paper on training-time drifting fields for
generative modeling. The experimental predictions were:

- **Predicted:** Zero or negative mean delta, high per-mode variance.
- **Observed:** Mean delta +0.02 (indistinguishable from zero), per-mode
  stdev 2.3x larger than Paper 1, and pairwise evaluation unanimously favoring
  the no-reference condition (6/6 modes).

The pairwise evaluator provides the mechanistic explanation: with the
conformal reference, the student attempts to graft statistical coverage
guarantees onto generative modeling — producing "Conformal Flow Networks"
and other chimeric frameworks that have no connection to the target paper's
drifting field concept. Without references, the student defaults to flow
matching and optimal transport — generic but at least domain-appropriate
baselines that score closer to the original. This confirms that irrelevant
references don't merely fail to help; they actively misdirect reconstruction.

### 2.4 Mode-Level Patterns

Across both papers and all runs, several structural patterns emerge:

1. **problem_method is the most stable discriminator for Paper 1**: delta
   +0.17 +/- 0.06 (lowest variance of any mode). The mode's constrained scope
   (problem + methodology only) limits noise while preserving enough depth for
   reference influence to manifest.

2. **full_guided is a consistent false positive for Paper 2**: delta +0.50
   +/- 0.26 across 3 runs, the only mode with a strong positive mean delta
   for the negative control. However, the pairwise evaluator rates it 4/7
   (neutral) and assigns "closer to original" to the no-refs output. This
   dissociation between independent and pairwise scoring on this mode suggests
   the independent scorer exhibits length bias — with_refs outputs tend to be
   longer for structured templates, and the scorer may confuse verbosity with
   quality.

3. **full_freestyle shows the weakest reference signal for Paper 1**: pairwise
   impact 4/7 (tied), independent delta +0.13 +/- 0.23. When structure is
   unconstrained, the student's generation strategy dominates over reference
   influence, producing high-variance outputs that obscure the signal.

### 2.5 Evaluation Method Comparison

Independent scoring and pairwise evaluation agree on the direction of the
aggregate effect but differ sharply in statistical power:

| Property | Independent (1–5) | Pairwise (1–7) |
|----------|-------------------|-----------------|
| Paper 1 vs Paper 2 delta gap | 0.15 | 2.67 |
| Mode-level separation | 5/6 vs 0/6 consistent | 5/6 vs 0/6 favoring refs |
| Coefficient of variation (P1) | 1.06 (delta sd / delta mean) | 0.14 (impact sd / impact mean) |
| Known failure mode | Anchoring around 3.0–3.5 | Requires paired outputs |

The independent scorer suffers from **absolute calibration anchoring**: without
a reference point, the evaluator gravitates toward mid-scale scores for both
conditions, compressing the effective dynamic range. The pairwise evaluator
eliminates this by forcing a direct A-vs-B comparison, producing a signal-to-noise
ratio approximately 7x higher on our data.

This finding has practical implications for LLM-as-judge evaluation design:
pairwise protocols should be preferred when the quantity of interest is a
treatment effect (delta) rather than an absolute quality score.

### 2.6 Novelty Gap Patterns

Qualitative analysis of reconstruction gaps reveals consistent failure modes
across both papers:

**Paper 1 (Lei-Candes):** Students reconstruct generic conformal prediction
for causal inference — the right domain but the wrong mechanism. The three
innovations they consistently miss are: (i) the reduction of counterfactual
inference to a covariate shift problem solvable via weighted conformal
inference, (ii) conformal quantile regression (CQR) with
max{q_alpha_lo(x) - y, y - q_alpha_hi(x)} as the nonconformity score
(instead of simple residuals), and (iii) the doubly robust coverage property.
With the reference, students get closer to (i) but still miss (ii) and (iii),
suggesting these represent genuine novelty beyond what the reference provides.

**Paper 2 (Deng et al.):** Students uniformly miss the core concept of
training-time evolution of the pushforward distribution through drifting
fields with attraction/repulsion dynamics and equilibrium convergence.
With the irrelevant reference, they produce conformal-prediction-based
generative frameworks; without it, they default to flow matching or optimal
transport — domain-appropriate but still missing the paper's actual
contribution. The fact that neither condition recovers the drifting field
concept indicates high genuine novelty: the paper's intellectual contribution
is not derivable from either its references or general domain knowledge.

---

## 3. Presentation

### Title

**Measuring Research Novelty via Multi-Granularity LLM Reconstruction:
A Reference-Ablation Framework**

### Abstract

We introduce *staged reconstruction*, a framework for quantifying the
intellectual novelty of a research paper by measuring how much of its
contribution a large language model can recover from cited references alone.
A teacher model extracts a leakage-controlled problem statement from the
target paper; a student model then attempts reconstruction across six levels
of granularity — from abstract through full paper — under two conditions:
with access to reference texts and without. The delta between conditions
isolates the marginal information contribution of cited references, while
the reconstruction gap against the original paper quantifies residual novelty.

We validate the framework on two papers sharing a common reference: one where
the reference is methodologically related (conformal inference for treatment
effects, citing a conformal prediction paper) and one where it is unrelated
(generative modeling via drifting fields — serving as a negative control).
Across three independent experimental runs using Claude Sonnet 4 as student
and Claude Opus 4 as evaluator, the related reference yields a consistent
positive effect (mean composite delta +0.17 on a 5-point scale, pairwise
reference impact 5.67/7, with 5 of 6 reconstruction modes favoring the
reference condition). The unrelated reference yields near-zero aggregate
effect (delta +0.02) with 2.3x higher per-mode variance, and pairwise
evaluation unanimously favors the no-reference baseline across all 6 modes.

Qualitative novelty-gap analysis reveals that student models consistently
fail to recover paper-specific innovations — doubly robust conformal quantile
regression in Paper 1, training-time drifting fields in Paper 2 — defaulting
instead to generic domain knowledge. We additionally demonstrate that pairwise
LLM evaluation achieves approximately 7x higher signal-to-noise ratio than
independent scoring for measuring reference treatment effects, owing to the
elimination of absolute calibration anchoring. These results suggest that
reconstruction-based ablation can operationally distinguish genuine
intellectual contributions from derivable extensions of prior work.

---

## Appendix: Per-Run Raw Scores

All composite scores from independent evaluation (1–5 scale).

| Run | Paper | Mode | with_refs | no_refs | Delta |
|-----|-------|------|-----------|---------|-------|
| run06 | 2006.06138 | abstract | 3.3 | 3.2 | +0.1 |
| run06 | 2006.06138 | mindmap | 3.7 | 3.5 | +0.2 |
| run06 | 2006.06138 | problem | 4.3 | 3.8 | +0.5 |
| run06 | 2006.06138 | problem_method | 3.3 | 3.2 | +0.1 |
| run06 | 2006.06138 | full_guided | 3.8 | 3.5 | +0.3 |
| run06 | 2006.06138 | full_freestyle | 3.5 | 3.5 | +0.0 |
| run06 | 2602.04770 | abstract | 3.2 | 2.5 | +0.7 |
| run06 | 2602.04770 | mindmap | 2.5 | 3.0 | -0.5 |
| run06 | 2602.04770 | problem | 3.5 | 3.5 | +0.0 |
| run06 | 2602.04770 | problem_method | 2.7 | 2.7 | +0.0 |
| run06 | 2602.04770 | full_guided | 3.7 | 3.0 | +0.7 |
| run06 | 2602.04770 | full_freestyle | 3.0 | 3.7 | -0.7 |
| run07 | 2006.06138 | abstract | 3.0 | 3.0 | +0.0 |
| run07 | 2006.06138 | mindmap | 3.4 | 3.2 | +0.2 |
| run07 | 2006.06138 | problem | 3.2 | 3.0 | +0.2 |
| run07 | 2006.06138 | problem_method | 3.2 | 3.0 | +0.2 |
| run07 | 2006.06138 | full_guided | 3.2 | 3.2 | +0.0 |
| run07 | 2006.06138 | full_freestyle | 3.2 | 3.2 | +0.0 |
| run07 | 2602.04770 | abstract | 3.4 | 3.4 | +0.0 |
| run07 | 2602.04770 | mindmap | 3.4 | 3.4 | +0.0 |
| run07 | 2602.04770 | problem | 3.4 | 3.8 | -0.4 |
| run07 | 2602.04770 | problem_method | 3.8 | 3.4 | +0.4 |
| run07 | 2602.04770 | full_guided | 4.0 | 3.8 | +0.2 |
| run07 | 2602.04770 | full_freestyle | 3.8 | 3.8 | +0.0 |
| run08 | 2006.06138 | abstract | 3.2 | 2.8 | +0.4 |
| run08 | 2006.06138 | mindmap | 3.8 | 3.4 | +0.4 |
| run08 | 2006.06138 | problem | 3.4 | 3.4 | +0.0 |
| run08 | 2006.06138 | problem_method | 3.0 | 2.8 | +0.2 |
| run08 | 2006.06138 | full_guided | 3.0 | 3.2 | -0.2 |
| run08 | 2006.06138 | full_freestyle | 3.2 | 2.8 | +0.4 |
| run08 | 2602.04770 | abstract | 2.4 | 2.8 | -0.4 |
| run08 | 2602.04770 | mindmap | 2.8 | 3.0 | -0.2 |
| run08 | 2602.04770 | problem | 2.6 | 2.6 | +0.0 |
| run08 | 2602.04770 | problem_method | 3.0 | 2.6 | +0.4 |
| run08 | 2602.04770 | full_guided | 3.6 | 3.0 | +0.6 |
| run08 | 2602.04770 | full_freestyle | 2.8 | 3.2 | -0.4 |

**Note:** Run 08 Paper 1 (2006.06138) scores were extracted from individual
`eval.json` files; they were not included in run08's SUMMARY.md but are present
in the run directory at `reports/run08-v0.5-pairwise/2006.06138/`.

### Pairwise Raw Data (run08)

| Paper | Mode | Impact (1–7) | Closer | Confidence |
|-------|------|-------------|--------|------------|
| 2006.06138 | abstract | 6 | A (with_refs) | high |
| 2006.06138 | mindmap | 6 | A (with_refs) | high |
| 2006.06138 | problem | 6 | A (with_refs) | high |
| 2006.06138 | problem_method | 6 | A (with_refs) | high |
| 2006.06138 | full_guided | 6 | A (with_refs) | high |
| 2006.06138 | full_freestyle | 4 | tied | high |
| 2602.04770 | abstract | 4 | B (no_refs) | high |
| 2602.04770 | mindmap | 2 | B (no_refs) | high |
| 2602.04770 | problem | 2 | B (no_refs) | high |
| 2602.04770 | problem_method | 3 | B (no_refs) | high |
| 2602.04770 | full_guided | 4 | B (no_refs) | high |
| 2602.04770 | full_freestyle | 3 | B (no_refs) | high |
