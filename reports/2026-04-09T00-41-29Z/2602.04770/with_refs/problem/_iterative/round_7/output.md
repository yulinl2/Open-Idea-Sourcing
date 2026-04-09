# Problem Formulation

## 2.1 Notation and Mathematical Setup

Let $\mathcal{X} \subseteq \mathbb{R}^d$ denote the data space and $P_{\text{data}}$ denote the unknown target data distribution over $\mathcal{X}$. We consider a generator network $G_\theta: \mathcal{Z} \to \mathcal{X}$ parameterized by $\theta \in \Theta$, where $\mathcal{Z} \subseteq \mathbb{R}^k$ is a latent space equipped with a simple prior distribution $P_z$ (typically standard Gaussian). The pushforward of $P_z$ under $G_\theta$ is denoted $P_\theta := (G_\theta)_\# P_z$, representing the distribution of generated samples.

Let $\{x_i\}_{i=1}^n \sim P_{\text{data}}$ be i.i.d. samples from the target distribution and $\{z_j\}_{j=1}^m \sim P_z$ be i.i.d. latent samples. We denote the corresponding generated samples as $\{\tilde{x}_j\}_{j=1}^m$ where $\tilde{x}_j = G_\theta(z_j)$. 

To enable sample movement in a learned representation space, we introduce an encoder network $E_\phi: \mathcal{X} \to \mathcal{H}$ parameterized by $\phi \in \Phi$, mapping data to a feature space $\mathcal{H} \subseteq \mathbb{R}^h$. We define the feature representations $h_i = E_\phi(x_i)$ for data samples and $\tilde{h}_j = E_\phi(\tilde{x}_j)$ for generated samples.

## 2.2 The Flow Field and Sample Dynamics

The core innovation lies in defining a **flow field** $F: \mathcal{H} \times \mathcal{H} \to \mathcal{H}$ that governs how samples move during training. For any point $h \in \mathcal{H}$, we define its movement as:

$$\Delta h = \frac{1}{n} \sum_{i=1}^n w(h, h_i) F(h, h_i) - \frac{1}{m} \sum_{j=1}^m w(h, \tilde{h}_j) F(h, \tilde{h}_j)$$

where $w: \mathcal{H} \times \mathcal{H} \to \mathbb{R}_+$ is a similarity weighting function (e.g., $w(h, h') = \exp(-\|h - h'\|^2/\sigma^2)$ for some bandwidth $\sigma > 0$).

The flow field $F$ must satisfy the **anti-symmetry property**:
$$F(h, h') = -F(h', h) \quad \forall h, h' \in \mathcal{H}$$

This ensures that when two samples are identical ($h = h'$), the flow becomes zero: $F(h, h) = -F(h, h) \Rightarrow F(h, h) = 0$.

## 2.3 Training Dynamics and Equilibrium

During training, generated samples evolve according to the flow field. At iteration $t$, each generated sample $\tilde{h}_j^{(t)}$ moves to:
$$\tilde{h}_j^{(t+1)} = \tilde{h}_j^{(t)} + \eta \Delta \tilde{h}_j^{(t)}$$

where $\eta > 0$ is a step size and $\Delta \tilde{h}_j^{(t)}$ is computed using the current positions of all samples.

The system reaches **equilibrium** when the flow field produces zero net movement for all generated samples. Due to the anti-symmetry property, this occurs precisely when the generated and target distributions match in the feature space, i.e., when $(E_\phi \circ G_\theta)_\# P_z = (E_\phi)_\# P_{\text{data}}$.

## 2.4 Formal Problem Statement

**Given:** 
- Target data samples $\{x_i\}_{i=1}^n \sim P_{\text{data}}$
- Latent samples $\{z_j\}_{j=1}^m \sim P_z$
- Generator network $G_\theta$ and encoder network $E_\phi$
- Anti-symmetric flow field $F$ and weighting function $w$

**Find:** Parameters $(\theta^*, \phi^*)$ such that the evolved generated distribution matches the target distribution.

**Objective:** Minimize the discrepancy between distributions by driving the flow field to equilibrium:

$$\mathcal{L}(\theta, \phi) = \mathbb{E}_{\tilde{h} \sim (E_\phi \circ G_\theta)_\# P_z} \left\| \Delta \tilde{h} \right\|^2$$

where $\Delta \tilde{h}$ is the movement prescribed by the flow field for generated sample $\tilde{h}$.

## 2.5 Technical Assumptions

**A1. Anti-symmetry:** The flow field satisfies $F(h, h') = -F(h', h)$ for all $h, h' \in \mathcal{H}$.

**A2. Lipschitz continuity:** Both $F$ and $w$ are Lipschitz continuous to ensure stable dynamics.

**A3. Sufficient capacity:** The networks $G_\theta$ and $E_\phi$ have sufficient capacity to represent the target distribution and meaningful features respectively.

**A4. Feature space expressiveness:** The feature space $\mathcal{H}$ preserves sufficient information for distribution matching, i.e., if $(E_\phi)_\# P = (E_\phi)_\# Q$ then $P \approx Q$ on $\mathcal{X}$.

**A5. Bounded support:** Both $P_{\text{data}}$ and $P_z$ have bounded support to ensure finite sample interactions.

These assumptions are justified as follows: A1 provides the mathematical foundation for equilibrium detection; A2 ensures training stability; A3-A4 are standard capacity assumptions in deep learning; A5 prevents pathological cases with infinite-range interactions.

## 2.6 Connection to Prior Work

Our formulation addresses key limitations in existing generative modeling paradigms:

**Adversarial methods** (GANs) require a separate discriminator network and suffer from training instabilities. Our approach eliminates the need for adversarial training by directly optimizing for distributional equilibrium.

**Iterative refinement methods** (diffusion models, score matching) require multiple forward passes at inference time. Our method achieves single-pass generation after training convergence.

**Variational approaches** (VAEs) impose restrictive distributional assumptions and often produce blurry samples. Our approach makes no parametric assumptions about the data distribution.

**Flow-based models** learn invertible transformations but are architecturally constrained. Our approach allows flexible generator architectures while maintaining principled training dynamics.

The key conceptual advance is leveraging the **iterative nature of training itself** to evolve the generated distribution, rather than requiring iteration at inference time. The anti-symmetric flow field provides a natural stopping criterion—when distributions match, all movement ceases—eliminating the need for external measures of distributional distance.