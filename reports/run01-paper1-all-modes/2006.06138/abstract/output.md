# Reconstruction: abstract
**Paper:** 2006.06138  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Set-Valued Prediction with Finite-Sample Risk Control

Many critical machine learning applications require outputting sets of predictions rather than single point estimates—from multi-label classification and object detection to protein structure prediction and neural machine translation. While existing methods can generate such prediction sets, they typically lack principled guarantees on the expected loss (risk) these sets will incur. Conformal prediction provides distribution-free coverage guarantees but focuses on controlling miscoverage probability rather than expected loss, and existing risk control methods either require strong distributional assumptions or only provide asymptotic guarantees.

We introduce **Risk-Controlled Set Prediction (RCSP)**, a distribution-free framework that constructs prediction sets with finite-sample guarantees on user-specified risk levels. Our approach leverages a novel calibration procedure that uses holdout data to learn a threshold function mapping from individual predictions to set sizes. The key insight is to employ a generalized conformal score that directly incorporates the target loss function, combined with a risk-aware quantile estimation procedure that accounts for the discrete nature of set-valued predictions.

RCSP works with any pre-trained model and any loss function, requiring only exchangeability between calibration and test data. We prove that our method controls the expected loss at the desired level with high probability, even in finite samples. The calibration procedure is computationally efficient, requiring only a single pass through the holdout data to compute empirical risk-quantile relationships.

Our framework unifies and extends existing approaches while providing stronger guarantees than coverage-based methods. We demonstrate the practical effectiveness of RCSP across diverse domains including computer vision, natural language processing, and structured prediction tasks, showing that it produces well-calibrated prediction sets that achieve the target risk level while maintaining reasonable set sizes.
