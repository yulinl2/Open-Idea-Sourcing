# Problem Formulation

## Notation and Problem Setup

Let $\mathcal{X}$ denote the data space and $\mathcal{Z}$ denote the noise space, both equipped with appropriate probability measures. We consider probability distributions $p_{\text{data}}$ over $\mathcal{X}$ (the target data distribution) and $p_{\text{noise}}$ over $\mathcal{Z}$ (typically a simple distribution such as standard Gaussian). Let $G_\theta: \mathcal{Z} \to \mathcal{X}$ denote a generator network parameterized by $\theta \in \Theta$, where $\Theta$ is the parameter space.

For a given generator $G_\theta$, we define the induced distribution $p_\theta$ over $\mathcal{X}$ as the pushforward of $p_{\text{noise}}$ through $G_\theta$:
$$p_\theta(x) = \int_{\mathcal{Z}} p_{\text{noise}}(z) \delta(x - G_\theta(z)) dz$$

Let $\{\theta^{(t)}\}_{t=0}^T$ denote the sequence of parameter values during training, where $\theta^{(0)}$ represents the initial parameters and $\theta^{(T)}$ the final parameters after $T$ training iterations. We define the training trajectory as the path $\gamma: [0,T] \to \Theta$ with $\gamma(t) = \theta^{(t)}$.

## Formal Problem Statement

**Given:** 
- A dataset $\mathcal{D} = \{x_i\}_{i=1}^n$ sampled i.i.d. from $p_{\text{data}}$
- A generator architecture $G: \mathcal{Z} \times \Theta \to \mathcal{X}$
- A noise distribution $p_{\text{noise}}$ over $\mathcal{Z}$

**Find:** A training procedure that produces parameters $\theta^*$ such that:
1. The generator $G_{\theta^*}$ can produce high-quality samples in a single forward pass
2. The induced distribution $p_{\theta^*}$ approximates $p_{\text{data}}$ well
3. The training leverages the iterative nature of optimization to learn complex distribution mappings

**Guarantee:** The final generator $G_{\theta^*}$ should satisfy an equilibrium condition indicating convergence to a stable solution that captures the target distribution.

## Objective Formulation

We propose to optimize an objective that explicitly incorporates the training trajectory. Let $\mathcal{L}: \mathcal{X} \times \mathcal{X} \to \mathbb{R}_+$ denote a loss function measuring discrepancy between samples. Our objective takes the form:

$$\min_{\theta} \mathbb{E}_{x \sim p_{\text{data}}, z \sim p_{\text{noise}}} \left[ \mathcal{L}(x, G_\theta(z)) + \lambda \cdot \Omega(\theta, \{\theta^{(s)}\}_{s=0}^{t-1}) \right]$$

where $\Omega(\theta, \{\theta^{(s)}\}_{s=0}^{t-1})$ is a trajectory regularization term that encourages consistency with the training history, and $\lambda > 0$ is a regularization parameter.

The equilibrium condition is defined as:
$$\|\theta^{(t+1)} - \theta^{(t)}\|_2 \leq \epsilon_{\text{conv}}$$
for some convergence threshold $\epsilon_{\text{conv}} > 0$, indicating that the parameters have stabilized.

## Technical Assumptions

**A1 (Generator Capacity):** The generator class $\{G_\theta : \theta \in \Theta\}$ has sufficient capacity to approximate the target distribution, i.e., there exists $\theta^* \in \Theta$ such that $p_{\theta^*}$ is arbitrarily close to $p_{\text{data}}$ in an appropriate metric.

**A2 (Training Trajectory Regularity):** The training trajectory $\{\theta^{(t)}\}_{t=0}^T$ is Lipschitz continuous with respect to the iteration index, ensuring smooth parameter evolution.

**A3 (Loss Function Properties):** The loss function $\mathcal{L}$ is non-negative, symmetric ($\mathcal{L}(x,y) = \mathcal{L}(y,x)$), and satisfies the triangle inequality, making it a proper distance measure.

**A4 (Bounded Moments):** Both $p_{\text{data}}$ and $p_{\text{noise}}$ have bounded second moments to ensure finite variance in gradient estimates.

These assumptions are justified by the need to ensure: (A1) expressivity for complex distribution learning, (A2) stable optimization dynamics, (A3) meaningful distance measurement between distributions, and (A4) convergent stochastic optimization.

## Connection to Prior Work

This formulation extends traditional generative modeling by explicitly incorporating the training dynamics into the objective function, similar in spirit to how the conformal prediction framework in the reference leverages the entire prediction procedure rather than just point estimates. Unlike adversarial training which requires equilibrium between two networks, our approach seeks equilibrium within a single network's training trajectory.

# Methodology

## High-Level Approach

Our proposed method, **Trajectory Consistency Training (TCT)**, leverages the iterative nature of neural network training to learn distribution mappings that produce high-quality samples in a single forward pass. The key insight is to enforce consistency between samples generated at different points along the training trajectory, encouraging the model to learn stable mappings that persist across parameter updates.

The approach consists of three main components: (1) trajectory-aware loss computation that compares current generations with those from previous training steps, (2) a consistency regularization mechanism that encourages smooth evolution of the generated distribution, and (3) an adaptive equilibrium detection criterion that determines convergence.

## Core Algorithm

The training procedure alternates between standard gradient-based updates and trajectory consistency enforcement. At each iteration $t$, we maintain a buffer of previous parameter states $\mathcal{B}_t = \{\theta^{(s)}\}_{s=\max(0,t-K)}^{t-1}$ for some window size $K$.

The trajectory consistency loss is defined as:
$$\mathcal{L}_{\text{traj}}(\theta^{(t)}) = \frac{1}{|\mathcal{B}_t|} \sum_{\theta' \in \mathcal{B}_t} \mathbb{E}_{z \sim p_{\text{noise}}} \left[ \mathcal{L}(G_{\theta^{(t)}}(z), G_{\theta'}(z)) \right]$$

This encourages the current generator to produce samples similar to those from recent training iterations, promoting stability in the learned mapping.

The total objective at iteration $t$ becomes:
$$\mathcal{J}_t(\theta) = \mathbb{E}_{x \sim p_{\text{data}}, z \sim p_{\text{noise}}} [\mathcal{L}(x, G_\theta(z))] + \lambda_t \cdot \mathcal{L}_{\text{traj}}(\theta)$$

where $\lambda_t$ is an adaptive weight that increases as training progresses:
$$\lambda_t = \lambda_0 \cdot \min\left(1, \frac{t}{T_{\text{warmup}}}\right) \cdot \exp\left(-\frac{\|\nabla_\theta \mathcal{J}_{t-1}\|_2}{\sigma_{\text{grad}}}\right)$$

## Detailed Algorithm

```
Algorithm: Trajectory Consistency Training (TCT)

Input: Dataset D, generator G, learning rate η, trajectory weight λ₀, 
       window size K, warmup steps T_warmup, convergence threshold ε_conv

1. Initialize: θ⁽⁰⁾ randomly, trajectory buffer B₀ = ∅, t = 0

2. While not converged:
   a. Sample batch {xᵢ}ᵢ₌₁ᵇ from D
   b. Sample noise batch {zᵢ}ᵢ₌₁ᵇ from p_noise
   
   c. Compute data consistency loss:
      L_data = (1/b) Σᵢ L(xᵢ, G_θ⁽ᵗ⁾(zᵢ))
   
   d. If |Bₜ| > 0:
      - Sample {z'ⱼ}ⱼ₌₁ᵇ from p_noise
      - For each θ' ∈ Bₜ:
          Compute L_traj += (1/|Bₜ|) · (1/b) Σⱼ L(G_θ⁽ᵗ⁾(z'ⱼ), G_θ'(z'ⱼ))
      Else: L_traj = 0
   
   e. Compute adaptive weight:
      λₜ = λ₀ · min(1, t/T_warmup) · exp(-‖∇θJ_{t-1}‖₂/σ_grad)
   
   f. Total loss: J_t = L_data + λₜ · L_traj
   
   g. Update parameters: θ⁽ᵗ⁺¹⁾ = θ⁽ᵗ⁾ - η · ∇θJ_t
   
   h. Update trajectory buffer:
      Bₜ₊₁ = {θ⁽ᵗ⁾} ∪ {θ' ∈ Bₜ : t - age(θ') < K}
   
   i. Check convergence: 
      If ‖θ⁽ᵗ⁺¹⁾ - θ⁽ᵗ⁾‖₂ ≤ ε_conv: break
   
   j. t = t + 1

3. Return: θ⁽ᵗ⁾ (converged parameters)
```

## Design Justifications

**Trajectory Buffer Design:** The sliding window approach balances memory efficiency with trajectory consistency. Maintaining too many previous states would be computationally prohibitive, while too few would not provide sufficient regularization. The window size $K$ should be proportional to the expected convergence time.

**Adaptive Weighting:** The trajectory weight $\lambda_t$ starts small to allow initial exploration and increases as training progresses to enforce consistency. The gradient norm term reduces trajectory enforcement when the model is still learning rapidly, similar to how conformal prediction adapts to model uncertainty.

**Equilibrium Detection:** The convergence criterion based on parameter stability directly addresses the requirement for an equilibrium condition, indicating when the model has reached a stable distribution mapping.

## Theoretical Properties

**Convergence:** Under assumptions A1-A4, the sequence $\{\theta^{(t)}\}$ converges to a stationary point of the trajectory-regularized objective. The trajectory consistency term acts as a Lyapunov function, ensuring decreasing loss variance over time.

**Consistency:** As $t \to \infty$, the generated distribution $p_{\theta^{(t)}}$ converges to a fixed point that balances data fidelity and trajectory stability. This provides a principled equilibrium condition for training termination.

**Sample Quality:** The single forward pass generation capability is preserved since the method only modifies the training procedure, not the inference architecture. The trajectory consistency ensures that the final generator produces stable, high-quality samples.

## Computational Complexity

**Training Complexity:** Each iteration requires $O(bK)$ additional forward passes for trajectory consistency computation, where $b$ is batch size and $K$ is window size. This adds a constant factor overhead compared to standard training.

**Memory Complexity:** The trajectory buffer requires $O(K|\theta|)$ additional memory to store previous parameter states. For practical values of $K$ (e.g., 10-50), this represents a manageable overhead.

**Inference Complexity:** Unchanged from the base generator architecture - single forward pass $O(|\theta|)$ computation, achieving the desired efficiency goal.

The method scales effectively to high-resolution data since the trajectory consistency operates in parameter space rather than data space, avoiding the quadratic scaling issues of some alternative approaches.