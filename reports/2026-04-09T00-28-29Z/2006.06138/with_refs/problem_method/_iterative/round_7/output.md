# Problem Formulation

## Notation and Setup

Let $(X_i, Y_i(1), Y_i(0))_{i=1}^n$ denote $n$ independent units, where $X_i \in \mathcal{X} \subseteq \mathbb{R}^d$ represents covariates and $Y_i(t) \in \mathbb{R}$ denotes the potential outcome under treatment $t \in \{0,1\}$ for unit $i$. The individual treatment effect for unit $i$ is $\tau_i = Y_i(1) - Y_i(0)$.

Let $T_i \in \{0,1\}$ denote the treatment assignment for unit $i$, and define the observed outcome as $Y_i = T_i Y_i(1) + (1-T_i) Y_i(0)$. Due to the fundamental problem of causal inference, we observe $(X_i, Y_i, T_i)$ but never both potential outcomes simultaneously.

For a new unit with covariates $X_{n+1}$, we aim to construct prediction intervals for the unobserved individual treatment effect $\tau_{n+1} = Y_{n+1}(1) - Y_{n+1}(0)$.

Let $\pi(x) = \mathbb{P}(T = 1 | X = x)$ denote the propensity score function, and assume $0 < \pi(x) < 1$ for all $x \in \mathcal{X}$ (overlap condition). The treatment assignment mechanism creates systematic covariate imbalance: the distribution of $X$ among treated units differs from that among control units, and both may differ from the target population distribution.

## Formal Problem Statement

**Given:** Training data $\mathcal{D}_n = \{(X_i, Y_i, T_i)\}_{i=1}^n$ and a new unit with covariates $X_{n+1}$.

**Find:** A prediction interval $\mathcal{C}_n(X_{n+1}) = [L_n(X_{n+1}), U_n(X_{n+1})]$ for the individual treatment effect $\tau_{n+1}$.

**Guarantee:** For a given confidence level $1-\alpha \in (0,1)$, ensure
$$\mathbb{P}(\tau_{n+1} \in \mathcal{C}_n(X_{n+1})) \geq 1-\alpha$$
where the probability is taken over the randomness in both the training data and the new unit.

## Objective

We seek to construct a procedure that provides valid uncertainty quantification for individual treatment effects by addressing three fundamental challenges:

1. **Unobservability constraint:** Each potential outcome $Y_{n+1}(t)$ can only be calibrated using data from units that actually received treatment $t$.

2. **Covariate shift correction:** The distributions of covariates in treated and control groups differ systematically due to the treatment assignment mechanism, requiring reweighting to achieve valid inference.

3. **Finite-sample validity:** The procedure should provide exact coverage guarantees without relying on asymptotic approximations or strong parametric assumptions.

## Technical Assumptions

**Assumption 1 (Exchangeability within treatment groups):** For each $t \in \{0,1\}$, the units $\{(X_i, Y_i(t)) : T_i = t\} \cup \{(X_{n+1}, Y_{n+1}(t))\}$ are exchangeable conditional on the treatment assignment pattern.

**Assumption 2 (Known propensity scores):** The propensity score function $\pi(x)$ is known or can be estimated with sufficient accuracy. In randomized experiments, $\pi(x)$ is determined by the experimental design.

**Assumption 3 (Overlap):** $0 < \pi(x) < 1$ for all $x \in \mathcal{X}$, ensuring that both treatment and control observations exist across the covariate space.

**Assumption 4 (SUTVA):** The Stable Unit Treatment Value Assumption holds: there are no interference effects between units and treatment is well-defined.

These assumptions are standard in causal inference and significantly weaker than typical requirements for uncertainty quantification methods, which often assume Gaussianity, homoskedasticity, or parametric model correctness.

## Connection to Prior Work

Our formulation extends conformal prediction methodology beyond the standard exchangeable setting. The key insight from Tibshirani et al. (2020) is that weighted conformal prediction can handle covariate shift when the likelihood ratio between test and training distributions is known. In our setting, the propensity score mechanism creates a specific pattern of covariate shift where:
- Treated units have covariate distribution proportional to $\pi(x) \cdot p(x)$
- Control units have covariate distribution proportional to $(1-\pi(x)) \cdot p(x)$
- The target population has covariate distribution $p(x)$

The work of Kivaranovic et al. (2020) addresses individual treatment effects but requires constructing separate prediction intervals for each potential outcome and combining them, leading to conservative intervals. Our approach leverages the mathematical structure of the treatment assignment mechanism to achieve tighter, more principled uncertainty quantification.

The fundamental insight is that the same propensity score mechanism that creates the covariate imbalance problem also provides the reweighting scheme needed to correct for it, enabling valid finite-sample inference for individual treatment effects under covariate shift.

# Methodology

## High-Level Approach

Our methodology constructs prediction intervals for individual treatment effects by combining weighted conformal prediction with propensity score reweighting. The core insight is to treat each potential outcome separately, using only data from the corresponding treatment group, while correcting for covariate distribution differences through importance weighting.

The approach consists of three main components:
1. **Separate calibration:** Construct prediction intervals for $Y_{n+1}(1)$ using only treated units and for $Y_{n+1}(0)$ using only control units
2. **Propensity score reweighting:** Weight observations to match the target population distribution
3. **Interval combination:** Combine the individual potential outcome intervals to form intervals for the treatment effect

## Core Algorithm

### Weighted Conformal Prediction for Potential Outcomes

For each treatment level $t \in \{0,1\}$, we construct weighted conformal prediction intervals. Let $\mathcal{I}_t = \{i : T_i = t\}$ denote the indices of units receiving treatment $t$, with $|\mathcal{I}_t| = n_t$.

**Step 1: Define nonconformity scores**
For a given score function $S: \mathbb{R}^d \times \mathbb{R} \times \mathcal{D} \to \mathbb{R}$, compute:
$$V_i^{(t)}(x,y) = S((x,y), \{(X_j, Y_j) : j \in \mathcal{I}_t \setminus \{i\}\})$$
for $i \in \mathcal{I}_t$, and
$$V_{n+1}^{(t)}(x,y) = S((x,y), \{(X_j, Y_j) : j \in \mathcal{I}_t\})$$

**Step 2: Compute importance weights**
Define the importance weights that rebalance from the treatment-specific distribution to the target population:
$$w_i^{(t)}(x) = \begin{cases}
\frac{1}{\pi(X_i)} & \text{if } t = 1 \\
\frac{1}{1-\pi(X_i)} & \text{if } t = 0
\end{cases}$$

The normalized weights are:
$$\tilde{w}_i^{(t)}(x) = \frac{w_i^{(t)}(x)}{\sum_{j \in \mathcal{I}_t} w_j^{(t)}(x) + w_{n+1}^{(t)}(x)}, \quad i \in \mathcal{I}_t$$
$$\tilde{w}_{n+1}^{(t)}(x) = \frac{w_{n+1}^{(t)}(x)}{\sum_{j \in \mathcal{I}_t} w_j^{(t)}(x) + w_{n+1}^{(t)}(x)}$$

**Step 3: Construct weighted prediction intervals**
The prediction interval for $Y_{n+1}(t)$ at level $1-\alpha_t$ is:
$$\mathcal{C}_n^{(t)}(x) = \left\{y \in \mathbb{R} : V_{n+1}^{(t)}(x,y) \leq \text{Quantile}\left(1-\alpha_t; \sum_{i \in \mathcal{I}_t} \tilde{w}_i^{(t)}(x) \delta_{V_i^{(t)}(x,y)} + \tilde{w}_{n+1}^{(t)}(x) \delta_{\infty}\right)\right\}$$

### Complete Algorithm

```
Algorithm: Weighted Conformal Prediction for Individual Treatment Effects

Input: Training data D_n = {(X_i, Y_i, T_i)}_{i=1}^n
       New covariate X_{n+1}
       Confidence level 1-α
       Score function S
       Propensity score function π

1. Partition data by treatment:
   I_1 = {i : T_i = 1}, I_0 = {i : T_i = 0}

2. For each treatment level t ∈ {0,1}:
   a. Set confidence level α_t according to combination rule:
      - Conservative: α_t = α/2 (Bonferroni correction)
      - Optimized: α_t based on error correlation structure
   
   b. Compute nonconformity scores:
      For i ∈ I_t:
        V_i^{(t)}(X_{n+1}, y) = S((X_{n+1}, y), {(X_j, Y_j) : j ∈ I_t \ {i}})
      
      V_{n+1}^{(t)}(X_{n+1}, y) = S((X_{n+1}, y), {(X_j, Y_j) : j ∈ I_t})
   
   c. Compute importance weights:
      w_i^{(t)}(X_{n+1}) = 1/π(X_i) if t=1, 1/(1-π(X_i)) if t=0
      Normalize: w̃_i^{(t)} = w_i^{(t)} / (Σ_j w_j^{(t)} + w_{n+1}^{(t)})
   
   d. Construct prediction interval:
      C_n^{(t)}(X_{n+1}) = {y : V_{n+1}^{(t)}(X_{n+1}, y) ≤ 
                           Quantile(1-α_t, Σ_i w̃_i^{(t)} δ_{V_i^{(t)}} + w̃_{n+1}^{(t)} δ_∞)}

3. Combine intervals for treatment effect:
   Let C_n^{(1)}(X_{n+1}) = [L_1, U_1] and C_n^{(0)}(X_{n+1}) = [L_0, U_0]
   
   Return: C_n(X_{n+1}) = [L_1 - U_0, U_1 - L_0]
```

## Design Justifications

**Separate treatment-specific calibration:** This design respects the fundamental constraint that we can only use treated units to calibrate intervals for treated potential outcomes, and control units for control potential outcomes. This avoids the bias that would arise from using the wrong reference distribution.

**Propensity score reweighting:** The importance weights $w_i^{(t)}(x) = 1/\mathbb{P}(T_i = t | X_i)$ correct for the selection bias introduced by the treatment assignment mechanism. This reweighting makes the calibration set representative of the target population rather than the treatment-specific subpopulation.

**Weighted quantile computation:** Following Tibshirani et al. (2020), we use weighted empirical distributions to compute quantiles. This preserves the exchangeability property needed for valid conformal prediction while accounting for covariate shift.

## Theoretical Properties

**Theorem (Finite-sample coverage):** Under Assumptions 1-4, if we set $\alpha_0 = \alpha_1 = \alpha/2$, then
$$\mathbb{P}(\tau_{n+1} \in \mathcal{C}_n(X_{n+1})) \geq 1-\alpha$$

**Proof sketch:** The result follows by applying weighted conformal prediction (Corollary 1 from Tibshirani et al.) to each treatment group separately, then using the union bound for interval combination. The propensity score weights ensure that the weighted empirical distributions match the target population, restoring exchangeability.

**Optimized combination:** Under additional assumptions about the correlation structure of potential outcome errors, tighter intervals can be achieved by choosing $\alpha_t$ values that account for the dependence between $Y_{n+1}(1)$ and $Y_{n+1}(0)$.

## Computational Complexity

The algorithm has computational complexity $O(n \cdot |\mathcal{Y}|)$ where $|\mathcal{Y}|$ is the discretization of the outcome space for interval construction. For split conformal prediction with pre-fitted models, this reduces to $O(n)$ as the score computation becomes a simple residual calculation.

The propensity score computation adds $O(n)$ overhead, and the weighted quantile computation requires $O(n \log n)$ operations. Overall complexity remains linear in sample size for practical implementations.