# Reconstruction: problem_method
**Paper:** 2602.04770  
**Condition:** no_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Problem Formulation

## Notation and Setup

Let $(\mathcal{X}, \mathcal{Y})$ denote the input and output spaces, where $\mathcal{X} \subseteq \mathbb{R}^d$ and $\mathcal{Y} \subseteq \mathbb{R}$. We observe data $(X_1, Y_1), \ldots, (X_n, Y_n), (X_{n+1}, Y_{n+1})$ drawn i.i.d. from an unknown distribution $P_{X,Y}$. The first $n$ observations constitute our training set, while $(X_{n+1}, Y_{n+1})$ represents a test point where we seek to predict $Y_{n+1}$ given $X_{n+1}$.

Let $\hat{\mu}: \mathcal{X} \rightarrow \mathbb{R}$ denote a point predictor trained on the first $n$ samples. In conformal prediction, we construct prediction intervals using a score function $s: \mathcal{X} \times \mathcal{Y} \times \mathbb{R} \rightarrow \mathbb{R}$ that measures the "non-conformity" or uncertainty of a prediction. Specifically, $s(x, y, \hat{\mu}(x))$ quantifies how unusual the true outcome $y$ is given the prediction $\hat{\mu}(x)$ at input $x$.

For a target miscoverage level $\alpha \in (0, 1)$, the conformal prediction interval is constructed as:
$$C_\alpha(X_{n+1}) = \{y \in \mathcal{Y} : s(X_{n+1}, y, \hat{\mu}(X_{n+1})) \leq \hat{q}_{1-\alpha}\}$$

where $\hat{q}_{1-\alpha}$ is the $(1-\alpha)$-quantile of the scores $\{s(X_i, Y_i, \hat{\mu}(X_i))\}_{i=1}^n$ computed on the training data.

## Formal Problem Statement

**Given:** 
- Training data $\{(X_i, Y_i)\}_{i=1}^n$ drawn i.i.d. from $P_{X,Y}$
- A point predictor $\hat{\mu}$ trained on this data
- Target coverage level $1-\alpha$ where $\alpha \in (0, 1)$
- A parametric family of score functions $\mathcal{S} = \{s_\theta : \theta \in \Theta\}$

**Find:** An optimal score function $s^* \in \mathcal{S}$ that minimizes expected interval width while maintaining finite-sample coverage guarantees.

**Guarantee:** The resulting prediction intervals must satisfy:
$$\mathbb{P}(Y_{n+1} \in C_\alpha(X_{n+1})) \geq 1 - \alpha$$
for any distribution $P_{X,Y}$ and any finite sample size $n$.

## Objective Function

We seek to solve the optimization problem:
$$s^* = \arg\min_{s \in \mathcal{S}} \mathbb{E}[\text{width}(C_\alpha^s(X_{n+1}))]$$
subject to the coverage constraint:
$$\inf_{P_{X,Y}} \mathbb{P}(Y_{n+1} \in C_\alpha^s(X_{n+1})) \geq 1 - \alpha$$

where $C_\alpha^s$ denotes the prediction interval constructed using score function $s$, and the infimum is taken over all possible distributions.

The width of an interval $C_\alpha^s(x) = \{y : s(x, y, \hat{\mu}(x)) \leq q\}$ depends on the level sets of the score function. For efficiency, we want score functions that produce compact, well-calibrated level sets around the point prediction.

## Technical Assumptions

**A1 (Exchangeability):** The augmented sequence $(X_1, Y_1), \ldots, (X_n, Y_n), (X_{n+1}, Y_{n+1})$ is exchangeable. This is the fundamental assumption enabling conformal prediction's finite-sample guarantees.

**A2 (Score Function Regularity):** Each $s_\theta \in \mathcal{S}$ is continuous in its arguments and satisfies $s_\theta(x, y, \hat{\mu}(x)) \geq 0$ for all $(x, y) \in \mathcal{X} \times \mathcal{Y}$.

**A3 (Parametric Constraint):** The parameter space $\Theta$ is compact, ensuring the existence of optimal parameters and enabling uniform convergence arguments.

**A4 (Interval Structure):** For each $x \in \mathcal{X}$ and threshold $q \geq 0$, the level set $\{y : s_\theta(x, y, \hat{\mu}(x)) \leq q\}$ forms a connected interval (possibly infinite), enabling meaningful interval prediction.

**A5 (Finite Moments):** $\mathbb{E}[|Y|^2] < \infty$ to ensure well-defined interval widths and enable concentration inequalities.

These assumptions are standard in conformal prediction literature and ensure both theoretical tractability and practical applicability of the framework.

# Methodology

## High-Level Approach

Our approach learns optimal score functions through a two-stage procedure that respects the coverage constraint while minimizing interval width. The key insight is to parameterize score functions as learnable models and optimize them using a regularized objective that balances coverage validity with interval efficiency.

We propose **Adaptive Conformal Score Learning (ACSL)**, which learns score functions $s_\theta(x, y, \hat{\mu}(x))$ by minimizing a surrogate loss that approximates expected interval width while maintaining coverage through careful regularization.

## Core Algorithm

### Score Function Parameterization

We parameterize the score function as:
$$s_\theta(x, y, \hat{\mu}(x)) = \|y - \hat{\mu}(x)\|_{\Sigma_\theta(x)}^2 + \lambda \cdot r_\theta(x, y, \hat{\mu}(x))$$

where:
- $\|\cdot\|_{\Sigma_\theta(x)}^2$ represents a learned Mahalanobis distance with $\Sigma_\theta(x) \succ 0$
- $r_\theta(x, y, \hat{\mu}(x))$ is a learned residual correction term
- $\lambda > 0$ balances the two components

The matrix $\Sigma_\theta(x)$ is parameterized through its Cholesky decomposition to ensure positive definiteness, while $r_\theta$ is implemented as a neural network with inputs $(x, y - \hat{\mu}(x))$.

### Training Objective

We minimize the following regularized loss function:
$$\mathcal{L}(\theta) = \mathbb{E}[\text{Width}(C_\alpha^{s_\theta}(X))] + \beta \cdot \text{Coverage-Penalty}(\theta)$$

The width term is approximated using:
$$\text{Width}(C_\alpha^{s_\theta}(x)) \approx 2\sqrt{\frac{\hat{q}_{1-\alpha}^{s_\theta}}{\lambda_{\min}(\Sigma_\theta(x))}}$$

where $\lambda_{\min}(\Sigma_\theta(x))$ is the smallest eigenvalue of $\Sigma_\theta(x)$.

The coverage penalty ensures finite-sample validity:
$$\text{Coverage-Penalty}(\theta) = \max\left(0, \alpha - \frac{1}{n}\sum_{i=1}^n \mathbb{I}[s_\theta(X_i, Y_i, \hat{\mu}(X_i)) \leq \hat{q}_{1-\alpha}^{s_\theta}]\right)^2$$

### Algorithm Implementation

```
Algorithm: Adaptive Conformal Score Learning (ACSL)

Input: Training data {(X_i, Y_i)}_{i=1}^n, point predictor μ̂, coverage level 1-α
Output: Learned score function s_θ*

1. Initialize parameters θ_0 randomly
2. For epoch t = 1 to T:
   a. Compute scores: R_i = s_θ_t(X_i, Y_i, μ̂(X_i)) for i = 1,...,n
   b. Compute quantile: q̂_{1-α} = Quantile(R_1,...,R_n, 1-α)
   c. Estimate interval widths: W_i = 2√(q̂_{1-α} / λ_min(Σ_θ_t(X_i)))
   d. Compute coverage rate: Ĉ = (1/n)∑_{i=1}^n I[R_i ≤ q̂_{1-α}]
   e. Update loss: L = (1/n)∑_{i=1}^n W_i + β·max(0, α - Ĉ)²
   f. Update parameters: θ_{t+1} = θ_t - η·∇_θ L
3. Return θ* = θ_T
```

### Theoretical Properties

**Coverage Guarantee:** Under exchangeability (A1), our method maintains the fundamental conformal prediction guarantee:
$$\mathbb{P}(Y_{n+1} \in C_\alpha^{s_{\theta^*}}(X_{n+1})) \geq 1 - \alpha$$

This holds because the coverage penalty term drives the empirical coverage toward the target level during training.

**Consistency:** As $n \to \infty$, under mild regularity conditions, our learned score function converges to:
$$s^* = \arg\min_{s \in \mathcal{S}} \mathbb{E}[\text{width}(C_\alpha^s(X))]$$
subject to achieving exact coverage $1-\alpha$.

**Convergence Rate:** The optimization converges at rate $O(1/\sqrt{T})$ where $T$ is the number of training iterations, following standard stochastic gradient descent analysis.

### Design Justifications

1. **Mahalanobis Distance:** The adaptive metric $\Sigma_\theta(x)$ allows the score function to learn input-dependent uncertainty patterns, generalizing simple residual-based scores.

2. **Regularized Objective:** The coverage penalty ensures we never sacrifice validity for efficiency, maintaining the finite-sample guarantee that distinguishes conformal prediction.

3. **Two-Stage Structure:** Separating the distance metric from residual corrections provides interpretability while maintaining expressiveness.

### Computational Complexity

- **Training:** $O(T \cdot n \cdot d^3)$ where $T$ is epochs, $n$ is sample size, $d$ is input dimension
- **Inference:** $O(d^3)$ per prediction for computing the Mahalanobis distance
- **Memory:** $O(d^2)$ for storing the learned covariance matrices

The cubic dependence on dimension comes from matrix operations, but can be reduced to $O(d^2)$ using low-rank approximations of $\Sigma_\theta(x)$ when $d$ is large.
