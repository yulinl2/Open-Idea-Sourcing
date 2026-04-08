# Problem Formulation

## Notation and Setup

Let $(\mathcal{X}, \mathcal{Y}) = (\mathbb{R}^d, \mathbb{R})$ denote the covariate and outcome spaces, respectively. We observe training data $\{(X_i, T_i, Y_i)\}_{i=1}^n$ where $X_i \in \mathcal{X}$ represents covariates, $T_i \in \{0,1\}$ denotes binary treatment assignment, and $Y_i \in \mathcal{Y}$ is the observed outcome. We assume the potential outcomes framework with $Y_i = T_i Y_i(1) + (1-T_i) Y_i(0)$, where $Y_i(1)$ and $Y_i(0)$ are the potential outcomes under treatment and control, respectively.

The conditional average treatment effect (CATE) at covariate value $x$ is defined as:
$$\tau(x) = \mathbb{E}[Y(1) - Y(0) | X = x]$$

For a new individual with covariates $X_{n+1}$, we seek to construct a prediction interval $\mathcal{C}_n(X_{n+1})$ for their individual treatment effect $\tau_{n+1} = Y_{n+1}(1) - Y_{n+1}(0)$ such that:
$$\mathbb{P}[\tau_{n+1} \in \mathcal{C}_n(X_{n+1})] \geq 1 - \alpha$$

for a pre-specified miscoverage level $\alpha \in (0,1)$.

## Problem Statement

**Given:** 
- Training data $\mathcal{D}_n = \{(X_i, T_i, Y_i)\}_{i=1}^n$ from some unknown distribution $P$
- A new individual with covariates $X_{n+1}$ drawn from potentially different distribution $\tilde{P}_X$
- Desired coverage level $1-\alpha$

**Find:** A prediction interval $\mathcal{C}_n(X_{n+1}) \subseteq \mathbb{R}$ 

**Guarantee:** $\mathbb{P}[\tau_{n+1} \in \mathcal{C}_n(X_{n+1})] \geq 1 - \alpha$ holds without distributional assumptions on $P$ and regardless of model misspecification.

## Objective

The core challenge is that individual treatment effects $\tau_{n+1}$ are never directly observed, as each individual receives only one treatment. We must construct valid prediction intervals despite this fundamental identification problem. Our objective is to develop a method that:

1. Provides finite-sample coverage guarantees without asymptotic approximations
2. Remains valid under covariate shift between training and test populations
3. Does not rely on correct specification of outcome models or propensity score models

## Technical Assumptions

**Assumption 1 (Unconfoundedness):** $(Y(0), Y(1)) \perp T | X$, meaning treatment assignment is conditionally independent of potential outcomes given covariates.

**Assumption 2 (Overlap):** There exists $\epsilon > 0$ such that $\epsilon \leq e(x) \leq 1-\epsilon$ for all $x$ in the support of $X$, where $e(x) = \mathbb{P}[T=1|X=x]$ is the propensity score.

**Assumption 3 (Covariate Shift):** The training data follows $(X_i, T_i, Y_i) \sim P_X \times P_{T|X} \times P_{Y|T,X}$ while the test individual follows $X_{n+1} \sim \tilde{P}_X$ with the same conditional distributions $P_{T|X}$ and $P_{Y|T,X}$.

**Assumption 4 (Known Likelihood Ratio):** The likelihood ratio $w(x) = d\tilde{P}_X(x)/dP_X(x)$ is known or can be accurately estimated from unlabeled test data.

These assumptions are standard in causal inference. Assumption 1 ensures identifiability of treatment effects, Assumption 2 prevents extrapolation issues, and Assumptions 3-4 formalize the covariate shift setting while enabling distribution-free inference.

## Connection to Prior Work

This formulation extends conformal prediction methodology beyond exchangeable data to the causal inference setting. While Tibshirani et al. (2020) developed weighted conformal prediction for covariate shift in standard regression, our problem requires handling the unobserved nature of individual treatment effects. The key insight is to construct conformity scores based on imputed treatment effects using observed outcomes under both treatment conditions, then apply weighted conformal procedures to account for population shift between training and target populations.

# Methodology

## High-Level Approach

Our approach, **Conformal Causal Prediction (CCP)**, adapts weighted conformal prediction to the causal inference setting by constructing conformity scores for individual treatment effects despite their unobservability. The key innovation is using outcome imputation under both treatment conditions to create pseudo-observations of treatment effects, then applying weighted conformal inference to provide distribution-free coverage guarantees.

## Core Algorithm

### Step 1: Outcome Model Estimation

We fit separate outcome models for each treatment group:
- $\hat{\mu}_0(x) = \mathbb{E}[Y|T=0, X=x]$ using data $\{(X_i, Y_i) : T_i = 0\}$
- $\hat{\mu}_1(x) = \mathbb{E}[Y|T=1, X=x]$ using data $\{(X_i, Y_i) : T_i = 1\}$

These can be estimated using any regression algorithm (e.g., random forests, neural networks, linear regression).

### Step 2: Treatment Effect Imputation

For each training individual $i$, we construct an imputed treatment effect:
$$\hat{\tau}_i = \hat{\mu}_1(X_i) - \hat{\mu}_0(X_i)$$

This provides a point estimate of the unobserved individual treatment effect for each training observation.

### Step 3: Conformity Score Construction

We define the conformity score for a hypothetical treatment effect value $\tau$ at covariate $x$ as:
$$S((x, \tau), \mathcal{D}) = |\tau - \hat{\tau}(x)|$$

where $\hat{\tau}(x) = \hat{\mu}_1(x) - \hat{\mu}_0(x)$ is the estimated CATE at $x$.

For the weighted conformal procedure, we compute conformity scores:
$$V_i^{(x,\tau)} = S((X_i, \hat{\tau}_i), \mathcal{D}_{-i} \cup \{(x,\tau)\})$$
$$V_{n+1}^{(x,\tau)} = S((x, \tau), \mathcal{D}_n)$$

### Step 4: Weighted Conformal Inference

Following the weighted conformal prediction framework, we define weights:
$$p_i^w(x) = \frac{w(X_i)}{\sum_{j=1}^n w(X_j) + w(x)}, \quad i = 1,\ldots,n$$
$$p_{n+1}^w(x) = \frac{w(x)}{\sum_{j=1}^n w(X_j) + w(x)}$$

The prediction interval is constructed as:
$$\mathcal{C}_n(x) = \left\{\tau \in \mathbb{R} : V_{n+1}^{(x,\tau)} \leq \text{Quantile}\left(1-\alpha; \sum_{i=1}^n p_i^w(x)\delta_{V_i^{(x,\tau)}} + p_{n+1}^w(x)\delta_{\infty}\right)\right\}$$

## Algorithm Implementation

```
Algorithm: Conformal Causal Prediction (CCP)

Input: Training data D_n = {(X_i, T_i, Y_i)}_{i=1}^n
       Test covariate X_{n+1}
       Likelihood ratio function w(·)
       Miscoverage level α

1. Split training data:
   D_0 = {(X_i, Y_i) : T_i = 0}
   D_1 = {(X_i, Y_i) : T_i = 1}

2. Fit outcome models:
   μ̂_0 ← FitModel(D_0)
   μ̂_1 ← FitModel(D_1)

3. Compute imputed treatment effects:
   For i = 1 to n:
     τ̂_i ← μ̂_1(X_i) - μ̂_0(X_i)

4. Compute weights:
   For i = 1 to n:
     w_i ← w(X_i)
   w_total ← Σ_{i=1}^n w_i + w(X_{n+1})
   
   For i = 1 to n:
     p_i ← w_i / w_total
   p_{n+1} ← w(X_{n+1}) / w_total

5. Construct prediction interval:
   τ̂_{n+1} ← μ̂_1(X_{n+1}) - μ̂_0(X_{n+1})
   
   For i = 1 to n:
     V_i ← |τ̂_i - τ̂_{n+1}|
   
   q ← WeightedQuantile(1-α, {V_i}_{i=1}^n ∪ {∞}, {p_i}_{i=1}^n ∪ {p_{n+1}})
   
   Return C_n(X_{n+1}) = [τ̂_{n+1} - q, τ̂_{n+1} + q]

Output: Prediction interval C_n(X_{n+1})
```

## Justification of Design Decisions

**Treatment Effect Imputation:** Since individual treatment effects are unobservable, we use outcome model predictions to create pseudo-observations. This approach leverages the unconfoundedness assumption to ensure that imputed effects capture the true treatment effect signal.

**Weighted Conformity Scores:** The weighting scheme directly addresses covariate shift by rebalancing training observations to match the test distribution. This follows the weighted exchangeability principle established in the conformal prediction literature.

**Absolute Residual Score:** We use $|\tau - \hat{\tau}(x)|$ as our conformity score because it naturally measures how much a hypothetical treatment effect deviates from the predicted effect, providing an intuitive notion of conformity for causal effects.

## Theoretical Properties

**Theorem (Coverage Guarantee):** Under Assumptions 1-4, the prediction interval $\mathcal{C}_n(X_{n+1})$ satisfies:
$$\mathbb{P}[\tau_{n+1} \in \mathcal{C}_n(X_{n+1})] \geq 1 - \alpha$$

The proof follows by showing that the imputed treatment effects, when weighted appropriately, satisfy a weighted exchangeability property that enables application of weighted conformal prediction theory.

**Consistency:** As $n \to \infty$, if the outcome models $\hat{\mu}_0, \hat{\mu}_1$ converge to the true conditional means, the prediction intervals achieve asymptotically exact coverage while maintaining finite-sample validity.

## Computational Complexity

The algorithm has complexity $O(n \log n + C_{\text{model}})$ where $C_{\text{model}}$ is the cost of fitting the outcome models. The $O(n \log n)$ term comes from computing the weighted quantile, while model fitting dominates in practice. The method scales linearly in the number of training observations and requires no iterative optimization, making it computationally efficient compared to Bayesian or bootstrap-based uncertainty quantification approaches.