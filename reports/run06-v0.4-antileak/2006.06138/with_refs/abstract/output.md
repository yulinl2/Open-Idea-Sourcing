# Reconstruction: abstract
**Paper:** 2006.06138  
**Condition:** with_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Conformal Prediction for Individual Treatment Effects Under Covariate Shift

Understanding heterogeneous treatment effects is crucial for personalized decision-making in medicine, policy, and social sciences, yet existing methods provide unreliable uncertainty quantification for individual-level causal effects. While machine learning approaches for estimating conditional average treatment effects achieve theoretical consistency, they fail to provide meaningful uncertainty bounds in finite samples, particularly when treatment effects vary substantially across individuals. This limitation is especially problematic in high-stakes applications where understanding the reliability of individual predictions is essential for safe deployment.

We propose **Weighted Conformal Causal Prediction (WCCP)**, a distribution-free framework that provides finite-sample coverage guarantees for individual treatment effect intervals without requiring parametric assumptions or asymptotic approximations. Our approach extends conformal prediction to the causal inference setting by constructing prediction intervals for individual treatment effects Y(1) - Y(0) using a novel weighting scheme that accounts for both propensity score imbalances and covariate shift between experimental and target populations. The key insight is to define nonconformity scores based on cross-fitted estimates of potential outcomes, then weight these scores by importance sampling ratios that correct for both treatment assignment probabilities and population differences.

WCCP provides several theoretical guarantees: (1) marginal coverage holds exactly in finite samples for any outcome distribution, (2) the method remains valid under covariate shift when likelihood ratios between populations can be estimated, and (3) coverage is maintained regardless of the complexity of underlying treatment effect heterogeneity. Unlike existing approaches that rely on asymptotic normality or specific model assumptions, our framework works with any base learner for outcome regression and handles both randomized experiments and observational studies satisfying standard causal identifiability conditions. The method naturally accommodates different target populations through reweighting, enabling reliable uncertainty quantification for treatment effect predictions in new contexts where covariate distributions may differ from the original study population.
