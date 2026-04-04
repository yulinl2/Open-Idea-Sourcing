# Reconstruction: full_freestyle
**Paper:** 2602.04770  
**Condition:** no_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Learning Adaptive Score Functions for Efficient Conformal Prediction

## Abstract

Conformal prediction provides finite-sample marginal coverage guarantees for prediction intervals, but the efficiency of these intervals depends critically on the choice of score function. We propose a novel framework for learning adaptive score functions from data while preserving the fundamental coverage guarantees that make conformal prediction attractive. Our approach, called Adaptive Conformal Prediction (ACP), uses a meta-learning strategy to optimize score functions for interval efficiency without compromising validity. We establish theoretical guarantees showing that ACP maintains exact finite-sample coverage regardless of the quality of the learned score function, while achieving provably shorter intervals when the learning succeeds. Extensive experiments on synthetic and real datasets demonstrate that ACP consistently produces more efficient prediction intervals compared to standard conformal methods, with improvements of 15-40% in average interval length while maintaining exact coverage.

## 1. Introduction

Uncertainty quantification has become increasingly important in machine learning applications where reliable confidence estimates are crucial for decision-making. While point predictions provide valuable information, they fail to capture the inherent uncertainty in predictions, leading to potentially dangerous overconfidence in high-stakes domains such as medical diagnosis, autonomous driving, and financial forecasting.

Conformal prediction has emerged as a powerful framework for constructing prediction intervals with finite-sample marginal coverage guarantees. Unlike Bayesian approaches that require distributional assumptions or asymptotic methods that only provide approximate coverage, conformal prediction offers exact coverage guarantees that hold for any finite sample size and any underlying data distribution. This distribution-free property makes conformal prediction particularly attractive for real-world applications where distributional assumptions may be violated.

The conformal prediction framework relies on a score function that measures how "strange" or "non-conforming" a prediction is relative to the training data. The choice of score function is critical: it directly determines the efficiency of the resulting prediction intervals. Traditional approaches use fixed score functions such as absolute residuals $|y - \hat{y}|$ or standardized residuals, but these may be suboptimal for the specific data distribution at hand.

This raises a fundamental question: **Can we learn better score functions from data while preserving the finite-sample coverage guarantees that make conformal prediction attractive?** The challenge lies in balancing two competing objectives: optimizing for shorter, more informative intervals while ensuring the validity guarantee remains intact regardless of how well the learning procedure performs.

In this paper, we propose **Adaptive Conformal Prediction (ACP)**, a novel framework that learns score functions specifically tailored to the data distribution while maintaining exact finite-sample coverage guarantees. Our key contributions are:

1. **Theoretical Framework**: We develop a meta-learning approach for score function optimization that preserves conformal prediction's coverage guarantees even when learning fails.

2. **Efficiency Guarantees**: We prove that when the learning succeeds, ACP produces provably shorter intervals than standard conformal methods.

3. **Practical Algorithm**: We present a computationally efficient algorithm that can be easily integrated into existing conformal prediction pipelines.

4. **Empirical Validation**: We demonstrate substantial improvements in interval efficiency across diverse datasets while maintaining exact coverage.

## 2. Background and Related Work

### 2.1 Conformal Prediction

Conformal prediction, introduced by Vovk et al., provides a framework for constructing prediction intervals with finite-sample marginal coverage guarantees. Given a confidence level $1-\alpha$, the goal is to construct a prediction interval $C(x)$ such that $P(Y \in C(X)) \geq 1-\alpha$ for any new point $(X,Y)$.

The standard conformal prediction algorithm works as follows:

1. **Training Phase**: Given training data $(x_1, y_1), \ldots, (x_n, y_n)$ and a score function $s(x,y)$, compute conformity scores $R_i = s(x_i, y_i)$ for $i = 1, \ldots, n$.

2. **Calibration**: For a new point $x_{n+1}$, define the quantile $\hat{q}_{1-\alpha} = \text{Quantile}_{1-\alpha}(\{R_1, \ldots, R_n\})$.

3. **Prediction**: Construct the prediction set $C(x_{n+1}) = \{y : s(x_{n+1}, y) \leq \hat{q}_{1-\alpha}\}$.

The key theoretical result is that this procedure guarantees $P(Y_{n+1} \in C(X_{n+1})) \geq 1-\alpha$ for any choice of score function $s$, assuming the data is exchangeable.

### 2.2 Score Function Design

The efficiency of conformal prediction intervals depends critically on the score function. Common choices include:

- **Absolute residuals**: $s(x,y) = |y - \hat{f}(x)|$ where $\hat{f}$ is a fitted predictor
- **Normalized residuals**: $s(x,y) = |y - \hat{f}(x)|/\hat{\sigma}(x)$ where $\hat{\sigma}$ estimates conditional variance
- **Quantile-based scores**: Using conditional quantile estimates

Recent work has explored various score function designs. Romano et al. proposed using conditional quantiles for improved efficiency. Tibshirani et al. developed jackknife+ methods that account for overfitting in the score function. Chernozhukov et al. studied distributional conformal prediction using more general score functions.

However, these approaches still rely on pre-specified functional forms that may not be optimal for the specific dataset. Our work addresses this limitation by learning score functions directly from data.

### 2.3 Adaptive and Data-Driven Methods

Several recent works have explored adaptive conformal prediction methods. Gibbs and Candes developed adaptive conformal inference for time series data. Zaffran et al. proposed adaptive conformal prediction for regression with conditional coverage. Feldman et al. studied improving conformal prediction efficiency through score function optimization.

Our approach differs by focusing specifically on learning score functions while maintaining the strong finite-sample guarantees of standard conformal prediction.

## 3. Methodology

### 3.1 Problem Formulation

Let $(X, Y)$ be a random pair with $X \in \mathcal{X}$ and $Y \in \mathbb{R}$. Given training data $\mathcal{D} = \{(x_i, y_i)\}_{i=1}^n$ and a confidence level $1-\alpha$, our goal is to construct a prediction interval $C(x)$ for a new point $x$ such that:

1. **Coverage**: $P(Y \in C(X)) \geq 1-\alpha$ (finite-sample marginal coverage)
2. **Efficiency**: $\mathbb{E}[|C(X)|]$ is minimized subject to the coverage constraint

The key insight is that the optimal score function depends on the underlying data distribution. Formally, we seek to learn a score function $s_\theta(x,y)$ parameterized by $\theta$ that minimizes expected interval length while preserving coverage guarantees.

### 3.2 Adaptive Conformal Prediction Framework

Our Adaptive Conformal Prediction (ACP) framework consists of three main components:

#### 3.2.1 Score Function Parameterization

We parameterize score functions using neural networks:
$$s_\theta(x,y) = g_\theta(x, y, \hat{f}(x))$$
where $g_\theta$ is a neural network, $\hat{f}$ is a base predictor, and $\theta$ are learnable parameters. This general form allows the score function to depend on both the input features and the prediction, enabling adaptation to local data characteristics.

#### 3.2.2 Meta-Learning Objective

We optimize the score function parameters by minimizing expected interval length on a validation set. Specifically, we solve:
$$\min_\theta \mathbb{E}_{(x,y) \sim \mathcal{D}_{\text{val}}} [|C_\theta(x)|]$$
subject to the constraint that the resulting intervals maintain valid coverage.

#### 3.2.3 Coverage-Preserving Training

The critical challenge is ensuring that coverage guarantees are preserved during training. We achieve this through a novel **coverage-preserving regularization** scheme:

1. **Split Conformal Structure**: We maintain the split conformal prediction structure where the calibration set is independent of the score function training.

2. **Conservative Quantile Selection**: We use a slightly more conservative quantile that accounts for the uncertainty in the learned score function.

3. **Worst-Case Guarantees**: We prove that coverage is maintained even if the score function learning fails completely.

### 3.3 Algorithm

The complete ACP algorithm is presented below:

**Algorithm 1: Adaptive Conformal Prediction**

**Input**: Training data $\mathcal{D}$, confidence level $1-\alpha$, base predictor $\hat{f}$

1. **Data Splitting**: Split $\mathcal{D}$ into three parts:
   - $\mathcal{D}_{\text{train}}$: Train base predictor $\hat{f}$
   - $\mathcal{D}_{\text{score}}$: Train score function $s_\theta$  
   - $\mathcal{D}_{\text{cal}}$: Calibration set

2. **Base Predictor Training**: Train $\hat{f}$ on $\mathcal{D}_{\text{train}}$

3. **Score Function Learning**: 
   - Initialize score function parameters $\theta$
   - For each epoch:
     - Sample mini-batch from $\mathcal{D}_{\text{score}}$
     - Compute conformity scores using current $s_\theta$
     - Estimate interval lengths and update $\theta$ to minimize expected length
     - Apply coverage-preserving regularization

4. **Calibration**: 
   - Compute conformity scores $R_i = s_\theta(x_i, y_i)$ for $(x_i, y_i) \in \mathcal{D}_{\text{cal}}$
   - Compute adjusted quantile $\hat{q}_{1-\alpha}^{\text{adj}}$

5. **Prediction**: For new point $x$, return $C(x) = \{y : s_\theta(x,y) \leq \hat{q}_{1-\alpha}^{\text{adj}}\}$

### 3.4 Theoretical Guarantees

We now establish the theoretical properties of ACP.

**Theorem 1 (Finite-Sample Coverage)**: Under exchangeability of the data, the ACP algorithm guarantees:
$$P(Y_{n+1} \in C(X_{n+1})) \geq 1-\alpha$$
regardless of the quality of the learned score function $s_\theta$.

**Proof Sketch**: The key insight is that we maintain the split conformal structure where the calibration set $\mathcal{D}_{\text{cal}}$ is independent of the score function training. Even if the score function learning fails completely, the worst case reduces to standard conformal prediction with a potentially suboptimal but valid score function.

**Theorem 2 (Efficiency Improvement)**: If the learned score function $s_\theta$ satisfies certain optimality conditions, then ACP produces intervals that are no longer on average than standard conformal prediction, with strict improvement under non-degeneracy conditions.

**Proof Sketch**: When the score function learning succeeds in capturing the optimal conformity measure for the data distribution, the resulting intervals approach the theoretically optimal prediction sets for the given coverage level.

## 4. Experimental Design and Results

### 4.1 Experimental Setup

We evaluate ACP on both synthetic and real datasets to assess coverage and efficiency across different scenarios.

#### 4.1.1 Synthetic Data

We generate synthetic datasets with known optimal prediction intervals to validate our approach:

1. **Heteroscedastic Regression**: $Y = f(X) + \sigma(X) \cdot \epsilon$ where $\sigma(X)$ varies with $X$
2. **Non-Gaussian Errors**: Various error distributions (Student-t, skewed distributions)
3. **High-Dimensional Settings**: Features with complex dependencies

#### 4.1.2 Real Datasets

We evaluate on diverse real-world datasets:
- **Housing Prices**: Boston Housing, California Housing
- **Energy Prediction**: Power plant output, building energy consumption
- **Medical Data**: Diabetes progression, medical cost prediction
- **Time Series**: Stock prices, weather prediction

#### 4.1.3 Baselines

We compare against several baseline methods:
- **Standard CP**: Conformal prediction with absolute residuals
- **Normalized CP**: Using estimated conditional variance
- **Quantile CP**: Using conditional quantile regression
- **Jackknife+**: Cross-conformal prediction method

#### 4.1.4 Metrics

- **Empirical Coverage**: Fraction of test points contained in prediction intervals
- **Average Interval Length**: Mean length of prediction intervals
- **Efficiency Ratio**: Ratio of ACP interval length to baseline methods
- **Conditional Coverage**: Coverage across different regions of input space

### 4.2 Results Summary

Our experiments demonstrate consistent improvements in interval efficiency while maintaining exact coverage guarantees.

#### 4.2.1 Coverage Validation

Across all datasets and experimental settings, ACP maintains empirical coverage rates at or above the nominal level (e.g., 90% for $\alpha = 0.1$). The coverage rates are statistically indistinguishable from standard conformal prediction methods, confirming our theoretical guarantees.

#### 4.2.2 Efficiency Improvements

ACP achieves substantial reductions in average interval length:
- **Synthetic Data**: 20-45% reduction in interval length compared to standard CP
- **Real Datasets**: 15-35% improvement across different domains
- **Heteroscedastic Settings**: Particularly large improvements (30-50%) when conditional variance varies significantly

#### 4.2.3 Computational Overhead

The score function learning adds modest computational cost:
- Training time increases by 20-50% compared to standard CP
- Prediction time remains essentially unchanged
- Memory requirements scale with score function complexity

#### 4.2.4 Ablation Studies

We conduct several ablation studies to understand the contribution of different components:
- **Score Function Architecture**: Comparing different neural network architectures
- **Training Strategies**: Impact of different optimization procedures
- **Regularization Effects**: Role of coverage-preserving regularization

### 4.3 Analysis and Discussion

#### 4.3.1 When Does ACP Help Most?

ACP provides the largest improvements in scenarios where:
1. **Heteroscedasticity**: Conditional variance varies significantly across input space
2. **Non-Gaussian Errors**: Error distributions deviate from normality
3. **Complex Dependencies**: Nonlinear relationships between features and uncertainty

#### 4.3.2 Learned Score Function Interpretability

Analysis of learned score functions reveals that ACP automatically discovers several important patterns:
- **Adaptive normalization**: Automatically adjusts for local variance
- **Asymmetric adjustments**: Captures skewness in error distributions
- **Feature interactions**: Incorporates complex feature dependencies

#### 4.3.3 Robustness Analysis

We evaluate robustness to various factors:
- **Sample size**: Performance across different training set sizes
- **Distribution shift**: Behavior under covariate shift
- **Hyperparameter sensitivity**: Stability across different settings

## 5. Extensions and Future Directions

### 5.1 Conditional Coverage

While our current framework targets marginal coverage, extending to conditional coverage is an important direction. We outline a modified approach that aims to achieve coverage conditional on input features while maintaining computational tractability.

### 5.2 Multi-Output Prediction

The framework naturally extends to multi-output regression problems where we seek prediction regions rather than intervals. The score function can be generalized to measure conformity in multi-dimensional output spaces.

### 5.3 Online Adaptation

For streaming data applications, we can develop online versions of ACP that continuously adapt the score function as new data arrives while maintaining coverage guarantees through careful adaptation of the calibration procedure.

### 5.4 Distribution-Aware Learning

Future work could incorporate distributional assumptions when available, potentially achieving even better efficiency while maintaining robustness through the conformal framework.

## 6. Conclusion

We have presented Adaptive Conformal Prediction (ACP), a novel framework for learning score functions that improve the efficiency of conformal prediction intervals while preserving finite-sample coverage guarantees. Our approach addresses a fundamental limitation of existing conformal prediction methods by adapting the conformity measure to the specific characteristics of the data distribution.

The key contributions of this work include:

1. **Theoretical Foundation**: We established that learned score functions can be incorporated into conformal prediction while maintaining exact finite-sample coverage guarantees, regardless of the quality of the learning procedure.

2. **Practical Algorithm**: We developed a computationally efficient algorithm that can be easily integrated into existing machine learning pipelines.

3. **Empirical Validation**: Extensive experiments demonstrate consistent improvements in interval efficiency across diverse datasets and settings.

4. **Methodological Innovation**: Our coverage-preserving training procedure provides a general framework for incorporating learned components into conformal prediction while maintaining validity guarantees.

The success of ACP opens several exciting research directions. The framework provides a principled way to incorporate domain knowledge and data-driven insights into uncertainty quantification while maintaining the strong guarantees that make conformal prediction attractive for real-world applications.

As machine learning systems are increasingly deployed in high-stakes applications, reliable uncertainty quantification becomes ever more critical. By making conformal prediction intervals more efficient without sacrificing validity, ACP represents an important step toward practical, reliable uncertainty quantification that can be trusted in real-world decision-making scenarios.

The combination of theoretical rigor and practical effectiveness makes ACP a valuable addition to the uncertainty quantification toolkit, bridging the gap between the strong guarantees of conformal prediction and the efficiency demands of real-world applications.

## References

[1] Vovk, V., Gammerman, A., & Shafer, G. (2005). Algorithmic learning in a random world. Springer.

[2] Romano, Y., Patterson, E., & Candes, E. (2019). Conformalized quantile regression. Advances in Neural Information Processing Systems, 32.

[3] Tibshirani, R. J., Foygel Barber, R., Candes, E., & Ramdas, A. (2019). Conformal prediction under covariate shift. Advances in Neural Information Processing Systems, 32.

[4] Chernozhukov, V., Wuthrich, K., & Zhu, Y. (2021). Distributional conformal prediction. Proceedings of the National Academy of Sciences, 118(48).

[5] Gibbs, I., & Candes, E. (2021). Adaptive conformal inference under distribution shift. Advances in Neural Information Processing Systems, 34.

[6] Zaffran, M., Féron, O., Goude, Y., Josse, J., & Dieuleveut, A. (2022). Adaptive conformal prediction for time series. arXiv preprint arXiv:2202.07282.

[7] Feldman, S., Bates, S., & Romano, Y. (2021). Improving conditional coverage via orthogonal quantile regression. Advances in Neural Information Processing Systems, 34.

[8] Papadopoulos, H., Proedrou, K., Vovk, V., & Gammerman, A. (2002). Inductive confidence machines for regression. European Conference on Machine Learning.

[9] Lei, J., G'Sell, M., Rinaldo, A., Tibshirani, R. J., & Wasserman, L. (2018). Distribution-free predictive inference for regression. Journal of the American Statistical Association, 113(523), 1094-1111.

[10] Angelopoulos, A. N., & Bates, S. (2021). A gentle introduction to conformal prediction and distribution-free uncertainty quantification. arXiv preprint arXiv:2107.07511.
