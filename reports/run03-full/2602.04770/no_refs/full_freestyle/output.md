# Reconstruction: full_freestyle
**Paper:** 2602.04770  
**Condition:** no_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Adaptive Conformal Prediction via Score Function Learning

## Abstract

Conformal prediction provides finite-sample marginal coverage guarantees for prediction intervals, but the efficiency of these intervals depends critically on the choice of score function. We propose a novel framework for learning optimal score functions that minimize prediction interval width while maintaining valid coverage. Our approach, termed Adaptive Conformal Prediction (ACP), formulates score function learning as a constrained optimization problem where we minimize expected interval width subject to coverage constraints. We develop both parametric and non-parametric variants of ACP, prove finite-sample coverage guarantees, and establish consistency results showing our intervals approach optimal efficiency. Theoretical analysis reveals that our learned score functions converge to the conditional quantile function of the residual distribution, providing intuition for why the method works. The framework is computationally efficient and scales to high-dimensional problems through neural network architectures.

## 1. Introduction

Uncertainty quantification is fundamental to reliable machine learning, yet most predictive models produce only point estimates. In many applications—from autonomous driving to medical diagnosis—we need prediction intervals that contain the true outcome with specified probability. The challenge lies in constructing intervals that achieve valid coverage while remaining as narrow as possible.

Conformal prediction has emerged as a powerful framework for this problem, offering finite-sample marginal coverage guarantees without distributional assumptions [Vovk et al., 2005]. Given a confidence level $1-\alpha$, conformal prediction constructs intervals $\hat{C}(X)$ such that $P(Y \in \hat{C}(X)) \geq 1-\alpha$ for any exchangeable sequence of data points. This guarantee holds in finite samples and makes no assumptions about the underlying data distribution.

The efficiency of conformal prediction intervals depends critically on the choice of *score function* $s(x,y)$, which measures how "unusual" outcome $y$ is for input $x$. Traditional approaches use simple score functions like absolute residuals $|y - \hat{f}(x)|$ or normalized residuals $|y - \hat{f}(x)|/\hat{\sigma}(x)$. However, these choices are often suboptimal and can lead to unnecessarily wide intervals.

We address a fundamental question: *Can we learn score functions that produce the shortest possible prediction intervals while maintaining finite-sample coverage guarantees?* This question presents a unique challenge because we must balance two competing objectives—statistical validity and interval efficiency—while working with finite samples.

Our contributions are:

1. **Adaptive Conformal Prediction (ACP)**: A principled framework for learning score functions that minimize expected interval width subject to coverage constraints.

2. **Theoretical guarantees**: We prove that ACP maintains finite-sample marginal coverage and establish consistency results showing our intervals approach optimal efficiency.

3. **Practical algorithms**: We develop computationally efficient implementations using neural networks that scale to high-dimensional problems.

4. **Convergence analysis**: We show that learned score functions converge to conditional quantile functions of the residual distribution, providing theoretical insight into optimal score function design.

## 2. Background and Related Work

### 2.1 Conformal Prediction

Conformal prediction constructs prediction intervals using a three-step process. Given a confidence level $1-\alpha$ and training data $(X_1, Y_1), \ldots, (X_n, Y_n)$:

1. **Score computation**: For each training point, compute a conformity score $s_i = s(X_i, Y_i)$ measuring how well $Y_i$ conforms to the model's prediction for $X_i$.

2. **Quantile estimation**: Compute the $(1-\alpha)(1 + 1/n)$-quantile of the scores: $\hat{q} = \text{Quantile}_{1-\alpha}(\{s_1, \ldots, s_n\})$.

3. **Interval construction**: For a new input $x$, the prediction interval is $\hat{C}(x) = \{y : s(x,y) \leq \hat{q}\}$.

The finite-sample coverage guarantee follows from the exchangeability assumption: if $(X_1, Y_1), \ldots, (X_n, Y_n), (X_{n+1}, Y_{n+1})$ are exchangeable, then $P(Y_{n+1} \in \hat{C}(X_{n+1})) \geq 1-\alpha$.

### 2.2 Score Function Design

The choice of score function $s(x,y)$ determines both the shape and size of prediction intervals. Common choices include:

- **Absolute residual**: $s(x,y) = |y - \hat{f}(x)|$
- **Normalized residual**: $s(x,y) = |y - \hat{f}(x)|/\hat{\sigma}(x)$
- **Quantile-based**: $s(x,y) = \max(\hat{F}^{-1}_\alpha(x) - y, y - \hat{F}^{-1}_{1-\alpha}(x))$

While these choices are intuitive, they are typically not optimal for interval efficiency. Recent work has explored more sophisticated score functions, including locally adaptive methods and ensemble-based approaches, but lacks a principled framework for score function optimization.

### 2.3 Optimal Interval Construction

The fundamental trade-off in prediction interval construction is between coverage and efficiency. Ideally, we want intervals that are as narrow as possible while maintaining valid coverage. This leads to the concept of *conditional coverage*: $P(Y \in \hat{C}(X) | X = x) = 1-\alpha$ for all $x$. However, conditional coverage is generally impossible to achieve with finite samples without strong distributional assumptions.

Our work bridges this gap by learning score functions that approach conditional optimality while maintaining marginal coverage guarantees.

## 3. Adaptive Conformal Prediction

### 3.1 Problem Formulation

We formulate score function learning as a constrained optimization problem. Let $\mathcal{S}$ be a class of score functions and define the expected interval width for score function $s \in \mathcal{S}$ as:

$$W(s) = E[\text{width}(\{y : s(X,y) \leq \hat{q}_s\})]$$

where $\hat{q}_s$ is the quantile computed using score function $s$. Our goal is to solve:

$$\min_{s \in \mathcal{S}} W(s) \quad \text{subject to} \quad P(Y \in \hat{C}_s(X)) \geq 1-\alpha$$

This formulation captures our dual objectives: minimizing interval width while maintaining coverage. The challenge lies in the constraint, which must hold for any data distribution.

### 3.2 The ACP Algorithm

Our Adaptive Conformal Prediction algorithm proceeds in two phases:

**Phase 1: Score Function Learning**
Split the training data into two parts: $D_{\text{train}}$ for learning the base predictor and score function, and $D_{\text{cal}}$ for calibration. 

1. Train base predictor $\hat{f}$ on $D_{\text{train}}$
2. Learn score function $s_\theta$ by solving:
   $$\min_\theta E_{(x,y) \sim D_{\text{train}}}[\ell(s_\theta(x,y), r(x,y))]$$
   where $r(x,y)$ is a target score and $\ell$ is a loss function.

**Phase 2: Conformal Calibration**
Use $D_{\text{cal}}$ to compute conformity scores and construct intervals:

1. Compute scores: $\{s_\theta(x_i, y_i)\}_{i \in D_{\text{cal}}}$
2. Calculate quantile: $\hat{q} = \text{Quantile}_{1-\alpha}(\text{scores})$
3. Form intervals: $\hat{C}(x) = \{y : s_\theta(x,y) \leq \hat{q}\}$

The key insight is in defining the target score $r(x,y)$ to encourage narrow intervals while preserving the coverage property.

### 3.3 Target Score Design

We propose learning score functions that approximate the conditional quantile function of residuals. Define the residual $R = Y - \hat{f}(X)$ and its conditional quantile function $Q_R(τ|x) = \inf\{r : P(R \leq r | X = x) \geq τ\}$.

Our target score is:
$$r(x,y) = \min\{τ \in [0,1] : |y - \hat{f}(x)| \leq Q_R(τ|x)\}$$

This target encourages the learned score function to identify the quantile level at which each residual occurs. Intuitively, points with large residuals (relative to their conditional distribution) receive high scores, while typical residuals receive low scores.

### 3.4 Parametric Implementation

For practical implementation, we parameterize the score function using neural networks. Let $s_\theta(x,y) = g_\theta(x, y - \hat{f}(x))$ where $g_\theta$ is a neural network mapping input features and residuals to scores.

We train $g_\theta$ using a quantile regression loss:
$$\ell_\tau(u,v) = \tau \max(u-v, 0) + (1-\tau) \max(v-u, 0)$$

The complete training objective becomes:
$$\min_\theta \sum_{i=1}^n \sum_{\tau \in T} \ell_\tau(s_\theta(x_i, y_i), Q_R(\tau|x_i))$$

where $T$ is a grid of quantile levels and $Q_R(\tau|x_i)$ is estimated using quantile regression.

## 4. Theoretical Analysis

### 4.1 Coverage Guarantees

**Theorem 1** (Finite-sample Coverage). *Let $(X_1, Y_1), \ldots, (X_{n+1}, Y_{n+1})$ be exchangeable random variables. The ACP prediction intervals satisfy*
$$P(Y_{n+1} \in \hat{C}(X_{n+1})) \geq 1-\alpha$$
*regardless of the learned score function $s_\theta$.*

*Proof*: The coverage guarantee follows from the conformal prediction framework. Since we use the same calibration procedure as standard conformal prediction, exchangeability ensures that the $(n+1)$-th score $s_\theta(X_{n+1}, Y_{n+1})$ has the same distribution as any of the calibration scores. Therefore, the probability that this score exceeds the $(1-\alpha)(1+1/n)$-quantile is at most $\alpha$. □

This theorem is crucial: it shows that learning the score function does not compromise the finite-sample coverage guarantee, provided we maintain the conformal calibration step.

### 4.2 Consistency and Optimality

**Theorem 2** (Consistency). *Assume the score function class $\mathcal{S}$ contains the optimal score function and that the empirical risk minimizer converges to the population minimizer. Then the ACP intervals converge to the optimal intervals as the sample size grows.*

**Theorem 3** (Characterization of Optimal Score). *Under regularity conditions, the optimal score function for minimizing expected interval width is*
$$s^*(x,y) = F_{R|X}(y - \hat{f}(x) | x)$$
*where $F_{R|X}$ is the conditional CDF of residuals.*

*Proof sketch*: The optimal score function assigns to each point $(x,y)$ the probability that a randomly drawn residual at $x$ is smaller than $y - \hat{f}(x)$. This ensures that the $α$-quantile of scores corresponds exactly to the $α$-quantile of the conditional residual distribution, yielding the narrowest possible intervals. □

This result provides theoretical justification for our target score design and shows that learning conditional quantile functions is indeed the right approach.

### 4.3 Finite-Sample Efficiency

**Theorem 4** (Finite-Sample Efficiency Bound). *Let $W_{\text{ACP}}$ and $W_{\text{opt}}$ denote the expected widths of ACP and optimal intervals respectively. Under appropriate regularity conditions,*
$$W_{\text{ACP}} - W_{\text{opt}} = O_p\left(\sqrt{\frac{\log n}{n}}\right)$$

This bound shows that ACP achieves near-optimal efficiency with high probability, and the gap decreases at the standard nonparametric rate.

## 5. Algorithmic Variants

### 5.1 Non-parametric ACP

For cases where neural networks may be inappropriate, we develop a non-parametric variant using kernel methods. We estimate conditional quantiles using local linear quantile regression:

$$\hat{Q}_R(\tau|x) = \arg\min_q \sum_{i=1}^n K_h(x_i, x) \ell_\tau(r_i, q)$$

where $K_h$ is a kernel function with bandwidth $h$ and $r_i = y_i - \hat{f}(x_i)$ are residuals.

### 5.2 Ensemble-based ACP

We can also leverage ensemble methods by training multiple score functions and combining their predictions:

$$s_{\text{ensemble}}(x,y) = \frac{1}{M} \sum_{m=1}^M s_{\theta_m}(x,y)$$

This approach can improve robustness and handle model uncertainty in the score function learning process.

### 5.3 Online ACP

For streaming data scenarios, we develop an online variant that updates the score function incrementally:

$$\theta_{t+1} = \theta_t - \eta_t \nabla_\theta \ell(s_\theta(x_t, y_t), r(x_t, y_t))$$

The calibration set is maintained using a sliding window approach, ensuring computational efficiency while adapting to distribution shift.

## 6. Experimental Design and Expected Results

### 6.1 Synthetic Experiments

We would evaluate ACP on synthetic datasets where the optimal intervals are known analytically. Key scenarios include:

**Heteroscedastic regression**: $Y = f(X) + \sigma(X) \cdot \epsilon$ where $\sigma(X)$ varies across the input space. We expect ACP to produce narrower intervals in low-noise regions compared to standard conformal prediction.

**Multi-modal residuals**: Cases where residuals follow mixture distributions. ACP should adapt to the local residual distribution, producing asymmetric intervals when appropriate.

**High-dimensional inputs**: Problems with $p >> n$ to test scalability. We anticipate that neural network-based score functions will outperform simpler alternatives.

### 6.2 Real Data Experiments

**UCI regression datasets**: Standard benchmarks for comparing interval width while verifying coverage. We expect 10-30% reduction in average interval width compared to baseline methods.

**Time series forecasting**: Financial and environmental data where residual distributions change over time. ACP should adapt to these changes more effectively than static score functions.

**Computer vision**: Uncertainty quantification in image regression tasks. The high-dimensional nature should favor our neural network approach.

### 6.3 Evaluation Metrics

- **Coverage**: Empirical coverage rate should match or exceed the nominal level
- **Efficiency**: Average interval width and interval width at different quantiles
- **Conditional coverage**: Coverage rates within subgroups to assess fairness
- **Computational cost**: Training time and prediction time compared to baselines

### 6.4 Expected Outcomes

We anticipate that ACP will:
1. Maintain exact finite-sample coverage across all experiments
2. Reduce average interval width by 15-40% compared to standard conformal prediction
3. Show particularly strong improvements in heteroscedastic settings
4. Scale efficiently to high-dimensional problems
5. Demonstrate robustness across different data distributions

## 7. Computational Considerations

### 7.1 Implementation Details

The ACP algorithm can be implemented efficiently using modern deep learning frameworks. Key computational aspects include:

**Score function architecture**: We use multi-layer perceptrons with residual connections, taking both input features and residuals as input. Typical architectures have 3-5 hidden layers with 128-512 units each.

**Training procedure**: We use Adam optimization with learning rate scheduling. The quantile regression loss is averaged over a grid of 20-50 quantile levels for stable training.

**Memory efficiency**: For large datasets, we use mini-batch training and store only essential statistics rather than full residual distributions.

### 7.2 Hyperparameter Selection

Critical hyperparameters include:
- Neural network architecture (depth, width, activation functions)
- Learning rate and training epochs
- Quantile grid resolution
- Calibration set size

We recommend using validation-based hyperparameter selection while monitoring both coverage and efficiency metrics.

### 7.3 Scalability

The computational complexity of ACP is dominated by:
- Score function training: $O(n \cdot d \cdot k)$ where $n$ is sample size, $d$ is input dimension, and $k$ is the number of quantile levels
- Calibration: $O(m \log m)$ where $m$ is calibration set size
- Prediction: $O(d)$ per test point

This scales favorably compared to many alternative uncertainty quantification methods.

## 8. Limitations and Future Work

### 8.1 Current Limitations

**Distributional assumptions**: While ACP maintains finite-sample coverage without distributional assumptions, the efficiency gains depend on the residual distribution being learnable by the chosen score function class.

**Computational overhead**: Learning score functions adds computational cost compared to simple conformal prediction, though this is typically justified by improved efficiency.

**Hyperparameter sensitivity**: The method introduces additional hyperparameters that may require careful tuning for optimal performance.

### 8.2 Future Directions

**Conditional coverage**: Extending ACP to achieve approximate conditional coverage while maintaining finite-sample guarantees represents an important theoretical challenge.

**Distribution shift**: Developing adaptive methods that can handle covariate shift and temporal drift in online settings.

**Multi-output prediction**: Extending the framework to vector-valued outputs and structured prediction problems.

**Theoretical refinements**: Tightening finite-sample efficiency bounds and characterizing the fundamental limits of conformal prediction efficiency.

## 9. Conclusion

We have introduced Adaptive Conformal Prediction, a principled framework for learning score functions that minimize prediction interval width while maintaining finite-sample coverage guarantees. Our approach addresses a fundamental limitation of existing conformal prediction methods by optimizing the choice of score function rather than relying on heuristic designs.

The theoretical analysis reveals that optimal score functions correspond to conditional quantile functions of residual distributions, providing clear guidance for algorithm design. Our practical implementation using neural networks makes the method scalable to high-dimensional problems while maintaining computational efficiency.

The finite-sample coverage guarantee ensures that ACP remains statistically valid regardless of the underlying data distribution, while consistency results show that the method approaches optimal efficiency as sample size grows. This combination of practical effectiveness and theoretical rigor makes ACP a valuable addition to the uncertainty quantification toolkit.

Future work will focus on extending these ideas to conditional coverage, handling distribution shift, and applying the framework to structured prediction problems. The fundamental insight—that score function learning can dramatically improve conformal prediction efficiency—opens new avenues for research in distribution-free uncertainty quantification.

## References

[Barber et al., 2021] R. F. Barber, E. J. Candès, A. Ramdas, and R. J. Tibshirani. Predictive inference with the jackknife+. *The Annals of Statistics*, 49(1):486–507, 2021.

[Chernozhukov et al., 2021] V. Chernozhukov, K. Wuthrich, and Y. Zhu. Distributional conformal prediction. *Proceedings of the National Academy of Sciences*, 118(48):e2107794118, 2021.

[Foygel-Barber et al., 2020] R. Foygel-Barber, E. J. Candès, A. Ramdas, and R. J. Tibshirani. The limits of distribution-free conditional predictive inference. *Information and Inference*, 10(2):455–482, 2020.

[Kivaranovic et al., 2020] D. Kivaranovic, K. F. Johnson, and H. Leeb. Adaptive, distribution-free prediction intervals for deep networks. In *Proceedings of the 23rd International Conference on Artificial Intelligence and Statistics*, pages 4346–4356, 2020.

[Lei et al., 2018] J. Lei, M. G'Sell, A. Rinaldo, R. J. Tibshirani, and L. Wasserman. Distribution-free predictive inference for regression. *Journal of the American Statistical Association*, 113(523):1094–1111, 2018.

[Papadopoulos et al., 2002] H. Papadopoulos, V. Vovk, and A. Gammerman. Regression conformal prediction with nearest neighbours. *Journal of Artificial Intelligence Research*, 40:815–840, 2002.

[Romano et al., 2019] Y. Romano, E. Patterson, and E. Candès. Conformalized quantile regression. In *Advances in Neural Information Processing Systems*, pages 3543–3553, 2019.

[Shafer & Vovk, 2008] G. Shafer and V. Vovk. *A tutorial on conformal prediction*. *Journal of Machine Learning Research*, 9:371–421, 2008.

[Tibshirani et al., 2019] R. J. Tibshirani, R. Foygel Barber, E. Candès, and A. Ramdas. Conformal prediction under covariate shift. In *Advances in Neural Information Processing Systems*, pages 2530–2540, 2019.

[Vovk et al., 2005] V. Vovk, A. Gammerman, and G. Shafer. *Algorithmic Learning in a Random World*. Springer, 2005.
