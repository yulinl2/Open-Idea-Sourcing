# Reconstruction: problem_method (iterative, 12 rounds)
**Paper:** 2602.04770  
**Condition:** with_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  
**Rounds:** 12  
**Best round:** 6 (score 3.4)  
**Converged:** True (reached max rounds (12))  
**Score trajectory:** 3.2 -> 2.6 -> 3.0 -> 3.0 -> 3.0 -> 3.4 -> 3.2 -> 3.0 -> 2.8 -> 3.2 -> 3.0 -> 2.8  

---

# Problem Formulation

## Notation and Setup

Let $\mathcal{X} \subseteq \mathbb{R}^d$ denote the data space and $P_{\text{data}}$ denote the unknown target data distribution over $\mathcal{X}$. Let $P_{\text{noise}}$ denote a simple noise distribution (e.g., standard Gaussian) from which we can easily sample. We consider a parametric generator $G_\theta: \mathcal{X} \to \mathcal{X}$ with parameters $\theta \in \Theta$, where $\Theta$ is the parameter space.

During training, we observe samples $\{x_i\}_{i=1}^n \sim P_{\text{data}}$ and can generate samples $\{z_j\}_{j=1}^m \sim P_{\text{noise}}$. Let $P_{\theta}$ denote the distribution induced by the generator, i.e., if $Z \sim P_{\text{noise}}$, then $G_\theta(Z) \sim P_{\theta}$.

## Distribution Evolution Framework

The key insight is to view training as governing the evolution of the generator's output distribution $P_{\theta(t)}$ over training iterations $t$. We define a **distribution drift field** $\mathbf{F}: \mathcal{X} \times \mathcal{X} \to \mathbb{R}^d$ that specifies how samples should move based on interactions between the current generated distribution and the target distribution.

For any sample $x \in \mathcal{X}$, define the drift vector:
$$\mathbf{v}(x; P_\theta, P_{\text{data}}) = \mathbb{E}_{x' \sim P_{\text{data}}}[\mathbf{F}(x, x')] - \mathbb{E}_{x' \sim P_\theta}[\mathbf{F}(x, x')]$$

This represents the net force on sample $x$ due to attraction from real data samples and repulsion from other generated samples.

## Equilibrium Condition

We seek an equilibrium where the drift field vanishes, i.e., for all $x$ in the support of $P_\theta^*$:
$$\mathbf{v}(x; P_{\theta^*}, P_{\text{data}}) = \mathbf{0}$$

This equilibrium condition ensures that the forces from real and generated samples balance, indicating that $P_{\theta^*} = P_{\text{data}}$.

## Problem Statement

**Given:** Training samples $\{x_i\}_{i=1}^n \sim P_{\text{data}}$, noise distribution $P_{\text{noise}}$, generator architecture $G_\theta$, and interaction function $\mathbf{F}$.

**Find:** Parameters $\theta^*$ such that the induced distribution $P_{\theta^*}$ satisfies the equilibrium condition.

**Objective:** We formulate this as learning the drift prediction function. The generator should learn to predict where samples should move:
$$\mathcal{L}(\theta) = \mathbb{E}_{z \sim P_{\text{noise}}} \left\| G_\theta(z) - (z + \mathbf{v}(z; P_\theta, P_{\text{data}})) \right\|^2$$

## Technical Assumptions

1. **Smoothness:** The generator $G_\theta$ is differentiable with respect to $\theta$, and the interaction function $\mathbf{F}$ is smooth.

2. **Bounded Support:** Both $P_{\text{data}}$ and $P_{\text{noise}}$ have bounded support to ensure well-defined expectations.

3. **Interaction locality:** The interaction function $\mathbf{F}(x, x')$ depends on the similarity between $x$ and $x'$, with stronger interactions for nearby samples.

4. **Equilibrium existence:** The system admits at least one equilibrium solution where the drift field vanishes.

These assumptions ensure that the training dynamics are well-defined and that the equilibrium corresponds to successful distribution matching.

# Methodology

## High-Level Approach

Our approach, **Drift Field Networks (DFN)**, treats generative modeling as learning to predict optimal sample movements in a dynamical system. Instead of adversarial training or likelihood maximization, we directly learn a vector field that guides samples from noise toward their ideal positions in the data distribution.

The core insight is that at equilibrium, generated samples should experience zero net drift when considering both attraction to real data and repulsion from other generated samples. During training, we explicitly compute these drift vectors and train the generator to predict where samples should move.

## Core Algorithm

### Interaction Function Design

We define the interaction function as:
$$\mathbf{F}(x, x') = K(x, x') \cdot \frac{x' - x}{\|x' - x\|_2 + \epsilon}$$

where $K(x, x') = \exp(-\|x - x'\|_2^2 / (2\sigma^2))$ is a Gaussian kernel that controls interaction strength based on similarity, and $\epsilon > 0$ prevents division by zero.

### Drift Computation

For a generated sample $G_\theta(z)$, we compute:

**Data attraction:**
$$\mathbf{a}_{\text{data}}(G_\theta(z)) = \frac{1}{n} \sum_{i=1}^n \mathbf{F}(G_\theta(z), x_i)$$

**Generated repulsion:**
$$\mathbf{r}_{\text{gen}}(G_\theta(z)) = \frac{1}{m-1} \sum_{j \neq k} \mathbf{F}(G_\theta(z), G_\theta(z_j))$$
where $z = z_k$ for some $k$.

**Net drift:**
$$\mathbf{v}(G_\theta(z)) = \mathbf{a}_{\text{data}}(G_\theta(z)) - \mathbf{r}_{\text{gen}}(G_\theta(z))$$

### Training Algorithm

```
Algorithm: Drift Field Network Training

Input: Data samples {x_i}, noise distribution P_noise, generator G_θ
Output: Trained generator parameters θ*

1. Initialize θ randomly
2. For each training iteration t:
   a. Sample noise batch {z_j} ~ P_noise
   b. Generate samples {G_θ(z_j)}
   c. For each generated sample G_θ(z_j):
      - Compute data attraction: a_data(G_θ(z_j))
      - Compute generated repulsion: r_gen(G_θ(z_j))  
      - Compute net drift: v(G_θ(z_j)) = a_data - r_gen
   d. Compute target positions: y_j = z_j + v(G_θ(z_j))
   e. Update θ to minimize: L = (1/m) Σ ||G_θ(z_j) - y_j||²
3. Return θ*
```

## Key Design Decisions

### Fixed-Point Formulation
The target position $y_j = z_j + \mathbf{v}(G_\theta(z_j))$ creates a fixed-point iteration where the generator learns to predict its own optimal output. This is inspired by fixed-point theory, where solutions satisfy $x = f(x)$.

### Kernel Bandwidth Selection
The bandwidth $\sigma$ in the interaction kernel controls the locality of interactions. We adapt it during training: $\sigma_t = \sigma_0 \cdot \gamma^t$ where $\gamma < 1$, starting with global interactions and progressively focusing on local refinements.

### Batch-wise Interactions
To make the method computationally tractable, we approximate the full distribution expectations using mini-batches, following the empirical process principle from the conformal prediction literature.

## Theoretical Properties

### Convergence Analysis
Under mild regularity conditions on $G_\theta$ and $\mathbf{F}$:

1. **Fixed-point existence:** The mapping $T(x) = x + \mathbf{v}(x; P_\theta, P_{\text{data}})$ has at least one fixed point when $P_\theta = P_{\text{data}}$.

2. **Convergence guarantee:** If the generator has sufficient capacity and the learning rate satisfies standard conditions, the training dynamics converge to a neighborhood of the equilibrium.

### Computational Complexity
- **Per iteration:** $O(nm + m^2)$ where $n$ is the number of data samples and $m$ is the batch size
- **Memory:** $O(n + m)$ for storing samples and computing interactions
- **Compared to GANs:** Similar computational cost but avoids the instability of adversarial training

The method scales favorably as it requires only forward passes and simple vector computations, without the discriminator overhead of adversarial approaches.
