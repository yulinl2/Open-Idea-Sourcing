# Paper Idea Mindmap

## Core Problem
- How to construct prediction intervals for counterfactual outcomes in causal inference that account for the covariate shift between treatment groups while providing finite-sample coverage guarantees.

## Key Observations from References
- **From Ref 1 (Tibshirani et al.)**: Weighted conformal prediction can handle covariate shift when the likelihood ratio between test and training distributions is known, using importance weights to rebalance the empirical distribution of nonconformity scores
- **From Ref 2 (Kivaranovic et al.)**: Conformal methods can be extended to construct prediction intervals for individual treatment effects, but their approach doesn't explicitly address the covariate shift problem inherent in causal inference
- **From Ref 1**: The quantile lemma shows that exchangeability of nonconformity scores is sufficient for coverage guarantees - this suggests we need to restore exchangeability in the causal setting
- **From Ref 2**: Treatment assignment creates natural stratification that breaks standard exchangeability assumptions

## Proposed Approach
### Main Idea
- Recognize that predicting counterfactual outcomes is fundamentally a covariate shift problem: when predicting Y(0) for treated units, the "training" distribution is control units while the "test" distribution is treated units
- Use propensity score weights as the likelihood ratios in weighted conformal prediction to correct for this covariate shift

### Sub-ideas
- **Propensity Score Weighting for Conformal Inference**
  - For predicting Y(0) on treated units: use weights w(x) = (1-e(x))/e(x) where e(x) is propensity score
  - For predicting Y(1) on control units: use weights w(x) = e(x)/(1-e(x))
  - This creates the correct likelihood ratio between source (opposite treatment) and target (actual treatment) distributions

- **Dual Weighted Conformal Procedure**
  - Construct separate weighted conformal intervals for Y(0)|T=1 and Y(1)|T=0
  - Use control units as calibration set for Y(0) predictions, weighted by propensity ratios
  - Use treated units as calibration set for Y(1) predictions, weighted by inverse propensity ratios

- **Individual Treatment Effect Intervals**
  - Combine the two counterfactual prediction intervals: ITE ∈ [Ŷ(1) - U₀, Ŷ(1) - L₀] for treated units
  - Account for correlation structure between potential outcomes when constructing joint intervals

## Theoretical Grounding
- **Weighted exchangeability**: Propensity score weighting creates the weighted exchangeability condition needed for Tibshirani et al.'s framework
- **Covariate shift correction**: The propensity score ratio e(x)/(1-e(x)) is exactly the likelihood ratio dP(X|T=1)/dP(X|T=0) under unconfoundedness
- **Finite-sample guarantees**: Inherits the finite-sample coverage properties of weighted conformal prediction without requiring asymptotic approximations

## Potential Challenges
- **Propensity score estimation error**: When propensity scores are estimated rather than known, need to account for additional uncertainty
  - Address by using cross-fitting or sample splitting to separate propensity score estimation from conformal calibration
- **Overlap assumption**: Method requires sufficient overlap in covariate distributions between treatment groups
  - Address by detecting and handling regions of poor overlap, possibly with more conservative intervals
- **Strong unconfoundedness**: Assumes no unmeasured confounding
  - Address by conducting sensitivity analysis or bounds under violations of unconfoundedness

## Connections to Existing Work
- **Extends Tibshirani et al.**: Applies their weighted conformal framework to the specific covariate shift induced by treatment assignment, using propensity scores as the natural importance weights
- **Improves upon Kivaranovic et al.**: Their approach uses Bonferroni correction and doesn't account for covariate shift, leading to overly conservative intervals; our approach directly addresses the shift and should yield tighter intervals
- **Connects to doubly robust estimation**: Could potentially combine with outcome model weighting for additional robustness properties
- **Relates to recent CATE literature**: Provides uncertainty quantification for any CATE estimation method by treating it as the base predictor in the conformal framework