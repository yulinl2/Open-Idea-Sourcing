# Problem Formulation

## Notation and Setup

Let $(\mathcal{X}, \mathcal{Y}, \mathcal{T})$ denote the covariate space $\mathbb{R}^d$, outcome space $\mathbb{R}$, and treatment space $\{0,1\}$ respectively. We observe $n$ i.i.d. samples $\{(X_i, Y_i, T_i)\}_{i=1}^n$ where $(X_i, Y_i, T_i) \sim P$ for some unknown distribution $P$ on $\mathcal{X} \times \mathcal{Y} \times \mathcal{T}$.

Under the potential outcomes framework, each unit $i$ has two potential outcomes: $Y_i(1)$ under treatment and $Y_i(0)$ under control. We observe $Y_i = T_i Y_i(1) + (1-T_i) Y_i(0)$. The individual treatment effect for unit $i$ is defined as:
$$\tau_i = Y_i(1) - Y_i(0)$$

For a new unit with covariates $X_{n+1}$, we define the individual treatment effect as:
$$\tau(X_{n+1}) = Y_{n+1}(1) - Y_{n+1}(0)$$

Let $\pi(x) = P(T=1|X=x)$ denote the propensity score, and define the likelihood ratio weights:
$$w_i(x) = \frac{\mathbf{1}\{T_i = 1\}}{\pi(x)} + \frac{\mathbf{1}\{T_i = 0\}}{1-\pi(x)}$$

## Problem Statement

**Given:** 
- Training data $\mathcal{D}_n = \{(X_i, Y_i, T_i)\}_{i=1}^n$ 
- A new covariate vector $X_{n+1}$
- Desired coverage level $1-\alpha$ for $\alpha \in (0,1)$
- Known or estimable propensity scores $\pi(x)$

**Find:** A prediction interval $\mathcal{C}_n(X_{n+1}) \subseteq \mathbb{R}$ such that:
$$P\left(\tau(X_{n+1}) \in \mathcal{C}_n(X_{n+1})\right) \geq 1-\alpha$$

**Guarantee:** The coverage probability should hold:
1. In finite samples without asymptotic approximations
2. For both randomized experiments and observational studies
3. When the target population (characterized by covariate distribution of $X_{n+1}$) may differ from the study population

## Objective

We seek to construct a conformal prediction interval that accounts for:
1. **Fundamental missingness:** For each unit, we observe only one potential outcome
2. **Covariate shift:** The distribution of $X_{n+1}$ may differ from the empirical distribution of $\{X_i\}_{i=1}^n$  
3. **Treatment-specific information:** Treated units inform about $Y(1)$, control units inform about $Y(0)$
4. **Finite-sample validity:** Coverage guarantees without relying on asymptotic normality

The key insight is that we must construct separate conformal intervals for $Y(1)$ and $Y(0)$ using only the relevant subgroups, then combine them appropriately while accounting for the correlation structure.

## Technical Assumptions

**Assumption 1 (Unconfoundedness):** $(Y(0), Y(1)) \perp T | X$

**Assumption 2 (Overlap):** There exists $\epsilon > 0$ such that $\epsilon \leq \pi(x) \leq 1-\epsilon$ for all $x$ in the support of $X$

**Assumption 3 (Propensity Score Knowledge):** The propensity score $\pi(x)$ is either known (randomized experiments) or can be estimated consistently

**Assumption 4 (Exchangeability within Groups):** Conditional on $X$ and $T$, the potential outcomes are exchangeable within treatment groups

**Assumption 5 (Score Function Regularity):** We have access to score functions $S_1$ and $S_0$ for measuring conformity of treated and control outcomes respectively, where $S_t: \mathcal{X} \times \mathcal{Y} \times \mathcal{D}^{n_t} \to \mathbb{R}_+$ for $t \in \{0,1\}$

These assumptions connect to the weighted exchangeability framework of Tibshirani et al. (2020), extending their covariate shift methodology to the causal inference setting where we have treatment-specific subgroups rather than a single shifted population.

# Methodology

## High-Level Approach

Our methodology extends weighted conformal prediction to handle the fundamental challenge of individual treatment effect inference: each potential outcome can only be calibrated using observations from the corresponding treatment group. We develop a **split-group weighted conformal** approach that:

1. Constructs separate weighted conformal intervals for $Y(1)$ and $Y(0)$ using only treated and control units respectively
2. Accounts for covariate shift between study and target populations through likelihood ratio weighting  
3. Combines the intervals to form valid prediction intervals for $\tau(X_{n+1})$

## Core Algorithm

### Algorithm 1: Split-Group Weighted Conformal for Individual Treatment Effects

```
Input: Training data D_n = {(X_i, Y_i, T_i)}_{i=1}^n
       New covariate X_{n+1}
       Coverage level 1-α
       Propensity scores π(·)
       Score functions S_1, S_0

1. Split data by treatment:
   D_1 = {(X_i, Y_i) : T_i = 1}  // treated units (size n_1)
   D_0 = {(X_i, Y_i) : T_i = 0}  // control units (size n_0)

2. For each treatment level t ∈ {0, 1}:
   
   a. Compute likelihood ratio weights:
      If t = 1: w_i = π(X_{n+1})/π(X_i) for (X_i, Y_i) ∈ D_1
      If t = 0: w_i = (1-π(X_{n+1}))/(1-π(X_i)) for (X_i, Y_i) ∈ D_0
   
   b. For each candidate value y ∈ ℝ:
      - Compute conformity scores:
        V_i^{(t)}(y) = S_t((X_i, Y_i), D_t ∪ {(X_{n+1}, y)}) for i ∈ D_t
        V_{n+1}^{(t)}(y) = S_t((X_{n+1}, y), D_t)
      
      - Compute weighted probabilities:
        p_i^{(t)} = w_i / (∑_{j∈D_t} w_j + w(X_{n+1})) for i ∈ D_t
        p_{n+1}^{(t)} = w(X_{n+1}) / (∑_{j∈D_t} w_j + w(X_{n+1}))
   
   c. Construct weighted conformal set:
      C_t(X_{n+1}) = {y : V_{n+1}^{(t)}(y) ≤ Quantile(1-α_t; ∑_{i∈D_t} p_i^{(t)}δ_{V_i^{(t)}(y)} + p_{n+1}^{(t)}δ_∞)}

3. Combine intervals for treatment effect:
   C_n(X_{n+1}) = {y_1 - y_0 : y_1 ∈ C_1(X_{n+1}), y_0 ∈ C_0(X_{n+1})}

Output: Prediction interval C_n(X_{n+1}) for τ(X_{n+1})
```

### Key Design Decisions

**Split-Group Architecture:** We construct separate conformal procedures for each treatment group because the fundamental constraint is that $Y_i(1)$ can only be calibrated using treated units and $Y_i(0)$ using control units. This respects the missing data structure inherent in causal inference.

**Weighted Conformity:** Following Tibshirani et al. (2020), we weight observations by likelihood ratios $w_i = \frac{p_{\text{target}}(X_i)}{p_{\text{study}}(X_i)}$ where:
- For treated outcomes: $w_i = \frac{\pi(X_{n+1})}{\pi(X_i)}$
- For control outcomes: $w_i = \frac{1-\pi(X_{n+1})}{1-\pi(X_i)}$

This ensures that the weighted empirical distribution of conformity scores resembles what we would obtain from the target population.

**Level Allocation:** The choice of $\alpha_1$ and $\alpha_0$ for individual intervals affects the final coverage. We propose:
- **Conservative approach:** $\alpha_1 = \alpha_0 = \alpha/2$ (Bonferroni correction)
- **Efficient approach:** Under independence assumptions, $\alpha_1 = \alpha_0 = 1-\sqrt{1-\alpha}$

## Theoretical Properties

**Theorem 1 (Finite-Sample Coverage):** Under Assumptions 1-5, Algorithm 1 with Bonferroni correction ($\alpha_1 = \alpha_0 = \alpha/2$) satisfies:
$$P(\tau(X_{n+1}) \in \mathcal{C}_n(X_{n+1})) \geq 1-\alpha$$

**Theorem 2 (Coverage under Independence):** If additionally $Y_{n+1}(0) \perp Y_{n+1}(1) | X_{n+1}$, then Algorithm 1 with $\alpha_1 = \alpha_0 = 1-\sqrt{1-\alpha}$ satisfies:
$$P(\tau(X_{n+1}) \in \mathcal{C}_n(X_{n+1})) \geq 1-\alpha$$

**Corollary (Randomized Experiments):** When $\pi(x) = \pi$ is constant (randomized trials), the weights simplify to $w_i = 1$ and we recover exact finite-sample coverage.

## Computational Complexity

The algorithm has complexity $O(n \cdot |\mathcal{Y}|)$ where $|\mathcal{Y}|$ is the discretization of the outcome space for computing the conformal sets. For continuous outcomes, we can use efficient algorithms:

1. **Grid Search:** Discretize outcome space with resolution $\delta$
2. **Binary Search:** For monotonic score functions, use binary search to find interval boundaries  
3. **Split Conformal:** Pre-fit regression models to reduce computational burden

The split-group structure means we only need to recompute conformity scores within each treatment group, reducing the computational cost compared to full conformal prediction on the entire dataset.