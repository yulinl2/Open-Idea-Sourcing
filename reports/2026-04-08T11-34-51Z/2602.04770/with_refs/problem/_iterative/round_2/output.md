# Problem Formulation

## 2.1 Notation and Problem Setup

Let $\mathcal{X} \subseteq \mathbb{R}^d$ denote the data space and $\mathcal{Z} \subseteq \mathbb{R}^m$ denote the noise space, where $d, m \in \mathbb{N}$. We consider two probability distributions: the target data distribution $p_{\text{data}}$ supported on $\mathcal{X}$, and a simple noise distribution $p_{\text{noise}}$ supported on $\mathcal{Z}$ (typically a standard Gaussian). Let $G_\theta: \mathcal{Z} \to \mathcal{X}$ be a neural network parameterized by $\theta \in \Theta \subseteq \mathbb{R}^k$, where $\Theta$ is a compact parameter space.

For any generator $G_\theta$, we define the induced distribution $p_\theta$ on $\mathcal{X}$ as the pushforward of $p_{\text{noise}}$ through $G_\theta$:
$$p_\theta(x) = \int_{\mathcal{Z}} p_{\text{noise}}(z) \delta(x - G_\theta(z)) dz$$

Let $\mathcal{D}(\cdot, \cdot)$ denote a divergence measure between probability distributions (e.g., Wasserstein distance, KL divergence). The fundamental challenge in generative modeling is to find parameters $\theta^*$ such that $\mathcal{D}(p_{\theta^*}, p_{\text{data}})$ is minimized.

## 2.2 The Distribution Evolution Framework

We propose to reformulate generative modeling as a dynamical system where the generated distribution evolves during training toward the target distribution. Let $\{G_{\theta_t}\}_{t=0}^T$ denote a sequence of generators indexed by training iteration $t$, with corresponding induced distributions $\{p_{\theta_t}\}_{t=0}^T$.

**Definition 1** (Distribution Evolution). A distribution evolution is a sequence $\{p_{\theta_t}\}_{t=0}^T$ where $p_{\theta_0}$ is an initial distribution (typically far from $p_{\text{data}}$) and $p_{\theta_T}$ approximates $p_{\text{data}}$ for sufficiently large $T$.

The key insight is to leverage the iterative nature of neural network training to drive this evolution, rather than requiring iterative refinement at inference time. At each training step $t$, we update the generator parameters via:
$$\theta_{t+1} = \theta_t - \eta \nabla_\theta \mathcal{L}(\theta_t)$$
where $\eta > 0$ is the learning rate and $\mathcal{L}(\theta)$ is a loss function to be specified.

## 2.3 Formal Problem Statement

**Given**: 
- A dataset $\mathcal{S} = \{x_i\}_{i=1}^n$ where $x_i \sim p_{\text{data}}$ i.i.d.
- A noise distribution $p_{\text{noise}}$
- A generator architecture $G_\theta: \mathcal{Z} \to \mathcal{X}$

**Find**: Parameters $\theta^*$ and a training procedure such that:

1. **Single-pass generation**: $G_{\theta^*}$ produces high-quality samples in one forward pass
2. **Distribution matching**: $\lim_{T \to \infty} \mathcal{D}(p_{\theta_T}, p_{\text{data}}) = 0$
3. **Training convergence**: The sequence $\{\theta_t\}_{t=0}^T$ converges to a stationary point

## 2.4 The Flow-Based Objective

We propose a training objective that directly optimizes the evolution of the generated distribution. Let $p_{\theta_t}$ and $p_{\theta_{t+1}}$ be consecutive distributions in the evolution sequence. The core idea is to minimize:

$$\mathcal{L}(\theta_t) = \mathcal{D}(p_{\theta_{t+1}}, p_{\text{data}}) + \lambda \mathcal{R}(p_{\theta_t}, p_{\theta_{t+1}})$$

where $\mathcal{R}(p_{\theta_t}, p_{\theta_{t+1}})$ is a regularization term that ensures smooth evolution, and $\lambda > 0$ is a regularization weight.

**Definition 2** (Flow Consistency). A generator sequence $\{G_{\theta_t}\}$ satisfies flow consistency if there exists a vector field $v_t: \mathcal{X} \to \mathcal{X}$ such that:
$$\frac{\partial p_{\theta_t}}{\partial t} + \nabla \cdot (p_{\theta_t} v_t) = 0$$

This ensures that the distribution evolution follows a continuous flow, connecting the noise distribution to the data distribution.

## 2.5 Assumptions

We make the following technical assumptions:

**A1** (Data regularity): The data distribution $p_{\text{data}}$ has bounded support and is absolutely continuous with respect to Lebesgue measure.

**A2** (Generator capacity): The generator class $\{G_\theta : \theta \in \Theta\}$ is rich enough to approximate any continuous function on compact subsets of $\mathcal{Z}$ (universal approximation).

**A3** (Lipschitz continuity): For each $\theta$, the generator $G_\theta$ is $L$-Lipschitz continuous for some $L > 0$, ensuring stable training dynamics.

**A4** (Noise distribution): $p_{\text{noise}}$ is a tractable distribution (e.g., standard Gaussian) that allows efficient sampling.

**A5** (Training dynamics): The loss function $\mathcal{L}(\theta)$ is differentiable and the gradient flow $\dot{\theta} = -\nabla_\theta \mathcal{L}(\theta)$ has a unique global minimum.

These assumptions ensure that: (A1-A2) the problem is well-posed and has a solution; (A3) training is numerically stable; (A4) efficient sampling is possible; and (A5) training converges to the desired equilibrium.

## 2.6 Connection to Prior Work

Traditional generative approaches can be viewed as special cases of our framework:

**Generative Adversarial Networks** optimize a minimax objective but require careful balancing of generator and discriminator updates, often leading to training instability. Our approach eliminates the adversarial component by directly optimizing distribution evolution.

**Variational Autoencoders** optimize a variational bound on the data likelihood but are limited by the choice of encoder architecture and prior distribution. Our framework directly optimizes the generator without requiring an encoder.

**Diffusion Models** perform iterative refinement at inference time, requiring $T$ network evaluations to generate a sample. Our approach moves this iteration to training time, enabling single-pass generation.

**Normalizing Flows** learn invertible transformations but are constrained by architectural requirements for invertibility. Our framework relaxes this constraint by optimizing the flow during training rather than enforcing it architecturally.

The key gap addressed by our formulation is the trade-off between generation quality and inference efficiency. Existing methods either sacrifice quality for speed (single-pass methods like VAEs) or require expensive iterative procedures (diffusion models). Our approach aims to achieve both high quality and single-pass efficiency by leveraging the training process itself as the iterative refinement mechanism.