# Reconstruction: abstract
**Paper:** 2006.06138  
**Condition:** with_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Conformal Prediction Intervals for Individual Treatment Effects

Understanding treatment effect heterogeneity is crucial across medicine, policy evaluation, and social sciences, where average treatment effects can mask substantial individual-level variation in treatment response. While machine learning methods for estimating conditional average treatment effects (CATE) have advanced significantly, they suffer from poor uncertainty quantification—a critical limitation when making high-stakes individualized treatment decisions. The fundamental challenge is that individual treatment effects are never directly observable, as each unit experiences only one potential outcome, making traditional uncertainty quantification approaches inadequate.

We propose **Causal Conformal Prediction**, a distribution-free framework that constructs finite-sample prediction intervals for individual treatment effects without requiring asymptotic approximations or strong parametric assumptions. Our approach leverages the potential outcomes framework by treating the unobserved counterfactual as a missing data problem. We develop weighted conformal prediction procedures that account for treatment assignment mechanisms in both randomized experiments and observational studies with unconfoundedness. The key innovation is constructing nonconformity scores based on pseudo-outcomes that combine observed outcomes with CATE estimates, then applying importance weighting to handle covariate shift between treated and control populations.

For randomized experiments, our method provides marginal coverage guarantees by exploiting the exchangeability of treatment assignments. For observational studies, we extend the framework using propensity score weighting to achieve coverage under unconfoundedness assumptions. The procedure naturally handles model misspecification by relying only on the validity of the conformity scores rather than the correctness of the underlying CATE estimator.

Our framework delivers several key contributions: (1) finite-sample coverage guarantees for individual treatment effect intervals without distributional assumptions, (2) robustness to CATE model misspecification, (3) seamless handling of both experimental and observational data, and (4) computational efficiency through split conformal procedures. This enables reliable uncertainty quantification for personalized treatment decisions in sensitive applications where understanding individual-level risk is paramount.
