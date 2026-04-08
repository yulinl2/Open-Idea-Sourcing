# Reconstruction: mindmap
**Paper:** 2006.06138  
**Condition:** with_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Paper Idea Mindmap

## Core Problem
- Construct distribution-free prediction intervals for individual treatment effects that provide valid uncertainty quantification under covariate shift between study and target populations.

## Key Observations from References
- Conformal prediction provides distribution-free coverage guarantees under exchangeability (Ref: Tibshirani et al.)
- Weighted conformal prediction can handle covariate shift when likelihood ratios are known/estimable (Ref: Tibshirani et al.)
- Split conformal is computationally efficient and maintains coverage when base model is pre-fitted (Ref: Tibshirani et al.)
- The quantile lemma enables finite-sample guarantees without parametric assumptions (Ref: Tibshirani et al.)

## Proposed Approach
### Main Idea
- Extend weighted conformal prediction to individual treatment effect estimation by treating potential outcomes as missing data and using importance weighting to handle both covariate shift and treatment assignment mechanisms.

### Sub-ideas
- **Dual Conformal Framework for ITEs**
  - Construct separate conformal predictors for treated and control potential outcomes
  - Combine via difference to get ITE intervals with proper uncertainty propagation
  - Handle the fundamental problem of causal inference (only one outcome observed per unit)

- **Weighted Exchangeability for Causal Settings**
  - Extend the weighted exchangeability concept to account for treatment propensity scores
  - Use doubly-robust weighting: w(x) = (dP_target/dP_study)(x) × (propensity adjustment)
  - Ensures valid coverage under both covariate shift and confounding

- **Split Conformal for Computational Efficiency**
  - Pre-fit CATE estimators (e.g., T-learner, X-learner) on auxiliary data
  - Use residuals from these estimators as conformity scores
  - Avoids refitting complex ML models for each candidate ITE value

- **Adaptive Weighting Scheme**
  - Estimate covariate shift weights using density ratio estimation on unlabeled target data
  - Incorporate uncertainty in weight estimation into final intervals
  - Robust to weight estimation errors through conservative adjustment

## Theoretical Grounding
- Weighted conformal prediction theory guarantees coverage under known likelihood ratios
- The exchangeability assumption can be relaxed to weighted exchangeability in causal settings
- Potential outcomes framework provides principled foundation for defining individual treatment effects
- Doubly-robust estimation theory ensures robustness to either outcome model or propensity model misspecification

## Potential Challenges
- **Weight Estimation Accuracy**
  - Challenge: Density ratio estimation can be unstable, especially in high dimensions
  - Solution: Use ensemble methods for weight estimation + conservative coverage adjustment based on weight uncertainty bounds

- **Overlap and Positivity Violations**
  - Challenge: Some target population regions may have no training data support
  - Solution: Detect low-overlap regions using weight magnitudes; provide warnings or exclude from inference

- **Computational Scalability**
  - Challenge: Need to compute quantiles over weighted distributions repeatedly
  - Solution: Pre-compute weighted empirical CDFs; use efficient quantile algorithms for weighted samples

## Connections to Existing Work
- **Builds directly on Tibshirani et al.'s weighted conformal framework**
  - Extends their covariate shift methodology to the causal inference setting
  - Adapts their split conformal approach for computational efficiency with CATE estimators
  - Uses their weighted exchangeability concept but adds treatment assignment mechanism

- **Differs from standard CATE uncertainty quantification approaches**
  - Most existing methods rely on asymptotic normality or bootstrap
  - Our approach provides finite-sample, distribution-free guarantees
  - Handles covariate shift explicitly rather than assuming identical populations

- **Novel contribution: Dual potential outcomes conformal prediction**
  - No existing work applies conformal prediction specifically to individual treatment effects
  - Addresses the unique challenge of missing counterfactuals through careful score construction
  - Provides principled way to combine uncertainty from both potential outcome predictions
