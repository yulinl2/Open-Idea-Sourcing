# Reconstruction: problem_method
**Paper:** 2602.04770  
**Condition:** with_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Section 1: Problem Formulation

## 1.1 Notation and Setup

Let $\mathcal{X} \subseteq \mathbb{R}^d$ denote the covariate space and $\mathcal{Y} \subseteq \mathbb{R}$ the response space. We observe training data $\{(X_i, Y_i)\}_{i=1}^n$ drawn i.i.d. from an unknown distribution $P_{XY}$, and seek to construct prediction intervals for a new test point $(X_{n+1}, Y_{n+1})$ drawn from the same distribution.

Let $\hat{\mu}: \mathcal{X} \to \mathbb{R}$ denote a point predictor (e.g., trained regression model) that maps covariates to predicted responses. A **score function** $s: \mathcal{X} \times \mathcal{Y} \times \mathcal{F} \to \mathbb{R}$ measures the conformity or "strangeness" of a response $y$ given covariates $x$ and predictor $\hat{\mu}$, where $\mathcal{F}$ is the space of predictors.

For a target coverage level $1-\alpha \in (0,1)$, we define the **empirical $(1-\alpha)$-quantile** of scores as:
$$\hat{q}_{1-\alpha} = \text{Quantile}_{1-\alpha}\left(\{s(X_i, Y_i, \hat{\mu})\}_{i=1}^n \cup \{\infty\}\right)$$

The **conformal prediction set** for test point $X_{n+1}$ is then:
$$\hat{C}(X_{n+1}) = \{y \in \mathcal{Y} : s(X_{n+1}, y, \hat{\mu}) \leq \hat{q}_{1-\alpha}\}$$

## 1.2 Formal Problem Statement

**Given:** 
- Training data $\{(X_i, Y_i)\}_{i=1}^n$ drawn i.i.d. from $P_{XY}$
- A class of score functions $\mathcal{S} = \{s_\theta : \theta \in \Theta\}$ parameterized by $\theta$
- Target coverage level $1-\alpha$

**Find:** An optimal score function $s^* \in \mathcal{S}$ that minimizes expected interval width while maintaining coverage guarantees.

**Guarantee:** The resulting prediction intervals must satisfy finite-sample marginal coverage:
$$\mathbb{P}(Y_{n+1} \in \hat{C}(X_{n+1})) \geq 1-\alpha$$
for any distribution $P_{XY}$ and any finite sample size $n$.

## 1.3 Optimization Objective

We seek to solve the constrained optimization problem:
$$\min_{s \in \mathcal{S}} \mathbb{E}[W(s, X_{n+1})] \quad \text{subject to} \quad \mathbb{P}(Y_{n+1} \in \hat{C}_s(X_{n+1})) \geq 1-\alpha$$

where $W(s, x)$ denotes the expected width of the prediction interval at point $x$ using score function $s$, and $\hat{C}_s(x)$ is the conformal prediction set constructed using score $s$.

For regression with interval predictions, we typically have $W(s, x) = \mathbb{E}[|\hat{C}_s(x)|]$ where $|\cdot|$ denotes interval length.

## 1.4 Technical Assumptions

**A1 (Exchangeability):** The augmented sequence $(X_1, Y_1), \ldots, (X_n, Y_n), (X_{n+1}, Y_{n+1})$ is exchangeable, ensuring the validity of conformal prediction.

**A2 (Score Function Regularity):** Each $s_\theta \in \mathcal{S}$ is measurable and satisfies appropriate continuity conditions for optimization.

**A3 (Prediction Set Structure):** For each $x \in \mathcal{X}$ and $s \in \mathcal{S}$, the prediction set $\{y : s(x, y, \hat{\mu}) \leq t\}$ forms an interval (or union of intervals) for any threshold $t$.

**A4 (Finite Moments):** $\mathbb{E}[|Y|^2] < \infty$ and score functions have bounded second moments to ensure well-defined optimization objectives.

These assumptions are standard in conformal prediction literature and align with the exchangeability requirements established in Tibshirani et al. (2020), while extending to the score function learning setting.

# Section 2: Methodology

## 2.1 Approach Overview

Our approach learns optimal score functions through a bilevel optimization framework that directly optimizes interval efficiency while maintaining conformal coverage guarantees. The key insight is to parameterize score functions and optimize their parameters using a validation-based objective that balances coverage and efficiency.

## 2.2 Score Function Parameterization

We parameterize score functions as:
$$s_\theta(x, y, \hat{\mu}) = g_\theta(x, |y - \hat{\mu}(x)|, \hat{\mu}(x))$$

where $g_\theta: \mathcal{X} \times \mathbb{R}_+ \times \mathbb{R} \to \mathbb{R}_+$ is a neural network with parameters $\theta$ that takes as input the covariates $x$, absolute residual $|y - \hat{\mu}(x)|$, and predicted value $\hat{\mu}(x)$.

This parameterization allows the score function to adapt to local prediction uncertainty patterns while maintaining the property that larger residuals generally yield larger scores.

## 2.3 Bilevel Optimization Algorithm

Our algorithm splits the training data into three parts: training set $D_{\text{train}}$ for fitting $\hat{\mu}$, calibration set $D_{\text{cal}}$ for computing quantiles, and validation set $D_{\text{val}}$ for optimizing score parameters.

```
Algorithm: Adaptive Conformal Score Learning

Input: Data D, coverage level 1-α, score function class S_θ
Output: Optimal score function s*

1. Split D into D_train, D_cal, D_val (proportions 0.6, 0.2, 0.2)

2. Train predictor μ̂ on D_train

3. Initialize score parameters θ₀

4. For t = 1, 2, ..., T:
   a. Compute scores on calibration set:
      S_cal = {s_θₜ(xᵢ, yᵢ, μ̂) : (xᵢ, yᵢ) ∈ D_cal}
   
   b. Compute conformal quantile:
      q̂₁₋ₐ = Quantile₁₋ₐ(S_cal ∪ {∞})
   
   c. Evaluate on validation set:
      For each (xⱼ, yⱼ) ∈ D_val:
         - Construct interval Ĉ_θₜ(xⱼ) = {y : s_θₜ(xⱼ, y, μ̂) ≤ q̂₁₋ₐ}
         - Compute coverage: cⱼ = 1[yⱼ ∈ Ĉ_θₜ(xⱼ)]
         - Compute width: wⱼ = |Ĉ_θₜ(xⱼ)|
   
   d. Compute validation objective:
      L(θₜ) = (1/|D_val|) Σⱼ wⱼ + λ · max(0, α - (1/|D_val|) Σⱼ cⱼ)²
   
   e. Update parameters: θₜ₊₁ = θₜ - η∇_θ L(θₜ)

5. Return s* = s_θₜ
```

## 2.4 Design Justifications

**Data Splitting Strategy:** The three-way split ensures proper separation between model training, conformal calibration, and score optimization, preventing overfitting while maintaining coverage guarantees.

**Penalty Formulation:** The quadratic penalty term $\lambda \cdot \max(0, \alpha - \hat{\text{coverage}})^2$ strongly penalizes under-coverage while allowing the algorithm to focus on width minimization when coverage is adequate.

**Gradient-Based Optimization:** We use automatic differentiation through the interval construction process, approximating discrete operations (quantile computation, interval membership) with smooth surrogates during training.

**Score Function Architecture:** The neural network $g_\theta$ uses the absolute residual as input, building on the intuition from Tibshirani et al. (2020) that effective score functions should incorporate prediction uncertainty measures.

## 2.5 Theoretical Properties

**Coverage Guarantee:** By construction, our method maintains the finite-sample coverage guarantee of standard conformal prediction. For any learned score function, the conformal procedure ensures:
$$\mathbb{P}(Y_{n+1} \in \hat{C}(X_{n+1})) \geq \frac{\lceil (n+1)(1-\alpha) \rceil}{n+1}$$

**Consistency:** Under regularity conditions on the score function class and assuming the validation objective converges, the learned score function approaches the population-optimal score that minimizes expected interval width subject to coverage constraints.

**Computational Complexity:** Each iteration requires $O(n \log n)$ time for quantile computation and $O(n \cdot |\Theta|)$ for gradient computation, where $|\Theta|$ is the number of parameters in the score function.

The method scales efficiently to large datasets through mini-batch processing of the validation objective and can leverage modern automatic differentiation frameworks for gradient computation.
