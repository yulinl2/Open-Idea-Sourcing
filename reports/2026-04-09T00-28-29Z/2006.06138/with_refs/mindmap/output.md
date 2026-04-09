# Reconstruction: mindmap (iterative, 12 rounds)
**Paper:** 2006.06138  
**Condition:** with_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  
**Rounds:** 12  
**Best round:** 8 (score 4.4)  
**Converged:** True (reached max rounds (12))  
**Score trajectory:** 3.8 -> 3.8 -> 3.0 -> 4.2 -> 3.8 -> 3.8 -> 3.8 -> 4.4 -> 3.8 -> 3.8 -> 4.0 -> 4.0  

---

# Paper Idea Mindmap

## Core Problem
- Constructing finite-sample valid prediction intervals for counterfactual outcomes in causal inference by recognizing that treatment assignment creates covariate shift between treatment groups, which can be addressed using propensity score weighted conformal inference.

## Key Observations from References

- **From Tibshirani et al. (2020)**: Weighted conformal prediction can handle covariate shift when the likelihood ratio between test and training covariate distributions is known, providing distribution-free prediction intervals with finite-sample coverage guarantees.

- **From Kivaranovic et al. (2020)**: Standard conformal prediction can be extended to individual treatment effects, but their approach doesn't account for the fundamental covariate shift problem - they treat the challenge as needing conditional prediction intervals rather than addressing distributional differences.

- **Key insight**: In causal inference, when predicting Y(0) for treated units or Y(1) for control units, we face exactly the covariate shift scenario that weighted conformal prediction was designed to handle - the "training" data (observed outcomes) comes from a different covariate distribution than the "test" data (units for which we want counterfactual predictions).

## Proposed Approach

### Main Idea
- Use propensity score weighting in conformal prediction to construct valid prediction intervals for counterfactual outcomes, where the propensity score naturally provides the likelihood ratio needed for weighted conformal inference.

### Sub-ideas

- **Propensity Score as Likelihood Ratio**
  - For predicting Y(0) on treated units: use weight w(x) = (1-e(x))/e(x) where e(x) is propensity score
  - For predicting Y(1) on control units: use weight w(x) = e(x)/(1-e(x))
  - These weights correct for the covariate shift between treatment groups

- **Two-Stage Conformal Procedure**
  - Stage 1: Fit outcome models μ₀(x) and μ₁(x) on respective treatment groups
  - Stage 2: Apply weighted conformal prediction using propensity-weighted residuals from the opposite treatment group
  - Construct intervals: μₜ(x) ± weighted quantile of residuals from group (1-t)

- **Handling Unknown Propensity Scores**
  - When propensity scores are unknown, estimate them using the full dataset
  - Show that estimation error in propensity scores doesn't invalidate coverage guarantees under mild conditions
  - Provide finite-sample bounds on coverage degradation due to propensity score estimation

## Theoretical Grounding

- **Weighted Exchangeability**: Under the weighted conformal framework, propensity-weighted residuals from the opposite treatment group become exchangeable with the target residual, enabling valid inference.

- **Connection to Importance Sampling**: The propensity score weighting is performing importance sampling to reweight the source distribution (observed treatment group) to match the target distribution (counterfactual treatment group).

- **Robustness to Model Misspecification**: Coverage guarantees hold even when outcome models μ₀, μ₁ are misspecified, as long as propensity scores are correctly specified or well-estimated.

## Potential Challenges

- **Propensity Score Estimation Error**
  - Address by deriving finite-sample bounds showing coverage degradation is controlled when propensity scores are estimated consistently
  - Provide practical guidance on when estimated propensity scores are "good enough"

- **Extreme Propensity Scores**
  - When propensity scores are near 0 or 1, weights become extreme and intervals may be very wide
  - Propose trimming strategies or alternative weighting schemes for practical implementation
  - Show how this connects to overlap assumptions in causal inference

- **Computational Efficiency**
  - Weighted quantile computation can be expensive with large datasets
  - Develop efficient algorithms for weighted conformal prediction in the causal setting
  - Consider split conformal variants for computational tractability

## Connections to Existing Work

- **Extends Tibshirani et al. (2020)**: Applies their weighted conformal framework to the specific covariate shift problem arising in causal inference, with propensity scores providing the natural likelihood ratio.

- **Improves on Kivaranovic et al. (2020)**: Their approach ignores the covariate shift problem and uses overly conservative Bonferroni-type corrections. Our method directly addresses the distributional mismatch and should provide tighter intervals.

- **Bridges Causal Inference and Conformal Prediction**: Makes explicit the connection between propensity score methods (addressing covariate imbalance) and weighted conformal prediction (addressing covariate shift), showing they solve the same fundamental problem.

- **Novel Contribution**: First to recognize that counterfactual prediction is fundamentally a covariate shift problem that can be solved using existing weighted conformal methods with propensity score weighting.
