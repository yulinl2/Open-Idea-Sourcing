# Reconstruction: problem
**Paper:** 2602.04770  
**Condition:** with_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Problem Formulation

## 2.1 Notation and Setup

Let $\mathcal{X} \subseteq \mathbb{R}^d$ denote the data space and $p_{\text{data}}$ denote the unknown target distribution over $\mathcal{X}$. We consider the fundamental problem of learning a generative model that can efficiently sample from $p_{\text{data}}$ without requiring iterative refinement procedures at inference time.

Let $p_{\text{noise}}$ denote a simple prior distribution (typically standard Gaussian $\mathcal{N}(0, I_d)$) from which we can easily sample. We seek to learn a mapping $G_\theta: \mathcal{Z} \to \mathcal{X}$, where $\mathcal{Z} \subseteq \mathbb{R}^d$ is the latent space, $\theta \in \Theta$ are learnable parameters, and the mapping satisfies $G_\theta(\mathbf{z}) \sim p_{\text{data}}$ when $\mathbf{z} \sim p_{\text{noise}}$.

For conditional generation, let $\mathcal{C}$ denote a conditioning space and $p_{\text{data}}(\mathbf{x}|\mathbf{c})$ denote the conditional target distribution for condition $\mathbf{c} \in \mathcal{C}$. We extend our mapping to $G_\theta: \mathcal{Z} \times \mathcal{C} \to \mathcal{X}$ such that $G_\theta(\mathbf{z}, \mathbf{c}) \sim p_{\text{data}}(\mathbf{x}|\mathbf{c})$.

## 2.2 Problem Statement

**Given:** A dataset $\mathcal{D} = \{(\mathbf{x}_i, \mathbf{c}_i)\}_{i=1}^N$ where $(\mathbf{x}_i, \mathbf{c}_i) \sim p_{\text{data}}(\mathbf{x}, \mathbf{c})$, and access to samples from the prior $p_{\text{noise}}$.

**Find:** Parameters $\theta^* \in \Theta$ such that the learned mapping $G_{\theta^*}$ satisfies:

1. **Single-step generation**: For any $\mathbf{z} \sim p_{\text{noise}}$ and $\mathbf{c} \in \mathcal{C}$, one forward pass $G_{\theta^*}(\mathbf{z}, \mathbf{c})$ produces a high-quality sample from $p_{\text{data}}(\mathbf{x}|\mathbf{c})$.

2. **Distribution matching**: The pushforward measure $(G_{\theta^*})_\# (p_{\text{noise}} \times p_{\text{condition}})$ approximates the joint distribution $p_{\text{data}}(\mathbf{x}, \mathbf{c})$, where $p_{\text{condition}}$ is the marginal conditioning distribution.

3. **Mode coverage**: The learned mapping avoids mode collapse, meaning $G_{\theta^*}$ can generate samples representing the full support of $p_{\text{data}}$.

## 2.3 Objective Formulation

We formulate the learning objective as finding parameters that minimize the distributional discrepancy:

$$\theta^* = \arg\min_{\theta \in \Theta} \mathcal{L}(\theta)$$

where the loss function $\mathcal{L}(\theta)$ measures the distance between the generated and target distributions. Specifically, we seek a loss that can be expressed as:

$$\mathcal{L}(\theta) = \mathbb{E}_{(\mathbf{x}, \mathbf{c}) \sim p_{\text{data}}} \mathbb{E}_{\mathbf{z} \sim p_{\text{noise}}} \ell(\mathbf{x}, G_\theta(\mathbf{z}, \mathbf{c}), \mathbf{c})$$

for some per-sample loss function $\ell: \mathcal{X} \times \mathcal{X} \times \mathcal{C} \to \mathbb{R}_+$.

The key requirement is that this objective should:
- Be tractable to optimize via gradient-based methods
- Not require adversarial training or minimax optimization  
- Enable direct regression from noise to data without iterative sampling
- Support flexible conditioning mechanisms

## 2.4 Technical Assumptions

We make the following assumptions to ensure theoretical tractability:

**A1 (Regularity):** The target distribution $p_{\text{data}}$ has support on a bounded subset of $\mathcal{X}$ and possesses sufficient regularity (e.g., absolute continuity with respect to Lebesgue measure on its support).

**A2 (Universal approximation):** The function class $\{G_\theta : \theta \in \Theta\}$ has sufficient capacity to approximate the optimal transport map from $p_{\text{noise}}$ to $p_{\text{data}}$. This is satisfied when $G_\theta$ is a sufficiently deep neural network.

**A3 (Lipschitz continuity):** There exists $L > 0$ such that for all $\theta$, the mapping $G_\theta$ is $L$-Lipschitz continuous. This ensures stability and prevents pathological behavior during training.

**A4 (Moment bounds):** Both $p_{\text{data}}$ and $p_{\text{noise}}$ have finite second moments, ensuring well-defined gradients and stable optimization.

**A5 (Conditioning regularity):** The conditional distributions $p_{\text{data}}(\mathbf{x}|\mathbf{c})$ vary smoothly with respect to the conditioning variable $\mathbf{c}$, enabling effective conditional generation.

These assumptions are standard in the generative modeling literature and are necessary to guarantee convergence of gradient-based optimization and the existence of solutions.

## 2.5 Connection to Prior Work

Our formulation addresses key limitations in existing generative modeling paradigms:

**Variational Autoencoders (VAEs)** optimize a variational lower bound on the log-likelihood but often produce blurry samples due to the Gaussian decoder assumption and KL regularization that can lead to posterior collapse.

**Generative Adversarial Networks (GANs)** achieve high sample quality through adversarial training but suffer from training instability, mode collapse, and the need for careful balancing between generator and discriminator.

**Diffusion Models** produce excellent samples but require hundreds of denoising steps at inference time, making them computationally expensive for real-time applications.

**Flow-based models** provide exact likelihood computation and stable training but are architecturally constrained by invertibility requirements, limiting their expressiveness.

**Score-based models** achieve strong results but also require iterative sampling procedures, inheriting the computational cost issues of diffusion approaches.

Our formulation seeks a middle ground: the single-step efficiency of VAEs and GANs combined with the training stability of diffusion models, without requiring adversarial objectives or iterative inference procedures. The key insight is to directly learn the mapping from noise to data through a carefully designed regression objective that preserves distributional properties while enabling efficient generation.
