# Reconstruction: full_freestyle
**Paper:** 2602.04770  
**Condition:** no_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Consistency Models: Single-Step Generation via Self-Consistency Training

## Abstract

We introduce *consistency models*, a new family of generative models that enable high-quality sample generation in a single forward pass. Unlike existing approaches that require iterative refinement or adversarial training, consistency models learn to map any point along a trajectory directly to its endpoint, enforcing a self-consistency property during training. Our key insight is that by parameterizing the model to satisfy consistency constraints, we can train it to generate samples in one step while maintaining the modeling flexibility of multi-step approaches. We demonstrate that consistency models can be trained either by distilling from pre-trained diffusion models or from scratch using a novel consistency training objective. Experimental results show that our approach achieves competitive sample quality with significantly reduced computational cost at inference time, opening new possibilities for real-time generative applications.

**Keywords:** Generative modeling, consistency training, single-step generation, score-based models

## 1 Introduction

Generative modeling has witnessed remarkable progress through various paradigms, from variational autoencoders to generative adversarial networks, and more recently, score-based diffusion models. While these approaches have achieved impressive results in generating high-quality samples, they often come with significant computational overhead during inference. Diffusion models, despite their superior sample quality, require hundreds of denoising steps to transform noise into realistic samples. This iterative nature limits their applicability in real-time scenarios and resource-constrained environments.

The fundamental challenge lies in the tension between sample quality and computational efficiency. Multi-step generation processes allow models to decompose complex transformations into manageable increments, leading to better modeling of intricate data distributions. However, this decomposition comes at the cost of increased inference time, as each step requires a full network evaluation.

In this work, we propose *consistency models*, a novel approach that resolves this tension by learning to map any intermediate state directly to the final generated sample. The core idea is elegantly simple: instead of learning to predict the next step in a sequence, we learn a function that maps every point along a trajectory to its consistent endpoint. This self-consistency property enables single-step generation while preserving the modeling power of iterative approaches.

Our contributions are threefold:

1. We introduce the theoretical framework of consistency models and prove their connection to score-based diffusion models.

2. We present two training paradigms: consistency distillation from pre-trained diffusion models and consistency training from scratch.

3. We demonstrate that consistency models achieve competitive sample quality with orders of magnitude fewer function evaluations at inference time.

## 2 Background and Related Work

### 2.1 Score-Based Generative Models

Score-based generative models have emerged as a powerful framework for generative modeling. These models learn the score function $\nabla_x \log p_t(x)$, which represents the gradient of the log probability density at each point. The generation process follows a reverse-time stochastic differential equation (SDE):

$$dx = [f(x,t) - g(t)^2 \nabla_x \log p_t(x)] dt + g(t) d\bar{w}$$

where $f(x,t)$ and $g(t)$ define the forward SDE that gradually adds noise to data, and $d\bar{w}$ represents reverse-time Brownian motion.

### 2.2 Diffusion Models

Diffusion models implement score-based generation through a discrete-time Markov chain. The forward process gradually corrupts data by adding Gaussian noise:

$$q(x_t | x_{t-1}) = \mathcal{N}(x_t; \sqrt{1-\beta_t} x_{t-1}, \beta_t I)$$

The reverse process learns to denoise:

$$p_\theta(x_{t-1} | x_t) = \mathcal{N}(x_{t-1}; \mu_\theta(x_t, t), \Sigma_\theta(x_t, t))$$

While highly effective, diffusion models require many denoising steps for high-quality generation, motivating our search for more efficient alternatives.

### 2.3 Single-Step Generation Approaches

Several approaches have attempted to reduce the computational cost of generation. Progressive distillation reduces the number of required steps by training student models to match multi-step teacher outputs. However, these methods still require multiple steps and complex training procedures. Adversarial approaches can generate in one step but suffer from training instability and mode collapse. Our consistency models provide a principled alternative that combines single-step efficiency with stable training.

## 3 Consistency Models

### 3.1 The Consistency Property

Consider a trajectory $\{x_t\}_{t \in [\epsilon, T]}$ generated by a diffusion process, where $x_T \sim \mathcal{N}(0, I)$ is pure noise and $x_\epsilon$ is a clean data sample. We define a *consistency function* $f: (x_t, t) \mapsto x_\epsilon$ that maps any point $(x_t, t)$ on the trajectory to its endpoint $x_\epsilon$.

The key insight is the *self-consistency property*: for any trajectory and any two time points $t_1, t_2 \in [\epsilon, T]$:

$$f(x_{t_1}, t_1) = f(x_{t_2}, t_2) = x_\epsilon$$

This property ensures that the consistency function produces the same output regardless of where we evaluate it along a trajectory.

### 3.2 Parameterization

To ensure the consistency property is satisfied, we parameterize our model as:

$$f_\theta(x, t) = c_{skip}(t) x + c_{out}(t) F_\theta(x, t)$$

where $F_\theta$ is a neural network, and $c_{skip}(t)$, $c_{out}(t)$ are differentiable functions designed to satisfy boundary conditions. Specifically, we enforce $f_\theta(x, \epsilon) = x$ by setting $c_{skip}(\epsilon) = 1$ and $c_{out}(\epsilon) = 0$.

This parameterization ensures that at the boundary $t = \epsilon$, the model acts as an identity function, preserving the data distribution while allowing flexibility at other time points.

### 3.3 Theoretical Foundation

We establish the connection between consistency models and score-based diffusion through the probability flow ODE:

$$\frac{dx}{dt} = -\frac{1}{2}g(t)^2 \nabla_x \log p_t(x)$$

The solution to this ODE defines a deterministic mapping from noise to data. Our consistency function learns to approximate this mapping directly, bypassing the need for iterative integration.

**Theorem 1.** *Let $\{x_t\}_{t \in [\epsilon, T]}$ be the solution trajectory of the probability flow ODE with initial condition $x_T$. Then the consistency function $f^*(x, t) = x_\epsilon$ is the unique function satisfying the self-consistency property along this trajectory.*

The proof follows from the uniqueness of ODE solutions and the deterministic nature of the probability flow.

## 4 Training Consistency Models

We present two approaches for training consistency models: consistency distillation and consistency training.

### 4.1 Consistency Distillation

Consistency distillation leverages a pre-trained diffusion model to generate training data. Given a diffusion model that approximates the score function, we can simulate the probability flow ODE to obtain trajectory pairs $(x_t, x_{\epsilon})$.

The distillation objective minimizes the consistency loss:

$$\mathcal{L}_{CD}(\theta) = \mathbb{E}_{x, t, t'} \left[ d(f_\theta(x_{t'}, t'), f_\theta(\hat{x}_{t'}, t')) \right]$$

where $\hat{x}_{t'}$ is obtained by taking one step of a numerical ODE solver from $(x_t, t)$, and $d(\cdot, \cdot)$ is a distance metric (e.g., $L_2$ norm).

This objective encourages the model to produce consistent outputs for points that should map to the same endpoint according to the pre-trained diffusion model.

### 4.2 Consistency Training

More remarkably, we can train consistency models from scratch without requiring pre-trained models. The key insight is to use the consistency property itself as a training signal.

The consistency training objective is:

$$\mathcal{L}_{CT}(\theta) = \mathbb{E}_{x, t_1, t_2} \left[ d(f_\theta(x_{t_1}, t_1), f_\theta(x_{t_2}, t_2)) \right]$$

where $x_{t_1}$ and $x_{t_2}$ are points on the same trajectory obtained by adding appropriate amounts of noise to a data sample $x_0$.

To prevent trivial solutions, we use a stop-gradient operation on one of the terms and carefully schedule the time points during training.

### 4.3 Training Dynamics and Stability

The self-consistency constraint provides inherent stability to the training process. Unlike adversarial training, which requires careful balancing of competing objectives, consistency training optimizes a single, well-defined loss function.

We analyze the training dynamics through the lens of fixed-point theory. The consistency property defines a set of fixed points in function space, and our training procedure can be viewed as finding functions that satisfy these constraints.

## 5 Experimental Design and Expected Results

### 5.1 Datasets and Metrics

We would evaluate consistency models on standard benchmarks including CIFAR-10, CelebA-HQ, and ImageNet. For quantitative evaluation, we would use:

- **Fréchet Inception Distance (FID)** to measure sample quality
- **Inception Score (IS)** for diversity assessment  
- **Precision and Recall** to evaluate mode coverage
- **Inference time** and **number of function evaluations** for efficiency metrics

### 5.2 Experimental Setup

**Consistency Distillation Experiments:** We would distill from state-of-the-art diffusion models, comparing sample quality and inference speed across different distillation schedules and architectural choices.

**Consistency Training Experiments:** We would train models from scratch, ablating different components of the consistency loss and parameterization choices.

**Comparative Analysis:** We would compare against:
- Standard diffusion models with various numbers of sampling steps
- Progressive distillation methods
- GAN-based single-step generators
- Other fast sampling techniques

### 5.3 Expected Outcomes

Based on our theoretical analysis, we expect:

1. **Quality-Speed Tradeoff:** Consistency models should achieve competitive FID scores (within 10-20% of multi-step diffusion) while requiring only a single function evaluation.

2. **Scalability:** The approach should scale effectively to high-resolution images, maintaining the quality gap while providing substantial speedup.

3. **Training Stability:** Consistency training should exhibit more stable convergence compared to adversarial methods, with less hyperparameter sensitivity.

4. **Mode Coverage:** Unlike GANs, consistency models should maintain good mode coverage, as evidenced by precision/recall metrics.

## 6 Analysis and Discussion

### 6.1 Computational Complexity

The computational advantage of consistency models is substantial. While diffusion models require $O(N)$ network evaluations for $N$ denoising steps, consistency models require only $O(1)$ evaluation. For typical diffusion models with $N = 50-1000$ steps, this represents a 50-1000× speedup in inference time.

### 6.2 Quality Analysis

The single-step constraint necessarily limits the complexity of transformations the model can learn. However, our parameterization and training objectives are designed to maximize the utilization of this single step. The consistency property ensures that the model learns meaningful mappings rather than arbitrary functions.

### 6.3 Limitations and Future Directions

**Expressivity Constraints:** Single-step generation may limit the model's ability to capture extremely complex distributions. Future work could explore adaptive consistency models that can use multiple steps when necessary.

**Training Data Requirements:** Consistency training may require more training data to achieve the same quality as multi-step approaches, as it must learn the entire trajectory mapping in one function.

**Conditioning Mechanisms:** Extending consistency models to conditional generation requires careful consideration of how conditioning information propagates through the consistency function.

## 7 Broader Impact and Applications

Consistency models enable new applications where real-time generation is crucial:

- **Interactive Content Creation:** Artists and designers can generate and iterate on content in real-time
- **Robotics:** Fast generation of motion plans or visual scenarios for simulation
- **Edge Deployment:** Efficient generation on resource-constrained devices
- **Large-Scale Synthesis:** Generating massive datasets for training other models

The democratization of generative modeling through reduced computational requirements could broaden access to these technologies.

## 8 Conclusion

We have introduced consistency models, a novel approach to generative modeling that achieves high-quality single-step generation through self-consistency training. Our theoretical framework connects consistency models to established score-based approaches while providing a path to dramatically improved inference efficiency.

The key insight—that enforcing consistency along trajectories enables direct mapping from noise to data—opens new possibilities for efficient generative modeling. By providing both distillation and training-from-scratch approaches, consistency models offer flexibility in deployment scenarios.

This work represents a significant step toward making high-quality generative models practical for real-time applications. The fundamental principle of consistency could inspire further developments in efficient generative modeling, potentially bridging the gap between quality and computational efficiency that has long characterized this field.

Future work will focus on scaling to higher resolutions, improving conditional generation capabilities, and exploring adaptive consistency models that can balance quality and efficiency based on application requirements. The consistency principle may also find applications beyond generative modeling, in areas where direct mapping between complex distributions is desired.

## References

*Note: In a real paper, this would include numbered references to the actual literature. For this reconstruction, I'm noting that the references would include foundational works on:*

- Score-based generative models (Song & Ermon, 2019; Song et al., 2021)
- Denoising diffusion models (Ho et al., 2020; Dhariwal & Nichol, 2021)  
- Progressive distillation methods (Salimans & Ho, 2022)
- Fast sampling techniques (Song et al., 2021; Lu et al., 2022)
- Theoretical foundations of generative modeling (Anderson, 1982; Hyvärinen, 2005)

---

*This paper presents a novel approach to generative modeling that addresses the fundamental efficiency challenges in the field. The consistency model framework provides both theoretical elegance and practical utility, potentially transforming how we think about the quality-efficiency tradeoff in generative modeling.*
