# Reconstruction: problem
**Paper:** 2006.06138  
**Condition:** with_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Problem Formulation

## 2.1 Notation and Setup

Let $\mathcal{X} \subseteq \mathbb{R}^d$ denote the covariate space and $\mathcal{Y} \subseteq \mathbb{R}$ the outcome space. We consider the potential outcomes framework where each unit $i$ has two potential outcomes: $Y_i(0)$ under control and $Y_i(1)$ under treatment. The observed outcome is $Y_i = T_i Y_i(1) + (1-T_i) Y_i(0)$, where $T_i \in \{0,1\}$ is the treatment indicator. Let $X_i \in \mathcal{X}$ denote the observed covariates for unit $i$.

The individual treatment effect (ITE) for unit $i$ is defined as:
$$\tau_i = Y_i(1) - Y_i(0)$$

The conditional average treatment effect (CATE) function is:
$$\tau(x) = \mathbb{E}[Y(1) - Y(0) | X = x] = \mathbb{E}[Y(1) | X = x] - \mathbb{E}[Y(0) | X = x]$$

Let $\mu_1(x) = \mathbb{E}[Y(1) | X = x]$ and $\mu_0(x) = \mathbb{E}[Y(0) | X = x]$ denote the conditional mean functions under treatment and control, respectively.

We observe $n$ units from a study population with data $\{(X_i, T_i, Y_i)\}_{i=1}^n$, where $(X_i, T_i, Y_i(T_i))$ are drawn i.i.d. from some distribution $P$. We may also have access to $m$ additional units $\{X_j^*\}_{j=1}^m$ from a target population drawn from distribution $Q$ on $\mathcal{X}$, where we wish to make predictions but do not observe outcomes.

## 2.2 Problem Statement

Our goal is to construct prediction intervals for individual treatment effects that provide finite-sample coverage guarantees without relying on asymptotic approximations or unverifiable modeling assumptions. Specifically, for a new unit with covariates $X_{n+1}$ from the target population, we seek to construct an interval $C_n(X_{n+1}) \subseteq \mathbb{R}$ such that:

$$\mathbb{P}\left(\tau_{n+1} \in C_n(X_{n+1})\right) \geq 1 - \alpha$$

for a pre-specified miscoverage level $\alpha \in (0,1)$, where the probability is taken over the randomness in both the training data and the new unit.

The fundamental challenge is that $\tau_{n+1} = Y_{n+1}(1) - Y_{n+1}(0)$ is never directly observable since we can only observe one potential outcome for each unit. This creates a missing data problem that distinguishes our setting from standard conformal prediction applications.

## 2.3 Objective

We aim to develop a methodology that constructs intervals $C_n(x)$ satisfying the following properties:

1. **Finite-sample validity**: The coverage guarantee holds for any finite sample size $n$, without requiring large-sample approximations.

2. **Distribution-free**: The method should work without assuming specific parametric forms for the outcome distributions or treatment effect heterogeneity.

3. **Covariate shift robustness**: When the target population distribution $Q$ differs from the study population distribution $P$ on $\mathcal{X}$, the intervals should maintain validity under appropriate conditions.

4. **Computational efficiency**: The method should be implementable with modern machine learning algorithms for estimating $\mu_1(x)$ and $\mu_0(x)$.

The key insight is to leverage conformal prediction methodology by constructing appropriate nonconformity scores that can handle the missing data structure inherent in causal inference problems.

## 2.4 Technical Assumptions

We require the following assumptions:

**Assumption 1 (Unconfoundedness)**: $(Y(0), Y(1)) \perp T | X$, meaning treatment assignment is conditionally independent of potential outcomes given covariates.

**Assumption 2 (Overlap)**: There exists $\epsilon > 0$ such that $\epsilon \leq e(x) \leq 1-\epsilon$ for all $x$ in the support of $X$, where $e(x) = \mathbb{P}(T=1|X=x)$ is the propensity score.

**Assumption 3 (Covariate shift structure)**: When the study and target populations differ, we assume $Q \ll P$ on $\mathcal{X}$ with known or estimable likelihood ratio $w(x) = \frac{dQ}{dP}(x)$.

**Assumption 4 (Exchangeability)**: Conditional on covariates and treatment assignment, the potential outcomes are exchangeable across units within each treatment group.

Assumption 1 ensures identifiability of causal effects from observational data. Assumption 2 guarantees that we observe sufficient overlap between treatment groups across the covariate space. Assumption 3 enables valid inference when generalizing to different populations, following the covariate shift framework of Tibshirani et al. (2020). Assumption 4 provides the foundation for applying conformal prediction techniques.

## 2.5 Connection to Prior Work

Standard conformal prediction methods (Vovk et al., 2005) require exchangeable data and cannot directly handle the missing data structure in causal inference. While Lei et al. (2018) and others have extended conformal prediction to various settings, the causal inference context presents unique challenges because individual treatment effects are fundamentally unobservable.

Existing approaches to uncertainty quantification for treatment effect heterogeneity typically rely on asymptotic normality of estimators (Künzel et al., 2019) or Bayesian methods with strong modeling assumptions. These approaches often fail to provide reliable finite-sample guarantees, particularly when the underlying models are misspecified.

Recent work on weighted conformal prediction under covariate shift (Tibshirani et al., 2020) provides a foundation for handling distribution mismatch between study and target populations. However, their framework assumes the full outcome is observable, which does not hold in our causal setting where we seek to predict the unobservable difference between potential outcomes.

Our formulation extends conformal prediction to the causal inference setting by carefully constructing nonconformity scores that account for the missing data structure while maintaining the finite-sample validity guarantees that make conformal methods attractive for high-stakes decision making.
