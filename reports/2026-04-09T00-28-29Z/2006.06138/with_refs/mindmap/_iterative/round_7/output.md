# Paper Idea Mindmap

## Core Problem
- Develop conformal prediction intervals for individual treatment effects that handle the covariate shift between treated and control populations while providing finite-sample coverage guarantees.

## Key Observations from References
- Weighted conformal prediction can handle covariate shift when likelihood ratios between source and target distributions are known (Tibshirani et al.)
- Conformal prediction for individual treatment effects is possible but current methods don't account for covariate shift between treatment groups (Kivaranovic et al.)
- In causal inference, treatment assignment creates systematic differences in covariate distributions - this is precisely a covariate shift problem
- Propensity scores quantify the likelihood of treatment assignment given covariates, providing natural weights for addressing this shift

## Proposed Approach

### Main Idea
- Combine propensity score weighting with conformal prediction to construct valid prediction intervals for counterfactual outcomes, leveraging the fact that propensity scores naturally address the covariate shift inherent in causal inference problems.

### Sub-ideas

- **Propensity-Weighted Conformal Intervals**
  - Use propensity scores π(x) = P(T=1|X=x) to define likelihood ratios w(x) = π(x)/(1-π(x)) for treated→control shift, and 1/w(x) for control→treated shift
  - Apply weighted conformal prediction where weights correct for the distribution mismatch when predicting counterfactual outcomes

- **Doubly Robust Construction**
  - Construct separate conformal intervals for Y(0) and Y(1) using propensity-weighted nonconformity scores
  - Combine intervals to get prediction intervals for individual treatment effects τ(x) = Y(1) - Y(0)
  - Maintains validity even if outcome models are misspecified, provided propensity scores are well-estimated

- **Split Conformal Variant**
  - Use sample splitting: fit outcome models on one split, estimate propensity scores on another, compute weighted conformal intervals on third split
  - Computationally efficient and avoids overfitting issues from using same data for model fitting and interval construction

- **Adaptive Weighting**
  - For units with extreme propensity scores, use truncated weights to avoid instability
  - Develop theory showing how truncation affects coverage guarantees

## Theoretical Grounding
- Weighted conformal prediction provides exact finite-sample coverage when weights equal likelihood ratios between distributions
- Propensity scores provide exactly these likelihood ratios for the covariate shift between treatment groups
- The fundamental problem of causal inference (never observing both potential outcomes) is addressed by treating it as a covariate shift problem where we predict from one population to another

## Potential Challenges

- **Propensity Score Estimation Error**
  - Address by developing theory for approximate weights when propensity scores are estimated rather than known
  - Show that consistent propensity score estimation preserves asymptotic coverage
  - Provide finite-sample bounds on coverage degradation

- **Extreme Propensity Scores**
  - Handle via weight truncation or trimming procedures
  - Develop adaptive methods that balance coverage guarantees with interval width
  - Study trade-offs between exact coverage and practical utility

- **Computational Complexity**
  - For full conformal prediction, need to recompute intervals for each possible outcome value
  - Mitigate through split conformal variants and efficient implementations
  - Develop approximation methods for very large datasets

## Connections to Existing Work

- **Extends Tibshirani et al.'s weighted conformal prediction**
  - Their method requires known likelihood ratios; we show propensity scores provide these ratios naturally in causal settings
  - Their framework handles general covariate shift; we specialize to the treatment assignment mechanism

- **Advances beyond Kivaranovic et al.'s approach**
  - Their method doesn't account for covariate shift between treatment groups
  - Our approach recognizes that this shift is fundamental to the causal inference problem
  - We provide more efficient intervals by properly weighting rather than using conservative union bounds

- **Connects to broader causal inference literature**
  - Links conformal prediction to established causal inference tools (propensity scores)
  - Provides distribution-free alternative to parametric approaches for uncertainty quantification
  - Bridges machine learning (conformal prediction) and causal inference communities