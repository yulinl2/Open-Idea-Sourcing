# Reconstruction: abstract
**Paper:** 2602.04770  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Learning Adaptive Conformal Score Functions for Efficient Prediction Intervals

Conformal prediction provides finite-sample marginal coverage guarantees for prediction intervals, making it invaluable for uncertainty quantification in high-stakes applications. However, the efficiency of conformal intervals—their ability to be narrow while maintaining coverage—depends critically on the choice of score function that measures how "unusual" a prediction-target pair appears. Current methods rely on fixed, often heuristically chosen score functions that may be suboptimal for specific datasets and prediction tasks.

We propose **Adaptive Conformal Prediction (ACP)**, a framework that learns data-driven score functions while preserving conformal prediction's finite-sample coverage guarantees. Our key insight is to parameterize the score function as a neural network and optimize it using a novel objective that balances interval efficiency with coverage validity. Specifically, we minimize expected interval length subject to maintaining proper calibration on a held-out validation set, ensuring the learned score function produces valid conformal intervals.

The critical challenge is that naively optimizing score functions can violate the exchangeability assumptions underlying conformal prediction's coverage guarantees. We address this through a careful data-splitting scheme that separates score function learning from conformal calibration, combined with theoretical analysis showing that our approach maintains finite-sample marginal coverage regardless of the learned score function's quality.

Our framework extends naturally to covariate shift settings by incorporating importance weighting, and provides consistency guarantees showing that learned score functions converge to efficiency-optimal choices. Empirically, ACP produces substantially shorter intervals than standard conformal methods while maintaining rigorous coverage guarantees across diverse regression and classification tasks, offering a principled approach to improving conformal prediction efficiency without sacrificing its fundamental reliability.
