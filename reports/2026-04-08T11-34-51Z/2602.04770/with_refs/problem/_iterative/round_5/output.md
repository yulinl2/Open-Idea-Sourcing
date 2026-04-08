# Problem Formulation

## 2.1 Notation and Mathematical Setup

Let $\mathcal{X} \subseteq \mathbb{R}^d$ denote the data space and $p_{\text{data}}$ the unknown target distribution over $\mathcal{X}$. We consider a generator network $G_\theta: \mathcal{Z} \to \mathcal{X}$ parameterized by $\theta \in \Theta$, where $\mathcal{Z} \subseteq \mathbb{R}^k$ is a latent space with a simple prior distribution $p_z$ (typically standard Gaussian). The pushforward operation $G_\theta\#p_z$ defines the generated distribution, where for any measurable set $A \subseteq \mathcal{X}$:
$$
(G_\theta\#p_z)(A) = p_z(\{z \in \mathcal{Z} : G_\theta(z) \in A\}).
$$

Let $\{x_i\}_{i=1}^n \sim p_{\text{data}}$ be i.i.d. samples from the target distribution, and let $\{z_j\}_{j=1}^m \sim p_z$ be i.i.d. samples from the latent prior. We denote the corresponding generated samples as $\{\tilde{x}_j\}_{j=1}^m$ where $\tilde{x}_j = G_\theta(z_j)$.

To enable particle interactions in a learned representation space, we introduce an encoder network $E_\phi: \mathcal{X} \to \mathcal{H}$ parameterized by $\phi \in \Phi$, mapping data to a feature space $\mathcal{H} \subseteq \mathbb{R}^h$. We define a similarity kernel $K: \mathcal{H} \times \mathcal{H} \to \mathbb{R}_+$ that measures affinity between points in feature space.

## 2.2 Particle Dynamics and Force Field

The core insight is to view generated samples as particles that evolve during training according to a force field. For a generated sample $\tilde{x}_j$, we define its movement direction as:
$$
\Delta_j(\theta, \phi) = \frac{1}{n} \sum_{i=1}^n K(E_\phi(\tilde{x}_j), E_\phi(x_i)) \cdot (E_\phi(x_i) - E_\phi(\tilde{x}_j)) - \frac{1}{m-1} \sum_{k \neq j} K(E_\phi(\tilde{x}_j), E_\phi(\tilde{x}_k)) \cdot (E_\phi(\tilde{x}_k) - E_\phi(\tilde{x}_j)).
$$

This force field exhibits a crucial **symmetry property**: when the generated and target distributions align perfectly in feature space, the attractive forces from data samples and repulsive forces from other generated samples balance exactly, yielding $\Delta_j(\theta, \phi) = 0$ for all $j$.

The movement is implemented through the generator update, where we seek to minimize:
$$
\mathcal{L}_{\text{particle}}(\theta, \phi) = \frac{1}{2m} \sum_{j=1}^m \|\Delta_j(\theta, \phi)\|^2.
$$

## 2.3 Feature Learning Objective

To learn meaningful representations that facilitate effective particle interactions, we train the encoder using a contrastive objective. We minimize:
$$
\mathcal{L}_{\text{feature}}(\phi) = -\frac{1}{n} \sum_{i=1}^n \log \frac{\exp(E_\phi(x_i)^\top E_\phi(x_i^+) / \tau)}{\sum_{k=1}^{n+m} \exp(E_\phi(x_i)^\top E_\phi(s_k) / \tau)},
$$
where $x_i^+$ represents a positive sample (e.g., augmented version of $x_i$), $\{s_k\}_{k=1}^{n+m} = \{x_1, \ldots, x_n, \tilde{x}_1, \ldots, \tilde{x}_m\}$ are all available samples, and $\tau > 0$ is a temperature parameter.

## 2.4 Problem Statement

**Given:** 
- Training samples $\{x_i\}_{i=1}^n \sim p_{\text{data}}$ from the target distribution
- Generator architecture $G_\theta$ and encoder architecture $E_\phi$
- Similarity kernel $K$ and temperature parameter $\tau$

**Find:** Parameters $(\theta^*, \phi^*)$ such that:

1. **Distribution Matching:** $G_{\theta^*}\#p_z \approx p_{\text{data}}$ in terms of distributional distance
2. **Equilibrium Condition:** $\Delta_j(\theta^*, \phi^*) \approx 0$ for all generated samples
3. **Single Forward Pass:** High-quality samples are generated via $G_{\theta^*}(z)$ for $z \sim p_z$ without iterative refinement

## 2.5 Optimization Objective

We jointly optimize the generator and encoder parameters by minimizing:
$$
\mathcal{L}(\theta, \phi) = \mathcal{L}_{\text{particle}}(\theta, \phi) + \lambda \mathcal{L}_{\text{feature}}(\phi),
$$
where $\lambda > 0$ is a weighting hyperparameter balancing particle dynamics and feature learning.

## 2.6 Technical Assumptions

**A1. Smoothness:** The generator $G_\theta$ and encoder $E_\phi$ are differentiable with respect to their parameters, enabling gradient-based optimization.

**A2. Kernel Properties:** The similarity kernel $K$ is positive, symmetric, and satisfies $K(h, h') \to 0$ as $\|h - h'\| \to \infty$, ensuring local interactions dominate.

**A3. Feature Space Geometry:** The encoder maps to a space $\mathcal{H}$ where Euclidean distances reflect meaningful data similarities, justifying the use of $\|E_\phi(x_i) - E_\phi(\tilde{x}_j)\|$ in the force computation.

**A4. Representational Capacity:** The generator has sufficient capacity to represent the target distribution, and the encoder can learn discriminative features for the given data modality.

**A5. Training Dynamics:** The joint optimization converges to a stationary point where particle forces balance, corresponding to distributional alignment.

## 2.7 Connection to Prior Work

Existing generative modeling approaches face a fundamental trade-off between generation quality and computational efficiency. **Generative Adversarial Networks** require adversarial training dynamics that can be unstable and prone to mode collapse. **Variational Autoencoders** impose restrictive distributional assumptions and often produce blurry samples. **Diffusion models** achieve high quality but require expensive iterative denoising at inference time.

**Flow-based models** learn invertible transformations but are architecturally constrained and computationally intensive. **Energy-based models** define distributions through energy functions but require MCMC sampling. These methods either compromise on sample quality, training stability, or inference efficiency.

Our formulation addresses these limitations by leveraging the **iterative nature of training itself** to evolve the generated distribution toward the target. Unlike existing approaches that require iteration at inference time, we achieve distributional alignment through particle dynamics during training, enabling single forward pass generation. The force field formulation provides a principled mechanism for distribution evolution, while the symmetry property ensures convergence to the desired equilibrium state.

The key insight differentiating our approach is treating **generated samples as particles** that move according to a learned force field, rather than viewing generation as a direct mapping problem. This perspective naturally incorporates both attractive forces from data samples and repulsive forces between generated samples, leading to comprehensive coverage of the target distribution without mode collapse.