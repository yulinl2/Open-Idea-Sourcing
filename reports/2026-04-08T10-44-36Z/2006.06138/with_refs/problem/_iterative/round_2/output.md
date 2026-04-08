# Problem Formulation

## 2.1 Notation and Setup

We consider a setting where units are assigned to one of two treatment conditions. Let $X \in \mathcal{X} \subseteq \mathbb{R}^d$ denote the covariate vector, $T \in \{0,1\}$ the binary treatment assignment, and $Y \in \mathbb{R}$ the observed outcome. We assume the data generating process follows the potential outcomes framework, where each unit has two potential outcomes: $Y(1)$ under treatment and $Y(0)$ under control. The observed outcome is $Y = TY(1) + (1-T)Y(0)$.

Let $\{(X_i, T_i, Y_i)\}_{i=1}^n$ denote our training data, where each triple is an independent draw from the joint distribution of $(X,T,Y)$. For a new unit with covariates $X_{n+1}$, we are interested in constructing prediction intervals for the individual treatment effect (ITE):
$$\tau(X_{n+1}) = Y_{n+1}(1) - Y_{n+1}(0),$$
where $Y_{n+1}(1)$ and $Y_{n+1}(0)$ are the potential outcomes for the new unit.

We decompose the potential outcomes as:
$$Y(t) = \mu_t(X) + \epsilon_t(X), \quad t \in \{0,1\},$$
where $\mu_t(x) = \mathbb{E}[Y(t)|X=x]$ are the conditional mean functions and $\epsilon_t(X) = Y(t) - \mu_t(X)$ are mean-zero error terms that may depend on $X$. The individual treatment effect can thus be written as:
$$\tau(X) = \underbrace{\mu_1(X) - \mu_0(X)}_{\text{CATE}} + \underbrace{\epsilon_1(X) - \epsilon_0(X)}_{\text{residual variation}}.$$

Let $\pi(x) = \mathbb{P}(T=1|X=x)$ denote the propensity score. We define the treated and control subpopulations with sample sizes $n_1 = \sum_{i=1}^n T_i$ and $n_0 = n - n_1$, respectively.

## 2.2 Problem Statement

The fundamental challenge in constructing prediction intervals for $\tau(X_{n+1})$ is that we never observe both potential outcomes for any unit. This creates two distinct but related problems:

**Problem 1 (Distributional Mismatch):** When constructing intervals for counterfactual outcomes, the covariate distributions in treated and control groups typically differ. Specifically, let $P_1(x) = \mathbb{P}(X \leq x | T=1)$ and $P_0(x) = \mathbb{P}(X \leq x | T=0)$ denote the conditional covariate distributions. Under general assignment mechanisms, $P_1 \neq P_0$, which means that standard prediction intervals constructed from treated units may not provide valid coverage when applied to the covariate distribution of control units, and vice versa.

**Problem 2 (Unobserved Residual Correlation):** The residual terms $\epsilon_1(X)$ and $\epsilon_0(X)$ are never jointly observed for any unit, making it impossible to directly estimate their joint distribution or correlation structure. This correlation affects the variance of $\tau(X) = \mu_1(X) - \mu_0(X) + \epsilon_1(X) - \epsilon_0(X)$.

## 2.3 Formal Problem Formulation

**Given:**
- Training data $\mathcal{D}_n = \{(X_i, T_i, Y_i)\}_{i=1}^n$
- A new unit's covariates $X_{n+1}$
- Desired coverage level $1-\alpha$ for $\alpha \in (0,1)$

**Find:** An interval-valued function $\mathcal{I}_n: \mathcal{X} \to \mathbb{R}^2$ such that the interval $\mathcal{I}_n(X_{n+1}) = [L_n(X_{n+1}), U_n(X_{n+1})]$ satisfies:
$$\mathbb{P}(\tau(X_{n+1}) \in \mathcal{I}_n(X_{n+1})) \geq 1-\alpha,$$
where the probability is taken over the randomness in $\mathcal{D}_n$, the assignment $T_{n+1}$, and the potential outcomes $(Y_{n+1}(0), Y_{n+1}(1))$.

**Objective:** Among all procedures satisfying the coverage constraint, we seek those that:
1. Minimize expected interval width: $\mathbb{E}[U_n(X_{n+1}) - L_n(X_{n+1})]$
2. Provide finite-sample (non-asymptotic) guarantees
3. Handle the distributional mismatch between treatment groups
4. Account for uncertainty in both the CATE estimation and residual variation

## 2.4 Key Technical Challenges

The core technical challenge is that constructing valid intervals for $\tau(X_{n+1})$ requires prediction intervals for both counterfactual outcomes $Y_{n+1}(0)$ and $Y_{n+1}(1)$, but:

1. **Covariate shift:** Intervals for $Y_{n+1}(1)$ must be constructed using data from treated units, but their covariate distribution may differ from that of $X_{n+1}$
2. **Limited overlap:** In observational studies, regions of covariate space may have limited representation in one treatment group
3. **Residual dependence:** The joint distribution of $(\epsilon_1(X), \epsilon_0(X))$ affects interval width but cannot be estimated directly

## 2.5 Assumptions

We make the following assumptions:

**A1 (Stable Unit Treatment Value Assumption):** The potential outcomes $(Y_i(0), Y_i(1))$ for unit $i$ are unaffected by the treatment assignments of other units.

**A2 (Unconfoundedness):** $T \perp (Y(0), Y(1)) | X$, meaning treatment assignment is conditionally independent of potential outcomes given covariates.

**A3 (Overlap):** There exists $\eta > 0$ such that $\eta \leq \pi(x) \leq 1-\eta$ for all $x$ in the support of $X$.

**A4 (Exchangeability):** The training data $\{(X_i, T_i, Y_i)\}_{i=1}^n$ and test point $(X_{n+1}, T_{n+1}, Y_{n+1})$ are exchangeable.

**A5 (Measurability):** All functions and sets involved are measurable with respect to appropriate $\sigma$-algebras.

These assumptions are standard in the causal inference literature. A1 rules out interference effects, A2 ensures identifiability of causal effects (satisfied by design in randomized experiments), A3 ensures sufficient overlap for estimation, A4 enables the use of conformal prediction methods, and A5 ensures technical well-definedness.

## 2.6 Connection to Prior Work

Existing approaches to this problem fall into several categories, each with significant limitations:

**Asymptotic methods** rely on central limit theorems and consistent estimation of nuisance functions, but provide poor finite-sample performance and require strong regularity conditions that may not hold with modern machine learning estimators.

**Bootstrap methods** can handle complex estimators but lack theoretical guarantees for the coverage of individual treatment effects, particularly when the number of treated and control units is imbalanced.

**Conformal prediction** has been successfully applied to conditional mean estimation but faces fundamental challenges when extended to treatment effects due to the distributional mismatch problem. The work of Kivaranovic et al. (2020) represents an important step in this direction but constructs conservative intervals that do not fully exploit the reweighting techniques developed for point estimation in causal inference.

**Bayesian approaches** can naturally quantify uncertainty but require strong prior assumptions and often lack computational tractability for complex models.

The key insight missing from prior work is that the distributional mismatch problem in uncertainty quantification is analogous to the covariate imbalance problem in point estimation, where techniques like inverse propensity weighting and doubly robust estimation have proven highly effective. Our formulation aims to bridge this gap by adapting these reweighting ideas to the conformal prediction framework, enabling valid finite-sample inference for individual treatment effects without strong parametric assumptions.