# Problem Formulation

## Notation and Setup

Let $\mathcal{X} \subseteq \mathbb{R}^d$ denote the data space and $p$ be a reference distribution on $\mathcal{X}$ (typically a simple distribution like standard Gaussian). Let $q$ denote the target data distribution we wish to model. We consider a generator network $f_\theta: \mathcal{X} \to \mathcal{X}$ parameterized by $\theta \in \Theta$, where $\Theta$ is the parameter space.

The **pushforward distribution** induced by the generator is defined as $f_{\theta\#}p$, where for any measurable set $A \subseteq \mathcal{X}$:
$$[f_{\theta\#}p](A) = p(f_\theta^{-1}(A))$$

During training, we observe i.i.d. samples $\{x_i\}_{i=1}^n \sim q$ from the target distribution and can generate samples $\{\epsilon_j\}_{j=1}^m \sim p$ from the reference distribution.

## Drift Field Formulation

The core innovation lies in defining a **drift field** $V_{p,q}: \mathcal{X} \to \mathcal{X}$ that governs how generated samples should move during training. For any point $x \in \mathcal{X}$, we define:

$$V_{p,q}(x) = \mathbb{E}_{x^+ \sim q}[\phi(x^+) \cdot w(x, x^+)] - \mathbb{E}_{x^- \sim f_{\theta\#}p}[\phi(x^-) \cdot w(x, x^-)]$$

where:
- $\phi: \mathcal{X} \to \mathcal{F}$ maps points to a feature space $\mathcal{F}$ (potentially using a pre-trained encoder)
- $w: \mathcal{X} \times \mathcal{X} \to \mathbb{R}_+$ is a kernel weighting function measuring similarity between points
- $x^+$ represents "positive" samples from the data distribution
- $x^-$ represents "negative" samples from the current generator distribution

The drift field exhibits the crucial **anti-symmetry property**:
$$V_{p,q}(x) = -V_{q,p}(x)$$

This ensures that when the distributions match ($f_{\theta\#}p = q$), the drift field vanishes: $V_{q,q}(x) = 0$ for all $x$.

## Problem Statement

**Given:** 
- Target data samples $\{x_i\}_{i=1}^n \sim q$
- Reference distribution $p$ with efficient sampling
- Feature mapping $\phi$ and kernel function $w$
- Desired coverage level $\alpha \in (0,1)$

**Find:** Parameters $\theta^*$ such that the generator $f_{\theta^*}$ produces high-quality samples in a single forward pass, where the pushforward distribution $f_{\theta^*\#}p$ closely approximates $q$.

**Constraint:** The training process should evolve the pushforward distribution $f_{\theta\#}p$ progressively through iterations, eliminating the need for iterative refinement at inference time.

## Optimization Objective

We minimize the **drift minimization loss**:
$$\mathcal{L}(\theta) = \mathbb{E}_{\epsilon \sim p}\left[\left\|f_\theta(\epsilon) - \text{stopgrad}(f_\theta(\epsilon) + V_{p,q}(f_\theta(\epsilon)))\right\|^2\right]$$

where $\text{stopgrad}(\cdot)$ prevents gradients from flowing through the drift target, ensuring training stability.

In practice, this is approximated using empirical samples:
$$\hat{\mathcal{L}}(\theta) = \frac{1}{m}\sum_{j=1}^m \left\|f_\theta(\epsilon_j) - \text{stopgrad}(f_\theta(\epsilon_j) + \hat{V}(f_\theta(\epsilon_j)))\right\|^2$$

where the empirical drift field is:
$$\hat{V}(x) = \frac{1}{n}\sum_{i=1}^n \phi(x_i) w(x, x_i) - \frac{1}{m}\sum_{k=1}^m \phi(f_\theta(\epsilon_k)) w(x, f_\theta(\epsilon_k))$$

## Technical Assumptions

**A1. Regularity:** The generator $f_\theta$ is differentiable in $\theta$, and the feature mapping $\phi$ is Lipschitz continuous.

**A2. Kernel Properties:** The kernel $w(x,y)$ is symmetric, non-negative, and integrable: $\int w(x,y) dy < \infty$ for all $x$.

**A3. Bounded Moments:** $\mathbb{E}_{x \sim q}[\|\phi(x)\|^2] < \infty$ and $\mathbb{E}_{\epsilon \sim p}[\|\phi(f_\theta(\epsilon))\|^2] < \infty$.

**A4. Sample Complexity:** We assume sufficient samples such that empirical drift field estimates concentrate around their expectations.

These assumptions ensure the drift field is well-defined and the optimization objective is tractable.

## Connection to Prior Work

Traditional generative models face a fundamental trade-off: **GANs** achieve single-pass generation but suffer from training instability and mode collapse; **diffusion models** produce high-quality samples but require expensive iterative sampling. **Flow models** learn invertible transformations but are architecturally constrained.

Our formulation addresses this gap by moving the iterative refinement from inference time to training time. Unlike diffusion models that perform $T$ denoising steps at inference, we perform the "denoising" through gradient-based training iterations. The anti-symmetric drift field provides a principled way to evolve the generator distribution during training, ensuring convergence to the target distribution while maintaining single-pass generation capability.

The conformal prediction literature (e.g., Tibshirani et al., 2020) provides techniques for distribution-free inference under covariate shift, which relates to our challenge of matching distributions. However, our focus is on generative modeling rather than predictive inference, requiring a fundamentally different mathematical framework centered on pushforward distributions and drift dynamics.