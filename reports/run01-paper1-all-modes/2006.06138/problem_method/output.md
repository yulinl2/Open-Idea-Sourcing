# Reconstruction: problem_method
**Paper:** 2006.06138  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Problem Formulation

## Notation and Setup

Let $\mathcal{X}$ denote the input space and $\mathcal{Y}$ denote the output space. We consider prediction problems where the output consists of sets rather than single elements, so we work with the power set $\mathcal{P}(\mathcal{Y})$ of all possible subsets of $\mathcal{Y}$. Let $(X_1, Y_1), \ldots, (X_n, Y_n)$ be training data drawn exchangeably from some unknown distribution $P$, and let $(X_{n+1}, Y_{n+1}), \ldots, (X_{n+m}, Y_{n+m})$ be test data drawn from the same distribution.

Given a pre-trained predictive model $\hat{f}: \mathcal{X} \to \mathcal{P}(\mathcal{Y})$ that outputs prediction sets, we define a loss function $\ell: \mathcal{P}(\mathcal{Y}) \times \mathcal{Y} \to \mathbb{R}_+$ that measures the cost of predicting set $S \subseteq \mathcal{Y}$ when the true label is $y \in \mathcal{Y}$. The risk of the model is defined as:
$$R(\hat{f}) = \mathbb{E}[\ell(\hat{f}(X), Y)]$$
where the expectation is taken over the data distribution $P$.

Let $\mathcal{D}_{\text{cal}} = \{(X_1, Y_1), \ldots, (X_k, Y_k)\}$ denote a calibration dataset of size $k$ drawn exchangeably from $P$ and independent of the training data used to fit $\hat{f}$.

## Problem Statement

**Given:**
- A pre-trained model $\hat{f}: \mathcal{X} \to \mathcal{P}(\mathcal{Y})$
- A user-specified loss function $\ell: \mathcal{P}(\mathcal{Y}) \times \mathcal{Y} \to \mathbb{R}_+$
- A risk tolerance level $\alpha \in (0, 1)$
- A calibration dataset $\mathcal{D}_{\text{cal}}$

**Find:** A calibrated prediction function $\hat{g}: \mathcal{X} \to \mathcal{P}(\mathcal{Y})$ such that:
$$\mathbb{E}[\ell(\hat{g}(X), Y)] \leq \alpha$$
with probability at least $1-\delta$ for some confidence parameter $\delta > 0$.

**Guarantee:** The risk constraint must hold in finite samples without requiring distributional assumptions beyond exchangeability. The method should be:
1. **Model-agnostic:** Work with any base predictor $\hat{f}$
2. **Loss-agnostic:** Handle any user-specified loss function $\ell$
3. **Distribution-free:** Require only exchangeability, not specific distributional forms

## Objective and Constraints

The primary objective is to construct prediction sets that satisfy the risk constraint while minimizing unnecessary conservatism. Formally, we seek to solve:
$$\min_{\hat{g}} \mathbb{E}[|\hat{g}(X)|] \quad \text{subject to} \quad \mathbb{E}[\ell(\hat{g}(X), Y)] \leq \alpha$$
where $|\cdot|$ denotes set cardinality, representing the cost of larger prediction sets.

## Technical Assumptions

1. **Exchangeability:** The sequence $(X_1, Y_1), \ldots, (X_{n+m}, Y_{n+m})$ is exchangeable under the joint distribution.

2. **Finite Loss:** The loss function $\ell$ is bounded: $\sup_{S,y} \ell(S,y) < \infty$.

3. **Measurability:** All prediction functions and loss functions are measurable with respect to the appropriate $\sigma$-algebras.

4. **Independence:** The calibration set $\mathcal{D}_{\text{cal}}$ is independent of the training data used to construct $\hat{f}$.

The exchangeability assumption is weaker than the i.i.d. assumption typically required in statistical learning theory, making our approach broadly applicable. Unlike standard conformal prediction which focuses on coverage guarantees for classification, our formulation addresses general risk control for arbitrary loss functions over set-valued predictions.

## Connection to Prior Work

This formulation extends conformal prediction beyond coverage to general risk control. While Tibshirani et al. (2020) address conformal prediction under covariate shift using importance weighting, our problem considers the more general setting of risk control for arbitrary loss functions. The exchangeability assumption aligns with the conformal prediction literature, but our focus on set-valued predictions with user-specified loss functions represents a significant generalization of the standard framework.

# Methodology

## High-Level Approach

Our approach, which we term **Risk Controlling Prediction Sets (RCPS)**, follows a two-stage procedure. First, we use the base model $\hat{f}$ to generate an initial prediction set. Second, we apply a calibration procedure that adjusts these sets to satisfy the risk constraint using the calibration data $\mathcal{D}_{\text{cal}}$.

The key insight is to construct a family of nested prediction sets parameterized by a threshold $\lambda \in \mathbb{R}_+$, then select $\lambda$ via empirical risk minimization on the calibration set to ensure the risk constraint is satisfied with high probability.

## Core Algorithm

### Step 1: Conformity Score Construction

For each input $x$, we define a conformity score function $s(x, y; \lambda)$ that measures how "conforming" label $y$ is to being included in the prediction set at threshold level $\lambda$. Let $\hat{f}(x) = \{y_1, y_2, \ldots, y_m\}$ be the base model's prediction set, and let $p_i = \hat{p}(y_i | x)$ denote the predicted probability or confidence score for label $y_i$.

We define the conformity score as:
$$s(x, y; \lambda) = \mathbb{I}[y \in \hat{f}(x)] \cdot \hat{p}(y | x) + \mathbb{I}[y \notin \hat{f}(x)] \cdot (-\infty)$$

### Step 2: Threshold-Parameterized Prediction Sets

For a given threshold $\lambda$, we construct the prediction set:
$$C(x; \lambda) = \{y \in \mathcal{Y} : s(x, y; \lambda) \geq \lambda\}$$

This creates a nested family of sets: $C(x; \lambda_1) \supseteq C(x; \lambda_2)$ when $\lambda_1 \leq \lambda_2$.

### Step 3: Risk-Controlling Calibration

We select the threshold $\lambda$ by minimizing the empirical risk on the calibration set while ensuring the constraint is satisfied:

```
Algorithm: Risk Controlling Prediction Sets (RCPS)

Input: Base model f̂, loss function ℓ, risk level α, calibration data D_cal
Output: Calibrated prediction function ĝ

1. Initialize: candidate thresholds Λ = {λ₁, λ₂, ..., λₘ}
2. For each λ ∈ Λ:
   a. Compute prediction sets: Cᵢ(λ) = C(Xᵢ; λ) for i = 1,...,k
   b. Calculate empirical risk: R̂(λ) = (1/k) Σᵢ₌₁ᵏ ℓ(Cᵢ(λ), Yᵢ)
3. Apply Hoeffding's inequality correction:
   R̂_corrected(λ) = R̂(λ) + √(log(2|Λ|/δ)/(2k))
4. Select threshold: λ* = max{λ ∈ Λ : R̂_corrected(λ) ≤ α}
5. Return: ĝ(x) = C(x; λ*)
```

## Theoretical Properties

**Theorem 1 (Finite-Sample Risk Control):** Under the exchangeability assumption, the RCPS procedure satisfies:
$$\mathbb{P}[\mathbb{E}[\ell(\hat{g}(X), Y)] \leq \alpha] \geq 1 - \delta$$

**Proof Sketch:** The result follows from the union bound over the finite threshold set $\Lambda$ combined with Hoeffding's inequality applied to the empirical risk estimates. The exchangeability assumption ensures that the calibration and test data are identically distributed.

**Theorem 2 (Consistency):** As $k \to \infty$, if the optimal threshold $\lambda^*$ satisfying the risk constraint exists and is unique, then $\lambda_k \to \lambda^*$ almost surely, where $\lambda_k$ is the threshold selected by RCPS using $k$ calibration samples.

## Design Justifications

1. **Nested Set Construction:** The threshold-based approach ensures computational efficiency by reducing the optimization to a one-dimensional search over $\lambda$ values.

2. **Empirical Risk Minimization:** Following the principle of structural risk minimization, we select the least conservative threshold (largest $\lambda$) that satisfies the risk constraint with high confidence.

3. **Hoeffding Correction:** The finite-sample correction accounts for the multiple testing problem when evaluating different thresholds, ensuring valid statistical guarantees.

4. **Model-Agnostic Design:** By working with the output of any base model $\hat{f}$, our approach can be applied post-hoc to existing trained models without retraining.

## Computational Complexity

The algorithm has time complexity $O(|\Lambda| \cdot k \cdot |\mathcal{Y}|)$ where $|\Lambda|$ is the number of candidate thresholds, $k$ is the calibration set size, and $|\mathcal{Y}|$ is the output space size. For continuous outputs, we can discretize the threshold space or use binary search, reducing complexity to $O(\log(1/\epsilon) \cdot k \cdot |\mathcal{Y}|)$ for precision $\epsilon$. The space complexity is $O(k \cdot |\mathcal{Y}|)$ for storing the calibration predictions.
