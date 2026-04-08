# Problem Formulation

## Notation and Setup

Let $\mathcal{X} \subseteq \mathbb{R}^d$ denote the data space and $p_{\text{data}}$ denote the unknown target data distribution over $\mathcal{X}$. Let $p_{\text{noise}}$ denote a simple noise distribution (e.g., standard Gaussian) from which we can easily sample. We consider a generator network $G_\theta: \mathcal{X} \to \mathcal{X}$ parameterized by $\theta \in \Theta$, where $\Theta$ is the parameter space.

During training at iteration $t$, the generator induces a distribution $p_t = G_{\theta_t} \# p_{\text{noise}}$ (the pushforward of $p_{\text{noise}}$ through $G_{\theta_t}$). Let $\{x_i\}_{i=1}^n \sim p_{\text{data}}$ denote real data samples and $\{z_j\}_{j=1}^m \sim p_{\text{noise}}$ denote noise samples. The generated samples at iteration $t$ are $\{\tilde{x}_j^{(t)}\}_{j=1}^m$ where $\tilde{x}_j^{(t)} = G_{\theta_t}(z_j)$.

For any two finite sets of samples $A = \{a_i\}$ and $B = \{b_j\}$, we define the **spatial interaction** between them as the collection of pairwise distances $\mathcal{D}(A, B) = \{\|a_i - b_j\|_2 : a_i \in A, b_j \in B\}$.

## Problem Statement

**Given:** 
- Real data samples $\{x_i\}_{i=1}^n \sim p_{\text{data}}$
- A generator architecture $G_\theta: \mathcal{X} \to \mathcal{X}$
- Access to noise samples $\{z_j\}_{j=1}^m \sim p_{\text{noise}}$

**Find:** Parameters $\theta^*$ such that the generator produces high-quality samples in a single forward pass.

**Guarantee:** The final generator $G_{\theta^*}$ should satisfy:
1. **Distribution matching:** $G_{\theta^*} \# p_{\text{noise}} \approx p_{\text{data}}$
2. **Single-step generation:** No iterative refinement required at inference
3. **Spatial equilibrium:** Generated samples are optimally positioned relative to real data

## Objective Formulation

We formulate the training process as finding an equilibrium where the spatial arrangement of generated samples relative to real samples indicates optimal generation quality. Inspired by the weighted exchangeability concepts in conformal prediction, we define a **spatial equilibrium condition**.

Let $\mathcal{S}_t = \{x_1, \ldots, x_n, \tilde{x}_1^{(t)}, \ldots, \tilde{x}_m^{(t)}\}$ denote the combined set of real and generated samples at iteration $t$. For each generated sample $\tilde{x}_j^{(t)}$, we compute its **conformity score**:

$$V_j^{(t)} = \text{Rank}\left(\|\tilde{x}_j^{(t)} - \text{NN}(\tilde{x}_j^{(t)}, \{x_i\}_{i=1}^n)\|_2 \text{ within } \mathcal{D}(\mathcal{S}_t, \{x_i\}_{i=1}^n)\right)$$

where $\text{NN}(\tilde{x}_j^{(t)}, \{x_i\}_{i=1}^n)$ denotes the nearest neighbor of $\tilde{x}_j^{(t)}$ among the real samples.

The **spatial equilibrium objective** is:

$$\mathcal{L}(\theta) = \mathbb{E}_{z \sim p_{\text{noise}}} \left[ \ell\left(\text{Quantile}\left(\frac{V^{(t)}}{n+m}, \mathcal{U}[0,1]\right)\right) \right]$$

where $V^{(t)}$ is the conformity score of $G_\theta(z)$, $\mathcal{U}[0,1]$ is the uniform distribution, and $\ell(\cdot)$ is a loss function that penalizes deviations from uniform conformity (e.g., $\ell(u) = (u - 0.5)^2$).

## Technical Assumptions

1. **Lipschitz Generator:** $G_\theta$ is $L$-Lipschitz continuous for all $\theta \in \Theta$
2. **Compact Support:** Both $p_{\text{data}}$ and $p_{\text{noise}}$ have compact support
3. **Differentiable Architecture:** $G_\theta$ is differentiable with respect to $\theta$
4. **Non-degeneracy:** The noise distribution $p_{\text{noise}}$ has full support on its domain
5. **Sufficient Capacity:** The generator family $\{G_\theta\}_{\theta \in \Theta}$ can approximate the optimal transport map from $p_{\text{noise}}$ to $p_{\text{data}}$

These assumptions ensure that: (i) the generator can learn meaningful mappings, (ii) the spatial relationships are well-defined and stable, and (iii) the conformity scores provide meaningful signals about distribution matching quality.

# Methodology

## High-Level Approach

Our method, **Spatial Equilibrium Generation (SEG)**, leverages the insight that during training, the generator's output distribution naturally evolves from noise toward the data distribution. Rather than requiring iterative refinement at inference time, we formalize this evolution process and define an equilibrium condition based on how generated samples spatially conform to real data samples.

The key idea is that when the generator reaches optimal quality, generated samples should be spatially distributed among real samples in a way that mimics the spatial relationships within the real data itself. We measure this through conformity scores inspired by conformal prediction, but adapted for generative modeling.

## Core Algorithm

### Spatial Conformity Score Computation

For a generated sample $\tilde{x} = G_\theta(z)$, we compute its conformity to the real data distribution by measuring how typical its spatial position is relative to real samples:

$$V(\tilde{x}) = \frac{1}{n} \sum_{i=1}^n \mathbf{1}\left[\|\tilde{x} - x_i\|_2 \leq \|\tilde{x} - \text{NN}(\tilde{x}, \{x_k\}_{k=1}^n)\|_2\right]$$

This score measures the fraction of real samples that are closer to $\tilde{x}$ than its nearest real neighbor, providing a measure of local density conformity.

### Equilibrium Loss Function

The generator should produce samples whose conformity scores are uniformly distributed, indicating that generated samples occupy the data space with the same density profile as real samples. Our loss function is:

$$\mathcal{L}_{\text{SEG}}(\theta) = \mathbb{E}_{z \sim p_{\text{noise}}} \left[ D_{\text{KL}}\left(\text{Uniform}[0,1] \,\|\, \delta_{V(G_\theta(z))}\right) \right]$$

where $\delta_v$ is a point mass at $v$. In practice, we approximate this using the empirical distribution of conformity scores over a batch.

### Training Algorithm

```
Algorithm 1: Spatial Equilibrium Generation (SEG)

Input: Real data {x_i}_{i=1}^n, generator G_θ, learning rate η, batch size m
Output: Trained generator parameters θ*

1. Initialize θ randomly
2. For t = 1, 2, ..., T:
   a. Sample noise batch: {z_j}_{j=1}^m ~ p_noise
   b. Generate samples: {x̃_j}_{j=1}^m where x̃_j = G_θ(z_j)
   
   c. Compute conformity scores:
      For j = 1, ..., m:
         V_j = (1/n) * Σ_{i=1}^n 1[||x̃_j - x_i||_2 ≤ ||x̃_j - NN(x̃_j, {x_i})||_2]
   
   d. Compute empirical CDF of conformity scores:
      F_emp(v) = (1/m) * Σ_{j=1}^m 1[V_j ≤ v]
   
   e. Compute equilibrium loss:
      L = Σ_{j=1}^m [F_emp(V_j) - V_j]^2  // Deviation from uniform CDF
   
   f. Update parameters: θ ← θ - η * ∇_θ L
   
3. Return θ*
```

## Design Justifications

**Spatial Conformity Design:** Our conformity score is inspired by the rank-based statistics in conformal prediction (Reference), but adapted for the generative setting. Unlike conformal prediction which uses conformity for uncertainty quantification, we use it to measure how well generated samples integrate spatially with real data.

**Equilibrium Condition:** The uniform distribution target for conformity scores ensures that generated samples are neither systematically too isolated (high conformity scores) nor too clustered (low conformity scores) relative to real data. This captures the intuition that a perfect generator should produce samples that are indistinguishable from real data in their spatial relationships.

**Single-Pass Generation:** By training the generator to directly produce spatially conforming samples, we eliminate the need for iterative refinement at inference time. The spatial equilibrium acts as a regularizer that encourages the generator to learn the full data distribution structure in one forward pass.

## Theoretical Properties

**Convergence:** Under the Lipschitz and compactness assumptions, the conformity scores are continuous functions of the generator parameters. The loss function is therefore well-defined and differentiable, ensuring gradient-based optimization can converge to local minima.

**Consistency:** As the number of real data samples $n \to \infty$, the empirical conformity scores converge to their population counterparts, ensuring that the equilibrium condition correctly identifies when the generated distribution matches the data distribution.

**Equilibrium Characterization:** At equilibrium, the generator satisfies:
$$\mathbb{E}_{z \sim p_{\text{noise}}}[V(G_{\theta^*}(z))] = 0.5$$
$$\text{Var}_{z \sim p_{\text{noise}}}[V(G_{\theta^*}(z))] = \frac{1}{12}$$

These are the mean and variance of the uniform distribution, providing a clear mathematical characterization of optimal generation quality.

## Computational Complexity

The conformity score computation requires $O(nm)$ distance calculations and $O(n)$ nearest neighbor searches per generated sample, leading to $O(nm \cdot n) = O(n^2m)$ complexity per training iteration. This can be optimized using efficient nearest neighbor data structures (e.g., KD-trees) to reduce the complexity to $O(nm \log n)$ per iteration.

The method scales favorably compared to adversarial approaches since it avoids the computational overhead of training multiple networks or performing iterative inference procedures.