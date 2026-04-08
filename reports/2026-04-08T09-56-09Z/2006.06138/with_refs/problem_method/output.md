# Reconstruction: problem_method (iterative, 4 rounds)
**Paper:** 2006.06138  
**Condition:** with_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  
**Rounds:** 4  
**Best round:** 4 (score 3.2)  
**Converged:** True (teacher recommended stop)  
**Score trajectory:** 2.8 -> 3.0 -> 3.0 -> 3.2  

---

# Problem Formulation

## Notation and Setup

Let $(\mathbf{X}, Y(0), Y(1)) \in \mathcal{X} \times \mathcal{Y} \times \mathcal{Y}$ denote the potential outcomes framework, where $\mathbf{X} \in \mathcal{X} \subseteq \mathbb{R}^d$ represents covariates, and $Y(0), Y(1) \in \mathcal{Y} \subseteq \mathbb{R}$ are the potential outcomes under control and treatment, respectively. Let $T \in \{0,1\}$ denote the binary treatment assignment. The observed outcome is $Y = TY(1) + (1-T)Y(0)$, so we observe triplets $(\mathbf{X}_i, T_i, Y_i)$ for $i = 1, \ldots, n$.

For any individual with covariates $\mathbf{x}$, the individual treatment effect (ITE) is defined as:
$$\tau(\mathbf{x}) = Y(1) - Y(0) \mid \mathbf{X} = \mathbf{x}$$

Let $P$ denote the joint distribution of $(\mathbf{X}, Y(0), Y(1), T)$, and let $P_{\text{target}}$ denote the target population distribution, which may differ from the study population distribution $P$.

## Problem Statement

**Given:** 
- Training data $\{(\mathbf{X}_i, T_i, Y_i)\}_{i=1}^n$ from study population $P$
- Target covariate $\mathbf{x}_{\text{new}}$ from target population $P_{\text{target}}$
- Desired coverage level $1-\alpha$ for $\alpha \in (0,1)$

**Find:** Prediction intervals $\hat{I}_0(\mathbf{x}_{\text{new}})$ and $\hat{I}_1(\mathbf{x}_{\text{new}})$ for the potential outcomes $Y(0)$ and $Y(1)$ respectively, such that these intervals can be used to construct a valid interval for the individual treatment effect $\tau(\mathbf{x}_{\text{new}})$.

**Guarantee:** The prediction intervals should satisfy finite-sample coverage guarantees:
$$\mathbb{P}\left(Y(0) \in \hat{I}_0(\mathbf{x}_{\text{new}}) \mid \mathbf{X} = \mathbf{x}_{\text{new}}\right) \geq 1-\alpha$$
$$\mathbb{P}\left(Y(1) \in \hat{I}_1(\mathbf{x}_{\text{new}}) \mid \mathbf{X} = \mathbf{x}_{\text{new}}\right) \geq 1-\alpha$$

## Objective

Our objective is to construct distribution-free prediction intervals that directly target the conditional distributions $Y(0) \mid \mathbf{X} = \mathbf{x}$ and $Y(1) \mid \mathbf{X} = \mathbf{x}$ separately, rather than attempting to model the treatment effect directly. This approach recognizes that predicting counterfactual outcomes is fundamentally different from standard prediction problems.

Formally, we seek to construct intervals by modeling the conditional quantiles:
$$Q_t^\beta(\mathbf{x}) = \inf\{y : \mathbb{P}(Y(t) \leq y \mid \mathbf{X} = \mathbf{x}) \geq \beta\}$$
for $t \in \{0,1\}$ and appropriate quantile levels $\beta$.

## Technical Assumptions

**Assumption 1 (Causal Identifiability):** We assume either:
- **(A1a) Randomized Experiment:** $T \perp (Y(0), Y(1)) \mid \mathbf{X}$ and $0 < \mathbb{P}(T=1 \mid \mathbf{X}) < 1$ almost surely
- **(A1b) Unconfoundedness:** $(Y(0), Y(1)) \perp T \mid \mathbf{X}$ and $0 < \mathbb{P}(T=1 \mid \mathbf{X}) < 1$ almost surely

**Assumption 2 (Covariate Shift):** When the target population differs from the study population, we assume the likelihood ratio $w(\mathbf{x}) = \frac{dP_{\text{target}}(\mathbf{X})}{dP(\mathbf{X})}(\mathbf{x})$ exists and is known or can be estimated accurately.

**Assumption 3 (Conditional Distribution Invariance):** The conditional outcome distributions are preserved across populations: $Y(t) \mid \mathbf{X} = \mathbf{x} \sim_P Y(t) \mid \mathbf{X} = \mathbf{x} \sim_{P_{\text{target}}}$ for $t \in \{0,1\}$.

**Assumption 4 (Overlap):** For each treatment arm $t \in \{0,1\}$, there exist sufficient observations such that $\sum_{i=1}^n \mathbf{1}(T_i = t) \geq 2$.

These assumptions are standard in causal inference and allow us to identify the conditional distributions of potential outcomes from observed data. Assumption 2 connects our approach to the covariate shift methodology developed in Tibshirani et al. (2020), while Assumption 3 ensures that uncertainty quantification remains valid across populations.

# Methodology

## High-Level Approach

Our methodology, **Conformal Causal Prediction (CCP)**, addresses the fundamental challenge of uncertainty quantification for individual treatment effects by decomposing the problem into separate prediction tasks for each potential outcome. Rather than directly modeling treatment effects, we construct distribution-free prediction intervals for $Y(0)$ and $Y(1)$ separately using a weighted conformal prediction framework that handles both within-study inference and covariate shift to target populations.

The key insight is to treat the prediction of each potential outcome $Y(t)$ as a distinct regression problem on the subset of units that received treatment $t$, then apply weighted conformal prediction to account for the sampling mechanism and potential population shift. This approach naturally handles the fundamental asymmetry in causal inference: we observe $Y(1)$ only for treated units and $Y(0)$ only for control units.

## Core Algorithm

### Algorithm 1: Conformal Causal Prediction

```
Input: 
- Training data {(X_i, T_i, Y_i)}_{i=1}^n
- Target covariate x_new
- Coverage level 1-α
- Weight function w(x) (identity if no covariate shift)
- Base quantile regression algorithms A_0, A_1

Step 1: Data Splitting by Treatment
- Define I_0 = {i : T_i = 0}, I_1 = {i : T_i = 1}
- Create treatment-specific datasets:
  D_0 = {(X_i, Y_i) : i ∈ I_0}
  D_1 = {(X_i, Y_i) : i ∈ I_1}

Step 2: Quantile Function Estimation
For each t ∈ {0,1}:
- Fit quantile regression models on D_t:
  Q̂_t^{α/2}(x) = A_t(D_t, α/2)
  Q̂_t^{1-α/2}(x) = A_t(D_t, 1-α/2)

Step 3: Conformity Score Computation
For each t ∈ {0,1} and i ∈ I_t:
- Compute conformity scores:
  V_i^{(t)} = max{Q̂_t^{α/2}(X_i) - Y_i, Y_i - Q̂_t^{1-α/2}(X_i), 0}

Step 4: Weight Calculation
For each t ∈ {0,1} and i ∈ I_t:
- Compute normalized weights:
  p_i^{(t)}(x_new) = w(X_i) / (∑_{j∈I_t} w(X_j) + w(x_new))
- Set p_{new}^{(t)}(x_new) = w(x_new) / (∑_{j∈I_t} w(X_j) + w(x_new))

Step 5: Conformal Quantile Computation
For each t ∈ {0,1}:
- Compute weighted quantile:
  q_t = Quantile(1-α; {p_i^{(t)}(x_new) δ_{V_i^{(t)}}}_{i∈I_t} ∪ {p_{new}^{(t)}(x_new) δ_∞})

Step 6: Interval Construction
For each t ∈ {0,1}:
- Construct prediction interval:
  Î_t(x_new) = [Q̂_t^{α/2}(x_new) - q_t, Q̂_t^{1-α/2}(x_new) + q_t]

Output: Prediction intervals Î_0(x_new), Î_1(x_new)
```

## Key Design Decisions

**Quantile-Based Conformity Scores:** We use conformity scores based on quantile regression rather than residuals from mean regression. This design choice directly targets the conditional distribution of outcomes rather than just deviations from a central tendency. The conformity score $V_i^{(t)}$ measures how far the observed outcome $Y_i$ falls outside the predicted quantile interval, providing a natural measure of non-conformity that respects the full distributional shape.

**Treatment-Stratified Conformal Prediction:** By splitting the data according to treatment assignment and applying conformal prediction separately to each subset, we respect the fundamental structure of the causal inference problem. This approach ensures that the prediction intervals for $Y(0)$ are based solely on control units and those for $Y(1)$ are based solely on treated units, avoiding any contamination between treatment arms.

**Weighted Exchangeability:** Following Tibshirani et al. (2020), we extend conformal prediction to handle covariate shift through careful weighting. The weights $w(\mathbf{x})$ rebalance the training distribution to match the target population, ensuring that the exchangeability assumption underlying conformal prediction holds in the reweighted space.

## Theoretical Properties

**Coverage Guarantee:** Under Assumptions 1-4, for each $t \in \{0,1\}$:
$$\mathbb{P}\left(Y(t) \in \hat{I}_t(\mathbf{x}_{\text{new}}) \mid \mathbf{X} = \mathbf{x}_{\text{new}}\right) \geq 1-\alpha$$

This follows from the weighted exchangeability property established in Tibshirani et al. (2020), applied separately to each treatment-stratified dataset.

**Finite-Sample Validity:** The coverage guarantee holds for any finite sample size $n$, without requiring asymptotic approximations or distributional assumptions beyond the causal identification conditions.

**Robustness to Model Misspecification:** The method maintains valid coverage even when the quantile regression models $\hat{Q}_t^{\beta}$ are misspecified, as long as the conformity scores capture the relevant aspects of distributional non-conformity.

## Computational Complexity

The algorithm has computational complexity $O(n \log n)$ per treatment arm for the quantile computations, plus the cost of fitting the base quantile regression algorithms. For $k$ quantile levels and $d$-dimensional covariates, the total complexity is $O(k \cdot C(n_0, d) + k \cdot C(n_1, d) + n \log n)$, where $C(n_t, d)$ is the complexity of the base algorithm on $n_t$ samples, and $n_0, n_1$ are the numbers of control and treated units respectively.

The method is computationally efficient compared to full conformal prediction because it avoids refitting models for each candidate outcome value, instead leveraging the quantile regression fits to define conformity scores directly.
