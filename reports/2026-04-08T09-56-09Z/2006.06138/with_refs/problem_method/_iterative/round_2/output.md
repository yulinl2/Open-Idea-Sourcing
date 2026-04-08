# Problem Formulation

## Notation and Setup

Let $(\mathbf{X}, Y(0), Y(1)) \in \mathcal{X} \times \mathcal{Y} \times \mathcal{Y}$ denote the potential outcomes for an individual, where $\mathbf{X} \in \mathcal{X} \subseteq \mathbb{R}^d$ represents covariates, and $Y(0), Y(1) \in \mathcal{Y} \subseteq \mathbb{R}$ represent potential outcomes under control and treatment conditions, respectively. Let $T \in \{0,1\}$ denote the treatment assignment, and define the observed outcome as $Y = TY(1) + (1-T)Y(0)$.

Consider a training dataset $\mathcal{D}_n = \{(\mathbf{X}_i, T_i, Y_i)\}_{i=1}^n$ where each observation consists of covariates, treatment assignment, and the corresponding observed outcome. For a new individual with covariates $\mathbf{X}_{n+1}$, we observe only one potential outcome depending on treatment assignment $T_{n+1}$, while the counterfactual outcome remains unobserved.

Let $P$ denote the joint distribution of $(\mathbf{X}, T, Y(0), Y(1))$ in the training population, and let $\tilde{P}$ denote the corresponding distribution in the target population where predictions are desired. We allow for covariate shift between training and target populations, meaning $P_{\mathbf{X}} \neq \tilde{P}_{\mathbf{X}}$ while maintaining $P_{Y(0),Y(1)|\mathbf{X}} = \tilde{P}_{Y(0),Y(1)|\mathbf{X}}$.

## Problem Statement

**Given:** 
- Training data $\mathcal{D}_n = \{(\mathbf{X}_i, T_i, Y_i)\}_{i=1}^n$
- A new individual with covariates $\mathbf{X}_{n+1}$ and treatment assignment $T_{n+1}$
- Desired coverage level $1-\alpha$ for $\alpha \in (0,1)$
- Likelihood ratio $w(\mathbf{x}) = d\tilde{P}_{\mathbf{X}}(\mathbf{x})/dP_{\mathbf{X}}(\mathbf{x})$ (known or estimable)

**Find:** Prediction intervals $\hat{C}_{n,0}(\mathbf{X}_{n+1})$ and $\hat{C}_{n,1}(\mathbf{X}_{n+1})$ for both potential outcomes $Y_{n+1}(0)$ and $Y_{n+1}(1)$.

**Guarantee:** The intervals should satisfy finite-sample coverage guarantees:
$$\mathbb{P}\left(Y_{n+1}(t) \in \hat{C}_{n,t}(\mathbf{X}_{n+1})\right) \geq 1-\alpha$$
for $t \in \{0,1\}$, where the probability is taken over the randomness in both training and test data.

## Objective

Our objective is to construct distribution-free prediction intervals that provide valid uncertainty quantification for individual potential outcomes without relying on:
- Asymptotic approximations
- Strong parametric modeling assumptions  
- Exchangeability between training and target populations

The key insight is to treat the prediction of each potential outcome $Y(0)$ and $Y(1)$ as separate prediction problems, leveraging the subset of training data where each outcome is observed, while accounting for covariate shift through appropriate weighting.

## Technical Assumptions

**Assumption 1 (Stable Unit Treatment Value):** The potential outcomes for individual $i$ depend only on their own treatment assignment: $Y_i(t) = Y_i(t, \mathbf{T})$ for any treatment vector $\mathbf{T}$ with $T_i = t$.

**Assumption 2 (Unconfoundedness):** Treatment assignment is unconfounded given observed covariates:
$$Y(0), Y(1) \perp T \mid \mathbf{X}$$

**Assumption 3 (Positivity):** For all $\mathbf{x}$ in the support of $\mathbf{X}$:
$$0 < \mathbb{P}(T = t \mid \mathbf{X} = \mathbf{x}) < 1 \quad \text{for } t \in \{0,1\}$$

**Assumption 4 (Covariate Shift):** The target population differs from the training population only in covariate distribution:
$$\tilde{P}_{Y(0),Y(1)|\mathbf{X}} = P_{Y(0),Y(1)|\mathbf{X}}$$
while $\tilde{P}_{\mathbf{X}} \neq P_{\mathbf{X}}$ in general.

**Assumption 5 (Absolute Continuity):** The target covariate distribution is absolutely continuous with respect to the training distribution: $\tilde{P}_{\mathbf{X}} \ll P_{\mathbf{X}}$.

**Assumption 6 (Known or Estimable Likelihood Ratio):** The likelihood ratio $w(\mathbf{x}) = d\tilde{P}_{\mathbf{X}}(\mathbf{x})/dP_{\mathbf{X}}(\mathbf{x})$ is either known or can be estimated accurately from auxiliary data.

These assumptions are standard in the causal inference literature and enable the identification and estimation of potential outcomes. Assumption 4-6 extend the framework to handle distribution shift, which is crucial for practical applications where the study population may differ from the target population.

# Methodology

## High-Level Approach

Our approach recognizes that predicting counterfactual outcomes requires fundamentally different treatment from standard prediction problems. Rather than attempting to directly estimate conditional average treatment effects, we construct separate prediction intervals for each potential outcome $Y(0)$ and $Y(1)$ by adapting weighted conformal prediction to the causal setting.

The key insight is to partition the training data by treatment assignment and apply weighted conformal prediction separately to each subset, using appropriate importance weights to account for covariate shift. This approach naturally handles the fundamental asymmetry in causal inference: we observe $Y(0)$ only for control units and $Y(1)$ only for treated units.

## Core Algorithm: Weighted Causal Conformal Prediction

For each potential outcome $Y(t)$ where $t \in \{0,1\}$, we construct prediction intervals using the following procedure:

### Step 1: Data Partitioning
Partition the training data by treatment assignment:
- $\mathcal{D}_{n,0} = \{(\mathbf{X}_i, Y_i) : T_i = 0, i = 1,\ldots,n\}$ with $|\mathcal{D}_{n,0}| = n_0$
- $\mathcal{D}_{n,1} = \{(\mathbf{X}_i, Y_i) : T_i = 1, i = 1,\ldots,n\}$ with $|\mathcal{D}_{n,1}| = n_1$

### Step 2: Score Function Definition
Define a score function $S_t(\mathbf{x}, y, \mathcal{Z})$ that measures how well the point $(\mathbf{x}, y)$ conforms to the dataset $\mathcal{Z}$. For computational efficiency, we use a split conformal approach with absolute residuals:

$$S_t(\mathbf{x}, y, \mathcal{Z}) = |y - \hat{\mu}_t(\mathbf{x})|$$

where $\hat{\mu}_t(\mathbf{x})$ is a regression function fitted on a separate training set for outcome $t$.

### Step 3: Nonconformity Score Computation
For a test point $(\mathbf{X}_{n+1}, y)$ and treatment $t$, compute nonconformity scores:

$$V_i^{(t)}(\mathbf{X}_{n+1}, y) = S_t(\mathbf{X}_j, Y_j, \mathcal{D}_{n,t} \setminus \{(\mathbf{X}_j, Y_j)\} \cup \{(\mathbf{X}_{n+1}, y)\})$$

for each $(\mathbf{X}_j, Y_j) \in \mathcal{D}_{n,t}$, and

$$V_{n_t+1}^{(t)}(\mathbf{X}_{n+1}, y) = S_t(\mathbf{X}_{n+1}, y, \mathcal{D}_{n,t})$$

### Step 4: Weight Computation
Define importance weights to account for covariate shift:

$$\tilde{w}_j^{(t)}(\mathbf{X}_{n+1}) = \frac{w(\mathbf{X}_j)}{\sum_{k: T_k = t} w(\mathbf{X}_k) + w(\mathbf{X}_{n+1})}$$

for $j$ such that $T_j = t$, and

$$\tilde{w}_{n_t+1}^{(t)}(\mathbf{X}_{n+1}) = \frac{w(\mathbf{X}_{n+1})}{\sum_{k: T_k = t} w(\mathbf{X}_k) + w(\mathbf{X}_{n+1})}$$

### Step 5: Weighted Conformal Prediction
The prediction interval for potential outcome $Y(t)$ is:

$$\hat{C}_{n,t}(\mathbf{X}_{n+1}) = \left\{y \in \mathbb{R} : V_{n_t+1}^{(t)}(\mathbf{X}_{n+1}, y) \leq Q_{1-\alpha}^{(t)}(\mathbf{X}_{n+1})\right\}$$

where $Q_{1-\alpha}^{(t)}(\mathbf{X}_{n+1})$ is the $(1-\alpha)$-quantile of the weighted distribution:

$$Q_{1-\alpha}^{(t)}(\mathbf{X}_{n+1}) = \text{Quantile}\left(1-\alpha; \sum_{j: T_j = t} \tilde{w}_j^{(t)}(\mathbf{X}_{n+1}) \delta_{V_j^{(t)}(\mathbf{X}_{n+1}, y)} + \tilde{w}_{n_t+1}^{(t)}(\mathbf{X}_{n+1}) \delta_{\infty}\right)$$

## Algorithm Implementation

```
Algorithm: Weighted Causal Conformal Prediction

Input: 
  - Training data D_n = {(X_i, T_i, Y_i)}_{i=1}^n
  - Test covariate X_{n+1}
  - Coverage level 1-α
  - Likelihood ratio function w(·)

Output: Prediction intervals C_{n,0}(X_{n+1}), C_{n,1}(X_{n+1})

1. Split training data by treatment:
   D_{n,0} ← {(X_i, Y_i) : T_i = 0}
   D_{n,1} ← {(X_i, Y_i) : T_i = 1}

2. For t ∈ {0,1}:
   a. Fit regression function μ̂_t on D_{n,t}
   
   b. For each candidate y:
      - Compute nonconformity scores:
        V_j^{(t)}(y) ← |Y_j - μ̂_t(X_j)| for (X_j, Y_j) ∈ D_{n,t}
        V_{n_t+1}^{(t)}(y) ← |y - μ̂_t(X_{n+1})|
      
      - Compute importance weights:
        w̃_j^{(t)} ← w(X_j) / [∑_{k:T_k=t} w(X_k) + w(X_{n+1})]
        w̃_{n_t+1}^{(t)} ← w(X_{n+1}) / [∑_{k:T_k=t} w(X_k) + w(X_{n+1})]
      
      - Compute weighted quantile:
        Q_{1-α}^{(t)} ← Quantile(1-α; ∑_j w̃_j^{(t)} δ_{V_j^{(t)}} + w̃_{n_t+1}^{(t)} δ_∞)
   
   c. Construct prediction interval:
      Ĉ_{n,t}(X_{n+1}) ← {y : V_{n_t+1}^{(t)}(y) ≤ Q_{1-α}^{(t)}}

3. Return Ĉ_{n,0}(X_{n+1}), Ĉ_{n,1}(X_{n+1})
```

## Theoretical Properties

**Theorem (Coverage Guarantee):** Under Assumptions 1-6, for each $t \in \{0,1\}$:

$$\mathbb{P}\left(Y_{n+1}(t) \in \hat{C}_{n,t}(\mathbf{X}_{n+1})\right) \geq 1-\alpha$$

This result follows from extending the weighted conformal prediction framework to the causal setting, where the key insight is that within each treatment group, the weighted nonconformity scores achieve the desired exchangeability property needed for coverage guarantees.

**Computational Complexity:** The algorithm has complexity $O(n \cdot |\mathcal{Y}|)$ for discrete outcomes or $O(n \log n)$ for continuous outcomes using efficient quantile computation, making it scalable to moderate-sized datasets.

## Design Justifications

1. **Separate Treatment of Potential Outcomes:** By constructing separate intervals for $Y(0)$ and $Y(1)$, we avoid the need to model the joint distribution of potential outcomes, which is fundamentally unidentifiable.

2. **Weighted Conformal Framework:** The importance weighting scheme directly addresses covariate shift by reweighting training observations to match the target population, extending the conformal prediction guarantees to the distribution shift setting.

3. **Split Conformal Approach:** Using pre-fitted regression functions avoids the computational burden of refitting models for each candidate prediction while maintaining coverage guarantees.

4. **Treatment-Specific Modeling:** Fitting separate models $\hat{\mu}_0$ and $\hat{\mu}_1$ allows for different functional relationships between covariates and outcomes under different treatments, increasing flexibility without compromising theoretical guarantees.