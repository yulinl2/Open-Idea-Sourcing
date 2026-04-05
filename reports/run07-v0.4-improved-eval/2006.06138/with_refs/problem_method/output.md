# Reconstruction: problem_method
**Paper:** 2006.06138  
**Condition:** with_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Problem Formulation

## Notation and Setup

Let $\mathcal{X} \subseteq \mathbb{R}^d$ denote the covariate space and $\mathcal{Y} \subseteq \mathbb{R}$ the outcome space. We observe $n$ training units $(X_i, Y_i) \in \mathcal{X} \times \mathcal{Y}$, $i = 1, \ldots, n$, where each unit has two potential outcomes: $Y_i(1)$ under treatment and $Y_i(0)$ under control. Let $W_i \in \{0,1\}$ denote the treatment assignment indicator, so that the observed outcome is $Y_i = W_i Y_i(1) + (1-W_i) Y_i(0)$.

For a new target unit with covariates $X_{n+1}$, we define the conditional average treatment effect (CATE) as:
$$\tau(x) = \mathbb{E}[Y(1) - Y(0) | X = x]$$

Let $P$ denote the joint distribution of $(X, Y(0), Y(1))$ in the training population, and $\tilde{P}$ denote the corresponding distribution in the target population. We allow for covariate shift between training and target populations, meaning the marginal covariate distributions may differ: $P_X \neq \tilde{P}_X$, while maintaining the assumption that the conditional potential outcome distributions remain invariant: $P_{Y(0), Y(1)|X} = \tilde{P}_{Y(0), Y(1)|X}$.

## Problem Statement

**Given:** Training data $\{(X_i, W_i, Y_i)\}_{i=1}^n$ from distribution $P$, a target covariate $X_{n+1}$ from distribution $\tilde{P}_X$, and a desired coverage level $1-\alpha \in (0,1)$.

**Find:** A prediction interval $\hat{C}_n(X_{n+1}) \subseteq \mathbb{R}$ for the individual treatment effect $\tau_{n+1} = Y_{n+1}(1) - Y_{n+1}(0)$.

**Guarantee:** The interval should satisfy the finite-sample coverage property:
$$\mathbb{P}\left[\tau_{n+1} \in \hat{C}_n(X_{n+1})\right] \geq 1 - \alpha$$
where the probability is taken over the randomness in both the training data and the target unit.

## Objective

Our objective is to construct a distribution-free prediction interval that provides valid uncertainty quantification for individual treatment effects without requiring:
- Asymptotic approximations or large-sample assumptions  
- Strong parametric assumptions on the outcome distributions
- Exchangeability between training and target populations
- Observability of both potential outcomes for any individual

The core challenge is that $\tau_{n+1}$ is never directly observable, as we can only observe one potential outcome per individual. We address this through a conformal prediction framework that leverages pseudo-outcomes constructed from estimated CATE functions.

## Technical Assumptions

**Assumption 1 (Unconfoundedness):** Treatment assignment is unconfounded given covariates:
$$(Y(0), Y(1)) \perp W | X$$

**Assumption 2 (Overlap):** There exist constants $0 < c < C < 1$ such that:
$$c \leq \mathbb{P}[W = 1 | X = x] \leq C \quad \text{for all } x \in \mathcal{X}$$

**Assumption 3 (Covariate Shift with Known Likelihood Ratio):** The target covariate distribution $\tilde{P}_X$ is absolutely continuous with respect to the training distribution $P_X$, and the likelihood ratio $w(x) = \frac{d\tilde{P}_X}{dP_X}(x)$ is known or can be accurately estimated.

**Assumption 4 (Potential Outcome Invariance):** The conditional distributions of potential outcomes given covariates are identical across populations:
$$P_{Y(0), Y(1)|X=x} = \tilde{P}_{Y(0), Y(1)|X=x} \quad \text{for all } x \in \mathcal{X}$$

These assumptions are standard in the causal inference literature. Assumption 1 ensures identifiability of causal effects, Assumption 2 prevents extrapolation issues, and Assumptions 3-4 formalize the covariate shift setting while maintaining causal effect transportability.

## Connection to Prior Work

This formulation extends the conformal prediction framework of Tibshirani et al. (2020) from the standard regression setting to causal inference. While their work addresses covariate shift for predictive inference on observed outcomes, our problem requires handling the fundamental challenge that individual treatment effects are never observed. We build upon their weighted conformal prediction methodology but must adapt it to work with pseudo-outcomes that serve as proxies for the unobservable individual treatment effects.

# Methodology

## High-Level Approach

Our approach constructs conformal prediction intervals for individual treatment effects by combining three key components: (1) estimation of conditional average treatment effects using machine learning methods, (2) construction of conformity scores based on pseudo-outcomes that proxy for unobservable individual treatment effects, and (3) weighted conformal prediction to handle covariate shift between training and target populations.

The core insight is that while we cannot observe individual treatment effects directly, we can construct pseudo-outcomes that capture the conformity of a hypothesized treatment effect value with the observed data pattern. By applying weighted conformal prediction to these pseudo-outcomes, we obtain finite-sample coverage guarantees that account for both the uncertainty in CATE estimation and the covariate shift.

## Core Algorithm

### Step 1: CATE Estimation and Data Splitting

We split the training data into two parts: $\mathcal{D}_1 = \{(X_i, W_i, Y_i)\}_{i=1}^{n_1}$ for CATE estimation and $\mathcal{D}_2 = \{(X_i, W_i, Y_i)\}_{i=n_1+1}^n$ for conformity score computation, where $n_1 + n_2 = n$.

Using $\mathcal{D}_1$, we estimate the CATE function $\hat{\tau}(x)$ and the conditional mean functions $\hat{\mu}_0(x) = \mathbb{E}[Y(0)|X=x]$ and $\hat{\mu}_1(x) = \mathbb{E}[Y(1)|X=x]$ using any suitable machine learning method (e.g., causal forests, T-learner, S-learner).

### Step 2: Pseudo-Outcome Construction

For each unit $i \in \mathcal{D}_2$ and each candidate treatment effect value $\tau \in \mathbb{R}$, we construct a pseudo-outcome that measures how well $\tau$ conforms to the observed data:

$$\tilde{Y}_i(\tau) = \begin{cases}
Y_i - \hat{\mu}_0(X_i) - \tau & \text{if } W_i = 1 \\
Y_i - \hat{\mu}_0(X_i) & \text{if } W_i = 0
\end{cases}$$

This pseudo-outcome represents the residual after subtracting the expected control outcome and (for treated units) the hypothesized treatment effect.

### Step 3: Conformity Score Definition

We define the conformity score for a candidate pair $(x, \tau)$ as:
$$S((x, \tau), \mathcal{D}_2) = |\tilde{Y}_{n_2+1}(\tau)|$$
where $\tilde{Y}_{n_2+1}(\tau)$ is the pseudo-outcome for a hypothetical unit with covariates $x$, treatment effect $\tau$, and outcome $Y$ determined by the conformity assessment.

For the calibration data points, we compute:
$$V_i^{(x,\tau)} = |\tilde{Y}_i(\tau)|, \quad i \in \mathcal{D}_2$$

### Step 4: Weighted Conformal Prediction

To handle covariate shift, we compute weighted quantiles using the likelihood ratio $w(x) = \frac{d\tilde{P}_X}{dP_X}(x)$. Define the weights:
$$p_i^w(x) = \frac{w(X_i)}{\sum_{j \in \mathcal{D}_2} w(X_j) + w(x)}, \quad i \in \mathcal{D}_2$$
$$p_{n+1}^w(x) = \frac{w(x)}{\sum_{j \in \mathcal{D}_2} w(X_j) + w(x)}$$

### Step 5: Interval Construction

The conformal prediction interval for the treatment effect at $X_{n+1}$ is:
$$\hat{C}_n(X_{n+1}) = \left\{\tau \in \mathbb{R} : V_{n+1}^{(X_{n+1},\tau)} \leq Q_{1-\alpha}^w(X_{n+1})\right\}$$

where $Q_{1-\alpha}^w(x)$ is the $(1-\alpha)$-quantile of the weighted distribution:
$$\sum_{i \in \mathcal{D}_2} p_i^w(x) \delta_{V_i^{(x,\tau)}} + p_{n+1}^w(x) \delta_{\infty}$$

## Complete Algorithm

```
Algorithm: Weighted Conformal Prediction for Individual Treatment Effects

Input: Training data {(X_i, W_i, Y_i)}_{i=1}^n, target covariate X_{n+1}, 
       coverage level 1-α, likelihood ratio function w(·)

1. Split training data: D_1 ← {(X_i, W_i, Y_i)}_{i=1}^{n_1}, 
                       D_2 ← {(X_i, W_i, Y_i)}_{i=n_1+1}^n

2. Fit CATE estimator on D_1:
   - Estimate μ̂_0(x), μ̂_1(x), τ̂(x) using preferred method

3. For each candidate τ and unit i ∈ D_2:
   - Compute pseudo-outcome: Ỹ_i(τ) = {Y_i - μ̂_0(X_i) - τ  if W_i = 1
                                       {Y_i - μ̂_0(X_i)      if W_i = 0
   - Compute conformity score: V_i^(τ) = |Ỹ_i(τ)|

4. Compute weights for target covariate X_{n+1}:
   - p_i^w ← w(X_i) / [∑_{j∈D_2} w(X_j) + w(X_{n+1})] for i ∈ D_2
   - p_{n+1}^w ← w(X_{n+1}) / [∑_{j∈D_2} w(X_j) + w(X_{n+1})]

5. For each candidate τ:
   - Compute V_{n+1}^(τ) = |Ỹ_{n+1}(τ)| where Ỹ_{n+1}(τ) is pseudo-outcome for (X_{n+1}, τ)
   - Compute weighted quantile: Q_{1-α}^w ← Quantile(1-α; ∑_i p_i^w δ_{V_i^(τ)} + p_{n+1}^w δ_∞)

6. Return: Ĉ_n(X_{n+1}) = {τ : V_{n+1}^(τ) ≤ Q_{1-α}^w}
```

## Theoretical Properties

**Theorem (Finite-Sample Coverage).** Under Assumptions 1-4, the conformal prediction interval satisfies:
$$\mathbb{P}[\tau_{n+1} \in \hat{C}_n(X_{n+1})] \geq 1 - \alpha$$

The proof follows by showing that the pseudo-outcomes, when weighted appropriately, satisfy a weighted exchangeability property that enables application of the weighted conformal prediction framework from Tibshirani et al. (2020).

**Consistency Property.** As $n_1, n_2 \to \infty$ with $n_1/n \to \rho \in (0,1)$, if the CATE estimator $\hat{\tau}(x)$ is consistent, then the intervals achieve asymptotic efficiency while maintaining finite-sample validity.

## Computational Complexity

The algorithm has computational complexity $O(n \cdot |\mathcal{T}|)$ where $|\mathcal{T}|$ is the number of candidate treatment effect values evaluated. In practice, we can efficiently search over $\mathcal{T}$ using bisection or grid search methods. The CATE estimation step dominates the computational cost and depends on the chosen base learner. The weighted quantile computations add minimal overhead compared to standard conformal prediction.

## Design Justifications

The pseudo-outcome construction is motivated by the need to create observable quantities that proxy for unobservable individual treatment effects while respecting the potential outcomes framework. The weighted conformal approach directly addresses covariate shift by reweighting the calibration data to match the target population. The data splitting ensures that the CATE estimation and conformity assessment are performed on independent data, which is crucial for maintaining the validity of coverage guarantees.
