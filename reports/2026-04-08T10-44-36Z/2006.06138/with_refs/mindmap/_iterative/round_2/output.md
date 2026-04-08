# Paper Idea Mindmap

## Core Problem
- How to construct reliable prediction intervals for individual treatment effects that provide valid uncertainty quantification in finite samples without strong parametric assumptions, addressing both subjects within and outside the study population.

## Key Observations from References
- Conformal prediction can provide finite-sample coverage guarantees without distributional assumptions (Ref arxiv-2006.01474)
- Individual treatment effects τ(X) = f(X,1) - f(X,-1) + e_{X,1} - e_{X,-1} include both systematic differences and error variability that cannot be directly observed
- Existing conformal approaches for ITEs require strong independence assumptions between potential outcome errors or Gaussian assumptions for shorter intervals
- The fundamental challenge is that we never observe both potential outcomes for any individual, making residual-based methods difficult

## Proposed Approach

### Main Idea
- Develop a **doubly-robust conformal framework** that leverages the distinction between subjects in the study (where one potential outcome is observed) versus new subjects (where both are missing), using weighted conformal prediction with propensity score adjustments and cross-fitting to handle model uncertainty.

### Sub-ideas

- **Asymmetric Conformal Construction**
  - For subjects in study: Use observed outcome + conformal interval for counterfactual outcome only
  - For new subjects: Use full conformal intervals for both potential outcomes with covariate shift correction
  - Justification: Reduces uncertainty by half for in-study subjects since one outcome is known

- **Weighted Conformal with Propensity Adjustment**
  - Weight conformal scores by inverse propensity scores to handle covariate shift between study and target populations
  - Use cross-fitted propensity score estimates to avoid overfitting
  - Justification: Ensures valid coverage when study population differs from target population

- **Doubly-Robust Residual Construction**
  - Combine outcome regression residuals with propensity-weighted inverse probability weighting
  - Use cross-fitting to split data for model fitting vs. conformal score computation
  - Justification: Provides robustness against misspecification of either outcome or propensity models

- **Adaptive Correlation Modeling**
  - Estimate correlation structure between potential outcome errors using sensitivity analysis bounds
  - Construct intervals that are valid across plausible correlation ranges rather than assuming independence
  - Justification: Avoids unrealistic independence assumptions while maintaining finite-sample validity

## Theoretical Grounding
- Weighted conformal prediction theory provides finite-sample coverage under covariate shift (recent work on distribution-free inference)
- Doubly-robust estimation theory ensures consistency when either outcome or propensity model is correct
- Cross-fitting techniques prevent overfitting bias in conformal score construction
- Sensitivity analysis bounds provide robustness to unmeasured confounding in correlation structure

## Potential Challenges

- **Computational Complexity with Cross-Fitting**
  - Challenge: Multiple model fits and conformal computations increase computational burden
  - Solution: Develop efficient algorithms using sample splitting and parallel computation, provide open-source implementation

- **Propensity Score Estimation in High Dimensions**
  - Challenge: Propensity scores may be difficult to estimate reliably with many covariates
  - Solution: Use regularized methods (e.g., LASSO) and provide diagnostic tools for propensity overlap assessment

- **Sensitivity to Correlation Assumptions**
  - Challenge: True correlation between potential outcome errors is unknowable
  - Solution: Provide sensitivity analysis framework and conservative bounds that work across reasonable correlation ranges

## Connections to Existing Work

- **Extends arxiv-2006.01474's approach** by removing strong independence assumptions and adding doubly-robust protection against model misspecification
- **Differs from standard CATE methods** by focusing on prediction intervals rather than point estimates, providing genuine uncertainty quantification rather than just confidence intervals for conditional expectations
- **Builds on weighted conformal prediction** literature but adapts it specifically to the causal inference setting with missing counterfactuals
- **Connects to doubly-robust causal inference** by bringing those robustness guarantees into the conformal prediction framework for the first time