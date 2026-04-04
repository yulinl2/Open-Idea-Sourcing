# Reconstruction: abstract
**Paper:** 2602.04770  
**Condition:** with_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Flow Matching with Distribution-Aware Training: A Single-Step Generative Framework

## Abstract

Current generative modeling approaches face a fundamental trade-off between generation quality and computational efficiency. While iterative methods like diffusion models achieve high-quality samples through multiple denoising steps, they impose significant computational overhead at inference time. Conversely, single-step methods often struggle to capture complex data distributions effectively. We propose **Flow Matching with Distribution-Aware Training (FM-DAT)**, a novel generative framework that learns direct mappings from noise to data distributions through a distribution-weighted training objective inspired by importance sampling principles.

Our approach leverages the insight that not all training samples contribute equally to learning the target distribution mapping. We introduce a dynamic weighting scheme that prioritizes training samples based on their local density and difficulty of generation, effectively focusing the model's capacity on the most informative regions of the data manifold. Specifically, we define importance weights using kernel density estimates of the data distribution and gradient magnitudes of a pre-trained score network, enabling the model to allocate learning capacity proportionally to local complexity.

The training objective combines standard flow matching losses with distribution-aware weights, encouraging the model to learn more accurate vector fields in high-density and high-curvature regions while maintaining global coverage. Unlike adversarial methods, our approach requires no discriminator and avoids mode collapse through explicit density-based regularization. The framework supports flexible conditional generation by incorporating conditioning variables into both the flow dynamics and the weighting scheme.

We demonstrate that FM-DAT achieves generation quality comparable to multi-step diffusion models while requiring only a single forward pass at inference time. The method scales effectively to high-resolution images and maintains stable training dynamics across different data modalities. Our distribution-aware weighting strategy provides a principled approach to handling the complexity of distribution-to-distribution learning without relegating computational burden to inference time, offering a promising direction for efficient high-quality generative modeling.
