# Reconstruction: full_freestyle
**Paper:** 2602.04770  
**Condition:** with_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Rectified Flow: Direct Generation Through Straight-Line Interpolation

**Abstract**

We present Rectified Flow, a novel approach to generative modeling that learns to map noise to data through straight-line trajectories in a single forward pass. Unlike existing methods that require iterative sampling procedures or adversarial training, our approach directly learns the optimal transport map between distributions by training a neural network to predict the straight-line path from noise to data. We show that this formulation naturally emerges from optimal transport theory and can be efficiently trained using a simple regression objective. Rectified Flow achieves high-quality generation in a single network evaluation while maintaining training stability and avoiding mode collapse. We demonstrate the effectiveness of our method on image generation tasks and show that it can be extended to conditional generation with flexible conditioning mechanisms.

## 1. Introduction

Generative modeling seeks to learn the underlying distribution of data and generate new samples from it. This fundamental problem in machine learning has seen remarkable progress through various paradigms, from variational autoencoders [Kingma & Welling, 2014] to generative adversarial networks [Goodfellow et al., 2014], and more recently, diffusion models [Ho et al., 2020] and normalizing flows [Rezende & Mohamed, 2015]. However, a persistent challenge remains: existing approaches often face a fundamental trade-off between generation quality and computational efficiency.

Current state-of-the-art methods like diffusion models achieve impressive sample quality but require hundreds or thousands of network evaluations during inference, making them computationally expensive for practical applications. Conversely, methods that generate samples in a single forward pass, such as GANs or VAEs, often struggle with training instability, mode collapse, or limited sample diversity.

This paper introduces **Rectified Flow**, a new generative modeling framework that addresses these limitations by learning to transform noise into data through straight-line trajectories. Our key insight is that the optimal transport map between a simple noise distribution and the target data distribution can be approximated by training a neural network to predict straight-line interpolations between paired noise and data samples.

The core idea is elegantly simple: given a noise sample $z_0$ and a data sample $x_1$ from the target distribution, we can define a straight-line path $x_t = (1-t)z_0 + tx_1$ for $t \in [0,1]$. By training a neural network $v_\theta(x_t, t)$ to predict the velocity field along these paths (i.e., $v_\theta(x_t, t) = x_1 - z_0$), we obtain a model that can generate high-quality samples in a single forward pass by solving the ordinary differential equation (ODE) $\frac{dx}{dt} = v_\theta(x_t, t)$ from $t=0$ to $t=1$.

Our main contributions are:

1. **Theoretical Foundation**: We establish the connection between straight-line interpolation and optimal transport, showing that rectified flows converge to the optimal transport map under mild conditions.

2. **Simple Training Objective**: We derive a straightforward regression loss that enables stable training without adversarial objectives or complex optimization procedures.

3. **Single-Step Generation**: Unlike iterative methods, rectified flow generates high-quality samples in a single network evaluation, making it computationally efficient.

4. **Empirical Validation**: We demonstrate that rectified flow achieves competitive results on standard image generation benchmarks while requiring significantly fewer computational resources than diffusion models.

5. **Conditional Extensions**: We show how the framework naturally extends to conditional generation with flexible conditioning mechanisms.

## 2. Background and Related Work

### 2.1 Generative Modeling Paradigms

Generative modeling has evolved through several major paradigms, each with distinct advantages and limitations. **Variational Autoencoders (VAEs)** [Kingma & Welling, 2014] learn a probabilistic encoder-decoder pair but often produce blurry samples due to the reconstruction loss. **Generative Adversarial Networks (GANs)** [Goodfellow et al., 2014] achieve sharp samples through adversarial training but suffer from training instability and mode collapse.

**Normalizing flows** [Rezende & Mohamed, 2015] learn invertible transformations between simple and complex distributions, enabling exact likelihood computation but requiring specialized architectures. **Diffusion models** [Ho et al., 2020; Song et al., 2021] have recently achieved state-of-the-art results by learning to reverse a noise corruption process, but require many sampling steps for high-quality generation.

### 2.2 Optimal Transport and Wasserstein Distance

Optimal transport theory provides a principled framework for measuring distances between probability distributions. Given two distributions $\mu$ and $\nu$, the Wasserstein-2 distance is defined as:

$$W_2(\mu, \nu) = \inf_{\gamma \in \Pi(\mu, \nu)} \left( \int_{\mathcal{X} \times \mathcal{Y}} \|x - y\|^2 d\gamma(x, y) \right)^{1/2}$$

where $\Pi(\mu, \nu)$ denotes the set of all joint distributions with marginals $\mu$ and $\nu$. The optimal coupling $\gamma^*$ that achieves this infimum defines a transport map that moves mass from $\mu$ to $\nu$ with minimal cost.

Recent work has explored connections between optimal transport and generative modeling. **Wasserstein GANs** [Arjovsky et al., 2017] use the Wasserstein distance as a more stable training objective. **Neural Optimal Transport** [Makkuva et al., 2020] learns transport maps using neural networks but requires solving a minimax optimization problem.

### 2.3 Flow-Based Models

Flow-based models learn invertible transformations between distributions. **Normalizing flows** require carefully designed architectures to maintain invertibility, limiting their expressiveness. **Continuous normalizing flows** [Chen et al., 2018] use neural ODEs to learn more flexible transformations but still require invertibility constraints.

Recent work on **flow matching** [Lipman et al., 2023] and **stochastic interpolants** [Albergo & Vanden-Eijnden, 2023] shares similarities with our approach but focuses on more complex interpolation schemes and stochastic processes. Our rectified flow framework differs by emphasizing the simplicity and efficiency of straight-line interpolation.

## 3. Rectified Flow

### 3.1 Motivation and Intuition

The key insight behind rectified flow is that we can learn a generative model by training a neural network to predict straight-line paths between noise and data. Consider a noise distribution $\pi_0$ (typically standard Gaussian) and a data distribution $\pi_1$. For any pair $(z_0, x_1)$ where $z_0 \sim \pi_0$ and $x_1 \sim \pi_1$, we can define a straight-line interpolation:

$$x_t = (1-t)z_0 + tx_1, \quad t \in [0,1]$$

The velocity along this path is constant: $\frac{dx_t}{dt} = x_1 - z_0$. If we can train a neural network $v_\theta(x_t, t)$ to predict this velocity field, then we can generate samples by solving the ODE:

$$\frac{dx}{dt} = v_\theta(x_t, t), \quad x(0) \sim \pi_0$$

The solution at $t=1$ will approximate samples from the data distribution $\pi_1$.

### 3.2 Theoretical Framework

We now formalize this intuition. Let $\pi_0$ and $\pi_1$ be probability measures on $\mathbb{R}^d$ representing the noise and data distributions, respectively. Define the **rectified flow** as the measure-valued curve $\{\pi_t\}_{t \in [0,1]}$ where $\pi_t$ is the pushforward of the straight-line interpolation.

**Definition 1** (Rectified Flow). Given distributions $\pi_0$ and $\pi_1$, the rectified flow is defined by the interpolation $x_t = (1-t)z_0 + tx_1$ where $(z_0, x_1) \sim \gamma$ for some coupling $\gamma \in \Pi(\pi_0, \pi_1)$.

The natural choice is the **independent coupling** where $z_0 \sim \pi_0$ and $x_1 \sim \pi_1$ are independent. This leads to the following velocity field:

$$v^*(x, t) = \mathbb{E}[x_1 - z_0 | x_t = x]$$

**Theorem 1** (Optimal Transport Connection). Under the independent coupling, the rectified flow with straight-line interpolation converges to the optimal transport map between $\pi_0$ and $\pi_1$ in the limit of infinite data.

*Proof Sketch*: The straight-line interpolation minimizes the kinetic energy of the transport, which is equivalent to finding the optimal transport map under the Wasserstein-2 metric. The independent coupling ensures that the learned velocity field approximates the gradient of the optimal transport potential.

### 3.3 Training Objective

To train a neural network $v_\theta(x, t)$ to approximate the true velocity field $v^*(x, t)$, we use a simple regression objective. Given training data $\{x_1^{(i)}\}_{i=1}^N$ sampled from the data distribution, we:

1. Sample noise $z_0^{(i)} \sim \pi_0$ (typically $\mathcal{N}(0, I)$)
2. Sample time $t^{(i)} \sim \text{Uniform}[0,1]$
3. Compute interpolation $x_t^{(i)} = (1-t^{(i)})z_0^{(i)} + t^{(i)}x_1^{(i)}$
4. Minimize the loss:

$$\mathcal{L}(\theta) = \mathbb{E}\left[\|v_\theta(x_t, t) - (x_1 - z_0)\|^2\right]$$

This objective is remarkably simple compared to adversarial training or variational bounds, yet it provably converges to the optimal transport map.

**Algorithm 1: Rectified Flow Training**
```
Input: Training data {x₁⁽ⁱ⁾}, neural network v_θ
for each training iteration do:
    Sample batch {x₁⁽ⁱ⁾} from data distribution
    Sample z₀⁽ⁱ⁾ ~ N(0, I) for each x₁⁽ⁱ⁾
    Sample t⁽ⁱ⁾ ~ Uniform[0,1] for each pair
    Compute x_t⁽ⁱ⁾ = (1-t⁽ⁱ⁾)z₀⁽ⁱ⁾ + t⁽ⁱ⁾x₁⁽ⁱ⁾
    Compute loss: L = ||v_θ(x_t⁽ⁱ⁾, t⁽ⁱ⁾) - (x₁⁽ⁱ⁾ - z₀⁽ⁱ⁾)||²
    Update θ using gradient descent
end for
```

### 3.4 Generation Process

Once trained, generation is straightforward: we solve the ODE starting from noise. For a single forward pass approximation, we can use Euler's method with a single step:

$$x_1 \approx z_0 + v_\theta(z_0, 0)$$

For higher quality, we can use more sophisticated ODE solvers, but even a single step often produces good results due to the straight-line nature of the learned trajectories.

**Algorithm 2: Rectified Flow Generation**
```
Input: Trained network v_θ, noise sample z₀ ~ N(0, I)
Option 1 (Single step): return z₀ + v_θ(z₀, 0)
Option 2 (Multi-step): 
    x₀ = z₀
    for t in [0, δt, 2δt, ..., 1-δt]:
        x_{t+δt} = x_t + δt * v_θ(x_t, t)
    return x₁
```

## 4. Properties and Analysis

### 4.1 Convergence Guarantees

We now analyze the theoretical properties of rectified flow. Our main result establishes convergence to the optimal transport map under mild conditions.

**Theorem 2** (Convergence to Optimal Transport). Assume $\pi_0$ and $\pi_1$ have finite second moments and the neural network $v_\theta$ has sufficient capacity. Then, as the number of training samples $N \to \infty$, the learned velocity field $v_\theta$ converges to the optimal transport map between $\pi_0$ and $\pi_1$.

The proof relies on the fact that the straight-line interpolation minimizes the kinetic energy among all possible transport paths, which is equivalent to optimal transport under the Wasserstein-2 metric.

### 4.2 Computational Complexity

Rectified flow offers significant computational advantages over existing methods:

- **Training**: Each iteration requires only forward passes and standard backpropagation, similar to supervised learning. No minimax optimization or iterative sampling.
- **Generation**: Single forward pass for approximate generation, or a few ODE steps for high quality. This contrasts with diffusion models that require hundreds of steps.
- **Memory**: No need to store intermediate states during generation, unlike autoregressive models.

### 4.3 Mode Coverage and Sample Diversity

Unlike GANs, rectified flow does not suffer from mode collapse because:

1. The training objective is a regression loss, not adversarial
2. Each noise sample is paired with a data sample, ensuring coverage
3. The straight-line interpolation preserves the diversity of the noise distribution

**Proposition 1** (Mode Coverage). If the noise distribution $\pi_0$ has full support on $\mathbb{R}^d$ and the neural network has sufficient capacity, then the generated distribution covers all modes of the data distribution $\pi_1$.

## 5. Extensions and Variants

### 5.1 Conditional Generation

Rectified flow naturally extends to conditional generation. Given conditioning information $c$, we modify the velocity field to $v_\theta(x, t, c)$ and train on conditional data pairs:

$$\mathcal{L}(\theta) = \mathbb{E}\left[\|v_\theta(x_t, t, c) - (x_1 - z_0)\|^2\right]$$

where $(x_1, c)$ are paired data and conditioning information.

### 5.2 Rectified Flow Refinement

We can iteratively improve the quality of rectified flow by training subsequent models on the generated samples. This "rectification" process makes the trajectories increasingly straight, improving generation quality.

**Algorithm 3: Rectified Flow Refinement**
```
Input: Initial model v₁, training data
for k = 1, 2, ..., K do:
    Generate synthetic data using v_k
    Train v_{k+1} using synthetic-real pairs
end for
```

### 5.3 Stochastic Rectified Flow

For applications requiring stochasticity, we can add noise to the ODE:

$$dx = v_\theta(x, t)dt + \sigma dW_t$$

where $W_t$ is a Wiener process and $\sigma$ controls the noise level. This provides a trade-off between deterministic transport and stochastic exploration.

## 6. Experimental Evaluation

We evaluate rectified flow on several image generation benchmarks, comparing against established methods in terms of sample quality, computational efficiency, and training stability.

### 6.1 Experimental Setup

**Datasets**: We experiment on CIFAR-10 (32×32 natural images), CelebA-HQ (256×256 faces), and ImageNet (256×256 natural images).

**Architecture**: We use U-Net architectures similar to those used in diffusion models, with time embedding and attention mechanisms. The network predicts the velocity vector at each pixel.

**Training Details**: We train using Adam optimizer with learning rate 1e-4, batch size 128, and standard data augmentation. Training typically converges within 100-200 epochs.

**Evaluation Metrics**: We measure sample quality using Fréchet Inception Distance (FID), Inception Score (IS), and visual inspection. We also measure computational efficiency in terms of network evaluations required for generation.

### 6.2 Sample Quality Results

Our experiments demonstrate that rectified flow achieves competitive sample quality with significantly improved computational efficiency:

**CIFAR-10**: Rectified flow achieves FID scores comparable to diffusion models (around 3-5) while requiring only 1-10 network evaluations compared to 100-1000 for diffusion models.

**CelebA-HQ**: Generated faces show good diversity and quality, with FID scores competitive with StyleGAN2 while avoiding the training instability issues of GANs.

**ImageNet**: On this challenging dataset, rectified flow produces coherent images with good mode coverage, though with slightly higher FID than state-of-the-art diffusion models.

### 6.3 Computational Efficiency

Rectified flow demonstrates substantial computational advantages:

- **Training Speed**: 2-3× faster training than diffusion models due to simpler objective
- **Generation Speed**: 10-100× faster generation than diffusion models
- **Memory Usage**: Constant memory during generation vs. linear growth for diffusion

### 6.4 Ablation Studies

We conduct ablation studies to understand the key components:

1. **Interpolation Scheme**: Straight-line interpolation outperforms more complex curves in both quality and efficiency
2. **Time Sampling**: Uniform sampling of time $t$ works best, though other schemes are possible
3. **Network Architecture**: Standard U-Net architectures work well, with attention improving quality on complex datasets
4. **ODE Solver**: Even single-step Euler method produces good results, with diminishing returns from more sophisticated solvers

### 6.5 Conditional Generation Results

For conditional generation experiments, we demonstrate:

- **Class-conditional ImageNet**: High-quality samples for each class with good intra-class diversity
- **Text-to-image**: Competitive results on caption-to-image generation tasks
- **Image-to-image**: Effective style transfer and image translation applications

## 7. Discussion and Limitations

### 7.1 Advantages

Rectified flow offers several key advantages over existing approaches:

1. **Simplicity**: The training objective is a straightforward regression loss, avoiding complex optimization procedures
2. **Efficiency**: Single-pass generation with optional multi-step refinement
3. **Stability**: No adversarial training or mode collapse issues
4. **Flexibility**: Easy extension to conditional generation and various applications
5. **Theoretical Grounding**: Strong connections to optimal transport theory

### 7.2 Limitations

Despite its advantages, rectified flow has some limitations:

1. **Sample Quality**: While competitive, it may not achieve the absolute best quality of state-of-the-art diffusion models on some datasets
2. **Straight-line Assumption**: The assumption that straight-line paths are optimal may not hold for all distributions
3. **Pairing**: The independent pairing of noise and data may not be optimal for all applications
4. **High-dimensional Challenges**: Like other methods, performance may degrade in very high-dimensional spaces

### 7.3 Future Directions

Several promising directions for future work include:

1. **Adaptive Interpolation**: Learning optimal interpolation paths rather than assuming straight lines
2. **Hierarchical Generation**: Applying rectified flow at multiple scales for improved quality
3. **Continuous Learning**: Adapting the model to new data without full retraining
4. **Theoretical Analysis**: Deeper understanding of convergence rates and optimality conditions

## 8. Conclusion

We have presented Rectified Flow, a novel approach to generative modeling that learns to map noise to data through straight-line trajectories. Our method addresses key limitations of existing approaches by providing:

- **Theoretical Foundation**: Strong connections to optimal transport theory ensure principled behavior
- **Practical Efficiency**: Single-pass generation with competitive quality
- **Training Simplicity**: Straightforward regression objective without adversarial training
- **Broad Applicability**: Natural extensions to conditional generation and various domains

The key insight that straight-line interpolation can effectively approximate optimal transport maps opens new possibilities for efficient generative modeling. While there remain challenges in achieving the absolute highest sample quality, the computational advantages and training stability make rectified flow an attractive alternative to existing methods.

Our experimental results demonstrate that rectified flow achieves competitive performance on standard benchmarks while requiring significantly fewer computational resources than iterative methods. The simplicity of the approach also makes it accessible for practical applications where computational efficiency is crucial.

As generative modeling continues to advance, we believe that the principles underlying rectified flow—direct transport learning through simple interpolation—will inspire further innovations in efficient, high-quality generation. The method's theoretical grounding in optimal transport theory provides a solid foundation for future developments, while its practical advantages make it immediately applicable to real-world problems.

The field of generative modeling has long sought methods that combine high sample quality with computational efficiency. Rectified flow represents a significant step toward this goal, demonstrating that simple, theoretically motivated approaches can compete with more complex alternatives while offering substantial practical advantages.

## References

[Albergo & Vanden-Eijnden, 2023] Albergo, M. S., & Vanden-Eijnden, E. (2023). Building normalizing flows with stochastic interpolants. *arXiv preprint arXiv:2209.15571*.

[Arjovsky et al., 2017] Arjovsky, M., Chintala, S., & Bottou, L. (2017). Wasserstein generative adversarial networks. *International Conference on Machine Learning*, 214-223.

[Chen et al., 2018] Chen, T. Q., Rubanova, Y., Bettencourt, J., & Duvenaud, D. K. (2018). Neural ordinary differential equations. *Advances in Neural Information Processing Systems*, 6571-6583.

[Goodfellow et al., 2014] Goodfellow, I., Pouget-Abadie, J., Mirza, M., Xu, B., Warde-Farley, D., Ozair, S., ... & Bengio, Y. (2014). Generative adversarial nets. *Advances in Neural Information Processing Systems*, 2672-2680.

[Ho et al., 2020] Ho, J., Jain, A., & Abbeel, P. (2020). Denoising diffusion probabilistic models. *Advances in Neural Information Processing Systems*, 6840-6851.

[Kingma & Welling, 2014] Kingma, D. P., & Welling, M. (2014). Auto-encoding variational bayes. *International Conference on Learning Representations*.

[Lipman et al., 2023] Lipman, Y., Chen, R. T., Ben-Hamu, H., Nickel, M., & Le, M. (2023). Flow matching for generative modeling. *International Conference on Learning Representations*.

[Makkuva et al., 2020] Makkuva, A., Taghvaei, A., Oh, S., & Lee, J. (2020). Optimal transport mapping via input convex neural networks. *International Conference on Machine Learning*, 6672-6681.

[Rezende & Mohamed, 2015] Rezende, D., & Mohamed, S. (2015). Variational inference with normalizing flows. *International Conference on Machine Learning*, 1530-1538.

[Song et al., 2021] Song, Y., Sohl-Dickstein, J., Kingma, D. P., Kumar, A., Ermon, S., & Poole, B. (2021). Score-based generative modeling through stochastic differential equations. *International Conference on Learning Representations*.

[Tibshirani et al., 2020] Tibshirani, R. J., Barber, R. F., Candès, E. J., & Ramdas, A. (2020). Conformal prediction under covariate shift. *Advances in Neural Information Processing Systems*, 2530-2540.
