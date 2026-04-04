# Reconstruction: problem
**Paper:** 2602.04770  
**Condition:** with_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Problem Formulation

## Notation and Problem Setup

Let $\mathcal{X}$ denote the data space (e.g., $\mathcal{X} = \mathbb{R}^d$ for images or $\mathcal{X} = \mathbb{R}^n$ for sequences), and let $\mathcal{Z}$ represent a simple prior space, typically $\mathcal{Z} = \mathbb{R}^k$ with $k \ll \dim(\mathcal{X})$. We consider probability measures $p_{\text{data}}$ on $\mathcal{X}$ representing the true data distribution and $p_{\text{prior}}$ on $\mathcal{Z}$ representing a tractable prior distribution (commonly $\mathcal{N}(0, I_k)$).

The fundamental challenge in generative modeling is to learn a mapping that transforms samples from the simple prior distribution to samples from the complex data distribution. Formally, we seek to construct a deterministic function $G_\theta: \mathcal{Z} \to \mathcal{X}$ parameterized by $\theta \in \Theta$, where $\Theta$ is the parameter space, such that for $z \sim p_{\text{prior}}$, the pushforward measure $(G_\theta)_\# p_{\text{prior}}$ closely approximates $p_{\text{data}}$.

Let $\mathcal{D} = \{x_i\}_{i=1}^n$ denote a dataset of $n$ independent samples from $p_{\text{data}}$. For conditional generation tasks, we extend the notation to include conditioning variables $c \in \mathcal{C}$ from a conditioning space, and seek $G_\theta: \mathcal{Z} \times \mathcal{C} \to \mathcal{X}$ such that $(G_\theta(\cdot, c))_\# p_{\text{prior}}$ approximates the conditional distribution $p_{\text{data}}(\cdot | c)$.

## Formal Problem Statement

**Given:** A dataset $\mathcal{D} = \{x_i\}_{i=1}^n$ where $x_i \stackrel{\text{i.i.d.}}{\sim} p_{\text{data}}$, a prior distribution $p_{\text{prior}}$ on $\mathcal{Z}$, and a family of functions $\mathcal{G} = \{G_\theta : \mathcal{Z} \to \mathcal{X} \mid \theta \in \Theta\}$.

**Find:** Parameters $\theta^* \in \Theta$ such that the generator $G_{\theta^*}$ satisfies:

1. **Single-pass generation:** For any $z \sim p_{\text{prior}}$, $G_{\theta^*}(z)$ produces a high-quality sample in one forward evaluation without iterative refinement.

2. **Distribution matching:** The pushforward measure $(G_{\theta^*})_\# p_{\text{prior}}$ closely approximates $p_{\text{data}}$ in an appropriate metric $d(\cdot, \cdot)$:
   $$d\left((G_{\theta^*})_\# p_{\text{prior}}, p_{\text{data}}\right) \leq \epsilon$$
   for some small $\epsilon > 0$.

3. **Computational efficiency:** The inference cost $\mathcal{C}_{\text{inf}}(G_{\theta^*})$ is significantly lower than iterative methods, i.e., $\mathcal{C}_{\text{inf}}(G_{\theta^*}) = O(1)$ rather than $O(T)$ for $T$-step iterative procedures.

## Optimization Objective

The core challenge is that direct optimization of distribution matching objectives is intractable. We propose to address this through a training-time complexity transfer paradigm. Instead of minimizing the intractable objective
$$\min_\theta \, d\left((G_\theta)_\# p_{\text{prior}}, p_{\text{data}}\right),$$
we seek a surrogate objective $\mathcal{L}(\theta; \mathcal{D})$ that:

1. **Enables tractable optimization:** $\mathcal{L}(\theta; \mathcal{D})$ can be efficiently computed and optimized using standard techniques.

2. **Transfers complexity to training:** The objective may involve computationally intensive procedures during training, but these do not affect inference cost.

3. **Provides distribution matching guarantees:** Minimizers of $\mathcal{L}(\theta; \mathcal{D})$ yield generators whose pushforward measures approximate $p_{\text{data}}$.

Formally, we require:
$$\mathcal{L}(\theta^*; \mathcal{D}) = \min_\theta \mathcal{L}(\theta; \mathcal{D}) \implies d\left((G_{\theta^*})_\# p_{\text{prior}}, p_{\text{data}}\right) \leq \epsilon(\mathcal{L}(\theta^*; \mathcal{D}))$$
where $\epsilon(\cdot)$ is a monotonically increasing function with $\lim_{L \to 0} \epsilon(L) = 0$.

## Technical Assumptions

We make the following assumptions to ensure theoretical tractability and practical applicability:

**A1. Smoothness:** The generator $G_\theta$ is differentiable with respect to both $z$ and $\theta$, enabling gradient-based optimization and ensuring continuity of the learned mapping.

**A2. Universal approximation:** The function class $\mathcal{G}$ has sufficient capacity to approximate the optimal transport map from $p_{\text{prior}}$ to $p_{\text{data}}$. This is typically satisfied by deep neural networks with appropriate depth and width.

**A3. Data regularity:** The data distribution $p_{\text{data}}$ has finite moments up to some order and satisfies appropriate concentration properties. This ensures stable learning and generalization.

**A4. Prior compatibility:** The prior $p_{\text{prior}}$ has full support on $\mathcal{Z}$ and admits efficient sampling. The standard choice $p_{\text{prior}} = \mathcal{N}(0, I_k)$ satisfies this requirement.

**A5. Computational tractability:** The surrogate objective $\mathcal{L}(\theta; \mathcal{D})$ and its gradients can be computed efficiently, enabling practical optimization with modern hardware and software frameworks.

These assumptions are standard in the generative modeling literature and are satisfied by most practical scenarios of interest.

## Connection to Prior Work

Existing generative modeling approaches can be categorized by how they handle the distribution-to-distribution mapping challenge:

**Iterative refinement methods** such as diffusion models and autoregressive models decompose the complex mapping into a sequence of simpler transformations. While achieving high sample quality, they require $T$ sequential evaluations at inference time, yielding $O(T)$ computational cost. Our formulation seeks to achieve comparable quality with $O(1)$ inference cost.

**Single-step adversarial methods** like GANs attempt direct distribution matching through adversarial training. However, they suffer from training instability, mode collapse, and limited scalability. Our approach aims to achieve the computational efficiency of single-step generation while avoiding the optimization difficulties of adversarial training.

**Likelihood-based methods** such as VAEs and normalizing flows provide tractable training objectives but often produce lower-quality samples or require architectural constraints that limit expressiveness. Our formulation seeks to maintain training tractability while removing these limitations.

**Flow matching and optimal transport methods** learn continuous paths between distributions but typically require iterative numerical integration for sampling. Our approach aims to distill such continuous dynamics into a single-step generator.

The key gap our formulation addresses is the lack of a principled framework for achieving high-quality single-step generation without adversarial training or architectural constraints. By transferring computational complexity from inference to training time, we aim to combine the best aspects of existing approaches: the quality of iterative methods, the efficiency of single-step generation, and the stability of non-adversarial training.
