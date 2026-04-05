# Reconstruction: problem
**Paper:** 2602.04770  
**Condition:** no_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Problem Formulation

## 2.1 Mathematical Setup and Notation

Let $\mathcal{X} \subset \mathbb{R}^d$ denote the data space and $p_{\text{data}}$ the unknown target distribution over $\mathcal{X}$ from which we observe samples $\{x_i\}_{i=1}^N$. We consider a latent space $\mathcal{Z} \subset \mathbb{R}^k$ equipped with a tractable prior distribution $p_z$, typically chosen as the standard Gaussian $\mathcal{N}(0, I_k)$. Our goal is to learn a generative mapping $G_\theta: \mathcal{Z} \to \mathcal{X}$ parameterized by $\theta \in \Theta$ such that the pushforward measure $G_\theta \# p_z$ closely approximates $p_{\text{data}}$.

For conditional generation, we extend our framework to include a conditioning space $\mathcal{C}$ with conditioning variables $c \in \mathcal{C}$. The conditional data distribution is denoted $p_{\text{data}}(x|c)$, and we seek to learn $G_\theta: \mathcal{Z} \times \mathcal{C} \to \mathcal{X}$ such that $G_\theta(\cdot, c) \# p_z \approx p_{\text{data}}(\cdot|c)$ for all $c \in \mathcal{C}$.

## 2.2 Problem Statement

**Given:** A dataset $\mathcal{D} = \{x_i\}_{i=1}^N$ drawn i.i.d. from an unknown distribution $p_{\text{data}}$ over $\mathcal{X}$, and optionally conditioning information $\{c_i\}_{i=1}^N$ from $\mathcal{C}$.

**Find:** Parameters $\theta^*$ for a neural network $G_\theta: \mathcal{Z} \times \mathcal{C} \to \mathcal{X}$ that minimizes the distributional discrepancy between the model distribution $p_\theta(x|c) := (G_\theta(\cdot, c) \# p_z)(x)$ and the target distribution $p_{\text{data}}(x|c)$.

**Subject to:** The constraint that generation requires exactly one forward pass through $G_\theta$, i.e., $x = G_\theta(z, c)$ for $z \sim p_z$.

## 2.3 Optimization Objective

The core challenge lies in defining an appropriate discrepancy measure between distributions that can be optimized efficiently. We formulate this as a minimax optimization problem:

$$\theta^* = \arg\min_\theta \mathcal{L}(\theta)$$

where the loss function $\mathcal{L}(\theta)$ must satisfy several key properties:
1. **Tractability**: Computable from finite samples without requiring density evaluation
2. **Statistical consistency**: Convergence $\mathcal{L}(\theta) \to 0$ implies distributional convergence $p_\theta \to p_{\text{data}}$
3. **Mode coverage**: Penalizes mode collapse and encourages full support coverage

A natural candidate is the integral probability metric (IPM) framework:

$$\mathcal{L}(\theta) = \sup_{f \in \mathcal{F}} \left| \mathbb{E}_{x \sim p_{\text{data}}}[f(x)] - \mathbb{E}_{z \sim p_z}[f(G_\theta(z))] \right|$$

where $\mathcal{F}$ is a function class that determines the metric's properties. However, this formulation requires solving an inner maximization problem, which typically necessitates adversarial training procedures.

## 2.4 Technical Assumptions

We make the following assumptions to ensure theoretical tractability and practical feasibility:

**A1 (Smoothness):** The generator $G_\theta$ is differentiable almost everywhere with respect to both $\theta$ and its inputs, enabling gradient-based optimization.

**A2 (Universal Approximation):** The function class parameterized by $G_\theta$ has sufficient capacity to approximate the optimal transport map between $p_z$ and $p_{\text{data}}$, at least in the limit of infinite parameters.

**A3 (Finite Moments):** Both $p_{\text{data}}$ and $p_z$ have finite second moments, ensuring well-defined covariance structures and preventing pathological behavior in high-dimensional spaces.

**A4 (Regularity):** The target distribution $p_{\text{data}}$ admits a smooth density (possibly after convolution with a small Gaussian kernel) to avoid measure-theoretic complications.

These assumptions are standard in the generative modeling literature and are weaker than those required by many existing approaches.

## 2.5 Relation to Existing Formulations

Our formulation addresses critical limitations in current generative modeling paradigms:

**Generative Adversarial Networks (GANs)** employ a similar single-pass generation mechanism but rely on adversarial training, which introduces training instability and requires careful balancing of generator and discriminator updates. Our formulation seeks to avoid this adversarial structure entirely.

**Variational Autoencoders (VAEs)** optimize a tractable lower bound on the log-likelihood but typically produce blurry samples due to the Gaussian decoder assumption and KL regularization. Our approach aims for direct distributional matching without variational approximations.

**Normalizing Flows** achieve exact likelihood computation through invertible transformations but are constrained by architectural limitations and computational overhead from Jacobian determinant calculations.

**Diffusion Models** achieve state-of-the-art sample quality but require hundreds of denoising steps at inference time, violating our single-pass constraint.

**Score-based Models** learn the gradient of the log-density but similarly require iterative sampling procedures through stochastic differential equations.

The key gap our formulation addresses is the lack of a training objective that enables high-quality, single-pass generation without adversarial dynamics or variational approximations. This requires developing new theoretical frameworks that can directly optimize distributional alignment while maintaining computational tractability.
