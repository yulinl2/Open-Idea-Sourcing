# Reconstruction: abstract
**Paper:** 2103.04984  
**Condition:** with_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Doubly Robust Conformal Prediction for Individual Treatment Effects

Estimating individual treatment effects (ITE) with reliable uncertainty quantification is crucial for personalized decision-making in medicine, policy, and other high-stakes domains. While machine learning methods can effectively estimate conditional average treatment effects (CATE), they typically fail to provide prediction intervals with guaranteed finite-sample coverage properties. This limitation is particularly problematic given the fundamental challenge of causal inference: for any individual, we observe only one potential outcome, making uncertainty quantification essential for counterfactual predictions.

We propose a novel framework that combines doubly robust estimation with weighted conformal prediction to construct prediction intervals for individual treatment effects with guaranteed marginal coverage. Our approach leverages the doubly robust property by using both propensity score and outcome regression models, ensuring validity when at least one model is correctly specified. For the conformal component, we develop a specialized weighting scheme that accounts for both the missing counterfactual structure and potential covariate shift between study and target populations. The method constructs separate conformity scores for treated and control potential outcomes, then combines them using inverse propensity weighting to form valid prediction intervals.

Our framework provides exact finite-sample coverage guarantees P(τ(X) ∈ C(X)) ≥ 1-α for randomized experiments, where τ(X) represents the true individual treatment effect. For observational studies, coverage is guaranteed under the doubly robust conditions. The method handles both within-study counterfactual inference and out-of-study generalization, accommodating different inferential targets (ATE, ATT, ATC) while maintaining computational efficiency through compatibility with modern machine learning pipelines.
