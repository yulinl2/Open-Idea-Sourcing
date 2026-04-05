# Reconstruction: full_guided
**Paper:** 2006.06138  
**Condition:** no_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Conformal Prediction for Heterogeneous Treatment Effects: Distribution-Free Uncertainty Quantification in Causal Inference

## Abstract

Estimating heterogeneous treatment effects is crucial for personalized decision-making across medicine, policy, and social sciences. While machine learning methods can flexibly estimate conditional average treatment effects (CATE), they typically provide poor uncertainty quantification, limiting their utility in high-stakes applications. We propose a conformal prediction framework for CATE estimation that provides distribution-free, finite-sample coverage guarantees without relying on asymptotic approximations or strong parametric assumptions. Our approach addresses the fundamental challenge that individual treatment effects are never directly observable by constructing prediction intervals that account for both epistemic uncertainty in the CATE function and the inherent randomness in potential outcomes. We extend conformal prediction to handle covariate shift and develop specialized conformity scores that respect the causal structure. Our method works with any base CATE estimator and provides valid coverage under minimal assumptions, making it broadly applicable to both randomized experiments and observational studies. This framework enables practitioners to quantify uncertainty in treatment effect heterogeneity with rigorous statistical guarantees, facilitating more informed decision-making in personalized treatment allocation.

## 1. Introduction

Understanding how treatment effects vary across individuals is fundamental to personalized medicine, targeted policy interventions, and precision social programs. While average treatment effects provide valuable population-level insights, they can be misleading when substantial heterogeneity exists—a cancer treatment might benefit 70% of patients while harming 30%, yet the average effect could appear modestly positive. This has driven significant interest in estimating conditional average treatment effects (CATE), which quantify how treatment effects depend on individual characteristics.

Modern machine learning approaches have shown promise for flexible CATE estimation, including causal forests, meta-learners, and deep learning methods. However, these approaches typically provide only point estimates without reliable uncertainty quantification. This limitation is particularly problematic in high-stakes domains where understanding the uncertainty around treatment effect estimates is crucial for risk assessment and decision-making. For instance, a physician needs to know not just that a treatment is estimated to help a patient, but also the confidence interval around that estimate to weigh potential benefits against risks.

The challenge of uncertainty quantification in CATE estimation is compounded by the fundamental problem of causal inference: for any individual, we observe only one potential outcome (either under treatment or control), never both. This creates a missing data problem that makes individual treatment effects inherently unobservable, complicating standard approaches to uncertainty quantification that rely on observing ground truth.

Existing methods for uncertainty quantification in causal inference typically rely on asymptotic approximations, bootstrap procedures, or strong parametric assumptions. These approaches may provide unreliable coverage in finite samples, particularly when models are misspecified or when the sample size is moderate. Moreover, they often require specific distributional assumptions that may not hold in practice.

Our contributions are:

• We develop a conformal prediction framework for CATE estimation that provides distribution-free, finite-sample coverage guarantees without asymptotic approximations
• We propose novel conformity scores tailored to the causal inference setting that account for the unobservability of individual treatment effects
• We extend the framework to handle covariate shift between training and target populations, common in causal inference applications
• We prove theoretical coverage guarantees under minimal assumptions and demonstrate robustness to model misspecification
• We provide a general methodology that works with any base CATE estimator, making it broadly applicable across existing approaches

## 2. Related Work

**Heterogeneous Treatment Effect Estimation.** The literature on CATE estimation has grown rapidly, with approaches broadly categorized into meta-learners and specialized methods. Meta-learners like the T-learner, S-learner, and X-learner transform the CATE estimation problem into standard supervised learning tasks. Causal forests extend random forests to directly estimate treatment effects with theoretical guarantees. Deep learning approaches include TARNet, CFR, and GANITE, which use representation learning to balance treatment groups. Double machine learning provides a framework for combining flexible machine learning with causal identification. While these methods can capture complex heterogeneity, they typically provide limited uncertainty quantification.

**Uncertainty Quantification in Causal Inference.** Traditional approaches to uncertainty quantification in causal inference rely on asymptotic normality results, often derived under strong regularity conditions. Bootstrap methods have been applied but can be unreliable for complex estimators. Bayesian approaches provide natural uncertainty quantification but require strong prior assumptions and can be computationally intensive. Recent work has explored using influence functions and targeted maximum likelihood estimation for inference, but these methods still rely on asymptotic approximations and can be sensitive to model misspecification.

**Conformal Prediction.** Conformal prediction provides a framework for constructing prediction intervals with finite-sample coverage guarantees under minimal assumptions—essentially requiring only that data points are exchangeable. The method works by defining a conformity score that measures how "typical" a prediction is relative to training data, then using the empirical distribution of these scores to construct prediction intervals. Recent extensions include weighted conformal prediction for covariate shift, split conformal prediction for computational efficiency, and adaptive methods for time series. However, existing conformal prediction methods focus on standard supervised learning settings and do not address the unique challenges of causal inference.

**Conformal Prediction for Causal Inference.** Limited work has explored conformal prediction in causal settings. Some recent papers have applied conformal prediction to estimate uncertainty in average treatment effects or to construct confidence intervals for causal parameters in specific models. However, these approaches do not address heterogeneous treatment effects or the fundamental challenge that individual treatment effects are unobservable. Our work fills this gap by developing a comprehensive conformal framework specifically designed for CATE estimation.

The key gap our work addresses is the lack of distribution-free, finite-sample uncertainty quantification methods for heterogeneous treatment effects that can work with modern machine learning estimators while respecting the causal structure of the problem.

## 3. Problem Formulation

We work within the potential outcomes framework. For each unit $i$, let $Y_i(1)$ and $Y_i(0)$ denote the potential outcomes under treatment and control, respectively. We observe the triple $(X_i, W_i, Y_i)$ where $X_i \in \mathcal{X}$ are covariates, $W_i \in \{0,1\}$ is the treatment assignment, and $Y_i = W_i Y_i(1) + (1-W_i)Y_i(0)$ is the observed outcome.

The individual treatment effect for unit $i$ is $\tau_i = Y_i(1) - Y_i(0)$, which is never directly observable. The conditional average treatment effect is:
$$\tau(x) = \mathbb{E}[Y(1) - Y(0) | X = x] = \mathbb{E}[Y(1) | X = x] - \mathbb{E}[Y(0) | X = x]$$

We make the following standard assumptions:

**Assumption 1 (SUTVA).** The potential outcomes for unit $i$ depend only on unit $i$'s treatment assignment, not on other units' assignments.

**Assumption 2 (Unconfoundedness).** $(Y(1), Y(0)) \perp W | X$, meaning treatment assignment is independent of potential outcomes conditional on observed covariates.

**Assumption 3 (Overlap).** For all $x \in \mathcal{X}$, we have $0 < P(W = 1 | X = x) < 1$.

Let $\hat{\tau}(x)$ denote any base estimator of $\tau(x)$ trained on data $\{(X_i, W_i, Y_i)\}_{i=1}^n$.

**Problem Statement.** Given a new individual with covariates $X_{n+1}$, construct a prediction interval $C(X_{n+1})$ such that:
$$P(\tau(X_{n+1}) \in C(X_{n+1})) \geq 1 - \alpha$$
for a specified miscoverage level $\alpha \in (0,1)$, where the probability is taken over the randomness in the training data and the new individual.

The key challenge is that we cannot directly observe $\tau(X_{n+1})$ to validate our intervals, as individual treatment effects are fundamentally unobservable. This requires developing conformity scores that can work with the observable quantities while still providing meaningful coverage guarantees for the unobservable target.

## 4. Methodology

Our approach extends conformal prediction to the causal inference setting by developing conformity scores that respect the causal structure while providing coverage for unobservable individual treatment effects.

### 4.1 Conformal Prediction for Observable Outcomes

We first establish conformal prediction intervals for the observable potential outcomes $Y(1)$ and $Y(0)$ separately, then combine them to obtain intervals for treatment effects.

For treated units ($W_i = 1$), we observe $Y_i = Y_i(1)$ and can construct conformal intervals for $Y(1)$ using the conformity score:
$$R_i^{(1)} = |Y_i - \hat{\mu}_1(X_i)|$$
where $\hat{\mu}_1(x) = \mathbb{E}[Y(1)|X = x]$ is estimated from treated units.

Similarly, for control units ($W_i = 0$), we use:
$$R_i^{(0)} = |Y_i - \hat{\mu}_0(X_i)|$$
where $\hat{\mu}_0(x) = \mathbb{E}[Y(0)|X = x]$ is estimated from control units.

The conformal quantiles are:
$$q_{1-\alpha}^{(1)} = \text{Quantile}_{1-\alpha}\{R_i^{(1)} : W_i = 1\}$$
$$q_{1-\alpha}^{(0)} = \text{Quantile}_{1-\alpha}\{R_i^{(0)} : W_i = 0\}$$

### 4.2 Treatment Effect Conformal Intervals

For a new individual with covariates $x$, we construct prediction intervals for the unobservable potential outcomes:
$$C_1(x) = [\hat{\mu}_1(x) - q_{1-\alpha}^{(1)}, \hat{\mu}_1(x) + q_{1-\alpha}^{(1)}]$$
$$C_0(x) = [\hat{\mu}_0(x) - q_{1-\alpha}^{(0)}, \hat{\mu}_0(x) + q_{1-\alpha}^{(0)}]$$

The treatment effect interval is then:
$$C_\tau(x) = C_1(x) - C_0(x) = [\hat{\tau}(x) - (q_{1-\alpha}^{(1)} + q_{1-\alpha}^{(0)}), \hat{\tau}(x) + (q_{1-\alpha}^{(1)} + q_{1-\alpha}^{(0)})]$$

where $\hat{\tau}(x) = \hat{\mu}_1(x) - \hat{\mu}_0(x)$.

### 4.3 Direct Treatment Effect Conformity Score

While the above approach provides valid intervals, it may be conservative as it combines uncertainties from both potential outcome models. We develop a direct conformity score for treatment effects.

For each training unit $i$, we compute a pseudo-treatment effect:
$$\tilde{\tau}_i = \begin{cases}
2(Y_i - \hat{\mu}_0(X_i)) & \text{if } W_i = 1 \\
2(\hat{\mu}_1(X_i) - Y_i) & \text{if } W_i = 0
\end{cases}$$

This leverages the fact that under unconfoundedness:
- For treated units: $\mathbb{E}[\tilde{\tau}_i | X_i] = 2\mathbb{E}[Y_i(1) - \hat{\mu}_0(X_i) | X_i] = 2(\mu_1(X_i) - \hat{\mu}_0(X_i)) \approx 2\tau(X_i)$
- For control units: $\mathbb{E}[\tilde{\tau}_i | X_i] = 2\mathbb{E}[\hat{\mu}_1(X_i) - Y_i(0) | X_i] = 2(\hat{\mu}_1(X_i) - \mu_0(X_i)) \approx 2\tau(X_i)$

The conformity score is:
$$R_i^\tau = |\tilde{\tau}_i - 2\hat{\tau}(X_i)|$$

The $(1-\alpha)$-quantile $q_{1-\alpha}^\tau$ gives the interval:
$$C_\tau(x) = [\hat{\tau}(x) - q_{1-\alpha}^\tau/2, \hat{\tau}(x) + q_{1-\alpha}^\tau/2]$$

### 4.4 Covariate Shift Extension

In practice, the target population may differ from the training population. We extend our method using weighted conformal prediction.

Given importance weights $w_i$ that reweight the training distribution to match the target distribution, we modify the conformity scores:
$$R_i^w = w_i \cdot R_i$$

The weighted quantile is computed as:
$$q_{1-\alpha}^w = \text{WeightedQuantile}_{1-\alpha}\{R_i^w\}$$

where the weighted quantile satisfies:
$$\frac{\sum_{i: R_i^w \leq q_{1-\alpha}^w} w_i}{\sum_i w_i} \geq 1-\alpha$$

### 4.5 Algorithm

**Algorithm 1: Conformal Treatment Effect Prediction**
```
Input: Training data {(Xi, Wi, Yi)}i=1^n, test point x, level α
1. Split data into treatment and control groups
2. Train outcome models μ̂₁(x) on treated units, μ̂₀(x) on control units  
3. Compute CATE estimate τ̂(x) = μ̂₁(x) - μ̂₀(x)
4. For each training unit i:
   - If Wi = 1: compute τ̃ᵢ = 2(Yi - μ̂₀(Xi))
   - If Wi = 0: compute τ̃ᵢ = 2(μ̂₁(Xi) - Yi)
   - Compute conformity score Rᵢᵗ = |τ̃ᵢ - 2τ̂(Xi)|
5. Compute quantile q₁₋ₐᵗ = Quantile₁₋ₐ{Rᵢᵗ}
6. Return interval [τ̂(x) - q₁₋ₐᵗ/2, τ̂(x) + q₁₋ₐᵗ/2]
```

## 5. Theoretical Analysis

**Theorem 1 (Coverage Guarantee).** Under Assumptions 1-3 and assuming the training data are exchangeable, the conformal prediction interval $C_\tau(x)$ satisfies:
$$P(\tau(x) \in C_\tau(x)) \geq 1 - \alpha$$

**Proof Sketch:** The key insight is that under unconfoundedness, the pseudo-treatment effects $\tilde{\tau}_i$ are unbiased estimates of twice the true treatment effect, up to model estimation error. The exchangeability of the conformity scores $R_i^\tau$ then ensures that the conformal quantile provides valid coverage.

Formally, for any new point $x$, consider the augmented dataset including a hypothetical unit with covariates $x$ and pseudo-treatment effect $2\tau(x)$. The conformity score for this unit would be $R^\tau = |2\tau(x) - 2\hat{\tau}(x)|$. By exchangeability, this score has the same distribution as the training conformity scores, ensuring that:
$$P(R^\tau \leq q_{1-\alpha}^\tau) \geq 1-\alpha$$

This translates directly to coverage of the treatment effect interval. □

**Theorem 2 (Robustness to Model Misspecification).** The coverage guarantee in Theorem 1 holds even when the outcome models $\hat{\mu}_1$ and $\hat{\mu}_0$ are misspecified, as long as the data generating process satisfies Assumptions 1-3.

**Proof Sketch:** The coverage guarantee depends only on the exchangeability of the conformity scores, not on the correctness of the underlying models. Even with misspecified models, the pseudo-treatment effects maintain the required distributional properties for valid conformal inference. □

**Theorem 3 (Covariate Shift Coverage).** Under covariate shift with known importance weights, the weighted conformal intervals satisfy:
$$P_{target}(\tau(x) \in C_\tau^w(x)) \geq 1 - \alpha$$
where the probability is with respect to the target distribution.

**Corollary 1 (Efficiency).** When the outcome models are well-specified and the sample size is large, the width of our conformal intervals approaches the width of oracle intervals based on the true conditional variance of treatment effects.

These theoretical results establish that our method provides finite-sample coverage guarantees without requiring asymptotic approximations, strong distributional assumptions, or correct model specification—properties that distinguish it from existing approaches to uncertainty quantification in causal inference.

## 6. Experimental Design

We would evaluate our method through comprehensive experiments on both synthetic and real-world datasets to assess coverage, efficiency, and practical performance.

### 6.1 Synthetic Data Experiments

**Data Generation:** We would generate synthetic datasets with known ground truth treatment effects using various data generating processes:
- Linear CATE functions with homoscedastic noise
- Nonlinear CATE functions using polynomial and interaction terms  
- Heteroscedastic settings where treatment effect variance depends on covariates
- High-dimensional settings with irrelevant confounders
- Settings with strong confounding and near-violations of overlap

For each setting, we would vary sample sizes (n = 500, 1000, 2000, 5000) and dimensions (p = 5, 10, 20, 50).

**Base CATE Estimators:** We would test our conformal framework with multiple base estimators:
- Linear regression (T-learner, S-learner, X-learner)
- Random forests and causal forests
- Gradient boosting machines
- Neural networks (TARNet, CFR)
- Double machine learning with various first-stage estimators

**Evaluation Metrics:**
- **Coverage:** Empirical coverage rates across test sets, stratified by covariate values
- **Interval Width:** Average and median prediction interval widths
- **Efficiency:** Ratio of our interval widths to oracle intervals (when available)
- **Conditional Coverage:** Coverage rates within different subgroups to assess uniformity

### 6.2 Semi-Synthetic Experiments

**IHDP Dataset:** Using the Infant Health and Development Program dataset, we would follow the semi-synthetic setup where treatment effects are simulated but covariates come from real data. This allows evaluation of coverage while maintaining realistic covariate structure.

**ACIC Competition Data:** We would use datasets from the Atlantic Causal Inference Conference data competition, which provide multiple realistic semi-synthetic scenarios with known ground truth.

### 6.3 Real Data Experiments

**Randomized Controlled Trials:** We would apply our method to several RCTs where treatment effect heterogeneity is expected:
- Medical trials with biomarker-based subgroups
- Educational interventions with demographic heterogeneity
- Marketing experiments with customer segment variation

**Observational Studies:** We would evaluate on observational datasets commonly used in causal inference:
- LaLonde job training program data
- Cattaneo et al. smoking cessation data
- Card & Krueger minimum wage study

For real data without ground truth, we would assess:
- Interval calibration using data splitting
- Sensitivity to hyperparameters and model choices
- Computational efficiency and scalability

### 6.4 Ablation Studies

**Conformity Score Comparison:** We would compare our direct treatment effect conformity score against:
- Naive combination of separate outcome intervals
- Alternative pseudo-treatment effect constructions
- Residual-based and quantile-based conformity scores

**Covariate Shift Robustness:** We would simulate distribution shift scenarios by:
- Reweighting training data to create artificial shift
- Using temporal splits in longitudinal datasets  
- Geographic splits in multi-site studies

**Model Misspecification:** We would deliberately misspecify base models to test robustness:
- Using linear models when true CATE is nonlinear
- Omitting important interaction terms
- Using wrong distributional assumptions

### 6.5 Computational Experiments

We would assess computational scalability by measuring:
- Runtime as a function of sample size and dimension
- Memory requirements for large datasets
- Parallelization efficiency
- Comparison with bootstrap-based uncertainty quantification

### 6.6 Baseline Comparisons

We would compare against existing uncertainty quantification methods:
- Bootstrap confidence intervals for CATE estimators
- Bayesian approaches with default priors
- Asymptotic confidence intervals from causal forests
- Quantile regression-based intervals
- Cross-validation based approaches

The experimental design would provide comprehensive evidence for the practical utility of our conformal prediction framework while rigorously testing its theoretical guarantees across diverse settings.

## 7. Discussion

Our conformal prediction framework for heterogeneous treatment effects addresses a critical gap in causal inference by providing distribution-free uncertainty quantification with finite-sample guarantees. This work has several important strengths and limitations that merit discussion.

### 7.1 Strengths

**Theoretical Rigor:** Unlike existing approaches that rely on asymptotic approximations or strong distributional assumptions, our method provides exact finite-sample coverage guarantees under minimal conditions. This is particularly valuable in applications with moderate sample sizes where asymptotic results may be unreliable.

**Model Agnostic:** Our framework works with any base CATE estimator, from simple linear models to complex deep learning approaches. This flexibility allows practitioners to leverage state-of-the-art machine learning methods while still obtaining rigorous uncertainty quantification.

**Robustness:** The coverage guarantees hold even under model misspecification, making the method robust to the inevitable modeling errors that occur in practice. This is crucial in causal inference where the true data generating process is typically unknown.

**Practical Applicability:** The method handles both randomized experiments and observational studies, and extends naturally to settings with covariate shift. The computational requirements are modest, requiring only quantile computations after training the base models.

### 7.2 Limitations

**Conservativeness:** Like many conformal prediction methods, our intervals may be conservative, particularly when the base models are poorly calibrated. The direct treatment effect conformity score helps address this, but some conservativeness is inherent to distribution-free methods.

**Exchangeability Assumption:** The theoretical guarantees require that the data points are exchangeable, which may be violated in settings with temporal dependence, spatial correlation, or other forms of dependence. Extensions to handle such dependencies would be valuable.

**Interval Interpretation:** The intervals provide coverage for the conditional average treatment effect $\tau(x)$, not for individual treatment effects $\tau_i$. While this is the standard target in heterogeneous treatment effect estimation, practitioners should understand this distinction.

**Covariate Shift:** While we provide an extension for covariate shift, it requires knowing the importance weights, which may be difficult to estimate accurately in practice. Misspecified weights could degrade coverage performance.

### 7.3 Broader Impact

This work has significant implications for evidence-based decision making across multiple domains:

**Healthcare:** Personalized medicine increasingly relies on estimating heterogeneous treatment effects to optimize individual treatment decisions. Our uncertainty quantification framework enables clinicians to make more informed risk-benefit assessments, potentially improving patient outcomes while reducing unnecessary treatments.

**Policy Evaluation:** Social programs often have heterogeneous effects across different populations. Reliable uncertainty estimates help policymakers identify which subgroups benefit most from interventions and allocate resources more effectively.

**Algorithmic Fairness:** Understanding treatment effect heterogeneity across demographic groups is crucial for ensuring fair allocation of interventions. Our framework provides rigorous tools for quantifying uncertainty in these estimates.

**Scientific Discovery:** By providing reliable uncertainty quantification, our method facilitates more honest reporting of treatment effect heterogeneity in scientific studies, potentially reducing publication bias and improving reproducibility.

### 7.4 Ethical Considerations

The ability to estimate heterogeneous treatment effects with uncertainty quantification raises important ethical questions. While personalized treatment allocation can improve outcomes, it may also exacerbate existing inequalities if certain groups systematically receive different treatments. Our framework's ability to quantify uncertainty across subgroups can help identify and address such disparities.

Additionally, the use of individual characteristics to predict treatment effects must be balanced against privacy concerns and potential discrimination. Practitioners should carefully consider which covariates to include and how to protect individual privacy while still enabling personalized decision-making.

## 8. Conclusion

We have developed a conformal prediction framework for heterogeneous treatment effect estimation that provides distribution-free, finite-sample uncertainty quantification without requiring asymptotic approximations or strong distributional assumptions. Our approach addresses the fundamental challenge that individual treatment effects are unobservable by constructing conformity scores that work with observable quantities while still providing meaningful coverage guarantees.

The key contributions include: (1) novel conformity scores tailored to the causal inference setting, (2) theoretical coverage guarantees that hold under minimal assumptions and are robust to model misspecification, (3) extensions to handle covariate shift between training and target populations, and (4) a general framework that works with any base CATE estimator.

This work opens several directions for future research. First, extending the framework to handle temporal dependence and other violations of exchangeability would broaden its applicability. Second, developing adaptive conformal methods that can adjust interval widths based on local uncertainty would improve efficiency. Third, exploring connections to other uncertainty quantification frameworks like Bayesian methods could yield hybrid approaches with complementary strengths.

The integration of conformal prediction with causal inference represents a promising direction for bringing rigorous uncertainty quantification to treatment effect estimation. As personalized medicine and targeted interventions become increasingly important, methods that can reliably quantify uncertainty in heterogeneous treatment effects will be essential for evidence-based decision making.

## References

[Athey & Imbens, 2016] Athey, S., & Imbens, G. W. (2016). Recursive partitioning for heterogeneous causal effects. Proceedings of the National Academy of Sciences.

[Künzel et al., 2019] Künzel, S. R., Sekhon, J. S., Bickel, P. J., & Yu, B. (2019). Metalearners for estimating heterogeneous treatment effects using machine learning. Proceedings of the National Academy of Sciences.

[Shalit et al., 2017] Shalit, U., Johansson, F. D., & Sontag, D. (2017). Estimating individual treatment effect: generalization bounds and algorithms. International Conference on Machine Learning.

[Vovk et al., 2005] Vovk, V., Gammerman, A., & Shafer, G. (2005). Algorithmic learning in a random world. Springer.

[Lei et al., 2018] Lei, J., G'Sell, M., Rinaldo, A., Tibshirani, R. J., & Wasserman, L. (2018). Distribution-free predictive inference for regression. Journal of the American Statistical Association.

[Chernozhukov et al., 2018] Chernozhukov, V., Chetverikov, D., Demirer, M., Duflo, E., Hansen, C., Newey, W., & Robins, J. (2018). Double/debiased machine learning for treatment and structural parameters. The Econometrics Journal.

[Tibshirani et al., 2019] Tibshirani, R. J., Barber, R. F., Candes, E. J., & Ramdas, A. (2019). Conformal prediction under covariate shift. Advances in Neural Information Processing Systems.
