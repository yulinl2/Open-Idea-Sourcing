# Reconstruction: full_guided
**Paper:** 2602.04770  
**Condition:** with_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Learning Adaptive Conformal Score Functions for Efficient Prediction Intervals

## Abstract

Conformal prediction provides finite-sample marginal coverage guarantees for prediction intervals, but the efficiency of these intervals depends critically on the choice of score function. Existing approaches either use fixed score functions that may be suboptimal for specific datasets, or focus primarily on coverage without optimizing interval width. We propose a novel framework for learning adaptive conformal score functions that minimize expected interval width while maintaining finite-sample coverage guarantees. Our approach combines a parameterized score function with a bilevel optimization procedure that directly optimizes interval efficiency subject to coverage constraints. We provide theoretical analysis showing that our learned score functions achieve asymptotic optimality under mild conditions, and demonstrate that the method maintains exact finite-sample coverage. The framework is general and can incorporate various base predictors and score function architectures, making it broadly applicable to regression and classification tasks requiring uncertainty quantification.

## 1. Introduction

Uncertainty quantification is fundamental to reliable machine learning, particularly in high-stakes applications where understanding prediction confidence is as important as the prediction itself. Prediction intervals that contain the true outcome with specified probability provide a principled approach to uncertainty quantification, but constructing such intervals with both validity and efficiency remains challenging.

Conformal prediction [Vovk et al., 2005] offers an elegant solution by providing finite-sample marginal coverage guarantees regardless of the underlying data distribution. Given a miscoverage level α, conformal prediction constructs intervals that contain the true outcome with probability at least 1-α. However, the practical utility of conformal prediction depends heavily on the choice of score function, which measures how "unusual" a potential outcome would be given the input.

The fundamental challenge is that different score functions can yield dramatically different interval widths while maintaining the same coverage guarantee. Standard approaches use simple score functions like absolute residuals or quantile-based measures, but these may be far from optimal for specific datasets or prediction tasks. Recent work has explored various score function designs [Romano et al., 2019; Angelopoulos et al., 2021], but the question of how to systematically learn optimal score functions remains largely unaddressed.

Our contributions are:
• We formalize the problem of learning optimal conformal score functions as a bilevel optimization that minimizes expected interval width subject to coverage constraints
• We propose a practical algorithm that learns parameterized score functions while maintaining finite-sample coverage guarantees
• We provide theoretical analysis showing asymptotic optimality of our approach under regularity conditions
• We demonstrate that our framework generalizes existing score function designs and can incorporate various neural network architectures

## 2. Related Work

**Conformal Prediction Foundations.** Conformal prediction was introduced by [Vovk et al., 2005] and provides distribution-free finite-sample coverage guarantees. The framework has been extended to various settings including regression [Lei et al., 2018], classification [Sadinle et al., 2019], and time series [Xu & Xie, 2021]. A key strength is that coverage holds for any data distribution without distributional assumptions.

**Score Function Design.** Most conformal prediction work uses simple score functions. [Romano et al., 2019] introduced conformalized quantile regression using quantile-based scores. [Angelopoulos et al., 2021] explored adaptive prediction sets for classification. [Tibshirani et al., 2020] developed weighted conformal prediction for covariate shift, demonstrating how score function modifications can address distributional challenges.

**Efficiency in Conformal Prediction.** While coverage is guaranteed by construction, interval efficiency varies significantly across score functions. [Lei et al., 2018] analyzed conditional coverage and efficiency trade-offs. [Romano et al., 2019] showed that quantile-based scores can improve efficiency over residual-based approaches. However, systematic approaches to optimizing score functions for efficiency remain limited.

**Learning-Based Uncertainty Quantification.** Related work includes learning prediction intervals through quantile regression [Koenker & Hallock, 2001] and neural network approaches [Pearce et al., 2018]. However, these methods typically lack finite-sample coverage guarantees. Our work bridges this gap by maintaining conformal prediction's validity while learning improved score functions.

**Bilevel Optimization.** Our approach uses bilevel optimization to learn score functions. This connects to meta-learning [Finn et al., 2017] and hyperparameter optimization [Franceschi et al., 2018], but applied to the novel setting of conformal score function learning.

The gap our work fills is the lack of principled methods for learning score functions that optimize interval efficiency while preserving conformal prediction's finite-sample coverage guarantees.

## 3. Problem Formulation

Let $(X, Y)$ denote input-output pairs where $X \in \mathcal{X}$ and $Y \in \mathcal{Y}$. We observe training data $\{(X_i, Y_i)\}_{i=1}^n$ drawn i.i.d. from some unknown distribution $P$. Our goal is to construct prediction intervals for a new test point $X_{n+1}$ that contain $Y_{n+1}$ with probability at least $1-\alpha$ for a specified miscoverage level $\alpha \in (0,1)$.

**Conformal Prediction Framework.** Given a score function $s: \mathcal{X} \times \mathcal{Y} \to \mathbb{R}$ and base predictor $\hat{f}$, conformal prediction works as follows:

1. Split training data into proper training set $\mathcal{I}_1$ and calibration set $\mathcal{I}_2$
2. Train base predictor $\hat{f}$ on $\mathcal{I}_1$
3. Compute conformity scores $S_i = s(X_i, Y_i, \hat{f})$ for $(X_i, Y_i) \in \mathcal{I}_2$
4. Calculate quantile $\hat{q} = \text{Quantile}_{1-\alpha}(\{S_i\}_{i \in \mathcal{I}_2})$
5. For test point $X_{n+1}$, predict interval $C(X_{n+1}) = \{y : s(X_{n+1}, y, \hat{f}) \leq \hat{q}\}$

**Score Function Parameterization.** We parameterize the score function as $s_\theta(x, y, \hat{f})$ where $\theta$ are learnable parameters. Common examples include:
- Residual-based: $s_\theta(x, y, \hat{f}) = |y - \hat{f}(x)|$
- Weighted residual: $s_\theta(x, y, \hat{f}) = w_\theta(x)|y - \hat{f}(x)|$
- Neural score: $s_\theta(x, y, \hat{f}) = g_\theta(x, y, \hat{f}(x))$ where $g_\theta$ is a neural network

**Optimization Objective.** Our goal is to learn $\theta$ that minimizes expected interval width while maintaining coverage:

$$\min_\theta \mathbb{E}[W(C_\theta(X))] \quad \text{subject to} \quad \mathbb{P}(Y \in C_\theta(X)) \geq 1-\alpha$$

where $W(C)$ denotes the width/size of prediction set $C$, and $C_\theta(X)$ is the conformal prediction set using score function $s_\theta$.

**Assumptions.** We assume:
1. Data $(X_i, Y_i)$ are exchangeable
2. Score function $s_\theta$ is continuous in $\theta$ and $y$
3. For each $x$, the set $\{y : s_\theta(x, y, \hat{f}) \leq t\}$ has well-defined measure for all $t$

## 4. Methodology

Our approach learns optimal score function parameters through a bilevel optimization procedure that directly optimizes interval efficiency while ensuring coverage constraints are satisfied.

**Algorithm Overview.** The key insight is to use a validation set to estimate interval efficiency and adjust score function parameters accordingly. We split the calibration data into two parts: one for computing the conformal quantile and another for evaluating interval quality.

**Bilevel Optimization Formulation.** Let $\mathcal{D}_{\text{cal}}$ and $\mathcal{D}_{\text{val}}$ denote calibration and validation sets respectively. Our bilevel optimization is:

$$\min_\theta \frac{1}{|\mathcal{D}_{\text{val}}|} \sum_{(x,y) \in \mathcal{D}_{\text{val}}} W(C_\theta(x))$$

where $C_\theta(x) = \{y' : s_\theta(x, y', \hat{f}) \leq \hat{q}_\theta\}$ and

$$\hat{q}_\theta = \text{Quantile}_{1-\alpha}\left(\{s_\theta(x_i, y_i, \hat{f})\}_{(x_i,y_i) \in \mathcal{D}_{\text{cal}}}\right)$$

**Practical Algorithm.** We implement this through the following procedure:

```
Algorithm 1: Adaptive Conformal Score Learning
Input: Training data D, miscoverage level α, score architecture s_θ
1. Split D into D_train, D_cal, D_val
2. Train base predictor f̂ on D_train
3. Initialize score parameters θ₀
4. For t = 1 to T:
   a. Compute q̂_θₜ = Quantile_{1-α}({s_θₜ(xᵢ, yᵢ, f̂)}_{(xᵢ,yᵢ) ∈ D_cal})
   b. Compute prediction sets C_θₜ(x) for all x in D_val
   c. Estimate efficiency: L(θₜ) = (1/|D_val|) Σ W(C_θₜ(x))
   d. Update: θₜ₊₁ = θₜ - η∇_θ L(θₜ)
5. Return θ_T
```

**Gradient Computation.** The key technical challenge is computing gradients of the interval width with respect to score parameters. For continuous $Y$, interval width is:

$$W(C_\theta(x)) = \int_{s_\theta(x,y,\hat{f}) \leq \hat{q}_\theta} dy$$

We use the implicit function theorem to compute $\nabla_\theta \hat{q}_\theta$ and chain rule for the full gradient. For discrete $Y$, we use the set size $|C_\theta(x)|$.

**Coverage Preservation.** A crucial property is that our learned score function preserves finite-sample coverage guarantees. This follows because:

1. We maintain the conformal prediction procedure exactly
2. The quantile $\hat{q}_\theta$ is computed on a separate calibration set
3. Coverage depends only on the exchangeability of conformity scores, not their specific values

**Score Function Architectures.** Our framework accommodates various score function designs:

- **Linear weighting**: $s_\theta(x, y, \hat{f}) = w_\theta^T \phi(x) |y - \hat{f}(x)|$
- **Neural networks**: $s_\theta(x, y, \hat{f}) = \text{NN}_\theta([x, y, \hat{f}(x)])$
- **Quantile-based**: Learn parameters of conditional quantile functions

## 5. Theoretical Analysis

We provide theoretical analysis of our approach's properties, focusing on coverage guarantees and asymptotic optimality.

**Finite-Sample Coverage Guarantee.**

**Theorem 1.** For any choice of score function parameters $\theta$, the conformal prediction intervals $C_\theta(X_{n+1})$ satisfy

$$\mathbb{P}(Y_{n+1} \in C_\theta(X_{n+1})) \geq 1 - \alpha$$

for any distribution $P$ and any sample size, provided the data are exchangeable.

*Proof Sketch:* This follows directly from the standard conformal prediction guarantee. The key insight is that our parameter learning occurs on a separate validation set and does not affect the calibration procedure. The coverage guarantee depends only on the exchangeability of conformity scores $\{s_\theta(X_i, Y_i, \hat{f})\}$ and the quantile computation, both of which are preserved in our framework.

**Asymptotic Optimality.**

**Theorem 2.** Under regularity conditions, as $n \to \infty$, the learned score function parameters $\hat{\theta}_n$ converge to

$$\theta^* = \arg\min_\theta \mathbb{E}[W(C_\theta(X))]$$

subject to $\mathbb{P}(Y \in C_\theta(X)) \geq 1-\alpha$.

*Proof Sketch:* The proof relies on uniform convergence of the empirical efficiency estimate to the population quantity and consistency of the quantile estimator. Under appropriate smoothness and compactness conditions, the empirical objective converges uniformly to the population objective, and standard M-estimation theory applies.

**Regularity Conditions:**
1. Score function $s_\theta$ is Lipschitz continuous in $\theta$
2. Parameter space $\Theta$ is compact
3. Moment conditions ensuring uniform convergence of empirical measures

**Computational Complexity.** Each iteration of our algorithm requires:
- Computing conformity scores: $O(|\mathcal{D}_{\text{cal}}|)$
- Quantile computation: $O(|\mathcal{D}_{\text{cal}}| \log |\mathcal{D}_{\text{cal}}|)$
- Gradient computation: $O(|\mathcal{D}_{\text{val}}| \cdot |\theta|)$

The overall complexity is $O(T \cdot n \log n \cdot |\theta|)$ where $T$ is the number of optimization iterations.

## 6. Experimental Design

We would evaluate our approach across multiple domains to demonstrate its generality and effectiveness compared to standard conformal prediction methods.

**Datasets.** Our experimental evaluation would include:
- **Regression**: California housing, Boston housing, energy efficiency prediction
- **High-dimensional regression**: Gene expression datasets, financial time series
- **Classification**: CIFAR-10, MNIST (for prediction set size), medical diagnosis datasets
- **Structured prediction**: Image segmentation with pixel-wise intervals

**Baseline Methods.** We would compare against:
- Standard conformal prediction with absolute residuals
- Conformalized quantile regression [Romano et al., 2019]
- Locally adaptive conformal prediction [Angelopoulos et al., 2021]
- Weighted conformal prediction [Tibshirani et al., 2020]
- Classical prediction intervals (quantile regression, bootstrap)

**Evaluation Metrics.**
- **Coverage**: Empirical coverage rate across test sets
- **Efficiency**: Average interval width (regression) or set size (classification)
- **Conditional coverage**: Coverage across different input regions
- **Computational time**: Training and inference speed

**Experimental Protocol.**
1. Split each dataset into train/calibration/validation/test (40%/20%/20%/20%)
2. Train base predictors on training set
3. Learn score function parameters using calibration/validation sets
4. Evaluate coverage and efficiency on held-out test set
5. Repeat across 10 random splits for statistical significance

**Ablation Studies.** We would investigate:
- Effect of score function architecture (linear vs. neural)
- Sensitivity to calibration/validation split ratios
- Performance across different miscoverage levels (α = 0.05, 0.1, 0.2)
- Robustness to covariate shift and model misspecification

**Implementation Details.** Experiments would use:
- Base predictors: Random forests, gradient boosting, neural networks
- Score function architectures: MLPs with 2-3 hidden layers
- Optimization: Adam optimizer with learning rate 0.001
- Early stopping based on validation efficiency

## 7. Discussion

**Strengths.** Our approach offers several advantages over existing methods. First, it maintains the fundamental finite-sample coverage guarantees that make conformal prediction attractive while systematically improving interval efficiency. Second, the framework is general and can incorporate various score function architectures and base predictors. Third, our bilevel optimization directly targets the objective of interest (interval width) rather than using proxy measures.

**Limitations.** Several limitations merit discussion. The approach requires additional data splitting, which may be problematic in small-sample settings. The bilevel optimization introduces computational overhead and hyperparameter tuning. Our theoretical analysis relies on regularity conditions that may not hold for all score function architectures. Additionally, the method assumes the validation set is representative of the test distribution, which may not hold under distribution shift.

**Computational Considerations.** While our method adds computational cost through score function learning, this is typically a one-time training cost. The inference procedure remains as efficient as standard conformal prediction. For very large datasets, mini-batch variants of our optimization could be developed.

**Extensions and Future Work.** Several extensions could enhance our framework. Adaptive splitting strategies could better allocate data between calibration and validation. Online variants could update score functions as new data arrives. The framework could be extended to conditional conformal prediction to improve coverage across input subgroups.

**Broader Impact.** Improved uncertainty quantification has significant implications for high-stakes applications like medical diagnosis, autonomous driving, and financial decision-making. Our method could make conformal prediction more practically useful by providing tighter intervals while maintaining statistical guarantees. However, users must understand that efficiency gains come from better score function design, not relaxing coverage requirements.

## 8. Conclusion

We have presented a novel framework for learning adaptive conformal score functions that optimize prediction interval efficiency while preserving finite-sample coverage guarantees. Our approach formulates score function learning as a bilevel optimization problem and provides both theoretical guarantees and practical algorithms. The method generalizes existing score function designs and can incorporate modern neural network architectures.

Key contributions include: (1) a principled optimization framework for conformal score functions, (2) theoretical analysis showing coverage preservation and asymptotic optimality, and (3) a practical algorithm that scales to real datasets. Our work bridges the gap between conformal prediction's theoretical guarantees and practical efficiency requirements.

**Open Questions.** Several directions warrant further investigation. Can we develop adaptive data splitting strategies that optimize the calibration/validation trade-off? How can we extend our approach to handle distribution shift more robustly? Can similar bilevel optimization ideas improve conditional conformal prediction methods? These questions point toward a rich research agenda in adaptive conformal prediction.

## References

[Angelopoulos et al., 2021] Angelopoulos, A. N., Bates, S., Malik, J., & Jordan, M. I. (2021). Uncertainty sets for image classifiers using conformal prediction. ICLR.

[Finn et al., 2017] Finn, C., Abbeel, P., & Levine, S. (2017). Model-agnostic meta-learning for fast adaptation of deep networks. ICML.

[Franceschi et al., 2018] Franceschi, L., Frasconi, P., Salzo, S., Grazzi, R., & Pontil, M. (2018). Bilevel programming for hyperparameter optimization and meta-learning. ICML.

[Koenker & Hallock, 2001] Koenker, R., & Hallock, K. F. (2001). Quantile regression. Journal of Economic Perspectives, 15(4), 143-156.

[Lei et al., 2018] Lei, J., G'Sell, M., Rinaldo, A., Tibshirani, R. J., & Wasserman, L. (2018). Distribution-free predictive inference for regression. Journal of the American Statistical Association, 113(523), 1094-1111.

[Pearce et al., 2018] Pearce, T., Zaki, M., Brintrup, A., & Neely, A. (2018). High-quality prediction intervals for deep learning: A distribution-free, ensembled approach. ICML.

[Romano et al., 2019] Romano, Y., Patterson, E., & Candes, E. (2019). Conformalized quantile regression. NeurIPS.

[Sadinle et al., 2019] Sadinle, M., Lei, J., & Wasserman, L. (2019). Least ambiguous set-valued classifiers with bounded error levels. Journal of the American Statistical Association, 114(525), 223-234.

[Tibshirani et al., 2020] Tibshirani, R. J., Barber, R. F., Candes, E. J., & Ramdas, A. (2020). Conformal prediction under covariate shift. NeurIPS.

[Vovk et al., 2005] Vovk, V., Gammerman, A., & Shafer, G. (2005). Algorithmic learning in a random world. Springer.

[Xu & Xie, 2021] Xu, C., & Xie, Y. (2021). Conformal prediction interval for dynamic time-series. ICML.
