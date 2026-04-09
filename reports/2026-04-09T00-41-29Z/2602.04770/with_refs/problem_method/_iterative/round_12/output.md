# Problem Formulation

## Notation and Problem Setup

Let $\mathcal{X} \subset \mathbb{R}^d$ denote the data space and $P_{\text{data}}$ be the unknown target distribution over $\mathcal{X}$. Let $P_{\text{prior}}$ be a simple prior distribution (e.g., standard Gaussian) from which we can efficiently sample. We denote by $\mathcal{P}(\mathcal{X})$ the space of probability distributions over $\mathcal{X}$.

For a neural network $G_\theta: \mathcal{X} \to \mathcal{X}$ parameterized by $\theta \in \Theta$, we define the **pushforward operation** $G_\theta \# P_{\text{prior}}$ as the distribution obtained by applying $G_\theta$ to samples from $P_{\text{prior}}$. That is, if $z \sim P_{\text{prior}}$, then $G_\theta(z) \sim G_\theta \# P_{\text{prior}}$.

## The Core Field Formulation

We introduce a **sample-level drift field** $F_\phi: \mathcal{X} \times \mathcal{X} \to \mathcal{X}$ parameterized by $\phi \in \Phi$, where $F_\phi(x, y)$ represents the direction and magnitude by which sample $x$ should move given the influence of sample $y$. This field must satisfy the **anti-symmetry property**:

$$F_\phi(x, y) = -F_\phi(y, x) \quad \forall x, y \in \mathcal{X}$$

This ensures that $F_\phi(x, x) = 0$, meaning samples do not influence themselves.

For a batch of generated samples $\{x_1, \ldots, x_m\}$ where $x_i = G_\theta(z_i)$ with $z_i \sim P_{\text{prior}}$, we define the **aggregate drift** for sample $x_i$ as:

$$\Delta_i = \sum_{j=1}^m w_{ij} F_\phi(x_i, x_j)$$

where $w_{ij}$ are similarity-based weights satisfying $w_{ii} = 0$ and $w_{ij} = w_{ji}$. A natural choice is:

$$w_{ij} = \begin{cases} 
\frac{\exp(-\|x_i - x_j\|^2 / 2\sigma^2)}{\sum_{k \neq i} \exp(-\|x_i - x_k\|^2 / 2\sigma^2)} & \text{if } i \neq j \\
0 & \text{if } i = j
\end{cases}$$

## Problem Statement

**Given:** Training dataset $\{x^{(n)}\}_{n=1}^N$ sampled from $P_{\text{data}}$, prior distribution $P_{\text{prior}}$, and desired coverage level $\alpha \in (0,1)$.

**Find:** Parameters $\theta^*$ and $\phi^*$ such that the generator $G_{\theta^*}$ produces samples that:
1. Match the target distribution: $G_{\theta^*} \# P_{\text{prior}} \approx P_{\text{data}}$
2. Can be generated in a single forward pass
3. Avoid mode collapse and capture the full data distribution

**Guarantee:** The trained generator should satisfy distributional matching in the sense that for any test function $h$ with appropriate regularity:
$$\left|\mathbb{E}_{x \sim G_{\theta^*} \# P_{\text{prior}}}[h(x)] - \mathbb{E}_{x \sim P_{\text{data}}}[h(x)]\right| \leq \epsilon$$
for sufficiently small $\epsilon > 0$.

## Training Objective

The core training paradigm is based on a **fixed-point consistency condition**. For each generated sample $x_i = G_\theta(z_i)$, we require:

$$x_i = G_\theta(z_i) + \text{sg}(\Delta_i)$$

where $\text{sg}(\cdot)$ denotes the stop-gradient operation that prevents direct backpropagation through the field computation.

This leads to the **self-consistency loss**:
$$\mathcal{L}_{\text{consistency}}(\theta, \phi) = \mathbb{E}_{z_1, \ldots, z_m \sim P_{\text{prior}}} \left[ \frac{1}{m} \sum_{i=1}^m \|G_\theta(z_i) - G_\theta(z_i) - \text{sg}(\Delta_i)\|^2 \right]$$

Combined with a standard reconstruction loss on real data:
$$\mathcal{L}_{\text{recon}}(\theta) = \mathbb{E}_{x \sim P_{\text{data}}} \left[ \|x - G_\theta(\mathcal{E}(x))\|^2 \right]$$

where $\mathcal{E}$ is an encoding function (potentially learned jointly), the total objective becomes:
$$\mathcal{L}(\theta, \phi) = \mathcal{L}_{\text{recon}}(\theta) + \lambda \mathcal{L}_{\text{consistency}}(\theta, \phi)$$

## Technical Assumptions

1. **Smoothness:** $G_\theta$ and $F_\phi$ are differentiable with respect to their parameters
2. **Boundedness:** The support of $P_{\text{data}}$ is contained in a bounded set
3. **Field regularity:** $F_\phi$ is Lipschitz continuous in both arguments
4. **Anti-symmetry:** $F_\phi(x, y) = -F_\phi(y, x)$ is enforced architecturally or through regularization
5. **Non-degeneracy:** The weights $w_{ij}$ provide sufficient connectivity between samples

This formulation connects to conformal prediction methodology through the weighted influence mechanism, where samples that are more similar (higher weights) have stronger mutual influence, analogous to how conformal methods weight conformity scores based on similarity or likelihood ratios.

# Methodology

## High-Level Approach

Our method, **Flow Matching with Sample-Level Fields (FMSF)**, learns to generate samples by training a generator network to satisfy a self-consistency condition governed by a learned drift field. The key insight is that during training, we can leverage the iterative nature of optimization to learn a field that operates on individual samples, guiding them toward the target distribution through weighted interactions.

## Core Architecture

### Generator Network
The generator $G_\theta: \mathbb{R}^d \to \mathbb{R}^d$ is implemented as a deep neural network (typically a U-Net or ResNet architecture for images) that maps from the prior space directly to the data space.

### Drift Field Network
The anti-symmetric drift field $F_\phi(x, y)$ is implemented using a Siamese-style architecture:
- Shared encoder $E_\phi: \mathbb{R}^d \to \mathbb{R}^h$ maps inputs to hidden representations
- Anti-symmetric combination: $F_\phi(x, y) = \text{MLP}_\phi(E_\phi(x), E_\phi(y)) - \text{MLP}_\phi(E_\phi(y), E_\phi(x))$

This architectural design automatically ensures the anti-symmetry property $F_\phi(x, y) = -F_\phi(y, x)$.

## Training Algorithm

```
Algorithm: Flow Matching with Sample-Level Fields (FMSF)

Input: Training data {x^(n)}_{n=1}^N, batch size m, learning rates η_G, η_F
Initialize: Generator parameters θ, field parameters φ
Set: λ = 1.0, σ = 0.1 (bandwidth parameter)

for epoch = 1 to max_epochs:
    # Sample real data batch
    {x_real^(i)}_{i=1}^m ~ P_data
    
    # Sample generated batch  
    {z^(i)}_{i=1}^m ~ P_prior
    {x_gen^(i)}_{i=1}^m = {G_θ(z^(i))}_{i=1}^m
    
    # Compute similarity weights
    for i = 1 to m:
        for j = 1 to m:
            if i ≠ j:
                w_ij = exp(-||x_gen^(i) - x_gen^(j)||^2 / (2σ^2))
            else:
                w_ij = 0
        # Normalize weights
        w_i = w_i / sum(w_i)
    
    # Compute drift field values
    for i = 1 to m:
        Δ_i = Σ_{j=1}^m w_ij * F_φ(x_gen^(i), x_gen^(j))
    
    # Self-consistency loss
    L_consistency = (1/m) * Σ_{i=1}^m ||G_θ(z^(i)) - G_θ(z^(i)) - sg(Δ_i)||^2
    
    # Reconstruction loss (optional, for conditional generation)
    L_recon = (1/m) * Σ_{i=1}^m ||x_real^(i) - G_θ(Encode(x_real^(i)))||^2
    
    # Total loss
    L = L_recon + λ * L_consistency
    
    # Update parameters
    θ ← θ - η_G * ∇_θ L
    φ ← φ - η_F * ∇_φ L_consistency

Output: Trained generator G_θ*, field F_φ*
```

## Key Design Decisions

### Stop-Gradient Operation
The stop-gradient operation in the consistency loss is crucial. It prevents the generator from trivially satisfying the consistency condition by making $\Delta_i = 0$, instead forcing the field to learn meaningful drift directions. This technique enables indirect optimization of the field's effect on sample quality without direct supervision.

### Weighted Influence Mechanism
The similarity-based weighting $w_{ij}$ serves multiple purposes:
1. **Locality:** Samples primarily influence nearby samples, creating smooth local corrections
2. **Stability:** Prevents distant outliers from dominating the drift computation
3. **Efficiency:** Sparse weight matrices can be used for large batches

This connects to conformal prediction's use of weighted conformity scores, where the influence of training points is weighted by their relevance to the test point.

### Anti-Symmetry Enforcement
The anti-symmetric property ensures that the field represents a conservative force field where $F_\phi(x, y) = -F_\phi(y, x)$. This prevents the field from creating artificial "sources" or "sinks" and ensures that the total drift across all samples sums to zero, maintaining the overall sample distribution's center of mass.

## Theoretical Properties

### Convergence Analysis
Under mild regularity conditions, the training procedure converges to a fixed point where:
$$G_\theta(z) = G_\theta(z) + \mathbb{E}_{\text{batch}}[\Delta(G_\theta(z))]$$

This fixed-point condition implies that the generator produces samples that are in equilibrium with the learned drift field.

### Distributional Matching
When the consistency condition is satisfied and the field $F_\phi$ is optimal, the pushforward distribution $G_\theta \# P_{\text{prior}}$ approximates the target distribution $P_{\text{data}}$ in the sense of minimizing an implicit optimal transport cost.

## Computational Complexity

- **Training:** $O(m^2 d + m \cdot C_G + m^2 \cdot C_F)$ per batch, where $C_G$ and $C_F$ are the costs of forward passes through the generator and field networks respectively
- **Inference:** $O(C_G)$ - single forward pass through the generator
- **Memory:** $O(m^2)$ for storing pairwise weights, which can be reduced using sparse representations or hierarchical approximations

## Extensions and Variants

### Conditional Generation
For conditional generation with labels $y$, the field becomes $F_\phi(x, y; c_x, c_y)$ where $c_x, c_y$ are the conditioning variables. The anti-symmetry property is maintained within each conditional class.

### Multi-Scale Fields
For high-resolution generation, multiple field networks can operate at different spatial scales, with coarse-scale fields handling global structure and fine-scale fields managing local details.

### Adaptive Weighting
The bandwidth parameter $\sigma$ in the similarity weights can be learned or adapted during training, allowing the model to automatically determine the appropriate scale of local interactions.

This methodology provides a principled approach to single-step generation that leverages the iterative nature of training to learn complex distribution mappings while maintaining computational efficiency during inference.