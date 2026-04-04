# Reconstruction: mindmap
**Paper:** 2006.06138  
**Condition:** with_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Paper Idea Mindmap

## Core Problem
- Develop a method to provide finite-sample guarantees on expected loss for set-valued predictions under exchangeability, working with arbitrary models and loss functions.

## Key Observations from References
- Conformal prediction can provide distribution-free coverage guarantees under exchangeability (Ref: arxiv-1904.06019)
- Weighted conformal scores can handle distributional shifts while maintaining validity (Ref: arxiv-1904.06019)
- Standard conformal prediction focuses on coverage rather than expected loss control
- Exchangeability is a weaker assumption than i.i.d. and more realistic for practical deployment

## Proposed Approach
### Main Idea
- Extend conformal prediction from coverage control to expected loss control by developing "Loss-Controlled Conformal Prediction" that uses quantile estimation of loss distributions rather than just coverage rates

### Sub-ideas
- **Conformal Loss Quantiles**: Instead of finding prediction sets with coverage guarantee 1-α, find sets that guarantee expected loss ≤ τ with probability 1-α
  - Use empirical quantiles of per-example losses on calibration set to estimate loss thresholds
  - Apply conformal framework to these loss quantiles for finite-sample guarantees

- **Set Construction via Loss Thresholding**: Build prediction sets by including all predictions with individual loss below a conformally-calibrated threshold
  - For multi-label: include labels with loss contribution below threshold
  - For detection: include bounding boxes with localization loss below threshold
  - Threshold determined by conformal quantile of calibration losses

- **Adaptive Loss Weighting**: Incorporate importance weighting (inspired by covariate shift handling) to adapt to different loss sensitivities
  - Weight losses by prediction confidence or uncertainty estimates
  - Maintain exchangeability while improving loss concentration

## Theoretical Grounding
- Conformal prediction theory guarantees that empirical quantiles concentrate around true quantiles under exchangeability
- By applying conformal framework to loss quantiles rather than coverage rates, we inherit finite-sample validity
- Expected loss control follows from controlling high-probability bounds on individual losses
- Exchangeability assumption allows for realistic deployment scenarios with temporal or batch effects

## Potential Challenges
- **Loss Distribution Estimation**: Individual prediction losses may be heavy-tailed or multimodal
  - Address by using robust quantile estimation and potentially adaptive binning strategies
  
- **Computational Efficiency**: Need to evaluate losses for all possible set elements during calibration
  - Use efficient approximations like sampling-based loss estimation or hierarchical thresholding

- **Set Size Control**: Pure loss control might lead to very large or very small prediction sets
  - Incorporate hybrid objectives that balance loss control with set size constraints

## Connections to Existing Work
- **Extends conformal prediction**: Moves beyond coverage guarantees to direct loss control while maintaining distribution-free finite-sample validity
- **Builds on covariate shift techniques**: Adapts the weighting ideas from arxiv-1904.06019 to handle heterogeneous loss sensitivities rather than distributional shift
- **Differs from standard risk control**: Provides stronger finite-sample guarantees compared to asymptotic risk bounds, and works with arbitrary loss functions rather than specific model classes
