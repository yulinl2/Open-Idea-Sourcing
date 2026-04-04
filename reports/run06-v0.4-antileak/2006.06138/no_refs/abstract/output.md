# Reconstruction: abstract
**Paper:** 2006.06138  
**Condition:** no_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Conformal Prediction for Heterogeneous Treatment Effects: Distribution-Free Uncertainty Quantification in Causal Inference

Understanding how treatments affect individuals differently is crucial across medicine, public policy, and social sciences, yet existing methods for estimating heterogeneous treatment effects provide inadequate uncertainty quantification. While machine learning approaches like causal forests and meta-learners offer appealing theoretical properties for estimating conditional average treatment effects (CATEs), they struggle to provide reliable prediction intervals for individual-level effects—a critical limitation when decisions affect human welfare. The fundamental challenge stems from the impossibility of observing both potential outcomes for any individual, combined with the need for finite-sample guarantees that don't rely on asymptotic approximations or strong parametric assumptions.

We propose a novel framework that adapts conformal prediction to the causal inference setting, providing distribution-free uncertainty quantification for individual treatment effects. Our approach constructs prediction intervals for CATEs by leveraging the exchangeability of treatment assignment in randomized experiments and extending recent advances in conformal inference to handle the missing counterfactual problem. Specifically, we develop conformalization procedures that work with any base CATE estimator (neural networks, random forests, etc.) and provide finite-sample coverage guarantees regardless of model specification or data distribution.

Key contributions include: (1) theoretical guarantees showing our intervals achieve nominal coverage under standard causal assumptions, (2) extensions to observational studies under unconfoundedness, and (3) adaptive procedures that account for both aleatoric uncertainty in individual responses and epistemic uncertainty from limited samples. This framework enables principled decision-making about treatment assignment while maintaining the flexibility of modern machine learning approaches.
