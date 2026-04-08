# Problem Formulation

## Notation and Setup

Let $\mathcal{X}$ and $\mathcal{Y}$ denote the input and output spaces, respectively. We consider probability distributions $P_X$ on $\mathcal{X}$ and $P_Y$ on $\mathcal{Y}$, where typically $\mathcal{X} = \mathbb{R}^d$ and $\mathcal{Y} = \mathbb{R}^k$ for some dimensions $d, k \geq 1$. Let $\mu$ denote a reference measure (e.g., Lebesgue measure) on both spaces.

We are interested in learning a mapping $T: \mathcal{X} \rightarrow \mathcal{Y}$ that transforms samples from a source distribution $P_X$ to match a target distribution $P_Y$. More precisely, if $X \sim P_X$, we want $T(X)$ to have distribution $P_Y$ (or approximately so).

Let $\mathcal{F} = \{f_\theta: \mathcal{X} \rightarrow \mathcal{Y} \mid \theta \in \Theta\}$ denote a parametric family of functions, where $\Theta \subseteq \mathbb{R}^p$ is the parameter space. We assume access to:
- Source samples: $\{x_i\}_{i=1}^n \stackrel{\text{i.i.d.}}{\sim} P_X$
- Target samples: $\{y_j\}_{j=1}^m \stackrel{\text{i.i.d.}}{\sim} P_Y$

## Problem Statement

**Given:** 
- Source distribution samples $\{x_i\}_{i=1}^n$ from $P_X$
- Target distribution samples $\{y_j\}_{j=1}^m$ from $P_Y$  
- Function class $\mathcal{F} = \{f_\theta\}$

**Find:** Parameters $\theta^* \in \Theta$ such that $f_{\theta^*}: \mathcal{X} \rightarrow \mathcal{Y}$ satisfies:
1. **Single-step generation:** For any $x \sim P_X$, compute $f_{\theta^*}(x)$ in one forward pass
2. **Distribution matching:** $f_{\theta^*}(X) \approx P_Y$ in distribution when $X \sim P_X$

**Guarantee:** The learned mapping $f_{\theta^*}$ should minimize the distributional discrepancy between the pushforward measure $(f_{\theta^*})_\# P_X$ and the target distribution $P_Y$.

## Objective Formulation

We formulate the learning objective as minimizing an optimal transport cost. Let $c: \mathcal{Y} \times \mathcal{Y} \rightarrow \mathbb{R}_+$ be a cost function (e.g., $c(y_1, y_2) = \|y_1 - y_2\|^2$). The optimal transport distance between the pushforward distribution $(f_\theta)_\# P_X$ and target distribution $P_Y$ is:

$$W_c((f_\theta)_\# P_X, P_Y) = \inf_{\gamma \in \Pi((f_\theta)_\# P_X, P_Y)} \int_{\mathcal{Y} \times \mathcal{Y}} c(y_1, y_2) \, d\gamma(y_1, y_2)$$

where $\Pi((f_\theta)_\# P_X, P_Y)$ denotes the set of all couplings between $(f_\theta)_\# P_X$ and $P_Y$.

Our optimization problem becomes:
$$\theta^* = \arg\min_{\theta \in \Theta} W_c((f_\theta)_\# P_X, P_Y)$$

Since we only have finite samples, we work with the empirical approximation:
$$\hat{\theta} = \arg\min_{\theta \in \Theta} W_c\left(\frac{1}{n}\sum_{i=1}^n \delta_{f_\theta(x_i)}, \frac{1}{m}\sum_{j=1}^m \delta_{y_j}\right)$$

## Technical Assumptions

**Assumption 1 (Regularity):** The function class $\mathcal{F}$ consists of Lipschitz continuous functions with Lipschitz constant $L < \infty$, i.e., $\|f_\theta(x_1) - f_\theta(x_2)\| \leq L\|x_1 - x_2\|$ for all $x_1, x_2 \in \mathcal{X}$ and $\theta \in \Theta$.

**Assumption 2 (Bounded support):** Both $P_X$ and $P_Y$ have bounded support, i.e., there exist compact sets $K_X \subset \mathcal{X}$ and $K_Y \subset \mathcal{Y}$ such that $P_X(K_X) = P_Y(K_Y) = 1$.

**Assumption 3 (Expressivity):** There exists $\theta_0 \in \Theta$ such that $(f_{\theta_0})_\# P_X = P_Y$, i.e., the function class is rich enough to represent the true transport map.

**Assumption 4 (Sample complexity):** We have sufficient samples such that $n, m \geq C \log(|\Theta|/\delta)$ for some constant $C$ and confidence parameter $\delta > 0$.

These assumptions are justified as follows: Assumption 1 ensures stability and prevents overfitting; Assumption 2 enables finite optimal transport costs; Assumption 3 guarantees realizability; Assumption 4 ensures statistical consistency. The framework connects to the conformal prediction literature by providing distribution-free guarantees on the quality of the learned transport map, analogous to how conformal methods provide distribution-free prediction intervals.

# Methodology

## High-Level Approach

Our approach learns single-step generative mappings by directly optimizing an empirical optimal transport objective. Rather than decomposing the complex distribution mapping into multiple simpler steps (as in diffusion models or iterative refinement methods), we train a neural network to perform the entire transformation in one forward pass. The key insight is to use the Wasserstein distance as a training objective, which can be efficiently computed using the Sinkhorn algorithm for regularized optimal transport.

## Core Algorithm: Direct Optimal Transport (DOT)

### Network Architecture

We parameterize the transport map as a deep neural network $f_\theta: \mathbb{R}^d \rightarrow \mathbb{R}^k$ with parameters $\theta$. The architecture consists of:
- Encoder layers that process the input $x \sim P_X$
- Transformation layers that perform the core distribution mapping
- Decoder layers that output $y = f_\theta(x)$ in the target space

### Sinkhorn-Regularized Optimal Transport Loss

Given source samples $\{x_i\}_{i=1}^n$ and target samples $\{y_j\}_{j=1}^m$, we compute transported samples $\{\tilde{y}_i = f_\theta(x_i)\}_{i=1}^n$ and minimize the regularized optimal transport cost:

$$\mathcal{L}_{\text{OT}}(\theta) = W_\varepsilon\left(\frac{1}{n}\sum_{i=1}^n \delta_{\tilde{y}_i}, \frac{1}{m}\sum_{j=1}^m \delta_{y_j}\right)$$

where $W_\varepsilon$ is the entropy-regularized Wasserstein distance:

$$W_\varepsilon(\mu, \nu) = \min_{\gamma \in \Pi(\mu, \nu)} \left\langle C, \gamma \right\rangle + \varepsilon H(\gamma)$$

Here $C_{ij} = c(\tilde{y}_i, y_j)$ is the cost matrix, $H(\gamma) = -\sum_{ij} \gamma_{ij} \log \gamma_{ij}$ is the entropy regularizer, and $\varepsilon > 0$ is the regularization parameter.

### Training Algorithm

```
Algorithm 1: Direct Optimal Transport Training

Input: Source samples {x_i}^n_i=1, target samples {y_j}^m_j=1
       Network f_θ, learning rate α, regularization ε
Output: Trained parameters θ*

1. Initialize θ randomly
2. For epoch = 1 to max_epochs:
   a. Sample mini-batch B_x from {x_i}, B_y from {y_j}
   b. Compute transported samples: ỹ_i = f_θ(x_i) for x_i ∈ B_x
   c. Construct cost matrix: C_ij = ||ỹ_i - y_j||^2 for y_j ∈ B_y
   d. Solve Sinkhorn iterations:
      • Initialize u = 1_n/n, v = 1_m/m
      • For k = 1 to K_sinkhorn:
        - u ← 1 / (K exp(-C/ε) v)
        - v ← 1 / (K^T exp(-C^T/ε) u)
      • Compute transport matrix: γ = diag(u) K diag(v)
        where K = exp(-C/ε)
   e. Compute loss: L = ⟨C, γ⟩ + ε H(γ)
   f. Update parameters: θ ← θ - α ∇_θ L
3. Return θ*
```

## Design Justifications

**Choice of Optimal Transport:** Unlike adversarial losses that can suffer from mode collapse or training instability, optimal transport provides a principled geometric distance between distributions. The Wasserstein distance metrizes weak convergence, ensuring that minimizing the empirical loss leads to convergence in distribution.

**Sinkhorn Regularization:** The entropy regularization makes the optimal transport problem strongly convex and enables efficient computation via the Sinkhorn algorithm. This connects to the conformal prediction literature's emphasis on computational efficiency - our approach avoids the expensive inner optimization loops required by adversarial methods.

**Single-Step Architecture:** By directly optimizing the transport map rather than learning a sequence of transformations, we achieve the desired single forward pass generation while maintaining the expressivity needed for complex distribution mappings.

## Theoretical Properties

**Proposition 1 (Consistency):** Under Assumptions 1-4, as $n, m \to \infty$, the empirical minimizer $\hat{\theta}$ converges to the population minimizer $\theta^*$ in probability.

**Proposition 2 (Generalization Bound):** With probability at least $1-\delta$, the generalization error satisfies:
$$W_c((f_{\hat{\theta}})_\# P_X, P_Y) \leq \hat{W}_c + O\left(\sqrt{\frac{\log(1/\delta)}{n}}\right)$$
where $\hat{W}_c$ is the empirical transport cost.

**Proposition 3 (Computational Complexity):** Each training iteration requires $O(nm K_{\text{sinkhorn}})$ operations, where $K_{\text{sinkhorn}}$ is typically small (10-100 iterations).

The consistency result follows from the uniform convergence of empirical measures under our regularity assumptions. The generalization bound leverages concentration inequalities for optimal transport, similar to how conformal prediction provides finite-sample guarantees. The computational complexity is linear in sample size, making the approach scalable to large datasets while avoiding the quadratic scaling of some transport-based methods.