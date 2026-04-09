# Problem Formulation

## 2.1 Notation and Setup

We consider the fundamental problem of causal inference with heterogeneous treatment effects. Let $(X, Y, T) \in \mathcal{X} \times \mathbb{R} \times \{0,1\}$ denote a random triple where $X$ represents covariates taking values in a measurable space $\mathcal{X}$, $Y$ is a real-valued outcome, and $T$ is a binary treatment indicator. We observe $n$ i.i.d. samples $\{(X_i, Y_i, T_i)\}_{i=1}^n$ from the joint distribution $P_{X,Y,T}$.

Following the potential outcomes framework, we define $Y^{(1)}$ and $Y^{(0)}$ as the potential outcomes under treatment and control, respectively. The observed outcome satisfies $Y = T \cdot Y^{(1)} + (1-T) \cdot Y^{(0)}$. The individual treatment effect (ITE) for a unit with covariates $x$ is defined as:
$$\tau(x) = Y^{(1)} - Y^{(0)}$$

Let $\mu_1(x) = \mathbb{E}[Y^{(1)} | X = x]$ and $\mu_0(x) = \mathbb{E}[Y^{(0)} | X = x]$ denote the conditional mean functions, so that the conditional average treatment effect (CATE) is $\tau_{\text{CATE}}(x) = \mu_1(x) - \mu_0(x)$.

For a new individual with covariates $X_{n+1}$, our goal is to construct a prediction interval $\mathcal{C}_n(X_{n+1})$ for their individual treatment effect $\tau(X_{n+1})$ such that:
$$\mathbb{P}(\tau(X_{n+1}) \in \mathcal{C}_n(X_{n+1})) \geq 1 - \alpha$$
for a pre-specified miscoverage level $\alpha \in (0,1)$.

## 2.2 The Distributional Mismatch Problem

A critical challenge arises from the fact that the covariate distributions differ between treated and control groups in general. Let $P_X^{(1)} = P_{X|T=1}$ and $P_X^{(0)} = P_{X|T=0}$ denote the conditional covariate distributions. When constructing prediction intervals for counterfactual outcomes, we face a fundamental mismatch: to predict $Y^{(0)}$ for individuals who might receive treatment, we need intervals that are valid under $P_X^{(1)}$, but our control group data comes from $P_X^{(0)}$.

Define the propensity score $e(x) = \mathbb{P}(T = 1 | X = x)$ and assume $0 < e(x) < 1$ for all $x \in \mathcal{X}$ (overlap assumption). The likelihood ratios are:
$$w_1(x) = \frac{e(x)}{1-e(x)}, \quad w_0(x) = \frac{1-e(x)}{e(x)}$$

These ratios naturally connect the distributional mismatch problem to causal identifiability through inverse probability weighting.

## 2.3 Formal Problem Statement

**Given:** 
- Training data $\mathcal{D}_n = \{(X_i, Y_i, T_i)\}_{i=1}^n$ drawn i.i.d. from $P_{X,Y,T}$
- A new covariate vector $X_{n+1}$ 
- Miscoverage level $\alpha \in (0,1)$
- Access to propensity scores $e(x)$ (known or estimated)

**Find:** A data-dependent prediction set $\mathcal{C}_n: \mathcal{X} \to 2^{\mathbb{R}}$ such that:
$$\mathbb{P}(\tau(X_{n+1}) \in \mathcal{C}_n(X_{n+1})) \geq 1 - \alpha$$

**Objective:** The prediction interval should:
1. Achieve the coverage guarantee without asymptotic approximations
2. Work under minimal distributional assumptions
3. Account for both aleatory uncertainty (individual response variability) and epistemic uncertainty (finite sample estimation error)
4. Naturally handle the distributional mismatch between treatment groups

## 2.4 Technical Assumptions

**Assumption 1 (Unconfoundedness):** $(Y^{(1)}, Y^{(0)}) \perp T | X$, i.e., treatment assignment is conditionally independent of potential outcomes given covariates.

**Assumption 2 (Overlap):** $0 < e(x) < 1$ for all $x \in \mathcal{X}$, ensuring both treatment and control observations exist in all covariate regions.

**Assumption 3 (Consistency):** $Y = T \cdot Y^{(1)} + (1-T) \cdot Y^{(0)}$, meaning observed outcomes equal potential outcomes under the assigned treatment.

**Assumption 4 (Exchangeability):** The augmented sequence $(X_1, Y_1^{(1)}, Y_1^{(0)}, T_1), \ldots, (X_{n+1}, Y_{n+1}^{(1)}, Y_{n+1}^{(0)}, T_{n+1})$ is exchangeable, where $T_{n+1}$ represents the (possibly hypothetical) treatment assignment for the test unit.

These assumptions are standard in causal inference and significantly weaker than parametric modeling assumptions typically required for uncertainty quantification.

## 2.5 Connection to Prior Work and Gap Analysis

Existing approaches to uncertainty quantification in causal inference fall into several categories:

**Parametric methods** rely on distributional assumptions (e.g., Gaussian errors) and asymptotic normality of estimators. These provide confidence intervals for $\tau_{\text{CATE}}(x)$ but fail to capture the full uncertainty in $\tau(x)$, which includes irreducible randomness from $Y^{(1)} - Y^{(0)}$.

**Bootstrap and resampling methods** can estimate the sampling distribution of CATE estimators but struggle with the counterfactual nature of individual treatment effects and often lack finite-sample guarantees.

**Recent conformal prediction work** has shown promise for distribution-free uncertainty quantification in supervised learning. The work of Tibshirani et al. (2020) extends conformal prediction to covariate shift settings using likelihood ratio weighting, while Kivaranovic et al. (2020) applies conformal methods to individual treatment effects but does not address the distributional mismatch problem.

**The key gap** is that no existing method simultaneously addresses: (1) the unobservable nature of individual treatment effects, (2) the distributional mismatch between treatment groups, and (3) the need for finite-sample coverage guarantees without strong parametric assumptions.

Our formulation recognizes that the same mathematical principles underlying causal identification (inverse probability weighting) naturally solve the distributional mismatch problem in conformal prediction. This connection suggests a unified approach where the propensity score serves dual roles: ensuring causal identifiability and correcting for covariate shift in uncertainty quantification.

The resulting framework should provide prediction intervals that maintain coverage guarantees even when either the outcome predictors or the propensity score estimates are imperfect, achieving graceful degradation rather than complete failure when key quantities are misspecified.