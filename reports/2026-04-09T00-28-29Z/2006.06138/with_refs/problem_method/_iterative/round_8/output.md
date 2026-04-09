# Problem Formulation

## Notation and Setup

Let $(X_i, Y_i(1), Y_i(0))$ for $i = 1, \ldots, n$ denote $n$ independent units, where $X_i \in \mathcal{X} \subseteq \mathbb{R}^d$ represents covariates and $Y_i(1), Y_i(0) \in \mathbb{R}$ represent potential outcomes under treatment and control, respectively. The individual treatment effect for unit $i$ is $\tau_i = Y_i(1) - Y_i(0)$.

Each unit is assigned to treatment $T_i \in \{0,1\}$ according to some assignment mechanism with propensity score $e(X_i) = \mathbb{P}(T_i = 1 | X_i)$. We observe the realized outcome $Y_i = T_i Y_i(1) + (1-T_i) Y_i(0)$, so our observed data is $\{(X_i, T_i, Y_i)\}_{i=1}^n$.

Let $P_X$ and $\tilde{P}_X$ denote the covariate distributions in the study population and target population, respectively. The likelihood ratio is $w(x) = d\tilde{P}_X(x)/dP_X(x)$ when $\tilde{P}_X$ is absolutely continuous with respect to $P_X$.

For a new unit with covariates $X_{n+1}$ drawn from $\tilde{P}_X$, we seek to construct prediction intervals for the unobserved potential outcomes $Y_{n+1}(1)$ and $Y_{n+1}(0)$, and consequently for the individual treatment effect $\tau_{n+1} = Y_{n+1}(1) - Y_{n+1}(0)$.

## Formal Problem Statement

**Given:** 
- Observed data $\mathcal{D}_n = \{(X_i, T_i, Y_i)\}_{i=1}^n$ from study population with covariate distribution $P_X$
- New unit covariates $X_{n+1}$ from target population with covariate distribution $\tilde{P}_X$
- Likelihood ratio $w(x) = d\tilde{P}_X(x)/dP_X(x)$ (known or estimable)
- Desired coverage level $1-\alpha$ for $\alpha \in (0,1)$

**Find:** Prediction intervals $\hat{C}_n^{(1)}(X_{n+1})$ and $\hat{C}_n^{(0)}(X_{n+1})$ such that:
$$\mathbb{P}\left(Y_{n+1}(1) \in \hat{C}_n^{(1)}(X_{n+1})\right) \geq 1-\alpha$$
$$\mathbb{P}\left(Y_{n+1}(0) \in \hat{C}_n^{(0)}(X_{n+1})\right) \geq 1-\alpha$$

**Guarantee:** The intervals should provide finite-sample coverage guarantees that:
1. Account for covariate shift between study and target populations
2. Respect the fundamental constraint that $Y_{n+1}(1)$ can only be calibrated using treated units and $Y_{n+1}(0)$ using control units
3. Remain valid under partial model misspecification

## Objective

Our objective is to construct distribution-free prediction intervals that achieve exact finite-sample coverage by extending conformal prediction to handle the covariate shift problem inherent in causal inference. The key insight is to use weighted conformal prediction where weights are determined by the treatment assignment mechanism and likelihood ratios.

Specifically, for potential outcome $Y_{n+1}(t)$ where $t \in \{0,1\}$, we construct intervals using only data from units that received treatment $t$, with weights that rebalance the covariate distribution to match the target population.

## Technical Assumptions

**Assumption 1 (Unconfoundedness):** $(Y_i(1), Y_i(0)) \perp T_i | X_i$ for all $i$.

**Assumption 2 (Overlap):** There exist constants $0 < c_1 < c_2 < 1$ such that $c_1 \leq e(X_i) \leq c_2$ almost surely.

**Assumption 3 (Covariate Shift):** The conditional distribution of potential outcomes given covariates is the same in study and target populations: $\mathbb{P}(Y(t) \leq y | X = x)$ is identical across populations for $t \in \{0,1\}$.

**Assumption 4 (Absolute Continuity):** The target covariate distribution $\tilde{P}_X$ is absolutely continuous with respect to the study covariate distribution $P_X$.

**Assumption 5 (Bounded Likelihood Ratio):** The likelihood ratio $w(x) = d\tilde{P}_X(x)/dP_X(x)$ is bounded: $\sup_{x \in \mathcal{X}} w(x) < \infty$.

These assumptions are standard in causal inference literature. Assumption 1 ensures identifiability of causal effects, Assumption 2 ensures sufficient overlap for estimation, and Assumptions 3-5 formalize the covariate shift setting while ensuring the weighted conformal procedure is well-defined.

## Connection to Prior Work

This formulation extends the weighted conformal prediction framework of Tibshirani et al. (2020) to the causal inference setting. While their work addresses covariate shift in standard prediction problems, our setting introduces the additional complexity that each potential outcome can only be calibrated using data from the corresponding treatment group. The individual treatment effect prediction interval construction builds on ideas from Kivaranovic et al. (2020), but our approach explicitly handles covariate shift through the weighting mechanism derived from the treatment assignment probabilities.

# Methodology

## High-Level Approach

Our methodology constructs valid prediction intervals for unobserved potential outcomes by combining two key insights: (1) weighted conformal prediction can handle covariate shift when likelihood ratios are known, and (2) the treatment assignment mechanism that creates covariate imbalance also provides the mathematical structure needed to correct for it.

The approach proceeds in three steps:
1. **Separate Calibration:** Construct weighted conformal intervals for each potential outcome using only data from the corresponding treatment group
2. **Propensity-Based Weighting:** Use treatment assignment probabilities to reweight observations and correct for covariate shift
3. **Interval Combination:** Combine the separate intervals to obtain prediction intervals for individual treatment effects

## Core Algorithm

### Weighted Conformal Prediction for Potential Outcomes

For a given treatment level $t \in \{0,1\}$ and test point $X_{n+1}$, we construct prediction intervals as follows:

**Algorithm 1: Weighted Conformal Prediction for Potential Outcomes**

```
Input: 
- Data D_n = {(X_i, T_i, Y_i)}_{i=1}^n
- Test covariate X_{n+1}
- Treatment level t ∈ {0,1}
- Coverage level 1-α
- Score function S(·,·)
- Likelihood ratio function w(·)

1. Extract treatment-specific data:
   D_t = {(X_i, Y_i) : T_i = t, i = 1,...,n}
   Let n_t = |D_t|

2. For each candidate value y ∈ ℝ:
   a. Compute nonconformity scores:
      V_i^{(t)}(y) = S((X_i, Y_i), D_t ∪ {(X_{n+1}, y)}) for i with T_i = t
      V_{n+1}^{(t)}(y) = S((X_{n+1}, y), D_t)
   
   b. Compute propensity-adjusted weights:
      For i with T_i = t:
      w̃_i(X_{n+1}) = w(X_i) / [∑_{j:T_j=t} w(X_j) + w(X_{n+1})]
      
      w̃_{n+1}(X_{n+1}) = w(X_{n+1}) / [∑_{j:T_j=t} w(X_j) + w(X_{n+1})]

3. Define weighted empirical distribution:
   F̃_t(v) = ∑_{i:T_i=t} w̃_i(X_{n+1}) · 𝟙{V_i^{(t)}(y) ≤ v} + w̃_{n+1}(X_{n+1}) · 𝟙{∞ ≤ v}

4. Construct prediction interval:
   Ĉ_n^{(t)}(X_{n+1}) = {y ∈ ℝ : V_{n+1}^{(t)}(y) ≤ Quantile(1-α; F̃_t)}

Output: Prediction interval Ĉ_n^{(t)}(X_{n+1})
```

### Individual Treatment Effect Intervals

Once we have prediction intervals for both potential outcomes, we construct intervals for the individual treatment effect:

**Algorithm 2: Individual Treatment Effect Intervals**

```
Input:
- Prediction intervals Ĉ_n^{(1)}(X_{n+1}) and Ĉ_n^{(0)}(X_{n+1})
- Coverage level 1-α

1. Apply Bonferroni correction:
   Construct intervals at level 1-α/2 for each potential outcome

2. Combine intervals:
   Ĉ_n^{τ}(X_{n+1}) = {a-b : a ∈ Ĉ_n^{(1)}(X_{n+1}), b ∈ Ĉ_n^{(0)}(X_{n+1})}
                     = [L_1 - U_0, U_1 - L_0]
   
   where [L_t, U_t] denotes the interval Ĉ_n^{(t)}(X_{n+1})

Output: Treatment effect interval Ĉ_n^{τ}(X_{n+1})
```

## Key Design Decisions

### Propensity-Based Weighting

The weights $w̃_i(X_{n+1})$ serve a dual purpose: they correct for covariate shift (via the likelihood ratio $w(\cdot)$) and account for the treatment assignment mechanism. This is justified by the connection between treatment assignment probabilities and the resulting covariate distributions in treated and control groups.

For randomized experiments where $e(X) = \pi$ is constant, the weights simplify to the standard covariate shift correction. For observational studies, the weights incorporate both the selection mechanism and distributional differences.

### Score Function Choice

We recommend using absolute residuals from a flexible regression model:
$$S((x,y), \mathcal{D}) = |y - \hat{\mu}(x)|$$
where $\hat{\mu}$ is fitted on dataset $\mathcal{D}$. This connects to the split conformal approach for computational efficiency while maintaining distribution-free guarantees.

### Separate Calibration Constraint

The fundamental constraint that $Y_{n+1}(1)$ can only be calibrated using treated units (and similarly for control) is enforced by constructing completely separate weighted conformal procedures for each treatment group. This ensures that the coverage guarantees respect the missing data structure inherent in causal inference.

## Theoretical Properties

**Theorem 1 (Finite-Sample Coverage):** Under Assumptions 1-5, for any score function $S$ and treatment level $t \in \{0,1\}$:
$$\mathbb{P}\left(Y_{n+1}(t) \in \hat{C}_n^{(t)}(X_{n+1})\right) \geq 1-\alpha$$

**Theorem 2 (Treatment Effect Coverage):** Under the same assumptions, using the Bonferroni-corrected procedure:
$$\mathbb{P}\left(\tau_{n+1} \in \hat{C}_n^{τ}(X_{n+1})\right) \geq 1-\alpha$$

**Corollary 1 (Robustness):** The coverage guarantees hold even when the likelihood ratio $w(\cdot)$ is estimated, provided the estimation error is bounded.

## Computational Complexity

The computational complexity is $O(n \cdot |\mathcal{Y}| \cdot C_{\text{fit}})$ where $|\mathcal{Y}|$ is the number of candidate $y$ values evaluated and $C_{\text{fit}}$ is the cost of fitting the score function. For split conformal with pre-fitted models, this reduces to $O(n \cdot |\mathcal{Y}|)$.

The separate treatment group processing means we only use $n_1$ treated and $n_0$ control units respectively, potentially reducing computational costs compared to methods that use all $n$ observations simultaneously.

Memory requirements scale linearly with sample size, making the approach practical for large datasets common in causal inference applications.