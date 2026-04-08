# Problem Formulation

## 2.1 Notation and Setup

Let $\mathcal{X} \subseteq \mathbb{R}^d$ denote the data space and $p_{\text{data}}$ denote the unknown target data distribution over $\mathcal{X}$. Let $p_{\text{noise}}$ be a simple, tractable noise distribution (e.g., standard Gaussian $\mathcal{N}(0, I_d)$) from which we can easily sample. Our goal is to learn a generative model that can transform samples from $p_{\text{noise}}$ to samples from $p_{\text{data}}$ in a single forward pass.

Consider a parametric generator network $G_\theta: \mathcal{X} \to \mathcal{X}$ with parameters $\theta \in \Theta$. At any training iteration $t$, let $p_t$ denote the distribution induced by the current generator: if $\mathbf{z} \sim p_{\text{noise}}$, then $G_\theta^{(t)}(\mathbf{z}) \sim p_t$. We define the **velocity field** $\mathbf{v}_t: \mathcal{X} \to \mathcal{X}$ as the infinitesimal direction in which generated samples should move to better align with the target distribution.

Let $\{\mathbf{x}_i\}_{i=1}^n$ denote a dataset of $n$ samples drawn i.i.d. from $p_{\text{data}}$, and let $\{\mathbf{z}_j\}_{j=1}^m$ be samples drawn i.i.d. from $p_{\text{noise}}$. At iteration $t$, we generate synthetic samples $\{\mathbf{y}_j^{(t)}\}_{j=1}^m$ where $\mathbf{y}_j^{(t)} = G_\theta^{(t)}(\mathbf{z}_j)$.

## 2.2 Formal Problem Statement

**Given:** 
- A dataset $\{\mathbf{x}_i\}_{i=1}^n$ sampled i.i.d. from unknown target distribution $p_{\text{data}}$
- A tractable noise distribution $p_{\text{noise}}$ 
- A parametric generator family $\{G_\theta : \theta \in \Theta\}$

**Find:** Parameters $\theta^* \in \Theta$ such that the induced distribution $p^* = G_{\theta^*} \# p_{\text{noise}}$ (pushforward of $p_{\text{noise}}$ through $G_{\theta^*}$) satisfies $p^* \approx p_{\text{data}}$.

**Constraints:**
- Generation must require only a single forward pass: $\mathbf{x} = G_{\theta^*}(\mathbf{z})$ for $\mathbf{z} \sim p_{\text{noise}}$
- The training process may be iterative, but inference must be direct

## 2.3 Flow Field Dynamics

We model the evolution of the generated distribution during training as following a **flow field** that drives generated samples toward the data distribution. Specifically, we define the velocity field $\mathbf{v}_t(\mathbf{y})$ at iteration $t$ and position $\mathbf{y} \in \mathcal{X}$ as:

$$\mathbf{v}_t(\mathbf{y}) = \mathbb{E}_{\mathbf{x} \sim p_{\text{data}}} [K(\mathbf{x}, \mathbf{y}) \cdot (\mathbf{x} - \mathbf{y})] - \mathbb{E}_{\mathbf{y}' \sim p_t} [K(\mathbf{y}', \mathbf{y}) \cdot (\mathbf{y}' - \mathbf{y})]$$

where $K: \mathcal{X} \times \mathcal{X} \to \mathbb{R}_+$ is a positive definite kernel function. The first term represents an **attractive force** pulling generated samples toward data points, while the second term represents a **repulsive force** preventing generated samples from clustering together.

The generated samples evolve according to the flow dynamics:
$$\frac{d\mathbf{y}}{dt} = \mathbf{v}_t(\mathbf{y})$$

At equilibrium, when $p_t = p_{\text{data}}$, we have $\mathbf{v}_t(\mathbf{y}) = 0$ for all $\mathbf{y}$, as the attractive and repulsive forces balance.

## 2.4 Optimization Objective

In practice, we approximate the expectations in the velocity field using empirical samples. The empirical velocity field becomes:

$$\hat{\mathbf{v}}_t(\mathbf{y}) = \frac{1}{n}\sum_{i=1}^n K(\mathbf{x}_i, \mathbf{y}) \cdot (\mathbf{x}_i - \mathbf{y}) - \frac{1}{m}\sum_{j=1}^m K(\mathbf{y}_j^{(t)}, \mathbf{y}) \cdot (\mathbf{y}_j^{(t)} - \mathbf{y})$$

We update the generator parameters by encouraging generated samples to move in the direction of this velocity field:

$$\mathcal{L}_t(\theta) = \frac{1}{m} \sum_{j=1}^m \left\| \frac{\partial G_\theta(\mathbf{z}_j)}{\partial \theta} - \hat{\mathbf{v}}_t(G_\theta(\mathbf{z}_j)) \right\|^2$$

The optimization proceeds via gradient descent:
$$\theta^{(t+1)} = \theta^{(t)} - \eta \nabla_\theta \mathcal{L}_t(\theta^{(t)})$$

## 2.5 Technical Assumptions

We require the following technical assumptions:

**A1 (Regularity):** The generator $G_\theta$ is twice continuously differentiable with respect to both $\theta$ and its input, and the parameter space $\Theta$ is compact.

**A2 (Kernel Properties):** The kernel $K(\mathbf{x}, \mathbf{y})$ is positive definite, bounded, and Lipschitz continuous. Common choices include the RBF kernel $K(\mathbf{x}, \mathbf{y}) = \exp(-\|\mathbf{x} - \mathbf{y}\|^2/(2\sigma^2))$.

**A3 (Sample Complexity):** We assume access to sufficiently many samples such that $n, m = \Omega(\text{poly}(d))$ where $d$ is the ambient dimension, ensuring good approximation of the true velocity field.

**A4 (Expressivity):** The generator family $\{G_\theta\}$ has sufficient capacity to represent the optimal transport map from $p_{\text{noise}}$ to $p_{\text{data}}$.

These assumptions ensure that: (A1) the optimization landscape is well-behaved; (A2) the velocity field provides meaningful directional information for distribution alignment; (A3) empirical estimates concentrate around their population counterparts; and (A4) the optimal solution exists within our model class.

## 2.6 Relationship to Prior Work

Our formulation addresses key limitations of existing generative modeling approaches. Unlike iterative methods such as diffusion models that require multiple denoising steps at inference time, our approach produces samples in a single forward pass once training converges. Unlike GANs, we avoid adversarial optimization by directly optimizing for distributional alignment through physically-motivated flow dynamics.

The velocity field formulation draws inspiration from optimal transport theory and kernel methods for distribution matching, but uniquely leverages the iterative nature of neural network training to progressively evolve a single-step generator. The equilibrium condition provides a clear convergence criterion, addressing the common challenge of determining when generative model training should terminate.

Our approach can be viewed as learning an amortized solution to the optimal transport problem, where instead of computing transport maps for each new noise sample, we learn a single neural network that approximates the optimal map across the entire noise distribution.