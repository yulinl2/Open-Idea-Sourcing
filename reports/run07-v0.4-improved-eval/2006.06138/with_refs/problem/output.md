# Reconstruction: problem
**Paper:** 2006.06138  
**Condition:** with_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Problem Formulation

## 2.1 Notation and Setup

Let $\mathcal{X} \subseteq \mathbb{R}^d$ denote the covariate space and $\mathcal{Y} \subseteq \mathbb{R}$ the outcome space. Under the potential outcomes framework, each unit $i$ is associated with a covariate vector $X_i \in \mathcal{X}$ and two potential outcomes: $Y_i(1)$ representing the outcome under treatment and $Y_i(0)$ representing the outcome under control. The individual treatment effect for unit $i$ is $\tau_i = Y_i(1) - Y_i(0)$. We observe the treatment assignment $T_i \in \{0,1\}$ and the realized outcome $Y_i = T_i Y_i(1) + (1-T_i) Y_i(0)$, but crucially, we never observe both potential outcomes for any individual.

Let $P$ denote the joint distribution over $(X, Y(0), Y(1), T)$, and define the conditional average treatment effect (CATE) function as:
$$\tau(x) = \mathbb{E}[Y(1) - Y(0) \mid X = x] = \mu_1(x) - \mu_0(x),$$
where $\mu_t(x) = \mathbb{E}[Y(t) \mid X = x]$ for $t \in \{0,1\}$.

We consider two distinct settings:
- **Training population**: We observe $n$ i.i.d. samples $\{(X_i, T_i, Y_i)\}_{i=1}^n$ from distribution $P$.
- **Target population**: We wish to make inferences about a new unit with covariates $X_{n+1}$ drawn from a potentially different marginal distribution $\tilde{P}_X$, while maintaining the assumption that the conditional distributions $P_{Y(0)|X}$ and $P_{Y(1)|X}$ remain unchanged.

## 2.2 Problem Statement

Given training data $\{(X_i, T_i, Y_i)\}_{i=1}^n$, we seek to construct prediction intervals $\hat{C}_n(x) \subseteq \mathbb{R}$ for the individual treatment effect $\tau(x)$ at any covariate value $x \in \mathcal{X}$ such that:

$$P\left(\tau(X_{n+1}) \in \hat{C}_n(X_{n+1})\right) \geq 1 - \alpha$$

for a pre-specified miscoverage level $\alpha \in (0,1)$, where the probability is taken over the randomness in both the training data and the test covariate $X_{n+1}$.

The fundamental challenge is that $\tau(x) = \mathbb{E}[Y(1) - Y(0) \mid X = x]$ is never directly observable, as we only observe one potential outcome per unit. This necessitates the construction of prediction intervals based on estimated CATE functions $\hat{\tau}(x)$ obtained from machine learning algorithms, while accounting for both the estimation uncertainty and the inherent unobservability of individual treatment effects.

## 2.3 Objective and Desiderata

Our objective is to develop a methodology that produces prediction intervals $\hat{C}_n(x)$ satisfying the following properties:

1. **Finite-sample validity**: The coverage guarantee should hold exactly in finite samples without relying on asymptotic approximations:
   $$P\left(\tau(X_{n+1}) \in \hat{C}_n(X_{n+1})\right) \geq 1 - \alpha$$

2. **Distribution-free guarantees**: The coverage should hold without assumptions on the underlying distribution $P$ or the form of treatment effect heterogeneity.

3. **Robustness to model misspecification**: The intervals should maintain valid coverage even when the base CATE estimator $\hat{\tau}(x)$ is misspecified.

4. **Covariate shift adaptation**: The methodology should handle settings where the test covariate distribution $\tilde{P}_X$ differs from the training distribution $P_X$, provided the likelihood ratio $w(x) = d\tilde{P}_X(x)/dP_X(x)$ is known or can be estimated.

## 2.4 Technical Assumptions

We impose the following assumptions:

**Assumption 1 (Unconfoundedness)**: Treatment assignment is unconfounded given covariates:
$$(Y(0), Y(1)) \perp T \mid X$$

**Assumption 2 (Overlap)**: There exists $\epsilon > 0$ such that $\epsilon \leq e(x) \leq 1-\epsilon$ for all $x$ in the support of $P_X$, where $e(x) = P(T=1|X=x)$ is the propensity score.

**Assumption 3 (SUTVA)**: The Stable Unit Treatment Value Assumption holds, ensuring no interference between units and consistency of potential outcomes.

**Assumption 4 (Covariate shift)**: When considering distribution shift, we assume:
- The conditional outcome distributions remain invariant: $P_{Y(t)|X} = \tilde{P}_{Y(t)|X}$ for $t \in \{0,1\}$
- The target covariate distribution $\tilde{P}_X$ is absolutely continuous with respect to the training distribution $P_X$
- The likelihood ratio $w(x) = d\tilde{P}_X(x)/dP_X(x)$ is known or can be accurately estimated

These assumptions are standard in the causal inference literature. Assumption 1 ensures identifiability of treatment effects, Assumption 2 guarantees that both treatment and control outcomes can be estimated across the covariate space, and Assumption 3 provides the foundational framework for potential outcomes. Assumption 4 extends the framework to handle realistic scenarios where training and deployment populations differ.

## 2.5 Connection to Prior Work

Existing approaches for CATE estimation uncertainty quantification suffer from several limitations that our formulation addresses:

**Asymptotic methods**: Traditional approaches rely on asymptotic normality of CATE estimators and construct confidence intervals using estimated standard errors. However, these methods require strong regularity conditions, large sample approximations, and often fail to account for the complex bias-variance tradeoffs inherent in modern machine learning estimators.

**Bootstrap-based methods**: While bootstrap approaches can capture some estimation uncertainty, they typically do not provide finite-sample guarantees and may fail under model misspecification or when the bootstrap distribution poorly approximates the true sampling distribution.

**Bayesian approaches**: Bayesian credible intervals can capture uncertainty but require strong prior assumptions and computational intensity, while lacking the distribution-free guarantees essential for robust decision-making.

Our formulation extends conformal prediction methodology, which provides distribution-free, finite-sample prediction intervals for standard regression problems [Tibshirani et al., 2020], to the causal inference setting. The key insight is that while individual treatment effects $\tau(X_i)$ are never observed, we can construct conformity scores based on estimated potential outcomes and leverage the exchangeability properties of the data to obtain valid coverage guarantees. Furthermore, by incorporating likelihood ratio weighting as in [Tibshirani et al., 2020], our approach handles covariate shift between training and target populations—a critical consideration for real-world deployment of causal inference methods.

The fundamental gap addressed by our formulation is the lack of reliable, assumption-lean uncertainty quantification for individual-level causal effects, which is essential for personalized decision-making in high-stakes applications where understanding both the magnitude and uncertainty of treatment effects is crucial.
