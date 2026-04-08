# Problem Formulation

## 2.1 Notation and Setup

Let $\mathcal{X}$ denote the covariate space and $\mathcal{Y} \subset \mathbb{R}$ the outcome space. For each individual $i$ in our study population, we define the potential outcomes framework with $Y_i(1)$ and $Y_i(0)$ representing the potential outcomes under treatment and control, respectively. The observed treatment assignment is denoted by $T_i \in \{0,1\}$, and the observed outcome is $Y_i = T_i Y_i(1) + (1-T_i)Y_i(0)$. Let $X_i \in \mathcal{X}$ represent the observed covariates for individual $i$.

We observe data $\{(X_i, T_i, Y_i)\}_{i=1}^n$ from the study population, where each individual reveals exactly one potential outcome: treated units reveal $Y_i(1)$ while control units reveal $Y_i(0)$. The individual treatment effect (ITE) for unit $i$ is defined as $\tau_i = Y_i(1) - Y_i(0)$, which remains unobserved for all individuals since we never observe both potential outcomes simultaneously.

Let $P$ denote the joint distribution of $(X, T, Y(1), Y(0))$ in the study population, and let $\tilde{P}$ denote the corresponding distribution in a target population of interest (which may differ from the study population). We denote the marginal covariate distributions as $P_X$ and $\tilde{P}_X$ respectively.

## 2.2 Problem Statement

Our goal is to construct distribution-free prediction intervals for individual treatment effects that provide finite-sample coverage guarantees. Specifically, for a target individual with covariates $x \in \mathcal{X}$, we seek to construct an interval $\hat{C}_n(x) \subset \mathbb{R}$ such that

$$P\left(\tau(x) \in \hat{C}_n(x)\right) \geq 1 - \alpha$$

where $\tau(x) = E[Y(1) - Y(0) | X = x]$ represents the conditional average treatment effect at $x$, and the probability is taken over the randomness in the observed data $\{(X_i, T_i, Y_i)\}_{i=1}^n$.

The fundamental challenge is that unlike standard prediction problems, the target quantity $\tau_i$ is never directly observed. However, we observe one component of each individual's treatment effect: $Y_i(1)$ for treated units and $Y_i(0)$ for control units. This creates a structured missing data problem where the missingness pattern is determined by the treatment assignment mechanism.

## 2.3 Key Insight and Approach

The crucial observation is that the treatment assignment mechanism creates a known pattern of missingness in potential outcomes. For treated individuals ($T_i = 1$), we observe $Y_i(1)$ but not $Y_i(0)$, while for control individuals ($T_i = 0$), we observe $Y_i(0)$ but not $Y_i(1)$. This is fundamentally different from typical conformal prediction settings where the target variable is completely unobserved during calibration.

We leverage this structure by recognizing that nonconformity scores for treatment effects can be constructed using the observed potential outcomes, appropriately weighted to account for the treatment assignment probabilities. The key insight is that we can create pseudo-treatment effects by pairing observed outcomes from treated and control units, then use conformal prediction methodology adapted to this structured missingness pattern.

## 2.4 Formal Objective

We seek to construct a function $\hat{C}_n: \mathcal{X} \rightarrow 2^{\mathbb{R}}$ that maps covariates to prediction intervals such that:

1. **Marginal Coverage**: $P(\tau(X) \in \hat{C}_n(X)) \geq 1 - \alpha$ for individuals drawn from the study population
2. **Finite-Sample Validity**: The coverage guarantee holds for any finite sample size $n$, without asymptotic approximations
3. **Distribution-Free**: The guarantee holds without parametric assumptions on the outcome distributions or treatment effect heterogeneity
4. **Covariate Shift Robustness**: When the target population differs from the study population, coverage is maintained under known covariate shift

The prediction intervals should be constructed using a conformal prediction framework adapted to the causal inference setting, where the nonconformity scores are designed to leverage the observed potential outcomes.

## 2.5 Technical Assumptions

**Assumption 1 (Stable Unit Treatment Value)**: The potential outcomes for individual $i$ depend only on their own treatment assignment: $Y_i(t) = Y_i(t, \mathbf{T})$ for any treatment vector $\mathbf{T}$ where $T_i = t$.

**Assumption 2 (Unconfoundedness)**: Treatment assignment is conditionally independent of potential outcomes given observed covariates: $(Y(1), Y(0)) \perp T | X$.

**Assumption 3 (Overlap)**: There exists $\eta > 0$ such that $\eta \leq e(x) \leq 1-\eta$ for all $x$ in the support of $P_X$, where $e(x) = P(T = 1 | X = x)$ is the propensity score.

**Assumption 4 (Covariate Shift)**: When considering distribution shift, we assume $\tilde{P}_{Y(1),Y(0)|X} = P_{Y(1),Y(0)|X}$ (conditional outcome distributions are preserved) and the likelihood ratio $w(x) = d\tilde{P}_X/dP_X$ is known or can be accurately estimated.

These assumptions are standard in causal inference and ensure identifiability of treatment effects while providing the structure needed for our conformal prediction approach.

## 2.6 Connection to Prior Work

Our formulation extends conformal prediction methodology beyond the exchangeable data setting by recognizing that treatment assignment creates a specific non-exchangeable structure. Unlike Tibshirani et al. (2020), who address covariate shift in standard prediction problems, we face the additional challenge that our target quantity (individual treatment effects) is never directly observed.

While existing causal inference methods focus on point estimation of treatment effects, and traditional conformal prediction assumes the target variable is observable during calibration, our approach bridges these areas by providing uncertainty quantification for unobserved individual-level causal effects. The key innovation is adapting the conformal framework to leverage the partial observability of potential outcomes, creating a new class of problems where conformal prediction can be applied despite the target being fundamentally unobserved.

This formulation addresses a critical gap in the literature: existing methods either provide point estimates without reliable uncertainty quantification, or provide uncertainty quantification only for average effects rather than individual effects. Our approach provides the first distribution-free, finite-sample uncertainty quantification for individual treatment effects.