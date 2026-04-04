# Reconstruction: abstract
**Paper:** 2006.06138  
**Condition:** with_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Learning to Predict Sets with Guaranteed Expected Loss Control

In many modern machine learning applications, algorithms must output structured prediction sets rather than single predictions—from multi-label classification and object detection to protein structure prediction and neural machine translation. While existing methods like conformal prediction provide coverage guarantees for prediction sets, they focus on controlling the probability of including the true target, not the expected loss incurred by the prediction set. This limitation is critical when different prediction errors have varying costs, or when users need explicit control over performance metrics like F1-score, IoU, or task-specific losses.

We introduce **Set-Valued Expected Risk Minimization (SVERM)**, a post-hoc calibration framework that transforms any pre-trained model into one that outputs prediction sets with finite-sample guarantees on user-specified expected loss. Our approach leverages a novel extension of empirical risk minimization to the set-valued prediction setting, combined with concentration inequalities to provide non-asymptotic bounds. Specifically, given a calibration dataset and target expected loss level α, SVERM learns a randomized set-valued predictor that provably achieves expected loss ≤ α + O(√(log(1/δ)/n)) with probability 1-δ.

The key innovation lies in our tractable approximation scheme for the inherently combinatorial set optimization problem, which maintains theoretical guarantees while scaling to high-dimensional output spaces. Unlike conformal methods that require exchangeability, SVERM accommodates covariate shift through importance weighting and works with arbitrary loss functions including non-decomposable metrics. Our framework provides the first finite-sample expected loss control for set-valued prediction, enabling principled uncertainty quantification across diverse domains while remaining computationally efficient and model-agnostic.
