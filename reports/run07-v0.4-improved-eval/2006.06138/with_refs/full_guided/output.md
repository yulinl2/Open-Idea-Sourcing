# Reconstruction: full_guided
**Paper:** 2006.06138  
**Condition:** with_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Conformal Prediction for Heterogeneous Treatment Effects: Distribution-Free Uncertainty Quantification Under Covariate Shift

## Abstract

Understanding how treatments affect individuals differently is crucial in medicine, policy evaluation, and social sciences, yet existing methods for estimating heterogeneous treatment effects provide poor uncertainty quantification. While conditional average treatment effects (CATE) can be estimated using flexible machine learning algorithms, these approaches typically lack reliable confidence intervals, particularly problematic in high-stakes decision-making contexts. We address this gap by extending conformal prediction methodology to provide distribution-free uncertainty quantification for individual treatment effects. Our approach handles both randomized experiments and observational studies, accommodates covariate shift between study and target populations, and provides finite-sample coverage guarantees without asymptotic approximations or unverifiable modeling assumptions. By leveraging weighted conformal prediction and carefully constructed nonconformity scores that account for the fundamental problem of causal inference, we enable reliable interval estimates for heterogeneous treatment effects that support risk-aware personalized decision-making.

## 1. Introduction

The estimation of heterogeneous treatment effects has become increasingly important across numerous domains where one-size-fits-all interventions are inadequate. In precision medicine, understanding which patients will benefit from specific treatments is essential for personalized care [Kunzel et al., 2019]. In economics and policy evaluation, recognizing that interventions may help some individuals while harming others is crucial for optimal resource allocation and policy design [Athey & Imbens, 2017]. Despite this importance, current methodological approaches focus primarily on point estimation of conditional average treatment effects (CATE) while providing inadequate uncertainty quantification.

The fundamental challenge in causal inference is that for any individual, we observe only one potential outcome—either under treatment or control—making individual treatment effects inherently unobservable. This creates unique difficulties for uncertainty quantification that go beyond standard prediction problems. Existing approaches typically rely on asymptotic approximations, bootstrap procedures, or Bayesian methods that require strong modeling assumptions and may not provide reliable finite-sample guarantees [Wager & Athey, 2018; Kunzel et al., 2019].

Recent advances in conformal prediction offer a promising alternative framework for distribution-free uncertainty quantification [Vovk et al., 2005; Lei et al., 2018]. Conformal prediction provides finite-sample coverage guarantees without requiring distributional assumptions, making it particularly attractive for causal inference applications where model misspecification is a constant concern. However, standard conformal prediction assumes exchangeable data, which is violated in many causal inference settings due to covariate shift between study and target populations.

**Contributions:**
• We develop a novel conformal prediction framework for heterogeneous treatment effects that provides finite-sample coverage guarantees for individual treatment effect intervals
• We extend the methodology to handle covariate shift between study and target populations using weighted conformal prediction
• We design specialized nonconformity scores that account for the fundamental problem of causal inference and the structure of treatment effect estimation
• We provide theoretical analysis showing our intervals achieve nominal coverage under standard causal assumptions
• We demonstrate applicability to both randomized experiments and observational studies under unconfoundedness

## 2. Related Work

**Heterogeneous Treatment Effects:** The literature on heterogeneous treatment effects has grown rapidly, with approaches ranging from subgroup analysis to sophisticated machine learning methods. Athey & Imbens [2016] introduced causal trees for discovering treatment effect heterogeneity, while Wager & Athey [2018] developed causal forests that provide asymptotic confidence intervals. Kunzel et al. [2019] proposed meta-learners that leverage flexible machine learning algorithms for CATE estimation. However, these methods generally provide only asymptotic uncertainty quantification that may be unreliable in finite samples.

**Conformal Prediction:** Conformal prediction, pioneered by Vovk et al. [2005], provides a framework for distribution-free uncertainty quantification. The key insight is that under exchangeability, nonconformity scores can be used to construct prediction intervals with exact finite-sample coverage guarantees. Lei et al. [2018] extended conformal prediction to regression settings, while recent work has explored applications in various domains. The split conformal approach [Papadopoulos et al., 2002; Lei et al., 2015] provides computational efficiency by separating model fitting from interval construction.

**Covariate Shift:** The problem of covariate shift, where training and test distributions differ in their covariate distributions but maintain the same conditional relationship between covariates and outcomes, has been extensively studied [Shimodaira, 2000; Quinonero-Candela et al., 2009]. Tibshirani et al. [2020] recently extended conformal prediction to handle covariate shift using weighted quantiles based on likelihood ratios, providing the foundation for our extension to causal inference.

**Uncertainty Quantification in Causal Inference:** While point estimation of treatment effects has received substantial attention, uncertainty quantification remains challenging. Traditional approaches rely on asymptotic normality or bootstrap methods, both of which may be unreliable in finite samples or under model misspecification. Recent work has explored Bayesian approaches [Hill, 2011] and ensemble methods [Nie & Wager, 2021], but these typically require strong assumptions about the underlying data-generating process.

**Gap Identification:** Existing methods for uncertainty quantification in causal inference either require strong modeling assumptions, rely on asymptotic approximations, or fail to account for covariate shift between study and target populations. Our work fills this gap by providing distribution-free, finite-sample uncertainty quantification for heterogeneous treatment effects that accommodates realistic deployment scenarios.

## 3. Problem Formulation

**Notation:** Let $\{(X_i, T_i, Y_i)\}_{i=1}^n$ denote our observed data, where $X_i \in \mathbb{R}^d$ represents covariates, $T_i \in \{0,1\}$ indicates treatment assignment, and $Y_i \in \mathbb{R}$ is the observed outcome. For each unit $i$, we define potential outcomes $Y_i(0)$ and $Y_i(1)$ representing what unit $i$'s outcome would be under control and treatment, respectively. The observed outcome satisfies $Y_i = T_i Y_i(1) + (1-T_i) Y_i(0)$.

**Causal Estimand:** Our primary interest lies in the individual treatment effect $\tau(x) = \mathbb{E}[Y(1) - Y(0) | X = x]$ for a new individual with covariates $x$. While this quantity is not directly observable for any individual, we aim to construct prediction intervals $\mathcal{C}_n(x)$ such that for a new unit with covariates $X_{n+1}$ drawn from some target distribution:

$$P(\tau(X_{n+1}) \in \mathcal{C}_n(X_{n+1})) \geq 1 - \alpha$$

**Assumptions:** We make the following standard causal assumptions:

1. **Unconfoundedness:** $(Y(0), Y(1)) \perp T | X$
2. **Overlap:** $0 < P(T = 1 | X = x) < 1$ for all $x$ in the support
3. **SUTVA:** No interference between units and consistency of potential outcomes

For randomized experiments, unconfoundedness is satisfied by design. For observational studies, this assumption requires that all confounders are observed and included in $X$.

**Covariate Shift Setting:** We consider the realistic scenario where the study population (from which training data is drawn) may differ from the target population (where we want to make predictions). Specifically:

- Training data: $(X_i, T_i, Y_i) \stackrel{iid}{\sim} P_{\text{study}} = P_X^{\text{study}} \times P_{T|X} \times P_{Y|T,X}$
- Target population: $X_{n+1} \sim P_X^{\text{target}}$, but $P_{T|X}$ and $P_{Y|T,X}$ remain unchanged

We assume the likelihood ratio $w(x) = \frac{dP_X^{\text{target}}}{dP_X^{\text{study}}}(x)$ is known or can be estimated accurately.

**Objective:** Construct prediction intervals $\mathcal{C}_n(x)$ that achieve nominal coverage for individual treatment effects while being:
- Distribution-free (no parametric assumptions)
- Finite-sample valid (exact coverage guarantees)
- Robust to covariate shift
- Computationally efficient

## 4. Methodology

Our approach builds on conformal prediction by carefully designing nonconformity scores that capture the uncertainty in treatment effect estimation while accounting for the fundamental problem of causal inference.

**Core Insight:** While individual treatment effects $\tau(x) = Y(1) - Y(0)$ are never directly observable, we can construct pseudo-outcomes that approximate treatment effects and apply conformal prediction to these quantities. The key challenge is designing nonconformity scores that properly account for the estimation uncertainty in both $\mathbb{E}[Y(1)|X=x]$ and $\mathbb{E}[Y(0)|X=x]$.

### 4.1 Treatment Effect Pseudo-Outcomes

For each unit $i$ in our training data, we construct a pseudo-outcome that approximates the treatment effect:

$$\tilde{\tau}_i = T_i \cdot \frac{Y_i - \hat{\mu}_0(X_i)}{\hat{e}(X_i)} + (1-T_i) \cdot \frac{\hat{\mu}_1(X_i) - Y_i}{1 - \hat{e}(X_i)}$$

where:
- $\hat{\mu}_t(x) = \mathbb{E}[Y|T=t, X=x]$ are estimated outcome regression functions
- $\hat{e}(x) = P(T=1|X=x)$ is the estimated propensity score

This pseudo-outcome is inspired by influence function approaches to treatment effect estimation and provides an unbiased estimate of $\tau(X_i)$ under our causal assumptions.

### 4.2 Nonconformity Score Design

We define our nonconformity score for a test point $(x, \tau)$ as:

$$S((x, \tau), \mathcal{D}) = |\tau - \hat{\tau}(x)|$$

where $\hat{\tau}(x) = \hat{\mu}_1(x) - \hat{\mu}_0(x)$ is our point estimate of the treatment effect, and $\mathcal{D}$ represents the training data used to fit the outcome models.

For training points, we compute:
$$V_i = S((X_i, \tilde{\tau}_i), \mathcal{D}_{-i}) = |\tilde{\tau}_i - \hat{\tau}_{-i}(X_i)|$$

where $\hat{\tau}_{-i}(x)$ is the treatment effect estimate obtained after removing unit $i$ from the training data.

### 4.3 Split Conformal for Computational Efficiency

To avoid the computational burden of leave-one-out estimation, we employ a split conformal approach:

1. **Split the data:** Divide training data into $\mathcal{D}_1$ (model fitting) and $\mathcal{D}_2$ (calibration)
2. **Fit models:** Use $\mathcal{D}_1$ to estimate $\hat{\mu}_0$, $\hat{\mu}_1$, $\hat{e}$, and $\hat{\tau}$
3. **Compute scores:** For each $(X_i, T_i, Y_i) \in \mathcal{D}_2$, compute:
   - Pseudo-outcome: $\tilde{\tau}_i$ using the fitted models
   - Nonconformity score: $V_i = |\tilde{\tau}_i - \hat{\tau}(X_i)|$

### 4.4 Weighted Conformal for Covariate Shift

When the target population differs from the study population, we employ weighted conformal prediction. For a test point $x$, we define weights:

$$p_i^w(x) = \frac{w(X_i)}{\sum_{j \in \mathcal{D}_2} w(X_j) + w(x)}, \quad p_{n+1}^w(x) = \frac{w(x)}{\sum_{j \in \mathcal{D}_2} w(X_j) + w(x)}$$

The prediction interval is then:

$$\mathcal{C}_n(x) = \left[\hat{\tau}(x) \pm \text{Quantile}\left(1-\alpha; \sum_{i \in \mathcal{D}_2} p_i^w(x) \delta_{V_i} + p_{n+1}^w(x) \delta_\infty\right)\right]$$

### 4.5 Algorithm Summary

**Algorithm 1: Conformal Treatment Effect Intervals**
```
Input: Training data {(X_i, T_i, Y_i)}_{i=1}^n, test point x, coverage level 1-α
1. Split data: D_1 ∪ D_2 = {1,...,n}, |D_1| ≈ |D_2|
2. Fit models on D_1:
   - Outcome models: μ̂_0(·), μ̂_1(·)  
   - Propensity model: ê(·)
   - Treatment effect: τ̂(·) = μ̂_1(·) - μ̂_0(·)
3. For each i ∈ D_2:
   - Compute pseudo-outcome: τ̃_i
   - Compute nonconformity score: V_i = |τ̃_i - τ̂(X_i)|
4. Compute weights: p_i^w(x) for covariate shift
5. Return interval: C_n(x) = τ̂(x) ± quantile
```

## 5. Theoretical Analysis

We now establish the finite-sample coverage properties of our conformal treatment effect intervals.

**Theorem 1 (Coverage Under No Covariate Shift):** Assume the causal assumptions hold and training/test data are exchangeable. Then for any base learning algorithms used to estimate $\mu_0$, $\mu_1$, and $e$:

$$P(\tau(X_{n+1}) \in \mathcal{C}_n(X_{n+1})) \geq 1 - \alpha$$

**Proof Sketch:** The key insight is that under our causal assumptions, the pseudo-outcomes $\tilde{\tau}_i$ are unbiased estimates of $\tau(X_i)$. By the exchangeability of the data and the symmetric construction of nonconformity scores, we can apply the fundamental conformal prediction result. The pseudo-outcome construction ensures that the nonconformity scores capture the relevant uncertainty in treatment effect estimation.

**Theorem 2 (Coverage Under Covariate Shift):** Assume the causal assumptions hold and let $w(x) = \frac{dP_X^{\text{target}}}{dP_X^{\text{study}}}(x)$ be the likelihood ratio between target and study populations. Then:

$$P(\tau(X_{n+1}) \in \mathcal{C}_n(X_{n+1})) \geq 1 - \alpha$$

where $X_{n+1} \sim P_X^{\text{target}}$ and the interval $\mathcal{C}_n$ is constructed using weighted conformal prediction.

**Proof Sketch:** This follows from the weighted exchangeability result of Tibshirani et al. [2020]. The likelihood ratio weighting ensures that the empirical distribution of weighted nonconformity scores from the study population resembles the distribution we would obtain from the target population.

**Lemma 1 (Unbiasedness of Pseudo-Outcomes):** Under unconfoundedness and overlap:

$$\mathbb{E}[\tilde{\tau}_i | X_i] = \tau(X_i)$$

**Proof:** This follows from the doubly robust property of the influence function estimator and our causal assumptions.

**Remark on Finite-Sample Validity:** Unlike asymptotic approaches, our coverage guarantees hold exactly in finite samples without requiring large sample approximations or specific model classes for the base learners. This makes our approach particularly valuable in settings with limited data.

**Remark on Model Misspecification:** While our coverage guarantees hold regardless of the quality of $\hat{\mu}_0$, $\hat{\mu}_1$, and $\hat{e}$, the width of the intervals will depend on these estimates. Better models lead to tighter intervals while maintaining coverage.

## 6. Experimental Design

We propose a comprehensive experimental evaluation to assess the empirical performance of our method across diverse settings.

### 6.1 Synthetic Data Experiments

**Setup:** We generate synthetic datasets with known treatment effects to evaluate coverage and interval width:

1. **Linear Setting:** $Y(0) = X^T\beta_0 + \epsilon_0$, $Y(1) = X^T\beta_1 + \epsilon_1$ with Gaussian noise
2. **Nonlinear Setting:** Treatment effects follow complex nonlinear patterns using polynomial and interaction terms
3. **Heteroskedastic Setting:** Error variances depend on covariates to test robustness

**Covariate Shift Simulation:** Create target populations by exponentially tilting the covariate distribution: $w(x) = \exp(x^T\gamma)$ for various $\gamma$ vectors.

**Metrics:**
- Empirical coverage rates across different $\alpha$ levels
- Average interval widths
- Coverage conditional on covariate values (to detect systematic biases)
- Computational time comparisons

### 6.2 Semi-Synthetic Benchmarks

**IHDP Dataset:** Use the Infant Health and Development Program dataset, a standard benchmark for causal inference methods. We use the semi-synthetic version where treatment effects are known.

**ACIC Competition Data:** Evaluate on datasets from the Atlantic Causal Inference Conference data competition, which provides realistic confounding structures with known ground truth.

### 6.3 Real Data Applications

**Medical Applications:**
- Warfarin dosing data to predict treatment effects of different dosing strategies
- Electronic health records for personalized treatment recommendations

**Economic Applications:**
- Job training programs using LaLonde data
- Educational interventions using school-level data

**Experimental Protocol:**
1. Split data into training/validation/test sets
2. Implement covariate shift by reweighting test set
3. Compare against baselines: asymptotic confidence intervals from causal forests, bootstrap methods, and Bayesian approaches
4. Evaluate coverage, width, and computational efficiency

### 6.4 Baseline Methods

**Causal Forest Confidence Intervals:** Asymptotic intervals from Wager & Athey [2018]
**Bootstrap Intervals:** Percentile and bias-corrected bootstrap
**Bayesian Credible Intervals:** Using Bayesian Additive Regression Trees (BART)
**Oracle Intervals:** When ground truth is known, construct optimal intervals for comparison

### 6.5 Ablation Studies

**Pseudo-Outcome Construction:** Compare different approaches for constructing $\tilde{\tau}_i$
**Base Learner Choice:** Evaluate sensitivity to choice of algorithms for $\hat{\mu}_0$, $\hat{\mu}_1$, $\hat{e}$
**Sample Splitting:** Analyze the effect of different splitting ratios between model fitting and calibration sets
**Weight Estimation:** Study robustness to errors in likelihood ratio estimation

## 7. Discussion

### 7.1 Strengths

**Finite-Sample Validity:** Our approach provides exact coverage guarantees without requiring asymptotic approximations, making it particularly valuable for small to moderate sample sizes common in many applications.

**Distribution-Free:** The method works without parametric assumptions about the outcome distribution, error terms, or treatment effect heterogeneity patterns.

**Covariate Shift Robustness:** The weighted extension naturally handles differences between study and target populations, a common challenge in practice.

**Computational Efficiency:** The split conformal approach avoids expensive leave-one-out computations while maintaining theoretical guarantees.

**Broad Applicability:** The framework applies to both randomized experiments and observational studies under standard causal assumptions.

### 7.2 Limitations

**Dependence on Base Learners:** While coverage is guaranteed regardless of model quality, interval width depends critically on the accuracy of outcome and propensity score models. Poor models lead to uninformative intervals.

**Unconfoundedness Requirement:** For observational studies, the method still requires the strong assumption that all confounders are observed and measured.

**Likelihood Ratio Estimation:** In covariate shift settings, accurate estimation of the likelihood ratio $w(x)$ can be challenging and errors propagate to coverage properties.

**Interval Interpretation:** The intervals cover the conditional average treatment effect $\tau(x) = \mathbb{E}[Y(1) - Y(0) | X = x]$ rather than individual-level effects, which may limit applicability in some personalized decision-making contexts.

### 7.3 Connections to Broader Impact

**Healthcare Applications:** Reliable uncertainty quantification for treatment effects could improve clinical decision-making by helping physicians understand the confidence in personalized treatment recommendations.

**Policy Evaluation:** Policymakers could use these intervals to assess the range of possible impacts when implementing interventions in new populations.

**Algorithmic Fairness:** The framework could help identify when treatment effect estimates are particularly uncertain for specific demographic groups, highlighting potential fairness concerns.

**Regulatory Approval:** Finite-sample guarantees may be valuable for regulatory agencies evaluating new interventions where asymptotic approximations are inappropriate.

### 7.4 Future Directions

**Multiple Treatments:** Extending the framework to handle multiple discrete or continuous treatment options.

**Time-Varying Treatments:** Adapting the methodology for longitudinal settings with time-varying confounders.

**Survival Outcomes:** Developing appropriate nonconformity scores for time-to-event outcomes.

**Adaptive Designs:** Incorporating the uncertainty quantification into sequential experimental design for more efficient data collection.

## 8. Conclusion

We have developed a novel framework for distribution-free uncertainty quantification of heterogeneous treatment effects that provides finite-sample coverage guarantees without strong modeling assumptions. By extending conformal prediction to the causal inference setting through carefully designed pseudo-outcomes and nonconformity scores, we address a critical gap in current methodology for personalized treatment effect estimation.

Our approach handles both randomized experiments and observational studies, accommodates covariate shift between study and target populations, and provides computationally efficient algorithms for practical implementation. The theoretical analysis demonstrates that our intervals achieve nominal coverage under standard causal assumptions, while the experimental design provides a comprehensive framework for empirical evaluation.

**Key contributions include:**
- First application of conformal prediction to heterogeneous treatment effect estimation
- Weighted extension for covariate shift in causal inference settings  
- Finite-sample coverage guarantees without asymptotic approximations
- Computationally efficient split conformal implementation

**Open questions for future work:**
- Optimal design of pseudo-outcomes for different outcome types
- Extensions to more complex causal structures (mediation, interference)
- Integration with adaptive experimental design
- Theoretical analysis of interval width optimality

This work opens new avenues for reliable uncertainty quantification in causal inference, with potential applications across medicine, economics, and policy evaluation where understanding treatment effect heterogeneity is crucial for optimal decision-making.

## References

[Athey & Imbens, 2016] Athey, S., & Imbens, G. (2016). Recursive partitioning for heterogeneous causal effects. Proceedings of the National Academy of Sciences.

[Athey & Imbens, 2017] Athey, S., & Imbens, G. W. (2017). The econometrics of randomized experiments. Handbook of Economic Field Experiments.

[Hill, 2011] Hill, J. L. (2011). Bayesian nonparametric modeling for causal inference. Journal of Computational and Graphical Statistics.

[Kunzel et al., 2019] Künzel, S. R., Sekhon, J. S., Bickel, P. J., & Yu, B. (2019). Metalearners for estimating heterogeneous treatment effects using machine learning. Proceedings of the National Academy of Sciences.

[Lei & Wasserman, 2014] Lei, J., & Wasserman, L. (2014). Distribution-free prediction bands for non-parametric regression. Journal of the Royal Statistical Society: Series B.

[Lei et al., 2015] Lei, J., G'Sell, M., Rinaldo, A., Tibshirani, R. J., & Wasserman, L. (2015). Distribution-free predictive inference for regression. Journal of the American Statistical Association.

[Lei et al., 2018] Lei, J., G'Sell, M., Rinaldo, A., Tibshirani, R. J., & Wasserman, L. (2018). Distribution-free predictive inference for regression. Journal of the American Statistical Association.

[Nie & Wager, 2021] Nie, X., & Wager, S. (2021). Quasi-oracle estimation of heterogeneous treatment effects. Biometrika.

[Papadopoulos et al., 2002] Papadopoulos, H., Proedrou, K., Vovk, V., & Gammerman, A. (2002). Inductive confidence machines for regression. European Conference on Machine Learning.

[Quinonero-Candela et al., 2009] Quiñonero-Candela, J., Sugiyama, M., Schwaighofer, A., & Lawrence, N. D. (2009). Dataset shift in machine learning. MIT Press.

[Shimodaira, 2000] Shimodaira, H. (2000). Improving predictive inference under covariate shift by weighting the log-likelihood function. Journal of Statistical Planning and Inference.

[Tibshirani et al., 2020] Tibshirani, R. J., Barber, R. F., Candes, E., & Ramdas, A. (2020). Conformal prediction under covariate shift. Neural Information Processing Systems.

[Vovk et al., 2005] Vovk, V., Gammerman, A., & Shafer, G. (2005). Algorithmic learning in a random world. Springer.

[Wager & Athey, 2018] Wager, S., & Athey, S. (2018). Estimation and inference of heterogeneous treatment effects using random forests. Journal of the American Statistical Association.
