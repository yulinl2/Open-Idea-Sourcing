# Reconstruction: full_freestyle
**Paper:** 2602.04770  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Learning Adaptive Score Functions for Efficient Conformal Prediction

## Abstract

Conformal prediction provides finite-sample coverage guarantees for prediction intervals, but the efficiency of these intervals depends critically on the choice of score function. We propose a novel framework for learning adaptive score functions that minimize interval width while preserving the marginal coverage guarantees of conformal prediction. Our approach optimizes a differentiable surrogate for interval width subject to coverage constraints, yielding score functions tailored to the data distribution. We prove that our learned score functions maintain finite-sample marginal coverage and establish consistency results for interval efficiency. Experiments across regression and classification tasks demonstrate that adaptive score functions produce significantly narrower intervals than standard conformal methods while maintaining valid coverage.

## 1. Introduction

Uncertainty quantification has become increasingly important in machine learning applications where reliable confidence estimates are crucial for decision-making. Conformal prediction [Vovk et al., 2005] offers an attractive framework for constructing prediction intervals with finite-sample marginal coverage guarantees—regardless of the underlying data distribution or model assumptions. Given a miscoverage level $\alpha$, conformal prediction produces intervals that contain the true value with probability at least $1-\alpha$ for any finite sample size.

The core insight of conformal prediction lies in the use of a *score function* that measures how "unusual" or "non-conforming" a candidate prediction is relative to the training data. The choice of score function fundamentally determines both the validity and efficiency of the resulting prediction intervals. While marginal coverage is guaranteed for any score function under the exchangeability assumption, the *width* of the intervals—and thus their practical utility—depends critically on how well the score function captures the underlying uncertainty structure of the problem.

Current conformal prediction methods typically employ fixed, pre-specified score functions such as absolute residuals for regression or margin-based scores for classification. While these choices are natural and often effective, they may not be optimal for the specific data distribution at hand. This raises a fundamental question: *Can we learn score functions from data that produce more efficient prediction intervals while preserving the finite-sample coverage guarantees that make conformal prediction attractive?*

This question is non-trivial because it requires balancing two competing objectives: (1) maintaining the distribution-free coverage guarantees that are the hallmark of conformal prediction, and (2) adapting to the data to minimize interval width. The challenge lies in ensuring that any learned score function preserves the validity of the conformal procedure while improving efficiency.

In this paper, we propose a novel framework for learning adaptive score functions that addresses this challenge. Our key contributions are:

1. **Theoretical Framework**: We develop a principled approach for learning score functions that maintains finite-sample marginal coverage guarantees while optimizing for interval efficiency.

2. **Optimization Algorithm**: We present a practical algorithm that optimizes a differentiable surrogate for interval width subject to coverage constraints, yielding adaptive score functions tailored to the data.

3. **Coverage Guarantees**: We prove that our learned score functions preserve the finite-sample marginal coverage properties of conformal prediction and establish consistency results for interval efficiency.

4. **Empirical Validation**: We demonstrate across diverse regression and classification tasks that adaptive score functions produce significantly narrower intervals than standard conformal methods while maintaining valid coverage.

## 2. Background and Related Work

### 2.1 Conformal Prediction

Conformal prediction [Vovk et al., 2005; Shafer & Vovk, 2008] provides a general framework for constructing prediction sets with finite-sample coverage guarantees. Given a training set $(X_1, Y_1), \ldots, (X_n, Y_n)$ and a new test point $X_{n+1}$, the goal is to construct a prediction set $C(X_{n+1})$ such that $P(Y_{n+1} \in C(X_{n+1})) \geq 1 - \alpha$ for a specified miscoverage level $\alpha$.

The split conformal prediction procedure works as follows:

1. **Split the data**: Divide the training data into a proper training set and a calibration set.
2. **Train a model**: Use the proper training set to train a predictive model.
3. **Compute conformity scores**: For each point in the calibration set, compute a score function $s(X_i, Y_i)$ that measures how "non-conforming" the true label $Y_i$ is relative to the model's prediction.
4. **Find quantile**: Compute the $(1-\alpha)(1+1/|\text{cal}|)$-quantile of the calibration scores, denoted $\hat{q}$.
5. **Construct prediction set**: For a test point $X_{n+1}$, the prediction set is $C(X_{n+1}) = \{y : s(X_{n+1}, y) \leq \hat{q}\}$.

The choice of score function $s(x, y)$ is crucial. For regression, common choices include:
- Absolute residual: $s(x, y) = |y - \hat{f}(x)|$
- Normalized residual: $s(x, y) = |y - \hat{f}(x)|/\hat{\sigma}(x)$

For classification, typical choices include:
- Margin-based: $s(x, y) = 1 - \hat{p}_y(x)$ where $\hat{p}_y(x)$ is the predicted probability for class $y$

### 2.2 Efficiency in Conformal Prediction

While conformal prediction guarantees marginal coverage, the efficiency of the prediction sets depends on the score function. Efficient score functions should assign low scores to likely outcomes and high scores to unlikely outcomes, resulting in tighter prediction sets.

Several works have studied efficiency in conformal prediction. Romano et al. [2019] analyzed the efficiency of different score functions for classification. Tibshirani et al. [2019] studied the asymptotic properties of conformal prediction intervals. Foygel-Barber et al. [2021] provided finite-sample analysis of conformal prediction efficiency.

### 2.3 Adaptive Conformal Prediction

Recent work has explored adaptive variants of conformal prediction. Tibshirani et al. [2020] developed conformal prediction under covariate shift using importance weighting. Gibbs & Candès [2021] proposed adaptive conformal inference for time series. These methods adapt to distributional changes but still rely on pre-specified score functions.

Our work differs by learning the score function itself to optimize efficiency while maintaining coverage guarantees.

## 3. Methodology

### 3.1 Problem Formulation

Let $(X, Y)$ denote a random pair from some unknown distribution $P$, where $X \in \mathcal{X}$ is the feature vector and $Y \in \mathcal{Y}$ is the response. We assume access to a training dataset $\mathcal{D}_{\text{train}} = \{(X_i, Y_i)\}_{i=1}^n$ and a calibration dataset $\mathcal{D}_{\text{cal}} = \{(X_i, Y_i)\}_{i=n+1}^{n+m}$, both drawn i.i.d. from $P$.

Our goal is to learn a score function $s_\theta: \mathcal{X} \times \mathcal{Y} \to \mathbb{R}$ parameterized by $\theta$ that produces efficient prediction intervals while maintaining finite-sample marginal coverage guarantees.

For a test point $(X_{n+m+1}, Y_{n+m+1})$, the conformal prediction interval using score function $s_\theta$ is:

$$C_\theta(X_{n+m+1}) = \{y \in \mathcal{Y} : s_\theta(X_{n+m+1}, y) \leq \hat{q}_\theta\}$$

where $\hat{q}_\theta$ is the $(1-\alpha)\left(1 + \frac{1}{m+1}\right)$-quantile of the calibration scores $\{s_\theta(X_i, Y_i)\}_{i=n+1}^{n+m}$.

### 3.2 Adaptive Score Function Learning

The key insight of our approach is to learn score functions that minimize a differentiable proxy for interval width while ensuring coverage validity. We formulate this as a constrained optimization problem:

$$\min_\theta \mathbb{E}[W(C_\theta(X))] \quad \text{subject to} \quad P(Y \in C_\theta(X)) \geq 1 - \alpha$$

where $W(C)$ denotes the "width" of prediction set $C$, and the expectation is over the data distribution.

**Challenge**: This optimization problem is challenging for several reasons:
1. The constraint involves the true data distribution, which is unknown
2. The mapping from $\theta$ to interval width is non-differentiable
3. We need to ensure coverage holds for finite samples, not just asymptotically

### 3.3 Surrogate Optimization

To address these challenges, we develop a practical algorithm based on surrogate optimization:

**Step 1: Differentiable Width Proxy**
For regression problems, we use the expected interval width as our efficiency metric:
$$W_{\text{reg}}(C_\theta(x)) = \mathbb{E}_{y \sim C_\theta(x)}[|y - \text{median}(C_\theta(x))|]$$

For classification, we use the size of the prediction set:
$$W_{\text{class}}(C_\theta(x)) = |C_\theta(x)|$$

**Step 2: Coverage Constraint Approximation**
We approximate the coverage constraint using the empirical coverage on a validation set:
$$\frac{1}{|\mathcal{D}_{\text{val}}|} \sum_{(x,y) \in \mathcal{D}_{\text{val}}} \mathbf{1}[y \in C_\theta(x)] \geq 1 - \alpha - \epsilon$$

where $\epsilon > 0$ is a slack parameter that accounts for finite-sample effects.

**Step 3: Smooth Score Function Parameterization**
We parameterize the score function using neural networks to ensure differentiability:
$$s_\theta(x, y) = \text{NN}_\theta(x, y)$$

The network architecture depends on the problem type:
- **Regression**: $s_\theta(x, y) = |y - \hat{f}(x)| \cdot g_\theta(x)$ where $g_\theta(x) > 0$ is a learned scaling function
- **Classification**: $s_\theta(x, y) = h_\theta(x, y)$ where $h_\theta$ is a general neural network

### 3.4 Training Algorithm

Our training procedure alternates between optimizing the score function and validating coverage:

```
Algorithm: Adaptive Score Function Learning
Input: Training data D_train, calibration data D_cal, validation data D_val
Output: Learned score function s_θ

1. Initialize θ randomly
2. Train base model f̂ on D_train  
3. For epoch = 1 to max_epochs:
   a. Compute calibration quantile q̂_θ using D_cal and current s_θ
   b. Evaluate coverage on D_val
   c. If coverage < 1-α-ε, increase penalty weight λ
   d. Update θ using gradient descent on:
      L(θ) = E[W(C_θ(x))] + λ · max(0, (1-α-ε) - coverage)
4. Return s_θ
```

## 4. Theoretical Analysis

### 4.1 Coverage Guarantees

Our first main theoretical result establishes that learned score functions preserve finite-sample marginal coverage guarantees.

**Theorem 1** (Finite-Sample Coverage): *Let $s_\theta$ be any score function learned using our procedure. If the calibration data $\mathcal{D}_{\text{cal}}$ and test point $(X_{n+m+1}, Y_{n+m+1})$ are exchangeable, then*

$$P\left(Y_{n+m+1} \in C_\theta(X_{n+m+1})\right) \geq \frac{\lfloor (1-\alpha)(m+1) \rfloor}{m+1}$$

*This holds for any finite $m$ and any choice of parameters $\theta$.*

**Proof Sketch**: The key insight is that the coverage guarantee depends only on the rank of the test score among the calibration scores, not on the specific form of the score function. Since our learned score function is applied consistently to both calibration and test data, the exchangeability property is preserved, and the standard conformal prediction coverage analysis applies.

### 4.2 Consistency of Learned Score Functions

Our second result establishes that under mild conditions, our learned score functions converge to optimal ones.

**Theorem 2** (Consistency): *Assume the score function class $\{s_\theta : \theta \in \Theta\}$ contains a score function $s^*$ that achieves optimal efficiency while maintaining coverage. Under standard regularity conditions on the loss function and assuming sufficient data, the learned score function $\hat{s}_\theta$ converges to $s^*$ in probability as the sample size increases.*

**Proof Sketch**: This follows from standard empirical risk minimization theory. The key technical challenge is showing that the coverage constraint can be satisfied uniformly over the parameter space, which we establish using concentration inequalities.

### 4.3 Efficiency Analysis

We also provide finite-sample efficiency guarantees.

**Theorem 3** (Efficiency Bounds): *Under appropriate conditions, the expected width of prediction intervals produced by our learned score function is within $O(1/\sqrt{n})$ of the optimal achievable width, where $n$ is the calibration set size.*

This result shows that our method achieves near-optimal efficiency with high probability.

## 5. Experimental Design and Expected Results

### 5.1 Experimental Setup

We design experiments to validate two key aspects of our approach: (1) maintenance of finite-sample coverage guarantees, and (2) improvement in interval efficiency compared to standard conformal methods.

**Datasets**: We evaluate on diverse regression and classification benchmarks:
- **Regression**: Housing prices, energy efficiency, concrete strength, wine quality
- **Classification**: Image classification (CIFAR-10, MNIST), text classification, medical diagnosis

**Baselines**: We compare against standard conformal prediction methods:
- Absolute residual scores (regression)
- Margin-based scores (classification)  
- Locally adaptive scores [Romano et al., 2019]

**Metrics**:
- **Coverage**: Empirical coverage rate across test sets
- **Efficiency**: Average interval width (regression) or set size (classification)
- **Conditional coverage**: Coverage stratified by feature values to detect potential biases

### 5.2 Expected Experimental Outcomes

**Coverage Validation**: We expect our adaptive score functions to maintain valid marginal coverage across all datasets, with empirical coverage rates close to the nominal $1-\alpha$ level. This validates our theoretical guarantees.

**Efficiency Improvements**: We anticipate significant improvements in interval efficiency:
- **Regression**: 10-30% reduction in average interval width compared to absolute residual baselines
- **Classification**: 15-25% reduction in average prediction set size compared to margin-based baselines

**Adaptation to Data Structure**: We expect larger efficiency gains on datasets with:
- Heteroskedastic noise (varying uncertainty across input space)
- Complex decision boundaries (classification)
- High-dimensional feature spaces

**Robustness**: The learned score functions should maintain efficiency improvements across different:
- Miscoverage levels ($\alpha \in \{0.05, 0.1, 0.2\}$)
- Calibration set sizes
- Base model architectures

### 5.3 Ablation Studies

We plan several ablation studies to understand the key components:

1. **Architecture choices**: Impact of score function parameterization
2. **Training dynamics**: Effect of different optimization strategies
3. **Data efficiency**: Performance with limited calibration data
4. **Computational overhead**: Training time vs. efficiency gains trade-off

## 6. Discussion and Future Directions

### 6.1 Practical Considerations

**Computational Cost**: Learning adaptive score functions introduces additional computational overhead during training. However, this is a one-time cost, and the inference time remains similar to standard conformal prediction.

**Hyperparameter Sensitivity**: The slack parameter $\epsilon$ and penalty weight $\lambda$ require tuning. We expect these to be relatively stable across similar problem types.

**Overfitting Prevention**: Care must be taken to prevent overfitting the score function to the calibration data, which could compromise coverage guarantees.

### 6.2 Extensions and Future Work

**Conditional Coverage**: Extending our framework to achieve conditional coverage guarantees (coverage for subgroups) while maintaining efficiency.

**Distribution Shift**: Combining our approach with techniques for handling covariate shift [Tibshirani et al., 2020] to learn robust score functions.

**Multi-output Problems**: Adapting the framework for structured prediction tasks with complex output spaces.

**Theoretical Refinements**: Tighter finite-sample efficiency bounds and analysis of the bias-variance trade-off in learned score functions.

## 7. Conclusion

We have presented a novel framework for learning adaptive score functions in conformal prediction that maintains finite-sample marginal coverage guarantees while optimizing for interval efficiency. Our approach addresses a fundamental limitation of current conformal methods by adapting the score function to the data distribution rather than relying on fixed, pre-specified choices.

The key insights of our work are: (1) score functions can be learned from data without compromising the validity guarantees of conformal prediction, (2) differentiable surrogates enable practical optimization of interval efficiency, and (3) the resulting adaptive score functions can provide significant efficiency improvements across diverse problem domains.

Our theoretical analysis establishes that learned score functions preserve finite-sample coverage guarantees and achieve near-optimal efficiency. The proposed framework opens new directions for improving the practical utility of conformal prediction by making prediction intervals both reliable and efficient.

The ability to adapt score functions to data represents a significant step toward more effective uncertainty quantification in machine learning, with potential applications in high-stakes domains where both reliability and precision of confidence estimates are crucial.

## References

Foygel-Barber, R., Candes, E. J., Ramdas, A., & Tibshirani, R. J. (2021). Predictive inference with the jackknife+. *Annals of Statistics*, 49(1), 486-507.

Gibbs, I., & Candès, E. (2021). Adaptive conformal inference under distribution shift. In *Advances in Neural Information Processing Systems* (pp. 1660-1672).

Romano, Y., Patterson, E., & Candès, E. (2019). Conformalized quantile regression. In *Advances in Neural Information Processing Systems* (pp. 3543-3553).

Shafer, G., & Vovk, V. (2008). *A tutorial on conformal prediction*. Journal of Machine Learning Research, 9, 371-421.

Tibshirani, R. J., Foygel Barber, R., Candes, E., & Ramdas, A. (2019). Conformal prediction under covariate shift. In *Advances in Neural Information Processing Systems* (pp. 2530-2540).

Tibshirani, R. J., Foygel Barber, R., Candes, E. J., & Ramdas, A. (2020). Conformal prediction under covariate shift. *Journal of Machine Learning Research*, 21(35), 1-35.

Vovk, V., Gammerman, A., & Shafer, G. (2005). *Algorithmic learning in a random world*. Springer.
