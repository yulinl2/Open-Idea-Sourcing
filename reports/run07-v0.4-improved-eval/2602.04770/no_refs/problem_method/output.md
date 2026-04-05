# Reconstruction: problem_method
**Paper:** 2602.04770  
**Condition:** no_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Problem Formulation

## 1.1 Notation and Setup

Let $\mathcal{X} \subseteq \mathbb{R}^d$ denote the data space and $p_{\text{data}}(\mathbf{x})$ the unknown target data distribution over $\mathcal{X}$. We assume access to a training dataset $\mathcal{D} = \{\mathbf{x}_i\}_{i=1}^N$ where $\mathbf{x}_i \sim p_{\text{data}}$ are i.i.d. samples. Let $\mathcal{Z} \subseteq \mathbb{R}^k$ denote a latent space equipped with a simple prior distribution $p_{\text{prior}}(\mathbf{z})$, typically chosen as $\mathcal{N}(\mathbf{0}, \mathbf{I})$.

We consider parametric generative models $G_\theta: \mathcal{Z} \to \mathcal{X}$ with parameters $\theta \in \Theta$, where $\Theta$ is the parameter space. The induced distribution over $\mathcal{X}$ is given by the pushforward measure:
$$p_\theta(\mathbf{x}) = \int_{\mathcal{Z}} p_{\text{prior}}(\mathbf{z}) \delta(\mathbf{x} - G_\theta(\mathbf{z})) d\mathbf{z}$$

For conditional generation, we extend the setup to include a conditioning variable $\mathbf{c} \in \mathcal{C}$, yielding conditional models $G_\theta: \mathcal{Z} \times \mathcal{C} \to \mathcal{X}$ and conditional distributions $p_\theta(\mathbf{x}|\mathbf{c})$.

## 1.2 Problem Statement

**Given:** Training dataset $\mathcal{D} = \{\mathbf{x}_i\}_{i=1}^N$ sampled from unknown distribution $p_{\text{data}}(\mathbf{x})$.

**Find:** Parameters $\theta^*$ for generator $G_\theta$ such that the induced distribution $p_{\theta^*}(\mathbf{x})$ closely approximates $p_{\text{data}}(\mathbf{x})$.

**Guarantee:** The learned generator should satisfy:
1. **Single-pass efficiency:** $G_{\theta^*}(\mathbf{z})$ produces high-quality samples in one forward evaluation
2. **Distribution coverage:** $p_{\theta^*}$ captures the full support and modes of $p_{\text{data}}$
3. **Sample quality:** Generated samples $\mathbf{x} = G_{\theta^*}(\mathbf{z})$ are perceptually indistinguishable from real data

## 1.3 Objective Formulation

We formulate the learning problem as minimizing a divergence between the data and model distributions. Let $D(p_{\text{data}}, p_\theta)$ denote a suitable divergence measure. The optimization problem becomes:
$$\theta^* = \arg\min_{\theta \in \Theta} \mathbb{E}_{\mathbf{x} \sim p_{\text{data}}}[\ell(\mathbf{x}, \theta)] + \lambda R(\theta)$$

where $\ell(\mathbf{x}, \theta)$ is a sample-wise loss function that encourages $p_\theta$ to match $p_{\text{data}}$, and $R(\theta)$ is a regularization term with weight $\lambda \geq 0$.

The key challenge is designing $\ell(\mathbf{x}, \theta)$ to avoid the computational overhead of iterative sampling procedures while maintaining modeling flexibility. Unlike adversarial approaches that require solving a minimax problem, or diffusion models that require multiple denoising steps, we seek a direct optimization objective.

## 1.4 Technical Assumptions

**A1. Smoothness:** The generator $G_\theta$ is differentiable with respect to both $\mathbf{z}$ and $\theta$, enabling gradient-based optimization.

**A2. Universal approximation:** The function class parameterized by $\theta$ (e.g., deep neural networks) can approximate the optimal transport map from $p_{\text{prior}}$ to $p_{\text{data}}$.

**A3. Data regularity:** The target distribution $p_{\text{data}}$ has finite second moments and is supported on a smooth manifold embedded in $\mathcal{X}$.

**A4. Prior compatibility:** The latent dimension $k$ is sufficient to capture the intrinsic dimensionality of the data manifold.

These assumptions are standard in the generative modeling literature and ensure that the optimization problem is well-posed and that gradient-based learning is feasible.

# Methodology

## 2.1 High-Level Approach

Our approach addresses the single-pass generation challenge through **consistency training**, where we train the generator to be consistent with a reference diffusion process without requiring iterative sampling. The key insight is to leverage the theoretical connection between score-based diffusion models and optimal transport to design a direct mapping that preserves the distributional properties of iterative approaches.

We propose training a neural network $G_\theta(\mathbf{z}, t)$ that maps noise samples $\mathbf{z}$ and time indices $t$ to data samples, such that $G_\theta(\mathbf{z}, 0) = \mathbf{z}$ and $G_\theta(\mathbf{z}, T) \approx \mathbf{x}$ for large $T$. The consistency property ensures that for any $t_1 < t_2$, we have $G_\theta(G_\theta(\mathbf{z}, t_1), t_2) = G_\theta(\mathbf{z}, t_2)$.

## 2.2 Core Algorithm: Consistency Training

### 2.2.1 Consistency Model Architecture

We parameterize the consistency model as:
$$G_\theta(\mathbf{z}, t) = c_{\text{skip}}(t)\mathbf{z} + c_{\text{out}}(t)F_\theta(\mathbf{z}, t)$$

where $F_\theta$ is a neural network, and $c_{\text{skip}}(t)$, $c_{\text{out}}(t)$ are scalar functions ensuring the boundary condition $G_\theta(\mathbf{z}, 0) = \mathbf{z}$. Specifically:
$$c_{\text{skip}}(t) = \frac{\sigma_{\text{data}}^2}{(t - \sigma_{\text{min}})^2 + \sigma_{\text{data}}^2}, \quad c_{\text{out}}(t) = \frac{t - \sigma_{\text{min}}}{\sqrt{\sigma_{\text{data}}^2 + t^2}}$$

### 2.2.2 Training Objective

The consistency training objective enforces self-consistency across different time steps:
$$\mathcal{L}_{\text{CD}}(\theta) = \mathbb{E}_{t,\mathbf{z},\mathbf{x}} \left[ d\left(G_\theta(\mathbf{z}, t_1), G_\theta(\hat{\mathbf{z}}, t_2)\right) \right]$$

where:
- $t_1, t_2 \sim \mathcal{U}[0, T]$ with $t_1 < t_2$
- $\mathbf{z} \sim \mathcal{N}(\mathbf{0}, \mathbf{I})$
- $\mathbf{x} \sim p_{\text{data}}$
- $\hat{\mathbf{z}} = \mathbf{x} + t_2 \mathbf{z}$ (noisy data sample)
- $d(\cdot, \cdot)$ is a distance metric (e.g., $\ell_2$ norm)

### 2.2.3 Training Algorithm

```
Algorithm 1: Consistency Training
Input: Dataset D, time horizon T, learning rate α
Output: Trained consistency model G_θ

1. Initialize network parameters θ randomly
2. For epoch = 1 to max_epochs:
   3. For each mini-batch B ⊂ D:
      4. Sample time steps t₁, t₂ ~ U[0,T] with t₁ < t₂
      5. Sample noise z ~ N(0,I)
      6. For each x in B:
         7. Compute noisy sample: z̃ = x + t₂ · z
         8. Forward pass: x₁ = G_θ(z, t₁), x₂ = G_θ(z̃, t₂)
         9. Compute consistency loss: ℓ = d(x₁, x₂)
      10. Compute gradient: ∇_θ ℓ
      11. Update parameters: θ ← θ - α∇_θ ℓ
12. Return G_θ
```

## 2.3 Design Justifications

**Boundary condition parameterization:** The specific forms of $c_{\text{skip}}(t)$ and $c_{\text{out}}(t)$ ensure numerical stability and proper scaling across time steps. This design prevents the vanishing gradient problem common in time-dependent neural networks.

**Self-consistency training:** By enforcing consistency between different time steps of the same trajectory, we implicitly learn the underlying flow that connects noise to data without requiring explicit simulation of the full diffusion process.

**Single-step generation:** At inference time, we simply evaluate $G_\theta(\mathbf{z}, T)$ for $\mathbf{z} \sim \mathcal{N}(\mathbf{0}, \mathbf{I})$, requiring only one forward pass through the network.

## 2.4 Theoretical Properties

**Proposition 1 (Consistency):** Under mild regularity conditions, if the training loss $\mathcal{L}_{\text{CD}}(\theta) = 0$, then $G_\theta$ satisfies the consistency property: $G_\theta(G_\theta(\mathbf{z}, t_1), t_2) = G_\theta(\mathbf{z}, t_2)$ for all $t_1 < t_2$.

**Proposition 2 (Convergence):** With appropriate learning rate scheduling and sufficient network capacity, the consistency training objective converges to a stationary point of $\mathcal{L}_{\text{CD}}$.

**Corollary (Sample Quality):** As $\mathcal{L}_{\text{CD}}(\theta) \to 0$, the distribution induced by $G_\theta(\mathbf{z}, T)$ approaches $p_{\text{data}}$.

## 2.5 Computational Complexity

**Training complexity:** Each training step requires $O(1)$ forward passes through the network, making it significantly more efficient than adversarial training (which requires training two networks) or iterative refinement approaches.

**Inference complexity:** Generation requires exactly one forward pass: $O(|\theta|)$ where $|\theta|$ is the number of model parameters. This represents a substantial speedup over diffusion models that typically require 50-1000 denoising steps.

**Memory complexity:** The model requires $O(|\theta|)$ memory during both training and inference, with no additional storage needed for intermediate states or auxiliary networks.

The proposed approach achieves the desired single-pass generation capability while maintaining theoretical guarantees on sample quality and distribution coverage, addressing the fundamental efficiency-quality trade-off in generative modeling.
