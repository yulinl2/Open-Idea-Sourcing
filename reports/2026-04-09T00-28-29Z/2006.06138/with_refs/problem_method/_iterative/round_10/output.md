# Problem Formulation

## Notation and Setup

Let $\mathcal{X} \subseteq \mathbb{R}^d$ denote the covariate space and $\mathcal{Y} \subseteq \mathbb{R}$ the outcome space. For each individual $i$, let $X_i \in \mathcal{X}$ represent their covariates and $(Y_i(0), Y_i(1)) \in \mathcal{Y}^2$ represent their potential outcomes under control ($T_i = 0$) and treatment ($T_i = 1$) respectively. Let $T_i \in \{0,1\}$ denote the treatment assignment, and $Y_i = T_i Y_i(1) + (1-T_i) Y_i(0)$ the observed outcome.

We observe data $\mathcal{D}_n = \{(X_i, T_i, Y_i)\}_{i=1}^n$ where $(X_i, T_i, Y_i(0), Y_i(1))$ are i.i.d. draws from some unknown distribution $P$. The propensity score is $e(x) = P(T = 1 | X = x)$, assumed to satisfy $0 < e(x) < 1$ for all $x \in \mathcal{X}$ (overlap assumption).

For a new individual with covariates $X_{n+1}$, we define the individual treatment effect as $\tau_{n+1} = Y_{n+1}(1) - Y_{n+1}(0)$. Our goal is to construct prediction intervals for the unobserved potential outcomes $Y_{n+1}(0)$ and $Y_{n+1}(1)$, which then enable inference about $\tau_{n+1}$.

## Problem Statement

**Given:** Training data $\mathcal{D}_n = \{(X_i, T_i, Y_i)\}_{i=1}^n$ and covariates $X_{n+1}$ for a new individual.

**Find:** Prediction intervals $\mathcal{C}_n^{(0)}(X_{n+1})$ and $\mathcal{C}_n^{(1)}(X_{n+1})$ for the unobserved potential outcomes $Y_{n+1}(0)$ and $Y_{n+1}(1)$ respectively.

**Guarantee:** For a specified confidence level $1-\alpha$, the intervals should satisfy:
$$P\left(Y_{n+1}(t) \in \mathcal{C}_n^{(t)}(X_{n+1})\right) \geq 1-\alpha, \quad t \in \{0,1\}$$

where the probability is taken over the randomness in $\mathcal{D}_n$ and $(X_{n+1}, Y_{n+1}(0), Y_{n+1}(1))$.

## Fundamental Challenge and Key Insight

The core challenge is that for each individual, we observe only one potential outcome—the one corresponding to their actual treatment assignment. This creates a missing data problem where:
- Units with $T_i = 1$ inform us about the distribution of $Y(1)|X$
- Units with $T_i = 0$ inform us about the distribution of $Y(0)|X$

Crucially, the treatment assignment mechanism creates covariate shift between groups: the distribution of $X|T=1$ typically differs from $X|T=0$, and both may differ from the target population distribution. However, this same mechanism provides the mathematical structure needed for correction through importance weighting.

## Technical Assumptions

**Assumption 1 (Unconfoundedness):** $(Y(0), Y(1)) \perp T | X$

**Assumption 2 (Overlap):** $0 < e(x) < 1$ for all $x \in \mathcal{X}$

**Assumption 3 (Exchangeability within groups):** Conditional on treatment assignment, units are exchangeable:
- $\{(X_i, Y_i) : T_i = t\}$ are exchangeable for $t \in \{0,1\}$

**Assumption 4 (Known or estimable propensity scores):** Either $e(x)$ is known, or we have access to a consistent estimator $\hat{e}(x)$ or auxiliary unlabeled data for estimation.

These assumptions are standard in causal inference. Assumption 1 ensures treatment assignment is as good as random conditional on observed covariates. Assumption 2 ensures both treatment groups are represented across the covariate space. Assumption 3 is weaker than i.i.d. and allows for conformal prediction within treatment groups. Assumption 4 enables the covariate shift correction.

## Connection to Prior Work

This formulation extends the covariate shift conformal prediction framework of Tibshirani et al. (2020) to the causal inference setting. While their work addresses distribution shift between training and test populations, our problem involves a specific type of shift induced by treatment assignment mechanisms. The key insight is that we can adapt their weighted conformal prediction approach, but must carefully account for the constraint that each potential outcome can only be calibrated using data from the corresponding treatment group.

The problem also connects to the individual treatment effect literature (Kivaranovic et al., 2020), but our focus is on prediction intervals for unobserved potential outcomes rather than the observed treatment effect difference, requiring novel handling of the missing counterfactual outcomes.

# Methodology

## High-Level Approach

Our approach adapts weighted conformal prediction to handle the covariate shift induced by treatment assignment mechanisms. The key insight is that while we cannot directly observe individual treatment effects, we can construct valid prediction intervals for each potential outcome separately by using only the data from the corresponding treatment group, appropriately weighted to account for covariate shift.

The methodology consists of three main components:
1. **Treatment-stratified conformal prediction:** Apply conformal prediction separately within each treatment group
2. **Covariate shift correction:** Use importance weighting to adjust for distributional differences between treatment groups and target population
3. **Interval combination:** Combine the potential outcome intervals to make inferences about treatment effects

## Core Algorithm

### Algorithm 1: Weighted Conformal Prediction for Potential Outcomes

**Input:** 
- Training data $\mathcal{D}_n = \{(X_i, T_i, Y_i)\}_{i=1}^n$
- Target covariates $X_{n+1}$  
- Confidence level $1-\alpha$
- Score function $S(\cdot, \cdot)$
- Propensity score function $e(\cdot)$

**Output:** Prediction intervals $\mathcal{C}_n^{(0)}(X_{n+1})$, $\mathcal{C}_n^{(1)}(X_{n+1})$

```
1. For each treatment level t ∈ {0,1}:
   
   2. Extract treatment-specific data:
      D_n^{(t)} = {(X_i, Y_i) : T_i = t, i = 1,...,n}
      Let n_t = |D_n^{(t)}|
   
   3. Define importance weights:
      For t = 1: w_i^{(1)}(x) = e(x)/e(X_i) for (X_i, Y_i) ∈ D_n^{(1)}
      For t = 0: w_i^{(0)}(x) = (1-e(x))/(1-e(X_i)) for (X_i, Y_i) ∈ D_n^{(0)}
   
   4. For each candidate value y ∈ ℝ:
      
      5. Compute nonconformity scores:
         V_i^{(t)}(x,y) = S((X_i, Y_i), D_n^{(t)} ∪ {(x,y)}) for i: T_i = t
         V_{n+1}^{(t)}(x,y) = S((x,y), D_n^{(t)})
      
      6. Compute weighted probabilities:
         p_i^{(t)}(x) = w_i^{(t)}(x) / (∑_{j: T_j = t} w_j^{(t)}(x) + w_{n+1}^{(t)}(x))
         p_{n+1}^{(t)}(x) = w_{n+1}^{(t)}(x) / (∑_{j: T_j = t} w_j^{(t)}(x) + w_{n+1}^{(t)}(x))
         where w_{n+1}^{(1)}(x) = 1 and w_{n+1}^{(0)}(x) = 1
   
   7. Include y in C_n^{(t)}(x) if:
      V_{n+1}^{(t)}(x,y) ≤ Quantile(1-α; ∑_{i: T_i = t} p_i^{(t)}(x)δ_{V_i^{(t)}(x,y)} + p_{n+1}^{(t)}(x)δ_∞)

8. Return intervals C_n^{(0)}(X_{n+1}), C_n^{(1)}(X_{n+1})
```

## Key Design Decisions

### Importance Weight Construction
The importance weights correct for covariate shift between treatment groups and the target population. For treatment group $t=1$, we weight observations by $e(X_{n+1})/e(X_i)$, which upweights observations from regions of covariate space that are underrepresented in the treated group relative to the target distribution. The construction ensures that the weighted empirical distribution of nonconformity scores resembles what we would observe from the target population.

### Treatment-Stratified Approach
We apply conformal prediction separately within each treatment group rather than pooling across treatments. This is essential because:
1. Each potential outcome can only be calibrated using data from the corresponding treatment group
2. The conditional distributions $Y(t)|X$ may differ substantially between $t=0$ and $t=1$
3. Pooling would violate the exchangeability required for conformal prediction validity

### Score Function Choice
The score function $S((x,y), \mathcal{D})$ measures how "unusual" the point $(x,y)$ is relative to the dataset $\mathcal{D}$. Common choices include:
- **Absolute residual:** $S((x,y), \mathcal{D}) = |y - \hat{\mu}(x)|$ where $\hat{\mu}$ is fitted on $\mathcal{D}$
- **Studentized residual:** $S((x,y), \mathcal{D}) = |y - \hat{\mu}(x)|/\hat{\sigma}(x)$ with estimated conditional variance $\hat{\sigma}^2(x)$

## Theoretical Properties

**Theorem (Finite-Sample Coverage).** Under Assumptions 1-4, for each $t \in \{0,1\}$:
$$P\left(Y_{n+1}(t) \in \mathcal{C}_n^{(t)}(X_{n+1})\right) \geq 1-\alpha$$

**Proof Sketch:** The key insight is that the importance weighting makes the nonconformity scores "look exchangeable" with respect to the target distribution. Specifically, under the covariate shift model with known propensity scores, the weighted empirical distribution of scores from treatment group $t$ converges to the distribution we would observe by drawing from the target population and assigning treatment $t$.

**Corollary (Treatment Effect Intervals).** Valid intervals for the individual treatment effect $\tau_{n+1} = Y_{n+1}(1) - Y_{n+1}(0)$ can be constructed as:
$$\mathcal{C}_n^{(\tau)}(X_{n+1}) = \{y_1 - y_0 : y_1 \in \mathcal{C}_n^{(1)}(X_{n+1}), y_0 \in \mathcal{C}_n^{(0)}(X_{n+1})\}$$

## Computational Complexity

The algorithm has computational complexity $O(n \cdot |\mathcal{Y}|)$ where $|\mathcal{Y}|$ represents the discretization of the outcome space for interval construction. For continuous outcomes, this can be reduced to $O(n \log n)$ using efficient quantile computation methods.

For the split conformal variant (where the score function uses a pre-fitted model), the complexity reduces to $O(n)$ per target point, making the method highly scalable.

The importance weight computation adds minimal overhead, requiring only evaluation of the propensity score function at $n+1$ points per prediction.