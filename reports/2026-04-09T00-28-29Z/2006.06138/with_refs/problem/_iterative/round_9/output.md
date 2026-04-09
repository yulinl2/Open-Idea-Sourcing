# Problem Formulation

## 2.1 Notation and Setup

Let $(X, Y(1), Y(0)) \in \mathcal{X} \times \mathbb{R} \times \mathbb{R}$ denote the potential outcomes framework, where $X$ represents covariates in some measurable space $\mathcal{X}$, and $Y(1), Y(0)$ are the potential outcomes under treatment and control, respectively. The individual treatment effect is defined as $\tau(X) = Y(1) - Y(0)$. Let $T \in \{0,1\}$ denote the treatment assignment indicator, and define the observed outcome as $Y = TY(1) + (1-T)Y(0)$.

We observe $n$ i.i.d. samples $\{(X_i, T_i, Y_i)\}_{i=1}^n$ from the joint distribution of $(X, T, Y)$, where each unit receives only one treatment. For a new unit with covariates $X_{n+1}$, we seek to construct prediction intervals for the counterfactual outcome $Y_{n+1}(1-T_{n+1})$ - that is, the outcome this unit would have experienced under the treatment they did not receive.

Let $\pi(x) = \mathbb{P}(T = 1 | X = x)$ denote the propensity score, and define the importance weights as:
$$w_1(x) = \frac{\pi(x)}{\pi(x)} = 1, \quad w_0(x) = \frac{1-\pi(x)}{1-\pi(x)} = 1$$
for units in their observed treatment group, and
$$w_1(x) = \frac{\pi(x)}{1-\pi(x)}, \quad w_0(x) = \frac{1-\pi(x)}{\pi(x)}$$
for counterfactual prediction, where $w_t(x)$ represents the weight needed to adjust from the distribution of covariates in group $1-t$ to group $t$.

## 2.2 Problem Statement

**Given:** 
- Training data $\mathcal{D}_n = \{(X_i, T_i, Y_i)\}_{i=1}^n$ 
- A new unit with covariates $X_{n+1}$ and treatment assignment $T_{n+1}$
- Desired coverage level $1-\alpha$ for $\alpha \in (0,1)$

**Find:** A prediction interval $\mathcal{C}_n(X_{n+1}, 1-T_{n+1})$ such that
$$\mathbb{P}\left(Y_{n+1}(1-T_{n+1}) \in \mathcal{C}_n(X_{n+1}, 1-T_{n+1})\right) \geq 1-\alpha$$

The fundamental challenge is that we never observe $Y_{n+1}(1-T_{n+1})$ for any unit, and the covariate distribution among treated units $\mathbb{P}(X|T=1)$ differs from that among controls $\mathbb{P}(X|T=0)$, creating a covariate shift problem when predicting counterfactual outcomes.

## 2.3 Objective

We seek to construct a weighted conformal prediction procedure that:

1. **Maintains finite-sample coverage guarantees** without asymptotic approximations
2. **Accounts for covariate shift** between treatment groups using importance weights derived from propensity scores
3. **Handles both sources of uncertainty:** the inherent variability in individual responses and the uncertainty from finite-sample estimation
4. **Provides distribution-free validity** without strong parametric assumptions

Formally, we aim to construct prediction intervals of the form:
$$\mathcal{C}_n(x, t) = \left\{y \in \mathbb{R} : V_{n+1}^{(x,y,t)} \leq \text{Quantile}\left(1-\alpha; \sum_{i: T_i = 1-t} \tilde{w}_i^{(x,t)} \delta_{V_i^{(x,y,t)}} + \tilde{w}_{n+1}^{(x,t)} \delta_{\infty}\right)\right\}$$

where $V_i^{(x,y,t)}$ are appropriately defined conformity scores, and $\tilde{w}_i^{(x,t)}$ are normalized importance weights that correct for the distributional mismatch between the group used for calibration and the target population.

## 2.4 Assumptions

**A1 (Unconfoundedness):** $(Y(1), Y(0)) \perp T | X$, ensuring that treatment assignment is conditionally independent of potential outcomes given covariates.

**A2 (Overlap):** There exist constants $c, C > 0$ such that $c \leq \pi(x) \leq 1-c$ for all $x$ in the support of $X$, ensuring that propensity scores are bounded away from 0 and 1.

**A3 (Consistency):** $Y = TY(1) + (1-T)Y(0)$, meaning observed outcomes correspond to potential outcomes under the assigned treatment.

**A4 (Exchangeability within groups):** Conditional on treatment assignment, units are exchangeable: $(X_i, Y_i(t)) | T_i = t$ are exchangeable for $t \in \{0,1\}$.

**A5 (Propensity score estimation):** We have access to either the true propensity score $\pi(x)$ or a consistent estimator $\hat{\pi}_n(x)$ such that $|\hat{\pi}_n(x) - \pi(x)| \to 0$ in probability uniformly over the support of $X$.

Assumptions A1-A3 are standard in causal inference and ensure identifiability of causal effects. A4 enables the application of conformal prediction methodology within treatment groups. A5 is crucial for constructing appropriate importance weights, and the connection between propensity scores and covariate shift correction makes this assumption natural in our setting.

## 2.5 Connection to Prior Work

Our formulation extends existing conformal prediction methodology in several key ways. Standard conformal prediction (Vovk et al., 2005) requires exchangeable data, which fails in counterfactual prediction due to covariate shift between treatment groups. The weighted conformal prediction framework of Tibshirani et al. (2020) addresses covariate shift when the likelihood ratio between training and test distributions is known, but does not address the causal inference setting where this ratio is determined by propensity scores.

Previous work on uncertainty quantification for individual treatment effects (Kivaranovic et al., 2020) focuses on constructing intervals for the treatment effect $\tau(X) = Y(1) - Y(0)$ by combining separate prediction intervals for $Y(1)$ and $Y(0)$. However, this approach does not address the fundamental covariate shift issue and can be overly conservative.

Our formulation bridges these gaps by recognizing that: (1) the propensity score $\pi(x)$ that determines causal identifiability also provides the appropriate likelihood ratio for covariate shift correction, and (2) weighted conformal prediction can be adapted to handle the specific structure of counterfactual prediction problems. This connection between causal inference and distribution-free prediction under covariate shift has not been previously explored and offers a principled approach to uncertainty quantification in causal inference.

The key insight is that when predicting $Y(1)$ for a unit in the control group, we need to reweight the treated units' data to match the covariate distribution of controls, using weights proportional to $(1-\pi(X_i))/\pi(X_i)$. This weighting scheme naturally arises from both the covariate shift correction perspective and the inverse probability weighting approach fundamental to causal inference.