# Paper Idea Mindmap

## Core Problem
- How to provide reliable uncertainty quantification for individual treatment effects when covariate distributions differ systematically between treated and control groups, leveraging the known structure of treatment assignment mechanisms.

## Key Observations from References
- Conformal prediction provides distribution-free coverage guarantees under exchangeability assumptions (Ref: arxiv-1904.06019)
- Weighted conformal prediction can handle covariate shift when likelihood ratios between source/target distributions are known or estimable (Ref: arxiv-1904.06019)
- The key insight is reweighting nonconformity scores by likelihood ratios to restore exchangeability-like properties
- Coverage guarantees hold even when the weighting mechanism is imperfect, provided it captures the essential distributional differences

## Proposed Approach

### Main Idea
- Develop **Causal Conformal Prediction** that treats treatment assignment as creating structured covariate shift between potential outcome inference problems, using propensity scores as natural likelihood ratios for reweighting.

### Sub-ideas

- **Structured Covariate Shift Recognition**
  - When inferring Y(0) for treated units, we're doing covariate shift from control to treated population
  - When inferring Y(1) for control units, we're doing covariate shift from treated to control population
  - The propensity score e(x) = P(T=1|X=x) provides the natural likelihood ratio: treated→control uses e(x)/(1-e(x)), control→treated uses (1-e(x))/e(x)

- **Dual Weighted Conformal Construction**
  - For treated unit i, construct conformal interval for Y_i(0) using control units weighted by (1-e(X_j))/e(X_i)
  - For control unit i, construct conformal interval for Y_i(1) using treated units weighted by e(X_j)/(1-e(X_i))
  - Individual treatment effect interval: [Y_i(1) - upper_Y_i(0), Y_i(1) - lower_Y_i(0)] for treated, [upper_Y_i(1) - Y_i(0), lower_Y_i(1) - Y_i(0)] for control

- **Randomization-Aware Guarantees**
  - In randomized experiments, propensity scores are known exactly, providing stronger theoretical guarantees
  - In observational studies, use estimated propensity scores with robustness properties
  - Develop "doubly robust" version: valid if either outcome model or propensity model is correct

- **Nonconformity Score Design**
  - Use residuals from outcome regression models: |Y - μ̂_t(X)| where μ̂_t is fitted on treatment group t
  - Alternative: Use nearest-neighbor distances in covariate space to capture local treatment effect variation
  - Adaptive scoring: Let nonconformity depend on estimated treatment effect heterogeneity

## Theoretical Grounding
- Weighted conformal prediction theory guarantees coverage when likelihood ratios correctly capture distributional differences
- Treatment assignment creates precisely the covariate shift structure that weighted conformal can handle
- Propensity scores are the natural likelihood ratios for this specific covariate shift problem
- In randomized trials, exact propensity scores provide exact finite-sample guarantees without asymptotic approximations

## Potential Challenges

- **Propensity Score Estimation**
  - Challenge: Estimated propensity scores introduce additional uncertainty
  - Solution: Develop theory showing robustness to propensity score misspecification, potentially using techniques from doubly robust estimation

- **Extreme Propensity Scores**
  - Challenge: Very high/low propensity scores create unstable weights
  - Solution: Implement principled trimming or stabilization, with theory showing how this affects coverage guarantees

- **High-Dimensional Covariates**
  - Challenge: Curse of dimensionality affects both propensity estimation and nearest-neighbor-based nonconformity scores
  - Solution: Develop dimension reduction techniques preserving the covariate shift structure, or use model-based nonconformity scores

## Connections to Existing Work

- **Extends arxiv-1904.06019's approach**
  - Takes their weighted conformal framework and applies it to the specific structure of causal inference
  - Uses propensity scores as the natural likelihood ratios they require
  - Leverages their theoretical guarantees but in a new domain with additional structure

- **Differs from standard causal inference uncertainty quantification**
  - Most existing work relies on asymptotic normality assumptions or bootstrap methods
  - Our approach provides finite-sample guarantees without distributional assumptions
  - Handles the systematic covariate differences that standard approaches often ignore

- **Novel contribution to conformal prediction literature**
  - First application to causal inference problems
  - Exploits known treatment assignment mechanism structure
  - Provides framework for heterogeneous treatment effect uncertainty that's both practical and theoretically grounded