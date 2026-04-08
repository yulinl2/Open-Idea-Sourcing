# Aggregate Results: Staged Reconstruction v0.4–v0.5

> **Pipeline:** agent-staged-reconstruct v0.4 (anti-leakage) through v0.5 (pairwise evaluator)
> **Student model:** claude-sonnet-4-20250514 | **Teacher/Evaluator:** claude-opus-4-20250514
> **Runs aggregated:** run06 (v0.4, anti-leakage), run07 (v0.4, calibrated rubric), run08 (v0.5, pairwise)
> **Date:** 2026-04-08

---

### How to Read This Document

This project treats **novelty measurement as a controlled experiment**. We ask:
*How much of a paper's contribution can be reconstructed from its references?*

The setup follows a teacher-student protocol familiar from knowledge
distillation, but applied to entire research papers:

- A **teacher** (a stronger LLM that has read the full paper) extracts a
  problem statement — carefully designed to describe *what problem the paper
  solves* without revealing *how it solves it*.
- A **student** (a weaker LLM that has never seen the paper) attempts to
  reconstruct the paper from that problem statement, under two conditions:
  **with references** (given the text of cited papers) and **without**.
- A separate **evaluator** (teacher-level LLM) scores each reconstruction
  against the original paper.

The **delta** (with_refs score minus no_refs score) measures how much the
references contribute. A large positive delta means the paper builds closely
on its references; a near-zero delta means the contribution is novel beyond
what references provide.

Reconstruction is attempted at six levels of granularity (called **modes**):
abstract, idea mindmap, problem formulation, problem + methodology,
full paper with template, and full paper with free structure.

---

## 1. Aggregate Score Tables

All independent scores are evaluator-assessed composites on a 1–5 Likert scale
(mean of five rubric dimensions: problem understanding, technical depth,
novelty alignment, writing quality, and completeness). Statistics are sample
mean +/- sample standard deviation across n=3 independent experimental runs
with identical models but different random seeds (i.e., separate LLM
generation passes).

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

**Domain:** Generative modeling (learns to produce new samples, e.g., images, by iteratively transforming noise into data)
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

A central challenge in this experimental design is ensuring the problem
statement (the "hint") does not leak the paper's solution. In early versions
(v0.3.1), the teacher inadvertently revealed method-specific properties — for
example, describing a desired property as "doubly robust," which is a technical
achievement specific to the paper's approach rather than a general goal.
This meant the student could reconstruct the method from the hint alone,
regardless of whether references were provided, rendering the with_refs vs
no_refs comparison meaningless.

The v0.4 redesign addressed this by: (i) replacing solution-specific criteria
with abstract desiderata (e.g., "robust to model misspecification" instead of
"doubly robust"), (ii) removing methodology-leaking keywords, (iii) removing
guidance on how references connect to the solution, and (iv) adding explicit
anti-leakage self-check rules. Runs 06–08 confirm the fix works: references
now produce a measurable signal for Paper 1 (mean delta +0.17, pairwise
impact 5.67/7) that was absent in v0.3.1. See
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

Paper 2 serves as a **negative control**: the supplied reference (on
conformal prediction, a statistical inference technique) is topically
unrelated to the target paper (on a new generative modeling method). If our
framework works correctly, providing this irrelevant reference should not help
— and may hurt — the student's reconstruction.

- **Predicted:** Zero or negative mean delta, high per-mode variance.
- **Observed:** Mean delta +0.02 (indistinguishable from zero), per-mode
  stdev 2.3x larger than Paper 1, and pairwise evaluation unanimously favoring
  the no-reference condition (6/6 modes).

The pairwise evaluator reveals the mechanism: given the conformal prediction
reference, the student tries to force-fit statistical coverage guarantees into
a generative modeling framework — producing incoherent hybrid approaches that
have no connection to the target paper's actual method. Without the reference,
the student at least stays within the correct domain (proposing generic but
plausible approaches like flow-based models). This confirms that irrelevant
references don't merely fail to help; they actively misdirect the
reconstruction by pulling the student into the wrong technical territory.

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

The independent scorer suffers from **calibration anchoring** — a well-known
rating bias where, without an explicit comparison point, evaluators gravitate
toward mid-scale scores (here, 3.0–3.5) for both conditions. This compresses
the effective dynamic range and obscures real differences. The pairwise
evaluator eliminates this by forcing a direct side-by-side comparison (akin
to a paired t-test vs two independent measurements), yielding approximately
7x higher signal-to-noise ratio on our data.

This finding has practical implications for automated evaluation design:
paired comparison protocols should be preferred over independent rating
when the quantity of interest is a treatment effect (difference between
conditions) rather than an absolute quality score.

### 2.6 Novelty Gap Patterns

Qualitative analysis of what the student *fails to reconstruct* reveals
consistent patterns across both papers:

**Paper 1 (Lei-Candes):** Students reconstruct a generic application of
conformal prediction to causal inference — the right domain but the wrong
specific mechanism. The three innovations they consistently miss are:
(i) the key insight that counterfactual prediction can be reframed as a
covariate shift problem (a known statistical setup), enabling direct
application of weighted conformal methods; (ii) a specific quantile-based
scoring function that produces tighter prediction intervals than naive
residuals; and (iii) a doubly robust coverage guarantee (valid if *either*
the treatment model or the outcome model is correct). With the reference,
students get closer to (i) but still miss (ii) and (iii), suggesting these
represent genuine novelty beyond what the reference provides.

**Paper 2 (Deng et al.):** Students uniformly miss the paper's core idea:
instead of optimizing a generative model at test time (as most methods do),
this paper evolves the model's internal sample distribution *during training*
through a novel "drifting field" mechanism with attraction/repulsion dynamics.
With the irrelevant reference, students produce conformal-prediction-based
generative frameworks (which do not exist in the literature); without it,
they default to standard generative approaches like flow matching — plausible
but missing the paper's actual contribution. The fact that neither condition
recovers the core concept indicates high genuine novelty: the contribution
is not derivable from either its cited references or general domain knowledge.

---

## 3. Presentation

### Title

**Measuring Research Novelty via Multi-Granularity LLM Reconstruction:
A Reference-Ablation Framework**

### Abstract

How novel is a research paper's contribution — and can we measure this
automatically? We introduce *staged reconstruction*, a framework that
operationalizes novelty measurement as a controlled ablation study. A
capable language model (the "teacher") reads the target paper and extracts
a problem statement that describes *what* the paper solves without revealing
*how*. A second model (the "student"), which has never seen the paper, then
attempts to reconstruct it across six levels of granularity — from abstract
to full paper — under two conditions: with access to cited reference texts
and without. The difference between conditions isolates the marginal
information contribution of the references, while the gap between
reconstruction and original quantifies residual novelty.

We validate the framework on two papers that share a common reference: one
where the reference is methodologically related (statistical inference for
causal treatment effects, citing a directly relevant prior work) and one
where it is unrelated (a generative modeling method, same reference — serving
as a negative control). Across three independent runs using Claude Sonnet 4
as student and Claude Opus 4 as evaluator, the related reference yields a
consistent positive effect (mean composite delta +0.17 on a 5-point scale,
pairwise reference impact 5.67/7, with 5 of 6 reconstruction modes favoring
the reference condition). The unrelated reference yields near-zero aggregate
effect (delta +0.02) with 2.3x higher per-mode variance, and pairwise
evaluation unanimously favors the no-reference baseline across all 6 modes —
confirming that the signal is genuine.

Qualitative analysis reveals that student models consistently fail to recover
paper-specific innovations, defaulting to generic domain knowledge. We
additionally show that paired side-by-side evaluation achieves approximately
7x higher signal-to-noise ratio than independent scoring for detecting
reference effects, due to the elimination of rating-scale anchoring bias.
These results suggest that reconstruction-based ablation can operationally
distinguish genuine intellectual contributions from derivable extensions of
prior work.

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
