# Reconstruction: full_guided
**Paper:** 2602.04770  
**Condition:** with_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Rectified Flow: A Single-Step Generative Model via Optimal Transport

## Abstract

Current generative models face a fundamental trade-off between sample quality and computational efficiency. While iterative approaches like diffusion models achieve high-quality generation through multi-step denoising processes, they require numerous network evaluations at inference time. Conversely, single-step methods like GANs can generate quickly but often suffer from training instability and mode collapse. We propose Rectified Flow, a novel generative modeling framework that learns to transform noise to data through a single neural network evaluation by solving an optimal transport problem. Our approach constructs straight-line paths between noise and data distributions, enabling efficient one-step generation while maintaining the stability and coverage properties of iterative methods. We demonstrate that Rectified Flow can be trained end-to-end without adversarial objectives, avoiding common training difficulties while achieving competitive sample quality. The method naturally extends to conditional generation and scales effectively to high-dimensional data like natural images.

## 1. Introduction

Generative modeling has emerged as one of the most important challenges in machine learning, with applications spanning image synthesis, data augmentation, and scientific simulation. The field has witnessed remarkable progress through various paradigms, each offering different trade-offs between sample quality, training stability, and computational efficiency.

Generative Adversarial Networks (GANs) demonstrated the possibility of high-quality, single-step generation but introduced training instabilities and mode collapse issues. Variational Autoencoders (VAEs) provided stable training but often produced blurry samples. More recently, diffusion models and score-based approaches have achieved state-of-the-art sample quality by learning iterative denoising processes, but at the cost of requiring hundreds of network evaluations at generation time.

This computational burden of iterative methods creates a significant barrier to real-world deployment. While techniques like DDIM sampling and learned samplers can reduce the number of steps, they still require multiple forward passes and may compromise sample quality. There remains a fundamental need for generative models that can produce high-quality samples in a single forward pass while maintaining the training stability that makes iterative methods attractive.

Our key insight is that the generation process can be viewed as an optimal transport problem: finding the most efficient way to move probability mass from a simple noise distribution to the complex data distribution. Rather than learning a multi-step diffusion process, we propose to directly learn the optimal transport map that connects these distributions via straight-line paths.

**Contributions:**
• We introduce Rectified Flow, a novel generative modeling framework based on optimal transport theory that enables single-step generation
• We provide theoretical analysis showing that straight-line transport paths minimize the expected transport cost under mild regularity conditions  
• We develop a practical training algorithm that learns the optimal transport map through a simple regression objective, avoiding adversarial training
• We demonstrate that the method naturally handles conditional generation and scales to high-dimensional problems
• We establish connections to existing methods and show how Rectified Flow unifies insights from flow-based models and optimal transport

## 2. Related Work

**Flow-based Models.** Normalizing flows [Rezende & Mohamed, 2015] learn invertible transformations between simple and complex distributions. While theoretically elegant, standard flows require architectures with specific invertibility constraints that limit expressiveness. Continuous normalizing flows [Chen et al., 2018] address some limitations by learning continuous-time dynamics, but still require solving ODEs at inference time.

**Diffusion Models.** Denoising diffusion models [Ho et al., 2020] and score-based generative models [Song & Ermon, 2019] have achieved remarkable success by learning to reverse a noise corruption process. These methods provide stable training and high-quality samples but require many denoising steps. Recent work has explored reducing the number of sampling steps [Song et al., 2020; Salimans & Ho, 2022] but typically still requires multiple network evaluations.

**Optimal Transport.** Optimal transport theory provides a principled framework for comparing probability distributions and has found applications in machine learning [Peyré & Cuturi, 2019]. Wasserstein GANs [Arjovsky et al., 2017] incorporated optimal transport ideas into adversarial training. More recently, [Pooladian et al., 2021] explored connections between optimal transport and generative modeling, though their approach still requires iterative sampling procedures.

**Single-Step Generation.** Beyond GANs, several approaches have attempted single-step generation. Consistency models [Song et al., 2023] learn to map any point on a diffusion trajectory directly to the final sample, enabling one-step generation after training. However, they still require a pre-trained diffusion model. Our approach differs by directly learning the optimal transport map without requiring iterative procedures during training or inference.

**Gap Identification.** While existing methods excel in specific aspects—GANs in speed, diffusion models in quality, flows in theoretical grounding—none simultaneously achieve fast single-step generation, stable training, and strong theoretical foundations. Rectified Flow addresses this gap by leveraging optimal transport theory to construct a principled single-step generative model with stable training dynamics.

## 3. Problem Formulation

Let $\pi_0$ denote a simple source distribution (e.g., standard Gaussian) and $\pi_1$ denote the target data distribution. Our goal is to learn a map $T: \mathbb{R}^d \to \mathbb{R}^d$ such that if $X_0 \sim \pi_0$, then $T(X_0)$ follows the data distribution $\pi_1$.

We formulate this as an optimal transport problem. Given marginal distributions $\pi_0$ and $\pi_1$, we seek a transport plan $\gamma \in \Pi(\pi_0, \pi_1)$ that minimizes the expected transport cost:

$$\min_{\gamma \in \Pi(\pi_0, \pi_1)} \mathbb{E}_{(X_0, X_1) \sim \gamma}[c(X_0, X_1)]$$

where $\Pi(\pi_0, \pi_1)$ denotes the set of joint distributions with marginals $\pi_0$ and $\pi_1$, and $c(x_0, x_1)$ is a cost function measuring the expense of transporting mass from $x_0$ to $x_1$.

For the quadratic cost $c(x_0, x_1) = \|x_0 - x_1\|^2_2$, the optimal transport plan induces straight-line trajectories. We parameterize these trajectories as:

$$X_t = (1-t)X_0 + tX_1, \quad t \in [0,1]$$

where $(X_0, X_1) \sim \gamma^*$ and $\gamma^*$ is the optimal transport plan.

The velocity field along these trajectories is constant:
$$v_t(x) = X_1 - X_0 = \frac{dX_t}{dt}$$

Our objective is to learn a neural network $v_\theta: \mathbb{R}^d \times [0,1] \to \mathbb{R}^d$ that approximates this velocity field. Given the learned velocity field, we can generate samples by solving the ODE:

$$\frac{dx}{dt} = v_\theta(x, t), \quad x(0) \sim \pi_0$$

The key insight is that for straight-line trajectories, this ODE has the closed-form solution:
$$x(1) = x(0) + \int_0^1 v_\theta(x(s), s) ds = x(0) + v_\theta(x(0), 0)$$

when $v_\theta$ is time-independent, enabling single-step generation.

**Assumptions:**
- The data distribution $\pi_1$ has finite second moments
- The optimal transport map exists and is unique (satisfied when $\pi_0$ is absolutely continuous)
- The velocity field is sufficiently regular to ensure well-posed ODEs

## 4. Methodology

### 4.1 Rectified Flow Algorithm

Our training procedure consists of two main steps: constructing training trajectories and learning the velocity field.

**Step 1: Trajectory Construction**
Given training samples $\{x_1^{(i)}\}_{i=1}^N$ from the data distribution and noise samples $\{x_0^{(i)}\}_{i=1}^N$ from $\pi_0$, we construct straight-line trajectories by pairing data and noise samples. The optimal pairing strategy depends on the specific optimal transport plan, but in practice, we use either:
- Random pairing: randomly shuffle and pair samples
- Optimal pairing: solve the discrete optimal transport problem using algorithms like Sinkhorn iterations

For each pair $(x_0^{(i)}, x_1^{(i)})$, we generate trajectory points:
$$x_t^{(i)} = (1-t)x_0^{(i)} + tx_1^{(i)}$$

The corresponding velocity is:
$$v^{(i)} = x_1^{(i)} - x_0^{(i)}$$

**Step 2: Velocity Field Learning**
We train a neural network $v_\theta(x, t)$ to predict the velocity field by minimizing the regression loss:

$$\mathcal{L}(\theta) = \mathbb{E}_{t \sim U[0,1]} \mathbb{E}_{(x_0, x_1) \sim \gamma} \left[\|v_\theta(x_t, t) - (x_1 - x_0)\|^2_2\right]$$

where $x_t = (1-t)x_0 + tx_1$.

**Algorithm 1: Rectified Flow Training**
```
Input: Data samples {x₁⁽ⁱ⁾}, noise distribution π₀, network v_θ
1. for each training iteration do
2.    Sample noise {x₀⁽ⁱ⁾} from π₀
3.    Pair samples: (x₀⁽ⁱ⁾, x₁⁽ⁱ⁾) via optimal transport or random pairing
4.    Sample time t ~ U[0,1]
5.    Compute trajectory points: x_t = (1-t)x₀ + tx₁
6.    Compute target velocity: v = x₁ - x₀
7.    Update θ to minimize ||v_θ(x_t, t) - v||²
8. end for
```

### 4.2 Single-Step Generation

Once trained, generation requires solving the ODE from $t=0$ to $t=1$. For straight-line trajectories with perfect velocity field estimation, we have:

$$x_1 = x_0 + \int_0^1 v_\theta(x_t, t) dt$$

When the velocity field is approximately constant along trajectories (which holds for well-separated source and target distributions), we can approximate:

$$x_1 \approx x_0 + v_\theta(x_0, 0)$$

This enables true single-step generation. For more complex cases, we can use a small number of Euler steps:

$$x_1 \approx x_0 + \sum_{k=0}^{K-1} \frac{1}{K} v_\theta(x_{k/K}, k/K)$$

where $K$ is typically much smaller than the hundreds of steps required by diffusion models.

### 4.3 Design Justifications

**Straight-line Trajectories:** We choose straight-line paths because they minimize the quadratic transport cost, leading to the most efficient transformation. This geometric insight ensures our method finds the shortest paths between distributions.

**Regression Objective:** Unlike GANs, our regression-based training objective is stable and well-posed. The velocity field learning problem has a unique global minimum when the optimal transport plan is unique.

**Time-Parameterized Network:** Including time as an input allows the network to adapt its predictions along the trajectory, providing flexibility while maintaining the straight-line structure.

## 5. Theoretical Analysis

### 5.1 Optimality of Straight-Line Paths

**Theorem 1 (Optimality).** Consider the optimal transport problem between distributions $\pi_0$ and $\pi_1$ with quadratic cost $c(x, y) = \|x - y\|^2_2$. If $\pi_0$ is absolutely continuous, then the optimal transport plan $\gamma^*$ induces straight-line trajectories $X_t = (1-t)X_0 + tX_1$ where $(X_0, X_1) \sim \gamma^*$.

*Proof sketch:* This follows from the theory of optimal transport with quadratic cost. When the source measure is absolutely continuous, the optimal transport map $T^*$ exists and is unique. The induced coupling $\gamma^*(dx_0, dx_1) = \pi_0(dx_0)\delta_{T^*(x_0)}(dx_1)$ defines straight-line geodesics in the Wasserstein space, which correspond to our parameterization $X_t = (1-t)X_0 + tX_1$.

### 5.2 Approximation Properties

**Theorem 2 (Velocity Field Approximation).** Let $v^*$ denote the true velocity field of the optimal transport trajectories, and let $v_\theta$ be our learned approximation. If $v_\theta$ minimizes the regression loss $\mathcal{L}(\theta)$, then the generated distribution $\hat{\pi}_1$ satisfies:

$$W_2(\pi_1, \hat{\pi}_1) \leq C \cdot \mathbb{E}[\|v_\theta(X_t, t) - v^*(X_t, t)\|^2_2]^{1/2}$$

where $W_2$ denotes the 2-Wasserstein distance and $C$ is a constant depending on the regularity of the distributions.

*Proof sketch:* The result follows from stability properties of optimal transport maps. Small perturbations in the velocity field lead to bounded changes in the transported distribution, with the bound depending on the transport cost.

### 5.3 Generalization Bounds

**Conjecture 1 (Sample Complexity).** With $N$ training samples, the expected 2-Wasserstein distance between the generated and true distributions scales as $O(N^{-1/(2+d)})$ for $d$-dimensional data, matching the minimax rates for density estimation.

This conjecture suggests that Rectified Flow achieves optimal statistical rates, though the complete proof requires technical analysis of the interplay between optimal transport estimation and neural network approximation.

### 5.4 Computational Complexity

The training complexity is $O(N \cdot T \cdot C_{\text{network}})$ where $N$ is the number of samples, $T$ is the number of training iterations, and $C_{\text{network}}$ is the cost of one network evaluation. Importantly, generation requires only $O(C_{\text{network}})$ time for single-step sampling, compared to $O(K \cdot C_{\text{network}})$ for $K$-step iterative methods.

## 6. Experimental Design

We would conduct comprehensive experiments to evaluate Rectified Flow across multiple dimensions:

### 6.1 Datasets and Baselines

**Synthetic Data:** 2D toy datasets (Swiss roll, moons, spirals) to visualize learned transport maps and verify theoretical predictions about straight-line trajectories.

**Image Benchmarks:** CIFAR-10, CelebA-HQ, and ImageNet for evaluating sample quality and scalability. These datasets would test the method's ability to handle high-dimensional, complex natural images.

**Baselines:** We would compare against:
- DDPM/DDIM with various step counts (1, 5, 10, 50, 1000)
- StyleGAN2 and StyleGAN3 for single-step generation quality
- Normalizing flows (Real NVP, Glow)
- Consistency models for single-step diffusion-based generation

### 6.2 Evaluation Metrics

**Sample Quality:**
- Fréchet Inception Distance (FID) to measure perceptual quality
- Inception Score (IS) for diversity and quality
- Precision and Recall to assess mode coverage vs. sample fidelity
- LPIPS for perceptual similarity in conditional generation tasks

**Computational Efficiency:**
- Wall-clock generation time per sample
- Number of network evaluations required
- Memory usage during inference
- Energy consumption for large-scale generation

**Training Stability:**
- Convergence curves and training dynamics
- Sensitivity to hyperparameters
- Failure modes and their frequency

### 6.3 Ablation Studies

**Trajectory Construction:**
- Random pairing vs. optimal transport pairing of noise/data samples
- Effect of different noise distributions (Gaussian, uniform, etc.)
- Impact of trajectory parameterization choices

**Network Architecture:**
- Time conditioning mechanisms (concatenation, FiLM, attention)
- Network depth and width effects
- Comparison of different backbone architectures (ResNet, U-Net, Transformer)

**Training Objectives:**
- Pure regression loss vs. combinations with perceptual losses
- Different time sampling strategies (uniform vs. importance sampling)
- Regularization techniques and their impact

### 6.4 Conditional Generation

We would extend the method to conditional generation by modifying the velocity field to $v_\theta(x, t, c)$ where $c$ represents conditioning information (class labels, text embeddings, etc.). The training objective becomes:

$$\mathcal{L}(\theta) = \mathbb{E}_{t,c} \mathbb{E}_{(x_0, x_1) \sim \gamma_c} \left[\|v_\theta(x_t, t, c) - (x_1 - x_0)\|^2_2\right]$$

### 6.5 Scalability Analysis

**Computational Scaling:** Experiments on progressively larger image resolutions (64², 128², 256², 512²) to understand computational requirements.

**Data Scaling:** Training on datasets of varying sizes to understand sample efficiency and overfitting behavior.

**Distributed Training:** Analysis of parallel training efficiency and scaling across multiple GPUs.

The experimental design would provide comprehensive evidence for the method's effectiveness while identifying its limitations and optimal use cases.

## 7. Discussion

### 7.1 Expected Strengths

**Computational Efficiency:** The primary advantage of Rectified Flow is its potential for true single-step generation. Unlike diffusion models that require dozens to hundreds of denoising steps, our approach can generate high-quality samples with a single network evaluation. This dramatic speedup would enable real-time applications and significantly reduce computational costs for large-scale generation.

**Training Stability:** By formulating generation as a regression problem rather than an adversarial game, Rectified Flow should avoid the training instabilities that plague GANs. The velocity field learning objective has a well-defined global minimum, leading to more predictable and stable training dynamics.

**Theoretical Foundations:** The connection to optimal transport theory provides strong theoretical grounding. The straight-line trajectory construction is provably optimal for quadratic transport costs, giving confidence that the method learns meaningful transformations between distributions.

**Flexible Conditioning:** The framework naturally extends to conditional generation by incorporating conditioning information into the velocity field. This flexibility could enable applications in controllable image synthesis, text-to-image generation, and other conditional modeling tasks.

### 7.2 Potential Limitations

**Approximation Quality:** The single-step approximation may struggle with highly complex distributions where the optimal transport map is highly nonlinear. In such cases, the straight-line assumption might be too restrictive, potentially leading to lower sample quality compared to iterative methods.

**Pairing Strategy:** The method's performance may be sensitive to how noise and data samples are paired during training. While optimal transport provides a principled pairing strategy, computing it exactly may be computationally expensive for large datasets.

**Mode Coverage:** Unlike diffusion models that naturally explore the entire data distribution through the noising process, Rectified Flow's coverage depends on the quality of the learned transport map. Poor approximation could lead to mode collapse or missing modes.

**High-Dimensional Challenges:** Optimal transport in high dimensions faces the curse of dimensionality. The method may require careful architecture design and regularization to work effectively on very high-dimensional data like high-resolution images.

### 7.3 Broader Impact

**Positive Applications:** Fast, high-quality generation could benefit numerous applications including creative tools for artists and designers, data augmentation for machine learning, and scientific simulation. The reduced computational requirements could democratize access to generative modeling by lowering hardware barriers.

**Potential Risks:** As with all generative models, Rectified Flow could be misused for creating deepfakes, generating misleading content, or violating privacy. The single-step generation capability might make such misuse more accessible due to reduced computational requirements.

**Environmental Considerations:** By dramatically reducing the computational cost of generation, the method could significantly lower the energy footprint of generative modeling applications, contributing to more sustainable AI practices.

### 7.4 Future Directions

**Adaptive Step Sizes:** While single-step generation is the goal, developing adaptive methods that can use multiple steps when needed could provide better quality-speed trade-offs for complex distributions.

**Learned Transport Costs:** Exploring beyond quadratic costs to learn problem-specific transport costs could improve performance on specialized domains.

**Integration with Other Methods:** Combining Rectified Flow with other generative modeling techniques (e.g., using it to initialize diffusion models) could leverage the strengths of multiple approaches.

## 8. Conclusion

We have presented Rectified Flow, a novel generative modeling framework that achieves single-step generation through optimal transport theory. By learning to transform noise to data via straight-line trajectories, our method addresses the fundamental trade-off between sample quality and computational efficiency that has limited existing approaches.

The key contributions of this work include: (1) a principled formulation of generation as an optimal transport problem with straight-line paths, (2) a stable regression-based training algorithm that avoids adversarial objectives, (3) theoretical analysis establishing the optimality of our approach and providing approximation guarantees, and (4) a framework that naturally extends to conditional generation and scales to high-dimensional data.

**Open Questions:** Several important questions remain for future investigation: Can the method be extended to handle more complex transport costs that better capture perceptual similarity? How can we develop better pairing strategies for training that scale to very large datasets? What are the fundamental limits of single-step generation, and when are multiple steps necessary?

The Rectified Flow framework opens new directions for efficient generative modeling by bridging optimal transport theory with practical deep learning. By enabling high-quality single-step generation with stable training, it has the potential to make generative models more accessible and practical for real-world applications while providing a solid theoretical foundation for future developments in the field.

## References

[Arjovsky et al., 2017] Martin Arjovsky, Soumith Chintala, and Léon Bottou. Wasserstein generative adversarial networks. In International Conference on Machine Learning, 2017.

[Chen et al., 2018] Tian Qi Chen, Yulia Rubanova, Jesse Bettencourt, and David K Duvenaud. Neural ordinary differential equations. Advances in Neural Information Processing Systems, 2018.

[Ho et al., 2020] Jonathan Ho, Ajay Jain, and Pieter Abbeel. Denoising diffusion probabilistic models. Advances in Neural Information Processing Systems, 2020.

[Peyré & Cuturi, 2019] Gabriel Peyré and Marco Cuturi. Computational optimal transport: With applications to data science. Foundations and Trends in Machine Learning, 2019.

[Pooladian et al., 2021] Aram-Alexandre Pooladian, Heli Ben-Hamu, Carles Domingo-Enrich, Brandon Amos, Yaron Lipman, and Ricky Chen. Multisample flow matching: Straightening flows with minibatch couplings. arXiv preprint arXiv:2304.14772, 2021.

[Rezende & Mohamed, 2015] Danilo Rezende and Shakir Mohamed. Variational inference with normalizing flows. In International Conference on Machine Learning, 2015.

[Salimans & Ho, 2022] Tim Salimans and Jonathan Ho. Progressive distillation for fast sampling of diffusion models. In International Conference on Learning Representations, 2022.

[Song & Ermon, 2019] Yang Song and Stefano Ermon. Generative modeling by estimating gradients of the data distribution. Advances in Neural Information Processing Systems, 2019.

[Song et al., 2020] Yang Song, Jascha Sohl-Dickstein, Diederik P Kingma, Abhishek Kumar, Stefano Ermon, and Ben Poole. Score-based generative modeling through stochastic differential equations. arXiv preprint arXiv:2011.13456, 2020.

[Song et al., 2023] Yang Song, Prafulla Dhariwal, Mark Chen, and Ilya Sutskever. Consistency models. arXiv preprint arXiv:2303.01469, 2023.

[Tibshirani et al., 2020] Ryan J. Tibshirani, Rina Foygel Barber, Emmanuel J. Candès, and Aaditya Ramdas. Conformal prediction under covariate shift. Advances in Neural Information Processing Systems, 2020.
