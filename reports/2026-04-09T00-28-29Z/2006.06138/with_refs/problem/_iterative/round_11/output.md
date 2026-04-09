# Problem Formulation

## 2.1 Notation and Setup

We consider the problem of uncertainty quantification for individual-level causal effects. Let $(X, Y(1), Y(0)) \in \mathcal{X} \times \mathcal{Y} \times \mathcal{Y}$ denote the potential outcomes framework, where $X$ represents covariates, $Y(1)$ is the potential outcome under treatment, and $Y(0)$ is the potential outcome under control. The individual treatment effect is defined as $\tau(X) = Y(1) - Y(0)$.

Let $T \in \{0,1\}$ denote the treatment assignment indicator, and define the observed outcome as $Y = TY(1) + (1-T)Y(0)$. We observe i.i.d. data $\{(X_i, T_i, Y_i)\}_{i=1}^n$ where each unit is observed under only one treatment condition, creating the fundamental problem of causal inference.

For a new individual with covariates $X_{n+1}$, our goal is to construct a prediction interval $\mathcal{C}_n(X_{n+1})$ for the unobserved individual treatment effect $\tau(X_{n+1}) = Y_{n+1}(1) - Y_{n+1}(0)$ such that
$$\mathbb{P}(\tau(X_{n+1}) \in \mathcal{C}_n(X_{n+1})) \geq 1 - \alpha$$
for a pre-specified miscoverage level $\alpha \in (0,1)$.

## 2.2 The Distribution Mismatch Problem

A critical challenge in constructing prediction intervals for counterfactual outcomes arises from distributional mismatch. When predicting $Y_{n+1}(1)$ for a new individual, we would ideally use the empirical distribution of residuals from treated units. However, the covariate distribution of treated units, $P_{X|T=1}$, typically differs from the marginal covariate distribution $P_X$ under which we wish to make predictions.

Formally, let $\mu_t(x) = \mathbb{E}[Y(t)|X = x]$ for $t \in \{0,1\}$ denote the conditional mean functions, and define the residuals $R_i(t) = Y_i(t) - \mu_t(X_i)$ for the potential outcomes. Standard conformal prediction would use the empirical quantiles of observed residuals $\{R_i(T_i) : T_i = t\}$ to construct intervals. However, this approach fails to account for the fact that these residuals are drawn from $P_{R(t)|T=t}$ rather than the desired $P_{R(t)}$.

## 2.3 Unified Weighting Framework

The key insight is that inverse probability weighting, fundamental to causal identification, provides a natural solution to the distribution mismatch problem. Define the propensity score $e(x) = \mathbb{P}(T = 1|X = x)$ and the likelihood ratio weights:
$$w_1(x) = \frac{1}{e(x)}, \quad w_0(x) = \frac{1}{1-e(x)}$$

These weights satisfy the crucial property that for any measurable function $g$:
$$\mathbb{E}[w_t(X) \cdot g(X) \cdot \mathbf{1}\{T = t\}] = \mathbb{E}[g(X)]$$

This relationship reveals that weighted exchangeability holds: the weighted empirical distribution of residuals from treated units properly represents the population distribution of treatment effect residuals.

## 2.4 Formal Problem Statement

**Given:** 
- Training data $\mathcal{D}_n = \{(X_i, T_i, Y_i)\}_{i=1}^n$ drawn i.i.d. from $(X, T, Y)$
- Outcome predictors $\hat{\mu}_t: \mathcal{X} \to \mathbb{R}$ for $t \in \{0,1\}$
- Propensity score estimates $\hat{e}: \mathcal{X} \to (0,1)$ or known propensity scores
- Target covariate $X_{n+1}$ for prediction

**Find:** A prediction interval $\mathcal{C}_n(X_{n+1}) \subseteq \mathbb{R}$ such that:
$$\mathbb{P}(\tau(X_{n+1}) \in \mathcal{C}_n(X_{n+1})) \geq 1 - \alpha$$

**Objective:** The prediction interval should:
1. Achieve finite-sample coverage guarantees without asymptotic approximations
2. Remain valid under imperfect estimation of either $\hat{\mu}_t$ or $\hat{e}$
3. Adapt to different target populations through appropriate weighting schemes
4. Leverage the connection between causal identification and distribution-free prediction

## 2.5 Technical Assumptions

**Assumption 1 (Unconfoundedness):** $(Y(0), Y(1)) \perp T | X$, ensuring that treatment assignment is ignorable given observed covariates.

**Assumption 2 (Overlap):** There exists $\epsilon > 0$ such that $\epsilon \leq e(x) \leq 1-\epsilon$ for all $x \in \mathcal{X}$, ensuring bounded propensity scores.

**Assumption 3 (Exchangeability):** The augmented data $\{(X_i, T_i, Y_i, X_{n+1})\}_{i=1}^{n+1}$ are exchangeable, where $(X_{n+1}, T_{n+1}, Y_{n+1})$ represents the test point.

These assumptions are standard in causal inference and significantly weaker than parametric modeling assumptions typically required for uncertainty quantification.

## 2.6 Connection to Prior Work

Our formulation extends conformal prediction under covariate shift (Tibshirani et al., 2020) to the causal setting. While their work addresses distribution mismatch in supervised learning using likelihood ratios $dP_{test}/dP_{train}$, we recognize that propensity score weights in causal inference serve the identical mathematical role.

Previous work on individual treatment effect prediction intervals (Kivaranovic et al., 2020) constructs separate intervals for $Y(1)$ and $Y(0)$ then combines them, leading to conservative intervals that do not exploit the causal structure. Our approach directly addresses the counterfactual prediction problem while maintaining the distribution-free guarantees of conformal prediction.

The formulation naturally accommodates different target populations: predicting effects for the entire population uses weights $w_t(x) = 1/\mathbb{P}(T=t|X=x)$, while predicting effects for treated units only uses uniform weights, and predicting effects for controls only requires reweighting the treated units to match the control distribution.

This unified framework reveals that the fundamental challenge of uncertainty quantification for individual causal effects is equivalent to the well-studied problem of prediction under covariate shift, with propensity scores providing the necessary likelihood ratios for valid inference.