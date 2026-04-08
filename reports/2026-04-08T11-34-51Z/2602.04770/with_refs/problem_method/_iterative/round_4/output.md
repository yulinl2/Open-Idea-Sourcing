# Problem Formulation

## Notation and Problem Setup

Let $\mathcal{X}$ denote the data space and $p_{\text{data}}$ the unknown target data distribution over $\mathcal{X}$. We consider a generator network $G_\theta: \mathcal{Z} \to \mathcal{X}$ parameterized by $\theta \in \Theta$, where $\mathcal{Z}$ is a latent space with a simple prior distribution $p_z$ (typically standard Gaussian). The generator induces a distribution $p_\theta$ over $\mathcal{X}$ through the pushforward: $p_\theta = G_\theta \# p_z$.

During training, we observe the evolution of the generator's output distribution. At training step $t$, let $p_t = p_{\theta_t}$ denote the current generator distribution. We define the **distribution evolution trajectory** as the sequence $\{p_t\}_{t=0}^T$ where $T$ is the total number of training steps.

For any two distributions $p$ and $q$ over $\mathcal{X}$, we define a **sample interaction function** $\Phi: \mathcal{X} \times \mathcal{X} \to \mathbb{R}$ that measures the influence between samples. This function satisfies:
- $\Phi(x, y) = \Phi(y, x)$ (symmetry)
- $\Phi(x, x) = 0$ (no self-interaction)
- $|\Phi(x, y)| \to 0$ as $d(x, y) \to \infty$ for some distance metric $d$

Given samples $\{x_i\}_{i=1}^n \sim p_{\text{data}}$ and $\{z_j\}_{j=1}^m \sim p_t$, we define the **distribution interaction energy** as:

$$E_t = \frac{1}{nm} \sum_{i=1}^n \sum_{j=1}^m \Phi(x_i, z_j) - \frac{1}{m^2} \sum_{j=1}^m \sum_{k \neq j} \Phi(z_j, z_k)$$

The first term represents **attraction** between generated samples and real data, while the second term represents **repulsion** among generated samples to encourage diversity.

## Formal Problem Statement

**Given:** 
- A dataset $\mathcal{D} = \{x_i\}_{i=1}^n$ sampled i.i.d. from $p_{\text{data}}$
- A generator architecture $G_\theta: \mathcal{Z} \to \mathcal{X}$
- A sample interaction function $\Phi: \mathcal{X} \times \mathcal{X} \to \mathbb{R}$

**Find:** A training procedure that evolves $\theta_t$ such that:
1. The generator produces high-quality samples in a single forward pass
2. The training converges to an equilibrium where distribution forces balance

**Guarantee:** At equilibrium, the expected interaction energy satisfies:
$$\mathbb{E}_{x \sim p_{\text{data}}, z \sim p_{\theta^*}}[\Phi(x, z)] = \mathbb{E}_{z_1, z_2 \sim p_{\theta^*}}[\Phi(z_1, z_2)]$$

where $\theta^*$ represents the equilibrium parameters.

## Objective Formulation

We formulate the training objective as minimizing the **distribution evolution loss**:

$$\mathcal{L}(\theta) = \mathbb{E}_{x \sim p_{\text{data}}} \mathbb{E}_{z \sim p_\theta} [-\Phi(x, z)] + \lambda \mathbb{E}_{z_1, z_2 \sim p_\theta} [\Phi(z_1, z_2)]$$

where $\lambda > 0$ is a hyperparameter controlling the strength of sample repulsion. The negative sign in the first term encourages attraction between generated and real samples, while the second term encourages repulsion among generated samples.

In practice, we approximate this objective using finite samples:

$$\hat{\mathcal{L}}(\theta) = -\frac{1}{nm} \sum_{i=1}^n \sum_{j=1}^m \Phi(x_i, G_\theta(z_j)) + \frac{\lambda}{m(m-1)} \sum_{j=1}^m \sum_{k \neq j} \Phi(G_\theta(z_j), G_\theta(z_k))$$

## Technical Assumptions

1. **Smoothness:** The generator $G_\theta$ is differentiable with respect to $\theta$, and the interaction function $\Phi$ is differentiable with respect to both arguments.

2. **Bounded Interaction:** There exists $M > 0$ such that $|\Phi(x, y)| \leq M$ for all $x, y \in \mathcal{X}$.

3. **Lipschitz Continuity:** The interaction function $\Phi$ is Lipschitz continuous: $|\Phi(x_1, y_1) - \Phi(x_2, y_2)| \leq L(\|x_1 - x_2\| + \|y_1 - y_2\|)$ for some $L > 0$.

4. **Non-degeneracy:** The generator mapping $G_\theta$ has sufficient capacity to approximate the target distribution, i.e., there exists $\theta^* \in \Theta$ such that $p_{\theta^*}$ can approximate $p_{\text{data}}$ arbitrarily well.

5. **Sample Complexity:** We assume access to sufficient samples such that the empirical approximation $\hat{\mathcal{L}}(\theta)$ concentrates around the true objective $\mathcal{L}(\theta)$.

These assumptions ensure that the training objective is well-defined, the optimization landscape is tractable, and the equilibrium condition can be meaningfully achieved through gradient-based optimization.

# Methodology

## High-Level Approach

Our proposed method, **Distribution Evolution via Sample Interactions (DESI)**, leverages the natural evolution of the generator's output distribution during training by explicitly governing this evolution through sample-level interactions. Rather than requiring iterative refinement at inference time, we design the training process to directly optimize for single-step generation quality through a physics-inspired interaction framework.

The key insight is to treat generated samples and real data samples as particles in a dynamical system, where attractive forces pull generated samples toward real data while repulsive forces among generated samples prevent mode collapse. The equilibrium of this system corresponds to a generator that produces diverse, high-quality samples.

## Core Algorithm

The DESI training procedure consists of the following components:

### Interaction Function Design

We propose a **kernel-based interaction function** that captures both local similarity and global distribution properties:

$$\Phi(x, y) = \exp\left(-\frac{\|x - y\|^2}{2\sigma^2}\right) - \tau$$

where $\sigma > 0$ controls the interaction range and $\tau \geq 0$ is a baseline offset that ensures $\mathbb{E}_{x,y}[\Phi(x,y)] = 0$ when $x,y$ are sampled from the same distribution. This design ensures that:
- Similar samples have positive interaction (attraction when $\|x-y\|$ is small)
- Dissimilar samples have negative interaction (repulsion when $\|x-y\|$ is large)
- The function decays smoothly with distance

### Training Algorithm

```
Algorithm 1: DESI Training
Input: Dataset D = {x_i}_{i=1}^n, generator G_θ, batch size m, learning rate η, λ > 0
Output: Trained generator parameters θ*

1. Initialize θ randomly
2. For t = 1 to T:
   a. Sample real data batch: {x_i}_{i=1}^n ~ D
   b. Sample latent codes: {z_j}_{j=1}^m ~ p_z
   c. Generate samples: {g_j}_{j=1}^m where g_j = G_θ(z_j)
   
   d. Compute attraction term:
      L_attract = -(1/nm) Σ_i Σ_j Φ(x_i, g_j)
   
   e. Compute repulsion term:
      L_repel = λ/(m(m-1)) Σ_j Σ_{k≠j} Φ(g_j, g_k)
   
   f. Total loss: L = L_attract + L_repel
   
   g. Update: θ ← θ - η ∇_θ L
   
   h. Adaptive σ update: σ ← σ * decay_factor
   
3. Return θ*
```

### Adaptive Interaction Range

To handle the evolving quality of generated samples, we employ an **adaptive interaction range** schedule. Initially, $\sigma$ is set large to encourage broad distribution coverage. As training progresses, $\sigma$ gradually decreases to focus on fine-grained sample quality:

$$\sigma_t = \sigma_0 \cdot \exp(-\beta t / T)$$

where $\sigma_0$ is the initial range, $\beta > 0$ controls the decay rate, and $T$ is the total training steps.

## Theoretical Properties

### Equilibrium Analysis

At equilibrium, the gradient of our objective vanishes: $\nabla_\theta \mathcal{L}(\theta^*) = 0$. This occurs when:

$$\mathbb{E}_{x \sim p_{\text{data}}, g \sim p_{\theta^*}} [\nabla_g \Phi(x, g)] = \lambda \mathbb{E}_{g_1, g_2 \sim p_{\theta^*}} [\nabla_{g_1} \Phi(g_1, g_2)]$$

This equilibrium condition ensures that the attractive forces from real data balance the repulsive forces among generated samples, leading to a generator that produces diverse samples concentrated around the data distribution.

### Convergence Properties

**Theorem:** Under Assumptions 1-5 and with appropriate choice of learning rate $\eta$ and repulsion strength $\lambda$, the DESI algorithm converges to a stationary point of $\mathcal{L}(\theta)$.

*Proof Sketch:* The bounded and Lipschitz properties of $\Phi$ ensure that $\mathcal{L}(\theta)$ is well-behaved. The gradient updates follow standard SGD convergence analysis, with the sample complexity assumption ensuring that the empirical objective concentrates around the true objective.

### Sample Complexity

The number of samples required for $\epsilon$-accurate estimation of the interaction terms scales as $O(\epsilon^{-2})$ due to the bounded nature of $\Phi$. This is comparable to standard generative model training requirements.

## Computational Complexity

**Training Complexity:** Each training step requires:
- $O(nm)$ operations for attraction term computation
- $O(m^2)$ operations for repulsion term computation  
- $O(|\theta|)$ operations for gradient computation and parameter updates

Total per-step complexity: $O(nm + m^2 + |\theta|)$

**Inference Complexity:** Once trained, sample generation requires only a single forward pass through $G_\theta$: $O(|\theta|)$ operations per sample.

**Memory Complexity:** $O(n + m + |\theta|)$ for storing data samples, generated samples, and model parameters.

## Design Justifications

1. **Kernel-based Interactions:** The exponential kernel naturally captures local similarity while the offset $\tau$ ensures proper normalization. This design is inspired by particle interaction potentials in physics.

2. **Dual Force System:** The attraction-repulsion framework directly addresses the fundamental challenge of balancing sample quality (attraction to data) with diversity (repulsion among samples).

3. **Adaptive Range:** The decreasing $\sigma$ schedule allows the model to first learn global distribution structure, then refine local details, similar to coarse-to-fine optimization strategies.

4. **Single-Step Generation:** By optimizing the equilibrium of sample interactions during training, we eliminate the need for iterative refinement at inference time, achieving the desired efficiency.

The DESI framework provides a principled approach to single-step generative modeling by explicitly governing distribution evolution through sample interactions, offering both theoretical guarantees and practical efficiency.