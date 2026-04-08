# Reconstruction: problem_method
**Paper:** 2006.06138  
**Condition:** no_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Problem Formulation

## Notation and Setup

Let $(\mathcal{X}, \mathcal{Y}, \mathcal{T})$ denote the covariate, outcome, and treatment spaces, respectively, where $\mathcal{X} \subseteq \mathbb{R}^d$, $\mathcal{Y} \subseteq \mathbb{R}$, and $\mathcal{T} = \{0, 1\}$ for binary treatments. For each unit $i$, we observe the triple $(X_i, T_i, Y_i)$ where $X_i \in \mathcal{X}$ represents covariates, $T_i \in \mathcal{T}$ indicates treatment assignment, and $Y_i \in \mathcal{Y}$ is the observed outcome.

Following the potential outcomes framework, let $Y_i(0)$ and $Y_i(1)$ denote the potential outcomes under control and treatment conditions, respectively. The fundamental causal inference problem ensures that we only observe $Y_i = T_i Y_i(1) + (1-T_i)Y_i(0)$ for each unit. The individual treatment effect (ITE) for unit $i$ is defined as:
$$\tau_i = Y_i(1) - Y_i(0)$$

Let $\tau(x) = \mathbb{E}[Y(1) - Y(0) \mid X = x]$ denote the conditional average treatment effect (CATE) function, which represents the expected treatment effect for individuals with covariates $x$.

## Problem Statement

**Given:** A dataset $\mathcal{D} = \{(X_i, T_i, Y_i)\}_{i=1}^n$ of $n$ independent observations, and a target covariate vector $x_0 \in \mathcal{X}$.

**Find:** A prediction interval $\mathcal{C}_\alpha(x_0, \mathcal{D})$ for the individual treatment effect $\tau_0$ of a new unit with covariates $x_0$.

**Guarantee:** The interval should satisfy finite-sample coverage guarantees:
$$\mathbb{P}(\tau_0 \in \mathcal{C}_\alpha(x_0, \mathcal{D})) \geq 1 - \alpha$$
where the probability is taken over the randomness in both the training data $\mathcal{D}$ and the potential outcomes $(Y_0(0), Y_0(1))$ of the target unit, and $\alpha \in (0, 1)$ is the desired miscoverage level.

## Objective and Key Challenges

The primary objective is to construct prediction intervals that provide valid uncertainty quantification for individual-level causal effects while maintaining computational tractability and practical utility. This requires addressing several fundamental challenges:

1. **Missing Counterfactuals:** For any individual, we observe only one potential outcome, making direct estimation of $\tau_0$ impossible without modeling assumptions.

2. **Dual Sources of Uncertainty:** The prediction interval must account for both epistemic uncertainty (due to finite sample estimation) and aleatoric uncertainty (inherent variability in individual responses).

3. **Model Agnosticism:** The approach should provide valid coverage regardless of the complexity or correctness of the underlying CATE estimation procedure.

## Technical Assumptions

We impose the following standard assumptions from the causal inference literature:

**Assumption 1 (SUTVA):** The Stable Unit Treatment Value Assumption holds, ensuring that potential outcomes for unit $i$ depend only on unit $i$'s treatment assignment and not on other units' treatments.

**Assumption 2 (Unconfoundedness):** Treatment assignment is unconfounded given observed covariates:
$$Y(0), Y(1) \perp T \mid X$$

**Assumption 3 (Overlap):** There exists $\epsilon > 0$ such that for all $x \in \mathcal{X}$:
$$\epsilon \leq e(x) \leq 1 - \epsilon$$
where $e(x) = \mathbb{P}(T = 1 \mid X = x)$ is the propensity score.

**Assumption 4 (Exchangeability):** The target unit with covariates $x_0$ is exchangeable with units in the training population, meaning $(X_0, Y_0(0), Y_0(1))$ follows the same distribution as training units.

These assumptions are standard in the causal inference literature and enable identification of causal effects from observational data. Assumption 4 ensures that our uncertainty quantification is meaningful for the target population.

## Connection to Prior Work

This formulation extends classical approaches to CATE estimation by explicitly addressing uncertainty quantification. Traditional methods focus on point estimation of $\tau(x)$ using techniques such as T-learners, S-learners, or more sophisticated meta-learning approaches. However, these methods typically rely on asymptotic normality assumptions that may not hold in finite samples or under model misspecification.

Recent work in conformal prediction provides a framework for distribution-free uncertainty quantification, but direct application to causal inference is non-trivial due to the missing counterfactual problem. Our formulation bridges this gap by seeking finite-sample guarantees for individual treatment effect prediction that do not rely on parametric assumptions about the outcome models or the treatment effect heterogeneity.

# Methodology

## High-Level Approach

Our proposed methodology, **Conformal Causal Prediction (CCP)**, leverages the conformal prediction framework to provide distribution-free uncertainty quantification for individual treatment effects. The key insight is to construct separate conformal predictors for the potential outcomes $Y(0)$ and $Y(1)$, then combine them to form prediction intervals for the treatment effect $\tau_0 = Y_0(1) - Y_0(1)$.

The approach consists of three main components: (1) splitting the data to ensure valid conformal inference, (2) training separate outcome models for treated and control units, and (3) constructing prediction intervals using conformal scores that account for the causal structure.

## Core Algorithm

### Data Splitting Strategy

We employ a three-way data split to maintain the validity of conformal prediction while accommodating the causal inference setting:

```
Algorithm 1: Data Splitting for Conformal Causal Prediction

Input: Dataset D = {(X_i, T_i, Y_i)}_{i=1}^n, split ratios (r_train, r_cal, r_test)

1. Randomly partition indices {1, ..., n} into three disjoint sets:
   - I_train: training set indices (|I_train| = ⌊r_train × n⌋)
   - I_cal: calibration set indices (|I_cal| = ⌊r_cal × n⌋)  
   - I_test: test set indices (remaining)

2. Create treatment-specific subsets:
   - D_train^(0) = {(X_i, Y_i) : i ∈ I_train, T_i = 0}
   - D_train^(1) = {(X_i, Y_i) : i ∈ I_train, T_i = 1}
   - D_cal^(0) = {(X_i, Y_i) : i ∈ I_cal, T_i = 0}
   - D_cal^(1) = {(X_i, Y_i) : i ∈ I_cal, T_i = 1}

Output: Split datasets for training and calibration
```

### Outcome Model Training

We train separate regression models for each treatment group to avoid extrapolation issues:

```
Algorithm 2: Treatment-Specific Model Training

Input: Training sets D_train^(0), D_train^(1)

1. Train control outcome model:
   μ̂_0(x) = argmin_{f ∈ F} Σ_{(x,y) ∈ D_train^(0)} L(f(x), y)

2. Train treatment outcome model:
   μ̂_1(x) = argmin_{f ∈ F} Σ_{(x,y) ∈ D_train^(1)} L(f(x), y)

Output: Fitted models μ̂_0, μ̂_1
```

where $F$ represents the function class (e.g., random forests, neural networks) and $L$ is a suitable loss function (e.g., squared error).

### Conformal Score Construction

For each treatment group, we compute conformal scores on the calibration set:

```
Algorithm 3: Conformal Score Computation

Input: Models μ̂_0, μ̂_1, calibration sets D_cal^(0), D_cal^(1)

1. Compute residuals for control group:
   R_i^(0) = |Y_i - μ̂_0(X_i)| for all (X_i, Y_i) ∈ D_cal^(0)

2. Compute residuals for treatment group:
   R_i^(1) = |Y_i - μ̂_1(X_i)| for all (X_i, Y_i) ∈ D_cal^(1)

3. Compute quantiles:
   q_α^(0) = Quantile(1 - α/2, {R_i^(0)})
   q_α^(1) = Quantile(1 - α/2, {R_i^(1)})

Output: Conformal quantiles q_α^(0), q_α^(1)
```

### Treatment Effect Prediction Interval

Finally, we construct the prediction interval for the individual treatment effect:

```
Algorithm 4: ITE Prediction Interval Construction

Input: Target covariates x_0, models μ̂_0, μ̂_1, quantiles q_α^(0), q_α^(1)

1. Predict potential outcomes:
   ŷ_0 = μ̂_0(x_0)
   ŷ_1 = μ̂_1(x_0)

2. Construct individual outcome intervals:
   C_0 = [ŷ_0 - q_α^(0), ŷ_0 + q_α^(0)]
   C_1 = [ŷ_1 - q_α^(1), ŷ_1 + q_α^(1)]

3. Compute treatment effect interval using interval arithmetic:
   C_τ = [ŷ_1 - ŷ_0 - (q_α^(0) + q_α^(1)), ŷ_1 - ŷ_0 + (q_α^(0) + q_α^(1))]

Output: Prediction interval C_τ for individual treatment effect
```

## Design Justifications

**Separate Model Training:** Training distinct models for each treatment group avoids the need to extrapolate predictions to regions of covariate space not well-represented in the training data. This is particularly important when treatment assignment depends on covariates.

**Conservative Interval Construction:** The final interval width incorporates uncertainty from both potential outcome predictions, leading to conservative but valid coverage. The interval arithmetic in Step 3 of Algorithm 4 ensures that we account for the maximum possible error in the treatment effect estimate.

**Treatment-Agnostic Conformal Scores:** Using absolute residuals as conformal scores makes minimal assumptions about the error distribution and works with any regression algorithm, maintaining the model-agnostic property of conformal prediction.

## Theoretical Properties

**Theorem 1 (Finite-Sample Coverage):** Under Assumptions 1-4, the prediction interval $C_τ$ satisfies:
$$\mathbb{P}(\tau_0 \in C_τ) \geq 1 - α$$
for any $\alpha \in (0, 1)$, where the probability is taken over the randomness in data splitting, training data, and the target unit's potential outcomes.

**Proof Sketch:** The result follows from the marginal coverage guarantees of conformal prediction applied to each treatment group separately, combined with the union bound for interval arithmetic operations.

**Corollary 1 (Asymptotic Efficiency):** As $n \to \infty$, if the outcome models achieve optimal prediction accuracy, the interval width converges to the minimal width achievable by any method satisfying the coverage constraint.

## Computational Complexity

The computational complexity of CCP is dominated by the training of the outcome models. Let $C_{train}$ denote the complexity of training a single model on $m$ samples. Then:

- **Training Phase:** $O(C_{train}(n_0) + C_{train}(n_1))$ where $n_0, n_1$ are the numbers of control and treated units in the training set.
- **Calibration Phase:** $O(m_0 + m_1 + m_0 \log m_0 + m_1 \log m_1)$ where $m_0, m_1$ are calibration set sizes, and the log terms arise from quantile computation.
- **Prediction Phase:** $O(1)$ per prediction after preprocessing.

The method scales linearly with sample size and can accommodate high-dimensional covariates through the choice of base learning algorithm, making it practical for real-world applications.
