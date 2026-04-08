# Problem Formulation

## 2.1 Notation and Setup

Let $\mathcal{X} \subseteq \mathbb{R}^d$ denote the covariate space and $\mathcal{Y} \subseteq \mathbb{R}$ the outcome space. For each individual $i$, we define potential outcomes $Y_i(0)$ and $Y_i(1)$ corresponding to control and treatment conditions, respectively, along with observed covariates $X_i \in \mathcal{X}$ and treatment assignment $T_i \in \{0,1\}$. The observed outcome is $Y_i = T_i Y_i(1) + (1-T_i) Y_i(0)$, following the consistency assumption of the potential outcomes framework.

The individual treatment effect (ITE) for unit $i$ is defined as:
$$\tau_i = Y_i(1) - Y_i(0)$$

This quantity is never directly observable since we observe only one potential outcome per individual. Our goal is to construct prediction intervals for $\tau_i$ that provide finite-sample coverage guarantees.

Let $P$ denote the joint distribution of $(X, Y(0), Y(1), T)$, and let $P_X$, $P_{Y(0)|X}$, $P_{Y(1)|X}$, and $P_{T|X}$ denote the corresponding marginal and conditional distributions. We observe $n$ samples $\{(X_i, T_i, Y_i)\}_{i=1}^n$ drawn from this distribution, and seek to make inference about $\tau_{n+1}$ for a new individual with covariates $X_{n+1}$.

## 2.2 Problem Statement

**Given:** 
- Training data $\mathcal{D}_n = \{(X_i, T_i, Y_i)\}_{i=1}^n$ where $Y_i = T_i Y_i(1) + (1-T_i) Y_i(0)$
- Target covariate $X_{n+1}$ (potentially from a different distribution than training covariates)
- Desired coverage level $1-\alpha$ for $\alpha \in (0,1)$

**Find:** A prediction interval $\hat{C}_n(X_{n+1}) \subseteq \mathbb{R}$ such that:
$$\mathbb{P}(\tau_{n+1} \in \hat{C}_n(X_{n+1})) \geq 1-\alpha$$

**Key Challenge:** The fundamental obstacle is that $\tau_{n+1} = Y_{n+1}(1) - Y_{n+1}(0)$ involves two potential outcomes, but we observe at most one. This creates a missing data problem where the "missingness" pattern is determined by treatment assignment.

## 2.3 Reformulation as Prediction Under Covariate Shift

We reframe ITE uncertainty quantification as a prediction problem under covariate shift by recognizing that:

1. **Pseudo-outcomes are observable:** For each training unit $i$, we can construct pseudo-treatment effects using the observed outcome and model-based imputations for the missing potential outcome.

2. **Covariate shift structure:** The "missing data" pattern creates an implicit covariate shift between units where we observe $Y(1)$ versus $Y(0)$, characterized by the propensity score $e(x) = \mathbb{P}(T=1|X=x)$.

Let $\hat{\mu}_0(x)$ and $\hat{\mu}_1(x)$ denote estimators of $\mathbb{E}[Y(0)|X=x]$ and $\mathbb{E}[Y(1)|X=x]$ respectively, fitted on the training data. We define pseudo-treatment effects:
$$\hat{\tau}_i = \begin{cases}
Y_i - \hat{\mu}_0(X_i) & \text{if } T_i = 1 \\
\hat{\mu}_1(X_i) - Y_i & \text{if } T_i = 0
\end{cases}$$

The key insight is that these pseudo-outcomes exhibit a specific covariate shift pattern that can be corrected using importance weighting.

## 2.4 Weighted Conformal Prediction Objective

We employ a weighted conformal prediction framework where the weights account for the systematic difference in covariate distributions between treated and control units. Define importance weights:
$$w_i(x) = \begin{cases}
\frac{e(x)}{e(X_i)} & \text{if } T_i = 1 \\
\frac{1-e(x)}{1-e(X_i)} & \text{if } T_i = 0
\end{cases}$$

For a nonconformity score function $S(\cdot)$, we compute scores $V_i = S(\hat{\tau}_i, X_i)$ for $i = 1, \ldots, n$. The prediction interval is constructed as:
$$\hat{C}_n(x) = \left\{ \tau : S(\tau, x) \leq \text{Quantile}\left(1-\alpha; \sum_{i=1}^n \tilde{w}_i(x) \delta_{V_i} + \tilde{w}_{n+1}(x) \delta_{\infty}\right) \right\}$$

where $\tilde{w}_i(x) = w_i(x) / \left(\sum_{j=1}^n w_j(x) + w_{n+1}(x)\right)$ are normalized weights.

## 2.5 Technical Assumptions

**A1 (Unconfoundedness):** $(Y(0), Y(1)) \perp T | X$, ensuring that treatment assignment is ignorable given observed covariates.

**A2 (Positivity):** $0 < e(x) < 1$ for all $x$ in the support of $X$, guaranteeing that both treatment conditions have positive probability.

**A3 (Consistency):** $Y = TY(1) + (1-T)Y(0)$, linking observed and potential outcomes.

**A4 (Propensity Score Estimation):** The propensity score $e(x)$ is either known (randomized experiments) or can be consistently estimated with sufficient accuracy for the importance weights to be well-defined.

**A5 (Outcome Model Quality):** The outcome models $\hat{\mu}_0$ and $\hat{\mu}_1$ need not be correctly specified, but should provide reasonable approximations to enable meaningful pseudo-outcome construction.

These assumptions are standard in causal inference and are significantly weaker than requiring correct model specification for the outcome surfaces or propensity score.

## 2.6 Connection to Prior Work

Traditional approaches to ITE uncertainty quantification rely heavily on parametric assumptions about outcome models or Bayesian posterior sampling, which can be unreliable when models are misspecified. Conformal prediction methods (Vovk et al., 2005; Lei et al., 2018) provide distribution-free coverage guarantees but have not been extended to handle the unique missing data structure of causal inference.

Recent work on conformal prediction under covariate shift (Tibshirani et al., 2020) provides the theoretical foundation for our approach, but does not address the specific challenge where the target variable itself is partially unobserved during training. Our formulation bridges this gap by recognizing that the causal inference setting induces a particular type of covariate shift that can be corrected through importance weighting based on the propensity score.

Unlike existing methods that focus on point estimation or require strong distributional assumptions, our approach provides finite-sample coverage guarantees for individual-level causal effects while accommodating both randomized experiments and observational studies under standard causal assumptions.