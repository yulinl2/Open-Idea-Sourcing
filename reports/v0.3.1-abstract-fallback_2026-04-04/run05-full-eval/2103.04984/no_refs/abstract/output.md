# Reconstruction: abstract
**Paper:** 2103.04984  
**Condition:** no_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

**Conformal Prediction for Individual Treatment Effects with Doubly Robust Coverage Guarantees**

Personalized treatment decisions require reliable estimates of individual treatment effects (ITEs) with valid uncertainty quantification. While machine learning methods excel at estimating conditional average treatment effects (CATE), they typically provide poorly calibrated confidence intervals that fail to achieve nominal coverage in finite samples. This limitation is particularly concerning in high-stakes applications like precision medicine, where understanding the uncertainty around treatment benefit is crucial for safe decision-making.

We propose **Doubly Robust Conformal Treatment Effects (DR-CTE)**, a novel framework that combines conformal prediction with doubly robust estimation to provide finite-sample marginal coverage guarantees for individual treatment effect intervals. Our approach constructs separate conformal predictors for treated and control potential outcomes using augmented inverse propensity weighting (AIPW) residuals as conformity scores. The key innovation is a cross-fitted procedure that ensures coverage holds even when both propensity score and outcome models are misspecified, as long as one is correctly specified.

For within-study subjects, we provide counterfactual intervals for the unobserved potential outcome that achieve exact 1-α coverage in randomized trials and maintain doubly robust coverage in observational studies. For out-of-study prediction, we extend the framework using covariate shift correction via importance weighting of conformity scores, enabling valid inference on new populations with different covariate distributions.

Our method provides the first finite-sample coverage guarantees for ITE prediction that are simultaneously model-agnostic, doubly robust, and applicable to both experimental and observational data. This addresses a critical gap between the flexibility of modern machine learning and the reliability requirements of causal inference applications.
