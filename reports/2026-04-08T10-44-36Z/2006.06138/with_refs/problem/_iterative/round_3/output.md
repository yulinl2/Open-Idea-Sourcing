# Problem Formulation

## 2.1 Notation and Setup

Let $\mathcal{X} \subseteq \mathbb{R}^d$ denote the covariate space and $\mathcal{Y} \subseteq \mathbb{R}$ the outcome space. Consider a random triple $(X, T, Y)$ where $X \in \mathcal{X}$ represents baseline covariates, $T \in \{0,1\}$ is a binary treatment indicator, and $Y \in \mathcal{Y}$ is the observed outcome. We adopt the potential outcomes framework where each unit has two potential outcomes: $Y(1)$ under treatment and $Y(0)$ under control. The observed outcome satisfies $Y = TY(1) + (1-T)Y(0)$.

The individual treatment effect (ITE) for a unit with covariates $x$ is defined as:
$$\tau(x) = Y(1) - Y(0)$$

This quantity is fundamentally unobservable since we can only observe one potential outcome for each unit. Our goal is to construct prediction intervals for $\tau(x)$ that provide reliable uncertainty quantification.

Let $P$ denote the joint distribution of $(X, T, Y)$, and define the conditional outcome distributions as $P_{Y|X,T=t}(\cdot|x)$ for $t \in \{0,1\}$. We observe an i.i.d. sample $\mathcal{D}_n = \{(X_i, T_i, Y_i)\}_{i=1}^n$ drawn from $P$.

## 2.2 The Covariate Shift Challenge

A fundamental challenge in constructing prediction intervals for ITEs arises from the distributional mismatch between treatment groups. Let $P_{X|T=1}$ and $P_{X|T=0}$ denote the marginal covariate distributions in the treated and control groups, respectively. In observational studies, and even in randomized experiments with imbalanced designs, these distributions typically differ: $P_{X|T=1} \neq P_{X|T=0}$.

This creates a covariate shift problem when applying standard distribution-free prediction methods. For a new unit with covariates $x$, we need to predict both $Y(1)$ and $Y(0)$, but the training data for these predictions comes from different covariate distributions. Specifically:
- To predict $Y(1)$, we use data from treated units with distribution $P_{X|T=1}$
- To predict $Y(0)$, we use data from control units with distribution $P_{X|T=0}$

Standard conformal prediction methods assume exchangeability between training and test data, which is violated when the target covariate $x$ comes from a different distribution than the training covariates for each treatment group.

## 2.3 Problem Statement

**Given:** An i.i.d. sample $\mathcal{D}_n = \{(X_i, T_i, Y_i)\}_{i=1}^n$ from distribution $P$, a target covariate vector $x \in \mathcal{X}$, and a miscoverage level $\alpha \in (0,1)$.

**Find:** A prediction interval $\mathcal{C}_n(x) = [L_n(x), U_n(x)]$ such that:
$$\mathbb{P}(\tau(x) \in \mathcal{C}_n(x)) \geq 1 - \alpha$$

**Constraints:**
1. The interval should provide finite-sample coverage guarantees without asymptotic approximations
2. The method should be distribution-free, requiring minimal assumptions about the data generating process
3. The procedure should handle covariate shift between treatment groups
4. The method should work for both units within the study population and new units from potentially different populations

## 2.4 Formal Objective

We seek to construct a mapping $\Psi: (\mathbb{R}^d \times \{0,1\} \times \mathbb{R})^n \times \mathbb{R}^d \times (0,1) \rightarrow \mathbb{R}^2$ such that:

$$\Psi(\mathcal{D}_n, x, \alpha) = (L_n(x), U_n(x))$$

with the coverage guarantee:
$$\inf_{P \in \mathcal{P}} \mathbb{P}_P(\tau(x) \in [L_n(x), U_n(x)]) \geq 1 - \alpha$$

where $\mathcal{P}$ is the class of distributions satisfying our assumptions (specified below).

The secondary objective is to minimize the expected interval width:
$$\mathbb{E}[U_n(x) - L_n(x)]$$
subject to the coverage constraint.

## 2.5 Key Assumptions

**A1 (Exchangeability within treatment groups):** Conditional on treatment assignment, the units are exchangeable:
$$(X_i, Y_i) \mid T_i = t \stackrel{d}{=} (X_j, Y_j) \mid T_j = t \quad \forall i,j, t \in \{0,1\}$$

**A2 (Unconfoundedness):** Treatment assignment is unconfounded given observed covariates:
$$Y(1), Y(0) \perp T \mid X$$

**A3 (Overlap):** There exists $\eta > 0$ such that:
$$\eta \leq \mathbb{P}(T = 1 \mid X = x) \leq 1 - \eta \quad \text{for all } x \in \mathcal{X}$$

**A4 (SUTVA):** The Stable Unit Treatment Value Assumption holds, meaning no interference between units and treatment variation irrelevance.

**Justification:** A1 enables the application of conformal prediction within each treatment group. A2 ensures that the conditional outcome distributions identify the causal effects of interest. A3 guarantees that we have sufficient overlap to estimate both potential outcomes. A4 is standard in causal inference to ensure well-defined potential outcomes.

## 2.6 Connection to Prior Work

Existing approaches to ITE uncertainty quantification fall into several categories, each with significant limitations:

**Asymptotic methods** rely on central limit theorems and delta method approximations, providing confidence intervals for the conditional average treatment effect $\mathbb{E}[\tau(x) \mid X = x]$ rather than prediction intervals for the individual effect $\tau(x)$. These methods fail to account for the irreducible uncertainty in individual responses.

**Bayesian approaches** require strong prior specifications and computational approximations that may not provide finite-sample guarantees. The posterior intervals depend heavily on modeling assumptions that are difficult to verify.

**Standard conformal prediction** has been developed for supervised learning settings where training and test data are exchangeable. Direct application to causal inference fails because of the covariate shift between treatment groups, as noted in Kivaranovic et al. (2020), who address this through conservative Bonferroni-type corrections that can be overly wide.

**Our contribution** addresses the covariate shift problem directly by developing distribution-free methods that account for the different covariate distributions across treatment groups while maintaining finite-sample coverage guarantees. This requires novel theoretical analysis of how conformal prediction can be adapted when the exchangeability assumption is violated due to the fundamental structure of the causal inference problem.

The key insight is that while we cannot achieve exchangeability between the full training set and test data, we can leverage the conditional exchangeability within treatment groups along with appropriate reweighting techniques to construct valid prediction intervals that properly account for both the estimation uncertainty and the irreducible variability in individual treatment effects.