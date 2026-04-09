# Problem Formulation

## 2.1 Notation and Setup

Let $(X, Y^{(1)}, Y^{(0)}) \sim P$ denote the joint distribution of covariates $X \in \mathcal{X} \subseteq \mathbb{R}^d$ and potential outcomes $Y^{(1)}, Y^{(0)} \in \mathbb{R}$ under treatment ($T=1$) and control ($T=0$), respectively. For each unit $i$ in our study, we observe the triple $(X_i, Y_i, T_i)$ where $T_i \in \{0,1\}$ is the treatment assignment and $Y_i = T_i Y_i^{(1)} + (1-T_i) Y_i^{(0)}$ is the observed outcome. The fundamental problem of causal inference is that we never observe both potential outcomes $(Y_i^{(1)}, Y_i^{(0)})$ for any individual.

Let $\{(X_i, Y_i, T_i)\}_{i=1}^n$ denote our training data, and consider a new individual with covariates $X_{n+1}$ drawn from some target distribution $Q_X$. Our goal is to construct prediction intervals for the counterfactual outcome $Y_{n+1}^{(1-T_{n+1})}$ - that is, the outcome this individual would experience under the treatment they did not receive.

We assume the standard causal inference framework with:
- **Stable Unit Treatment Value Assumption (SUTVA)**: No interference between units and well-defined treatments
- **Unconfoundedness**: $(Y^{(1)}, Y^{(0)}) \perp T \mid X$, meaning treatment assignment is independent of potential outcomes given covariates
- **Positivity**: $0 < \pi(x) < 1$ for all $x \in \mathcal{X}$, where $\pi(x) = P(T=1|X=x)$ is the propensity score

## 2.2 The Covariate Shift Challenge

A critical but often overlooked challenge arises when the covariate distribution of the target population differs from that of the study population. Specifically, let $P_X$ denote the covariate distribution in the training data and $Q_X$ denote the target covariate distribution. When $P_X \neq Q_X$, standard prediction intervals may fail to achieve nominal coverage.

Furthermore, within the study itself, the covariate distributions differ between treatment groups. For treated units, we observe covariates distributed as $P_X^{(1)}(x) = P(X=x|T=1)$, while for control units, covariates follow $P_X^{(0)}(x) = P(X=x|T=0)$. When constructing prediction intervals for counterfactual outcomes, this creates a fundamental distributional mismatch that must be addressed.

## 2.3 Problem Statement

**Given:** 
- Training data $\{(X_i, Y_i, T_i)\}_{i=1}^n$ from distribution $P$
- A new individual with covariates $X_{n+1}$ from target distribution $Q_X$
- Desired coverage level $1-\alpha$ for $\alpha \in (0,1)$
- Access to likelihood ratio $w(x) = \frac{dQ_X}{dP_X}(x)$ (or ability to estimate it)

**Find:** A prediction interval $\mathcal{C}_n(X_{n+1}) \subseteq \mathbb{R}$ such that:
$$P\left(Y_{n+1}^{(1-T_{n+1})} \in \mathcal{C}_n(X_{n+1})\right) \geq 1-\alpha$$

**Objective:** The prediction interval should:
1. Achieve finite-sample coverage without asymptotic approximations
2. Be distribution-free, requiring no parametric assumptions
3. Handle covariate shift between study and target populations
4. Account for distributional differences between treatment groups within the study
5. Degrade gracefully when key quantities are estimated imperfectly

## 2.4 Technical Approach

We leverage the connection between importance weighting for covariate shift and inverse probability weighting in causal inference. The key insight is that the propensity score $\pi(x)$ naturally provides the likelihood ratio needed to reweight observations from the control group to match the treated group's covariate distribution when predicting $Y^{(1)}$ for treated units, and vice versa.

For a treated individual ($T_{n+1} = 1$) seeking a prediction interval for $Y_{n+1}^{(0)}$, we construct weights:
$$w_i^{(0)}(x) = \frac{(1-T_i) \cdot w(X_i) \cdot \pi(X_i)}{(1-\pi(X_i))} \cdot \frac{1}{\sum_{j=1}^n \frac{(1-T_j) \cdot w(X_j) \cdot \pi(X_j)}{(1-\pi(X_j))}}$$

These weights simultaneously correct for:
- The covariate shift from study to target population (via $w(X_i)$)
- The distributional mismatch between treated and control groups (via the propensity score ratio)

## 2.5 Weighted Conformal Prediction Framework

We extend the conformal prediction methodology of Vovk et al. (2005) to handle the weighted exchangeability that arises in our causal setting. Given a conformity score function $S((x,y), \mathcal{D})$ that measures how well point $(x,y)$ conforms to dataset $\mathcal{D}$, we compute weighted nonconformity scores and use weighted quantiles to determine inclusion in the prediction set.

The prediction interval for $Y_{n+1}^{(1-T_{n+1})}$ is constructed as:
$$\mathcal{C}_n(x) = \left\{y \in \mathbb{R} : S((x,y), \mathcal{D}_n) \leq \text{WeightedQuantile}_{1-\alpha}\left(\{S_i\}_{i=1}^n, \{w_i\}_{i=1}^n\right)\right\}$$

where $S_i$ are the nonconformity scores from training data and $w_i$ are the appropriately constructed importance weights.

## 2.6 Key Assumptions

1. **Causal Assumptions**: SUTVA, unconfoundedness, and positivity hold
2. **Covariate Shift**: Target distribution $Q_X$ is absolutely continuous with respect to study distribution $P_X$
3. **Known/Estimable Weights**: The likelihood ratio $w(x) = dQ_X/dP_X(x)$ is known or can be estimated accurately
4. **Propensity Score**: $\pi(x) = P(T=1|X=x)$ is known or can be estimated consistently

## 2.7 Connection to Prior Work

This formulation extends beyond existing approaches in several ways:

**Conformal Prediction Literature**: While Tibshirani et al. (2020) developed weighted conformal prediction for covariate shift in standard supervised learning, our work addresses the more complex setting where the relevant training data for counterfactual prediction comes from a different treatment group, creating a double covariate shift problem.

**Causal Inference Literature**: Existing work on individual treatment effect estimation (e.g., Kivaranovic et al., 2020) focuses on prediction intervals for the treatment effect $\tau(x) = Y^{(1)} - Y^{(0)}$ but does not address counterfactual outcome prediction under covariate shift. Our approach directly targets the more fundamental problem of predicting unobserved potential outcomes.

**Gap Addressed**: Current methods either handle covariate shift in supervised learning or uncertainty quantification in causal inference, but not both simultaneously. Our formulation provides the first distribution-free approach to counterfactual outcome prediction that accounts for both the inherent covariate shift in causal inference and potential differences between study and target populations.