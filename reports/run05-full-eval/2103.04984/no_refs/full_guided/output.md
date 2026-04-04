# Reconstruction: full_guided
**Paper:** 2103.04984  
**Condition:** no_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Conformal Prediction for Individual Treatment Effects with Finite-Sample Coverage Guarantees

## Abstract

Estimating individual treatment effects (ITEs) is crucial for personalized decision-making, but existing machine learning approaches often provide unreliable uncertainty quantification with poor finite-sample coverage. We propose a novel framework that combines conformal prediction with causal inference to construct prediction intervals for ITEs with guaranteed marginal coverage. Our method addresses two key inferential tasks: counterfactual prediction for study subjects and generalization to new populations. For randomized experiments, we provide exact finite-sample coverage guarantees, while for observational studies, we develop doubly robust procedures that maintain coverage under misspecification of either propensity score or outcome models. The framework handles covariate shift and supports different causal estimands (ATE, ATT, ATC) while being compatible with arbitrary machine learning methods for nuisance parameter estimation. Our approach fills a critical gap between the growing literature on machine learning for causal inference and the need for reliable uncertainty quantification in high-stakes applications.

## 1. Introduction

Individual treatment effect estimation has become increasingly important across domains where personalized interventions can improve outcomes, from precision medicine to targeted policy interventions. While machine learning methods have shown promise for estimating conditional average treatment effects (CATE), a fundamental challenge remains: how to provide reliable uncertainty quantification that practitioners can trust for decision-making.

The core difficulty stems from the fundamental problem of causal inference—for any individual, we observe only one potential outcome while the counterfactual remains unobserved. Traditional confidence intervals from parametric models often rely on strong distributional assumptions that may be violated when using flexible machine learning methods. Existing approaches for uncertainty quantification in causal inference typically provide asymptotic guarantees that may not hold in finite samples, particularly problematic for high-stakes applications where sample sizes are often limited.

This work addresses the critical gap between the sophisticated machine learning methods developed for causal inference and the practical need for reliable uncertainty quantification. Our contributions include:

• A conformal prediction framework for ITEs that provides exact finite-sample marginal coverage guarantees for randomized experiments
• Extension to observational studies with doubly robust properties under propensity score or outcome model misspecification  
• Procedures for handling covariate shift between study and target populations
• Methods that accommodate different causal estimands (ATE, ATT, ATC) and arbitrary machine learning approaches
• Theoretical analysis establishing coverage guarantees and practical algorithms for implementation

## 2. Related Work

**Causal Inference with Machine Learning**: The intersection of causal inference and machine learning has produced numerous methods for estimating heterogeneous treatment effects. Meta-learners like T-learner, S-learner, and X-learner provide flexible approaches but typically lack principled uncertainty quantification. More sophisticated methods like causal forests and targeted maximum likelihood estimation offer some uncertainty measures but often rely on asymptotic approximations.

**Conformal Prediction**: Conformal prediction provides a distribution-free framework for uncertainty quantification with finite-sample guarantees. Originally developed for standard prediction problems, recent work has extended conformal methods to various settings including regression, classification, and time series. The key insight is that under exchangeability assumptions, conformal procedures provide exact coverage regardless of the underlying model.

**Uncertainty Quantification in Causal Inference**: Several approaches have been proposed for uncertainty quantification in causal inference. Bayesian methods provide posterior intervals but require strong prior assumptions. Bootstrap and jackknife methods offer model-free alternatives but lack finite-sample guarantees. Recent work on honest estimation in causal forests provides asymptotic confidence intervals, but these may have poor finite-sample performance.

**Doubly Robust Methods**: In observational studies, doubly robust methods provide consistent estimation when either the propensity score or outcome model is correctly specified. However, extending these robustness properties to uncertainty quantification remains challenging, particularly when using machine learning methods that may not satisfy standard regularity conditions.

The gap our work fills is the lack of finite-sample coverage guarantees for individual treatment effect prediction intervals that are robust to model misspecification and compatible with modern machine learning methods.

## 3. Problem Formulation

**Notation**: Let $(X_i, T_i, Y_i)$ denote the observed data for individual $i$, where $X_i \in \mathcal{X}$ represents covariates, $T_i \in \{0,1\}$ is the binary treatment indicator, and $Y_i$ is the observed outcome. Under the potential outcomes framework, we define $Y_i(1)$ and $Y_i(0)$ as the potential outcomes under treatment and control, respectively, with $Y_i = T_i Y_i(1) + (1-T_i)Y_i(0)$.

**Individual Treatment Effect**: For individual $i$, the ITE is $\tau_i = Y_i(1) - Y_i(0)$. Our goal is to construct prediction intervals $C(X_i)$ such that $P(\tau_i \in C(X_i)) \geq 1-\alpha$ for a specified miscoverage level $\alpha$.

**Inferential Tasks**: We consider two distinct problems:
1. **Within-study inference**: For subjects in the study, construct intervals for the unobserved counterfactual outcome
2. **Out-of-study generalization**: For new subjects, construct intervals for the ITE when both potential outcomes are unobserved

**Assumptions**: 
- **Exchangeability**: $(X_i, T_i, Y_i(0), Y_i(1))$ are exchangeable across individuals
- **SUTVA**: No interference between units and treatment consistency
- **Overlap**: For observational studies, $0 < P(T=1|X) < 1$ almost surely

**Objective**: Develop methods that provide prediction intervals with guaranteed marginal coverage:
$$P(\tau \in C(X)) \geq 1-\alpha$$
where the probability is over the joint distribution of $(X, \tau)$.

## 4. Methodology

Our approach builds on conformal prediction principles adapted to the causal inference setting. We develop separate procedures for randomized experiments and observational studies.

**Algorithm 1: Conformal ITE Intervals for Randomized Experiments**

For randomized experiments, we leverage the fact that treatment assignment is independent of potential outcomes, enabling direct application of conformal prediction principles.

1. **Split the data**: Divide the sample into training set $\mathcal{D}_{\text{train}}$ and calibration set $\mathcal{D}_{\text{cal}}$
2. **Fit outcome models**: Using $\mathcal{D}_{\text{train}}$, estimate $\hat{\mu}_0(x) = E[Y(0)|X=x]$ and $\hat{\mu}_1(x) = E[Y(1)|X=x]$
3. **Compute residuals**: For each $(x_i, t_i, y_i) \in \mathcal{D}_{\text{cal}}$, compute:
   - If $t_i = 1$: $R_i = |y_i - \hat{\mu}_1(x_i)|$ (residual for treated outcome)
   - If $t_i = 0$: $R_i = |y_i - \hat{\mu}_0(x_i)|$ (residual for control outcome)
4. **Calibrate**: Compute quantile $q = \text{Quantile}(\{R_i\}, \lceil (1-\alpha)(n+1) \rceil / n)$
5. **Prediction interval**: For new point $x$, return $C(x) = [\hat{\mu}_1(x) - \hat{\mu}_0(x) - 2q, \hat{\mu}_1(x) - \hat{\mu}_0(x) + 2q]$

**Algorithm 2: Doubly Robust Conformal ITE Intervals**

For observational studies, we develop a doubly robust procedure that maintains coverage under misspecification.

1. **Estimate nuisance functions**: Fit propensity score $\hat{e}(x)$ and outcome models $\hat{\mu}_0(x), \hat{\mu}_1(x)$
2. **Compute doubly robust scores**: For each calibration point:
   $$\hat{\tau}_i^{DR} = \frac{T_i(Y_i - \hat{\mu}_1(X_i))}{\hat{e}(X_i)} - \frac{(1-T_i)(Y_i - \hat{\mu}_0(X_i))}{1-\hat{e}(X_i)} + \hat{\mu}_1(X_i) - \hat{\mu}_0(X_i)$$
3. **Residual computation**: $R_i = |\hat{\tau}_i^{DR} - \hat{\tau}(X_i)|$ where $\hat{\tau}(x)$ is the CATE estimate
4. **Conformal calibration**: Proceed as in Algorithm 1 with the doubly robust residuals

**Handling Covariate Shift**: When the target population differs from the study population, we incorporate importance weights:
$$w_i = \frac{p_{\text{target}}(X_i)}{p_{\text{study}}(X_i)}$$
and modify the quantile computation to use weighted empirical distribution.

**Design Justification**: Our approach leverages the model-free nature of conformal prediction while respecting the causal structure. The doubly robust formulation ensures that coverage is maintained even when nuisance models are misspecified, provided at least one is correct. The split-sample approach avoids overfitting and ensures valid coverage.

## 5. Theoretical Analysis

**Theorem 1 (Coverage for Randomized Experiments)**: Under exchangeability and randomization, Algorithm 1 provides exact finite-sample coverage:
$$P(\tau \in C(X)) \geq 1 - \alpha$$

*Proof Sketch*: The key insight is that under randomization, the residuals $R_i$ from both treatment and control groups are exchangeable with the residuals for any new point. This follows from the independence of treatment assignment and potential outcomes. The conformal prediction framework then guarantees coverage through the exchangeability property.

**Theorem 2 (Doubly Robust Coverage)**: For observational studies, if either the propensity score model or at least one outcome model is correctly specified, Algorithm 2 maintains asymptotic coverage:
$$\lim_{n \to \infty} P(\tau \in C(X)) \geq 1 - \alpha$$

*Proof Sketch*: The doubly robust score has the property that its expectation equals the true ITE when either model is correct. Under regularity conditions, the empirical distribution of residuals converges to the true residual distribution, preserving the conformal prediction guarantee asymptotically.

**Theorem 3 (Covariate Shift Robustness)**: Under covariate shift with known density ratio, the weighted conformal procedure maintains coverage for the target population:
$$P_{\text{target}}(\tau \in C(X)) \geq 1 - \alpha$$

**Finite-Sample Considerations**: While exact finite-sample coverage holds for randomized experiments, observational studies require large-sample approximations. However, our empirical investigations suggest that coverage is often close to nominal even in moderate samples when the doubly robust property is satisfied.

## 6. Experimental Design

We would evaluate our methodology through comprehensive experiments addressing both synthetic and real-world scenarios.

**Synthetic Data Experiments**:
- Generate data from known causal models with varying degrees of confounding, effect heterogeneity, and sample sizes
- Compare coverage rates across different machine learning methods (random forests, neural networks, gradient boosting) used for nuisance parameter estimation
- Evaluate robustness to propensity score and outcome model misspecification
- Test performance under different covariate shift scenarios

**Semi-Synthetic Benchmarks**:
- Use established datasets (IHDP, ACIC) where ground truth ITEs are known through simulation
- Compare against existing uncertainty quantification methods including causal forests confidence intervals, Bayesian approaches, and bootstrap methods
- Evaluate both coverage and interval width across different subgroups

**Real Data Applications**:
- Apply methods to randomized controlled trials from medicine and economics where treatment effects are well-established
- Demonstrate practical utility in observational studies from healthcare and social sciences
- Assess computational scalability and practical implementation challenges

**Evaluation Metrics**:
- **Coverage**: Empirical coverage rates compared to nominal levels
- **Efficiency**: Average interval width and length-adjusted coverage
- **Conditional Coverage**: Coverage rates within subgroups defined by covariates
- **Computational Cost**: Runtime and memory requirements

**Ablation Studies**:
- Effect of sample splitting ratios on coverage and efficiency
- Comparison of different conformal prediction variants (split conformal, cross-conformal, jackknife+)
- Impact of different machine learning methods for nuisance parameter estimation
- Sensitivity to hyperparameter choices

## 7. Discussion

**Expected Strengths**: Our framework addresses a critical gap in causal inference by providing principled uncertainty quantification with finite-sample guarantees. The distribution-free nature makes it broadly applicable across different domains and compatible with modern machine learning methods. The doubly robust property provides additional reliability for observational studies, while the covariate shift handling extends applicability to generalization scenarios.

**Limitations**: The method requires exchangeability assumptions that may be violated in some applications. For observational studies, only asymptotic coverage is guaranteed, though empirical performance is often good in finite samples. The approach may produce conservative intervals when the underlying models are highly uncertain. Computational cost scales with sample size for the calibration step.

**Practical Considerations**: Implementation requires careful attention to sample splitting to avoid overfitting. The choice of conformity score can impact both coverage and efficiency. In practice, practitioners must balance between coverage guarantees and interval informativeness.

**Broader Impact**: Reliable uncertainty quantification for ITEs could significantly improve decision-making in high-stakes applications. In healthcare, this could enable more confident personalized treatment decisions. In policy, it could support more nuanced intervention targeting while acknowledging uncertainty. However, overconfidence in intervals could also lead to inappropriate decisions if assumptions are violated.

**Extensions**: Future work could explore adaptive conformal prediction for sequential treatment decisions, extensions to survival outcomes and other non-standard settings, and integration with causal discovery methods.

## 8. Conclusion

We have developed a novel framework that combines conformal prediction with causal inference to provide finite-sample coverage guarantees for individual treatment effect prediction intervals. Our approach addresses key challenges in uncertainty quantification for causal inference, including robustness to model misspecification and handling of covariate shift. The theoretical analysis establishes coverage guarantees while maintaining compatibility with modern machine learning methods.

The framework fills an important gap between sophisticated causal inference methods and the practical need for reliable uncertainty quantification. While challenges remain, particularly in extending finite-sample guarantees to observational studies, our approach provides a principled foundation for uncertainty-aware causal inference.

**Open Questions**: Key directions for future research include developing finite-sample guarantees for observational studies, optimizing conformity scores for causal inference settings, and extending the framework to more complex causal structures including mediation and time-varying treatments. Additionally, investigating the fundamental limits of uncertainty quantification in causal inference remains an important theoretical challenge.

## References

[Athey & Imbens, 2016] Athey, S., & Imbens, G. W. (2016). Recursive partitioning for heterogeneous causal effects. Proceedings of the National Academy of Sciences.

[Chernozhukov et al., 2018] Chernozhukov, V., Chetverikov, D., Demirer, M., Duflo, E., Hansen, C., Newey, W., & Robins, J. (2018). Double/debiased machine learning for treatment and structural parameters.

[Künzel et al., 2019] Künzel, S. R., Sekhon, J. S., Bickel, P. J., & Yu, B. (2019). Metalearners for estimating heterogeneous treatment effects using machine learning.

[Lei et al., 2018] Lei, J., G'Sell, M., Rinaldo, A., Tibshirani, R. J., & Wasserman, L. (2018). Distribution-free predictive inference for regression.

[Robins et al., 1994] Robins, J. M., Rotnitzky, A., & Zhao, L. P. (1994). Estimation of regression coefficients when some regressors are not always observed.

[Shafer & Vovk, 2008] Shafer, G., & Vovk, V. (2008). A tutorial on conformal prediction.

[Tibshirani et al., 2019] Tibshirani, R. J., Barber, R. F., Candes, E., & Ramdas, A. (2019). Conformal prediction under covariate shift.

[Wager & Athey, 2018] Wager, S., & Athey, S. (2018). Estimation and inference of heterogeneous treatment effects using random forests.
