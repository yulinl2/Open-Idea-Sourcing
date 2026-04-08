# Reconstruction: problem_method (iterative, 5 rounds)
**Paper:** 2602.04770  
**Condition:** with_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  
**Rounds:** 5  
**Best round:** 1 (score 3.2)  
**Converged:** True (reached max rounds (5))  
**Score trajectory:** 3.2 -> 2.6 -> 3.0 -> 3.0 -> 3.0  

---

# Problem Formulation

## Notation and Problem Setup

Let $\mathcal{X}$ denote the data space and $\mathcal{Z}$ denote the noise space, both equipped with appropriate probability measures. We consider two probability distributions: a noise distribution $p_z$ supported on $\mathcal{Z}$ (typically a simple distribution like standard Gaussian) and a target data distribution $p_x$ supported on $\mathcal{X}$. 

Let $G_\theta: \mathcal{Z} \to \mathcal{X}$ be a parameterized generator network with parameters $\theta \in \Theta$, where $\Theta$ is the parameter space. For a sample $z \sim p_z$, we denote the generated sample as $x = G_\theta(z)$, which induces a generated distribution $p_{G_\theta}$ on $\mathcal{X}$.

## Formal Problem Statement

**Given:** 
- A dataset $\mathcal{D} = \{x_1, x_2, \ldots, x_n\}$ where $x_i \sim p_x$ are i.i.d. samples from the target distribution
- A noise distribution $p_z$ that is easy to sample from
- A parameterized generator network $G_\theta: \mathcal{Z} \to \mathcal{X}$

**Find:** Parameters $\theta^*$ such that the generator $G_{\theta^*}$ maps samples from $p_z$ to samples that follow the target distribution $p_x$ in a single forward pass.

**Guarantee:** The generated distribution $p_{G_{\theta^*}}$ should approximate the target distribution $p_x$ with respect to an appropriate divergence measure, while maintaining computational efficiency during inference.

## Objective Formulation

The core challenge is to learn a direct mapping between distributions without iterative refinement. We formulate this as finding parameters that minimize the distributional discrepancy:

$$\theta^* = \arg\min_{\theta \in \Theta} \mathcal{L}(p_x, p_{G_\theta})$$

where $\mathcal{L}$ is a suitable loss function measuring the distance between the target and generated distributions. Unlike iterative approaches that require multiple forward passes during generation, our objective seeks to capture the entire distribution mapping in the generator's single forward transformation.

The key insight is that we need a training procedure that can learn complex distribution mappings directly, without relying on iterative procedures that progressively refine samples from noise to data.

## Technical Assumptions

1. **Smoothness Assumption:** The generator $G_\theta$ is differentiable with respect to $\theta$, enabling gradient-based optimization.

2. **Universal Approximation:** The generator architecture has sufficient capacity to approximate the optimal transport map from $p_z$ to $p_x$.

3. **Sample Accessibility:** We have access to i.i.d. samples from both $p_z$ (by construction) and $p_x$ (through the dataset $\mathcal{D}$).

4. **Bounded Moments:** Both $p_z$ and $p_x$ have finite second moments, ensuring well-defined optimization dynamics.

5. **Regularity:** The target distribution $p_x$ is sufficiently regular to admit a continuous mapping from the noise distribution $p_z$.

These assumptions are justified by the need to ensure: (i) tractable optimization through gradient descent, (ii) theoretical guarantees on the existence of a solution, and (iii) practical implementability with finite samples.

# Methodology

## High-Level Approach

Our approach, termed **Flow Matching**, learns to directly map between distributions by training the generator to match the instantaneous velocity field of a continuous-time normalizing flow. Instead of learning the complex multi-step dynamics required by iterative methods, we train the generator to predict the optimal direction to transform noise samples into data samples in a single step.

The key innovation is to construct a continuous-time interpolation between the noise and data distributions, then train our generator to predict the vector field that governs this interpolation. This allows us to bypass iterative sampling while maintaining the modeling capacity of flow-based approaches.

## Core Algorithm

### Flow Construction

We define a time-dependent probability path $p_t(x)$ for $t \in [0,1]$ that interpolates between the noise distribution $p_0 = p_z$ and the data distribution $p_1 = p_x$. A natural choice is the linear interpolation:

$$x_t = (1-t)z + tx_1$$

where $z \sim p_z$ and $x_1 \sim p_x$ are independent samples. This defines a coupling between noise and data that induces the probability path $p_t$.

### Vector Field Learning

The probability path $p_t(x)$ evolves according to the continuity equation:

$$\frac{\partial p_t}{\partial t} + \nabla \cdot (p_t v_t) = 0$$

where $v_t(x)$ is the velocity field. For our linear interpolation, the target velocity field is:

$$v_t(x) = x_1 - z = x_1 - (x_t - tx_1)/(1-t)$$

However, since we don't observe the paired $(z, x_1)$ directly, we train our generator to predict this velocity field.

### Training Objective

We parameterize the velocity field with our generator: $v_t(x) \approx G_\theta(x, t)$. The training objective is the Flow Matching loss:

$$\mathcal{L}_{FM}(\theta) = \mathbb{E}_{t \sim U[0,1], z \sim p_z, x_1 \sim p_x}\left[\|G_\theta(x_t, t) - (x_1 - z)\|^2\right]$$

where $x_t = (1-t)z + tx_1$.

### Generation Process

Once trained, generation requires only a single forward pass:

```
Algorithm: Flow Matching Generation
1. Sample z ~ p_z
2. Set t = 1
3. Compute x = z + G_θ*(z, 1)
4. Return x
```

This contrasts with iterative methods that require multiple evaluations of the network with different time steps.

## Theoretical Properties

**Convergence:** Under standard regularity conditions and sufficient model capacity, the Flow Matching objective converges to the true velocity field as the number of training samples approaches infinity. This follows from the consistency of empirical risk minimization for smooth loss functions.

**Consistency:** The generated distribution $p_{G_{\theta^*}}$ converges in distribution to the target distribution $p_x$ as both the model capacity and training data size increase.

**Single-Pass Guarantee:** Unlike iterative methods, our approach generates samples in exactly one forward pass through the network, providing deterministic computational cost.

## Computational Complexity

**Training Complexity:** Each training iteration requires $O(B)$ forward passes for batch size $B$, same as standard neural network training. The time complexity per forward pass depends on the generator architecture.

**Inference Complexity:** Generation requires exactly one forward pass: $O(1)$ network evaluations per sample, compared to $O(T)$ evaluations for $T$-step iterative methods.

**Memory Complexity:** Training requires storing gradients for the generator network but does not need to maintain intermediate states across multiple time steps, unlike iterative approaches.

## Design Justifications

The linear interpolation path is chosen for its simplicity and theoretical tractability, while still providing sufficient flexibility to model complex data distributions. The Flow Matching objective directly optimizes the quantity we care about (the velocity field) rather than using adversarial training or variational bounds, leading to more stable optimization.

The single-step generation is achieved by training the network to predict the entire transformation from noise to data, effectively amortizing the iterative refinement process into the training phase. This design directly addresses the core problem of achieving high-quality generation without iterative procedures during inference.
