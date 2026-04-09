# Problem Formulation

## 2.1 Notation and Problem Setup

Let $\mathcal{X} \subseteq \mathbb{R}^d$ denote the data space and $p$ be a fixed reference distribution on $\mathcal{X}$ (typically standard Gaussian). Let $q$ denote the target data distribution we wish to model. Our goal is to learn a generator $f_\theta: \mathcal{X} \to \mathcal{X}$ parameterized by $\theta$ that maps samples from $p$ to samples that approximate $q$.

We denote by $f_\theta\#p$ the **pushforward distribution** of $p$ under $f_\theta$, defined by $(f_\theta\#p)(A) = p(f_\theta^{-1}(A))$ for any measurable set $A$. The fundamental challenge is to find $\theta$ such that $f_\theta\#p \approx q$.

Let $\{x_i\}_{i=1}^n \sim q$ denote i.i.d. samples from the target distribution, and let $\{\epsilon_i\}_{i=1}^m \sim p$ denote samples from the reference distribution. During training at iteration $t$, we have access to the current generator $f_{\theta_t}$ and can generate samples $\{f_{\theta_t}(\epsilon_j)\}_{j=1}^m$ from the current pushforward distribution $f_{\theta_t}\#p$.

## 2.2 Drift Field Formulation

The core insight is to view generative modeling as a dynamical system where generated samples evolve according to a **drift field** during training. We define the drift field $V_{p,q}: \mathcal{X} \to \mathcal{X}$ that specifies how points should move to better align the pushforward distribution with the target distribution.

For any point $z \in \mathcal{X}$, we define:
$$V_{p,q}(z) = \mathbb{E}_{x \sim q}[w_+(z,x) \cdot x] - \mathbb{E}_{y \sim p}[w_-(z,f_\theta(y)) \cdot f_\theta(y)]$$

where $w_+: \mathcal{X} \times \mathcal{X} \to \mathbb{R}_+$ and $w_-: \mathcal{X} \times \mathcal{X} \to \mathbb{R}_+$ are positive weighting functions that determine the influence of nearby points. The first term represents attraction toward data samples (positive drift), while the second term represents repulsion from other generated samples (negative drift).

**Key Property (Anti-symmetry):** The drift field satisfies $V_{p,q}(z) = -V_{q,p}(z)$, which ensures that when $f_\theta\#p = q$, the drift field becomes zero everywhere, creating a natural equilibrium.

## 2.3 Training Objective

During training, we minimize the following loss function:
$$\mathcal{L}(\theta) = \mathbb{E}_{\epsilon \sim p}\left[\|f_\theta(\epsilon) - \text{stopgrad}(f_\theta(\epsilon) + V_{f_\theta\#p,q}(f_\theta(\epsilon)))\|^2\right]$$

where $\text{stopgrad}(\cdot)$ denotes the stop-gradient operator that prevents gradients from flowing through its argument during backpropagation.

The empirical version of this loss, computed using finite samples, is:
$$\hat{\mathcal{L}}(\theta) = \frac{1}{m}\sum_{j=1}^m \|f_\theta(\epsilon_j) - \text{stopgrad}(f_\theta(\epsilon_j) + \hat{V}(f_\theta(\epsilon_j)))\|^2$$

where the empirical drift field is:
$$\hat{V}(z) = \frac{1}{n}\sum_{i=1}^n w_+(z,x_i) \cdot x_i - \frac{1}{m}\sum_{k=1}^m w_-(z,f_\theta(\epsilon_k)) \cdot f_\theta(\epsilon_k)$$

## 2.4 Formal Problem Statement

**Given:**
- Target data samples $\{x_i\}_{i=1}^n \sim q$
- Reference distribution $p$ (e.g., $\mathcal{N}(0,I)$)
- Generator architecture $f_\theta: \mathcal{X} \to \mathcal{X}$
- Weighting functions $w_+, w_-: \mathcal{X} \times \mathcal{X} \to \mathbb{R}_+$

**Find:** Parameters $\theta^*$ such that:
1. $f_{\theta^*}\#p \approx q$ (distributional matching)
2. $f_{\theta^*}$ generates high-quality samples in a single forward pass
3. The training process converges to an equilibrium where $V_{f_{\theta^*}\#p,q}(z) \approx 0$ for $z$ in the support of $f_{\theta^*}\#p$

**Optimization Objective:** 
$$\theta^* = \arg\min_\theta \mathcal{L}(\theta)$$

## 2.5 Technical Assumptions

1. **Smoothness:** The generator $f_\theta$ is differentiable with respect to $\theta$, and the weighting functions $w_+, w_-$ are continuous.

2. **Bounded Support:** Both $p$ and $q$ have bounded support or exponentially decaying tails to ensure the drift field is well-defined.

3. **Non-degeneracy:** The weighting functions satisfy $w_+(z,x) > 0$ and $w_-(z,y) > 0$ for all relevant $(z,x)$ and $(z,y)$ pairs to prevent trivial solutions.

4. **Finite Sample Approximation:** We assume $n,m$ are sufficiently large such that the empirical drift field $\hat{V}$ provides a reasonable approximation to the true drift field $V_{p,q}$.

5. **Feature Space:** In practice, the drift field may be computed in a learned feature space $\phi: \mathcal{X} \to \mathcal{Z}$ using a pre-trained encoder, requiring $\phi$ to preserve relevant geometric structure.

## 2.6 Connection to Prior Work

This formulation addresses key limitations of existing generative modeling approaches:

- **Diffusion Models** perform iterative refinement at inference time through a learned denoising process. Our approach moves this iteration to training time via the evolving pushforward distribution.

- **GANs** use adversarial training between generator and discriminator networks, but lack the explicit geometric structure of our drift field formulation.

- **Flow Models** learn invertible transformations but require architectural constraints. Our approach allows arbitrary generator architectures while maintaining theoretical grounding through the anti-symmetric drift field.

- **Mean-Shift Algorithms** traditionally move points toward density modes. Our generalization uses separate positive and negative point sets with anti-symmetric dynamics.

The key innovation is recognizing that the iterative nature of training can be explicitly leveraged to evolve the generator's output distribution, eliminating the need for iteration at inference time while maintaining the modeling capacity that makes iterative approaches successful.