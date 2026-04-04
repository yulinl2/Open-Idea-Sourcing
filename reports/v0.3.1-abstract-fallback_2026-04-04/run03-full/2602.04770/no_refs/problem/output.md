# Reconstruction: problem
**Paper:** 2602.04770  
**Condition:** no_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Problem Formulation

## Notation and Setup

Let $\mathcal{X}$ denote the input space and $\mathcal{Y} \subseteq \mathbb{R}$ the output space. We observe an exchangeable sequence of training examples $(X_1, Y_1), \ldots, (X_n, Y_n)$ drawn from an unknown distribution $P_{X,Y}$, and seek to construct prediction intervals for a new test point $X_{n+1}$ with corresponding unobserved outcome $Y_{n+1}$, where $(X_{n+1}, Y_{n+1})$ is exchangeable with the training data.

Let $\hat{\mu}: \mathcal{X} \to \mathbb{R}$ denote a point predictor trained on the data, which may be any regression function (e.g., neural network, random forest, linear model). For a target miscoverage level $\alpha \in (0,1)$, our goal is to construct prediction intervals $\mathcal{C}_\alpha(X_{n+1}) \subseteq \mathbb{R}$ such that
$$\mathbb{P}(Y_{n+1} \in \mathcal{C}_\alpha(X_{n+1})) \geq 1 - \alpha$$
with finite-sample validity.

## Conformal Prediction Framework

Following the conformal prediction paradigm, we construct intervals using a *score function* $s: \mathcal{X} \times \mathbb{R} \to \mathbb{R}$, which measures the "strangeness" or "non-conformity" of observing outcome $y$ given input $x$. For each training example, we compute the score $s(X_i, Y_i)$ for $i = 1, \ldots, n$.

The conformal prediction procedure works as follows:
1. Compute scores $S_i = s(X_i, Y_i)$ for all training examples
2. For a candidate prediction $y$ at test point $X_{n+1}$, compute $s(X_{n+1}, y)$
3. Define the prediction set as
   $$\mathcal{C}_\alpha(X_{n+1}) = \{y \in \mathcal{Y} : s(X_{n+1}, y) \leq \hat{Q}_{1-\alpha}(\{S_1, \ldots, S_n, s(X_{n+1}, y)\})\}$$
   where $\hat{Q}_{1-\alpha}(\cdot)$ denotes the $(1-\alpha)$-quantile of the augmented score set.

This construction guarantees that $\mathbb{P}(Y_{n+1} \in \mathcal{C}_\alpha(X_{n+1})) \geq 1 - \alpha$ for any choice of score function $s$, under the sole assumption of exchangeability.

## Problem Statement

The central challenge lies in the choice of score function $s$. While any score function yields valid coverage, the *efficiency* of the resulting prediction intervals—measured by their expected width—depends critically on this choice. Formally, we seek to solve:

$$\min_{s \in \mathcal{S}} \mathbb{E}[|\mathcal{C}_\alpha(X_{n+1})|]$$

subject to the coverage constraint
$$\mathbb{P}(Y_{n+1} \in \mathcal{C}_\alpha(X_{n+1})) \geq 1 - \alpha$$

where $\mathcal{S}$ denotes the space of admissible score functions and $|\mathcal{C}_\alpha(X_{n+1})|$ represents the width (Lebesgue measure) of the prediction interval.

However, this optimization problem is intractable in its raw form since:
1. The expectation is over the unknown distribution $P_{X,Y}$
2. The constraint is automatically satisfied by the conformal procedure
3. The space $\mathcal{S}$ is infinite-dimensional and poorly structured

## Reformulation via Score Function Learning

We reformulate the problem by parameterizing the score function class. Let $\mathcal{S}_\theta = \{s_\theta : \theta \in \Theta\}$ be a parametric family of score functions, where $\Theta \subseteq \mathbb{R}^d$ is the parameter space. Our objective becomes:

$$\min_{\theta \in \Theta} \mathbb{E}_{(X,Y) \sim P_{X,Y}}[w_\alpha(X, Y; \theta)]$$

where $w_\alpha(X, Y; \theta)$ represents the expected width of the conformal prediction interval when using score function $s_\theta$.

Since the true distribution is unknown, we approximate this objective using the empirical distribution:

$$\min_{\theta \in \Theta} \frac{1}{n} \sum_{i=1}^n w_\alpha(X_i, Y_i; \theta)$$

The key technical challenge is that $w_\alpha(X_i, Y_i; \theta)$ is not directly computable, as it requires knowledge of the quantile $\hat{Q}_{1-\alpha}$ which depends on the entire dataset in a complex, non-differentiable manner.

## Technical Assumptions

We make the following assumptions:

**A1 (Exchangeability):** The sequence $(X_1, Y_1), \ldots, (X_n, Y_n), (X_{n+1}, Y_{n+1})$ is exchangeable. This is the minimal assumption required for conformal prediction validity.

**A2 (Score Function Regularity):** The score functions $s_\theta$ are continuous in both arguments and differentiable with respect to $\theta$. This enables gradient-based optimization.

**A3 (Bounded Outputs):** The output space $\mathcal{Y}$ is bounded, or the score functions have appropriate tail behavior to ensure finite interval widths. This ensures well-defined optimization objectives.

**A4 (Finite Parameter Space):** The parameter space $\Theta$ is compact, ensuring the existence of optimal parameters and enabling uniform convergence arguments.

## Connection to Prior Work

Classical conformal prediction methods rely on heuristically chosen score functions, such as absolute residuals $s(x,y) = |\hat{\mu}(x) - y|$ or normalized residuals $s(x,y) = |\hat{\mu}(x) - y|/\hat{\sigma}(x)$ where $\hat{\sigma}$ estimates conditional variance. While these approaches guarantee coverage, they may produce unnecessarily wide intervals.

Recent work has explored adaptive conformal methods that adjust the score function based on local density or conditional quantiles, but these typically require additional distributional assumptions or asymptotic arguments. Our formulation addresses the fundamental question: can we learn optimal score functions directly from data while preserving finite-sample coverage guarantees?

The key gap our formulation addresses is the lack of a principled, data-driven approach to score function selection that maintains the non-asymptotic validity of conformal prediction while optimizing interval efficiency. This requires developing novel techniques to handle the non-differentiable quantile operations inherent in the conformal procedure while ensuring the learned score functions generalize beyond the training data.
