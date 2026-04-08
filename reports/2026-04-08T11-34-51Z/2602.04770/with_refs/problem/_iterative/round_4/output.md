# Problem Formulation

## Notation and Problem Setup

Let $\mathcal{X}$ denote the data space (e.g., $\mathbb{R}^d$ for continuous data or the space of natural images) and let $p_{\text{data}}$ be the unknown target distribution over $\mathcal{X}$ from which we observe training samples $\{x_i\}_{i=1}^n \sim p_{\text{data}}$. Let $p_{\text{noise}}$ denote a simple prior distribution (typically standard Gaussian) from which we can easily sample. Our goal is to learn a generator $G_\theta: \mathcal{Z} \to \mathcal{X}$ parameterized by $\theta$ that maps samples $z \sim p_{\text{noise}}$ from the noise space $\mathcal{Z}$ to the data space $\mathcal{X}$.

Let $p_{\theta}$ denote the pushforward distribution induced by the generator: if $z \sim p_{\text{noise}}$, then $G_\theta(z) \sim p_{\theta}$. The fundamental challenge is to find parameters $\theta^*$ such that $p_{\theta^*} = p_{\text{data}}$.

We introduce the key innovation of treating generated samples as particles that evolve during training. Let $\{z_j\}_{j=1}^m$ be a fixed set of noise samples, and define the generated particles at training iteration $t$ as $\{x_j^{(t)}\}_{j=1}^m$ where $x_j^{(t)} = G_{\theta^{(t)}}(z_j)$. These particles move in $\mathcal{X}$ as training progresses according to the dynamics:

$$\frac{dx_j^{(t)}}{dt} = \nabla_\theta G_{\theta^{(t)}}(z_j) \cdot \frac{d\theta^{(t)}}{dt}$$

## Particle Dynamics and Force Fields

We model the evolution of generated particles through a force field $F: \mathcal{X} \times \mathcal{X} \to \mathbb{R}^d$ that governs how particles should move based on their interactions with both data samples and other generated samples. Specifically, we define the total force acting on a generated particle $x$ as:

$$F_{\text{total}}(x) = \frac{1}{n}\sum_{i=1}^n F(x, x_i^{\text{data}}) + \frac{1}{m}\sum_{j=1}^m F(x, x_j^{\text{gen}})$$

where $\{x_i^{\text{data}}\}_{i=1}^n$ are the training data samples and $\{x_j^{\text{gen}}\}_{j=1}^m$ are the current generated samples.

The force field $F(x, y)$ should satisfy a crucial **antisymmetry property**: $F(x, y) = -F(y, x)$ for all $x, y \in \mathcal{X}$. This ensures that when the generated and data distributions align perfectly, the net force on any particle becomes zero, establishing equilibrium.

## Formal Problem Statement

**Given:**
- Training dataset $\mathcal{D} = \{x_i\}_{i=1}^n$ sampled i.i.d. from unknown target distribution $p_{\text{data}}$
- Generator architecture $G_\theta: \mathcal{Z} \to \mathcal{X}$ with parameters $\theta \in \Theta$
- Prior distribution $p_{\text{noise}}$ over noise space $\mathcal{Z}$
- Antisymmetric force field $F: \mathcal{X} \times \mathcal{X} \to \mathbb{R}^d$ with $F(x,y) = -F(y,x)$

**Find:** Parameters $\theta^*$ such that the equilibrium condition holds:

$$\mathbb{E}_{x \sim p_{\theta^*}} \mathbb{E}_{y \sim p_{\text{data}}} [F(x, y)] + \mathbb{E}_{x \sim p_{\theta^*}} \mathbb{E}_{y \sim p_{\theta^*}} [F(x, y)] = 0$$

This equilibrium condition is satisfied if and only if $p_{\theta^*} = p_{\text{data}}$ due to the antisymmetry of $F$.

## Optimization Objective

We formulate the training objective as minimizing the expected magnitude of forces acting on generated particles. Let $S_\theta = \{G_\theta(z_j)\}_{j=1}^m$ denote the set of generated samples for a fixed collection of noise samples $\{z_j\}_{j=1}^m$. The objective function is:

$$\mathcal{L}(\theta) = \mathbb{E}_{x \sim S_\theta} \left\| \frac{1}{n}\sum_{i=1}^n F(x, x_i) + \frac{1}{|S_\theta|}\sum_{y \in S_\theta} F(x, y) \right\|^2$$

The gradient of this objective with respect to $\theta$ provides the direction for parameter updates that will move generated particles according to the force field dynamics.

## Technical Assumptions

**A1. Generator Regularity:** The generator $G_\theta$ is differentiable with respect to both its input and parameters, with bounded gradients on compact sets.

**A2. Force Field Properties:** The force field $F(x, y)$ satisfies:
- Antisymmetry: $F(x, y) = -F(y, x)$
- Lipschitz continuity in both arguments
- Integrability: $\mathbb{E}_{x,y \sim p}[\|F(x, y)\|] < \infty$ for any distribution $p$ with finite second moments

**A3. Data Distribution:** The target distribution $p_{\text{data}}$ has finite second moments and is supported on a bounded subset of $\mathcal{X}$.

**A4. Identifiability:** The generator class $\{G_\theta : \theta \in \Theta\}$ is rich enough to represent the target distribution, i.e., there exists $\theta^* \in \Theta$ such that $G_{\theta^*} \# p_{\text{noise}} = p_{\text{data}}$.

The antisymmetry assumption (A2) is crucial as it ensures that the equilibrium condition $p_\theta = p_{\text{data}}$ corresponds to zero net force, providing a principled stopping criterion. The Lipschitz continuity ensures stable training dynamics, while the integrability condition prevents infinite forces that could destabilize training.

## Connection to Prior Work

Traditional generative adversarial networks (GANs) learn through a minimax game between generator and discriminator, requiring careful balancing of two networks and suffering from training instabilities. Variational autoencoders (VAEs) optimize a tractable lower bound but often produce blurry samples due to the Kullback-Leibler regularization.

Flow-based models and diffusion models achieve high-quality generation but require multiple network evaluations at inference time. Diffusion models, in particular, use iterative denoising processes that can require hundreds of function evaluations.

Our formulation differs fundamentally by leveraging the iterative nature of training itself to evolve the generated distribution toward the target. The antisymmetric force field provides a natural equilibrium condition that existing methods lack. Unlike GANs, we avoid adversarial training dynamics. Unlike VAEs, we directly minimize distributional discrepancy without variational bounds. Unlike diffusion models, we require only a single forward pass at inference time while maintaining the modeling capacity of iterative approaches through the training process itself.

The particle dynamics perspective connects to optimal transport theory and gradient flows, but our antisymmetric force formulation provides a novel way to ensure convergence to the correct equilibrium without requiring explicit transport map computation or complex sampling procedures during inference.