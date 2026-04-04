# Reconstruction: abstract
**Paper:** 2006.06138  
**Condition:** no_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Set-Valued Prediction with Finite-Sample Loss Control via Adaptive Conformal Risk Control

**Abstract**

Modern machine learning applications increasingly require algorithms to output sets of predictions rather than single point estimates, spanning domains from multi-label classification to object detection and protein folding. While conformal prediction provides distribution-free coverage guarantees for prediction sets, existing methods primarily focus on controlling set size or marginal coverage rather than directly controlling task-specific loss functions. This creates a fundamental gap between theoretical guarantees and practical objectives in set-valued prediction problems.

We introduce **Adaptive Conformal Risk Control (ACRC)**, a post-hoc calibration framework that constructs prediction sets with finite-sample guarantees on user-specified expected loss functions. Our approach leverages a novel risk-aware scoring mechanism that adaptively weights potential set elements based on their contribution to the overall risk, combined with a sequential calibration procedure that maintains loss control under distribution shift between calibration and test data.

ACRC operates by: (1) defining risk-calibrated scores that incorporate both model confidence and loss sensitivity, (2) employing a multi-level conformal framework that simultaneously controls multiple risk thresholds, and (3) using adaptive quantile estimation to maintain guarantees under covariate shift. The method provides finite-sample bounds showing that with probability at least 1-δ, the expected loss on test data remains below a user-specified threshold α, requiring only exchangeability between calibration and test examples.

Our framework accommodates arbitrary loss functions without model retraining, scales efficiently through approximate set construction algorithms, and provides the first distribution-free finite-sample guarantees for expected loss control in set-valued prediction. This bridges the gap between conformal prediction theory and practical risk-sensitive applications across computer vision and natural language processing domains.
