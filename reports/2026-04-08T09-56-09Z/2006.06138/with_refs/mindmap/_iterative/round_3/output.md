# Paper Idea Mindmap

## Core Problem
- How to provide reliable uncertainty quantification for individual-level treatment effects when only one potential outcome is observed per subject, distinguishing between inference for study participants versus new individuals.

## Key Observations from References
- Conformal prediction provides distribution-free coverage guarantees under exchangeability assumptions without requiring modeling assumptions about the data generating process
- Weighted conformal prediction can handle covariate shift when likelihood ratios between training and test distributions are known or estimable
- The quantile lemma shows that exchangeable random variables naturally provide finite-sample coverage guarantees through empirical quantile calculations
- Split conformal prediction offers computational efficiency by pre-fitting models on separate data, maintaining coverage guarantees conditional on the pre-fitting stage

## Proposed Approach
### Main Idea
- Develop a **Causal Conformal Prediction** framework that adapts conformal prediction to the potential outcomes setting by treating the fundamental problem of causal inference as a structured missing data problem with known missingness mechanism (treatment assignment).

### Sub-ideas
- **Potential Outcome Conformal Scores**: Define nonconformity scores based on observed outcomes and fitted potential outcome functions, creating exchangeable scores under randomized treatment assignment
  - For subject i with observed (Xi, Ti, Yi), define scores as residuals from μ̂t(Xi) where t ∈ {0,1}
  - Key insight: Under randomization, (Xi, Ti, Yi^obs) are exchangeable, enabling direct application of conformal prediction

- **Stratified Conformal for Designed Experiments**: Exploit known propensity scores in randomized experiments
  - Within each stratum with propensity score π(x), apply conformal prediction separately to treatment and control groups
  - Combine predictions using known assignment probabilities: Ĉ(x) = π(x)Ĉ₁(x) + (1-π(x))Ĉ₀(x)
  - Provides exact finite-sample guarantees even with varying assignment probabilities across strata

- **Weighted Conformal for Observational Studies**: Extend weighted conformal prediction using estimated propensity scores
  - Weight training observations by inverse propensity scores to create pseudo-randomized exchangeability
  - Handle covariate shift between study and target populations using double weighting (propensity + covariate shift)
  - Robust to misspecification if either propensity model or outcome model is well-specified

- **Population vs. Individual Distinction**: Create separate procedures for different inferential targets
  - **In-sample inference**: For study participants, use partial exchangeability (one outcome observed, one counterfactual)
  - **Out-of-sample inference**: For new individuals, treat as standard covariate shift problem with estimated treatment effect functions

## Theoretical Grounding
- Builds on the exchangeability foundation of conformal prediction, extending it to the structured missingness of the causal setting
- Under randomization, the symmetry in treatment assignment creates the exchangeability needed for conformal guarantees
- Weighted conformal theory provides the foundation for handling observational studies and population shift
- The distinction between observed and counterfactual outcomes maps naturally to the missing data framework that conformal prediction can handle

## Potential Challenges
- **Propensity score estimation error**: Address through doubly-robust constructions where good estimation of either propensity or outcome model suffices for coverage
  - Use cross-fitting to reduce bias from model fitting on the same data used for inference
- **Computational complexity with multiple potential outcomes**: Develop efficient algorithms by pre-computing outcome models and using split conformal approaches
  - Separate model fitting from conformal calibration to maintain computational tractability
- **Defining meaningful nonconformity scores**: Ensure scores capture treatment effect heterogeneity rather than just outcome prediction
  - Consider scores based on individualized treatment effect estimates rather than separate outcome predictions

## Connections to Existing Work
- **Extends conformal prediction**: Applies the distribution-free coverage framework to causal inference, maintaining finite-sample guarantees without asymptotic approximations
- **Differs from weighted conformal**: While weighted conformal handles covariate shift, this approach handles the structured missingness of potential outcomes with known/estimable assignment mechanisms
- **Complements existing CATE methods**: Provides uncertainty quantification for any base CATE estimation method, similar to how conformal prediction works with any regression algorithm
- **Bridges causal inference and distribution-free inference**: Creates a principled connection between the potential outcomes framework and recent advances in assumption-free uncertainty quantification