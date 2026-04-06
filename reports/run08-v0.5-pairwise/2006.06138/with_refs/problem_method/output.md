# Reconstruction: problem_method
**Paper:** 2006.06138  
**Condition:** with_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Problem Formulation

## Notation and Setup

Let $(\mathcal{X}, \mathcal{Y}) = \mathbb{R}^d \times \mathbb{R}$ denote the covariate and outcome spaces. We consider the potential outcomes framework where each unit $i$ has two potential outcomes: $Y_i(0)$ under control and $Y_i(1)$ under treatment. The observed data consists of $n$ units $\{(X_i, T_i, Y_i)\}_{i=1}^n$ where $X_i \in \mathcal{X}$ are covariates, $T_i \in \{0,1\}$ is the treatment assignment, and $Y_i = T_i Y_i(1) + (1-T_i)Y_i(0)$ is the observed outcome.

The individual treatment effect (ITE) for unit $i$ is defined as $\tau_i = Y_i(1) - Y_i(0)$. The conditional average treatment effect (CATE) function is $\tau(x) = \mathbb{E}[Y(1) - Y(0) | X = x]$, where the expectation is taken over the population distribution.

Let $P$ denote the joint distribution of $(X, T, Y(0), Y(1))$ and $P_X$ the marginal distribution of covariates. We distinguish between two inference targets:
- **Within-study inference**: For a unit $i$ in the study with observed $(X_i, T_i, Y_i)$, construct a prediction interval for the unobserved potential outcome $Y_i(1-T_i)$ and hence for $\tau_i$.
- **Out-of-study inference**: For a new unit with covariates $X_{\text{new}}$ drawn from a potentially different distribution $\tilde{P}_X$, construct a prediction interval for $\tau_{\text{new}} = Y_{\text{new}}(1) - Y_{\text{new}}(0)$.

## Formal Problem Statement

**Given**: Training data $\mathcal{D} = \{(X_i, T_i, Y_i)\}_{i=1}^n$ and a target coverage level $1-\alpha \in (0,1)$.

**Find**: A prediction interval construction $\hat{C}_n: \mathcal{X} \rightarrow 2^{\mathbb{R}}$ that produces intervals $\hat{C}_n(x)$ for the individual treatment effect $\tau(x)$.

**Guarantee**: The intervals should satisfy finite-sample coverage guarantees:
1. **Within-study coverage**: For any $i \in \{1,\ldots,n\}$,
   $$\mathbb{P}[\tau_i \in \hat{C}_n(X_i)] \geq 1-\alpha$$
2. **Out-of-study coverage under covariate shift**: For $X_{\text{new}} \sim \tilde{P}_X$ with known likelihood ratio $w(x) = d\tilde{P}_X(x)/dP_X(x)$,
   $$\mathbb{P}[\tau_{\text{new}} \in \hat{C}_n(X_{\text{new}})] \geq 1-\alpha$$

## Technical Assumptions

**A1. Unconfoundedness**: $(Y(0), Y(1)) \perp T | X$, ensuring that treatment assignment is ignorable given observed covariates.

**A2. Overlap**: $0 < \pi(x) < 1$ for all $x$ in the support of $P_X$, where $\pi(x) = \mathbb{P}[T=1|X=x]$ is the propensity score.

**A3. Absolute continuity**: For out-of-study inference, $\tilde{P}_X \ll P_X$ with bounded likelihood ratio $w(x) = d\tilde{P}_X(x)/dP_X(x)$.

**A4. Regularity**: The outcome regression functions $\mu_0(x) = \mathbb{E}[Y(0)|X=x]$ and $\mu_1(x) = \mathbb{E}[Y(1)|X=x]$ are well-defined and measurable.

These assumptions are standard in the causal inference literature. A1 and A2 enable identification of causal effects from observational data, while A3 allows for distribution-free inference under covariate shift by extending the weighted conformal prediction framework of Tibshirani et al. (2020).

## Connection to Prior Work

Our formulation builds directly on the conformal prediction framework, particularly the extension to covariate shift in Tibshirani et al. (2020). However, the causal inference setting introduces fundamental challenges: the target quantity $\tau_i$ is never directly observed, requiring us to construct nonconformity scores based on predicted counterfactuals rather than observed residuals. This necessitates a novel adaptation of weighted exchangeability to handle the missing data structure inherent in causal inference.

# Methodology

## Overview

Our approach, **Conformal Causal Prediction (CCP)**, extends weighted conformal prediction to handle the missing counterfactual problem in causal inference. The key insight is to construct nonconformity scores using estimated individual treatment effects while maintaining the exchangeability properties required for valid coverage.

## Core Algorithm

### Step 1: Outcome Regression and CATE Estimation

We first estimate the outcome regression functions and CATE using any base learning algorithm:

```
1. Split data D into training D_train and calibration D_cal sets
2. Fit outcome regressors μ̂_0 and μ̂_1 on D_train:
   - μ̂_0(x) ← regression of {Y_i : T_i = 0} on {X_i : T_i = 0}  
   - μ̂_1(x) ← regression of {Y_i : T_i = 1} on {X_i : T_i = 1}
3. Estimate CATE: τ̂(x) = μ̂_1(x) - μ̂_0(x)
```

### Step 2: Nonconformity Score Construction

For each unit $i$ in the calibration set, we define the nonconformity score as:

$$V_i = |Y_i - \hat{\mu}_{T_i}(X_i)| + |\hat{\tau}(X_i) - \tau_{\text{pseudo},i}|$$

where $\tau_{\text{pseudo},i} = Y_i - \hat{\mu}_{1-T_i}(X_i)$ is a pseudo-treatment effect that uses the observed outcome and predicted counterfactual.

This score captures both the quality of outcome prediction and the uncertainty in treatment effect estimation. The first term measures how well we predict the observed outcome, while the second term measures the discrepancy between our CATE estimate and the pseudo-treatment effect.

### Step 3: Weighted Conformal Intervals

For a target point $x$, we construct the prediction interval using weighted quantiles:

```
For target point x:
1. Compute weights for covariate shift:
   w_i(x) = dP̃_X(X_i)/dP_X(X_i) for i in calibration set
   w_{n+1}(x) = dP̃_X(x)/dP_X(x) for target point

2. Normalize weights:
   p̃_i(x) = w_i(x) / (∑_{j∈cal} w_j(x) + w_{n+1}(x))
   p̃_{n+1}(x) = w_{n+1}(x) / (∑_{j∈cal} w_j(x) + w_{n+1}(x))

3. Compute weighted quantile:
   q_{1-α}(x) = Quantile(1-α; ∑_{i∈cal} p̃_i(x)δ_{V_i} + p̃_{n+1}(x)δ_∞)

4. Return interval:
   Ĉ_n(x) = τ̂(x) ± q_{1-α}(x)
```

### Step 4: Algorithm for Both Settings

**Algorithm 1: Conformal Causal Prediction**
```
Input: Data D = {(X_i, T_i, Y_i)}_{i=1}^n, coverage level 1-α, 
       weight function w(·) (identity for within-study)

1. Randomly split D into D_train (50%) and D_cal (50%)

2. Train base models on D_train:
   μ̂_0, μ̂_1 ← FitOutcomeModels(D_train)
   τ̂(x) ← μ̂_1(x) - μ̂_0(x)

3. Compute nonconformity scores on D_cal:
   For each (X_i, T_i, Y_i) ∈ D_cal:
     τ_pseudo,i ← Y_i - μ̂_{1-T_i}(X_i)  
     V_i ← |Y_i - μ̂_{T_i}(X_i)| + |τ̂(X_i) - τ_pseudo,i|

4. For target point x:
   Compute weights: p̃_i(x) as in Step 3 above
   q_{1-α}(x) ← WeightedQuantile(1-α, {V_i}, {p̃_i(x)})
   Return Ĉ_n(x) = τ̂(x) ± q_{1-α}(x)
```

## Theoretical Justification

**Theorem** (Finite-Sample Coverage): Under assumptions A1-A4, Algorithm 1 satisfies:
1. $\mathbb{P}[\tau_i \in \hat{C}_n(X_i)] \geq 1-\alpha$ for within-study inference
2. $\mathbb{P}[\tau_{\text{new}} \in \hat{C}_n(X_{\text{new}})] \geq 1-\alpha$ under covariate shift

The proof follows by establishing that the nonconformity scores maintain weighted exchangeability. The key insight is that our score construction ensures that $V_i$ measures the total prediction error for unit $i$'s treatment effect, and the weighted quantile procedure from Tibshirani et al. (2020) provides the desired coverage guarantees.

## Design Justifications

**Nonconformity Score Design**: Our two-component score balances outcome prediction accuracy with treatment effect uncertainty. The first component $|Y_i - \hat{\mu}_{T_i}(X_i)|$ is a standard conformal score for the observed outcome. The second component $|\hat{\tau}(X_i) - \tau_{\text{pseudo},i}|$ captures the additional uncertainty from estimating the unobserved counterfactual.

**Weighted Extension**: We directly leverage the covariate shift methodology from Tibshirani et al. (2020), applying their weighted quantile approach to our causal nonconformity scores. This ensures distribution-free validity under covariate shift without additional parametric assumptions.

**Sample Splitting**: Following standard practice in conformal prediction, we split the data to ensure that the nonconformity scores are computed on independent data from the model fitting, preserving the exchangeability required for coverage guarantees.

## Computational Complexity

The algorithm has complexity $O(n \log n)$ per target point, dominated by the weighted quantile computation. The base model fitting step depends on the chosen regression algorithm but is performed only once. For $m$ target points, the total complexity is $O(n \log n \cdot m + \text{ModelFitting}(n))$, making it computationally efficient for practical applications.
