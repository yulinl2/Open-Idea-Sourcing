# Problem Formulation

## Notation and Setup

Let $\mathcal{X} \subseteq \mathbb{R}^d$ denote the covariate space and $\mathcal{Y} \subseteq \mathbb{R}$ the outcome space. For each unit $i$, let $X_i \in \mathcal{X}$ represent observed covariates, $T_i \in \{0,1\}$ the treatment assignment, and $Y_i \in \mathcal{Y}$ the observed outcome. Following the potential outcomes framework, let $Y_i(1)$ and $Y_i(0)$ denote the potential outcomes under treatment and control, respectively, with the fundamental constraint that $Y_i = T_i Y_i(1) + (1-T_i) Y_i(0)$.

The individual treatment effect for unit $i$ is defined as $\tau_i = Y_i(1) - Y_i(0)$. Let $e_i(t) = Y_i(t) - \mu_t(X_i)$ denote the error term for potential outcome $t$, where $\mu_t(x) = \mathbb{E}[Y(t)|X=x]$ represents the conditional mean function. The treatment assignment mechanism is characterized by propensity scores $\pi(x) = \mathbb{P}[T=1|X=x]$.

We observe training data $\mathcal{D}_n = \{(X_i, T_i, Y_i)\}_{i=1}^n$ and seek to construct prediction intervals for the individual treatment effect $\tau$ for a new unit with covariates $X$.

## Problem Statement

**Given:** Training data $\mathcal{D}_n$ from a population $P$ and a new covariate vector $X$ from a potentially different population $\tilde{P}$.

**Find:** A prediction interval $\mathcal{I}_n(X) = [L_n(X), U_n(X)]$ for the unobserved individual treatment effect $\tau(X) = Y(1) - Y(0)$.

**Guarantee:** The interval should satisfy
$$\mathbb{P}_{\tilde{P}}[\tau(X) \in \mathcal{I}_n(X)] \geq 1-\alpha$$
for a pre-specified confidence level $1-\alpha \in (0,1)$, where the probability is taken over both the training data and the new observation under the target distribution $\tilde{P}$.

## Technical Assumptions

**Assumption 1 (Causal Assumptions):** We assume unconfoundedness: $(Y(0), Y(1)) \perp T | X$, and overlap: $0 < \pi(x) < 1$ for all $x$ in the support of $X$.

**Assumption 2 (Covariate Shift):** The training covariates $X_1, \ldots, X_n$ are drawn from distribution $P_X$, while the target covariate $X$ is drawn from distribution $\tilde{P}_X$. The conditional outcome distributions satisfy $P_{Y(t)|X} = \tilde{P}_{Y(t)|X}$ for $t \in \{0,1\}$.

**Assumption 3 (Likelihood Ratio):** The likelihood ratio $w(x) = d\tilde{P}_X/dP_X(x)$ is known or can be estimated accurately. We assume $\mathbb{E}_{P_X}[w(X)] < \infty$.

**Assumption 4 (Exchangeability Structure):** Conditional on treatment assignment, the potential outcomes exhibit a weighted exchangeability property that respects the covariate shift mechanism.

These assumptions are standard in causal inference under covariate shift. Assumption 1 ensures identifiability of causal effects, while Assumption 2 formalizes the covariate shift setting where only the marginal covariate distribution changes between populations. Assumption 3 is necessary for reweighting procedures, following the covariate shift literature. Assumption 4 captures the key insight that the same mechanism creating distributional differences also provides the mathematical structure for correction.

## Connection to Prior Work

Our formulation extends the weighted conformal prediction framework of Tibshirani et al. (2020) from the standard regression setting to causal inference. While Kivaranovic et al. (2020) addressed individual treatment effects using conformal prediction, they assumed exchangeable data without covariate shift. Our approach combines these perspectives, recognizing that the treatment assignment mechanism creates systematic covariate imbalances that must be corrected through appropriate reweighting, similar to how propensity score methods address confounding in causal inference.

# Methodology

## High-Level Approach

Our methodology leverages the fundamental insight that uncertainty quantification for individual treatment effects must respect the constraint that each potential outcome can only be calibrated using data from the corresponding treatment group. We propose a **Weighted Conformal Causal Inference (WCCI)** procedure that combines conformal prediction with importance weighting to handle covariate shift in causal settings.

The key innovation is recognizing that the propensity score mechanism that creates covariate imbalance also provides the reweighting structure needed for valid inference across different populations. We construct separate weighted conformal intervals for each potential outcome, then combine them to obtain intervals for the individual treatment effect.

## Core Algorithm

### Step 1: Propensity Score Estimation and Weight Construction

For each training unit $i$, compute importance weights:
$$w_i = \frac{\tilde{\pi}(X_i)}{\pi(X_i)} \cdot \frac{T_i}{\pi(X_i)} + \frac{1-\tilde{\pi}(X_i)}{1-\pi(X_i)} \cdot \frac{1-T_i}{1-\pi(X_i)}$$

where $\pi(x)$ and $\tilde{\pi}(x)$ are the propensity scores in the training and target populations, respectively.

### Step 2: Outcome Model Fitting

Fit regression models $\hat{\mu}_1$ and $\hat{\mu}_0$ for the treated and control outcomes using any base learning algorithm $\mathcal{A}$.

### Step 3: Weighted Conformal Score Construction

For a candidate value $y$ and treatment level $t \in \{0,1\}$, define nonconformity scores:

For training units in treatment group $t$:
$$V_{i}^{(t)}(X, y) = S((X, y), \{(X_j, Y_j) : T_j = t, j \neq i\})$$

For the test point:
$$V_{n+1}^{(t)}(X, y) = S((X, y), \{(X_j, Y_j) : T_j = t, j = 1, \ldots, n\})$$

where $S$ is a score function, e.g., $S((x,y), \mathcal{Z}) = |y - \hat{\mu}_t(x)|$ for absolute residuals.

### Step 4: Weighted Quantile Computation

For each treatment level $t$, compute weighted quantiles:
$$Q_t^{(1-\alpha/2)}(X) = \text{Quantile}\left(1-\frac{\alpha}{2}; \sum_{i: T_i=t} \tilde{w}_i^{(t)}(X) \delta_{V_i^{(t)}(X, y)} + \tilde{w}_{n+1}^{(t)}(X) \delta_{\infty}\right)$$

where the normalized weights are:
$$\tilde{w}_i^{(t)}(X) = \frac{w_i}{\sum_{j: T_j=t} w_j + w(X)}, \quad \tilde{w}_{n+1}^{(t)}(X) = \frac{w(X)}{\sum_{j: T_j=t} w_j + w(X)}$$

### Step 5: Individual Potential Outcome Intervals

Construct prediction intervals for each potential outcome:
$$\mathcal{C}_t(X) = \left\{y : V_{n+1}^{(t)}(X, y) \leq Q_t^{(1-\alpha/2)}(X)\right\}$$

### Step 6: Treatment Effect Interval Construction

Combine the potential outcome intervals using Minkowski arithmetic:
$$\mathcal{I}_n(X) = \mathcal{C}_1(X) \ominus \mathcal{C}_0(X) = \{y_1 - y_0 : y_1 \in \mathcal{C}_1(X), y_0 \in \mathcal{C}_0(X)\}$$

## Detailed Algorithm

```
Algorithm: Weighted Conformal Causal Inference (WCCI)

Input: Training data D_n = {(X_i, T_i, Y_i)}_{i=1}^n
       Test covariate X
       Confidence level 1-α
       Score function S
       Base learner A

1. Estimate propensity scores:
   π̂(x) ← fit propensity model on D_n
   
2. Compute importance weights:
   For i = 1, ..., n:
     w_i ← compute_weight(X_i, π̂, target_distribution)
   w_test ← compute_weight(X, π̂, target_distribution)

3. Fit outcome models:
   μ̂_1 ← A({(X_i, Y_i) : T_i = 1})
   μ̂_0 ← A({(X_i, Y_i) : T_i = 0})

4. For each treatment level t ∈ {0, 1}:
   
   4.1. Compute nonconformity scores:
        For i such that T_i = t:
          V_i^(t) ← S((X_i, Y_i), D_{-i} ∩ {T_j = t})
   
   4.2. For each candidate y:
        V_test^(t)(y) ← S((X, y), {(X_j, Y_j) : T_j = t})
   
   4.3. Compute weighted quantile:
        Q_t ← WeightedQuantile(1-α/2, {V_i^(t), w_i}, w_test)
   
   4.4. Construct potential outcome interval:
        C_t(X) ← {y : V_test^(t)(y) ≤ Q_t}

5. Construct treatment effect interval:
   I_n(X) ← C_1(X) ⊖ C_0(X)

Output: Prediction interval I_n(X) for τ(X)
```

## Theoretical Properties

**Theorem (Finite-Sample Coverage):** Under Assumptions 1-4, the WCCI procedure satisfies:
$$\mathbb{P}_{\tilde{P}}[\tau(X) \in \mathcal{I}_n(X)] \geq 1-\alpha$$

The proof follows by extending the weighted exchangeability arguments from Tibshirani et al. (2020) to the causal setting, leveraging the fact that the reweighting procedure creates exchangeability between the training and test nonconformity scores within each treatment group.

**Robustness Property:** The method maintains validity even if either the propensity score model or the outcome regression models are misspecified, provided the importance weights are computed correctly.

## Computational Complexity

The algorithm has complexity $O(n \log n)$ for the weighted quantile computations, plus the cost of fitting the base learners. For split conformal variants, the outcome models are fit only once, reducing computational burden. The method scales efficiently to high-dimensional settings when combined with modern machine learning algorithms.

## Design Justifications

The use of separate intervals for each potential outcome respects the fundamental constraint that treated units can only inform about treated outcomes. The Minkowski arithmetic combination follows from the linearity of the treatment effect definition. The weighted quantile approach directly addresses covariate shift while maintaining the distribution-free nature of conformal prediction, providing a principled solution that leverages the mathematical structure inherent in the treatment assignment mechanism.