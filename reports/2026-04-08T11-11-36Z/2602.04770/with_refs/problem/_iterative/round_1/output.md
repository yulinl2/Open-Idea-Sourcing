# Problem Formulation

## 2.1 Notation and Setup

Let $\mathcal{X}$ and $\mathcal{Y}$ denote the input and output spaces, respectively, where $\mathcal{X} \subseteq \mathbb{R}^d$ and $\mathcal{Y} \subseteq \mathbb{R}^k$. We consider probability distributions $P_{\text{source}}$ and $P_{\text{target}}$ defined on $\mathcal{X} \times \mathcal{Y}$, representing source and target distributions respectively. Let $\mu_{\text{source}}$ and $\mu_{\text{target}}$ denote the marginal distributions on $\mathcal{X}$ induced by $P_{\text{source}}$ and $P_{\text{target}}$.

For a generative model, we define a neural network $G_\theta: \mathcal{Z} \times \mathcal{X} \to \mathcal{Y}$ parameterized by $\theta$, where $\mathcal{Z} \subseteq \mathbb{R}^m$ is a latent noise space. Given a noise distribution $\pi$ on $\mathcal{Z}$ (typically standard Gaussian) and conditioning variable $x \in \mathcal{X}$, the model generates samples via $y = G_\theta(z, x)$ where $z \sim \pi$.

Let $P_{\theta}(y|x)$ denote the distribution induced by the generative model:
$$P_{\theta}(y|x) = \int_{\mathcal{Z}} \delta(y - G_\theta(z, x)) \pi(z) dz$$
where $\delta(\cdot)$ is the Dirac delta function.

## 2.2 Problem Statement

**Given:** 
- Training dataset $\mathcal{D}_{\text{source}} = \{(x_i, y_i)\}_{i=1}^n$ drawn i.i.d. from $P_{\text{source}}$
- Target marginal distribution $\mu_{\text{target}}$ on $\mathcal{X}$ (or samples from it)
- Conditional distribution relationship: $P_{\text{target}}(y|x) = P_{\text{source}}(y|x)$ for all $x \in \mathcal{X}$

**Find:** Parameters $\theta^*$ such that the generative model $G_{\theta^*}$ produces samples from the target distribution $P_{\text{target}}$ in a single forward pass, i.e., for $(x,y) \sim P_{\text{target}}$:
$$G_{\theta^*}(z, x) \stackrel{d}{=} y \quad \text{where } z \sim \pi$$

**Constraint:** The generation process must require only one forward evaluation of $G_{\theta^*}$, without iterative refinement procedures.

## 2.3 Optimization Objective

We formulate the learning objective as a weighted distribution matching problem. Define the likelihood ratio $w(x) = \frac{d\mu_{\text{target}}}{d\mu_{\text{source}}}(x)$ when $\mu_{\text{target}}$ is absolutely continuous with respect to $\mu_{\text{source}}$.

The primary objective seeks to minimize the weighted discrepancy between the model distribution and source distribution:
$$\mathcal{L}(\theta) = \mathbb{E}_{x \sim \mu_{\text{source}}} \left[ w(x) \cdot D\left(P_{\text{source}}(y|x), P_\theta(y|x)\right) \right]$$

where $D(\cdot, \cdot)$ is a suitable divergence measure between probability distributions.

For practical implementation with finite samples, we approximate this as:
$$\hat{\mathcal{L}}(\theta) = \frac{1}{n} \sum_{i=1}^n w(x_i) \cdot \ell(y_i, G_\theta(z_i, x_i))$$

where $z_i \sim \pi$ are i.i.d. noise samples, and $\ell(\cdot, \cdot)$ is a suitable loss function (e.g., $\ell_2$ loss for continuous outputs, cross-entropy for discrete outputs).

The optimization problem becomes:
$$\theta^* = \arg\min_\theta \hat{\mathcal{L}}(\theta) + \lambda R(\theta)$$

where $R(\theta)$ is a regularization term and $\lambda \geq 0$ is a regularization parameter.

## 2.4 Technical Assumptions

**A1 (Covariate Shift).** The conditional distributions are identical across source and target: $P_{\text{target}}(y|x) = P_{\text{source}}(y|x)$ for all $x \in \mathcal{X}$. This assumption is standard in domain adaptation and ensures that the relationship between inputs and outputs remains consistent, with only the input distribution changing.

**A2 (Absolute Continuity).** The target marginal $\mu_{\text{target}}$ is absolutely continuous with respect to the source marginal $\mu_{\text{source}}$, i.e., $\mu_{\text{target}} \ll \mu_{\text{source}}$. This ensures the likelihood ratio $w(x) = \frac{d\mu_{\text{target}}}{d\mu_{\text{source}}}(x)$ exists almost everywhere.

**A3 (Bounded Likelihood Ratio).** There exist constants $0 < c_{\min} \leq c_{\max} < \infty$ such that $c_{\min} \leq w(x) \leq c_{\max}$ for $\mu_{\text{source}}$-almost all $x \in \mathcal{X}$. This prevents extreme reweighting that could lead to optimization instability.

**A4 (Universal Approximation).** The function class $\{G_\theta : \theta \in \Theta\}$ has sufficient capacity to approximate the optimal mapping, i.e., there exists $\theta^* \in \Theta$ such that $P_{\theta^*}(y|x) = P_{\text{source}}(y|x)$ for all $x \in \mathcal{X}$.

**A5 (Noise Distribution).** The noise distribution $\pi$ has sufficient support and regularity (e.g., standard Gaussian) to enable generation of diverse outputs through the deterministic mapping $G_\theta$.

## 2.5 Connection to Prior Work

Traditional generative models operate under the assumption of identical source and target distributions, limiting their applicability when deployment conditions differ from training. Iterative approaches like diffusion models \cite{ho2020denoising} and autoregressive models achieve high quality but require multiple forward passes, violating our single-step constraint.

Adversarial methods \cite{goodfellow2014generative} can theoretically achieve single-step generation but suffer from training instability and mode collapse, particularly problematic under distribution shift. Variational approaches \cite{kingma2013auto} provide stable training but typically require distributional assumptions that may not hold under covariate shift.

Our formulation extends recent work on conformal prediction under covariate shift \cite{tibshirani2019conformal}, which demonstrates how likelihood ratio weighting can maintain statistical guarantees when training and test distributions differ. However, while conformal prediction addresses uncertainty quantification, our problem requires learning the underlying generative mapping itself.

The key innovation in our formulation is the integration of importance weighting—well-established in domain adaptation—with single-step generative modeling. This bridges the gap between distribution-shift-aware learning and efficient generation, addressing limitations of existing approaches that either ignore distribution shift or require computationally expensive iterative procedures.

Unlike prior work that treats covariate shift and generative modeling as separate challenges, our unified formulation enables principled single-step generation that is robust to distribution shift by design, opening new possibilities for efficient deployment of generative models in non-stationary environments.