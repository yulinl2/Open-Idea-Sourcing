# Problem Formulation

## Notation and Setup

Let $(X_i, Y_i(0), Y_i(1))$ for $i = 1, \ldots, n$ denote $n$ units, where $X_i \in \mathcal{X} \subseteq \mathbb{R}^d$ represents covariates and $Y_i(t) \in \mathbb{R}$ denotes the potential outcome under treatment $t \in \{0,1\}$. The individual treatment effect for unit $i$ is defined as $\tau_i = Y_i(1) - Y_i(0)$. Let $T_i \in \{0,1\}$ denote the treatment assignment indicator, and define the observed outcome as $Y_i = T_i Y_i(1) + (1-T_i) Y_i(0)$. We observe the dataset $\mathcal{D}_n = \{(X_i, T_i, Y_i)\}_{i=1}^n$.

For a new unit with covariates $X_{n+1}$, we seek to construct prediction intervals for the unobserved potential outcomes $Y_{n+1}(0)$ and $Y_{n+1}(1)$, which enables inference about the individual treatment effect $\tau_{n+1} = Y_{n+1}(1) - Y_{n+1}(0)$.

Let $\pi(x) = \mathbb{P}[T = 1 | X = x]$ denote the propensity score function. We assume the propensity score is either known (as in randomized experiments) or can be estimated consistently. Define the likelihood ratio weights as:
$$w_t(x) = \frac{\mathbb{I}(t=1)}{\pi(x)} + \frac{\mathbb{I}(t=0)}{1-\pi(x)}$$

Let $P_X$ denote the covariate distribution in the study population, and $\tilde{P}_X$ denote the covariate distribution in the target population. When these differ, we have covariate shift characterized by the density ratio $r(x) = d\tilde{P}_X(x)/dP_X(x)$.

## Problem Statement

**Given:** 
- Training data $\mathcal{D}_n = \{(X_i, T_i, Y_i)\}_{i=1}^n$ 
- A new covariate vector $X_{n+1}$ (possibly from target population $\tilde{P}_X$)
- Desired coverage level $1-\alpha$ where $\alpha \in (0,1)$
- Propensity score function $\pi(\cdot)$ or its estimate $\hat{\pi}(\cdot)$

**Find:** Prediction intervals $\hat{C}_{n,0}(X_{n+1})$ and $\hat{C}_{n,1}(X_{n+1})$ such that:
$$\mathbb{P}[Y_{n+1}(0) \in \hat{C}_{n,0}(X_{n+1})] \geq 1-\alpha$$
$$\mathbb{P}[Y_{n+1}(1) \in \hat{C}_{n,1}(X_{n+1})] \geq 1-\alpha$$

**Guarantee:** The intervals should provide valid finite-sample coverage without distributional assumptions, accounting for:
1. The fundamental missingness pattern where $Y_i(1-T_i)$ is never observed
2. Covariate shift between study and target populations
3. Estimation uncertainty in both outcome models and propensity scores

## Technical Assumptions

**A1 (Consistency/No Unmeasured Confounding):** $(Y_i(0), Y_i(1)) \perp T_i | X_i$ for all $i$.

**A2 (Overlap):** There exists $\epsilon > 0$ such that $\epsilon \leq \pi(x) \leq 1-\epsilon$ for all $x \in \text{supp}(P_X) \cup \text{supp}(\tilde{P}_X)$.

**A3 (Covariate Shift Structure):** If study and target populations differ, then $\tilde{P}_X \ll P_X$ with known or estimable density ratio $r(x) = d\tilde{P}_X(x)/dP_X(x)$.

**A4 (Propensity Score Knowledge):** Either $\pi(x)$ is known exactly (randomized experiments) or can be estimated with $\|\hat{\pi} - \pi\|_\infty = o_p(1)$.

These assumptions are standard in causal inference. A1 ensures identifiability of potential outcomes from observed data. A2 prevents extreme propensity scores that would make inference unstable. A3 formalizes the covariate shift problem while maintaining identifiability. A4 allows for both experimental and observational settings.

The key insight connecting to prior work is that the covariate shift problem in Tibshirani et al. (2020) provides the mathematical framework for reweighting, while the treatment effect setting in Kivaranovic et al. (2020) motivates the conditional prediction interval approach. However, neither work addresses the intersection: constructing valid intervals for individual potential outcomes under covariate shift induced by the treatment assignment mechanism itself.

# Methodology

## High-Level Approach

Our approach extends weighted conformal prediction to handle the unique structure of causal inference problems. The key insight is that each potential outcome can only be calibrated using data from units that actually received the corresponding treatment level, but the treatment assignment mechanism creates systematic covariate imbalance that must be corrected through inverse propensity weighting.

We propose **Causally-Weighted Conformal Prediction (CWCP)**, which constructs separate prediction intervals for $Y(0)$ and $Y(1)$ by:
1. Using only control units to calibrate intervals for $Y(0)$ 
2. Using only treated units to calibrate intervals for $Y(1)$
3. Reweighting each group to match the target population distribution
4. Applying conformal prediction with these causally-motivated weights

## Core Algorithm

### Algorithm 1: Causally-Weighted Conformal Prediction

**Input:** Training data $\mathcal{D}_n$, test covariate $X_{n+1}$, level $\alpha$, propensity score $\pi(\cdot)$, density ratio $r(\cdot)$

**Step 1: Fit outcome models**
- Fit $\hat{\mu}_0(x)$ using control units $\{(X_i, Y_i) : T_i = 0\}$
- Fit $\hat{\mu}_1(x)$ using treated units $\{(X_i, Y_i) : T_i = 1\}$

**Step 2: Compute nonconformity scores**
For each potential outcome value $y$ and treatment $t \in \{0,1\}$:
```
For i = 1 to n:
    If T_i == t:
        V_i^{(t)}(y) = |Y_i - hat_mu_t(X_i)|
    Else:
        V_i^{(t)}(y) = infinity
    
V_{n+1}^{(t)}(y) = |y - hat_mu_t(X_{n+1})|
```

**Step 3: Compute causal weights**
For treatment group $t$ and test point $X_{n+1}$:
```
total_weight = 0
For i = 1 to n:
    If T_i == t:
        w_i = r(X_i) / (pi(X_i)^t * (1-pi(X_i))^{1-t})
        total_weight += w_i

w_{n+1} = r(X_{n+1}) / (pi(X_{n+1})^t * (1-pi(X_{n+1}))^{1-t})
total_weight += w_{n+1}

For i = 1 to n:
    tilde_w_i^{(t)} = w_i / total_weight if T_i == t, else 0
    
tilde_w_{n+1}^{(t)} = w_{n+1} / total_weight
```

**Step 4: Construct prediction intervals**
```
For t in {0, 1}:
    quantile_t = WeightedQuantile(1-alpha, 
                                  {V_i^{(t)}(y)}_{i=1}^n ∪ {∞}, 
                                  {tilde_w_i^{(t)}}_{i=1}^n ∪ {tilde_w_{n+1}^{(t)}})
    
    C_t(X_{n+1}) = {y : V_{n+1}^{(t)}(y) ≤ quantile_t}
```

**Output:** Intervals $\hat{C}_{n,0}(X_{n+1})$ and $\hat{C}_{n,1}(X_{n+1})$

## Key Design Decisions

**Separate Calibration by Treatment Group:** This respects the fundamental constraint that we can only observe $Y_i(t)$ for units with $T_i = t$. Unlike standard conformal prediction that uses all data points, we necessarily partition the calibration set by treatment received.

**Inverse Propensity Weighting:** The weights $w_i = r(X_i)/[\pi(X_i)^{T_i}(1-\pi(X_i))^{1-T_i}]$ serve two purposes:
1. $r(X_i)$ corrects for covariate shift between study and target populations  
2. $1/[\pi(X_i)^{T_i}(1-\pi(X_i))^{1-T_i}]$ corrects for treatment-induced covariate imbalance

This extends the covariate shift correction from Tibshirani et al. (2020) to the causal setting where the shift is induced by treatment assignment rather than external factors.

**Weighted Quantile Computation:** We use the weighted empirical distribution:
$$F_t^{(w)}(v) = \sum_{i: T_i = t} \tilde{w}_i^{(t)} \mathbb{I}(V_i^{(t)} \leq v) + \tilde{w}_{n+1}^{(t)} \mathbb{I}(\infty \leq v)$$

The inclusion of $\infty$ with weight $\tilde{w}_{n+1}^{(t)}$ ensures the test point contributes to the quantile calculation, maintaining the exchangeability structure needed for valid coverage.

## Theoretical Properties

**Theorem (Finite-Sample Coverage):** Under assumptions A1-A4, for each $t \in \{0,1\}$:
$$\mathbb{P}[Y_{n+1}(t) \in \hat{C}_{n,t}(X_{n+1})] \geq 1-\alpha$$

**Proof Sketch:** The key insight is that after reweighting, the nonconformity scores $\{V_i^{(t)}: T_i = t\} \cup \{V_{n+1}^{(t)}\}$ become exchangeable under the weighted measure. This follows from the weighted exchangeability framework of Tibshirani et al. (2020), adapted to respect the treatment-specific calibration constraint.

**Robustness Property:** The method maintains validity if either the outcome model $\hat{\mu}_t$ or the propensity score model $\hat{\pi}$ is correctly specified, providing double robustness similar to augmented inverse probability weighting estimators.

## Computational Complexity

The algorithm has complexity $O(n \log n)$ per treatment group for the weighted quantile computation, leading to overall complexity $O(n \log n)$. The bottleneck is typically fitting the outcome models $\hat{\mu}_0, \hat{\mu}_1$, which depends on the chosen regression method.

For split conformal variants where outcome models are pre-fitted, the complexity reduces to $O(n)$ per interval, making the method highly scalable.