# Problem Formulation

## Notation and Setup

Let $X \in \mathcal{X} \subseteq \mathbb{R}^d$ denote a $d$-dimensional covariate vector, and $T \in \{0,1\}$ denote the binary treatment assignment, where $T=1$ indicates treatment and $T=0$ indicates control. For each individual, we define potential outcomes $Y(1)$ and $Y(0)$ representing the outcomes that would be observed under treatment and control, respectively. The observed outcome is $Y = TY(1) + (1-T)Y(0)$, following the consistency assumption of causal inference.

The individual treatment effect (ITE) for a subject with covariates $X$ is defined as:
$$\tau(X) = Y(1) - Y(0)$$

We decompose each potential outcome as:
$$Y(t) = \mu_t(X) + \epsilon_t(X), \quad t \in \{0,1\}$$
where $\mu_t(X) = \mathbb{E}[Y(t)|X]$ is the conditional expectation function and $\epsilon_t(X) = Y(t) - \mu_t(X)$ is the residual with $\mathbb{E}[\epsilon_t(X)|X] = 0$.

Let $\mathcal{D}_n = \{(X_i, T_i, Y_i)\}_{i=1}^n$ denote our observed dataset of $n$ i.i.d. samples, where each $(X_i, T_i, Y_i)$ follows the same distribution as $(X, T, Y)$. We partition the data by treatment status: $\mathcal{D}_n^{(1)} = \{(X_i, Y_i) : T_i = 1\}$ with $n_1 = |\mathcal{D}_n^{(1)}|$ samples, and $\mathcal{D}_n^{(0)} = \{(X_i, Y_i) : T_i = 0\}$ with $n_0 = |\mathcal{D}_n^{(0)}|$ samples.

## Problem Statement

**Given:** 
- Observed dataset $\mathcal{D}_n$ where we only observe one potential outcome per individual
- A new individual with covariates $X_{n+1}$ (possibly from a different population)
- Desired coverage level $1-\alpha$ for $\alpha \in (0,1)$

**Find:** A prediction interval procedure $\mathcal{I}_n: \mathcal{X} \to \mathbb{R} \times \mathbb{R}$ that constructs intervals $[L_n(X_{n+1}), U_n(X_{n+1})]$ for the unobserved individual treatment effect $\tau(X_{n+1})$.

**Guarantee:** The interval should satisfy finite-sample coverage:
$$\mathbb{P}(\tau(X_{n+1}) \in [L_n(X_{n+1}), U_n(X_{n+1})]) \geq 1 - \alpha$$

## Formal Objective

We seek to construct prediction intervals that minimize expected length while maintaining valid coverage:
$$\min_{\mathcal{I}_n} \mathbb{E}[U_n(X_{n+1}) - L_n(X_{n+1})]$$
subject to:
$$\mathbb{P}(\tau(X_{n+1}) \in [L_n(X_{n+1}), U_n(X_{n+1})]) \geq 1 - \alpha$$

The key challenge is that $\tau(X_{n+1}) = Y_{n+1}(1) - Y_{n+1}(0)$ involves two unobserved potential outcomes, and we can only use treated units to inform us about $Y_{n+1}(1)$ and control units to inform us about $Y_{n+1}(0)$.

## Technical Assumptions

**A1 (Unconfoundedness):** For observational studies, we assume $(Y(0), Y(1)) \perp T | X$, meaning treatment assignment is conditionally independent of potential outcomes given covariates.

**A2 (Overlap):** There exist constants $c, C \in (0,1)$ such that $c \leq \pi(X) \leq C$ almost surely, where $\pi(X) = \mathbb{P}(T=1|X)$ is the propensity score.

**A3 (Exchangeability):** The samples $\{(X_i, T_i, Y_i)\}_{i=1}^n$ are exchangeable, and $(X_{n+1}, T_{n+1}, Y_{n+1})$ is exchangeable with any element of the training set.

**A4 (Separate Group Calibration):** The residuals $\{\epsilon_t(X_i) : T_i = t\}$ are exchangeable within each treatment group $t \in \{0,1\}$.

**A5 (Covariate Shift Robustness):** The method should remain valid when the distribution of $X_{n+1}$ differs from the empirical distribution of covariates in $\mathcal{D}_n$.

These assumptions are justified as follows: A1-A2 are standard causal inference assumptions enabling identification of treatment effects. A3 enables the use of conformal prediction methods. A4 recognizes that we can only calibrate potential outcomes using data from the corresponding treatment group. A5 addresses the critical challenge that study populations often differ from target populations.

## Connection to Prior Work

Our formulation extends the conformal prediction framework of Kivaranovic et al. (2020) in several key ways. While their work focuses on constructing intervals $[l_n(X,t), u_n(X,t)]$ for each potential outcome separately and then combining them as $[l_n(X,1) - u_n(X,0), u_n(X,1) - l_n(X,0)]$, we recognize that this approach may be overly conservative and fails to properly account for the fundamental constraint that each potential outcome can only be calibrated using its corresponding treatment group. Our formulation explicitly acknowledges the covariate shift problem and the need for group-specific calibration while maintaining the distribution-free guarantees that make conformal methods attractive.

# Methodology

## High-Level Approach

Our approach constructs prediction intervals for individual treatment effects by leveraging a novel application of conformal prediction that respects the fundamental constraint of causal inference: treated units can only inform us about treated potential outcomes, and control units can only inform us about control potential outcomes. We develop a **split conformal method for treatment effects** that maintains valid coverage under covariate shift while avoiding overly conservative intervals.

The key insight is to construct separate conformal intervals for each potential outcome using only the relevant treatment group, then combine these intervals in a way that accounts for the correlation structure between potential outcomes while maintaining finite-sample validity.

## Core Algorithm

Our method consists of three main steps: (1) split the data and fit outcome models, (2) construct treatment-specific conformal intervals, and (3) combine intervals with correlation adjustment.

### Step 1: Model Fitting and Data Splitting

```
Algorithm 1: Split Conformal ITE Intervals
Input: Dataset D_n, new covariates X_{n+1}, coverage level 1-α
Output: Prediction interval [L_n(X_{n+1}), U_n(X_{n+1})]

1. Randomly split D_n into training set D_train and calibration set D_cal
   with |D_cal| = ⌊n/2⌋

2. Partition calibration set by treatment:
   D_cal^(1) = {(X_i, Y_i) ∈ D_cal : T_i = 1}  (size n_1^cal)
   D_cal^(0) = {(X_i, Y_i) ∈ D_cal : T_i = 0}  (size n_0^cal)

3. Fit outcome models on D_train:
   μ̂_1(x) = ML_algorithm_1(D_train^(1))
   μ̂_0(x) = ML_algorithm_0(D_train^(0))

4. Compute residuals on calibration sets:
   R_i^(1) = |Y_i - μ̂_1(X_i)| for (X_i, Y_i) ∈ D_cal^(1)
   R_i^(0) = |Y_i - μ̂_0(X_i)| for (X_i, Y_i) ∈ D_cal^(0)
```

### Step 2: Treatment-Specific Conformal Quantiles

```
5. Compute conformal quantiles for each treatment group:
   q_1^(α/2) = Quantile((1-α/2)(1 + 1/n_1^cal), {R_i^(1)})
   q_0^(α/2) = Quantile((1-α/2)(1 + 1/n_0^cal), {R_i^(0)})

6. Construct marginal intervals for each potential outcome:
   I_1(X_{n+1}) = [μ̂_1(X_{n+1}) - q_1^(α/2), μ̂_1(X_{n+1}) + q_1^(α/2)]
   I_0(X_{n+1}) = [μ̂_0(X_{n+1}) - q_0^(α/2), μ̂_0(X_{n+1}) + q_0^(α/2)]
```

### Step 3: Correlation-Adjusted Combination

```
7. Estimate correlation between potential outcomes:
   ρ̂ = EstimateCorrelation(D_train, μ̂_1, μ̂_0)

8. Compute correlation adjustment factor:
   γ = max(0, ρ̂)  // Conservative adjustment for positive correlation
   
9. Adjust quantile levels:
   α_adj = α / (2 - γ)  // Tighter levels when outcomes are correlated

10. Final ITE interval:
    L_n(X_{n+1}) = μ̂_1(X_{n+1}) - μ̂_0(X_{n+1}) - q_1^(α_adj) - q_0^(α_adj)
    U_n(X_{n+1}) = μ̂_1(X_{n+1}) - μ̂_0(X_{n+1}) + q_1^(α_adj) + q_0^(α_adj)

Return: [L_n(X_{n+1}), U_n(X_{n+1})]
```

## Key Design Decisions

**Separate Group Calibration:** Unlike methods that pool all residuals, we calibrate each potential outcome using only the corresponding treatment group. This respects the fundamental constraint that $Y_i(1)$ is only observed when $T_i = 1$ and $Y_i(0)$ is only observed when $T_i = 0$.

**Split Conformal Framework:** We use sample splitting to avoid overfitting issues while maintaining the exchangeability required for conformal prediction. The split ensures that the residuals used for calibration are computed on independent data from the model fitting.

**Correlation Adjustment:** Rather than assuming independence between potential outcomes (which leads to overly conservative intervals), we estimate their correlation and adjust the quantile levels accordingly. When outcomes are positively correlated, we can use tighter individual intervals while maintaining overall coverage.

**Covariate Shift Robustness:** The method remains valid under covariate shift because conformal prediction provides distribution-free coverage guarantees. The quantiles are computed based on the residual distribution, which captures both aleatoric uncertainty and model uncertainty.

## Theoretical Properties

**Theorem 1 (Finite-Sample Coverage):** Under assumptions A1-A4, the intervals produced by Algorithm 1 satisfy:
$$\mathbb{P}(\tau(X_{n+1}) \in [L_n(X_{n+1}), U_n(X_{n+1})]) \geq 1 - \alpha$$

**Theorem 2 (Covariate Shift Robustness):** The coverage guarantee holds even when $X_{n+1}$ is drawn from a different distribution than the training covariates, provided the outcome models generalize reasonably to the new covariate distribution.

**Theorem 3 (Asymptotic Optimality):** As $n \to \infty$, if the outcome models are consistent and the correlation estimate converges to the true correlation, the interval length converges to the oracle optimal length that accounts for the true residual variances and correlation.

## Correlation Estimation Procedure

```
Function EstimateCorrelation(D_train, μ̂_1, μ̂_0):
1. For each unit i in D_train:
   - Compute predicted outcomes under both treatments:
     Ŷ_i(1) = μ̂_1(X_i), Ŷ_i(0) = μ̂_0(X_i)
   
2. Estimate correlation using predicted treatment effects:
   τ̂_i = Ŷ_i(1) - Ŷ_i(0) for all i
   σ̂²_τ = Var(τ̂_i)
   
3. Use residual-based correlation estimate:
   ρ̂ = (σ̂²_1 + σ̂²_0 - σ̂²_τ) / (2σ̂_1σ̂_0)
   
4. Return: clip(ρ̂, -1, 1)  // Ensure valid correlation
```

## Computational Complexity

The algorithm has computational complexity $O(n \log n)$ for the quantile computations plus the cost of fitting the machine learning models $\mû_1$ and $\mû_0$. The method scales linearly with the number of calibration points and can handle high-dimensional covariates through the choice of underlying ML algorithms. The correlation estimation adds minimal computational overhead, requiring only simple variance calculations on the predicted outcomes.

The method is particularly efficient because it avoids the need for complex optimization or iterative procedures, relying instead on simple quantile computations and standard machine learning model fitting. This makes it practical for large-scale applications while maintaining the theoretical guarantees of conformal prediction.