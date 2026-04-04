# Reconstruction: mindmap
**Paper:** 2006.06138  
**Condition:** with_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Paper Idea Mindmap

## Core Problem
- How to provide finite-sample, distribution-free uncertainty quantification for individual treatment effects when we can only observe one potential outcome per unit.

## Key Observations from References
- Conformal prediction provides exact finite-sample coverage guarantees without distributional assumptions, relying only on exchangeability
- Weighted conformal prediction can handle covariate shift by reweighting the empirical distribution of nonconformity scores using likelihood ratios
- The quantile lemma shows that for exchangeable random variables, empirical quantiles provide valid coverage bounds
- Split conformal prediction offers computational efficiency by pre-fitting the prediction function on separate data

## Proposed Approach

### Main Idea
- Extend conformal prediction to heterogeneous treatment effects by treating the fundamental problem of causal inference (missing counterfactuals) as a structured missing data problem, using weighted conformal methods to account for the systematic missingness pattern.

### Sub-ideas
- **Conformal Causal Intervals**: Construct prediction intervals for individual treatment effects τ(x) = E[Y(1) - Y(0)|X = x] by:
  - Defining nonconformity scores based on imputed counterfactuals from fitted outcome models
  - Using importance weights to account for treatment assignment probabilities in observational studies
  - Leveraging the fact that under unconfoundedness, treated and control units are "exchangeable" within propensity score strata

- **Two-Model Approach**: 
  - Fit separate outcome models μ₀(x) and μ₁(x) for control and treatment groups
  - For each unit i, compute pseudo-treatment effect τ̂ᵢ = μ₁(xᵢ) - μ₀(xᵢ) using leave-one-out fitting
  - Define nonconformity scores as |τᵢ - τ̂ᵢ| where τᵢ is the "true" treatment effect (observed for treated units as Yᵢ - μ₀(xᵢ), and for control units as μ₁(xᵢ) - Yᵢ)

- **Propensity Score Weighting**:
  - Weight nonconformity scores by inverse propensity weights to ensure exchangeability across treatment groups
  - For observational studies: wᵢ = 1/e(xᵢ) for treated units, wᵢ = 1/(1-e(xᵢ)) for control units
  - This creates "pseudo-randomization" making treatment effects exchangeable

- **Cross-Fitting for Robustness**:
  - Use sample splitting to avoid overfitting when estimating both outcome models and propensity scores
  - Employ cross-fitting techniques to use all data while maintaining valid inference

## Theoretical Grounding
- The weighted exchangeability framework from conformal prediction under covariate shift naturally extends to the causal setting where treatment assignment creates a form of "structured covariate shift"
- Under unconfoundedness (Y(0), Y(1) ⊥ T | X), the propensity score weighting restores exchangeability of potential outcomes across treatment groups
- The quantile lemma ensures finite-sample coverage regardless of the quality of outcome model fits, providing robustness against model misspecification
- Sample splitting/cross-fitting maintains exchangeability even when using the same data to fit models and construct intervals

## Potential Challenges
- **Overlap assumption violations**: Address by trimming extreme propensity scores or using adaptive weighting schemes that downweight units with poor overlap
- **High-dimensional confounders**: Extend to settings with many covariates by using regularized models for outcome regression and propensity score estimation, leveraging recent work on high-dimensional conformal prediction
- **Unmeasured confounding**: Develop sensitivity analysis tools that show how intervals would change under different levels of hidden confounding
- **Computational efficiency**: Implement split conformal variants that pre-fit outcome models to avoid refitting for each test point

## Connections to Existing Work
- **Extends conformal prediction**: Builds directly on the weighted conformal framework for covariate shift, treating treatment assignment as creating systematic covariate shift between treated/control populations
- **Differs from existing causal uncertainty methods**: Unlike Bayesian approaches or asymptotic methods, provides exact finite-sample guarantees without requiring correct model specification or large-sample approximations
- **Complements recent causal inference advances**: Works with any base learner (random forests, neural networks, etc.) for outcome modeling, making it compatible with modern machine learning approaches to causal inference
- **Relates to doubly robust methods**: The two-model approach mirrors doubly robust estimation but focuses on uncertainty quantification rather than point estimation
