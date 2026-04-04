# Reconstruction: abstract
**Paper:** 2006.06138  
**Condition:** with_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Conformal Prediction for Heterogeneous Treatment Effects

Understanding how treatments affect individuals differently is crucial for personalized medicine and evidence-based policy, yet current methods for estimating heterogeneous treatment effects provide poor uncertainty quantification. While machine learning approaches can flexibly estimate conditional average treatment effects (CATE), they typically rely on asymptotic approximations or strong modeling assumptions that may not hold in practice, limiting their reliability for high-stakes decision-making where treatment assignment errors could be costly.

We propose **Conformal Causal Inference**, a distribution-free framework that provides finite-sample prediction intervals for individual treatment effects. Our approach leverages recent advances in weighted conformal prediction to handle the fundamental challenge that individual treatment effects are never directly observable. We construct prediction intervals by treating the problem as inference under covariate shift, where we observe either treated or control outcomes for each individual but need to predict the unobserved counterfactual. 

Our method works by: (1) using propensity score weighting to create pseudo-exchangeability between observed and counterfactual outcomes, (2) applying conformal prediction with carefully constructed nonconformity scores that account for both treatment assignment and outcome prediction uncertainty, and (3) combining intervals for potential outcomes to yield treatment effect intervals with guaranteed coverage. The approach accommodates both randomized experiments and observational studies under standard unconfoundedness assumptions, requires no parametric modeling assumptions, and provides valid inference even when the study population differs from the target population.

This framework enables reliable uncertainty quantification for personalized treatment decisions while maintaining the flexibility of modern machine learning methods, with coverage guarantees that hold in finite samples regardless of the underlying data distribution.
