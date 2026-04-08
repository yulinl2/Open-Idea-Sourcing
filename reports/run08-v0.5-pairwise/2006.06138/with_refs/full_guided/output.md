# Reconstruction: full_guided
**Paper:** 2006.06138  
**Condition:** with_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Distribution-Free Prediction Intervals for Individual Treatment Effects Under Covariate Shift

## Abstract

Estimating individual treatment effects is crucial for personalized decision-making, but existing methods provide poor uncertainty quantification. We address two fundamental challenges: constructing valid prediction intervals for conditional average treatment effects (CATE) when treatment assignment mechanisms differ between study and target populations, and handling the inherent missing data problem where only one potential outcome is observed per individual. Building on conformal prediction methodology, we develop a weighted conformal framework that provides distribution-free coverage guarantees for individual treatment effects under covariate shift. Our approach extends conformal prediction to the causal inference setting by carefully handling the asymmetry between treated and control groups, and incorporates likelihood ratio weighting to account for distributional differences between study and target populations. The method requires no parametric assumptions and provides finite-sample coverage guarantees. We establish theoretical properties showing that our intervals achieve the nominal coverage rate regardless of the underlying data generating process or the quality of the CATE estimator used.

## 1. Introduction

Understanding how treatments affect individuals differently is fundamental to personalized medicine, targeted policy interventions, and precision agriculture. While average treatment effects provide valuable population-level insights, they can be misleading when treatment effects exhibit substantial heterogeneity across individuals. For instance, a drug might benefit 70% of patients while causing adverse effects in the remaining 30%, yielding a positive average effect that masks important individual-level variation.

The challenge of estimating conditional average treatment effects (CATE) - the expected treatment effect for individuals with specific characteristics - has received considerable attention in the causal inference literature. However, most existing methods focus on point estimation and provide poor uncertainty quantification. This limitation is particularly problematic in high-stakes applications where decision-makers need reliable assessments of uncertainty to weigh potential benefits against risks.

Two distinct inference problems arise when constructing prediction intervals for individual treatment effects:
1. **Within-study inference**: Constructing intervals for individuals in the study population, where one potential outcome is observed
2. **Out-of-study inference**: Constructing intervals for new individuals from a potentially different population, where both potential outcomes are missing

The fundamental challenge stems from the missing data problem inherent to causal inference - for any individual, we observe only one potential outcome (either under treatment or control), never both. This creates unique difficulties for uncertainty quantification that do not arise in standard prediction problems.

Additionally, real-world applications often involve covariate shift, where the distribution of individual characteristics differs between the study population and the target population of interest. For example, clinical trial participants may systematically differ from the broader patient population who will ultimately receive the treatment.

This work makes the following contributions:
• We develop a weighted conformal prediction framework for individual treatment effects that handles covariate shift between study and target populations
• We establish finite-sample coverage guarantees that hold regardless of the quality of the underlying CATE estimator or the data generating process
• We provide separate procedures for within-study and out-of-study inference, each with appropriate theoretical justifications
• We extend the weighted exchangeability framework of Tibshirani et al. [2020] to the causal inference setting with careful treatment of the asymmetry between treatment groups

## 2. Related Work

**Causal Inference and Treatment Effect Heterogeneity.** The potential outcomes framework [Rubin, 1974; Holland, 1986] provides the foundation for defining individual treatment effects. Recent work has developed sophisticated methods for estimating CATE using machine learning techniques, including causal forests [Wager and Athey, 2018], targeted maximum likelihood estimation [van der Laan and Rose, 2011], and double machine learning [Chernozhukov et al., 2018]. However, these methods typically provide only point estimates or rely on asymptotic normality assumptions that may be violated in finite samples.

**Uncertainty Quantification in Causal Inference.** Most approaches to uncertainty quantification for treatment effects rely on parametric assumptions or asymptotic approximations. Bootstrap methods have been proposed but lack theoretical guarantees in the causal setting due to the fundamental missing data problem. Some recent work has explored Bayesian approaches [Hill, 2011; Hahn et al., 2020], but these require strong prior assumptions and may not provide frequentist coverage guarantees.

**Conformal Prediction.** Conformal prediction, pioneered by Vovk et al. [2005], provides a distribution-free framework for constructing prediction intervals with finite-sample coverage guarantees. The key insight is that under exchangeability, the conformity score of a new observation has a known distribution relative to the scores of training observations. Recent work has extended conformal prediction to handle covariate shift [Tibshirani et al., 2020], which is directly relevant to our setting.

**Conformal Prediction Under Covariate Shift.** Tibshirani et al. [2020] show that when the likelihood ratio between test and training covariate distributions is known, a weighted version of conformal prediction can provide valid coverage. Their approach replaces the empirical distribution of conformity scores with a weighted distribution where weights are proportional to likelihood ratios. This framework provides the foundation for our extension to causal inference problems.

**Gap Identification.** While conformal prediction has been successfully applied to standard prediction problems and extended to handle covariate shift, its application to causal inference remains largely unexplored. The key challenges that our work addresses are: (1) handling the asymmetric nature of treatment assignment in the conformal framework, (2) properly accounting for the missing data structure inherent to causal inference, and (3) providing valid inference for both within-study and out-of-study populations under covariate shift.

## 3. Problem Formulation

**Notation and Setup.** Let $\mathcal{X} \subseteq \mathbb{R}^d$ denote the covariate space and $\mathcal{Y} \subseteq \mathbb{R}$ the outcome space. For an individual with covariates $X = x$, let $Y(1)$ and $Y(0)$ denote the potential outcomes under treatment and control, respectively. The individual treatment effect is $\tau(x) = Y(1) - Y(0)$, and the conditional average treatment effect is $\text{CATE}(x) = \mathbb{E}[\tau(x) | X = x] = \mathbb{E}[Y(1) - Y(0) | X = x]$.

We observe a study dataset $\mathcal{D} = \{(X_i, T_i, Y_i)\}_{i=1}^n$ where $X_i \in \mathcal{X}$ are covariates, $T_i \in \{0,1\}$ is the treatment assignment, and $Y_i = T_i Y_i(1) + (1-T_i) Y_i(0)$ is the observed outcome. Under the stable unit treatment value assumption (SUTVA), we have $Y_i = Y_i(T_i)$.

**Study Population Model.** The study data are generated according to:
- $(X_i, Y_i(0), Y_i(1)) \stackrel{\text{i.i.d.}}{\sim} P$ for $i = 1, \ldots, n$
- $T_i | X_i \sim \text{Bernoulli}(e(X_i))$ where $e(x) = \mathbb{P}(T = 1 | X = x)$ is the propensity score
- Treatment assignment is independent across individuals: $T_i \perp T_j | X_i, X_j$ for $i \neq j$

**Target Population and Covariate Shift.** We consider inference for individuals from a target population that may differ from the study population. Specifically:
- Study population: $X \sim P_X$
- Target population: $X \sim \tilde{P}_X$

We assume the conditional outcome distributions remain unchanged: $Y(t) | X \sim P_{Y(t)|X}$ for $t \in \{0,1\}$ in both populations, but the covariate distributions may differ. When $P_X \neq \tilde{P}_X$, we have covariate shift.

**Inference Problems.** We consider two distinct inference problems:

1. **Within-study inference**: For an individual $(X_{n+1}, T_{n+1}, Y_{n+1})$ from the study population, construct a prediction interval for $\tau_{n+1} = Y_{n+1}(1) - Y_{n+1}(0)$ given observed data $(X_{n+1}, T_{n+1}, Y_{n+1})$.

2. **Out-of-study inference**: For a new individual with covariates $X_{\text{new}} \sim \tilde{P}_X$ from the target population, construct a prediction interval for $\tau_{\text{new}} = Y_{\text{new}}(1) - Y_{\text{new}}(0)$ given only $X_{\text{new}}$.

**Assumptions.** We make the following standard assumptions:
- **Unconfoundedness**: $Y(0), Y(1) \perp T | X$
- **Overlap**: $0 < e(x) < 1$ for all $x \in \mathcal{X}$
- **SUTVA**: No interference between units and well-defined treatments

For the covariate shift setting, we additionally assume:
- **Absolute continuity**: $\tilde{P}_X \ll P_X$ with known likelihood ratio $w(x) = \frac{d\tilde{P}_X}{dP_X}(x)$

**Objective.** Our goal is to construct prediction intervals $\hat{C}_n(x)$ such that for a nominal coverage level $1-\alpha$:
$$\mathbb{P}(\tau \in \hat{C}_n(X)) \geq 1-\alpha$$
where the probability is taken over the appropriate population (study or target) and the randomness in the training data.

## 4. Methodology

Our approach builds on the weighted conformal prediction framework of Tibshirani et al. [2020] but requires substantial modifications to handle the causal inference setting. The key challenges are: (1) the individual treatment effect $\tau_i$ is never directly observed, (2) the treatment assignment creates asymmetry in the data structure, and (3) we must carefully handle the missing data pattern inherent to causal inference.

**Base CATE Estimator.** We assume access to a base algorithm that produces an estimator $\hat{\tau}(\cdot)$ of the CATE function. This could be any method such as causal forests, T-learner, S-learner, or doubly robust methods. Our framework provides valid coverage regardless of the quality of $\hat{\tau}(\cdot)$.

**Conformity Scores for Treatment Effects.** The central challenge is defining appropriate conformity scores when the quantity of interest (individual treatment effect) is never observed. We propose the following approach:

For an individual with covariates $x$ and hypothetical treatment effect $\tau$, we define the conformity score as:
$$S((x, \tau), \mathcal{D}) = |\tau - \hat{\tau}(x)|$$

where $\hat{\tau}(x)$ is computed using the dataset $\mathcal{D}$. This score measures how well a hypothetical treatment effect $\tau$ conforms to what we would predict based on the individual's covariates and the training data.

**Handling Observed Data.** For individuals in the training set, we cannot directly compute their true treatment effects. Instead, we use imputed treatment effects based on the observed outcomes and estimated counterfactuals:

For individual $i$ with observed $(X_i, T_i, Y_i)$:
$$\tilde{\tau}_i = \begin{cases}
Y_i - \hat{\mu}_0(X_i) & \text{if } T_i = 1 \\
\hat{\mu}_1(X_i) - Y_i & \text{if } T_i = 0
\end{cases}$$

where $\hat{\mu}_t(x) = \mathbb{E}[Y | X = x, T = t]$ are estimated outcome regression functions.

**Within-Study Conformal Prediction.** For within-study inference, we adapt the standard conformal prediction procedure. Given a new individual $(X_{n+1}, T_{n+1}, Y_{n+1})$ from the study population:

1. Compute imputed treatment effects $\tilde{\tau}_i$ for $i = 1, \ldots, n$
2. For each candidate value $\tau$, compute conformity scores:
   - $V_i^{(\tau)} = |\tilde{\tau}_i - \hat{\tau}_{-i}(X_i)|$ for $i = 1, \ldots, n$
   - $V_{n+1}^{(\tau)} = |\tau - \hat{\tau}(X_{n+1})|$

where $\hat{\tau}_{-i}(\cdot)$ is the CATE estimator trained on data excluding individual $i$.

3. The prediction interval is:
$$\hat{C}_n(X_{n+1}) = \left\{\tau : V_{n+1}^{(\tau)} \leq \text{Quantile}\left(1-\alpha; \{V_i^{(\tau)}\}_{i=1}^n \cup \{\infty\}\right)\right\}$$

**Weighted Conformal for Covariate Shift.** For out-of-study inference under covariate shift, we extend the weighted conformal framework. Given a new individual with covariates $X_{\text{new}} \sim \tilde{P}_X$:

1. Compute weights $w_i = w(X_i)$ for $i = 1, \ldots, n$ and $w_{\text{new}} = w(X_{\text{new}})$
2. Define normalized weights:
$$p_i^w(X_{\text{new}}) = \frac{w_i}{\sum_{j=1}^n w_j + w_{\text{new}}}, \quad p_{n+1}^w(X_{\text{new}}) = \frac{w_{\text{new}}}{\sum_{j=1}^n w_j + w_{\text{new}}}$$

3. For each candidate $\tau$, the weighted prediction interval is:
$$\hat{C}_n(X_{\text{new}}) = \left\{\tau : V_{n+1}^{(\tau)} \leq \text{Quantile}\left(1-\alpha; \sum_{i=1}^n p_i^w \delta_{V_i^{(\tau)}} + p_{n+1}^w \delta_\infty\right)\right\}$$

**Split Conformal Variant.** To improve computational efficiency, we also develop a split conformal variant:

1. Split the data into training set $\mathcal{D}_{\text{train}}$ and calibration set $\mathcal{D}_{\text{cal}}$
2. Train CATE estimator $\hat{\tau}(\cdot)$ on $\mathcal{D}_{\text{train}}$
3. Compute imputed treatment effects $\tilde{\tau}_i$ for calibration set
4. For new individual, the interval becomes:
$$\hat{C}_n(x) = \hat{\tau}(x) \pm \text{Quantile}(1-\alpha; \{|\tilde{\tau}_i - \hat{\tau}(X_i)|\}_{i \in \mathcal{D}_{\text{cal}}} \cup \{\infty\})$$

This approach is computationally more efficient as it avoids refitting the CATE estimator for each candidate treatment effect value.

## 5. Theoretical Analysis

We now establish the theoretical properties of our proposed methods. The key insight is that despite the missing data structure of causal inference, we can still achieve valid coverage by carefully constructing exchangeable sequences of conformity scores.

**Theorem 1 (Coverage for Within-Study Inference).** Under the assumptions of unconfoundedness and overlap, the within-study conformal prediction interval satisfies:
$$\mathbb{P}(\tau_{n+1} \in \hat{C}_n(X_{n+1})) \geq 1 - \alpha$$

Furthermore, if ties occur with probability zero, this probability is upper bounded by $1 - \alpha + \frac{1}{n+1}$.

*Proof Sketch:* The key insight is that the imputed treatment effects $\tilde{\tau}_i$, while not equal to the true treatment effects, maintain the exchangeability property required for conformal prediction. Under unconfoundedness, the conditional distribution of $\tilde{\tau}_i$ given $X_i$ has the same relationship to the true CATE as the conditional distribution of $\tau_{n+1}$ given $X_{n+1}$. This ensures that the conformity scores $V_i^{(\tau)}$ are exchangeable, allowing us to apply the standard conformal prediction result.

**Theorem 2 (Coverage Under Covariate Shift).** Assume the covariate shift model where $X_{\text{new}} \sim \tilde{P}_X$ and study data have $X_i \sim P_X$, with known likelihood ratio $w(x) = \frac{d\tilde{P}_X}{dP_X}(x)$. Then the weighted conformal prediction interval satisfies:
$$\mathbb{P}(\tau_{\text{new}} \in \hat{C}_n(X_{\text{new}})) \geq 1 - \alpha$$

*Proof Sketch:* This result follows by extending Theorem 2 of Tibshirani et al. [2020] to the causal inference setting. The weighted exchangeability property is preserved under the likelihood ratio weighting, ensuring that the weighted quantile provides valid coverage for the target population.

**Corollary 1 (Split Conformal Coverage).** Under the same assumptions as Theorems 1 and 2, the split conformal variants provide the same coverage guarantees, conditional on the training set used to fit $\hat{\tau}(\cdot)$.

**Robustness Properties.** A key strength of our approach is its robustness to model misspecification:

**Theorem 3 (Model-Free Coverage).** The coverage guarantees in Theorems 1 and 2 hold regardless of:
1. The choice of base CATE estimator $\hat{\tau}(\cdot)$
2. The quality of outcome regression estimates $\hat{\mu}_0(\cdot), \hat{\mu}_1(\cdot)$
3. The correctness of any parametric assumptions about the data generating process

This robustness stems from the distribution-free nature of conformal prediction - the coverage guarantee depends only on the exchangeability of conformity scores, not on the correctness of any modeling assumptions.

**Finite-Sample Validity.** Unlike asymptotic approaches that rely on normality assumptions, our method provides exact finite-sample coverage guarantees. This is particularly valuable in applications with limited sample sizes where asymptotic approximations may be poor.

**Optimality Considerations.** While our intervals achieve the desired coverage, they may not be optimal in terms of length. The efficiency of the intervals depends on the quality of the base CATE estimator - better estimators will generally produce shorter intervals while maintaining valid coverage.

## 6. Experimental Design

We would evaluate our methodology through comprehensive simulation studies and real-data applications designed to assess both coverage properties and practical performance.

**Simulation Study Design.** We would construct synthetic datasets with known ground truth to rigorously evaluate coverage and efficiency:

*Data Generating Process:* Generate covariates $X \sim \mathcal{N}(0, I_d)$ with varying dimensions $d \in \{5, 10, 20\}$. Define heterogeneous treatment effects:
$$\tau(x) = \beta_0 + \beta_1^T x + \beta_2 \cdot \mathbf{1}(x_1 > 0) \cdot x_2 + \epsilon$$
where $\epsilon \sim \mathcal{N}(0, \sigma_\tau^2)$ represents irreducible heterogeneity.

*Outcome Models:* Use nonlinear outcome functions with varying complexity:
- Linear: $\mu_t(x) = \alpha_t + \gamma_t^T x$
- Nonlinear: $\mu_t(x) = \alpha_t + \gamma_t^T x + \delta_t \sin(\|x\|_2)$
- Complex: Neural network-based outcome functions

*Covariate Shift Scenarios:*
1. No shift: $\tilde{P}_X = P_X$
2. Location shift: $\tilde{P}_X = P_X(\cdot - \mu)$ for various $\mu$
3. Exponential tilting: $d\tilde{P}_X/dP_X \propto \exp(\beta^T x)$
4. Selection bias: Target population excludes certain covariate regions

*Evaluation Metrics:*
- **Coverage**: Empirical coverage rates across different subgroups
- **Length**: Average and median interval lengths
- **Conditional Coverage**: Coverage rates conditional on covariate values
- **Robustness**: Performance under model misspecification

**Baseline Comparisons.** We would compare against several alternatives:
- Bootstrap-based intervals from causal forests
- Bayesian credible intervals from BART
- Asymptotic normal intervals from doubly robust estimators
- Oracle intervals (using true CATE function)

**Real Data Applications.** We would demonstrate practical utility using established causal inference datasets:

*Medical Applications:*
- **ACTG 175 HIV Dataset**: Evaluate treatment effect heterogeneity for HIV therapies, with covariate shift representing different patient populations
- **IHDP Dataset**: Intensive care for low birth weight infants, commonly used in causal inference benchmarks

*Policy Evaluation:*
- **LaLonde Job Training Dataset**: Employment training program effects with demographic covariate shifts
- **NSW Experimental Data**: Comparison with observational CPS controls

*Experimental Protocol:*
1. Split each dataset into training, calibration, and test sets
2. Artificially induce covariate shift in test set through resampling
3. Apply all methods and evaluate coverage/efficiency
4. Assess performance across different subgroups and shift magnitudes

**Computational Efficiency Study.** We would evaluate scalability:
- Runtime comparison between full and split conformal variants
- Memory usage for different dataset sizes
- Parallelization opportunities for interval construction

**Sensitivity Analysis.** Key sensitivity analyses would include:
- Robustness to propensity score misspecification
- Performance under violations of overlap assumption
- Impact of likelihood ratio estimation errors
- Behavior with different base CATE estimators

**Expected Outcomes.** We anticipate that our method will:
1. Achieve nominal coverage rates across all scenarios
2. Provide shorter intervals when base estimators are accurate
3. Maintain robustness even with poor base estimators
4. Show particular advantages in covariate shift settings where standard methods fail
5. Scale well to moderate-dimensional problems

## 7. Discussion

**Strengths and Advantages.** Our approach offers several key advantages over existing methods for uncertainty quantification in causal inference:

*Distribution-Free Guarantees:* Unlike methods that rely on asymptotic normality or parametric assumptions, our approach provides exact finite-sample coverage guarantees regardless of the underlying data generating process. This is particularly valuable in applications with limited sample sizes or complex, unknown data distributions.

*Robustness to Model Misspecification:* The coverage guarantees hold regardless of the quality of the base CATE estimator or outcome regression models. This robustness is crucial in practice where model specification is challenging and misspecification is common.

*Handling Covariate Shift:* Our weighted extension naturally handles distributional differences between study and target populations, a common challenge in real-world applications where study participants may not be representative of the broader population of interest.

*Computational Flexibility:* The split conformal variant provides computational efficiency while maintaining theoretical guarantees, making the approach scalable to larger datasets and more complex base estimators.

**Limitations and Challenges.** Several limitations merit discussion:

*Interval Efficiency:* While our intervals achieve valid coverage, they may not be optimal in terms of length. The efficiency depends heavily on the quality of the base CATE estimator, and poor estimators can lead to overly conservative intervals.

*Likelihood Ratio Estimation:* The covariate shift extension requires knowledge or accurate estimation of the likelihood ratio $w(x) = d\tilde{P}_X/dP_X(x)$. In practice, this ratio must be estimated from data, introducing additional uncertainty that our current analysis does not fully address.

*Computational Complexity:* For the full conformal procedure, constructing intervals requires evaluating many candidate treatment effect values, which can be computationally intensive for complex base estimators. The split variant addresses this but may produce longer intervals.

*High-Dimensional Challenges:* While our method handles moderate-dimensional covariates, performance in very high-dimensional settings remains to be established. The curse of dimensionality may affect both the base CATE estimator and the likelihood ratio estimation.

**Connections to Broader Impact.** This work contributes to the growing need for reliable uncertainty quantification in automated decision-making systems. As machine learning methods are increasingly deployed in high-stakes applications like healthcare and policy, providing valid measures of uncertainty becomes crucial for responsible AI.

*Healthcare Applications:* In precision medicine, our method could help clinicians understand not just whether a treatment is likely to help a patient, but also the range of possible effects. This uncertainty information is crucial for shared decision-making and risk assessment.

*Policy Evaluation:* For social programs and interventions, understanding the distribution of individual-level effects can inform targeting strategies and help policymakers anticipate heterogeneous impacts across different populations.

*Algorithmic Fairness:* By providing individual-level uncertainty estimates, our method could help identify subgroups where treatment effect predictions are particularly uncertain, potentially revealing hidden biases or gaps in representation.

**Future Directions.** Several extensions could enhance the practical utility of our approach:

*Adaptive Inference:* Developing methods that can adaptively choose between different base estimators or combine multiple estimators to improve interval efficiency while maintaining coverage guarantees.

*Sequential Learning:* Extending the framework to settings where data arrive sequentially and treatment decisions must be made online, incorporating both exploration and exploitation considerations.

*Multiple Treatments:* Generalizing to settings with multiple treatment options, requiring careful handling of the increased complexity in the missing data structure.

*Causal Discovery:* Combining our uncertainty quantification approach with causal structure learning to provide robust inference even when the causal graph is uncertain.

## 8. Conclusion

We have developed a distribution-free framework for constructing prediction intervals for individual treatment effects that handles covariate shift between study and target populations. Our approach extends conformal prediction methodology to the causal inference setting by carefully addressing the missing data structure inherent to treatment effect estimation.

The key contributions of this work include: (1) a novel application of weighted conformal prediction to causal inference that provides finite-sample coverage guarantees, (2) separate procedures for within-study and out-of-study inference with appropriate theoretical justifications, (3) robustness to model misspecification and distributional assumptions, and (4) computational efficiency through split conformal variants.

Our theoretical analysis establishes that the proposed intervals achieve the nominal coverage rate regardless of the quality of the underlying CATE estimator or the complexity of the data generating process. This model-free property is particularly valuable in practice where treatment effect heterogeneity is complex and difficult to model accurately.

The work opens several directions for future research. First, developing more efficient interval construction procedures that can achieve shorter intervals while maintaining valid coverage. Second, extending the framework to handle estimated likelihood ratios with appropriate uncertainty quantification. Third, investigating performance in high-dimensional settings and developing dimension reduction strategies when needed.

From a broader perspective, this work contributes to the critical need for reliable uncertainty quantification in causal inference applications. As personalized treatment strategies become increasingly important across domains from medicine to education to social policy, providing valid measures of uncertainty for individual-level predictions becomes essential for responsible decision-making.

The intersection of causal inference and conformal prediction represents a promising research direction that combines the robustness of distribution-free methods with the practical importance of causal effect estimation. Our framework provides a solid foundation for this intersection while highlighting important open questions for future investigation.

## References

[Chernozhukov et al., 2018] V. Chernozhukov, D. Chetverikov, M. Demirer, E. Duflo, C. Hansen, W. Newey, and J. Robins. Double/debiased machine learning for treatment and structural parameters. The Econometrics Journal, 21(1):C1-C68, 2018.

[Hahn et al., 2020] P. R. Hahn, J. S. Murray, and C. M. Carvalho. Bayesian regression tree models for causal inference: regularization, confounding, and heterogeneous effects. Bayesian Analysis, 15(3):965-1056, 2020.

[Hill, 2011] J. L. Hill. Bayesian nonparametric modeling for causal inference. Journal of Computational and Graphical Statistics, 20(1):217-240, 2011.

[Holland, 1986] P. W. Holland. Statistics and causal inference. Journal of the American Statistical Association, 81(396):945-960, 1986.

[Lei et al., 2015] J. Lei, M. G'Sell, A. Rinaldo, R. J. Tibshirani, and L. Wasserman. Distribution-free predictive inference for regression. Journal of the American Statistical Association, 113(523):1094-1111, 2015.

[Lei et al., 2018] J. Lei, M. G'Sell, A. Rinaldo, R. J. Tibshirani, and L. Wasserman. Distribution-free predictive inference for regression. Journal of the American Statistical Association, 113(523):1094-1111, 2018.

[Lei and Wasserman, 2014] J. Lei and L. Wasserman. Distribution-free prediction bands for non-parametric regression. Journal of the Royal Statistical Society: Series B, 76(1):71-96, 2014.

[Papadopoulos et al., 2002] H. Papadopoulos, K. Proedrou, V. Vovk, and A. Gammerman. Inductive confidence machines for regression. In European Conference on Machine Learning, pages 345-356, 2002.

[Rubin, 1974] D. B. Rubin. Estimating causal effects of treatments in randomized and nonrandomized studies. Journal of Educational Psychology, 66(5):688-701, 1974.

[Tibshirani et al., 2020] R. J. Tibshirani, R. F. Barber, E. J. Candes, and A. Ramdas. Conformal prediction under covariate shift. In Advances in Neural Information Processing Systems, volume 33, pages 2530-2540, 2020.

[van der Laan and Rose, 2011] M. J. van der Laan and S. Rose. Targeted Learning: Causal Inference for Observational and Experimental Data. Springer, 2011.

[Vovk et al., 2005] V. Vovk, A. Gammerman, and G. Shafer. Algorithmic Learning in a Random World. Springer, 2005.

[Wager and Athey, 2018] S. Wager and S. Athey. Estimation and inference of heterogeneous treatment effects using random forests. Journal of the American Statistical Association, 113(523):1228-1242, 2018.
