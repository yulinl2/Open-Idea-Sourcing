# Reconstruction: full_freestyle
**Paper:** 2103.04984  
**Condition:** no_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Doubly Robust Conformal Prediction for Individual Treatment Effects

## Abstract

We develop a novel framework for constructing prediction intervals for individual treatment effects (ITEs) that provides finite-sample marginal coverage guarantees without strong modeling assumptions. Our method combines conformal prediction with doubly robust estimation to handle the fundamental challenge that individual counterfactuals are never observed. The key innovation is a cross-fitting procedure that constructs separate conformal predictors for treated and control outcomes, then combines them using influence function-based corrections to account for selection bias. We prove that our intervals achieve exact 1-α coverage for randomized experiments and maintain coverage under model misspecification in observational studies when either the propensity score or outcome models are correctly specified. The framework extends naturally to handle covariate shift between study and target populations, multiple inferential targets (ATE, ATT, ATC), and modern machine learning estimators. Through theoretical analysis and simulation studies, we demonstrate that our approach provides reliable uncertainty quantification for personalized treatment decisions while maintaining computational efficiency.

**Keywords:** Causal inference, conformal prediction, individual treatment effects, uncertainty quantification, doubly robust estimation

## 1. Introduction

The estimation of individual treatment effects (ITEs) has emerged as a central challenge in modern causal inference, driven by applications in precision medicine, personalized policy interventions, and algorithmic decision-making. While traditional causal inference focuses on population-level quantities like the average treatment effect (ATE), many practical scenarios require understanding how treatments affect specific individuals or subgroups. This shift toward personalized inference introduces fundamental statistical challenges that existing methods struggle to address satisfactorily.

The core difficulty lies in the fundamental problem of causal inference: for any individual, we observe only one potential outcome—either under treatment or control—while the counterfactual remains unobserved. This missing data problem is particularly acute when constructing prediction intervals for ITEs, as standard uncertainty quantification techniques assume access to true outcomes for validation. Moreover, the inferential task bifurcates into two distinct scenarios: (1) predicting counterfactuals for individuals in the study sample where one potential outcome is observed, and (2) predicting both potential outcomes for new individuals from potentially different populations.

Existing approaches to ITE estimation, while sophisticated in their use of machine learning techniques, typically provide point estimates with ad-hoc uncertainty measures that lack finite-sample guarantees. Methods based on Bayesian inference require strong prior assumptions, while frequentist approaches often rely on asymptotic normality that may not hold in finite samples or with complex estimators. The resulting confidence intervals frequently exhibit poor coverage properties, particularly when modern machine learning methods are employed for nuisance parameter estimation.

This paper introduces a novel framework that addresses these limitations by combining conformal prediction with doubly robust causal inference. Conformal prediction offers an attractive solution to the uncertainty quantification problem because it provides distribution-free, finite-sample coverage guarantees without requiring strong modeling assumptions. However, naively applying conformal methods to causal inference fails because the standard assumption that outcomes are exchangeable is violated when treatment assignment depends on covariates.

Our main contributions are threefold:

**Theoretical Innovation:** We develop a doubly robust conformal prediction framework that constructs valid prediction intervals for ITEs under minimal assumptions. Our method uses cross-fitting to separate the roles of outcome modeling and propensity score estimation, ensuring that coverage guarantees hold even when one of these nuisance functions is misspecified.

**Methodological Framework:** We provide a unified approach that handles multiple inferential scenarios: within-study counterfactual prediction, out-of-study generalization under covariate shift, and various causal estimands (ATE, ATT, ATC). The framework naturally accommodates modern machine learning estimators while preserving coverage properties.

**Practical Implementation:** We demonstrate how the theoretical framework translates into computationally efficient algorithms that can be readily applied to real-world problems. The method requires minimal hyperparameter tuning and provides interpretable uncertainty measures for practitioners.

The remainder of the paper is organized as follows. Section 2 reviews related work in causal inference, conformal prediction, and uncertainty quantification. Section 3 formalizes the problem setup and introduces our notation. Section 4 presents the core theoretical development, including our doubly robust conformal prediction algorithm and coverage guarantees. Section 5 extends the framework to handle covariate shift and multiple inferential targets. Section 6 describes our experimental design and expected results. Section 7 concludes with implications and future directions.

## 2. Related Work

### 2.1 Individual Treatment Effect Estimation

The literature on ITE estimation has evolved rapidly, driven by advances in machine learning and growing demand for personalized interventions. Early approaches focused on parametric models that directly estimate the conditional average treatment effect (CATE) function $\tau(x) = \mathbb{E}[Y(1) - Y(0) | X = x]$, where $Y(1)$ and $Y(0)$ represent potential outcomes under treatment and control, respectively.

Modern methods leverage flexible machine learning techniques to estimate ITEs without strong functional form assumptions. Notable approaches include causal forests [Wager & Athey, 2018], which extend random forests to causal settings; neural network-based methods like TARNet and CFR [Shalit et al., 2017]; and meta-learning approaches that decompose the ITE estimation problem into supervised learning subproblems [Künzel et al., 2019]. While these methods have shown impressive empirical performance, they typically provide only point estimates or heuristic uncertainty measures that lack theoretical guarantees.

The challenge of uncertainty quantification for ITEs has received increasing attention. Bayesian approaches, such as Bayesian Additive Regression Trees for causal inference [Hill, 2011], provide posterior distributions over treatment effects but require strong prior specifications. Frequentist methods often rely on asymptotic theory or bootstrap procedures that may not provide accurate coverage in finite samples, particularly when complex machine learning estimators are employed.

### 2.2 Doubly Robust Estimation

Doubly robust estimation has emerged as a cornerstone of modern causal inference, providing protection against model misspecification by combining outcome regression and propensity score methods. The key insight is that valid causal inference requires correct specification of only one of two nuisance functions: either the outcome model or the propensity score model.

The canonical doubly robust estimator for the ATE takes the form:

$$\hat{\tau}_{DR} = \frac{1}{n}\sum_{i=1}^n \left[\frac{T_i Y_i}{\hat{e}(X_i)} - \frac{(1-T_i)Y_i}{1-\hat{e}(X_i)} + \left(\frac{T_i}{\hat{e}(X_i)} - \frac{1-T_i}{1-\hat{e}(X_i)}\right)\hat{m}(X_i)\right]$$

where $\hat{e}(x)$ is an estimated propensity score and $\hat{m}(x)$ is an estimated outcome function. This estimator remains consistent if either $\hat{e}(x) \to e(x)$ or $\hat{m}(x) \to m(x)$, where $e(x) = P(T=1|X=x)$ and $m(x) = \mathbb{E}[Y|X=x,T=0]$.

Recent work has extended doubly robust methods to handle machine learning estimators through cross-fitting procedures that separate the roles of nuisance parameter estimation and final inference [Chernozhukov et al., 2018]. These developments have enabled the use of flexible, data-adaptive methods while preserving the theoretical guarantees of doubly robust estimation.

### 2.3 Conformal Prediction

Conformal prediction, introduced by Vovk et al. [2005], provides a distribution-free framework for constructing prediction intervals with finite-sample coverage guarantees. The method is based on the principle of exchangeability: if observations are exchangeable, then prediction intervals constructed using conformal methods will contain the true outcome with probability at least $1-\alpha$ for any pre-specified level $\alpha$.

The basic conformal prediction algorithm proceeds as follows: given a fitted model $\hat{f}$ and a new point $x_{n+1}$, compute conformity scores for all training points, typically as $R_i = |Y_i - \hat{f}(X_i)|$. The prediction interval is then constructed as $[\hat{f}(x_{n+1}) \pm q]$, where $q$ is the $(1-\alpha)$-quantile of the conformity scores.

Recent advances have extended conformal prediction to handle various challenges including covariate shift [Tibshirani et al., 2019], conditional coverage [Romano et al., 2019], and high-dimensional settings [Lei et al., 2018]. However, the application of conformal methods to causal inference has received limited attention, primarily due to the violation of exchangeability assumptions when treatment assignment depends on covariates.

### 2.4 Uncertainty Quantification in Causal Inference

The intersection of uncertainty quantification and causal inference presents unique challenges that distinguish it from standard prediction problems. In causal settings, the fundamental issue is that we never observe both potential outcomes for any individual, making traditional validation approaches impossible.

Several recent works have begun to address this challenge. Lei & Ding [2021] developed distribution-free prediction intervals for treatment effects in randomized experiments, while Chernozhukov et al. [2021] proposed methods for uncertainty quantification in high-dimensional causal inference. However, these approaches either require randomized treatment assignment or rely on specific modeling assumptions that may not hold in practice.

The present work builds on these foundations by developing a general framework that combines the robustness of doubly robust estimation with the finite-sample guarantees of conformal prediction, providing a principled approach to uncertainty quantification for ITEs across a wide range of settings.

## 3. Problem Setup and Notation

### 3.1 Causal Framework

We adopt the potential outcomes framework [Rubin, 1974] to formalize the causal inference problem. For each unit $i$ in a population, let $Y_i(1)$ and $Y_i(0)$ denote the potential outcomes under treatment and control, respectively. The observed treatment assignment is denoted by $T_i \in \{0, 1\}$, and the observed outcome is $Y_i = T_i Y_i(1) + (1-T_i) Y_i(0)$. Each unit is also characterized by a vector of pre-treatment covariates $X_i \in \mathcal{X} \subseteq \mathbb{R}^p$.

The individual treatment effect for unit $i$ is defined as $\tau_i = Y_i(1) - Y_i(0)$. Since only one potential outcome is observed for each unit, $\tau_i$ cannot be directly computed. Instead, we focus on constructing prediction intervals for $\tau_i$ that account for this fundamental uncertainty.

We make the standard assumptions of causal inference:

**Assumption 1 (SUTVA):** The Stable Unit Treatment Value Assumption holds, meaning there are no interference effects between units and no hidden versions of treatments.

**Assumption 2 (Unconfoundedness):** Treatment assignment is unconfounded given observed covariates: $(Y(1), Y(0)) \perp T | X$.

**Assumption 3 (Overlap):** There exists $\epsilon > 0$ such that $\epsilon < e(x) < 1-\epsilon$ for all $x \in \mathcal{X}$, where $e(x) = P(T=1|X=x)$ is the propensity score.

### 3.2 Inferential Targets

We consider two primary inferential scenarios:

**Within-Study Inference:** Given a study sample $\{(X_i, T_i, Y_i)\}_{i=1}^n$, construct prediction intervals for the unobserved counterfactual outcomes. Specifically, for a treated unit $i$ with $T_i = 1$, we observe $Y_i(1)$ and seek an interval for $Y_i(0)$. For a control unit with $T_i = 0$, we observe $Y_i(0)$ and seek an interval for $Y_i(1)$.

**Out-of-Study Inference:** For a new unit with covariates $X_{new}$ from a potentially different population, construct prediction intervals for both $Y_{new}(1)$ and $Y_{new}(0)$, and consequently for $\tau_{new} = Y_{new}(1) - Y_{new}(0)$.

### 3.3 Coverage Requirements

For any prediction interval construction method, we require finite-sample marginal coverage guarantees:

**Definition 1 (Marginal Coverage):** A prediction interval $C_{\alpha}(X)$ has marginal coverage level $1-\alpha$ if $P(Y \in C_{\alpha}(X)) \geq 1-\alpha$ for any joint distribution of $(X,Y)$.

In the causal setting, this translates to requiring that prediction intervals for counterfactual outcomes satisfy:

$$P(Y_i(1-T_i) \in C_{\alpha}(X_i, T_i)) \geq 1-\alpha$$

for within-study inference, and

$$P(Y_{new}(t) \in C_{\alpha}(X_{new}, t)) \geq 1-\alpha$$

for $t \in \{0,1\}$ in out-of-study inference.

### 3.4 Challenges and Objectives

The key challenges in achieving these coverage guarantees are:

1. **Missing Counterfactuals:** Standard conformal prediction assumes access to true outcomes for validation, which is impossible for counterfactual inference.

2. **Selection Bias:** Treatment assignment typically depends on covariates, violating the exchangeability assumption underlying conformal prediction.

3. **Model Misspecification:** Reliance on either outcome or propensity score models introduces potential bias that must be accounted for in uncertainty quantification.

4. **Covariate Shift:** The target population may differ from the study population in covariate distribution.

Our objective is to develop a method that addresses all these challenges while providing computationally efficient algorithms for practical implementation.

## 4. Doubly Robust Conformal Prediction

### 4.1 Core Methodology

The central insight of our approach is to construct separate conformal predictors for treated and control outcomes, then combine them using doubly robust corrections that account for selection bias. The method proceeds in three stages: cross-fitting for nuisance parameter estimation, conformity score computation with bias correction, and interval construction.

#### Stage 1: Cross-Fitting for Nuisance Parameters

To avoid overfitting bias when using flexible machine learning methods, we employ a cross-fitting procedure. Partition the sample into $K$ folds $\{I_k\}_{k=1}^K$ of approximately equal size. For each fold $k$:

1. **Outcome Modeling:** Using data from folds $\{I_j : j \neq k\}$, estimate outcome functions:
   - $\hat{\mu}_1^{(-k)}(x) = \mathbb{E}[Y|X=x, T=1]$
   - $\hat{\mu}_0^{(-k)}(x) = \mathbb{E}[Y|X=x, T=0]$

2. **Propensity Score Estimation:** Using the same training folds, estimate the propensity score:
   - $\hat{e}^{(-k)}(x) = P(T=1|X=x)$

The superscript $(-k)$ indicates that fold $k$ was excluded from training.

#### Stage 2: Doubly Robust Conformity Scores

For each unit $i$ in fold $I_k$, we construct doubly robust conformity scores that measure how well the estimated model predicts the observed outcome while correcting for selection bias.

**Treated Units ($T_i = 1$):** The conformity score for predicting $Y_i(0)$ is:

$$R_i^{(0)} = \left|Y_i(0)^{DR} - \hat{\mu}_0^{(-k)}(X_i)\right|$$

where the doubly robust "pseudo-outcome" is:

$$Y_i(0)^{DR} = \hat{\mu}_0^{(-k)}(X_i) + \frac{1-T_i}{1-\hat{e}^{(-k)}(X_i)}(Y_i - \hat{\mu}_0^{(-k)}(X_i))$$

**Control Units ($T_i = 0$):** Similarly, the conformity score for predicting $Y_i(1)$ is:

$$R_i^{(1)} = \left|Y_i(1)^{DR} - \hat{\mu}_1^{(-k)}(X_i)\right|$$

where:

$$Y_i(1)^{DR} = \hat{\mu}_1^{(-k)}(X_i) + \frac{T_i}{\hat{e}^{(-k)}(X_i)}(Y_i - \hat{\mu}_1^{(-k)}(X_i))$$

**Key Insight:** The pseudo-outcomes $Y_i(t)^{DR}$ serve as bias-corrected estimates of the unobserved counterfactuals. When either the outcome model or propensity score is correctly specified, these pseudo-outcomes are unbiased estimators of the true counterfactuals.

#### Stage 3: Prediction Interval Construction

**Within-Study Intervals:** For a unit $i$ with treatment status $T_i$, the prediction interval for the counterfactual outcome $Y_i(1-T_i)$ is:

$$C_{\alpha}(X_i, T_i) = \left[\hat{\mu}_{1-T_i}^{(-k_i)}(X_i) \pm Q_{1-\alpha}^{(1-T_i)}\right]$$

where $Q_{1-\alpha}^{(t)}$ is the $(1-\alpha)$-quantile of the conformity scores $\{R_j^{(t)} : T_j = 1-t\}$ and $k_i$ is the fold containing unit $i$.

**Out-of-Study Intervals:** For a new unit with covariates $X_{new}$, we construct intervals for both potential outcomes:

$$C_{\alpha}^{(t)}(X_{new}) = \left[\bar{\mu}_t(X_{new}) \pm Q_{1-\alpha}^{(t)}\right]$$

where $\bar{\mu}_t(x) = \frac{1}{K}\sum_{k=1}^K \hat{\mu}_t^{(-k)}(x)$ is the ensemble prediction.

### 4.2 Theoretical Analysis

We now establish the coverage properties of our doubly robust conformal prediction intervals.

**Theorem 1 (Coverage for Randomized Experiments):** In randomized experiments where $T_i \stackrel{iid}{\sim} \text{Bernoulli}(p)$ independently of covariates, the prediction intervals satisfy exact marginal coverage:

$$P(Y_i(1-T_i) \in C_{\alpha}(X_i, T_i)) = 1-\alpha$$

*Proof Sketch:* In randomized experiments, the pseudo-outcomes $Y_i(t)^{DR}$ reduce to the observed outcomes for units in the opposite treatment group. The exchangeability of treatment assignments ensures that the conformity scores are exchangeable, leading to exact coverage by standard conformal prediction theory.

**Theorem 2 (Coverage for Observational Studies):** Under Assumptions 1-3, if either the outcome models $\{\mu_t(x)\}_{t=0,1}$ or the propensity score model $e(x)$ is correctly specified, then:

$$\liminf_{n \to \infty} P(Y_i(1-T_i) \in C_{\alpha}(X_i, T_i)) \geq 1-\alpha$$

*Proof Sketch:* The doubly robust property ensures that the pseudo-outcomes are asymptotically unbiased when either nuisance function is correctly specified. Combined with consistency conditions on the quantile estimation, this yields asymptotic coverage. The finite-sample behavior depends on the convergence rates of the nuisance parameter estimators.

**Theorem 3 (Robustness to Model Misspecification):** When both nuisance functions are misspecified but the bias terms satisfy certain boundedness conditions, the coverage probability degrades gracefully:

$$P(Y_i(1-T_i) \in C_{\alpha}(X_i, T_i)) \geq 1-\alpha - \delta(n)$$

where $\delta(n) \to 0$ as the sample size increases and the misspecification bias decreases.

### 4.3 Algorithm Implementation

**Algorithm 1: Doubly Robust Conformal Prediction for ITEs**

**Input:** Sample $\{(X_i, T_i, Y_i)\}_{i=1}^n$, significance level $\alpha$, number of folds $K$

**Output:** Prediction intervals for counterfactual outcomes

1. **Initialization:** Partition sample into $K$ folds $\{I_k\}_{k=1}^K$

2. **Cross-fitting:**
   ```
   For k = 1 to K:
       Train_data = {(X_i, T_i, Y_i) : i ∉ I_k}
       Fit μ̂₁^(-k)(x) on {(X_i, Y_i) : T_i = 1, i ∉ I_k}
       Fit μ̂₀^(-k)(x) on {(X_i, Y_i) : T_i = 0, i ∉ I_k}
       Fit ê^(-k)(x) on Train_data
   ```

3. **Conformity Score Computation:**
   ```
   R⁽⁰⁾ = [], R⁽¹⁾ = []
   For i = 1 to n:
       k = fold containing unit i
       If T_i = 1:
           Y_i⁽⁰⁾^DR = μ̂₀^(-k)(X_i) + (1-T_i)/(1-ê^(-k)(X_i)) * (Y_i - μ̂₀^(-k)(X_i))
           Append |Y_i⁽⁰⁾^DR - μ̂₀^(-k)(X_i)| to R⁽⁰⁾
       Else:
           Y_i⁽¹⁾^DR = μ̂₁^(-k)(X_i) + T_i/ê^(-k)(X_i) * (Y_i - μ̂₁^(-k)(X_i))
           Append |Y_i⁽¹⁾^DR - μ̂₁^(-k)(X_i)| to R⁽¹⁾
   ```

4. **Quantile Computation:**
   ```
   Q₁₋α⁽⁰⁾ = (1-α)-quantile of R⁽⁰⁾
   Q₁₋α⁽¹⁾ = (1-α)-quantile of R⁽¹⁾
   ```

5. **Interval Construction:**
   ```
   For each unit i:
       k = fold containing unit i
       If T_i = 1:
           Interval for Y_i(0): [μ̂₀^(-k)(X_i) ± Q₁₋α⁽⁰⁾]
       Else:
           Interval for Y_i(1): [μ̂₁^(-k)(X_i) ± Q₁₋α⁽¹⁾]
   ```

**Computational Complexity:** The algorithm has time complexity $O(n \cdot C)$ where $C$ is the cost of fitting the machine learning models. The cross-fitting procedure requires fitting $2K$ outcome models and $K$ propensity score models, making it computationally feasible even for large datasets.

## 5. Extensions and Generalizations

### 5.1 Handling Covariate Shift

In many applications, the target population differs from the study population in covariate distribution. Let $P_{study}(X)$ and $P_{target}(X)$ denote the covariate distributions in the study and target populations, respectively. We assume access to a sample of covariates $\{X_j^{target}\}_{j=1}^m$ from the target population.

**Weighted Conformal Prediction:** We modify our conformity scores using importance weights to account for covariate shift:

$$w_i = \frac{p_{target}(X_i)}{p_{study}(X_i)} \cdot \frac{n}{n + m}$$

where the density ratio can be estimated using methods such as kernel mean matching or discriminative approaches.

The weighted quantiles are then computed as:

$$Q_{1-\alpha,weighted}^{(t)} = \text{weighted } (1-\alpha)\text{-quantile of } \{R_j^{(t)}\}$$

using weights $\{w_j\}$ for the conformity scores.

**Theorem 4 (Coverage under Covariate Shift):** Under appropriate regularity conditions on the density ratio estimation, the weighted conformal intervals maintain asymptotic coverage for the target population:

$$\lim_{n,m \to \infty} P_{target}(Y(t) \in C_{\alpha,weighted}^{(t)}(X)) \geq 1-\alpha$$

### 5.2 Multiple Inferential Targets

Our framework naturally extends to different causal estimands beyond individual treatment effects:

**Average Treatment Effect (ATE):** Construct intervals for $\tau_{ATE} = \mathbb{E}[Y(1) - Y(0)]$ by aggregating individual predictions:

$$C_{\alpha}^{ATE} = \left[\frac{1}{n}\sum_{i=1}^n \hat{\tau}_i \pm t_{1-\alpha/2} \cdot \hat{SE}(\hat{\tau}_{ATE})\right]$$

where $\hat{\tau}_i$ are point estimates and $\hat{SE}(\hat{\tau}_{ATE})$ incorporates both estimation uncertainty and conformal prediction intervals.

**Average Treatment Effect on the Treated (ATT):** Focus on the subpopulation with $T_i = 1$:

$$C_{\alpha}^{ATT} = \left[\frac{1}{n_1}\sum_{i:T_i=1} (\hat{Y}_i(1) - \hat{Y}_i(0)) \pm Q_{1-\alpha}^{ATT}\right]$$

where the quantile is computed using conformity scores from the treated subpopulation.

**Conditional Average Treatment Effects (CATE):** For subgroups defined by covariate values $X \in \mathcal{S}$:

$$C_{\alpha}^{CATE}(\mathcal{S}) = \left[\frac{1}{|\mathcal{S}|}\sum_{i:X_i \in \mathcal{S}} \hat{\tau}_i \pm Q_{1-\alpha}^{\mathcal{S}}\right]$$

### 5.3 Adaptive Conformity Scores

To improve the efficiency of prediction intervals, we can adapt the conformity scores to local covariate information:

**Locally Weighted Scores:** Define conformity scores that give more weight to similar units:

$$R_i^{(t),adaptive} = \left|Y_i(t)^{DR} - \hat{\mu}_t^{(-k)}(X_i)\right| \cdot \sqrt{\hat{\sigma}_t^2(X_i)}$$

where $\hat{\sigma}_t^2(x)$ is an estimate of the conditional variance of the outcome.

**Quantile Regression Approach:** Instead of using absolute residuals, employ quantile regression to directly model the conditional quantiles:

$$\hat{Q}_{\alpha/2}(x,t) = \text{argmin}_q \sum_{i:T_i=1-t} \rho_{\alpha/2}(Y_i(t)^{DR} - q)$$

where $\rho_{\alpha}(u) = u(\alpha - \mathbb{I}(u < 0))$ is the quantile loss function.

## 6. Experimental Design and Expected Results

### 6.1 Simulation Study Design

We design comprehensive simulation studies to evaluate the finite-sample performance of our doubly robust conformal prediction method across various scenarios:

**Data Generating Processes:** We consider multiple DGPs that vary in:
- Dimensionality: $p \in \{5, 10, 20, 50\}$
- Sample size: $n \in \{500, 1000, 2000, 5000\}$
- Treatment assignment mechanism: randomized vs. observational with varying degrees of confounding
- Outcome model complexity: linear, polynomial, and nonlinear interactions
- Propensity score model: logistic, nonlinear, and misspecified forms
- Heterogeneity: constant vs. heterogeneous treatment effects

**Baseline Methods:** We compare against:
- Standard conformal prediction (ignoring treatment assignment)
- Bootstrap-based intervals for causal forests
- Bayesian credible intervals from BART
- Asymptotic intervals from doubly robust estimators
- Oracle intervals (using true propensity scores and outcome models)

**Evaluation Metrics:**
- **Coverage Probability:** Empirical coverage rates across simulation replications
- **Interval Width:** Average width of prediction intervals
- **Conditional Coverage:** Coverage rates within covariate subgroups
- **Robustness:** Performance under model misspecification scenarios

### 6.2 Expected Simulation Results

Based on our theoretical analysis, we expect the following patterns:

**Coverage Performance:**
- Our method should achieve near-nominal coverage (95% for $\alpha = 0.05$) across all scenarios
- Coverage should be exact in randomized experiments and approach nominal levels in observational studies
- The method should maintain coverage even when either the outcome model or propensity score is misspecified
- Baseline methods that ignore treatment assignment should exhibit severe under-coverage

**Efficiency Comparisons:**
- Interval widths should be competitive with oracle methods when models are well-specified
- The doubly robust property should provide substantial improvements over single-model approaches when one model is misspecified
- Adaptive conformity scores should yield narrower intervals in heterogeneous settings

**Computational Performance:**
- Runtime should scale linearly with sample size
- Cross-fitting overhead should be modest compared to single-fold approaches
- Memory requirements should remain manageable for typical dataset sizes

### 6.3 Real Data Applications

We plan to evaluate our method on several real-world datasets:

**Medical Applications:**
- **IHDP Dataset:** Infant Health and Development Program data for evaluating early intervention effects
- **ACIC Competition Data:** Synthetic datasets based on real observational studies
- **Lalonde Dataset:** Classic labor economics dataset for job training program evaluation

**Policy Applications:**
- **National Supported Work Demonstration:** Employment training program evaluation
- **Head Start Impact Study:** Early childhood education program effects

**Expected Real Data Results:**
- Our intervals should provide more reliable uncertainty quantification than existing methods
- Coverage validation using cross-validation techniques should confirm theoretical predictions
- Practitioners should find the intervals informative for decision-making while maintaining appropriate uncertainty

### 6.4 Computational Experiments

**Scalability Analysis:**
- Evaluate performance on datasets with $n$ ranging from $10^3$ to $10^6$ observations
- Compare computational efficiency across different machine learning base learners
- Assess memory usage and parallelization opportunities

**Hyperparameter Sensitivity:**
- Investigate the effect of the number of cross-fitting folds $K$
- Evaluate robustness to choices of base learning algorithms
- Analyze the impact of sample splitting ratios

**Expected Computational Results:**
- The method should scale well to large datasets
- Cross-fitting should provide computational benefits through parallelization
- Hyperparameter choices should have minimal impact on coverage properties

## 7. Discussion and Future Directions

### 7.1 Theoretical Implications

Our work bridges two important areas of statistics—causal inference and conformal prediction—in a principled manner. The theoretical contributions extend beyond the immediate application to ITEs:

**Distribution-Free Causal Inference:** Our framework demonstrates that finite-sample guarantees are achievable in causal settings without strong distributional assumptions. This opens avenues for developing similar guarantees for other causal estimands and more complex treatment regimes.

**Robustness Properties:** The combination of doubly robust estimation with conformal prediction provides a new paradigm for uncertainty quantification that is robust to model misspecification. This approach could be extended to other semi-parametric estimation problems.

**Cross-Fitting Theory:** Our analysis contributes to the growing literature on cross-fitting methods by establishing coverage properties for conformal prediction in this setting. The results have implications for other areas where cross-fitting is employed to avoid overfitting bias.

### 7.2 Methodological Extensions

Several natural extensions of our framework merit investigation:

**Multiple Treatments:** Extending to settings with multiple discrete or continuous treatment levels requires developing appropriate conformity scores and handling the increased complexity of propensity score estimation.

**Time-Varying Treatments:** Dynamic treatment regimes present additional challenges in defining appropriate exchangeability assumptions and constructing valid conformity scores across time periods.

**Interference and Network Effects:** When the SUTVA assumption is violated due to interference between units, the conformal prediction framework requires modification to account for dependence structures.

**High-Dimensional Covariates:** While our current framework handles moderate dimensionality, extending to truly high-dimensional settings (p >> n) requires careful consideration of convergence rates and regularization techniques.

### 7.3 Practical Considerations
