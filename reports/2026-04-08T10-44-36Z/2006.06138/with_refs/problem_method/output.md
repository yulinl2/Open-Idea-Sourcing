# Reconstruction: problem_method (iterative, 5 rounds)
**Paper:** 2006.06138  
**Condition:** with_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  
**Rounds:** 5  
**Best round:** 5 (score 3.2)  
**Converged:** True (reached max rounds (5))  
**Score trajectory:** 2.8 -> 3.0 -> 2.8 -> 2.8 -> 3.2  

---

# Problem Formulation

## Notation and Setup

We consider the standard potential outcomes framework for causal inference. Let $X \in \mathcal{X} \subseteq \mathbb{R}^d$ denote a $d$-dimensional covariate vector, and let $T \in \{0,1\}$ be a binary treatment indicator where $T=1$ denotes treatment and $T=0$ denotes control. For each unit, we define potential outcomes $Y^{(1)}(X)$ and $Y^{(0)}(X)$ representing the outcomes that would be observed under treatment and control, respectively, given covariates $X$.

The observed outcome follows the consistency assumption: $Y = TY^{(1)} + (1-T)Y^{(0)}$. The individual treatment effect (ITE) for a unit with covariates $x$ is defined as:
$$\tau(x) = Y^{(1)}(x) - Y^{(0)}(x)$$

Let $\pi(x) = \mathbb{P}(T=1|X=x)$ denote the propensity score, and assume $0 < \pi(x) < 1$ for all $x \in \mathcal{X}$ (positivity assumption). We observe a dataset $\mathcal{D}_n = \{(X_i, T_i, Y_i)\}_{i=1}^n$ where $(X_i, T_i, Y_i)$ are i.i.d. draws from the joint distribution of $(X, T, Y)$.

For a new unit with covariates $X_{\text{new}}$ (which may come from a different population), we want to construct a prediction interval for the unobserved individual treatment effect $\tau(X_{\text{new}})$.

## Problem Statement

**Given:** 
- Training data $\mathcal{D}_n = \{(X_i, T_i, Y_i)\}_{i=1}^n$ 
- New covariate vector $X_{\text{new}}$
- Desired coverage level $1-\alpha$ where $\alpha \in (0,1)$

**Find:** An interval-valued function $\mathcal{I}_n: \mathcal{X} \to \mathbb{R} \times \mathbb{R}$ such that $\mathcal{I}_n(X_{\text{new}}) = [L_n(X_{\text{new}}), U_n(X_{\text{new}})]$

**Guarantee:** The prediction interval should satisfy:
$$\mathbb{P}(\tau(X_{\text{new}}) \in \mathcal{I}_n(X_{\text{new}})) \geq 1-\alpha$$

where the probability is taken over both the training data $\mathcal{D}_n$ and the randomness in the potential outcomes for the new unit.

## Core Challenge and Objective

The fundamental challenge is that we never observe both potential outcomes $Y^{(1)}(X_i)$ and $Y^{(0)}(X_i)$ for any unit $i$, making direct calibration of prediction intervals for $\tau(X)$ impossible. For treated units ($T_i = 1$), we observe $Y_i = Y^{(1)}(X_i)$ but not $Y^{(0)}(X_i)$. For control units ($T_i = 0$), we observe $Y_i = Y^{(0)}(X_i)$ but not $Y^{(1)}(X_i)$.

Additionally, the covariate distributions in the treated and control groups typically differ:
$$\mathbb{P}(X|T=1) \neq \mathbb{P}(X|T=0) \neq \mathbb{P}(X_{\text{new}})$$

This covariate shift must be addressed to ensure valid inference for the target population.

Our objective is to construct prediction intervals that:
1. **Respect the fundamental constraint**: Each potential outcome can only be calibrated using data from the corresponding treatment group
2. **Account for covariate shift**: Handle distributional differences between treatment groups and the target population
3. **Provide finite-sample validity**: Achieve exact coverage guarantees without asymptotic approximations
4. **Leverage propensity information**: Use knowledge of the treatment assignment mechanism to correct for distributional imbalances

## Technical Assumptions

**Assumption 1 (Consistency):** $Y = TY^{(1)} + (1-T)Y^{(0)}$

**Assumption 2 (Positivity):** $0 < \pi(x) < 1$ for all $x \in \mathcal{X}$

**Assumption 3 (Unconfoundedness):** $(Y^{(1)}, Y^{(0)}) \perp T | X$

**Assumption 4 (Exchangeability):** The training units $(X_i, T_i, Y_i)$ are exchangeable conditional on treatment assignment, and the new unit $(X_{\text{new}}, T_{\text{new}}, Y_{\text{new}})$ is exchangeable with units of the same treatment status.

**Assumption 5 (Known or estimable propensity scores):** The propensity scores $\pi(x)$ are either known (as in randomized experiments) or can be consistently estimated from the data.

These assumptions are standard in causal inference and allow us to identify the individual treatment effect distribution while accounting for the selection mechanism that creates covariate imbalance between treatment groups.

## Connection to Prior Work

Our formulation extends the conformal prediction framework of Kivaranovic et al. (2020), who proposed intervals for individual treatment effects but did not fully address the covariate shift problem. While their approach constructs separate intervals for $Y^{(1)}$ and $Y^{(0)}$ and combines them via Bonferroni-type corrections, it does not account for the fact that the treated and control groups may have systematically different covariate distributions. Our formulation recognizes that the treatment assignment mechanism $\pi(x)$ that creates this distributional imbalance also provides the mathematical structure needed to correct for it through appropriate reweighting schemes.

# Methodology

## High-Level Approach

Our approach leverages the key insight that the same propensity score mechanism that creates covariate imbalance between treatment groups also provides the solution for correcting this imbalance. We develop a **propensity-weighted conformal prediction** method that:

1. Uses the treatment assignment probabilities to reweight observations, ensuring valid inference across different covariate distributions
2. Constructs separate conformally-calibrated prediction intervals for each potential outcome using only the relevant treatment group
3. Combines these intervals while properly accounting for their dependence structure
4. Achieves exact finite-sample coverage in randomized experiments and asymptotically valid coverage in observational studies

## Core Algorithm: Propensity-Weighted Conformal Intervals

### Step 1: Propensity Score Estimation or Specification

For randomized experiments, propensity scores are known by design. For observational studies, estimate propensity scores using the treated units:
$$\hat{\pi}(x) = \mathbb{E}[T|X=x]$$

### Step 2: Weighted Conformal Calibration for Each Potential Outcome

**For the treated potential outcome $Y^{(1)}$:**

Let $\mathcal{I}_1 = \{i : T_i = 1\}$ denote the treated units. For each treated unit $i \in \mathcal{I}_1$, compute the propensity weight:
$$w_i^{(1)} = \frac{\pi(X_{\text{new}})}{\pi(X_i)}$$

Fit a regression model $\hat{m}^{(1)}(x)$ using the treated units to estimate $\mathbb{E}[Y^{(1)}|X=x]$.

Compute weighted conformal scores for treated units:
$$R_i^{(1)} = |Y_i - \hat{m}^{(1)}(X_i)| \cdot w_i^{(1)}, \quad i \in \mathcal{I}_1$$

**For the control potential outcome $Y^{(0)}$:**

Let $\mathcal{I}_0 = \{i : T_i = 0\}$ denote the control units. For each control unit $i \in \mathcal{I}_0$, compute the propensity weight:
$$w_i^{(0)} = \frac{1-\pi(X_{\text{new}})}{1-\pi(X_i)}$$

Fit a regression model $\hat{m}^{(0)}(x)$ using the control units to estimate $\mathbb{E}[Y^{(0)}|X=x]$.

Compute weighted conformal scores for control units:
$$R_i^{(0)} = |Y_i - \hat{m}^{(0)}(X_i)| \cdot w_i^{(0)}, \quad i \in \mathcal{I}_0$$

### Step 3: Quantile Computation with Weighted Empirical Distribution

For level $1-\alpha_1$, compute the $(1-\alpha_1)$-quantile of the weighted empirical distribution of $\{R_i^{(1)}\}_{i \in \mathcal{I}_1}$:
$$\hat{q}^{(1)}_{1-\alpha_1} = \inf\left\{q : \sum_{i \in \mathcal{I}_1} w_i^{(1)} \mathbf{1}(R_i^{(1)} \leq q) \geq (1-\alpha_1)\sum_{i \in \mathcal{I}_1} w_i^{(1)}\right\}$$

Similarly, for level $1-\alpha_0$, compute:
$$\hat{q}^{(0)}_{1-\alpha_0} = \inf\left\{q : \sum_{i \in \mathcal{I}_0} w_i^{(0)} \mathbf{1}(R_i^{(0)} \leq q) \geq (1-\alpha_0)\sum_{i \in \mathcal{I}_0} w_i^{(0)}\right\}$$

### Step 4: Individual Potential Outcome Intervals

Construct prediction intervals for each potential outcome:
$$\mathcal{C}^{(1)}(X_{\text{new}}) = [\hat{m}^{(1)}(X_{\text{new}}) - \hat{q}^{(1)}_{1-\alpha_1}, \hat{m}^{(1)}(X_{\text{new}}) + \hat{q}^{(1)}_{1-\alpha_1}]$$
$$\mathcal{C}^{(0)}(X_{\text{new}}) = [\hat{m}^{(0)}(X_{\text{new}}) - \hat{q}^{(0)}_{1-\alpha_0}, \hat{m}^{(0)}(X_{\text{new}}) + \hat{q}^{(0)}_{1-\alpha_0}]$$

### Step 5: Treatment Effect Interval Construction

The final prediction interval for the individual treatment effect is:
$$\mathcal{I}_n(X_{\text{new}}) = [\ell^{(1)} - u^{(0)}, u^{(1)} - \ell^{(0)}]$$

where $[\ell^{(1)}, u^{(1)}] = \mathcal{C}^{(1)}(X_{\text{new}})$ and $[\ell^{(0)}, u^{(0)}] = \mathcal{C}^{(0)}(X_{\text{new}})$.

The choice of $\alpha_1$ and $\alpha_0$ depends on the desired coverage guarantee and assumptions about the dependence between potential outcomes.

## Algorithm Summary

```
Algorithm: Propensity-Weighted Conformal Prediction for ITE

Input: Training data D_n, new covariates X_new, confidence level 1-α
Output: Prediction interval I_n(X_new) for τ(X_new)

1. Estimate or specify propensity scores π(x)
2. Split data into treated (I_1) and control (I_0) groups
3. Fit regression models m̂^(1)(x) and m̂^(0)(x) on respective groups
4. For each group t ∈ {0,1}:
   a. Compute propensity weights w_i^(t) for units in group t
   b. Compute weighted conformal scores R_i^(t)
   c. Find weighted quantile q̂^(t)_{1-α_t}
   d. Construct interval C^(t)(X_new)
5. Combine intervals: I_n(X_new) = [ℓ^(1) - u^(0), u^(1) - ℓ^(0)]
6. Return I_n(X_new)
```

## Theoretical Properties

**Theorem (Finite-Sample Coverage for Randomized Experiments):** Under Assumptions 1-2 with known propensity scores, if we set $\alpha_1 = \alpha_0 = \alpha/2$, then:
$$\mathbb{P}(\tau(X_{\text{new}}) \in \mathcal{I}_n(X_{\text{new}})) \geq 1-\alpha$$

**Theorem (Asymptotic Coverage for Observational Studies):** Under Assumptions 1-5 with consistent propensity score estimation, the coverage probability converges to the nominal level:
$$\lim_{n \to \infty} \mathbb{P}(\tau(X_{\text{new}}) \in \mathcal{I}_n(X_{\text{new}})) \geq 1-\alpha$$

## Key Design Decisions

**Propensity Weighting Rationale:** The weights $w_i^{(1)} = \pi(X_{\text{new}})/\pi(X_i)$ and $w_i^{(0)} = (1-\pi(X_{\text{new}}))/(1-\pi(X_i))$ rebalance the training data to match the covariate distribution at the target point $X_{\text{new}}$. This addresses the covariate shift problem directly within the conformal framework.

**Separate Calibration:** By calibrating each potential outcome separately using only the relevant treatment group, we respect the fundamental constraint that each potential outcome can only be informed by units that actually received that treatment.

**Weighted Quantiles:** The weighted empirical distribution function accounts for the fact that units with covariates similar to $X_{\text{new}}$ should receive higher weight in determining the appropriate quantile.

## Computational Complexity

The algorithm has computational complexity $O(n \log n)$ due to the sorting required for quantile computation, plus the cost of fitting the regression models $\hat{m}^{(1)}$ and $\hat{m}^{(0)}$. The propensity score estimation adds at most $O(n)$ for parametric models or the complexity of the chosen non-parametric method. This makes the approach scalable to large datasets while maintaining the finite-sample validity guarantees.
