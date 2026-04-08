# Reconstruction: problem
**Paper:** 2006.06138  
**Condition:** with_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Problem Formulation

## Notation and Setup

Let $\mathcal{X}$ denote the input space and $\mathcal{Y}$ denote the output space. We consider prediction problems where the output consists of sets rather than single elements, so our target is to construct prediction sets $\hat{S} \subseteq \mathcal{Y}$. Let $(X, Y) \sim P$ denote a random pair where $X \in \mathcal{X}$ is the input and $Y \in \mathcal{Y}$ is the true output.

Given a pre-trained model $f: \mathcal{X} \to \mathcal{F}$ that maps inputs to some feature space $\mathcal{F}$, we seek to construct a set-valued predictor $\Gamma: \mathcal{X} \times \mathcal{F} \to 2^{\mathcal{Y}}$ such that $\Gamma(x, f(x))$ produces a prediction set for input $x$. Let $\ell: 2^{\mathcal{Y}} \times \mathcal{Y} \to \mathbb{R}_+$ denote a loss function that measures the quality of a prediction set $S$ given the true output $y$.

We assume access to a calibration dataset $\mathcal{D}_{\text{cal}} = \{(X_1, Y_1), \ldots, (X_n, Y_n)\}$ of $n$ i.i.d. samples drawn from distribution $P_{\text{cal}}$, and we wish to provide guarantees for test data $(X_{\text{test}}, Y_{\text{test}}) \sim P_{\text{test}}$. The relationship between $P_{\text{cal}}$ and $P_{\text{test}}$ will be specified in our assumptions.

## Problem Statement

**Given:**
- A pre-trained model $f: \mathcal{X} \to \mathcal{F}$
- A loss function $\ell: 2^{\mathcal{Y}} \times \mathcal{Y} \to \mathbb{R}_+$
- A target expected loss level $\alpha \in (0, 1)$
- A calibration dataset $\mathcal{D}_{\text{cal}} = \{(X_i, Y_i)\}_{i=1}^n$

**Find:** A set-valued predictor $\Gamma: \mathcal{X} \times \mathcal{F} \to 2^{\mathcal{Y}}$ such that
$$\mathbb{E}_{(X_{\text{test}}, Y_{\text{test}}) \sim P_{\text{test}}}[\ell(\Gamma(X_{\text{test}}, f(X_{\text{test}})), Y_{\text{test}})] \leq \alpha$$

**Constraints:**
1. The guarantee must hold with high probability over the randomness in $\mathcal{D}_{\text{cal}}$
2. The method must be model-agnostic (work with any pre-trained $f$)
3. The method must be loss-agnostic (work with any loss function $\ell$)

## Objective

Our primary objective is to construct prediction sets that satisfy the expected loss constraint while being as informative as possible. Formally, we seek to solve:

$$\min_{\Gamma} \mathbb{E}_{(X,Y) \sim P_{\text{test}}}[|\Gamma(X, f(X))|]$$

subject to:
$$\mathbb{P}_{\mathcal{D}_{\text{cal}} \sim P_{\text{cal}}^n}\left(\mathbb{E}_{(X_{\text{test}}, Y_{\text{test}}) \sim P_{\text{test}}}[\ell(\Gamma(X_{\text{test}}, f(X_{\text{test}})), Y_{\text{test}})] \leq \alpha\right) \geq 1 - \delta$$

where $|\cdot|$ denotes set cardinality and $\delta \in (0, 1)$ is a confidence parameter. This formulation seeks prediction sets that are both accurate (low expected loss) and efficient (small average size).

## Technical Assumptions

We make the following minimal assumptions:

**A1 (Finite Sample Access):** We have access to a finite calibration dataset $\mathcal{D}_{\text{cal}}$ of size $n$, where each $(X_i, Y_i)$ is drawn i.i.d. from $P_{\text{cal}}$.

**A2 (Bounded Loss):** The loss function $\ell$ is bounded: $\ell(S, y) \in [0, L]$ for some $L < \infty$ and all $S \subseteq \mathcal{Y}, y \in \mathcal{Y}$.

**A3 (Measurability):** The predictor $\Gamma$ is measurable with respect to the appropriate $\sigma$-algebras.

**A4 (Distribution Relationship):** The calibration and test distributions satisfy one of the following:
- **(A4a) Exchangeability:** $P_{\text{cal}} = P_{\text{test}}$
- **(A4b) Covariate Shift:** $P_{\text{cal}}(Y|X) = P_{\text{test}}(Y|X)$ but $P_{\text{cal}}(X) \neq P_{\text{test}}(X)$, with known likelihood ratio $w(x) = \frac{dP_{\text{test}}(X)}{dP_{\text{cal}}(X)}(x)$

Assumption A1 reflects the practical constraint of finite data. A2 ensures theoretical tractability while accommodating most loss functions of interest (e.g., 0-1 loss, F1 loss, coverage loss). A3 is standard for measurable prediction functions. A4 captures the most common scenarios in practice: either the calibration and test data are identically distributed, or there is covariate shift with a known reweighting mechanism.

## Connection to Prior Work

Classical conformal prediction methods [Vovk et al., 2005] provide set-valued predictions with marginal coverage guarantees under exchangeability. However, these methods are designed specifically for coverage control (ensuring $\mathbb{P}(Y \in \hat{S}) \geq 1-\alpha$) and do not extend to arbitrary loss functions. Recent work by Tibshirani et al. [2020] extends conformal prediction to handle covariate shift, but remains limited to coverage-based objectives.

Existing approaches for general loss control either: (1) require strong distributional assumptions that rarely hold in practice, (2) provide only asymptotic guarantees that may not hold for finite samples, or (3) are tailored to specific loss functions or model classes. Multi-label classification methods [Zhang & Zhou, 2014] and structured prediction techniques [Daumé III et al., 2009] often provide loss-specific solutions but lack the generality and finite-sample guarantees we seek.

Our formulation addresses the fundamental gap between the need for flexible, finite-sample guarantees on arbitrary losses and the limited scope of existing conformal methods. By extending beyond coverage to general expected loss control while maintaining the model-agnostic and finite-sample properties of conformal prediction, we provide a unified framework for set-valued prediction across diverse applications.
