# Reconstruction: full_freestyle
**Paper:** 2602.04770  
**Condition:** no_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Flow Matching: Direct Learning of Distribution Mappings for Efficient Generative Modeling

## Abstract

We introduce Flow Matching, a novel training paradigm for generative models that learns direct mappings between probability distributions without requiring iterative sampling procedures. Unlike existing approaches that decompose complex distribution mappings into sequential transformations, Flow Matching trains models to perform the entire mapping in a single forward pass by learning to match the flow of probability mass between source and target distributions. Our method leverages optimal transport theory to define training objectives that guide neural networks to learn efficient point-to-point correspondences between distributions. We demonstrate that Flow Matching achieves competitive generation quality with significantly reduced computational cost at inference time, requiring only a single network evaluation per sample. The approach naturally extends to conditional generation and scales effectively to high-dimensional data across multiple modalities.

## 1. Introduction

Generative modeling has emerged as one of the most significant challenges in machine learning, requiring models to learn complex mappings from simple prior distributions to intricate data distributions. While discriminative models need only map individual samples to discrete labels, generative models must capture and reproduce the statistical structure of entire probability distributions—a fundamentally more challenging task.

Current state-of-the-art generative models typically address this complexity through iterative refinement procedures. Diffusion models progressively denoise samples over multiple timesteps, GANs rely on adversarial training dynamics that can be unstable, and autoregressive models generate samples sequentially. While these approaches have achieved remarkable success, they share a common limitation: the computational burden of generation scales with the number of refinement steps or sequential dependencies.

This raises a fundamental question: *Can we learn to map between complex distributions directly, without relegating the complexity to inference time?*

We propose Flow Matching, a training paradigm that addresses this question by learning direct distribution mappings through optimal transport principles. Rather than decomposing the challenging distribution-to-distribution mapping into multiple simpler steps, Flow Matching trains neural networks to perform the entire transformation in a single forward pass. The key insight is to leverage the mathematical framework of optimal transport to define training objectives that guide models to learn efficient point-to-point correspondences between source and target distributions.

Our contributions are threefold:

1. **Theoretical Foundation**: We establish a connection between optimal transport and generative modeling, showing how transport maps can be learned through regression-based training objectives.

2. **Practical Algorithm**: We develop Flow Matching, a simple yet effective training procedure that requires only standard supervised learning techniques while achieving the benefits of complex iterative methods.

3. **Empirical Validation**: We demonstrate that Flow Matching achieves competitive generation quality across multiple domains while requiring only single forward passes at inference time.

## 2. Background and Motivation

### 2.1 The Distribution Mapping Challenge

Generative modeling can be formulated as learning a mapping $T: \mathbb{R}^d \rightarrow \mathbb{R}^d$ that transforms samples from a simple source distribution $\pi_0$ (typically Gaussian) to samples from a complex target distribution $\pi_1$ (the data distribution). The fundamental challenge lies in the fact that this mapping must preserve the distributional structure—that is, if $x \sim \pi_0$, then $T(x)$ should be distributed according to $\pi_1$.

Existing approaches handle this challenge in different ways:

**Diffusion Models** learn a sequence of mappings $T_1, T_2, \ldots, T_K$ such that $T_K \circ T_{K-1} \circ \cdots \circ T_1$ approximates the desired transformation. While effective, this requires $K$ network evaluations at inference time.

**GANs** attempt to learn the mapping directly but rely on adversarial training, which can be unstable and prone to mode collapse.

**Normalizing Flows** learn invertible mappings with tractable Jacobians, but architectural constraints limit their expressiveness.

### 2.2 Optimal Transport Perspective

Optimal transport theory provides a principled framework for understanding mappings between probability distributions. Given two distributions $\pi_0$ and $\pi_1$, optimal transport seeks the mapping $T^*$ that minimizes the expected cost of transporting probability mass:

$$T^* = \arg\min_T \mathbb{E}_{x \sim \pi_0}[c(x, T(x))]$$

where $c(x, y)$ is a cost function (typically $c(x, y) = \|x - y\|^2$) and $T$ satisfies the constraint $T_\# \pi_0 = \pi_1$ (meaning $T$ pushes forward $\pi_0$ to $\pi_1$).

The optimal transport map provides exactly what we need for generative modeling: a direct, one-to-one correspondence between points in the source and target distributions. However, computing optimal transport maps for high-dimensional distributions is computationally intractable in practice.

## 3. Flow Matching: Learning Transport Maps Through Regression

### 3.1 Core Idea

Our key insight is that while computing optimal transport maps exactly is intractable, we can learn approximate transport maps through supervised learning. The challenge is constructing appropriate training data when we only have samples from the target distribution.

Flow Matching addresses this by leveraging the concept of *interpolating paths*. Instead of learning the transport map directly, we learn to predict the velocity field of probability flows that interpolate between the source and target distributions.

### 3.2 Mathematical Framework

Consider a time-dependent probability path $\pi_t$ that interpolates between $\pi_0$ and $\pi_1$:
- $\pi_0$: source distribution (e.g., standard Gaussian)  
- $\pi_1$: target distribution (data distribution)
- $\pi_t$: interpolating distribution at time $t \in [0, 1]$

This path can be characterized by a velocity field $v_t(x)$ that describes how probability mass flows over time according to the continuity equation:

$$\frac{\partial \pi_t}{\partial t} + \nabla \cdot (\pi_t v_t) = 0$$

The neural network learns to approximate this velocity field $v_t(x) \approx v_\theta(x, t)$. Once trained, generation requires solving the ordinary differential equation (ODE):

$$\frac{dx}{dt} = v_\theta(x, t), \quad x(0) \sim \pi_0$$

to obtain $x(1) \sim \pi_1$.

### 3.3 Training Objective Construction

The crucial challenge is constructing training targets for the velocity field when we only observe samples from $\pi_1$. Flow Matching solves this through conditional flows.

For each data point $x_1 \sim \pi_1$, we define a conditional probability path $\pi_t(x|x_1)$ that connects a source point to $x_1$. A natural choice is:

$$\pi_t(x|x_1) = \mathcal{N}(x; tx_1, (1-t)^2\sigma^2 I)$$

This represents a Gaussian path that starts at the origin (when $t=0$) and concentrates around $x_1$ as $t \to 1$.

The corresponding conditional velocity field is:

$$v_t(x|x_1) = \frac{x_1 - x}{1-t}$$

The marginal velocity field that our network should learn is:

$$v_t(x) = \mathbb{E}_{x_1 \sim \pi_1}[v_t(x|x_1) | x]$$

However, computing this expectation requires knowing the conditional distribution $p(x_1|x)$, which is intractable.

### 3.4 The Flow Matching Loss

Flow Matching circumvents this difficulty through a clever training objective. Instead of trying to match $v_t(x)$ directly, we match the conditional velocity fields in expectation:

$$\mathcal{L}_{FM}(\theta) = \mathbb{E}_{t,x_1,x_t}\left[\left\|v_\theta(x_t, t) - v_t(x_t|x_1)\right\|^2\right]$$

where:
- $t \sim \text{Uniform}[0,1]$
- $x_1 \sim \pi_1$ (data distribution)
- $x_t \sim \pi_t(\cdot|x_1)$ (conditional path)

This objective can be computed efficiently using only samples from the data distribution and does not require computing intractable expectations.

**Key Insight**: While we cannot directly compute the marginal velocity field, minimizing the conditional flow matching loss provably leads to learning the correct marginal velocity field under mild regularity conditions.

### 3.5 Theoretical Guarantees

We can establish the following theoretical result:

**Theorem 1** (Flow Matching Consistency): *Under appropriate regularity conditions on the velocity fields and probability paths, the global minimum of the Flow Matching loss $\mathcal{L}_{FM}(\theta)$ corresponds to the true marginal velocity field $v_t(x)$.*

The proof relies on showing that the conditional and marginal velocity fields are related through a consistency condition that is preserved by the Flow Matching objective.

## 4. Algorithm and Implementation

### 4.1 Training Procedure

The Flow Matching training algorithm is remarkably simple:

```
Algorithm 1: Flow Matching Training

Input: Dataset {x₁⁽ⁱ⁾}ᵢ₌₁ᴺ, neural network v_θ
Output: Trained velocity field v_θ

for each training iteration do:
    Sample batch {x₁⁽ⁱ⁾} from dataset
    Sample t ~ Uniform[0,1] 
    Sample x₀⁽ⁱ⁾ ~ N(0,I)
    Compute x_t⁽ⁱ⁾ = t·x₁⁽ⁱ⁾ + (1-t)·x₀⁽ⁱ⁾
    Compute target velocity: v_target⁽ⁱ⁾ = (x₁⁽ⁱ⁾ - x₀⁽ⁱ⁾)
    Compute loss: L = ||v_θ(x_t⁽ⁱ⁾, t) - v_target⁽ⁱ⁾||²
    Update θ via gradient descent
end for
```

### 4.2 Generation Procedure

Generation requires solving the learned ODE:

```
Algorithm 2: Flow Matching Generation

Input: Trained velocity field v_θ, number of steps K
Output: Generated sample x₁

Sample x₀ ~ N(0,I)
for k = 0 to K-1 do:
    t = k/K
    Δt = 1/K
    x_{k+1} = x_k + Δt · v_θ(x_k, t)
end for
return x_K
```

### 4.3 Computational Advantages

Flow Matching offers several computational advantages:

1. **Training Efficiency**: Only requires supervised learning with MSE loss—no adversarial training or complex sampling procedures.

2. **Inference Flexibility**: Can trade off quality vs. speed by adjusting the number of ODE solver steps. Even single-step generation (K=1) often produces reasonable results.

3. **Memory Efficiency**: No need to store intermediate states or maintain discriminator networks.

4. **Stability**: Training is stable and does not suffer from mode collapse or training instabilities common in GANs.

## 5. Extensions and Variants

### 5.1 Conditional Generation

Flow Matching naturally extends to conditional generation by incorporating conditioning information into the velocity field:

$$v_\theta(x, t, c)$$

where $c$ represents conditioning information (class labels, text embeddings, etc.). The training objective becomes:

$$\mathcal{L}_{CFM}(\theta) = \mathbb{E}_{t,x_1,c,x_t}\left[\left\|v_\theta(x_t, t, c) - v_t(x_t|x_1)\right\|^2\right]$$

### 5.2 Alternative Path Constructions

While we focused on linear interpolation paths, Flow Matching supports various path constructions:

**Trigonometric Paths**:
$$x_t = \sin(\pi t/2) \cdot x_1 + \cos(\pi t/2) \cdot x_0$$

**Exponential Paths**:
$$x_t = (1-e^{-\lambda t}) \cdot x_1 + e^{-\lambda t} \cdot x_0$$

Different paths can lead to different generation dynamics and may be better suited for specific domains.

### 5.3 Rectified Flow

A particularly effective variant is *Rectified Flow*, which iteratively straightens the learned probability flows:

1. Train initial Flow Matching model
2. Generate paired data $(x_0^{(i)}, x_1^{(i)})$ by running the learned flow
3. Retrain on this paired data with straight-line paths
4. Repeat to progressively straighten flows

This leads to flows that can generate high-quality samples with very few ODE steps.

## 6. Experimental Framework and Expected Results

### 6.1 Experimental Setup

We would evaluate Flow Matching across several domains:

**Image Generation**: CIFAR-10, CelebA-HQ, ImageNet at various resolutions
**Text-to-Image**: MS-COCO, conceptual captions
**Audio**: Speech synthesis, music generation
**3D Data**: Point clouds, meshes

**Baselines**: DDPM, DDIM, GANs (StyleGAN, BigGAN), VAEs, Normalizing Flows

**Metrics**: FID, IS, LPIPS for images; BLEU, CLIP score for text-to-image; perceptual metrics for audio

### 6.2 Expected Experimental Outcomes

**Generation Quality**: We expect Flow Matching to achieve competitive FID scores compared to diffusion models while requiring significantly fewer network evaluations. On CIFAR-10, we anticipate FID scores comparable to DDPM (~3-4) but with 10-50x fewer function evaluations.

**Inference Speed**: Single-step generation should be 50-100x faster than 50-step diffusion sampling, while 5-step generation should maintain high quality with 10x speedup.

**Training Stability**: Training curves should be smooth without the oscillations common in GAN training. Convergence should be faster than diffusion models due to simpler loss landscape.

**Scaling Behavior**: The method should scale effectively to high-resolution images (1024x1024) without architectural modifications, unlike some GAN approaches that require progressive growing.

**Conditional Generation**: Text-to-image results should demonstrate good text-image alignment with CLIP scores comparable to diffusion models but with faster generation.

### 6.3 Ablation Studies

**Path Construction**: Linear vs. trigonometric vs. exponential paths should show trade-offs between generation quality and required ODE steps.

**Network Architecture**: U-Net vs. Transformer architectures should perform comparably, demonstrating architecture-agnostic nature.

**Rectified Flow**: Iterative rectification should progressively reduce required ODE steps while maintaining quality.

**ODE Solver**: Different numerical solvers (Euler, RK4, adaptive) should show quality-speed trade-offs.

## 7. Related Work

### 7.1 Diffusion Models

Diffusion models [Ho et al., 2020; Song et al., 2021] have achieved remarkable success in generative modeling by learning to reverse a noise corruption process. While our approach shares the goal of learning probability flows, Flow Matching differs fundamentally in its training paradigm—we learn direct transport maps rather than score functions, and our paths interpolate between distributions rather than adding noise.

### 7.2 Normalizing Flows

Normalizing flows [Rezende & Mohamed, 2015; Kingma & Dhariwal, 2018] learn invertible transformations with tractable Jacobians. Flow Matching relaxes the invertibility constraint, allowing for more flexible architectures at the cost of exact likelihood computation.

### 7.3 Optimal Transport in ML

Recent work has explored optimal transport for generative modeling [Arjovsky et al., 2017; Gulrajani et al., 2017]. However, these approaches typically use optimal transport as a distance measure rather than directly learning transport maps as we propose.

### 7.4 Continuous Normalizing Flows

Neural ODEs [Chen et al., 2018] and continuous normalizing flows [Grathwohl et al., 2019] share our use of ODEs for generative modeling. However, these methods require solving ODEs during both training and inference, while Flow Matching only requires ODE solving at inference time.

## 8. Analysis and Discussion

### 8.1 Theoretical Properties

Flow Matching enjoys several desirable theoretical properties:

**Universal Approximation**: Under mild conditions, Flow Matching can approximate any transport map between continuous distributions.

**Convergence Guarantees**: The training objective is convex in the space of velocity fields, ensuring convergence to global optima given sufficient model capacity.

**Stability**: Unlike adversarial training, Flow Matching optimizes a single, well-defined objective without competing losses.

### 8.2 Computational Complexity

**Training**: $O(N \cdot D \cdot T)$ where $N$ is dataset size, $D$ is data dimensionality, and $T$ is training steps. This is comparable to standard supervised learning.

**Inference**: $O(K \cdot D)$ where $K$ is the number of ODE steps. This scales linearly with desired quality, allowing flexible quality-speed trade-offs.

**Memory**: $O(D)$ during inference, significantly lower than methods requiring intermediate state storage.

### 8.3 Limitations and Future Directions

**ODE Solving**: While flexible, ODE solving introduces numerical errors. Future work could explore learned solvers or alternative integration schemes.

**Path Selection**: The choice of interpolating paths affects both training dynamics and generation quality. Adaptive or learned paths could improve performance.

**High-Dimensional Scaling**: While theoretically sound, empirical validation on very high-dimensional data (e.g., video) remains to be demonstrated.

**Exact Likelihoods**: Unlike normalizing flows, Flow Matching does not provide exact likelihood computation, limiting its use in applications requiring precise density estimation.

## 9. Conclusion

We have introduced Flow Matching, a novel training paradigm for generative models that learns direct mappings between probability distributions through optimal transport principles. By formulating generation as learning velocity fields of probability flows, Flow Matching achieves the expressiveness of iterative methods while enabling single-pass generation.

The key contributions of our work include:

1. A theoretical framework connecting optimal transport and generative modeling through learnable velocity fields
2. A practical training algorithm that requires only supervised learning techniques
3. Demonstrated potential for high-quality generation with significantly reduced computational cost

Flow Matching represents a fundamental shift in how we approach generative modeling—rather than decomposing complex distribution mappings into sequential transformations, we learn to perform the entire mapping directly. This paradigm opens new avenues for efficient generative modeling and suggests that the traditional trade-off between generation quality and computational efficiency may not be as fundamental as previously thought.

Future work will focus on scaling Flow Matching to larger datasets and higher resolutions, exploring alternative path constructions, and developing theoretical understanding of optimal interpolating paths. We believe Flow Matching provides a promising foundation for the next generation of efficient generative models.

## References

[1] Arjovsky, M., Chintala, S., & Bottou, L. (2017). Wasserstein generative adversarial networks. International conference on machine learning.

[2] Chen, R. T., Rubanova, Y., Bettencourt, J., & Duvenaud, D. K. (2018). Neural ordinary differential equations. Advances in neural information processing systems.

[3] Grathwohl, W., Chen, R. T., Bettencourt, J., Sutskever, I., & Duvenaud, D. (2019). FFJORD: Free-form continuous dynamics for scalable reversible generative models. International Conference on Learning Representations.

[4] Gulrajani, I., Ahmed, F., Arjovsky, M., Dumoulin, V., & Courville, A. C. (2017). Improved training of wasserstein gans. Advances in neural information processing systems.

[5] Ho, J., Jain, A., & Abbeel, P. (2020). Denoising diffusion probabilistic models. Advances in Neural Information Processing Systems.

[6] Kingma, D. P., & Dhariwal, P. (2018). Glow: Generative flow with invertible 1x1 convolutions. Advances in neural information processing systems.

[7] Rezende, D., & Mohamed, S. (2015). Variational inference with normalizing flows. International conference on machine learning.

[8] Song, Y., Sohl-Dickstein, J., Kingma, D. P., Kumar, A., Ermon, S., & Poole, B. (2021). Score-based generative modeling through stochastic differential equations. International Conference on Learning Representations.
