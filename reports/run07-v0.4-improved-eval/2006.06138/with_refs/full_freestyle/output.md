# Reconstruction: full_freestyle
**Paper:** 2006.06138  
**Condition:** with_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Conformal Prediction for Heterogeneous Treatment Effects: Distribution-Free Uncertainty Quantification Under Covariate Shift

**Abstract**

Understanding how treatments affect individuals differently is crucial for personalized decision-making in medicine, policy, and social sciences. While methods for estimating conditional average treatment effects (CATE) have advanced significantly, reliable uncertainty quantification for individual treatment effects remains an open challenge. Existing approaches typically rely on asymptotic approximations or strong modeling assumptions that may not hold in practice. We propose a novel framework that adapts conformal prediction to provide distribution-free uncertainty intervals for heterogeneous treatment effects. Our method handles both randomized experiments and observational studies, accommodates covariate shift between study and target populations, and provides finite-sample coverage guarantees without requiring asymptotic regimes. We extend weighted conformal prediction to the causal inference setting, developing theory for treatment effect heterogeneity under potential outcomes framework. The resulting prediction intervals are valid regardless of the underlying data distribution or the machine learning algorithm used for CATE estimation, making our approach broadly applicable across domains where reliable uncertainty quantification is essential for safe decision-making.

## 1. Introduction

The fundamental problem of causal inference is that for any individual, we observe only one potential outcome—either under treatment or control—making individual treatment effects inherently unobservable. This missing data problem becomes particularly acute when we move beyond estimating average treatment effects to understanding treatment effect heterogeneity, where the goal is to predict how a specific individual will respond to treatment.

Current approaches to heterogeneous treatment effect estimation focus primarily on point estimation of conditional average treatment effects (CATE) using flexible machine learning methods. While these techniques can capture complex patterns in treatment response, they generally provide poor uncertainty quantification. Standard approaches rely on asymptotic normality assumptions, bootstrap procedures, or Bayesian methods that may not provide reliable coverage in finite samples, especially when the true data-generating process deviates from modeling assumptions.

This limitation is particularly concerning in high-stakes applications. In precision medicine, incorrect treatment recommendations could harm patients. In policy evaluation, poorly calibrated uncertainty estimates could lead to inefficient resource allocation. In these domains, decision-makers need not just point estimates but reliable uncertainty intervals that accurately reflect both the inherent variability in treatment response and the uncertainty due to finite sample estimation.

We address this challenge by developing a conformal prediction framework for heterogeneous treatment effects. Conformal prediction, pioneered by Vovk and colleagues, provides distribution-free prediction intervals with finite-sample coverage guarantees. Our key insight is that the exchangeability assumptions underlying conformal prediction can be adapted to the causal inference setting through careful construction of nonconformity scores that respect the potential outcomes framework.

Our contributions are threefold. First, we develop theory extending conformal prediction to treatment effect estimation, providing finite-sample coverage guarantees for individual treatment effect intervals without requiring asymptotic approximations or distributional assumptions. Second, we address the practically important case of covariate shift, where the study population differs from the target population, by adapting weighted conformal prediction techniques. Third, we show how our framework accommodates both randomized experiments and observational studies under standard identifying assumptions.

The resulting method provides prediction intervals for individual treatment effects that are valid regardless of the underlying data distribution, the machine learning algorithm used for estimation, or the sample size. This distribution-free property makes our approach broadly applicable across domains where reliable uncertainty quantification is essential.

## 2. Background and Related Work

### 2.1 Heterogeneous Treatment Effects

Let $Y(1)$ and $Y(0)$ denote potential outcomes under treatment and control, respectively, for a given individual. The individual treatment effect is $\tau = Y(1) - Y(0)$, which is never directly observable since we only see one potential outcome for each unit. The conditional average treatment effect (CATE) is defined as $\tau(x) = \mathbb{E}[Y(1) - Y(0) | X = x]$, where $X$ represents observed covariates.

Recent advances in CATE estimation have focused on flexible machine learning approaches including causal forests [Wager & Athey, 2018], meta-learners [Künzel et al., 2019], and deep learning methods [Shalit et al., 2017]. These methods can capture complex treatment effect heterogeneity but typically provide only point estimates or rely on asymptotic approximations for uncertainty quantification.

The challenge of uncertainty quantification for treatment effects has been recognized in several recent works. Bootstrap-based approaches suffer from computational burden and may not provide reliable coverage when the underlying model is misspecified. Bayesian methods require strong prior assumptions and can be sensitive to model specification. Our work addresses these limitations by providing a distribution-free alternative with finite-sample guarantees.

### 2.2 Conformal Prediction

Conformal prediction provides a framework for constructing prediction intervals with finite-sample coverage guarantees under minimal assumptions. Given training data $(X_i, Y_i)_{i=1}^n$ and a new covariate $X_{n+1}$, conformal prediction constructs a set $C_n(X_{n+1})$ such that $\mathbb{P}(Y_{n+1} \in C_n(X_{n+1})) \geq 1 - \alpha$ for any desired coverage level $1 - \alpha$.

The key insight is that if $(X_1, Y_1), \ldots, (X_{n+1}, Y_{n+1})$ are exchangeable, then appropriately constructed prediction sets achieve the desired coverage. The method relies on nonconformity scores that measure how unusual a point is relative to the training data.

Recent extensions have addressed covariate shift [Tibshirani et al., 2019], where training and test distributions differ but the likelihood ratio is known or estimable. This extension uses weighted exchangeability to maintain coverage guarantees when the covariate distributions differ between training and test populations.

### 2.3 Causal Inference Under Covariate Shift

The problem of covariate shift in causal inference arises when the study population differs from the target population of interest. This is common in practice—clinical trials may have different demographics than the general population, or policy evaluations may be conducted in specific contexts that differ from broader implementation settings.

Standard approaches to addressing covariate shift in causal inference include inverse probability weighting and outcome regression with careful attention to external validity. However, these methods typically focus on point estimation rather than uncertainty quantification. Our work extends these ideas to provide uncertainty intervals that are valid under covariate shift.

## 3. Methodology

### 3.1 Problem Setup

Consider $n$ units with observed data $(X_i, T_i, Y_i)_{i=1}^n$, where $X_i \in \mathbb{R}^d$ represents covariates, $T_i \in \{0,1\}$ is the treatment indicator, and $Y_i$ is the observed outcome. We observe $Y_i = T_i Y_i(1) + (1-T_i) Y_i(0)$, where $Y_i(1)$ and $Y_i(0)$ are potential outcomes.

Our goal is to construct prediction intervals for the individual treatment effect $\tau_{n+1} = Y_{n+1}(1) - Y_{n+1}(0)$ for a new unit with covariates $X_{n+1}$. We assume access to point estimates $\hat{\mu}_1(x) = \hat{\mathbb{E}}[Y(1)|X=x]$ and $\hat{\mu}_0(x) = \hat{\mathbb{E}}[Y(0)|X=x]$ from any machine learning algorithm, giving us $\hat{\tau}(x) = \hat{\mu}_1(x) - \hat{\mu}_0(x)$.

### 3.2 Conformal Prediction for Treatment Effects

The key challenge in adapting conformal prediction to treatment effects is constructing appropriate nonconformity scores. Since individual treatment effects are never observed, we cannot directly compute residuals as in standard regression conformal prediction.

Our approach constructs pseudo-residuals for treatment effects using the following insight: while we cannot observe $\tau_i$, we can construct unbiased estimates using the fitted outcome models and the observed data.

For unit $i$, define the pseudo-treatment effect as:
$$\tilde{\tau}_i = T_i \left(\frac{Y_i - \hat{\mu}_0(X_i)}{\hat{e}(X_i)}\right) + (1-T_i) \left(\frac{\hat{\mu}_1(X_i) - Y_i}{1-\hat{e}(X_i)}\right) + \hat{\tau}(X_i)$$

where $\hat{e}(x)$ is an estimate of the propensity score $\mathbb{P}(T=1|X=x)$. This construction ensures that $\mathbb{E}[\tilde{\tau}_i | X_i] = \tau(X_i)$ under standard identifying assumptions.

The nonconformity score for a candidate treatment effect value $\tau$ at covariate $x$ is:
$$V_i^{(x,\tau)} = |\tilde{\tau}_i - \tau|$$

This measures how well the candidate value $\tau$ conforms to the pseudo-treatment effect computed from the observed data.

### 3.3 Coverage Guarantees

Our main theoretical result establishes finite-sample coverage for treatment effect prediction intervals.

**Theorem 1.** Under the assumptions of unconfoundedness, overlap, and exchangeability of $(X_i, T_i, Y_i(0), Y_i(1))_{i=1}^{n+1}$, the conformal prediction interval
$$C_n(X_{n+1}) = \left\{\tau : V_{n+1}^{(X_{n+1},\tau)} \leq \text{Quantile}\left(1-\alpha; \{V_i^{(X_{n+1},\tau)}\}_{i=1}^n \cup \{\infty\}\right)\right\}$$
satisfies $\mathbb{P}(\tau_{n+1} \in C_n(X_{n+1})) \geq 1 - \alpha$.

The proof relies on showing that the nonconformity scores $V_i^{(X_{n+1},\tau_{n+1})}$ are exchangeable when $\tau = \tau_{n+1}$, despite the fact that individual treatment effects are unobserved.

### 3.4 Extension to Covariate Shift

In practice, the study population may differ from the target population. We extend our framework to handle covariate shift using weighted conformal prediction.

Suppose the study population has covariate distribution $P_X$ while the target population has distribution $\tilde{P}_X$. If the likelihood ratio $w(x) = d\tilde{P}_X(x)/dP_X(x)$ is known or can be estimated, we can modify the conformal procedure using weighted quantiles.

Define weights:
$$p_i^w(x) = \frac{w(X_i)}{\sum_{j=1}^n w(X_j) + w(x)}, \quad i = 1, \ldots, n$$
$$p_{n+1}^w(x) = \frac{w(x)}{\sum_{j=1}^n w(X_j) + w(x)}$$

The weighted conformal prediction interval becomes:
$$C_n^w(X_{n+1}) = \left\{\tau : V_{n+1}^{(X_{n+1},\tau)} \leq \text{Quantile}\left(1-\alpha; \sum_{i=1}^n p_i^w(X_{n+1}) \delta_{V_i^{(X_{n+1},\tau)}} + p_{n+1}^w(X_{n+1}) \delta_\infty\right)\right\}$$

**Theorem 2.** Under covariate shift with known likelihood ratio $w(x)$, the weighted conformal prediction interval $C_n^w(X_{n+1})$ satisfies $\mathbb{P}(\tau_{n+1} \in C_n^w(X_{n+1})) \geq 1 - \alpha$.

### 3.5 Computational Implementation

For computational efficiency, we adapt the split conformal approach to our setting. We divide the data into three parts:
1. Training set for fitting outcome models $\hat{\mu}_1$ and $\hat{\mu}_0$
2. Calibration set for computing nonconformity scores
3. Test set for evaluation

This avoids refitting models for each candidate $\tau$ value and makes the method computationally tractable for large datasets.

## 4. Theoretical Analysis

### 4.1 Validity Under Standard Assumptions

Our method requires three key assumptions:
1. **Unconfoundedness**: $(Y(0), Y(1)) \perp T | X$
2. **Overlap**: $0 < \mathbb{P}(T=1|X=x) < 1$ for all $x$ in the support
3. **Exchangeability**: $(X_i, T_i, Y_i(0), Y_i(1))_{i=1}^{n+1}$ are exchangeable

These are standard assumptions in causal inference. Unconfoundedness ensures identification of causal effects, overlap ensures finite variance of estimates, and exchangeability enables the conformal prediction framework.

### 4.2 Robustness to Model Misspecification

A key advantage of our approach is robustness to misspecification of the outcome models $\hat{\mu}_1$ and $\hat{\mu}_0$. Even if these models are incorrect, our prediction intervals maintain nominal coverage as long as the exchangeability assumption holds.

This robustness stems from the distribution-free nature of conformal prediction. The coverage guarantee depends only on the rank of the nonconformity score at the test point, not on the accuracy of the underlying models.

### 4.3 Adaptive Interval Widths

Our prediction intervals automatically adapt to the local uncertainty in treatment effect estimation. In regions where the outcome models are uncertain or where there is high variability in treatment response, the intervals will be wider. This adaptive behavior is achieved without explicit modeling of the uncertainty structure.

## 5. Experimental Design

We would evaluate our method through comprehensive simulation studies and real data applications designed to test key aspects of the framework.

### 5.1 Simulation Studies

**Synthetic Data Generation**: We would generate data with known heterogeneous treatment effects using various functional forms:
- Linear treatment effects: $\tau(x) = x^T\beta$  
- Nonlinear effects: $\tau(x) = \sin(x_1) + x_2^2$
- Interaction effects: $\tau(x) = x_1 \cdot x_2$

We would vary sample sizes, dimensionality, and noise levels to test robustness.

**Coverage Evaluation**: For each setting, we would compute empirical coverage rates across 1000 simulation replications. We expect coverage to be at or above the nominal level (e.g., 90%) with tight confidence intervals around the target.

**Comparison Methods**: We would compare against:
- Bootstrap confidence intervals from causal forests
- Bayesian credible intervals from Gaussian process methods  
- Asymptotic intervals from doubly robust estimators

We expect our method to achieve better coverage, especially in small samples or under model misspecification.

**Covariate Shift Experiments**: We would simulate covariate shift by reweighting the test distribution and compare our weighted conformal approach against standard methods that ignore the shift. We expect substantial improvements in coverage under covariate shift.

### 5.2 Real Data Applications

**Medical Data**: Using datasets like the IHDP benchmark, we would construct prediction intervals for treatment effects of interventions on health outcomes. We would evaluate coverage on held-out data and compare interval widths.

**Policy Evaluation**: Using data from randomized policy experiments, we would construct intervals for individual-level policy effects and assess their utility for targeting decisions.

**A/B Testing**: In online settings, we would apply our method to construct intervals for user-level treatment effects, demonstrating scalability to large datasets.

### 5.3 Expected Results

We anticipate several key findings:

**Superior Coverage**: Our method should achieve nominal coverage rates even in challenging settings where competing methods fail, particularly under model misspecification or in small samples.

**Adaptive Intervals**: Interval widths should appropriately reflect local uncertainty, being wider in regions with limited data or high variability and narrower where treatment effects are more precisely estimable.

**Robustness**: Coverage should remain stable across different outcome model specifications and estimation algorithms, demonstrating the distribution-free nature of our approach.

**Covariate Shift Benefits**: The weighted version should maintain coverage under covariate shift while standard methods deteriorate, with improvements being most pronounced when the shift is substantial.

## 6. Discussion and Future Directions

### 6.1 Practical Considerations

Our framework addresses several practical challenges in treatment effect uncertainty quantification. The distribution-free nature eliminates the need for practitioners to make strong distributional assumptions or worry about asymptotic approximations in finite samples. The modular design allows integration with any machine learning algorithm for outcome modeling.

However, several practical considerations remain. The method requires estimation of propensity scores, which can be challenging in high-dimensional settings. The exchangeability assumption may be violated in time series or spatial data. Future work could address these limitations through extensions to dependent data settings.

### 6.2 Connections to Selective Inference

Our work connects to the growing literature on selective inference and post-selection inference. When treatment assignment rules are derived from the same data used for inference, standard confidence intervals may not maintain coverage. Our framework could potentially be extended to provide valid inference after data-driven treatment assignment.

### 6.3 Multi-Armed and Continuous Treatments

While we focus on binary treatments, the framework could be extended to multi-armed or continuous treatment settings. This would require careful construction of nonconformity scores that respect the structure of the treatment space while maintaining exchangeability properties.

### 6.4 Causal Discovery Applications

An interesting future direction would be applying conformal prediction to uncertainty quantification in causal discovery, where the goal is to learn causal structure from data. Prediction intervals for causal effects could help quantify uncertainty about discovered relationships.

## 7. Conclusion

We have developed a novel framework for uncertainty quantification in heterogeneous treatment effect estimation that provides finite-sample coverage guarantees without requiring asymptotic approximations or strong modeling assumptions. By adapting conformal prediction to the causal inference setting, we address a critical gap in current methodology where reliable uncertainty quantification is essential for safe decision-making.

Our approach offers several key advantages: distribution-free validity, robustness to model misspecification, automatic adaptation to local uncertainty, and extensions to handle covariate shift between study and target populations. These properties make the method broadly applicable across domains where treatment effect heterogeneity is important.

The theoretical foundations we establish open several avenues for future research, including extensions to dependent data, multi-armed treatments, and selective inference settings. As personalized treatment decisions become increasingly important across medicine, policy, and technology, reliable uncertainty quantification methods like ours will be essential for translating research findings into safe and effective interventions.

The distribution-free nature of our approach represents a fundamental shift from current practice, providing practitioners with tools that work regardless of the underlying data distribution or the complexity of treatment effect patterns. This reliability is crucial for building trust in automated decision-making systems and ensuring that uncertainty quantification keeps pace with advances in treatment effect estimation.

## References

[1] Künzel, S. R., Sekhon, J. S., Bickel, P. J., & Yu, B. (2019). Metalearners for estimating heterogeneous treatment effects using machine learning. *Proceedings of the National Academy of Sciences*, 116(10), 4156-4165.

[2] Lei, J., G'Sell, M., Rinaldo, A., Tibshirani, R. J., & Wasserman, L. (2018). Distribution-free predictive inference for regression. *Journal of the American Statistical Association*, 113(523), 1094-1111.

[3] Lei, J., & Wasserman, L. (2014). Distribution-free prediction bands for non-parametric regression. *Journal of the Royal Statistical Society: Series B*, 76(1), 71-96.

[4] Shalit, U., Johansson, F. D., & Sontag, D. (2017). Estimating individual treatment effect: generalization bounds and algorithms. *International Conference on Machine Learning*, 3076-3085.

[5] Tibshirani, R. J., Barber, R. F., Candes, E. J., & Ramdas, A. (2019). Conformal prediction under covariate shift. *Advances in Neural Information Processing Systems*, 2530-2540.

[6] Vovk, V., Gammerman, A., & Shafer, G. (2005). *Algorithmic learning in a random world*. Springer Science & Business Media.

[7] Wager, S., & Athey, S. (2018). Estimation and inference of heterogeneous treatment effects using random forests. *Journal of the American Statistical Association*, 113(523), 1228-1242.
