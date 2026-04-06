# Reconstruction: full_guided
**Paper:** 2006.06138  
**Condition:** no_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Distribution-Free Prediction Intervals for Individual Treatment Effects

## Abstract

Understanding treatment effect heterogeneity is crucial for personalized decision-making, yet existing methods for estimating conditional average treatment effects (CATE) provide poor uncertainty quantification. We address the fundamental challenge of constructing prediction intervals for individual treatment effects when only one potential outcome is observed per unit. We propose a novel framework that combines conformal prediction with causal inference to provide distribution-free prediction intervals with finite-sample coverage guarantees. Our approach handles both within-study inference (where one potential outcome is observed) and out-of-study inference (where both potential outcomes are unobserved) under covariate shift. The method requires no parametric assumptions and is robust to model misspecification of both outcome regression and propensity score models. We establish theoretical coverage guarantees and demonstrate how the framework accommodates various CATE estimators as base learners while maintaining valid uncertainty quantification.

## 1. Introduction

Personalized treatment decisions require understanding not just whether a treatment works on average, but how it affects different individuals. In precision medicine, knowing that a drug reduces symptoms for 70% of patients while causing adverse effects in 30% is far more actionable than knowing it has a positive average effect. Similarly, in policy evaluation, understanding which subpopulations benefit from interventions enables more targeted and effective resource allocation.

The fundamental challenge in estimating individual treatment effects lies in the missing data problem: for any individual, we observe only one potential outcome—either under treatment or control, but never both. This creates a unique inference problem that differs substantially from standard prediction tasks. While machine learning methods have been developed to estimate conditional average treatment effects (CATE), they typically provide point estimates without reliable uncertainty quantification, limiting their utility in high-stakes decision-making contexts.

Existing approaches to CATE estimation uncertainty fall short in several ways. Bayesian methods require strong parametric assumptions that may be violated. Bootstrap-based approaches lack theoretical guarantees and can be computationally prohibitive. Asymptotic confidence intervals may not provide adequate coverage in finite samples, particularly when treatment effects are heterogeneous.

We propose a distribution-free framework for constructing prediction intervals for individual treatment effects that addresses these limitations. Our contributions include:

• A novel application of conformal prediction to causal inference that provides finite-sample coverage guarantees without parametric assumptions
• Separate treatments of within-study inference (one potential outcome observed) and out-of-study inference (both potential outcomes unobserved)  
• Theoretical analysis showing robustness to model misspecification of both outcome regression and propensity score models
• Extension to handle covariate shift between study and target populations
• A flexible framework that accommodates various CATE estimators as base learners while maintaining valid uncertainty quantification

## 2. Related Work

**Causal Inference and Treatment Effect Heterogeneity.** The potential outcomes framework provides the foundation for causal inference, with extensive work on estimating average treatment effects under unconfoundedness assumptions. Methods for estimating heterogeneous treatment effects include meta-learners such as T-learner, S-learner, and X-learner, as well as specialized approaches like causal forests and Bayesian additive regression trees. However, most focus on point estimation rather than uncertainty quantification.

**Uncertainty Quantification in Causal Inference.** Traditional approaches to uncertainty quantification in causal settings rely on asymptotic normality or bootstrap methods. Bayesian approaches provide posterior uncertainty but require strong modeling assumptions. Recent work has begun exploring conformal prediction for causal inference, but primarily for average treatment effects rather than individual-level heterogeneity.

**Conformal Prediction.** Conformal prediction provides a distribution-free framework for constructing prediction sets with finite-sample coverage guarantees. The method works by using a calibration set to determine how "nonconforming" a new prediction is relative to training data. Extensions include weighted conformal prediction for covariate shift and split conformal prediction for computational efficiency. However, application to causal inference presents unique challenges due to the missing data structure of potential outcomes.

**Distribution-Free Inference.** Beyond conformal prediction, other distribution-free methods include permutation tests, rank-based methods, and empirical likelihood approaches. These methods share the appealing property of providing valid inference without strong distributional assumptions, making them attractive for robust causal inference.

**Gap in Literature.** While conformal prediction has been applied to standard prediction problems and causal inference methods have been developed for treatment effect heterogeneity, the intersection remains largely unexplored. Existing work does not adequately address the unique challenges of constructing prediction intervals for individual treatment effects, particularly the distinction between within-study and out-of-study inference and the handling of covariate shift in causal settings.

## 3. Problem Formulation

**Notation and Setup.** Let $(X_i, T_i, Y_i)$ denote the observed data for unit $i$, where $X_i \in \mathcal{X}$ represents covariates, $T_i \in \{0,1\}$ is the treatment indicator, and $Y_i \in \mathbb{R}$ is the observed outcome. Under the potential outcomes framework, each unit has two potential outcomes: $Y_i(1)$ under treatment and $Y_i(0)$ under control. We observe $Y_i = T_i Y_i(1) + (1-T_i)Y_i(0)$.

The individual treatment effect (ITE) for unit $i$ is $\tau_i = Y_i(1) - Y_i(0)$. The conditional average treatment effect is $\tau(x) = \mathbb{E}[Y(1) - Y(0) | X = x]$.

**Assumptions.** We maintain standard causal inference assumptions:
1. **Unconfoundedness**: $(Y(1), Y(0)) \perp T | X$
2. **Overlap**: $0 < e(x) < 1$ for all $x$, where $e(x) = P(T=1|X=x)$ is the propensity score
3. **SUTVA**: No interference between units and treatment variation irrelevance

**Problem Statement.** Given training data $\{(X_i, T_i, Y_i)\}_{i=1}^n$, we aim to construct prediction intervals for individual treatment effects that satisfy:

$$P(\tau \in C_\alpha(x)) \geq 1-\alpha$$

for a specified miscoverage level $\alpha \in (0,1)$, where $C_\alpha(x)$ is a prediction interval that may depend on covariates $x$.

We consider two distinct inference problems:
1. **Within-study inference**: For units in the study population where one potential outcome is observed
2. **Out-of-study inference**: For new units where both potential outcomes are unobserved

**Objective.** Construct a distribution-free method that provides finite-sample coverage guarantees without parametric assumptions, handles covariate shift, and accommodates various CATE estimators as base learners.

## 4. Methodology

**Overview.** Our approach combines conformal prediction with causal inference by treating the individual treatment effect as a partially observed quantity that can be conformalized. The key insight is to construct conformity scores that account for the missing data structure of potential outcomes.

**Base CATE Estimator.** Let $\hat{\tau}(x)$ denote any CATE estimator trained on the data. This could be a meta-learner (T-learner, S-learner, X-learner), causal forest, or other method. Our framework is agnostic to the choice of base estimator.

**Conformity Scores for ITEs.** For within-study inference, we define conformity scores that measure how well the CATE estimate predicts the observable component of the ITE. For unit $i$, define:

$$R_i = \begin{cases}
Y_i - \hat{\mu}_0(X_i) - \hat{\tau}(X_i) & \text{if } T_i = 1 \\
\hat{\mu}_0(X_i) + \hat{\tau}(X_i) - Y_i & \text{if } T_i = 0
\end{cases}$$

where $\hat{\mu}_0(x)$ is an estimate of $\mathbb{E}[Y(0)|X=x]$. This score measures the residual between the observed outcome and the predicted potential outcome.

**Algorithm for Within-Study Inference:**

1. Split data into training set $I_{\text{train}}$ and calibration set $I_{\text{cal}}$
2. Train CATE estimator $\hat{\tau}(x)$ and outcome model $\hat{\mu}_0(x)$ on $I_{\text{train}}$
3. Compute conformity scores $\{R_i\}_{i \in I_{\text{cal}}}$ 
4. For new unit with covariates $x$ and observed outcome under treatment $t$:
   - Compute predicted counterfactual: $\hat{y}_{1-t} = \hat{\mu}_0(x) + (1-t)\hat{\tau}(x)$ if $t=0$, or $\hat{y}_{1-t} = \hat{\mu}_0(x)$ if $t=1$
   - Construct interval: $\hat{\tau}(x) \pm Q_{1-\alpha}(\{|R_i|\}_{i \in I_{\text{cal}}})$

**Out-of-Study Inference.** For new units where both potential outcomes are unobserved, we use a different approach based on the joint distribution of potential outcomes:

$$R_i^{\text{out}} = |\hat{\tau}(X_i) - \tilde{\tau}_i|$$

where $\tilde{\tau}_i$ is a pseudo-ITE constructed using both treated and control units with similar covariates through matching or weighting.

**Handling Covariate Shift.** When the target population differs from the study population, we employ weighted conformal prediction. Let $w(x) = \frac{q(x)}{p(x)}$ where $p(x)$ and $q(x)$ are the covariate densities in source and target populations. The weighted quantile is:

$$Q_{1-\alpha}^w = \inf\left\{t : \sum_{i \in I_{\text{cal}}} w(X_i) \mathbb{I}(R_i \leq t) \geq (1-\alpha)\sum_{i \in I_{\text{cal}}} w(X_i)\right\}$$

**Theoretical Properties.** Under the stated assumptions and exchangeability of calibration data, our method provides:
- Marginal coverage: $P(\tau \in C_\alpha(X)) \geq 1-\alpha$ 
- Robustness to model misspecification of both $\hat{\tau}$ and $\hat{\mu}_0$
- Valid coverage under covariate shift when weights are correctly specified

## 5. Theoretical Analysis

**Theorem 1 (Marginal Coverage).** Under unconfoundedness, overlap, and exchangeability of the calibration set, the conformal prediction interval satisfies:
$$P(\tau \in C_\alpha(X)) \geq 1-\alpha$$

*Proof Sketch:* The key insight is that the conformity scores $R_i$ are exchangeable under the stated assumptions. For within-study inference, the observed outcome provides information about one potential outcome, and the conformity score measures the prediction error for the unobserved counterfactual. By the conformal prediction guarantee, the $(1-\alpha)$-quantile of calibration scores provides the desired coverage.

**Theorem 2 (Robustness to Model Misspecification).** The coverage guarantee holds even when the base CATE estimator $\hat{\tau}$ and outcome model $\hat{\mu}_0$ are misspecified, provided the calibration data remains exchangeable.

*Proof Sketch:* Conformal prediction provides distribution-free guarantees that do not depend on the accuracy of the underlying model. The coverage depends only on the exchangeability of conformity scores, not on the quality of point predictions.

**Theorem 3 (Coverage Under Covariate Shift).** When covariate distributions differ between source and target populations, weighted conformal prediction with importance weights $w(x) = q(x)/p(x)$ maintains coverage:
$$P_{Q}(\tau \in C_\alpha^w(X)) \geq 1-\alpha$$
where $P_Q$ denotes probability under the target distribution.

**Finite-Sample Properties.** Unlike asymptotic methods, our guarantees hold in finite samples. The prediction intervals may be conservative (coverage > $1-\alpha$) due to the discrete nature of empirical quantiles, but this conservatism decreases as the calibration set size increases.

**Conditional Coverage.** While we establish marginal coverage, conditional coverage $P(\tau \in C_\alpha(X) | X = x)$ is generally not guaranteed. This is a fundamental limitation of conformal prediction that affects our method as well. However, the intervals adapt to local prediction accuracy through the conformity scores.

## 6. Experimental Design

**Datasets.** We would evaluate our method on both synthetic and real datasets:

*Synthetic Data:* Generate data with known ground truth ITEs using various heterogeneity patterns (linear, nonlinear, interactions). Control treatment assignment mechanism (randomized vs. observational with confounding). Vary sample sizes and dimensionality.

*Semi-synthetic Data:* Use real covariate distributions (e.g., from IHDP, ACIC benchmarks) with synthetic potential outcomes to enable evaluation against ground truth.

*Real Data:* Apply to randomized controlled trials where treatment effect heterogeneity is of interest (e.g., medical trials, A/B tests with user heterogeneity).

**Baselines.** Compare against:
- Bootstrap confidence intervals for CATE estimates
- Bayesian credible intervals (using Bayesian CART, GP methods)
- Quantile regression approaches adapted for causal inference
- Oracle methods when ground truth is available

**Evaluation Metrics.**
- *Coverage*: Empirical coverage rates across different subgroups
- *Interval Width*: Average and median prediction interval widths
- *Conditional Coverage*: Coverage rates conditional on covariate values
- *Efficiency*: Comparison of interval widths among methods achieving nominal coverage

**Experimental Scenarios:**
1. *Base Learner Comparison*: Evaluate with different CATE estimators (T-learner, X-learner, causal forest)
2. *Sample Size Analysis*: Performance across varying training and calibration set sizes
3. *Covariate Shift*: Robustness when target population differs from training population
4. *Model Misspecification*: Performance when base learners are poorly specified
5. *Heterogeneity Patterns*: Different types of treatment effect heterogeneity (smooth vs. discontinuous)

**Ablation Studies:**
- Effect of calibration set size on coverage and efficiency
- Comparison of different conformity score definitions
- Impact of propensity score estimation quality
- Performance with different covariate shift scenarios

## 7. Discussion

**Strengths.** Our framework provides several advantages over existing approaches. The distribution-free nature eliminates the need for parametric assumptions that may be violated in practice. Finite-sample coverage guarantees offer reliability even with limited data, crucial in many causal inference applications. The framework's flexibility allows practitioners to use their preferred CATE estimator while gaining principled uncertainty quantification. Robustness to model misspecification provides additional reliability in real-world applications where perfect model specification is unrealistic.

**Limitations.** The method provides only marginal coverage, not conditional coverage, which limits its utility for individual-level decisions. Prediction intervals may be conservative, particularly with small calibration sets. The approach requires splitting data between training and calibration, potentially reducing power. For out-of-study inference, the method relies on the quality of pseudo-ITE construction, which may be challenging when populations differ substantially.

**Computational Considerations.** The method is computationally efficient, requiring only sorting of conformity scores after base model training. However, for large datasets, the calibration step scales linearly with calibration set size. Weighted conformal prediction adds complexity when handling covariate shift, requiring accurate estimation of importance weights.

**Broader Impact.** Reliable uncertainty quantification for individual treatment effects has significant implications for personalized medicine, policy evaluation, and algorithmic decision-making. However, practitioners must be cautious about over-interpreting prediction intervals, particularly regarding conditional coverage. The method's robustness properties make it suitable for deployment in sensitive applications where model misspecification is a concern.

**Extensions.** Future work could explore conditional coverage improvements through localized conformal prediction or adaptive methods. Multi-armed treatment settings present additional challenges and opportunities. Integration with active learning could optimize data collection for improved interval efficiency.

## 8. Conclusion

We have presented a novel framework for constructing distribution-free prediction intervals for individual treatment effects that addresses a critical gap in causal inference methodology. By combining conformal prediction with causal inference principles, our approach provides finite-sample coverage guarantees without parametric assumptions while maintaining robustness to model misspecification.

The framework handles both within-study and out-of-study inference scenarios, accommodates covariate shift, and works with various CATE estimators as base learners. Theoretical analysis establishes marginal coverage guarantees and robustness properties, while the proposed experimental design would comprehensively evaluate performance across diverse scenarios.

Key contributions include the novel application of conformal prediction to individual treatment effects, theoretical coverage guarantees under causal inference assumptions, and a flexible framework that enhances existing CATE estimation methods with principled uncertainty quantification.

Open questions remain regarding conditional coverage improvements, optimal calibration set sizing, and extensions to more complex treatment regimes. Nevertheless, this work provides a solid foundation for reliable uncertainty quantification in personalized treatment effect estimation, with immediate applications in precision medicine, policy evaluation, and algorithmic decision-making.

## References

[Note: As no specific references were provided, this section would typically include relevant citations from the causal inference, conformal prediction, and uncertainty quantification literature, formatted as requested.]
