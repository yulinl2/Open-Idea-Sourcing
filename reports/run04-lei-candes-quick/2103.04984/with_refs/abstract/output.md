# Reconstruction: abstract
**Paper:** 2103.04984  
**Condition:** with_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Doubly Robust Conformal Prediction for Individual Treatment Effects

Personalized medicine and policy interventions increasingly require reliable uncertainty quantification for individual treatment effects (ITEs), yet existing methods for conditional average treatment effect (CATE) estimation provide poorly calibrated confidence intervals that often exhibit severe undercoverage in finite samples. This limitation severely hampers their adoption in high-stakes applications where decision-makers need trustworthy uncertainty estimates alongside point predictions.

Current approaches face fundamental challenges: flexible machine learning methods for CATE estimation lack finite-sample coverage guarantees, while methods with theoretical coverage properties often rely on restrictive parametric assumptions. Moreover, existing solutions inadequately address the dual inferential tasks of constructing intervals for study subjects (where one potential outcome is observed) versus new subjects (where both outcomes are counterfactual), particularly under covariate shift between study and target populations.

We propose **Doubly Robust Conformal Causal Inference (DR-CCI)**, a novel framework that combines weighted conformal prediction with doubly robust estimation to provide finite-sample marginal coverage guarantees for individual treatment effects. Our approach constructs prediction intervals using residuals from doubly robust CATE estimators, employing importance weighting to handle covariate shift and separate conformalization procedures for the two inferential tasks. The method achieves exact coverage P(Y ∈ C(X)) ≥ 1-α under randomized experiments and maintains coverage under observational studies when either the propensity score or outcome regression models are correctly specified.

Key contributions include: (1) finite-sample coverage guarantees without distributional assumptions, (2) robustness to model misspecification through doubly robust properties, (3) unified treatment of in-study and out-of-study inference under covariate shift, and (4) accommodation of different coverage criteria (ATE, ATT, ATC-type). Our framework provides a principled foundation for reliable uncertainty quantification in personalized causal inference.
