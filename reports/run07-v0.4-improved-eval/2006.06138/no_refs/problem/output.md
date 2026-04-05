# Reconstruction: problem
**Paper:** 2006.06138  
**Condition:** no_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Problem Formulation

## 2.1 Notation and Setup

We consider the potential outcomes framework for causal inference. Let $X \in \mathcal{X} \subseteq \mathbb{R}^d$ denote a $d$-dimensional covariate vector, $T \in \{0,1\}$ a binary treatment assignment, and $Y \in \mathcal{Y} \subseteq \mathbb{R}$ a real-valued outcome. For each unit, we define potential outcomes $Y(0)$ and $Y(1)$ representing the outcomes that would be observed under control and treatment, respectively. The observed outcome is $Y = TY(1) + (1-T)Y(0)$.

The conditional average treatment effect (CATE) function is defined as:
$$\tau(x) = \mathbb{E}[Y(1) - Y(0) \mid X = x]$$

Let $P$ denote the joint distribution of $(X, T, Y)$ in the study population, and let $Q$ denote the marginal distribution of covariates $X$ in a potentially different target population of interest. We observe a dataset $\mathcal{D} = \{(X_i, T_i, Y_i)\}_{i=1}^n$ drawn i.i.d. from $P$.

For uncertainty quantification, we seek to construct prediction intervals $\mathcal{C}_\alpha(x) = [L_\alpha(x), U_\alpha(x)]$ for the CATE $\tau(x)$ at a given significance level $\alpha \in (0,1)$, where $L_\alpha$ and $U_\alpha$ are functions learned from the data.

## 2.2 Problem Statement

**Given:** 
- A dataset $\mathcal{D} = \{(X_i, T_i, Y_i)\}_{i=1}^n$ sampled from distribution $P$
- A target covariate distribution $Q$ (which may differ from the marginal of $X$ under $P$)
- A miscoverage level $\alpha \in (0,1)$

**Find:** Functions $L_\alpha, U_\alpha : \mathcal{X} \to \mathbb{R}$ such that the prediction intervals $\mathcal{C}_\alpha(x) = [L_\alpha(x), U_\alpha(x)]$ satisfy finite-sample coverage guarantees.

**Guarantee:** The primary objective is to ensure that for a new unit with covariates $X \sim Q$, the prediction interval contains the true CATE with high probability:
$$\mathbb{P}_{X \sim Q}[\tau(X) \in \mathcal{C}_\alpha(X)] \geq 1 - \alpha$$

This guarantee should hold in finite samples without requiring asymptotic approximations or strong parametric assumptions about the outcome models.

## 2.3 Technical Challenges

The fundamental challenge in this problem is the **missing counterfactual problem**: for any individual unit $i$, we observe only one potential outcome $Y_i(T_i)$, never both $Y_i(1)$ and $Y_i(0)$. This creates several layers of uncertainty:

1. **Model uncertainty**: Any estimator $\hat{\tau}(x)$ relies on models for $\mathbb{E}[Y(1)|X=x]$ and $\mathbb{E}[Y(0)|X=x]$, which may be misspecified.

2. **Sampling uncertainty**: Even with correct models, finite sample effects introduce variability.

3. **Covariate shift**: The target distribution $Q$ may differ from the study population's covariate distribution.

Unlike standard regression problems where prediction intervals can be constructed by modeling the conditional distribution $Y|X$, CATE estimation requires simultaneous inference about two conditional expectations that cannot be jointly observed for any individual.

## 2.4 Assumptions

We make the following standard assumptions in causal inference:

**A1 (Consistency):** $Y = TY(1) + (1-T)Y(0)$ for all units.

**A2 (Unconfoundedness):** $(Y(0), Y(1)) \perp T \mid X$, i.e., treatment assignment is conditionally independent of potential outcomes given covariates.

**A3 (Overlap):** There exist constants $c, C \in (0,1)$ such that $c \leq e(x) \leq C$ for all $x \in \mathcal{X}$, where $e(x) = \mathbb{P}[T=1|X=x]$ is the propensity score.

**A4 (Bounded outcomes):** $|Y(0)|, |Y(1)| \leq M$ almost surely for some constant $M < \infty$.

Assumptions A1-A3 are standard for causal inference and ensure identification of causal effects. A2 is satisfied by design in randomized experiments but requires careful justification in observational studies. A4 provides technical convenience and can often be achieved through outcome transformations.

## 2.5 Relationship to Prior Work

Traditional approaches to CATE estimation focus on point estimation using methods such as T-learners, S-learners, or more sophisticated techniques like causal forests and targeted maximum likelihood estimation. However, these methods typically provide uncertainty quantification through asymptotic normality assumptions that may not hold in finite samples, particularly when using flexible machine learning algorithms.

Existing uncertainty quantification approaches suffer from several limitations:

1. **Asymptotic guarantees**: Methods based on influence functions or bootstrap require large sample approximations that may be poor in practice.

2. **Parametric assumptions**: Confidence intervals derived from likelihood-based methods assume correct model specification.

3. **Double robustness limitations**: While some estimators achieve point-wise consistency under weaker assumptions, their uncertainty quantification often requires stronger conditions.

Our formulation addresses these gaps by seeking finite-sample coverage guarantees that are robust to model misspecification and do not rely on asymptotic approximations. This connects to recent developments in conformal prediction, which provides distribution-free uncertainty quantification, but extends these ideas to the more challenging setting of causal inference where the target quantity (individual treatment effects) is never directly observed.

The key insight is that while individual treatment effects cannot be observed, we can leverage the exchangeability of units and careful calibration procedures to provide valid uncertainty quantification even in this challenging setting.
