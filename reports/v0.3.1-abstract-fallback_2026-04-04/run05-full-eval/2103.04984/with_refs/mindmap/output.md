# Reconstruction: mindmap
**Paper:** 2103.04984  
**Condition:** with_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Paper Idea Mindmap

## Core Problem
- Develop conformal prediction methods for individual treatment effects that provide finite-sample marginal coverage guarantees for both within-study counterfactual inference and out-of-study generalization under covariate shift.

## Key Observations from References
- Conformal prediction can provide distribution-free coverage guarantees but requires exchangeability assumption (Ref: arxiv-1904.06019)
- Weighted conformal scores can handle covariate shift by reweighting to match target distribution (Ref: arxiv-1904.06019)
- Standard conformal prediction breaks down when training and test distributions differ, which is common in causal inference applications

## Proposed Approach
### Main Idea
- Develop a "Causal Conformal Prediction" framework that combines conformal prediction with causal inference by treating the missing counterfactual as a covariate shift problem where we shift from the observed outcome distribution to the unobserved counterfactual distribution.

### Sub-ideas
- **Doubly Robust Conformal Scores**
  - Use influence function-based residuals from doubly robust estimators as conformal scores
  - Leverages existing doubly robust theory to handle propensity score and outcome model misspecification
  
- **Counterfactual Reweighting**
  - For within-study inference: weight conformal scores by inverse propensity scores to create "pseudo-counterfactuals"
  - For out-of-study inference: combine covariate shift weights with treatment assignment weights
  
- **Multi-Task Conformal Framework**
  - Simultaneously construct prediction intervals for Y(0) and Y(1) using shared conformal quantiles
  - Use cross-fitting to avoid overfitting when machine learning methods estimate nuisance parameters
  
- **Adaptive Coverage Targets**
  - Adjust coverage level based on propensity score overlap to account for extrapolation uncertainty
  - Provide honest coverage that acknowledges when counterfactual inference is inherently uncertain

## Theoretical Grounding
- Conformal prediction theory guarantees marginal coverage under exchangeability
- Weighted conformal prediction extends this to covariate shift settings
- Doubly robust estimation theory provides robustness to model misspecification
- Influence function theory connects causal inference residuals to prediction errors
- Cross-fitting theory enables valid inference with machine learning nuisance estimation

## Potential Challenges
- **Overlap Assumption Violations**
  - Address by developing "honest" intervals that widen appropriately in regions of poor overlap
  - Use propensity score diagnostics to flag when coverage guarantees may not hold
  
- **High-Dimensional Covariate Shifts**
  - Leverage recent advances in high-dimensional density ratio estimation
  - Develop adaptive weighting schemes that balance bias-variance tradeoffs
  
- **Computational Scalability**
  - Use efficient algorithms for weighted quantile computation
  - Develop approximate methods for large-scale applications

## Connections to Existing Work
- **Extends arxiv-1904.06019**: Applies weighted conformal prediction to the novel setting of causal inference where "covariate shift" occurs between factual and counterfactual distributions
- **Differs from standard CATE methods**: Provides finite-sample coverage guarantees rather than asymptotic normality assumptions
- **Complements doubly robust literature**: Uses existing doubly robust estimators as building blocks but adds rigorous uncertainty quantification
- **Novel contribution**: First method to provide non-asymptotic coverage for individual treatment effects under both model misspecification and covariate shift
