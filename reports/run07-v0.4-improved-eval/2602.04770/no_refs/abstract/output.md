# Reconstruction: abstract
**Paper:** 2602.04770  
**Condition:** no_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Abstract

Generative modeling faces a fundamental trade-off between sample quality and computational efficiency. While diffusion models achieve state-of-the-art results through iterative denoising processes, they require hundreds of network evaluations at inference time. Conversely, single-step generators like GANs suffer from training instability and mode collapse. We propose **Rectified Flow Networks (RFNs)**, a novel generative modeling framework that learns to transform noise into data through a single neural ordinary differential equation (ODE) evaluation.

Our approach parameterizes the velocity field of a continuous-time normalizing flow using a neural network, but crucially employs a **rectified training objective** that encourages straight-line trajectories in the latent space. Specifically, we minimize the discrepancy between the learned velocity field and the optimal transport path connecting noise to data distributions. This rectification process naturally leads to flows that can be accurately simulated with a single Euler step, eliminating the need for iterative sampling while maintaining high sample quality.

RFNs offer several key advantages: (1) single-step generation with quality comparable to multi-step diffusion models, (2) stable training without adversarial objectives, (3) natural support for conditional generation through classifier-free guidance, and (4) theoretical guarantees on trajectory optimality. Our framework bridges the gap between the modeling flexibility of continuous normalizing flows and the efficiency requirements of practical applications, enabling high-quality generative modeling with minimal computational overhead at inference time.
