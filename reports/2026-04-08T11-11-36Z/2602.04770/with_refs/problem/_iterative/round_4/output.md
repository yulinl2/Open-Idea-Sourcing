# Problem Formulation

## 2.1 Notation and Setup

Let $\mathcal{X} \subseteq \mathbb{R}^d$ denote the data space and $p_{\text{data}}$ be the unknown target distribution we wish to model. We consider a parametric generator $G_\theta: \mathcal{Z} \to \mathcal{X}$ with parameters $\theta \in \Theta$, where $\mathcal{Z} \subseteq \mathbb{R}^k$ is a latent space equipped with a fixed prior distribution $p_z$ (typically standard Gaussian).

For any generator $G_\theta$, define the **pushforward distribution** (or generated distribution) as:
$$p_\theta(x) := (G_\theta)_\# p_z(x) = \int_{\mathcal{Z}} p_z(z) \delta(x - G_\theta(z)) dz$$
where $\delta(\cdot)$ is the Dirac delta function and $(G_\theta)_\#$ denotes the pushforward operator.

During training, we observe the evolution of parameters through gradient-based optimization. Let $\theta_t$ denote the parameters at training step $t$, and consider the **distributional trajectory** $\{p_{\theta_t}\}_{t \geq 0}$ induced by the parameter updates. We seek to characterize and control the dynamics governing this distributional evolution.

## 2.2 Problem Statement

**Given:** 
- A dataset $\mathcal{D} = \{x_i\}_{i=1}^n$ sampled i.i.d. from $p_{\text{data}}$
- A generator architecture $G_\theta: \mathcal{Z} \to \mathcal{X}$
- A fixed latent prior $p_z$

**Find:** A training objective $\mathcal{L}(\theta)$ and corresponding parameter update rule that induces distributional dynamics with the following properties:

1. **Single-step generation:** At convergence, $G_{\theta^*}$ produces high-quality samples in one forward pass
2. **Distributional convergence:** $p_{\theta_t} \to p_{\text{data}}$ as $t \to \infty$ in an appropriate metric
3. **Symmetric equilibrium:** The dynamics admit a unique equilibrium characterized by balance between opposing forces
4. **Computational efficiency:** Training scales favorably compared to iterative generation methods

## 2.3 Distributional Dynamics Framework

We formulate the training process as governing the evolution of the entire generated distribution rather than individual samples. Define a **distributional velocity field** $v_t: \mathcal{P}(\mathcal{X}) \to T_{\mathcal{P}(\mathcal{X})}$ where $\mathcal{P}(\mathcal{X})$ is the space of probability measures on $\mathcal{X}$ and $T_{\mathcal{P}(\mathcal{X})}$ is its tangent space.

The distributional evolution follows:
$$\frac{d}{dt} p_{\theta_t} = v_t(p_{\theta_t})$$

We require $v_t$ to satisfy a **symmetry condition**: there exist opposing force terms $F^+_t(p)$ and $F^-_t(p)$ such that:
$$v_t(p) = F^+_t(p) - F^-_t(p)$$
where $F^+_t$ represents attraction toward $p_{\text{data}}$ and $F^-_t$ represents a regularizing force that prevents mode collapse.

## 2.4 Optimization Objective

Rather than directly optimizing distributional matching, we seek an objective $\mathcal{L}(\theta)$ that **indirectly** induces the desired distributional dynamics. The objective should decompose as:
$$\mathcal{L}(\theta) = \mathcal{L}_{\text{match}}(\theta) + \lambda \mathcal{L}_{\text{reg}}(\theta)$$

where:
- $\mathcal{L}_{\text{match}}(\theta)$ measures distributional discrepancy between $p_{\theta}$ and $p_{\text{data}}$
- $\mathcal{L}_{\text{reg}}(\theta)$ provides regularization to ensure proper equilibrium behavior
- $\lambda > 0$ is a balance parameter

The gradient updates $\theta_{t+1} = \theta_t - \eta \nabla_\theta \mathcal{L}(\theta_t)$ should induce the distributional velocity field satisfying our symmetry requirements.

## 2.5 Equilibrium Characterization

We require the dynamics to converge to a unique equilibrium $p^* = p_{\text{data}}$ characterized by:
$$v_t(p^*) = 0 \iff F^+_t(p^*) = F^-_t(p^*)$$

This balance condition ensures that at equilibrium, the attractive force toward the data distribution exactly balances the regularizing force, preventing both underfitting and mode collapse.

## 2.6 Technical Assumptions

**A1. Generator Expressivity:** The generator family $\{G_\theta : \theta \in \Theta\}$ is sufficiently expressive such that there exists $\theta^* \in \Theta$ with $p_{\theta^*} = p_{\text{data}}$.

**A2. Smooth Pushforward:** The mapping $\theta \mapsto p_\theta$ is differentiable in an appropriate sense (e.g., in the Wasserstein space), enabling well-defined distributional gradients.

**A3. Force Decomposition:** The velocity field admits the symmetric decomposition $v_t = F^+_t - F^-_t$ where both force terms are continuous and satisfy appropriate growth conditions.

**A4. Equilibrium Uniqueness:** The balance condition $F^+_t(p) = F^-_t(p)$ has a unique solution $p^* = p_{\text{data}}$ in the space of probability measures.

**A5. Convergence Regularity:** The parameter updates remain in a compact subset of $\Theta$ with probability 1, ensuring the distributional trajectory is well-defined.

## 2.7 Connection to Prior Work

Existing generative modeling approaches typically fall into several categories, each with limitations our formulation addresses:

**Adversarial Methods:** GANs optimize a minimax objective but lack explicit characterization of distributional evolution and suffer from training instability. Our symmetric force decomposition provides principled equilibrium analysis.

**Likelihood-based Models:** VAEs and normalizing flows optimize explicit likelihoods but often require architectural constraints or iterative sampling. Our approach targets direct distributional matching without likelihood computation.

**Iterative Refinement:** Diffusion models achieve high quality through multi-step denoising but require many function evaluations at inference. Our single-step generation requirement explicitly addresses this computational limitation.

**Score-based Methods:** Recent work on score matching provides distributional perspectives but typically requires iterative sampling procedures. Our formulation seeks to leverage distributional dynamics during training to enable direct single-step generation.

The key gap our formulation addresses is the lack of principled frameworks that explicitly model how the generated distribution evolves during training and leverage this evolution to achieve single-step, high-quality generation through symmetric equilibrium dynamics.