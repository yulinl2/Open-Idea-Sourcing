# Reconstruction: full_guided
**Paper:** 2006.06138  
**Condition:** with_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Conformal Prediction Intervals for Conditional Average Treatment Effects

## Abstract

Estimating treatment effect heterogeneity is crucial for personalized decision-making across medicine, policy, and social sciences. While machine learning methods can estimate conditional average treatment effects (CATE), they typically provide poor uncertainty quantification, limiting their utility in high-stakes applications. We propose a novel framework that combines conformal prediction with causal inference to construct distribution-free prediction intervals for individual treatment effects. Our approach leverages weighted conformal prediction to handle both randomized experiments and observational studies, providing finite-sample coverage guarantees without asymptotic approximations or parametric assumptions. The method accounts for the fundamental problem of causal inference—that only one potential outcome is observed per individual—by constructing intervals around CATE estimates that maintain valid coverage even under model misspecification. We extend the framework to handle covariate shift between study and target populations, enabling robust uncertainty quantification for treatment effect predictions in new populations.

## 1. Introduction

The estimation of treatment effects has traditionally focused on population averages, but there is growing recognition that treatment effects often vary substantially across individuals. A medical intervention might benefit 70% of patients while harming the remaining 30%, making the average treatment effect misleading for individual decision-making. This has motivated extensive research into estimating conditional average treatment effects (CATE), which quantify how treatment effects vary as a function of individual characteristics.

Modern machine learning approaches to CATE estimation, including causal forests [Wager & Athey, 2018], meta-learners [Künzel et al., 2019], and neural network-based methods, have shown promising empirical performance. However, these methods typically provide only point estimates without reliable uncertainty quantification. This limitation is particularly problematic in high-stakes applications where understanding the uncertainty around treatment effect predictions is crucial for decision-making.

The challenge of uncertainty quantification for CATE estimation is compounded by the fundamental problem of causal inference: for any individual, we observe only one potential outcome (either under treatment or control), never both. This creates unique challenges compared to standard prediction problems, as the "ground truth" individual treatment effect is never directly observable, even in the training data.

Existing approaches to uncertainty quantification for CATE estimation rely heavily on asymptotic approximations, bootstrap procedures, or strong parametric assumptions that may not hold in practice. These methods often fail to provide reliable finite-sample guarantees, and their validity can be sensitive to model misspecification—a common concern when using flexible machine learning methods.

Our contributions are:

• We develop a conformal prediction framework for CATE estimation that provides distribution-free prediction intervals with finite-sample coverage guarantees
• We extend the approach to handle observational studies through weighted conformal prediction, accounting for propensity score-based reweighting
• We address covariate shift between study and target populations, enabling robust uncertainty quantification when deploying CATE models to new populations
• We provide theoretical analysis showing that our intervals maintain valid coverage even under model misspecification of the underlying CATE function
• We design the framework to work with any base CATE estimation method, making it broadly applicable across different machine learning approaches

## 2. Related Work

**Conditional Average Treatment Effect Estimation.** The literature on CATE estimation has grown rapidly, with methods broadly categorized into meta-learners, tree-based approaches, and representation learning methods. Meta-learners such as the T-learner, S-learner, and X-learner [Künzel et al., 2019] use separate models for treatment and control groups or combine them in various ways. Causal forests [Wager & Athey, 2018] extend random forests to directly estimate treatment effects with theoretical guarantees. More recently, neural network approaches have been developed for high-dimensional settings [Shalit et al., 2017; Yoon et al., 2018].

**Uncertainty Quantification in Causal Inference.** Most existing approaches to uncertainty quantification for treatment effects rely on asymptotic theory or bootstrap methods. Wager & Athey [2018] provide asymptotic confidence intervals for causal forests based on infinitesimal jackknife variance estimation. Nie & Wager [2021] develop quasi-oracle theory for meta-learners, providing asymptotic confidence intervals under regularity conditions. However, these methods require large sample assumptions and can be sensitive to model misspecification.

**Conformal Prediction.** Conformal prediction, pioneered by Vovk et al. [2005], provides distribution-free prediction intervals with finite-sample coverage guarantees under exchangeability assumptions. The framework has been extended to various settings, including regression [Lei et al., 2018], classification [Sadinle et al., 2019], and high-dimensional problems [Lei & Wasserman, 2014]. Tibshirani et al. [2019] extended conformal prediction to handle covariate shift through weighted procedures, which is particularly relevant for our work.

**Conformal Prediction in Causal Settings.** The application of conformal prediction to causal inference problems is relatively new. Lei & Candès [2021] applied conformal prediction to estimate confidence intervals for average treatment effects, but their approach focuses on population-level quantities rather than individual treatment effects. Our work addresses the more challenging problem of uncertainty quantification for individual-level causal quantities.

**Gap Identification.** While existing methods provide point estimates for CATE and some offer asymptotic uncertainty quantification, there remains a significant gap in providing reliable, finite-sample uncertainty quantification for individual treatment effects. This gap is particularly important given the high-stakes nature of many applications and the sensitivity of existing methods to model assumptions. Our work fills this gap by adapting conformal prediction methodology to the unique challenges of causal inference.

## 3. Problem Formulation

We work within the potential outcomes framework [Rubin, 1974]. For each individual $i$, we define potential outcomes $Y_i(0)$ and $Y_i(1)$ representing the outcomes that would be observed under control and treatment, respectively. We observe covariates $X_i \in \mathcal{X} \subseteq \mathbb{R}^d$, treatment assignment $T_i \in \{0,1\}$, and the realized outcome $Y_i = T_i Y_i(1) + (1-T_i)Y_i(0)$.

The individual treatment effect for unit $i$ is $\tau_i = Y_i(1) - Y_i(0)$, which is never directly observed due to the fundamental problem of causal inference. Our target estimand is the conditional average treatment effect:
$$\tau(x) = \mathbb{E}[Y(1) - Y(0) | X = x] = \mathbb{E}[Y(1) | X = x] - \mathbb{E}[Y(0) | X = x]$$

**Assumptions.** We make the following standard assumptions:
1. **SUTVA (Stable Unit Treatment Value Assumption):** The potential outcomes for unit $i$ are unaffected by the treatment assignments of other units.
2. **Unconfoundedness:** $(Y(0), Y(1)) \perp T | X$, meaning treatment assignment is conditionally independent of potential outcomes given covariates.
3. **Overlap:** $0 < e(x) < 1$ for all $x \in \mathcal{X}$, where $e(x) = P(T = 1 | X = x)$ is the propensity score.

**Objective.** Given training data $\{(X_i, T_i, Y_i)\}_{i=1}^n$ and a new covariate vector $X_{n+1}$, we aim to construct a prediction interval $\hat{C}_n(X_{n+1})$ such that:
$$P(\tau(X_{n+1}) \in \hat{C}_n(X_{n+1})) \geq 1 - \alpha$$

for a pre-specified miscoverage level $\alpha \in (0,1)$, where the probability is taken over the randomness in the training data and the new covariate $X_{n+1}$.

**Key Challenge.** Unlike standard prediction problems, we never observe the true individual treatment effect $\tau_i$ for any unit in our training data. This creates a unique challenge for applying conformal prediction, which typically relies on computing nonconformity scores based on observed prediction errors.

## 4. Methodology

Our approach addresses the fundamental challenge of unobserved individual treatment effects by constructing conformal prediction intervals around CATE estimates. We leverage the fact that while individual treatment effects are unobserved, we can estimate them using any base CATE estimation method and then apply conformal prediction to quantify uncertainty around these estimates.

### 4.1 Conformal CATE Prediction

Let $\hat{\tau}(\cdot)$ be any CATE estimator trained on data $\{(X_i, T_i, Y_i)\}_{i=1}^n$. For a new point $x$, we want to construct a prediction interval for $\tau(x)$.

We define our nonconformity score as:
$$S((x, \tau), \mathcal{D}) = |\tau - \hat{\tau}_{-x}(x)|$$

where $\hat{\tau}_{-x}(\cdot)$ is the CATE estimator trained on dataset $\mathcal{D}$ excluding any point with covariate $x$, and $\tau$ is a candidate treatment effect value.

However, since we never observe true treatment effects $\tau_i$, we cannot directly compute these scores for training points. Instead, we use a cross-validation approach:

**Algorithm 1: Conformal CATE Prediction**
1. Split training data into $K$ folds: $\mathcal{D} = \mathcal{D}_1 \cup \cdots \cup \mathcal{D}_K$
2. For each fold $k = 1, \ldots, K$:
   - Train CATE estimator $\hat{\tau}^{(-k)}$ on $\mathcal{D} \setminus \mathcal{D}_k$
   - For each $(X_i, T_i, Y_i) \in \mathcal{D}_k$, compute pseudo-treatment effect:
     $$\tilde{\tau}_i = \hat{\mu}^{(-k)}_1(X_i) - \hat{\mu}^{(-k)}_0(X_i)$$
     where $\hat{\mu}^{(-k)}_t(x) = \mathbb{E}[Y | X = x, T = t]$ estimated on $\mathcal{D} \setminus \mathcal{D}_k$
3. Compute nonconformity scores: $V_i = |\tilde{\tau}_i - \hat{\tau}^{(-k)}(X_i)|$ for $i \in \mathcal{D}_k$
4. For new point $x$, construct interval:
   $$\hat{C}_n(x) = \hat{\tau}(x) \pm \text{Quantile}\left(\frac{\lceil (1-\alpha)(n+1) \rceil}{n}, \{V_i\}_{i=1}^n\right)$$

### 4.2 Weighted Conformal Prediction for Observational Studies

In observational studies, treatment assignment is not randomized, potentially violating the exchangeability assumption required for standard conformal prediction. We address this using inverse propensity weighting combined with weighted conformal prediction.

Let $\hat{e}(x)$ be an estimated propensity score. We define weights:
$$w_i = \frac{T_i}{\hat{e}(X_i)} + \frac{1-T_i}{1-\hat{e}(X_i)}$$

These weights rebalance the data to approximate a randomized experiment. We then apply weighted conformal prediction [Tibshirani et al., 2020]:

**Algorithm 2: Weighted Conformal CATE Prediction**
1. Compute propensity weights $w_i$ for all training points
2. Follow Algorithm 1 to compute nonconformity scores $V_i$
3. For new point $x$ with weight $w(x)$, construct weighted quantile:
   $$\hat{C}_n(x) = \hat{\tau}(x) \pm \text{WQuantile}\left(1-\alpha, \{V_i\}_{i=1}^n, \{w_i\}_{i=1}^n\right)$$

where WQuantile computes the weighted quantile using the procedure from Tibshirani et al. [2020].

### 4.3 Handling Covariate Shift

When deploying CATE models to new populations with different covariate distributions, we extend our approach using the weighted conformal prediction framework for covariate shift.

Let $P_X$ and $\tilde{P}_X$ denote the covariate distributions in the training and target populations, respectively. Assuming we can estimate the likelihood ratio $w(x) = d\tilde{P}_X(x)/dP_X(x)$, we apply the weighted conformal procedure:

**Algorithm 3: Conformal CATE under Covariate Shift**
1. Estimate likelihood ratio $w(x) = d\tilde{P}_X(x)/dP_X(x)$ using training and target covariate data
2. Compute nonconformity scores $V_i$ as in Algorithm 1
3. For new point $x$ from target population:
   $$\hat{C}_n(x) = \hat{\tau}(x) \pm \text{WQuantile}\left(1-\alpha, \{V_i\}_{i=1}^n, \{w(X_i)\}_{i=1}^n\right)$$

## 5. Theoretical Analysis

We provide theoretical guarantees for our conformal CATE prediction intervals. Our main result shows that the intervals maintain valid coverage even when the base CATE estimator is misspecified.

**Theorem 1 (Coverage Guarantee).** Under the unconfoundedness assumption and assuming the data satisfies exchangeability after propensity score weighting, the prediction intervals constructed by Algorithm 2 satisfy:
$$P(\tau(X_{n+1}) \in \hat{C}_n(X_{n+1})) \geq 1 - \alpha$$

*Proof Sketch:* The key insight is that our construction ensures the nonconformity scores $V_i$ are exchangeable with the nonconformity score that would be computed for the test point. Even though we use pseudo-treatment effects $\tilde{\tau}_i$ instead of true treatment effects, the exchangeability property is preserved because:

1. The pseudo-treatment effects $\tilde{\tau}_i$ are constructed using the same procedure for all points
2. The cross-validation ensures that the CATE estimator used to compute $\tilde{\tau}_i$ is independent of the point $(X_i, T_i, Y_i)$
3. Under unconfoundedness, $\tilde{\tau}_i$ is an unbiased estimator of $\tau(X_i)$

The weighted version handles non-exchangeable data by reweighting to approximate exchangeability, following the framework of Tibshirani et al. [2020].

**Theorem 2 (Robustness to Model Misspecification).** The coverage guarantee in Theorem 1 holds even when the base CATE estimator $\hat{\tau}$ is misspecified, provided that the outcome regression models used to construct pseudo-treatment effects satisfy certain consistency conditions.

*Proof Sketch:* The robustness comes from the fact that our nonconformity scores measure the discrepancy between pseudo-treatment effects and CATE estimates. Even if $\hat{\tau}$ is misspecified, as long as the pseudo-treatment effects provide reasonable approximations to true treatment effects, the conformal procedure will adapt to the estimation errors and maintain coverage.

**Theorem 3 (Covariate Shift).** Under covariate shift, if the likelihood ratio $w(x) = d\tilde{P}_X(x)/dP_X(x)$ can be estimated consistently, then Algorithm 3 provides valid coverage for the target population:
$$P_{\tilde{P}}(\tau(X_{n+1}) \in \hat{C}_n(X_{n+1})) \geq 1 - \alpha$$

where $P_{\tilde{P}}$ denotes probability under the target distribution.

## 6. Experimental Design

We would conduct comprehensive experiments to evaluate our method across different settings and compare against existing approaches for uncertainty quantification in CATE estimation.

**Synthetic Data Experiments:**
- Generate data with known treatment effects using various functional forms (linear, non-linear, discontinuous)
- Vary sample sizes from 500 to 5000 to assess finite-sample performance
- Test different levels of treatment effect heterogeneity
- Introduce model misspecification by using different data generating processes than those assumed by base CATE estimators
- Evaluate coverage rates, interval widths, and computational efficiency

**Semi-synthetic Benchmarks:**
- Use datasets like IHDP (Infant Health and Development Program) and ACIC 2016 competition datasets where ground truth treatment effects are available through simulation
- Compare against asymptotic confidence intervals from causal forests and meta-learners
- Evaluate performance under different propensity score specifications
- Test robustness to violations of overlap assumption

**Real Data Applications:**
- Apply to observational studies in healthcare (e.g., treatment effectiveness studies)
- Demonstrate covariate shift scenarios using multi-site clinical trials
- Compare interval coverage on held-out test sets using cross-validation
- Assess practical utility by measuring how often intervals inform decision-making

**Baseline Methods:**
- Asymptotic confidence intervals from causal forests [Wager & Athey, 2018]
- Bootstrap intervals for meta-learners
- Bayesian approaches with credible intervals
- Jackknife variance estimation methods

**Evaluation Metrics:**
- Coverage rates (primary metric)
- Average interval width (efficiency)
- Computational time
- Robustness to hyperparameter choices
- Performance under covariate shift

**Ablation Studies:**
- Effect of different base CATE estimators
- Impact of cross-validation fold number
- Sensitivity to propensity score estimation
- Performance with different sample splitting ratios

## 7. Discussion

**Strengths:** Our approach provides several key advantages over existing methods for uncertainty quantification in CATE estimation. The finite-sample coverage guarantees offer stronger theoretical foundations than asymptotic approaches, which is particularly valuable in applications with limited sample sizes. The distribution-free nature means the method works without strong parametric assumptions about the data generating process. The framework's compatibility with any base CATE estimator makes it broadly applicable across different machine learning approaches.

**Limitations:** The method requires the ability to estimate outcome regression models $\hat{\mu}_0$ and $\hat{\mu}_1$ reasonably well to construct meaningful pseudo-treatment effects. In settings with very high-dimensional covariates or complex interactions, this estimation step may be challenging. The cross-validation procedure increases computational cost compared to simple point estimation. The coverage guarantees assume unconfoundedness, which cannot be tested from observational data.

**Computational Considerations:** The cross-validation approach requires training multiple CATE estimators, increasing computational burden by a factor of $K$ (the number of folds). However, this can be parallelized, and the cost is often acceptable given the importance of uncertainty quantification in high-stakes applications.

**Extensions:** The framework could be extended to handle time-to-event outcomes, multiple treatments, or continuous treatments. The weighted conformal prediction approach could be adapted to handle other forms of distribution shift beyond covariate shift, such as temporal shift in longitudinal studies.

**Broader Impact:** Reliable uncertainty quantification for treatment effects is crucial for responsible deployment of machine learning in healthcare, policy, and other sensitive domains. By providing principled methods for assessing uncertainty around individual treatment effect predictions, this work contributes to more informed and safer decision-making in personalized interventions.

## 8. Conclusion

We have developed a novel framework that combines conformal prediction with causal inference to provide distribution-free prediction intervals for conditional average treatment effects. Our approach addresses a critical gap in the literature by offering finite-sample coverage guarantees without relying on asymptotic approximations or strong parametric assumptions.

The key contributions include: (1) a conformal prediction framework that handles the unique challenges of unobserved individual treatment effects, (2) extensions to observational studies through weighted conformal prediction, (3) methods for handling covariate shift between study and target populations, and (4) theoretical guarantees showing robustness to model misspecification.

**Open Questions:** Several important directions remain for future work. First, developing more efficient computational procedures that reduce the cross-validation overhead while maintaining coverage guarantees. Second, extending the framework to handle unmeasured confounding through sensitivity analysis approaches. Third, investigating how to optimally choose base CATE estimators to minimize interval width while maintaining coverage. Finally, developing adaptive procedures that can automatically adjust to the level of treatment effect heterogeneity in the data.

This work opens up new possibilities for principled uncertainty quantification in causal inference, with the potential to improve decision-making across numerous applications where understanding treatment effect heterogeneity is crucial.

## References

[Künzel et al., 2019] Künzel, S. R., Sekhon, J. S., Bickel, P. J., & Yu, B. (2019). Metalearners for estimating heterogeneous treatment effects using machine learning. *Proceedings of the National Academy of Sciences*, 116(10), 4156-4165.

[Lei & Wasserman, 2014] Lei, J., & Wasserman, L. (2014). Distribution-free prediction bands for non-parametric regression. *Journal of the Royal Statistical Society: Series B*, 76(1), 71-96.

[Lei et al., 2018] Lei, J., G'Sell, M., Rinaldo, A., Tibshirani, R. J., & Wasserman, L. (2018). Distribution-free predictive inference for regression. *Journal of the American Statistical Association*, 113(523), 1094-1111.

[Nie & Wager, 2021] Nie, X., & Wager, S. (2021). Quasi-oracle estimation of heterogeneous treatment effects. *Biometrika*, 108(2), 299-319.

[Rubin, 1974] Rubin, D. B. (1974). Estimating causal effects of treatments in randomized and nonrandomized studies. *Journal of Educational Psychology*, 66(5), 688-701.

[Sadinle et al., 2019] Sadinle, M., Lei, J., & Wasserman, L. (2019). Least ambiguous set-valued classifiers with bounded error levels. *Journal of the American Statistical Association*, 114(525), 223-234.

[Shalit et al., 2017] Shalit, U., Johansson, F. D., & Sontag, D. (2017). Estimating individual treatment effect: generalization bounds and algorithms. *Proceedings of the 34th International Conference on Machine Learning*, 3076-3085.

[Tibshirani et al., 2020] Tibshirani, R. J., Barber, R. F., Candes, E. J., & Ramdas, A. (2020). Conformal prediction under covariate shift. *Advances in Neural Information Processing Systems*, 33, 2530-2540.

[Vovk et al., 2005] Vovk, V., Gammerman, A., & Shafer, G. (2005). *Algorithmic learning in a random world*. Springer Science & Business Media.

[Wager & Athey, 2018] Wager, S., & Athey, S. (2018). Estimation and inference of heterogeneous treatment effects using random forests. *Journal of the American Statistical Association*, 113(523), 1228-1242.

[Yoon et al., 2018] Yoon, J., Jordon, J., & van der Schaar, M. (2018). GANITE: Estimation of individualized treatment effects using generative adversarial nets. *International Conference on Learning Representations*.
