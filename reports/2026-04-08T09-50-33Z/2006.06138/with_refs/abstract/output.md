# Reconstruction: abstract (iterative, 2 rounds)
**Paper:** 2006.06138  
**Condition:** with_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  
**Rounds:** 2  
**Converged:** True (teacher recommended stop)  
**Score trajectory:** 3.4 -> 3.2  

---

# Distribution-Free Causal Prediction Intervals via Weighted Conformal Inference

Understanding heterogeneous treatment effects is crucial for personalized decision-making, yet existing methods for estimating conditional average treatment effects (CATE) provide poor uncertainty quantification. The fundamental challenge lies in constructing valid prediction intervals for individual-level causal effects when only one potential outcome is observed per unit, compounded by uncertainty in both treatment assignment mechanisms and outcome models. Current approaches either rely on strong parametric assumptions or fail to provide finite-sample validity guarantees, limiting their utility in high-stakes applications where reliable uncertainty assessment is essential.

We propose a novel framework that extends conformal prediction to causal inference settings, enabling distribution-free construction of prediction intervals for individual treatment effects. Our approach leverages a doubly-weighted conformal procedure that accounts for both the propensity score (treatment assignment probabilities) and outcome regression uncertainties. Specifically, we construct nonconformity scores using cross-fitted nuisance function estimates and apply carefully designed weights that reflect both the target population's covariate distribution and the treatment assignment mechanism. This yields prediction intervals that maintain finite-sample validity under weak assumptions: either the propensity score model or the outcome regression functions must be correctly specified, but not both simultaneously.

The key technical innovation is showing that our weighted nonconformity scores satisfy a generalized exchangeability property under standard causal assumptions (unconfoundedness and overlap), enabling application of weighted conformal prediction theory. Our framework naturally handles covariate shift between study and target populations, extends to counterfactual prediction for new individuals, and provides valid inference for both randomized experiments and observational studies. Unlike existing methods, our approach requires no distributional assumptions about potential outcomes and maintains coverage guarantees even with misspecified nuisance functions, offering a robust solution for uncertainty quantification in personalized treatment effect estimation.
