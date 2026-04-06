# Reconstruction: problem
**Paper:** 2006.06138  
**Condition:** no_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Problem Formulation

## 2.1 Notation and Setup

Let $(\mathcal{X}, \mathcal{Y}, \mathcal{T})$ denote the covariate, outcome, and treatment spaces, respectively, where $\mathcal{X} \subseteq \mathbb{R}^d$, $\mathcal{Y} \subseteq \mathbb{R}$, and $\mathcal{T} = \{0, 1\}$ for binary treatments. For each unit $i$, let $X_i \in \mathcal{X}$ represent observed covariates, $T_i \in \mathcal{T}$ the treatment assignment, and $Y_i \in \mathcal{Y}$ the observed outcome.

Under the potential outcomes framework, each unit $i$ possesses two potential outcomes: $Y_i(1)$ under treatment and $Y_i(0)$ under control. The fundamental problem of causal inference is that we observe only one potential outcome for each unit: $Y_i = T_i Y_i(1) + (1-T_i) Y_i(0)$. The individual treatment effect (ITE) for unit $i$ is defined as:
$$\tau_i = Y_i(1) - Y_i(0)$$

The conditional average treatment effect (CATE) function is:
$$\tau(x) = \mathbb{E}[Y(1) - Y(0) \mid X = x] = \mu_1(x) - \mu_0(x)$$
where $\mu_t(x) = \mathbb{E}[Y(t) \mid X = x]$ for $t \in \{0, 1\}$.

Let $P_{XY}$ denote the joint distribution of $(X, Y(0), Y(1))$ and $\mathcal{D}_n = \{(X_i, T_i, Y_i)\}_{i=1}^n$ represent our observed training data of size $n$. We distinguish between two inference scenarios:
- **Within-study inference**: Constructing prediction intervals for units in $\mathcal{D}_n$
- **Out-of-study inference**: Constructing prediction intervals for new units $(X_{n+1}, T_{n+1})$ drawn from a potentially different distribution $P'_{XT}$

## 2.2 Problem Statement

Given training data $\mathcal{D}_n$ and a target unit with covariates $x_0$, we seek to construct prediction intervals $\mathcal{C}_\alpha(x_0) \subseteq \mathcal{Y}$ such that:
$$\mathbb{P}(\tau_0 \in \mathcal{C}_\alpha(x_0)) \geq 1 - \alpha$$
where $\tau_0$ is the unobserved individual treatment effect for the target unit and $\alpha \in (0, 1)$ is the miscoverage level.

The core challenge is that $\tau_0$ is never directly observable, even for units in the training set. This creates a **doubly missing data problem**: for within-study units, one potential outcome is missing; for out-of-study units, both potential outcomes are missing.

We require our prediction intervals to satisfy **finite-sample validity** without relying on asymptotic approximations or strong parametric assumptions. Specifically, the coverage guarantee must hold for any finite sample size $n$ and any underlying data distribution satisfying our stated assumptions.

## 2.3 Formal Objective

Our objective is to develop a procedure $\mathcal{A}: \mathcal{D}_n \times \mathcal{X} \to 2^{\mathcal{Y}}$ that maps training data and target covariates to prediction intervals, such that:

1. **Marginal coverage**: For any $P_{XY}$ satisfying our assumptions,
   $$\inf_{x \in \mathcal{X}} \mathbb{P}_{(X_0, Y_0(0), Y_0(1)) \sim P_{XY}}(\tau_0 \in \mathcal{A}(\mathcal{D}_n, x)) \geq 1 - \alpha$$

2. **Distribution-free validity**: The coverage guarantee holds without knowledge of the functional form of $\tau(x)$, $\mu_0(x)$, or $\mu_1(x)$

3. **Covariate shift robustness**: For out-of-study inference, coverage is maintained when the target covariate distribution $P'_X$ differs from the training distribution $P_X$, provided overlap conditions are satisfied

4. **Computational tractability**: The procedure should be implementable with modern machine learning algorithms for CATE estimation

## 2.4 Technical Assumptions

**Assumption 1 (SUTVA)**: The Stable Unit Treatment Value Assumption holds: (i) no interference between units, and (ii) treatment is consistently defined across units.

**Assumption 2 (Unconfoundedness)**: Treatment assignment is unconfounded given observed covariates: $(Y(0), Y(1)) \perp T \mid X$.

**Assumption 3 (Overlap)**: There exists $\epsilon > 0$ such that $\epsilon \leq e(x) \leq 1-\epsilon$ for all $x \in \mathcal{X}$, where $e(x) = \mathbb{P}(T = 1 \mid X = x)$ is the propensity score.

**Assumption 4 (Exchangeability)**: Training units $(X_i, Y_i(0), Y_i(1))$ are exchangeable under $P_{XY}$.

**Assumption 5 (Bounded Outcomes)**: There exists $M > 0$ such that $|Y(t)| \leq M$ almost surely for $t \in \{0, 1\}$.

Assumptions 1-3 are standard in the causal inference literature and enable identification of CATE from observational data. Assumption 4 is required for distribution-free methods and is weaker than independence. Assumption 5 ensures finite prediction intervals and can be relaxed to sub-Gaussian conditions.

## 2.5 Connection to Prior Work and Gap Analysis

Existing approaches to CATE uncertainty quantification fall into several categories, each with significant limitations:

**Parametric approaches** assume specific functional forms for $\tau(x)$ and rely on asymptotic normality of estimators. These methods fail when models are misspecified and provide poor finite-sample coverage.

**Bootstrap methods** attempt to quantify uncertainty through resampling but lack theoretical guarantees for the complex, non-linear estimators commonly used in heterogeneous treatment effect estimation. The bootstrap often fails for high-dimensional problems with machine learning base learners.

**Bayesian methods** require strong prior assumptions and computational approximations that compromise coverage guarantees. While they provide natural uncertainty quantification, their validity depends critically on correct model specification.

**Conformal prediction** has emerged as a powerful distribution-free framework for constructing prediction intervals with finite-sample guarantees. However, existing conformal methods are designed for standard prediction problems where the target quantity is directly observable. The causal inference setting presents unique challenges: the target quantity (individual treatment effect) is never observed, and we must handle the fundamental problem of missing counterfactuals.

Recent work on **conformal causal inference** has begun to address some of these challenges but remains limited. Existing methods either: (i) focus only on average treatment effects rather than individual effects, (ii) require restrictive assumptions about the data generating process, or (iii) fail to handle covariate shift between training and target populations.

The key gap our formulation addresses is the lack of **distribution-free, finite-sample valid prediction intervals for individual treatment effects** that can handle both within-study and out-of-study inference under covariate shift. This requires developing new theoretical frameworks that extend conformal prediction to the causal setting while properly accounting for the doubly missing data problem inherent in individual treatment effect estimation.
