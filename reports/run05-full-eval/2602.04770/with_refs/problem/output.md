# Reconstruction: problem
**Paper:** 2602.04770  
**Condition:** with_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Problem Formulation

## 2.1 Notation and Setup

Let $\mathcal{X} \subseteq \mathbb{R}^d$ denote the covariate space and $\mathcal{Y} \subseteq \mathbb{R}$ the response space. We observe training data $\{(X_i, Y_i)\}_{i=1}^n$ drawn i.i.d. from an unknown distribution $P_{XY}$ on $\mathcal{X} \times \mathcal{Y}$. Given a new test point $X_{n+1}$ drawn from the same distribution, our goal is to construct a prediction interval $C(X_{n+1}) \subseteq \mathcal{Y}$ that contains the unobserved response $Y_{n+1}$ with high probability.

Let $\hat{\mu}: \mathcal{X} \to \mathbb{R}$ denote a point predictor trained on the data, and let $s: \mathcal{X} \times \mathcal{Y} \times \mathcal{F} \to \mathbb{R}_+$ be a conformity score function parameterized by $\theta \in \mathcal{F}$, where $\mathcal{F}$ represents a function class. The score $s(x, y; \theta)$ measures how "non-conforming" the pair $(x, y)$ is relative to the training data, with larger values indicating greater non-conformity.

Standard conformal prediction constructs intervals using a fixed score function, typically $s(x, y) = |y - \hat{\mu}(x)|$. For a miscoverage level $\alpha \in (0, 1)$, the conformal quantile is defined as:
$$\hat{q}_{1-\alpha} = \text{Quantile}\left(\frac{\lceil (n+1)(1-\alpha) \rceil}{n+1}, \{s(X_i, Y_i)\}_{i=1}^n\right)$$

The resulting prediction interval is $C(X_{n+1}) = \{y \in \mathcal{Y} : s(X_{n+1}, y) \leq \hat{q}_{1-\alpha}\}$.

## 2.2 Problem Statement

We seek to learn an optimal score function $s^*(\cdot, \cdot; \theta^*)$ from the training data while preserving conformal prediction's finite-sample coverage guarantees. Formally, given training data $\{(X_i, Y_i)\}_{i=1}^n$ and miscoverage level $\alpha$, we aim to find:

**Given:** 
- Training sample $\{(X_i, Y_i)\}_{i=1}^n \sim P_{XY}^n$
- Function class $\mathcal{F}$ for score functions
- Miscoverage level $\alpha \in (0, 1)$

**Find:** A data-dependent score function $\hat{s}(\cdot, \cdot; \hat{\theta})$ where $\hat{\theta} = \hat{\theta}(\{(X_i, Y_i)\}_{i=1}^n)$

**Such that:** The resulting conformal prediction intervals satisfy both:

1. **Finite-sample marginal coverage:** For any distribution $P_{XY}$ and any $n \geq 1$,
   $$\mathbb{P}(Y_{n+1} \in C(X_{n+1})) \geq 1 - \alpha$$

2. **Interval efficiency:** Among all procedures satisfying (1), minimize the expected interval length
   $$\mathbb{E}[|C(X_{n+1})|]$$

## 2.3 Optimization Objective

The core challenge lies in balancing two competing objectives. We seek to solve:
$$\min_{\theta \in \mathcal{F}} \mathbb{E}_{(X,Y) \sim P_{XY}}[\ell(s(X, Y; \theta))]$$
where $\ell$ is a loss function that encourages shorter prediction intervals, subject to the constraint that the finite-sample coverage guarantee remains valid.

A natural choice for $\ell$ would encourage the score function to produce tight quantiles, such as:
$$\ell(s(x, y; \theta)) = \mathbb{E}_{Y' \sim P_{Y|X=x}}[\mathbf{1}\{s(x, Y'; \theta) \leq s(x, y; \theta)\}]$$
which measures the conditional coverage probability. However, optimizing this directly may violate the marginal coverage guarantee.

## 2.4 Technical Assumptions

We require the following assumptions:

**A1. Exchangeability:** The augmented sequence $(X_1, Y_1), \ldots, (X_n, Y_n), (X_{n+1}, Y_{n+1})$ is exchangeable. This is the standard assumption enabling conformal prediction's validity guarantees.

**A2. Measurability:** The function class $\mathcal{F}$ consists of measurable functions, and the learning procedure $\hat{\theta}(\cdot)$ is measurable with respect to the training data.

**A3. Score function properties:** For each $\theta \in \mathcal{F}$ and $x \in \mathcal{X}$, the function $y \mapsto s(x, y; \theta)$ is continuous, enabling well-defined level sets for interval construction.

**A4. Bounded complexity:** The function class $\mathcal{F}$ has appropriate complexity constraints (e.g., finite VC dimension, Rademacher complexity bounds) to ensure statistical learnability.

Assumption A1 is fundamental to conformal prediction and cannot be relaxed without additional techniques such as those in Tibshirani et al. (2020). Assumptions A2-A3 ensure technical well-posedness, while A4 is necessary for any learning-theoretic guarantees on the optimization objective.

## 2.5 Connection to Prior Work

Existing conformal prediction methods \cite{vovk2005} achieve finite-sample coverage using fixed score functions, most commonly absolute residuals $s(x, y) = |y - \hat{\mu}(x)|$. While these provide the desired coverage guarantees, they are not adapted to the underlying data distribution and may produce unnecessarily wide intervals.

Recent extensions have addressed distributional robustness \cite{tibshirani2020conformal} and improved conditional coverage, but have not tackled the fundamental question of learning optimal score functions. The key insight missing from prior work is how to maintain the non-asymptotic, assumption-free coverage guarantees of conformal prediction while allowing the score function itself to be learned from data.

Our formulation bridges this gap by requiring that coverage guarantees hold regardless of how well the learning procedure performs, thus preserving conformal prediction's key advantage while potentially improving efficiency through data-adaptive scoring.
