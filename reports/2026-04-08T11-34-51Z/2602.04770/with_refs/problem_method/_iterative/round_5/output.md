# Problem Formulation

## Notation and Problem Setup

Let $\mathcal{X}$ denote the data space and $\mathcal{Z}$ denote the latent noise space, both equipped with appropriate probability measures. We consider a generator network $G_\theta: \mathcal{Z} \to \mathcal{X}$ parameterized by $\theta \in \Theta$, where $\Theta$ is the parameter space. Let $p_{\text{data}}$ denote the unknown target data distribution over $\mathcal{X}$, and let $p_z$ denote a fixed prior distribution over $\mathcal{Z}$ (typically standard Gaussian).

During training, the generator induces a sequence of output distributions $\{p_{\theta^{(t)}}\}_{t=0}^T$ as the parameters evolve from initialization $\theta^{(0)}$ to final parameters $\theta^{(T)}$. At any training step $t$, we have access to:
- A batch of real samples $\mathbf{x} = \{x_i\}_{i=1}^n \sim p_{\text{data}}$
- A batch of generated samples $\mathbf{g} = \{G_{\theta^{(t)}}(z_i)\}_{i=1}^m$ where $z_i \sim p_z$

We define the **sample interaction function** $\phi: \mathcal{X} \times \mathcal{X} \to \mathbb{R}$ that measures the influence between any two samples based on their similarity. This function satisfies:
- $\phi(x, x') = \phi(x', x)$ (symmetry)
- $\phi(x, x') \to 0$ as $\|x - x'\| \to \infty$ (locality)
- $\phi(x, x) > 0$ (self-interaction)

## Problem Statement

**Given:** A dataset $\mathcal{D} = \{x_i\}_{i=1}^N$ sampled from $p_{\text{data}}$, a generator architecture $G_\theta$, and a sample interaction function $\phi$.

**Find:** A training procedure that evolves the generator parameters $\theta$ such that the final output distribution $p_{\theta^{(T)}}$ approximates $p_{\text{data}}$ in a single forward pass, without requiring iterative refinement at inference time.

**Guarantee:** The training procedure should converge to an equilibrium where the net forces acting on generated samples from real data samples are balanced, formally characterized by a fixed-point condition.

## Objective Formulation

We formulate the training objective through a **vector field** $\mathbf{v}_\theta: \mathcal{X} \to \mathcal{X}$ that specifies how each generated sample should move in the data space. For a generated sample $g = G_\theta(z)$, the vector field is defined as:

$$\mathbf{v}_\theta(g) = \frac{1}{n} \sum_{i=1}^n \phi(g, x_i) \cdot \frac{x_i - g}{\|x_i - g\|_2 + \epsilon} - \frac{\lambda}{m-1} \sum_{j \neq i} \phi(g, g_j) \cdot \frac{g_j - g}{\|g_j - g\|_2 + \epsilon}$$

where $\{x_i\}$ are real samples, $\{g_j\}$ are other generated samples, $\lambda > 0$ is a repulsion strength parameter, and $\epsilon > 0$ prevents division by zero.

The first term creates **attraction forces** that pull generated samples toward similar real samples, while the second term creates **repulsion forces** that push generated samples away from each other to avoid mode collapse.

## Equilibrium Condition

At equilibrium, the net force on generated samples should vanish:
$$\mathbb{E}_{z \sim p_z}[\mathbf{v}_\theta(G_\theta(z))] = \mathbf{0}$$

This occurs when the attractive forces from real data balance the repulsive forces between generated samples, indicating that $p_\theta$ has properly covered the support of $p_{\text{data}}$.

## Training Objective

Rather than directly minimizing a scalar loss, we train the generator to predict where samples should move according to the vector field. The objective is:
$$\mathcal{L}(\theta) = \mathbb{E}_{z \sim p_z}\left[\left\|G_\theta(z) + \mathbf{v}_\theta(G_\theta(z)) - G_\theta(z)\right\|_2^2\right] = \mathbb{E}_{z \sim p_z}\left[\|\mathbf{v}_\theta(G_\theta(z))\|_2^2\right]$$

## Technical Assumptions

1. **Smoothness:** The generator $G_\theta$ is continuously differentiable with respect to both $z$ and $\theta$.

2. **Bounded Support:** The data distribution $p_{\text{data}}$ has bounded support, ensuring finite interaction forces.

3. **Interaction Function Properties:** $\phi(x, x')$ is continuous, symmetric, and satisfies the locality and positivity conditions stated above.

4. **Sample Accessibility:** During training, we can efficiently sample from both $p_{\text{data}}$ (via the dataset) and the current generator distribution $p_\theta$.

5. **Parameter Regularity:** The parameter space $\Theta$ is compact and the generator family $\{G_\theta : \theta \in \Theta\}$ is sufficiently rich to approximate $p_{\text{data}}$.

This formulation connects to the conformal prediction framework in the reference through the concept of coverage guarantees - our equilibrium condition ensures that generated samples "cover" the real data distribution in a principled manner, analogous to how conformal intervals provide coverage guarantees for predictions.

# Methodology

## High-Level Approach

Our proposed method, **Dynamic Equilibrium Training (DET)**, leverages the inherent iterative nature of neural network training to explicitly govern the evolution of the generator's output distribution. Instead of optimizing a traditional adversarial or reconstruction loss, we train the generator to minimize the magnitude of forces acting on generated samples, driving the system toward a natural equilibrium where generated and real samples interact harmoniously.

The key insight is that at equilibrium, generated samples should experience zero net force - attraction from nearby real samples should be balanced by repulsion from other generated samples. This creates a training dynamic where the generator learns to place samples in regions that minimize these competing forces.

## Core Algorithm

The training procedure alternates between computing the current vector field and updating the generator to reduce force magnitudes:

```
Algorithm: Dynamic Equilibrium Training (DET)

Input: Dataset D = {x_i}, generator G_θ, interaction function φ, 
       learning rate η, repulsion strength λ, batch sizes n, m
Output: Trained generator parameters θ*

1. Initialize θ randomly
2. For t = 1 to T:
   a. Sample real batch: X = {x_i}_{i=1}^n ~ p_data
   b. Sample noise batch: Z = {z_j}_{j=1}^m ~ p_z  
   c. Generate samples: G = {G_θ(z_j)}_{j=1}^m
   
   d. For each generated sample g_j ∈ G:
      // Compute attraction forces from real samples
      F_attract = (1/n) Σ_{i=1}^n φ(g_j, x_i) · (x_i - g_j)/||x_i - g_j||_2
      
      // Compute repulsion forces from other generated samples  
      F_repel = (λ/(m-1)) Σ_{k≠j} φ(g_j, g_k) · (g_k - g_j)/||g_k - g_j||_2
      
      // Net vector field
      v_j = F_attract - F_repel
   
   e. Compute loss: L = (1/m) Σ_{j=1}^m ||v_j||_2^2
   
   f. Update parameters: θ ← θ - η ∇_θ L
   
3. Return θ*
```

## Vector Field Computation

The vector field $\mathbf{v}_\theta(g)$ for a generated sample $g$ is computed as:

$$\mathbf{v}_\theta(g) = \underbrace{\frac{1}{n} \sum_{i=1}^n \phi(g, x_i) \cdot \frac{x_i - g}{\|x_i - g\|_2 + \epsilon}}_{\text{Attraction from real samples}} - \underbrace{\frac{\lambda}{m-1} \sum_{j \neq i} \phi(g, g_j) \cdot \frac{g_j - g}{\|g_j - g\|_2 + \epsilon}}_{\text{Repulsion from generated samples}}$$

The interaction function $\phi(x, x')$ can be implemented as:
$$\phi(x, x') = \exp\left(-\frac{\|x - x'\|_2^2}{2\sigma^2}\right)$$

where $\sigma$ controls the interaction range. This Gaussian kernel ensures that interactions are strongest between nearby samples and decay smoothly with distance.

## Design Justifications

**Force-Based Dynamics:** The physics-inspired approach of balancing attractive and repulsive forces provides an intuitive and principled way to achieve distributional equilibrium. Unlike adversarial training which relies on a discriminator's imperfect gradient signals, our method directly computes the forces needed to move samples toward optimal positions.

**Single Forward Pass Generation:** Once trained, the generator produces high-quality samples in a single forward pass without iterative refinement, addressing the computational efficiency requirement.

**Mode Coverage:** The repulsion forces between generated samples naturally prevent mode collapse by ensuring diversity, while attraction forces ensure coverage of the real data distribution.

**Conditional Generation:** The framework naturally extends to conditional generation by modifying the interaction function to consider label information: $\phi(x, x') \rightarrow \phi(x, x', y, y')$ where $y, y'$ are labels.

## Theoretical Properties

**Convergence:** Under mild regularity conditions on $G_\theta$ and $\phi$, the training objective $\mathcal{L}(\theta) = \mathbb{E}[\|\mathbf{v}_\theta(G_\theta(z))\|_2^2]$ has a global minimum at $\mathcal{L}(\theta^*) = 0$ when $p_\theta = p_{\text{data}}$. The gradient descent updates drive the system toward this equilibrium.

**Equilibrium Characterization:** At equilibrium, the condition $\mathbb{E}_{z \sim p_z}[\mathbf{v}_\theta(G_\theta(z))] = \mathbf{0}$ implies that the generator distribution has achieved proper coverage of the data distribution with appropriate sample density.

**Stability:** The repulsion parameter $\lambda$ provides a stability mechanism - higher values prevent mode collapse but may slow convergence, while lower values risk instability but enable faster training.

## Computational Complexity

The computational cost per training iteration is $O(nm + m^2)$ where $n$ is the real batch size and $m$ is the generated batch size. The $nm$ term comes from computing attraction forces between all real-generated pairs, while the $m^2$ term comes from repulsion forces between all generated pairs.

For efficiency, we can use approximate nearest neighbor methods or hierarchical clustering to reduce the $m^2$ repulsion computation to $O(m \log m)$ by only computing repulsion forces between nearby generated samples.

The memory complexity is $O(n + m)$ for storing sample batches, making the method scalable to high-resolution data by controlling batch sizes rather than model capacity.

This methodology provides a principled alternative to adversarial training that directly optimizes for distributional equilibrium while maintaining computational efficiency and theoretical grounding.