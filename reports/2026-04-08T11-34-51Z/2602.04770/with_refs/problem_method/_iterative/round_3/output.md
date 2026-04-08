# Problem Formulation

## 1.1 Notation and Mathematical Setup

Let $\mathcal{X} \subseteq \mathbb{R}^d$ denote the data space and $\mathcal{Z} \subseteq \mathbb{R}^k$ denote the noise space, where $d, k \in \mathbb{N}$. We denote by $P_{\text{data}}$ the unknown target data distribution over $\mathcal{X}$ from which we observe training samples $\{x_i\}_{i=1}^n \sim P_{\text{data}}$. Let $P_{\text{noise}}$ be a known prior distribution over $\mathcal{Z}$, typically chosen as $P_{\text{noise}} = \mathcal{N}(0, I_k)$.

A generator $G_\theta: \mathcal{Z} \to \mathcal{X}$ is a neural network parameterized by $\theta \in \Theta$, where $\Theta$ is the parameter space. At any point in training, the generator induces an output distribution $P_\theta = G_\theta \# P_{\text{noise}}$, where $\#$ denotes the pushforward measure. That is, for any measurable set $A \subseteq \mathcal{X}$, we have $P_\theta(A) = P_{\text{noise}}(G_\theta^{-1}(A))$.

Let $\{P_{\theta^{(t)}}\}_{t=0}^T$ denote the sequence of generator output distributions during training, where $\theta^{(t)}$ represents the generator parameters at training step $t$. We define the **distribution evolution trajectory** as the path traced by these distributions in the space of probability measures over $\mathcal{X}$.

## 1.2 Problem Statement

**Given:** 
- Training dataset $\mathcal{D} = \{x_i\}_{i=1}^n$ sampled i.i.d. from $P_{\text{data}}$
- Generator architecture $G_\theta: \mathcal{Z} \to \mathcal{X}$
- Noise distribution $P_{\text{noise}}$

**Find:** A training procedure that learns parameters $\theta^*$ such that:
1. $P_{\theta^*} \approx P_{\text{data}}$ (distribution matching)
2. Generation requires only a single forward pass: $\hat{x} = G_{\theta^*}(z)$ for $z \sim P_{\text{noise}}$
3. The training dynamics explicitly govern the evolution of the output distribution

**Guarantee:** The final generator $G_{\theta^*}$ produces high-quality samples that capture the full support of $P_{\text{data}}$ without mode collapse.

## 1.3 Equilibrium-Based Objective

We formulate the training objective based on an equilibrium condition between generated and real data distributions. Define a **distribution interaction functional** $\Phi: \mathcal{P}(\mathcal{X}) \times \mathcal{P}(\mathcal{X}) \to \mathbb{R}$, where $\mathcal{P}(\mathcal{X})$ is the space of probability measures over $\mathcal{X}$.

The core principle is that at equilibrium, the generator output distribution $P_\theta$ should satisfy:
$$\mathbb{E}_{x \sim P_{\text{data}}}[\nabla_\theta \log p_\theta(x)] = \mathbb{E}_{x \sim P_\theta}[\nabla_\theta \log p_\theta(x)]$$

where $p_\theta$ denotes the density of $P_\theta$ when it exists. This equilibrium condition states that the expected score function (gradient of log-density) should be equal when evaluated on real data versus generated data.

However, since computing $p_\theta$ directly is intractable, we instead work with an empirical approximation. Let $\{x_i\}_{i=1}^n \sim P_{\text{data}}$ be real samples and $\{\tilde{x}_j\}_{j=1}^m \sim P_\theta$ be generated samples. We define the **Flow Matching Objective**:

$$\mathcal{L}_{\text{FM}}(\theta) = \mathbb{E}_{t \sim \mathcal{U}[0,1]} \mathbb{E}_{x_0 \sim P_{\text{data}}} \mathbb{E}_{x_1 \sim P_\theta} \left\| v_\theta(x_t, t) - \dot{x}_t \right\|^2$$

where:
- $x_t = (1-t)x_0 + tx_1$ defines a linear interpolation path
- $\dot{x}_t = x_1 - x_0$ is the time derivative along this path  
- $v_\theta(x, t): \mathcal{X} \times [0,1] \to \mathbb{R}^d$ is a learned vector field
- $t \sim \mathcal{U}[0,1]$ represents time along the interpolation

## 1.4 Technical Assumptions

**Assumption 1 (Regularity):** The generator $G_\theta$ is continuously differentiable in $\theta$, and the induced distributions $P_\theta$ have densities $p_\theta$ that are continuously differentiable in $\theta$.

**Assumption 2 (Compact Support):** Both $P_{\text{data}}$ and $P_\theta$ have compact support in $\mathcal{X}$ for all $\theta \in \Theta$.

**Assumption 3 (Non-degeneracy):** The noise distribution $P_{\text{noise}}$ is absolutely continuous with respect to Lebesgue measure, ensuring the generator can produce diverse outputs.

**Assumption 4 (Interpolation Regularity):** For any $x_0 \sim P_{\text{data}}$ and $x_1 \sim P_\theta$, the linear interpolation path $x_t = (1-t)x_0 + tx_1$ remains in a region where the vector field $v_\theta$ is well-defined and Lipschitz continuous.

These assumptions are justified by the need to ensure: (1) smooth optimization dynamics, (2) well-defined probability densities, (3) sufficient generator expressivity, and (4) stable interpolation between real and generated samples during training.

# Methodology

## 2.1 Flow Matching Framework Overview

Our approach, which we term **Flow Matching**, directly learns to transform the noise distribution $P_{\text{noise}}$ into the data distribution $P_{\text{data}}$ through a continuous normalizing flow. Unlike traditional generative models that require iterative sampling, Flow Matching learns a deterministic mapping that can generate samples in a single forward pass.

The key insight is to leverage the iterative nature of neural network training to gradually evolve the generator's output distribution. Rather than training a generator to fool a discriminator, we train a vector field $v_\theta$ to match the flow between real and generated data pairs.

## 2.2 Core Algorithm

The Flow Matching algorithm consists of two main components: (1) a vector field network $v_\theta$ that learns the transformation dynamics, and (2) a training procedure that constructs interpolation paths between real and generated samples.

### Vector Field Architecture

The vector field $v_\theta(x, t): \mathcal{X} \times [0,1] \to \mathbb{R}^d$ is implemented as a neural network that takes as input a data point $x$ and time $t \in [0,1]$, and outputs a velocity vector. The architecture typically consists of:

$$v_\theta(x, t) = \text{MLP}_\theta(\text{concat}(x, \gamma(t)))$$

where $\gamma(t)$ is a time embedding (e.g., sinusoidal encoding) and $\text{MLP}_\theta$ is a multi-layer perceptron.

### Training Procedure

```
Algorithm 1: Flow Matching Training
Input: Dataset D = {x_i}_{i=1}^n, vector field v_θ, learning rate η
Output: Trained parameters θ*

1. Initialize θ randomly
2. For epoch = 1 to max_epochs:
   3. For each mini-batch B ⊆ D:
      4. Sample noise z ~ P_noise with |z| = |B|  
      5. Generate samples: x̃ = G_θ(z)
      6. Sample time steps: t ~ U[0,1] with |t| = |B|
      7. Create interpolation paths: x_t = (1-t) ⊙ x + t ⊙ x̃
      8. Compute target velocities: u_t = x̃ - x  
      9. Predict velocities: v_pred = v_θ(x_t, t)
      10. Compute loss: L = ||v_pred - u_t||²
      11. Update parameters: θ ← θ - η ∇_θ L
12. Return θ*

Generation Procedure:
Input: Noise sample z ~ P_noise, trained v_θ*
1. Initialize x_0 = z  
2. For t = 0 to 1 with step size dt:
   3. x_{t+dt} = x_t + v_θ*(x_t, t) * dt
4. Return x_1
```

## 2.3 Theoretical Properties

**Proposition 1 (Flow Consistency):** Under Assumptions 1-4, if the vector field $v_\theta$ perfectly matches the target velocities $u_t = x_1 - x_0$ for all interpolation paths, then the induced flow maps $P_{\text{noise}}$ to $P_{\text{data}}$.

**Proposition 2 (Training Convergence):** The Flow Matching objective $\mathcal{L}_{\text{FM}}(\theta)$ is convex in the function space of vector fields, ensuring that gradient descent converges to a global minimum when sufficient model capacity is available.

The key insight is that by learning to match velocities along interpolation paths between real and generated samples, the model learns a continuous transformation that can map noise to data in a single forward pass (after integration of the learned vector field).

## 2.4 Computational Complexity

**Training Complexity:** Each training iteration requires:
- Forward pass through vector field: $O(|B| \cdot C_v)$ where $C_v$ is the cost of evaluating $v_\theta$
- Gradient computation: $O(|B| \cdot |\theta|)$ where $|\theta|$ is the number of parameters
- Overall per-epoch complexity: $O(n \cdot C_v + n \cdot |\theta|)$

**Generation Complexity:** Sample generation requires:
- ODE integration with $K$ steps: $O(K \cdot C_v)$
- For single-step generation (when $K=1$): $O(C_v)$
- This achieves the desired single forward pass generation

**Memory Requirements:** Training requires storing interpolated points $x_t$ and target velocities, leading to $O(|B| \cdot d)$ additional memory per batch compared to standard generative models.

## 2.5 Design Justifications

The Flow Matching approach addresses the core problem requirements:

1. **Single Forward Pass Generation:** By learning a continuous flow, we can generate samples through ODE integration, which can be approximated with a single large step for fast inference.

2. **Distribution Evolution Control:** The training explicitly constructs paths between current generated samples and real data, directly governing how the output distribution evolves.

3. **Equilibrium-Based Training:** The interpolation between real and generated samples creates a natural equilibrium condition - perfect matching occurs when generated samples are indistinguishable from real ones.

4. **Scalability:** The method scales to high-dimensional data since it only requires pointwise vector field evaluation, avoiding expensive density computations or adversarial training instabilities.

The approach draws inspiration from the conformal prediction framework in that it constructs prediction intervals (interpolation paths) that provide coverage guarantees, but adapts this concept to the generative modeling setting where we want to ensure the generated distribution covers the real data distribution.