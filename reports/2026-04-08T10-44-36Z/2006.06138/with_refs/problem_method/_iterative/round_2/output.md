# Problem Formulation

## Notation and Setup

Let $\mathcal{X} \subseteq \mathbb{R}^d$ denote the covariate space and $\mathcal{Y} \subseteq \mathbb{R}$ the outcome space. For each individual $i$, let $X_i \in \mathcal{X}$ represent the observed covariates and $T_i \in \{0,1\}$ indicate treatment assignment, where $T_i = 1$ denotes treatment and $T_i = 0$ denotes control. Each individual has two potential outcomes: $Y_i(1)$ under treatment and $Y_i(0)$ under control, but we only observe $Y_i = T_i Y_i(1) + (1-T_i) Y_i(0)$.

The individual treatment effect (ITE) for individual $i$ is defined as:
$$\tau_i = Y_i(1) - Y_i(0)$$

Let $\mu_1(x) = \mathbb{E}[Y(1) | X = x]$ and $\mu_0(x) = \mathbb{E}[Y(0) | X = x]$ denote the conditional mean functions, and define the conditional average treatment effect (CATE) as:
$$\tau(x) = \mu_1(x) - \mu_0(x)$$

We decompose the potential outcomes as:
$$Y(t) = \mu_t(X) + \epsilon_t, \quad t \in \{0,1\}$$
where $\epsilon_t$ represents the residual error with $\mathbb{E}[\epsilon_t | X] = 0$.

The observed data consists of $n$ i.i.d. samples $\mathcal{D}_n = \{(X_i, T_i, Y_i)\}_{i=1}^n$ drawn from the joint distribution of $(X, T, Y)$. Let $\mathcal{D}_n^{(1)} = \{(X_i, Y_i) : T_i = 1\}$ and $\mathcal{D}_n^{(0)} = \{(X_i, Y_i) : T_i = 0\}$ denote the treated and control subsamples respectively, with sizes $n_1$ and $n_0$ where $n_1 + n_0 = n$.

## Problem Statement

**Given:** A dataset $\mathcal{D}_n$ and a new individual with covariates $X_{n+1}$.

**Find:** A prediction interval $\mathcal{I}_n(X_{n+1}) = [L_n(X_{n+1}), U_n(X_{n+1})]$ for the individual treatment effect $\tau_{n+1} = Y_{n+1}(1) - Y_{n+1}(0)$.

**Guarantee:** The prediction interval should satisfy:
$$\mathbb{P}(\tau_{n+1} \in \mathcal{I}_n(X_{n+1})) \geq 1 - \alpha$$
for a pre-specified miscoverage level $\alpha \in (0,1)$, where the probability is taken over both the training data $\mathcal{D}_n$ and the test point $(X_{n+1}, \tau_{n+1})$.

## Objective

Our objective is to construct prediction intervals that achieve valid finite-sample coverage while being as narrow as possible. Formally, we seek to minimize the expected interval width:
$$\mathbb{E}[U_n(X_{n+1}) - L_n(X_{n+1})]$$
subject to the coverage constraint above.

The challenge lies in the fact that individual treatment effects $\tau_i$ are never directly observed in the training data, making traditional residual-based approaches inapplicable. We must account for two sources of uncertainty:
1. **Estimation uncertainty:** Due to finite sample estimation of $\mu_1(x)$ and $\mu_0(x)$
2. **Inherent variability:** Due to the residual terms $\epsilon_1 - \epsilon_0$

## Technical Assumptions

We make the following assumptions:

**A1 (Unconfoundedness):** $(Y(0), Y(1)) \perp T | X$, meaning treatment assignment is independent of potential outcomes conditional on observed covariates.

**A2 (Overlap):** There exists $c > 0$ such that $c \leq e(x) \leq 1-c$ for all $x \in \mathcal{X}$, where $e(x) = \mathbb{P}(T = 1 | X = x)$ is the propensity score.

**A3 (Exchangeability):** The augmented sequence $\{(X_i, T_i, Y_i)\}_{i=1}^{n+1}$ is exchangeable, which holds when the data are i.i.d.

**A4 (Covariate Shift Awareness):** The distribution of covariates may differ between treated ($P_X^{(1)}$), control ($P_X^{(0)}$), and target populations ($P_X^{target}$).

Assumptions A1-A2 are standard in causal inference and ensure identifiability of causal effects. A3 enables the application of conformal prediction techniques. A4 acknowledges that real-world applications often involve distribution shift, requiring methods that remain valid across different covariate distributions.

## Connection to Prior Work

This formulation extends the conformal prediction framework of Vovk et al. (2005) to the causal inference setting. While Kivaranovic et al. (2020) proposed conformal intervals for ITEs under randomized experiments, our formulation addresses the broader challenge of handling both randomized and observational studies under standard causal assumptions, while explicitly accounting for covariate shift between study populations and target populations.

# Methodology

## High-Level Approach

Our approach constructs prediction intervals for individual treatment effects by leveraging conformal prediction principles adapted to the causal inference setting. The key insight is to create pseudo-residuals that capture both the estimation uncertainty and the inherent variability in individual responses, while properly handling the distributional differences between treated and control groups.

The method consists of three main components:
1. **Outcome regression:** Estimate $\hat{\mu}_1(x)$ and $\hat{\mu}_0(x)$ using any regression algorithm
2. **Propensity estimation:** Estimate $\hat{e}(x)$ to handle covariate shift
3. **Conformal calibration:** Use weighted conformal prediction to construct valid intervals

## Core Algorithm

Our proposed method, **Causally-Aware Weighted Conformal Prediction (CA-WCP)**, proceeds as follows:

### Algorithm 1: CA-WCP for Individual Treatment Effects

```
Input: Training data D_n, test covariate X_{n+1}, miscoverage level α
Output: Prediction interval I_n(X_{n+1}) for τ_{n+1}

1. Split data: D_n = D_cal ∪ D_train (|D_cal| = m, |D_train| = n-m)

2. Train models on D_train:
   - Fit μ̂_1(x) using treated units in D_train
   - Fit μ̂_0(x) using control units in D_train  
   - Fit ê(x) using all units in D_train

3. For each calibration point (X_i, T_i, Y_i) ∈ D_cal:
   a) Compute predicted outcomes:
      Ŷ_i(1) = μ̂_1(X_i), Ŷ_i(0) = μ̂_0(X_i)
   
   b) Compute importance weights:
      w_i^{(1)} = P_target(X_i) / [ê(X_i) · P_train(X_i)]
      w_i^{(0)} = P_target(X_i) / [(1-ê(X_i)) · P_train(X_i)]
   
   c) Compute pseudo-residuals:
      If T_i = 1: R_i = w_i^{(1)} · |Y_i - Ŷ_i(1)| + ζ · √(w_i^{(0)}) · σ̂_0(X_i)
      If T_i = 0: R_i = w_i^{(0)} · |Y_i - Ŷ_i(0)| + ζ · √(w_i^{(1)}) · σ̂_1(X_i)
      
      where ζ ~ N(0,1) and σ̂_t(x) are estimated conditional standard deviations

4. Compute quantile:
   Q = Quantile({R_i}_{i∈D_cal}, (1-α)(1 + 1/m))

5. Return prediction interval:
   I_n(X_{n+1}) = [μ̂_1(X_{n+1}) - μ̂_0(X_{n+1}) - Q, 
                   μ̂_1(X_{n+1}) - μ̂_0(X_{n+1}) + Q]
```

## Key Design Decisions

### Weighted Conformal Scores

The importance weights $w_i^{(t)}$ address covariate shift by reweighting calibration residuals according to the ratio between target and training covariate densities, adjusted by propensity scores. This ensures validity even when the study population differs from the target population.

### Pseudo-Residual Construction

Since we never observe both $Y_i(1)$ and $Y_i(0)$ for the same individual, we construct pseudo-residuals that account for uncertainty in the unobserved potential outcome. For a treated individual, we observe the residual for the treated outcome but must account for uncertainty in the control outcome using the estimated conditional variance $\sigmâ_0(X_i)$.

### Adaptive Quantile Selection

The quantile level $(1-\alpha)(1 + 1/m)$ follows from conformal prediction theory and ensures finite-sample coverage guarantees under exchangeability.

## Theoretical Properties

**Theorem 1 (Finite-Sample Coverage):** Under assumptions A1-A3, if the covariate distributions are identical across groups ($P_X^{(1)} = P_X^{(0)} = P_X^{target}$), then:
$$\mathbb{P}(\tau_{n+1} \in \mathcal{I}_n(X_{n+1})) \geq 1 - \alpha$$

**Theorem 2 (Covariate Shift Robustness):** Under assumptions A1-A4, if the importance weights are computed correctly and $\max_i w_i^{(t)} = O(m^{1/4})$, then:
$$\lim_{n \to \infty} \mathbb{P}(\tau_{n+1} \in \mathcal{I}_n(X_{n+1})) \geq 1 - \alpha$$

**Theorem 3 (Adaptive Width):** The expected interval width satisfies:
$$\mathbb{E}[U_n(X_{n+1}) - L_n(X_{n+1})] = O\left(\sqrt{\frac{\log n}{n}} + \sigma_{\epsilon_1 - \epsilon_0}\right)$$
where the first term captures estimation uncertainty and the second captures inherent variability.

## Computational Complexity

The algorithm has computational complexity $O(n \log n)$ due to the quantile computation step, plus the complexity of fitting the outcome regression and propensity score models. The method is highly parallelizable since outcome models can be trained independently, and the calibration step involves only simple arithmetic operations.

The memory requirement is $O(n)$ for storing calibration residuals, making the approach scalable to large datasets. The method can accommodate any base learning algorithm for $\hat{\mu}_1$, $\hat{\mu}_0$, and $\hat{e}$, including neural networks, random forests, or gradient boosting machines.