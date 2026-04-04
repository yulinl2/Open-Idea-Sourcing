# Reconstruction: problem
**Paper:** 2006.06138  
**Condition:** with_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Problem Formulation

## Notation and Setup

Let $\mathcal{X}$ denote the input space and $\mathcal{Y}$ denote the output space. For set prediction tasks, we consider prediction sets $\hat{S} \subseteq \mathcal{Y}$ rather than point predictions. Let $(X_1, Y_1), \ldots, (X_n, Y_n)$ be a sequence of data points where $X_i \in \mathcal{X}$ and $Y_i \in \mathcal{Y}$. We assume these points are exchangeable, meaning their joint distribution is invariant to permutations.

Let $f: \mathcal{X} \to 2^{\mathcal{Y}}$ be a set-valued predictor that maps inputs to prediction sets, where $2^{\mathcal{Y}}$ denotes the power set of $\mathcal{Y}$. Given a loss function $\ell: 2^{\mathcal{Y}} \times \mathcal{Y} \to \mathbb{R}_+$ that measures the cost of predicting set $\hat{S}$ when the true label is $y$, we define the risk of predictor $f$ as:
$$R(f) = \mathbb{E}[\ell(f(X), Y)]$$
where the expectation is taken over the joint distribution of $(X, Y)$.

For a user-specified risk tolerance $\alpha \in (0, 1)$, we seek to construct a predictor $\hat{f}$ such that $R(\hat{f}) \leq \alpha$ with high probability. We assume access to a calibration set $\{(X_1, Y_1), \ldots, (X_m, Y_m)\}$ that is exchangeable with future test points, but we do not assume independence or identical distribution.

## Problem Statement

**Given:**
- A base model $g: \mathcal{X} \to \mathbb{R}^{|\mathcal{Y}|}$ (or any representation of uncertainty over $\mathcal{Y}$)
- A calibration dataset $\mathcal{D}_{\text{cal}} = \{(X_i, Y_i)\}_{i=1}^m$ exchangeable with test data
- A loss function $\ell: 2^{\mathcal{Y}} \times \mathcal{Y} \to \mathbb{R}_+$
- A risk tolerance level $\alpha \in (0, 1)$

**Find:** A set-valued predictor $\hat{f}: \mathcal{X} \to 2^{\mathcal{Y}}$ such that for a new test point $(X_{m+1}, Y_{m+1})$ exchangeable with the calibration data:
$$\mathbb{P}[R(\hat{f}) \leq \alpha] \geq 1 - \delta$$
for some confidence level $\delta \in (0, 1)$, where the probability is over the randomness in the calibration set and the construction procedure.

## Objective and Constraints

The primary objective is to construct prediction sets that satisfy the risk constraint while being as informative as possible. Formally, we seek:

$$\min_{\hat{f}} \mathbb{E}[|\hat{f}(X)|] \quad \text{subject to} \quad \mathbb{P}[R(\hat{f}) \leq \alpha] \geq 1 - \delta$$

where $|\hat{f}(X)|$ denotes the size of the prediction set. This captures the trade-off between informativeness (smaller sets) and risk control.

The construction must be:
1. **Model-agnostic**: Work with any base model $g$ without requiring retraining
2. **Computationally efficient**: Scale to practical problem sizes
3. **Distribution-free**: Require no assumptions beyond exchangeability

## Technical Assumptions

**A1. Exchangeability:** The sequence $(X_1, Y_1), \ldots, (X_m, Y_m), (X_{m+1}, Y_{m+1})$ is exchangeable. This is weaker than the i.i.d. assumption and allows for certain types of distribution shift.

**A2. Measurability:** The loss function $\ell$ is measurable, and the prediction sets $\hat{f}(x)$ are measurable subsets of $\mathcal{Y}$.

**A3. Bounded Loss:** Without loss of generality, assume $\ell(\hat{S}, y) \in [0, 1]$ for all $\hat{S} \subseteq \mathcal{Y}$ and $y \in \mathcal{Y}$. This can be achieved by normalization.

**A4. Finite Calibration Set:** We have access to a finite calibration set of size $m$, where $m$ is large enough to provide meaningful statistical guarantees.

The exchangeability assumption (A1) is particularly important as it allows our method to handle realistic scenarios where the test distribution may differ from the training distribution, extending beyond the standard i.i.d. setting assumed by most existing approaches.

## Relationship to Prior Work

Classical conformal prediction \citep{vovk2005algorithmic} provides distribution-free coverage guarantees but focuses on marginal coverage rather than expected loss control. Recent extensions \citep{tibshirani2019conformal} handle covariate shift through weighted conformal scores, but still target coverage rather than risk.

Risk-controlling prediction sets have been studied in specific contexts \citep{angelopoulos2021uncertainty}, but existing methods either: (1) require strong distributional assumptions, (2) work only for specific loss functions or model classes, (3) lack finite-sample guarantees, or (4) are computationally intractable for large-scale problems.

Our formulation addresses these limitations by seeking a unified framework that provides finite-sample risk control guarantees under minimal assumptions, applicable to arbitrary models and loss functions. The key innovation lies in extending the conformal prediction paradigm from coverage control to general risk control while maintaining computational tractability and distribution-free validity.
