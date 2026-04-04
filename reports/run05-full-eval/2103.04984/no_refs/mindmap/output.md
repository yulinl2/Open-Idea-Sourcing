# Reconstruction: mindmap
**Paper:** 2103.04984  
**Condition:** no_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Paper Idea Mindmap

## Core Problem
- Develop prediction intervals for individual treatment effects that guarantee finite-sample marginal coverage without strong modeling assumptions, handling both within-study counterfactual inference and out-of-study generalization.

## Key Observations from Field Knowledge
- Conformal prediction provides distribution-free finite-sample coverage guarantees for prediction intervals
- Doubly robust estimators can handle misspecification in either propensity scores or outcome models
- Cross-fitting/sample splitting prevents overfitting when using machine learning for nuisance parameters
- Weighted conformal prediction can handle covariate shift between training and test distributions
- CATE estimation suffers from fundamental identifiability issues that standard uncertainty quantification doesn't address

## Proposed Approach
### Main Idea
- Combine doubly robust CATE estimation with weighted conformal prediction, using cross-fitting to enable machine learning while preserving coverage guarantees for both observed and counterfactual outcomes.

### Sub-ideas
- **Doubly Robust Conformal Framework**
  - Use AIPW (Augmented Inverse Propensity Weighting) scores as the base for conformal prediction
  - Ensures robustness to misspecification in either propensity or outcome models
  
- **Cross-Fitted Conformal Residuals**
  - Split data into folds for nuisance parameter estimation and conformal score computation
  - Prevents data snooping that could invalidate coverage guarantees
  
- **Treatment-Aware Conformity Scores**
  - Design conformity scores that account for the observed treatment assignment
  - For subject i with treatment Ti, use residual |Yi - μ̂(Xi, Ti)| weighted by propensity score
  
- **Counterfactual Interval Construction**
  - For unobserved potential outcome, use AIPW-based imputation plus conformal adjustment
  - Combine uncertainty from both outcome prediction and treatment effect estimation
  
- **Covariate Shift Handling**
  - Use importance weights based on covariate density ratios between study and target populations
  - Apply weighted conformal prediction with these importance weights

## Theoretical Grounding
- Conformal prediction theory guarantees marginal coverage under exchangeability assumptions
- Doubly robust estimation provides √n-consistent CATE estimates under weak conditions
- Cross-fitting enables use of flexible ML methods while preserving asymptotic properties
- Weighted conformal prediction maintains coverage under covariate shift with known density ratios
- AIPW scores have favorable bias properties that should translate to better conformal intervals

## Potential Challenges
- **Exchangeability Violations in Observational Data**
  - Address through careful covariate adjustment and sensitivity analysis
  - Develop diagnostic tools to detect when assumptions are violated
  
- **Computational Complexity with Large Datasets**
  - Implement efficient algorithms for cross-fitting and conformal score computation
  - Use approximate methods for density ratio estimation when exact computation is infeasible
  
- **Unknown Covariate Shift**
  - Develop methods to estimate density ratios from data
  - Provide robust intervals that account for uncertainty in shift estimation
  
- **Multiple Treatment Arms**
  - Extend framework to handle multi-valued treatments
  - Address increased complexity in counterfactual inference

## Connections to Existing Work
- **Extends standard conformal prediction** by handling the missing counterfactual problem specific to causal inference
- **Builds on doubly robust literature** by adding finite-sample uncertainty quantification to existing point estimators
- **Improves upon existing CATE uncertainty methods** by providing distribution-free coverage guarantees rather than asymptotic approximations
- **Connects to covariate shift literature** by using importance weighting techniques within the conformal framework
- **Differs from Bayesian approaches** by avoiding strong parametric assumptions while still providing meaningful uncertainty quantification
