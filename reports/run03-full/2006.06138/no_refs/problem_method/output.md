# Reconstruction: problem_method
**Paper:** 2006.06138  
**Condition:** no_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Problem Formulation

## Setup and Notation

Let $\mathcal{X}$ denote the input space and $\mathcal{Y}$ denote the output space. We consider a setting where each input $x \in \mathcal{X}$ is associated with a ground truth set $Y \subseteq \mathcal{Y}$, and we wish to predict a set $\hat{Y} \subseteq \mathcal{Y}$. Let $(X, Y) \sim P$ be the unknown data distribution, where $X$ is the input and $Y$ is the true output set.

We assume access to:
- A pre-trained model $f: \mathcal{X} \rightarrow \mathbb{R}^{|\mathcal{Y}|}$ that outputs scores for each possible output element
- A calibration dataset $\mathcal{D}_{\text{cal}} = \{(x_i, Y_i)\}_{i=1}^n$ drawn i.i.d. from $P$
- A test point $x_{\text{test}}$ with unknown true set $Y_{\text{test}}$

Let $\ell: 2^{\mathcal{Y}} \times 2^{\mathcal{Y}} \rightarrow \mathbb{R}_+$ be a user-specified loss function that measures the discrepancy between a predicted set $\hat{Y}$ and the true set $Y$. Common examples include:
- **Set-based F1 loss**: $\ell(\hat{Y}, Y) = 1 - \frac{2|\hat{Y} \cap Y|}{|\hat{Y}| + |Y|}$
- **Jaccard loss**: $\ell(\hat{Y}, Y) = 1 - \frac{|\hat{Y} \cap Y|}{|\hat{Y} \cup Y|}$
- **Hamming loss**: $\ell(\hat{Y}, Y) = |\hat{Y} \triangle Y|$ (symmetric difference)

## Problem Statement

**Given**: A pre-trained model $f$, a loss function $\ell$, a calibration dataset $\mathcal{D}_{\text{cal}}$, and a target risk level $\alpha \in (0, 1)$.

**Find**: A prediction set construction method $\mathcal{C}: \mathcal{X} \times \mathcal{D}_{\text{cal}} \rightarrow 2^{\mathcal{Y}}$ that maps test inputs to prediction sets.

**Guarantee**: The method must satisfy the finite-sample risk control property:
$$\mathbb{E}[\ell(\mathcal{C}(X_{\text{test}}, \mathcal{D}_{\text{cal}}), Y_{\text{test}})] \leq \alpha$$
where the expectation is taken over the joint distribution of $(X_{\text{test}}, Y_{\text{test}}) \sim P$ and the randomness in the calibration dataset $\mathcal{D}_{\text{cal}}$.

## Technical Assumptions

1. **Exchangeability**: The calibration data $\mathcal{D}_{\text{cal}}$ and test point $(X_{\text{test}}, Y_{\text{test}})$ are exchangeable under $P$. This is weaker than the i.i.d. assumption and allows for certain forms of distribution shift.

2. **Finite output space**: We assume $|\mathcal{Y}| < \infty$ for computational tractability, though extensions to infinite spaces are possible under additional structure.

3. **Loss boundedness**: The loss function satisfies $\ell(\hat{Y}, Y) \in [0, L]$ for some finite constant $L$ and all sets $\hat{Y}, Y \subseteq \mathcal{Y}$.

4. **Model accessibility**: We can evaluate the pre-trained model $f$ but do not require access to its training procedure or the ability to retrain it.

These assumptions are minimal and realistic for practical applications. The exchangeability assumption, in particular, is much weaker than requiring identical distributions between calibration and test data, allowing for covariate shift and other common forms of distribution mismatch.

# Methodology

## High-Level Approach

Our approach, which we call **Risk Controlling Prediction Sets (RCPS)**, builds upon the principle of conformal prediction but extends it to control arbitrary loss functions rather than just coverage. The key insight is to use the calibration data to learn a threshold that, when applied to the model's output scores, produces prediction sets with controlled expected loss.

The method proceeds in two phases:
1. **Calibration phase**: Use the calibration data to learn a score threshold that controls the empirical risk
2. **Prediction phase**: Apply this threshold to construct prediction sets for new test inputs

## Core Algorithm

Let $s: \mathcal{X} \times 2^{\mathcal{Y}} \rightarrow \mathbb{R}$ be a conformity score function that measures how "conforming" a predicted set is given the model's outputs. We define:

$$s(x, \hat{Y}) = -\sum_{y \in \hat{Y}} f(x)_y + \lambda |\hat{Y}|$$

where $f(x)_y$ is the model's score for element $y$ and $\lambda \geq 0$ is a regularization parameter that penalizes large sets.

For each calibration example $(x_i, Y_i)$, we compute the loss-weighted conformity score:
$$V_i = \ell(\hat{Y}_i^*, Y_i) + \beta \cdot s(x_i, \hat{Y}_i^*)$$

where $\hat{Y}_i^* = \arg\min_{\hat{Y}} s(x_i, \hat{Y})$ and $\beta > 0$ is a coupling parameter.

**Algorithm 1: Risk Controlling Prediction Sets**

```
Input: Model f, loss function ℓ, calibration data D_cal, risk level α
Output: Prediction set constructor C

1. // Calibration phase
2. For i = 1 to n:
3.     Compute optimal set: Ŷ_i* = argmin_{Ŷ⊆Y} s(x_i, Ŷ)
4.     Compute score: V_i = ℓ(Ŷ_i*, Y_i) + β · s(x_i, Ŷ_i*)
5. 
6. // Find threshold using empirical risk minimization
7. Sort V_1, ..., V_n in ascending order: V_(1) ≤ ... ≤ V_(n)
8. Find τ = V_(⌈(1-α)(n+1)⌉)
9. 
10. // Prediction phase
11. Function C(x_test):
12.     Return Ŷ = {Ŷ ⊆ Y : ℓ(Ŷ, Y) + β · s(x_test, Ŷ) ≤ τ}
13.     (In practice, solve: argmin_{Ŷ} s(x_test, Ŷ) subject to score ≤ τ)
```

## Key Design Decisions

**Choice of conformity score**: The conformity score $s(x, \hat{Y})$ balances model confidence (sum of scores for included elements) with set size. The regularization term $\lambda |\hat{Y}|$ prevents trivially large sets, while the negative sum encourages including high-scoring elements.

**Loss-weighted scoring**: By incorporating the loss $\ell(\hat{Y}_i^*, Y_i)$ directly into the conformity score $V_i$, we ensure that the threshold selection process accounts for the actual loss function rather than just coverage.

**Quantile-based threshold**: The threshold $\tau$ is chosen as the $\lceil(1-\alpha)(n+1)\rceil$-th order statistic of the calibration scores, following the conformal prediction framework but adapted for loss control.

## Theoretical Properties

**Theorem 1** (Finite-sample risk control): Under the exchangeability assumption, the RCPS method satisfies:
$$\mathbb{E}[\ell(\mathcal{C}(X_{\text{test}}, \mathcal{D}_{\text{cal}}), Y_{\text{test}})] \leq \alpha + \frac{L}{n+1}$$

where $L$ is the upper bound on the loss function.

**Proof sketch**: The result follows from the exchangeability of calibration and test data, which ensures that the rank of the test score among calibration scores is uniformly distributed. The additional $\frac{L}{n+1}$ term accounts for the finite-sample approximation error.

**Theorem 2** (Consistency): As $n \rightarrow \infty$, the empirical risk converges to the target level: $\mathbb{E}[\ell(\mathcal{C}(X_{\text{test}}, \mathcal{D}_{\text{cal}}), Y_{\text{test}})] \rightarrow \alpha$.

## Computational Complexity

The calibration phase requires solving $n$ optimization problems of the form $\arg\min_{\hat{Y}} s(x_i, \hat{Y})$. For finite output spaces with $|\mathcal{Y}| = m$, this can be solved exactly in $O(2^m)$ time via enumeration, or approximately in $O(m \log m)$ time using greedy selection based on score ratios.

The prediction phase requires solving a single constrained optimization problem, with the same complexity as the calibration subproblems. For large output spaces, we can use beam search or other approximate methods while maintaining the theoretical guarantees in expectation.

The overall computational complexity is $O(n \cdot m \log m)$ for the approximate greedy approach, making the method practical for moderately-sized output spaces and calibration sets.
