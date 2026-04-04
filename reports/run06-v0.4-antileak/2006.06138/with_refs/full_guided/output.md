# Reconstruction: full_guided
**Paper:** 2006.06138  
**Condition:** with_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Conformal Prediction for Individual Treatment Effect Uncertainty Quantification

## Abstract

Estimating heterogeneous treatment effects is crucial for personalized decision-making across medicine, policy, and social sciences. While machine learning methods can estimate individual treatment effects, they provide poor uncertainty quantification—a critical limitation in high-stakes applications. We address this gap by developing a conformal prediction framework for individual treatment effect estimation that provides distribution-free uncertainty quantification without strong parametric assumptions. Our approach leverages recent advances in weighted conformal prediction to handle the fundamental challenge that we never observe both potential outcomes for any individual. We extend conformal methods to the causal inference setting by constructing prediction intervals for counterfactual outcomes and combining them to quantify uncertainty in treatment effect estimates. Our framework accommodates both randomized experiments and observational studies, handles covariate shift between populations, and provides finite-sample coverage guarantees regardless of model complexity or dimensionality. The method is robust to model misspecification and provides reliable uncertainty bounds that account for both sampling variability and inherent response heterogeneity.

## 1. Introduction

Understanding how treatments affect different individuals is fundamental to personalized medicine, targeted policy interventions, and evidence-based decision-making. While average treatment effects provide useful population-level summaries, they can mask substantial heterogeneity in individual responses. A treatment showing positive average effects might help most patients while severely harming a minority, raising critical questions about deployment and risk assessment.

The challenge of estimating individual treatment effects is compounded by the fundamental problem of causal inference: we never observe both potential outcomes for any individual [Rubin, 1974]. This missing data problem makes uncertainty quantification particularly difficult, as standard statistical approaches rely on observing multiple realizations of the quantity of interest.

Recent advances in machine learning have produced sophisticated methods for estimating heterogeneous treatment effects [Künzel et al., 2019; Chernozhukov et al., 2018]. However, these methods typically provide point estimates without reliable uncertainty quantification. This limitation is particularly problematic in high-stakes applications where understanding the reliability of predictions is as important as the predictions themselves.

Conformal prediction [Vovk et al., 2005] offers a promising framework for distribution-free uncertainty quantification that makes minimal assumptions about the underlying data distribution. Recent work has extended conformal methods beyond the exchangeable setting to handle covariate shift [Tibshirani et al., 2020], opening possibilities for causal inference applications where treatment and control groups may have different covariate distributions.

**Contributions:**
• We develop the first conformal prediction framework for individual treatment effect estimation, providing distribution-free uncertainty quantification for causal effects
• We extend weighted conformal prediction to handle the missing counterfactual problem inherent in causal inference
• We provide finite-sample coverage guarantees that hold regardless of model complexity, dimensionality, or distributional assumptions
• We accommodate both randomized experiments and observational studies under standard causal assumptions
• We handle covariate shift between target populations and experimental populations

## 2. Related Work

**Heterogeneous Treatment Effect Estimation:** The literature on estimating treatment effect heterogeneity has evolved from simple subgroup analyses to sophisticated machine learning approaches. Meta-learners such as the T-learner, S-learner, and X-learner [Künzel et al., 2019] adapt standard supervised learning algorithms to the causal setting. Double machine learning approaches [Chernozhukov et al., 2018] provide theoretical guarantees for treatment effect estimation in high-dimensional settings. Causal forests [Wager & Athey, 2018] extend random forests to estimate conditional average treatment effects with asymptotic normality results.

However, these methods typically rely on asymptotic approximations for uncertainty quantification, which may perform poorly in finite samples or under model misspecification. Moreover, they often require strong parametric assumptions or specific functional form assumptions that may not hold in practice.

**Conformal Prediction:** Conformal prediction provides distribution-free prediction intervals with finite-sample coverage guarantees [Vovk et al., 2005]. The framework requires only exchangeability of the data and makes no distributional assumptions. Recent developments have extended conformal methods to regression [Lei & Wasserman, 2014], high-dimensional settings [Lei et al., 2018], and time series [Xu & Xie, 2021].

Tibshirani et al. [2020] developed weighted conformal prediction to handle covariate shift, where training and test distributions differ but the likelihood ratio is known or estimable. This extension is particularly relevant for causal inference, where treatment and control groups may have different covariate distributions.

**Uncertainty Quantification in Causal Inference:** Most work on uncertainty quantification in causal inference focuses on average treatment effects rather than individual effects. Bootstrap methods [Efron & Tibshirani, 1993] and asymptotic approximations are commonly used but may not provide reliable finite-sample coverage. Bayesian approaches [Hill, 2011] can provide uncertainty quantification but require strong prior assumptions.

**Gap in Literature:** Despite extensive work on both heterogeneous treatment effect estimation and conformal prediction, no existing method provides distribution-free uncertainty quantification for individual treatment effects. This gap is particularly important given the high-stakes nature of many causal inference applications.

## 3. Problem Formulation

**Notation:** Let $(X_i, T_i, Y_i)$ denote the observed data for individual $i$, where $X_i \in \mathbb{R}^d$ is a covariate vector, $T_i \in \{0,1\}$ is the treatment indicator, and $Y_i \in \mathbb{R}$ is the observed outcome. We use the potential outcomes framework with $Y_i(0)$ and $Y_i(1)$ denoting the potential outcomes under control and treatment, respectively. The observed outcome is $Y_i = T_i Y_i(1) + (1-T_i) Y_i(0)$.

**Fundamental Problem:** For any individual, we observe only one potential outcome. The individual treatment effect is $\tau_i = Y_i(1) - Y_i(0)$, but this is never directly observable.

**Assumptions:** We make standard causal inference assumptions:
1. **Stable Unit Treatment Value Assumption (SUTVA):** No interference between units and consistent treatment application
2. **Unconfoundedness:** $(Y_i(0), Y_i(1)) \perp T_i | X_i$
3. **Overlap:** $0 < P(T_i = 1 | X_i) < 1$ for all $x$ in the support of $X_i$

**Objective:** Given training data $\{(X_i, T_i, Y_i)\}_{i=1}^n$ and a new individual with covariates $X_{n+1}$, construct a prediction interval $\hat{C}_n(X_{n+1})$ such that:
$$P(\tau_{n+1} \in \hat{C}_n(X_{n+1})) \geq 1 - \alpha$$
for a specified miscoverage level $\alpha \in (0,1)$.

**Challenges:** 
1. We never observe $\tau_i$ directly, making standard conformal prediction inapplicable
2. Treatment and control groups may have different covariate distributions
3. The target population for inference may differ from the experimental population
4. We need finite-sample guarantees without distributional assumptions

## 4. Methodology

Our approach constructs conformal prediction intervals for individual treatment effects by separately modeling potential outcomes and combining the resulting uncertainty. The key insight is to treat the missing counterfactual problem as a covariate shift problem where we use weighted conformal prediction to handle the distributional differences between treatment groups.

**Step 1: Separate Outcome Models**
We fit separate models for each potential outcome using only the relevant observed data:
- Control model $\hat{\mu}_0(x)$ trained on $\{(X_i, Y_i) : T_i = 0\}$
- Treatment model $\hat{\mu}_1(x)$ trained on $\{(X_i, Y_i) : T_i = 1\}$

**Step 2: Weighted Conformal Prediction for Counterfactuals**
For a new individual with covariates $x$ and observed treatment $t$, we need to predict the counterfactual outcome $Y(1-t)$. This creates a covariate shift problem since the model for outcome $Y(1-t)$ was trained on individuals with treatment $(1-t)$, but we want to predict for someone who actually received treatment $t$.

We define the propensity score $e(x) = P(T = 1 | X = x)$ and use importance weights:
- For predicting $Y(0)$ when $T = 1$: $w_0(x) = \frac{1-e(x)}{e(x)}$
- For predicting $Y(1)$ when $T = 0$: $w_1(x) = \frac{e(x)}{1-e(x)}$

**Step 3: Conformal Prediction Intervals**
Using split conformal prediction for computational efficiency, we construct:

For control outcomes (using control group data):
$$\hat{C}_0(x) = \hat{\mu}_0(x) \pm \text{Quantile}\left(1-\alpha/2; \left\{\frac{|Y_i - \hat{\mu}_0(X_i)|}{w_0(X_i)}\right\}_{T_i=0} \cup \{\infty\}\right)$$

For treatment outcomes (using treatment group data):
$$\hat{C}_1(x) = \hat{\mu}_1(x) \pm \text{Quantile}\left(1-\alpha/2; \left\{\frac{|Y_i - \hat{\mu}_1(X_i)|}{w_1(X_i)}\right\}_{T_i=1} \cup \{\infty\}\right)$$

**Step 4: Treatment Effect Interval**
The individual treatment effect interval is:
$$\hat{C}_{\tau}(x) = \hat{C}_1(x) - \hat{C}_0(x) = [\hat{\mu}_1(x) - \hat{q}_0(x), \hat{\mu}_1(x) + \hat{q}_1(x)] - [\hat{\mu}_0(x) - \hat{q}_0(x), \hat{\mu}_0(x) + \hat{q}_0(x)]$$

where $\hat{q}_0(x)$ and $\hat{q}_1(x)$ are the weighted quantiles from Step 3.

**Algorithm:**
```
Input: Training data {(X_i, T_i, Y_i)}, test point x, level α
1. Split data by treatment: D_0 = {(X_i, Y_i) : T_i = 0}, D_1 = {(X_i, Y_i) : T_i = 1}
2. Estimate propensity scores: ê(x) for all x
3. Fit outcome models: μ̂_0 on D_0, μ̂_1 on D_1  
4. Compute importance weights: w_0(x) = (1-ê(x))/ê(x), w_1(x) = ê(x)/(1-ê(x))
5. Compute weighted residual quantiles:
   q̂_0 = Quantile(1-α/2; {|Y_i - μ̂_0(X_i)|/w_0(X_i) : T_i = 0} ∪ {∞})
   q̂_1 = Quantile(1-α/2; {|Y_i - μ̂_1(X_i)|/w_1(X_i) : T_i = 1} ∪ {∞})
6. Return: Ĉ_τ(x) = [μ̂_1(x) - μ̂_0(x) - q̂_1 - q̂_0, μ̂_1(x) - μ̂_0(x) + q̂_1 + q̂_0]
```

**Design Justification:** 
- Importance weighting corrects for covariate distribution differences between treatment groups
- Split conformal approach avoids overfitting and reduces computational burden
- Separate modeling of potential outcomes allows flexible model choice for each outcome
- Conservative interval combination ensures coverage while maintaining informativeness

## 5. Theoretical Analysis

**Theorem 1 (Coverage Guarantee):** Under the stated assumptions and with correctly specified propensity scores, the conformal prediction interval for individual treatment effects satisfies:
$$P(\tau_{n+1} \in \hat{C}_{\tau}(X_{n+1})) \geq 1 - \alpha$$

**Proof Sketch:** The key insight is that importance weighting makes the residuals from different treatment groups "look exchangeable" with respect to the target individual's counterfactual outcome.

For an individual with covariates $x$ who received treatment $t$, we need coverage for the counterfactual outcome $Y(1-t)$. The weighted conformal prediction ensures that:
$$P(Y_{n+1}(1-t) \in \hat{C}_{1-t}(X_{n+1})) \geq 1 - \alpha/2$$

By the union bound and independence of the potential outcomes conditioning on covariates:
$$P(Y_{n+1}(0) \in \hat{C}_0(X_{n+1}) \text{ and } Y_{n+1}(1) \in \hat{C}_1(X_{n+1})) \geq 1 - \alpha$$

Since $\tau_{n+1} = Y_{n+1}(1) - Y_{n+1}(0)$, the result follows from interval arithmetic.

**Theorem 2 (Robustness to Propensity Score Misspecification):** If the propensity score is estimated with bounded error $|\hat{e}(x) - e(x)| \leq \epsilon$ uniformly, then the coverage probability is bounded below by $1 - \alpha - \delta(\epsilon)$ where $\delta(\epsilon) \to 0$ as $\epsilon \to 0$.

**Corollary 1 (Randomized Experiments):** In randomized experiments where $e(x) = e$ is constant, the importance weights become unity and the method reduces to standard conformal prediction applied separately to each treatment group.

**Finite-Sample Properties:** Unlike asymptotic approaches, our coverage guarantees hold for any finite sample size $n$ and any model complexity. The method is valid regardless of whether the outcome models $\hat{\mu}_0, \hat{\mu}_1$ are correctly specified, though misspecification affects interval width.

**Computational Complexity:** The algorithm has complexity $O(n \log n)$ due to the quantile computations, making it scalable to large datasets.

## 6. Experimental Design

**Synthetic Data Experiments:**
We would evaluate the method on synthetic datasets with known ground truth treatment effects, varying:
- Sample sizes: $n \in \{100, 500, 1000, 5000\}$
- Dimensionality: $d \in \{5, 10, 20, 50\}$
- Effect heterogeneity: Linear, nonlinear, and discontinuous treatment effects
- Confounding strength: Weak, moderate, and strong confounding
- Model misspecification: Correct and incorrect functional forms for outcome models

**Real Data Applications:**
- **Medical:** Re-analysis of clinical trial data (e.g., ACTG 175 HIV treatment trial)
- **Economics:** Job training program evaluation using LaLonde dataset
- **Education:** School intervention effects using randomized education trials

**Baseline Methods:**
- Quantile regression approaches [Meinshausen, 2006]
- Bootstrap confidence intervals for meta-learners
- Bayesian methods with default priors [Hill, 2011]
- Asymptotic confidence intervals from causal forests [Wager & Athey, 2018]

**Evaluation Metrics:**
- **Coverage:** Empirical coverage probability compared to nominal level $1-\alpha$
- **Width:** Average and median interval widths
- **Conditional Coverage:** Coverage rates conditional on covariates and true effect sizes
- **Computational Time:** Runtime comparison across methods

**Ablation Studies:**
- Effect of propensity score estimation method
- Comparison of different outcome modeling approaches
- Sensitivity to hyperparameter choices
- Performance under various confounding scenarios

**Covariate Shift Experiments:**
We would test scenarios where the target population differs from the experimental population by:
- Simulating population shifts through importance sampling
- Using different propensity score models for data generation vs. analysis
- Evaluating robustness to covariate distribution changes

## 7. Discussion

**Expected Strengths:**
Our approach addresses a critical gap in causal inference by providing the first distribution-free uncertainty quantification method for individual treatment effects. The finite-sample coverage guarantees are particularly valuable in applications with limited data or high-stakes decisions. The method's robustness to model misspecification makes it broadly applicable across domains.

The framework naturally accommodates modern machine learning methods for outcome modeling while maintaining theoretical guarantees. This flexibility allows practitioners to leverage sophisticated algorithms while retaining reliable uncertainty quantification.

**Expected Limitations:**
The method requires accurate propensity score estimation, which can be challenging in observational studies with strong confounding. While we provide robustness results, severe propensity score misspecification could degrade coverage.

Interval width depends on the quality of outcome models and the degree of covariate overlap between treatment groups. In settings with limited overlap, intervals may be wide, reflecting the fundamental difficulty of extrapolation in causal inference.

The conservative nature of interval combination (using union bounds) may result in wider intervals than necessary, though this ensures valid coverage. More sophisticated combination methods could potentially improve efficiency.

**Broader Impact:**
This work has significant implications for personalized medicine, where understanding uncertainty in treatment effect estimates is crucial for patient safety and regulatory approval. In policy applications, reliable uncertainty quantification can inform decisions about program implementation and resource allocation.

The method could also impact machine learning fairness, as it provides tools for understanding whether algorithmic treatment recommendations are reliable across different demographic groups.

**Future Directions:**
Extensions could include handling multiple treatments, time-varying treatments, and survival outcomes. Integration with active learning frameworks could guide data collection to minimize uncertainty in treatment effect estimates.

## 8. Conclusion

We have developed the first conformal prediction framework for individual treatment effect estimation, providing distribution-free uncertainty quantification with finite-sample coverage guarantees. Our approach addresses the fundamental challenge of missing counterfactual outcomes through weighted conformal prediction, accommodating both randomized experiments and observational studies.

The method's key contributions include: (1) valid finite-sample coverage regardless of model complexity or dimensionality, (2) robustness to model misspecification, (3) accommodation of covariate shift between populations, and (4) computational efficiency suitable for large-scale applications.

**Open Questions:**
- Can we develop more efficient interval combination methods that maintain coverage while reducing width?
- How can the framework be extended to handle time-varying treatments and dynamic treatment regimes?
- What are the optimal strategies for outcome model selection within the conformal framework?
- Can we develop adaptive methods that adjust interval width based on local uncertainty?

This work opens new avenues for reliable uncertainty quantification in causal inference, with immediate applications in personalized medicine, policy evaluation, and algorithmic decision-making.

## References

[Chernozhukov et al., 2018] V. Chernozhukov, D. Chetverikov, M. Demirer, E. Duflo, C. Hansen, W. Newey, and J. Robins. Double/debiased machine learning for treatment and structural parameters. The Econometrics Journal, 21(1):C1–C68, 2018.

[Efron & Tibshirani, 1993] B. Efron and R. J. Tibshirani. An Introduction to the Bootstrap. Chapman & Hall, 1993.

[Hill, 2011] J. L. Hill. Bayesian nonparametric modeling for causal inference. Journal of Computational and Graphical Statistics, 20(1):217–240, 2011.

[Künzel et al., 2019] S. R. Künzel, J. S. Sekhon, P. J. Bickel, and B. Yu. Metalearners for estimating heterogeneous treatment effects using machine learning. Proceedings of the National Academy of Sciences, 116(10):4156–4165, 2019.

[Lei & Wasserman, 2014] J. Lei and L. Wasserman. Distribution-free prediction bands for non-parametric regression. Journal of the Royal Statistical Society: Series B, 76(1):71–96, 2014.

[Lei et al., 2018] J. Lei, M. G'Sell, A. Rinaldo, R. J. Tibshirani, and L. Wasserman. Distribution-free predictive inference for regression. Journal of the American Statistical Association, 113(523):1094–1111, 2018.

[Meinshausen, 2006] N. Meinshausen. Quantile regression forests. Journal of Machine Learning Research, 7:983–999, 2006.

[Rubin, 1974] D. B. Rubin. Estimating causal effects of treatments in randomized and nonrandomized studies. Journal of Educational Psychology, 66(5):688–701, 1974.

[Tibshirani et al., 2020] R. J. Tibshirani, R. F. Barber, E. J. Candès, and A. Ramdas. Conformal prediction under covariate shift. In Advances in Neural Information Processing Systems, pages 2530–2540, 2020.

[Vovk et al., 2005] V. Vovk, A. Gammerman, and G. Shafer. Algorithmic Learning in a Random World. Springer, 2005.

[Wager & Athey, 2018] S. Wager and S. Athey. Estimation and inference of heterogeneous treatment effects using random forests. Journal of the American Statistical Association, 113(523):1228–1242, 2018.

[Xu & Xie, 2021] C. Xu and Y. Xie. Conformal prediction interval for dynamic time-series. In International Conference on Machine Learning, pages 11559–11569, 2021.
