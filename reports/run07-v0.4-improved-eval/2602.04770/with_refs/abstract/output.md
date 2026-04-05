# Reconstruction: abstract
**Paper:** 2602.04770  
**Condition:** with_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Flow Rectified Transport: Single-Step High-Quality Generation via Optimal Transport Flows

## Abstract

Current generative modeling approaches face a fundamental trade-off between sample quality and computational efficiency. While diffusion models achieve high-quality generation through iterative denoising processes, they require hundreds of network evaluations at inference time. Conversely, single-step methods like GANs suffer from mode collapse and training instability. We introduce Flow Rectified Transport (FRT), a novel generative modeling framework that combines the theoretical rigor of optimal transport with the efficiency of normalizing flows to enable high-quality sample generation in a single forward pass.

Our approach learns a rectified transport map between a simple source distribution (e.g., Gaussian noise) and the target data distribution by decomposing the optimal transport problem into a sequence of simpler flow-based transformations. Unlike traditional flow models that require invertible architectures, FRT employs a rectification mechanism that progressively corrects transport errors through a series of non-invertible neural networks, each optimized to minimize the Wasserstein distance to intermediate target distributions. The key insight is that by learning multiple rectified transport steps during training—but collapsing them into a single composite map at inference—we can achieve the modeling flexibility of iterative methods while maintaining single-step generation efficiency.

FRT addresses several critical limitations of existing approaches: it avoids the adversarial training dynamics that plague GANs, eliminates the computational overhead of iterative sampling in diffusion models, and naturally handles high-dimensional data without architectural constraints. Our framework supports flexible conditioning mechanisms and scales efficiently with data dimensionality. The rectified transport formulation provides theoretical guarantees on distribution matching while the flow-based parameterization ensures stable training dynamics. We expect FRT to enable practical high-quality generation for real-time applications while maintaining the theoretical foundations necessary for reliable performance across diverse domains.
