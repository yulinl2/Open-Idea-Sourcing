# Reconstruction: problem_method
**Paper:** 2006.06138  
**Condition:** no_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Problem Formulation

## Notation and Setup

Let $\mathcal{X}$ denote the input space and $\mathcal{Y}$ denote the output space. We consider prediction problems where the output is a set, so we work with the power set $\mathcal{P}(\mathcal{Y})$ as our prediction space. Let $(X_1, Y_1), \ldots, (X_n, Y_n)$ be exchangeable random pairs drawn from some unknown distribution $P$ on $\mathcal{X} \times \mathcal{P}(\mathcal{Y})$.

We assume access to a pre-trained model $f: \mathcal{X} \to \mathbb{R}^{|\mathcal{Y}|}$ that produces scores for each possible output element. Let $\ell: \mathcal{P}(\mathcal{Y}) \times \mathcal{P}(\mathcal{Y}) \to \mathbb{R}_+$ be a loss function that measures the cost of predicting set $\hat{Y}$ when the true set is $Y$. Common examples include:
- **Hamming loss**: $\ell(\hat{Y}, Y) = |\hat{Y} \triangle Y|$ (symmetric difference)
- **Precision-recall based losses**: $\ell(\hat{Y}, Y) = 1 - \frac{2|\hat{Y} \cap Y|}{|\hat{Y}| + |Y|}$ (F1 loss)
- **Coverage loss**: $\ell(\hat{Y}, Y) = \mathbf{1}[Y \not\subseteq \hat{Y}]$ (indicator of incomplete coverage)

We partition our data into a calibration set $\{(X_i, Y_i)\}_{i=1}^m$ and a test set $\{(X_j, Y_j)\}_{j=m+1}^n$. Let $\mathcal{C}: \mathcal{X} \times \mathbb{R} \to \mathcal{P}(\mathcal{Y})$ denote a set-valued predictor parameterized by a threshold $\tau \in \mathbb{R}$, where typically $\mathcal{C}(x, \tau) = \{y \in \mathcal{Y} : f(x)_y \geq \tau\}$.

## Formal Problem Statement

**Given:**
- A pre-trained scoring model $f: \mathcal{X} \to \mathbb{R}^{|\mathcal{Y}|}$
- A loss function $\ell: \mathcal{P}(\mathcal{Y}) \times \mathcal{P}(\mathcal{Y}) \to \mathbb{R}_+$
- A calibration dataset $\{(X_i, Y_i)\}_{i=1}^m$ of exchangeable samples
- A desired risk level $\alpha \in (0, 1)$

**Find:** A threshold $\hat{\tau}$ such that the resulting predictor $\mathcal{C}(\cdot, \hat{\tau})$ satisfies the risk control guarantee.

**Guarantee:** With probability at least $1-\delta$ over the randomness in data splitting, the expected loss on future test data satisfies:
$$\mathbb{E}_{(X,Y) \sim P}[\ell(\mathcal{C}(X, \hat{\tau}), Y)] \leq \alpha$$

## Technical Assumptions

**Assumption 1 (Exchangeability):** The sequence $(X_1, Y_1), (X_2, Y_2), \ldots$ is exchangeable under the data distribution $P$. This is weaker than the i.i.d. assumption and allows for certain types of dependence and distribution shift.

**Assumption 2 (Monotonicity):** The set predictor $\mathcal{C}(x, \tau)$ is monotone decreasing in $\tau$ for each fixed $x$. That is, if $\tau_1 \leq \tau_2$, then $\mathcal{C}(x, \tau_2) \subseteq \mathcal{C}(x, \tau_1)$.

**Assumption 3 (Loss Monotonicity):** The loss function satisfies a weak monotonicity property: for nested sets $A \subseteq B$, we have either $\ell(A, Y) \geq \ell(B, Y)$ for all $Y$ (precision-favoring) or $\ell(A, Y) \leq \ell(B, Y)$ for all $Y$ (recall-favoring).

These assumptions are minimal and realistic: exchangeability is standard in conformal prediction, monotonicity naturally holds for threshold-based predictors, and loss monotonicity captures the intuitive trade-off between precision and recall in set prediction.

## Connection to Prior Work

This formulation extends classical risk control from single predictions to set-valued predictions. Unlike standard conformal prediction which controls coverage probability, we directly control expected loss. The exchangeability assumption connects to the conformal prediction literature while being more general than i.i.d. assumptions in classical PAC learning. The monotonicity assumptions enable efficient algorithms based on threshold selection, similar to approaches in multi-label learning and object detection post-processing.

# Methodology

## High-Level Approach

Our approach, **Risk Controlling Prediction Sets (RCPS)**, adapts the Learn Then Test (LTT) framework to set prediction. The key insight is to use the calibration data to learn a threshold that controls risk, then apply this threshold to future test instances. We leverage the exchangeability of the data to provide finite-sample guarantees through a concentration inequality.

## Core Algorithm

The RCPS algorithm consists of two phases:

### Phase 1: Threshold Learning
Given calibration data and risk level $\alpha$, we solve:
$$\hat{\tau} = \arg\min_{\tau} \left\{ \frac{1}{m} \sum_{i=1}^m \ell(\mathcal{C}(X_i, \tau), Y_i) \leq \alpha - \lambda_m(\delta) \right\}$$

where $\lambda_m(\delta) = \sqrt{\frac{\log(2/\delta)}{2m}}$ is the concentration radius from Hoeffding's inequality.

### Phase 2: Prediction
For a new test instance $X$, output the prediction set $\mathcal{C}(X, \hat{\tau})$.

## Detailed Algorithm

```
Algorithm: Risk Controlling Prediction Sets (RCPS)

Input: 
  - Scoring model f: X → R^|Y|
  - Loss function ℓ: P(Y) × P(Y) → R₊
  - Calibration data {(Xᵢ, Yᵢ)}ᵢ₌₁ᵐ
  - Risk level α ∈ (0,1)
  - Confidence level δ ∈ (0,1)

Step 1: Compute concentration radius
  λₘ(δ) ← √(log(2/δ) / (2m))

Step 2: Generate candidate thresholds
  Τ ← {f(Xᵢ)ⱼ : i ∈ [m], j ∈ [|Y|]} ∪ {-∞, +∞}
  Sort Τ in ascending order

Step 3: Find optimal threshold
  for τ ∈ Τ do:
    R̂ₘ(τ) ← (1/m) ∑ᵢ₌₁ᵐ ℓ(C(Xᵢ, τ), Yᵢ)
    if R̂ₘ(τ) ≤ α - λₘ(δ) then:
      τ̂ ← τ
      break

Step 4: Return threshold
  return τ̂

Prediction: For new input X, return C(X, τ̂)
```

## Theoretical Properties

**Theorem 1 (Risk Control Guarantee):** Under Assumptions 1-3, with probability at least $1-\delta$ over the calibration data, the RCPS predictor satisfies:
$$\mathbb{E}_{(X,Y) \sim P}[\ell(\mathcal{C}(X, \hat{\tau}), Y)] \leq \alpha$$

**Proof Sketch:** By exchangeability and Hoeffding's inequality, with probability $1-\delta$:
$$\left|\mathbb{E}[\ell(\mathcal{C}(X, \hat{\tau}), Y)] - \frac{1}{m}\sum_{i=1}^m \ell(\mathcal{C}(X_i, \hat{\tau}), Y_i)\right| \leq \lambda_m(\delta)$$

Since $\hat{\tau}$ is chosen such that the empirical risk plus $\lambda_m(\delta)$ is at most $\alpha$, the result follows.

**Theorem 2 (Consistency):** As $m \to \infty$, $\hat{\tau}$ converges to the population-optimal threshold $\tau^* = \inf\{\tau : \mathbb{E}[\ell(\mathcal{C}(X, \tau), Y)] \leq \alpha\}$.

## Design Justifications

**Threshold-based approach:** We parameterize predictors by thresholds because this naturally induces the monotonicity required for our theoretical analysis while being computationally efficient. This design is inspired by score-based methods in information retrieval and object detection.

**Finite candidate set:** Rather than optimizing over all possible thresholds, we restrict to the finite set of observed scores. This makes the algorithm tractable while preserving optimality due to the discrete nature of the problem.

**Hoeffding concentration:** We use Hoeffding's inequality rather than more sophisticated concentration bounds because it requires no distributional assumptions beyond exchangeability and provides explicit finite-sample guarantees.

## Computational Complexity

The algorithm has time complexity $O(m|\mathcal{Y}| \log(m|\mathcal{Y}|) + m|\mathcal{Y}|^2)$ where the first term comes from sorting candidate thresholds and the second from evaluating losses. The space complexity is $O(m|\mathcal{Y}|)$. For large label spaces, we can use approximation techniques such as sampling a subset of candidate thresholds or using efficient loss computation methods specific to the loss function structure.

The algorithm requires no model retraining and can be applied as a post-processing step to any pre-trained scoring model, making it highly practical for real-world deployment.
