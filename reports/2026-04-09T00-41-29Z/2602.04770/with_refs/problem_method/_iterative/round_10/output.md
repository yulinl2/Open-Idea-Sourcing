# Problem Formulation

## Notation and Setup

Let $\mathcal{X} \subseteq \mathbb{R}^d$ denote the data space and $P_{\text{data}}$ be the unknown target distribution over $\mathcal{X}$. Let $P_{\text{prior}}$ be a known prior distribution (e.g., standard Gaussian) from which we can easily sample. We denote by $\mathcal{P}(\mathcal{X})$ the space of probability distributions over $\mathcal{X}$.

For a neural network $G_\theta: \mathcal{X} \to \mathcal{X}$ parameterized by $\theta \in \Theta$, we define the **pushforward operation** $G_\theta \# P_{\text{prior}}$ as the distribution obtained by applying $G_\theta$ to samples from $P_{\text{prior}}$. Formally, for any measurable set $A \subseteq \mathcal{X}$:
$$
(G_\theta \# P_{\text{prior}})(A) = P_{\text{prior}}(G_\theta^{-1}(A))
$$

During training, we observe samples $\{x_i\}_{i=1}^n \sim P_{\text{data}}$ and generated samples $\{G_\theta(z_i)\}_{i=1}^m$ where $z_i \sim P_{\text{prior}}$.

## Sample-Level Vector Field

We define a **sample-level vector field** $v_\phi: \mathcal{X} \times \mathcal{X} \to \mathcal{X}$ parameterized by $\phi \in \Phi$, which takes two samples as input and outputs a direction vector. This field governs how samples should move in the data space.

The field satisfies the **anti-symmetry property**:
$$
v_\phi(x, y) = -v_\phi(y, x) \quad \forall x, y \in \mathcal{X}
$$

This ensures that $v_\phi(x, x) = 0$, meaning identical samples exert no influence on each other.

## Weighted Influence Mechanism

For a given sample $x$, we define its **drift direction** as a weighted combination of influences from a reference set $\mathcal{S} = \{s_1, s_2, \ldots, s_k\}$:
$$
d_\phi(x; \mathcal{S}) = \sum_{i=1}^k w(x, s_i) \cdot v_\phi(x, s_i)
$$

where $w: \mathcal{X} \times \mathcal{X} \to \mathbb{R}_+$ is a similarity-based weighting function. A natural choice is:
$$
w(x, y) = \exp\left(-\frac{\|x - y\|^2}{2\sigma^2}\right)
$$

for some bandwidth parameter $\sigma > 0$.

## Problem Statement

**Given:** 
- Training samples $\{x_i\}_{i=1}^n \sim P_{\text{data}}$
- Prior distribution $P_{\text{prior}}$ 
- Generator architecture $G_\theta$
- Vector field architecture $v_\phi$

**Find:** Parameters $\theta^*, \phi^*$ such that the generator $G_{\theta^*}$ can transform samples from $P_{\text{prior}}$ to high-quality samples from $P_{\text{data}}$ in a single forward pass.

**Objective:** We formulate training as a fixed-point problem where the network output should equal itself plus a sample-level correction:
$$
G_\theta(z) = G_\theta(z) + \lambda \cdot d_\phi(G_\theta(z); \mathcal{S}_{\text{data}})
$$

where $\mathcal{S}_{\text{data}} = \{x_1, \ldots, x_n\}$ is the training data and $\lambda > 0$ is a step size parameter.

## Technical Assumptions

1. **Smoothness:** Both $G_\theta$ and $v_\phi$ are differentiable with respect to their parameters
2. **Boundedness:** The vector field $v_\phi$ produces bounded outputs: $\|v_\phi(x,y)\| \leq M$ for some $M > 0$
3. **Lipschitz continuity:** The weighting function $w$ is Lipschitz continuous
4. **Non-degeneracy:** The similarity weights satisfy $\sum_{i=1}^n w(x, x_i) > 0$ for all $x$ in the support of generated samples

# Methodology

## High-Level Approach

Our approach, which we call **Flow Matching with Sample-Level Fields** (FMSF), trains a generator to produce high-quality samples in a single forward pass by leveraging a sample-level vector field that governs how generated samples should move toward the target distribution.

The key insight is to formulate training as making the generator output consistent with a corrected version of itself, where the correction is computed by a learnable vector field operating on individual samples. This avoids iterative refinement during inference while maintaining the modeling capacity of field-based approaches.

## Core Algorithm

### Training Procedure

```
Algorithm 1: Flow Matching with Sample-Level Fields (FMSF)

Input: Training data {x_i}_{i=1}^n, prior P_prior, architectures G_θ, v_φ
Output: Trained parameters θ*, φ*

1. Initialize θ, φ randomly
2. For epoch = 1 to max_epochs:
   3. Sample batch {z_j}_{j=1}^B ~ P_prior
   4. Generate samples: g_j = G_θ(z_j) for j = 1,...,B
   5. Sample reference data batch {x_k}_{k=1}^K from training set
   
   6. For each generated sample g_j:
      7. Compute drift: d_j = Σ_k w(g_j, x_k) * v_φ(g_j, x_k)
      8. Compute target: t_j = g_j + λ * d_j
   
   9. Compute flow matching loss:
      L_flow = (1/B) * Σ_j ||G_θ(z_j) - sg(t_j)||^2
   
   10. Compute field regularization:
       L_reg = (1/B²) * Σ_j Σ_k ||v_φ(g_j, x_k) + v_φ(x_k, g_j)||^2
   
   11. Total loss: L = L_flow + β * L_reg
   12. Update θ, φ using gradient descent on L
```

Here `sg(·)` denotes the stop-gradient operator, preventing backpropagation through the field computation.

### Key Components

**Flow Matching Loss:** The primary objective ensures that the generator output matches the field-corrected target:
$$
\mathcal{L}_{\text{flow}} = \mathbb{E}_{z \sim P_{\text{prior}}} \left[ \left\| G_\theta(z) - \text{sg}\left( G_\theta(z) + \lambda \cdot d_\phi(G_\theta(z); \mathcal{S}_{\text{data}}) \right) \right\|^2 \right]
$$

The stop-gradient operation is crucial as it prevents direct optimization of the field parameters through this loss, enabling indirect optimization of the field's effect on the generator.

**Anti-Symmetry Regularization:** To enforce the anti-symmetry property:
$$
\mathcal{L}_{\text{reg}} = \mathbb{E}_{x,y} \left[ \left\| v_\phi(x,y) + v_\phi(y,x) \right\|^2 \right]
$$

**Weighted Similarity Kernel:** We use an RBF kernel for sample relationships:
$$
w(x,y) = \exp\left( -\frac{\|x-y\|^2}{2\sigma^2} \right)
$$

where $\sigma$ is adapted during training based on the median distance between samples.

## Architecture Design

**Generator $G_\theta$:** Standard convolutional or transformer-based architecture mapping from latent space to data space.

**Vector Field $v_\phi$:** A neural network taking concatenated sample pairs $(x,y)$ as input and outputting a vector in $\mathcal{X}$. To enforce anti-symmetry, we use the architecture:
$$
v_\phi(x,y) = \text{MLP}_\phi([x;y]) - \text{MLP}_\phi([y;x])
$$

where $[·;·]$ denotes concatenation.

## Theoretical Properties

**Convergence:** Under standard regularity conditions and with appropriate learning rates, the training procedure converges to a local minimum of the combined objective. The stop-gradient operation ensures that the field learns to provide useful corrections without interfering with direct generator optimization.

**Fixed-Point Consistency:** At convergence, generated samples satisfy the approximate fixed-point condition:
$$
G_{\theta^*}(z) \approx G_{\theta^*}(z) + \lambda \cdot d_{\phi^*}(G_{\theta^*}(z); \mathcal{S}_{\text{data}})
$$

This implies that $d_{\phi^*}(G_{\theta^*}(z); \mathcal{S}_{\text{data}}) \approx 0$, meaning generated samples require minimal correction.

## Computational Complexity

**Training:** Each iteration requires $O(BK)$ field evaluations where $B$ is the batch size and $K$ is the number of reference samples. The overall complexity per iteration is $O(BK \cdot C_v + B \cdot C_G)$ where $C_v$ and $C_G$ are the costs of evaluating the vector field and generator respectively.

**Inference:** Generation requires only a single forward pass through $G_\theta$, giving $O(C_G)$ complexity per sample - no iterative refinement needed.

## Design Justifications

The weighted influence mechanism draws inspiration from conformal prediction's use of similarity-based weighting (as in the covariate shift extension), where samples with higher similarity receive greater influence. The anti-symmetry property ensures mathematical consistency and prevents trivial solutions. The stop-gradient approach enables indirect optimization similar to techniques used in meta-learning and enables the field to learn meaningful corrections without directly interfering with generator training.