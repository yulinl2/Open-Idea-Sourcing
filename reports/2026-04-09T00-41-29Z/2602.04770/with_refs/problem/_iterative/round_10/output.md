# Problem Formulation

## 2.1 Notation and Setup

Let $\mathcal{X} \subseteq \mathbb{R}^d$ denote the data space and $p$ be a fixed base distribution on $\mathcal{X}$ (e.g., standard Gaussian). Let $q$ denote the target data distribution we wish to model. We consider a parametric generator $f_\theta: \mathcal{X} \to \mathcal{X}$ with parameters $\theta \in \Theta$, where $\Theta$ is the parameter space.

The **pushforward distribution** induced by $f_\theta$ is defined as $f_\theta\#p$, where for any measurable set $A \subseteq \mathcal{X}$:
$$(f_\theta\#p)(A) = p(f_\theta^{-1}(A))$$

During training, we observe i.i.d. samples $\{x_i\}_{i=1}^n \sim q$ from the target distribution. At each training iteration $t$, the current generator parameters $\theta^{(t)}$ induce a pushforward distribution $f_{\theta^{(t)}}\#p$ that evolves as training progresses.

## 2.2 Drift Field Formulation

We define a **drift field** $V_{p,q}: \mathcal{X} \to \mathbb{R}^d$ that governs how generated samples should move during training. For any point $x \in \mathcal{X}$, the drift is computed as:

$$V_{p,q}(x) = \sum_{i=1}^n K(x, x_i) \frac{x_i - x}{\|x_i - x\|} - \sum_{j=1}^m K(x, \tilde{x}_j) \frac{\tilde{x}_j - x}{\|\tilde{x}_j - x\|}$$

where:
- $\{x_i\}_{i=1}^n$ are samples from the target distribution $q$
- $\{\tilde{x}_j\}_{j=1}^m$ are samples from the current pushforward distribution $f_{\theta^{(t)}}\#p$
- $K: \mathcal{X} \times \mathcal{X} \to \mathbb{R}_+$ is a kernel function (e.g., RBF kernel)

The drift field exhibits the crucial **anti-symmetry property**:
$$V_{p,q}(x) = -V_{q,p}(x)$$

This ensures that when the distributions match ($p = q$), the drift field vanishes: $V_{p,p}(x) = 0$ for all $x$.

## 2.3 Problem Statement

**Given**: 
- Base distribution $p$ on $\mathcal{X}$
- Target samples $\{x_i\}_{i=1}^n \sim q$ 
- Parametric generator family $\{f_\theta : \theta \in \Theta\}$
- Kernel function $K$

**Find**: Parameters $\theta^*$ such that the pushforward distribution $f_{\theta^*}\#p$ approximates the target distribution $q$ in a single forward pass.

**Constraint**: The training procedure must leverage the iterative nature of optimization by evolving the pushforward distribution $f_{\theta^{(t)}}\#p$ at each training step $t$, eliminating the need for iterative refinement at inference time.

## 2.4 Training Objective

At each training iteration $t$, we sample $\{z_i\}_{i=1}^m \sim p$ and compute their images $\{\tilde{x}_i^{(t)}\}_{i=1}^m = \{f_{\theta^{(t)}}(z_i)\}_{i=1}^m$ under the current generator. The **drifted targets** are computed as:

$$\tilde{x}_i^{(t+1)} = \tilde{x}_i^{(t)} + \eta \cdot V_{f_{\theta^{(t)}}\#p, q}(\tilde{x}_i^{(t)})$$

where $\eta > 0$ is a drift step size.

The training loss at iteration $t$ is:
$$\mathcal{L}(\theta) = \frac{1}{m} \sum_{i=1}^m \|f_\theta(z_i) - \text{sg}(\tilde{x}_i^{(t+1)})\|^2$$

where $\text{sg}(\cdot)$ denotes the stop-gradient operator, preventing gradients from flowing through the drifted targets.

## 2.5 Technical Assumptions

**A1 (Generator Capacity)**: The generator family $\{f_\theta\}$ has sufficient capacity to represent the optimal transport map from $p$ to $q$.

**A2 (Kernel Properties)**: The kernel $K$ is positive definite, translation-invariant, and satisfies $K(x,y) \to 0$ as $\|x-y\| \to \infty$.

**A3 (Sample Complexity)**: The number of target samples $n$ and generated samples $m$ per iteration are sufficient for stable drift estimation.

**A4 (Optimization)**: The parameter update rule ensures convergence to a stationary point of the drift-corrected objective.

**A5 (Feature Space)**: When working in learned feature spaces via pre-trained encoders $\phi: \mathcal{X} \to \mathcal{Z}$, the drift field is computed in the encoded space $\mathcal{Z}$ where distances are more semantically meaningful.

## 2.6 Connection to Prior Work

Traditional generative models face a fundamental trade-off: **GANs** achieve single-pass generation but suffer from training instability and mode collapse; **VAEs** provide stable training but with limited expressiveness; **diffusion and flow models** achieve high quality through iterative refinement but require multiple network evaluations at inference.

Our formulation addresses this limitation by recognizing that the iterative refinement paradigm successful in diffusion models can be **moved from inference time to training time**. Unlike existing approaches that treat the generator's output distribution as static during training, we explicitly model and control the evolution of the pushforward distribution $f_{\theta^{(t)}}\#p$ through the anti-symmetric drift field.

This contrasts with standard training objectives that only consider instantaneous generator outputs, ignoring the distributional evolution that naturally occurs during iterative optimization. The anti-symmetry property provides a principled stopping criterion—drift naturally ceases when distributions align—unlike adversarial training which lacks such natural equilibrium conditions.

The stop-gradient technique ensures stable optimization by treating drifted positions as fixed targets, similar to momentum-based methods but with explicit geometric interpretation through the drift field dynamics.