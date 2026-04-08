# Problem Formulation

## 2.1 Notation and Setup

Let $\mathcal{X} \subseteq \mathbb{R}^d$ denote the covariate space and $\mathcal{Y} \subseteq \mathbb{R}$ the outcome space. We consider the potential outcomes framework where each unit $i$ has two potential outcomes: $Y_i(1)$ under treatment and $Y_i(0)$ under control. The observed outcome is $Y_i = T_i Y_i(1) + (1-T_i) Y_i(0)$, where $T_i \in \{0,1\}$ is the treatment assignment indicator. Let $X_i \in \mathcal{X}$ denote the covariate vector for unit $i$.

For any $x \in \mathcal{X}$, the conditional average treatment effect (CATE) is defined as:
$$\tau(x) = \mathbb{E}[Y(1) - Y(0) \mid X = x]$$

We observe training data $\mathcal{D}_n = \{(X_i, T_i, Y_i)\}_{i=1}^n$ from either a randomized experiment or observational study. Our goal is to construct prediction intervals for the CATE at new covariate values that provide valid uncertainty quantification.

Let $P$ denote the joint distribution of $(X, T, Y)$ in the training population and $\tilde{P}$ the distribution in the target population where we wish to make predictions. We allow for covariate shift between these populations, meaning $P_X \neq \tilde{P}_X$ while maintaining $P_{Y|X,T} = \tilde{P}_{Y|X,T}$.

## 2.2 Problem Statement

**Given:** Training data $\mathcal{D}_n = \{(X_i, T_i, Y_i)\}_{i=1}^n$ and a new covariate point $X_{n+1}$ from the target population.

**Find:** A prediction interval $C_n(X_{n+1}) \subseteq \mathbb{R}$ such that for a specified coverage level $1-\alpha \in (0,1)$:
$$\mathbb{P}[\tau(X_{n+1}) \in C_n(X_{n+1})] \geq 1-\alpha$$

**Key Challenge:** Unlike standard prediction problems where we can observe $Y_{n+1}$ to validate our intervals, the true CATE $\tau(X_{n+1})$ is never directly observable since it represents the difference between two potential outcomes, only one of which can be realized for any individual.

## 2.3 Formal Objective

We seek to construct a conformal prediction framework that produces intervals $C_n(\cdot)$ satisfying:

1. **Finite-sample validity:** The coverage guarantee holds for any finite sample size $n$, without requiring asymptotic approximations.

2. **Distribution-free property:** The coverage guarantee holds regardless of the underlying data generating process, without parametric modeling assumptions.

3. **Covariate shift robustness:** When the training and target populations differ in covariate distribution, the intervals maintain valid coverage through appropriate reweighting.

Formally, we aim to construct $C_n(X_{n+1})$ as a function of $\mathcal{D}_n$ and $X_{n+1}$ such that:
$$\inf_{P \in \mathcal{P}} \mathbb{P}_P[\tau(X_{n+1}) \in C_n(X_{n+1})] \geq 1-\alpha$$
where $\mathcal{P}$ represents the class of all distributions satisfying our stated assumptions.

## 2.4 Technical Assumptions

**A1 (Causal Identification):** For randomized experiments, treatment assignment is independent of potential outcomes: $(Y(0), Y(1)) \perp T \mid X$. For observational studies, we assume unconfoundedness: $(Y(0), Y(1)) \perp T \mid X$ and overlap: $0 < \mathbb{P}[T=1 \mid X=x] < 1$ for all $x$ in the support of $X$.

**A2 (Covariate Shift Structure):** The training data $(X_i, T_i, Y_i)_{i=1}^n$ are i.i.d. from distribution $P$, and the target point $(X_{n+1}, T_{n+1}, Y_{n+1})$ is drawn from $\tilde{P}$ where $P_{Y|X,T} = \tilde{P}_{Y|X,T}$ but potentially $P_X \neq \tilde{P}_X$.

**A3 (Likelihood Ratio Access):** When covariate shift is present, we assume access to the likelihood ratio $w(x) = d\tilde{P}_X(x)/dP_X(x)$ either exactly or through accurate estimation using auxiliary unlabeled data from the target population.

**A4 (Pseudo-outcome Construction):** We assume access to a method for constructing pseudo-outcomes $\hat{\tau}_i$ that serve as proxies for the unobservable individual treatment effects. These may be derived from methods such as T-learner, S-learner, or doubly robust estimation.

## 2.5 Connection to Prior Work

Our formulation extends conformal prediction methodology beyond its traditional scope in several key ways. Standard conformal prediction (Vovk et al., 2005) assumes exchangeability of training and test data and focuses on predicting directly observable outcomes. Recent work on conformal prediction under covariate shift (Tibshirani et al., 2020) addresses distribution mismatch but still concerns observable quantities.

The causal inference literature has developed numerous methods for CATE estimation (Künzel et al., 2019; Nie & Wager, 2021) but typically relies on asymptotic theory for uncertainty quantification. Existing approaches often assume correct model specification or require large sample sizes for valid inference.

**Key Gap:** No existing method provides finite-sample, distribution-free prediction intervals for conditional average treatment effects that remain valid under covariate shift and model misspecification. Our formulation addresses this gap by adapting weighted conformal prediction to the unique challenges of causal effect estimation, where the target quantity $\tau(x)$ is never directly observable and must be inferred through pseudo-outcomes constructed from the observed data.

The fundamental innovation lies in recognizing that while individual treatment effects are unobservable, we can still apply conformal prediction principles by carefully constructing conformity scores based on pseudo-outcomes and appropriately weighting them to account for both the causal estimation uncertainty and potential covariate distribution shifts.