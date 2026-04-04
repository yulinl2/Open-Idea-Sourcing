# Reconstruction: full_guided
**Paper:** 2602.04770  
**Condition:** no_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Learning Optimal Score Functions for Efficient Conformal Prediction

## Abstract

Conformal prediction provides finite-sample coverage guarantees for prediction intervals, but the efficiency of these intervals depends critically on the choice of score function used to measure prediction uncertainty. Existing methods either use fixed score functions that may be suboptimal for specific datasets, or lack theoretical guarantees when learning adaptive scores. We propose a novel framework for learning optimal score functions that minimizes expected interval width while maintaining finite-sample marginal coverage guarantees. Our approach combines empirical risk minimization over a restricted function class with a calibration step that ensures validity. We establish theoretical consistency results showing that our learned score functions converge to the optimal conditional quantile-based scores under mild regularity conditions. The method is computationally efficient, requiring only standard optimization techniques, and can be applied with any base predictor. Our framework bridges the gap between the statistical rigor of conformal prediction and the adaptivity needed for practical efficiency.

## 1. Introduction

Prediction intervals that provide uncertainty quantification are crucial in high-stakes applications such as medical diagnosis, autonomous driving, and financial risk assessment. While point predictions may suffice for some tasks, decision-makers often require probabilistic guarantees about prediction reliability. The challenge lies in constructing intervals that are both statistically valid—containing the true outcome with a specified probability—and practically useful through minimal width.

Conformal prediction has emerged as a powerful framework for constructing prediction intervals with finite-sample marginal coverage guarantees. Unlike asymptotic methods that rely on large-sample approximations, conformal prediction provides exact coverage for any finite sample size and any underlying data distribution. The key insight is to use past prediction errors, measured by a score function, to calibrate the width of future prediction intervals.

However, the efficiency of conformal prediction intervals depends heavily on the choice of score function. Most existing approaches use simple, fixed score functions such as absolute residuals or quantile-based scores. While these choices are reasonable defaults, they may be far from optimal for specific datasets or prediction tasks. Recent work has begun exploring adaptive score functions, but existing methods either lack theoretical guarantees or require restrictive assumptions about the data distribution.

**Our contributions are:**
• We formalize the problem of learning optimal score functions for conformal prediction as a constrained optimization problem that minimizes expected interval width subject to coverage constraints
• We propose a practical two-stage algorithm that learns score functions via empirical risk minimization followed by conformal calibration
• We establish theoretical consistency guarantees showing convergence to optimal conditional quantile-based scores under regularity conditions
• We provide finite-sample analysis of our method's coverage and efficiency properties
• We demonstrate how our framework can incorporate various function classes and base predictors while maintaining computational tractability

## 2. Related Work

**Conformal Prediction.** The conformal prediction framework was introduced by Vovk et al. and provides distribution-free coverage guarantees for prediction intervals. The standard approach uses a fixed score function to measure prediction uncertainty, with common choices including absolute residuals for regression and margin-based scores for classification. Recent extensions have explored exchangeable sequences, conditional coverage, and online settings.

**Adaptive Score Functions.** Several recent works have investigated learning or adapting score functions in conformal prediction. Conformalized quantile regression learns conditional quantiles directly but requires specific model architectures. Other approaches have explored using auxiliary information or meta-learning to adapt scores, but these methods often lack theoretical guarantees or require strong distributional assumptions.

**Efficient Conformal Methods.** Research on improving conformal prediction efficiency has focused on several directions: conditional coverage methods that provide validity for subgroups, locally adaptive approaches that adjust intervals based on input features, and ensemble methods that combine multiple score functions. However, most work treats the score function as fixed rather than learnable.

**Quantile Regression and Uncertainty Quantification.** Our work connects to the broader literature on quantile regression and probabilistic forecasting. While these methods can produce prediction intervals, they typically lack the finite-sample guarantees of conformal prediction. Recent work has explored combining quantile methods with conformal calibration.

**Gap Identification.** Existing methods face a fundamental trade-off: fixed score functions provide theoretical guarantees but may be inefficient, while adaptive methods can improve efficiency but often sacrifice validity guarantees. Our work fills this gap by providing a principled framework for learning score functions that maintains the finite-sample coverage properties of conformal prediction while optimizing for efficiency.

## 3. Problem Formulation

Let $(X_1, Y_1), \ldots, (X_n, Y_n)$ be training data where $X_i \in \mathcal{X}$ are features and $Y_i \in \mathbb{R}$ are responses. We have a base predictor $\hat{f}: \mathcal{X} \to \mathbb{R}$ trained on this data. For a new test point $X_{n+1}$, we want to construct a prediction interval $C_\alpha(X_{n+1})$ such that:

$$\mathbb{P}(Y_{n+1} \in C_\alpha(X_{n+1})) \geq 1 - \alpha$$

for a specified miscoverage level $\alpha \in (0, 1)$.

**Score Functions.** A score function $s: \mathcal{X} \times \mathbb{R} \times \mathbb{R} \to \mathbb{R}_+$ measures the "badness" of predicting $\hat{y}$ when the true value is $y$ for input $x$. Common choices include:
- Absolute residual: $s(x, y, \hat{y}) = |y - \hat{y}|$
- Quantile-based: $s(x, y, \hat{y}) = \max(\alpha(y - \hat{y}), (1-\alpha)(\hat{y} - y))$

**Conformal Prediction Intervals.** Given a score function $s$ and significance level $\alpha$, conformal prediction constructs intervals as:

1. Compute scores on calibration data: $S_i = s(X_i, Y_i, \hat{f}(X_i))$ for $i \in I_{cal}$
2. Find the $(1-\alpha)$-quantile: $q = \text{Quantile}_{1-\alpha}(\{S_i\}_{i \in I_{cal}})$  
3. Prediction interval: $C_\alpha(x) = \{y : s(x, y, \hat{f}(x)) \leq q\}$

**Optimization Objective.** We want to learn a score function $s_\theta$ parameterized by $\theta$ that minimizes expected interval width:

$$\min_\theta \mathbb{E}[|C_\alpha(X)|]$$

subject to the constraint that $\mathbb{P}(Y \in C_\alpha(X)) \geq 1 - \alpha$ for all distributions.

**Function Class.** We restrict our attention to score functions in a class $\mathcal{S}$ that ensures:
1. **Validity**: The resulting intervals achieve finite-sample coverage
2. **Computability**: The intervals $C_\alpha(x)$ can be computed efficiently
3. **Learnability**: The class has bounded complexity for generalization

## 4. Methodology

We propose a two-stage approach: first learn a score function to minimize interval width, then apply conformal calibration to ensure coverage.

### 4.1 Stage 1: Score Function Learning

We parameterize score functions as $s_\theta(x, y, \hat{y})$ where $\theta$ are learnable parameters. To ensure computability, we focus on the class:

$$s_\theta(x, y, \hat{y}) = g_\theta(x, y - \hat{y})$$

where $g_\theta: \mathcal{X} \times \mathbb{R} \to \mathbb{R}_+$ is a neural network that takes features $x$ and residual $r = y - \hat{y}$ as input.

**Training Objective.** We minimize a surrogate for expected interval width. For a given score function, the interval width at point $x$ with prediction $\hat{y}$ is approximately:

$$W_\theta(x, \hat{y}) = \sup\{y_+ - y_- : s_\theta(x, y_-, \hat{y}) = s_\theta(x, y_+, \hat{y}) = q\}$$

Since computing this exactly is intractable, we use the approximation:

$$\hat{W}_\theta(x, \hat{y}) = 2 \cdot s_\theta^{-1}(x, q, \hat{y})$$

where $s_\theta^{-1}(x, q, \hat{y})$ is the inverse function giving the residual $r$ such that $s_\theta(x, r, 0) = q$.

**Empirical Risk Minimization.** We minimize:

$$\hat{L}(\theta) = \frac{1}{|I_{train}|} \sum_{i \in I_{train}} \hat{W}_\theta(X_i, \hat{f}(X_i))$$

with regularization to prevent overfitting:

$$\min_\theta \hat{L}(\theta) + \lambda R(\theta)$$

### 4.2 Stage 2: Conformal Calibration

After learning $\theta^*$, we apply standard conformal prediction:

1. Compute scores on held-out calibration set: $S_i = s_{\theta^*}(X_i, Y_i, \hat{f}(X_i))$
2. Find quantile: $q_{1-\alpha} = \text{Quantile}_{1-\alpha}(\{S_i\})$
3. Prediction intervals: $C_\alpha(x) = \{y : s_{\theta^*}(x, y, \hat{f}(x)) \leq q_{1-\alpha}\}$

### 4.3 Algorithm

```
Algorithm: Learned Conformal Prediction
Input: Data (X,Y), base predictor f̂, significance α
Split data: I_train, I_cal, I_test

// Stage 1: Learn score function
Initialize θ
for epoch in 1...E:
    Sample batch from I_train
    Compute loss L̂(θ) + λR(θ)  
    Update θ via gradient descent
θ* ← final parameters

// Stage 2: Conformal calibration  
S ← [s_θ*(Xi, Yi, f̂(Xi)) for i in I_cal]
q ← Quantile_{1-α}(S)

// Prediction
for test point x:
    return C_α(x) = {y : s_θ*(x, y, f̂(x)) ≤ q}
```

### 4.4 Design Justifications

**Two-stage approach**: Separating learning from calibration allows us to optimize for efficiency while preserving finite-sample guarantees through the conformal step.

**Function class choice**: The form $g_\theta(x, y - \hat{y})$ ensures that intervals are symmetric around the base prediction when appropriate, while allowing asymmetry to be learned from data.

**Surrogate objective**: The width approximation $\hat{W}_\theta$ provides a differentiable proxy for the true interval width, enabling gradient-based optimization.

## 5. Theoretical Analysis

### 5.1 Finite-Sample Coverage Guarantee

**Theorem 1** (Coverage Validity): Under exchangeability of $(X_1, Y_1), \ldots, (X_{n+1}, Y_{n+1})$, our method achieves:

$$\mathbb{P}(Y_{n+1} \in C_\alpha(X_{n+1})) \geq 1 - \alpha$$

for any learned score function $s_{\theta^*}$.

*Proof Sketch*: This follows directly from the conformal prediction guarantee. The calibration step ensures that regardless of the learned score function, the resulting intervals have valid coverage. The key insight is that Stage 2 treats the learned score as fixed and applies standard conformal calibration.

### 5.2 Consistency Analysis

We establish that under regularity conditions, our learned score functions converge to optimal conditional quantile-based scores.

**Assumption 1**: The optimal score function $s^*(x, y, \hat{y}) = |y - Q_{1-\alpha/2}(Y|X=x)| \vee |y - Q_{\alpha/2}(Y|X=x)|$ lies in the closure of our function class.

**Assumption 2**: The function class $\mathcal{S}$ has finite Rademacher complexity.

**Theorem 2** (Consistency): Under Assumptions 1-2, as $n \to \infty$:

$$\mathbb{E}[|C_\alpha(X)|] - \mathbb{E}[|C^*_\alpha(X)|] \to 0$$

where $C^*_\alpha$ are intervals based on the optimal score function.

*Proof Sketch*: The proof follows standard empirical risk minimization theory. The key steps are: (1) showing that our surrogate loss converges to the true expected width, (2) applying uniform convergence results for our function class, and (3) establishing that the optimal score corresponds to conditional quantiles.

### 5.3 Computational Complexity

**Proposition 1**: For neural network score functions with $p$ parameters, each training iteration requires $O(np)$ time where $n$ is the training set size. Inference requires $O(p + \log |I_{cal}|)$ time per prediction.

The computational cost is comparable to training any neural network, with the additional overhead of quantile computation during calibration.

## 6. Experimental Design

### 6.1 Datasets

We would evaluate on diverse regression benchmarks:

**Synthetic Data**: 
- Linear regression with heteroscedastic noise to test adaptation to varying uncertainty
- Nonlinear functions with different noise patterns (e.g., input-dependent variance)
- Multi-modal distributions to test robustness

**Real Datasets**:
- UCI regression datasets (Boston Housing, Energy Efficiency, Concrete Strength)
- Time series data (stock prices, weather forecasting) 
- High-dimensional data (gene expression, image regression tasks)
- Datasets with natural heteroscedasticity (e.g., financial data)

### 6.2 Baselines

**Fixed Score Functions**:
- Absolute residual: $s(x,y,\hat{y}) = |y - \hat{y}|$
- Quantile-based score with fixed quantiles
- Squared residual for Gaussian assumptions

**Adaptive Methods**:
- Conformalized quantile regression 
- Locally adaptive conformal prediction
- Ensemble conformal methods
- Meta-learning approaches for score adaptation

**Oracle Methods**:
- True conditional quantiles (when available in synthetic settings)
- Cross-validation optimized fixed scores

### 6.3 Evaluation Metrics

**Coverage**: Empirical coverage rate $\frac{1}{m}\sum_{i=1}^m \mathbf{1}[Y_i \in C_\alpha(X_i)]$ should be $\geq 1-\alpha$.

**Efficiency**: 
- Average interval width: $\frac{1}{m}\sum_{i=1}^m |C_\alpha(X_i)|$
- Relative efficiency vs. baselines
- Width as function of confidence level

**Robustness**:
- Coverage across different subgroups/quantiles of the data
- Performance under distribution shift
- Sensitivity to hyperparameter choices

### 6.4 Ablation Studies

**Architecture Choices**:
- Effect of network depth/width for $g_\theta$
- Different input representations (raw residuals vs. normalized)
- Comparison of different regularization schemes

**Training Procedures**:
- Impact of train/calibration split ratio
- Effect of surrogate loss approximation quality
- Comparison with end-to-end vs. two-stage training

**Function Class Variations**:
- Asymmetric vs. symmetric score functions
- Linear vs. nonlinear parameterizations
- Incorporating additional features beyond residuals

### 6.5 Computational Experiments

**Scalability**: Test on datasets of varying size (10³ to 10⁶ samples) to evaluate computational scaling.

**Convergence**: Analyze training dynamics and convergence properties of the optimization procedure.

**Hyperparameter Sensitivity**: Grid search over key hyperparameters (learning rate, regularization, network architecture) to assess robustness.

## 7. Discussion

### 7.1 Expected Strengths

**Theoretical Rigor**: Our two-stage approach maintains the finite-sample coverage guarantees that make conformal prediction attractive while optimizing for efficiency. This addresses a key limitation of purely adaptive methods that may sacrifice validity.

**Practical Flexibility**: The framework can incorporate different base predictors, function classes, and regularization schemes. This modularity makes it applicable across diverse domains and prediction tasks.

**Empirical Efficiency**: By learning from data rather than using fixed scores, we expect significant improvements in interval width, especially on datasets with heteroscedastic noise or complex uncertainty patterns.

### 7.2 Potential Limitations

**Computational Overhead**: Learning score functions requires additional training time and hyperparameter tuning compared to fixed-score conformal prediction. The benefit-cost trade-off may not be favorable for small datasets or simple prediction tasks.

**Generalization Concerns**: Like any learned component, score functions may overfit to training data. While our theoretical analysis suggests consistency, finite-sample performance depends on careful regularization and validation.

**Interval Computation**: For complex learned score functions, computing the prediction intervals $\{y : s_\theta(x,y,\hat{y}) \leq q\}$ may require numerical optimization rather than closed-form solutions.

**Distribution Shift**: Learned score functions may be less robust to distribution shift compared to simple, fixed alternatives. The method's performance when training and test distributions differ requires careful evaluation.

### 7.3 Broader Impact

**Methodological Contributions**: Our framework provides a principled way to combine the statistical rigor of conformal prediction with modern machine learning's adaptivity. This could influence broader research on uncertainty quantification methods.

**Application Domains**: Improved prediction intervals could have significant impact in high-stakes applications like medical diagnosis, autonomous systems, and financial risk management where both validity and efficiency matter.

**Computational Considerations**: The method's computational requirements may limit adoption in resource-constrained settings, highlighting the need for efficient implementations and approximations.

## 8. Conclusion

We have proposed a novel framework for learning optimal score functions in conformal prediction that achieves finite-sample coverage guarantees while minimizing expected interval width. Our two-stage approach separates the learning of efficient score functions from the calibration step that ensures validity, providing both theoretical guarantees and practical flexibility.

The key contributions include: (1) a principled formulation of score function learning as constrained optimization, (2) a practical algorithm that combines empirical risk minimization with conformal calibration, (3) theoretical consistency results showing convergence to optimal conditional quantile-based scores, and (4) finite-sample coverage guarantees that preserve the fundamental appeal of conformal prediction.

**Open Questions**: Several important directions remain for future work. First, developing more sophisticated function classes and training procedures that can better capture complex uncertainty patterns. Second, extending the framework to conditional coverage guarantees that provide validity for specific subgroups. Third, investigating the robustness of learned score functions under distribution shift and adversarial perturbations. Finally, developing efficient approximation methods for computing prediction intervals with complex learned score functions.

Our work demonstrates that the statistical rigor of conformal prediction need not come at the cost of efficiency, opening new avenues for practical uncertainty quantification in machine learning applications.

## References

[Note: As no specific references were provided, this section would typically include citations to foundational work on conformal prediction (Vovk et al.), recent advances in adaptive conformal methods, quantile regression literature, and related uncertainty quantification approaches. The format would follow standard academic conventions.]
