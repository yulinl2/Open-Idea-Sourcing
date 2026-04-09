# Paper Idea Mindmap

## Core Problem
- Develop a method for constructing prediction intervals for counterfactual outcomes in causal inference that handles the covariate shift between treated and control populations while providing finite-sample coverage guarantees.

## Key Observations from References
- Weighted conformal prediction (Ref 1) can handle covariate shift when the likelihood ratio between source and target distributions is known or estimable
- Standard conformal prediction provides finite-sample coverage guarantees under exchangeability assumptions
- Individual treatment effect prediction (Ref 2) faces the fundamental problem that we never observe both potential outcomes for any individual
- The covariate distribution among treated units differs systematically from that among control units - this is precisely the covariate shift problem that weighted conformal prediction addresses
- Propensity scores provide likelihood ratios that quantify differences in covariate distributions between treatment groups

## Proposed Approach
### Main Idea
- Apply weighted conformal prediction to counterfactual outcome prediction by using propensity scores as the likelihood ratio weights, recognizing that predicting Y(0) for treated units involves covariate shift from treated to control distribution

### Sub-ideas
- **Propensity Score Weighting for Conformal Prediction**
  - Use estimated propensity scores π(x) = P(T=1|X=x) to construct likelihood ratio weights: w(x) = π(x)/(1-π(x)) for predicting control outcomes among treated units, and w(x) = (1-π(x))/π(x) for predicting treated outcomes among control units
  
- **Split Conformal for Computational Efficiency**
  - Employ split conformal prediction to avoid refitting models for each test point, making the method computationally tractable for large datasets
  
- **Separate Outcome Models**
  - Fit separate outcome models μ₀(x) and μ₁(x) on control and treated units respectively, then use weighted conformal prediction to construct intervals around these point predictions
  
- **Coverage Guarantee Structure**
  - Provide marginal coverage P(Y₁(x) ∈ Ĉ₁(x)) ≥ 1-α for any x, where the probability is over the randomness in both treatment assignment and outcomes

## Theoretical Grounding
- Weighted conformal prediction (Tibshirani et al.) guarantees coverage under covariate shift when likelihood ratios are known
- Propensity scores provide exactly these likelihood ratios between treatment group covariate distributions
- The exchangeability assumption in standard conformal prediction is replaced by weighted exchangeability under the reweighted distribution
- Finite-sample coverage holds even when outcome models are misspecified, provided propensity scores are correctly specified or well-estimated

## Potential Challenges
- **Propensity Score Estimation Error**
  - Address through cross-fitting/sample splitting: use separate samples for propensity score estimation and conformal prediction to maintain coverage guarantees
  - Provide theoretical analysis showing robustness to propensity score misspecification when overlap conditions hold

- **Extreme Propensity Scores**
  - Handle near-deterministic treatment assignment through propensity score trimming or stabilization
  - Develop adaptive procedures that adjust coverage level based on estimated propensity score quality

- **Computational Complexity with Weighted Quantiles**
  - Implement efficient algorithms for computing weighted quantiles in the conformal prediction step
  - Leverage existing weighted conformal prediction computational frameworks

## Connections to Existing Work
- **Extends Tibshirani et al. (2020)**: Applies their weighted conformal framework to the specific covariate shift problem in causal inference, using propensity scores as the natural likelihood ratio weights
- **Differs from Kivaranovic et al. (2020)**: Rather than constructing intervals for individual treatment effects τ(x) = Y₁(x) - Y₀(x), focuses on the more fundamental problem of constructing intervals for individual counterfactual outcomes Y₁(x) and Y₀(x) separately
- **Builds on causal inference literature**: Connects the long-established use of propensity scores for covariate adjustment to modern conformal prediction methodology
- **Novel contribution**: First to recognize and exploit the connection between propensity score weighting and weighted conformal prediction for handling the inherent covariate shift in counterfactual prediction