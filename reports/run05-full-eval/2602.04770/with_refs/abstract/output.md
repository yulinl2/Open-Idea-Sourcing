# Reconstruction: abstract
**Paper:** 2602.04770  
**Condition:** with_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Learning Optimal Conformal Score Functions with Coverage Guarantees

Conformal prediction provides finite-sample marginal coverage guarantees for prediction intervals, making it invaluable for uncertainty quantification in high-stakes applications. However, the efficiency of conformal intervals—their ability to be as short as possible while maintaining validity—depends critically on the choice of score function used to measure non-conformity. Existing methods typically employ fixed, heuristic score functions such as absolute residuals or quantile-based scores, which may be suboptimal for the underlying data distribution and lead to unnecessarily wide intervals.

We propose **Adaptive Conformal Prediction (ACP)**, a framework that learns data-driven score functions while preserving finite-sample coverage guarantees. Our key insight is to formulate score function learning as a bi-level optimization problem: the outer level minimizes expected interval length subject to coverage constraints, while the inner level maintains the conformal prediction procedure's validity through a novel regularization scheme. Specifically, we parameterize score functions using neural networks and introduce a coverage-aware loss that penalizes violations of the marginal coverage requirement during training.

To ensure robustness, we develop a **safety mechanism** that automatically falls back to classical conformal methods when the learned score function performs poorly, guaranteeing that coverage is never compromised regardless of the learning outcome. We further extend our approach to handle covariate shift by incorporating importance weighting techniques.

Our method achieves provably valid finite-sample coverage while empirically demonstrating significant improvements in interval efficiency across diverse datasets. This work bridges the gap between the theoretical guarantees of conformal prediction and the practical need for adaptive, data-driven uncertainty quantification methods.
