# Reconstruction: problem
**Paper:** 2602.04770  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Problem Formulation

## Setup and Notation

Let $\mathcal{X}$ denote the input space and $\mathcal{Y}$ denote the output space, where we consider the regression setting with $\mathcal{Y} \subseteq \mathbb{R}$. We observe a training dataset $\mathcal{D}_n = \{(X_1, Y_1), \ldots, (X_n, Y_n)\}$ of $n$ i.i.d. samples drawn from an unknown distribution $P$ over $\mathcal{X} \times \mathcal{Y}$. Given a new test point $X_{n+1}$, our goal is to construct a prediction interval $\mathcal{C}(X_{n+1}) \subseteq \mathcal{Y}$ for the unobserved response $Y_{n+1}$.

Let $\hat{\mu}: \mathcal{X} \to \mathbb{R}$ denote a point predictor trained on $\mathcal{D}_n$. A **score function** $s: \mathcal{X} \times \mathcal{Y} \times \mathcal{H} \to \mathbb{R}$ maps input-output pairs and model parameters to real-valued conformity scores, where $\mathcal{H}$ represents the space of possible models or parameters. Lower scores indicate better conformity between the prediction and the true value.

For a given score function $s$ and miscoverage level $\alpha \in (0,1)$, the **conformal prediction interval** is constructed as:
$$\mathcal{C}_\alpha(x) = \{y \in \mathcal{Y} : s(x, y, \hat{\mu}) \leq \hat{q}_{1-\alpha}\}$$
where $\hat{q}_{1-\alpha}$ is the $(1-\alpha)$-quantile of the conformity scores on the training data:
$$\hat{q}_{1-\alpha} = \text{Quantile}_{1-\alpha}\{s(X_i, Y_i, \hat{\mu}) : i = 1, \ldots, n\}$$

## Problem Statement

The central challenge is to learn an optimal score function $s^*$ from data that produces prediction intervals with two essential properties:

**Coverage Guarantee**: For any finite sample size $n$ and any underlying distribution $P$, the prediction intervals must satisfy finite-sample marginal coverage:
$$\mathbb{P}(Y_{n+1} \in \mathcal{C}_\alpha(X_{n+1})) \geq 1 - \alpha$$

**Efficiency**: Among all score functions satisfying the coverage guarantee, $s^*$ should minimize the expected interval length:
$$s^* \in \arg\min_{s \in \mathcal{S}} \mathbb{E}[|\mathcal{C}_\alpha^s(X_{n+1})|]$$
where $\mathcal{S}$ denotes the class of admissible score functions and $|\cdot|$ denotes interval length.

## Optimization Objective

We formalize the learning problem as finding a score function $s_\theta$ parameterized by $\theta \in \Theta$ that minimizes expected interval length while maintaining coverage validity. The objective can be written as:

$$\min_{\theta \in \Theta} \mathbb{E}_{(X,Y) \sim P}[|\mathcal{C}_\alpha^{\theta}(X)|] \quad \text{subject to} \quad \mathbb{P}(Y \in \mathcal{C}_\alpha^{\theta}(X)) \geq 1 - \alpha$$

Since the true distribution $P$ is unknown, we approximate this using the empirical distribution. However, the constraint must be enforced in a way that preserves the finite-sample coverage guarantees that make conformal prediction theoretically attractive.

A key challenge is that directly optimizing interval length on the training data can lead to overfitting and coverage violations. We require a learning framework that respects the conformal prediction structure while allowing data-driven adaptation of the score function.

## Technical Assumptions

We make the following assumptions:

**A1 (Exchangeability)**: The augmented sequence $(X_1, Y_1), \ldots, (X_n, Y_n), (X_{n+1}, Y_{n+1})$ is exchangeable. This is the standard assumption required for conformal prediction validity and is weaker than independence.

**A2 (Score Function Class)**: The parameterized score functions $\{s_\theta : \theta \in \Theta\}$ form a well-behaved function class with sufficient regularity for optimization. Specifically, we assume $\Theta$ is compact and $s_\theta$ is continuous in $\theta$.

**A3 (Monotonicity)**: For each fixed $(x, \hat{\mu})$, the score function $s_\theta(x, y, \hat{\mu})$ satisfies appropriate monotonicity or unimodality conditions in $y$ to ensure that the resulting prediction sets $\mathcal{C}_\alpha^{\theta}(x)$ are intervals.

**A4 (Finite Moments)**: The distribution $P$ has finite second moments to ensure well-defined optimization objectives and concentration properties.

These assumptions are minimal and standard in the conformal prediction literature, ensuring our formulation maintains the distribution-free nature that makes conformal methods broadly applicable.

## Connection to Prior Work

Classical conformal prediction \cite{vovk2005algorithmic} uses fixed score functions such as $s(x, y, \hat{\mu}) = |y - \hat{\mu}(x)|$ for regression. While these provide valid coverage, they may be suboptimal in terms of interval efficiency. The work of Tibshirani et al. \cite{arxiv-1904.06019} addresses distribution shift but still relies on pre-specified score functions.

Recent advances have explored adaptive conformal methods that adjust the quantile level based on past performance, but these do not fundamentally change the score function itself. Our formulation addresses a more fundamental question: rather than fixing the score function a priori, can we learn it from data while preserving the finite-sample validity that distinguishes conformal prediction from asymptotic methods?

The key innovation in our problem formulation is maintaining the non-asymptotic coverage guarantees of conformal prediction while introducing adaptivity in the score function. This requires careful treatment of the learning-theoretic aspects to avoid the pitfalls of data snooping that could invalidate the coverage properties.
