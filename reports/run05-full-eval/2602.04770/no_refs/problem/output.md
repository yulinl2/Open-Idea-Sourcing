# Reconstruction: problem
**Paper:** 2602.04770  
**Condition:** no_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Problem Formulation

## 2.1 Notation and Setup

Let $\mathcal{X}$ denote the input space and $\mathcal{Y} \subseteq \mathbb{R}$ the output space. We observe an exchangeable sequence $(X_1, Y_1), \ldots, (X_{n+1}, Y_{n+1})$ of random variables drawn from an unknown distribution $P$ on $\mathcal{X} \times \mathcal{Y}$. The first $n$ pairs constitute our training data $\mathcal{D}_n = \{(X_i, Y_i)\}_{i=1}^n$, while $(X_{n+1}, Y_{n+1})$ represents a test point where we seek to predict $Y_{n+1}$ given $X_{n+1}$.

For a miscoverage level $\alpha \in (0,1)$, our goal is to construct a prediction interval $\mathcal{C}_\alpha(X_{n+1}) \subseteq \mathcal{Y}$ such that
$$\mathbb{P}(Y_{n+1} \in \mathcal{C}_\alpha(X_{n+1})) \geq 1 - \alpha$$
holds for any distribution $P$ and any sample size $n$.

Let $\mathcal{S}$ denote a class of score functions $s: \mathcal{X} \times \mathcal{Y} \times \mathcal{D}_n \to \mathbb{R}$, where $s(x, y, \mathcal{D}_n)$ measures the "conformity" of the pair $(x, y)$ with respect to the training data. Higher scores indicate greater conformity. We define $S_i = s(X_i, Y_i, \mathcal{D}_n)$ for $i = 1, \ldots, n$ as the conformity scores on the training data.

## 2.2 Conformal Prediction Framework

Standard conformal prediction constructs intervals using a fixed score function $s_0 \in \mathcal{S}$. Given a test input $X_{n+1}$, the prediction set is defined as
$$\mathcal{C}_\alpha^{s_0}(X_{n+1}) = \left\{y \in \mathcal{Y} : s_0(X_{n+1}, y, \mathcal{D}_n) \geq \hat{q}_\alpha^{s_0}\right\}$$
where $\hat{q}_\alpha^{s_0}$ is the $\lceil (1-\alpha)(n+1) \rceil$-th largest value among $\{S_1^{s_0}, \ldots, S_n^{s_0}, s_0(X_{n+1}, y, \mathcal{D}_n)\}$ for any $y \in \mathcal{Y}$.

By the exchangeability assumption, this procedure guarantees that $\mathbb{P}(Y_{n+1} \in \mathcal{C}_\alpha^{s_0}(X_{n+1})) \geq 1 - \alpha$ regardless of the underlying distribution $P$.

## 2.3 The Score Function Learning Problem

The efficiency of conformal intervals depends critically on the choice of score function. Intuitively, an optimal score function should assign low scores to unlikely $(x,y)$ pairs and high scores to likely pairs, thereby producing tighter intervals around the true conditional distribution.

**Problem Statement**: Given the training data $\mathcal{D}_n$ and score function class $\mathcal{S}$, we seek to learn a score function $\hat{s} \in \mathcal{S}$ that minimizes the expected interval length while preserving the finite-sample coverage guarantee.

Formally, let $L(\mathcal{C})$ denote the length of interval $\mathcal{C}$ (with appropriate extension to multi-dimensional outputs). We aim to solve:
$$\min_{\hat{s} \in \mathcal{S}} \mathbb{E}\left[L\left(\mathcal{C}_\alpha^{\hat{s}}(X_{n+1})\right)\right]$$
subject to the constraint that
$$\mathbb{P}\left(Y_{n+1} \in \mathcal{C}_\alpha^{\hat{s}}(X_{n+1})\right) \geq 1 - \alpha$$
holds for any distribution $P$ and any realization of the learning procedure.

## 2.4 Technical Challenges

The fundamental challenge lies in the tension between these two objectives. While learning $\hat{s}$ from $\mathcal{D}_n$ can potentially improve efficiency, it introduces dependence between the score function and the data used to compute quantiles, potentially violating the exchangeability assumption that underlies conformal prediction's coverage guarantees.

More precisely, if $\hat{s}$ depends on $\mathcal{D}_n$, then the conformity scores $S_i = \hat{s}(X_i, Y_i, \mathcal{D}_n)$ are no longer exchangeable with the test score $\hat{s}(X_{n+1}, Y_{n+1}, \mathcal{D}_n)$, since the latter involves a point that was not used in training $\hat{s}$.

## 2.5 Assumptions

We make the following technical assumptions:

**A1 (Exchangeability)**: The sequence $(X_1, Y_1), \ldots, (X_{n+1}, Y_{n+1})$ is exchangeable under the data-generating distribution $P$.

**A2 (Score Function Class)**: The class $\mathcal{S}$ is sufficiently rich to contain functions that can approximate the optimal score function, yet structured enough to enable effective learning from finite samples.

**A3 (Measurability)**: All score functions in $\mathcal{S}$ are measurable, and the learning procedure produces measurable score functions.

**A4 (Computational Tractability)**: The quantile computation and set construction $\{y : \hat{s}(X_{n+1}, y, \mathcal{D}_n) \geq \hat{q}_\alpha\}$ can be performed efficiently.

Assumption A1 is standard in conformal prediction and enables the finite-sample guarantees. Assumptions A2-A4 ensure that the learning problem is well-posed and computationally feasible.

## 2.6 Relationship to Prior Work

Classical conformal prediction methods \citep{vovk2005algorithmic, lei2018distribution} employ fixed score functions such as absolute residuals $s(x,y,\mathcal{D}_n) = -|\hat{f}(x) - y|$ where $\hat{f}$ is a point predictor trained on $\mathcal{D}_n$. While these approaches guarantee coverage, they may be inefficient when the fixed score function is poorly suited to the data distribution.

Recent work on locally adaptive conformal prediction \citep{papadopoulos2002inductive, lei2018distribution} considers score functions that adapt to local properties of the input space, but typically still rely on pre-specified functional forms rather than learning the score function from data.

Quantile regression approaches \citep{koenker2001quantile} directly estimate conditional quantiles but generally lack finite-sample coverage guarantees. Our formulation bridges this gap by maintaining conformal prediction's validity while enabling data-driven score function selection.

The key innovation in our problem formulation is the explicit treatment of the score function as a learnable component while preserving the finite-sample guarantees that distinguish conformal prediction from asymptotic methods. This requires careful handling of the dependence structure introduced by learning, which existing approaches have not adequately addressed.
