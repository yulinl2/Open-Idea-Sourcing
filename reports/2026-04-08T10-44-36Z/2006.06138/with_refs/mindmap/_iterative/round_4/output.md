# Paper Idea Mindmap

## Core Problem
Develop finite-sample uncertainty quantification methods for individual treatment effects that handle covariate shift between treated/control populations and provide reliable prediction intervals without strong distributional assumptions.

## Key Observations from References
- Conformal prediction can provide finite-sample coverage guarantees without distributional assumptions (Ref arxiv-2006.01474)
- Individual treatment effects τ(X) = f(X,1) - f(X,-1) + e_{X,1} - e_{X,-1} involve unobserved counterfactuals
- Existing conformal methods for ITEs require T-conditional prediction intervals but don't address covariate shift
- Current approaches are conservative because they don't leverage the fact that one potential outcome is observed for in-study subjects

## Proposed Approach

### Main Idea
Develop **weighted conformal inference** for counterfactual prediction that combines inverse propensity weighting with conformal prediction to handle covariate shift while providing doubly robust uncertainty quantification.

### Sub-ideas

- **Weighted Conformal Scores for Observed Outcomes**
  - Use inverse propensity weights π(x)^{-1} to reweight conformal scores for the observed outcome Y
  - This corrects for selection bias when the treated population differs from target population
  - Maintains finite-sample coverage under covariate shift

- **Separate Inference for In-Study vs Out-of-Study Subjects**
  - For in-study subjects: Only need counterfactual inference for unobserved Y'
  - For out-of-study subjects: Need full joint inference for both potential outcomes
  - Use different weighting schemes and combination rules for each case

- **Doubly Robust Conformal Intervals**
  - Combine outcome regression residuals with propensity-weighted conformal scores
  - Valid when either outcome model OR propensity model is correctly specified
  - Use cross-fitting to avoid overfitting bias in finite samples

- **Adaptive Interval Combination**
  - Instead of fixed Bonferroni-style combination (level α/2 each), use data-adaptive combination
  - Weight intervals based on estimated correlation structure of errors e_{X,1} - e_{X,-1}
  - Shrink intervals when positive correlation is detected (common unobserved confounders)

## Theoretical Grounding
- Weighted conformal prediction theory shows coverage is maintained under covariate shift with proper weights
- Inverse propensity weighting has established theory for handling selection bias in causal inference
- Doubly robust estimation provides robustness when either outcome or treatment model is misspecified
- Conformal prediction's exchangeability requirements can be satisfied through appropriate reweighting

## Potential Challenges

- **Propensity Score Estimation in Finite Samples**
  - Challenge: Extreme propensity weights can destabilize inference
  - Solution: Use stabilized weights and cross-fitting with multiple folds to reduce variance

- **Maintaining Exchangeability Under Weighting**
  - Challenge: Weighted observations may not satisfy exchangeability assumptions
  - Solution: Develop theory for weighted exchangeable sequences and show coverage holds

- **Computational Complexity with Cross-Fitting**
  - Challenge: Multiple model fits required for doubly robust approach
  - Solution: Use efficient cross-fitting algorithms and parallel computation

## Connections to Existing Work

- **Extends arxiv-2006.01474 approach**
  - Their method assumes no covariate shift and uses conservative Bonferroni combination
  - Our approach handles covariate shift through weighting and uses adaptive combination
  - Maintains their finite-sample guarantees while improving efficiency

- **Builds on weighted conformal prediction literature**
  - Leverages recent advances in handling covariate shift in conformal inference
  - Adapts weighting schemes specifically for the causal inference setting with unobserved counterfactuals

- **Connects to doubly robust causal inference**
  - Brings robustness properties from average treatment effect estimation to individual-level uncertainty quantification
  - Uses similar cross-fitting strategies but adapted for prediction intervals rather than point estimation