# Problem Formulation

## Notation and Mathematical Setup

Let $\mathcal{X} \subseteq \mathbb{R}^d$ denote the data space and $P_{\text{data}}$ the unknown target distribution over $\mathcal{X}$. We consider a generator network $G_\theta: \mathcal{Z} \to \mathcal{X}$ parameterized by $\theta \in \Theta$, where $\mathcal{Z} \subseteq \mathbb{R}^k$ is a latent space equipped with a simple prior distribution $P_z$ (typically standard Gaussian). The pushforward of $P_z$ through $G_\theta$ defines the generated distribution $P_\theta = (G_\theta)_\# P_z$.

Let $\{x_i\}_{i=1}^n \sim P_{\text{data}}$ denote samples from the target distribution and $\{z_j\}_{j=1}^m \sim P_z$ denote samples from the latent prior. We define the generated samples as $\{\tilde{x}_j\}_{j=1}^m$ where $\tilde{x}_j = G_\theta(z_j)$.

For any two distributions $P$ and $Q$ over $\mathcal{X}$, we assume access to a similarity function $s: \mathcal{X} \times \mathcal{X} \to \mathbb{R}_+$ that measures the affinity between samples. In practice, this similarity is computed in a learned feature space $\mathcal{F}$ via an encoder $\phi: \mathcal{X} \to \mathcal{F}$, such that $s(x, x') = \kappa(\phi(x), \phi(x'))$ for some kernel function $\kappa$.

## Formal Problem Statement

**Given:** 
- Target samples $\{x_i\}_{i=1}^n \sim P_{\text{data}}$
- Latent samples $\{z_j\}_{j=1}^m \sim P_z$  
- Generator $G_\theta$ and encoder $\phi$ (to be learned)
- Similarity kernel $\kappa$

**Find:** Parameters $\theta^*$ and $\phi^*$ such that the generated distribution $P_{\theta^*}$ matches the target distribution $P_{\text{data}}$ through a training process that evolves generated samples via particle dynamics.

**Guarantee:** The training dynamics should reach an equilibrium where $P_{\theta^*} = P_{\text{data}}$, achieved when the force field governing sample movement becomes zero.

## Particle Flow Dynamics

We model the evolution of generated samples as particles moving under a force field. For each generated sample $\tilde{x}_j$, we define its movement direction through a **flow field** $F: \mathcal{X} \to \mathcal{X}$ that depends on interactions with both target samples and other generated samples.

Specifically, for a generated sample $\tilde{x} = G_\theta(z)$, the flow field is defined as:

$$F(\tilde{x}) = \frac{1}{n} \sum_{i=1}^n s(\tilde{x}, x_i) \cdot (x_i - \tilde{x}) - \frac{1}{m} \sum_{j=1}^m s(\tilde{x}, \tilde{x}_j) \cdot (\tilde{x}_j - \tilde{x})$$

This field exhibits the crucial **anti-symmetry property**: if we swap the roles of target and generated distributions, the field direction reverses. Formally, defining the field for target samples as:

$$F(x) = \frac{1}{m} \sum_{j=1}^m s(x, \tilde{x}_j) \cdot (\tilde{x}_j - x) - \frac{1}{n} \sum_{i=1}^n s(x, x_i) \cdot (x_i - x)$$

we have $F_{\text{target}}(x) = -F_{\text{generated}}(x)$ when evaluated at the same point, ensuring that $F(x) = 0$ when the distributions match.

## Training Objective

The generator parameters are updated to align generated samples with their flow directions. At each training iteration $t$, we minimize:

$$\mathcal{L}(\theta) = \frac{1}{m} \sum_{j=1}^m \left\| \frac{\partial G_\theta(z_j)}{\partial \theta} - F(G_\theta(z_j)) \right\|^2$$

where $\frac{\partial G_\theta(z_j)}{\partial \theta}$ represents the direction of change in the generated sample with respect to parameter updates.

Simultaneously, the encoder parameters $\phi$ are optimized to learn meaningful feature representations that enhance the similarity function's discriminative power:

$$\mathcal{L}_{\text{enc}}(\phi) = \mathbb{E}_{x \sim P_{\text{data}}, \tilde{x} \sim P_\theta} \left[ \ell(\phi(x), \phi(\tilde{x})) \right]$$

where $\ell$ is a contrastive loss that encourages similar samples to have similar representations.

## Technical Assumptions

**A1. Smoothness:** The generator $G_\theta$ is differentiable with respect to $\theta$, and the similarity function $s$ is continuous.

**A2. Bounded Support:** Both $P_{\text{data}}$ and the generated distributions have bounded support, ensuring finite flow field magnitudes.

**A3. Non-degeneracy:** The similarity function $s(x, x') > 0$ for all $x \neq x'$ and $s(x, x) = c > 0$ for some constant $c$, preventing collapse to point masses.

**A4. Feature Consistency:** The encoder $\phi$ provides stable representations that preserve relevant similarity relationships across training iterations.

**A5. Sufficient Capacity:** The generator $G_\theta$ has sufficient capacity to represent the target distribution, and the number of generated samples $m$ scales appropriately with the complexity of $P_{\text{data}}$.

These assumptions ensure that: (1) the flow field is well-defined and computable, (2) the training dynamics are stable, (3) the equilibrium condition $F(x) = 0$ corresponds to distributional matching, and (4) the generator can achieve this equilibrium through gradient-based optimization.

## Connection to Prior Work

This formulation addresses key limitations in existing generative modeling approaches. Unlike adversarial methods that require careful balancing of competing objectives, our approach provides a single, principled objective based on particle dynamics. Compared to iterative refinement methods (e.g., diffusion models) that require multiple forward passes at inference, our approach generates samples in a single forward pass after training.

The anti-symmetric flow field generalizes ideas from contrastive learning and mean-shift algorithms to the distributional matching setting, while the particle-based perspective connects to recent work in gradient flows and optimal transport. However, unlike methods that require pre-computed transport maps or expensive optimal transport computations, our approach learns the appropriate dynamics through the training process itself, leveraging the natural iterative structure of neural network optimization.