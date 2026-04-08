# Reconstruction: problem
**Paper:** 2006.06138  
**Condition:** with_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Problem Formulation

## Notation and Setup

Let $(\mathcal{X}, \mathcal{Y}) = (\mathbb{R}^d, \mathbb{R})$ denote the covariate and outcome spaces, respectively. We consider the potential outcomes framework where each unit $i$ has two potential outcomes: $Y_i(1)$ under treatment and $Y_i(0)$ under control. The individual treatment effect for unit $i$ is $\tau_i = Y_i(1) - Y_i(0)$. Let $W_i \in \{0,1\}$ denote the treatment assignment, and define the observed outcome as $Y_i = W_i Y_i(1) + (1-W_i) Y_i(0)$.

For a study population, we observe $n$ units $\{(X_i, W_i, Y_i)\}_{i=1}^n$ where $X_i \in \mathcal{X}$ are covariates. The conditional average treatment effect (CATE) function is defined as:
$$\tau(x) = \mathbb{E}[Y(1) - Y(0) | X = x] = \mu_1(x) - \mu_0(x)$$
where $\mu_w(x) = \mathbb{E}[Y(w) | X = x]$ for $w \in \{0,1\}$.

We distinguish between two inference targets:
1. **Within-study inference**: For a unit $i$ in the study with covariates $X_i$, construct a prediction interval for the unobserved potential outcome $Y_i(1-W_i)$, and hence for the individual treatment effect $\tau_i$.
2. **Out-of-study inference**: For a new unit with covariates $X_{n+1}$ drawn from a potentially different distribution, construct prediction intervals for both potential outcomes $Y_{n+1}(0), Y_{n+1}(1)$ and the individual treatment effect $\tau_{n+1}$.

## Formal Problem Statement

**Given**: 
- Study data $\mathcal{D}_n = \{(X_i, W_i, Y_i)\}_{i=1}^n$ where only one potential outcome is observed per unit
- A target coverage level $1-\alpha \in (0,1)$
- For out-of-study inference: knowledge of or ability to estimate the likelihood ratio $w(x) = \frac{d\tilde{P}_X(x)}{dP_X(x)}$ where $P_X$ and $\tilde{P}_X$ are the study and target covariate distributions respectively

**Find**: Prediction intervals $\hat{C}_n^{(0)}(x), \hat{C}_n^{(1)}(x), \hat{C}_n^{\tau}(x)$ such that:

For within-study inference:
$$\mathbb{P}\left(Y_i(0) \in \hat{C}_n^{(0)}(X_i) \mid W_i = 1\right) \geq 1-\alpha$$
$$\mathbb{P}\left(Y_i(1) \in \hat{C}_n^{(1)}(X_i) \mid W_i = 0\right) \geq 1-\alpha$$
$$\mathbb{P}\left(\tau_i \in \hat{C}_n^{\tau}(X_i)\right) \geq 1-\alpha$$

For out-of-study inference under covariate shift:
$$\mathbb{P}\left(Y_{n+1}(w) \in \hat{C}_n^{(w)}(X_{n+1})\right) \geq 1-\alpha \quad \text{for } w \in \{0,1\}$$
$$\mathbb{P}\left(\tau_{n+1} \in \hat{C}_n^{\tau}(X_{n+1})\right) \geq 1-\alpha$$

where the probabilities are taken over the randomness in treatment assignments and potential outcomes.

## Methodological Approach

Building on the conformal prediction framework of Tibshirani et al. (2020), we extend their weighted conformal methodology to the causal inference setting. The key insight is to construct separate conformity scores for each treatment group while accounting for the fundamental challenge that individual treatment effects are never directly observable.

For within-study inference, we define separate nonconformity scores for each treatment group:
$$S^{(w)}((x,y), \mathcal{Z}^{(w)}) = |y - \hat{\mu}^{(w)}(x)|$$
where $\hat{\mu}^{(w)}$ is a regression function fitted on the subset of units receiving treatment $w$, and $\mathcal{Z}^{(w)} = \{(X_i, Y_i) : W_i = w\}$.

For out-of-study inference under covariate shift, we adapt the weighted quantile approach from Tibshirani et al. (2020). Define weights:
$$p_i^{(w)}(x) = \frac{w(X_i) \mathbb{I}(W_i = w)}{\sum_{j: W_j = w} w(X_j) + w(x)}$$

The weighted conformal prediction intervals are then:
$$\hat{C}_n^{(w)}(x) = \left\{y : S^{(w)}((x,y), \mathcal{Z}^{(w)}) \leq Q_{1-\alpha}\left(\sum_{i: W_i = w} p_i^{(w)}(x) \delta_{S^{(w)}_i} + p_{n+1}^{(w)}(x) \delta_{\infty}\right)\right\}$$

where $S^{(w)}_i = S^{(w)}((X_i, Y_i), \mathcal{Z}^{(w)} \setminus \{(X_i, Y_i)\})$ and $Q_{1-\alpha}$ denotes the $(1-\alpha)$-quantile.

## Technical Assumptions

**A1. Stable Unit Treatment Value Assumption (SUTVA)**: The potential outcomes for unit $i$ are unaffected by the treatment assignments of other units, and there are no hidden variations of treatments.

**A2. Conditional Exchangeability**: Within each treatment group $w$, the units $\{(X_i, Y_i(w)) : W_i = w\}$ are exchangeable conditional on treatment assignment.

**A3. Overlap**: For all $x$ in the support of the covariate distribution, $0 < \mathbb{P}(W = 1 | X = x) < 1$.

**A4. Covariate Shift Model**: The target covariate distribution $\tilde{P}_X$ is absolutely continuous with respect to the study distribution $P_X$, with known or estimable likelihood ratio $w(x) = \frac{d\tilde{P}_X(x)}{dP_X(x)}$.

**A5. Consistency of Outcome Models**: The regression functions $\hat{\mu}^{(w)}$ satisfy basic consistency properties (this assumption can be relaxed as conformal prediction provides model-free guarantees).

Assumption A1 is standard in causal inference and ensures well-defined individual treatment effects. A2 extends the exchangeability assumption from Tibshirani et al. (2020) to the causal setting, allowing for different data generating processes across treatment groups. A3 ensures that we observe sufficient units in both treatment groups across the covariate space. A4 directly adapts the covariate shift framework, while A5 acknowledges that while better models improve efficiency, the coverage guarantees hold regardless of model quality.

## Connection to Prior Work and Novel Contributions

This formulation extends the distribution-free conformal prediction framework of Tibshirani et al. (2020) from the standard supervised learning setting to causal inference with individual treatment effect estimation. While their work addresses covariate shift in prediction problems where the full outcome is observable, our setting presents the fundamental challenge that individual treatment effects are never directly observed—we only see $Y_i(W_i)$ for each unit $i$.

The key methodological innovation is decomposing the problem into separate conformal procedures for each treatment group, then combining them to form intervals for individual treatment effects. This approach preserves the finite-sample, distribution-free guarantees of conformal prediction while addressing the unique challenges of causal inference. Unlike existing CATE estimation methods that focus primarily on point estimation, our framework provides the first principled approach for uncertainty quantification of individual treatment effects with guaranteed coverage properties under covariate shift.
