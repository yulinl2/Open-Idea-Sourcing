# Problem Formulation

## Notation and Mathematical Framework

Let $\mathcal{X}$ denote the data space and $P_{\text{data}}$ denote the target data distribution supported on $\mathcal{X}$. We consider a generator network $G_\theta: \mathcal{Z} \to \mathcal{X}$ parameterized by $\theta$, where $\mathcal{Z}$ is a latent space with prior distribution $P_{\text{prior}}$ (typically standard Gaussian). The pushforward operation $G_\theta \sharp P_{\text{prior}}$ defines the generated distribution, where for any measurable set $A \subseteq \mathcal{X}$:
$$G_\theta \sharp P_{\text{prior}}(A) = P_{\text{prior}}(G_\theta^{-1}(A))$$

During training at iteration $t$, we denote the generator parameters as $\theta^{(t)}$ and the corresponding generated distribution as $P_g^{(t)} = G_{\theta^{(t)}} \sharp P_{\text{prior}}$. Let $\{x_i\}_{i=1}^n$ be samples from $P_{\text{data}}$ and $\{z_j\}_{j=1}^m$ be samples from $P_{\text{prior}}$, yielding generated samples $\{G_{\theta^{(t)}}(z_j)\}_{j=1}^m$.

## Problem Statement

**Given:** A target distribution $P_{\text{data}}$ known only through samples $\{x_i\}_{i=1}^n$, and a generator network $G_\theta$ initialized with parameters $\theta^{(0)}$.

**Find:** A training procedure that iteratively updates $\theta^{(t)} \to \theta^{(t+1)}$ such that:
1. The generated distribution $P_g^{(t)}$ converges to $P_{\text{data}}$ as $t \to \infty$
2. Each training iteration moves generated samples according to a principled dynamics that respects the underlying geometry of the data manifold
3. High-quality samples can be generated in a single forward pass after training

**Guarantee:** The training dynamics should exhibit an equilibrium property where sample movement ceases when $P_g^{(t)} = P_{\text{data}}$.

## Proposed Dynamics and Objective

We propose that generated samples should move according to a **particle dynamics** governed by interactions with both data samples and other generated samples. Specifically, for a generated sample $g = G_{\theta^{(t)}}(z)$, we define its movement direction as:

$$\Delta g = \sum_{i=1}^n w_{\text{data}}(g, x_i) \cdot (x_i - g) + \sum_{j \neq g} w_{\text{gen}}(g, g_j) \cdot (g_j - g)$$

where:
- $w_{\text{data}}(g, x_i)$ represents the attractive force from data sample $x_i$ to generated sample $g$
- $w_{\text{gen}}(g, g_j)$ represents the repulsive force between generated samples $g$ and $g_j$
- The weights depend on similarity/distance relationships in a learned feature space

The key insight is that these forces should satisfy a **symmetry property**: when $P_g^{(t)} = P_{\text{data}}$, the expected movement $\mathbb{E}_{g \sim P_g^{(t)}}[\Delta g] = 0$, ensuring equilibrium.

## Formal Optimization Objective

Let $\phi: \mathcal{X} \to \mathcal{H}$ be a feature extraction function mapping samples to a learned representation space $\mathcal{H}$. Define the weight functions:

$$w_{\text{data}}(g, x_i) = \frac{K(\phi(g), \phi(x_i))}{\sum_{k=1}^n K(\phi(g), \phi(x_k)) + \sum_{k=1}^m K(\phi(g), \phi(g_k))}$$

$$w_{\text{gen}}(g, g_j) = -\frac{K(\phi(g), \phi(g_j))}{\sum_{k=1}^n K(\phi(g), \phi(x_k)) + \sum_{k=1}^m K(\phi(g), \phi(g_k))}$$

where $K(\cdot, \cdot)$ is a similarity kernel (e.g., RBF kernel).

The training objective becomes:
$$\mathcal{L}(\theta^{(t)}) = \mathbb{E}_{z \sim P_{\text{prior}}} \left[ \left\| G_{\theta^{(t+1)}}(z) - \left( G_{\theta^{(t)}}(z) + \eta \cdot \Delta G_{\theta^{(t)}}(z) \right) \right\|^2 \right]$$

where $\eta$ is a step size parameter and $\Delta G_{\theta^{(t)}}(z)$ is the movement direction for the generated sample.

## Technical Assumptions

**A1 (Smoothness):** The generator $G_\theta$ is differentiable with respect to $\theta$ and Lipschitz continuous in both $\theta$ and $z$.

**A2 (Feature Space):** The feature extraction function $\phi$ provides a metric space where semantic similarity corresponds to proximity, and can be learned jointly with the generator.

**A3 (Kernel Properties):** The similarity kernel $K(\cdot, \cdot)$ is positive definite, symmetric, and provides meaningful distance relationships in the feature space.

**A4 (Sample Accessibility):** We have access to sufficient samples from both $P_{\text{data}}$ and the ability to generate samples from the current $P_g^{(t)}$.

**A5 (Equilibrium Condition):** The dynamics satisfy $\mathbb{E}_{g \sim P_{\text{data}}}[\Delta g] = 0$ when samples are drawn from the target distribution, ensuring convergence.

These assumptions are justified as follows: A1 enables gradient-based optimization; A2 allows meaningful similarity computations; A3 ensures the force field is well-defined; A4 is necessary for practical implementation; A5 guarantees theoretical convergence.

## Connection to Prior Work

Traditional generative models like GANs require adversarial training between generator and discriminator networks, which can suffer from training instability and mode collapse. Variational autoencoders impose restrictive distributional assumptions. Flow-based models require architectural constraints for invertibility.

Our formulation differs fundamentally by:
1. **Direct distribution evolution:** Rather than learning a fixed mapping, we evolve the generated distribution through iterative particle dynamics
2. **Equilibrium-based training:** The training process itself drives convergence through force balance, eliminating the need for adversarial objectives
3. **Single-pass generation:** Unlike iterative refinement methods (e.g., diffusion models), samples are generated in one forward pass after training

The proposed particle dynamics draws inspiration from mean-shift algorithms in computer vision, but operates in learned feature spaces and incorporates both attractive and repulsive forces. Unlike conformal prediction methods that focus on uncertainty quantification, our approach directly shapes the generated distribution to match the target through principled sample movement.

This formulation addresses the fundamental challenge of learning complex distribution mappings without requiring iterative inference, while providing theoretical guarantees for convergence through the equilibrium property of the underlying dynamics.