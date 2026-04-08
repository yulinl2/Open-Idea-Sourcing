# Reconstruction: problem_method
**Paper:** 2006.06138  
**Condition:** no_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Problem Formulation

## Notation and Setup

We consider the potential outcomes framework for causal inference. Let $\mathcal{X} \subseteq \mathbb{R}^d$ denote the covariate space and $\mathcal{Y} \subseteq \mathbb{R}$ the outcome space. For each individual $i$, we observe a covariate vector $X_i \in \mathcal{X}$, a binary treatment assignment $T_i \in \{0,1\}$, and an outcome $Y_i \in \mathcal{Y}$.

Under the potential outcomes framework, each individual $i$ has two potential outcomes: $Y_i(1)$ representing the outcome under treatment and $Y_i(0)$ representing the outcome under control. The fundamental problem of causal inference is that we only observe one of these potential outcomes:
$$Y_i = T_i Y_i(1) + (1-T_i) Y_i(0)$$

The individual treatment effect (ITE) for individual $i$ is defined as:
$$\tau_i = Y_i(1) - Y_i(0)$$

The conditional average treatment effect (CATE) function is defined as:
$$\tau(x) = \mathbb{E}[Y(1) - Y(0) | X = x] = \mathbb{E}[Y(1) | X = x] - \mathbb{E}[Y(0) | X = x]$$

Let $\mu_1(x) = \mathbb{E}[Y(1) | X = x]$ and $\mu_0(x) = \mathbb{E}[Y(0) | X = x]$ denote the conditional mean functions for treated and control outcomes, respectively. The propensity score is defined as $e(x) = \mathbb{P}[T = 1 | X = x]$.

## Problem Statement

**Given:** A dataset $\mathcal{D} = \{(X_i, T_i, Y_i)\}_{i=1}^n$ drawn from some unknown distribution $P$, and a target covariate vector $x_0 \in \mathcal{X}$.

**Find:** A prediction interval $\mathcal{I}(x_0) = [\hat{L}(x_0), \hat{U}(x_0)]$ for the conditional average treatment effect $\tau(x_0)$.

**Guarantee:** The interval should satisfy finite-sample coverage guarantees:
$$\mathbb{P}[\tau(x_0) \in \mathcal{I}(x_0)] \geq 1 - \alpha$$
for a pre-specified confidence level $1 - \alpha$, where the probability is taken over the randomness in the training data $\mathcal{D}$.

## Objective

Our objective is to construct prediction intervals that provide valid uncertainty quantification for CATE estimates without relying on asymptotic approximations or strong parametric assumptions. Specifically, we seek to minimize the expected interval width:
$$\mathbb{E}[\hat{U}(x_0) - \hat{L}(x_0)]$$
subject to the coverage constraint:
$$\mathbb{P}[\tau(x_0) \in \mathcal{I}(x_0)] \geq 1 - \alpha$$

## Technical Assumptions

We make the following standard assumptions for causal inference:

**Assumption 1 (SUTVA):** The Stable Unit Treatment Value Assumption holds, meaning there are no interference effects between units and treatment variations are irrelevant.

**Assumption 2 (Unconfoundedness):** Treatment assignment is unconfounded given observed covariates:
$$(Y(0), Y(1)) \perp T | X$$

**Assumption 3 (Overlap):** There exists $\epsilon > 0$ such that for all $x$ in the support of $X$:
$$\epsilon \leq e(x) \leq 1 - \epsilon$$

**Assumption 4 (Exchangeability):** The training data $\{(X_i, T_i, Y_i)\}_{i=1}^n$ are exchangeable, which includes the i.i.d. case as a special instance.

These assumptions are standard in the causal inference literature. Unconfoundedness is necessary for identifying causal effects from observational data, while overlap ensures that we have sufficient support for estimation in both treatment groups. The exchangeability assumption is weaker than the typical i.i.d. assumption and is required for conformal prediction methods.

## Connection to Prior Work

This formulation extends classical approaches to CATE estimation by incorporating finite-sample uncertainty quantification. Traditional methods focus on point estimation of $\tau(x)$ using regression adjustment, inverse propensity weighting, or doubly robust estimators. Recent machine learning approaches employ meta-learners such as T-learner, S-learner, and X-learner, but these typically provide only point estimates without reliable uncertainty bounds.

The challenge of uncertainty quantification for CATE estimation differs fundamentally from standard regression problems due to the unobserved nature of individual treatment effects. Standard bootstrap or asymptotic methods may fail due to the complex bias-variance trade-offs inherent in causal estimation and potential model misspecification.

# Methodology

## High-Level Approach

We propose a conformal prediction framework for CATE estimation that provides distribution-free finite-sample coverage guarantees. Our approach, termed **Conformal Causal Prediction (CCP)**, combines flexible machine learning estimators for CATE with conformal inference to construct prediction intervals.

The key insight is to leverage the exchangeability of the data to construct nonconformity scores that capture the uncertainty in CATE estimation. Rather than directly applying conformal prediction to the unobservable individual treatment effects, we develop a novel approach that works with observable quantities while maintaining valid coverage for the target estimand.

## Core Algorithm

Our methodology consists of three main components: (1) CATE estimation using ensemble methods, (2) construction of nonconformity scores based on cross-fitted residuals, and (3) conformal interval construction.

### Step 1: Ensemble CATE Estimation

We employ an ensemble of base learners to estimate the CATE function. Let $\{\hat{\tau}_j\}_{j=1}^J$ denote $J$ different CATE estimators, which may include:
- T-learner: $\hat{\tau}_T(x) = \hat{\mu}_1(x) - \hat{\mu}_0(x)$
- X-learner with cross-fitting
- Causal forests
- Doubly robust learners

The ensemble estimate is constructed as:
$$\hat{\tau}(x) = \frac{1}{J} \sum_{j=1}^J \hat{\tau}_j(x)$$

### Step 2: Nonconformity Score Construction

The challenge in applying conformal prediction to CATE estimation is that individual treatment effects $\tau_i = Y_i(1) - Y_i(0)$ are never observed. We address this by constructing nonconformity scores based on cross-fitted pseudo-outcomes.

We split the data into $K$ folds $\{I_k\}_{k=1}^K$. For each fold $k$, we:

1. Train CATE estimators on $\mathcal{D} \setminus I_k$
2. For each $i \in I_k$, compute the pseudo-outcome:
   $$\tilde{\tau}_i = \frac{T_i (Y_i - \hat{\mu}_0^{(-k)}(X_i))}{\hat{e}^{(-k)}(X_i)} - \frac{(1-T_i)(Y_i - \hat{\mu}_1^{(-k)}(X_i))}{1-\hat{e}^{(-k)}(X_i)}$$

where $\hat{\mu}_t^{(-k)}$ and $\hat{e}^{(-k)}$ are estimates trained on data excluding fold $k$.

The nonconformity score for individual $i$ is then:
$$R_i = |\tilde{\tau}_i - \hat{\tau}^{(-k)}(X_i)|$$

### Step 3: Conformal Interval Construction

Given nonconformity scores $\{R_i\}_{i=1}^n$, we construct the prediction interval for $\tau(x_0)$ as:
$$\mathcal{I}(x_0) = [\hat{\tau}(x_0) - \hat{q}, \hat{\tau}(x_0) + \hat{q}]$$

where $\hat{q}$ is the $(1-\alpha)(1+1/n)$-th quantile of the nonconformity scores $\{R_i\}_{i=1}^n$.

## Complete Algorithm

```
Algorithm: Conformal Causal Prediction (CCP)

Input: Dataset D = {(Xi, Ti, Yi)}_{i=1}^n, target point x0, confidence level 1-α
Output: Prediction interval I(x0) for τ(x0)

1. Data Splitting:
   Split D into K folds {Ik}_{k=1}^K

2. Cross-fitted CATE Estimation:
   For k = 1 to K:
     a. Train μ̂1^(-k), μ̂0^(-k), ê^(-k) on D \ Ik
     b. Train ensemble CATE estimators {τ̂j^(-k)}_{j=1}^J on D \ Ik
     c. For each i ∈ Ik:
        - Compute pseudo-outcome: τ̃i = (Ti(Yi - μ̂0^(-k)(Xi)))/ê^(-k)(Xi) - ((1-Ti)(Yi - μ̂1^(-k)(Xi)))/(1-ê^(-k)(Xi))
        - Compute τ̂^(-k)(Xi) = (1/J)∑_{j=1}^J τ̂j^(-k)(Xi)

3. Nonconformity Score Computation:
   For i = 1 to n:
     Ri = |τ̃i - τ̂^(-k)(Xi)| where k is the fold containing i

4. Final CATE Estimation:
   Train ensemble estimators on full dataset D
   Compute τ̂(x0) = (1/J)∑_{j=1}^J τ̂j(x0)

5. Quantile Computation:
   q̂ = (1-α)(1+1/n)-th quantile of {Ri}_{i=1}^n

6. Interval Construction:
   Return I(x0) = [τ̂(x0) - q̂, τ̂(x0) + q̂]
```

## Design Justifications

**Pseudo-outcome Construction:** The pseudo-outcome $\tilde{\tau}_i$ provides an unbiased estimate of the individual treatment effect under the unconfoundedness assumption. This construction leverages the doubly robust property, making the method robust to misspecification of either the outcome regression or propensity score model.

**Cross-fitting:** We employ cross-fitting to avoid overfitting bias in the nonconformity scores. This ensures that the scores properly capture the prediction uncertainty rather than the fitting uncertainty.

**Ensemble Methods:** Using multiple CATE estimators reduces the dependence on any single modeling choice and improves robustness to model misspecification.

## Theoretical Properties

**Theorem 1 (Finite-sample Coverage):** Under Assumptions 1-4, the prediction interval $\mathcal{I}(x_0)$ satisfies:
$$\mathbb{P}[\tau(x_0) \in \mathcal{I}(x_0)] \geq 1 - \alpha$$

The coverage guarantee holds exactly in finite samples without requiring asymptotic approximations or distributional assumptions beyond exchangeability.

**Theorem 2 (Conditional Coverage):** Under additional regularity conditions on the nonconformity score distribution, approximate conditional coverage can be achieved:
$$\mathbb{P}[\tau(x_0) \in \mathcal{I}(x_0) | X_0 = x_0] \approx 1 - \alpha$$

## Computational Complexity

The computational complexity of CCP is dominated by the ensemble CATE estimation step. For $J$ base learners each with complexity $O(f(n,d))$, the total complexity is $O(K \cdot J \cdot f(n,d))$ where $K$ is the number of cross-validation folds. The conformal inference step adds only $O(n \log n)$ complexity for quantile computation, making it computationally efficient relative to the base estimation procedures.

The method scales well with both sample size and dimensionality, inheriting the scalability properties of the chosen base CATE estimators while adding minimal computational overhead for uncertainty quantification.
