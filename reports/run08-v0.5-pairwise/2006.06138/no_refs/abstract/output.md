# Reconstruction: abstract
**Paper:** 2006.06138  
**Condition:** no_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Distribution-Free Prediction Intervals for Individual Treatment Effects via Nested Conformal Inference

Understanding treatment effect heterogeneity is crucial for personalized decision-making in medicine, policy, and social sciences. While machine learning methods can estimate conditional average treatment effects (CATE), they typically provide point estimates without reliable uncertainty quantification—a critical limitation when treatment decisions carry significant consequences. The fundamental challenge stems from the missing data problem inherent in causal inference: for any individual, we observe only one potential outcome, making direct validation of individual treatment effect predictions impossible.

We propose a novel framework that combines nested conformal prediction with outcome imputation to construct distribution-free prediction intervals for individual treatment effects. Our approach first trains separate conformal predictors for treated and control outcomes using cross-validation, then constructs treatment effect intervals by combining the prediction intervals through a carefully designed aggregation procedure that accounts for the dependence structure between potential outcomes. For individuals within the study population, we leverage the observed outcome to tighten intervals via a conditional conformal approach. For out-of-study individuals facing covariate shift, we extend recent work on weighted conformal prediction to maintain coverage guarantees under distribution shift.

Key theoretical contributions include finite-sample coverage guarantees that hold without parametric assumptions, robustness to CATE model misspecification, and explicit handling of both randomized and observational settings through propensity score weighting. Our framework enables practitioners to quantify uncertainty in treatment effect predictions while maintaining the flexibility of modern machine learning methods, bridging the gap between causal inference and distribution-free uncertainty quantification for reliable personalized treatment recommendations.
