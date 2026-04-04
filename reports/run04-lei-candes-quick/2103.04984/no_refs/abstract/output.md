# Reconstruction: abstract
**Paper:** 2103.04984  
**Condition:** no_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Conformal Prediction for Individual Treatment Effects with Covariate Shift Robustness

**Abstract**

Estimating individual treatment effects (ITEs) with reliable uncertainty quantification is crucial for personalized decision-making in medicine, policy, and other high-stakes domains. While existing methods for conditional average treatment effects (CATE) using flexible machine learning algorithms can achieve good point estimation performance, they typically fail to provide prediction intervals with valid finite-sample coverage guarantees. This limitation is particularly problematic when making individual-level decisions where uncertainty quantification is essential for risk assessment.

We propose **Doubly Robust Conformal Treatment Effect Prediction (DR-CTEP)**, a novel framework that combines conformal prediction with doubly robust estimation to provide finite-sample marginal coverage guarantees for individual treatment effects. Our approach constructs separate conformity scores for treated and control units using augmented inverse propensity weighting (AIPW) residuals, then combines them through a weighted conformal procedure that accounts for the propensity score. For subjects in the study population, we leverage the observed potential outcome to construct tighter intervals via a novel "semi-factual" conformal score that exploits the partial observability structure. For new subjects under covariate shift, we develop a covariate-shift-aware conformal procedure using importance weighting between source and target distributions.

The key theoretical contribution is proving that our intervals achieve exact 1-α marginal coverage for randomized experiments and maintain coverage under either correct propensity score or outcome model specification in observational studies. Our method naturally handles different inferential targets (ATE-type, ATT-type, ATC-type coverage) and provides a principled approach to uncertainty quantification for personalized treatment decisions without restrictive distributional assumptions.
