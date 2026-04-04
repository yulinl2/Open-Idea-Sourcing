# Reconstruction: problem
**Paper:** 2602.04770  
**Condition:** with_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Problem Formulation

## Notation and Setup

Let $\mathcal{X} \subseteq \mathbb{R}^d$ denote the covariate space and $\mathcal{Y} \subseteq \mathbb{R}$ the response space. We observe training data $(X_1, Y_1), \ldots, (X_n, Y_n)$ drawn i.i.d. from an unknown distribution $P$ on $\mathcal{X} \times \mathcal{Y}$, and seek to construct prediction intervals for a new test point $(X_{n+1}, Y_{n+1}) \sim P$.

A **score function** is a mapping $s: \mathcal{X} \times \mathcal{Y} \times \Theta \to \mathbb{R}$, where $\Theta$ is a parameter space, such that smaller values of $s(x, y; \theta)$ indicate better agreement between the prediction model (parameterized by $\theta$) and the observed outcome $y$ at covariate $x$. Given a score function $s(\cdot, \cdot; \theta)$ fitted on training data, the **conformal prediction set** at level $\alpha \in (0, 1)$ for a test point $X_{n+1}$ is defined as:
$$\mathcal{C}_\alpha(X_{n+1}) = \{y \in \mathcal{Y} : s(X_{n+1}, y; \hat{\theta}) \leq \hat{q}_{1-\alpha}\}$$
where $\hat{\theta}$ is the parameter estimate from training data, and $\hat{q}_{1-\alpha}$ is the $(1-\alpha)$-quantile of the scores $\{s(X_i, Y_i; \hat{\theta})\}_{i=1}^n$.

The **marginal coverage** of this prediction set is $\mathbb{P}(Y_{n+1} \in \mathcal{C}_\alpha(X_{n+1}))$, and the **average interval width** (for interval-valued prediction sets) is $\mathbb{E}[|\mathcal{C}_\alpha(X_{n+1})|]$, where $|\cdot|$ denotes the Lebesgue measure.

## Problem Statement

**Given:** Training data $\{(X_i, Y_i)\}_{i=1}^n$ drawn i.i.d. from $P$, a parametric family of score functions $\{s(\cdot, \cdot; \theta) : \theta \in \Theta\}$, and a miscoverage level $\alpha \in (0, 1)$.

**Find:** An optimal parameter $\theta^* \in \Theta$ such that the resulting conformal prediction sets satisfy:

1. **Finite-sample marginal coverage guarantee:**
   $$\mathbb{P}(Y_{n+1} \in \mathcal{C}_\alpha(X_{n+1})) \geq 1 - \alpha$$
   for any $n \geq 1$ and any distribution $P$.

2. **Optimal efficiency:** Among all score functions that achieve valid coverage, $\theta^*$ minimizes the expected interval width:
   $$\theta^* \in \arg\min_{\theta \in \Theta_{\text{valid}}} \mathbb{E}[|\mathcal{C}_\alpha(X_{n+1})|]$$
   where $\Theta_{\text{valid}} = \{\theta \in \Theta : \mathbb{P}(Y_{n+1} \in \mathcal{C}_\alpha(X_{n+1})) \geq 1 - \alpha\}$.

## Optimization Objective

The core challenge is that the coverage constraint in the definition of $\Theta_{\text{valid}}$ involves the unknown distribution $P$, making direct optimization intractable. We therefore seek a data-driven approach that learns $\theta^*$ by solving:

$$\min_{\theta \in \Theta} \mathbb{E}_P[|\mathcal{C}_\alpha(X_{n+1})|] \quad \text{subject to} \quad \mathbb{P}_P(Y_{n+1} \in \mathcal{C}_\alpha(X_{n+1})) \geq 1 - \alpha$$

Since both the objective and constraint involve unknown expectations under $P$, we approximate this using empirical quantities. However, naively replacing population quantities with sample averages can lead to overfitting and coverage violations. The key insight is to leverage the **finite-sample coverage guarantee** of conformal prediction: for any score function, the conformal procedure automatically ensures valid coverage. This allows us to focus on minimizing interval width while the coverage property is maintained by design.

## Technical Assumptions

**A1. Exchangeability:** The augmented sequence $(X_1, Y_1), \ldots, (X_n, Y_n), (X_{n+1}, Y_{n+1})$ is exchangeable. This is the fundamental assumption underlying conformal prediction's finite-sample guarantees.

**A2. Score function regularity:** The score function $s(x, y; \theta)$ is continuous in $\theta$ for each $(x, y)$, and the parameter space $\Theta$ is compact. This ensures the existence of optimal parameters and stability of the optimization procedure.

**A3. Conditional coverage assumption:** For efficiency, we assume that smaller score values correspond to higher likelihood under the true conditional distribution $P(Y|X)$. Formally, for the optimal score function, $\mathbb{P}(Y \leq y | X = x)$ should be monotonically related to $s(x, y; \theta^*)$.

**A4. Bounded response:** The response space $\mathcal{Y}$ is bounded, ensuring that interval widths are finite and well-defined.

Assumption A1 is essential for conformal prediction's validity guarantees. A2 provides the technical regularity needed for optimization. A3 connects the score function to the underlying probabilistic structure, enabling efficiency. A4 is primarily for technical convenience and can often be relaxed.

## Connection to Prior Work

Standard conformal prediction \citep{vovk2005algorithmic} typically uses fixed score functions derived from point predictors, such as $s(x, y; \theta) = |y - \hat{f}_\theta(x)|$ for regression. While this guarantees coverage, the resulting intervals may be suboptimally wide because the score function is not tailored to the specific distribution $P$.

Recent work on adaptive conformal prediction has explored learning aspects of the conformal procedure, but primarily focuses on conditional coverage \citep{lei2018distribution} or handling covariate shift \citep{tibshirani2019conformal}. The latter work addresses distribution shift between training and test data but assumes a fixed score function and does not optimize for interval efficiency.

Our formulation addresses a fundamental gap: **how to learn the score function itself to achieve optimal efficiency while maintaining finite-sample coverage guarantees**. Unlike conditional coverage approaches that require additional distributional assumptions, our focus on marginal coverage preserves the assumption-free nature of conformal prediction while enabling principled optimization of interval width. This represents a novel direction that bridges the gap between the statistical validity of conformal methods and the adaptivity of modern machine learning approaches.
