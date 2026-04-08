# Problem Formulation

## 1. Problem Formulation

### 1.1 Notation and Setup

Let $\mathcal{X} \subseteq \mathbb{R}^d$ denote the covariate space and $\mathcal{Y} \subseteq \mathbb{R}$ the outcome space. We work within the potential outcomes framework where each unit $i$ has two potential outcomes: $Y_i(1)$ under treatment and $Y_i(0)$ under control. The observed outcome is $Y_i = T_i Y_i(1) + (1-T_i) Y_i(0)$ where $T_i \in \{0,1\}$ is the treatment assignment.

Let $\{(X_i, T_i, Y_i)\}_{i=1}^n$ denote our training sample where $(X_i, T_i, Y_i) \sim P$ for some unknown distribution $P$. For a new unit with covariates $X_{n+1}$, we seek to construct prediction intervals for the unobserved potential outcomes $Y_{n+1}(1)$ and $Y_{n+1}(0)$.

Define the conditional average treatment effect (CATE) as:
$$\tau(x) = \mathbb{E}[Y(1) - Y(0) | X = x]$$

Our primary goal is to construct prediction intervals $\hat{I}_1(x)$ and $\hat{I}_0(x)$ such that for a new unit with covariates $x$:
$$P(Y(1) \in \hat{I}_1(x)) \geq 1-\alpha \quad \text{and} \quad P(Y(0) \in \hat{I}_0(x)) \geq 1-\alpha$$

### 1.2 Formal Problem Statement

**Given:** 
- Training data $\mathcal{D} = \{(X_i, T_i, Y_i)\}_{i=1}^n$
- Confidence level $1-\alpha \in (0,1)$
- Test covariate $X_{n+1}$ (possibly from a different distribution than training covariates)

**Find:** Prediction intervals $\hat{I}_1(X_{n+1})$ and $\hat{I}_0(X_{n+1})$ for potential outcomes $Y_{n+1}(1)$ and $Y_{n+1}(0)$

**Guarantee:** The intervals should satisfy finite-sample coverage:
$$P(Y_{n+1}(1) \in \hat{I}_1(X_{n+1})) \geq 1-\alpha \quad \text{and} \quad P(Y_{n+1}(0) \in \hat{I}_0(X_{n+1})) \geq 1-\alpha$$

where the probability is taken over the randomness in the training data and the test unit.

### 1.3 Technical Assumptions

**Assumption 1 (Stable Unit Treatment Value):** The potential outcomes for unit $i$ are unaffected by the treatment assignments of other units.

**Assumption 2 (Unconfoundedness):** $(Y(1), Y(0)) \perp T | X$, meaning treatment assignment is conditionally independent of potential outcomes given covariates.

**Assumption 3 (Positivity):** There exist constants $c_1, c_2 > 0$ such that $c_1 \leq P(T=1|X=x) \leq 1-c_2$ for all $x$ in the support of $X$.

**Assumption 4 (Covariate Shift):** The training and test covariates may come from different distributions $P_X$ and $\tilde{P}_X$ respectively, but the conditional outcome distributions remain unchanged: $P_{Y(t)|X} = \tilde{P}_{Y(t)|X}$ for $t \in \{0,1\}$.

**Assumption 5 (Known Likelihood Ratio):** When covariate shift is present, we assume knowledge of or ability to estimate the likelihood ratio $w(x) = d\tilde{P}_X(x)/dP_X(x)$.

### 1.4 Connection to Prior Work

This formulation extends conformal prediction methodology to the causal inference setting. Standard conformal prediction (Vovk et al., 2005) provides distribution-free prediction intervals under exchangeability, while the weighted conformal approach (Tibshirani et al., 2020) handles covariate shift. Our key insight is that predicting counterfactual outcomes requires treating each potential outcome as a separate prediction problem, where we observe only one outcome per unit but can leverage the structure imposed by causal assumptions.

The fundamental challenge is that for any individual, we never observe both $Y(1)$ and $Y(0)$, making standard prediction interval construction impossible. However, by recognizing that units with different treatment assignments but similar covariates provide information about each other's counterfactual outcomes, we can construct valid intervals through a careful adaptation of conformal methodology.

# Methodology

## 2. Methodology

### 2.1 High-Level Approach

Our approach decomposes the problem of constructing treatment effect intervals into two separate potential outcome prediction problems. For each potential outcome $Y(t)$ where $t \in \{0,1\}$, we construct prediction intervals using a weighted conformal prediction framework that accounts for both the missing counterfactual structure and potential covariate shift.

The key insight is to treat units receiving treatment $t$ as providing direct observations of $Y(t)$, while using the causal assumptions to appropriately weight and utilize information from all units when constructing prediction intervals. This approach naturally handles the fundamental problem of causal inference while providing finite-sample coverage guarantees.

### 2.2 Weighted Conformal Prediction for Potential Outcomes

For each treatment level $t \in \{0,1\}$, we construct prediction intervals using a modified conformal prediction procedure. Let $\mathcal{I}_t = \{i : T_i = t\}$ denote the indices of units receiving treatment $t$, and define $n_t = |\mathcal{I}_t|$.

**Step 1: Score Function Definition**
For treatment level $t$, we define a nonconformity score function $S_t$ that measures how well a potential outcome value conforms to the observed data. A natural choice is:
$$S_t((x,y), \mathcal{D}) = |y - \hat{\mu}_t(x)|$$
where $\hat{\mu}_t(x)$ is a regression function estimating $\mathbb{E}[Y(t)|X=x]$ fitted on units with $T_i = t$.

**Step 2: Weighted Nonconformity Scores**
For a test point $(x,y)$ and treatment level $t$, we compute nonconformity scores:
$$V_i^{(t)}(x,y) = S_t((X_i, Y_i), \mathcal{D}_{-i} \cup \{(x,y)\}) \quad \text{for } i \in \mathcal{I}_t$$
$$V_{n+1}^{(t)}(x,y) = S_t((x,y), \mathcal{D})$$

To handle covariate shift, we weight these scores using propensity-adjusted likelihood ratios:
$$\tilde{w}_i(x) = w(X_i) \cdot \frac{\pi_t(X_i)}{\pi_t(x)} \quad \text{for } i \in \mathcal{I}_t$$
where $w(X_i) = d\tilde{P}_X(X_i)/dP_X(X_i)$ is the covariate shift weight and $\pi_t(x) = P(T=t|X=x)$ is the propensity score.

### 2.3 Core Algorithm

```
Algorithm: Causal Conformal Prediction Intervals

Input: Training data D = {(Xi, Ti, Yi)}_{i=1}^n
       Test covariate x
       Confidence level α
       Likelihood ratio function w(·) [if covariate shift present]

Output: Prediction intervals Î₁(x) and Î₀(x)

1. For each treatment level t ∈ {0,1}:
   a. Identify treated units: It = {i : Ti = t}
   b. Fit outcome model: μ̂t = fit_model({(Xi, Yi) : i ∈ It})
   c. Estimate propensity scores: π̂t(·) = fit_propensity_model(D)

2. For each treatment level t ∈ {0,1}:
   a. For each y ∈ R:
      i. Compute nonconformity scores:
         - For i ∈ It: Vi^(t)(x,y) = |Yi - μ̂t(Xi)|
         - V_{n+1}^(t)(x,y) = |y - μ̂t(x)|
      
      ii. Compute weights:
         - For i ∈ It: w̃i(x) = w(Xi) · π̂t(Xi)/π̂t(x)
         - w̃_{n+1}(x) = w(x)
      
      iii. Normalize weights:
         - p̃i^w(x) = w̃i(x) / (∑_{j∈It} w̃j(x) + w̃_{n+1}(x))
         - p̃_{n+1}^w(x) = w̃_{n+1}(x) / (∑_{j∈It} w̃j(x) + w̃_{n+1}(x))
   
   b. Construct prediction interval:
      Ît(x) = {y ∈ R : V_{n+1}^(t)(x,y) ≤ Quantile(1-α, ∑_{i∈It} p̃i^w(x)δ_{Vi^(t)(x,y)} + p̃_{n+1}^w(x)δ_∞)}

3. Return intervals Î₁(x) and Î₀(x)
```

### 2.4 Split Conformal Variant

For computational efficiency, we provide a split conformal variant:

```
Algorithm: Split Causal Conformal Prediction

Input: Training data D = {(Xi, Ti, Yi)}_{i=1}^n split into Dpre and Dcal
       Test covariate x, confidence level α

1. Fit models on Dpre:
   - μ̂₁ = fit_model({(Xi, Yi) : i ∈ Dpre, Ti = 1})
   - μ̂₀ = fit_model({(Xi, Yi) : i ∈ Dpre, Ti = 0})
   - π̂(·) = fit_propensity_model(Dpre)

2. For each treatment level t ∈ {0,1}:
   a. Compute residuals on calibration set:
      Ri^(t) = |Yi - μ̂t(Xi)| for i ∈ Dcal with Ti = t
   
   b. Construct interval:
      Ît(x) = μ̂t(x) ± Quantile(1-α, {w̃i(x)Ri^(t) : i ∈ Dcal, Ti = t} ∪ {∞})
```

### 2.5 Theoretical Properties

**Theorem (Coverage Guarantee):** Under Assumptions 1-5, the prediction intervals $\hat{I}_1(x)$ and $\hat{I}_0(x)$ constructed by our algorithm satisfy:
$$P(Y_{n+1}(1) \in \hat{I}_1(X_{n+1})) \geq 1-\alpha$$
$$P(Y_{n+1}(0) \in \hat{I}_0(X_{n+1})) \geq 1-\alpha$$

The key insight in the proof is that the weighted nonconformity scores become exchangeable after appropriate reweighting, extending the fundamental exchangeability property underlying conformal prediction to the causal setting.

### 2.6 Design Justifications

**Separate Treatment of Potential Outcomes:** By constructing separate intervals for $Y(1)$ and $Y(0)$, we avoid the need to model their joint distribution, which is fundamentally unidentifiable from observational data.

**Propensity Score Weighting:** The inclusion of propensity scores $\pi_t(x)$ in the weights ensures that the conformal procedure properly accounts for the selection mechanism determining treatment assignment.

**Robustness to Model Misspecification:** Following the conformal prediction paradigm, our method maintains coverage guarantees even when the outcome models $\hat{\mu}_t$ are misspecified, as long as the propensity score model or the covariate shift weights are reasonably accurate.

### 2.7 Computational Complexity

The computational complexity is $O(n \cdot |\mathcal{Y}|)$ for the full conformal version, where $|\mathcal{Y}|$ represents the discretization of the outcome space. The split conformal variant reduces this to $O(n)$ after the initial model fitting phase, making it practical for large datasets. The method scales linearly with the number of training samples and can be easily parallelized across different outcome values or treatment levels.