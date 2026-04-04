# Reconstruction: problem_method
**Paper:** 2602.04770  
**Condition:** no_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Problem Formulation

## Notation and Setup

Let $(\mathcal{X}, \mathcal{Y})$ denote the input and output spaces, where $\mathcal{X} \subseteq \mathbb{R}^d$ and $\mathcal{Y} \subseteq \mathbb{R}$. We observe data $(X_1, Y_1), \ldots, (X_n, Y_n), (X_{n+1}, Y_{n+1})$ drawn i.i.d. from an unknown distribution $P_{XY}$. The first $n$ samples constitute the training set, while $(X_{n+1}, Y_{n+1})$ represents a test point where we seek to construct a prediction interval for $Y_{n+1}$ given $X_{n+1}$.

Let $\hat{\mu}: \mathcal{X} \to \mathbb{R}$ denote a point predictor trained on the first $n$ samples. A **score function** is a mapping $s: \mathcal{X} \times \mathcal{Y} \times \mathcal{F} \to \mathbb{R}$, where $\mathcal{F}$ represents the space of predictive models. For a given score function $s$ and model $\hat{\mu}$, we define the **nonconformity score** of a sample $(x, y)$ as $s(x, y, \hat{\mu})$. Higher scores indicate greater nonconformity between the observation and the model prediction.

For a miscoverage level $\alpha \in (0, 1)$, we aim to construct prediction sets $\mathcal{C}_\alpha(X_{n+1})$ such that $\mathbb{P}(Y_{n+1} \in \mathcal{C}_\alpha(X_{n+1})) \geq 1 - \alpha$.

## Problem Statement

**Given:** 
- Training data $\{(X_i, Y_i)\}_{i=1}^n$ drawn i.i.d. from $P_{XY}$
- Test input $X_{n+1}$ from the same distribution
- Desired coverage level $1 - \alpha$ where $\alpha \in (0, 1)$
- A class of score functions $\mathcal{S} = \{s_\theta : \theta \in \Theta\}$ parameterized by $\theta$

**Find:** A data-driven procedure for selecting $s_{\hat{\theta}} \in \mathcal{S}$ and constructing prediction intervals $\mathcal{C}_\alpha(X_{n+1})$ such that:

1. **Finite-sample marginal coverage guarantee:**
   $$\mathbb{P}(Y_{n+1} \in \mathcal{C}_\alpha(X_{n+1})) \geq 1 - \alpha$$
   for any $n \geq 1$, any distribution $P_{XY}$, and any choice of $\hat{\theta}$

2. **Interval efficiency:** Among all procedures satisfying (1), minimize the expected interval length
   $$\mathbb{E}[|\mathcal{C}_\alpha(X_{n+1})|]$$

## Objective Formulation

The core challenge lies in the **selection-coverage trade-off**: we wish to optimize the score function for efficiency while preserving distribution-free coverage guarantees. Formally, we seek to solve:

$$\min_{\theta \in \Theta} \mathbb{E}[L(s_\theta, X_{n+1}, Y_{n+1})]$$

subject to the constraint that the resulting conformal prediction procedure maintains $\mathbb{P}(Y_{n+1} \in \mathcal{C}_\alpha(X_{n+1})) \geq 1 - \alpha$, where $L(\cdot)$ represents an efficiency loss (e.g., expected interval length).

The fundamental difficulty is that direct optimization of $\theta$ using the training data can invalidate the exchangeability assumption underlying conformal prediction's coverage guarantees.

## Technical Assumptions

**Assumption 1 (Exchangeability):** The augmented sequence $(X_1, Y_1), \ldots, (X_n, Y_n), (X_{n+1}, Y_{n+1})$ is exchangeable.

**Assumption 2 (Score Function Regularity):** Each $s_\theta \in \mathcal{S}$ is measurable, and the parameter space $\Theta$ is equipped with a suitable topology for optimization.

**Assumption 3 (Finite Moments):** For efficiency analysis, we assume $\mathbb{E}[|s_\theta(X, Y, \hat{\mu})|] < \infty$ for all $\theta \in \Theta$.

These assumptions are standard in conformal prediction theory, with Assumption 1 being the minimal requirement for finite-sample coverage guarantees.

## Connection to Prior Work

This formulation extends classical conformal prediction by introducing learnable score functions while preserving the fundamental coverage guarantee. Standard conformal methods use fixed score functions such as $s(x, y, \hat{\mu}) = |y - \hat{\mu}(x)|$ (absolute residual) or $s(x, y, \hat{\mu}) = (y - \hat{\mu}(x))^2$ (squared residual), which may be suboptimal for specific distributions or prediction tasks.

# Methodology

## High-Level Approach

Our proposed method, **Adaptive Conformal Prediction with Cross-Validation (ACP-CV)**, addresses the selection-coverage trade-off through a careful data-splitting strategy. The key insight is to separate the data used for score function learning from the data used for conformal quantile estimation, thereby preserving exchangeability for coverage guarantees while enabling optimization for efficiency.

## Core Algorithm

The algorithm operates in three phases: (1) score function optimization via cross-validation, (2) conformal quantile computation, and (3) prediction interval construction.

### Algorithm 1: ACP-CV

```
Input: Training data {(X_i, Y_i)}_{i=1}^n, test point X_{n+1}, 
       coverage level 1-α, score function class S = {s_θ : θ ∈ Θ}

Phase 1: Score Function Learning
1. Randomly partition {1, 2, ..., n} into K disjoint folds F_1, ..., F_K
2. For each fold k = 1, ..., K:
   a. Train predictor μ̂_k on data {(X_i, Y_i) : i ∉ F_k}
   b. Compute out-of-fold scores: R_i^(k) = s_θ(X_i, Y_i, μ̂_k) for i ∈ F_k
3. Define efficiency loss: L_n(θ) = (1/n) Σ_{i=1}^n ℓ(R_i^(k_i), X_i)
   where k_i is the fold containing index i, and ℓ measures interval width
4. Optimize: θ̂ = argmin_{θ∈Θ} L_n(θ)

Phase 2: Conformal Quantile Estimation  
5. Train final predictor μ̂ on full training data {(X_i, Y_i)}_{i=1}^n
6. Compute conformity scores: R_i = s_{θ̂}(X_i, Y_i, μ̂) for i = 1, ..., n
7. Compute conformal quantile: q̂ = Quantile(R_1, ..., R_n; level = ⌈(n+1)(1-α)⌉/n)

Phase 3: Prediction Interval Construction
8. For test point X_{n+1}, construct prediction set:
   C_α(X_{n+1}) = {y ∈ Y : s_{θ̂}(X_{n+1}, y, μ̂) ≤ q̂}
```

## Key Design Decisions

**Cross-Validation for Score Learning:** The use of K-fold cross-validation in Phase 1 ensures that the scores used for optimizing $\theta$ are computed on data independent of the training set for each fold's predictor. This prevents overfitting of the score function to the specific predictor-data combination.

**Separate Quantile Computation:** Phase 2 computes the conformal quantile using the full training data with the learned score function $s_{\hat{\theta}}$. This separation is crucial: while $\hat{\theta}$ is learned from the data, the quantile computation treats $s_{\hat{\theta}}$ as fixed, preserving the exchangeability required for coverage guarantees.

**Efficiency Loss Design:** The loss function $\ell(r, x)$ in Step 3 should encourage score functions that lead to shorter intervals. For regression with interval predictions, a natural choice is:
$$\ell(r, x) = \mathbb{E}[|\{y : s_{\theta}(x, y, \hat{\mu}) \leq r\}|]$$

## Theoretical Properties

**Theorem 1 (Finite-Sample Coverage):** Under Assumptions 1-3, Algorithm 1 satisfies
$$\mathbb{P}(Y_{n+1} \in \mathcal{C}_\alpha(X_{n+1})) \geq 1 - \alpha$$
for any choice of $\hat{\theta}$, including the optimized value from Step 4.

*Proof Sketch:* The coverage guarantee follows from the standard conformal prediction analysis applied to Phase 2. The key observation is that once $\hat{\theta}$ is fixed (regardless of how it was chosen), the scores $R_1, \ldots, R_n, R_{n+1}$ where $R_{n+1} = s_{\hat{\theta}}(X_{n+1}, Y_{n+1}, \hat{\mu})$ are exchangeable, ensuring the validity of the conformal quantile.

**Theorem 2 (Consistency):** If the score function class $\mathcal{S}$ contains the optimal score function $s^*$ for the given distribution, and the optimization in Step 4 is consistent, then the expected interval length of Algorithm 1 converges to the optimal achievable length as $n \to \infty$.

## Computational Complexity

The computational complexity is dominated by three components:
- **Cross-validation:** $O(K \cdot T_{\text{train}} + n \cdot T_{\text{score}})$ where $T_{\text{train}}$ is the cost of training the predictor and $T_{\text{score}}$ is the cost of computing one score
- **Score optimization:** $O(T_{\text{opt}})$ where $T_{\text{opt}}$ depends on the optimization algorithm and parameter space $\Theta$  
- **Final prediction:** $O(T_{\text{train}} + n \log n)$ for training the final predictor and computing the quantile

For typical choices where score computation is $O(1)$ and standard predictors are used, the overall complexity is $O(K \cdot T_{\text{train}} + T_{\text{opt}} + n \log n)$, which scales reasonably with the data size.
