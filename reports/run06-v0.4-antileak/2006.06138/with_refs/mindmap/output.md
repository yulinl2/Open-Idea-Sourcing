# Reconstruction: mindmap
**Paper:** 2006.06138  
**Condition:** with_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Paper Idea Mindmap

## Core Problem
- Developing distribution-free uncertainty quantification for individual-level causal effects that accounts for both sampling variability and fundamental counterfactual uncertainty without requiring strong parametric assumptions.

## Key Observations from References
- Conformal prediction provides distribution-free prediction intervals with finite-sample guarantees under exchangeability (Ref: arxiv-1904.06019)
- Weighted conformal prediction can handle covariate shift when likelihood ratios are known, extending beyond exchangeable data (Ref: arxiv-1904.06019)
- The quantile lemma shows that exchangeable random variables naturally provide valid coverage guarantees through empirical quantiles (Ref: arxiv-1904.06019)
- Split conformal prediction offers computational efficiency while maintaining coverage guarantees (Ref: arxiv-1904.06019)

## Proposed Approach
### Main Idea
- Extend weighted conformal prediction to the causal inference setting by treating potential outcomes as missing data and using propensity score weighting to achieve a form of "causal exchangeability" for uncertainty quantification around individual treatment effects.

### Sub-ideas
- **Causal Conformal Framework**
  - Define nonconformity scores based on residuals from outcome models fitted on both treatment and control groups
  - Use inverse propensity weighting to rebalance the observed data to approximate the target population's covariate distribution
  
- **Doubly-Robust Score Construction**
  - Combine outcome regression residuals with propensity score adjustments: S((x,τ,y), Z) = |y - μ̂_τ(x)| / π̂_τ(x)^(τ) * (1-π̂_τ(x))^(1-τ)
  - This accounts for both outcome model misspecification and propensity model misspecification
  
- **Cross-Fitting for Honesty**
  - Use sample splitting to ensure the models used for score computation are independent of the data used for quantile estimation
  - Prevents overfitting bias in uncertainty estimates
  
- **Weighted Quantile Computation**
  - For individual i with covariates x_i, construct prediction intervals using weighted quantiles where weights reflect both propensity scores and covariate similarity
  - Handle both randomized experiments (known propensities) and observational studies (estimated propensities)

## Theoretical Grounding
- Builds on the weighted exchangeability result from conformal prediction under covariate shift
- Under unconfoundedness and overlap assumptions, the weighted nonconformity scores should behave as if exchangeable in the target population
- Finite-sample validity doesn't rely on asymptotic normality or model correctness, only on the validity of the causal identification assumptions
- The doubly-robust construction provides some protection against model misspecification

## Potential Challenges
- **Propensity Score Estimation Error**: Address by using cross-fitting and allowing for flexible propensity models, potentially with ensemble methods or machine learning
- **Overlap Violations**: Develop trimming strategies or modify weights when propensity scores are near 0 or 1, possibly using stabilized weights
- **Computational Complexity**: Implement efficient algorithms for weighted quantile computation and consider approximations for very large datasets
- **Multiple Comparisons**: When providing intervals for many individuals simultaneously, develop procedures that control family-wise error rates

## Connections to Existing Work
- **Extends Ref arxiv-1904.06019**: Applies the weighted conformal prediction framework to causal inference, where the "covariate shift" is between observed and counterfactual distributions
- **Novel Application Domain**: While conformal prediction has been applied to standard prediction problems, this represents a new application to causal inference where the fundamental challenge is missing counterfactual outcomes rather than distributional shift
- **Methodological Innovation**: The combination of doubly-robust estimation with conformal prediction creates a new framework that inherits robustness properties from both literatures
- **Practical Impact**: Addresses the critical gap in uncertainty quantification for individual treatment effects, which is essential for precision medicine and personalized policy applications
