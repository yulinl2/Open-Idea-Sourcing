# Reconstruction: abstract (iterative, 5 rounds)
**Paper:** 2602.04770  
**Condition:** with_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  
**Rounds:** 5  
**Best round:** 4 (score 3.4)  
**Converged:** True (reached max rounds (5))  
**Score trajectory:** 2.8 -> 2.8 -> 2.8 -> 3.4 -> 3.2  

---

# Distribution Matching via Iterative Sample Attraction

## Abstract

Current generative modeling approaches face a fundamental trade-off between generation quality and computational efficiency, requiring either iterative refinement during inference or adversarial training with discriminative components. We propose **Iterative Sample Attraction (ISA)**, a novel training paradigm that learns to map between distributions through direct pairwise interactions between generated and real samples, eliminating the need for iterative inference or discriminative signals. Our approach formulates generative learning as a discrete dynamical system where, at each training iteration, generated samples are explicitly moved toward real samples through weighted attraction forces computed via kernel-based similarity measures. The key insight is that the iterative nature inherent in neural network training can be leveraged to evolve the output distribution: rather than performing iterative refinement at inference time, we perform iterative distribution alignment during training itself.

Specifically, ISA computes movement vectors for each generated sample based on its weighted interactions with all real samples in the current batch, where weights are determined by anti-symmetric kernel functions that ensure swapping data and generated distributions reverses movement direction. The training objective minimizes the expected movement magnitude, naturally defining an equilibrium condition where sample movement stops when distributions align. This formulation requires no discriminator, supports flexible conditional generation through kernel conditioning, and produces high-quality samples in a single forward pass once trained.

Our approach addresses key limitations of existing methods: it avoids mode collapse through explicit full-distribution coverage, scales to high-resolution data through efficient pairwise computations, and provides a principled training objective with theoretical convergence guarantees. The method is modality-agnostic and can be trained from scratch without requiring pre-trained models. By moving the computational complexity from inference to training, ISA enables efficient generation while maintaining the modeling capacity of more complex iterative approaches.
