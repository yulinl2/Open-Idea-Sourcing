# Reconstruction: problem
**Paper:** 2602.04770  
**Condition:** no_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Problem Formulation

## 2.1 Notation and Setup

Let $\mathcal{X} \subset \mathbb{R}^d$ denote the data space and $p_{\text{data}}(\mathbf{x})$ the unknown target data distribution over $\mathcal{X}$. We assume access to a dataset $\mathcal{D} = \{\mathbf{x}_i\}_{i=1}^N$ of i.i.d. samples drawn from $p_{\text{data}}$. Let $\mathcal{Z} \subset \mathbb{R}^k$ denote a latent space equipped with a simple prior distribution $p_{\mathcal{Z}}(\mathbf{z})$, typically chosen as a standard Gaussian $\mathcal{N}(\mathbf{0}, \mathbf{I})$ for tractability.

We seek to learn a generative mapping $G_\theta: \mathcal{Z} \rightarrow \mathcal{X}$ parameterized by $\theta \in \Theta$ that transforms samples from the prior $p_{\mathcal{Z}}$ to samples that approximate the data distribution. For conditional generation, we extend this to $G_\theta: \mathcal{Z} \times \mathcal{C} \rightarrow \mathcal{X}$, where $\mathcal{C}$ represents the conditioning space (e.g., class labels, text embeddings, or other auxiliary information).

The pushforward distribution induced by the generator is defined as:
$$p_\theta(\mathbf{x}) = \int_{\mathcal{Z}} p_{\mathcal{Z}}(\mathbf{z}) \delta(\mathbf{x} - G_\theta(\mathbf{z})) d\mathbf{z}$$
where $\delta(\cdot)$ is the Dirac delta function.

## 2.2 Problem Statement

**Given:** A dataset $\mathcal{D}$ sampled from an unknown distribution $p_{\text{data}}$ and a tractable prior $p_{\mathcal{Z}}$.

**Find:** Parameters $\theta^*$ for a generator $G_\theta$ such that:
1. The pushforward distribution $p_{\theta^*}$ closely approximates $p_{\text{data}}$
2. Generation requires only a single forward pass: $\mathbf{x} = G_{\theta^*}(\mathbf{z})$ for $\mathbf{z} \sim p_{\mathcal{Z}}$
3. The mapping preserves the support and captures the full diversity of $p_{\text{data}}$

**Constraints:**
- No iterative refinement during inference
- No adversarial training dynamics
- Scalability to high-dimensional data

## 2.3 Optimization Objective

The core challenge lies in defining a training objective that enables learning the complex distribution mapping $p_{\mathcal{Z}} \rightarrow p_{\text{data}}$ without deferring computational complexity to inference time. We formulate this as finding:

$$\theta^* = \arg\min_\theta \mathcal{L}(\theta)$$

where the loss function $\mathcal{L}(\theta)$ must satisfy several requirements. First, it should measure distributional discrepancy:
$$\mathcal{L}(\theta) = D(p_{\text{data}}, p_\theta) + \mathcal{R}(\theta)$$

where $D(\cdot, \cdot)$ is a suitable divergence measure and $\mathcal{R}(\theta)$ represents regularization terms.

However, direct computation of $D(p_{\text{data}}, p_\theta)$ is intractable since we cannot evaluate $p_\theta$ explicitly. The fundamental challenge is designing a tractable surrogate objective that:

1. **Approximates distributional alignment** without requiring density evaluation
2. **Avoids adversarial dynamics** that can lead to training instability
3. **Supports single-step generation** without iterative procedures
4. **Scales efficiently** to high-dimensional problems

## 2.4 Technical Assumptions

We make the following assumptions to ensure theoretical tractability and practical feasibility:

**A1 (Smoothness):** The generator $G_\theta$ is differentiable almost everywhere, enabling gradient-based optimization.

**A2 (Universal approximation):** The function class parameterized by $\theta$ has sufficient capacity to approximate the optimal transport map between $p_{\mathcal{Z}}$ and $p_{\text{data}}$, justified by universal approximation theorems for neural networks.

**A3 (Data accessibility):** We have access to sufficient samples from $p_{\text{data}}$ to estimate expectations and gradients reliably, with sample complexity scaling polynomially with problem dimension.

**A4 (Prior-data compatibility):** The dimensions of latent and data spaces satisfy $k \leq d$, ensuring the existence of an injective mapping that preserves the support of $p_{\text{data}}$.

**A5 (Regularity):** Both $p_{\text{data}}$ and $p_{\mathcal{Z}}$ have bounded support or sufficiently light tails to ensure finite moments, guaranteeing convergence of empirical estimates.

## 2.5 Relationship to Existing Formulations

Current generative modeling paradigms address distribution learning through different computational trade-offs:

**Generative Adversarial Networks (GANs)** formulate generation as a minimax game:
$$\min_\theta \max_\phi \mathbb{E}_{\mathbf{x} \sim p_{\text{data}}}[\log D_\phi(\mathbf{x})] + \mathbb{E}_{\mathbf{z} \sim p_{\mathcal{Z}}}[\log(1 - D_\phi(G_\theta(\mathbf{z})))]$$

While GANs achieve single-step generation, they suffer from adversarial training instabilities and mode collapse.

**Variational Autoencoders (VAEs)** optimize a variational lower bound:
$$\mathcal{L}_{\text{VAE}} = \mathbb{E}_{\mathbf{x} \sim p_{\text{data}}}[\mathbb{E}_{q_\phi(\mathbf{z}|\mathbf{x})}[-\log p_\theta(\mathbf{x}|\mathbf{z})] + \text{KL}(q_\phi(\mathbf{z}|\mathbf{x}) \| p(\mathbf{z}))]$$

VAEs provide stable training but often produce blurry samples due to the reconstruction objective.

**Diffusion Models** learn to reverse a forward noising process:
$$\mathcal{L}_{\text{diffusion}} = \mathbb{E}_{t,\mathbf{x}_0,\boldsymbol{\epsilon}}[\|\boldsymbol{\epsilon} - \boldsymbol{\epsilon}_\theta(\mathbf{x}_t, t)\|^2]$$

While achieving excellent sample quality, diffusion models require hundreds of denoising steps during inference.

**Normalizing Flows** learn invertible transformations:
$$\log p_\theta(\mathbf{x}) = \log p_{\mathcal{Z}}(f_\theta^{-1}(\mathbf{x})) + \log|\det(\nabla_\mathbf{x} f_\theta^{-1}(\mathbf{x}))|$$

Flows enable exact likelihood computation but are constrained by architectural requirements for invertibility.

Our formulation seeks to combine the **single-step efficiency** of GANs with the **training stability** of VAEs, while achieving the **sample quality** of diffusion models without their inference-time computational burden. The key insight is that the complexity of distribution mapping should be absorbed during training through an appropriate objective function, rather than being deferred to inference time through iterative procedures.
