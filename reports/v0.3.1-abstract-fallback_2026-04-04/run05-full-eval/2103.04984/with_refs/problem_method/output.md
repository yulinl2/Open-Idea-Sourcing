# Reconstruction: problem_method
**Paper:** 2103.04984  
**Condition:** with_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Section 1: Problem Formulation

## 1.1 Notation and Setup

Let $(\mathcal{X}, \mathcal{Y}, \mathcal{T})$ denote the covariate, outcome, and treatment spaces, respectively, where $\mathcal{T} = \{0,1\}$ for binary treatments. For any unit $i$, let $X_i \in \mathcal{X}$ represent observed covariates, $T_i \in \mathcal{T}$ the treatment assignment, and $Y_i \in \mathcal{Y}$ the observed outcome. Under the potential outcomes framework, each unit has two potential outcomes: $Y_i(1)$ (outcome under treatment) and $Y_i(0)$ (outcome under control). The fundamental problem of causal inference is that only one potential outcome is observed: $Y_i = T_i Y_i(1) + (1-T_i)Y_i(0)$.

The individual treatment effect (ITE) for unit $i$ is defined as:
$$\tau_i = Y_i(1) - Y_i(0)$$

The conditional average treatment effect (CATE) function is:
$$\tau(x) = \mathbb{E}[Y(1) - Y(0) | X = x]$$

Let $\{(X_i, T_i, Y_i)\}_{i=1}^n$ denote the training sample drawn from distribution $P$, and let $\{(X_j, T_j, Y_j)\}_{j=1}^m$ denote test units drawn from distribution $Q$, where potentially $P \neq Q$ due to covariate shift. The propensity score is $e(x) = P(T=1|X=x)$.

## 1.2 Formal Problem Statement

**Given**: 
- Training data $\{(X_i, T_i, Y_i)\}_{i=1}^n$ from distribution $P$
- Test covariates $\{X_j\}_{j=1}^m$ from distribution $Q$ (potentially different from $P$)
- Significance level $\alpha \in (0,1)$
- Inferential target: either within-study counterfactual inference or out-of-study generalization

**Find**: For each test unit $j$, construct prediction intervals $C_j = [L_j, U_j]$ for the unobserved potential outcome, where:
- For within-study inference: intervals for $Y_j(1-T_j)$ given observed $Y_j(T_j)$
- For out-of-study inference: intervals for $Y_j(t)$ for $t \in \{0,1\}$ when both potential outcomes are unobserved

**Guarantee**: The prediction intervals must satisfy finite-sample marginal coverage:
$$P_{Q}\left(Y_j(t) \in C_j(X_j, t)\right) \geq 1-\alpha$$
for the target inferential quantity, where the probability is taken over the test distribution $Q$.

## 1.3 Technical Assumptions

**Assumption 1 (SUTVA)**: The Stable Unit Treatment Value Assumption holds: (i) no interference between units, and (ii) treatment consistency.

**Assumption 2 (Overlap)**: For observational studies, $0 < e(x) < 1$ for all $x$ in the support of the covariate distribution.

**Assumption 3 (Unconfoundedness)**: For observational studies, $(Y(0), Y(1)) \perp T | X$, i.e., treatment assignment is unconfounded given observed covariates.

**Assumption 4 (Covariate Shift)**: The test and training distributions may differ only in the marginal distribution of covariates: $P(Y(t)|X) = Q(Y(t)|X)$ for $t \in \{0,1\}$, but potentially $P(X) \neq Q(X)$.

**Assumption 5 (Density Ratio Boundedness)**: The likelihood ratio $w(x) = \frac{dQ(X)}{dP(X)}(x)$ exists and is bounded: $\sup_{x} w(x) \leq W < \infty$ for some constant $W$.

These assumptions are standard in causal inference literature and necessary for identifiability. Assumption 4 captures the covariate shift setting studied in Tibshirani et al. (2020), while Assumption 5 ensures the weighted conformal procedure remains well-defined.

## 1.4 Connection to Prior Work

This formulation extends standard conformal prediction to causal inference under covariate shift. Classical conformal prediction (Vovk et al., 2005) requires exchangeability between training and test data, which fails under covariate shift. Tibshirani et al. (2020) address this by introducing weighted conformal scores, but their work focuses on standard prediction problems rather than causal inference where counterfactual outcomes are never jointly observed.

# Section 2: Methodology

## 2.1 High-Level Approach

Our approach combines weighted conformal prediction with doubly robust estimation to construct valid prediction intervals for counterfactual outcomes under covariate shift. The key insight is to use importance weighting to correct for distributional differences between training and test populations, while leveraging the doubly robust property to maintain validity even when either propensity score or outcome models are misspecified.

The methodology consists of three main components: (1) estimation of nuisance parameters (propensity scores and outcome functions) using flexible machine learning methods, (2) construction of doubly robust pseudo-outcomes that serve as surrogates for unobserved counterfactuals, and (3) application of weighted conformal prediction to these pseudo-outcomes with importance weights that correct for covariate shift.

## 2.2 Core Algorithm

### 2.2.1 Nuisance Parameter Estimation

Let $\hat{e}(x)$ and $\hat{\mu}_t(x) = \mathbb{E}[Y|X=x, T=t]$ denote estimators of the propensity score and outcome regression functions, respectively. These can be estimated using any machine learning method (random forests, neural networks, etc.) with appropriate cross-fitting to avoid overfitting bias.

### 2.2.2 Doubly Robust Pseudo-Outcomes

For each training unit $i$ and treatment level $t$, construct the doubly robust pseudo-outcome:

$$\hat{Y}_i(t) = \frac{\mathbb{I}\{T_i = t\}(Y_i - \hat{\mu}_t(X_i))}{\hat{e}(X_i)^t(1-\hat{e}(X_i))^{1-t}} + \hat{\mu}_t(X_i)$$

These pseudo-outcomes have the property that $\mathbb{E}[\hat{Y}_i(t)|X_i] = \mathbb{E}[Y_i(t)|X_i]$ when either the propensity score or outcome model is correctly specified.

### 2.2.3 Importance Weight Estimation

Estimate the likelihood ratio $\hat{w}(x) = \frac{dQ(X)}{dP(X)}(x)$ using density ratio estimation techniques or by training a classifier to distinguish between training and test covariate distributions.

### 2.2.4 Weighted Conformal Prediction

The weighted conformal algorithm proceeds as follows:

```
Algorithm: Weighted Conformal Prediction for Causal Inference

Input: Training data {(X_i, T_i, Y_i)}_{i=1}^n, test covariate X_test, 
       target treatment t, significance level α

1. Split training data into two folds: D_1 (for nuisance estimation) and D_2 (for conformal scores)

2. Using D_1, estimate:
   - Propensity score: ê(x)
   - Outcome functions: μ̂_0(x), μ̂_1(x)  
   - Importance weights: ŵ(x)

3. For each i ∈ D_2, compute doubly robust pseudo-outcome:
   Ŷ_i(t) = [I{T_i = t}(Y_i - μ̂_t(X_i))] / [ê(X_i)^t(1-ê(X_i))^{1-t}] + μ̂_t(X_i)

4. Compute point prediction for test unit:
   Ŷ_test(t) = μ̂_t(X_test)

5. For each i ∈ D_2, compute weighted conformity score:
   S_i = ŵ(X_i) · |Ŷ_i(t) - μ̂_t(X_i)|

6. Find quantile: Q = Quantile({S_i}_{i∈D_2}, (1-α)(1 + 1/|D_2|))

7. Return prediction interval: [Ŷ_test(t) - Q/ŵ(X_test), Ŷ_test(t) + Q/ŵ(X_test)]
```

### 2.2.5 Coverage Guarantee

**Theorem**: Under Assumptions 1-5, the weighted conformal prediction intervals satisfy:
$$P_Q(Y(t) \in C(X, t)) \geq 1 - \alpha$$

The proof follows by showing that the weighted conformity scores are exchangeable under the importance-weighted measure, extending the analysis of Tibshirani et al. (2020) to the doubly robust pseudo-outcomes.

## 2.3 Design Justifications

**Doubly Robust Pseudo-Outcomes**: We use doubly robust estimators because they provide consistent estimation when either the propensity score or outcome model is correctly specified, but not necessarily both. This robustness is crucial when using flexible machine learning methods that may not perfectly capture the true relationships.

**Cross-Fitting**: The data splitting in Step 1 prevents overfitting bias in the nuisance parameter estimates, which could otherwise invalidate the coverage guarantee.

**Weighted Conformity Scores**: Following Tibshirani et al. (2020), the importance weighting corrects for covariate shift by reweighting the training distribution to match the test distribution, ensuring exchangeability under the reweighted measure.

## 2.4 Theoretical Properties

**Finite-Sample Validity**: The coverage guarantee holds exactly in finite samples without asymptotic approximations, provided the importance weights are known or consistently estimated.

**Double Robustness**: The method maintains valid coverage when either the propensity score or outcome models are misspecified, but not necessarily both.

**Efficiency**: When both nuisance models are correctly specified, the intervals achieve optimal efficiency in the sense of having minimal expected width among all valid conformal methods.

## 2.5 Computational Complexity

The computational complexity is dominated by: (1) nuisance parameter estimation: $O(n \log n)$ for tree-based methods, (2) importance weight estimation: $O(n \log n)$, and (3) conformal quantile computation: $O(n \log n)$. The overall complexity is $O(n \log n)$, making the method scalable to large datasets. The method can be easily parallelized across different test points and treatment levels.
