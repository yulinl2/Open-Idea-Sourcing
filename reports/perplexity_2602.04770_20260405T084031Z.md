---
title: Geo-Perplexity Analysis
target: "Generative Modeling via Drifting"
source: "https://arxiv.org/pdf/2602.04770"
models: ['gpt-4o']
generated: 2026-04-05 08:40 UTC
---

# Geo-Perplexity Analysis: Generative Modeling via Drifting

## Overview

- **Target paper**: Generative Modeling via Drifting
- **Source**: `https://arxiv.org/pdf/2602.04770`
- **Models evaluated**: gpt-4o
- **Cited references found**: 63
- **References with extracted text**: 55
- **Generated**: 2026-04-05 08:40 UTC

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

PPL(target | target) = **1.000034**
- Avg logprob: -0.0000
- Tokens echoed: 645 across 1 chunks
- Context tokens: 645

### Cited Reference Perplexities

**Statistics** (n=54 valid, 1 errored):
- Mean PPL: 1.006349
- Median PPL: 1.000010
- Std: 0.025978
- Range: [1.000000, 1.117460]
- Mean PPL/self ratio: 1.006314
- Max PPL/self ratio: 1.117422

| Rank | PPL | PPL/self | Ctx Tokens | Echo Tokens | Source | Reference |
|------|-----|---------|------------|-------------|--------|-----------|
| 1 | 1.000000 | 0.999966 | 4732 | 645 | full-text(raw) | RoFormer: Enhanced Transformer with Rotary Positio… |
| 2 | 1.000000 | 0.999966 | 5142 | 645 | full-text(raw) | Inductive Moment Matching |
| 3 | 1.000000 | 0.999966 | 1181 | 645 | full-text(LLM) | Score-Based Generative Modeling through Stochastic… |
| 4 | 1.000000 | 0.999966 | 2194 | 645 | full-text(LLM) | Exploring Simple Siamese Representation Learning |
| 5 | 1.000000 | 0.999966 | 1087 | 645 | full-text(LLM) | Generative Moment Matching Networks |
| 6 | 1.000000 | 0.999966 | 3718 | 645 | full-text(raw) | Flow map matching with stochastic interpolants: A … |
| 7 | 1.000000 | 0.999966 | 4095 | 645 | full-text(raw) | Stochastic Interpolants: A Unifying Framework for … |
| 8 | 1.000000 | 0.999966 | 3590 | 645 | full-text(LLM) | Classifier-Free Diffusion Guidance |
| 9 | 1.000000 | 0.999966 | 2286 | 645 | full-text(LLM) | Masked Autoencoders Are Scalable Vision Learners |
| 10 | 1.000000 | 0.999966 | 4030 | 645 | full-text(raw) | Scaling up GANs for Text-to-Image Synthesis |
| 11 | 1.000000 | 0.999966 | 4988 | 645 | full-text(raw) | Understanding Diffusion Objectives as the ELBO wit… |
| 12 | 1.000000 | 0.999966 | 2888 | 645 | full-text(LLM) | Flow Matching for Generative Modeling |
| 13 | 1.000001 | 0.999966 | 4027 | 645 | full-text(raw) | Contrastive Flow Matching |
| 14 | 1.000001 | 0.999966 | 4188 | 645 | full-text(raw) | There is No VAE: End-to-End Pixel-Space Generative… |
| 15 | 1.000001 | 0.999966 | 2544 | 645 | full-text(LLM) | Diffusion Models Beat GANs on Image Synthesis |
| 16 | 1.000001 | 0.999967 | 3248 | 645 | full-text(LLM) | Normalizing Flows are Capable Generative Models |
| 17 | 1.000001 | 0.999967 | 1005 | 645 | full-text(LLM) | Mean Flows for One-step Generative Modeling |
| 18 | 1.000001 | 0.999967 | 1307 | 645 | full-text(LLM) | Improved Techniques for Training Consistency Model… |
| 19 | 1.000002 | 0.999968 | 4139 | 645 | full-text(raw) | One Step Diffusion via Shortcut Models |
| 20 | 1.000003 | 0.999968 | 3925 | 645 | full-text(raw) | Variational Inference with Normalizing Flows |
| 21 | 1.000003 | 0.999969 | 2120 | 645 | full-text(LLM) | Coulomb GANs: Provably Optimal Nash Equilibria via… |
| 22 | 1.000004 | 0.999970 | 1769 | 645 | full-text(LLM) | Training generative neural networks via Maximum Me… |
| 23 | 1.000005 | 0.999971 | 6000 | 645 | full-text(raw) | Denoising Diffusion Probabilistic Models |
| 24 | 1.000006 | 0.999971 | 4374 | 645 | full-text(raw) | Density estimation using Real NVP |
| 25 | 1.000006 | 0.999972 | 489 | 645 | full-text(LLM) | Scalable Diffusion Models with Transformers |
| 26 | 1.000007 | 0.999973 | 534 | 645 | full-text(LLM) | Adversarial Flow Models |
| 27 | 1.000009 | 0.999975 | 4427 | 645 | full-text(raw) | Diff-Instruct: A Universal Approach for Transferri… |
| 28 | 1.000011 | 0.999977 | 3810 | 645 | full-text(raw) | Taming Transformers for High-Resolution Image Synt… |
| 29 | 1.000011 | 0.999977 | 4377 | 645 | full-text(raw) | Score identity Distillation: Exponentially Fast Di… |
| 30 | 1.000020 | 0.999986 | 4449 | 645 | full-text(raw) | Representation Alignment for Generation: Training … |
| 31 | 1.000022 | 0.999988 | 904 | 645 | full-text(LLM) | StyleGAN-XL: Scaling StyleGAN to Large Diverse Dat… |
| 32 | 1.000022 | 0.999988 | 570 | 645 | full-text(LLM) | Flow Straight and Fast: Learning to Generate and T… |
| 33 | 1.000022 | 0.999988 | 4171 | 645 | full-text(raw) | An Image is Worth 16x16 Words: Transformers for Im… |
| 34 | 1.000026 | 0.999992 | 1700 | 645 | full-text(LLM) | PixelDiT: Pixel Diffusion Transformers for Image G… |
| 35 | 1.000039 | 1.000004 | 1241 | 645 | full-text(LLM) | ConvNeXt V2: Co-designing and Scaling ConvNets wit… |
| 36 | 1.000042 | 1.000008 | 474 | 645 | full-text(LLM) | One-Step Diffusion with Distribution Matching Dist… |
| 37 | 1.000042 | 1.000008 | 3625 | 645 | full-text(raw) | Diffusion policy: Visuomotor policy learning via a… |
| 38 | 1.000076 | 1.000041 | 4356 | 645 | full-text(raw) | Deep Unsupervised Learning using Nonequilibrium Th… |
| 39 | 1.000093 | 1.000059 | 569 | 645 | full-text(LLM) | Learning Transferable Visual Models From Natural L… |
| 40 | 1.000099 | 1.000065 | 4364 | 645 | full-text(raw) | Root Mean Square Layer Normalization |
| 41 | 1.000169 | 1.000135 | 669 | 645 | full-text(LLM) | High-Resolution Image Synthesis with Latent Diffus… |
| 42 | 1.000175 | 1.000141 | 3546 | 645 | full-text(raw) | Improved Baselines with Momentum Contrastive Learn… |
| 43 | 1.000331 | 1.000296 | 904 | 645 | full-text(LLM) | Reconstruction vs. Generation: Taming Optimization… |
| 44 | 1.000340 | 1.000306 | 402 | 645 | full-text(LLM) | A Simple Framework for Contrastive Learning of Vis… |
| 45 | 1.000350 | 1.000316 | 4004 | 645 | full-text(raw) | Deep Residual Learning for Image Recognition |
| 46 | 1.000473 | 1.000439 | 4617 | 645 | full-text(raw) | Simpler Diffusion (SiD2): 1.5 FID on ImageNet512 w… |
| 47 | 1.000475 | 1.000440 | 617 | 645 | full-text(LLM) | simple diffusion: End-to-end diffusion for high re… |
| 48 | 1.000513 | 1.000479 | 4136 | 645 | full-text(raw) | GLU Variants Improve Transformer |
| 49 | 1.000717 | 1.000683 | 4506 | 645 | full-text(raw) | Improved Mean Flows: On the Challenges of Fastforw… |
| 50 | 1.000812 | 1.000778 | 4346 | 645 | full-text(raw) | Query-Key Normalization for Transformers |
| 51 | 1.001005 | 1.000970 | 4181 | 645 | full-text(raw) | Representation Learning with Contrastive Predictiv… |
| 52 | 1.103758 | 1.103721 | 4130 | 10 | full-text(raw) | Group Normalization |
| 53 | 1.115663 | 1.115625 | 713 | 10 | full-text(LLM) | Large Scale GAN Training for High Fidelity Natural… |
| 54 | 1.117460 | 1.117422 | 524 | 10 | full-text(LLM) | Batch Normalization: Accelerating Deep Network Tra… |
| 55 | — | — | 3830 | 0 | full-text(raw) | The Unreasonable Effectiveness of Deep Features as… ⚠ |

### Distribution of PPL / self ratio

Values >1 mean the reference makes the target harder to predict than itself.

```
  PPL/self
    1.0000–  1.0098 │ ████████████████████████████████████████ (51)
    1.0098–  1.0195 │  (0)
    1.0195–  1.0293 │  (0)
    1.0293–  1.0391 │  (0)
    1.0391–  1.0489 │  (0)
    1.0489–  1.0587 │  (0)
    1.0587–  1.0685 │  (0)
    1.0685–  1.0783 │  (0)
    1.0783–  1.0881 │  (0)
    1.0881–  1.0978 │  (0)
    1.0978–  1.1076 │  (1)
    1.1076–  1.1174 │ █ (2)
```

### Distribution of raw PPL

```
  PPL
    1.0000–  1.0098 │ ████████████████████████████████████████ (51)
    1.0098–  1.0196 │  (0)
    1.0196–  1.0294 │  (0)
    1.0294–  1.0392 │  (0)
    1.0392–  1.0489 │  (0)
    1.0489–  1.0587 │  (0)
    1.0587–  1.0685 │  (0)
    1.0685–  1.0783 │  (0)
    1.0783–  1.0881 │  (0)
    1.0881–  1.0979 │  (0)
    1.0979–  1.1077 │  (1)
    1.1077–  1.1175 │ █ (2)
```

## Errors (1 total)

- **gpt-4o** | The Unreasonable Effectiveness of Deep Features as: chunk 1/1: Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-YHtdLrQ8KAel6oYw0LVgAlx7 on tokens per min (TPM): Limit 30000, Used 26968, Requested 4557. Please try again in 3.05s. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}
