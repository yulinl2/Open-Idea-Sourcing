# Reconstruction: mindmap
**Paper:** 2006.06138  
**Condition:** with_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Paper Idea Mindmap

## Core Problem
- How to provide reliable uncertainty quantification for conditional average treatment effects (CATE) with finite-sample coverage guarantees that work under covariate shift between study and target populations.

## Key Observations from References
- Conformal prediction provides distribution-free prediction intervals with exact finite-sample coverage guarantees under exchangeability (Ref: arxiv-1904.06019)
- Weighted conformal prediction can handle covariate shift when likelihood ratios between training and test distributions are known or estimable (Ref: arxiv-1904.06019)
- The fundamental challenge in CATE estimation is that only one potential outcome is observed per individual, making direct uncertainty quantification impossible
- Split conformal methods offer computational efficiency by using pre-fitted models with separate calibration data

## Proposed Approach
### Main Idea
- Develop a conformal prediction framework for CATE estimation that treats the unobserved counterfactual as a missing data problem, using weighted exchangeability to handle both the fundamental problem of causal inference and covariate shift simultaneously.

### Sub-ideas
- **Pseudo-outcome Construction**
  - Use influence function-based pseudo-outcomes that capture individual treatment effect estimates
  - Apply doubly robust estimation to create stable pseudo-outcomes that remain valid under model misspecification
  
- **Weighted Conformal for Causal Inference**
  - Extend weighted conformal prediction to handle propensity score reweighting for causal identification
  - Combine covariate shift weights with inverse propensity weights to address both distribution shift and treatment assignment bias
  
- **Split Conformal with Cross-fitting**
  - Use cross-fitting to avoid overfitting bias in both outcome models and propensity score models
  - Apply split conformal on the cross-fitted pseudo-outcomes to maintain exchangeability properties
  
- **Adaptive Weighting Scheme**
  - Develop composite weights that account for: (1) likelihood ratio for covariate shift, (2) inverse propensity scores for causal identification, (3) overlap weights for stability
  - Use estimated weights with theoretical guarantees when true weights are unknown

## Theoretical Grounding
- Weighted exchangeability from Tibshirani et al. provides the foundation for handling distribution shift
- Influence function theory ensures that pseudo-outcomes have the right asymptotic properties for causal inference
- Cross-fitting combined with Donsker conditions can maintain the exchangeability needed for conformal guarantees
- Doubly robust estimation provides protection against misspecification of either outcome or propensity models

## Potential Challenges
- **Weight Estimation Error**
  - Challenge: Estimated likelihood ratios and propensity scores introduce additional uncertainty
  - Solution: Use sample splitting and cross-fitting to ensure weights are estimated on independent data, maintaining conditional exchangeability
  
- **Overlap and Extreme Weights**
  - Challenge: Poor overlap or extreme propensity scores can lead to unstable weights
  - Solution: Incorporate overlap weighting schemes and develop truncation strategies that preserve coverage guarantees
  
- **Model Misspecification**
  - Challenge: Both outcome models and propensity models may be misspecified
  - Solution: Leverage doubly robust pseudo-outcomes and show that conformal coverage is preserved even under some forms of misspecification

## Connections to Existing Work
- **Extends Tibshirani et al.'s weighted conformal prediction** by combining covariate shift handling with causal inference requirements, using composite weights that address both challenges simultaneously
- **Differs from standard CATE uncertainty quantification** by providing finite-sample guarantees rather than asymptotic approximations, and by being robust to model misspecification through the conformal framework
- **Builds on influence function methods** but uses them within a conformal framework rather than relying on asymptotic normality assumptions
- **Connects to doubly robust estimation literature** by using DR pseudo-outcomes as the basis for conformal prediction, providing both bias protection and coverage guarantees
