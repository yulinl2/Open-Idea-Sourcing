# Problem Formulation

## 2.1 Notation and Setup

Let $\mathcal{X} \subseteq \mathbb{R}^d$ denote the covariate space and $\mathcal{Y} \subseteq \mathbb{R}$ the outcome space. Consider a population of units characterized by covariates $X \in \mathcal{X}$, binary treatment assignment $T \in \{0,1\}$, and observed outcome $Y \in \mathcal{Y}$. For each unit, we define potential outcomes $Y(0)$ and $Y(1)$ corresponding to outcomes under control and treatment, respectively. The fundamental problem of causal inference is that we observe only one potential outcome: $Y = TY(1) + (1-T)Y(0)$.

The individual treatment effect (ITE) for a unit with covariates $x$ is defined as:
$$\tau(x) = Y(1) - Y(0)$$

Let $\mu_t(x) = \mathbb{E}[Y(t) \mid X = x]$ denote the conditional mean function for treatment $t \in \{0,1\}$, and define the conditional average treatment effect as $\text{CATE}(x) = \mu_1(x) - \mu_0(x)$. We can decompose the ITE as:
$$\tau(x) = \text{CATE}(x) + \epsilon_1(x) - \epsilon_0(x)$$
where $\epsilon_t(x) = Y(t) - \mu_t(x)$ represents the residual under treatment $t$.

## 2.2 Data and Distributions

We observe $n$ independent samples $\{(X_i, T_i, Y_i)\}_{i=1}^n$ drawn from the joint distribution of $(X, T, Y)$. Let $\pi(x) = \mathbb{P}(T = 1 \mid X = x)$ denote the propensity score. We assume $0 < \pi(x) < 1$ for all $x$ in the support of $X$ (overlap assumption).

For a new unit with covariates $X_{n+1}$, we seek to construct a prediction interval $\mathcal{I}_{n,\alpha}(X_{n+1})$ such that:
$$\mathbb{P}\left(\tau(X_{n+1}) \in \mathcal{I}_{n,\alpha}(X_{n+1})\right) \geq 1 - \alpha$$
for a specified miscoverage level $\alpha \in (0,1)$.

## 2.3 The Covariate Shift Challenge

A fundamental challenge arises from the fact that the distribution of covariates differs between treatment groups. Let $P_t$ denote the distribution of $X$ conditional on $T = t$. When constructing prediction intervals for counterfactual outcomes, we face a covariate shift problem: to predict $Y(1-T_{n+1})$ for a new unit, the relevant training distribution is $P_{1-T_{n+1}}$, but the test point $X_{n+1}$ comes from $P_{T_{n+1}}$.

Specifically, for a unit assigned to treatment $t$, we observe $Y(t)$ but need to predict $Y(1-t)$. The challenge is that the covariate distribution in the training data for treatment $1-t$ may differ systematically from the distribution generating $X_{n+1}$.

## 2.4 Problem Statement

**Given:** 
- Training data $\mathcal{D}_n = \{(X_i, T_i, Y_i)\}_{i=1}^n$
- A new unit with covariates $X_{n+1}$ and treatment assignment $T_{n+1}$
- Miscoverage level $\alpha \in (0,1)$

**Find:** A prediction interval procedure $\mathcal{I}_{n,\alpha}: \mathcal{X} \to \mathbb{R}^2$ that constructs intervals $\mathcal{I}_{n,\alpha}(X_{n+1}) = [L_n(X_{n+1}), U_n(X_{n+1})]$ satisfying:

1. **Finite-sample coverage guarantee:**
   $$\mathbb{P}\left(\tau(X_{n+1}) \in \mathcal{I}_{n,\alpha}(X_{n+1})\right) \geq 1 - \alpha$$

2. **Distribution-free validity:** The guarantee holds without parametric assumptions on the data generating process.

3. **Covariate shift robustness:** The procedure accounts for distributional differences between $P_0$ and $P_1$.

## 2.5 Objective and Constraints

Our objective is to construct the shortest possible prediction intervals subject to the coverage constraint. Formally, we seek to minimize:
$$\mathbb{E}[U_n(X_{n+1}) - L_n(X_{n+1})]$$
subject to the coverage guarantee above.

The procedure must handle two sources of uncertainty:
1. **Estimation uncertainty:** Arising from estimating $\mu_t(x)$ and the conditional distributions of $\epsilon_t(x)$ from finite samples
2. **Fundamental uncertainty:** Arising from the inherent variability in individual responses, captured by $\text{Var}(\epsilon_1(x) - \epsilon_0(x))$

## 2.6 Technical Assumptions

**A1 (Unconfoundedness):** $(Y(0), Y(1)) \perp T \mid X$, meaning treatment assignment is ignorable given observed covariates.

**A2 (Overlap):** $0 < \pi(x) < 1$ for all $x$ in the support of $X$.

**A3 (Exchangeability):** The training samples $\{(X_i, T_i, Y_i)\}_{i=1}^n$ are exchangeable with $(X_{n+1}, T_{n+1}, Y_{n+1})$.

**A4 (Finite moments):** $\mathbb{E}[Y(t)^2 \mid X = x] < \infty$ for $t \in \{0,1\}$ and all $x$.

These assumptions are standard in the causal inference literature. A1 and A2 ensure identification of causal effects from observational data. A3 is required for conformal prediction methods, while A4 ensures well-defined prediction intervals.

## 2.7 Connection to Prior Work

Existing approaches to ITE uncertainty quantification fall into several categories:

**Parametric methods** rely on distributional assumptions (e.g., Gaussian errors) and asymptotic approximations, limiting their reliability in finite samples and when model assumptions are violated.

**Bootstrap and subsampling methods** capture estimation uncertainty but often fail to account for the fundamental variability in individual responses and lack finite-sample guarantees.

**Conformal prediction approaches** \citep{kivaranovic2020conformal} provide distribution-free finite-sample guarantees but do not address the covariate shift problem inherent in causal inference. These methods construct separate prediction intervals for $Y(0)$ and $Y(1)$ and combine them, but this approach is overly conservative because it ignores the dependence structure between potential outcomes and fails to account for the distributional mismatch between training and test covariates.

**Weighted conformal prediction** methods have been developed for standard supervised learning under covariate shift, but their application to causal inference requires careful handling of the likelihood ratios between treatment groups and the target population.

Our formulation addresses these limitations by extending distribution-free prediction methods to account for the specific structure of causal inference problems, where the covariate distribution of the training data for each treatment group may differ from the target population, and where we must quantify uncertainty about inherently unobservable counterfactual outcomes.