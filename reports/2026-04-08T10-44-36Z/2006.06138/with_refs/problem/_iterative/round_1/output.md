# Problem Formulation

## Notation and Setup

Consider a setting where we observe $n$ independent and identically distributed samples $\{(X_i, T_i, Y_i)\}_{i=1}^n$, where $X_i \in \mathcal{X} \subseteq \mathbb{R}^d$ represents covariates, $T_i \in \{0,1\}$ denotes binary treatment assignment, and $Y_i \in \mathbb{R}$ is the observed outcome. Let $(X, T, Y)$ denote a generic observation from the same distribution.

Following the potential outcomes framework, we define $Y^{(0)}(X)$ and $Y^{(1)}(X)$ as the potential outcomes under control and treatment, respectively, for an individual with covariates $X$. The observed outcome satisfies $Y = T \cdot Y^{(1)}(X) + (1-T) \cdot Y^{(0)}(X)$. The individual treatment effect (ITE) is defined as:
$$\tau(X) = Y^{(1)}(X) - Y^{(0)}(X)$$

We decompose each potential outcome as:
$$Y^{(t)}(X) = \mu_t(X) + \varepsilon_t(X), \quad t \in \{0,1\}$$
where $\mu_t(X) = \mathbb{E}[Y^{(t)}(X) | X]$ are the conditional mean functions and $\varepsilon_t(X)$ are mean-zero error terms with $\mathbb{E}[\varepsilon_t(X) | X] = 0$.

The individual treatment effect can thus be written as:
$$\tau(X) = \underbrace{\mu_1(X) - \mu_0(X)}_{\text{CATE}(X)} + \underbrace{\varepsilon_1(X) - \varepsilon_0(X)}_{\text{residual variation}}$$

The conditional average treatment effect (CATE) is $\text{CATE}(X) = \mathbb{E}[\tau(X) | X]$, while the residual term $\varepsilon_1(X) - \varepsilon_0(X)$ captures the inherent individual-level variability that cannot be explained by covariates.

## Problem Statement

**Given:** Training data $\mathcal{D}_n = \{(X_i, T_i, Y_i)\}_{i=1}^n$ and a new individual with covariates $X_{\text{new}}$.

**Goal:** Construct a prediction interval $\mathcal{I}_n(X_{\text{new}}) = [L_n(X_{\text{new}}), U_n(X_{\text{new}})]$ for the individual treatment effect $\tau(X_{\text{new}})$ that satisfies:
$$\mathbb{P}(\tau(X_{\text{new}}) \in \mathcal{I}_n(X_{\text{new}})) \geq 1 - \alpha$$
for a pre-specified confidence level $1-\alpha$, where the probability is taken over both the training data $\mathcal{D}_n$ and the randomness in $\tau(X_{\text{new}})$.

**Key Challenge:** The fundamental difficulty is that $\tau(X_i)$ is never observed for any individual $i$ in the training data, as each person receives only one treatment. This prevents direct application of standard prediction interval methods that rely on observed residuals.

## Formal Objective

We seek to construct prediction intervals that simultaneously account for:

1. **Estimation uncertainty:** Arising from finite-sample estimation of $\mu_0(\cdot)$ and $\mu_1(\cdot)$ using machine learning methods
2. **Residual uncertainty:** Stemming from the unobservable individual-level variation $\varepsilon_1(X) - \varepsilon_0(X)$
3. **Distributional robustness:** Valid without strong parametric assumptions on error distributions

The prediction interval should satisfy the coverage guarantee:
$$\inf_{P \in \mathcal{P}} \mathbb{P}_P(\tau(X_{\text{new}}) \in \mathcal{I}_n(X_{\text{new}})) \geq 1 - \alpha$$
where $\mathcal{P}$ represents the class of data-generating distributions satisfying our assumptions.

For practical utility, we additionally desire that the interval width $U_n(X_{\text{new}}) - L_n(X_{\text{new}})$ should:
- Decrease as the sample size $n$ increases (when estimation uncertainty dominates)
- Remain bounded away from zero (due to irreducible residual uncertainty)
- Adapt to the complexity and uncertainty of the underlying regression functions

## Technical Assumptions

**Assumption 1 (Unconfoundedness):** $(Y^{(0)}, Y^{(1)}) \perp T | X$, meaning treatment assignment is conditionally independent of potential outcomes given observed covariates.

**Assumption 2 (Positivity):** There exist constants $0 < c < C < 1$ such that $c \leq \mathbb{P}(T = 1 | X) \leq C$ almost surely.

**Assumption 3 (Exchangeability):** The training samples $\{(X_i, T_i, Y_i)\}_{i=1}^n$ are exchangeable, and $(X_{\text{new}}, \tau(X_{\text{new}}))$ is exchangeable with respect to the training data.

*Justification:* Assumption 1 enables causal identification from observational data and is standard in causal inference. Assumption 2 ensures sufficient overlap between treatment groups. Assumption 3 is essential for conformal prediction methods and holds naturally in randomized experiments.

**Assumption 4 (Regularity):** The regression functions $\mu_0(\cdot)$ and $\mu_1(\cdot)$ are sufficiently regular to admit consistent estimation by the chosen machine learning method.

**Assumption 5 (Finite Moments):** $\mathbb{E}[|\varepsilon_t(X)|^{2+\delta}] < \infty$ for some $\delta > 0$ and $t \in \{0,1\}$.

*Justification:* These ensure that prediction intervals have well-defined finite-sample properties and that asymptotic results hold.

## Connection to Prior Work

Existing approaches to uncertainty quantification for treatment effects fall into several categories, each with significant limitations:

**Confidence Intervals for CATE:** Methods like those in Wager & Athey (2018) provide confidence intervals for $\mathbb{E}[\tau(X) | X]$ but ignore the residual variation $\varepsilon_1(X) - \varepsilon_0(X)$. These intervals shrink to zero as sample size increases and do not capture the full uncertainty in individual predictions.

**Parametric Prediction Intervals:** Traditional approaches assume specific distributional forms (e.g., Gaussian errors) and rely on asymptotic normality. These methods often fail when the parametric assumptions are violated and provide poor finite-sample coverage.

**Bootstrap Methods:** While bootstrap can account for estimation uncertainty, it struggles with the unobserved nature of individual treatment effects and often requires strong assumptions about the data-generating process.

**Conformal Prediction for Single Outcomes:** Standard conformal methods (Vovk et al., 2005) work well for predicting single outcomes but cannot directly handle the difference of two unobserved potential outcomes.

Our formulation addresses these gaps by extending conformal prediction to handle the fundamental challenge that individual treatment effects are never directly observed. Unlike existing approaches, we aim to provide finite-sample coverage guarantees without strong distributional assumptions while properly accounting for both estimation and residual uncertainty. The key insight is to construct prediction intervals for each potential outcome separately and then combine them in a principled manner that preserves the coverage guarantee for their difference.