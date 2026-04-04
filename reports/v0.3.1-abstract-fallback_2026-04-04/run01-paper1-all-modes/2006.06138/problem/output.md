# Reconstruction: problem
**Paper:** 2006.06138  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Problem Formulation

## Notation and Setup

Let $\mathcal{X}$ denote the input space and $\mathcal{Y}$ denote the output space. We consider the problem of set-valued prediction, where for each input $x \in \mathcal{X}$, we aim to output a prediction set $\Gamma(x) \subseteq \mathcal{Y}$ rather than a single prediction. Let $\mathcal{P}(\mathcal{Y})$ denote the power set of $\mathcal{Y}$, so that prediction functions take the form $\Gamma: \mathcal{X} \to \mathcal{P}(\mathcal{Y})$.

We assume access to a dataset $\{(X_1, Y_1), \ldots, (X_n, Y_n)\}$ of $n$ i.i.d. samples drawn from an unknown distribution $P$ over $\mathcal{X} \times \mathcal{Y}$. We partition this dataset into a training set $\mathcal{D}_{\text{train}} = \{(X_1, Y_1), \ldots, (X_m, Y_m)\}$ and a calibration set $\mathcal{D}_{\text{cal}} = \{(X_{m+1}, Y_{m+1}), \ldots, (X_n, Y_n)\}$, where $m < n$. Let $n_{\text{cal}} = n - m$ denote the size of the calibration set.

Given a user-specified loss function $\ell: \mathcal{P}(\mathcal{Y}) \times \mathcal{Y} \to \mathbb{R}_+$, where $\ell(\Gamma, y)$ measures the cost of predicting set $\Gamma$ when the true label is $y$, we define the risk of a prediction function $\Gamma$ as:
$$R(\Gamma) = \mathbb{E}_{(X,Y) \sim P}[\ell(\Gamma(X), Y)]$$

We assume access to a pre-trained base model $f: \mathcal{X} \to \mathcal{Z}$ that maps inputs to some representation space $\mathcal{Z}$. This model may have been trained on $\mathcal{D}_{\text{train}}$ or on external data, and we treat it as fixed throughout our analysis.

## Problem Statement

**Given:** 
- A pre-trained model $f: \mathcal{X} \to \mathcal{Z}$
- A calibration dataset $\mathcal{D}_{\text{cal}} = \{(X_i, Y_i)\}_{i=m+1}^n$ 
- A loss function $\ell: \mathcal{P}(\mathcal{Y}) \times \mathcal{Y} \to \mathbb{R}_+$
- A risk level $\alpha \in (0,1)$

**Find:** A prediction function $\hat{\Gamma}: \mathcal{X} \to \mathcal{P}(\mathcal{Y})$ such that with probability at least $1-\delta$ over the randomness in $\mathcal{D}_{\text{cal}}$:
$$R(\hat{\Gamma}) \leq \alpha$$

where the probability statement holds for any test distribution that is exchangeable with the calibration data.

## Formal Objective

Our goal is to construct a calibration procedure that, given the calibration set $\mathcal{D}_{\text{cal}}$, outputs a prediction function $\hat{\Gamma}$ satisfying the risk constraint. Formally, we seek a mapping:
$$\mathcal{C}: (\mathcal{X} \times \mathcal{Y})^{n_{\text{cal}}} \times [0,1] \to (\mathcal{X} \to \mathcal{P}(\mathcal{Y}))$$

such that for $\hat{\Gamma} = \mathcal{C}(\mathcal{D}_{\text{cal}}, \alpha)$:
$$\mathbb{P}_{\mathcal{D}_{\text{cal}}}[R(\hat{\Gamma}) \leq \alpha] \geq 1 - \delta$$

where the probability is taken over the random draw of the calibration set $\mathcal{D}_{\text{cal}}$.

Additionally, we desire that $\hat{\Gamma}$ produces prediction sets that are not unnecessarily large. While we do not impose this as a hard constraint, we seek procedures that minimize set size subject to the risk constraint, i.e., that solve:
$$\min_{\Gamma} \mathbb{E}_{X \sim P_X}[|\Gamma(X)|] \quad \text{subject to} \quad R(\Gamma) \leq \alpha$$

where $|\cdot|$ denotes set cardinality and $P_X$ is the marginal distribution of $X$.

## Technical Assumptions

We make the following minimal assumptions:

**A1 (Exchangeability):** The samples $(X_1, Y_1), \ldots, (X_n, Y_n)$ are exchangeable. This is weaker than the i.i.d. assumption and allows for certain forms of dependence while ensuring that the empirical distribution converges to the true distribution.

**A2 (Finite Loss):** The loss function $\ell$ is non-negative and bounded: $0 \leq \ell(\Gamma, y) \leq L$ for some constant $L < \infty$ and all $\Gamma \subseteq \mathcal{Y}, y \in \mathcal{Y}$.

**A3 (Monotonicity):** For any $y \in \mathcal{Y}$ and sets $\Gamma_1 \subseteq \Gamma_2 \subseteq \mathcal{Y}$, we have $\ell(\Gamma_1, y) \geq \ell(\Gamma_2, y)$. This captures the intuition that larger prediction sets should incur lower loss.

Assumption A1 is standard in conformal prediction and distribution-free inference, allowing us to avoid strong parametric assumptions about the data distribution. Assumption A2 ensures that concentration inequalities can be applied effectively. Assumption A3 is natural for set prediction tasks, as including the true label in the prediction set should reduce the loss.

## Relationship to Prior Work

Classical conformal prediction methods \cite{vovk2005algorithmic} provide distribution-free coverage guarantees for prediction sets, ensuring that $\mathbb{P}[Y \in \Gamma(X)] \geq 1-\alpha$ for a miscoverage rate $\alpha$. However, these methods are specifically designed for the 0-1 coverage loss and do not extend to general loss functions.

Recent work on conformal prediction under covariate shift \cite{tibshirani2019conformal} addresses distributional robustness but remains focused on coverage guarantees rather than general risk control. Risk-controlling prediction sets represent a significant generalization that can handle arbitrary loss functions while maintaining the distribution-free nature of conformal methods.

The key gap addressed by our formulation is the lack of finite-sample, distribution-free methods for controlling expected loss in set-valued prediction beyond the special case of coverage. Existing approaches either: (1) require strong distributional assumptions, (2) provide only asymptotic guarantees, or (3) are limited to specific loss functions. Our formulation seeks to bridge this gap by providing a unified framework that works with any loss function while maintaining the computational efficiency and theoretical rigor of conformal prediction methods.
