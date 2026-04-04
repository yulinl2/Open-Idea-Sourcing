# Reconstruction: problem_method
**Paper:** 2602.04770  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Problem Formulation

## Notation and Setup

Let $\mathcal{X}$ denote the input space and $\mathcal{Y} \subseteq \mathbb{R}$ the output space. We observe training data $\{(X_1, Y_1), \ldots, (X_n, Y_n)\}$ drawn i.i.d. from an unknown distribution $P_{XY}$, and wish to construct prediction intervals for a new test point $(X_{n+1}, Y_{n+1})$ drawn from the same distribution.

Let $\hat{\mu}: \mathcal{X} \rightarrow \mathbb{R}$ denote a fitted regression function (e.g., neural network, random forest) trained on the data. A conformal score function is defined as $s: \mathcal{X} \times \mathcal{Y} \times \mathcal{F} \rightarrow \mathbb{R}$, where $\mathcal{F}$ is the space of fitted models, such that $s(x, y, \hat{\mu})$ measures the "non-conformity" or unusualness of observing output $y$ given input $x$ and model $\hat{\mu}$.

For a miscoverage level $\alpha \in (0,1)$, the conformal prediction interval at level $1-\alpha$ is constructed as:
$$C_{\alpha}(X_{n+1}) = \{y \in \mathcal{Y} : s(X_{n+1}, y, \hat{\mu}) \leq \hat{q}_{1-\alpha}\}$$
where $\hat{q}_{1-\alpha}$ is the $(1-\alpha)(1 + 1/n)$-th empirical quantile of the conformity scores $\{s(X_i, Y_i, \hat{\mu})\}_{i=1}^n$.

## Problem Statement

**Given:** 
- Training data $\{(X_i, Y_i)\}_{i=1}^n$ drawn i.i.d. from $P_{XY}$
- A fitted regression function $\hat{\mu}$
- Miscoverage level $\alpha \in (0,1)$
- A parametric family of score functions $\mathcal{S}_\theta = \{s_\theta : \theta \in \Theta\}$

**Find:** A score function $s_{\hat{\theta}} \in \mathcal{S}_\theta$ that minimizes expected interval length while maintaining finite-sample marginal coverage guarantees.

**Guarantee:** The resulting prediction intervals must satisfy:
$$\mathbb{P}(Y_{n+1} \in C_{\alpha}(X_{n+1})) \geq 1 - \alpha$$
for any finite sample size $n$ and any underlying distribution $P_{XY}$.

## Objective

We seek to solve the constrained optimization problem:
$$\min_{\theta \in \Theta} \mathbb{E}[\text{length}(C_{\alpha}^{(\theta)}(X_{n+1}))]$$
subject to the finite-sample coverage constraint:
$$\mathbb{P}(Y_{n+1} \in C_{\alpha}^{(\theta)}(X_{n+1})) \geq 1 - \alpha$$

where $C_{\alpha}^{(\theta)}(x)$ denotes the conformal interval constructed using score function $s_\theta$.

## Technical Assumptions

**A1 (Exchangeability):** The augmented sequence $(X_1, Y_1), \ldots, (X_n, Y_n), (X_{n+1}, Y_{n+1})$ is exchangeable.

**A2 (Score Function Properties):** For each $\theta \in \Theta$, the score function $s_\theta(x, y, \hat{\mu})$ is measurable and satisfies the monotonicity property: for fixed $x$ and $\hat{\mu}$, the set $\{y : s_\theta(x, y, \hat{\mu}) \leq t\}$ is an interval for all $t \in \mathbb{R}$.

**A3 (Parametric Regularity):** The parameter space $\Theta$ is compact, and $s_\theta(x, y, \hat{\mu})$ is continuous in $\theta$ for all $(x, y, \hat{\mu})$.

**A4 (Model Independence):** The choice of score function parameters $\theta$ is independent of the fitted model $\hat{\mu}$ to preserve the validity of conformal prediction.

These assumptions are justified as follows: A1 ensures the fundamental validity of conformal prediction as established in the foundational literature. A2 guarantees that the conformal sets are intervals rather than arbitrary sets, which is essential for interpretability and efficiency. A3 provides the regularity needed for optimization and theoretical analysis. A4 prevents overfitting to the specific model, maintaining the distribution-free nature of conformal prediction.

# Methodology

## High-Level Approach

Our approach, termed **Adaptive Conformal Score Learning (ACSL)**, learns optimal score function parameters through a novel two-stage procedure that preserves finite-sample coverage guarantees. The key insight is to use a data-splitting strategy where we learn score function parameters on one portion of the data and construct conformal intervals on the remaining portion, ensuring that the coverage guarantees remain valid.

## Core Algorithm

We propose a parametric family of adaptive score functions:
$$s_\theta(x, y, \hat{\mu}) = |y - \hat{\mu}(x)| \cdot w_\theta(x, \hat{\mu}(x))$$

where $w_\theta: \mathcal{X} \times \mathbb{R} \rightarrow \mathbb{R}_{+}$ is a learned weighting function that adapts the conformity score based on local properties of the input and predicted output. We parameterize $w_\theta$ as:
$$w_\theta(x, \hat{\mu}(x)) = \exp(\theta^T \phi(x, \hat{\mu}(x)))$$

where $\phi(x, \hat{\mu}(x)) \in \mathbb{R}^d$ is a feature vector capturing relevant characteristics such as prediction uncertainty estimates, local density, and model-specific features.

### Algorithm: Adaptive Conformal Score Learning

```
Input: Training data {(Xi, Yi)}_{i=1}^n, fitted model μ̂, miscoverage α
Output: Learned score function s_θ̂, prediction interval function C_α

1. Data Splitting:
   - Randomly partition indices {1,...,n} into I₁ and I₂ with |I₁| = ⌊n/2⌋
   - Set D₁ = {(Xi, Yi) : i ∈ I₁}, D₂ = {(Xi, Yi) : i ∈ I₂}

2. Score Function Learning:
   - Initialize θ₀ ∈ Θ
   - For t = 1, 2, ..., T:
     a. Compute conformity scores: Si^(t) = s_θₜ(Xi, Yi, μ̂) for i ∈ I₁
     b. Compute quantile: q₁₋α^(t) = empirical (1-α)(1 + 1/|I₁|)-quantile of {Si^(t)}
     c. Estimate interval lengths: Li^(t) = 2 · q₁₋α^(t) / w_θₜ(Xi, μ̂(Xi)) for i ∈ I₁
     d. Update: θₜ₊₁ = θₜ - η∇θ(1/|I₁| ∑_{i∈I₁} Li^(t))
   - Set θ̂ = θₜ

3. Conformal Interval Construction:
   - Compute final conformity scores: Si = s_θ̂(Xi, Yi, μ̂) for i ∈ I₂
   - Compute final quantile: q̂₁₋α = empirical (1-α)(1 + 1/|I₂|)-quantile of {Si}
   - Return prediction interval: C_α(x) = {y : s_θ̂(x, y, μ̂) ≤ q̂₁₋α}
```

## Key Design Decisions

**Data Splitting Strategy:** Following the approach in Tibshirani et al. (2020), we employ data splitting to maintain the exchangeability required for conformal prediction validity. The first split learns the score function parameters, while the second split constructs the final conformal intervals with valid coverage guarantees.

**Multiplicative Score Structure:** The multiplicative form $|y - \hat{\mu}(x)| \cdot w_\theta(x, \hat{\mu}(x))$ preserves the essential structure of absolute residual-based scores while allowing adaptive weighting. This ensures that the resulting conformal sets remain intervals.

**Exponential Parameterization:** The exponential parameterization of $w_\theta$ ensures positivity and provides a natural log-linear structure that is amenable to gradient-based optimization.

**Feature Engineering:** The feature vector $\phi(x, \hat{\mu}(x))$ should capture factors that influence prediction uncertainty, such as:
- Local data density estimates
- Model-specific uncertainty measures (e.g., ensemble variance)
- Distance to training data
- Gradient norms or other complexity measures

## Theoretical Properties

**Theorem 1 (Finite-Sample Coverage):** Under assumptions A1-A4, the prediction intervals produced by ACSL satisfy:
$$\mathbb{P}(Y_{n+1} \in C_{\alpha}(X_{n+1})) \geq 1 - \alpha$$
for any finite sample size $n$.

**Proof Sketch:** The validity follows from the data-splitting strategy. Since the score function parameters $\hat{\theta}$ are learned only on $D_1$, the exchangeability of $(X_i, Y_i)_{i \in I_2} \cup \{(X_{n+1}, Y_{n+1})\}$ is preserved, ensuring standard conformal prediction guarantees apply to the second stage.

**Theorem 2 (Consistency):** Under additional regularity conditions, as $n \rightarrow \infty$, the learned score function converges to the population minimizer of expected interval length subject to the coverage constraint.

## Computational Complexity

The algorithm has computational complexity $O(T \cdot n \cdot d + n \log n)$ where $T$ is the number of optimization iterations and $d$ is the feature dimension. The dominant terms are:
- Score function evaluation: $O(T \cdot n \cdot d)$ 
- Quantile computation: $O(n \log n)$ per iteration
- Gradient computation: $O(T \cdot n \cdot d)$

This complexity is comparable to standard conformal prediction methods with the additional overhead of learning the score function parameters, making it practical for real-world applications.
