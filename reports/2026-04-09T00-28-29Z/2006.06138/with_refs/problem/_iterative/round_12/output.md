# Problem Formulation

## 2.1 Notation and Setup

Let $(\mathcal{X}, \mathcal{Y}, \mathcal{T})$ denote the covariate, outcome, and treatment spaces, where $\mathcal{X} \subseteq \mathbb{R}^d$, $\mathcal{Y} \subseteq \mathbb{R}$, and $\mathcal{T} = \{0, 1\}$. We observe $n$ i.i.d. samples $(X_i, Y_i, T_i)_{i=1}^n$ drawn from some unknown joint distribution $P$. For each unit $i$, we observe the covariate vector $X_i \in \mathcal{X}$, the treatment assignment $T_i \in \{0, 1\}$, and the realized outcome $Y_i \in \mathcal{Y}$ under the assigned treatment.

Following the potential outcomes framework, let $Y_i(0)$ and $Y_i(1)$ denote the potential outcomes for unit $i$ under control and treatment, respectively. We observe $Y_i = T_i Y_i(1) + (1 - T_i) Y_i(0)$, but never both potential outcomes simultaneously. The individual treatment effect for unit $i$ is defined as $\tau_i = Y_i(1) - Y_i(0)$.

For a new unit with covariates $X_{n+1}$, our goal is to construct a prediction interval $\mathcal{C}_n(X_{n+1}) \subseteq \mathcal{Y}$ that contains the unobserved counterfactual outcome with high probability. Specifically, if the new unit receives treatment $T_{n+1} = t$, we seek to provide uncertainty quantification for the counterfactual outcome $Y_{n+1}(1-t)$ that would have been observed under the opposite treatment.

Let $\pi(x) = P(T = 1 | X = x)$ denote the propensity score, and define the inverse probability weights $w_t(x) = \frac{\mathbf{1}\{T = t\}}{\pi(x)^t (1-\pi(x))^{1-t}}$ for $t \in \{0, 1\}$. For observational studies, we assume access to either the true propensity scores or consistent estimates $\hat{\pi}(x)$.

## 2.2 Problem Statement

**Given:** 
- Training data $\mathcal{D}_n = \{(X_i, Y_i, T_i)\}_{i=1}^n$ drawn i.i.d. from distribution $P$
- A new covariate vector $X_{n+1}$ 
- A target coverage level $1 - \alpha$ for $\alpha \in (0, 1)$
- Propensity scores $\pi(x)$ or estimates $\hat{\pi}(x)$

**Find:** A prediction set construction $\mathcal{C}_n: \mathcal{X} \to 2^{\mathcal{Y}}$ such that for any treatment assignment $T_{n+1} = t$:

$$P\left(Y_{n+1}(1-t) \in \mathcal{C}_n(X_{n+1}) \right) \geq 1 - \alpha$$

where the probability is taken over the randomness in both the training data $\mathcal{D}_n$ and the test point $(X_{n+1}, Y_{n+1}(0), Y_{n+1}(1))$.

## 2.3 Weighted Conformal Objective

Our approach extends conformal prediction to handle the distributional mismatch between treated and control populations. For a given target population (e.g., the treated units when predicting $Y_{n+1}(0)$), we construct weighted prediction intervals using the conformal framework.

Let $S: \mathcal{X} \times \mathcal{Y} \times \mathcal{D}_n \to \mathbb{R}$ be a conformity score function that measures how typical a point $(x, y)$ is relative to the training data. For predicting the counterfactual outcome $Y_{n+1}(1-t)$ for a unit that received treatment $t$, we define weighted nonconformity scores:

$$V_i^{(t)}(x, y) = S(X_i, Y_i, \mathcal{D}_n) \cdot w_{1-t}(X_i) \cdot \mathbf{1}\{T_i = 1-t\}$$

for $i = 1, \ldots, n$, and 

$$V_{n+1}^{(t)}(x, y) = S(x, y, \mathcal{D}_n \cup \{(x, y)\}) \cdot w_{1-t}(x)$$

The prediction interval is then constructed as:

$$\mathcal{C}_n(x) = \left\{y \in \mathcal{Y} : V_{n+1}^{(t)}(x, y) \leq \text{Quantile}\left(1-\alpha; \sum_{i=1}^n \tilde{w}_i^{(t)}(x) \delta_{V_i^{(t)}(x,y)} + \tilde{w}_{n+1}^{(t)}(x) \delta_{\infty}\right)\right\}$$

where the normalized weights are:
$$\tilde{w}_i^{(t)}(x) = \frac{w_{1-t}(X_i) \mathbf{1}\{T_i = 1-t\}}{\sum_{j=1}^n w_{1-t}(X_j) \mathbf{1}\{T_j = 1-t\} + w_{1-t}(x)}, \quad \tilde{w}_{n+1}^{(t)}(x) = \frac{w_{1-t}(x)}{\sum_{j=1}^n w_{1-t}(X_j) \mathbf{1}\{T_j = 1-t\} + w_{1-t}(x)}$$

## 2.4 Technical Assumptions

**Assumption 1 (Unconfoundedness):** For observational studies, we assume $(Y(0), Y(1)) \perp T | X$, i.e., treatment assignment is unconfounded given observed covariates.

**Assumption 2 (Overlap):** There exist constants $0 < c_1 < c_2 < 1$ such that $c_1 \leq \pi(x) \leq c_2$ for all $x \in \mathcal{X}$. This ensures that both treatment groups are represented across the covariate space and prevents extreme weights.

**Assumption 3 (Exchangeability):** The augmented data $(X_1, Y_1(0), Y_1(1)), \ldots, (X_n, Y_n(0), Y_n(1)), (X_{n+1}, Y_{n+1}(0), Y_{n+1}(1))$ are exchangeable under the complete data distribution (before treatment assignment).

**Assumption 4 (Score Function):** The conformity score function $S$ is permutation-invariant with respect to the training data ordering and satisfies basic measurability conditions.

These assumptions are standard in the causal inference literature. Assumption 1 enables causal identification, Assumption 2 ensures finite variance of the inverse probability weights, Assumption 3 allows application of conformal prediction theory, and Assumption 4 ensures the validity of the conformal procedure.

## 2.5 Connection to Prior Work

Our formulation addresses a fundamental gap in existing approaches. Traditional conformal prediction methods \citep{tibshirani2020conformal} assume exchangeability between training and test data, which fails in causal settings where we seek to predict counterfactual outcomes for populations with different covariate distributions than the training data from the opposite treatment group.

Previous work on conformal prediction for individual treatment effects \citep{kivaranovic2020conformal} focuses on constructing intervals for the treatment effect $\tau = Y(1) - Y(0)$ itself, but does not address the fundamental distributional mismatch problem when predicting counterfactual outcomes. Their approach requires combining separate prediction intervals for $Y(1)$ and $Y(0)$, leading to conservative intervals that do not account for the covariate shift between treatment groups.

Our weighted conformal approach recognizes that the same inverse probability weights used for causal identification naturally solve the distributional mismatch problem. By reweighting the conformity scores from the control group to match the treated population distribution (or vice versa), we ensure that the empirical quantiles used in conformal prediction are computed on a population that matches the target population for inference. This connection between causal identification and distribution-free prediction provides both theoretical elegance and practical improvements in interval efficiency.

The proposed method extends the covariate shift framework of \citet{tibshirani2020conformal} to the causal inference setting, where the "likelihood ratio" between populations is naturally given by the inverse probability weights rather than requiring separate estimation of density ratios.