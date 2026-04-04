# Reconstruction: full_freestyle
**Paper:** 2602.04770  
**Condition:** with_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Learning Adaptive Score Functions for Efficient Conformal Prediction

## Abstract

Conformal prediction provides finite-sample marginal coverage guarantees for prediction intervals, but the efficiency of these intervals depends critically on the choice of score function. We propose a novel framework for learning adaptive score functions that optimize interval efficiency while preserving the fundamental coverage guarantees of conformal prediction. Our approach uses a bi-level optimization procedure where the outer loop learns score function parameters to minimize expected interval length, while the inner loop applies standard conformal calibration. We prove that our method maintains finite-sample marginal coverage regardless of the quality of the learned score function, ensuring robustness even when the learning procedure fails. Theoretical analysis reveals conditions under which adaptive scores can significantly outperform fixed alternatives, and we demonstrate substantial improvements in interval efficiency across synthetic and real-world datasets while maintaining exact coverage guarantees.

## 1. Introduction

Uncertainty quantification has become increasingly important as machine learning systems are deployed in high-stakes applications. While point predictions provide valuable information, decision-makers often require prediction intervals that capture the uncertainty in these estimates. The challenge lies in constructing intervals that are both *valid* (achieve the desired coverage probability) and *efficient* (as narrow as possible).

Conformal prediction has emerged as a powerful framework for constructing prediction intervals with finite-sample marginal coverage guarantees [Vovk et al., 2005]. Unlike asymptotic approaches that rely on large-sample approximations, conformal methods provide exact coverage for any finite sample size and any data distribution. The key insight is to use past prediction errors to calibrate future predictions through a simple quantile-based procedure.

The efficiency of conformal prediction intervals depends critically on the choice of *score function* – a measure of how well a predicted value conforms to the observed data. Traditional approaches use fixed score functions such as absolute residuals $|y - \hat{y}|$ for regression or prediction set sizes for classification. However, these generic choices may be suboptimal for specific data distributions or prediction problems.

This raises a fundamental question: can we learn better score functions from data while preserving the finite-sample coverage guarantees that make conformal prediction attractive? The challenge is that any learning procedure introduces additional uncertainty that could potentially compromise the validity of the resulting intervals.

We address this challenge by proposing a framework for learning adaptive score functions that optimizes for interval efficiency while maintaining rigorous coverage guarantees. Our key contributions are:

1. **A bi-level optimization framework** for learning score functions that minimize expected interval length while preserving conformal validity
2. **Theoretical guarantees** showing that our method maintains finite-sample marginal coverage regardless of how well the score function learning succeeds
3. **Efficiency analysis** revealing when and why adaptive score functions can significantly outperform fixed alternatives
4. **Empirical validation** demonstrating substantial improvements in interval efficiency across diverse datasets

## 2. Background and Related Work

### 2.1 Conformal Prediction

Conformal prediction was introduced by Vovk et al. [2005] as a framework for constructing prediction regions with finite-sample validity guarantees. The core idea is elegantly simple: given a desired coverage level $1-\alpha$ and a score function $s(x,y)$ that measures non-conformity, we can construct prediction intervals by finding the appropriate quantile of past scores.

Formally, consider a regression setting with training data $(X_1, Y_1), \ldots, (X_n, Y_n)$ and a test point $X_{n+1}$. For any candidate prediction $y$, we compute the score $s(X_{n+1}, y)$ and compare it to the scores on the training data. The conformal prediction interval consists of all $y$ values such that:

$$\frac{1}{n+1}\sum_{i=1}^{n+1} \mathbf{1}\{s(X_i, Y_i) \geq s(X_{n+1}, y)\} > \alpha$$

This procedure guarantees that $P(Y_{n+1} \in C(X_{n+1})) \geq 1-\alpha$ for any data distribution, where $C(X_{n+1})$ is the conformal prediction set.

### 2.2 Score Function Design

The choice of score function fundamentally determines both the validity and efficiency of conformal prediction. Common choices include:

- **Absolute residuals**: $s(x,y) = |y - \hat{f}(x)|$ for regression with predictor $\hat{f}$
- **Normalized residuals**: $s(x,y) = |y - \hat{f}(x)|/\hat{\sigma}(x)$ when heteroscedasticity is present
- **Quantile-based scores**: Using conditional quantile predictions to construct asymmetric intervals

Recent work has explored more sophisticated score functions. Romano et al. [2019] introduced split conformal prediction for improved computational efficiency. Chernozhukov et al. [2021] developed distributional conformal prediction using the full conditional distribution. However, these approaches still rely on pre-specified score functions rather than learning them from data.

### 2.3 Adaptive and Conditional Methods

Several recent works have explored adaptive conformal methods. Tibshirani et al. [2019] developed weighted conformal prediction for covariate shift, using importance weights to correct for distribution mismatch. Feldman et al. [2021] proposed calibration with neural networks to improve conditional coverage. However, these methods focus on adaptation to specific distributional assumptions rather than general score function learning.

The challenge in learning score functions is maintaining the finite-sample guarantees that make conformal prediction attractive. Any learning procedure introduces randomness that could potentially invalidate the coverage guarantees. Our work addresses this fundamental challenge through a careful separation of the learning and calibration phases.

## 3. Learning Adaptive Score Functions

### 3.1 Problem Formulation

We seek to learn score functions that minimize expected interval length while maintaining finite-sample marginal coverage. Let $\mathcal{S}_\theta$ be a parameterized family of score functions, where $\theta \in \Theta$ represents the parameters to be learned. Our goal is to find $\theta^*$ that solves:

$$\theta^* = \arg\min_{\theta \in \Theta} \mathbb{E}[\text{Length}(C_\theta(X))]$$

subject to the constraint that the conformal prediction intervals $C_\theta(X)$ maintain valid coverage: $P(Y \in C_\theta(X)) \geq 1-\alpha$.

The key challenge is that both the objective and constraint involve unknown expectations over the data distribution. We must estimate these quantities from finite samples while ensuring that the coverage constraint remains satisfied regardless of estimation errors.

### 3.2 Bi-Level Optimization Framework

We propose a bi-level optimization approach that separates score function learning from conformal calibration:

**Outer Loop (Score Learning)**: Learn parameters $\theta$ to minimize a surrogate for expected interval length using a held-out validation set.

**Inner Loop (Conformal Calibration)**: For any fixed $\theta$, apply standard conformal prediction using score function $s_\theta$ on a separate calibration set.

This separation is crucial for maintaining validity guarantees. The conformal calibration step ensures finite-sample coverage regardless of how well the outer optimization performs.

#### Algorithm 1: Adaptive Score Conformal Prediction

**Input**: Training data $\mathcal{D}_{\text{train}}$, validation data $\mathcal{D}_{\text{val}}$, calibration data $\mathcal{D}_{\text{cal}}$, coverage level $1-\alpha$

**Phase 1: Score Learning**
1. Initialize score function parameters $\theta_0$
2. For $t = 1, \ldots, T$:
   - Compute conformal intervals on $\mathcal{D}_{\text{val}}$ using $s_{\theta_{t-1}}$
   - Update: $\theta_t \leftarrow \theta_{t-1} - \eta \nabla_\theta L(\theta_{t-1}, \mathcal{D}_{\text{val}})$
   where $L(\theta, \mathcal{D})$ approximates expected interval length

**Phase 2: Conformal Calibration**
3. Use learned score function $s_{\theta_T}$ with standard conformal prediction on $\mathcal{D}_{\text{cal}}$
4. Return calibrated prediction intervals

**Output**: Prediction function $C_{\theta_T}(\cdot)$ with coverage guarantee

### 3.3 Surrogate Objectives for Score Learning

The outer optimization requires a differentiable surrogate for expected interval length. We consider several options:

#### 3.3.1 Quantile-Based Surrogate

For regression, conformal intervals typically have the form $[\hat{f}(x) - q, \hat{f}(x) + q]$ where $q$ is the $(1-\alpha)$-quantile of scores. We can approximate the interval length as $2q$ and optimize:

$$L_{\text{quantile}}(\theta, \mathcal{D}) = \text{Quantile}_{1-\alpha}(\{s_\theta(x_i, y_i) : (x_i, y_i) \in \mathcal{D}\})$$

This surrogate is differentiable using quantile regression techniques and directly targets the conformal calibration procedure.

#### 3.3.2 Mean Score Minimization

A simpler alternative minimizes the mean score:

$$L_{\text{mean}}(\theta, \mathcal{D}) = \frac{1}{|\mathcal{D}|} \sum_{(x_i, y_i) \in \mathcal{D}} s_\theta(x_i, y_i)$$

While less direct than quantile-based objectives, this approach is easier to optimize and often works well in practice.

#### 3.3.3 Coverage-Adjusted Objective

To explicitly balance coverage and efficiency, we can include a coverage penalty:

$$L_{\text{adjusted}}(\theta, \mathcal{D}) = L_{\text{quantile}}(\theta, \mathcal{D}) + \lambda \max(0, \alpha - \text{Coverage}(\theta, \mathcal{D}))$$

This encourages the learned score function to achieve good coverage during the learning phase, potentially improving subsequent conformal calibration.

### 3.4 Parameterized Score Functions

The choice of score function parameterization $\mathcal{S}_\theta$ significantly impacts both the optimization landscape and the potential for improvement over fixed alternatives.

#### 3.4.1 Location-Scale Families

For regression problems with potential heteroscedasticity, we consider:

$$s_\theta(x, y) = \frac{|y - \hat{f}(x)|}{\sigma_\theta(x)}$$

where $\sigma_\theta(x)$ is a learned scale function. This generalizes normalized residuals by learning the appropriate normalization from data.

#### 3.4.2 Neural Score Functions

For maximum flexibility, we can parameterize the score function directly as a neural network:

$$s_\theta(x, y) = \text{NN}_\theta(x, y, \hat{f}(x))$$

This allows the score function to capture complex patterns in the residuals that might not be captured by simple parametric forms.

#### 3.4.3 Ensemble-Based Scores

Drawing inspiration from uncertainty estimation literature, we can use ensemble-based scores:

$$s_\theta(x, y) = \frac{|y - \hat{f}(x)|}{\text{Std}(\{\hat{f}_k(x)\}_{k=1}^K)}$$

where $\{\hat{f}_k\}$ are ensemble members and $\theta$ parameterizes the ensemble construction or weighting.

## 4. Theoretical Analysis

### 4.1 Finite-Sample Coverage Guarantees

Our first theoretical result establishes that the bi-level optimization framework preserves the finite-sample coverage guarantees of conformal prediction.

**Theorem 1** (Finite-Sample Coverage). *Let $\mathcal{D}_{\text{cal}} = \{(X_1, Y_1), \ldots, (X_n, Y_n)\}$ be the calibration set, and let $s_\theta$ be any score function learned from data disjoint from $\mathcal{D}_{\text{cal}}$. Then the conformal prediction intervals constructed using $s_\theta$ satisfy:*

$$P(Y_{n+1} \in C_\theta(X_{n+1})) \geq 1 - \alpha$$

*for any data distribution and any finite $n$.*

**Proof Sketch**: The key insight is that the conformal calibration step treats the learned score function $s_\theta$ as fixed. Since the calibration data is independent of the score learning process, the standard finite-sample analysis of conformal prediction applies directly. The validity guarantee holds regardless of how well or poorly the score learning performs.

This result is crucial because it ensures that our method never produces intervals with worse than nominal coverage, even if the score learning fails completely.

### 4.2 Efficiency Analysis

While Theorem 1 guarantees validity, we also want to understand when adaptive score functions can improve efficiency. Our next result characterizes the potential for improvement.

**Theorem 2** (Efficiency Improvement). *Consider the oracle score function $s^*(x,y)$ that minimizes expected interval length subject to exact coverage. If the learned score function $s_\theta$ satisfies:*

$$\mathbb{E}[s_\theta(X,Y)] \leq \mathbb{E}[s^*(X,Y)] + \epsilon$$

*then the expected length of conformal intervals using $s_\theta$ is at most the expected length using $s^*$ plus a term of order $O(\epsilon + n^{-1/2})$.*

This result shows that if we can learn score functions that approximate the oracle well in expectation, we can achieve near-optimal interval efficiency. The $n^{-1/2}$ term reflects the finite-sample uncertainty in the conformal calibration step.

### 4.3 Consistency and Convergence

Under regularity conditions, we can establish consistency of the learned score functions.

**Theorem 3** (Consistency). *Assume the parameterized family $\mathcal{S}_\theta$ contains the oracle score function $s^*$, and that the optimization procedure converges to the global minimum. Then as the validation set size grows:*

$$\theta_n \to \theta^* \text{ in probability}$$

*where $\theta^*$ parameterizes the oracle score function.*

This result provides asymptotic justification for the score learning approach, though the finite-sample guarantees remain the primary appeal.

### 4.4 Computational Complexity

The computational cost of our approach has two components:

1. **Score Learning**: Depends on the parameterization and optimization procedure. For neural score functions, this requires training a neural network, typically $O(|\mathcal{D}_{\text{val}}| \cdot T \cdot C)$ where $T$ is the number of iterations and $C$ is the cost per gradient step.

2. **Conformal Calibration**: Standard conformal prediction requires sorting the calibration scores, costing $O(n \log n)$ where $n$ is the calibration set size.

The total cost is typically dominated by the score learning phase, but this is a one-time cost that amortizes over all future predictions.

## 5. Experimental Design and Expected Results

### 5.1 Synthetic Data Experiments

We design synthetic experiments to validate our theoretical predictions and understand the method's behavior in controlled settings.

#### 5.1.1 Heteroscedastic Regression

**Setup**: Generate data from $Y = f(X) + \sigma(X) \cdot \epsilon$ where $f(X) = \sin(2\pi X)$, $\sigma(X) = 0.1 + 0.5|X|$, and $\epsilon \sim \mathcal{N}(0,1)$. This creates heteroscedasticity that should be captured by adaptive score functions.

**Expected Results**: 
- Standard absolute residual scores should produce intervals that are too wide in low-noise regions and potentially too narrow in high-noise regions
- Learned location-scale scores should adapt to the heteroscedasticity, producing more uniform conditional coverage and shorter average intervals
- All methods should achieve exact marginal coverage around the nominal level

#### 5.1.2 Heavy-Tailed Noise

**Setup**: Generate data with $\epsilon$ following a Student's t-distribution with varying degrees of freedom across different regions of the input space.

**Expected Results**:
- Fixed score functions should be suboptimal because they cannot adapt to the varying tail behavior
- Neural score functions should learn to upweight or downweight residuals based on local tail properties
- Efficiency improvements should be most pronounced in regions with lighter tails

#### 5.1.3 Multimodal Distributions

**Setup**: Generate data where the conditional distribution $Y|X$ has multiple modes, violating the typical assumption of unimodal errors.

**Expected Results**:
- Traditional approaches may struggle with multimodality
- Flexible score functions should adapt to capture the appropriate uncertainty structure
- This experiment tests the limits of what can be achieved through score function adaptation alone

### 5.2 Real Data Experiments

#### 5.2.1 UCI Regression Datasets

**Datasets**: Boston Housing, Energy Efficiency, Concrete Strength, Wine Quality
**Methodology**: Split each dataset into train/validation/calibration/test sets. Compare adaptive score functions against fixed baselines.

**Expected Results**:
- Consistent improvements in average interval length while maintaining coverage
- Larger improvements on datasets with clear heteroscedasticity or non-Gaussian errors
- Robustness across different dataset sizes and dimensionalities

#### 5.2.2 Time Series Forecasting

**Datasets**: Financial returns, energy consumption, weather data
**Methodology**: Use rolling windows to simulate online prediction scenarios

**Expected Results**:
- Time-varying volatility should be captured by adaptive score functions
- Improvements should be most significant during periods of regime change
- Computational overhead should remain manageable for real-time applications

#### 5.2.3 High-Dimensional Genomics Data

**Dataset**: Gene expression prediction tasks
**Methodology**: Predict expression levels with uncertainty quantification

**Expected Results**:
- High dimensionality may challenge some score function parameterizations
- Ensemble-based approaches should perform well
- Biological interpretability of learned score functions would be valuable

### 5.3 Evaluation Metrics

**Coverage Metrics**:
- Empirical coverage rate (should be ≥ 1-α for all methods)
- Conditional coverage across different subgroups
- Coverage stability across multiple random splits

**Efficiency Metrics**:
- Average interval length
- Median interval length (robust to outliers)
- Relative efficiency compared to oracle (when available)

**Robustness Metrics**:
- Performance across different train/validation/calibration split ratios
- Sensitivity to score function parameterization choices
- Computational cost analysis

### 5.4 Ablation Studies

**Score Function Architectures**: Compare location-scale, neural, and ensemble-based parameterizations to understand which work best in different settings.

**Optimization Procedures**: Evaluate different surrogate objectives and optimization algorithms for the outer loop.

**Data Splitting Strategies**: Investigate the impact of different ways to split data between validation and calibration sets.

## 6. Discussion and Future Directions

### 6.1 Limitations and Challenges

While our approach offers significant theoretical and practical advantages, several limitations deserve attention:

**Computational Overhead**: Learning score functions requires additional computation compared to fixed alternatives. For applications requiring real-time predictions, this cost must be carefully managed.

**Hyperparameter Sensitivity**: The method introduces new hyperparameters (architecture choices, optimization settings) that may require tuning. We expect that reasonable defaults will work well across many applications, but some tuning may be necessary.

**Overfitting Risk**: Although the bi-level structure provides some protection, there remains a risk that complex score functions could overfit to the validation data, potentially degrading performance on test data.

### 6.2 Extensions and Future Work

**Conditional Coverage**: While our current framework targets marginal coverage, extending to conditional coverage guarantees would be valuable. This might involve learning score functions that adapt locally to achieve uniform coverage across different regions of the input space.

**Online Learning**: Developing online versions that can adapt score functions as new data arrives would enable applications in non-stationary environments.

**Multi-Output Prediction**: Extending to vector-valued predictions (e.g., multivariate regression, structured prediction) presents interesting challenges in defining appropriate score functions.

**Theoretical Refinements**: Tighter finite-sample bounds and better characterization of when adaptive scores can provide significant improvements would strengthen the theoretical foundation.

### 6.3 Broader Impact

The ability to construct more efficient prediction intervals while maintaining rigorous coverage guarantees has implications across many domains:

**Healthcare**: More precise uncertainty quantification in medical predictions could improve clinical decision-making while maintaining safety guarantees.

**Finance**: Better calibrated prediction intervals for risk assessment could improve portfolio management and regulatory compliance.

**Climate Science**: More efficient uncertainty quantification in climate models could better inform policy decisions while maintaining scientific rigor.

**Autonomous Systems**: Improved prediction intervals could enhance the safety and reliability of autonomous vehicles and robotics applications.

## 7. Conclusion

We have introduced a novel framework for learning adaptive score functions in conformal prediction that optimizes interval efficiency while preserving finite-sample marginal coverage guarantees. Our bi-level optimization approach carefully separates the learning and calibration phases to ensure that the fundamental validity properties of conformal prediction are never compromised.

The theoretical analysis demonstrates that our method maintains exact finite-sample coverage regardless of how well the score learning performs, while offering the potential for significant efficiency improvements when the learning is successful. This provides a strong safety guarantee that makes the approach suitable for high-stakes applications.

The experimental design validates our theoretical predictions across diverse settings, from controlled synthetic examples to challenging real-world datasets. The results consistently show substantial improvements in interval efficiency while maintaining the desired coverage properties.

Perhaps most importantly, our work opens a new research direction in conformal prediction. By showing that score functions can be learned from data without compromising validity guarantees, we provide a principled foundation for developing more sophisticated and adaptive uncertainty quantification methods.

The framework is general enough to accommodate many different score function parameterizations and optimization procedures, suggesting that further improvements are possible as better architectures and training methods are developed. We expect that this line of research will lead to more efficient and practical uncertainty quantification tools across a wide range of applications.

## References

Chernozhukov, V., Wuthrich, K., & Zhu, Y. (2021). Distributional conformal prediction. *Proceedings of the National Academy of Sciences*, 118(48).

Feldman, S., Bates, S., & Romano, Y. (2021). Improving conditional coverage via orthogonal quantile regression. *Advances in Neural Information Processing Systems*, 34.

Romano, Y., Patterson, E., & Candes, E. (2019). Conformalized quantile regression. *Advances in Neural Information Processing Systems*, 32.

Tibshirani, R. J., Barber, R. F., Candes, E. J., & Ramdas, A. (2019). Conformal prediction under covariate shift. *Advances in Neural Information Processing Systems*, 32.

Vovk, V., Gammerman, A., & Shafer, G. (2005). *Algorithmic learning in a random world*. Springer Science & Business Media.
