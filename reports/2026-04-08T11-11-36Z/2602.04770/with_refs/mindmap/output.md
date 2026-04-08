# Reconstruction: mindmap (iterative, 4 rounds)
**Paper:** 2602.04770  
**Condition:** with_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  
**Rounds:** 4  
**Best round:** 1 (score 3.0)  
**Converged:** True (score plateau (delta=0.20) and hint stable)  
**Score trajectory:** 3.0 -> 2.8 -> 2.8 -> 3.0  

---

# Paper Idea Mindmap

## Core Problem
- Current generative models require iterative refinement procedures at inference time, but we need single-step generation that can learn complex distribution mappings directly without decomposing them into multiple simpler transformations.

## Key Observations from References
- Conformal prediction provides distribution-free guarantees by leveraging exchangeability properties of data
- Weighted versions of statistical procedures can handle distribution shifts when likelihood ratios are known
- Quantile-based methods can provide finite-sample guarantees without distributional assumptions
- Covariate shift techniques show how to reweight samples to account for distribution mismatches

## Proposed Approach
### Main Idea
- Develop a **Conformal Flow Network** that learns direct mappings between distributions by treating generation as a weighted conformal prediction problem, where we predict the "conformity" of generated samples to the target distribution in a single forward pass.

### Sub-ideas
- **Conformal Score Learning**
  - Train a neural network to predict conformity scores S(x, D) that measure how well sample x fits dataset D
  - Use these scores to construct prediction sets that contain valid samples with high probability
  - Replace iterative refinement with direct conformity-based sampling

- **Distribution Ratio Estimation**
  - Learn the likelihood ratio w(x) = p_data(x)/p_noise(x) between target and noise distributions
  - Use this ratio to weight conformity scores, enabling direct mapping from noise to data
  - Leverage the weighted exchangeability framework from covariate shift literature

- **Single-Step Conformal Generation**
  - At inference, sample z ~ p_noise and compute conformity threshold via quantile of weighted training scores
  - Generate x = G(z) such that S(x, D_train) ≤ threshold with high probability
  - Use differentiable quantile operations to make the entire process end-to-end trainable

- **Adaptive Threshold Learning**
  - Learn coverage level α adaptively based on generation quality metrics
  - Use split conformal approach: separate networks for score prediction and threshold estimation
  - Enable conditional generation by conditioning both score function and thresholds on context

## Theoretical Grounding
- Conformal prediction theory guarantees finite-sample coverage without distributional assumptions
- Weighted conformal methods handle distribution shift when likelihood ratios are available
- The exchangeability assumption can be relaxed to weighted exchangeability for generative modeling
- Quantile-based approaches provide robust statistical guarantees that transfer to generative settings

## Potential Challenges
- **Likelihood Ratio Estimation Challenge**: Accurately estimating w(x) = p_data(x)/p_noise(x) is non-trivial
  - Address by using density ratio estimation techniques or adversarial approaches to learn ratios
  - Alternative: Learn ratios implicitly through the conformity score training process

- **Discrete Quantile Operations Challenge**: Standard quantile operations are non-differentiable
  - Address by using soft/differentiable quantile approximations (e.g., soft sorting, temperature-based smoothing)
  - Alternative: Use reinforcement learning or gradient estimation techniques for discrete operations

## Connections to Existing Work
- **Extends conformal prediction beyond uncertainty quantification to generative modeling**: Uses the theoretical framework of weighted exchangeability to handle the noise-to-data distribution shift inherent in generation
- **Differs from standard flow models**: Instead of learning invertible transformations through multiple coupling layers, directly learns conformity-based mappings that guarantee statistical validity
- **Relates to score-based models**: Similar motivation of using score functions, but replaces iterative denoising with single-step conformal prediction
- **Connects to adversarial training**: The conformity score learning resembles discriminator training, but with principled statistical guarantees rather than just adversarial objectives
