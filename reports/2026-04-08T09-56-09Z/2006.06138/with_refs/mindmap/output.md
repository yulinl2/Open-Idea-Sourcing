# Reconstruction: mindmap (iterative, 5 rounds)
**Paper:** 2006.06138  
**Condition:** with_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  
**Rounds:** 5  
**Best round:** 5 (score 4.0)  
**Converged:** True (reached max rounds (5))  
**Score trajectory:** 3.8 -> 3.8 -> 3.0 -> 3.6 -> 4.0  

---

# Paper Idea Mindmap

## Core Problem
- How to provide reliable uncertainty quantification for individual treatment effects when covariate distributions differ systematically between treatment and control groups, leveraging the known treatment assignment mechanism.

## Key Observations from References
- Conformal prediction provides distribution-free coverage guarantees under exchangeability assumptions (Ref: arxiv-1904.06019)
- When covariate distributions differ between training and test sets, weighted conformal prediction can restore validity if the likelihood ratio is known (Ref: arxiv-1904.06019)
- The likelihood ratio weighting rebalances the empirical distribution to "look exchangeable" with the test distribution (Ref: arxiv-1904.06019)
- Split conformal methods offer computational efficiency by using pre-fitted models (Ref: arxiv-1904.06019)

## Proposed Approach
### Main Idea
- Develop "Causal Conformal Prediction" that treats counterfactual inference as a covariate shift problem where the likelihood ratio is determined by the known propensity score (treatment assignment mechanism)

### Sub-ideas
- **Propensity-Weighted Conformal Intervals**
  - For treated units, use control units weighted by e(X)/(1-e(X)) to approximate the counterfactual control outcome distribution
  - For control units, use treated units weighted by (1-e(X))/e(X) to approximate the counterfactual treatment outcome distribution
  - The propensity score e(X) = P(T=1|X) provides the exact likelihood ratio needed for valid covariate shift correction

- **Doubly Robust Conformal Construction**
  - Combine outcome modeling with propensity weighting in the nonconformity score
  - Use score function: S((x,y,t), Z) = |y - μ̂_t(x)| where μ̂_t is fitted on the opposite treatment group
  - Weight by inverse propensity scores when computing quantiles
  - Maintains validity if either the outcome model or propensity model is correctly specified

- **Split Causal Conformal for Efficiency**
  - Pre-fit outcome models μ̂_0, μ̂_1 on separate data splits
  - Use residuals from opposite treatment group's model as nonconformity scores
  - Apply propensity weighting only at the quantile computation step
  - Enables fast interval construction: τ̂(x) ± weighted quantile of cross-treatment residuals

## Theoretical Grounding
- The fundamental insight is that T|X creates a known, structured covariate shift between treatment groups
- In randomized experiments, e(X) is known by design, eliminating the need to estimate likelihood ratios
- The weighted exchangeability framework from conformal prediction under covariate shift directly applies
- Finite-sample validity follows from the quantile lemma applied to propensity-weighted nonconformity scores

## Potential Challenges
- **Extreme propensity scores leading to unstable weights**
  - Address through propensity score trimming or stabilized weights
  - Develop theory for coverage under trimming
- **Computational burden when propensity scores vary across units**
  - Leverage split conformal approach to pre-compute residuals
  - Use efficient quantile computation for weighted empirical distributions
- **Extension to observational studies with estimated propensity scores**
  - Develop double robustness results that account for propensity score estimation error
  - Investigate coverage properties under propensity score misspecification

## Connections to Existing Work
- **Extends arxiv-1904.06019's covariate shift framework** by recognizing that treatment assignment creates structured, known likelihood ratios via propensity scores
- **Differs from standard causal inference** by providing finite-sample, distribution-free uncertainty quantification rather than asymptotic normality-based intervals
- **Complements existing CATE methods** by providing a model-agnostic approach to uncertainty quantification that can wrap around any point estimator
- **Builds on split conformal methodology** but adapts it to the causal setting where the "test" distribution (counterfactual) is never directly observed
