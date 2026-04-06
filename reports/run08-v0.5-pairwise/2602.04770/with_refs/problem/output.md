# Reconstruction: problem
**Paper:** 2602.04770  
**Condition:** with_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Problem Formulation

## 2.1 Notation and Setup

Let $\mathcal{X}$ denote the data space and $p_{\text{data}}$ the unknown target data distribution over $\mathcal{X}$. We consider the problem of learning a generative model that can produce samples from $p_{\text{data}}$ in a single forward pass. Let $\mathcal{Z}$ denote a latent space with a simple prior distribution $p_{\text{prior}}(\mathbf{z})$ (typically standard Gaussian), and let $G_{\boldsymbol{\theta}}: \mathcal{Z} \to \mathcal{X}$ be a neural network parameterized by $\boldsymbol{\theta}$.

The fundamental challenge is to learn a mapping $G_{\boldsymbol{\theta}}$ such that the pushforward measure $G_{\boldsymbol{\theta}}\#p_{\text{prior}}$ approximates $p_{\text{data}}$, where $(G_{\boldsymbol{\theta}}\#p_{\text{prior}})(\mathbf{x}) = \int p_{\text{prior}}(\mathbf{z}) \delta(G_{\boldsymbol{\theta}}(\mathbf{z}) - \mathbf{x}) d\mathbf{z}$ denotes the distribution of $G_{\boldsymbol{\theta}}(\mathbf{z})$ when $\mathbf{z} \sim p_{\text{prior}}$.

Given a training dataset $\mathcal{D} = \{\mathbf{x}_i\}_{i=1}^n$ where $\mathbf{x}_i \sim p_{\text{data}}$ independently, we seek to find parameters $\boldsymbol{\theta}^*$ that minimize a suitable divergence between the model distribution and the data distribution.

## 2.2 Problem Statement

**Given:** 
- Training data $\mathcal{D} = \{\mathbf{x}_i\}_{i=1}^n$ sampled i.i.d. from unknown distribution $p_{\text{data}}$
- Prior distribution $p_{\text{prior}}(\mathbf{z})$ on latent space $\mathcal{Z}$
- Neural network architecture $G_{\boldsymbol{\theta}}: \mathcal{Z} \to \mathcal{X}$

**Find:** Parameters $\boldsymbol{\theta}^*$ such that $G_{\boldsymbol{\theta}^*}$ enables high-quality sample generation via:
$$\mathbf{z} \sim p_{\text{prior}}, \quad \mathbf{x} = G_{\boldsymbol{\theta}^*}(\mathbf{z})$$

**Subject to:** Single forward pass constraint - no iterative refinement at inference time.

The core challenge is that direct optimization of distributional divergences like KL divergence or Wasserstein distance is intractable, as they require access to density functions or solutions to optimal transport problems that are computationally prohibitive for high-dimensional data.

## 2.3 Objective Formulation

Drawing inspiration from the conformal prediction framework of Tibshirani et al. (2020), which provides distribution-free guarantees by comparing conformity scores, we propose to learn the generator by optimizing a **flow matching objective** that enables tractable training while maintaining the single-step generation property.

Specifically, we define a time-dependent vector field $v_t(\mathbf{x}): [0,1] \times \mathcal{X} \to \mathcal{X}$ and consider the ordinary differential equation (ODE):
$$\frac{d\mathbf{x}_t}{dt} = v_t(\mathbf{x}_t), \quad \mathbf{x}_0 \sim p_{\text{prior}}, \quad \mathbf{x}_1 \sim p_{\text{data}}$$

The key insight is to construct a **conditional flow** $\psi_t(\mathbf{x} | \mathbf{x}_1)$ that interpolates between the prior and each data point:
$$\psi_t(\mathbf{x} | \mathbf{x}_1) = (1-t)\mathbf{x} + t\mathbf{x}_1 + \sigma_t \boldsymbol{\epsilon}$$
where $\boldsymbol{\epsilon} \sim \mathcal{N}(\mathbf{0}, \mathbf{I})$ and $\sigma_t$ is a time-dependent noise schedule.

The **flow matching loss** is then defined as:
$$\mathcal{L}_{\text{FM}}(\boldsymbol{\theta}) = \mathbb{E}_{t \sim \mathcal{U}[0,1]} \mathbb{E}_{\mathbf{x}_1 \sim p_{\text{data}}} \mathbb{E}_{\mathbf{x}_t \sim p_t(\cdot | \mathbf{x}_1)} \left\| v_{\boldsymbol{\theta}}(t, \mathbf{x}_t) - \frac{d\psi_t(\mathbf{x}_t | \mathbf{x}_1)}{dt} \right\|^2$$

where $v_{\boldsymbol{\theta}}$ is a neural network that learns to predict the vector field, and $p_t(\mathbf{x} | \mathbf{x}_1)$ is the marginal distribution of $\psi_t(\mathbf{x} | \mathbf{x}_1)$.

## 2.4 Technical Assumptions

**A1 (Regularity):** The vector field $v_{\boldsymbol{\theta}}$ is Lipschitz continuous in $\mathbf{x}$ uniformly over $t \in [0,1]$, ensuring existence and uniqueness of ODE solutions.

**A2 (Universal Approximation):** The neural network class has sufficient capacity to approximate the optimal vector field within arbitrary precision on compact domains.

**A3 (Data Regularity):** The target distribution $p_{\text{data}}$ has finite second moments and is supported on a bounded domain (or has exponentially decaying tails).

**A4 (Interpolation Path):** The conditional flow $\psi_t(\mathbf{x} | \mathbf{x}_1)$ defines a valid probability path from $p_{\text{prior}}$ to data points, with $\psi_0(\mathbf{x} | \mathbf{x}_1) \sim p_{\text{prior}}$ and $\psi_1(\mathbf{x} | \mathbf{x}_1) = \mathbf{x}_1$.

These assumptions are standard in the continuous normalizing flow literature and significantly weaker than assumptions required by adversarial training approaches.

## 2.5 Connection to Prior Work and Novel Contributions

**Relation to Conformal Prediction:** While Tibshirani et al. (2020) develop weighted conformal prediction for distribution-free inference under covariate shift, our approach adapts their core insight about comparing conformity scores in a weighted manner. In our context, the "conformity" of a generated sample is measured by how well it follows the learned vector field, and we weight different training trajectories based on their likelihood under the interpolating path.

**Departure from Multi-Step Methods:** Unlike diffusion models that require hundreds of denoising steps, or normalizing flows that need invertible architectures, our formulation enables generation via a single ODE integration from $t=0$ to $t=1$. This addresses the fundamental computational bottleneck of iterative generation methods.

**Beyond Adversarial Training:** Traditional GANs optimize a min-max objective that can suffer from mode collapse and training instability. Our flow matching objective provides a direct, stable optimization target without adversarial dynamics, similar to how conformal prediction avoids distributional assumptions by focusing on rank-based guarantees.

**Gap Addressed:** Existing single-step generation methods either require restrictive architectural constraints (invertibility for normalizing flows) or suffer from training instabilities (GANs). Our formulation provides a principled, stable training objective for single-step generation that scales to high-dimensional data while maintaining theoretical guarantees about the learned distribution.

The key innovation is recognizing that optimal transport between distributions can be learned implicitly through vector field matching, avoiding both the computational overhead of multi-step sampling and the instabilities of adversarial optimization.
