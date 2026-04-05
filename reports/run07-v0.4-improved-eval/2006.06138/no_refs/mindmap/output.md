# Reconstruction: mindmap
**Paper:** 2006.06138  
**Condition:** no_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Paper Idea Mindmap

## Core Problem
- How to construct reliable prediction intervals for individual-level treatment effects that provide finite-sample coverage guarantees without strong parametric assumptions.

## Key Observations from Field Knowledge
- Conformal prediction provides distribution-free finite-sample coverage guarantees for prediction intervals
- Cross-fitting techniques can help reduce bias when using machine learning methods for causal inference
- The fundamental problem of causal inference means we never observe both potential outcomes for the same individual
- Existing uncertainty quantification for CATE relies heavily on asymptotic normality assumptions that may fail
- Doubly robust estimators can provide protection against misspecification of either propensity score or outcome models

## Proposed Approach
### Main Idea
- Develop a conformal prediction framework specifically adapted for individual treatment effect estimation that leverages cross-fitting and creates "pseudo-outcomes" to enable valid uncertainty quantification

### Sub-ideas
- **Conformal CATE Framework**
  - Adapt conformal prediction to work with unobserved counterfactuals by using doubly robust score functions as conformity scores
  - Use cross-fitting to avoid overfitting bias when estimating nuisance functions (propensity scores, outcome models)

- **Pseudo-Outcome Construction**
  - Create synthetic treatment effect observations using doubly robust estimators across different folds
  - These pseudo-outcomes serve as the basis for computing conformity scores in a way that respects the causal structure

- **Covariate Shift Robustness**
  - Incorporate importance weighting into the conformal procedure to handle distribution shift between training and target populations
  - Use weighted conformity scores that account for differences in covariate distributions

- **Multi-Fold Cross-Conformal Approach**
  - Combine cross-fitting for nuisance parameter estimation with cross-conformal prediction
  - Use different data splits for training base learners and calibrating prediction intervals

## Theoretical Grounding
- Conformal prediction theory guarantees marginal coverage under exchangeability assumptions
- Doubly robust theory ensures consistency if either propensity score or outcome model is correctly specified
- Cross-fitting theory shows how sample splitting can eliminate bias from overfitting in high-dimensional settings
- The combination should inherit robustness properties from doubly robust estimation while gaining finite-sample coverage guarantees from conformal prediction

## Potential Challenges
- **Exchangeability Assumption**
  - The standard conformal assumption may be violated in observational studies with unmeasured confounding
  - Address by: Sensitivity analysis framework showing how coverage degrades with violations, or conditional conformal approaches

- **Computational Complexity**
  - Multiple layers of cross-fitting and conformal calibration could be computationally expensive
  - Address by: Efficient implementation using pre-computed fold predictions and parallelization

- **Coverage vs. Efficiency Trade-off**
  - Conformal intervals might be wider than necessary, especially with complex base learners
  - Address by: Adaptive conformity scores that use auxiliary information about prediction quality

- **Negative Treatment Effects**
  - Standard conformal methods assume exchangeable residuals, but treatment effects can have different signs
  - Address by: Separate calibration for positive and negative predicted effects, or quantile-based conformity scores

## Connections to Existing Work
- **Extends conformal prediction literature** by adapting it to the causal inference setting where true outcomes are never fully observed
- **Builds on doubly robust causal inference** by adding principled uncertainty quantification without relying on asymptotic approximations
- **Connects to cross-fitting methodology** by showing how sample splitting can be combined with conformal calibration for causal quantities
- **Relates to meta-learning approaches** for CATE estimation by providing a model-agnostic uncertainty quantification layer that can wrap around any base CATE estimator
- **Differs from bootstrap-based approaches** by providing exact finite-sample guarantees rather than asymptotic approximations
- **Complements Bayesian approaches** by offering frequentist coverage guarantees without requiring prior specification or MCMC computation
