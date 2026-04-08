# Paper Idea Mindmap

## Core Problem
- Develop reliable uncertainty quantification methods for individual treatment effects that work in finite samples without strong parametric assumptions, addressing both subjects within the study (one outcome observed) and new subjects (both outcomes missing).

## Key Observations from References
- Conformal prediction can provide finite-sample coverage guarantees without distributional assumptions (Ref: arxiv-2006.01474)
- Individual treatment effects τ(X) = f(X,1) - f(X,-1) + e_{X,1} - e_{X,-1} contain both systematic and random components that require different uncertainty quantification approaches
- Existing conformal methods for treatment effects are conservative and don't distinguish between in-study vs. out-of-study inference challenges
- The fundamental asymmetry exists: for in-study subjects, one potential outcome is observed, requiring only counterfactual prediction for the missing outcome

## Proposed Approach

### Main Idea
- Develop a **stratified conformal framework** that explicitly separates uncertainty quantification for in-study subjects (semi-factual inference) from out-of-study subjects (full counterfactual inference), leveraging the observed outcome information for tighter intervals when available.

### Sub-ideas

- **Adaptive Conformal Weighting**
  - Use importance weighting in conformal scores to handle covariate shift between study and target populations
  - Develop population-aware nonconformity measures that account for distributional differences

- **Semi-Factual Conformal Intervals**
  - For in-study subjects: construct intervals around τ(X) = Y - Ŷ₀(X) where Y is observed and only Ŷ₀(X) needs prediction
  - Use residual-based conformal scores that condition on the observed treatment assignment
  - Achieve narrower intervals by exploiting the fact that estimation uncertainty is reduced by half

- **Doubly-Robust Conformal Construction**
  - Combine outcome regression and propensity score methods within conformal framework
  - Use cross-fitting to avoid overfitting bias in nonconformity score construction
  - Provide robustness against misspecification of either outcome or treatment assignment model

- **Hierarchical Uncertainty Decomposition**
  - Separate aleatoric uncertainty (irreducible randomness) from epistemic uncertainty (model estimation)
  - Use nested conformal procedures: inner level for outcome prediction, outer level for treatment effect aggregation
  - Scale intervals appropriately based on sample size and model complexity

## Theoretical Grounding
- Conformal prediction theory guarantees marginal coverage under exchangeability assumptions
- Weighted conformal methods can handle covariate shift while maintaining coverage (established in recent literature)
- The semi-factual case should achieve √2 improvement in interval width compared to full counterfactual case due to reduced uncertainty
- Doubly-robust estimation theory provides robustness guarantees that should transfer to conformal setting

## Potential Challenges

- **Exchangeability under covariate shift**
  - Address by developing locally weighted conformal scores that adapt to covariate density ratios
  - Use conditional conformal methods when global exchangeability fails

- **Calibration with small subgroups**
  - Implement smoothed conformal scores using kernel methods to borrow strength across similar covariate values
  - Develop adaptive bandwidth selection for local conformal regions

- **Computational scalability with complex ML models**
  - Use efficient cross-fitting schemes and parallel computation for conformal score calculation
  - Develop approximate conformal methods for very large datasets

## Connections to Existing Work

- **Extends arxiv-2006.01474's approach** by:
  - Distinguishing between in-study vs. out-of-study inference rather than treating all cases uniformly
  - Incorporating covariate shift handling and population weighting
  - Providing less conservative intervals through better uncertainty decomposition

- **Differs from standard CATE uncertainty quantification** by:
  - Focusing on prediction intervals rather than confidence intervals for conditional expectations
  - Providing finite-sample guarantees rather than asymptotic approximations
  - Handling both individual-level randomness and estimation uncertainty in a unified framework

- **Builds on weighted conformal prediction literature** by:
  - Adapting importance weighting specifically for causal inference settings
  - Addressing the unique challenge of missing counterfactual outcomes in weight construction