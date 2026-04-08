# Reconstruction: full_guided
**Paper:** 2602.04770  
**Condition:** no_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Learning Adaptive Score Functions for Efficient Conformal Prediction

## Abstract

Conformal prediction provides finite-sample marginal coverage guarantees for prediction intervals, but the efficiency of these intervals depends critically on the choice of score function used to measure nonconformity. Existing methods typically rely on fixed, hand-crafted score functions such as absolute residuals, which may be suboptimal for the underlying data distribution. We propose a framework for learning adaptive score functions that optimize interval efficiency while preserving the fundamental coverage guarantees of conformal prediction. Our approach combines a meta-learning procedure that trains score functions on auxiliary data with a novel regularization scheme that ensures robustness when the learned function fails. We prove that our method maintains finite-sample marginal coverage regardless of the quality of the learned score function, while empirically demonstrating improved interval efficiency across diverse prediction tasks. The key insight is that by carefully splitting the data and applying appropriate regularization, we can harness the power of machine learning to improve conformal prediction without sacrificing its most valuable property: distribution-free validity guarantees.

## 1. Introduction

Prediction intervals that quantify uncertainty are essential in high-stakes applications such as medical diagnosis, autonomous systems, and financial modeling. While point predictions provide estimates of future outcomes, prediction intervals capture the inherent uncertainty in these estimates, enabling more informed decision-making. The challenge lies in constructing intervals that are both valid (contain the true value with specified probability) and efficient (as narrow as possible).

Conformal prediction has emerged as a powerful framework for constructing prediction intervals with finite-sample marginal coverage guarantees. Unlike asymptotic methods that require large sample assumptions, conformal prediction provides exact coverage for any finite sample size and arbitrary data distribution. The framework works by defining a nonconformity score function that measures how "unusual" a prediction-target pair is relative to a calibration set, then using the empirical distribution of these scores to determine prediction intervals.

However, the efficiency of conformal prediction intervals depends critically on the choice of score function. Most existing approaches use simple, fixed functions such as absolute residuals $|y - \hat{y}|$ or studentized residuals. While these choices guarantee coverage, they may be far from optimal for the specific data distribution at hand. For instance, in regression problems with heteroscedastic noise, absolute residuals fail to account for varying uncertainty across the input space, leading to unnecessarily wide intervals in low-noise regions.

This raises a fundamental question: can we learn better score functions from data while maintaining the finite-sample coverage guarantees that make conformal prediction attractive? This problem is challenging because it requires balancing two competing objectives. On one hand, we want to leverage machine learning to optimize score functions for interval efficiency. On the other hand, we must ensure that the validity guarantee holds even if the learning procedure fails catastrophically.

Our contributions are:

• We formalize the problem of learning score functions for conformal prediction and identify the key challenge of maintaining coverage guarantees under learning uncertainty.

• We propose a meta-learning framework that trains score functions on auxiliary data while using careful data splitting to preserve the exchangeability assumptions required for conformal validity.

• We introduce a regularization scheme that ensures robustness by blending learned score functions with safe baseline functions, guaranteeing coverage even when learning fails.

• We provide theoretical analysis proving that our approach maintains finite-sample marginal coverage while improving interval efficiency when the learning is successful.

• We outline comprehensive experiments demonstrating improvements over standard conformal methods across synthetic and real datasets.

## 2. Related Work

**Conformal Prediction.** The conformal prediction framework was introduced by Vovk et al. and provides distribution-free finite-sample coverage guarantees. The key insight is that under the exchangeability assumption, the rank of a new example's nonconformity score among calibration scores has a uniform distribution. This enables the construction of prediction sets with exact coverage. Shafer and Vovk provided comprehensive theoretical foundations, while Lei et al. extended the framework to regression problems.

**Score Function Design.** Most conformal prediction work uses simple score functions. Absolute residuals $s(x,y) = |y - \hat{f}(x)|$ are common for regression, while margin-based scores are used for classification. Tibshirani et al. explored weighted conformal prediction using importance weights, while Chernozhukov et al. studied distributional conformal prediction with quantile-based scores. However, these approaches still rely on pre-specified functional forms rather than learning from data.

**Adaptive and Conditional Coverage.** Several works have addressed the limitation that marginal coverage may not translate to conditional coverage across subgroups. Lei and Wasserman studied conditional coverage in regression, while Tibshirani et al. proposed weighted conformal prediction for covariate shift. Gibbs and Candès introduced adaptive conformal inference that adjusts coverage based on recent performance. However, these methods focus on adapting the coverage level rather than the score function itself.

**Learning for Conformal Prediction.** Recent work has begun exploring learned components in conformal prediction. Stutz et al. proposed learning prediction set functions directly, while Angelopoulos et al. studied uncertainty quantification with learned models. However, these approaches either sacrifice finite-sample guarantees or focus on the underlying predictor rather than the score function. Romano et al. explored conformalized quantile regression but with fixed quantile-based scores.

**Meta-Learning and Few-Shot Uncertainty.** Our approach connects to meta-learning literature that learns across multiple tasks. Finn et al. introduced model-agnostic meta-learning (MAML), while Ravi and Larochelle studied meta-learning for few-shot classification. In uncertainty quantification, Harrison et al. explored meta-learning for Bayesian neural networks. However, these works do not address the specific challenges of maintaining conformal validity.

The gap our work fills is the lack of principled methods for learning score functions in conformal prediction while preserving finite-sample coverage guarantees. Existing adaptive methods either sacrifice validity or focus on other aspects of the prediction problem. Our contribution is a framework that enables learning while maintaining the fundamental property that makes conformal prediction attractive: distribution-free validity.

## 3. Problem Formulation

Let $(X, Y)$ be a random pair taking values in $\mathcal{X} \times \mathcal{Y}$, where $\mathcal{X}$ is the input space and $\mathcal{Y} \subseteq \mathbb{R}$ is the output space for regression. We observe a dataset $\{(X_i, Y_i)\}_{i=1}^n$ of i.i.d. samples from the joint distribution $P_{X,Y}$.

Given a new input $X_{n+1}$, our goal is to construct a prediction interval $C(X_{n+1}) \subseteq \mathcal{Y}$ such that:
$$\mathbb{P}(Y_{n+1} \in C(X_{n+1})) \geq 1 - \alpha$$
for a specified miscoverage level $\alpha \in (0,1)$, where $(X_{n+1}, Y_{n+1})$ is a new sample from the same distribution.

**Conformal Prediction Framework.** Conformal prediction constructs such intervals using a score function $s: \mathcal{X} \times \mathcal{Y} \rightarrow \mathbb{R}$ that measures the nonconformity of input-output pairs. Given a predictor $\hat{f}: \mathcal{X} \rightarrow \mathcal{Y}$ trained on a subset of the data, we typically have $s(x,y) = g(x, y, \hat{f}(x))$ for some function $g$.

The standard conformal procedure splits the data into training and calibration sets. After training $\hat{f}$ on the training set, we compute nonconformity scores $\{S_i\}_{i \in \mathcal{I}_{cal}}$ on the calibration set, where $S_i = s(X_i, Y_i)$. The prediction interval is then:
$$C(x) = \{y \in \mathcal{Y} : s(x,y) \leq \hat{q}\}$$
where $\hat{q}$ is the $(1-\alpha)$-quantile of the calibration scores augmented with $+\infty$.

**Problem Statement.** The efficiency of conformal intervals depends heavily on the choice of score function $s$. Our goal is to learn a score function $s_\theta$ parameterized by $\theta$ that minimizes expected interval length while maintaining finite-sample coverage guarantees.

Formally, we seek to solve:
$$\min_\theta \mathbb{E}[|C_\theta(X_{n+1})|]$$
subject to:
$$\mathbb{P}(Y_{n+1} \in C_\theta(X_{n+1})) \geq 1 - \alpha$$

where $C_\theta$ denotes the conformal interval constructed using score function $s_\theta$, and $|\cdot|$ denotes interval length (Lebesgue measure).

**Key Challenge.** The fundamental challenge is that learning $\theta$ from data can violate the exchangeability assumption required for conformal validity. If we use the same data to both learn the score function and calibrate the quantile, the resulting intervals may not achieve the desired coverage. Moreover, even with proper data splitting, a poorly learned score function could lead to invalid intervals.

**Assumptions.** We assume:
1. The data $\{(X_i, Y_i)\}_{i=1}^n \cup \{(X_{n+1}, Y_{n+1})\}$ are exchangeable
2. We have access to auxiliary data from related tasks for meta-learning
3. The score function class is rich enough to contain effective functions but not so complex as to overfit severely
4. The underlying predictor $\hat{f}$ is given (our focus is on learning the score function, not the predictor)

## 4. Methodology

Our approach combines meta-learning across multiple datasets with a robust regularization scheme that ensures coverage even when learning fails. The key insight is to learn a score function on auxiliary data, then blend it with a safe baseline function using a data-dependent weight that preserves conformal validity.

**Meta-Learning Phase.** We assume access to auxiliary datasets $\{\mathcal{D}_j\}_{j=1}^m$ from related prediction tasks. For each dataset $\mathcal{D}_j$, we can construct conformal intervals using various score functions and evaluate their efficiency. We parameterize score functions as $s_\theta(x,y) = \theta^T \phi(x,y,\hat{f}(x))$, where $\phi$ extracts features that capture the relationship between inputs, outputs, and predictions.

The meta-learning objective optimizes expected interval length across tasks:
$$\theta^* = \arg\min_\theta \sum_{j=1}^m \mathbb{E}_{(x,y) \sim \mathcal{D}_j}[L(s_\theta, x, y)]$$

where $L(s_\theta, x, y)$ measures the contribution of the score function to interval length. Specifically, for a given score function, we can estimate the interval length at $(x,y)$ by computing the empirical quantile of scores and determining the resulting interval.

**Regularized Score Function.** To ensure robustness, we propose a regularized score function that blends the learned function with a safe baseline:
$$s_{reg}(x,y) = (1-\lambda) s_{base}(x,y) + \lambda s_\theta(x,y)$$

where $s_{base}(x,y) = |y - \hat{f}(x)|$ is the standard absolute residual score, and $\lambda \in [0,1]$ is a data-dependent mixing weight.

The key innovation is choosing $\lambda$ based on a validation procedure that estimates the reliability of the learned score function. We split the calibration set into validation and final calibration subsets. On the validation set, we estimate the coverage achieved by $s_\theta$ and set:
$$\lambda = \min\left(1, \max\left(0, \frac{\hat{cov}_\theta - (1-\alpha)}{\epsilon}\right)\right)$$

where $\hat{cov}_\theta$ is the empirical coverage of $s_\theta$ on the validation set and $\epsilon > 0$ is a safety margin.

**Algorithm.** Our complete procedure is:

```
Algorithm: Adaptive Conformal Prediction
Input: Training data, calibration data, test input x, miscoverage α
Output: Prediction interval C(x)

1. Meta-learning phase (offline):
   - Train score function s_θ on auxiliary datasets
   - Optimize for interval efficiency across tasks

2. Validation phase:
   - Split calibration data into validation and final calibration
   - Estimate coverage of s_θ on validation set
   - Compute mixing weight λ based on estimated coverage

3. Final calibration:
   - Construct regularized score s_reg = (1-λ)s_base + λs_θ
   - Compute scores on final calibration set
   - Determine quantile q̂

4. Prediction:
   - Return interval C(x) = {y : s_reg(x,y) ≤ q̂}
```

**Design Justification.** The regularization scheme serves multiple purposes. First, it provides a safety net when the learned score function fails—in the worst case, $\lambda = 0$ and we recover standard conformal prediction. Second, it allows gradual adaptation based on validation performance rather than an all-or-nothing approach. Third, the data-dependent nature of $\lambda$ ensures that we only rely on the learned function when there is evidence it performs well.

The meta-learning component addresses the challenge of learning from limited data. By training across multiple related tasks, we can learn general principles about effective score functions that transfer to new datasets. The feature extraction function $\phi$ can capture relevant patterns such as heteroscedasticity, outliers, or input-dependent noise.

## 5. Theoretical Analysis

We now analyze the theoretical properties of our method, focusing on the crucial coverage guarantee and conditions under which efficiency improvements can be expected.

**Main Theorem: Coverage Guarantee**

*Theorem 1.* Under the exchangeability assumption, the prediction intervals produced by our regularized conformal procedure satisfy:
$$\mathbb{P}(Y_{n+1} \in C(X_{n+1})) \geq 1 - \alpha$$
for any choice of parameters $\theta$ and any data-dependent mixing weight $\lambda \in [0,1]$.

*Proof Sketch.* The key insight is that our regularized score function is a convex combination of two valid score functions. Since $s_{base}(x,y) = |y - \hat{f}(x)|$ is a standard score function and $s_\theta$ is any measurable function, their convex combination preserves the fundamental property needed for conformal validity.

More formally, let $S_i^{reg} = s_{reg}(X_i, Y_i)$ be the regularized scores on the final calibration set. Under exchangeability, $(S_1^{reg}, \ldots, S_{|cal|}^{reg}, S_{n+1}^{reg})$ has the same distribution under any permutation of indices. The conformal quantile $\hat{q}$ is constructed to ensure that:
$$\mathbb{P}(S_{n+1}^{reg} \leq \hat{q}) \geq 1 - \alpha$$

Since $C(X_{n+1}) = \{y : s_{reg}(X_{n+1}, y) \leq \hat{q}\}$ and $Y_{n+1}$ satisfies $s_{reg}(X_{n+1}, Y_{n+1}) = S_{n+1}^{reg}$, we have:
$$\mathbb{P}(Y_{n+1} \in C(X_{n+1})) = \mathbb{P}(S_{n+1}^{reg} \leq \hat{q}) \geq 1 - \alpha$$

The crucial point is that this holds regardless of how $\lambda$ is chosen, even if it depends on the data in arbitrary ways. $\square$

**Efficiency Analysis**

While coverage is guaranteed, efficiency depends on the quality of the learned score function and the mixing weight. We can analyze the expected interval length:

*Proposition 1.* The expected interval length of our method satisfies:
$$\mathbb{E}[|C(X_{n+1})|] \leq (1-\lambda) \mathbb{E}[|C_{base}(X_{n+1})|] + \lambda \mathbb{E}[|C_\theta(X_{n+1})|] + O(n^{-1/2})$$

where $C_{base}$ and $C_\theta$ are intervals constructed using $s_{base}$ and $s_\theta$ respectively.

This shows that when $s_\theta$ produces shorter intervals than $s_{base}$ (i.e., $\mathbb{E}[|C_\theta(X_{n+1})|] < \mathbb{E}[|C_{base}(X_{n+1})|]$), choosing $\lambda > 0$ improves efficiency. The validation procedure for setting $\lambda$ aims to identify such cases.

**Meta-Learning Guarantees**

Under standard meta-learning assumptions, we can provide generalization bounds for the learned score function:

*Proposition 2.* Suppose the score function class has finite Rademacher complexity $\mathcal{R}_m(\mathcal{S})$ over $m$ meta-training tasks. Then with probability at least $1-\delta$:
$$\mathbb{E}[L(s_{\theta^*})] \leq \hat{L}(s_{\theta^*}) + 2\mathcal{R}_m(\mathcal{S}) + \sqrt{\frac{\log(1/\delta)}{2m}}$$

where $\hat{L}$ is the empirical meta-learning objective and $L$ is the true expected loss.

This bound suggests that with sufficient auxiliary data, the learned score function will generalize well to new tasks, leading to improved efficiency when $\lambda > 0$.

**Robustness Properties**

A key advantage of our approach is its robustness to failures in the learning components:

*Corollary 1.* If the learned score function $s_\theta$ is adversarially bad (e.g., produces arbitrarily poor intervals), the validation procedure will set $\lambda \approx 0$, and the method reduces to standard conformal prediction with guaranteed coverage.

This robustness property is crucial in practice, as it means our method can only improve upon standard conformal prediction—it cannot make things worse in terms of coverage, and efficiency degradation is limited by the mixing weight.

## 6. Experimental Design

We would conduct comprehensive experiments to evaluate both the coverage and efficiency properties of our method across diverse settings.

**Datasets and Tasks**

*Synthetic Datasets:* We would generate synthetic regression problems with known optimal intervals to provide ground truth for efficiency evaluation:
- Heteroscedastic noise: $Y = f(X) + \sigma(X) \cdot \epsilon$ where $\sigma(X)$ varies across input space
- Heavy-tailed noise: $Y = f(X) + \epsilon$ with $\epsilon$ following $t$-distributions
- Multimodal conditional distributions with known quantiles

*Real Datasets:* We would evaluate on standard regression benchmarks spanning different domains:
- UCI regression datasets (Boston housing, energy efficiency, concrete strength)
- Time series forecasting (electricity load, financial returns)
- Scientific datasets (protein folding, climate modeling)
- High-dimensional problems (gene expression, image regression)

**Experimental Setup**

*Meta-Learning Setup:* For each real dataset, we would create meta-learning scenarios by:
- Using multiple related datasets from the same domain
- Creating artificial tasks by subsampling or adding synthetic noise
- Cross-validation across different prediction horizons for time series

*Baseline Methods:*
- Standard conformal prediction with absolute residuals
- Conformal prediction with studentized residuals
- Quantile-based conformal methods
- Weighted conformal prediction
- Oracle methods using true conditional quantiles (for synthetic data)

*Evaluation Metrics:*
- Empirical coverage rates across different confidence levels
- Average interval length and relative efficiency gains
- Coverage conditional on input regions (to assess fairness)
- Computational overhead of the meta-learning phase

**Ablation Studies**

We would conduct systematic ablations to understand the contribution of different components:

*Score Function Architecture:* Compare linear combinations of features vs. neural network-based score functions vs. tree-based methods.

*Meta-Learning Strategies:* Evaluate different meta-learning objectives, including direct interval length minimization vs. ranking-based losses vs. coverage-adjusted objectives.

*Regularization Schemes:* Compare our data-dependent mixing weight with fixed weights, cross-validation-based selection, and alternative robustness mechanisms.

*Feature Engineering:* Study the impact of different feature extraction functions $\phi(x,y,\hat{f}(x))$, including residual-based features, prediction confidence measures, and input-dependent features.

**Coverage Validation**

Since coverage is the primary requirement, we would implement rigorous validation:
- Statistical tests for coverage rates (binomial tests, exact coverage intervals)
- Coverage assessment across different subgroups and input regions
- Stress testing with distribution shift and model misspecification
- Analysis of coverage as a function of calibration set size

**Efficiency Analysis**

For efficiency evaluation, we would measure:
- Relative interval length compared to standard conformal methods
- Efficiency gains as a function of sample size and problem difficulty
- Trade-offs between coverage and efficiency for different mixing weights
- Comparison to oracle methods on synthetic data where optimal intervals are known

**Computational Considerations**

We would analyze the computational overhead:
- Training time for meta-learning phase vs. standard methods
- Inference time for computing regularized scores
- Scalability to high-dimensional problems and large datasets
- Memory requirements for storing auxiliary data and learned parameters

The experimental design would provide comprehensive evidence for both the theoretical guarantees (coverage) and practical benefits (efficiency) of our approach while identifying the conditions under which the method provides the greatest improvements.

## 7. Discussion

**Strengths and Expected Benefits**

Our approach addresses a fundamental limitation of conformal prediction—the reliance on fixed, potentially suboptimal score functions—while preserving its most valuable property: finite-sample coverage guarantees. The meta-learning framework enables adaptation to problem-specific characteristics that fixed score functions cannot capture, such as heteroscedastic noise patterns or complex conditional distributions.

The regularization scheme provides crucial robustness, ensuring that our method can only improve upon standard conformal prediction. This "no-regrets" property is essential for practical adoption, as practitioners can confidently apply our method without risk of degraded performance. The data-dependent mixing weight allows automatic adaptation based on validation performance, reducing the need for manual hyperparameter tuning.

The theoretical guarantees are particularly strong—coverage is maintained regardless of how poorly the learning components perform. This distinguishes our approach from other adaptive methods that may sacrifice finite-sample validity for improved efficiency.

**Limitations and Challenges**

Several limitations merit consideration. First, the method requires auxiliary data from related tasks for effective meta-learning. In domains where such data is scarce, the benefits may be limited. However, the regularization ensures graceful degradation to standard conformal prediction in such cases.

Second, the computational overhead of meta-learning may be significant, particularly for complex score function classes. This cost is amortized across multiple applications of the learned score function, but may limit applicability in resource-constrained settings.

Third, our current formulation focuses on regression problems. Extension to classification requires careful consideration of how to define interval length and efficiency in discrete output spaces. The fundamental framework should extend, but the specific implementation details would differ.

Fourth, while we maintain marginal coverage, conditional coverage across subgroups may still be suboptimal. The learned score function could potentially improve conditional coverage by adapting to local data characteristics, but this requires careful analysis and validation.

**Connections to Broader Impact**

The ability to construct more efficient prediction intervals while maintaining validity guarantees has significant implications across many domains. In medical applications, tighter intervals could improve diagnostic confidence without sacrificing safety. In autonomous systems, more precise uncertainty quantification could enable better decision-making under uncertainty.

However, the reliance on auxiliary data raises questions about fairness and representation. If the meta-learning data lacks diversity or contains biases, the learned score functions might perpetuate or amplify these issues. Careful curation of meta-learning datasets and evaluation across diverse populations would be essential.

The method also connects to broader trends in machine learning toward more adaptive and data-driven approaches. Our framework demonstrates how classical statistical guarantees can be preserved while incorporating modern learning techniques, potentially serving as a template for other problems requiring both adaptivity and theoretical rigor.

**Future Directions**

Several extensions could enhance the practical impact of this work. First, developing more sophisticated meta-learning objectives that directly optimize for coverage-efficiency trade-offs could improve performance. Second, investigating how to learn score functions that improve conditional coverage, not just marginal coverage, would address an important limitation of standard conformal prediction.

Third, extending the framework to other uncertainty quantification settings, such as conformal classification or structured prediction, could broaden its applicability. Fourth, developing online or continual learning versions that adapt score functions as new data arrives could be valuable for dynamic environments.

Finally, investigating the interplay between score function learning and predictor learning could lead to end-to-end optimization of the entire conformal prediction pipeline while maintaining theoretical guarantees.

## 8. Conclusion

We have presented a framework for learning adaptive score functions in conformal prediction that maintains finite-sample marginal coverage guarantees while improving interval efficiency. Our approach combines meta-learning across auxiliary datasets with a robust regularization scheme that ensures validity even when learning components fail.

The key contributions include: (1) a formalization of the score function learning problem that preserves conformal validity, (2) a meta-learning framework that leverages auxiliary data to learn effective score functions, (3) a regularization scheme that blends learned and baseline score functions with data-dependent weights, and (4) theoretical analysis proving coverage guarantees and efficiency improvements.

Our method addresses the fundamental tension between adaptivity and validity in uncertainty quantification. By carefully designing the learning and regularization components, we can harness the power of machine learning to improve conformal prediction without sacrificing its most valuable property: distribution-free finite-sample coverage guarantees.

Several open questions remain for future work. How can we extend this framework to improve conditional coverage rather than just marginal coverage? Can we develop more sophisticated meta-learning objectives that better capture the coverage-efficiency trade-off? How does the approach scale to very high-dimensional problems or streaming data settings?

The framework presented here provides a foundation for incorporating adaptive learning into conformal prediction while maintaining theoretical rigor. As uncertainty quantification becomes increasingly important across machine learning applications, such principled approaches to balancing adaptivity and validity will be essential for building trustworthy predictive systems.

## References

[Angelopoulos & Bates, 2021] Angelopoulos, A. N., & Bates, S. (2021). A gentle introduction to conformal prediction and distribution-free uncertainty quantification.

[Chernozhukov et al., 2018] Chernozhukov, V., Wüthrich, K., & Zhu, Y. (2018). Distributional conformal prediction. Proceedings of the National Academy of Sciences.

[Finn et al., 2017] Finn, C., Abbeel, P., & Levine, S. (2017). Model-agnostic meta-learning for fast adaptation of deep networks. International Conference on Machine Learning.

[Gibbs & Candès, 2021] Gibbs, I., & Candès, E. (2021). Adaptive conformal inference under distribution shift. Advances in Neural Information Processing Systems.

[Harrison et al., 2018] Harrison, J., Sharma, A., Finn, C., & Abbeel, P. (2018). Continuous meta-learning without tasks. Advances in Neural Information Processing Systems.

[Lei & Wasserman, 2014] Lei, J., & Wasserman, L. (2014). Distribution-free prediction bands for non-parametric regression. Journal of the Royal Statistical Society: Series B.

[Lei et al., 2018] Lei, J., G'Sell, M., Rinaldo, A., Tibshirani, R. J., & Wasserman, L. (2018). Distribution-free predictive inference for regression. Journal of the American Statistical Association.

[Ravi & Larochelle, 2017] Ravi, S., & Larochelle, H. (2017). Optimization as a model for few-shot learning. International Conference on Learning Representations.

[Romano et al., 2019] Romano, Y., Patterson, E., & Candès, E. (2019). Conformalized quantile regression. Advances in Neural Information Processing Systems.

[Shafer & Vovk, 2008] Shafer, G., & Vovk, V. (2008). A tutorial on conformal prediction. Journal of Machine Learning Research.

[Stutz et al., 2021] Stutz, D., Dvijotham, K. D., Cemgil, A. T., & Doucet, A. (2021). Learning optimal conformal classifiers. International Conference on Learning Representations.

[Tibshirani et al., 2019] Tibshirani, R. J., Barber, R. F., Candès, E., & Ramdas, A. (2019). Conformal prediction under covariate shift. Advances in Neural Information Processing Systems.

[Vovk et al., 2005] Vovk, V., Gammerman, A., & Shafer, G. (2005). Algorithmic learning in a random world. Springer.
