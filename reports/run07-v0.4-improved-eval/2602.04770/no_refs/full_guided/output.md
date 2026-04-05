# Reconstruction: full_guided
**Paper:** 2602.04770  
**Condition:** no_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Rectified Flow: A Straight Path to High-Quality Generation

## Abstract

Current generative models face a fundamental trade-off between generation quality and computational efficiency. While diffusion models achieve state-of-the-art sample quality, they require hundreds of function evaluations during inference. Flow-based models can generate samples in a single step but often struggle with complex, high-dimensional distributions. We propose Rectified Flow, a novel generative modeling framework that learns straight-line trajectories between noise and data distributions. Our approach trains a neural network to predict velocity fields that transport samples along the shortest paths in probability space, enabling high-quality generation in a single forward pass. The key insight is that by explicitly encouraging straight trajectories during training, we can achieve both the modeling flexibility of iterative methods and the efficiency of single-step generation. Rectified Flow avoids adversarial training, supports flexible conditioning, and scales naturally to high-dimensional data. We demonstrate that this approach bridges the gap between quality and efficiency in generative modeling, opening new possibilities for real-time generation applications.

## 1. Introduction

Generative modeling has emerged as one of the most impactful areas of machine learning, with applications spanning image synthesis, drug discovery, and robotics. The fundamental challenge lies in learning complex mappings between probability distributions - transforming simple noise distributions into rich data distributions that capture the complexity of natural phenomena.

Recent advances have established two dominant paradigms. Diffusion models achieve remarkable sample quality by learning to reverse a gradual noising process, but require hundreds of denoising steps at inference time. Flow-based models can generate samples in a single forward pass but often struggle to model complex distributions effectively, particularly in high-dimensional spaces like natural images.

This creates a fundamental tension: the iterative nature that enables diffusion models to achieve high quality also makes them computationally expensive at generation time. For many applications - from real-time interactive systems to resource-constrained environments - this computational cost is prohibitive.

We introduce Rectified Flow, a generative modeling framework that resolves this tension by learning straight-line trajectories between noise and data distributions. The key insight is that the shortest path between two points is a straight line, and by explicitly encouraging such trajectories during training, we can achieve efficient generation without sacrificing modeling capability.

**Contributions:**
• We propose Rectified Flow, a novel framework for learning straight-line transport maps between distributions
• We develop a training objective that encourages direct paths while maintaining theoretical guarantees
• We show how to extend the approach to conditional generation with flexible conditioning mechanisms
• We demonstrate that single-step generation can achieve quality comparable to iterative methods
• We provide theoretical analysis connecting straight-line flows to optimal transport theory

## 2. Related Work

**Flow-Based Models.** Normalizing flows learn invertible transformations between simple and complex distributions. Early approaches like Real NVP and Glow use coupling layers to maintain tractability, but often struggle with expressiveness. Continuous normalizing flows use neural ODEs to learn more flexible transformations but require expensive ODE solvers at inference time. Our approach differs by explicitly targeting straight-line trajectories, avoiding both architectural constraints and expensive integration.

**Diffusion Models.** Denoising diffusion probabilistic models have achieved state-of-the-art results in image generation by learning to reverse a fixed noising process. Score-based generative models provide a continuous perspective, learning score functions that guide sampling through stochastic differential equations. While highly effective, these approaches inherently require many function evaluations. Recent work on consistency models and progressive distillation attempts to reduce sampling steps but often at the cost of sample quality.

**Optimal Transport.** Optimal transport theory studies the most efficient ways to transform one distribution into another. The Wasserstein distance provides a natural metric for comparing distributions, and computing optimal transport maps has connections to generative modeling. However, computing exact optimal transport maps is computationally intractable for high-dimensional distributions. Our approach can be viewed as learning approximations to optimal transport maps with straight-line structure.

**Single-Step Generation.** Several recent works have explored single-step generation. Adversarial networks can generate samples in one forward pass but suffer from training instability and mode collapse. Variational autoencoders provide stable training but often produce blurry samples. Flow matching and related approaches learn continuous-time flows but don't explicitly encourage straight trajectories.

**Gap Identification.** While existing methods achieve either high quality through iteration or efficiency through single-step generation, no approach successfully combines both properties. The key missing piece is a principled way to learn direct transport maps that maintain the modeling flexibility of iterative approaches while enabling efficient inference.

## 3. Problem Formulation

Let $p_0$ denote a simple source distribution (e.g., standard Gaussian) and $p_1$ denote the target data distribution. Our goal is to learn a transport map $T: \mathbb{R}^d \to \mathbb{R}^d$ such that if $X_0 \sim p_0$, then $T(X_0)$ has distribution $p_1$.

We parameterize this transport through a time-dependent velocity field $v_\theta(x, t)$ where $\theta$ represents learnable parameters. Given an initial point $x_0 \sim p_0$, we define the trajectory:

$$\frac{dx_t}{dt} = v_\theta(x_t, t), \quad x_0 \sim p_0$$

with the transport map given by $T(x_0) = x_1$ where $x_1$ is the solution at time $t=1$.

**Straight-Line Assumption.** The key insight of Rectified Flow is to encourage trajectories that follow straight lines. For any pair $(x_0, x_1)$ where $x_0 \sim p_0$ and $x_1 \sim p_1$, the straight-line path is:

$$x_t^* = (1-t)x_0 + tx_1, \quad t \in [0,1]$$

The corresponding velocity field is simply:
$$v^*(x_t, t) = x_1 - x_0$$

**Objective Function.** We train the velocity field to match these straight-line velocities. Given a coupling between $p_0$ and $p_1$ (which we discuss below), our training objective is:

$$\mathcal{L}(\theta) = \mathbb{E}_{(x_0,x_1) \sim \pi, t \sim \text{Uniform}[0,1]} \left[ \|v_\theta(x_t^*, t) - (x_1 - x_0)\|^2 \right]$$

where $\pi$ is a joint distribution over $(x_0, x_1)$ pairs and $x_t^* = (1-t)x_0 + tx_1$.

**Coupling Strategy.** A critical design choice is how to couple points between $p_0$ and $p_1$. We consider several strategies:
- **Independent coupling**: Sample $x_0 \sim p_0$ and $x_1 \sim p_1$ independently
- **Optimal transport coupling**: Use approximate optimal transport to find optimal pairings
- **Learned coupling**: Train an auxiliary network to predict optimal pairings

## 4. Methodology

### 4.1 Core Algorithm

The Rectified Flow training procedure is remarkably simple:

**Algorithm 1: Rectified Flow Training**
```
Input: Dataset D, source distribution p_0, coupling strategy π
Initialize: Neural network v_θ
for each training iteration do:
    Sample (x_0, x_1) ~ π
    Sample t ~ Uniform[0,1]
    Compute x_t = (1-t)x_0 + tx_1
    Compute target velocity: v_target = x_1 - x_0
    Update θ to minimize ||v_θ(x_t, t) - v_target||²
end
```

**Generation** requires only a single forward pass:
```
Input: Noise sample x_0 ~ p_0
Output: Generated sample x_1 = x_0 + v_θ(x_0, 0)
```

### 4.2 Network Architecture

We parameterize the velocity field $v_\theta(x, t)$ using a neural network that takes as input the current position $x$ and time $t$, and outputs a velocity vector of the same dimension as $x$.

For image generation, we use a U-Net architecture similar to diffusion models, with time embedding injected at multiple scales. The key difference is that our network predicts velocities rather than noise or denoised images.

**Time Embedding.** We encode time $t$ using sinusoidal embeddings and inject these throughout the network:
$$\text{embed}(t) = [\sin(2^0 \pi t), \cos(2^0 \pi t), \ldots, \sin(2^k \pi t), \cos(2^k \pi t)]$$

### 4.3 Coupling Strategies

**Independent Coupling.** The simplest approach samples source and target points independently. While this doesn't minimize transport cost, it's computationally efficient and often works well in practice.

**Minibatch Optimal Transport.** For better coupling, we solve optimal transport problems within minibatches using the Sinkhorn algorithm. This provides better pairings while remaining computationally tractable.

**Progressive Refinement.** We can iteratively improve the coupling by using the current model to transport points and then recomputing optimal pairings. This leads to progressively straighter trajectories.

### 4.4 Conditional Generation

For conditional generation, we modify the velocity field to take conditioning information $c$:
$$v_\theta(x, t, c) : \mathbb{R}^d \times [0,1] \times \mathcal{C} \to \mathbb{R}^d$$

The training objective becomes:
$$\mathcal{L}(\theta) = \mathbb{E}_{(x_0,x_1,c) \sim \pi, t} \left[ \|v_\theta(x_t^*, t, c) - (x_1 - x_0)\|^2 \right]$$

This naturally supports various conditioning modalities including class labels, text descriptions, and spatial conditioning.

## 5. Theoretical Analysis

### 5.1 Connection to Optimal Transport

Rectified Flow can be viewed as learning approximations to optimal transport maps with additional straight-line constraints. The Monge problem seeks a map $T$ minimizing:
$$\int \|x - T(x)\|^2 dp_0(x)$$

Our straight-line constraint enforces that $T(x_0) = x_0 + v_\theta(x_0, 0)$, providing a specific parameterization of transport maps.

**Proposition 1.** Under perfect training (zero loss), Rectified Flow learns a transport map that pushes $p_0$ to $p_1$.

*Proof Sketch:* If $v_\theta(x_t, t) = x_1 - x_0$ exactly for all coupled pairs, then following the ODE $dx/dt = v_\theta(x, t)$ from any $x_0 \sim p_0$ yields the corresponding $x_1$ from the coupling.

### 5.2 Approximation Quality

The quality of our approximation depends on how well straight lines approximate optimal transport paths.

**Proposition 2.** If the optimal transport map between $p_0$ and $p_1$ has straight-line structure (i.e., $T(x) = x + v$ for some constant $v$), then Rectified Flow recovers the optimal map exactly.

This holds for translations between Gaussian distributions and provides intuition for why the method works well when distributions are not too different.

### 5.3 Generalization Bounds

We can bound the generalization error in terms of the network capacity and the complexity of the true velocity field.

**Theorem 1.** With probability $1-\delta$, the population loss of a trained Rectified Flow model satisfies:
$$\mathcal{L}(\hat{\theta}) \leq \hat{\mathcal{L}}(\hat{\theta}) + O\left(\sqrt{\frac{\log(1/\delta) + \text{complexity}(\mathcal{F})}{n}}\right)$$

where $\hat{\mathcal{L}}$ is the empirical loss, $n$ is the training set size, and $\mathcal{F}$ is the function class.

### 5.4 Computational Complexity

**Training Complexity:** Each training step requires one forward pass through the velocity network, giving $O(|\theta|)$ complexity per step, where $|\theta|$ is the number of parameters.

**Generation Complexity:** Generation requires exactly one forward pass, giving $O(|\theta|)$ complexity per sample - dramatically more efficient than iterative methods.

## 6. Experimental Design

### 6.1 Datasets and Baselines

**Datasets:** We would evaluate on standard benchmarks including:
- CIFAR-10 and CIFAR-100 for controlled comparison
- CelebA-HQ and FFHQ for high-resolution face generation  
- ImageNet for large-scale natural image synthesis
- 2D synthetic datasets for visualization and analysis

**Baselines:** We would compare against:
- Diffusion models (DDPM, DDIM) with varying numbers of sampling steps
- Flow-based models (Glow, Flow++, Continuous Normalizing Flows)
- GANs (StyleGAN2, Progressive GAN)
- VAEs (β-VAE, VQ-VAE)
- Recent single-step methods (Consistency Models, Progressive Distillation)

### 6.2 Evaluation Metrics

**Sample Quality:**
- Fréchet Inception Distance (FID) for overall quality
- Inception Score (IS) for diversity and quality
- Precision and Recall to measure mode coverage vs. quality trade-offs
- LPIPS for perceptual similarity assessment

**Efficiency Metrics:**
- Wall-clock time for single sample generation
- GPU memory usage during inference
- Total FLOPs per generated sample
- Energy consumption measurements

**Distribution Matching:**
- Wasserstein distance estimates between generated and real distributions
- Maximum Mean Discrepancy (MMD) with various kernels
- Coverage metrics to detect mode collapse

### 6.3 Ablation Studies

**Coupling Strategy Ablation:**
- Compare independent vs. optimal transport coupling
- Evaluate progressive refinement strategies
- Analyze impact of minibatch size on coupling quality

**Architecture Ablation:**
- Study impact of network depth and width
- Compare different time embedding strategies
- Evaluate various normalization schemes

**Training Dynamics:**
- Analyze convergence properties with different learning rates
- Study impact of training time distribution (uniform vs. other)
- Evaluate curriculum learning strategies

### 6.4 Conditional Generation Experiments

**Class-Conditional Generation:**
- Evaluate on ImageNet with 1000 classes
- Measure class-conditional FID scores
- Analyze conditioning strength vs. sample diversity

**Text-to-Image Generation:**
- Implement conditioning on text embeddings
- Compare against diffusion-based text-to-image models
- Evaluate semantic alignment and text faithfulness

### 6.5 Scalability Analysis

**High-Resolution Generation:**
- Scale to 512×512 and 1024×1024 images
- Analyze memory and computational requirements
- Compare progressive vs. direct high-resolution training

**Large Dataset Training:**
- Evaluate training stability on large datasets
- Analyze data efficiency compared to baselines
- Study transfer learning capabilities

## 7. Discussion

### 7.1 Expected Strengths

**Computational Efficiency:** The single-step generation property makes Rectified Flow exceptionally efficient at inference time, enabling real-time applications that are impractical with iterative methods.

**Training Stability:** Unlike GANs, our approach avoids adversarial training dynamics, potentially leading to more stable and predictable training. The regression-based objective provides clear gradients throughout training.

**Theoretical Grounding:** The connection to optimal transport theory provides principled foundations and suggests natural extensions and improvements.

**Flexibility:** The framework naturally supports conditional generation and can be adapted to various data modalities without architectural constraints.

### 7.2 Expected Limitations

**Straight-Line Assumption:** The core assumption that straight lines provide good transport paths may not hold for all distribution pairs. Complex, multimodal distributions might require curved paths for optimal transport.

**Coupling Dependency:** The quality of results depends heavily on the coupling strategy between source and target distributions. Poor coupling could lead to suboptimal transport maps.

**Limited Theoretical Guarantees:** While we provide some theoretical analysis, the approximation quality for general distributions remains an open question.

**Potential Mode Collapse:** Without explicit diversity mechanisms, the model might fail to capture all modes of complex distributions.

### 7.3 Broader Impact

**Positive Impacts:**
- Enables real-time generative applications in creative tools and interactive systems
- Reduces computational requirements, making generative models more accessible
- Could accelerate scientific applications requiring fast generation (e.g., molecular design)

**Potential Concerns:**
- Efficient generation could exacerbate concerns about deepfakes and synthetic media
- Lower computational barriers might increase misuse of generative technology
- Need for responsible deployment and detection mechanisms

**Environmental Considerations:**
- Reduced inference costs could significantly decrease energy consumption for deployed generative models
- However, training costs remain substantial and require consideration

## 8. Conclusion

We have presented Rectified Flow, a novel generative modeling framework that learns straight-line trajectories between noise and data distributions. By explicitly encouraging direct transport paths during training, our approach achieves the efficiency of single-step generation while maintaining the modeling flexibility of iterative methods.

The key contributions include: (1) a simple yet effective training procedure based on velocity field regression, (2) theoretical connections to optimal transport theory, (3) natural extensions to conditional generation, and (4) computational efficiency that enables real-time applications.

**Open Questions and Future Work:**
- How can we better handle distributions where straight-line transport is suboptimal?
- Can we develop adaptive coupling strategies that improve automatically during training?
- What are the fundamental limits of single-step generation quality?
- How does the approach scale to very high-dimensional spaces and complex multimodal distributions?

Rectified Flow represents a step toward resolving the fundamental tension between generation quality and computational efficiency in generative modeling. While challenges remain, the approach opens new possibilities for practical generative applications and provides a foundation for future research in efficient generative modeling.

## References

[Note: As no specific references were provided, this section would typically include citations to the relevant literature mentioned throughout the paper, formatted as [Author, Year]. The actual paper would include full bibliographic information for works on diffusion models, flow-based models, optimal transport, and related generative modeling approaches.]
