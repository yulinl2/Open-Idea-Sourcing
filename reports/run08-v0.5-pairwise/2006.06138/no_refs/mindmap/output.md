# Reconstruction: mindmap
**Paper:** 2006.06138  
**Condition:** no_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Paper Idea Mindmap

## Core Problem
- Develop distribution-free methods for constructing prediction intervals around individual treatment effects that provide valid coverage guarantees without strong parametric assumptions.

## Key Observations from Field Knowledge
- Conformal prediction provides distribution-free coverage guarantees for prediction intervals in standard supervised learning settings
- Split conformal methods can handle covariate shift and model misspecification robustly
- Causal inference literature has established doubly robust methods for point estimation of treatment effects
- Quantile regression and conditional quantile estimation can capture heterogeneity in treatment effects
- Cross-fitting techniques help reduce overfitting bias when using machine learning for causal inference

## Proposed Approach

### Main Idea
- Combine conformal prediction with doubly robust causal inference to create "causal conformal intervals" that provide valid coverage for individual treatment effects under minimal assumptions

### Sub-ideas
- **Doubly Robust Conformal Score Construction**
  - Use AIPW (Augmented Inverse Propensity Weighting) estimators to create pseudo-outcomes for treatment effects
  - Apply conformal prediction to these pseudo-outcomes to get prediction intervals
  - Leverage double robustness to handle model misspecification in either outcome or propensity models

- **Two-Stage Conformal Procedure**
  - Stage 1: Estimate nuisance functions (outcome regression, propensity scores) using cross-fitting
  - Stage 2: Apply weighted conformal prediction where weights account for propensity score uncertainty
  - This separates the causal identification problem from the uncertainty quantification problem

- **Covariate Shift Adaptation**
  - Extend weighted conformal prediction to handle distribution shifts between study and target populations
  - Use importance weighting based on covariate distributions to maintain coverage under shift
  - Combine with doubly robust estimation to be robust to both covariate shift and model misspecification

- **Conditional Coverage Enhancement**
  - Develop locally weighted conformal scores that provide better conditional coverage
  - Use kernel smoothing or nearest neighbor approaches to focus on similar individuals
  - Balance between local validity and statistical power

## Theoretical Grounding
- Conformal prediction theory guarantees marginal coverage under exchangeability assumptions
- Doubly robust estimation provides √n-consistent estimation under weaker conditions than either component alone
- Weighted conformal methods maintain coverage under covariate shift when importance weights are known
- Cross-fitting prevents overfitting bias that could invalidate coverage guarantees

## Potential Challenges

- **Exchangeability Under Treatment Assignment**
  - Challenge: Standard conformal prediction assumes exchangeable data, but treatment assignment creates dependence
  - Solution: Condition on treatment assignment and apply conformal prediction separately within treatment groups, then combine using causal estimands

- **Finite Sample Coverage with High-Dimensional Covariates**
  - Challenge: Coverage guarantees may deteriorate with many covariates and limited sample size
  - Solution: Use regularized estimation for nuisance functions and develop finite-sample corrections for conformal scores

- **Computational Scalability**
  - Challenge: Cross-fitting and conformal prediction both require multiple model fits
  - Solution: Develop efficient algorithms using pre-computed base learners and parallelization

- **Unmeasured Confounding in Observational Studies**
  - Challenge: Causal identification assumptions may be violated
  - Solution: Develop sensitivity analysis framework showing how coverage changes under violations of unconfoundedness

## Connections to Existing Work

- **Extends Conformal Prediction Literature**
  - Builds on Vovk et al.'s foundational work by adapting conformal methods to causal inference settings
  - Generalizes weighted conformal prediction (Tibshirani et al.) to handle treatment effect heterogeneity

- **Advances Causal ML Uncertainty Quantification**
  - Complements recent work on Bayesian approaches to CATE uncertainty by providing frequentist guarantees
  - Differs from bootstrap-based approaches by providing exact finite-sample coverage without distributional assumptions

- **Integrates with Doubly Robust Causal Inference**
  - Leverages established theory from Robins, Rotnitzky, and others on efficient influence functions
  - Extends recent work on cross-fitting in causal inference (Chernozhukov et al.) to uncertainty quantification

- **Novel Contribution to Distribution-Free Inference**
  - First to combine conformal prediction with causal inference in a principled way
  - Addresses gap between point estimation methods (well-developed) and uncertainty quantification (limited) in causal ML
