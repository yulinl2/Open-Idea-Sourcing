# Problem Formulation

## 2.1 Notation and Setup

Let $(X, Y(1), Y(0))$ denote the potential outcomes framework, where $X \in \mathcal{X} \subseteq \mathbb{R}^d$ represents covariates, $Y(1)$ is the potential outcome under treatment, and $Y(0)$ is the potential outcome under control. The individual treatment effect is defined as $\tau(X) = Y(1) - Y(0)$. Let $T \in \{0,1\}$ denote the treatment assignment indicator, and define the observed outcome as $Y = TY(1) + (1-T)Y(0)$.

We observe training data $\{(X_i, T_i, Y_i)\}_{i=1}^n$ where $(X_i, T_i, Y_i)$ are i.i.d. draws from some distribution $P$. For a new subject with covariates $X_{n+1}$, we seek to construct a prediction interval for the counterfactual outcome $Y_{n+1}(1-T_{n+1})$ - that is, the outcome under the treatment condition opposite to what they would receive.

Let $P_X^{(t)}$ denote the marginal distribution of covariates among subjects with treatment assignment $T = t$, and let $\mu_t(x) = \mathbb{E}[Y(t)|X = x]$ denote the conditional mean function for potential outcome $t$. The propensity score is defined as $\pi(x) = P(T = 1|X = x)$.

## 2.2 Problem Statement

**Given:** Training data $\{(X_i, T_i, Y_i)\}_{i=1}^n$ and a new subject with covariates $X_{n+1}$ and treatment assignment $T_{n+1}$.

**Find:** A prediction interval $C_n(X_{n+1}, 1-T_{n+1})$ such that
$$P\left(Y_{n+1}(1-T_{n+1}) \in C_n(X_{n+1}, 1-T_{n+1})\right) \geq 1-\alpha$$
for a specified miscoverage level $\alpha \in (0,1)$.

**Key Challenge:** The fundamental difficulty is that we never observe both $Y_i(1)$ and $Y_i(0)$ for any individual $i$. Additionally, when predicting $Y_{n+1}(1-T_{n+1})$, there is a distributional mismatch: if $T_{n+1} = 1$, we seek to predict the control outcome, but our observed control outcomes come from subjects with $T_i = 0$, whose covariate distribution $P_X^{(0)}$ may differ from that of treated subjects $P_X^{(1)}$.

## 2.3 Objective and Approach

Our objective is to construct distribution-free prediction intervals that:

1. **Maintain finite-sample coverage** without asymptotic approximations
2. **Handle covariate shift** between treatment groups through importance weighting
3. **Leverage the connection** between inverse propensity weighting and covariate shift correction

We propose to use weighted conformal prediction with importance weights defined by the inverse propensity score. Specifically, for predicting $Y_{n+1}(0)$ when $T_{n+1} = 1$, we weight the nonconformity scores from the control group by
$$w_i = \frac{\pi(X_i)}{1-\pi(X_i)} \cdot \frac{1-\pi(X_{n+1})}{\pi(X_{n+1})}$$
where the first factor corrects for the covariate shift and the second normalizes relative to the target subject.

## 2.4 Technical Assumptions

**A1 (Unconfoundedness):** $(Y(1), Y(0)) \perp T | X$, meaning treatment assignment is conditionally independent of potential outcomes given covariates.

**A2 (Overlap):** There exist constants $c, C > 0$ such that $c \leq \pi(x) \leq C$ for all $x$ in the support of $X$.

**A3 (Exchangeability within groups):** Conditional on $T = t$, the pairs $(X_i, Y_i)$ with $T_i = t$ are exchangeable.

**A4 (Propensity score specification):** Either the propensity score $\pi(x)$ is known, or we have access to a consistent estimator $\hat{\pi}(x)$.

**Justification:** A1 is the standard identifying assumption for causal inference from observational data. A2 ensures that importance weights remain bounded, preventing extreme reweighting. A3 enables the application of conformal prediction within each treatment group. A4 is necessary for computing the importance weights, though our method provides robustness when this assumption is violated.

## 2.5 Connection to Prior Work

Our formulation extends the weighted conformal prediction framework of Tibshirani et al. (2020) to the causal inference setting. While their work addresses covariate shift in standard supervised learning, we face the additional challenge that the "target distribution" (subjects assigned to one treatment but for whom we want to predict the outcome under the opposite treatment) is not directly observable in the training data.

Previous work on uncertainty quantification for treatment effects (Kivaranovic et al., 2020) has focused on prediction intervals for the individual treatment effect $\tau(X) = Y(1) - Y(0)$. However, this requires constructing intervals for both potential outcomes simultaneously and typically yields conservative results. Our approach directly targets the counterfactual outcome of interest, potentially yielding tighter intervals.

The key insight connecting our work to the covariate shift literature is recognizing that the likelihood ratio between the covariate distribution of subjects assigned to treatment $t$ and those assigned to treatment $1-t$ is precisely $\frac{\pi(x)}{1-\pi(x)}$ (up to the direction of the ratio). This natural connection allows us to leverage importance weighting techniques while maintaining the finite-sample guarantees of conformal prediction.

Our formulation addresses a critical gap in the literature: while substantial work exists on point estimation of treatment effects and on conformal prediction under covariate shift separately, the intersection of these areas—providing rigorous uncertainty quantification for counterfactual predictions in the presence of treatment-induced covariate shift—has received limited attention.