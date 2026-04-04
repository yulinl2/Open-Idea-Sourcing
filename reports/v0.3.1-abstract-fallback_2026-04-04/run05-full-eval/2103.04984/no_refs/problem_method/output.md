# Reconstruction: problem_method
**Paper:** 2103.04984  
**Condition:** no_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Problem Formulation

## Notation and Setup

Let $(\mathcal{X}, \mathcal{Y}, \mathcal{T})$ denote the covariate, outcome, and treatment spaces, respectively, where $\mathcal{T} = \{0,1\}$ for binary treatments. For each unit $i$, let $X_i \in \mathcal{X}$ represent pre-treatment covariates, $T_i \in \mathcal{T}$ the treatment assignment, and $Y_i \in \mathcal{Y}$ the observed outcome. Under the potential outcomes framework, each unit has two potential outcomes: $Y_i(1)$ under treatment and $Y_i(0)$ under control, with the fundamental problem of causal inference being that only one is observed: $Y_i = T_i Y_i(1) + (1-T_i)Y_i(0)$.

The individual treatment effect (ITE) for unit $i$ is defined as:
$$\tau_i = Y_i(1) - Y_i(0)$$

The conditional average treatment effect (CATE) function is:
$$\tau(x) = \mathbb{E}[Y(1) - Y(0) | X = x] = \mu_1(x) - \mu_0(x)$$
where $\mu_t(x) = \mathbb{E}[Y(t) | X = x]$ for $t \in \{0,1\}$.

Let $\mathcal{D}_n = \{(X_i, T_i, Y_i)\}_{i=1}^n$ denote the training data from the source population with distribution $P$. For out-of-study inference, let $\mathcal{D}_m = \{X_j\}_{j=1}^m$ represent covariates from a target population with potentially different distribution $Q$.

## Problem Statement

**Given:** Training data $\mathcal{D}_n$ and significance level $\alpha \in (0,1)$.

**Find:** For any query point $x \in \mathcal{X}$, construct prediction intervals $C_n(x) = [L_n(x), U_n(x)]$ such that:

1. **Within-study counterfactual inference:** For units in the training population where one potential outcome is observed, the interval covers the unobserved counterfactual:
   $$P(Y_i(1-T_i) \in C_n(X_i) | T_i, X_i) \geq 1-\alpha$$

2. **Out-of-study generalization:** For new units from the target population where both potential outcomes are unobserved:
   $$P_Q(Y(t) \in C_n(X)) \geq 1-\alpha \quad \text{for } t \in \{0,1\}$$

3. **Treatment effect intervals:** For the individual treatment effect:
   $$P(\tau_i \in C_n^{\tau}(X_i)) \geq 1-\alpha$$

**Guarantee:** The coverage probability should hold in finite samples without relying on asymptotic approximations or strong parametric assumptions.

## Objective

The primary objective is to develop a method that provides **marginal coverage guarantees**:
$$\mathbb{E}_{(X,Y)} \left[ \mathbf{1}\{Y \in C_n(X)\} \right] \geq 1-\alpha$$

This marginal guarantee is weaker than pointwise coverage $P(Y \in C_n(x) | X = x) \geq 1-\alpha$ for all $x$, but is achievable without strong modeling assumptions. The method should be:

- **Distribution-free:** Valid regardless of the underlying data distribution
- **Model-agnostic:** Compatible with any machine learning algorithm for nuisance parameter estimation
- **Doubly robust:** Maintain coverage if either the propensity score model $e(x) = P(T=1|X=x)$ or outcome models $\mu_t(x)$ are correctly specified

## Technical Assumptions

**Assumption 1 (SUTVA):** The Stable Unit Treatment Value Assumption holds: (i) no interference between units, and (ii) treatment is well-defined with no hidden variations.

**Assumption 2 (Overlap):** There exists $\eta > 0$ such that $\eta \leq e(x) \leq 1-\eta$ for all $x$ in the support of $X$.

**Assumption 3 (Unconfoundedness):** For randomized experiments, treatment assignment is independent of potential outcomes: $(Y(0), Y(1)) \perp T | X$. For observational studies, this holds conditional on observed covariates.

**Assumption 4 (Exchangeability):** Training observations $(X_i, T_i, Y_i)$ are exchangeable, allowing for the application of conformal prediction principles.

**Assumption 5 (Covariate Shift):** For out-of-study inference, we allow the marginal distribution of covariates to differ between source and target populations, i.e., $P_X \neq Q_X$, but assume the conditional distributions satisfy $P_{Y|X} = Q_{Y|X}$.

These assumptions are standard in causal inference literature and are weaker than typical parametric modeling assumptions. The exchangeability assumption is crucial for conformal prediction validity, while the overlap condition ensures identifiability of causal effects.

# Methodology

## High-Level Approach

Our proposed method, **Conformal Causal Inference (CCI)**, combines conformal prediction with causal inference to provide finite-sample coverage guarantees for individual treatment effects. The key insight is to construct prediction intervals using conformal scores that account for the missing counterfactual nature of causal inference problems.

The approach consists of three main components:
1. **Nuisance parameter estimation** using any machine learning method
2. **Conformal score construction** tailored to causal inference targets
3. **Prediction interval formation** with finite-sample guarantees

## Core Algorithm

### Algorithm 1: Conformal Causal Inference

```
Input: Training data D_n, significance level α, query point x
Output: Prediction interval C_n(x) = [L_n(x), U_n(x)]

Step 1: Data Splitting
- Randomly split D_n into D_train (size n₁) and D_calib (size n₂)
- Ensure n₁ + n₂ = n

Step 2: Nuisance Parameter Estimation
- Train propensity score model: ê(x) using D_train
- Train outcome regression models: μ̂₀(x), μ̂₁(x) using D_train

Step 3: Doubly Robust Score Construction
For each (X_i, T_i, Y_i) ∈ D_calib, compute:
- ψ̂₀(X_i, T_i, Y_i) = μ̂₀(X_i) + (1-T_i)/(1-ê(X_i)) * (Y_i - μ̂₀(X_i))
- ψ̂₁(X_i, T_i, Y_i) = μ̂₁(X_i) + T_i/ê(X_i) * (Y_i - μ̂₁(X_i))

Step 4: Conformal Score Calculation
For target t ∈ {0,1} and each i ∈ D_calib:
- Compute residual: R_i^(t) = |Y_i - ψ̂_t(X_i, T_i, Y_i)|
- For treatment effect: R_i^τ = |τ̂_i - (ψ̂₁(X_i,T_i,Y_i) - ψ̂₀(X_i,T_i,Y_i))|
  where τ̂_i is the observed treatment effect when available

Step 5: Quantile Computation
- Sort residuals: R_{(1)}^(t) ≤ ... ≤ R_{(n₂)}^(t)
- Compute quantile: q̂_α^(t) = R_{(⌈(n₂+1)(1-α)⌉)}^(t)

Step 6: Prediction Interval Construction
For query point x:
- Point estimates: ψ̂₀(x), ψ̂₁(x) using trained models
- Intervals: C_n^(t)(x) = [ψ̂_t(x) - q̂_α^(t), ψ̂_t(x) + q̂_α^(t)]
- Treatment effect interval: C_n^τ(x) = [τ̂(x) - q̂_α^τ, τ̂(x) + q̂_α^τ]
  where τ̂(x) = ψ̂₁(x) - ψ̂₀(x)
```

## Doubly Robust Conformal Scores

The core innovation lies in the construction of doubly robust estimators within the conformal framework. For each potential outcome $t \in \{0,1\}$, we define:

$$\psi_t(X_i, T_i, Y_i) = \mu_t(X_i) + \frac{\mathbf{1}\{T_i = t\}}{e(X_i)^{T_i}(1-e(X_i))^{1-T_i}} (Y_i - \mu_t(X_i))$$

This estimator is doubly robust because it provides consistent estimation of $\mathbb{E}[Y(t)|X_i]$ if either the propensity score model $e(\cdot)$ or the outcome model $\mu_t(\cdot)$ is correctly specified.

The conformal score for potential outcome $Y(t)$ is then:
$$R_i^{(t)} = |Y_i - \psi_t(X_i, T_i, Y_i)|$$

For treatment effects, when the true ITE $\tau_i$ is not directly observable, we use the doubly robust estimator:
$$\hat{\tau}(X_i) = \psi_1(X_i, T_i, Y_i) - \psi_0(X_i, T_i, Y_i)$$

## Handling Covariate Shift

For out-of-study inference under covariate shift, we employ **weighted conformal prediction**. Given importance weights $w_i = \frac{dQ_X}{dP_X}(X_i)$ that can be estimated using density ratio estimation techniques, we modify the quantile computation:

```
Step 5 (Modified): Weighted Quantile Computation
- Compute weighted empirical CDF: F̂_w(r) = Σᵢ wᵢ𝟙{Rᵢ ≤ r} / Σᵢ wᵢ
- Find quantile: q̂_α^(t) = inf{r : F̂_w(r) ≥ 1-α}
```

## Theoretical Properties

**Theorem 1 (Marginal Coverage):** Under Assumptions 1-4, for any machine learning algorithms used to estimate nuisance parameters, the prediction intervals satisfy:
$$\mathbb{E}\left[\mathbf{1}\{Y(t) \in C_n^{(t)}(X)\}\right] \geq 1 - \alpha$$

**Theorem 2 (Double Robustness):** The coverage guarantee holds if either the propensity score model or the outcome regression models are consistently estimated, without requiring both to be correct.

**Theorem 3 (Covariate Shift Robustness):** Under Assumption 5 and with consistent density ratio estimation, the weighted conformal intervals maintain coverage for the target population.

## Computational Complexity

The algorithm has computational complexity $O(n \log n)$ due to the sorting step in quantile computation, plus the complexity of training the nuisance parameter models. The method is highly parallelizable:
- Nuisance parameter estimation can be distributed across models
- Conformal score computation is embarrassingly parallel
- The method scales linearly with the number of query points

The data splitting requirement reduces the effective sample size by half, but this is a fundamental limitation of conformal prediction that ensures finite-sample validity without distributional assumptions.
