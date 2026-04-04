# Reconstruction: mindmap
**Paper:** 2103.04984  
**Condition:** no_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Paper Idea Mindmap

## Core Problem
- Develop prediction intervals for individual treatment effects that guarantee finite-sample marginal coverage without strong modeling assumptions, handling both in-study and out-of-study inference under potential covariate shift.

## Key Observations from References
- Conformal prediction provides distribution-free coverage guarantees but typically assumes exchangeability between calibration and test data
- Doubly robust methods in causal inference maintain consistency when either propensity score or outcome model is correctly specified
- Weighted conformal prediction can handle covariate shift by reweighting calibration data to match test distribution
- Cross-fitting techniques reduce overfitting bias when using flexible machine learning methods for nuisance parameter estimation
- The missing data structure in causal inference (only one potential outcome observed per unit) creates unique challenges for uncertainty quantification

## Proposed Approach

### Main Idea
- Combine doubly robust estimation with weighted conformal prediction, using cross-fitting to create "pseudo-outcomes" for the unobserved counterfactuals, then apply conformal prediction to these augmented data with appropriate weights for different inferential targets.

### Sub-ideas

- **Doubly Robust Pseudo-Outcome Construction**
  - Use cross-fitted nuisance functions (propensity scores and outcome models) to impute missing counterfactuals
  - Create augmented dataset where each unit has both potential outcomes (one observed, one imputed)
  - Leverage AIPW-style corrections to maintain double robustness property

- **Weighted Conformal Calibration**
  - Apply different weighting schemes for different inferential targets:
    - Equal weights for ATE-type inference
    - Propensity score weights for ATT-type inference  
    - Inverse propensity weights for ATC-type inference
  - Use importance weights for covariate shift between study and target populations

- **Cross-Fitting Integration**
  - Split data into folds for cross-fitting nuisance functions
  - Use separate fold for conformal calibration to avoid overfitting
  - Aggregate prediction intervals across folds using appropriate combination rules

- **Adaptive Coverage Adjustment**
  - Develop theory for how conformal coverage translates when applied to pseudo-outcomes
  - Adjust nominal coverage level to account for imputation uncertainty
  - Provide finite-sample coverage guarantees under minimal assumptions

## Theoretical Grounding
- Conformal prediction theory guarantees marginal coverage under exchangeability, which can be relaxed using importance weighting
- Doubly robust estimation provides √n-consistent treatment effect estimates under weak conditions
- Cross-fitting eliminates bias from using same data for model fitting and inference
- Weighted conformal methods have been shown to maintain coverage under covariate shift in supervised learning settings

## Potential Challenges

- **Imputation Uncertainty Propagation**
  - Challenge: Conformal intervals on pseudo-outcomes may not reflect true counterfactual uncertainty
  - Solution: Develop theory for coverage correction based on nuisance function estimation error, potentially using bootstrap or influence function approaches

- **Weight Estimation and Stability**
  - Challenge: Importance weights for covariate shift may be unstable with extreme values
  - Solution: Use stabilized weights with trimming/truncation, develop robust weight estimation procedures

- **Computational Complexity**
  - Challenge: Cross-fitting plus conformal calibration creates significant computational burden
  - Solution: Develop efficient algorithms, possibly using approximate conformal methods or parallel processing

- **Assumption Verification**
  - Challenge: Method relies on unconfoundedness and overlap assumptions that cannot be tested
  - Solution: Provide sensitivity analysis tools and robustness checks for assumption violations

## Connections to Existing Work

- **Extends conformal prediction literature** by handling the missing data structure inherent in causal inference and providing coverage for treatment effects rather than just outcomes

- **Builds on doubly robust causal inference** by adding finite-sample uncertainty quantification while preserving the robustness properties of AIPW estimation

- **Generalizes weighted conformal methods** from supervised learning to causal inference settings with multiple inferential targets and complex weighting schemes

- **Differs from existing CATE uncertainty methods** by providing distribution-free guarantees rather than relying on asymptotic normality or specific model assumptions

- **Connects to transportability literature** by handling covariate shift between study and target populations through importance weighting in the conformal framework
