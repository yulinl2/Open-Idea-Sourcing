# Paper Idea Mindmap

## Core Problem
- How to provide reliable uncertainty quantification for individual-level treatment effects when only one potential outcome is observed per individual, distinguishing between inference for study participants versus new individuals.

## Key Observations from References
- Conformal prediction provides distribution-free coverage guarantees under exchangeability without modeling assumptions (Ref: arxiv-1904.06019)
- Weighted conformal prediction can handle covariate shift when likelihood ratios between distributions are known or estimable (Ref: arxiv-1904.06019)
- Split conformal methods offer computational efficiency by pre-fitting models on separate data (Ref: arxiv-1904.06019)
- Exchangeability can be relaxed to weighted exchangeability with appropriate modifications to conformal procedures (Ref: arxiv-1904.06019)

## Proposed Approach
### Main Idea
- Develop a "causal conformal prediction" framework that adapts conformal methods to the potential outcomes setting, using treatment assignment mechanisms to create appropriate exchangeability structures for uncertainty quantification

### Sub-ideas
- **Stratified Conformal for Randomized Experiments**
  - Within each treatment stratum, outcomes are exchangeable conditional on covariates
  - Use separate conformal procedures within treatment groups, then combine via weighted averaging based on propensity scores
  
- **Weighted Conformal for Observational Studies**  
  - Adapt covariate shift methodology where "shift" is from study population to target population
  - Weight training observations by inverse propensity scores to create pseudo-exchangeability
  - Use doubly robust score functions that incorporate both outcome and treatment models
  
- **Distinguishing Study vs. External Inference**
  - For study participants: Use leave-one-out conformal with the observed outcome as anchor
  - For new individuals: Use full conformal prediction treating both potential outcomes as missing
  - Provide separate coverage guarantees and interval constructions for each case
  
- **Doubly Robust Score Functions**
  - Define nonconformity scores as S((x,t,y), Z) = |y - μ̂(x,t)| / σ̂(x,t) where μ̂, σ̂ are doubly robust estimators
  - Ensures validity when either outcome model or propensity model is correctly specified
  - Incorporates treatment effect heterogeneity naturally through conditional mean modeling

## Theoretical Grounding
- Conformal prediction's finite-sample guarantees extend to causal settings when appropriate exchangeability structures are identified
- Stratification by treatment preserves exchangeability within strata for randomized experiments
- Inverse propensity weighting creates weighted exchangeability for observational studies, analogous to covariate shift correction
- Doubly robust estimators provide protection against model misspecification while maintaining the distribution-free nature

## Potential Challenges
- **Propensity Score Estimation Error**
  - Address through cross-fitting procedures that separate propensity estimation from conformal calibration
  - Provide theoretical analysis of how estimation error affects coverage guarantees
  
- **Finite Sample Performance with Sparse Strata**
  - Develop adaptive procedures that pool information across similar strata when sample sizes are small
  - Use regularized/smoothed versions of conformal quantiles in extreme cases
  
- **Computational Complexity**
  - Leverage split conformal methodology to avoid refitting models for each candidate interval
  - Develop efficient algorithms for weighted quantile computation in the causal setting

## Connections to Existing Work
- **Extends arxiv-1904.06019's covariate shift framework** by recognizing that causal inference involves a specific type of "shift" between treated/control populations and target populations of interest
- **Differs from standard CATE methods** by focusing on valid uncertainty quantification rather than just point estimation, providing finite-sample guarantees rather than asymptotic approximations
- **Builds on potential outcomes framework** but operationalizes it through conformal prediction's exchangeability-based approach rather than traditional parametric or semiparametric methods
- **Connects to stratified sampling literature** by treating randomized experiments as creating natural strata for conformal procedures