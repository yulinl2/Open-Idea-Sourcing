# Reconstruction: abstract
**Paper:** 2602.04770  
**Condition:** no_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

**Learning Adaptive Score Functions for Efficient Conformal Prediction**

Conformal prediction provides finite-sample marginal coverage guarantees for prediction intervals, making it invaluable for uncertainty quantification in high-stakes applications. However, the efficiency of conformal intervals—their ability to be as narrow as possible while maintaining coverage—depends critically on the choice of score function that measures how "unusual" a prediction is. Current methods typically employ fixed, heuristic score functions such as absolute residuals or quantile-based scores, which may be suboptimal for the underlying data distribution and can result in unnecessarily wide intervals.

We propose **Adaptive Conformal Prediction (ACP)**, a framework that learns data-driven score functions while preserving conformal prediction's finite-sample coverage guarantees. Our key insight is to formulate score function learning as a constrained optimization problem: minimize expected interval length subject to maintaining valid conformal coverage on a held-out calibration set. We introduce a neural network-based score function parameterization and develop a bilevel optimization algorithm that alternates between updating score function parameters and recomputing conformal quantiles.

Crucially, our method includes a **coverage-preserving fallback mechanism**: if the learned score function fails to achieve valid coverage during calibration, we automatically revert to a provably valid baseline score function. This ensures that ACP maintains conformal prediction's finite-sample guarantees regardless of optimization performance, while potentially achieving significant efficiency gains when learning succeeds.

Our approach promises to advance conformal prediction by making it both more efficient and more adaptive to data characteristics, with applications spanning regression, classification, and structured prediction tasks where tight, reliable uncertainty estimates are essential.
