# Reconstruction: problem_method
**Paper:** 2006.06138  
**Condition:** no_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Problem Formulation

## Notation and Setup

Let $(\mathcal{X}, \mathcal{Y})$ denote the covariate and outcome spaces, where $\mathcal{X} \subseteq \mathbb{R}^d$ and $\mathcal{Y} \subseteq \mathbb{R}$. For each unit $i$, let $X_i \in \mathcal{X}$ represent observed covariates and $T_i \in \{0,1\}$ denote the binary treatment assignment. Under the potential outcomes framework, each unit has two potential outcomes: $Y_i(1)$ (outcome under treatment) and $Y_i(0)$ (outcome under control). The observed outcome is $Y_i = T_i Y_i(1) + (1-T_i) Y_i(0)$.

The individual treatment effect (ITE) for unit $i$ is defined as:
$$\tau_i = Y_i(1) - Y_i(0)$$

The conditional average treatment effect (CATE) function is:
$$\tau(x) = \mathbb{E}[Y(1) - Y(0) | X = x] = \mathbb{E}[Y(1) | X = x] - \mathbb{E}[Y(0) | X = x]$$

Let $P$ denote the joint distribution of $(X, T, Y(0), Y(1))$, and let $P_X$ denote the marginal distribution of covariates $X$. We observe a dataset $\mathcal{D} = \{(X_i, T_i, Y_i)\}_{i=1}^n$ drawn from $P$.

## Problem Statement

**Given:** A dataset $\mathcal{D} = \{(X_i, T_i, Y_i)\}_{i=1}^n$ and a target covariate vector $x_0 \in \mathcal{X}$.

**Find:** A prediction interval $\mathcal{C}_\alpha(x_0) = [L_\alpha(x_0), U_\alpha(x_0)]$ for the individual treatment effect $\tau_0$ of a unit with covariates $x_0$.

**Guarantee:** For a specified miscoverage level $\alpha \in (0,1)$, the interval should satisfy:
$$\mathbb{P}(\tau_0 \in \mathcal{C}_\alpha(x_0)) \geq 1 - \alpha$$

This guarantee must hold under two distinct scenarios:
1. **Within-study inference:** $x_0$ corresponds to a unit in the study population where one potential outcome was observed
2. **Out-of-study inference:** $x_0$ corresponds to a new unit from a potentially shifted population where no outcomes have been observed

## Objective

Our objective is to construct distribution-free prediction intervals that provide valid coverage guarantees without relying on strong parametric assumptions. Formally, we seek to minimize the expected interval width:
$$\mathbb{E}[U_\alpha(X) - L_\alpha(X)]$$
subject to the coverage constraint:
$$\mathbb{P}(\tau(X) \in \mathcal{C}_\alpha(X)) \geq 1 - \alpha$$

The fundamental challenge is that individual treatment effects $\tau_i$ are never directly observable, requiring us to construct intervals based on estimated potential outcomes or CATE functions.

## Technical Assumptions

**Assumption 1 (Stable Unit Treatment Value Assumption - SUTVA):** The potential outcomes for unit $i$ are unaffected by the treatment assignments of other units, and there is only one version of each treatment level.

**Assumption 2 (Overlap/Positivity):** For all $x$ in the support of $P_X$:
$$0 < \mathbb{P}(T = 1 | X = x) < 1$$

**Assumption 3 (Unconfoundedness):** Treatment assignment is independent of potential outcomes conditional on observed covariates:
$$(Y(0), Y(1)) \perp T | X$$

**Assumption 4 (Exchangeability):** The observed data points are exchangeable, allowing for the application of conformal prediction principles.

These assumptions are standard in the causal inference literature. Assumption 3 can be relaxed to allow for observational studies with unobserved confounding through the use of instrumental variables or other identification strategies. Assumption 4 is crucial for our distribution-free approach and is weaker than requiring i.i.d. data.

The problem formulation connects to the broader literature on conformal prediction for uncertainty quantification and causal inference for treatment effect estimation, bridging these two areas to address the unique challenges of providing reliable intervals for unobserved individual treatment effects.

# Methodology

## High-Level Approach

Our approach combines conformal prediction with causal inference to construct distribution-free prediction intervals for individual treatment effects. The key insight is to leverage the exchangeability of residuals from well-calibrated models to provide finite-sample coverage guarantees. We propose a two-stage procedure: first estimate conditional mean functions for potential outcomes, then apply conformal prediction to the resulting treatment effect predictions.

## Core Algorithm: Conformal Causal Intervals (CCI)

The algorithm operates by constructing nonconformity scores that measure how "unusual" a particular treatment effect value would be given the observed data. We split the data and use cross-fitting to avoid overfitting bias.

### Algorithm 1: Conformal Causal Intervals

```
Input: Dataset D = {(Xi, Ti, Yi)}_{i=1}^n, target covariates x0, 
       miscoverage level α ∈ (0,1)
Output: Prediction interval C_α(x0) = [L_α(x0), U_α(x0)]

1. Randomly split D into three folds: D1, D2, D3 of approximately equal size

2. For each fold k ∈ {1,2,3}:
   a. Train μ̂1^(-k)(x) = E[Y|X=x, T=1] on D_{-k} = D \ Dk  
   b. Train μ̂0^(-k)(x) = E[Y|X=x, T=0] on D_{-k}
   c. Compute τ̂^(-k)(x) = μ̂1^(-k)(x) - μ̂0^(-k)(x)

3. For each unit i in fold k, compute nonconformity score:
   If Ti = 1: Ri = |Yi - μ̂1^(-k)(Xi)|
   If Ti = 0: Ri = |Yi - μ̂0^(-k)(Xi)|

4. Compute treatment effect prediction for x0:
   τ̂(x0) = (1/3) * Σ_{k=1}^3 τ̂^(-k)(x0)

5. For x0, compute prediction intervals for potential outcomes:
   Q1 = Quantile((1-α/2), {Ri : Ti = 1})
   Q0 = Quantile((1-α/2), {Ri : Ti = 0})
   
6. Construct treatment effect interval:
   L_α(x0) = τ̂(x0) - Q1 - Q0
   U_α(x0) = τ̂(x0) + Q1 + Q0

7. Return C_α(x0) = [L_α(x0), U_α(x0)]
```

### Refined Nonconformity Score

The basic algorithm can be improved by using more sophisticated nonconformity scores that account for the heteroscedasticity in treatment effects. We define:

$$R_i = \frac{|Y_i - \hat{\mu}_{T_i}^{(-k)}(X_i)|}{\hat{\sigma}_{T_i}^{(-k)}(X_i)}$$

where $\hat{\sigma}_t^{(-k)}(x)$ estimates the conditional standard deviation $\text{Var}(Y|X=x, T=t)^{1/2}$ using the data excluding fold $k$.

## Handling Covariate Shift

For out-of-study inference where the target population may differ from the study population, we incorporate importance weighting. Let $w(x) = \frac{dP_{\text{target}}(x)}{dP_{\text{study}}(x)}$ denote the density ratio between target and study populations.

### Algorithm 2: Weighted Conformal Causal Intervals

```
Input: Study data D, target covariates x0, importance weights {wi}_{i=1}^n
Output: Weighted prediction interval

1. Estimate density ratio ŵ(x) using study and target covariate samples

2. Modify nonconformity scores: R̃i = Ri * ŵ(Xi)

3. Compute weighted quantiles:
   Q̃1 = WeightedQuantile((1-α/2), {R̃i : Ti = 1}, {ŵi : Ti = 1})
   Q̃0 = WeightedQuantile((1-α/2), {R̃i : Ti = 0}, {ŵi : Ti = 0})

4. Construct interval: C_α(x0) = [τ̂(x0) - Q̃1 - Q̃0, τ̂(x0) + Q̃1 + Q̃0]
```

## Design Justifications

**Cross-fitting:** We use 3-fold cross-fitting to ensure that the nonconformity scores are computed using models that have not seen the corresponding data points, preventing overfitting and ensuring valid coverage.

**Separate quantiles for treatment groups:** Computing separate quantiles for treated and control units accounts for potential differences in outcome variability between groups, leading to tighter intervals when such differences exist.

**Additive interval construction:** The interval $[\taû(x_0) - Q_1 - Q_0, \taû(x_0) + Q_1 + Q_0]$ provides conservative coverage by accounting for uncertainty in both potential outcome predictions.

## Theoretical Properties

**Theorem 1 (Marginal Coverage):** Under Assumptions 1-4, for any distribution $P$ and any machine learning algorithms used to estimate $\mu_1$ and $\mu_0$, the prediction intervals satisfy:
$$\mathbb{P}(\tau_0 \in \mathcal{C}_\alpha(X_0)) \geq 1 - \alpha$$

**Theorem 2 (Conditional Coverage):** If the conditional quantiles of the nonconformity scores are well-estimated, the intervals achieve approximate conditional coverage:
$$\mathbb{P}(\tau_0 \in \mathcal{C}_\alpha(x_0) | X_0 = x_0) \approx 1 - \alpha$$

**Consistency:** As $n \to \infty$, if the base learners consistently estimate the conditional means, the interval width converges to the optimal width under the true data generating process.

## Computational Complexity

The algorithm has computational complexity $O(n \log n + C_{\text{ML}})$, where $C_{\text{ML}}$ is the cost of training the base machine learning models. The $O(n \log n)$ term comes from sorting to compute quantiles. The cross-fitting requires training models three times, but this provides robustness against overfitting while maintaining the same asymptotic complexity as single-model approaches.

The method is highly parallelizable, as the three folds can be processed independently, and the base learners can be any off-the-shelf machine learning algorithm (random forests, neural networks, etc.), making it practically implementable across diverse applications.
