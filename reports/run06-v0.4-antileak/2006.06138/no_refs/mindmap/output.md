# Reconstruction: mindmap
**Paper:** 2006.06138  
**Condition:** no_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Paper Idea Mindmap

## Core Problem
- How to provide reliable uncertainty quantification for individual-level treatment effects when we can only observe one potential outcome per unit, especially in finite samples with possible model misspecification.

## Key Observations from Field Knowledge
- Conformal prediction provides distribution-free uncertainty quantification without strong parametric assumptions
- Cross-fitting techniques can help reduce overfitting bias in causal inference with machine learning
- Potential outcomes framework creates fundamental identifiability challenges for individual-level effects
- Existing methods either assume correct model specification or rely on asymptotic properties that may not hold in practice
- Uncertainty in heterogeneous treatment effects comes from multiple sources: sampling variability, model uncertainty, and inherent response variability

## Proposed Approach
### Main Idea
- Develop a conformal prediction framework specifically adapted for individual treatment effect estimation that provides valid prediction intervals without requiring correct model specification

### Sub-ideas
- **Counterfactual Conformal Prediction**
  - Adapt conformal prediction to handle missing counterfactuals by using cross-fitting to estimate both potential outcomes
  - Create separate conformity scores for treated and control outcomes, then combine them appropriately
  
- **Doubly-Robust Conformal Intervals**
  - Integrate doubly-robust estimation (combining outcome regression and propensity score methods) with conformal prediction
  - Provides protection against misspecification in either the outcome model or propensity score model
  
- **Multi-Source Uncertainty Decomposition**
  - Explicitly separate uncertainty from sampling variability versus inherent response heterogeneity
  - Use nested conformal procedures to quantify different uncertainty sources
  
- **Adaptive Coverage for Subgroups**
  - Develop locally adaptive conformal methods that provide valid coverage even when treatment effects vary dramatically across covariate space
  - Use weighted conformal prediction with importance weights based on covariate similarity

## Theoretical Grounding
- Conformal prediction provides finite-sample coverage guarantees under minimal assumptions (exchangeability)
- Cross-fitting ensures that conformity scores are computed on independent data, maintaining validity
- Doubly-robust estimation provides consistency under weaker assumptions than either component alone
- Importance weighting in conformal prediction can maintain marginal coverage while improving conditional coverage

## Potential Challenges
- **Exchangeability assumption may be violated**
  - Address through stratified conformal prediction or by developing theory for weakly dependent data
  - Use robust conformal methods that provide approximate coverage under mild violations
  
- **Computational complexity with high-dimensional covariates**
  - Develop efficient algorithms using modern optimization techniques
  - Consider dimensionality reduction while preserving conformal validity
  
- **Combining uncertainty from multiple sources**
  - Carefully calibrate how to aggregate conformity scores from different potential outcome models
  - Ensure that combined intervals maintain nominal coverage rates

## Connections to Existing Work
- **Extends classical conformal prediction** by adapting it to the causal inference setting where some outcomes are fundamentally unobservable
- **Builds on doubly-robust causal inference** by adding rigorous uncertainty quantification without relying on asymptotic normality
- **Complements recent work on honest causal forests** by providing an alternative approach that doesn't require tree-based methods and works with any base learner
- **Differs from Bayesian approaches** by providing frequentist guarantees without requiring prior specification or MCMC computation
- **Advances beyond standard bootstrap methods** by providing coverage guarantees even under model misspecification
