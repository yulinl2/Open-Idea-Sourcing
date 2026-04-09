# Problem Formulation

## Notation and Setup

Let $\mathcal{X} \subseteq \mathbb{R}^d$ denote the data space and $P_{\text{data}}$ be the unknown target data distribution over $\mathcal{X}$. Let $P_{\text{prior}}$ be a simple prior distribution (e.g., standard Gaussian) from which we can easily sample. We denote by $\mathcal{P}(\mathcal{X})$ the space of probability distributions over $\mathcal{X}$.

For a neural network $G_\theta: \mathcal{X} \to \mathcal{X}$ parameterized by $\theta \in \Theta$, we define the **pushforward operation** $G_\theta \sharp P_{\text{prior}}$ as the distribution of $G_\theta(z)$ when $z \sim P_{\text{prior}}$. This represents how the generator transforms the prior distribution into an output distribution.

During training, we consider a sequence of generator states $G_{\theta^{(t)}}$ for iterations $t = 0, 1, 2, \ldots$. At each iteration, we have access to:
- A batch of real data samples $\{x_i\}_{i=1}^n \sim P_{\text{data}}$  
- A batch of generated samples $\{G_{\theta^{(t)}}(z_i)\}_{i=1}^m$ where $z_i \sim P_{\text{prior}}$

## The Sample-Level Vector Field

We define a **vector field** $v_\phi: \mathcal{X} \times \mathcal{X} \to \mathcal{X}$ parameterized by $\phi \in \Phi$, which takes two inputs:
- $x_0$: a sample from the current generator distribution $G_{\theta^{(t)}} \sharp P_{\text{prior}}$
- $x_1$: a sample from the target data distribution $P_{\text{data}}$

The field outputs a direction vector indicating how sample $x_0$ should move to better align the generator distribution with the data distribution.

**Anti-symmetry Property**: We require that $v_\phi$ satisfies
$$v_\phi(x_0, x_1) = -v_\phi(x_1, x_0)$$
for all $x_0, x_1 \in \mathcal{X}$. This ensures that when we swap the roles of the two distributions, the field direction reverses, and importantly, $v_\phi(x, x) = 0$ for any $x$.

## Problem Statement

**Given**: 
- Training data $\{x_i\}_{i=1}^N \sim P_{\text{data}}$
- Prior distribution $P_{\text{prior}}$ 
- Generator architecture $G_\theta$ and vector field architecture $v_\phi$

**Find**: Parameters $\theta^*, \phi^*$ such that the trained generator $G_{\theta^*}$ can produce high-quality samples in a single forward pass.

**Guarantee**: The generator distribution $G_{\theta^*} \sharp P_{\text{prior}}$ should approximate the data distribution $P_{\text{data}}$ with minimal distributional distance.

## Training Objective

The core training principle is to make the generator output equal to itself plus a correction computed by the vector field:

$$G_{\theta^{(t+1)}}(z) = G_{\theta^{(t)}}(z) + v_\phi(G_{\theta^{(t)}}(z), x_{\text{data}})$$

where $x_{\text{data}}$ is sampled from the training data. However, to prevent direct backpropagation through the field computation, we use a **stop-gradient** operation:

$$\mathcal{L}(\theta, \phi) = \mathbb{E}_{z \sim P_{\text{prior}}, x \sim P_{\text{data}}} \left[ \left\| G_\theta(z) - \text{sg}[G_\theta(z) + v_\phi(G_\theta(z), x)] \right\|^2 \right]$$

where $\text{sg}[\cdot]$ denotes the stop-gradient operator that treats its argument as a constant during backpropagation.

## Technical Assumptions

1. **Smoothness**: Both $G_\theta$ and $v_\phi$ are differentiable with respect to their parameters and inputs.

2. **Bounded Support**: The data distribution $P_{\text{data}}$ has bounded support, and the generator outputs remain in a bounded region during training.

3. **Anti-symmetry**: The vector field satisfies $v_\phi(x_0, x_1) = -v_\phi(x_1, x_0)$ by construction.

4. **Lipschitz Continuity**: The vector field $v_\phi$ is Lipschitz continuous to ensure training stability.

This formulation connects to conformal prediction methodology in that both approaches deal with distribution alignment and leverage symmetry properties for theoretical guarantees, though our anti-symmetric field operates on individual samples rather than prediction intervals.

# Methodology

## High-Level Approach

Our approach, **Flow Matching**, trains a generator to produce high-quality samples in a single forward pass by learning a vector field that governs how generated samples should move to match the target distribution. The key insight is to formulate training as a fixed-point problem where the generator output equals itself plus a field-computed correction, while using stop-gradient operations to enable indirect optimization.

## Core Algorithm

The Flow Matching algorithm alternates between updating the vector field $v_\phi$ and the generator $G_\theta$:

```
Algorithm: Flow Matching Training

Input: Training data {x_i}_{i=1}^N, prior P_prior, learning rates λ_θ, λ_φ
Initialize: θ^(0), φ^(0)

For t = 0, 1, 2, ..., T_max:
    // Sample batches
    {z_j}_{j=1}^m ~ P_prior
    {x_i}_{i=1}^n ~ training data
    
    // Generate current samples  
    {x0_j = G_θ^(t)(z_j)}_{j=1}^m
    
    // Compute vector field updates
    For each pair (x0_j, x_i):
        v_ji = v_φ^(t)(x0_j, x_i)
        v_ij = -v_ji  // Anti-symmetry
    
    // Update vector field parameters
    L_φ = (1/mn) Σ_j Σ_i ||x0_j + v_ji - x_i||^2
    φ^(t+1) = φ^(t) - λ_φ ∇_φ L_φ
    
    // Update generator parameters with stop-gradient
    target_j = sg[x0_j + v_φ^(t+1)(x0_j, x_i)]  // Stop gradient here
    L_θ = (1/m) Σ_j ||G_θ^(t)(z_j) - target_j||^2  
    θ^(t+1) = θ^(t) - λ_θ ∇_θ L_θ

Return: G_θ^(T_max)
```

## Vector Field Architecture

The anti-symmetric vector field is constructed as:
$$v_\phi(x_0, x_1) = \text{MLP}_\phi([x_0; x_1; x_0 - x_1]) - \text{MLP}_\phi([x_1; x_0; x_1 - x_0])$$

This architecture automatically satisfies the anti-symmetry property $v_\phi(x_0, x_1) = -v_\phi(x_1, x_0)$ and ensures $v_\phi(x, x) = 0$.

## Training Dynamics

The stop-gradient operation creates an indirect optimization scheme:

1. **Vector Field Update**: $v_\phi$ learns to predict the displacement needed to transform generated samples toward data samples
2. **Generator Update**: $G_\theta$ learns to directly produce samples that, when combined with the field correction, match the target locations

This decoupling prevents the generator from simply learning to cancel out the vector field, which would lead to trivial solutions.

## Design Justifications

**Anti-symmetry Design**: Inspired by conformal prediction's use of symmetric constructions for coverage guarantees, our anti-symmetric field ensures that swapping distribution roles reverses the flow direction, providing a principled way to handle the asymmetry between generated and real samples.

**Stop-Gradient Operation**: Following techniques from self-supervised learning, the stop-gradient prevents direct optimization of the field target, forcing the generator to learn meaningful transformations rather than exploiting the training objective.

**Fixed-Point Formulation**: The training objective $G_\theta(z) = G_\theta(z) + v_\phi(G_\theta(z), x)$ creates a fixed-point iteration where convergence implies the generator produces samples that require no further correction.

## Theoretical Properties

**Convergence**: Under Lipschitz continuity assumptions on $v_\phi$ and $G_\theta$, and with appropriate learning rate schedules, the training dynamics converge to a fixed point where $v_\phi(G_\theta(z), x) \approx 0$ for samples $x$ from the data distribution.

**Distribution Matching**: At convergence, the generator distribution $G_\theta \sharp P_{\text{prior}}$ approximates $P_{\text{data}}$ in the sense that the expected field magnitude $\mathbb{E}_{x_0 \sim G_\theta \sharp P_{\text{prior}}, x_1 \sim P_{\text{data}}}[\|v_\phi(x_0, x_1)\|]$ is minimized.

## Computational Complexity

- **Training**: $O(mn \cdot C)$ per iteration, where $m$ is the generated batch size, $n$ is the real data batch size, and $C$ is the cost of vector field evaluation
- **Inference**: $O(1)$ forward pass through $G_\theta$, achieving the desired single-step generation
- **Memory**: Linear in batch size, with no need to store intermediate states during generation

The method scales efficiently to high-dimensional data as the vector field operates on individual samples rather than requiring expensive iterative refinement procedures at inference time.