# Reconstruction: abstract
**Paper:** 2006.06138  
**Condition:** no_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Set-Valued Prediction with Finite-Sample Risk Control via Weighted Conformal Methods

Modern machine learning applications increasingly require prediction of sets rather than single outputs—from multi-label classification in medical diagnosis to object detection in autonomous systems. While existing approaches focus on optimizing set-based metrics during training, they provide no formal guarantees about the expected loss of prediction sets at test time. This gap is particularly problematic in safety-critical applications where practitioners need principled control over risk levels.

We introduce **Weighted Risk-Controlled Prediction Sets (W-RCPS)**, a post-hoc calibration framework that provides finite-sample guarantees on the expected loss of arbitrary set-valued predictions. Our approach leverages a novel weighted conformal prediction mechanism that adaptively adjusts prediction set inclusion thresholds based on instance-specific risk estimates derived from a holdout calibration set. Unlike standard conformal methods that control coverage, W-RCPS directly controls expected loss through a risk-aware weighting scheme that accounts for heteroscedastic uncertainty across different regions of the input space.

The method requires only: (1) a pre-trained model producing set-valued predictions, (2) a user-specified risk tolerance level α, and (3) a calibration set with true labels. Under the mild assumption of exchangeability between calibration and test data, W-RCPS guarantees that the expected loss remains below α with high probability. The approach is model-agnostic, computationally efficient (requiring only threshold selection), and handles arbitrary loss functions including Hamming loss, Jaccard loss, and custom domain-specific metrics.

We demonstrate the effectiveness of W-RCPS across multi-label classification, semantic segmentation, and multi-object detection tasks, showing consistent risk control while maintaining competitive predictive performance compared to uncalibrated baselines.
