# Problem Formulation

## Notation and Problem Setup

Let $\mathcal{X}$ denote the data space (e.g., $\mathcal{X} = \mathbb{R}^d$ for $d$-dimensional real-valued data) and let $p_{\text{data}}$ be the unknown target distribution over $\mathcal{X}$. We consider the fundamental problem of learning a generative model that can efficiently map from a simple prior distribution to the complex data distribution.

Let $p_{\text{prior}}$ denote a tractable prior distribution over $\mathcal{Z}$, where $\mathcal{Z}$ is a latent space (typically $\mathcal{Z} = \mathbb{R}^k$ for some dimension $k$). We assume $p_{\text{prior}}$ is easy to sample from, such as a standard Gaussian $\mathcal{N}(0, I_k)$. Let $G_\theta: \mathcal{Z} \to \mathcal{X}$ be a parametric generator network with parameters $\theta \in \Theta$, where $\Theta$ is the parameter space.

For a sample $z \sim p_{\text{prior}}$, the generator produces $x = G_\theta(z)$, inducing a pushforward distribution $p_\theta = G_\theta \# p_{\text{prior}}$ over $\mathcal{X}$, defined by
$$p_\theta(A) = p_{\text{prior}}(G_\theta^{-1}(A))$$
for any measurable set $A \subseteq \mathcal{X}$.

Let $\{x_i\}_{i=1}^n$ be i.i.d. samples from $p_{\text{data}}$. We denote the empirical data distribution as $\hat{p}_n = \frac{1}{n}\sum_{i=1}^n \delta_{x_i}$, where $\delta_{x_i}$ is the Dirac delta at $x_i$.

## Formal Problem Statement

**Given:** 
- A dataset $\mathcal{D} = \{x_i\}_{i=1}^n$ with $x_i \sim p_{\text{data}}$ i.i.d.
- A tractable prior distribution $p_{\text{prior}}$ over latent space $\mathcal{Z}$
- A parametric generator family $\{G_\theta : \theta \in \Theta\}$

**Find:** Parameters $\theta^* \in \Theta$ such that the induced distribution $p_{\theta^*}$ approximates $p_{\text{data}}$ well, enabling high-quality sample generation in a single forward pass.

**Guarantee:** The learned generator $G_{\theta^*}$ should satisfy:
1. **Sample Quality:** Generated samples $G_{\theta^*}(z)$ for $z \sim p_{\text{prior}}$ are perceptually and statistically similar to samples from $p_{\text{data}}$
2. **Distribution Coverage:** The pushforward distribution $p_{\theta^*}$ captures the full support and modes of $p_{\text{data}}$
3. **Computational Efficiency:** Generation requires only a single forward pass through $G_{\theta^*}$

## Optimization Objective

The core challenge is to define a training objective that enables learning the complex distribution mapping without requiring iterative refinement. We seek to minimize a divergence between the target and generated distributions:

$$\theta^* = \arg\min_{\theta \in \Theta} \mathcal{L}(p_{\text{data}}, p_\theta)$$

where $\mathcal{L}$ is a suitable loss function measuring distributional discrepancy. The key requirement is that this objective should be:

1. **Tractable:** Computable from finite samples without intractable integrals
2. **Informative:** Provides meaningful gradients for learning complex mappings
3. **Stable:** Converges reliably during training without mode collapse
4. **Scalable:** Remains computationally feasible for high-dimensional data

Since we cannot directly optimize over distributions, we work with the empirical approximation:
$$\hat{\mathcal{L}}_n(\theta) = \mathcal{L}(\hat{p}_n, p_\theta)$$

The challenge is that standard approaches either require adversarial training (which can be unstable) or iterative sampling procedures (which violate our single-pass requirement).

## Technical Assumptions

We make the following technical assumptions:

**A1. Generator Expressivity:** The generator family $\{G_\theta\}$ has sufficient capacity to approximate the target distribution, i.e., there exists $\theta^* \in \Theta$ such that $p_{\theta^*} \approx p_{\text{data}}$ in an appropriate sense.

*Justification:* This is a standard approximation assumption in deep generative modeling, typically satisfied by sufficiently expressive neural networks.

**A2. Sample Complexity:** The dataset size $n$ is sufficiently large relative to the complexity of $p_{\text{data}}$ and the generator family to enable reliable estimation.

*Justification:* Standard statistical learning theory requirement for generalization from finite samples.

**A3. Regularity:** Both $p_{\text{data}}$ and $p_{\text{prior}}$ have densities with respect to appropriate reference measures, and the generator $G_\theta$ is sufficiently smooth.

*Justification:* Enables application of standard optimization techniques and theoretical analysis.

**A4. Prior Compatibility:** The prior $p_{\text{prior}}$ and generator architecture are chosen such that the induced distribution family $\{p_\theta\}$ can capture the essential characteristics of $p_{\text{data}}$.

*Justification:* Ensures the modeling approach is fundamentally sound for the target domain.

## Connection to Prior Work

Existing generative modeling approaches fall into several categories, each with limitations that our formulation aims to address:

**Variational Methods:** Variational autoencoders (VAEs) optimize a tractable lower bound but often produce blurry samples due to the restrictive variational approximation. Our formulation seeks direct distribution matching without variational bounds.

**Adversarial Methods:** Generative adversarial networks (GANs) learn through adversarial training but suffer from training instability and mode collapse. Our approach aims for a more direct, stable training objective.

**Likelihood-Based Methods:** Autoregressive models and normalizing flows provide tractable likelihood computation but require sequential generation or invertible architectures, respectively. We seek unconditional single-pass generation.

**Iterative Refinement:** Diffusion models achieve high sample quality through iterative denoising but require multiple network evaluations. Our formulation explicitly targets single-pass generation.

**Score-Based Methods:** These learn the score function of the data distribution but typically require iterative sampling procedures like Langevin dynamics.

The gap our formulation addresses is the lack of a principled, stable training paradigm that can learn complex distribution mappings for high-quality single-pass generation. We seek an objective that combines the stability and theoretical grounding of likelihood-based methods with the flexibility and sample quality of adversarial approaches, while maintaining the computational efficiency of single forward-pass generation.