# Reconstruction: problem_method
**Paper:** 2006.06138  
**Condition:** with_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Problem Formulation

## Notation and Setup

Let $\mathcal{X}$ denote the input space and $\mathcal{Y}$ denote the label space. For set prediction tasks, we consider scenarios where each input $X \in \mathcal{X}$ may be associated with a subset $Y \subseteq \mathcal{Y}$ of labels, objects, or regions. Let $(X_1, Y_1), \ldots, (X_n, Y_n)$ be a sequence of exchangeable random pairs drawn from some unknown distribution $P$ on $\mathcal{X} \times 2^{\mathcal{Y}}$, where $2^{\mathcal{Y}}$ denotes the power set of $\mathcal{Y}$.

Given a base predictor $f: \mathcal{X} \rightarrow 2^{\mathcal{Y}}$ that outputs prediction sets, we define a loss function $\ell: 2^{\mathcal{Y}} \times 2^{\mathcal{Y}} \rightarrow \mathbb{R}_+$ that measures the cost of predicting set $\hat{Y}$ when the true label set is $Y$. The expected loss (risk) of predictor $f$ is:
$$R(f) = \mathbb{E}_{(X,Y) \sim P}[\ell(f(X), Y)]$$

Let $\mathcal{D}_{\text{cal}} = \{(X_1, Y_1), \ldots, (X_m, Y_m)\}$ be a calibration dataset and $\mathcal{D}_{\text{test}} = \{(X_{m+1}, Y_{m+1}), \ldots, (X_{m+k}, Y_{m+k})\}$ be a test dataset, where all $(m+k)$ examples are exchangeable.

## Formal Problem Statement

**Given:** 
- A base predictor $f: \mathcal{X} \rightarrow 2^{\mathcal{Y}}$ (potentially suboptimal)
- A loss function $\ell: 2^{\mathcal{Y}} \times 2^{\mathcal{Y}} \rightarrow \mathbb{R}_+$
- A calibration dataset $\mathcal{D}_{\text{cal}}$ of size $m$
- A desired risk level $\alpha \in (0,1)$

**Find:** A calibrated predictor $\hat{f}: \mathcal{X} \rightarrow 2^{\mathcal{Y}}$ constructed using only $\mathcal{D}_{\text{cal}}$

**Guarantee:** With probability at least $1-\delta$ over the randomness in data splitting, the expected loss on future test data satisfies:
$$\mathbb{E}_{(X,Y) \sim P}[\ell(\hat{f}(X), Y)] \leq \alpha$$

## Objective

The primary objective is to develop a distribution-free, finite-sample method that transforms any base predictor $f$ into a risk-controlled predictor $\hat{f}$ such that:

1. **Finite-sample validity:** The risk guarantee holds for any finite calibration set size $m$, without asymptotic approximations
2. **Distribution-free:** No assumptions on $P$ beyond exchangeability
3. **Model-agnostic:** Works with arbitrary base predictors $f$ and loss functions $\ell$
4. **Computational efficiency:** The calibration procedure scales polynomially in $m$ and $|\mathcal{Y}|$

## Technical Assumptions

**A1. Exchangeability:** The sequence $(X_1, Y_1), \ldots, (X_{m+k}, Y_1)$ is exchangeable under the joint distribution $P^{m+k}$.

**A2. Measurability:** The loss function $\ell$ is measurable, and the base predictor $f$ produces measurable sets.

**A3. Bounded loss:** There exists $L < \infty$ such that $\ell(\hat{Y}, Y) \leq L$ for all $\hat{Y}, Y \subseteq \mathcal{Y}$.

**A4. Calibration-test split:** The calibration and test sets are formed by a random split of the available data, maintaining exchangeability.

The exchangeability assumption (A1) is weaker than the i.i.d. assumption commonly used in machine learning, allowing for certain forms of dependence and distribution shift as studied in conformal prediction literature. This connects our formulation to the work of Tibshirani et al., who showed that exchangeability suffices for valid conformal inference even under covariate shift.

## Connection to Prior Work

Our formulation extends the conformal prediction framework beyond coverage guarantees to general risk control. While standard conformal prediction focuses on controlling the probability of miscoverage (i.e., $\mathbb{P}(Y \not\in \hat{C}(X)) \leq \alpha$), our approach targets the expected value of arbitrary loss functions. This generalization is crucial for set prediction tasks where different types of errors have different costs, such as false positives versus false negatives in multi-label classification, or missing small versus large objects in detection.

# Methodology

## High-Level Approach

Our approach, termed **Risk Controlling Prediction Sets (RCPS)**, adapts the conformal prediction principle to control expected loss rather than miscoverage probability. The key insight is to construct a randomized prediction set that interpolates between different deterministic prediction sets based on empirical risk estimates on the calibration data.

The method proceeds in two phases: (1) **Calibration phase:** Use the calibration set to estimate a risk-controlling threshold, and (2) **Prediction phase:** Apply this threshold to construct prediction sets that satisfy the desired risk constraint.

## Core Algorithm

Let $\mathcal{F} = \{f_\lambda : \lambda \in \Lambda\}$ be a family of prediction functions parameterized by $\lambda$, where each $f_\lambda(x)$ outputs a subset of $\mathcal{Y}$. For concreteness, consider the family of threshold-based predictors:
$$f_\lambda(x) = \{y \in \mathcal{Y} : s(x, y) \geq \lambda\}$$
where $s: \mathcal{X} \times \mathcal{Y} \rightarrow \mathbb{R}$ is a conformity score function derived from the base predictor.

**Algorithm 1: Risk Controlling Prediction Sets (RCPS)**

```
Input: Calibration data D_cal = {(X_i, Y_i)}_{i=1}^m, loss function ℓ, 
       score function s, risk level α
Output: Calibrated predictor f̂

1. Compute calibration scores:
   For i = 1, ..., m:
     For each λ ∈ Λ:
       Compute prediction f_λ(X_i) = {y : s(X_i, y) ≥ λ}
       Compute loss L_i(λ) = ℓ(f_λ(X_i), Y_i)

2. Estimate empirical risk for each λ:
   R̂(λ) = (1/m) * Σ_{i=1}^m L_i(λ)

3. Find risk-controlling threshold:
   λ̂ = inf{λ ∈ Λ : R̂(λ) ≤ α}

4. Handle randomization for exact risk control:
   If R̂(λ̂) < α:
     Find λ_next = sup{λ > λ̂ : R̂(λ) > α}
     Set q = (α - R̂(λ̂)) / (R̂(λ_next) - R̂(λ̂))
   Else:
     Set q = 0

5. Define calibrated predictor:
   f̂(x) = {
     f_λ̂(x)           with probability 1-q
     f_λ_next(x)       with probability q
   }
```

## Theoretical Foundation

The validity of RCPS relies on the following key theorem:

**Theorem 1 (Risk Control Guarantee):** Under assumptions A1-A4, for any $\delta \in (0,1)$, with probability at least $1-\delta$ over the random split of data:
$$\mathbb{E}[\ell(\hat{f}(X), Y)] \leq \alpha + O\left(\sqrt{\frac{\log(1/\delta)}{m}}\right)$$

The proof leverages concentration inequalities for exchangeable sequences and the uniform convergence of empirical risk estimates across the function class $\mathcal{F}$.

## Design Justifications

**Choice of Function Family:** The threshold-based family $\{f_\lambda\}$ provides a natural ordering of prediction sets by inclusion, enabling efficient search over the risk-accuracy tradeoff. This connects to the nested structure used in conformal prediction.

**Randomization Mechanism:** The randomized interpolation between $f_{\lambdâ}$ and $f_{\lambda_\text{next}}$ ensures exact risk control rather than conservative bounds, following the approach of Vovk et al. in conformal prediction.

**Empirical Risk Estimation:** Using the empirical average $\hat{R}(\lambda) = \frac{1}{m}\sum_{i=1}^m L_i(\lambda)$ provides unbiased estimates under exchangeability, generalizing the approach of Tibshirani et al. for weighted conformal scores.

## Extensions for Distribution Shift

When calibration and test data may come from different distributions, we can incorporate importance weights following the covariate shift framework:

```
Modified Step 2: Weighted empirical risk
R̂_w(λ) = (Σ_{i=1}^m w_i * L_i(λ)) / (Σ_{i=1}^m w_i)
```

where $w_i = \frac{p_\text{test}(X_i)}{p_\text{cal}(X_i)}$ are importance weights estimated from the marginal distributions.

## Computational Complexity

The algorithm requires:
- **Time complexity:** $O(m \cdot |\Lambda| \cdot T_\ell)$ where $T_\ell$ is the cost of evaluating the loss function
- **Space complexity:** $O(m \cdot |\Lambda|)$ to store calibration losses

For continuous parameter spaces $\Lambda$, efficient search strategies (e.g., binary search when risk is monotonic in $\lambda$) can reduce the complexity to $O(m \cdot \log|\Lambda| \cdot T_\ell)$.

The method requires no model retraining and can be applied as a post-processing step to any base predictor, making it computationally practical for large-scale applications.
