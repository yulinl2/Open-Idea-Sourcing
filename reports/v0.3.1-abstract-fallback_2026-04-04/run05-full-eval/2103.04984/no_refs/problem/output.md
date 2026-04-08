# Reconstruction: problem
**Paper:** 2103.04984  
**Condition:** no_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Problem Formulation

## 2.1 Setup and Notation

We consider the potential outcomes framework for causal inference. Let $X \in \mathcal{X} \subseteq \mathbb{R}^d$ denote a vector of pre-treatment covariates, $T \in \{0,1\}$ a binary treatment indicator, and $Y(t) \in \mathbb{R}$ the potential outcome under treatment $t$. The observed outcome is $Y = TY(1) + (1-T)Y(0)$. The individual treatment effect (ITE) for a unit with covariates $x$ is defined as $\tau(x) = Y(1) - Y(0)$.

Let $P$ denote the joint distribution of $(X, T, Y(0), Y(1))$ in the study population, and let $\{(X_i, T_i, Y_i)\}_{i=1}^n$ be an i.i.d. sample from the marginal distribution of $(X, T, Y)$. We distinguish between two inferential settings:

**Within-study inference**: For a subject $i$ in the study sample with observed $(X_i, T_i, Y_i)$, construct a prediction interval for the unobserved counterfactual $Y_i(1-T_i)$.

**Out-of-study inference**: For a new subject with covariates $X_{new}$ drawn from a potentially different distribution $Q$, construct prediction intervals for $Y_{new}(0)$, $Y_{new}(1)$, or $\tau(X_{new})$.

## 2.2 Formal Problem Statement

**Given**: 
- A dataset $\mathcal{D}_n = \{(X_i, T_i, Y_i)\}_{i=1}^n$ 
- A target coverage level $1-\alpha$ for $\alpha \in (0,1)$
- A query point $x \in \mathcal{X}$ (either from the study sample or a new subject)

**Find**: Prediction intervals $C_0(x), C_1(x) \subset \mathbb{R}$ such that for the corresponding potential outcomes $Y(0), Y(1)$:

$$P(Y(t) \in C_t(x) \mid X = x) \geq 1-\alpha \quad \text{for } t \in \{0,1\}$$

with the probability taken over the randomness in $\mathcal{D}_n$ and, when applicable, the distribution of new subjects.

For treatment effect inference, we seek an interval $C_\tau(x)$ such that:
$$P(\tau(x) \in C_\tau(x)) \geq 1-\alpha$$

## 2.3 Coverage Requirements

We require **marginal coverage** guarantees that hold in finite samples without asymptotic approximations. Specifically, for any fixed $x$:

$$\inf_{P \in \mathcal{P}} P(Y(t) \in C_t(x) \mid X = x) \geq 1-\alpha$$

where $\mathcal{P}$ is the class of distributions satisfying our assumptions. For randomized experiments, we seek **exact coverage** where the inequality becomes an equality.

The coverage guarantee must be **distribution-free** in the sense that it holds without parametric assumptions on the outcome distributions $Y(t) \mid X$, and **model-agnostic** in that it remains valid when machine learning methods are used for nuisance parameter estimation.

## 2.4 Technical Assumptions

**Assumption 1 (SUTVA)**: The Stable Unit Treatment Value Assumption holds: there are no interference effects between units and treatment variations are irrelevant.

**Assumption 2 (Overlap)**: For observational studies, we assume $\eta \leq e(x) \leq 1-\eta$ for some $\eta > 0$ and all $x \in \mathcal{X}$, where $e(x) = P(T=1 \mid X=x)$ is the propensity score. For randomized experiments, $e(x)$ is known by design.

**Assumption 3 (Unconfoundedness)**: For observational studies, $(Y(0), Y(1)) \perp T \mid X$. For randomized experiments, this holds by design.

**Assumption 4 (Exchangeability)**: The study sample is exchangeable, allowing for the application of conformal prediction principles.

These assumptions are standard in the causal inference literature. Assumption 1 enables the potential outcomes framework, Assumption 2 ensures identifiability, Assumption 3 enables causal identification from observational data, and Assumption 4 is minimal for finite-sample inference.

## 2.5 Connection to Prior Work and Gaps

Existing approaches to uncertainty quantification in causal inference suffer from several limitations. Classical parametric methods rely on strong distributional assumptions that are rarely satisfied in practice. Bootstrap-based approaches provide asymptotic coverage but may fail in finite samples, particularly when using flexible machine learning methods that can overfit.

Recent work on conformal prediction has shown promise for providing distribution-free prediction intervals, but its application to causal inference faces unique challenges. Standard conformal methods assume access to i.i.d. data from the target distribution, which is violated in causal settings where we seek to predict counterfactuals or generalize across populations.

The key gaps our formulation addresses are:

1. **Counterfactual prediction**: Existing conformal methods cannot directly handle the fundamental problem of causal inference where counterfactuals are never observed.

2. **Doubly robust coverage**: Current methods lack robustness to misspecification of either propensity score or outcome models when both are estimated.

3. **Covariate shift**: Standard approaches fail when the target population differs from the study population.

4. **Treatment effect intervals**: Constructing valid intervals for $\tau(x) = Y(1) - Y(0)$ requires careful handling of dependence between the two potential outcomes.

Our formulation seeks prediction intervals that maintain valid coverage under these challenging conditions while leveraging the flexibility of modern machine learning methods for nuisance parameter estimation.
