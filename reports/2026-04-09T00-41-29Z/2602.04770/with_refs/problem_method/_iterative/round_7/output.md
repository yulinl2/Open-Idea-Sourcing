# Problem Formulation

## Notation and Problem Setup

Let $\mathcal{X} \subset \mathbb{R}^d$ denote the data space and $P_{\text{data}}$ denote the unknown target data distribution. We consider a generator network $G_\theta: \mathcal{Z} \to \mathcal{X}$ parameterized by $\theta \in \Theta$, where $\mathcal{Z} \subset \mathbb{R}^k$ is a latent space equipped with a known prior distribution $P_{\text{prior}}$ (typically standard Gaussian). The generator defines a pushforward distribution $P_{\theta} = G_\theta \# P_{\text{prior}}$, where $(G_\theta \# P_{\text{prior}})(A) = P_{\text{prior}}(G_\theta^{-1}(A))$ for any measurable set $A \subset \mathcal{X}$.

During training, we observe a sequence of parameter updates $\{\theta^{(t)}\}_{t=0}^T$ that evolve the pushforward distribution from an initial $P_{\theta^{(0)}}$ toward the target $P_{\text{data}}$. Let $\mathcal{P}(\mathcal{X})$ denote the space of probability measures on $\mathcal{X}$ equipped with an appropriate metric $d(\cdot, \cdot)$ (e.g., Wasserstein distance).

## Formal Problem Statement

**Given:** 
- A dataset $\{x_i\}_{i=1}^n \sim P_{\text{data}}$ 
- A generator architecture $G_\theta: \mathcal{Z} \to \mathcal{X}$
- A prior distribution $P_{\text{prior}}$ on $\mathcal{Z}$

**Find:** A training procedure that learns parameters $\theta^*$ such that the generator produces high-quality samples in a single forward pass, i.e., $x \sim G_{\theta^*} \# P_{\text{prior}}$ should be indistinguishable from $x \sim P_{\text{data}}$.

**Guarantee:** The training procedure should converge to an equilibrium where $P_{\theta^*} = P_{\text{data}}$.

## Objective Formulation

We formulate the training objective through a vector field $v_t: \Theta \to \mathbb{R}^{|\Theta|}$ that governs the evolution of the generator's pushforward distribution. The key insight is to define this field such that it vanishes when the generated and target distributions match.

Let $\mathcal{F}: \Theta \to \mathbb{R}$ be a functional that measures the discrepancy between $P_{\theta}$ and $P_{\text{data}}$. We seek a vector field $v_t(\theta)$ with the following properties:

1. **Equilibrium condition:** $v_t(\theta^*) = 0 \iff P_{\theta^*} = P_{\text{data}}$
2. **Symmetry property:** If we define $\tilde{v}_t(\theta)$ as the field obtained by swapping the roles of $P_{\theta}$ and $P_{\text{data}}$, then $v_t(\theta) = -\tilde{v}_t(\theta)$ when $P_{\theta} = P_{\text{data}}$

The training objective becomes finding a fixed point of the mapping:
$$\theta \mapsto \theta + v_t(\theta)$$

This formulation leverages the iterative nature of neural network training by defining how the transformation from prior to data should evolve at each step.

## Technical Assumptions

**A1 (Regularity):** The generator $G_\theta$ is differentiable with respect to $\theta$, and the pushforward operation $\theta \mapsto P_{\theta}$ is well-defined and continuous in an appropriate topology.

**A2 (Identifiability):** The mapping $\theta \mapsto P_{\theta}$ is injective in a neighborhood of the optimal parameters, ensuring that matching distributions implies matching parameters.

**A3 (Bounded Support):** The data distribution $P_{\text{data}}$ has bounded support, ensuring finite moments and well-defined Wasserstein distances.

**A4 (Stop-gradient compatibility):** The vector field $v_t(\theta)$ can be computed without backpropagating through distribution-dependent quantities, enabling indirect optimization paths.

These assumptions are justified by the need to: (A1) enable gradient-based optimization; (A2) ensure uniqueness of the solution; (A3) guarantee numerical stability; (A4) allow practical implementation of the training algorithm.

The connection to prior formulations lies in the conformal prediction framework's use of exchangeability and symmetry properties. Just as conformal methods define nonconformity scores that are symmetric under permutation of data points, our approach defines a vector field that exhibits symmetry properties under swapping of distributions, guaranteeing equilibrium when distributions match.

# Methodology

## High-Level Approach

Our proposed method, **Flow Matching Networks (FMN)**, trains generative models by defining a continuous-time vector field that governs how the generator's output distribution should evolve during training. The key innovation is to construct this field using a symmetry principle: the field should vanish precisely when the generated and target distributions are equal.

The approach operates by: (1) defining a time-dependent vector field $v_t(\theta)$ in parameter space that respects distributional symmetry; (2) training the generator to satisfy a fixed-point condition where the network's output equals its output plus a correction term; (3) using stop-gradient operations to enable indirect optimization of the governing field.

## Core Algorithm

### Vector Field Construction

We define the vector field $v_t: \Theta \to \mathbb{R}^{|\Theta|}$ through a symmetry-based construction. Let $\phi: \mathcal{X} \to \mathbb{R}^m$ be a feature map (e.g., from a pre-trained network), and define the empirical distribution matching loss:

$$\mathcal{L}_{\text{match}}(\theta) = \left\|\frac{1}{n}\sum_{i=1}^n \phi(x_i) - \mathbb{E}_{z \sim P_{\text{prior}}}[\phi(G_\theta(z))]\right\|_2^2$$

The vector field is constructed as:
$$v_t(\theta) = \nabla_\theta \mathcal{L}_{\text{match}}(\theta) - \text{stopgrad}(\nabla_\theta \mathcal{L}_{\text{match}}(\tilde{\theta}))$$

where $\tilde{\theta}$ represents parameters that would generate the target distribution, and $\text{stopgrad}(\cdot)$ prevents gradient flow. This construction ensures the symmetry property: when $P_\theta = P_{\text{data}}$, we have $\tilde{\theta} = \theta$, making $v_t(\theta) = 0$.

### Fixed-Point Training Objective

The training objective seeks parameters $\theta^*$ satisfying the fixed-point condition:
$$\theta^* = \theta^* + \alpha v_t(\theta^*)$$

for some step size $\alpha > 0$. This is equivalent to finding $\theta^*$ such that $v_t(\theta^*) = 0$.

In practice, we optimize the surrogate objective:
$$\mathcal{L}_{\text{fixed}}(\theta) = \|v_t(\theta)\|_2^2$$

### Complete Training Algorithm

```
Algorithm: Flow Matching Networks Training

Input: Dataset {x_i}_{i=1}^n, generator G_θ, feature map φ, learning rate η
Output: Trained parameters θ*

1. Initialize θ^(0) randomly
2. For t = 0, 1, 2, ..., T_max:
   
   3. Sample batch {x_j}_{j=1}^B from dataset
   4. Sample latent codes {z_j}_{j=1}^B ~ P_prior
   
   5. Compute generated samples: g_j = G_θ^(t)(z_j)
   6. Compute feature statistics:
      - μ_data = (1/B) Σ_j φ(x_j)  
      - μ_gen = (1/B) Σ_j φ(g_j)
   
   7. Compute vector field:
      - ∇_match = ∇_θ ||μ_data - μ_gen||_2^2
      - v_t = ∇_match - stopgrad(∇_match_target)
   
   8. Update parameters: θ^(t+1) = θ^(t) - η · v_t
   
   9. If ||v_t|| < ε, break (convergence)

10. Return θ* = θ^(T)
```

## Key Design Decisions

**Symmetry-based field construction:** The vector field design is motivated by the conformal prediction principle that symmetric constructions lead to exact coverage guarantees. By ensuring $v_t(\theta) = -v_t(\tilde{\theta})$ when distributions match, we guarantee a unique equilibrium.

**Stop-gradient operations:** Following the conformal prediction methodology of avoiding direct optimization of distribution-dependent quantities, we use stop-gradient operations to enable indirect optimization paths that are more stable than direct adversarial training.

**Feature-based matching:** Rather than matching distributions directly, we match feature statistics $\phi(x)$, which provides a tractable approximation while maintaining the symmetry properties of the vector field.

## Theoretical Properties

**Convergence:** Under standard regularity conditions (Lipschitz continuity of $G_\theta$, bounded feature maps $\phi$), the fixed-point iteration converges to a unique equilibrium $\theta^*$ satisfying $v_t(\theta^*) = 0$.

**Consistency:** At the equilibrium, the symmetry property ensures that $P_{\theta^*} = P_{\text{data}}$ in the feature space defined by $\phi$. For sufficiently rich feature maps (e.g., from universal approximators), this implies distributional equality.

**Stability:** The vector field construction avoids the instabilities of adversarial training by eliminating the need for a separate discriminator network. The fixed-point formulation provides inherent stability guarantees.

## Computational Complexity

The computational complexity per training iteration is $O(B \cdot C_G + B \cdot C_\phi)$, where $B$ is the batch size, $C_G$ is the cost of a generator forward pass, and $C_\phi$ is the cost of feature extraction. This is comparable to standard GAN training but eliminates the discriminator overhead.

The memory complexity is $O(|\Theta| + B \cdot d)$ for storing parameters and batch features, which scales linearly with model size and batch size. The stop-gradient operations do not introduce additional memory overhead beyond standard automatic differentiation.