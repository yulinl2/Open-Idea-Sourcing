# Reconstruction: problem (iterative, 5 rounds)
**Paper:** 2602.04770  
**Condition:** with_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  
**Rounds:** 5  
**Best round:** 3 (score 3.4)  
**Converged:** True (reached max rounds (5))  
**Score trajectory:** 3.2 -> 3.2 -> 3.4 -> 3.0 -> 3.4  

---

# Problem Formulation

## Notation and Problem Setup

Let $\mathcal{X}$ denote the data space and $\mathcal{Z}$ denote the noise space, both equipped with appropriate probability measures. We consider two probability distributions: the target data distribution $p_{\text{data}}(x)$ supported on $\mathcal{X}$, and a tractable noise distribution $p_{\text{noise}}(z)$ supported on $\mathcal{Z}$ (typically a standard Gaussian). Let $G_\theta: \mathcal{Z} \to \mathcal{X}$ be a generator network parameterized by $\theta \in \Theta$, where $\Theta$ is the parameter space.

During training, we have access to a dataset $\{x_i\}_{i=1}^n$ of $n$ samples drawn i.i.d. from $p_{\text{data}}$. At each training iteration $t$, the generator $G_{\theta^{(t)}}$ induces a distribution $p_{\theta^{(t)}}(x)$ over the data space via the pushforward measure: for any measurable set $A \subseteq \mathcal{X}$,
$$p_{\theta^{(t)}}(A) = p_{\text{noise}}\{z : G_{\theta^{(t)}}(z) \in A\}.$$

The key insight is to view generated samples as particles that evolve during training according to a dynamical system. Let $\{z_j\}_{j=1}^m$ be a fixed set of noise samples, and define the corresponding generated samples at iteration $t$ as $x_j^{(t)} = G_{\theta^{(t)}}(z_j)$. These samples constitute a particle system where each particle $x_j^{(t)}$ moves in the data space as training progresses.

## Formal Problem Statement

**Given:** 
- A dataset $\{x_i\}_{i=1}^n$ sampled from the target distribution $p_{\text{data}}$
- A generator architecture $G_\theta: \mathcal{Z} \to \mathcal{X}$
- A noise distribution $p_{\text{noise}}(z)$

**Find:** A training procedure that evolves the generator parameters $\theta^{(t)}$ such that the induced distribution $p_{\theta^{(t)}}$ converges to $p_{\text{data}}$ as $t \to \infty$.

**Constraint:** The generator must produce high-quality samples in a single forward pass at inference time, without requiring iterative refinement.

The core challenge is to design a particle dynamics that governs how generated samples $x_j^{(t)}$ move during training. We seek a vector field $v_t: \mathcal{X} \to \mathcal{X}$ such that particles follow the ordinary differential equation:
$$\frac{dx_j^{(t)}}{dt} = v_t(x_j^{(t)})$$

This vector field should satisfy two critical properties:
1. **Convergence:** When $p_{\theta^{(t)}} = p_{\text{data}}$, we have $v_t(x) = 0$ for all $x$
2. **Direction:** The field $v_t(x)$ points in directions that reduce the discrepancy between $p_{\theta^{(t)}}$ and $p_{\text{data}}$

## Objective Formulation

We propose that the vector field $v_t(x)$ should be determined by the score difference between the current generated distribution and the target distribution:
$$v_t(x) = \nabla_x \log p_{\text{data}}(x) - \nabla_x \log p_{\theta^{(t)}}(x)$$

This formulation ensures that particles move along the gradient of the log-density ratio, naturally driving the generated distribution toward the target distribution. When the distributions match, $\nabla_x \log p_{\text{data}}(x) = \nabla_x \log p_{\theta^{(t)}}(x)$, yielding $v_t(x) = 0$ and achieving equilibrium.

The training objective becomes minimizing the expected squared magnitude of the vector field:
$$\mathcal{L}(\theta) = \mathbb{E}_{x \sim p_{\theta}}[\|v_t(x)\|^2] = \mathbb{E}_{x \sim p_{\theta}}[\|\nabla_x \log p_{\text{data}}(x) - \nabla_x \log p_{\theta}(x)\|^2]$$

This objective is minimized when $p_{\theta} = p_{\text{data}}$, providing a principled training target. However, since $p_{\theta}$ and its score are not directly accessible, we must develop tractable approximations.

## Technical Assumptions

**A1. Regularity:** The generator $G_\theta$ is twice differentiable with respect to both $\theta$ and its input, and the target distribution $p_{\text{data}}$ has a well-defined score function $\nabla_x \log p_{\text{data}}(x)$.

**A2. Score Accessibility:** We can obtain unbiased estimates of $\nabla_x \log p_{\text{data}}(x)$ either through a pre-trained score network or via denoising score matching on the training data.

**A3. Particle Representation:** The generated distribution $p_{\theta^{(t)}}$ can be adequately represented by a finite particle system $\{x_j^{(t)}\}_{j=1}^m$ for sufficiently large $m$.

**A4. Smoothness:** The vector field $v_t(x)$ is Lipschitz continuous, ensuring the existence and uniqueness of solutions to the particle dynamics.

**A5. Bounded Support:** Both $p_{\text{data}}$ and $p_{\theta}$ have support contained in a bounded region of $\mathcal{X}$, preventing particles from diverging to infinity.

These assumptions are standard in the generative modeling literature and are necessary to ensure well-posed dynamics and convergence guarantees.

## Connection to Prior Work

Traditional generative models face a fundamental trade-off between sample quality and inference efficiency. Generative Adversarial Networks (GANs) achieve single-pass generation but suffer from training instability and mode collapse. Variational Autoencoders (VAEs) provide stable training but often produce blurry samples. Diffusion models achieve high sample quality but require hundreds of denoising steps at inference time.

Score-based generative models have shown that the score function $\nabla_x \log p_{\text{data}}(x)$ contains sufficient information to generate samples via Langevin dynamics, but again require iterative sampling procedures. Our formulation bridges this gap by using score information to guide the training process rather than the inference process.

The key insight differentiating our approach is the interpretation of generated samples as particles in a dynamical system. While existing methods typically view generation as a static mapping problem, we leverage the inherently iterative nature of neural network training to evolve the generated distribution. This perspective allows us to achieve the modeling capacity of iterative methods while maintaining single-pass inference.

Our formulation addresses the core limitation of existing approaches: the need for either adversarial training (which can be unstable) or iterative inference (which is computationally expensive). By casting the problem as particle dynamics driven by score differences, we obtain a principled objective that naturally converges to the target distribution while preserving the efficiency of single-forward-pass generation.
