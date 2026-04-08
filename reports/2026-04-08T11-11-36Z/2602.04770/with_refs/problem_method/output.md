# Reconstruction: problem_method (iterative, 3 rounds)
**Paper:** 2602.04770  
**Condition:** with_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  
**Rounds:** 3  
**Best round:** 2 (score 2.8)  
**Converged:** True (score plateau (delta=0.00) and hint stable)  
**Score trajectory:** 2.6 -> 2.8 -> 2.8  

---

# Problem Formulation

We consider the fundamental challenge of learning mappings between probability distributions for generative modeling. Let $\mathcal{X} \subseteq \mathbb{R}^d$ denote the data space and $p_{\text{data}}$ the unknown target data distribution. Traditional generative approaches require iterative procedures at inference time, involving multiple forward passes through neural networks to progressively transform samples from a simple prior distribution $p_0$ (typically standard Gaussian) to the target distribution.

## Notation and Setup

Let $G_\theta: \mathbb{R}^d \to \mathbb{R}^d$ denote a generator network parameterized by $\theta \in \Theta$, where $\Theta$ is the parameter space. During training at iteration $t$, the generator induces an output distribution $p_t = G_{\theta_t} \# p_0$, where $\#$ denotes the pushforward operation. We observe that this distribution naturally evolves over the course of training: $p_0 \to p_1 \to p_2 \to \cdots \to p_T$.

Let $\{x_i\}_{i=1}^n$ denote samples from $p_{\text{data}}$, and let $\{z_i\}_{i=1}^m$ denote samples from the prior $p_0$. We define the trajectory of generator outputs during training as $\{G_{\theta_t}(z)\}_{t=0}^T$ for any fixed $z \sim p_0$.

## Problem Statement

**Given:** 
- Training samples $\{x_i\}_{i=1}^n \sim p_{\text{data}}$
- A prior distribution $p_0$ (e.g., $\mathcal{N}(0, I)$)
- A generator architecture $G_\theta$

**Find:** Parameters $\theta^*$ such that $G_{\theta^*}$ produces high-quality samples from $p_{\text{data}}$ in a single forward pass.

**Guarantee:** The final generator distribution $p^* = G_{\theta^*} \# p_0$ should satisfy:
1. **Sample quality:** $d(p^*, p_{\text{data}}) \leq \epsilon$ for some distance metric $d$ and tolerance $\epsilon > 0$
2. **Single-step inference:** No iterative refinement required at test time
3. **Training stability:** Convergence without adversarial dynamics

## Objective Formulation

The key insight is to formalize the natural evolution of the generator's output distribution during training. We propose to directly model this evolution process by defining a consistency condition between consecutive training iterations.

For a generator $G_\theta$ and a target distribution represented by samples $\{x_i\}_{i=1}^n$, we define the **flow consistency loss**:

$$\mathcal{L}_{\text{consistency}}(\theta) = \mathbb{E}_{z \sim p_0, t \sim \mathcal{U}[0,1]} \left[ \left\| G_\theta(z) - \Phi_t(G_\theta(z), \epsilon_\theta(G_\theta(z), t)) \right\|_2^2 \right]$$

where $\Phi_t$ represents a target trajectory function and $\epsilon_\theta$ is a learned noise prediction network.

Additionally, we incorporate a **boundary condition** that ensures proper alignment with the data distribution:

$$\mathcal{L}_{\text{boundary}}(\theta) = \mathbb{E}_{x \sim p_{\text{data}}} \left[ \left\| x - G_\theta(\mathcal{T}(x)) \right\|_2^2 \right]$$

where $\mathcal{T}: \mathcal{X} \to \mathbb{R}^d$ is a learned encoder that maps data points to the latent space.

The complete objective becomes:
$$\mathcal{L}(\theta) = \mathcal{L}_{\text{consistency}}(\theta) + \lambda \mathcal{L}_{\text{boundary}}(\theta)$$

## Technical Assumptions

1. **Smoothness:** $G_\theta$ is continuously differentiable with respect to both input and parameters
2. **Lipschitz continuity:** $\|\nabla_z G_\theta(z)\|_2 \leq L$ for some constant $L > 0$
3. **Bounded support:** The data distribution $p_{\text{data}}$ has bounded support or exponentially decaying tails
4. **Trajectory regularity:** The optimal trajectory from noise to data admits a smooth parameterization
5. **Encoder invertibility:** The mapping $\mathcal{T}$ is approximately invertible on the data manifold

This formulation leverages the natural evolution of the generator during training while avoiding the need for adversarial objectives or iterative sampling procedures.

# Methodology

## High-Level Approach

Our approach, which we term **Consistency Training**, directly models the evolution of the generator's output distribution during training. Instead of requiring iterative refinement at inference time, we train the generator to be consistent with its own trajectory, ensuring that a single forward pass produces high-quality samples.

The key insight is that during standard neural network training, the generator's output distribution naturally evolves from the prior $p_0$ toward the data distribution $p_{\text{data}}$. We formalize this evolution and enforce consistency conditions that eliminate the need for multi-step sampling.

## Core Algorithm

### Consistency Model Architecture

We define a **consistency model** $f_\theta: \mathbb{R}^d \times [0,1] \to \mathbb{R}^d$ that takes as input a point $x$ and a time parameter $t \in [0,1]$, where $t=0$ corresponds to pure noise and $t=1$ corresponds to clean data. The model satisfies the **consistency property**:

$$f_\theta(x, 0) = x \quad \text{and} \quad f_\theta(x, 1) = \text{clean data}$$

The consistency condition requires that for any point on the trajectory, the model maps it directly to the final clean state:

$$f_\theta(f_\theta(x, t), s) = f_\theta(x, s) \quad \forall s \leq t$$

### Training Procedure

```
Algorithm: Consistency Training

Input: Dataset {x_i}, prior p_0, learning rate η, batch size B
Initialize: θ randomly
Define: Time discretization 0 = t_0 < t_1 < ... < t_T = 1

for epoch = 1 to max_epochs:
    for batch in dataset:
        # Sample noise and time steps
        z ~ p_0^B                           # Sample B noise vectors
        t ~ Uniform[1, T]^B                 # Sample B time indices
        
        # Add noise to data according to schedule
        x_t = √(α_t) * x + √(1-α_t) * z    # Noise schedule
        
        # Consistency loss: model should map x_t directly to x_0
        x_pred = f_θ(x_t, t)
        
        # Self-consistency: f(f(x,t), s) = f(x, s) for s < t
        s ~ Uniform[1, t-1]^B
        x_s = f_θ(x_t, s)
        x_pred_s = f_θ(x_s, s)
        
        # Combined loss
        L_boundary = ||x_pred - x||²
        L_consistency = ||x_pred_s - f_θ(x_t, s)||²
        L_total = L_boundary + λ * L_consistency
        
        # Update parameters
        θ ← θ - η * ∇_θ L_total
        
    end for
end for

# Inference (single step)
sample():
    z ~ p_0
    return f_θ(z, 1)
```

### Noise Schedule Design

We employ a carefully designed noise schedule $\{\alpha_t\}_{t=0}^T$ that governs the interpolation between noise and data:

$$\alpha_t = \cos^2\left(\frac{t \cdot \pi}{2}\right)$$

This schedule ensures smooth transitions and stable training dynamics, with the boundary conditions $\alpha_0 = 1$ (pure data) and $\alpha_T = 0$ (pure noise).

### Network Architecture

The consistency model $f_\theta$ is implemented as a U-Net architecture with the following modifications:

1. **Time embedding:** Time parameter $t$ is embedded using sinusoidal positional encoding
2. **Skip connections:** Residual connections that preserve the input structure
3. **Boundary parameterization:** The network outputs $f_\theta(x,t) = x + g_\theta(x,t) \cdot h(t)$ where $h(0) = 0$ ensures the boundary condition

## Theoretical Properties

### Convergence Analysis

**Theorem:** Under Assumptions 1-5 from the problem formulation, the consistency training objective converges to a global minimum where $f_{\theta^*}(z, 1) \sim p_{\text{data}}$ for $z \sim p_0$.

*Proof sketch:* The consistency condition creates a contraction mapping in the space of trajectories. The boundary condition ensures proper alignment with the data distribution. The combination guarantees convergence to the desired fixed point.

### Sample Quality Guarantee

**Corollary:** The trained consistency model satisfies:
$$\mathbb{E}_{z \sim p_0}[d(f_{\theta^*}(z, 1), p_{\text{data}})] \leq \epsilon$$
where $\epsilon$ depends on the approximation capacity of the network and the discretization error.

## Computational Complexity

- **Training:** $O(T \cdot B \cdot C)$ per iteration, where $T$ is the number of time steps, $B$ is batch size, and $C$ is the cost of one network forward pass
- **Inference:** $O(C)$ - single forward pass, no iterative refinement required
- **Memory:** $O(|\theta|)$ - only model parameters, no additional trajectory storage

## Key Design Decisions

1. **Direct trajectory modeling:** Unlike diffusion models that learn the score function, we directly parameterize the mapping from any point on the trajectory to the final result
2. **Self-consistency enforcement:** The consistency condition eliminates accumulated errors from iterative procedures
3. **Boundary condition integration:** Explicit enforcement of data alignment through the boundary loss
4. **Single-step inference:** The trained model requires only one forward pass, dramatically reducing computational cost

This methodology addresses the core challenge of single-step high-quality generation while maintaining training stability and avoiding adversarial dynamics.
