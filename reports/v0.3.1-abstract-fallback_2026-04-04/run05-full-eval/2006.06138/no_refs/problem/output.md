# Reconstruction: problem
**Paper:** 2006.06138  
**Condition:** no_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Problem Formulation

## Notation and Setup

Let $\mathcal{X}$ denote the input space and $\mathcal{Y}$ denote the output space. We consider prediction problems where the output is a set, so each true label $Y \in \mathcal{P}(\mathcal{Y})$ where $\mathcal{P}(\mathcal{Y})$ denotes the power set of $\mathcal{Y}$. Let $(\mathcal{X} \times \mathcal{P}(\mathcal{Y}), \mathcal{F}, P)$ be a probability space where $P$ is the unknown data-generating distribution.

Given a trained model $f: \mathcal{X} \rightarrow \mathbb{R}^{|\mathcal{Y}|}$ that outputs scores for each possible label, we seek to construct a prediction set function $\mathcal{C}: \mathcal{X} \rightarrow \mathcal{P}(\mathcal{Y})$ that maps inputs to subsets of labels. Let $\ell: \mathcal{P}(\mathcal{Y}) \times \mathcal{P}(\mathcal{Y}) \rightarrow \mathbb{R}_+$ be a loss function that measures the cost of predicting set $\hat{Y}$ when the true label set is $Y$.

We assume access to:
- A calibration dataset $\mathcal{D}_{\text{cal}} = \{(X_i, Y_i)\}_{i=1}^n$ drawn from $P$
- A test dataset $\mathcal{D}_{\text{test}} = \{(X_j, Y_j)\}_{j=1}^m$ drawn from $P$
- A pre-trained model $f$ (which we do not modify)

## Problem Statement

**Objective**: Construct a prediction set function $\mathcal{C}$ such that for a user-specified risk level $\alpha \in (0,1)$, we have
$$\mathbb{E}_{(X,Y) \sim P}[\ell(\mathcal{C}(X), Y)] \leq \alpha$$
with high probability, using only the finite calibration set $\mathcal{D}_{\text{cal}}$.

**Formal Problem**: Given a risk tolerance $\alpha$, calibration data $\mathcal{D}_{\text{cal}}$, pre-trained model $f$, and loss function $\ell$, find a prediction set function $\mathcal{C}$ and confidence level $\delta \in (0,1)$ such that
$$\mathbb{P}\left(\mathbb{E}_{(X,Y) \sim P}[\ell(\mathcal{C}(X), Y)] \leq \alpha\right) \geq 1-\delta$$
where the probability is taken over the randomness in $\mathcal{D}_{\text{cal}}$.

## Technical Assumptions

We make the following minimal assumptions:

**A1 (Exchangeability)**: The calibration and test data are exchangeable under $P$. Specifically, for any finite sequence $(X_1, Y_1), \ldots, (X_{n+m}, Y_{n+m})$ where the first $n$ pairs form $\mathcal{D}_{\text{cal}}$ and the remaining $m$ pairs form $\mathcal{D}_{\text{test}}$, the joint distribution is invariant under permutations.

**A2 (Loss Boundedness)**: The loss function $\ell$ is bounded, i.e., $\ell(\hat{Y}, Y) \in [0, L]$ for some finite constant $L > 0$ and all $\hat{Y}, Y \in \mathcal{P}(\mathcal{Y})$.

**A3 (Model Access)**: We have access to a pre-trained model $f$ that can be evaluated on new inputs, but we cannot modify its parameters or retrain it.

The exchangeability assumption (A1) is significantly weaker than the typical i.i.d. assumption and accommodates realistic scenarios where data distributions may shift over time while maintaining some structural relationship. The boundedness assumption (A2) is standard and satisfied by most practical loss functions. The model access assumption (A3) reflects the common practical constraint where models are expensive to train and practitioners need post-hoc calibration methods.

## Connection to Prior Work

Classical approaches to risk control in machine learning typically assume access to the true data distribution or require strong parametric assumptions. Conformal prediction methods provide distribution-free guarantees but focus primarily on coverage rather than expected loss control, and existing extensions to set prediction scenarios either lack finite-sample guarantees or require restrictive assumptions about the underlying model or data distribution.

Recent work on risk-controlling prediction sets has made progress on this problem, but existing methods either: (i) require knowledge of the loss distribution, (ii) only provide asymptotic guarantees, (iii) are computationally intractable for large label spaces, or (iv) work only for specific model architectures. Our formulation addresses these limitations by seeking a method that provides finite-sample guarantees under minimal assumptions while remaining computationally tractable for arbitrary models and loss functions.

The key technical challenge is that unlike coverage-based metrics (which depend only on set membership), expected loss depends on the full structure of both the predicted and true label sets, making it significantly more difficult to control without distributional assumptions.
