# Section 1: Problem Formulation

## 1.1 Notation and Setup

We consider the potential outcomes framework for causal inference. Let $X \in \mathcal{X} \subseteq \mathbb{R}^d$ denote a covariate vector, $T \in \{0,1\}$ denote the binary treatment assignment, and $Y \in \mathbb{R}$ denote the observed outcome. For each unit, we define potential outcomes $Y^{(1)}$ and $Y^{(0)}$ representing the outcomes that would be observed under treatment and control, respectively. The fundamental problem of causal inference is that we only observe one potential outcome: $Y = TY^{(1)} + (1-T)Y^{(0)}$.

The individual treatment effect (ITE) for a unit with covariates $x$ is defined as:
$$\tau(x) = Y^{(1)} - Y^{(0)}$$

We decompose each potential outcome into a systematic component and random error:
$$Y^{(t)} = \mu_t(X) + \varepsilon^{(t)}, \quad t \in \{0,1\}$$
where $\mu_t(x) = \mathbb{E}[Y^{(t)} | X = x]$ is the conditional mean function and $\varepsilon^{(t)}$ represents the idiosyncratic error with $\mathbb{E}[\varepsilon^{(t)} | X] = 0$.

The individual treatment effect can thus be written as:
$$\tau(X) = \mu_1(X) - \mu_0(X) + \varepsilon^{(1)} - \varepsilon^{(0)} = \Delta(X) + \eta$$
where $\Delta(X) = \mu_1(X) - \mu_0(X)$ is the conditional average treatment effect (CATE) and $\eta = \varepsilon^{(1)} - \varepsilon^{(0)}$ captures the individual-specific deviation from the CATE.

## 1.2 Data and Distributional Assumptions

Let $\mathcal{D}_n = \{(X_i, T_i, Y_i)\}_{i=1}^n$ denote our observed dataset, where $(X_i, T_i, Y_i)$ are i.i.d. copies of $(X, T, Y)$. We partition the data into treated and control groups:
- $\mathcal{D}_n^{(1)} = \{(X_i, Y_i) : T_i = 1\}$ with $n_1 = |\mathcal{D}_n^{(1)}|$
- $\mathcal{D}_n^{(0)} = \{(X_i, Y_i) : T_i = 0\}$ with $n_0 = |\mathcal{D}_n^{(0)}|$

We make the following standard causal inference assumptions:

**Assumption 1 (Stable Unit Treatment Value)**: The potential outcomes for unit $i$ do not depend on the treatment assignments of other units.

**Assumption 2 (Unconfoundedness)**: $(Y^{(1)}, Y^{(0)}) \perp T | X$, meaning treatment assignment is independent of potential outcomes conditional on observed covariates.

**Assumption 3 (Overlap)**: There exists $c > 0$ such that $c \leq \pi(x) \leq 1-c$ for all $x \in \mathcal{X}$, where $\pi(x) = \mathbb{P}(T = 1 | X = x)$ is the propensity score.

**Assumption 4 (Exchangeability within Groups)**: Conditional on treatment assignment, units are exchangeable: $(X_i, Y_i^{(t)}) | T_i = t$ are exchangeable for $t \in \{0,1\}$.

## 1.3 Problem Statement

**Given**: 
- Training data $\mathcal{D}_n$ satisfying Assumptions 1-4
- A new unit with covariates $X_{\text{new}}$ (which may come from a different population)
- Confidence level $1-\alpha$ where $\alpha \in (0,1)$

**Find**: A prediction interval $\mathcal{I}_n(X_{\text{new}}) = [L_n(X_{\text{new}}), U_n(X_{\text{new}})]$ for the individual treatment effect $\tau(X_{\text{new}})$.

**Guarantee**: The interval should satisfy finite-sample coverage:
$$\mathbb{P}(\tau(X_{\text{new}}) \in \mathcal{I}_n(X_{\text{new}})) \geq 1-\alpha$$

## 1.4 Technical Challenges and Objectives

The core challenge is that we cannot directly observe realizations of $\tau(X_i) = Y_i^{(1)} - Y_i^{(0)}$ for any unit $i$, since each unit is observed under only one treatment condition. This prevents the direct application of standard conformal prediction methods.

Our objective is to construct prediction intervals that:

1. **Respect the fundamental constraint**: Information about $Y^{(1)}$ can only be obtained from treated units ($T_i = 1$), and information about $Y^{(0)}$ can only be obtained from control units ($T_i = 0$).

2. **Handle covariate shift**: The distribution of covariates among treated units $P(X | T = 1)$ may differ from that among control units $P(X | T = 0)$, and both may differ from the target population distribution $P(X_{\text{new}})$.

3. **Account for two sources of uncertainty**:
   - **Estimation uncertainty**: Due to finite sample sizes in each treatment group
   - **Intrinsic variability**: Due to the random component $\eta = \varepsilon^{(1)} - \varepsilon^{(0)}$

4. **Maintain validity under model misspecification**: The method should remain valid even if the regression models for $\mu_0(\cdot)$ and $\mu_1(\cdot)$ are misspecified.

The key insight is that we must construct separate conformal prediction intervals for each potential outcome using only the corresponding treatment group, then combine these intervals while carefully accounting for the dependence structure between $\varepsilon^{(1)}$ and $\varepsilon^{(0)}$.

# Section 2: Methodology

## 2.1 Overview of Approach

Our methodology extends conformal prediction to the causal inference setting by constructing separate conformal intervals for each potential outcome, then combining them using union bounds or distributional assumptions. The approach consists of three main steps:

1. **Separate Conformal Intervals**: Construct conformal prediction intervals for $Y^{(1)}$ using only treated units and for $Y^{(0)}$ using only control units
2. **Interval Combination**: Combine the separate intervals to form an interval for the difference $\tau(X) = Y^{(1)} - Y^{(0)}$
3. **Coverage Adjustment**: Ensure the combined interval maintains the desired coverage level

## 2.2 Treatment-Specific Conformal Prediction

For each treatment level $t \in \{0,1\}$, we apply conformal prediction using only units that received treatment $t$.

**Step 1: Fit Regression Models**
Using the treatment-specific datasets $\mathcal{D}_n^{(t)}$, we fit regression models:
$$\hat{\mu}_t(x) = \mathcal{A}_t(\mathcal{D}_n^{(t)}, x)$$
where $\mathcal{A}_t$ can be any regression algorithm (linear regression, random forests, neural networks, etc.).

**Step 2: Compute Residuals**
For each unit $i$ with $T_i = t$, compute the residual:
$$R_i^{(t)} = |Y_i - \hat{\mu}_t(X_i)|$$

**Step 3: Conformal Quantiles**
For a new unit with covariates $x$, define the conformal scores and compute quantiles. For treatment level $t$, let $\mathcal{R}^{(t)} = \{R_i^{(t)} : T_i = t\}$ be the set of residuals from treatment group $t$.

The conformal quantile for coverage level $1-\beta$ is:
$$q_{1-\beta}^{(t)} = \text{Quantile}\left(\mathcal{R}^{(t)} \cup \{\infty\}, \frac{\lceil (n_t + 1)(1-\beta) \rceil}{n_t + 1}\right)$$

**Step 4: Treatment-Specific Intervals**
The conformal prediction interval for $Y^{(t)}$ given covariates $x$ is:
$$\mathcal{C}_t(x) = [\hat{\mu}_t(x) - q_{1-\beta}^{(t)}, \hat{\mu}_t(x) + q_{1-\beta}^{(t)}]$$

## 2.3 Main Algorithm: Conservative Union Bound Approach

Our primary method uses a union bound to ensure finite-sample coverage without distributional assumptions.

```
Algorithm 1: Conservative ITE Conformal Intervals
Input: Dataset D_n, new covariates x_new, confidence level 1-α
Output: Prediction interval I_n(x_new) for τ(x_new)

1. Split data by treatment:
   D_n^(0) = {(X_i, Y_i) : T_i = 0}
   D_n^(1) = {(X_i, Y_i) : T_i = 1}

2. Fit regression models:
   μ̂_0(·) = A_0(D_n^(0), ·)
   μ̂_1(·) = A_1(D_n^(1), ·)

3. Compute residuals for each treatment group:
   For i with T_i = 0: R_i^(0) = |Y_i - μ̂_0(X_i)|
   For i with T_i = 1: R_i^(1) = |Y_i - μ̂_1(X_i)|

4. Compute conformal quantiles for level 1-α/2:
   q^(0) = Quantile(R^(0) ∪ {∞}, ⌈(n_0 + 1)(1-α/2)⌉/(n_0 + 1))
   q^(1) = Quantile(R^(1) ∪ {∞}, ⌈(n_1 + 1)(1-α/2)⌉/(n_1 + 1))

5. Construct treatment-specific intervals:
   C_0(x_new) = [μ̂_0(x_new) - q^(0), μ̂_0(x_new) + q^(0)]
   C_1(x_new) = [μ̂_1(x_new) - q^(1), μ̂_1(x_new) + q^(1)]

6. Combine intervals for ITE:
   L_n(x_new) = (μ̂_1(x_new) - q^(1)) - (μ̂_0(x_new) + q^(0))
   U_n(x_new) = (μ̂_1(x_new) + q^(1)) - (μ̂_0(x_new) - q^(0))
   
7. Return: I_n(x_new) = [L_n(x_new), U_n(x_new)]
```

## 2.4 Theoretical Properties

**Theorem 1 (Finite-Sample Coverage)**: Under Assumptions 1-4, Algorithm 1 produces intervals with finite-sample coverage:
$$\mathbb{P}(\tau(X_{\text{new}}) \in \mathcal{I}_n(X_{\text{new}})) \geq 1-\alpha$$

**Proof Sketch**: By the union bound and conformal prediction theory:
- $\mathbb{P}(Y^{(1)} \in \mathcal{C}_1(X_{\text{new}})) \geq 1-\alpha/2$
- $\mathbb{P}(Y^{(0)} \in \mathcal{C}_0(X_{\text{new}})) \geq 1-\alpha/2$
- Therefore: $\mathbb{P}(Y^{(1)} \in \mathcal{C}_1(X_{\text{new}}) \text{ and } Y^{(0)} \in \mathcal{C}_0(X_{\text{new}})) \geq 1-\alpha$
- The interval $\mathcal{I}_n(X_{\text{new}})$ contains $\tau(X_{\text{new}}) = Y^{(1)} - Y^{(0)}$ whenever both potential outcomes lie in their respective intervals.

## 2.5 Improved Method Under Independence

When we can assume conditional independence of the error terms, we can construct tighter intervals.

```
Algorithm 2: Independence-Based ITE Conformal Intervals
Input: Dataset D_n, new covariates x_new, confidence level 1-α
Output: Prediction interval I_n(x_new) for τ(x_new)

1-3. [Same as Algorithm 1, steps 1-3]

4. Compute conformal quantiles for level √(1-α):
   q^(0) = Quantile(R^(0) ∪ {∞}, ⌈(n_0 + 1)√(1-α)⌉/(n_0 + 1))
   q^(1) = Quantile(R^(1) ∪ {∞}, ⌈(n_1 + 1)√(1-α)⌉/(n_1 + 1))

5-7. [Same as Algorithm 1, steps 5-7]
```

**Theorem 2 (Coverage Under Independence)**: If $\varepsilon^{(1)} \perp \varepsilon^{(0)} | X$, then Algorithm 2 provides coverage $\mathbb{P}(\tau(X_{\text{new}}) \in \mathcal{I}_n(X_{\text{new}})) \geq 1-\alpha$ with tighter intervals than Algorithm 1.

## 2.6 Asymptotic Method Under Gaussian Errors

For even tighter intervals when stronger assumptions hold, we provide an asymptotic method.

**Assumption 5 (Gaussian Errors)**: Conditional on $X$, $(\varepsilon^{(1)}, \varepsilon^{(0)})$ follows a bivariate normal distribution with $\text{Var}(\varepsilon^{(1)}) = \text{Var}(\varepsilon^{(0)}) = \sigma^2$ and correlation $\rho \geq 0$.

**Assumption 6 (Consistency)**: The regression estimators satisfy $\sup_{x \in \mathcal{K}} |\hat{\mu}_t(x) - \mu_t(x)| \to 0$ in probability for any compact set $\mathcal{K}$.

Under these assumptions, we can construct asymptotically valid intervals that account for the correlation structure between errors, leading to substantially tighter intervals when the correlation is positive.

## 2.7 Computational Complexity

The computational complexity of our methods is dominated by:
1. **Regression fitting**: $O(n \cdot C(\mathcal{A}))$ where $C(\mathcal{A})$ is the complexity of the regression algorithm
2. **Residual computation**: $O(n)$
3. **Quantile computation**: $O(n \log n)$ for sorting

The overall complexity is $O(n \cdot C(\mathcal{A}) + n \log n)$, which scales linearly with the regression algorithm complexity. The method is embarrassingly parallel across treatment groups, allowing for efficient implementation in large-scale settings.

## 2.8 Key Design Decisions

**Separate vs. Joint Modeling**: We construct separate intervals for each potential outcome rather than directly modeling the treatment effect. This respects the fundamental constraint that information about each potential outcome comes only from the corresponding treatment group.

**Union Bound vs. Distributional Assumptions**: Our primary method uses union bounds for robustness, while our secondary methods leverage independence or Gaussian assumptions for efficiency.

**Quantile Level Choice**: The choice of $\alpha/2$ (conservative) vs. $\sqrt{1-\alpha}$ (independence) vs. correlation-adjusted levels reflects the trade-off between robustness and efficiency.

This methodology provides a principled framework for uncertainty quantification in individual treatment effects that maintains finite-sample validity while being applicable to a wide range of regression algorithms and study designs.