# Reconstruction: problem_method
**Paper:** 2602.04770  
**Condition:** with_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Problem Formulation

## Notation and Setup

Let $\mathcal{X} \subseteq \mathbb{R}^d$ denote the data space and $P_{\text{data}}$ be the unknown target data distribution over $\mathcal{X}$. We consider a generative model parameterized by $\theta \in \Theta$, where $\Theta$ is the parameter space. Let $P_{\theta}$ denote the model distribution induced by parameters $\theta$, and let $P_{\text{noise}}$ be a simple base distribution (e.g., standard Gaussian) from which we can easily sample.

For a generative model $G_{\theta}: \mathcal{Z} \to \mathcal{X}$ mapping from noise space $\mathcal{Z}$ to data space $\mathcal{X}$, we define the pushforward distribution as:
$$P_{\theta}(A) = P_{\text{noise}}(\{z \in \mathcal{Z} : G_{\theta}(z) \in A\})$$
for any measurable set $A \subseteq \mathcal{X}$.

## Problem Statement

**Given:** 
- Training dataset $\{x_i\}_{i=1}^n$ sampled i.i.d. from $P_{\text{data}}$
- Access to samples from base distribution $P_{\text{noise}}$
- Neural network architecture $G_{\theta}: \mathcal{Z} \to \mathcal{X}$

**Find:** Parameters $\theta^*$ such that the induced distribution $P_{\theta^*}$ approximates $P_{\text{data}}$

**Guarantee:** The model should generate high-quality samples in a single forward pass while achieving:
1. **Distribution matching**: $P_{\theta^*} \approx P_{\text{data}}$ in a suitable metric
2. **Single-step generation**: Samples $G_{\theta^*}(z)$ for $z \sim P_{\text{noise}}$ require only one network evaluation
3. **Mode coverage**: The generated distribution captures the full support and diversity of $P_{\text{data}}$

## Objective Formulation

Drawing inspiration from the weighted exchangeability framework in conformal prediction, we formulate the training objective as a distribution-matching problem with importance weighting. We define the **weighted distributional loss**:

$$\mathcal{L}(\theta) = \mathbb{E}_{z \sim P_{\text{noise}}} \left[ w(G_{\theta}(z)) \cdot \ell(G_{\theta}(z)) \right] - \mathbb{E}_{x \sim P_{\text{data}}} \left[ \ell(x) \right]$$

where:
- $\ell: \mathcal{X} \to \mathbb{R}$ is a score function measuring data conformity (analogous to nonconformity scores in conformal prediction)
- $w: \mathcal{X} \to \mathbb{R}_+$ is an importance weight function that emphasizes regions where the model distribution differs from the data distribution

The empirical version becomes:
$$\hat{\mathcal{L}}(\theta) = \frac{1}{m} \sum_{j=1}^m w(G_{\theta}(z_j)) \cdot \ell(G_{\theta}(z_j)) - \frac{1}{n} \sum_{i=1}^n \ell(x_i)$$

where $\{z_j\}_{j=1}^m$ are samples from $P_{\text{noise}}$ and $\{x_i\}_{i=1}^n$ are training data points.

## Technical Assumptions

**A1. Smoothness:** $G_{\theta}$ is differentiable with respect to $\theta$ and Lipschitz continuous in $z$.

**A2. Score function properties:** $\ell$ is bounded, measurable, and captures meaningful data structure (e.g., local density, nearest neighbor distances, or learned feature representations).

**A3. Weight function design:** $w(x) = \frac{d\hat{P}_{\text{data}}}{dP_{\theta}}(x)$ approximates the likelihood ratio between empirical data distribution and current model distribution, similar to the covariate shift correction in the reference.

**A4. Base distribution:** $P_{\text{noise}}$ has full support on $\mathcal{Z}$ and admits efficient sampling.

**A5. Network capacity:** The function class $\{G_{\theta} : \theta \in \Theta\}$ has sufficient capacity to approximate the optimal transport map from $P_{\text{noise}}$ to $P_{\text{data}}$.

These assumptions adapt the weighted exchangeability framework from conformal prediction to the generative modeling setting, where we seek to match distributions rather than construct prediction intervals.

# Methodology

## High-Level Approach

Our approach, **Weighted Conformity Generative Modeling (WCGM)**, adapts the importance weighting mechanism from conformal prediction under covariate shift to train single-step generative models. The key insight is to treat the discrepancy between model and data distributions as analogous to covariate shift, using importance weights to rebalance the training objective.

## Core Algorithm

### Score Function Design

We define the conformity score function as:
$$\ell(x) = -\log \hat{p}_{\text{data}}(x) + \lambda \cdot d_{\text{NN}}(x)$$

where:
- $\hat{p}_{\text{data}}(x)$ is a kernel density estimate of the data distribution
- $d_{\text{NN}}(x)$ is the distance to the $k$-th nearest neighbor in the training set
- $\lambda > 0$ balances density and diversity terms

### Importance Weight Computation

Following the weighted conformal framework, we compute importance weights as:
$$w(x) = \frac{\hat{p}_{\text{data}}(x)}{\hat{p}_{\theta}(x) + \epsilon}$$

where $\hat{p}_{\theta}(x)$ is estimated using samples from the current model and $\epsilon > 0$ prevents division by zero.

### Training Algorithm

```
Algorithm: Weighted Conformity Generative Training

Input: Training data {x_i}_{i=1}^n, generator G_θ, batch size m
Initialize: θ randomly, learning rate η

For epoch = 1 to max_epochs:
    1. Sample noise batch {z_j}_{j=1}^m ~ P_noise
    
    2. Generate samples: x̂_j = G_θ(z_j) for j = 1,...,m
    
    3. Compute conformity scores:
       - For real data: ℓ_i = ℓ(x_i) for i = 1,...,n
       - For generated data: ℓ̂_j = ℓ(x̂_j) for j = 1,...,m
    
    4. Update density estimates:
       - p̂_data using {x_i} and {x̂_j} from previous iterations
       - p̂_θ using current generated samples {x̂_j}
    
    5. Compute importance weights: w_j = p̂_data(x̂_j) / (p̂_θ(x̂_j) + ε)
    
    6. Compute weighted loss:
       L̂(θ) = (1/m)∑_{j=1}^m w_j · ℓ̂_j - (1/n)∑_{i=1}^n ℓ_i
    
    7. Update parameters: θ ← θ - η∇_θ L̂(θ)
    
    8. Optional: Clip weights w_j to [1/C, C] for stability

Return: Trained generator G_θ*
```

## Key Design Decisions

**Conformity Score Choice:** The combination of density and nearest-neighbor terms ensures both high likelihood and diversity, preventing mode collapse by penalizing generated samples that are too similar to training data.

**Weight Clipping:** Similar to practical implementations of importance sampling, we clip extreme weights to maintain training stability while preserving the reweighting effect.

**Density Estimation:** We use kernel density estimation with adaptive bandwidth, updated periodically during training to track the evolving model distribution.

## Theoretical Properties

**Proposition 1 (Consistency):** Under assumptions A1-A5, if the importance weights $w(x)$ correctly approximate $d\hat{P}_{\text{data}}/dP_{\theta}(x)$ and the score function $\ell$ distinguishes between distributions, then minimizing $\hat{\mathcal{L}}(\theta)$ leads to $P_{\theta^*} \to P_{\text{data}}$ as $n, m \to \infty$.

**Proposition 2 (Single-Step Generation):** The trained generator $G_{\theta^*}$ produces samples in $O(1)$ forward passes, independent of data dimensionality or complexity.

**Proof Sketch:** The weighted objective directly optimizes the distributional discrepancy without requiring iterative refinement. The importance weighting corrects for the mismatch between model and data distributions, similar to how weighted conformal prediction corrects for covariate shift.

## Computational Complexity

- **Training:** $O(T \cdot m \cdot (C_G + C_\ell + C_w))$ where $T$ is training iterations, $C_G$ is generator forward pass cost, $C_\ell$ is score computation cost, and $C_w$ is weight computation cost
- **Generation:** $O(C_G)$ per sample - single forward pass through generator
- **Memory:** $O(n + m)$ for storing training data and current batch

The approach scales favorably compared to iterative methods like diffusion models, which require $O(K \cdot C_G)$ for $K$ denoising steps.

This methodology directly addresses the core problem by enabling single-step generation while using the principled importance weighting framework from conformal prediction to ensure proper distribution matching and mode coverage.
