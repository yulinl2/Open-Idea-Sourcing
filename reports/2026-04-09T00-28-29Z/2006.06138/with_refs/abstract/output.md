# Reconstruction: abstract (iterative, 12 rounds)
**Paper:** 2006.06138  
**Condition:** with_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  
**Rounds:** 12  
**Best round:** 10 (score 4.2)  
**Converged:** True (reached max rounds (12))  
**Score trajectory:** 2.8 -> 3.2 -> 3.2 -> 3.8 -> 4.0 -> 3.8 -> 4.0 -> 3.8 -> 3.8 -> 4.2 -> 4.0 -> 4.0  

---

# Conformal Prediction Intervals for Individual Treatment Effects Under Covariate Shift

Understanding how treatments affect individuals differently is crucial for personalized decision-making in medicine and policy, yet existing methods for estimating conditional average treatment effects (CATE) provide poor uncertainty quantification. While recent advances in conformal prediction offer distribution-free uncertainty quantification for standard prediction problems, applying these methods to causal inference faces fundamental challenges: we never observe both potential outcomes for any individual, and the covariate distributions typically differ between treated and control groups even in randomized experiments.

We propose a novel framework that extends weighted conformal prediction to construct finite-sample valid prediction intervals for individual treatment effects. Our approach addresses the covariate shift problem by reweighting observations according to the inverse propensity score, enabling valid inference about counterfactual outcomes. Specifically, we develop a two-stage procedure that first constructs conformal prediction intervals for each potential outcome separately using appropriately weighted quantiles of nonconformity scores, then combines these intervals to obtain coverage guarantees for the individual treatment effect.

Our method achieves exact finite-sample coverage in randomized experiments where propensity scores are known by design, requiring only that either the outcome model or the propensity score model is correctly specified—but not both. Unlike existing approaches that rely on asymptotic approximations or strong parametric assumptions, our intervals maintain validity under arbitrary data distributions and flexible machine learning algorithms. The procedure naturally handles heteroskedasticity and provides a principled way to quantify uncertainty about treatment effects for individuals within the study population.

We establish theoretical guarantees showing that our weighted conformal intervals achieve the desired coverage probability exactly, and demonstrate through simulations that the method produces well-calibrated intervals with reasonable width across various data-generating processes. This work provides the first distribution-free approach for uncertainty quantification in causal inference that explicitly accounts for covariate shift, offering a practical tool for reliable individualized treatment recommendations.
