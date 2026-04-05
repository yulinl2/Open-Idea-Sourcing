---
title: Geo-Perplexity Analysis
target: "Generative Modeling via Drifting"
source: "https://arxiv.org/pdf/2602.04770"
models: ['gpt-4o']
generated: 2026-04-05 15:11 UTC
---

# Geo-Perplexity Analysis: Generative Modeling via Drifting

## Overview

- **Target paper**: Generative Modeling via Drifting
- **Source**: `https://arxiv.org/pdf/2602.04770`
- **Models evaluated**: gpt-4o
- **Cited references found**: 63
- **References with extracted text**: 55
- **Generated**: 2026-04-05 15:11 UTC

## Methodology

**Exact conditional perplexity** via verbatim-echo with logprobs:

1. Reference paper text → system message (~6K tokens context)
2. Target paper text is chunked into ~800-token windows
3. Model is instructed to reproduce each chunk **verbatim**
4. `logprobs=True` returns P(token_i | context, token_1..i-1) for each echoed token
5. **PPL = exp(−(1/N) Σ log p(token_i))** — exact, not approximate

**Interpretation**: Lower PPL → target is more predictable given that reference → reference explains more of the target's content. Higher PPL → target says something the reference doesn't prepare you for.

## Results: gpt-4o

### Self-Perplexity (lower bound)

PPL(target | target) = **1.000035**
- Avg logprob: -0.0000
- Tokens echoed: 645 across 1 chunks
- Context tokens: 645

### Cited Reference Perplexities

**Statistics** (n=55 valid, 0 errored):
- Mean PPL: 1.012371
- Median PPL: 1.000024
- Std: 0.036308
- Range: [1.000000, 1.196466]
- Mean PPL/self ratio: 1.012336
- Max PPL/self ratio: 1.196425

| Rank | PPL | PPL/self | Ctx Tokens | Echo Tokens | Source | Reference |
|------|-----|---------|------------|-------------|--------|-----------|
| 1 | 1.000000 | 0.999966 | 4188 | 645 | full-text(raw) | There is No VAE: End-to-End Pixel-Space Generative… |
| 2 | 1.000000 | 0.999966 | 4988 | 645 | full-text(raw) | Understanding Diffusion Objectives as the ELBO wit… |
| 3 | 1.000000 | 0.999966 | 3718 | 645 | full-text(raw) | Flow map matching with stochastic interpolants: A … |
| 4 | 1.000000 | 0.999966 | 4095 | 645 | full-text(raw) | Stochastic Interpolants: A Unifying Framework for … |
| 5 | 1.000000 | 0.999966 | 4732 | 645 | full-text(raw) | RoFormer: Enhanced Transformer with Rotary Positio… |
| 6 | 1.000000 | 0.999966 | 4030 | 645 | full-text(raw) | Scaling up GANs for Text-to-Image Synthesis |
| 7 | 1.000000 | 0.999966 | 4027 | 645 | full-text(raw) | Contrastive Flow Matching |
| 8 | 1.000000 | 0.999966 | 2888 | 645 | full-text(LLM) | Flow Matching for Generative Modeling |
| 9 | 1.000001 | 0.999966 | 2194 | 645 | full-text(LLM) | Exploring Simple Siamese Representation Learning |
| 10 | 1.000001 | 0.999966 | 1181 | 645 | full-text(LLM) | Score-Based Generative Modeling through Stochastic… |
| 11 | 1.000001 | 0.999966 | 2544 | 645 | full-text(LLM) | Diffusion Models Beat GANs on Image Synthesis |
| 12 | 1.000001 | 0.999966 | 3248 | 645 | full-text(LLM) | Normalizing Flows are Capable Generative Models |
| 13 | 1.000001 | 0.999967 | 4139 | 645 | full-text(raw) | One Step Diffusion via Shortcut Models |
| 14 | 1.000001 | 0.999967 | 2120 | 645 | full-text(LLM) | Coulomb GANs: Provably Optimal Nash Equilibria via… |
| 15 | 1.000002 | 0.999967 | 1307 | 645 | full-text(LLM) | Improved Techniques for Training Consistency Model… |
| 16 | 1.000002 | 0.999968 | 5142 | 645 | full-text(raw) | Inductive Moment Matching |
| 17 | 1.000002 | 0.999968 | 1087 | 645 | full-text(LLM) | Generative Moment Matching Networks |
| 18 | 1.000004 | 0.999969 | 4449 | 645 | full-text(raw) | Representation Alignment for Generation: Training … |
| 19 | 1.000004 | 0.999969 | 1769 | 645 | full-text(LLM) | Training generative neural networks via Maximum Me… |
| 20 | 1.000005 | 0.999970 | 4374 | 645 | full-text(raw) | Density estimation using Real NVP |
| 21 | 1.000006 | 0.999971 | 489 | 645 | full-text(LLM) | Scalable Diffusion Models with Transformers |
| 22 | 1.000012 | 0.999977 | 4377 | 645 | full-text(raw) | Score identity Distillation: Exponentially Fast Di… |
| 23 | 1.000016 | 0.999982 | 3590 | 645 | full-text(LLM) | Classifier-Free Diffusion Guidance |
| 24 | 1.000019 | 0.999984 | 3625 | 645 | full-text(raw) | Diffusion policy: Visuomotor policy learning via a… |
| 25 | 1.000021 | 0.999987 | 904 | 645 | full-text(LLM) | StyleGAN-XL: Scaling StyleGAN to Large Diverse Dat… |
| 26 | 1.000021 | 0.999987 | 570 | 645 | full-text(LLM) | Flow Straight and Fast: Learning to Generate and T… |
| 27 | 1.000024 | 0.999989 | 3925 | 645 | full-text(raw) | Variational Inference with Normalizing Flows |
| 28 | 1.000024 | 0.999990 | 1700 | 645 | full-text(LLM) | PixelDiT: Pixel Diffusion Transformers for Image G… |
| 29 | 1.000030 | 0.999995 | 4171 | 645 | full-text(raw) | An Image is Worth 16x16 Words: Transformers for Im… |
| 30 | 1.000030 | 0.999996 | 4427 | 645 | full-text(raw) | Diff-Instruct: A Universal Approach for Transferri… |
| 31 | 1.000031 | 0.999996 | 534 | 645 | full-text(LLM) | Adversarial Flow Models |
| 32 | 1.000038 | 1.000004 | 3546 | 645 | full-text(raw) | Improved Baselines with Momentum Contrastive Learn… |
| 33 | 1.000039 | 1.000004 | 474 | 645 | full-text(LLM) | One-Step Diffusion with Distribution Matching Dist… |
| 34 | 1.000040 | 1.000005 | 4136 | 645 | full-text(raw) | GLU Variants Improve Transformer |
| 35 | 1.000041 | 1.000006 | 1241 | 645 | full-text(LLM) | ConvNeXt V2: Co-designing and Scaling ConvNets wit… |
| 36 | 1.000046 | 1.000012 | 2286 | 645 | full-text(LLM) | Masked Autoencoders Are Scalable Vision Learners |
| 37 | 1.000047 | 1.000012 | 3810 | 645 | full-text(raw) | Taming Transformers for High-Resolution Image Synt… |
| 38 | 1.000052 | 1.000018 | 4356 | 645 | full-text(raw) | Deep Unsupervised Learning using Nonequilibrium Th… |
| 39 | 1.000076 | 1.000041 | 4181 | 645 | full-text(raw) | Representation Learning with Contrastive Predictiv… |
| 40 | 1.000080 | 1.000046 | 4506 | 645 | full-text(raw) | Improved Mean Flows: On the Challenges of Fastforw… |
| 41 | 1.000112 | 1.000077 | 617 | 645 | full-text(LLM) | simple diffusion: End-to-end diffusion for high re… |
| 42 | 1.000127 | 1.000092 | 6000 | 645 | full-text(raw) | Denoising Diffusion Probabilistic Models |
| 43 | 1.000170 | 1.000136 | 4617 | 645 | full-text(raw) | Simpler Diffusion (SiD2): 1.5 FID on ImageNet512 w… |
| 44 | 1.000174 | 1.000140 | 669 | 645 | full-text(LLM) | High-Resolution Image Synthesis with Latent Diffus… |
| 45 | 1.000186 | 1.000151 | 3830 | 645 | full-text(raw) | The Unreasonable Effectiveness of Deep Features as… |
| 46 | 1.000340 | 1.000305 | 904 | 645 | full-text(LLM) | Reconstruction vs. Generation: Taming Optimization… |
| 47 | 1.000381 | 1.000346 | 402 | 645 | full-text(LLM) | A Simple Framework for Contrastive Learning of Vis… |
| 48 | 1.000915 | 1.000881 | 4364 | 645 | full-text(raw) | Root Mean Square Layer Normalization |
| 49 | 1.044545 | 1.044508 | 4130 | 10 | full-text(raw) | Group Normalization |
| 50 | 1.070460 | 1.070423 | 569 | 10 | full-text(LLM) | Learning Transferable Visual Models From Natural L… |
| 51 | 1.070877 | 1.070840 | 713 | 10 | full-text(LLM) | Large Scale GAN Training for High Fidelity Natural… |
| 52 | 1.093184 | 1.093146 | 524 | 10 | full-text(LLM) | Batch Normalization: Accelerating Deep Network Tra… |
| 53 | 1.100488 | 1.100450 | 4346 | 10 | full-text(raw) | Query-Key Normalization for Transformers |
| 54 | 1.101242 | 1.101204 | 4004 | 10 | full-text(raw) | Deep Residual Learning for Image Recognition |
| 55 | 1.196466 | 1.196425 | 1005 | 10 | full-text(LLM) | Mean Flows for One-step Generative Modeling |

### Distribution of PPL / self ratio

Values >1 mean the reference makes the target harder to predict than itself.

```
  PPL/self
    1.0000–  1.0163 │ ████████████████████████████████████████ (48)
    1.0163–  1.0327 │  (0)
    1.0327–  1.0491 │  (1)
    1.0491–  1.0655 │  (0)
    1.0655–  1.0818 │ █ (2)
    1.0818–  1.0982 │  (1)
    1.0982–  1.1146 │ █ (2)
    1.1146–  1.1309 │  (0)
    1.1309–  1.1473 │  (0)
    1.1473–  1.1637 │  (0)
    1.1637–  1.1801 │  (0)
    1.1801–  1.1964 │  (1)
```

### Distribution of raw PPL

```
  PPL
    1.0000–  1.0164 │ ████████████████████████████████████████ (48)
    1.0164–  1.0327 │  (0)
    1.0327–  1.0491 │  (1)
    1.0491–  1.0655 │  (0)
    1.0655–  1.0819 │ █ (2)
    1.0819–  1.0982 │  (1)
    1.0982–  1.1146 │ █ (2)
    1.1146–  1.1310 │  (0)
    1.1310–  1.1473 │  (0)
    1.1473–  1.1637 │  (0)
    1.1637–  1.1801 │  (0)
    1.1801–  1.1965 │  (1)
```
