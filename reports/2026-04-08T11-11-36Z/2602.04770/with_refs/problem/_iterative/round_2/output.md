# Problem Formulation

## 2.1 Notation and Setup

Let $\mathcal{X}$ denote the data space (e.g., $\mathbb{R}^d$ for images or sequences) and let $P_{\text{data}}$ be the unknown target data distribution over $\mathcal{X}$. We consider the standard generative modeling setup where we have access to a training dataset $\{x_i\}_{i=1}^n$ with $x_i \sim P_{\text{data}}$ i.i.d., and our goal is to learn a generative model that can produce samples resembling those from $P_{\text{data}}$.

Let $P_{\text{noise}}$ denote a simple prior distribution (typically $\mathcal{N}(0, I)$) over a latent space $\mathcal{Z} \subseteq \mathbb{R}^k$. A generative model is parameterized by a neural network $G_\theta: \mathcal{Z} \to \mathcal{X}$ with parameters $\theta \in \Theta$. The pushforward measure induced by $G_\theta$ is denoted $G_\theta \sharp P_{\text{noise}}$, where $(G_\theta \sharp P_{\text{noise}})(A) = P_{\text{noise}}(G_\theta^{-1}(A))$ for any measurable set $A \subseteq \mathcal{X}$.

During training, we consider a sequence of generator parameters $\{\theta_t\}_{t=0}^T$ evolving according to some optimization dynamics. Let $P_t = G_{\theta_t} \sharp P_{\text{noise}}$ denote the generated distribution at training step $t$. Our framework requires defining a family of positive kernel functions $\{K_t: \mathcal{X} \times \mathcal{X} \to \mathbb{R}_+\}_{t=0}^T$ that will guide the evolution of the generated distribution.

## 2.2 Problem Statement

**Given:** 
- Training data $\{x_i\}_{i=1}^n$ sampled i.i.d. from unknown $P_{\text{data}}$
- Prior distribution $P_{\text{noise}}$ over latent space $\mathcal{Z}$
- Family of kernel functions $\{K_t\}_{t=0}^T$

**Find:** A sequence of generator parameters $\{\theta_t\}_{t=0}^T$ such that:

1. **Single-step generation:** At convergence ($t = T$), $G_{\theta_T}$ produces high-quality samples in one forward pass: $z \sim P_{\text{noise}} \mapsto G_{\theta_T}(z)$

2. **Distribution matching:** The final generated distribution $P_T$ closely approximates $P_{\text{data}}$ in a distributional sense

3. **Principled evolution:** The sequence $\{P_t\}_{t=0}^T$ follows a well-defined trajectory in distribution space, with $P_0$ typically far from $P_{\text{data}}$ and $P_T \approx P_{\text{data}}$

## 2.3 Optimization Objective

We formulate the training objective as a kernel-based distributional matching problem. At each training step $t$, we seek to minimize:

$$\mathcal{L}_t(\theta) = \mathbb{E}_{x \sim P_{\text{data}}} \mathbb{E}_{x' \sim G_\theta \sharp P_{\text{noise}}} K_t(x, x') - \frac{1}{2}\mathbb{E}_{x, x' \sim P_{\text{data}}} K_t(x, x') - \frac{1}{2}\mathbb{E}_{x, x' \sim G_\theta \sharp P_{\text{noise}}} K_t(x, x')$$

This can be equivalently written as:
$$\mathcal{L}_t(\theta) = -\frac{1}{2}\|\mu_{P_{\text{data}}}^{K_t} - \mu_{G_\theta \sharp P_{\text{noise}}}^{K_t}\|_{\mathcal{H}_{K_t}}^2$$

where $\mu_P^{K_t}$ denotes the kernel mean embedding of distribution $P$ in the reproducing kernel Hilbert space (RKHS) $\mathcal{H}_{K_t}$ induced by kernel $K_t$.

The overall training procedure evolves $\theta_t$ according to:
$$\theta_{t+1} = \theta_t - \eta_t \nabla_\theta \mathcal{L}_t(\theta_t)$$

where $\eta_t > 0$ is the learning rate at step $t$.

## 2.4 Key Technical Assumptions

**A1 (Kernel Properties):** Each $K_t$ is a positive definite kernel with bounded RKHS norm, and the kernel family $\{K_t\}$ is designed such that characteristic kernels (those for which kernel mean embeddings are injective) appear in the sequence.

**A2 (Generator Expressivity):** The generator family $\{G_\theta : \theta \in \Theta\}$ has sufficient capacity to approximate the optimal transport map from $P_{\text{noise}}$ to $P_{\text{data}}$, at least within the support of the data distribution.

**A3 (Kernel Evolution):** The kernel sequence $\{K_t\}$ evolves in a way that initially focuses on matching coarse distributional properties and progressively refines to capture finer-scale structure. Formally, we assume there exists a schedule such that early kernels have large bandwidth/low frequency content while later kernels capture high-frequency details.

**A4 (Optimization Landscape):** The loss functions $\{\mathcal{L}_t\}$ have favorable optimization properties, with critical points corresponding to distributional matches and avoiding pathological local minima that would prevent convergence to the target distribution.

**A5 (Finite Sample Approximation):** The empirical approximation of $\mathcal{L}_t$ using finite training data provides a sufficiently accurate proxy for the population objective, with approximation error decreasing as $n \to \infty$.

These assumptions are necessary to ensure that: (i) the kernel-based objective provides meaningful distributional distance, (ii) the generator can represent the required mapping, (iii) the progressive kernel schedule enables stable training, (iv) optimization can find good solutions, and (v) finite data training generalizes to the true distribution.

## 2.5 Connection to Prior Work

Our formulation addresses key limitations in existing generative modeling paradigms:

**Iterative Methods:** Unlike diffusion models and autoregressive approaches that require $O(T)$ network evaluations at inference time, our method performs generation in $O(1)$ forward passes while leveraging iterative training dynamics.

**Adversarial Training:** Unlike GANs which rely on adversarial min-max optimization that can suffer from training instabilities and mode collapse, our approach uses a single-objective kernel-based loss that directly measures distributional discrepancy.

**Likelihood-based Models:** Unlike VAEs and normalizing flows that require architectural constraints for tractable likelihood computation, our method can use arbitrary generator architectures by focusing on distributional matching rather than explicit density modeling.

**Kernel Methods:** While kernel-based approaches like Maximum Mean Discrepancy (MMD) have been explored for generative modeling, prior work typically uses fixed kernels throughout training. Our key innovation is the progressive evolution of kernels during training, enabling a curriculum that starts with coarse distributional matching and refines to capture fine details.

The progressive kernel schedule addresses the fundamental challenge that learning complex distribution mappings in a single step is difficult, but can be decomposed into a sequence of simpler matching problems that collectively achieve the desired transformation while maintaining single-step inference capability.