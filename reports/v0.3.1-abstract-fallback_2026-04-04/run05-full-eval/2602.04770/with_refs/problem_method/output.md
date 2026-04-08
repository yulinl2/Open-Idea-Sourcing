# Reconstruction: problem_method
**Paper:** 2602.04770  
**Condition:** with_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Problem Formulation

## Notation and Setup

Let $\mathcal{X}$ denote the covariate space and $\mathcal{Y}$ the response space. We observe training data $(X_1, Y_1), \ldots, (X_n, Y_n)$ drawn i.i.d. from some unknown distribution $P_{XY}$, and seek to construct prediction intervals for a new test point $X_{n+1}$ with unknown response $Y_{n+1}$, where $(X_{n+1}, Y_{n+1) \sim P_{XY}$.

Let $\hat{\mu}: \mathcal{X} \to \mathcal{Y}$ be a point predictor (e.g., trained regression model). A **score function** $s: \mathcal{X} \times \mathcal{Y} \times \mathcal{F} \to \mathbb{R}$ maps a covariate-response pair and predictor to a real-valued conformity score, where $\mathcal{F}$ is the space of predictors. Lower scores indicate better conformity. Standard choices include:
- Absolute residual: $s(x, y, \hat{\mu}) = |y - \hat{\mu}(x)|$
- Normalized residual: $s(x, y, \hat{\mu}) = |y - \hat{\mu}(x)|/\hat{\sigma}(x)$ for some variance estimate $\hat{\sigma}$

For a given score function $s$ and miscoverage level $\alpha \in (0,1)$, conformal prediction constructs intervals by:
1. Computing conformity scores $S_i = s(X_i, Y_i, \hat{\mu})$ for $i = 1, \ldots, n$
2. Finding the $(1-\alpha)(1 + 1/n)$-quantile: $\hat{q} = \text{Quantile}(\{S_1, \ldots, S_n\}, (1-\alpha)(1 + 1/n))$
3. Defining the prediction set $\hat{C}(X_{n+1}) = \{y \in \mathcal{Y} : s(X_{n+1}, y, \hat{\mu}) \leq \hat{q}\}$

## Problem Statement

**Given:** Training data $\{(X_i, Y_i)\}_{i=1}^n$, miscoverage level $\alpha \in (0,1)$, and a class of score functions $\mathcal{S}$.

**Find:** A data-dependent score function $\hat{s}_n \in \mathcal{S}$ that produces conformal prediction intervals $\hat{C}_{\hat{s}_n}(X_{n+1})$.

**Guarantee:** The intervals must satisfy **finite-sample marginal coverage**:
$$\mathbb{P}(Y_{n+1} \in \hat{C}_{\hat{s}_n}(X_{n+1})) \geq 1 - \alpha$$
for any $n \geq 1$, any distribution $P_{XY}$, and any choice of predictor $\hat{\mu}$, regardless of how $\hat{s}_n$ is selected from $\mathcal{S}$.

## Objective

Among all methods satisfying the coverage guarantee, minimize the expected interval length:
$$\mathbb{E}[\text{Length}(\hat{C}_{\hat{s}_n}(X_{n+1}))]$$
where the expectation is over the training data, test point, and any randomness in the score selection procedure.

## Technical Assumptions

**A1. Exchangeability:** The augmented sequence $(X_1, Y_1), \ldots, (X_n, Y_n), (X_{n+1}, Y_{n+1})$ is exchangeable. This is the standard assumption enabling conformal prediction's finite-sample guarantees.

**A2. Score Function Class:** $\mathcal{S}$ is a collection of measurable score functions. We do not assume $\mathcal{S}$ contains the optimal score function for the true distribution.

**A3. Regularity:** For computational tractability, we may assume $\mathcal{S}$ has finite VC dimension or satisfies other complexity constraints, though this is not required for coverage guarantees.

**A4. Interval Form:** For each $s \in \mathcal{S}$ and test point $x$, the prediction set $\{y : s(x, y, \hat{\mu}) \leq t\}$ forms an interval for sufficiently large $t$. This ensures well-defined interval lengths.

## Connection to Prior Work

This formulation extends the classical conformal prediction framework by introducing **adaptive score selection**. While Tibshirani et al. (2020) address distribution shift through weighted scores with known density ratios, our problem considers the fundamental question of learning the score function itself from data. The key challenge is maintaining the finite-sample coverage guarantee of standard conformal prediction while adaptively choosing scores, which requires careful handling of the data dependence introduced by the learning procedure.

# Methodology

## High-Level Approach

Our approach, **Adaptive Conformal Prediction (ACP)**, uses a data-splitting strategy to learn score functions while preserving finite-sample coverage guarantees. The key insight is to separate the data used for score function learning from the data used for conformal calibration, ensuring that the exchangeability property required for coverage guarantees is maintained.

## Core Algorithm

We employ a three-stage procedure:

1. **Split:** Partition training data into score learning set $\mathcal{D}_{\text{learn}}$ and calibration set $\mathcal{D}_{\text{cal}}$
2. **Learn:** Use $\mathcal{D}_{\text{learn}}$ to select score function $\hat{s}$ from class $\mathcal{S}$
3. **Calibrate:** Use $\mathcal{D}_{\text{cal}}$ with fixed $\hat{s}$ for standard conformal prediction

### Algorithm: Adaptive Conformal Prediction

```
Input: Training data {(X_i, Y_i)}_{i=1}^n, score function class S, 
       miscoverage level α, split ratio γ ∈ (0,1)

1. Randomly partition indices {1,...,n} into:
   - I_learn: |I_learn| = ⌊γn⌋ (score learning)
   - I_cal: |I_cal| = n - ⌊γn⌋ (calibration)

2. Train predictor μ̂ on full dataset {(X_i, Y_i)}_{i=1}^n

3. Score Learning Phase:
   D_learn = {(X_i, Y_i) : i ∈ I_learn}
   ŝ = argmin_{s∈S} L(s, D_learn, μ̂)
   where L is a surrogate loss for interval length

4. Calibration Phase:
   D_cal = {(X_i, Y_i) : i ∈ I_cal}
   For each i ∈ I_cal: compute S_i = ŝ(X_i, Y_i, μ̂)
   q̂ = Quantile({S_i : i ∈ I_cal}, (1-α)(1 + 1/|I_cal|))

5. Prediction:
   For test point X_{n+1}:
   Ĉ(X_{n+1}) = {y ∈ Y : ŝ(X_{n+1}, y, μ̂) ≤ q̂}

Output: Prediction interval Ĉ(X_{n+1})
```

## Score Function Learning

The surrogate loss $L(s, \mathcal{D}_{\text{learn}}, \hat{\mu})$ approximates expected interval length. For regression with interval-valued prediction sets, we use:

$$L(s, \mathcal{D}_{\text{learn}}, \hat{\mu}) = \frac{1}{|\mathcal{D}_{\text{learn}}|} \sum_{(x,y) \in \mathcal{D}_{\text{learn}}} \ell(s(x, y, \hat{\mu}))$$

where $\ell: \mathbb{R} \to \mathbb{R}_+$ is a loss function. Key choices:

**Quantile-based loss:** $\ell(s) = s \cdot (\mathbf{1}\{s \geq \hat{q}_{\alpha}\} - \alpha)$ where $\hat{q}_{\alpha}$ is an estimated $(1-\alpha)$-quantile of scores.

**Cross-validation loss:** Use nested data splitting within $\mathcal{D}_{\text{learn}}$ to estimate interval lengths directly.

## Theoretical Properties

**Theorem 1 (Finite-Sample Coverage):** Under exchangeability (A1), the ACP intervals satisfy
$$\mathbb{P}(Y_{n+1} \in \hat{C}(X_{n+1})) \geq 1 - \alpha$$
regardless of the score function class $\mathcal{S}$, the choice of $\hat{s}$, or the performance of the learning procedure.

**Proof Sketch:** The coverage guarantee follows from the exchangeability of $(X_i, Y_i)_{i \in I_{\text{cal}}} \cup \{(X_{n+1}, Y_{n+1})\}$ and the fact that $\hat{s}$ is determined independently of $\mathcal{D}_{\text{cal}}$. Standard conformal prediction theory applies to the calibration phase.

**Theorem 2 (Consistency):** If $\mathcal{S}$ contains score functions with finite expected interval length under the true distribution, and the empirical loss converges uniformly over $\mathcal{S}$, then ACP intervals achieve asymptotically optimal length as $n \to \infty$.

## Design Justifications

**Data Splitting:** Inspired by the weighted conformal prediction approach of Tibshirani et al. (2020), we use separation of concerns—learning and calibration use disjoint data to maintain exchangeability. This is crucial for preserving finite-sample guarantees.

**Surrogate Loss Design:** Direct optimization of interval length is computationally challenging since it requires solving conformal prediction for each candidate score function. Our surrogate losses provide tractable approximations while maintaining the ranking of score functions.

**Split Ratio Selection:** The choice of $\gamma$ trades off between score learning accuracy (larger $\gamma$) and calibration stability (smaller $\gamma$). Cross-validation can be used to select $\gamma$ in practice.

## Computational Complexity

The computational cost is $O(T \cdot C_s + n \log n)$ where:
- $T$ is the cost of optimizing over $\mathcal{S}$ (depends on parameterization)
- $C_s$ is the cost of evaluating the surrogate loss
- $n \log n$ accounts for quantile computation in calibration

For parametric score function classes (e.g., neural networks), $T$ scales with the optimization procedure. The method is practical for moderate-sized datasets and score function classes.
