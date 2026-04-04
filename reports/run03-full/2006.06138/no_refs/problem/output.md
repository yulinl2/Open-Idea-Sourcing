# Reconstruction: problem
**Paper:** 2006.06138  
**Condition:** no_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Problem Formulation

## Notation and Setup

Let $\mathcal{X}$ denote the input space and $\mathcal{Y}$ denote the output space. We consider a setting where we have access to a pre-trained predictor $f: \mathcal{X} \to \mathcal{P}(\mathcal{Y})$, where $\mathcal{P}(\mathcal{Y})$ denotes the power set of $\mathcal{Y}$ (i.e., all possible subsets of $\mathcal{Y}$). The predictor $f$ maps each input $x \in \mathcal{X}$ to a prediction set $f(x) \subseteq \mathcal{Y}$.

Let $(X, Y) \sim P$ denote a random pair drawn from an unknown distribution $P$ over $\mathcal{X} \times \mathcal{Y}$. We assume access to:
- A calibration dataset $\mathcal{D}_{\text{cal}} = \{(X_1, Y_1), \ldots, (X_n, Y_n)\}$ of $n$ i.i.d. samples from $P$
- A test instance $X_{\text{test}}$ drawn from the same marginal distribution as the calibration data

Let $\ell: \mathcal{P}(\mathcal{Y}) \times \mathcal{Y} \to \mathbb{R}_+$ denote a user-specified loss function that measures the quality of a prediction set $S \subseteq \mathcal{Y}$ given the true label $y \in \mathcal{Y}$. Common examples include:
- **Set size loss**: $\ell(S, y) = |S|$ (encourages smaller prediction sets)
- **Coverage loss**: $\ell(S, y) = \mathbf{1}[y \notin S]$ (penalizes missing the true label)
- **Weighted coverage loss**: $\ell(S, y) = w(y) \cdot \mathbf{1}[y \notin S]$ for importance weights $w: \mathcal{Y} \to \mathbb{R}_+$

## Problem Statement

Given a pre-trained predictor $f$, a loss function $\ell$, a target risk level $\alpha \in (0, 1)$, and a calibration dataset $\mathcal{D}_{\text{cal}}$, we seek to construct a **set-valued predictor** $\hat{C}: \mathcal{X} \to \mathcal{P}(\mathcal{Y})$ such that:

$$\mathbb{E}_{(X_{\text{test}}, Y_{\text{test}}) \sim P}[\ell(\hat{C}(X_{\text{test}}), Y_{\text{test}})] \leq \alpha$$

with high probability over the randomness in the calibration dataset $\mathcal{D}_{\text{cal}}$.

More precisely, we require that for any distribution $P$ and any $\delta \in (0, 1)$:
$$\mathbb{P}_{\mathcal{D}_{\text{cal}} \sim P^n}\left[\mathbb{E}_{(X_{\text{test}}, Y_{\text{test}}) \sim P}[\ell(\hat{C}(X_{\text{test}}), Y_{\text{test}})] \leq \alpha\right] \geq 1 - \delta$$

The predictor $\hat{C}$ must be constructed using only the calibration data $\mathcal{D}_{\text{cal}}$ and the base predictor $f$, without access to the test distribution or additional labeled data.

## Objective and Constraints

Our primary objective is **risk control**: ensuring the expected loss remains below the specified threshold $\alpha$. Subject to this constraint, we seek prediction sets that are as informative as possible, which typically translates to minimizing a secondary objective such as expected set size:

$$\min_{\hat{C}} \mathbb{E}_{X \sim P_X}[|\hat{C}(X)|] \quad \text{subject to} \quad \mathbb{E}_{(X,Y) \sim P}[\ell(\hat{C}(X), Y)] \leq \alpha$$

However, since we only have finite-sample access to $P$ through $\mathcal{D}_{\text{cal}}$, we must work with empirical approximations while maintaining the finite-sample guarantee.

## Technical Assumptions

We make the following minimal assumptions:

**A1 (Exchangeability)**: The calibration data $\mathcal{D}_{\text{cal}}$ and test point $(X_{\text{test}}, Y_{\text{test}})$ are exchangeable. This is weaker than the standard i.i.d. assumption and allows for certain forms of distribution shift.

**A2 (Measurability)**: The loss function $\ell$ is measurable, and the prediction sets output by $\hat{C}$ are measurable subsets of $\mathcal{Y}$.

**A3 (Bounded Loss)**: The loss function $\ell$ is bounded, i.e., $\sup_{S,y} \ell(S,y) < \infty$. This ensures that concentration inequalities can be applied effectively.

These assumptions are significantly weaker than those required by traditional statistical learning theory, which typically assumes i.i.d. data, specific parametric forms, or asymptotic regimes.

## Relationship to Prior Work

Classical approaches to set prediction fall into several categories, each with significant limitations for our setting:

**Conformal Prediction** provides distribution-free coverage guarantees but is primarily designed for the coverage loss $\ell(S,y) = \mathbf{1}[y \notin S]$ and does not naturally extend to general loss functions or risk control beyond coverage.

**PAC-Bayes Theory** offers finite-sample risk bounds but requires specifying prior distributions over predictors and typically applies to single-valued predictions rather than set-valued outputs.

**Multiple Testing Procedures** control family-wise error rates but do not provide expected loss control and are not designed for the prediction setting where the "hypotheses" (potential labels) depend on the input.

**Empirical Risk Minimization** with surrogate losses can handle general loss functions but requires retraining models and provides only asymptotic guarantees under strong distributional assumptions.

Our formulation bridges these gaps by seeking finite-sample expected loss control for arbitrary loss functions while working with pre-trained models and making minimal distributional assumptions. This represents a significant generalization of existing frameworks and addresses practical needs in modern machine learning applications where models are often pre-trained and deployed across diverse domains with varying loss requirements.
