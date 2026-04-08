# Reconstruction Dispatch Summary

**Run:** run07-v0.4-improved-eval
**Version:** v0.4.0 (improved eval rubric, anti-leakage prompt)
**Student model:** claude-sonnet-4-20250514
**Teacher model:** claude-opus-4-20250514

## Paper: 2006.06138 — Lei-Candes (conformal inference)

| Mode | with_refs | no_refs | delta |
|------|-----------|---------|-------|
| abstract | 3.0 | 3.0 | +0.0 |
| mindmap | 3.4 | 3.2 | +0.2 |
| problem | 3.2 | 3.0 | +0.2 |
| problem_method | 3.2 | 3.0 | +0.2 |
| full_guided | 3.2 | 3.2 | +0.0 |
| full_freestyle | 3.2 | 3.2 | +0.0 |
| **AVERAGE** | | | **+0.10** |

### Novelty gaps (2006.06138)

**with_refs:**

- **abstract**: The original paper's core mechanism is conformal quantile regression (CQR) that takes arbitrary conditional quantile est
- **mindmap**: The paper's key insight is to apply weighted conformal inference directly to the counterfactual inference problem, treat
- **problem**: The paper's core innovation is applying weighted conformal inference to construct intervals for COUNTERFACTUALS (the uno
- **problem_method**: The paper's core mechanism is counterfactual inference on Y(1) and Y(0) separately using weighted split-CQR with propens
- **full_guided**: The original paper's core contribution is using weighted conformal inference to construct prediction intervals directly 
- **full_freestyle**: The original paper's core mechanism is recognizing that counterfactual inference reduces to a covariate shift problem wh

**no_refs:**

- **abstract**: The original paper's core contribution is weighted conformal inference for counterfactual prediction that handles covari
- **mindmap**: The paper's core contribution is applying WEIGHTED conformal inference to handle covariate shift between treated/control
- **problem**: The paper's core contribution is applying weighted conformal inference to construct prediction intervals for individual 
- **problem_method**: The original paper's key contribution is applying weighted conformal quantile regression (CQR) to construct prediction i
- **full_guided**: The original paper's core contribution is weighted conformal quantile regression (CQR) that achieves doubly robust cover
- **full_freestyle**: The original paper's core contribution is weighted conformal inference that: (1) handles covariate shifts between treatm

## Paper: 2602.04770 — Deng et al (generative modeling)

| Mode | with_refs | no_refs | delta |
|------|-----------|---------|-------|
| abstract | 3.4 | 3.4 | +0.0 |
| mindmap | 3.4 | 3.4 | +0.0 |
| problem | 3.4 | 3.8 | -0.4 |
| problem_method | 3.8 | 3.4 | +0.4 |
| full_guided | 4.0 | 3.8 | +0.2 |
| full_freestyle | 3.8 | 3.8 | +0.0 |
| **AVERAGE** | | | **+0.03** |

### Novelty gaps (2602.04770)

**with_refs:**

- **abstract**: The paper's key innovation is the drifting field concept where samples evolve during training iterations through attract
- **mindmap**: The paper's key insight is using a drifting field that governs sample movement during training iterations, creating an e
- **problem**: The paper's key insight is modeling generation as a training-time evolution of the pushforward distribution through a dr
- **problem_method**: The paper's key innovation is the drifting field V_p,q that governs sample movement during training time, with attractio
- **full_guided**: The paper's core insight is a drifting field V(x) = V+_p(x) - V-_q(x) that uses kernel-based attraction from data sample
- **full_freestyle**: The original paper's key innovation is a drifting field based on kernel-weighted attraction to data samples and repulsio

**no_refs:**

- **abstract**: The actual paper introduces a 'drifting field' that evolves the pushforward distribution during training time through at
- **mindmap**: The paper's key innovation is a drifting field V that governs sample movement during training through attraction to data
- **problem**: The paper's key innovation is the concept of 'drifting' - evolving the pushforward distribution during training time thr
- **problem_method**: The paper's key insight is a drifting field V that governs sample movement through attraction to data samples and repuls
- **full_guided**: The paper's core mechanism is a drifting field based on kernel-weighted attraction to data samples and repulsion from ge
- **full_freestyle**: The original paper's key innovation is a drifting field V_p,q that governs sample movement during training through attra
