# Reconstruction: abstract
**Paper:** 2602.04770  
**Condition:** no_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Abstract

Generative modeling faces a fundamental trade-off between generation quality and computational efficiency. While iterative approaches like diffusion models achieve high-quality synthesis through progressive refinement, they require multiple forward passes at inference time. Conversely, single-step methods like GANs offer fast generation but suffer from training instability and mode collapse. We propose **Flow-Guided Consistency Training (FGCT)**, a novel framework that combines the stability of continuous normalizing flows with consistency regularization to enable high-quality single-step generation.

Our approach trains a neural network to directly map noise to data by leveraging a pre-trained continuous normalizing flow as a teacher model. During training, we sample random timesteps along the flow's trajectory and enforce consistency: the student network's output from noise should match the flow's output at that timestep when both are evolved to the data distribution. This consistency loss, combined with a reconstruction objective, allows the student to distill the multi-step flow dynamics into a single forward pass while avoiding adversarial training altogether.

FGCT addresses key limitations of existing methods by providing stable training through the flow teacher, maintaining distribution coverage through consistency regularization, and achieving computational efficiency through single-step inference. The framework naturally extends to conditional generation by conditioning both teacher and student networks. We demonstrate that FGCT enables fast, high-quality synthesis across image, audio, and molecular domains while maintaining the theoretical guarantees of normalizing flows and eliminating the computational overhead of iterative generation.
