# Problem Formulation

## Notation and Setup

Let $\mathcal{X} \subseteq \mathbb{R}^d$ denote the covariate space and $\mathcal{Y} \subseteq \mathbb{R}$ the outcome space. For each individual $i$, we observe covariates $X_i \in \mathcal{X}$, treatment assignment $T_i \in \{0,1\}$, and outcome $Y_i \in \mathcal{Y}$. We define the potential outcomes framework where $Y_i(1)$ and $Y_i(0)$ represent the potential outcomes under treatment and control, respectively, with the observed outcome $Y_i = T_i Y_i(1) + (1-T_i) Y_i(0)$.

The individual treatment effect (ITE) for individual $i$ is defined as:
$$\tau_i = Y_i(1) - Y_i(0)$$

The fundamental problem of causal inference is that we never observe both potential outcomes simultaneously—only one is revealed based on the treatment assignment. This creates a missing data problem that complicates uncertainty quantification.

Let $D_n = \{(X_i, T_i, Y_i)\}_{i=1}^n$ denote our training dataset of $n$ i.i.d. observations. For a new individual with covariates $X$, we seek to construct prediction intervals for their individual treatment effect $\tau(X) = Y(1) - Y(0)$.

## Formal Problem Statement

**Given:** Training data $D_n = \{(X_i, T_i, Y_i)\}_{i=1}^n$ where $(X_i, T_i, Y_i)$ are i.i.d. copies of $(X, T, Y)$, and a new covariate vector $X$.

**Find:** An interval-valued function $\Gamma_{D_n}: \mathcal{X} \to \{[a,b] : a \leq b\}$ that produces prediction intervals for the individual treatment effect.

**Guarantee:** For a specified confidence level $1-\alpha$ where $\alpha \in (0,1)$, the prediction interval should satisfy:
$$\mathbb{P}(\tau(X) \in \Gamma_{D_n}(X)) \geq 1-\alpha$$
where the probability is taken over both the randomness in the training data $D_n$ and the new observation $(X, \tau(X))$.

## Objective

Our objective is to construct prediction intervals that achieve valid finite-sample coverage while being as narrow as possible. Specifically, we aim to minimize the expected interval width:
$$\mathbb{E}[\text{width}(\Gamma_{D_n}(X))]$$
subject to the coverage constraint above.

The challenge lies in the fact that individual treatment effects $\tau_i$ are never directly observed in the training data, making standard prediction interval methods inapplicable. We must therefore develop methods that can quantify uncertainty about unobserved quantities using only the observed data structure.

## Technical Assumptions

**Assumption 1 (Unconfoundedness):** Treatment assignment is unconfounded given covariates:
$$(Y(0), Y(1)) \perp T \mid X$$
This assumption is automatically satisfied in randomized experiments and is the standard identifying assumption for observational studies.

**Assumption 2 (Overlap):** There exists $\eta > 0$ such that:
$$\eta \leq \mathbb{P}(T = 1 \mid X = x) \leq 1 - \eta$$
for all $x$ in the support of $X$. This ensures that both treatment and control observations are available across the covariate space.

**Assumption 3 (Exchangeability):** The training observations $(X_i, T_i, Y_i)$ are exchangeable with the test observation $(X, T, Y)$, where $T$ represents a hypothetical treatment assignment for the test individual.

**Assumption 4 (Regularity):** The outcome regression functions $\mu_t(x) = \mathbb{E}[Y(t) \mid X = x]$ for $t \in \{0,1\}$ are well-defined and finite for all $x$ in the support of $X$.

These assumptions are standard in the causal inference literature and are considerably weaker than parametric modeling assumptions typically required for uncertainty quantification.

## Connection to Prior Work

Our formulation extends the conformal prediction framework of Vovk et al. (2005) to the causal inference setting. While Kivaranovic et al. (2020) propose conformal intervals for individual treatment effects, their approach requires separate prediction intervals for each potential outcome and combines them using union bounds, leading to conservative intervals. Our formulation seeks to directly address the individual treatment effect while maintaining finite-sample validity without requiring distributional assumptions about the error terms or asymptotic approximations.

The key insight is that while we cannot observe individual treatment effects directly, we can leverage the conditional exchangeability structure induced by treatment assignment to construct valid prediction intervals that account for both the uncertainty in estimating the outcome regression functions and the inherent variability in individual responses.

# Methodology

## High-Level Approach

Our proposed method, **Conformal Causal Prediction (CCP)**, constructs prediction intervals for individual treatment effects by extending conformal prediction to handle the missing data structure inherent in causal inference. The key insight is to use the observed outcomes under each treatment arm to construct conformity scores that respect the causal structure, then combine these scores to produce valid intervals for the unobserved individual treatment effect.

The method proceeds in three stages: (1) fit outcome regression models for each treatment arm, (2) construct treatment-specific conformity scores using conformal prediction, and (3) combine these scores through a novel aggregation procedure that maintains finite-sample validity.

## Core Algorithm

Our algorithm leverages a split-conformal approach adapted for the causal setting. We split the training data by treatment assignment and apply conformal prediction within each arm, then aggregate the results.

### Algorithm 1: Conformal Causal Prediction

```
Input: Training data D_n = {(X_i, T_i, Y_i)}_{i=1}^n, test covariate X, confidence level α
Output: Prediction interval Γ_{D_n}(X) for τ(X)

1. Split data by treatment:
   D_1 = {(X_i, Y_i) : T_i = 1, i = 1,...,n}  // Treatment group, size n_1
   D_0 = {(X_i, Y_i) : T_i = 0, i = 1,...,n}  // Control group, size n_0

2. For each treatment arm t ∈ {0,1}:
   a. Further split D_t into training D_t^{train} and calibration D_t^{cal} sets
   b. Fit regression model μ̂_t on D_t^{train}
   c. Compute residuals on calibration set: R_i^{(t)} = |Y_i - μ̂_t(X_i)| for (X_i, Y_i) ∈ D_t^{cal}
   d. Compute conformity score quantile: q_t = Quantile(R^{(t)}, (1-α_t)(1 + 1/|D_t^{cal}|))

3. Construct marginal prediction intervals:
   I_t(X) = [μ̂_t(X) - q_t, μ̂_t(X) + q_t] for t ∈ {0,1}

4. Form treatment effect interval using difference of intervals:
   Γ_{D_n}(X) = [L(X), U(X)] where:
   L(X) = μ̂_1(X) - μ̂_0(X) - (q_1 + q_0)
   U(X) = μ̂_1(X) - μ̂_0(X) + (q_1 + q_0)

5. Return Γ_{D_n}(X)
```

### Adaptive Significance Level Selection

The choice of significance levels $α_1$ and $α_0$ for each treatment arm is crucial for controlling the overall coverage. We propose two strategies:

**Strategy 1 (Conservative Union Bound):** Set $α_1 = α_0 = α/2$ to ensure coverage via Bonferroni correction.

**Strategy 2 (Adaptive):** Under conditional independence of errors across treatment arms, set $α_1 = α_0 = 1 - \sqrt{1-α}$, which provides tighter intervals while maintaining coverage.

## Theoretical Properties

**Theorem (Finite-Sample Coverage):** Under Assumptions 1-4, Algorithm 1 with Strategy 1 produces prediction intervals satisfying:
$$\mathbb{P}(\tau(X) \in \Gamma_{D_n}(X)) \geq 1 - α$$
for all $n \geq 2$ and any choice of regression models $μ̂_0, μ̂_1$.

The proof relies on the fact that conformal prediction provides marginal coverage for each potential outcome, and the union bound ensures joint coverage for their difference.

**Theorem (Consistency):** If the regression models $μ̂_t$ are consistent (i.e., $μ̂_t(x) \to \mu_t(x)$ in probability for all $x$), then the interval width converges to the irreducible uncertainty:
$$\text{width}(\Gamma_{D_n}(X)) \to 2 \cdot \text{Quantile}(|Y(1) - \mu_1(X)| + |Y(0) - \mu_0(X)|, 1-α)$$
as $n \to \infty$.

## Design Justifications

**Split-Conformal Approach:** We use split-conformal rather than full-conformal prediction to avoid the computational burden of refitting models for each test point, while maintaining the same finite-sample guarantees.

**Treatment-Stratified Splitting:** By splitting data according to treatment assignment, we ensure that each treatment arm has sufficient calibration data while respecting the missing data structure.

**Additive Interval Construction:** The interval $[μ̂_1(X) - μ̂_0(X) ± (q_1 + q_0)]$ accounts for uncertainty in both potential outcome predictions. This construction is more principled than naively applying conformal prediction to a directly estimated treatment effect function, which would ignore the compound uncertainty structure.

**Model Agnostic Design:** Our method works with any regression algorithm (linear models, random forests, neural networks, etc.) for the outcome models $μ̂_t$, inheriting their flexibility while providing rigorous uncertainty quantification.

## Computational Complexity

The computational complexity is dominated by fitting the two outcome regression models. If each model fitting takes time $O(f(n))$, then the overall algorithm runs in $O(f(n_1) + f(n_0))$ time, where $n_1$ and $n_0$ are the sizes of the treatment and control groups. The conformal calibration step adds only $O(n)$ time for sorting the residuals.

For linear regression, this gives $O(d^3 + nd^2)$ complexity. For more complex models like random forests or neural networks, the complexity scales with the specific algorithm used, but the conformal overhead remains minimal.

The method scales well to large datasets since it requires only a single pass through the data for model fitting and calibration, making it practical for real-world applications.