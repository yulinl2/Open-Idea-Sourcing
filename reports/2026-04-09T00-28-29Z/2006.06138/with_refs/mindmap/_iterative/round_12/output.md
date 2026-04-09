# Paper Idea Mindmap

## Core Problem
- Develop finite-sample prediction intervals for counterfactual outcomes in causal inference that account for covariate shift between treatment groups using weighted conformal inference with propensity score reweighting.

## Key Observations from References
- Weighted conformal prediction (Ref 1) provides distribution-free prediction intervals under covariate shift when the likelihood ratio between test and training distributions is known
- Standard conformal prediction requires exchangeability, but covariate shift violates this assumption
- Individual treatment effect inference (Ref 2) faces the fundamental problem that counterfactual outcomes are never observed
- Propensity scores naturally provide likelihood ratios between treatment and control covariate distributions
- The covariate shift problem in causal inference is precisely what weighted conformal inference was designed to handle

## Proposed Approach

### Main Idea
- Recognize that predicting counterfactual outcomes involves covariate shift: when predicting Y(0) for treated units, the "training" data (control units) has different covariate distribution than "test" data (treated units)
- Apply weighted conformal inference using propensity score weights to construct prediction intervals for counterfactual outcomes with finite-sample coverage guarantees

### Sub-ideas
- **Propensity Score Weighting for Covariate Shift**
  - Use estimated propensity scores e(x) = P(T=1|X=x) to construct likelihood ratio weights
  - For predicting Y(0) on treated units: w(x) = (1-e(x))/e(x)
  - For predicting Y(1) on control units: w(x) = e(x)/(1-e(x))

- **Weighted Conformal Construction**
  - Fit outcome models μ₀(x), μ₁(x) on control and treated units respectively
  - Compute residuals on appropriate groups with propensity score reweighting
  - Use weighted quantiles of residuals to form prediction intervals

- **Two-Stage Procedure**
  - Stage 1: Estimate propensity scores using logistic regression or flexible ML methods
  - Stage 2: Apply weighted conformal inference for counterfactual prediction intervals

## Theoretical Grounding
- Weighted conformal inference (Ref 1) guarantees coverage when likelihood ratios are known/well-estimated
- Propensity scores provide exactly the needed likelihood ratios for treatment assignment mechanism
- Coverage guarantees hold even with misspecified outcome models, provided propensity model is correct
- Finite-sample validity without asymptotic approximations or distributional assumptions

## Potential Challenges
- **Propensity Score Estimation Error**
  - Address through cross-fitting: use separate samples for propensity estimation and conformal inference
  - Develop theory for coverage under estimated weights (extension of existing weighted conformal theory)

- **Extreme Propensity Scores**
  - Handle through weight trimming or overlap restrictions
  - Develop adaptive procedures that adjust coverage level based on propensity score quality

- **Computational Efficiency**
  - Use split conformal approach: fit models on training set, compute weighted residuals on calibration set
  - Develop efficient algorithms for weighted quantile computation

## Connections to Existing Work
- **Extends Ref 1**: Applies weighted conformal inference to causal inference setting, using propensity scores as natural likelihood ratios
- **Complements Ref 2**: Provides alternative to their Bonferroni-style approach for individual treatment effects, potentially with tighter intervals by properly accounting for covariate shift
- **Novel synthesis**: First to connect propensity score methodology with weighted conformal inference for counterfactual uncertainty quantification
- **Methodological bridge**: Links classical causal inference tools (propensity scores) with modern conformal prediction framework