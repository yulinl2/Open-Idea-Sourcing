# Reconstruction: problem_method
**Paper:** 2006.06138  
**Condition:** with_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Problem Formulation

## Notation and Setup

Let $(\mathcal{X}, \mathcal{Y})$ denote the covariate and outcome spaces, where $\mathcal{X} \subseteq \mathbb{R}^d$ and $\mathcal{Y} \subseteq \mathbb{R}$. Consider the potential outcomes framework with binary treatment $T \in \{0,1\}$. For each unit $i$, let $Y_i(0)$ and $Y_i(1)$ denote the potential outcomes under control and treatment, respectively, with observed covariates $X_i \in \mathcal{X}$. The observed outcome is $Y_i = T_i Y_i(1) + (1-T_i) Y_i(0)$, and the individual treatment effect (ITE) is $\tau_i = Y_i(1) - Y_i(0)$.

Let $P$ denote the population distribution over $(X, Y(0), Y(1), T)$, and assume we observe $n$ i.i.d. samples $\{(X_i, Y_i, T_i)\}_{i=1}^n$ drawn from $P$. For a new unit with covariates $X_{n+1}$, we aim to construct prediction intervals for the unobserved potential outcome.

Define the conditional outcome distributions:
- $\mu_0(x) = \mathbb{E}[Y(0) | X = x]$ and $\mu_1(x) = \mathbb{E}[Y(1) | X = x]$
- $\sigma_0^2(x) = \text{Var}[Y(0) | X = x]$ and $\sigma_1^2(x) = \text{Var}[Y(1) | X = x]$

The conditional individual treatment effect is $\tau(x) = \mu_1(x) - \mu_0(x)$.

## Problem Statement

**Given:** 
- Training data $\mathcal{D}_n = \{(X_i, Y_i, T_i)\}_{i=1}^n$ sampled i.i.d. from $P$
- A new unit's covariates $X_{n+1}$
- Desired coverage level $1-\alpha \in (0,1)$
- Target population distribution $\tilde{P}$ over covariates (potentially different from training distribution)

**Find:** Prediction intervals $\hat{C}_t(X_{n+1}) \subseteq \mathcal{Y}$ for $t \in \{0,1\}$ such that if the new unit were assigned treatment $t$, its potential outcome $Y_{n+1}(t)$ would be contained in $\hat{C}_t(X_{n+1})$.

**Guarantee:** The prediction intervals should satisfy
$$\mathbb{P}_{\tilde{P}}\left[Y_{n+1}(t) \in \hat{C}_t(X_{n+1})\right] \geq 1-\alpha$$
for $t \in \{0,1\}$, where the probability is taken over $(X_{n+1}, Y_{n+1}(0), Y_{n+1}(1)) \sim \tilde{P}$ and the randomness in $\mathcal{D}_n$.

## Objective

Our objective is to construct distribution-free prediction intervals that provide valid uncertainty quantification for counterfactual outcomes without requiring:
1. Parametric assumptions about the outcome distributions
2. Asymptotic approximations
3. Knowledge of the true conditional mean or variance functions
4. Identical training and target population distributions

The intervals should be as narrow as possible while maintaining the coverage guarantee, and should naturally handle covariate shift between training and target populations.

## Technical Assumptions

**Assumption 1 (Unconfoundedness):** $(Y(0), Y(1)) \perp T | X$, meaning treatment assignment is conditionally independent of potential outcomes given covariates.

**Assumption 2 (Overlap):** There exist constants $c, C > 0$ such that $c \leq e(x) \leq C$ for all $x \in \mathcal{X}$, where $e(x) = \mathbb{P}[T = 1 | X = x]$ is the propensity score.

**Assumption 3 (Covariate Shift):** The conditional outcome distributions are invariant across populations: $\mathbb{P}[Y(t) | X = x]$ is the same under $P$ and $\tilde{P}$ for $t \in \{0,1\}$ and all $x \in \mathcal{X}$.

**Assumption 4 (Likelihood Ratio):** The likelihood ratio $w(x) = \frac{d\tilde{P}_X}{dP_X}(x)$ exists and is known or can be estimated accurately, where $P_X$ and $\tilde{P}_X$ are the marginal covariate distributions under $P$ and $\tilde{P}$, respectively.

**Assumption 5 (Regularity):** The outcome distributions have finite second moments: $\mathbb{E}[Y(t)^2 | X = x] < \infty$ for $t \in \{0,1\}$ and all $x \in \mathcal{X}$.

These assumptions are standard in the causal inference literature. Assumption 1 ensures identifiability of causal effects from observational data. Assumption 2 guarantees sufficient overlap to estimate both potential outcomes. Assumption 3 allows us to transfer knowledge about outcome distributions from training to target populations. Assumption 4 connects our work to the covariate shift literature exemplified by Tibshirani et al. (2020), enabling us to reweight training observations appropriately. Assumption 5 ensures well-defined prediction intervals.

## Connection to Prior Work

This formulation extends the conformal prediction framework of Tibshirani et al. (2020) from standard supervised learning to causal inference settings. While their work addresses covariate shift in prediction problems where all outcomes are observed, our setting involves the fundamental missing data problem of causal inference: for each unit, we observe only one potential outcome. This creates additional challenges in defining appropriate nonconformity scores and establishing exchangeability properties needed for valid conformal inference.

# Methodology

## High-Level Approach

Our approach extends weighted conformal prediction to handle missing counterfactuals in causal inference. The key insight is to construct separate conformal prediction intervals for each potential outcome using only the relevant subset of training data, while appropriately reweighting observations to account for both propensity score imbalance and covariate shift between training and target populations.

We propose a **Causal Weighted Conformal Prediction** method that:
1. Partitions training data by treatment assignment
2. Constructs treatment-specific nonconformity scores using imputed counterfactuals
3. Applies weighted conformal prediction with importance weights combining propensity scores and likelihood ratios
4. Produces valid prediction intervals for both potential outcomes

## Core Algorithm

### Treatment-Specific Outcome Imputation

For each treatment group $t \in \{0,1\}$, we first estimate outcome models using the observed data:
- Fit $\hat{\mu}_t: \mathcal{X} \to \mathbb{R}$ using $\{(X_i, Y_i) : T_i = t\}$
- For computational efficiency, we use a split conformal approach where models are fit on a separate pre-training set

### Weighted Nonconformity Scores

For a test point $(x, y)$ and treatment $t$, we define the nonconformity score as:
$$S_t((x,y)) = |y - \hat{\mu}_t(x)|$$

For each training observation $i$ with $T_i = t$, the nonconformity score is:
$$V_{t,i} = |Y_i - \hat{\mu}_t(X_i)|$$

### Importance Weighting

To account for both propensity score imbalance and covariate shift, we define composite weights:
$$w_t(x) = \frac{\tilde{p}_X(x)}{p_X(x)} \cdot \frac{\mathbf{1}(T = t)}{e_t(x)}$$

where:
- $\frac{\tilde{p}_X(x)}{p_X(x)}$ is the likelihood ratio for covariate shift
- $\frac{\mathbf{1}(T = t)}{e_t(x)}$ is the inverse propensity weight with $e_0(x) = 1-e(x)$ and $e_1(x) = e(x)$

For training observations in treatment group $t$, the normalized weights are:
$$\tilde{w}_{t,i}(x) = \frac{w_t(X_i)}{\sum_{j: T_j = t} w_t(X_j) + w_t(x)}$$

### Causal Weighted Conformal Prediction Algorithm

```
Algorithm: Causal Weighted Conformal Prediction

Input: 
  - Training data D_n = {(X_i, Y_i, T_i)}_{i=1}^n
  - Test covariate X_{n+1}
  - Coverage level 1-α
  - Likelihood ratio function w(x) = dP̃_X/dP_X(x)
  - Propensity score function e(x)

Output: Prediction intervals Ĉ_0(X_{n+1}), Ĉ_1(X_{n+1})

1. Split training data by treatment:
   D_0 = {(X_i, Y_i) : T_i = 0}
   D_1 = {(X_i, Y_i) : T_i = 1}

2. For each treatment t ∈ {0,1}:
   
   a. Fit outcome model μ̂_t using D_t
   
   b. Compute nonconformity scores:
      For i with T_i = t: V_{t,i} = |Y_i - μ̂_t(X_i)|
   
   c. Compute importance weights:
      For i with T_i = t: w_{t,i} = w(X_i) / e_t(X_i)
   
   d. Compute normalized weights:
      w̃_{t,i}(X_{n+1}) = w_{t,i} / (∑_{j:T_j=t} w_{t,j} + w(X_{n+1})/e_t(X_{n+1}))
   
   e. Construct weighted empirical distribution:
      F̂_t(·|X_{n+1}) = ∑_{i:T_i=t} w̃_{t,i}(X_{n+1}) δ_{V_{t,i}} + w̃_{t,n+1}(X_{n+1}) δ_∞
   
   f. Compute prediction interval:
      Ĉ_t(X_{n+1}) = [μ̂_t(X_{n+1}) - q_t, μ̂_t(X_{n+1}) + q_t]
      where q_t = Quantile(1-α; F̂_t(·|X_{n+1}))

3. Return Ĉ_0(X_{n+1}), Ĉ_1(X_{n+1})
```

## Key Design Decisions

**Separate Treatment-Specific Models:** We construct separate conformal prediction intervals for each potential outcome rather than trying to model treatment effects directly. This design choice is motivated by the fundamental asymmetry in causal inference—we observe different subsets of the data for each potential outcome. This approach also allows for different levels of uncertainty in different treatment arms.

**Composite Importance Weighting:** Our weighting scheme combines two types of reweighting. The likelihood ratio $w(x)$ handles covariate shift as in Tibshirani et al. (2020), while inverse propensity weighting addresses the selection bias inherent in observational data. This combination ensures that our nonconformity scores properly reflect the distribution of residuals we would expect to see in the target population.

**Split Conformal Approach:** Following the computational efficiency strategy in the reference work, we use pre-fitted models rather than refitting for each potential outcome value. This dramatically reduces computational cost while maintaining theoretical guarantees.

## Theoretical Properties

**Theorem (Coverage Guarantee):** Under Assumptions 1-5, for each $t \in \{0,1\}$, the prediction interval $\hat{C}_t(X_{n+1})$ satisfies:
$$\mathbb{P}_{\tilde{P}}\left[Y_{n+1}(t) \in \hat{C}_t(X_{n+1})\right] \geq 1-\alpha$$

The proof follows by extending the weighted exchangeability arguments from Tibshirani et al. (2020) to the causal setting, where the key insight is that after appropriate reweighting, the residuals from each treatment group become exchangeable with the residuals we would observe for a new unit from the target population.

**Finite Sample Validity:** Unlike asymptotic approaches, our method provides exact finite-sample coverage guarantees that do not rely on large-sample approximations or normality assumptions.

**Model Agnostic:** The coverage guarantee holds regardless of the choice of base learning algorithm used to fit $\hat{\mu}_t$, making the method robust to model misspecification.

## Computational Complexity

The computational complexity is $O(n \log n)$ per treatment arm due to the quantile computation, where $n$ is the sample size. The overall complexity is $O(n \log n)$ since we process each treatment group separately. This is significantly more efficient than full conformal prediction, which would require $O(n \cdot |\mathcal{Y}|)$ operations where $|\mathcal{Y}|$ is the size of the discretized outcome space.

The method scales well with dimensionality since the conformal framework does not directly depend on the covariate dimension $d$, though the underlying outcome models may have dimension-dependent complexity.
