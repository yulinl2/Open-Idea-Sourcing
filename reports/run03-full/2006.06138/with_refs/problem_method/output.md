# Reconstruction: problem_method
**Paper:** 2006.06138  
**Condition:** with_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Problem Formulation

## Notation and Setup

Let $\mathcal{X}$ denote the input space and $\mathcal{Y}$ denote the output space. We consider a setting where each instance $x \in \mathcal{X}$ may be associated with multiple valid outputs, requiring prediction sets rather than single predictions. Let $\mathcal{P}(\mathcal{Y})$ denote the power set of $\mathcal{Y}$, representing all possible subsets of outputs.

We assume access to:
- A pre-trained model $f: \mathcal{X} \to \mathbb{R}^{|\mathcal{Y}|}$ that produces scores for each possible output
- A calibration dataset $\mathcal{D}_{\text{cal}} = \{(X_i, Y_i)\}_{i=1}^n$ where $(X_i, Y_i) \sim P_{XY}$
- A loss function $\ell: \mathcal{P}(\mathcal{Y}) \times \mathcal{Y} \to \mathbb{R}_+$ that measures the quality of prediction sets

The loss function $\ell(\hat{Y}, Y)$ evaluates how well a prediction set $\hat{Y} \subseteq \mathcal{Y}$ covers the true output $Y$. Common examples include:
- **Coverage loss**: $\ell(\hat{Y}, Y) = \mathbb{I}[Y \notin \hat{Y}]$ (indicator of miscoverage)
- **Set size loss**: $\ell(\hat{Y}, Y) = |\hat{Y}|$ (penalizes large prediction sets)
- **Composite loss**: $\ell(\hat{Y}, Y) = \mathbb{I}[Y \notin \hat{Y}] + \lambda|\hat{Y}|$ (trades off coverage and efficiency)

## Problem Statement

**Given**: 
- A pre-trained model $f$
- A calibration dataset $\mathcal{D}_{\text{cal}}$
- A user-specified loss function $\ell$ and target risk level $\alpha \in (0,1)$

**Find**: A prediction rule $\mathcal{C}: \mathcal{X} \to \mathcal{P}(\mathcal{Y})$ that maps inputs to prediction sets

**Guarantee**: For a new test point $(X_{\text{test}}, Y_{\text{test}}) \sim P_{XY}$, we require:
$$\mathbb{E}[\ell(\mathcal{C}(X_{\text{test}}), Y_{\text{test}})] \leq \alpha$$

This expectation is taken over the joint distribution of test data and the randomness in the calibration procedure.

## Objective and Constraints

The core objective is to construct prediction sets with **finite-sample expected loss control**. Unlike asymptotic guarantees, we require that the bound holds for any finite calibration sample size $n$, without assuming the calibration and test data are identically distributed.

Formally, we seek to solve:
$$\min_{\mathcal{C}} \mathbb{E}[|\mathcal{C}(X_{\text{test}})|] \quad \text{subject to} \quad \mathbb{E}[\ell(\mathcal{C}(X_{\text{test}}), Y_{\text{test}})] \leq \alpha$$

This optimization balances prediction set efficiency (small sets) with loss control (satisfying the user's risk tolerance).

## Technical Assumptions

We make the following minimal assumptions:

**A1 (Exchangeability)**: The calibration data $(X_1, Y_1), \ldots, (X_n, Y_n), (X_{\text{test}}, Y_{\text{test}})$ are exchangeable under the joint distribution.

**A2 (Loss boundedness)**: The loss function satisfies $0 \leq \ell(\hat{Y}, Y) \leq M$ for some finite constant $M$.

**A3 (Model accessibility)**: We can evaluate the pre-trained model $f(x)$ for any input $x$, but cannot modify its parameters.

Assumption A1 is weaker than the i.i.d. assumption and allows for certain forms of dependence between calibration and test data. When covariate shift is present, we will extend this using importance weighting as suggested by the conformal prediction literature under distribution shift.

## Connection to Prior Work

This formulation extends conformal prediction beyond the standard coverage guarantee $\mathbb{P}[Y_{\text{test}} \in \mathcal{C}(X_{\text{test}})] \geq 1-\alpha$ to arbitrary loss functions. While classical conformal prediction focuses solely on marginal coverage, our framework accommodates the broader class of losses relevant to set-valued prediction problems.

The exchangeability assumption connects to the foundational work on conformal prediction, while our extension to general loss functions addresses the limitation that coverage alone may not capture the full cost of prediction errors in applications like multi-label classification or object detection.

# Methodology

## High-Level Approach

Our approach, **Risk-Controlling Prediction Sets (RCPS)**, extends the conformal prediction framework to provide expected loss control for arbitrary loss functions. The key insight is to use the calibration data to learn a threshold that ensures the expected loss constraint is satisfied in finite samples.

The method operates in two phases:
1. **Calibration phase**: Use the calibration data to learn a threshold parameter that controls expected loss
2. **Prediction phase**: For new inputs, construct prediction sets using the learned threshold

## Core Algorithm

### Conformity Scores

For each calibration example $(X_i, Y_i)$, we define a **conformity score** $S_i$ that measures how well the true output $Y_i$ aligns with the model's predictions. A natural choice is:
$$S_i = f(X_i)_{Y_i}$$
where $f(X_i)_{Y_i}$ denotes the model's score for the true label $Y_i$.

For a test input $X_{\text{test}}$, we construct prediction sets of the form:
$$\mathcal{C}_\tau(X_{\text{test}}) = \{y \in \mathcal{Y} : f(X_{\text{test}})_y \geq \tau\}$$
where $\tau$ is a threshold parameter to be calibrated.

### Risk-Controlling Calibration

The core innovation is to choose the threshold $\tau$ to control expected loss rather than just coverage. Define the **loss-augmented conformity scores**:
$$R_i(\tau) = \ell(\mathcal{C}_\tau(X_i), Y_i)$$

These represent the loss incurred when applying threshold $\tau$ to calibration example $i$.

**Algorithm: Risk-Controlling Prediction Sets**

```
Input: Calibration data {(X_i, Y_i)}_{i=1}^n, model f, loss ℓ, target level α

1. For each calibration example i = 1, ..., n:
   - Compute conformity score S_i = f(X_i)_{Y_i}
   
2. Define candidate thresholds T = {S_1, S_2, ..., S_n, -∞}

3. For each threshold τ ∈ T:
   - Compute empirical risk: R̂(τ) = (1/n) Σ_{i=1}^n ℓ(C_τ(X_i), Y_i)
   
4. Select threshold: τ̂ = max{τ ∈ T : R̂(τ) ≤ α}

5. For test input X_test:
   - Return prediction set C_{τ̂}(X_test) = {y ∈ Y : f(X_test)_y ≥ τ̂}
```

### Theoretical Properties

**Theorem 1 (Finite-Sample Risk Control)**: Under assumptions A1-A3, the RCPS algorithm satisfies:
$$\mathbb{E}[\ell(\mathcal{C}_{\hat{\tau}}(X_{\text{test}}), Y_{\text{test}})] \leq \alpha + \frac{M}{n+1}$$

The proof relies on the exchangeability of the augmented sequence $(X_1, Y_1), \ldots, (X_n, Y_n), (X_{\text{test}}, Y_{\text{test}})$ and properties of the empirical risk minimization over the finite threshold set.

**Theorem 2 (Asymptotic Optimality)**: As $n \to \infty$, if the threshold set is sufficiently rich, the RCPS threshold converges to the population risk minimizer:
$$\hat{\tau} \to \arg\min_\tau \mathbb{E}[\ell(\mathcal{C}_\tau(X), Y)]$$

### Extension to Covariate Shift

When the test distribution differs from the calibration distribution, we incorporate importance weights following the weighted conformal prediction framework. Let $w(x) = \frac{dP_{\text{test}}(x)}{dP_{\text{cal}}(x)}$ denote the likelihood ratio.

The weighted empirical risk becomes:
$$\hat{R}_w(\tau) = \frac{\sum_{i=1}^n w(X_i) \ell(\mathcal{C}_\tau(X_i), Y_i)}{\sum_{i=1}^n w(X_i)}$$

The threshold selection rule is modified to use $\hat{R}_w(\tau) \leq \alpha$.

## Design Justifications

**Choice of threshold set**: We restrict to the finite set of observed conformity scores to ensure computational tractability while maintaining theoretical guarantees. This discretization is crucial for the finite-sample analysis.

**Empirical risk minimization**: Using the empirical average directly connects to concentration inequalities and enables finite-sample bounds without distributional assumptions beyond exchangeability.

**Conformity score design**: The choice $S_i = f(X_i)_{Y_i}$ leverages the pre-trained model's confidence while remaining model-agnostic in the sense that we don't modify the underlying predictor.

## Computational Complexity

The algorithm has time complexity $O(n^2 |\mathcal{Y}|)$ in the worst case:
- Computing conformity scores: $O(n|\mathcal{Y}|)$
- Evaluating empirical risk for each threshold: $O(n|\mathcal{Y}|)$ per threshold
- Total: $O(n \cdot n|\mathcal{Y}|) = O(n^2|\mathcal{Y}|)$

For large output spaces, this can be optimized using efficient data structures or approximation schemes, making the method practically viable for real-world applications.
