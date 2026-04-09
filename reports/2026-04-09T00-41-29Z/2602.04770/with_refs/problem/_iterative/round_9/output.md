# Problem Formulation

## 2.1 Notation and Problem Setup

Let $\mathcal{X}$ denote the data space (e.g., $\mathbb{R}^d$ for images) and let $P_{\text{data}}$ be the unknown target distribution over $\mathcal{X}$. Our goal is to learn a generator network $G_\theta: \mathcal{Z} \to \mathcal{X}$ parameterized by $\theta \in \Theta$, where $\mathcal{Z}$ is a latent space (typically $\mathbb{R}^k$ with some simple prior distribution $P_z$, such as standard Gaussian). 

Let $P_{\theta} = G_\theta \# P_z$ denote the pushforward measure induced by the generator, where for any measurable set $A \subseteq \mathcal{X}$, we have $P_{\theta}(A) = P_z(G_\theta^{-1}(A))$. The fundamental challenge is to find parameters $\theta^*$ such that $P_{\theta^*} \approx P_{\text{data}}$.

During training, we have access to samples $\{x_i\}_{i=1}^n \sim P_{\text{data}}$ from the target distribution and can generate samples $\{G_\theta(z_j)\}_{j=1}^m$ where $z_j \sim P_z$. Let $\mathcal{F}$ denote a feature space equipped with a similarity kernel $k: \mathcal{F} \times \mathcal{F} \to \mathbb{R}_+$, and let $\phi: \mathcal{X} \to \mathcal{F}$ be a feature mapping (which may be learned jointly with the generator).

## 2.2 The Drift Field Formulation

The core insight is to view generated samples as particles that move in feature space according to a drift field during training. For any sample $x \in \mathcal{X}$, we define the drift field $v_t(x): \mathcal{X} \to \mathcal{F}$ at training iteration $t$ as:

$$v_t(x) = \mathbb{E}_{x' \sim P_{\text{data}}} [k(\phi(x), \phi(x')) \cdot (\phi(x') - \phi(x))] - \mathbb{E}_{x'' \sim P_{\theta_t}} [k(\phi(x), \phi(x'')) \cdot (\phi(x'') - \phi(x))]$$

This field has the crucial **anti-symmetry property**: if we swap the roles of $P_{\text{data}}$ and $P_{\theta_t}$, the drift direction flips:
$$v_t^{\text{swap}}(x) = \mathbb{E}_{x'' \sim P_{\theta_t}} [k(\phi(x), \phi(x'')) \cdot (\phi(x'') - \phi(x))] - \mathbb{E}_{x' \sim P_{\text{data}}} [k(\phi(x), \phi(x')) \cdot (\phi(x') - \phi(x))] = -v_t(x)$$

When $P_{\theta_t} = P_{\text{data}}$, we have $v_t(x) = 0$ for all $x$, establishing a natural equilibrium condition.

## 2.3 Sample Evolution Dynamics

During training, generated samples evolve according to the drift field. Specifically, let $\{x_j^{(t)}\}_{j=1}^m$ denote the generated samples at iteration $t$, where $x_j^{(t)} = G_{\theta_t}(z_j)$. The evolution of these samples follows:

$$x_j^{(t+1)} = x_j^{(t)} + \eta \cdot v_t(x_j^{(t)}) + \text{generator update}$$

where $\eta > 0$ is a step size and the generator update term captures how $G_{\theta_t} \to G_{\theta_{t+1}}$ affects sample positions.

In practice, we approximate the expectations in $v_t(x)$ using empirical averages:
$$\hat{v}_t(x) = \frac{1}{n}\sum_{i=1}^n k(\phi(x), \phi(x_i)) \cdot (\phi(x_i) - \phi(x)) - \frac{1}{m}\sum_{j=1}^m k(\phi(x), \phi(x_j^{(t)})) \cdot (\phi(x_j^{(t)}) - \phi(x))$$

## 2.4 Training Objective

The generator parameters are updated to minimize the discrepancy between the current sample positions and their drift-adjusted target positions. We define the training objective as:

$$\mathcal{L}(\theta_t) = \mathbb{E}_{z \sim P_z} \left[ \|\phi(G_{\theta_t}(z)) - \text{sg}(\phi(G_{\theta_t}(z)) + \hat{v}_t(G_{\theta_t}(z)))\|^2 \right]$$

where $\text{sg}(\cdot)$ denotes the stop-gradient operator, preventing backpropagation through the drift computation and creating stable targets for the generator to move toward.

## 2.5 Formal Problem Statement

**Given:** 
- Training samples $\{x_i\}_{i=1}^n \sim P_{\text{data}}$
- Generator architecture $G_\theta: \mathcal{Z} \to \mathcal{X}$
- Feature mapping $\phi: \mathcal{X} \to \mathcal{F}$ 
- Similarity kernel $k: \mathcal{F} \times \mathcal{F} \to \mathbb{R}_+$

**Find:** Parameters $\theta^*$ such that the iterative process:
$$\theta_{t+1} = \theta_t - \alpha \nabla_{\theta_t} \mathcal{L}(\theta_t)$$
converges to a point where $P_{\theta^*} \approx P_{\text{data}}$.

**Guarantee:** The anti-symmetry property of the drift field ensures that at equilibrium ($P_{\theta^*} = P_{\text{data}}$), the drift field vanishes ($v(x) = 0$ for all $x$), providing a principled stopping criterion.

## 2.6 Key Assumptions

1. **Feature Space Assumption:** The feature mapping $\phi$ provides a meaningful similarity metric such that $k(\phi(x), \phi(x'))$ reflects semantic similarity between samples $x$ and $x'$.

2. **Kernel Properties:** The kernel $k$ is positive, symmetric, and induces appropriate local averaging behavior (e.g., $k(u,v) = \exp(-\|u-v\|^2/\sigma^2)$ for some bandwidth $\sigma > 0$).

3. **Finite Sample Approximation:** The empirical approximations $\hat{v}_t$ converge to the true drift field $v_t$ as sample sizes $n,m \to \infty$.

4. **Generator Capacity:** The generator $G_\theta$ has sufficient capacity to represent the mapping needed to align $P_\theta$ with $P_{\text{data}}$.

5. **Smooth Evolution:** The generator updates are small enough that the drift field remains approximately valid across training steps.

## 2.7 Connection to Prior Work

This formulation addresses key limitations of existing generative modeling approaches:

- **Unlike GANs**, our method avoids adversarial training instabilities by using a principled drift field rather than a discriminator-based objective.
- **Unlike VAEs**, we do not require a tractable encoder or variational bound, allowing more flexible generator architectures.
- **Unlike diffusion models**, we achieve single-step generation without iterative denoising, while still leveraging iterative refinement during training.
- **Unlike normalizing flows**, we do not require invertible transformations, enabling standard feed-forward architectures.

The anti-symmetry property provides a mathematical foundation that existing methods lack, ensuring natural convergence when the generated and target distributions match.