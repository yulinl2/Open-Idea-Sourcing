# Paper Idea Mindmap

## Core Problem
- Current methods for heterogeneous treatment effects focus on point estimates but fail to provide reliable uncertainty quantification for individual-level treatment effects, which is crucial for personalized decision-making in high-stakes domains.

## Key Observations from References
- Conformal prediction can provide finite-sample coverage guarantees without distributional assumptions (Ref arxiv-2006.01474)
- Individual treatment effects τ(X) = f(X,1) - f(X,-1) + e_{X,1} - e_{X,-1} include both systematic differences and error variability that standard CATE methods ignore
- The fundamental problem is that we never observe both potential outcomes Y(1) and Y(0) for the same individual
- Existing conformal approaches require strong assumptions (independence of errors, Gaussianity) for tighter intervals

## Proposed Approach

### Main Idea
- Develop a **doubly-robust conformal framework** that combines outcome modeling with propensity score weighting to create prediction intervals for individual treatment effects that are valid under weaker assumptions and provide better finite-sample performance.

### Sub-ideas

- **Weighted Conformal Scores**
  - Use inverse propensity weighting within conformal prediction to handle covariate shift between study and target populations
  - Construct conformal scores that account for treatment assignment probabilities: S_i = |Y_i - f̂(X_i, T_i)| / π̂(T_i|X_i)

- **Cross-Fitted Ensemble Approach**
  - Split data into K folds and fit both outcome models μ̂(x,t) and propensity models π̂(t|x) on different folds
  - Create ensemble prediction intervals by averaging quantiles across folds to reduce overfitting bias
  - This provides robustness when either outcome or propensity model is misspecified

- **Adaptive Correlation Modeling**
  - Instead of assuming independence or specific correlation structure between e_{X,1} and e_{X,-1}, learn this from data
  - Use auxiliary regression on observed covariates to estimate Cor(e_{X,1}, e_{X,-1}|X) and adjust interval width accordingly
  - When correlation is positive (common confounder effect), intervals can be narrower; when negative, use conservative bounds

- **Multi-Level Coverage Guarantees**
  - Provide both marginal coverage (across all individuals) and conditional coverage (within covariate subgroups)
  - Use localized conformal prediction with adaptive neighborhoods based on covariate similarity
  - Balance between local validity and sufficient sample size through data-driven bandwidth selection

## Theoretical Grounding
- Doubly-robust property ensures validity if either outcome model or propensity model is correctly specified
- Conformal prediction provides distribution-free finite-sample guarantees without requiring consistency of underlying algorithms
- Cross-fitting prevents overfitting bias that could invalidate coverage, building on recent work in causal inference with machine learning
- Weighted conformal scores have been shown to handle covariate shift while maintaining coverage properties

## Potential Challenges

- **Computational Complexity**
  - Cross-fitting with ensemble methods increases computational burden by factor of K
  - Address through efficient implementations and parallel processing, plus theoretical analysis showing when simpler versions suffice

- **Small Sample Performance**
  - With limited data, both outcome and propensity models may be poorly estimated
  - Develop adaptive procedures that automatically switch to more conservative bounds when sample size is insufficient
  - Use stability selection to identify when models are unreliable

- **High-Dimensional Covariates**
  - Standard conformal methods can be conservative in high dimensions
  - Incorporate dimension reduction techniques within the conformal framework
  - Use sparsity-inducing methods for both outcome and propensity modeling

## Connections to Existing Work

- **Extends arxiv-2006.01474's approach** by removing the restrictive independence assumption between errors and providing better finite-sample performance through doubly-robust estimation
- **Differs from standard CATE literature** by focusing on prediction intervals rather than just point estimates, and by explicitly handling the unobserved nature of individual treatment effects
- **Builds on recent doubly-robust conformal work** but adapts it specifically for the causal inference setting where we need intervals for unobserved counterfactual differences
- **Connects to covariate shift literature** by using propensity weighting to handle differences between study and target populations, which is common in real applications