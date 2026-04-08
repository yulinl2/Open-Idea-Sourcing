# Problem Formulation

## 2.1 Setup and Notation

We consider the fundamental problem of causal inference where we observe data from a randomized experiment or observational study. Let $\mathcal{X} \subseteq \mathbb{R}^d$ denote the covariate space and $\mathcal{Y} \subseteq \mathbb{R}$ the outcome space. For each unit $i$, we observe a triple $(X_i, T_i, Y_i)$ where $X_i \in \mathcal{X}$ represents covariates, $T_i \in \{0,1\}$ indicates treatment assignment (with $T_i = 1$ for treatment and $T_i = 0$ for control), and $Y_i \in \mathcal{Y}$ is the observed outcome.

Under the potential outcomes framework, each unit $i$ has two potential outcomes: $Y_i(1)$ under treatment and $Y_i(0)$ under control. We observe $Y_i = T_i Y_i(1) + (1-T_i) Y_i(0)$, while the counterfactual outcome $Y_i(1-T_i)$ remains unobserved. The individual treatment effect (ITE) for unit $i$ is defined as:
$$\tau_i = Y_i(1) - Y_i(0)$$

Let $\mathbb{P}$ denote the joint distribution of $(X, T, Y(0), Y(1))$ and $\mathbb{P}_X$ the marginal distribution of covariates $X$. We denote by $e(x) = \mathbb{P}(T=1|X=x)$ the propensity score and define the conditional outcome distributions $\mathbb{P}_{Y|X,T}(\cdot|x,t) = \mathbb{P}(Y \in \cdot | X=x, T=t)$ for $t \in \{0,1\}$.

## 2.2 Problem Statement

Given a training dataset $\mathcal{D}_n = \{(X_i, T_i, Y_i)\}_{i=1}^n$ drawn i.i.d. from $\mathbb{P}$, our goal is to construct prediction intervals for counterfactual outcomes that maintain valid coverage guarantees. Specifically, for a new unit with covariates $X_{n+1}$ and treatment assignment $T_{n+1}$, we seek to construct an interval $\mathcal{I}_n(X_{n+1}, 1-T_{n+1})$ such that:

$$\mathbb{P}\left(Y_{n+1}(1-T_{n+1}) \in \mathcal{I}_n(X_{n+1}, 1-T_{n+1}) \mid \mathcal{D}_n\right) \geq 1-\alpha$$

for a pre-specified miscoverage level $\alpha \in (0,1)$.

The fundamental challenge is that the target distribution for prediction differs from the training distribution due to covariate shift. When predicting $Y(1)$ for units assigned to control ($T=0$), we must account for the distributional mismatch between $\mathbb{P}_{X|T=0}$ (source) and $\mathbb{P}_{X|T=1}$ (target), and vice versa.

## 2.3 Distributional Mismatch and Importance Weighting

The core difficulty arises from the covariate shift between treated and control populations. For a unit with $T_{n+1} = 0$, we wish to predict $Y_{n+1}(1)$, but our training data for the treated outcome comes from the distribution $\mathbb{P}_{X|T=1}$, while the test unit's covariates follow $\mathbb{P}_{X|T=0}$.

To address this mismatch, we leverage importance weighting with likelihood ratios:
$$w(x,t) = \frac{d\mathbb{P}_{X|T=1-t}}{d\mathbb{P}_{X|T=t}}(x)$$

Under standard causal assumptions, these likelihood ratios have a natural connection to propensity scores:
$$w(x,0) = \frac{e(x)}{1-e(x)}, \quad w(x,1) = \frac{1-e(x)}{e(x)}$$

## 2.4 Formal Objective

We seek to construct prediction intervals $\mathcal{I}_n(x,t)$ that satisfy the following coverage guarantee:

**Primary Objective:** For any $\alpha \in (0,1)$ and $(x,t) \in \mathcal{X} \times \{0,1\}$:
$$\mathbb{P}(Y(t) \in \mathcal{I}_n(x,t)) \geq 1-\alpha$$

**Robustness Objective:** The coverage guarantee should degrade gracefully when key quantities are estimated imperfectly, maintaining validity under either of the following conditions:
1. The propensity score model $\hat{e}(x)$ is correctly specified
2. The outcome regression models $\hat{\mu}_t(x) = \mathbb{E}[Y(t)|X=x]$ are correctly specified

**Efficiency Objective:** Among all procedures satisfying the coverage constraint, minimize the expected interval width:
$$\mathbb{E}[\text{width}(\mathcal{I}_n(X,T))]$$

## 2.5 Technical Assumptions

We require the following assumptions for our theoretical guarantees:

**Assumption 1 (Exchangeability):** The training data $\{(X_i, T_i, Y_i)\}_{i=1}^n$ are exchangeable, and the test unit $(X_{n+1}, T_{n+1}, Y_{n+1})$ is exchangeable with the training data.

**Assumption 2 (Overlap):** There exist constants $0 < c_{\min} < c_{\max} < 1$ such that $c_{\min} \leq e(x) \leq c_{\max}$ for all $x$ in the support of $\mathbb{P}_X$.

**Assumption 3 (SUTVA):** The Stable Unit Treatment Value Assumption holds: potential outcomes for unit $i$ are unaffected by the treatment assignments of other units.

**Assumption 4 (Unconfoundedness):** $(Y(0), Y(1)) \perp T | X$, meaning treatment assignment is ignorable given observed covariates.

**Assumption 5 (Finite Moments):** For some $p > 2$, $\mathbb{E}[|Y(t)|^p | X] < \infty$ almost surely for $t \in \{0,1\}$.

Assumptions 1-3 are standard in the causal inference literature and enable identification of causal effects. Assumption 4 is the key identifying assumption that allows us to treat the problem as one of covariate shift rather than unmeasured confounding. Assumption 5 ensures well-behaved tail behavior for our distributional results.

## 2.6 Connection to Prior Work

Existing approaches to uncertainty quantification in causal inference typically fall into two categories. **Parametric methods** rely on strong distributional assumptions and asymptotic approximations that may fail in finite samples, particularly when treatment effects are heterogeneous or sample sizes are moderate. **Bootstrap-based approaches** can provide some finite-sample validity but often lack theoretical guarantees and may perform poorly under model misspecification.

Recent work by Kivaranovic et al. (2020) introduced conformal prediction methods for individual treatment effects, providing finite-sample coverage guarantees without distributional assumptions. However, their approach constructs separate prediction intervals for each treatment group and combines them using union bounds, leading to conservative intervals that may be unnecessarily wide.

Our formulation addresses a fundamental gap in this literature: **none of these approaches properly account for the covariate shift inherent in counterfactual prediction**. When constructing prediction intervals for $Y(1)$ using data from treated units to make predictions about control units (or vice versa), the distributional mismatch between $\mathbb{P}_{X|T=1}$ and $\mathbb{P}_{X|T=0}$ can lead to miscoverage even when the underlying prediction models are well-specified.

The key insight of our formulation is to leverage the natural connection between importance weighting for covariate shift correction and inverse probability weighting in causal inference. By incorporating propensity score-based weights into distribution-free prediction methods, we can maintain coverage guarantees while accounting for the distributional differences between treatment groups. This approach provides a principled framework for uncertainty quantification that is both theoretically grounded and practically implementable across a wide range of causal inference settings.