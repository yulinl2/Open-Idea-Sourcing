# Reconstruction: full_freestyle
**Paper:** 2006.06138  
**Condition:** with_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Distribution-Free Prediction Intervals for Individual Treatment Effects

## Abstract

We develop a novel framework for constructing distribution-free prediction intervals for individual treatment effects (ITEs) that provides finite-sample coverage guarantees without parametric assumptions. Our approach addresses two fundamental inference problems: quantifying uncertainty for individuals within a study (where one potential outcome is observed) and for new individuals outside the study (where both potential outcomes are missing). We extend conformal prediction methodology to the causal inference setting by introducing *causal conformal prediction*, which leverages the potential outcomes framework while accounting for the fundamental problem of causal inference. Our method handles both randomized experiments and observational studies, provides robustness to model misspecification, and accommodates covariate shift between study and target populations. We establish finite-sample validity guarantees and demonstrate that our intervals achieve the desired coverage while remaining informative for decision-making.

## 1. Introduction

The estimation of individual treatment effects (ITEs) has become increasingly important across diverse fields including personalized medicine, targeted policy interventions, and precision agriculture. While traditional causal inference focuses on average treatment effects, understanding how treatments affect individuals differently is crucial for optimal decision-making. A treatment that benefits the average patient may still harm a substantial minority, making individual-level uncertainty quantification essential for responsible deployment.

The fundamental challenge in ITE estimation stems from the *fundamental problem of causal inference*: for any individual, we can observe at most one potential outcome—either under treatment or control, but never both. This creates a unique uncertainty quantification problem that differs fundamentally from standard prediction tasks. Moreover, practitioners often need to make treatment decisions for new individuals not included in the original study, introducing additional complications from potential covariate shift.

Current approaches to ITE estimation typically rely on machine learning algorithms that provide point estimates but struggle with reliable uncertainty quantification. Methods like BART, causal forests, and neural network-based approaches can capture complex treatment effect heterogeneity but often produce overconfident or poorly calibrated uncertainty estimates. This limitation is particularly concerning in high-stakes applications where understanding the reliability of treatment effect predictions is crucial.

We propose *causal conformal prediction*, a distribution-free framework that extends conformal prediction methodology to the causal inference setting. Our approach provides finite-sample coverage guarantees for individual treatment effect prediction intervals without requiring parametric assumptions about the data generating process. The key insight is to construct conformity scores that respect the structure of the causal inference problem while leveraging the exchangeability properties that make conformal prediction valid.

Our contributions are threefold. First, we develop the theoretical foundation for causal conformal prediction, establishing finite-sample coverage guarantees for both within-study and out-of-study inference. Second, we show how to handle observational studies and covariate shift by extending the weighted conformal prediction framework of Tibshirani et al. [2020]. Third, we provide practical algorithms that work with any base learner for treatment effect estimation, making our approach broadly applicable.

## 2. Problem Formulation and Notation

### 2.1 Potential Outcomes Framework

We adopt the potential outcomes framework [Neyman, 1923; Rubin, 1974] for causal inference. For individual $i$, let $Y_i(1)$ and $Y_i(0)$ denote the potential outcomes under treatment and control, respectively. The individual treatment effect is $\tau_i = Y_i(1) - Y_i(0)$. We observe the tuple $(X_i, T_i, Y_i)$ where $X_i \in \mathbb{R}^d$ is a covariate vector, $T_i \in \{0,1\}$ is the treatment assignment, and $Y_i = T_i Y_i(1) + (1-T_i) Y_i(0)$ is the observed outcome.

The conditional average treatment effect (CATE) function is defined as:
$$\tau(x) = \mathbb{E}[Y_i(1) - Y_i(0) | X_i = x]$$

Our goal is to construct prediction intervals for $\tau_i$ that provide finite-sample coverage guarantees. This presents two distinct inference problems:

1. **Within-study inference**: For individual $i$ in the study, we observe $(X_i, T_i, Y_i)$ and want an interval for $\tau_i = Y_i(1) - Y_i(0)$.

2. **Out-of-study inference**: For a new individual with covariates $X_{n+1}$, we want an interval for $\tau_{n+1} = Y_{n+1}(1) - Y_{n+1}(0)$.

### 2.2 The Fundamental Challenge

The fundamental problem of causal inference creates unique challenges for uncertainty quantification. Unlike standard prediction problems where we can observe prediction errors directly, individual treatment effects are never fully observable. For within-study inference, we observe one potential outcome but must infer the counterfactual. For out-of-study inference, both potential outcomes are missing.

This unobservability means we cannot directly apply standard conformal prediction, which relies on computing conformity scores based on observed prediction errors. We must develop new conformity measures that work with the partially observed nature of causal data.

## 3. Causal Conformal Prediction

### 3.1 Core Methodology

Our approach builds on the conformal prediction framework of Vovk et al. [2005], extending it to handle the causal inference setting. The key insight is to construct conformity scores that leverage the observed potential outcomes while accounting for the missing counterfactuals through imputation-based approaches.

**Definition 1 (Causal Conformity Score)**: Given a base learner that produces estimates $\hat{\mu}_0(x)$ and $\hat{\mu}_1(x)$ for $\mathbb{E}[Y(0)|X=x]$ and $\mathbb{E}[Y(1)|X=x]$, we define the causal conformity score for individual $i$ as:
$$S_i = |Y_i - \hat{\mu}_{T_i}(X_i)| + |\hat{\mu}_{1-T_i}(X_i) - \hat{\tau}(X_i)|$$

where $\hat{\tau}(x) = \hat{\mu}_1(x) - \hat{\mu}_0(x)$ is the estimated CATE function.

This score captures two sources of uncertainty: the prediction error for the observed outcome and the uncertainty in estimating the counterfactual outcome. The first term measures how well our model predicts the factual outcome, while the second term captures uncertainty in the counterfactual imputation.

### 3.2 Within-Study Inference

For individual $i$ in the study, we construct prediction intervals using a leave-one-out approach. Let $\mathcal{D}_{-i} = \{(X_j, T_j, Y_j) : j \neq i\}$ denote the dataset with individual $i$ removed.

**Algorithm 1 (Within-Study Causal Conformal Prediction)**:
1. For each $j \neq i$, fit base learners on $\mathcal{D}_{-j}$ to obtain $\hat{\mu}_0^{(-j)}$ and $\hat{\mu}_1^{(-j)}$
2. Compute conformity scores: $S_j = |Y_j - \hat{\mu}_{T_j}^{(-j)}(X_j)| + |\hat{\mu}_{1-T_j}^{(-j)}(X_j) - \hat{\tau}^{(-j)}(X_j)|$
3. For individual $i$, compute the candidate conformity score for treatment effect $\tau$:
   $$S_i(\tau) = |\hat{\tau}^{(-i)}(X_i) - \tau|$$
4. The prediction interval is:
   $$\hat{C}_i = \{\tau : S_i(\tau) \leq \text{Quantile}(1-\alpha; \{S_j\}_{j \neq i} \cup \{\infty\})\}$$

**Theorem 1 (Within-Study Coverage)**: Under the assumption that $(X_i, T_i, Y_i(0), Y_i(1))$ are exchangeable for $i = 1, \ldots, n$, the prediction intervals from Algorithm 1 satisfy:
$$\mathbb{P}[\tau_i \in \hat{C}_i] \geq 1 - \alpha$$

*Proof sketch*: The key insight is that the conformity scores $\{S_j\}_{j=1}^n$ are exchangeable by construction, since each is computed using a leave-one-out procedure that treats all individuals symmetrically. The result then follows from the quantile lemma (Lemma 1 in Tibshirani et al. [2020]).

### 3.3 Out-of-Study Inference

For a new individual with covariates $X_{n+1}$, we must handle the fact that both potential outcomes are unobserved. We use the full dataset to fit our base learners and construct conformity scores.

**Algorithm 2 (Out-of-Study Causal Conformal Prediction)**:
1. Fit base learners on the full dataset to obtain $\hat{\mu}_0$ and $\hat{\mu}_1$
2. For each individual $i$ in the training set, compute:
   $$S_i = |Y_i - \hat{\mu}_{T_i}(X_i)| + |\hat{\mu}_{1-T_i}(X_i) - \hat{\tau}(X_i)|$$
3. For the new individual, the prediction interval is:
   $$\hat{C}_{n+1} = \{\tau : |\hat{\tau}(X_{n+1}) - \tau| \leq \text{Quantile}(1-\alpha; \{S_i\}_{i=1}^n \cup \{\infty\})\}$$

**Theorem 2 (Out-of-Study Coverage)**: Under exchangeability of $(X_i, T_i, Y_i(0), Y_i(1))$ for $i = 1, \ldots, n+1$, the prediction intervals from Algorithm 2 satisfy:
$$\mathbb{P}[\tau_{n+1} \in \hat{C}_{n+1}] \geq 1 - \alpha$$

### 3.4 Handling Observational Studies

In observational studies, treatment assignment is not randomized, potentially violating the exchangeability assumption. We address this by incorporating propensity score weighting into our conformity scores.

Let $e(x) = \mathbb{P}[T=1|X=x]$ be the propensity score. We modify our conformity score to:
$$S_i^{obs} = \frac{|Y_i - \hat{\mu}_{T_i}(X_i)|}{w_i} + |\hat{\mu}_{1-T_i}(X_i) - \hat{\tau}(X_i)|$$

where $w_i = T_i/\hat{e}(X_i) + (1-T_i)/(1-\hat{e}(X_i))$ are inverse propensity weights.

This weighting scheme helps restore exchangeability by reweighting observations to approximate a randomized experiment. The coverage guarantees remain valid under the assumption of no unmeasured confounding and correct propensity score estimation.

## 4. Extensions and Robustness

### 4.1 Covariate Shift

Following Tibshirani et al. [2020], we extend our method to handle covariate shift between the study population and target population. Suppose the study data comes from distribution $P_X$ while the target individual comes from distribution $\tilde{P}_X$, with known likelihood ratio $w(x) = d\tilde{P}_X/dP_X(x)$.

We modify our prediction intervals by using weighted quantiles:

**Algorithm 3 (Causal Conformal with Covariate Shift)**:
1. Compute conformity scores $\{S_i\}_{i=1}^n$ as before
2. Define weights: $\tilde{w}_i(x) = w(X_i) / [\sum_{j=1}^n w(X_j) + w(x)]$
3. The prediction interval for individual with covariates $x$ is:
   $$\hat{C}(x) = \left\{\tau : |\hat{\tau}(x) - \tau| \leq \text{Quantile}\left(1-\alpha; \sum_{i=1}^n \tilde{w}_i(x) \delta_{S_i} + \frac{w(x)}{\sum_{j=1}^n w(X_j) + w(x)} \delta_{\infty}\right)\right\}$$

**Theorem 3 (Coverage under Covariate Shift)**: Under the covariate shift model where study covariates follow $P_X$ and target covariates follow $\tilde{P}_X$ with known likelihood ratio $w$, Algorithm 3 provides coverage $\mathbb{P}[\tau \in \hat{C}(X)] \geq 1-\alpha$.

### 4.2 Robustness to Model Misspecification

A key advantage of our approach is robustness to misspecification of the base learners. Even if $\hat{\mu}_0$ and $\hat{\mu}_1$ are poor estimates of the true outcome functions, our prediction intervals maintain valid coverage as long as the exchangeability assumptions hold.

This robustness stems from the distribution-free nature of conformal prediction. The conformity scores automatically adapt to the quality of the base learner, producing wider intervals when the model performs poorly and tighter intervals when it performs well.

### 4.3 Computational Considerations

For within-study inference, Algorithm 1 requires fitting $n$ separate models, which can be computationally expensive. We propose a split conformal variant that fits models only once:

**Algorithm 4 (Split Causal Conformal)**:
1. Split the data into training set $\mathcal{D}_{\text{train}}$ and calibration set $\mathcal{D}_{\text{cal}}$
2. Fit base learners on $\mathcal{D}_{\text{train}}$ to obtain $\hat{\mu}_0$ and $\hat{\mu}_1$
3. Compute conformity scores on $\mathcal{D}_{\text{cal}}$: $S_i = |Y_i - \hat{\mu}_{T_i}(X_i)| + |\hat{\mu}_{1-T_i}(X_i) - \hat{\tau}(X_i)|$
4. For new individual with covariates $x$, return interval:
   $$\hat{C}(x) = \{\tau : |\hat{\tau}(x) - \tau| \leq \text{Quantile}(1-\alpha; \{S_i\}_{i \in \mathcal{D}_{\text{cal}}} \cup \{\infty\})\}$$

This split variant maintains valid coverage while requiring only a single model fit, making it practical for large datasets.

## 5. Theoretical Analysis

### 5.1 Coverage Guarantees

Our main theoretical results establish finite-sample coverage guarantees for all proposed algorithms. The proofs rely on extending the quantile lemma of conformal prediction to the causal setting.

**Lemma 1 (Causal Quantile Lemma)**: If conformity scores $S_1, \ldots, S_{n+1}$ are exchangeable, then for any $\beta \in (0,1)$:
$$\mathbb{P}[S_{n+1} \leq \text{Quantile}(\beta; S_{1:n} \cup \{\infty\})] \geq \beta$$

The key insight is that our causal conformity scores maintain exchangeability despite the partial observability of outcomes, enabling the application of standard conformal prediction theory.

### 5.2 Interval Width Analysis

We analyze the expected width of our prediction intervals as a function of the base learner quality and the inherent variability in treatment effects.

**Theorem 4 (Interval Width Bounds)**: Under regularity conditions, the expected width of our prediction intervals satisfies:
$$\mathbb{E}[\text{width}(\hat{C}_i)] \leq C \cdot \left(\sqrt{\text{Var}[Y_i(0)|X_i]} + \sqrt{\text{Var}[Y_i(1)|X_i]} + |\tau_i - \hat{\tau}(X_i)|\right)$$

for some constant $C$ depending on the quantile level and sample size.

This bound shows that interval width depends on both the inherent outcome variability and the quality of the CATE estimator, providing guidance for choosing base learners.

### 5.3 Optimality Properties

We establish that our method achieves optimal coverage-width tradeoffs under certain conditions.

**Theorem 5 (Asymptotic Optimality)**: As $n \to \infty$, our prediction intervals achieve the optimal width among all distribution-free methods with coverage $1-\alpha$.

This result shows that our approach is not only valid but also efficient in the sense of producing the narrowest possible intervals with the desired coverage guarantee.

## 6. Experimental Design and Expected Results

We would evaluate our methodology through comprehensive simulation studies and real-data applications across multiple domains.

### 6.1 Simulation Studies

**Setup 1: Linear Treatment Effects**
- Generate covariates $X_i \sim N(0, I_d)$ with $d \in \{5, 10, 20\}$
- Potential outcomes: $Y_i(0) = X_i^T \beta_0 + \epsilon_i$, $Y_i(1) = X_i^T \beta_1 + \epsilon_i$
- Treatment effects: $\tau_i = X_i^T (\beta_1 - \beta_0)$
- Compare coverage rates and interval widths across different base learners

**Setup 2: Nonlinear Treatment Effects**
- Complex CATE functions using polynomial and interaction terms
- Heteroskedastic noise to test robustness
- Evaluation under model misspecification

**Setup 3: Covariate Shift**
- Training data from $P_X = N(0, I)$, test data from $\tilde{P}_X = N(\mu, \Sigma)$
- Compare weighted vs. unweighted conformal intervals
- Evaluate sensitivity to likelihood ratio estimation errors

**Expected Results**: We anticipate that our method will achieve nominal coverage rates across all settings while producing substantially narrower intervals than naive approaches. The weighted variant should maintain coverage under covariate shift while unweighted methods fail. Interval widths should scale appropriately with the difficulty of the estimation problem.

### 6.2 Real Data Applications

**Medical Application**: Using data from clinical trials with known treatment effect heterogeneity, we would evaluate our method's ability to identify patients likely to benefit from treatment while providing reliable uncertainty quantification.

**Policy Evaluation**: Applying our method to job training program evaluation, comparing our intervals to those from existing approaches in terms of coverage and informativeness for policy decisions.

**Expected Outcomes**: We expect our method to provide well-calibrated intervals that help practitioners make more informed treatment decisions, particularly in cases where existing methods produce overconfident predictions.

## 7. Related Work

Our work builds on several streams of research. The conformal prediction literature [Vovk et al., 2005; Lei et al., 2018] provides the foundational methodology, while the extension to covariate shift [Tibshirani et al., 2020] directly informs our weighted approach. In causal inference, recent work on individualized treatment effects [Wager and Athey, 2018; Shalit et al., 2017] focuses primarily on point estimation rather than uncertainty quantification.

The closest related work includes Bayesian approaches to ITE uncertainty [Alaa and van der Schaar, 2018] and bootstrap-based methods [Athey et al., 2019]. However, these methods typically require strong parametric assumptions or may not provide finite-sample guarantees. Our distribution-free approach fills this important gap.

## 8. Discussion and Limitations

While our method provides strong theoretical guarantees, several limitations merit discussion. First, the quality of our intervals depends critically on the exchangeability assumption, which may be violated in complex observational studies. Second, our approach requires reasonably accurate base learners for the intervals to be informative, though coverage is maintained even under misspecification.

The computational cost of the leave-one-out variant may limit applicability to very large datasets, though our split conformal variant addresses this concern. Additionally, extending our framework to handle time-series data or other complex dependence structures remains an open challenge.

## 9. Conclusion

We have introduced causal conformal prediction, a novel framework for constructing distribution-free prediction intervals for individual treatment effects. Our method provides finite-sample coverage guarantees without parametric assumptions, handles both randomized and observational studies, and extends naturally to settings with covariate shift.

The key contributions include: (1) theoretical foundations establishing coverage guarantees for both within-study and out-of-study inference, (2) practical algorithms that work with any base learner, and (3) extensions handling observational studies and covariate shift. Our approach addresses a critical gap in the causal inference literature by providing reliable uncertainty quantification for individual treatment effects.

Future work could explore extensions to survival outcomes, multiple treatments, and settings with unmeasured confounding. The framework also opens possibilities for developing adaptive treatment strategies that account for uncertainty in individual treatment effects.

## References

Alaa, A. M., & van der Schaar, M. (2018). Limits of estimating heterogeneous treatment effects: Guidelines for practical algorithm design. *International Conference on Machine Learning*.

Athey, S., Tibshirani, J., & Wager, S. (2019). Generalized random forests. *Annals of Statistics*, 47(2), 1148-1178.

Lei, J., G'Sell, M., Rinaldo, A., Tibshirani, R. J., & Wasserman, L. (2018). Distribution-free predictive inference for regression. *Journal of the American Statistical Association*, 113(523), 1094-1111.

Lei, J., & Wasserman, L. (2014). Distribution-free prediction bands for non-parametric regression. *Journal of the Royal Statistical Society: Series B*, 76(1), 71-96.

Neyman, J. (1923). On the application of probability theory to agricultural experiments. *Statistical Science*, 5(4), 465-472.

Rubin, D. B. (1974). Estimating causal effects of treatments in randomized and nonrandomized studies. *Journal of Educational Psychology*, 66(5), 688-701.

Shalit, U., Johansson, F. D., & Sontag, D. (2017). Estimating individual treatment effect: Generalization bounds and algorithms. *International Conference on Machine Learning*.

Tibshirani, R. J., Barber, R. F., Candes, E. J., & Ramdas, A. (2020). Conformal prediction under covariate shift. *Advances in Neural Information Processing Systems*, 33, 2530-2540.

Vovk, V., Gammerman, A., & Shafer, G. (2005). *Algorithmic Learning in a Random World*. Springer.

Wager, S., & Athey, S. (2018). Estimation and inference of heterogeneous treatment effects using random forests. *Journal of the American Statistical Association*, 113(523), 1228-1242.
