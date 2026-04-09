# Problem Formulation

## Notation and Setup

Let $(X, Y(1), Y(0)) \in \mathcal{X} \times \mathcal{Y} \times \mathcal{Y}$ denote the potential outcomes framework, where $X \in \mathcal{X} \subseteq \mathbb{R}^d$ represents covariates, $Y(1) \in \mathcal{Y} \subseteq \mathbb{R}$ is the potential outcome under treatment, and $Y(0) \in \mathcal{Y}$ is the potential outcome under control. Let $T \in \{0,1\}$ denote the treatment assignment indicator. The observed outcome is $Y = TY(1) + (1-T)Y(0)$, and we observe the data $(X_i, T_i, Y_i)_{i=1}^n$ where each triple is drawn i.i.d. from some joint distribution $P$.

The individual treatment effect for covariate vector $x$ is defined as:
$$\tau(x) = Y(1) - Y(0) \mid X = x$$

For a new individual with covariates $X_{n+1}$, we seek to construct a prediction interval for the unobserved counterfactual outcome. Specifically, if the individual receives treatment $t \in \{0,1\}$, we observe $Y_{n+1} = Y_{n+1}(t)$ but wish to predict $Y_{n+1}(1-t)$ - the outcome they would have experienced under the alternative treatment.

Let $\pi(x) = P(T = 1 \mid X = x)$ denote the propensity score, and define the likelihood ratio for covariate shift correction as:
$$w_t(x) = \frac{P(X = x \mid T = 1-t)}{P(X = x \mid T = t)}$$

This ratio accounts for the distributional mismatch between covariates in the treated and control groups when predicting counterfactual outcomes.

## Problem Statement

**Given:** Training data $\mathcal{D}_n = \{(X_i, T_i, Y_i)\}_{i=1}^n$ drawn i.i.d. from distribution $P$, a new individual with covariates $X_{n+1}$, observed treatment $T_{n+1}$, and a target coverage level $1-\alpha$ for $\alpha \in (0,1)$.

**Find:** A prediction interval $\mathcal{C}_n(X_{n+1}, T_{n+1}) \subseteq \mathbb{R}$ such that:
$$P\left(Y_{n+1}(1-T_{n+1}) \in \mathcal{C}_n(X_{n+1}, T_{n+1})\right) \geq 1-\alpha$$

where the probability is taken over the randomness in $\mathcal{D}_n$, $X_{n+1}$, $T_{n+1}$, and $Y_{n+1}(1-T_{n+1})$.

The challenge is that $Y_{n+1}(1-T_{n+1})$ is never observed, and the covariate distribution among subjects who received treatment $1-T_{n+1}$ in the training data differs from the distribution of $X_{n+1}$.

## Formal Objective

We seek to construct a weighted conformal prediction procedure that provides distribution-free coverage guarantees. Specifically, define nonconformity scores:
$$V_i^{(y)} = S((X_i, y), \mathcal{D}_n^{(1-T_{n+1})})$$

where $S$ is a score function measuring how well point $(X_i, y)$ conforms to the subset of training data $\mathcal{D}_n^{(1-T_{n+1})} = \{(X_j, Y_j) : T_j = 1-T_{n+1}\}$, and:
$$V_{n+1}^{(y)} = S((X_{n+1}, y), \mathcal{D}_n^{(1-T_{n+1})})$$

The weighted conformal prediction interval is:
$$\mathcal{C}_n(X_{n+1}, T_{n+1}) = \left\{y \in \mathbb{R} : V_{n+1}^{(y)} \leq \text{Quantile}\left(1-\alpha; \sum_{i: T_i = 1-T_{n+1}} \tilde{w}_i \delta_{V_i^{(y)}} + \tilde{w}_{n+1} \delta_{\infty}\right)\right\}$$

where the weights are defined as:
$$\tilde{w}_i = \frac{w_{T_{n+1}}(X_i)}{\sum_{j: T_j = 1-T_{n+1}} w_{T_{n+1}}(X_j) + w_{T_{n+1}}(X_{n+1})}, \quad \tilde{w}_{n+1} = \frac{w_{T_{n+1}}(X_{n+1})}{\sum_{j: T_j = 1-T_{n+1}} w_{T_{n+1}}(X_j) + w_{T_{n+1}}(X_{n+1})}$$

## Technical Assumptions

**A1 (Unconfoundedness):** $(Y(1), Y(0)) \perp T \mid X$, meaning treatment assignment is conditionally independent of potential outcomes given covariates.

**A2 (Overlap):** $0 < \pi(x) < 1$ for all $x$ in the support of $X$, ensuring both treatment and control observations exist across the covariate space.

**A3 (Absolute Continuity):** The covariate distribution in the control group is absolutely continuous with respect to that in the treated group (and vice versa), so likelihood ratios $w_t(x)$ are well-defined.

**A4 (Known or Estimable Weights):** Either the likelihood ratios $w_t(x)$ are known, or they can be estimated consistently using auxiliary unlabeled data or through density estimation methods.

These assumptions are standard in causal inference literature. A1 and A2 enable identification of treatment effects, while A3 and A4 are necessary for the weighted conformal procedure to correct for covariate shift between treatment groups.

## Connection to Prior Work

Standard conformal prediction (Vovk et al., 2005) assumes exchangeability between training and test data, which fails in our setting due to the fundamental problem of causal inference - we never observe both potential outcomes for any individual. Recent work on conformal prediction under covariate shift (Tibshirani et al., 2020) provides the key insight that importance weighting can maintain coverage guarantees when test and training covariate distributions differ.

However, existing approaches do not address the specific challenges of counterfactual prediction: (1) the "training data" for predicting $Y(1-t)$ consists only of subjects who received treatment $1-t$, creating an inherent covariate shift problem; (2) we cannot directly observe residuals for the quantity of interest $Y(1) - Y(0)$; and (3) the weighting mechanism naturally connects to causal inference through the propensity score.

Our formulation extends weighted conformal prediction to handle counterfactual outcomes by recognizing that predicting $Y_{n+1}(1-T_{n+1})$ is equivalent to a covariate shift problem where the likelihood ratio $w_{T_{n+1}}(x)$ corrects for the distributional mismatch between the target individual and the training subjects who received the alternative treatment. This provides a principled framework for uncertainty quantification in causal inference that maintains finite-sample validity without strong parametric assumptions.