# Reconstruction: problem_method
**Paper:** 2602.04770  
**Condition:** with_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Problem Formulation

## 1.1 Notation and Setup

Let $\mathcal{X}$ denote the data space (e.g., $\mathcal{X} = \mathbb{R}^d$ for images or $\mathcal{X} = \mathbb{R}^n$ for sequences), and let $\mathcal{Z}$ represent a simple prior space, typically $\mathcal{Z} = \mathbb{R}^k$ with $k \ll \dim(\mathcal{X})$. We consider probability distributions $P_{\mathcal{X}}$ over the data space and $P_{\mathcal{Z}}$ over the prior space, where $P_{\mathcal{Z}}$ is typically a simple distribution such as $\mathcal{N}(0, I_k)$.

Let $\{(x_i)\}_{i=1}^n$ denote i.i.d. samples from the unknown data distribution $P_{\mathcal{X}}$. We seek to learn a generative mapping $G_\theta: \mathcal{Z} \to \mathcal{X}$ parameterized by $\theta \in \Theta$, such that for $z \sim P_{\mathcal{Z}}$, the generated samples $G_\theta(z)$ approximate the target distribution $P_{\mathcal{X}}$.

## 1.2 Problem Statement

**Given:** 
- Training dataset $\mathcal{D} = \{x_i\}_{i=1}^n$ where $x_i \sim P_{\mathcal{X}}$
- Prior distribution $P_{\mathcal{Z}}$ over latent space $\mathcal{Z}$
- Target coverage level $1-\alpha \in (0,1)$

**Find:** A generator function $G_\theta: \mathcal{Z} \to \mathcal{X}$ that enables single-pass generation.

**Guarantee:** The pushforward distribution $(G_\theta)_\# P_{\mathcal{Z}}$ should approximate $P_{\mathcal{X}}$ such that:
$$\mathbb{P}_{z \sim P_{\mathcal{Z}}}[G_\theta(z) \text{ is indistinguishable from } P_{\mathcal{X}}] \geq 1-\alpha$$

## 1.3 Objective Formulation

The core challenge lies in defining an appropriate training objective that enables direct distribution matching without iterative refinement. Drawing inspiration from the conformal prediction framework, we formulate this as a distribution-free coverage problem.

Let $S: \mathcal{X} \times \mathcal{D} \to \mathbb{R}_+$ be a conformity score function that measures how well a sample $x$ conforms to the training distribution represented by dataset $\mathcal{D}$. For example:
$$S(x, \mathcal{D}) = \min_{x_i \in \mathcal{D}} \|x - x_i\|_2$$

Our objective is to learn $G_\theta$ such that generated samples achieve conformity scores that are statistically indistinguishable from those of real data samples. Specifically, we require:

$$\mathbb{P}_{z \sim P_{\mathcal{Z}}}[S(G_\theta(z), \mathcal{D}) \leq Q_{1-\alpha}(\{S(x_i, \mathcal{D}_{-i})\}_{i=1}^n)] \geq 1-\alpha$$

where $Q_{1-\alpha}$ denotes the $(1-\alpha)$-quantile and $\mathcal{D}_{-i} = \mathcal{D} \setminus \{x_i\}$.

## 1.4 Technical Assumptions

**Assumption 1 (Regularity):** The generator $G_\theta$ is continuously differentiable with respect to $\theta$, and the data distribution $P_{\mathcal{X}}$ has finite second moments.

**Assumption 2 (Conformity Score Properties):** The score function $S$ satisfies:
- **Permutation Invariance:** $S(x, \mathcal{D}) = S(x, \pi(\mathcal{D}))$ for any permutation $\pi$
- **Continuity:** $S$ is continuous in its first argument
- **Non-degeneracy:** $S(x, \mathcal{D}) = 0$ if and only if $x \in \mathcal{D}$

**Assumption 3 (Finite Sample Exchangeability):** For any fixed generator $G_\theta$, the augmented dataset $\mathcal{D} \cup \{G_\theta(z)\}$ maintains the exchangeability property required for conformal prediction validity.

These assumptions ensure that our approach inherits the finite-sample guarantees of conformal prediction while enabling end-to-end learning of the generator.

# Methodology

## 2.1 Conformal Generative Modeling Framework

Our approach, termed **Conformal Generative Modeling (CGM)**, directly optimizes the generator to produce samples that satisfy conformal prediction criteria. Unlike traditional generative models that rely on distributional divergences, CGM leverages the finite-sample guarantees of conformal prediction to ensure generated samples are statistically indistinguishable from real data.

The key insight is to reformulate generative modeling as a conformal coverage optimization problem. Instead of minimizing a divergence between distributions, we train the generator to maximize the probability that generated samples achieve conformity scores within the acceptable range defined by the training data.

## 2.2 Core Algorithm

### 2.2.1 Conformity-Aware Loss Function

We define the conformity-aware loss function:
$$\mathcal{L}_{\text{conf}}(\theta) = \mathbb{E}_{z \sim P_{\mathcal{Z}}} \left[ \ell\left(S(G_\theta(z), \mathcal{D}), Q_{1-\alpha}(\{S(x_i, \mathcal{D}_{-i})\}_{i=1}^n)\right) \right]$$

where $\ell(s, t)$ is a loss function that penalizes conformity scores $s$ that exceed the threshold $t$. We use:
$$\ell(s, t) = \max(0, s - t)^2 + \lambda \cdot \mathbf{1}[s > t]$$

The first term provides a smooth gradient signal, while the second term (with indicator function $\mathbf{1}[\cdot]$) enforces the hard constraint.

### 2.2.2 Weighted Conformal Training

To handle potential distribution shift between generated and real samples, we employ a weighted conformal approach inspired by the covariate shift methodology. We define importance weights:
$$w(x) = \frac{p_{\text{real}}(x)}{p_{\text{gen}}(x)} \approx \frac{\exp(-S(x, \mathcal{D}))}{\mathbb{E}_{z}[\exp(-S(G_\theta(z), \mathcal{D}))]}$$

The weighted conformity threshold becomes:
$$Q^w_{1-\alpha} = \text{Quantile}\left(1-\alpha; \sum_{i=1}^n \tilde{w}_i \delta_{S(x_i, \mathcal{D}_{-i})} + \tilde{w}_{n+1} \delta_{\infty}\right)$$

where $\tilde{w}_i = w(x_i) / \sum_{j=1}^{n+1} w(x_j)$ are normalized weights.

### 2.2.3 Training Algorithm

```
Algorithm: Conformal Generative Model Training

Input: Dataset D = {x_i}_{i=1}^n, coverage level α, batch size B
Output: Generator G_θ

1. Initialize generator parameters θ
2. For epoch = 1 to max_epochs:
   a. Compute conformity scores for training data:
      For i = 1 to n:
         s_i = S(x_i, D_{-i})
   
   b. Compute conformity threshold:
      Q = Quantile(1-α, {s_i}_{i=1}^n ∪ {∞})
   
   c. Sample batch of latents: {z_j}_{j=1}^B ~ P_Z
   
   d. Generate samples: {x̂_j = G_θ(z_j)}_{j=1}^B
   
   e. Compute conformity scores for generated samples:
      For j = 1 to B:
         ŝ_j = S(x̂_j, D)
   
   f. Compute loss:
      L = (1/B) Σ_{j=1}^B max(0, ŝ_j - Q)²
   
   g. Update parameters: θ ← θ - η ∇_θ L
   
   h. Update importance weights (optional):
      w_i ← exp(-S(x_i, D)) for i = 1,...,n
      w_gen ← (1/B) Σ_{j=1}^B exp(-S(x̂_j, D))
      Recompute Q with weighted quantile
```

## 2.3 Theoretical Properties

**Theorem (Conformal Coverage Guarantee):** Under Assumptions 1-3, the trained generator $G_{\theta^*}$ satisfies:
$$\mathbb{P}_{z \sim P_{\mathcal{Z}}}[S(G_{\theta^*}(z), \mathcal{D}) \leq Q_{1-\alpha}] \geq 1-\alpha$$

with probability at least $1-\delta$ over the training data, where $\delta$ depends on the optimization convergence rate.

**Proof Sketch:** The result follows from the finite-sample validity of conformal prediction (Theorem 1 in the reference) combined with the exchangeability maintained by our training procedure. The weighted extension (Corollary 1) handles potential distribution shift between generated and real samples.

## 2.4 Computational Complexity

The computational complexity per training iteration is $O(n^2 + nB)$, where the $O(n^2)$ term comes from computing leave-one-out conformity scores and the $O(nB)$ term from evaluating generated samples against the training set. This is comparable to other single-pass generative models and significantly more efficient than iterative methods that require $O(TB)$ for $T$ refinement steps.

The conformity score computation can be accelerated using approximate nearest neighbor methods, reducing the complexity to $O(n \log n + nB)$ in practice.

## 2.5 Design Justifications

**Choice of Conformity Score:** We use distance-based scores as they provide intuitive geometric interpretation and satisfy the required properties. Alternative scores based on density estimation or learned representations are also compatible with our framework.

**Weighted Extension:** The importance weighting mechanism addresses the chicken-and-egg problem where generated samples may initially have different statistics than real data, ensuring stable training dynamics.

**Direct Optimization:** Unlike adversarial approaches, our method avoids the instabilities associated with minimax optimization by directly optimizing a well-defined, single-objective loss function with theoretical guarantees.
