# Reconstruction: abstract
**Paper:** 2602.04770  
**Condition:** no_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Learning Optimal Score Functions for Efficient Conformal Prediction

**Abstract**

Conformal prediction provides distribution-free finite-sample coverage guarantees for prediction intervals, but the efficiency of these intervals critically depends on the choice of score function used to quantify prediction uncertainty. Existing approaches either rely on heuristic score functions that may be suboptimal, or use fixed scoring rules that cannot adapt to the specific characteristics of the prediction problem. This leads to unnecessarily wide intervals that, while maintaining valid coverage, sacrifice practical utility.

We propose **Adaptive Conformal Score Learning (ACSL)**, a novel framework that jointly optimizes both the underlying predictor and the conformal score function to minimize expected interval width while preserving finite-sample marginal coverage guarantees. Our approach formulates score function learning as a constrained optimization problem where we minimize a differentiable upper bound on interval width subject to an empirical coverage constraint. We introduce a parametric score function class based on neural networks that can capture complex relationships between predictions and true uncertainty, and develop a bilevel optimization algorithm that alternates between updating the predictor and the score function parameters.

Theoretically, we prove that our learned score functions maintain the finite-sample coverage property of conformal prediction while achieving asymptotic optimality in terms of interval width. Our framework is model-agnostic and can be applied to any base predictor, from linear models to deep neural networks. The method scales efficiently to high-dimensional problems and provides a principled way to incorporate domain knowledge about prediction uncertainty through the score function architecture. This work bridges the gap between the statistical rigor of conformal prediction and the practical need for efficient uncertainty quantification in modern machine learning applications.
