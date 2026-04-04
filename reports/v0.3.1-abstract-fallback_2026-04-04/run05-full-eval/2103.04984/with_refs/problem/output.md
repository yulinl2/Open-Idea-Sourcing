# Reconstruction: problem
**Paper:** 2103.04984  
**Condition:** with_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Problem Formulation

## Notation and Setup

Let $(\mathcal{X}, \mathcal{Y}, \mathcal{T})$ denote the covariate, outcome, and treatment spaces, respectively, where $\mathcal{X} \subseteq \mathbb{R}^d$, $\mathcal{Y} \subseteq \mathbb{R}$, and $\mathcal{T} = \{0,1\}$. For each unit $i$, let $X_i \in \mathcal{X}$ represent observed covariates, $T_i \in \mathcal{T}$ the treatment assignment, and $Y_i \in \mathcal{Y}$ the observed outcome.

Following the potential outcomes framework, let $Y_i(1)$ and $Y_i(0)$ denote the potential outcomes under treatment and control, respectively. The observed outcome satisfies $Y_i = T_i Y_i(1) + (1-T_i) Y_i(0)$. The individual treatment effect (ITE) for unit $i$ is defined as $\tau_i = Y_i(1) - Y_i(0)$.

Let $P$ denote the joint distribution of $(X, Y(1), Y(0), T)$ for the study population, and let $Q$ denote the corresponding distribution for a potentially different target population. We observe a dataset $\mathcal{D}_n = \{(X_i, T_i, Y_i)\}_{i=1}^n$ drawn from $P$.

For a given unit with covariates $x$, define the conditional average treatment effect as:
$$\tau(x) = \mathbb{E}[Y(1) - Y(0) | X = x]$$

Our goal is to construct prediction intervals for counterfactual outcomes. Specifically, for a unit with covariates $x$ and observed outcome under treatment $t \in \{0,1\}$, we seek to predict the unobserved potential outcome $Y(1-t)$ with a prediction interval $C_{1-t}(x)$.

## Problem Statement

**Given**: A dataset $\mathcal{D}_n = \{(X_i, T_i, Y_i)\}_{i=1}^n$ from distribution $P$, a significance level $\alpha \in (0,1)$, and a target unit with covariates $x$ (either from $P$ or a shifted distribution $Q$).

**Find**: Prediction intervals $C_0(x)$ and $C_1(x)$ such that for any $t \in \{0,1\}$:
$$\mathbb{P}_{Y(1-t)|X=x}[Y(1-t) \in C_{1-t}(x)] \geq 1-\alpha$$

**Guarantee**: The coverage probability should hold in finite samples without requiring the correctness of any particular model for the outcome regression or propensity score.

We consider two distinct inferential scenarios:

1. **Within-study inference**: The target unit belongs to the study population ($x \sim P_X$), and we observe either $Y(1)$ or $Y(0)$ but seek to predict the counterfactual.

2. **Out-of-study inference**: The target unit belongs to a potentially shifted population ($x \sim Q_X$), and we seek to predict both potential outcomes.

## Objective

Our primary objective is to construct distribution-free prediction intervals that satisfy:

$$\inf_{P \in \mathcal{P}} \mathbb{P}_P[Y(1-t) \in C_{1-t}(X) | T = t] \geq 1-\alpha$$

where $\mathcal{P}$ represents the class of distributions satisfying our assumptions. For the covariate shift setting, we require:

$$\inf_{Q \in \mathcal{Q}} \mathbb{P}_Q[Y(1-t) \in C_{1-t}(X)] \geq 1-\alpha$$

where $\mathcal{Q}$ represents distributions that may differ from $P$ in their covariate distribution but share the same conditional outcome distributions.

The intervals should be constructed using only the observed data $\mathcal{D}_n$ and should remain valid regardless of the specific machine learning methods used to estimate nuisance parameters such as $\mathbb{E}[Y|X,T]$ and $\mathbb{P}[T=1|X]$.

## Assumptions

**A1 (Unconfoundedness)**: $(Y(1), Y(0)) \perp T | X$. Treatment assignment is conditionally independent of potential outcomes given observed covariates.

**A2 (Positivity)**: $\eta(x) \in (\epsilon, 1-\epsilon)$ for some $\epsilon > 0$ and all $x$ in the support of $X$, where $\eta(x) = \mathbb{P}[T=1|X=x]$ is the propensity score.

**A3 (SUTVA)**: The potential outcomes for unit $i$ do not depend on the treatment assignments of other units, and there are no hidden variations of treatments.

**A4 (Covariate shift)**: For out-of-study inference, we assume that while $P_X \neq Q_X$ may hold, the conditional distributions satisfy $P_{Y(t)|X} = Q_{Y(t)|X}$ for $t \in \{0,1\}$.

**A5 (Exchangeability)**: Within each treatment group, the units are exchangeable: $(X_i, Y_i(t))_{i: T_i = t}$ are exchangeable for $t \in \{0,1\}$.

Assumptions A1-A3 are standard for causal inference and ensure identifiability of causal effects. A4 allows for distribution shift in covariates while maintaining the relevance of the study population for inference about the target population. A5 enables the application of conformal prediction techniques within treatment groups.

## Connection to Prior Work

Standard conformal prediction methods \citep{vovk2005algorithmic} provide distribution-free prediction intervals but assume exchangeability of all observations, which is violated in causal inference settings due to the fundamental problem of causal inference. Existing approaches for uncertainty quantification in causal inference typically rely on asymptotic normality assumptions or parametric models \citep{kennedy2020optimal}, leading to poor finite-sample coverage when these assumptions fail.

Recent work on conformal prediction under covariate shift \citep{tibshirani2019conformal} addresses distribution shift but does not handle the missing data structure inherent in causal inference. Methods for estimating conditional average treatment effects often use cross-fitting and sample splitting \citep{chernozhukov2018double} but do not provide the finite-sample coverage guarantees that conformal methods offer.

The key gap addressed by our formulation is the lack of distribution-free, finite-sample valid prediction intervals for counterfactual outcomes that remain robust to model misspecification and can handle both within-study and out-of-study inference under covariate shift. Our approach must reconcile the exchangeability requirements of conformal prediction with the non-exchangeable structure induced by treatment assignment and missing counterfactuals.
