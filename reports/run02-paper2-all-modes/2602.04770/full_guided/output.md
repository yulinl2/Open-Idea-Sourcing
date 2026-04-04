# Reconstruction: full_guided
**Paper:** 2602.04770  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Learning Adaptive Score Functions for Efficient Conformal Prediction

## Abstract

Conformal prediction provides finite-sample marginal coverage guarantees for prediction intervals, but the efficiency of these intervals depends critically on the choice of score function. Existing methods rely on fixed, pre-specified score functions that may be suboptimal for specific datasets and prediction tasks. We propose a novel framework for learning adaptive score functions from data that produce shorter prediction intervals while preserving the fundamental coverage guarantees of conformal prediction. Our approach combines a parameterized score function with a carefully designed training objective that balances interval efficiency with coverage validity. We provide theoretical analysis showing that our learned score functions maintain finite-sample marginal coverage under mild regularity conditions, and establish consistency results for interval length optimization. The framework is general and can be applied to various regression tasks, offering a principled way to improve upon standard conformal methods without sacrificing their distributional robustness.

## 1. Introduction

Uncertainty quantification in machine learning has become increasingly important as predictive models are deployed in high-stakes applications. While point predictions are valuable, many real-world scenarios require prediction intervals that capture the uncertainty around these estimates. The challenge lies in constructing intervals that are both statistically valid—containing the true value with specified probability—and practically useful through their efficiency.

Conformal prediction [Vovk et al., 2005] has emerged as a powerful framework for constructing prediction intervals with finite-sample marginal coverage guarantees. Unlike Bayesian or asymptotic approaches, conformal methods make no distributional assumptions and provide valid coverage for any finite sample size. The key insight is to use past prediction errors, quantified through a score function, to calibrate future predictions.

However, the efficiency of conformal prediction intervals depends critically on the choice of score function. Standard approaches use simple, fixed score functions such as absolute residuals or normalized residuals. While these provide valid coverage, they may not be optimal for the specific characteristics of the data and prediction task at hand. This limitation motivates a fundamental question: can we learn score functions from data that produce more efficient intervals while maintaining coverage guarantees?

**Contributions:**
• We propose a framework for learning adaptive score functions that optimize interval efficiency while preserving finite-sample marginal coverage guarantees
• We provide theoretical analysis establishing coverage validity and consistency properties of our learned score functions under regularity conditions
• We develop a practical algorithm that jointly optimizes the score function and prediction model through a carefully designed objective function
• We demonstrate how the framework can be extended to handle covariate shift scenarios by incorporating importance weighting

## 2. Related Work

**Conformal Prediction.** The foundational work on conformal prediction [Vovk et al., 2005] established the framework for distribution-free prediction intervals. Split conformal prediction [Papadopoulos et al., 2002] provides a computationally efficient variant that maintains exact finite-sample coverage. Recent advances have extended conformal methods to handle covariate shift [Tibshirani et al., 2020], improving coverage under distributional changes between training and test data.

**Score Function Design.** Traditional conformal methods employ fixed score functions such as absolute residuals |Y - Ŷ| or studentized residuals. Some work has explored alternative score functions for specific domains, such as quantile-based scores for heteroscedastic data. However, these approaches still rely on pre-specified functional forms rather than learning from data.

**Adaptive and Learned Uncertainty Quantification.** Several approaches have proposed learning uncertainty estimates directly, including deep ensembles and variational methods. However, these typically lack finite-sample coverage guarantees. Some recent work has explored combining learned uncertainty with conformal methods, but without learning the score function itself.

**Efficiency in Conformal Prediction.** Research on improving conformal prediction efficiency has focused on conditional coverage and locally adaptive methods. These approaches modify the conformal framework to achieve better conditional properties but do not address the fundamental question of score function optimization.

The gap our work fills is the lack of principled methods for learning score functions that optimize interval efficiency while maintaining the distributional robustness and finite-sample guarantees that make conformal prediction attractive.

## 3. Problem Formulation

Consider a regression setting with input space $\mathcal{X} \subseteq \mathbb{R}^d$ and output space $\mathcal{Y} \subseteq \mathbb{R}$. Let $(X_1, Y_1), \ldots, (X_n, Y_n), (X_{n+1}, Y_{n+1})$ be exchangeable random variables drawn from some unknown distribution $P$.

Given a prediction function $\hat{f}: \mathcal{X} \to \mathcal{Y}$ and a score function $s: \mathcal{X} \times \mathcal{Y} \times \mathcal{Y} \to \mathbb{R}_+$, the conformal prediction framework constructs prediction intervals as follows:

1. Compute conformity scores: $R_i = s(X_i, Y_i, \hat{f}(X_i))$ for $i = 1, \ldots, n$
2. For miscoverage level $\alpha \in (0,1)$, find the $(1-\alpha)(1+1/n)$-quantile: $\hat{q} = \text{Quantile}_{1-\alpha}(\{R_1, \ldots, R_n\})$
3. Construct prediction interval: $C(X_{n+1}) = \{y \in \mathcal{Y} : s(X_{n+1}, y, \hat{f}(X_{n+1})) \leq \hat{q}\}$

**Standard Coverage Guarantee:** For any distribution $P$ and any prediction function $\hat{f}$, we have $\mathbb{P}(Y_{n+1} \in C(X_{n+1})) \geq 1-\alpha$.

**Problem Statement:** Design a method to learn a parameterized score function $s_\theta(x, y, \hat{y})$ from data such that:
1. **Coverage:** The resulting conformal intervals maintain finite-sample marginal coverage guarantees
2. **Efficiency:** The intervals are shorter than those produced by standard fixed score functions

**Assumptions:**
- Exchangeability of $(X_i, Y_i)_{i=1}^{n+1}$
- Score function $s_\theta$ is continuous in $\theta$ and satisfies $s_\theta(x, y, \hat{y}) = 0$ if and only if $y = \hat{y}$
- The parameter space $\Theta$ is compact

## 4. Methodology

Our approach learns an adaptive score function $s_\theta$ by optimizing a carefully designed objective that balances interval efficiency with coverage validity. The key insight is to use a held-out validation set to estimate interval properties while maintaining the coverage guarantees on fresh test data.

### 4.1 Algorithm Overview

**Data Splitting:** Partition the available data into three sets:
- Training set $\mathcal{D}_{\text{train}}$ for learning the prediction function $\hat{f}$
- Calibration set $\mathcal{D}_{\text{cal}}$ for conformal calibration
- Validation set $\mathcal{D}_{\text{val}}$ for score function learning

**Score Function Parameterization:** We parameterize the score function as:
$$s_\theta(x, y, \hat{y}) = g_\theta(x, |y - \hat{y}|, h(x, \hat{y}))$$

where $g_\theta$ is a neural network with parameters $\theta$, and $h(x, \hat{y})$ captures additional features such as local prediction uncertainty or input complexity measures.

### 4.2 Learning Objective

The learning objective combines interval efficiency with coverage validity:

$$\mathcal{L}(\theta) = \mathbb{E}_{(x,y) \sim \mathcal{D}_{\text{val}}}[\ell_{\text{width}}(x, y, \theta)] + \lambda \ell_{\text{coverage}}(\theta)$$

**Efficiency Term:** The width penalty encourages shorter intervals:
$$\ell_{\text{width}}(x, y, \theta) = \text{width}(C_\theta(x))$$

where $C_\theta(x)$ is the conformal interval using score function $s_\theta$.

**Coverage Regularization:** To maintain coverage, we include a penalty term:
$$\ell_{\text{coverage}}(\theta) = \max\left(0, \alpha - \hat{\text{coverage}}_{\text{val}}(\theta)\right)^2$$

where $\hat{\text{coverage}}_{\text{val}}(\theta)$ is the empirical coverage on the validation set.

### 4.3 Training Algorithm

```
Algorithm: Adaptive Score Function Learning

Input: Training data D_train, calibration data D_cal, validation data D_val
Output: Learned score function s_θ

1. Train prediction function f̂ on D_train
2. Initialize score function parameters θ₀
3. For epoch = 1 to max_epochs:
   a. Compute conformity scores on D_cal using current s_θ
   b. Determine conformal quantile q̂
   c. Evaluate intervals on D_val and compute L(θ)
   d. Update θ ← θ - η∇_θ L(θ)
4. Return s_θ
```

### 4.4 Coverage Preservation

The key insight for maintaining coverage is that the score function learning uses only the validation set for optimization, while the conformal calibration uses the separate calibration set. This ensures that the coverage guarantee on fresh test data remains valid, as the calibration step follows the standard conformal protocol.

**Theoretical Justification:** Since the learned parameters $\theta^*$ depend only on the validation data, and the conformal quantile $\hat{q}$ is computed on the independent calibration set, the exchangeability required for coverage guarantees is preserved for new test points.

## 5. Theoretical Analysis

### 5.1 Coverage Guarantee

**Theorem 1 (Finite-Sample Coverage):** Let $s_{\theta^*}$ be the score function learned using the proposed algorithm. For any distribution $P$ and any learned parameters $\theta^*$, the conformal prediction intervals satisfy:

$$\mathbb{P}(Y_{n+1} \in C_{\theta^*}(X_{n+1})) \geq 1-\alpha$$

**Proof Sketch:** The coverage guarantee follows from the standard conformal prediction analysis. The key observation is that $\theta^*$ is determined using only the validation set, which is independent of the calibration set used to compute the conformal quantile. Therefore, the exchangeability condition required for conformal coverage is maintained.

### 5.2 Consistency of Interval Length

**Theorem 2 (Asymptotic Efficiency):** Under regularity conditions on the score function class and assuming the validation set size grows proportionally with the total sample size, the learned score function converges to the optimal score function in the class:

$$\lim_{n \to \infty} \mathbb{E}[\text{width}(C_{\theta^*}(X))] = \inf_{\theta \in \Theta} \mathbb{E}[\text{width}(C_\theta(X))]$$

**Proof Sketch:** This follows from uniform convergence arguments for the empirical risk minimization over the score function class, combined with the consistency of empirical coverage estimates.

### 5.3 Robustness Under Model Misspecification

**Proposition 1:** The coverage guarantees remain valid even when the prediction function $\hat{f}$ is misspecified or when the score function class does not contain the optimal score function.

This robustness property is inherited from the distribution-free nature of conformal prediction and ensures practical applicability.

## 6. Experimental Design

### 6.1 Datasets and Setup

**Synthetic Data:** We would generate datasets with known ground truth to validate theoretical predictions:
- Heteroscedastic regression with varying noise levels
- Non-linear relationships with different complexity levels
- Datasets with known optimal score functions for verification

**Real-World Datasets:** 
- UCI regression benchmarks (Boston Housing, Energy Efficiency, Concrete Strength)
- Time series prediction tasks (electricity load, stock prices)
- High-dimensional datasets (gene expression, image regression)

**Data Splitting:** For each dataset, we would use 60% for training the prediction model, 20% for conformal calibration, 15% for score function learning, and 5% for final evaluation.

### 6.2 Baselines and Metrics

**Baselines:**
- Standard conformal prediction with absolute residuals
- Conformal prediction with normalized residuals
- Quantile-based score functions
- Locally weighted conformal prediction
- Methods from [Tibshirani et al., 2020] for covariate shift scenarios

**Evaluation Metrics:**
- **Coverage:** Empirical coverage rate across test examples
- **Efficiency:** Average interval width, median interval width
- **Conditional Coverage:** Coverage stratified by input regions
- **Computational Cost:** Training time and prediction time

### 6.3 Experimental Questions

**Efficiency Gains:** How much shorter are intervals produced by learned score functions compared to fixed alternatives across different data characteristics?

**Coverage Validity:** Do the learned score functions maintain the theoretical coverage guarantees in practice across diverse datasets?

**Robustness:** How does performance degrade under distribution shift, model misspecification, and limited calibration data?

**Ablation Studies:** 
- Impact of score function architecture choices
- Effect of validation set size on learning quality
- Sensitivity to hyperparameter λ in the objective function

### 6.4 Implementation Details

**Score Function Architecture:** Multi-layer perceptrons with 2-3 hidden layers, ReLU activations, and careful initialization to ensure positive outputs.

**Optimization:** Adam optimizer with learning rate scheduling and early stopping based on validation loss.

**Feature Engineering:** Input features would include prediction confidence measures, local data density estimates, and input complexity metrics.

## 7. Discussion

### 7.1 Strengths and Expected Benefits

**Theoretical Soundness:** Our approach maintains the finite-sample coverage guarantees that make conformal prediction attractive while optimizing for efficiency. This combination of validity and adaptivity addresses a key limitation of existing methods.

**Generality:** The framework can be applied to various regression tasks and can incorporate domain-specific knowledge through the score function parameterization.

**Practical Impact:** By learning from data rather than relying on fixed score functions, the method should produce shorter intervals in practice, making conformal prediction more useful for decision-making applications.

### 7.2 Limitations and Challenges

**Data Requirements:** The approach requires sufficient data for three-way splitting, which may be limiting in small-sample scenarios. The validation set size affects the quality of score function learning.

**Computational Overhead:** Learning the score function adds computational cost compared to standard conformal methods, though this is a one-time cost during training.

**Hyperparameter Sensitivity:** The balance between efficiency and coverage (parameter λ) may require careful tuning for different applications.

**Theoretical Gaps:** While we establish coverage guarantees, the analysis of how much efficiency improvement is possible remains an open theoretical question.

### 7.3 Broader Impact

**Positive Applications:** Improved uncertainty quantification could benefit high-stakes applications like medical diagnosis, autonomous systems, and financial modeling where both validity and efficiency of uncertainty estimates matter.

**Potential Risks:** More efficient intervals might lead to overconfidence if practitioners don't understand the coverage guarantees. Clear communication about the probabilistic interpretation remains crucial.

## 8. Conclusion

We have proposed a novel framework for learning adaptive score functions in conformal prediction that optimizes interval efficiency while preserving finite-sample marginal coverage guarantees. Our approach addresses a fundamental limitation of existing conformal methods by moving beyond fixed, pre-specified score functions to data-driven alternatives.

The key contributions include: (1) a principled learning objective that balances efficiency and coverage, (2) theoretical analysis establishing coverage validity and consistency properties, and (3) a practical algorithm that can be applied to diverse regression tasks. Our framework maintains the distributional robustness that makes conformal prediction attractive while improving practical utility through shorter intervals.

**Open Questions and Future Work:**
- Can we establish finite-sample bounds on the efficiency gains achievable through score function learning?
- How can the framework be extended to classification and structured prediction settings?
- What are the optimal score function architectures for different types of prediction tasks?
- Can we develop adaptive methods that automatically balance the efficiency-coverage trade-off without manual hyperparameter tuning?

The proposed framework opens new directions for making conformal prediction more adaptive and efficient while maintaining its fundamental theoretical guarantees.

## References

[Papadopoulos et al., 2002] Papadopoulos, H., Proedrou, K., Vovk, V., and Gammerman, A. Inductive confidence machines for regression. In European Conference on Machine Learning, 2002.

[Tibshirani et al., 2020] Tibshirani, R. J., Barber, R. F., Candes, E. J., and Ramdas, A. Conformal prediction under covariate shift. In Neural Information Processing Systems, 2020.

[Vovk et al., 2005] Vovk, V., Gammerman, A., and Shafer, G. Algorithmic Learning in a Random World. Springer, 2005.
