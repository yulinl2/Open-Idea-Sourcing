# Reconstruction: problem_method
**Paper:** 2602.04770  
**Condition:** with_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Problem Formulation

We consider the fundamental challenge of learning generative models that can efficiently transform between probability distributions. Let $\mathcal{X} \subseteq \mathbb{R}^d$ denote the data space and let $P_{\text{data}}$ be the unknown target data distribution over $\mathcal{X}$. We assume access to a training dataset $\mathcal{D} = \{x_i\}_{i=1}^n$ where $x_i \sim P_{\text{data}}$ are i.i.d. samples.

Let $P_{\text{noise}}$ denote a simple base distribution (typically $\mathcal{N}(0, I_d)$) from which we can easily sample. Our goal is to learn a transformation $T_\theta: \mathcal{X} \to \mathcal{X}$ parameterized by $\theta \in \Theta$ that maps samples from $P_{\text{noise}}$ to samples from $P_{\text{data}}$ in a single forward pass.

**Formal Problem Statement:** Given training data $\mathcal{D} = \{x_i\}_{i=1}^n$ where $x_i \sim P_{\text{data}}$, find parameters $\theta^* \in \Theta$ such that:

1. **Generation Quality:** For $z \sim P_{\text{noise}}$, the transformed sample $T_{\theta^*}(z)$ follows a distribution $P_{\theta^*}$ that approximates $P_{\text{data}}$
2. **Efficiency:** The transformation requires only a single forward pass through $T_{\theta^*}$
3. **Coverage:** The learned distribution $P_{\theta^*}$ captures the full support of $P_{\text{data}}$ without mode collapse

We formalize this as an optimization problem over the Wasserstein-2 distance:
$$\theta^* = \arg\min_{\theta \in \Theta} W_2^2(P_{\text{data}}, P_{\theta})$$
where $P_{\theta}$ is the pushforward measure $(T_\theta)_\# P_{\text{noise}}$ and
$$W_2^2(P, Q) = \inf_{\gamma \in \Pi(P,Q)} \int_{\mathcal{X} \times \mathcal{X}} \|x - y\|^2 d\gamma(x,y)$$
with $\Pi(P,Q)$ denoting the set of all couplings between distributions $P$ and $Q$.

**Technical Assumptions:**
1. **Regularity:** $P_{\text{data}}$ has finite second moments and compact support
2. **Smoothness:** The transformation $T_\theta$ is differentiable with respect to both input and parameters
3. **Invertibility:** There exists an optimal coupling $\gamma^*$ between $P_{\text{noise}}$ and $P_{\text{data}}$ that is deterministic
4. **Approximation:** The function class $\{T_\theta : \theta \in \Theta\}$ is sufficiently rich to approximate the optimal transport map

This formulation extends beyond traditional adversarial approaches by directly optimizing transport cost rather than relying on minimax objectives, while maintaining the single-pass efficiency requirement that distinguishes it from iterative sampling methods.

# Methodology

Our approach, which we term **Rectified Flow**, learns the optimal transport map between $P_{\text{noise}}$ and $P_{\text{data}}$ by training a neural network to predict velocity fields along straight-line paths connecting noise and data samples.

## Core Algorithm

The key insight is to parameterize the transformation as the solution to an ordinary differential equation (ODE) with a learned velocity field. Given a coupling $\gamma$ between $P_{\text{noise}}$ and $P_{\text{data}}$, we define straight-line paths:
$$\mathbf{x}_t = (1-t)\mathbf{z} + t\mathbf{x}_1, \quad t \in [0,1]$$
where $(\mathbf{z}, \mathbf{x}_1) \sim \gamma$, with $\mathbf{z} \sim P_{\text{noise}}$ and $\mathbf{x}_1 \sim P_{\text{data}}$.

The velocity field along these paths is simply:
$$\mathbf{v}_t(\mathbf{x}_t) = \mathbf{x}_1 - \mathbf{z}$$

We train a neural network $v_\theta: \mathbb{R}^d \times [0,1] \to \mathbb{R}^d$ to approximate this velocity field by minimizing:
$$\mathcal{L}(\theta) = \mathbb{E}_{(\mathbf{z},\mathbf{x}_1) \sim \gamma, t \sim \text{Uniform}[0,1]} \left[\|v_\theta(\mathbf{x}_t, t) - (\mathbf{x}_1 - \mathbf{z})\|^2\right]$$

**Algorithm 1: Rectified Flow Training**
```
1. Initialize neural network v_θ(x, t)
2. For each training iteration:
   a. Sample batch {x₁⁽ⁱ⁾}ᵢ₌₁ᵇ from training data
   b. Sample batch {z⁽ⁱ⁾}ᵢ₌₁ᵇ from P_noise
   c. Sample time steps {t⁽ⁱ⁾}ᵢ₌₁ᵇ uniformly from [0,1]
   d. Compute interpolated points: x_t⁽ⁱ⁾ = (1-t⁽ⁱ⁾)z⁽ⁱ⁾ + t⁽ⁱ⁾x₁⁽ⁱ⁾
   e. Compute target velocities: v_target⁽ⁱ⁾ = x₁⁽ⁱ⁾ - z⁽ⁱ⁾
   f. Update θ to minimize: Σᵢ ||v_θ(x_t⁽ⁱ⁾, t⁽ⁱ⁾) - v_target⁽ⁱ⁾||²
3. Return trained velocity field v_θ
```

## Generation Process

Once trained, we generate samples by solving the ODE:
$$\frac{d\mathbf{x}}{dt} = v_\theta(\mathbf{x}, t), \quad \mathbf{x}(0) = \mathbf{z} \sim P_{\text{noise}}$$

The generated sample is $\mathbf{x}(1)$, obtained by integrating from $t=0$ to $t=1$.

**Algorithm 2: Rectified Flow Sampling**
```
1. Sample initial noise: z ~ P_noise
2. Initialize: x₀ = z, t = 0, Δt = 1/N (for N integration steps)
3. For i = 0 to N-1:
   a. Compute velocity: v = v_θ(xᵢ, t)
   b. Update: xᵢ₊₁ = xᵢ + Δt · v
   c. Update: t = t + Δt
4. Return x_N as generated sample
```

## Design Justifications

**Straight-line paths:** Unlike curved trajectories in other flow-based models, straight lines minimize transport cost under the $L^2$ metric, directly optimizing our Wasserstein-2 objective. This connects to optimal transport theory where, under regularity conditions, optimal transport maps correspond to gradients of convex functions that induce straight-line displacement.

**Velocity field parameterization:** By learning the velocity field rather than the transformation directly, we leverage the universal approximation properties of neural networks while ensuring the learned map integrates consistently along trajectories. This approach draws inspiration from neural ODEs but with the crucial difference that our target velocity field has a simple analytical form.

**Coupling strategy:** In practice, we use the empirical coupling $\gamma_n = \frac{1}{n}\sum_{i=1}^n \delta_{(z_i, x_i)}$ where $z_i \sim P_{\text{noise}}$ and $x_i$ are training samples. This corresponds to an independent coupling, which while not optimal, provides a tractable approximation that can be iteratively refined.

## Theoretical Properties

**Convergence:** Under standard regularity conditions on the neural network approximation, the learned velocity field $v_\theta$ converges to the true velocity field as the network capacity increases and training data grows. The integration of the learned ODE then converges to the optimal transport map.

**Consistency:** The straight-line parameterization ensures that the learned transformation preserves the marginal distributions by construction - integrating from $P_{\text{noise}}$ at $t=0$ to $P_{\text{data}}$ at $t=1$.

**Computational Complexity:** Training requires $O(nd)$ operations per batch, where $n$ is batch size and $d$ is dimensionality. Generation requires solving an ODE, typically with $O(N)$ network evaluations for $N$ integration steps, but can achieve high quality with small $N$ (often $N \leq 10$) due to the straight-line geometry.

The method's efficiency stems from avoiding adversarial training dynamics while maintaining the single-pass generation property through direct optimization of the transport objective.
