# Teacher Prompt Info Leakage Analysis

**Date:** 2026-04-04
**Context:** Examining v0.3.1 teacher hints for solution leakage before redesign

## Summary

The v0.3.1 teacher prompt produced hints that leaked the paper's approach
through four distinct vectors. This was compounded by hallucinated paper
metadata, meaning most archived results tested fabricated problems rather
than the actual papers.

## Leakage Vectors Identified

### 1. `evaluation_criteria` leaked solution properties

The prompt asked: "What would a good solution look like?" This inherently
reveals what the paper's solution achieves.

**Example (2103.04984 hint, which was actually Lei-Candès 2006.06138):**
> "A good solution should provide prediction intervals with guaranteed
> marginal coverage... the method should be robust to misspecification of
> either the propensity score or outcome models (doubly robust property)"

"Doubly robust" is the paper's key technical contribution, not a general
desideratum. A researcher BEFORE seeing the paper would not think to require
double robustness — they'd want "robustness to model misspecification" at most.

### 2. `domain_keywords` leaked methodology terms

Keywords included method-specific terms like "conformal inference", "inverse
propensity weighting", "double robustness" — all core to the paper's approach,
not just its problem domain.

### 3. `reference_guidance` revealed how references connect to solution

> "This paper introduces weighted conformal prediction methods... directly
> relevant because in causal inference, the treated and control groups often
> have different covariate distributions"

This tells the student exactly how to apply the reference — bridging from
covariate shift (reference) to causal inference (paper) is THE key insight.

### 4. Empirical confirmation: with_refs ≈ no_refs

Both conditions produced nearly identical approaches (doubly robust conformal
prediction with IPW weighting). The no_refs student even invented "DR-CTE"
(Doubly Robust Conformal Treatment Effects) — essentially the paper's method
— from the hint alone, without any reference text. This proves the hint
itself was sufficient to reconstruct the approach.

**Scores:** with_refs vs no_refs deltas were mostly ≈ (±0.2), confirming
the hint dominated the reference signal.

## Redesign (v0.4)

The teacher prompt was rewritten with:

1. **Removed `evaluation_criteria`** → replaced with `desirable_properties`
   that describe abstract desiderata ("should work without strong distributional
   assumptions") not specific achievements ("should be doubly robust")

2. **Removed `domain_keywords`** → these consistently leaked method terms

3. **Removed `reference_guidance`** → prevented hinting at how references
   connect to the solution

4. **Added explicit anti-leakage rules** with examples of acceptable vs
   leaked properties

5. **Added self-check instruction** — teacher must review each field and ask
   "Could a reader infer the approach from this alone?"

## Expected Impact

With the corrected data and redesigned prompt:

- **Paper 1 (2006.06138, Lei-Candès):** The reference paper (1904.06019,
  conformal prediction under covariate shift) is directly relevant. We expect
  a real with_refs vs no_refs signal — the reference should help the student
  discover weighted conformal methods, but the specific application to
  counterfactual inference should require genuine insight.

- **Paper 2 (2602.04770, Deng et al.):** Generative modeling — completely
  unrelated to the reference. This is a clean negative control. The with_refs
  condition should show zero or negative delta (irrelevant reference = noise).

## Data Correction

All three test papers in v0.3.1 had fabricated metadata. The actual papers
at the user-specified URLs are now correctly identified and cached. See
`reports/v0.3.1-abstract-fallback_2026-04-04/VERSION_NOTES.md` for details.

---

## Validation Results (v0.5, 2026-04-06)

The predictions above have been validated by run08 (v0.5 pairwise evaluator):

### Paper 1 (Lei-Candès, RELATED reference)

**Prediction:** Real with_refs vs no_refs signal expected.
**Result: CONFIRMED.**

- Independent composite delta: **+0.20** avg (refs help)
- Pairwise impact: **6/7** on 5 of 6 modes (strong positive)
- All 5 modes favor with_refs output (Output A)
- Evaluator: *"Reference to Tibshirani et al. was crucial for correctly
  identifying the weighted conformal approach"*

### Paper 2 (Deng et al., UNRELATED reference)

**Prediction:** Zero or negative delta (irrelevant reference = noise).
**Result: CONFIRMED.**

- Independent composite delta: **-0.00** avg (no effect)
- Pairwise impact: **2-4/7** (refs hurt or neutral on all 6 modes)
- All 6 modes favor no_refs output (Output B)
- Evaluator: *"Conformal prediction reference led completely away from
  the paper's core drifting field concept"*

### Conclusions

1. The v0.4 anti-leakage redesign successfully eliminated hint dominance —
   references now produce a measurable signal.
2. The negative control validates that the signal is genuine: unrelated
   references don't just fail to help, they actively distract.
3. The pairwise evaluator (v0.5) produces much sharper discrimination
   than independent scoring, which suffered from anchoring (all scores
   converging to novelty_alignment=2, reconstruction_difficulty=4).
