# Paper Idea Mindmap

## Core Problem
- Develop finite-sample uncertainty quantification methods for individual treatment effects that handle covariate shift between study and target populations while accounting for the fundamental counterfactual inference challenge.

## Key Observations from References
- Weighted conformal prediction can handle covariate shift when likelihood ratios are known/estimable (Tibshirani et al.)
- Standard conformal prediction requires exchangeability, but weighted versions can work under "weighted exchangeability"
- Individual treatment effect prediction requires combining intervals for both potential outcomes, but only one is observed per subject (Kivaranovic et al.)
- Conformal methods provide finite-sample coverage guarantees without distributional assumptions
- Propensity scores naturally provide likelihood ratios for treatment assignment in causal inference

## Proposed Approach

### Main Idea
- Combine weighted conformal inference with propensity-based reweighting to create doubly robust prediction intervals for counterfactual outcomes, leveraging the fact that one potential outcome is observed for study subjects while both are missing for new subjects.

### Sub-ideas

- **Weighted Conformal for Observed Outcomes**
  - For subjects in study: use standard conformal prediction for observed outcome, weighted conformal for counterfactual outcome
  - Weights based on inverse propensity scores to adjust for treatment selection bias

- **Doubly Robust Weighting Scheme** 
  - Primary weights: inverse propensity scores w(x) = 1/π(x) for treated, 1/(1-π(x)) for control
  - Secondary weights: outcome model residuals to handle model misspecification
  - Combines benefits of both propensity and outcome modeling

- **Separate Procedures for Study vs. New Subjects**
  - Study subjects: observed outcome + weighted conformal counterfactual
  - New subjects: weighted conformal for both potential outcomes using full covariate shift adjustment
  - Accounts for different information availability

- **Adaptive Coverage Levels**
  - Use α/2 for each potential outcome when both are unobserved (new subjects)
  - Use different coverage allocation when one outcome is observed (study subjects)
  - Optimize coverage allocation based on propensity score overlap

## Theoretical Grounding
- Weighted exchangeability from Tibshirani et al. provides foundation for covariate shift handling
- Propensity score theory ensures proper reweighting for causal inference
- Doubly robust property: valid inference when either propensity or outcome model is correct
- Conformal prediction's finite-sample guarantees carry through to weighted versions

## Potential Challenges

- **Propensity Score Estimation**
  - Challenge: Poor propensity estimates can degrade performance
  - Solution: Use ensemble methods, cross-fitting, or assume access to true propensities initially

- **Extreme Weights Problem**
  - Challenge: Very small propensities create unstable weights
  - Solution: Weight trimming with theoretical adjustment to maintain coverage guarantees

- **Computational Complexity**
  - Challenge: Need to recompute weighted quantiles for each test point
  - Solution: Develop efficient algorithms using sorted residuals and cumulative weight calculations

## Connections to Existing Work

- **Extends Tibshirani et al.'s covariate shift approach**
  - Uses their weighted conformal framework but with propensity-based weights instead of general likelihood ratios
  - Adds causal inference perspective with treatment-specific weighting

- **Builds on Kivaranovic et al.'s treatment effect intervals**
  - Addresses their limitation of not handling covariate shift
  - Provides more sophisticated combination of outcome intervals using causal inference principles
  - Maintains their finite-sample coverage guarantees while adding robustness

- **Connects to doubly robust estimation literature**
  - Brings robustness properties from average treatment effect estimation to uncertainty quantification
  - Novel application of doubly robust ideas to prediction intervals rather than point estimation