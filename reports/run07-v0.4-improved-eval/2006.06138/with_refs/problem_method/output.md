# Reconstruction: problem_method
**Paper:** 2006.06138  
**Condition:** with_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Problem Formulation

## 1.1 Notation and Setup

We consider the standard potential outcomes framework for causal inference. Let $\mathcal{X} \subseteq \mathbb{R}^d$ denote the covariate space and $\mathcal{Y} \subseteq \mathbb{R}$ the outcome space. For each individual $i$, we observe covariates $X_i \in \mathcal{X}$, treatment assignment $T_i \in \{0,1\}$, and the realized outcome $Y_i \in \mathcal{Y}$. We denote the potential outcomes as $Y_i(0)$ and $Y_i(1)$, representing the outcomes individual $i$ would experience under control and treatment, respectively. The fundamental problem of causal inference is that we only observe $Y_i = T_i Y_i(1) + (1-T_i)Y_i(0)$ for each individual.

The individual treatment effect (ITE) for individual $i$ is defined as:
$$\tau_i = Y_i(1) - Y_i(0)$$

Let $P$ denote the joint distribution of $(X, Y(0), Y(1), T)$, and let $P_X$ denote the marginal distribution of covariates. We assume access to training data $\{(X_i, T_i, Y_i)\}_{i=1}^n$ drawn from $P$.

## 1.2 Problem Statement

**Given:** Training data $\{(X_i, T_i, Y_i)\}_{i=1}^n$ and a target individual with covariates $X_{n+1}$.

**Find:** A prediction interval $\hat{C}_n(X_{n+1}) \subseteq \mathbb{R}$ for the unobserved individual treatment effect $\tau_{n+1} = Y_{n+1}(1) - Y_{n+1}(0)$.

**Guarantee:** For a pre-specified miscoverage level $\alpha \in (0,1)$, we require:
$$\mathbb{P}\left(\tau_{n+1} \in \hat{C}_n(X_{n+1})\right) \geq 1 - \alpha$$

where the probability is taken over the randomness in the training data and the target individual.

## 1.3 Technical Assumptions

We make the following standard assumptions for causal inference:

**Assumption 1 (Unconfoundedness):** $(Y(0), Y(1)) \perp T \mid X$, where $\perp$ denotes statistical independence.

**Assumption 2 (Overlap):** There exists $\epsilon > 0$ such that $\epsilon \leq e(x) \leq 1-\epsilon$ for all $x \in \mathcal{X}$, where $e(x) = \mathbb{P}(T=1 \mid X=x)$ is the propensity score.

**Assumption 3 (Exchangeability):** The augmented data points $(X_i, Y_i(0), Y_i(1), T_i)$ for $i = 1, \ldots, n+1$ are exchangeable.

These assumptions are standard in the causal inference literature and enable identification of treatment effects from observational data. Assumption 3 can be relaxed to accommodate covariate shift between training and target populations, following the weighted exchangeability framework of Tibshirani et al. (2020).

## 1.4 Connection to Prior Work

Our formulation extends the conformal prediction framework of Vovk et al. (2005) to the causal inference setting. The key challenge is that individual treatment effects $\tau_i$ are never directly observed, unlike the standard regression setting where conformal prediction has been extensively studied. The weighted conformal prediction methodology of Tibshirani et al. (2020) provides a foundation for handling distributional differences between training and target populations, which we adapt to address the fundamental missing data problem in causal inference.

# Methodology

## 2.1 Overview of Approach

Our approach constructs prediction intervals for individual treatment effects by leveraging the conformal prediction framework while addressing the fundamental challenge that ITEs are never directly observed. The key insight is to construct pseudo-outcomes that serve as proxies for the unobserved treatment effects, then apply a modified conformal procedure that accounts for the uncertainty in these pseudo-outcomes.

## 2.2 Pseudo-Outcome Construction

Since individual treatment effects $\tau_i = Y_i(1) - Y_i(0)$ are never observed, we construct pseudo-outcomes using estimated potential outcome functions. Let $\hat{\mu}_0(x)$ and $\hat{\mu}_1(x)$ denote estimators of $\mathbb{E}[Y(0) \mid X=x]$ and $\mathbb{E}[Y(1) \mid X=x]$, respectively, fitted using the training data.

For each individual $i$ in the training set, we define the pseudo-outcome:
$$\tilde{\tau}_i = \hat{\mu}_1(X_i) - \hat{\mu}_0(X_i) + \epsilon_i$$

where $\epsilon_i$ is a correction term that accounts for the uncertainty in the potential outcome estimates:
$$\epsilon_i = \begin{cases}
Y_i - \hat{\mu}_1(X_i) & \text{if } T_i = 1 \\
\hat{\mu}_0(X_i) - Y_i & \text{if } T_i = 0
\end{cases}$$

This construction ensures that $\tilde{\tau}_i$ incorporates both the estimated treatment effect and the residual information from the observed outcome.

## 2.3 Conformal Prediction Algorithm

We define a conformity score function that measures how typical a given treatment effect is relative to the pseudo-outcomes:
$$S((x, \tau), \mathcal{D}) = |\tau - \hat{\mu}_1(x) + \hat{\mu}_0(x)|$$

where $\mathcal{D}$ represents the training dataset.

**Algorithm 1: Conformal Prediction for Individual Treatment Effects**

```
Input: Training data {(X_i, T_i, Y_i)}_{i=1}^n, target covariates X_{n+1}, 
       miscoverage level α
Output: Prediction interval C_n(X_{n+1})

1. Split training data into two sets:
   - D_fit: for fitting potential outcome models
   - D_cal: for calibration

2. Fit potential outcome models on D_fit:
   μ̂_0(x) ← fit model for E[Y|X=x, T=0]
   μ̂_1(x) ← fit model for E[Y|X=x, T=1]

3. Compute pseudo-outcomes for calibration set D_cal:
   For each (X_i, T_i, Y_i) in D_cal:
     τ̃_i ← μ̂_1(X_i) - μ̂_0(X_i) + ε_i
     where ε_i = (Y_i - μ̂_1(X_i)) if T_i=1, else (μ̂_0(X_i) - Y_i)

4. For target point X_{n+1}, compute conformity scores:
   For each τ̃_i in calibration set:
     V_i ← |τ̃_i - (μ̂_1(X_{n+1}) - μ̂_0(X_{n+1}))|

5. Compute quantile:
   q ← Quantile(1-α; {V_1, ..., V_m, ∞})
   where m = |D_cal|

6. Return prediction interval:
   C_n(X_{n+1}) ← [μ̂_1(X_{n+1}) - μ̂_0(X_{n+1}) ± q]
```

## 2.4 Extension to Covariate Shift

When the target population differs from the training population, we adapt the weighted conformal prediction approach. Assuming access to the likelihood ratio $w(x) = \frac{d\tilde{P}_X(x)}{dP_X(x)}$ between target and training covariate distributions, we modify the quantile computation in Step 5:

```
5. Compute weighted quantile:
   Define weights: p_i^w = w(X_i) / (∑_{j=1}^m w(X_j) + w(X_{n+1}))
                  p_{n+1}^w = w(X_{n+1}) / (∑_{j=1}^m w(X_j) + w(X_{n+1}))
   
   q ← Quantile(1-α; ∑_{i=1}^m p_i^w δ_{V_i} + p_{n+1}^w δ_∞)
```

## 2.5 Theoretical Properties

**Theorem (Coverage Guarantee):** Under Assumptions 1-3, the prediction interval $\hat{C}_n(X_{n+1})$ satisfies:
$$\mathbb{P}(\tau_{n+1} \in \hat{C}_n(X_{n+1})) \geq 1 - \alpha$$

The proof follows from the exchangeability of the conformity scores constructed from pseudo-outcomes and the application of the fundamental conformal prediction lemma (Lemma 1 from Tibshirani et al., 2020).

## 2.6 Computational Complexity

The algorithm has computational complexity $O(n \log n)$ for the quantile computation, plus the cost of fitting the potential outcome models. The split conformal approach avoids refitting models for each candidate treatment effect value, making the method computationally efficient. The method scales linearly with the calibration set size and can handle high-dimensional covariates through the choice of flexible machine learning models for $\hat{\mu}_0$ and $\hat{\mu}_1$.
