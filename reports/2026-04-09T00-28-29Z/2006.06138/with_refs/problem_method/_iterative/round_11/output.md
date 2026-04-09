# Problem Formulation

## Notation and Setup

Let $(X_i, Y_i(1), Y_i(0))$ for $i = 1, \ldots, n$ denote the potential outcomes framework, where $X_i \in \mathcal{X} \subseteq \mathbb{R}^d$ represents covariates, $Y_i(1) \in \mathbb{R}$ is the potential outcome under treatment, and $Y_i(0) \in \mathbb{R}$ is the potential outcome under control. Let $T_i \in \{0,1\}$ denote the treatment assignment indicator, and define the observed outcome as $Y_i = T_i Y_i(1) + (1-T_i) Y_i(0)$. The individual treatment effect for unit $i$ is $\tau_i = Y_i(1) - Y_i(0)$.

For a new unit with covariates $X_{n+1}$, we observe the treatment assignment $T_{n+1}$ but seek to construct prediction intervals for the unobserved potential outcome $Y_{n+1}(1-T_{n+1})$ - that is, the counterfactual outcome under the treatment not received.

Let $P$ denote the joint distribution of $(X, Y(1), Y(0), T)$, and assume the following causal identification conditions hold:
- **Unconfoundedness**: $(Y(1), Y(0)) \perp T \mid X$
- **Overlap**: $0 < e(x) < 1$ for all $x \in \mathcal{X}$, where $e(x) = \mathbb{P}(T=1 \mid X=x)$ is the propensity score

Define the covariate distributions in the treated and control groups as:
$$P_X^{(1)} = \mathcal{L}(X \mid T=1), \quad P_X^{(0)} = \mathcal{L}(X \mid T=0)$$

Let $P_X^{\text{target}}$ denote the covariate distribution of the target population, which may differ from both $P_X^{(1)}$ and $P_X^{(0)}$. The likelihood ratios are:
$$w^{(1)}(x) = \frac{dP_X^{\text{target}}}{dP_X^{(1)}}(x), \quad w^{(0)}(x) = \frac{dP_X^{\text{target}}}{dP_X^{(0)}}(x)$$

## Problem Statement

**Given**: 
- Training data $\mathcal{D}_n = \{(X_i, Y_i, T_i)\}_{i=1}^n$ where each unit is observed under only one treatment condition
- A new unit with covariates $X_{n+1}$ and treatment assignment $T_{n+1}$
- Target coverage level $1-\alpha$ for $\alpha \in (0,1)$

**Find**: A prediction interval $\mathcal{C}_n(X_{n+1}, 1-T_{n+1})$ such that:
$$\mathbb{P}\left(Y_{n+1}(1-T_{n+1}) \in \mathcal{C}_n(X_{n+1}, 1-T_{n+1})\right) \geq 1-\alpha$$

**Guarantee**: The coverage probability should hold:
1. **Exactly in finite samples** when the propensity score $e(x)$ is known (randomized experiments)
2. **Asymptotically** when $e(x)$ must be estimated (observational studies)
3. **Under covariate shift** when the target population differs from the study population

## Objective and Constraints

The fundamental challenge is that for each unit, we observe only one potential outcome while the counterfactual remains missing. This creates a unique constraint: prediction intervals for $Y(1)$ can only be calibrated using data from treated units ($T=1$), while intervals for $Y(0)$ can only use control units ($T=0$).

Formally, define the treatment-specific datasets:
$$\mathcal{D}_n^{(1)} = \{(X_i, Y_i) : T_i = 1\}, \quad \mathcal{D}_n^{(0)} = \{(X_i, Y_i) : T_i = 0\}$$

The core constraint is that any valid prediction interval for $Y_{n+1}(t)$ must satisfy:
$$\mathbb{P}\left(Y_{n+1}(t) \in \mathcal{C}_n^{(t)}(X_{n+1}) \mid \mathcal{D}_n^{(t)}\right) \geq 1-\alpha$$
where the interval $\mathcal{C}_n^{(t)}(X_{n+1})$ depends only on $\mathcal{D}_n^{(t)}$.

## Technical Assumptions

**A1 (Causal Identification)**: Unconfoundedness and overlap hold as stated above.

**A2 (Exchangeability within Treatment Groups)**: Conditional on treatment assignment, the units are exchangeable:
$$\{(X_i, Y_i) : T_i = t\} \text{ are exchangeable for } t \in \{0,1\}$$

**A3 (Absolute Continuity)**: For covariate shift correction, $P_X^{\text{target}}$ is absolutely continuous with respect to both $P_X^{(1)}$ and $P_X^{(0)}$, and the likelihood ratios $w^{(1)}(x)$ and $w^{(0)}(x)$ are known or can be estimated consistently.

**A4 (Bounded Likelihood Ratios)**: There exist constants $M^{(1)}, M^{(0)} > 0$ such that:
$$\sup_{x \in \mathcal{X}} w^{(1)}(x) \leq M^{(1)}, \quad \sup_{x \in \mathcal{X}} w^{(0)}(x) \leq M^{(0)}$$

These assumptions connect naturally to the conformal prediction framework under covariate shift (Tibshirani et al., 2020), where weighted exchangeability enables distribution-free inference despite distributional differences between groups.

# Methodology

## High-Level Approach

Our approach extends weighted conformal prediction to handle the fundamental asymmetry in causal inference: treated units inform us about treated potential outcomes, while control units inform us about control potential outcomes. We construct separate prediction intervals for each potential outcome using only the relevant treatment group, then combine them appropriately based on the target estimand.

The key insight is that the same propensity score mechanism that creates covariate imbalance between treatment groups also provides the mathematical structure needed for valid inference under covariate shift.

## Core Algorithm: Treatment-Specific Weighted Conformal Prediction

For a target unit with covariates $x$ and desired treatment level $t \in \{0,1\}$, we construct prediction intervals using the following procedure:

### Algorithm 1: Counterfactual Prediction Intervals

```
Input: Training data D_n, target covariates x, target treatment t, 
       significance level α, score function S, likelihood ratios w^(t)

1. Extract treatment-specific data:
   D_n^(t) = {(X_i, Y_i) : T_i = t}
   Let n_t = |D_n^(t)|

2. For each candidate outcome value y ∈ ℝ:
   a. Compute nonconformity scores:
      V_i^(x,y) = S((X_i, Y_i), D_n^(t) ∪ {(x,y)}) for i: T_i = t
      V_{n_t+1}^(x,y) = S((x,y), D_n^(t))
   
   b. Compute weighted probabilities:
      p_i^w(x) = w^(t)(X_i) / (∑_{j:T_j=t} w^(t)(X_j) + w^(t)(x)) for i: T_i = t
      p_{n_t+1}^w(x) = w^(t)(x) / (∑_{j:T_j=t} w^(t)(X_j) + w^(t)(x))
   
   c. Include y in prediction set if:
      V_{n_t+1}^(x,y) ≤ Quantile(1-α; ∑_{i:T_i=t} p_i^w(x)δ_{V_i^(x,y)} + p_{n_t+1}^w(x)δ_∞)

3. Return: C_n^(t)(x) = {y ∈ ℝ : y satisfies step 2c}
```

### Split Conformal Variant

For computational efficiency, we provide a split conformal version:

```
Input: Training data D_n, fitted models μ̂^(1), μ̂^(0), target (x,t), level α

1. Split treatment-specific data:
   D_n^(t) = {(X_i, Y_i) : T_i = t} into fitting and calibration sets
   
2. Compute residuals on calibration set:
   R_i = |Y_i - μ̂^(t)(X_i)| for i in calibration set with T_i = t
   
3. Compute weighted quantile:
   q̂ = Quantile(1-α; ∑_i p_i^w(x)δ_{R_i} + p_{n_t+1}^w(x)δ_∞)
   
4. Return: C_n^(t)(x) = [μ̂^(t)(x) - q̂, μ̂^(t)(x) + q̂]
```

## Theoretical Properties

**Theorem 1 (Finite-Sample Coverage)**: Under assumptions A1-A4, for any score function $S$, the prediction interval $\mathcal{C}_n^{(t)}(x)$ constructed by Algorithm 1 satisfies:
$$\mathbb{P}(Y_{n+1}(t) \in \mathcal{C}_n^{(t)}(X_{n+1})) \geq 1-\alpha$$

**Theorem 2 (Exact Coverage in Randomized Experiments)**: When treatment assignment is completely randomized (i.e., $w^{(1)}(x) = w^{(0)}(x) = 1$ for all $x$), the coverage probability equals exactly $1-\alpha + \mathcal{O}(1/n_t)$.

**Theorem 3 (Asymptotic Validity under Covariate Shift)**: When likelihood ratios are estimated consistently, $\hat{w}^{(t)}(x) \to w^{(t)}(x)$ in probability, then:
$$\lim_{n \to \infty} \mathbb{P}(Y_{n+1}(t) \in \mathcal{C}_n^{(t)}(X_{n+1})) \geq 1-\alpha$$

## Design Justifications

**Treatment-Specific Calibration**: Following the insight from Kivaranovic et al. (2020), we recognize that each potential outcome can only be calibrated using data from the corresponding treatment group. This respects the fundamental constraint of causal inference.

**Weighted Exchangeability**: We extend the weighted conformal prediction framework of Tibshirani et al. (2020) to handle the covariate shift between treatment groups and the target population. The weights $w^{(t)}(x)$ rebalance the calibration data to match the target distribution.

**Score Function Flexibility**: Our framework accommodates arbitrary score functions $S$, enabling the use of complex machine learning models for conditional mean estimation while maintaining distribution-free coverage guarantees.

## Computational Complexity

- **Full Conformal**: $\mathcal{O}(n_t \cdot |\mathcal{Y}|)$ where $|\mathcal{Y}|$ is the discretization of the outcome space
- **Split Conformal**: $\mathcal{O}(n_t \log n_t)$ due to quantile computation
- **Memory**: $\mathcal{O}(n_t)$ for storing treatment-specific calibration data

The split conformal variant provides significant computational savings while maintaining the same theoretical guarantees, making the method practical for large-scale applications.