# Reconstruction: abstract
**Paper:** 2006.06138  
**Condition:** with_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Risk-Controlled Set Prediction via Conformal Loss Calibration

Machine learning applications increasingly require models to output sets of predictions—multiple labels in multi-label classification, object bounding boxes in detection, or pixel segments in semantic segmentation. While practitioners need principled control over the expected loss of these prediction sets, existing methods either lack finite-sample guarantees, require strong distributional assumptions, or are computationally prohibitive. Conformal prediction provides distribution-free coverage guarantees for single predictions, but does not directly address expected loss control for arbitrary set-prediction tasks.

We introduce **Conformal Loss Calibration (CLC)**, a post-hoc method that provides finite-sample guarantees on the expected loss of prediction sets under exchangeability assumptions. Our approach works by: (1) defining a conformity score based on the empirical loss of candidate prediction sets on a calibration dataset, (2) using conformal quantiles to determine loss-controlled thresholds, and (3) constructing prediction sets by including all candidates whose predicted loss falls below this threshold. The method is model-agnostic, requiring only that the underlying model can score or rank potential set elements.

CLC extends naturally to covariate shift scenarios using importance weighting techniques, maintains computational efficiency through efficient set enumeration strategies, and provides intuitive risk control via a single user-specified parameter. Unlike existing approaches that focus on coverage or specific loss functions, our framework handles arbitrary loss functions while providing rigorous finite-sample bounds on expected loss. We demonstrate the versatility of CLC across computer vision tasks (object detection, semantic segmentation) and NLP applications (multi-label text classification), showing that practitioners can achieve reliable loss control without retraining models or making distributional assumptions.
