# Reconstruction: problem
**Paper:** 2006.06138  
**Condition:** no_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Problem Formulation

## Notation and Setup

Let $(\mathcal{X}, \mathcal{T}, \mathcal{Y})$ denote the covariate, treatment, and outcome spaces, respectively. For an individual with covariates $X \in \mathcal{X}$, let $T \in \mathcal{T} = \{0,1\}$ denote the binary treatment assignment, and let $Y \in \mathcal{Y} \subseteq \mathbb{R}$ denote the observed outcome. Following the potential outcomes framework, we define $Y(0)$ and $Y(1)$ as the potential outcomes under control and treatment, respectively, such that the observed outcome is $Y = TY(1) + (1-T)Y(0)$.

The individual treatment effect (ITE) for a unit with covariates $x$ is defined as:
$$\tau(x) = \mathbb{E}[Y(1) - Y(0) \mid X = x]$$

Let $P_{X,Y(0),Y(1)}$ denote the joint distribution over covariates and potential outcomes, and let $P_X$ denote the marginal distribution of covariates. We observe $n$ independent samples $\{(X_i, T_i, Y_i)\}_{i=1}^n$ drawn from the observational distribution, where treatment assignment may depend on covariates through the propensity score $e(x) = \mathbb{P}(T = 1 \mid X = x)$.

For uncertainty quantification, we seek to construct prediction intervals $\mathcal{C}_\alpha(x) = [L_\alpha(x), U_\alpha(x)]$ such that for a specified confidence level $1-\alpha \in (0,1)$:
$$\mathbb{P}(\tau(X) \in \mathcal{C}_\alpha(X)) \geq 1-\alpha$$
where the probability is taken over the distribution of a new individual's covariates $X \sim P_X$.

## Problem Statement

**Given:** 
- Observational data $\mathcal{D} = \{(X_i, T_i, Y_i)\}_{i=1}^n$ 
- Target confidence level $1-\alpha$
- Population distribution $P_X$ (which may differ from the empirical distribution)

**Find:** A procedure that constructs prediction intervals $\mathcal{C}_\alpha(x)$ for the individual treatment effect $\tau(x)$ such that the marginal coverage guarantee holds:
$$\mathbb{P}_{X \sim P_X}(\tau(X) \in \mathcal{C}_\alpha(X)) \geq 1-\alpha$$

**Constraints:** The procedure should satisfy this guarantee:
1. **Exactly** (not asymptotically) for any finite sample size $n$
2. **Distribution-free** without parametric assumptions on outcome distributions
3. **Model-agnostic** regardless of the complexity of $\tau(\cdot)$ or choice of base learner

## Objective and Formal Guarantee

The primary objective is to achieve **marginal coverage** while maintaining **efficiency**. Formally, we seek the shortest expected interval length among all procedures satisfying the coverage constraint:

$$\min_{\mathcal{C}_\alpha} \mathbb{E}_{X \sim P_X}[U_\alpha(X) - L_\alpha(X)]$$
$$\text{subject to } \mathbb{P}_{X \sim P_X}(\tau(X) \in \mathcal{C}_\alpha(X)) \geq 1-\alpha$$

The fundamental challenge arises from the **missing counterfactuals problem**: for each individual $i$, we observe either $Y_i(0)$ or $Y_i(1)$ but never both. This creates two sources of uncertainty:

1. **Epistemic uncertainty** from finite sample estimation of $\tau(x)$
2. **Aleatoric uncertainty** from inherent variability in potential outcomes

Unlike standard prediction intervals for directly observed quantities, ITE prediction intervals must account for the fact that $\tau(x)$ itself is never directly observable, even in the training data.

## Technical Assumptions

We require the following standard causal inference assumptions:

**Assumption 1 (SUTVA):** The Stable Unit Treatment Value Assumption holds, ensuring that potential outcomes for individual $i$ depend only on individual $i$'s treatment assignment.

**Assumption 2 (Unconfoundedness):** Treatment assignment is conditionally independent of potential outcomes given observed covariates:
$$(Y(0), Y(1)) \perp T \mid X$$

**Assumption 3 (Overlap):** The propensity score is bounded away from 0 and 1:
$$0 < \eta \leq e(x) \leq 1-\eta < 1$$
for some $\eta > 0$ and all $x$ in the support of $P_X$.

**Assumption 4 (Exchangeability):** The observed data $\{(X_i, T_i, Y_i)\}_{i=1}^n$ are exchangeable, and any future test point $(X, T, Y)$ is exchangeable with the training data.

These assumptions are standard in the causal inference literature and necessary for identifying individual treatment effects from observational data. Assumption 4 is crucial for conformal prediction methods and is weaker than requiring independent and identically distributed data.

## Connection to Prior Work and Gap Analysis

Existing approaches to heterogeneous treatment effect estimation fall into several categories, each with significant limitations for uncertainty quantification:

**Meta-learning approaches** such as T-learner, S-learner, and X-learner \cite{kunzel2019metalearners} provide point estimates of $\tau(x)$ but offer no principled uncertainty quantification. Bootstrap-based intervals from these methods lack finite-sample guarantees and can severely undercover due to bias in the base estimators.

**Causal forests and related ensemble methods** \cite{wager2018estimation} provide asymptotic confidence intervals under strong regularity conditions, but these guarantees may not hold in finite samples or under model misspecification. The coverage depends critically on the honesty condition and subsample sizes, making practical implementation challenging.

**Bayesian approaches** offer posterior credible intervals but require strong prior specifications and computational assumptions. The coverage properties depend heavily on prior choice and model correctness, providing no distribution-free guarantees.

**Conformal prediction** has emerged as a powerful framework for distribution-free uncertainty quantification \cite{vovk2005algorithmic,lei2018distribution}, but its application to causal inference presents unique challenges. Standard conformal methods assume access to true labels during calibration, which is impossible for ITEs due to the fundamental problem of causal inference.

The key gap addressed by this work is the lack of **finite-sample, distribution-free uncertainty quantification** for individual treatment effects. While recent work has begun exploring conformal prediction for causal inference, existing approaches either require strong modeling assumptions, fail to properly account for the missing counterfactuals problem, or provide only conditional rather than marginal coverage guarantees.

Our formulation explicitly addresses this gap by seeking procedures that provide exact finite-sample marginal coverage guarantees without parametric assumptions, while remaining robust to model misspecification in the underlying treatment effect estimation.
