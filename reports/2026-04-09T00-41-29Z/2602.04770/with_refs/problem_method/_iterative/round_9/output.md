# Problem Formulation

## Notation and Problem Setup

Let $\mathcal{X} \subseteq \mathbb{R}^d$ denote the data space and let $P_{\text{data}}$ be an unknown target distribution over $\mathcal{X}$. Let $P_{\text{prior}}$ be a known prior distribution (e.g., standard Gaussian) that is easy to sample from. We denote by $\mathcal{P}(\mathcal{X})$ the space of probability distributions over $\mathcal{X}$.

Consider a generator network $G_\theta: \mathcal{X} \to \mathcal{X}$ parameterized by $\theta \in \Theta$, where $\Theta$ is the parameter space. For any distribution $P$ and measurable function $G$, we denote the pushforward distribution by $G_\sharp P$, defined such that $(G_\sharp P)(A) = P(G^{-1}(A))$ for any measurable set $A$.

During training, we have access to samples $\{x_i\}_{i=1}^n \sim P_{\text{data}}$ from the target distribution. At each training iteration $t$, the current generator $G_{\theta^{(t)}}$ defines a pushforward $G_{\theta^{(t)}}\sharp P_{\text{prior}}$ of the prior distribution.

## The Sample-Level Vector Field

We introduce a vector field $v_\phi: \mathcal{X} \times \mathcal{X} \to \mathcal{X}$ parameterized by $\phi \in \Phi$, which takes as input a sample $x$ and a "context" sample $y$, and outputs a direction vector indicating how $x$ should move. The key insight is that this field should satisfy an anti-symmetry property:

$$v_\phi(x, y) = -v_\phi(y, x) \quad \forall x, y \in \mathcal{X}$$

This anti-symmetry ensures that $v_\phi(x, x) = 0$, meaning samples require no correction when compared to themselves.

## Training Objective

At each training step, we sample batches $\{x_i\}_{i=1}^m \sim P_{\text{data}}$ and $\{z_j\}_{j=1}^m \sim P_{\text{prior}}$, then generate $\{g_j\}_{j=1}^m$ where $g_j = G_{\theta}(z_j)$. The core training principle is to enforce the fixed-point condition:

$$G_{\theta}(z) = G_{\theta}(z) + \frac{1}{m}\sum_{i=1}^m v_\phi(G_{\theta}(z), x_i) \quad \forall z \sim P_{\text{prior}}$$

However, since $G_{\theta}(z)$ appears on both sides, we use a stop-gradient operation $\text{sg}(\cdot)$ to prevent direct backpropagation through the field's first argument:

$$\mathcal{L}(\theta, \phi) = \mathbb{E}_{z \sim P_{\text{prior}}} \left[ \left\| G_{\theta}(z) - \left( \text{sg}(G_{\theta}(z)) + \frac{1}{m}\sum_{i=1}^m v_\phi(\text{sg}(G_{\theta}(z)), x_i) \right) \right\|^2 \right]$$

This formulation allows the generator to be optimized indirectly through the vector field's influence on the fixed-point equation.

## Formal Problem Statement

**Given:** 
- Samples $\{x_i\}_{i=1}^n \sim P_{\text{data}}$ from target distribution
- Prior distribution $P_{\text{prior}}$ 
- Generator architecture $G_\theta: \mathcal{X} \to \mathcal{X}$
- Vector field architecture $v_\phi: \mathcal{X} \times \mathcal{X} \to \mathcal{X}$

**Find:** Parameters $\theta^*, \phi^*$ such that $G_{\theta^*} \sharp P_{\text{prior}} \approx P_{\text{data}}$

**Guarantee:** The trained generator produces high-quality samples in a single forward pass while the vector field satisfies anti-symmetry and drives the generator toward the target distribution.

## Technical Assumptions

1. **Smoothness:** Both $G_\theta$ and $v_\phi$ are differentiable with respect to their parameters
2. **Anti-symmetry:** The vector field satisfies $v_\phi(x,y) = -v_\phi(y,x)$ by construction
3. **Bounded support:** The data distribution has bounded support or appropriate tail conditions
4. **Regularity:** The target distribution $P_{\text{data}}$ admits a density with respect to Lebesgue measure

# Methodology

## High-Level Approach

Our approach, which we term **Consistency Training**, leverages the iterative nature of the training process itself rather than requiring iterative inference. The key insight is to define a sample-level vector field that operates directly on generated samples, guiding them toward the target distribution through an anti-symmetric correction mechanism.

The method consists of three main components: (1) an anti-symmetric vector field that computes sample-level corrections, (2) a fixed-point training objective that enforces self-consistency, and (3) a stop-gradient mechanism that enables indirect optimization of the generator through the field's influence.

## Core Architecture

### Anti-Symmetric Vector Field Design

We implement the anti-symmetric property by constructing $v_\phi(x,y)$ as:

$$v_\phi(x,y) = f_\phi(x,y) - f_\phi(y,x)$$

where $f_\phi: \mathcal{X} \times \mathcal{X} \to \mathcal{X}$ is an arbitrary neural network. This construction automatically ensures anti-symmetry since:

$$v_\phi(y,x) = f_\phi(y,x) - f_\phi(x,y) = -[f_\phi(x,y) - f_\phi(y,x)] = -v_\phi(x,y)$$

### Generator Update Mechanism

The generator is updated to satisfy the consistency condition:

$$G_{\theta}(z) = G_{\theta}(z) + \mathbb{E}_{x \sim P_{\text{data}}}[v_\phi(G_{\theta}(z), x)]$$

In practice, we approximate the expectation using empirical samples and apply stop-gradients:

$$\mathcal{L}_{\text{consistency}}(\theta, \phi) = \mathbb{E}_{z \sim P_{\text{prior}}} \left[ \left\| G_{\theta}(z) - \text{sg}(G_{\theta}(z)) - \frac{1}{n}\sum_{i=1}^n v_\phi(\text{sg}(G_{\theta}(z)), x_i) \right\|^2 \right]$$

## Training Algorithm

```
Algorithm: Consistency Training

Input: Data samples {x_i}, prior P_prior, learning rates λ_θ, λ_φ
Initialize: Generator G_θ, vector field v_φ
For each training iteration t:
    1. Sample batch {z_j} ~ P_prior
    2. Sample batch {x_i} ~ P_data  
    3. Generate samples: g_j = G_θ(z_j)
    
    4. Compute vector field corrections:
       For each generated sample g_j:
           correction_j = (1/|batch|) * Σ_i v_φ(g_j, x_i)
    
    5. Compute consistency loss:
       L_consistency = Σ_j ||G_θ(z_j) - sg(g_j) - correction_j||²
    
    6. Update parameters:
       θ ← θ - λ_θ * ∇_θ L_consistency  
       φ ← φ - λ_φ * ∇_φ L_consistency
    
    7. Optional: Apply exponential moving average to θ
End For
```

## Key Design Decisions

### Stop-Gradient Justification
The stop-gradient operation in step 5 is crucial because it prevents the generator from trivially satisfying the consistency condition by making $G_\theta(z) = 0$. By treating $\text{sg}(G_\theta(z))$ as a constant during backpropagation, we force the generator to move toward the target distribution indirectly through the vector field's guidance.

### Anti-Symmetry Benefits  
The anti-symmetric property ensures that when generated samples are close to real data samples, the correction field naturally diminishes. This creates a stable equilibrium where well-generated samples receive minimal correction, while poorly generated samples receive strong directional guidance toward the data distribution.

### Single-Step Generation
Unlike diffusion models or iterative refinement methods, our approach produces high-quality samples in a single forward pass through $G_\theta$. The iterative refinement is embedded in the training process rather than the inference process.

## Theoretical Properties

### Convergence Analysis
Under mild regularity conditions, the consistency training objective has a unique fixed point when the generator distribution matches the target distribution. The anti-symmetric field ensures that $v_\phi(x,x) = 0$, creating natural stability around the target distribution.

### Computational Complexity
- **Training:** $O(mn)$ per iteration, where $m$ is the generated batch size and $n$ is the data batch size
- **Inference:** $O(1)$ - single forward pass through the generator
- **Memory:** $O(m + n)$ for storing batches during training

The method scales favorably compared to iterative sampling approaches, which require $O(T)$ network evaluations for $T$ sampling steps.

## Extensions and Variants

### Conditional Generation
For conditional generation tasks, we extend the vector field to $v_\phi(x, y, c)$ where $c$ represents conditioning information. The anti-symmetry property becomes $v_\phi(x, y, c) = -v_\phi(y, x, c)$.

### Multi-Scale Training
We can apply consistency training at multiple resolutions simultaneously, with vector fields operating at different scales to capture both global structure and fine details.

This methodology directly addresses the problem formulation by providing a principled way to train generative models that produce high-quality samples in a single forward pass, while leveraging the anti-symmetric vector field to ensure stable and efficient training dynamics.