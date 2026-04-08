# Paper Idea Mindmap

## Core Problem
- Develop reliable uncertainty quantification methods for individual-level treatment effects that provide finite-sample coverage guarantees without strong modeling assumptions.

## Key Observations from References
- Conformal prediction provides distribution-free coverage guarantees under exchangeability assumptions (Ref: arxiv-1904.06019)
- Weighted conformal prediction can handle covariate shift when likelihood ratios are known or estimable (Ref: arxiv-1904.06019)
- The quantile lemma enables finite-sample guarantees by exploiting exchangeability properties of nonconformity scores
- Split conformal methods offer computational efficiency while maintaining coverage properties

## Proposed Approach

### Main Idea
- Extend weighted conformal prediction to causal inference by treating treatment assignment as a form of "selection shift" and constructing prediction intervals for individual treatment effects using propensity score reweighting combined with conformal methodology.

### Sub-ideas
- **Causal Conformal Framework**
  - Define nonconformity scores based on potential outcome residuals from flexible ML models
  - Use inverse propensity weighting to create "pseudo-exchangeability" between treated and control units
  
- **Doubly Robust Extension**
  - Combine outcome model residuals with propensity score adjustments
  - Construct weighted quantiles using both treatment assignment probabilities and outcome model uncertainties
  
- **Population Shift Adaptation**
  - Handle cases where study population differs from target population
  - Use importance weighting based on covariate distributions between populations
  
- **Split Causal Conformal**
  - Pre-fit both outcome models and propensity score models on separate data
  - Compute treatment effect predictions and nonconformity scores on held-out calibration set
  - Construct prediction intervals using weighted empirical quantiles

## Theoretical Grounding
- Builds on weighted exchangeability theory from conformal prediction literature
- Leverages causal inference identification results (unconfoundedness, overlap)
- Finite-sample coverage follows from quantile lemma applied to reweighted nonconformity scores
- Doubly robust properties provide robustness to model misspecification in either propensity or outcome models

## Potential Challenges
- **Propensity score estimation quality**
  - Address through ensemble methods or adaptive weighting schemes
  - Develop diagnostic tools for detecting poor propensity score overlap
  
- **High-dimensional confounders**
  - Combine with dimension reduction techniques or regularized estimation
  - Use cross-fitting procedures to avoid overfitting biases
  
- **Computational scalability**
  - Leverage split conformal approach to avoid refitting models
  - Develop efficient algorithms for weighted quantile computation

## Connections to Existing Work
- **Extends arxiv-1904.06019's weighted conformal prediction**: Instead of covariate shift, handles "treatment assignment shift" where propensity scores create the weighting mechanism
- **Differs from standard causal ML approaches**: Focuses on uncertainty quantification rather than point estimation, providing finite-sample guarantees rather than asymptotic properties
- **Complements doubly robust estimation**: Maintains robustness properties while adding rigorous uncertainty quantification through conformal methodology
- **Bridges conformal prediction and causal inference**: First application of conformal methods to individual treatment effect estimation with formal coverage guarantees