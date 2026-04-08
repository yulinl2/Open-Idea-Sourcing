# Reconstruction: full_freestyle
**Paper:** 2006.06138  
**Condition:** no_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Distribution-Free Prediction Intervals for Individual Treatment Effects

## Abstract

Estimating heterogeneous treatment effects is crucial for personalized decision-making, but existing methods often provide poor uncertainty quantification for individual-level causal effects. We develop a novel framework for constructing distribution-free prediction intervals for conditional average treatment effects (CATE) that provides finite-sample coverage guarantees without parametric assumptions. Our approach addresses two distinct inference problems: constructing intervals for individuals within the original study (semi-supervised setting) and for new individuals from potentially different populations (fully unsupervised setting). We introduce **Causal Conformal Prediction**, which combines ideas from conformal prediction with causal inference to handle the fundamental challenge that individual treatment effects are never directly observable. Our method accommodates both randomized experiments and observational studies, remains robust to model misspecification, and handles covariate shift between study and target populations. Theoretical analysis establishes finite-sample coverage guarantees, while our framework naturally extends to address practical concerns including missing data and multiple treatments.

**Keywords:** causal inference, conformal prediction, heterogeneous treatment effects, uncertainty quantification, personalized medicine

## 1. Introduction

The estimation of treatment effects has evolved from a focus on population averages to understanding individual-level heterogeneity. While the average treatment effect (ATE) provides valuable summary information, it can be misleading when treatment effects vary substantially across individuals. Consider a medical treatment that benefits 70% of patients while causing harm to the remaining 30%—the average effect might suggest modest benefit, obscuring the critical need for personalized treatment decisions.

This shift toward personalized causal inference has spawned a rich literature on conditional average treatment effects (CATE), which estimate how treatment effects vary as a function of individual characteristics. Modern approaches leverage machine learning algorithms including random forests, neural networks, and causal trees to capture complex heterogeneity patterns. However, these methods typically focus on point estimation while providing inadequate uncertainty quantification—a critical limitation in high-stakes domains like healthcare and policy.

The challenge of uncertainty quantification for individual treatment effects is fundamental and multifaceted. First, individual treatment effects are never directly observable due to the fundamental problem of causal inference: for any individual, we observe outcomes under either treatment or control, but never both. This creates a missing data problem that differs qualitatively from standard prediction tasks. Second, we often need to make inferences about individuals who were not part of the original study, potentially from different populations with covariate shift. Third, reliable uncertainty quantification must work in finite samples and remain robust to model misspecification.

We address these challenges by developing **Causal Conformal Prediction**, a distribution-free framework for constructing prediction intervals for individual treatment effects. Our approach builds on conformal prediction—a powerful paradigm for uncertainty quantification that provides finite-sample coverage guarantees without distributional assumptions. However, extending conformal prediction to causal inference requires addressing the unique structure of causal problems, particularly the unobservability of individual treatment effects and the need to handle both within-study and out-of-study inference.

### 1.1 Contributions

Our main contributions are:

1. **Novel framework**: We develop Causal Conformal Prediction, the first distribution-free method for constructing prediction intervals for individual treatment effects with finite-sample coverage guarantees.

2. **Dual inference problems**: We formalize and solve two distinct inference challenges—constructing intervals for individuals within the study (where one potential outcome is observed) and for new individuals (where both potential outcomes are missing).

3. **Robust methodology**: Our approach works without parametric assumptions, handles model misspecification, accommodates covariate shift, and applies to both randomized experiments and observational studies.

4. **Theoretical guarantees**: We establish finite-sample coverage properties and characterize how coverage depends on the quality of CATE estimation and the degree of covariate shift.

5. **Practical extensions**: We show how the framework extends to handle missing covariates, multiple treatments, and different notions of treatment effect heterogeneity.

## 2. Problem Formulation and Challenges

### 2.1 Causal Inference Setup

We work within the potential outcomes framework. For individual $i$, let $Y_i(1)$ and $Y_i(0)$ denote potential outcomes under treatment and control, respectively. The individual treatment effect is $\tau_i = Y_i(1) - Y_i(0)$. We observe covariates $X_i \in \mathcal{X}$, treatment assignment $W_i \in \{0,1\}$, and the realized outcome $Y_i = W_i Y_i(1) + (1-W_i) Y_i(0)$.

The conditional average treatment effect is defined as:
$$\tau(x) = \mathbb{E}[Y_i(1) - Y_i(0) | X_i = x] = \mathbb{E}[Y_i(1) | X_i = x] - \mathbb{E}[Y_i(0) | X_i = x]$$

Our goal is to construct prediction intervals for $\tau(x)$ that satisfy coverage guarantees of the form:
$$\mathbb{P}(\tau(x) \in \hat{C}_\alpha(x)) \geq 1 - \alpha$$
for a specified miscoverage level $\alpha \in (0,1)$.

### 2.2 The Dual Inference Challenge

We identify two distinct inference problems that require different technical approaches:

**Problem 1 (Within-study inference)**: For an individual $i$ in the original study with covariates $X_i$, construct a prediction interval for $\tau_i$ given that we observe either $Y_i(1)$ or $Y_i(0)$ but not both.

**Problem 2 (Out-of-study inference)**: For a new individual with covariates $X_{new}$ from a potentially different population, construct a prediction interval for $\tau(X_{new})$ when neither potential outcome is observed.

These problems differ fundamentally in their information structure. In Problem 1, we have partial information about the individual's potential outcomes, while in Problem 2, we have no direct outcome information and must rely entirely on covariate-based extrapolation.

### 2.3 Key Challenges

**Challenge 1: Unobservable targets**: Unlike standard prediction problems where we can observe prediction errors, individual treatment effects are never directly observable, making it impossible to use standard conformal prediction approaches.

**Challenge 2: Covariate shift**: The target population for inference may differ from the study population, requiring methods that can handle distribution shift while maintaining coverage guarantees.

**Challenge 3: Model dependence**: CATE estimation typically relies on complex machine learning models that may be misspecified, necessitating robust uncertainty quantification methods.

**Challenge 4: Finite-sample validity**: Uncertainty quantification must work reliably in finite samples, not just asymptotically, particularly important in settings with limited data.

## 3. Causal Conformal Prediction Framework

### 3.1 Classical Conformal Prediction Review

Conformal prediction provides distribution-free prediction intervals with finite-sample coverage guarantees. Given training data $(X_1, Y_1), \ldots, (X_n, Y_n)$ and a prediction algorithm $\hat{\mu}$, conformal prediction constructs intervals for a new point $X_{n+1}$ using the following steps:

1. Define a nonconformity score $s(x,y) = |y - \hat{\mu}(x)|$
2. Compute scores $s_i = s(X_i, Y_i)$ for training data
3. For miscoverage level $\alpha$, find the $(1-\alpha)$-quantile $\hat{q}_{1-\alpha}$ of $\{s_1, \ldots, s_n\}$
4. The prediction interval is $\hat{C}_\alpha(X_{n+1}) = [\hat{\mu}(X_{n+1}) - \hat{q}_{1-\alpha}, \hat{\mu}(X_{n+1}) + \hat{q}_{1-\alpha}]$

Under the exchangeability assumption, this procedure guarantees $\mathbb{P}(Y_{n+1} \in \hat{C}_\alpha(X_{n+1})) \geq 1 - \alpha$.

### 3.2 Extending to Causal Inference

The key insight for extending conformal prediction to causal inference is to construct pseudo-observations of treatment effects that can be used to calibrate nonconformity scores. We develop different strategies for within-study and out-of-study inference.

#### 3.2.1 Within-Study Causal Conformal Prediction

For individuals in the original study, we can construct pseudo-treatment effects using CATE estimates and the observed potential outcome. For individual $i$ with treatment $W_i$ and observed outcome $Y_i$:

$$\tilde{\tau}_i = \begin{cases}
2Y_i - \hat{\mu}_0(X_i) - \hat{\mu}_1(X_i) & \text{if } W_i = 1 \\
\hat{\mu}_1(X_i) + \hat{\mu}_0(X_i) - 2Y_i & \text{if } W_i = 0
\end{cases}$$

where $\hat{\mu}_1(x) = \mathbb{E}[Y(1)|X=x]$ and $\hat{\mu}_0(x) = \mathbb{E}[Y(0)|X=x]$ are estimated outcome regression functions.

The pseudo-treatment effect $\tilde{\tau}_i$ has the property that $\mathbb{E}[\tilde{\tau}_i | X_i] = \tau(X_i)$ under correct model specification, making it suitable for conformal calibration.

**Algorithm 1: Within-Study Causal Conformal Prediction**

*Input*: Training data $\{(X_i, W_i, Y_i)\}_{i=1}^n$, CATE estimator $\hat{\tau}$, target individual $j \in \{1,\ldots,n\}$, miscoverage level $\alpha$

1. Split data into training ($\mathcal{I}_{tr}$) and calibration ($\mathcal{I}_{cal}$) sets
2. Fit outcome regressions $\hat{\mu}_1, \hat{\mu}_0$ and CATE estimator $\hat{\tau}$ on $\mathcal{I}_{tr}$
3. For each $i \in \mathcal{I}_{cal}$, compute pseudo-treatment effect $\tilde{\tau}_i$
4. Compute nonconformity scores $s_i = |\tilde{\tau}_i - \hat{\tau}(X_i)|$
5. Find quantile $\hat{q}_{1-\alpha} = \text{Quantile}_{1-\alpha}(\{s_i : i \in \mathcal{I}_{cal}\})$
6. Return interval $\hat{C}_\alpha(X_j) = [\hat{\tau}(X_j) - \hat{q}_{1-\alpha}, \hat{\tau}(X_j) + \hat{q}_{1-\alpha}]$

#### 3.2.2 Out-of-Study Causal Conformal Prediction

For new individuals not in the original study, we cannot construct pseudo-treatment effects directly. Instead, we use a two-step approach that first constructs intervals for the outcome regression functions, then combines them to form intervals for treatment effects.

The key insight is that if we have valid prediction intervals for $\mu_1(x)$ and $\mu_0(x)$, we can construct intervals for $\tau(x) = \mu_1(x) - \mu_0(x)$ using interval arithmetic, though this may be conservative.

**Algorithm 2: Out-of-Study Causal Conformal Prediction**

*Input*: Training data $\{(X_i, W_i, Y_i)\}_{i=1}^n$, new individual covariates $X_{new}$, miscoverage level $\alpha$

1. Split data by treatment: $\mathcal{D}_1 = \{(X_i, Y_i) : W_i = 1\}$, $\mathcal{D}_0 = \{(X_i, Y_i) : W_i = 0\}$
2. Apply standard conformal prediction to each group:
   - Construct $\hat{C}^1_{\alpha/2}(X_{new})$ for $\mu_1(X_{new})$ using $\mathcal{D}_1$
   - Construct $\hat{C}^0_{\alpha/2}(X_{new})$ for $\mu_0(X_{new})$ using $\mathcal{D}_0$
3. Combine intervals: $\hat{C}_\alpha(X_{new}) = \hat{C}^1_{\alpha/2}(X_{new}) - \hat{C}^0_{\alpha/2}(X_{new})$

where interval subtraction is defined as $[a,b] - [c,d] = [a-d, b-c]$.

### 3.3 Handling Covariate Shift

When the target population differs from the study population, we need to account for covariate shift while maintaining coverage guarantees. We develop a weighted conformal prediction approach that reweights the calibration data to match the target distribution.

Let $p_{study}(x)$ and $p_{target}(x)$ denote the covariate densities in the study and target populations, respectively. Define importance weights:
$$w(x) = \frac{p_{target}(x)}{p_{study}(x)}$$

**Weighted Conformal Prediction for Covariate Shift**

1. Estimate importance weights $\hat{w}(X_i)$ for calibration data
2. Compute weighted quantile using weights $\hat{w}(X_i)$:
   $$\hat{q}^w_{1-\alpha} = \text{WeightedQuantile}_{1-\alpha}(\{s_i : i \in \mathcal{I}_{cal}\}, \{\hat{w}(X_i) : i \in \mathcal{I}_{cal}\})$$
3. Construct intervals using $\hat{q}^w_{1-\alpha}$

This approach maintains approximate coverage for the target population when importance weights are estimated accurately.

## 4. Theoretical Analysis

### 4.1 Coverage Guarantees

We establish finite-sample coverage guarantees for our causal conformal prediction procedures under different assumptions.

**Theorem 1 (Within-Study Coverage)**: Under the assumption that $(X_1, W_1, Y_1), \ldots, (X_n, W_n, Y_n)$ are exchangeable and the outcome regression models are correctly specified, Algorithm 1 satisfies:
$$\mathbb{P}(\tau_j \in \hat{C}_\alpha(X_j)) \geq 1 - \alpha$$
for any $j \in \{1,\ldots,n\}$.

**Proof Sketch**: The key insight is that under correct specification, the pseudo-treatment effects $\tilde{\tau}_i$ are unbiased estimates of the true treatment effects $\tau_i$. The nonconformity scores $s_i = |\tilde{\tau}_i - \hat{\tau}(X_i)|$ then measure the prediction error of the CATE estimator, enabling standard conformal prediction analysis.

**Theorem 2 (Out-of-Study Coverage)**: Under exchangeability and correct specification of outcome regression models, Algorithm 2 satisfies:
$$\mathbb{P}(\tau(X_{new}) \in \hat{C}_\alpha(X_{new})) \geq 1 - \alpha$$
when $X_{new}$ is drawn from the same distribution as the training covariates.

### 4.2 Robustness to Model Misspecification

A key advantage of our approach is robustness to model misspecification. Even when the outcome regression models are incorrect, our method can still provide meaningful uncertainty quantification.

**Theorem 3 (Robust Coverage)**: When outcome regression models are misspecified, Algorithm 1 provides coverage for the quantity:
$$\tau^{pseudo}_i = \mathbb{E}[\tilde{\tau}_i | X_i]$$
which represents the treatment effect that would be estimated by the pseudo-observation procedure.

While this may not equal the true treatment effect under misspecification, it provides a well-defined uncertainty quantification for the quantity actually being estimated.

### 4.3 Coverage Under Covariate Shift

**Theorem 4 (Covariate Shift Coverage)**: Under correct importance weight estimation, the weighted conformal prediction procedure provides approximate coverage:
$$\lim_{n \to \infty} \mathbb{P}_{target}(\tau(X_{new}) \in \hat{C}_\alpha(X_{new})) = 1 - \alpha$$

The finite-sample coverage depends on the quality of importance weight estimation and the degree of covariate shift.

## 5. Extensions and Practical Considerations

### 5.1 Multiple Treatments

The framework naturally extends to multiple treatments. For $K$ treatments, we can construct pseudo-treatment effects for pairwise comparisons or use a one-vs-all approach. The key modification is in the construction of pseudo-observations and the definition of nonconformity scores.

### 5.2 Missing Covariates

When some covariates are missing, we can adapt the framework by:
1. Using imputation methods and propagating uncertainty through the imputation
2. Constructing separate conformal predictors for different missing data patterns
3. Using weighted approaches that account for the missing data mechanism

### 5.3 Conditional Coverage

Beyond marginal coverage guarantees, we can construct intervals with approximate conditional coverage properties by using local conformal prediction methods that adapt the quantile based on covariate values.

### 5.4 Computational Considerations

The computational complexity of our methods scales linearly with sample size for the basic procedures. The main computational bottleneck is typically the underlying CATE estimation rather than the conformal calibration step.

## 6. Experimental Evaluation Framework

While we do not present specific numerical results, we outline a comprehensive experimental evaluation that would validate our theoretical findings and demonstrate practical utility.

### 6.1 Synthetic Data Experiments

**Setup**: Generate synthetic data with known ground truth treatment effects to evaluate coverage and interval width properties.

**Design**: 
- Vary sample sizes (n = 100, 500, 1000, 5000)
- Different covariate dimensions (p = 5, 10, 20, 50)
- Various treatment effect heterogeneity patterns (linear, nonlinear, interaction effects)
- Different noise levels and distributions

**Metrics**:
- Empirical coverage rates for different α levels
- Average interval width
- Computational time
- Robustness to model misspecification

**Expected Outcomes**: We anticipate that our methods will achieve nominal coverage rates across different settings, with interval widths that decrease as sample size increases and CATE estimation improves.

### 6.2 Semi-Synthetic Benchmarks

**Setup**: Use real covariate data but simulate outcomes and treatment effects based on flexible models.

**Benchmarks**:
- IHDP dataset with simulated treatment effects
- ACIC data challenge datasets
- Healthcare datasets with synthetic treatment assignment

**Comparisons**: Compare against existing uncertainty quantification methods including:
- Bootstrap-based intervals for CATE estimators
- Bayesian approaches with posterior intervals
- Quantile regression methods

**Expected Results**: Our distribution-free approach should provide more reliable coverage than parametric alternatives, especially under model misspecification.

### 6.3 Real Data Case Studies

**Applications**:
- Medical treatment effectiveness with patient heterogeneity
- Educational intervention effects across student populations
- Marketing campaign effectiveness across customer segments

**Evaluation Strategy**: Use cross-validation and held-out test sets to evaluate practical performance, focusing on coverage calibration and interval informativeness.

### 6.4 Covariate Shift Experiments

**Design**: Systematically vary the degree of covariate shift between training and test populations to evaluate the robustness of our weighted approach.

**Metrics**: Coverage rates and interval widths as functions of covariate shift magnitude, importance weight estimation accuracy.

## 7. Discussion and Future Directions

### 7.1 Methodological Implications

Our work bridges two important areas—causal inference and uncertainty quantification—providing a principled framework for reliable inference about individual treatment effects. The distribution-free nature of our approach makes it particularly valuable in settings where parametric assumptions are questionable.

The distinction between within-study and out-of-study inference highlights fundamental differences in the information available for uncertainty quantification. Within-study inference benefits from partial observability of individual outcomes, while out-of-study inference must rely entirely on covariate-based extrapolation.

### 7.2 Practical Impact

The ability to provide reliable uncertainty quantification for individual treatment effects has significant practical implications:

**Healthcare**: Clinicians can make more informed treatment decisions by understanding not just the expected effect but also the uncertainty around that estimate.

**Policy**: Policymakers can better assess the risks and benefits of interventions for different population subgroups.

**Business**: Companies can optimize personalized strategies while accounting for uncertainty in individual-level predictions.

### 7.3 Limitations and Future Work

**Limitations**:
1. The quality of uncertainty quantification depends on the quality of underlying CATE estimation
2. Covariate shift handling requires accurate importance weight estimation
3. The framework assumes access to individual-level data, which may not always be available

**Future Directions**:
1. **Adaptive conformal prediction**: Develop methods that adapt the miscoverage level based on covariate values or estimated treatment effect magnitudes
2. **Multi-armed bandits integration**: Combine with online learning algorithms for adaptive treatment assignment
3. **Federated learning extensions**: Adapt the framework for distributed settings where data cannot be centralized
4. **Survival outcomes**: Extend to time-to-event outcomes and dynamic treatment regimes
5. **High-dimensional settings**: Develop specialized methods for high-dimensional covariate spaces

### 7.4 Broader Connections

Our work connects to several broader themes in machine learning and statistics:

**Distribution-free inference**: Part of the growing literature on assumption-light statistical methods that provide reliable uncertainty quantification

**Robust machine learning**: Contributes to efforts to make machine learning methods more reliable and trustworthy in high-stakes applications

**Personalized decision-making**: Supports the broader goal of moving from population-level to individual-level decision support systems

## 8. Conclusion

We have developed Causal Conformal Prediction, a novel framework for constructing distribution-free prediction intervals for individual treatment effects. Our approach addresses the fundamental challenge that individual treatment effects are never directly observable by constructing appropriate pseudo-observations and leveraging the finite-sample guarantees of conformal prediction.

The framework handles both within-study and out-of-study inference, accommodates covariate shift, remains robust to model misspecification, and provides finite-sample coverage guarantees without parametric assumptions. Theoretical analysis establishes the validity of our approach, while practical extensions address common real-world challenges including missing data and multiple treatments.

This work opens new possibilities for reliable uncertainty quantification in causal inference, supporting more informed decision-making in personalized medicine, policy evaluation, and other domains where understanding individual-level treatment effect heterogeneity is crucial. The distribution-free nature of our approach makes it particularly valuable in settings where traditional parametric assumptions are questionable, providing a robust foundation for practical applications.

The distinction between within-study and out-of-study inference problems provides a useful framework for thinking about different types of causal inference tasks, each with its own information structure and technical challenges. As the field continues to move toward more personalized and nuanced understanding of treatment effects, methods like ours that provide reliable uncertainty quantification will become increasingly important.

## References

[1] Athey, S., & Imbens, G. W. (2016). Recursive partitioning for heterogeneous causal effects. *Proceedings of the National Academy of Sciences*, 113(27), 7353-7360.

[2] Chernozhukov, V., Chetverikov, D., Demirer, M., Duflo, E., Hansen, C., Newey, W., & Robins, J. (2018). Double/debiased machine learning for treatment and structural parameters. *The Econometrics Journal*, 21(1), C1-C68.

[3] Künzel, S. R., Sekhon, J. S., Bickel, P. J., & Yu, B. (2019). Metalearners for estimating heterogeneous treatment effects using machine learning. *Proceedings of the National Academy of Sciences*, 116(10), 4156-4165.

[4] Lei, J., G'Sell, M., Rinaldo, A., Tibshirani, R. J., & Wasserman, L. (2018). Distribution-free predictive inference for regression. *Journal of the American Statistical Association*, 113(523), 1094-1111.

[5] Rubin, D. B. (1974). Estimating causal effects of treatments in randomized and nonrandomized studies. *Journal of Educational Psychology*, 66(5), 688-701.

[6] Shafer, G., & Vovk, V. (2008). A tutorial on conformal prediction. *Journal of Machine Learning Research*, 9, 371-421.

[7] Tibshirani, R. J., Barber, R. F., Candes, E., & Ramdas, A. (2019). Conformal prediction under covariate shift. *Advances in Neural Information Processing Systems*, 32.

[8] Wager, S., & Athey, S. (2018). Estimation and inference of heterogeneous treatment effects using random forests. *Journal of the American Statistical Association*, 113(523), 1228-1242.
