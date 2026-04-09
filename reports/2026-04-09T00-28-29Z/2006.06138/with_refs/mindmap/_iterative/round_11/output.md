# Paper Idea Mindmap

## Core Problem
- How to construct finite-sample valid prediction intervals for counterfactual outcomes in causal inference by recognizing that treatment assignment creates a covariate shift problem that can be addressed through propensity score weighted conformal inference.

## Key Observations from References
- Weighted conformal prediction (Tibshirani et al.) handles covariate shift by reweighting nonconformity scores using likelihood ratios between training and test distributions
- Standard conformal prediction provides finite-sample coverage guarantees under exchangeability assumptions
- Individual treatment effect inference (Kivaranovic et al.) requires handling unobserved counterfactual outcomes
- The fundamental challenge in causal inference is that treated and control units have different covariate distributions - exactly the covariate shift problem weighted conformal inference was designed to solve

## Proposed Approach
### Main Idea
- Leverage propensity scores as the likelihood ratio weights in weighted conformal prediction to construct valid prediction intervals for counterfactual outcomes, recognizing that propensity scores naturally quantify the covariate shift induced by treatment assignment.

### Sub-ideas
- **Propensity Score as Likelihood Ratio**: Use w(x) = π(x)/(1-π(x)) when predicting Y(0) for treated units, and w(x) = (1-π(x))/π(x) when predicting Y(1) for control units
  - This directly addresses the covariate shift between source (e.g., treated units) and target (control distribution) when constructing counterfactual intervals
- **Split Conformal for Efficiency**: Employ split conformal prediction to avoid refitting outcome models for each potential outcome value
  - Pre-fit outcome models μ₀(x) and μ₁(x) on separate data, then use residuals for conformal calibration
- **Doubly Robust Extension**: Combine with outcome regression to achieve robustness when either propensity score or outcome model is correctly specified
  - Use pseudo-outcomes based on doubly robust estimators as the basis for nonconformity scores

## Theoretical Grounding
- Weighted conformal prediction (Corollary 1 from Tibshirani et al.) guarantees coverage when likelihood ratios are known or well-estimated
- Propensity scores provide exactly these likelihood ratios for the covariate shift induced by treatment assignment
- The weighted exchangeability condition is satisfied when propensity scores are correctly specified, enabling finite-sample validity
- Coverage holds even with outcome model misspecification, provided propensity scores are accurate

## Potential Challenges
- **Propensity Score Estimation Error**: Address through cross-fitting/sample splitting to avoid overfitting bias, similar to doubly robust methods
  - Use separate samples for propensity score estimation and conformal calibration
- **Extreme Propensity Scores**: Handle near-zero propensity scores through trimming or stabilization
  - Develop adaptive procedures that adjust coverage level based on propensity score overlap
- **High-Dimensional Covariates**: Extend to settings where flexible machine learning is needed for both propensity and outcome models
  - Investigate whether Neyman orthogonality conditions can preserve validity

## Connections to Existing Work
- **Extends Tibshirani et al.**: Applies weighted conformal prediction to a new domain (causal inference) where the covariate shift has natural causal interpretation
- **Complements Kivaranovic et al.**: Provides a more direct approach to counterfactual uncertainty quantification without requiring separate treatment-conditional intervals
- **Differs from standard causal inference**: Moves beyond point estimation and asymptotic confidence intervals to provide finite-sample prediction intervals that account for both estimation uncertainty and irreducible outcome variability
- **Connects to doubly robust literature**: Inherits robustness properties when combined with flexible outcome modeling, but provides distribution-free coverage guarantees