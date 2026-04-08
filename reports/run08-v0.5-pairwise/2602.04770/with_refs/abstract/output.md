# Reconstruction: abstract
**Paper:** 2602.04770  
**Condition:** with_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Conformal Flow Networks: Single-Step Generative Modeling with Distribution-Free Guarantees

## Abstract

Current generative models face a fundamental trade-off between sample quality and computational efficiency, with high-quality methods requiring multiple iterative refinement steps at inference time. We propose **Conformal Flow Networks (CFNs)**, a novel generative modeling framework that produces high-quality samples in a single forward pass while providing distribution-free coverage guarantees for the generated samples. Our approach builds upon conformal prediction theory, extending weighted conformal inference beyond covariate shift to the generative setting where we must learn mappings between entire distributions.

CFNs employ a neural transport network that directly maps from a simple base distribution to the target data distribution, trained using a novel **conformal consistency loss** that ensures the generated samples conform to the empirical data distribution with probabilistic guarantees. We introduce a weighted exchangeability framework for generative modeling, where training samples are reweighted according to their conformity scores, enabling the network to focus on hard-to-generate regions while maintaining global distribution coverage. The key innovation is a **conformal calibration mechanism** that dynamically adjusts the transport mapping during training to satisfy coverage constraints, eliminating the need for adversarial training or iterative sampling procedures.

Our method provides theoretical guarantees that generated samples lie within conformal prediction sets of the true data distribution with user-specified probability, addressing mode collapse by ensuring diverse sample generation across the entire support. CFNs scale efficiently to high-dimensional data and support flexible conditional generation through covariate-aware conformal weighting. Unlike existing approaches that require multiple network evaluations or complex training dynamics, CFNs achieve competitive sample quality through a single deterministic forward pass while offering unprecedented reliability guarantees for generative modeling applications requiring certified sample validity.
