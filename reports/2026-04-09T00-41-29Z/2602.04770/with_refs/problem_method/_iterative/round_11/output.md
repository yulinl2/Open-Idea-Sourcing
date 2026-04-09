# Section 1: Problem Formulation

## 1.1 Notation and Setup

Let $\mathcal{X} \subset \mathbb{R}^d$ denote the data space and $p_{\text{data}}$ the unknown target data distribution over $\mathcal{X}$. Let $p_{\text{prior}}$ be a fixed prior distribution (e.g., standard Gaussian) from which we can efficiently sample. We seek to learn a generator $G_\theta: \mathcal{X} \to \mathcal{X}$ parameterized by $\theta \in \Theta$ that transforms samples from $p_{\text{prior}}$ to approximate samples from $p_{\text{data}}$.

For any measurable function $f: \mathcal{X} \to \mathcal{X}$, define the **pushforward operation** $f_\# p$ of distribution $p$ by $f$ as:
$$[f_\# p](A) = p(f^{-1}(A))$$
for any measurable set $A \subseteq \mathcal{X}$. The generator $G_\theta$ induces the pushforward distribution $(G_\theta)_\# p_{\text{prior}}$ over the data space.

## 1.2 Sample-Level Vector Field

Central to our approach is a **sample-level vector field** $V_\phi: \mathcal{X} \times \mathcal{X} \to \mathcal{X}$ parameterized by $\phi \in \Phi$, which takes two samples as input and outputs a direction vector. This field governs how individual samples should move to better align two distributions.

**Definition 1 (Anti-symmetric Vector Field):** A vector field $V_\phi$ is anti-symmetric if for all $x, y \in \mathcal{X}$:
$$V_\phi(x, y) = -V_\phi(y, x)$$

This anti-symmetry ensures that $V_\phi(x, x) = 0$ and that swapping the roles of two distributions reverses the field direction.

## 1.3 Weighted Field Aggregation

For a given sample $x$ and a collection of samples $\{x_1, \ldots, x_n\}$, we define the **aggregated field** as:
$$\mathcal{V}_\phi(x; \{x_i\}_{i=1}^n) = \sum_{i=1}^n w(x, x_i) V_\phi(x, x_i)$$
where $w: \mathcal{X} \times \mathcal{X} \to \mathbb{R}_+$ is a similarity weighting function (e.g., $w(x, y) = \exp(-\|x - y\|^2/2\sigma^2)$ for some bandwidth $\sigma > 0$).

## 1.4 Problem Statement

**Given:** 
- Training samples $\{x_i\}_{i=1}^n \sim p_{\text{data}}$ from the target distribution
- Prior distribution $p_{\text{prior}}$ from which we can sample
- Anti-symmetric vector field $V_\phi$
- Similarity weighting function $w$

**Find:** Parameters $(\theta, \phi)$ such that the generator $G_\theta$ produces high-quality samples in a single forward pass.

**Objective:** We formulate training as a fixed-point problem where the generator output should equal itself plus a correction from the vector field:
$$G_\theta(z) = G_\theta(z) + \mathcal{V}_\phi(G_\theta(z); \{x_i\}_{i=1}^n)$$

This leads to the consistency condition:
$$\mathcal{V}_\phi(G_\theta(z); \{x_i\}_{i=1}^n) = 0$$

## 1.5 Technical Assumptions

**Assumption 1:** The vector field $V_\phi$ is Lipschitz continuous in both arguments with constant $L_V$.

**Assumption 2:** The similarity weighting function $w$ is bounded: $0 \leq w(x, y) \leq W_{\max}$ for all $x, y \in \mathcal{X}$.

**Assumption 3:** The generator $G_\theta$ is differentiable with respect to $\theta$ and Lipschitz continuous with constant $L_G$.

**Assumption 4:** The training data $\{x_i\}_{i=1}^n$ are i.i.d. samples from $p_{\text{data}}$.

These assumptions ensure well-posedness of the optimization problem and enable theoretical analysis of convergence properties.

# Section 2: Methodology

## 2.1 Core Algorithm: Flow Matching with Vector Fields

Our approach, termed **Vector Field Flow Matching**, trains a generator to produce samples that satisfy a consistency condition with respect to an anti-symmetric vector field. The key insight is to use stop-gradient operations to prevent direct backpropagation through the field while still optimizing its effect.

### 2.1.1 Training Objective

For each training iteration, we sample a batch of prior samples $\{z_j\}_{j=1}^m \sim p_{\text{prior}}$ and compute generated samples $\{G_\theta(z_j)\}_{j=1}^m$. The training loss combines two terms:

$$\mathcal{L}(\theta, \phi) = \mathcal{L}_{\text{consistency}}(\theta, \phi) + \lambda \mathcal{L}_{\text{field}}(\phi)$$

**Consistency Loss:** This enforces that generated samples should be fixed points of the field-corrected transformation:
$$\mathcal{L}_{\text{consistency}}(\theta, \phi) = \frac{1}{m} \sum_{j=1}^m \left\| G_\theta(z_j) - \text{sg}[G_\theta(z_j) + \mathcal{V}_\phi(G_\theta(z_j); \{x_i\}_{i=1}^n)] \right\|^2$$

where $\text{sg}[\cdot]$ denotes the stop-gradient operation.

**Field Regularization Loss:** This encourages the field to provide meaningful corrections by minimizing the field magnitude on real data:
$$\mathcal{L}_{\text{field}}(\phi) = \frac{1}{n} \sum_{i=1}^n \left\| \mathcal{V}_\phi(x_i; \{x_j\}_{j \neq i}) \right\|^2$$

### 2.1.2 Detailed Algorithm

```
Algorithm 1: Vector Field Flow Matching

Input: Training data {x_i}_{i=1}^n, prior p_prior, batch size m, 
       learning rates η_θ, η_φ, regularization λ
Output: Trained generator G_θ

1. Initialize parameters θ, φ randomly
2. For epoch = 1 to max_epochs:
   a. Sample batch {z_j}_{j=1}^m ~ p_prior
   b. Generate samples: g_j = G_θ(z_j) for j = 1,...,m
   
   c. Compute aggregated fields:
      For j = 1 to m:
         v_j = Σ_{i=1}^n w(g_j, x_i) * V_φ(g_j, x_i)
   
   d. Compute consistency loss:
      L_cons = (1/m) * Σ_{j=1}^m ||g_j - sg[g_j + v_j]||²
   
   e. Compute field regularization:
      L_field = (1/n) * Σ_{i=1}^n ||Σ_{j≠i} w(x_i, x_j) * V_φ(x_i, x_j)||²
   
   f. Total loss: L = L_cons + λ * L_field
   
   g. Update parameters:
      θ ← θ - η_θ * ∇_θ L
      φ ← φ - η_φ * ∇_φ L

3. Return G_θ
```

## 2.2 Architectural Design

### 2.2.1 Generator Architecture
The generator $G_\theta$ can be implemented using any differentiable architecture (e.g., fully connected networks, convolutional networks, or transformers). For image generation, we employ a U-Net-like architecture with skip connections to preserve fine-grained information.

### 2.2.2 Vector Field Architecture
The anti-symmetric vector field $V_\phi(x, y)$ is implemented as:
$$V_\phi(x, y) = f_\phi(x, y) - f_\phi(y, x)$$
where $f_\phi$ is a neural network. This construction automatically ensures anti-symmetry. The network $f_\phi$ processes the concatenated input $[x; y]$ through several layers with residual connections.

### 2.2.3 Similarity Weighting
We use a learnable similarity function:
$$w(x, y) = \exp(-\|h_\psi(x) - h_\psi(y)\|^2 / 2\sigma^2)$$
where $h_\psi$ is a learned embedding network and $\sigma$ is a temperature parameter.

## 2.3 Theoretical Properties

**Proposition 1 (Consistency):** Under Assumptions 1-4, if the optimization converges to a global minimum of $\mathcal{L}(\theta, \phi)$, then $G_\theta(z)$ produces samples that satisfy the field consistency condition.

**Proposition 2 (Convergence):** The gradient descent updates have bounded variance, and under standard smoothness assumptions, the algorithm converges to a stationary point of the loss function.

**Proof Sketch:** The stop-gradient operation ensures that the consistency loss provides a well-defined gradient signal to the generator. The anti-symmetry of the vector field guarantees that the aggregated field has bounded magnitude, preventing instability during training.

## 2.4 Computational Complexity

**Training Complexity:** Each iteration requires $O(mn + n^2)$ operations for computing the vector field aggregations, where $m$ is the batch size and $n$ is the training set size. The generator and field network evaluations add $O(m \cdot C_G + mn \cdot C_V)$ where $C_G$ and $C_V$ are the computational costs of the respective networks.

**Inference Complexity:** Generation requires only a single forward pass through $G_\theta$, giving $O(C_G)$ complexity per sample, achieving the desired efficiency goal.

**Memory Complexity:** The method requires storing the entire training set for field computations, leading to $O(n \cdot d)$ memory overhead beyond standard neural network training.

## 2.5 Design Justifications

The stop-gradient operation in the consistency loss is crucial—it prevents the generator from trivially minimizing the loss by making $\mathcal{V}_\phi$ large and negative. Instead, it forces the generator to produce samples that are already close to their field-corrected versions.

The anti-symmetry property ensures that the field provides meaningful directional information rather than arbitrary corrections. When two distributions are identical, the field should provide no correction, which is guaranteed by the anti-symmetric property.

The weighted aggregation allows the field to focus on relevant samples, similar to kernel methods in classical machine learning, enabling better local adaptation of the generation process.