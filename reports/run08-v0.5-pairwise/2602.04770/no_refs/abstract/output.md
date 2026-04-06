# Reconstruction: abstract
**Paper:** 2602.04770  
**Condition:** no_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Flow Matching with Optimal Transport: Single-Step Generative Modeling via Continuous Normalizing Flows

Generative modeling faces a fundamental computational bottleneck: existing approaches either require expensive iterative sampling procedures or sacrifice sample quality for efficiency. Diffusion models achieve state-of-the-art results but demand hundreds of denoising steps, while GANs enable single-step generation but suffer from training instability and mode collapse. This creates a critical gap between sample quality and computational efficiency that limits the practical deployment of generative models.

We propose **Optimal Transport Flow Matching (OTFM)**, a novel framework that combines continuous normalizing flows with optimal transport theory to enable high-quality single-step generation. Our approach learns a time-dependent vector field that defines the optimal transport map between a simple prior distribution and the target data distribution. Unlike standard flow matching methods that rely on straight-line interpolation, OTFM leverages the Wasserstein-2 optimal transport plan to define curved trajectories that minimize transport cost while preserving probability mass.

The key innovation is a tractable training objective derived from the flow matching framework but regularized by optimal transport constraints. We parameterize the vector field using a neural network and train it to match both the instantaneous change in probability density and the optimal transport direction at each point along the trajectory. This eliminates the need for adversarial training while ensuring that the learned flow captures the full support of the target distribution.

Our approach naturally extends to conditional generation by incorporating conditioning information into the transport plan, enabling flexible control over sample generation. We expect OTFM to achieve competitive sample quality with diffusion models while requiring only a single forward pass, representing a significant advance in efficient generative modeling across diverse data modalities.
