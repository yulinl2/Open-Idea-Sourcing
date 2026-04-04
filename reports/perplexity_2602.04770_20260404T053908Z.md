---
title: Geo-Perplexity Analysis
target: "Generative Modeling via Drifting"
source: "https://arxiv.org/pdf/2602.04770"
models: ['gpt-4o']
generated: 2026-04-04 05:39 UTC
---

# Geo-Perplexity Analysis: Generative Modeling via Drifting

## Overview

- **Target paper**: Generative Modeling via Drifting
- **Source**: `https://arxiv.org/pdf/2602.04770`
- **Models evaluated**: gpt-4o
- **Cited references found**: 63
- **References with extracted text**: 60
- **Generated**: 2026-04-04 05:39 UTC

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

PPL(target | target) = **1.000006**
- Avg logprob: -0.0000
- Tokens echoed: 1022 across 2 chunks
- Context tokens: 1022

### Random Field Reference (control)

PPL(target | random) = **1.001154** (ratio vs self: 1.001148)
- Reference: An optimal control perspective on diffusion-based generative modeling
- Source: full-text(LLM)
- Avg logprob: -0.0012
- Tokens echoed: 1025 across 2 chunks
- Context tokens: 823

### Cited Reference Perplexities

**Statistics** (n=60 valid, 0 errored):
- Mean PPL: 1.001100
- Median PPL: 1.000152
- Std: 0.001695
- Range: [1.000020, 1.007160]
- Mean PPL/self ratio: 1.001094
- Max PPL/self ratio: 1.007154

| Rank | PPL | PPL/self | Ctx Tokens | Echo Tokens | Source | Reference |
|------|-----|---------|------------|-------------|--------|-----------|
| 1 | 1.000020 | 1.000014 | 2542 | 1022 | full-text(LLM) | Diffusion Models Beat GANs on Image Synthesis |
| 2 | 1.000028 | 1.000022 | 2286 | 1022 | full-text(LLM) | Masked Autoencoders Are Scalable Vision Learners |
| 3 | 1.000029 | 1.000023 | 674 | 1022 | full-text(LLM) | Representation Alignment for Generation: Training … |
| 4 | 1.000030 | 1.000024 | 767 | 1022 | full-text(LLM) | Deep Unsupervised Learning using Nonequilibrium Th… |
| 5 | 1.000034 | 1.000028 | 1103 | 1022 | full-text(LLM) | ConvNeXt V2: Co-designing and Scaling ConvNets wit… |
| 6 | 1.000034 | 1.000028 | 699 | 1022 | full-text(LLM) | Adversarial Flow Models |
| 7 | 1.000037 | 1.000031 | 1153 | 1022 | full-text(LLM) | One Step Diffusion via Shortcut Models |
| 8 | 1.000049 | 1.000043 | 1164 | 1022 | full-text(LLM) | simple diffusion: End-to-end diffusion for high re… |
| 9 | 1.000053 | 1.000047 | 2963 | 1022 | full-text(LLM) | Normalizing Flows are Capable Generative Models |
| 10 | 1.000054 | 1.000048 | 907 | 1022 | full-text(LLM) | Density estimation using Real NVP |
| 11 | 1.000055 | 1.000049 | 2818 | 1022 | full-text(LLM) | Score-Based Generative Modeling through Stochastic… |
| 12 | 1.000055 | 1.000049 | 904 | 1022 | full-text(LLM) | Reconstruction vs. Generation: Taming Optimization… |
| 13 | 1.000060 | 1.000054 | 1767 | 1022 | full-text(LLM) | Training generative neural networks via Maximum Me… |
| 14 | 1.000065 | 1.000059 | 1230 | 1022 | full-text(LLM) | Generative Moment Matching Networks |
| 15 | 1.000068 | 1.000062 | 471 | 1022 | full-text(LLM) | Scalable Diffusion Models with Transformers |
| 16 | 1.000071 | 1.000065 | 1715 | 1022 | full-text(LLM) | Exploring Simple Siamese Representation Learning |
| 17 | 1.000077 | 1.000071 | 1704 | 1022 | full-text(LLM) | Large Scale GAN Training for High Fidelity Natural… |
| 18 | 1.000079 | 1.000073 | 999 | 1022 | full-text(LLM) | Diff-Instruct: A Universal Approach for Transferri… |
| 19 | 1.000080 | 1.000074 | 1429 | 1022 | full-text(LLM) | There is No VAE: End-to-End Pixel-Space Generative… |
| 20 | 1.000090 | 1.000084 | 1137 | 1022 | full-text(LLM) | Improved Baselines with Momentum Contrastive Learn… |
| 21 | 1.000108 | 1.000102 | 480 | 1022 | full-text(LLM) | Batch Normalization: Accelerating Deep Network Tra… |
| 22 | 1.000120 | 1.000114 | 1602 | 1022 | full-text(LLM) | GLU Variants Improve Transformer |
| 23 | 1.000124 | 1.000118 | 2300 | 1022 | full-text(LLM) | Coulomb GANs: Provably Optimal Nash Equilibria via… |
| 24 | 1.000131 | 1.000125 | 896 | 1022 | full-text(LLM) | Flow map matching with stochastic interpolants: A … |
| 25 | 1.000138 | 1.000132 | 1365 | 1022 | full-text(LLM) | Root Mean Square Layer Normalization |
| 26 | 1.000140 | 1.000134 | 1791 | 1022 | full-text(LLM) | PixelDiT: Pixel Diffusion Transformers for Image G… |
| 27 | 1.000140 | 1.000134 | 860 | 1022 | full-text(LLM) | Diffusion policy: Visuomotor policy learning via a… |
| 28 | 1.000140 | 1.000134 | 2587 | 1022 | full-text(LLM) | Representation Learning with Contrastive Predictiv… |
| 29 | 1.000142 | 1.000136 | 3191 | 1022 | full-text(LLM) | An Image is Worth 16x16 Words: Transformers for Im… |
| 30 | 1.000143 | 1.000137 | 1781 | 1022 | full-text(LLM) | Deep Residual Learning for Image Recognition |
| 31 | 1.000160 | 1.000154 | 2069 | 1022 | full-text(LLM) | Mean Flows for One-step Generative Modeling |
| 32 | 1.000179 | 1.000173 | 570 | 1022 | full-text(LLM) | Improved Mean Flows: On the Challenges of Fastforw… |
| 33 | 1.000198 | 1.000192 | 1045 | 1022 | full-text(LLM) | Stochastic Interpolants: A Unifying Framework for … |
| 34 | 1.000229 | 1.000223 | 34 | 1022 | S2-TLDR | AUTO-ENCODING VARIATIONAL BAYES |
| 35 | 1.000311 | 1.000305 | 990 | 1022 | full-text(LLM) | Contrastive Flow Matching |
| 36 | 1.000324 | 1.000318 | 1884 | 1022 | full-text(LLM) | Score identity Distillation: Exponentially Fast Di… |
| 37 | 1.000336 | 1.000330 | 599 | 1022 | full-text(LLM) | Simpler Diffusion (SiD2): 1.5 FID on ImageNet512 w… |
| 38 | 1.000430 | 1.000424 | 898 | 1022 | full-text(LLM) | One-Step Diffusion with Distribution Matching Dist… |
| 39 | 1.000507 | 1.000501 | 330 | 1022 | full-text(LLM) | Denoising Diffusion Probabilistic Models |
| 40 | 1.000519 | 1.000513 | 1077 | 1022 | full-text(LLM) | Understanding Diffusion Objectives as the ELBO wit… |
| 41 | 1.000525 | 1.000519 | 2205 | 1022 | full-text(LLM) | RoFormer: Enhanced Transformer with Rotary Positio… |
| 42 | 1.000568 | 1.000562 | 2915 | 1022 | full-text(LLM) | Flow Matching for Generative Modeling |
| 43 | 1.000835 | 1.000829 | 854 | 1022 | full-text(LLM) | Classifier-Free Diffusion Guidance |
| 44 | 1.001185 | 1.001179 | 511 | 1025 | full-text(LLM) | Variational Inference with Normalizing Flows |
| 45 | 1.001214 | 1.001208 | 38 | 806 | S2-TLDR | Mean Shift, Mode Seeking, and Clustering |
| 46 | 1.001515 | 1.001509 | 393 | 1025 | full-text(LLM) | Inductive Moment Matching |
| 47 | 1.002142 | 1.002136 | 283 | 1025 | full-text(LLM) | Flow Straight and Fast: Learning to Generate and T… |
| 48 | 1.002437 | 1.002431 | 474 | 236 | full-text(LLM) | Taming Transformers for High-Resolution Image Synt… |
| 49 | 1.002567 | 1.002561 | 669 | 236 | full-text(LLM) | High-Resolution Image Synthesis with Latent Diffus… |
| 50 | 1.003159 | 1.003153 | 621 | 236 | full-text(LLM) | Learning Transferable Visual Models From Natural L… |
| 51 | 1.003360 | 1.003354 | 635 | 236 | full-text(LLM) | Scaling up GANs for Text-to-Image Synthesis |
| 52 | 1.003462 | 1.003456 | 51 | 236 | S2-TLDR | Decoupled Weight Decay Regularization |
| 53 | 1.003674 | 1.003668 | 4919 | 236 | full-text(raw) | Improved Techniques for Training Consistency Model… |
| 54 | 1.003796 | 1.003790 | 1071 | 236 | full-text(LLM) | Group Normalization |
| 55 | 1.003978 | 1.003972 | 471 | 236 | full-text(LLM) | A Simple Framework for Contrastive Learning of Vis… |
| 56 | 1.004243 | 1.004237 | 761 | 236 | full-text(LLM) | StyleGAN-XL: Scaling StyleGAN to Large Diverse Dat… |
| 57 | 1.004558 | 1.004552 | 666 | 236 | full-text(LLM) | Query-Key Normalization for Transformers |
| 58 | 1.004953 | 1.004947 | 56 | 236 | S2-TLDR | GANs Trained by a Two Time-Scale Update Rule Conve… |
| 59 | 1.005053 | 1.005047 | 50 | 236 | S2-TLDR | GENERATIVE ADVERSARIAL NETS |
| 60 | 1.007160 | 1.007154 | 262 | 236 | full-text(LLM) | The Unreasonable Effectiveness of Deep Features as… |

### Distribution of PPL / self ratio

Values >1 mean the reference makes the target harder to predict than itself.

```
  PPL/self
    1.000014–  1.000609 │ ████████████████████████████████████████ (42)
    1.000609–  1.001204 │ █ (2)
    1.001204–  1.001799 │ █ (2)
    1.001799–  1.002394 │  (1)
    1.002394–  1.002989 │ █ (2)
    1.002989–  1.003584 │ ██ (3)
    1.003584–  1.004179 │ ██ (3)
    1.004179–  1.004774 │ █ (2)
    1.004774–  1.005369 │ █ (2)
    1.005369–  1.005964 │  (0)
    1.005964–  1.006559 │  (0)
    1.006559–  1.007154 │  (1)
```

### Distribution of raw PPL

```
  PPL
    1.000020–  1.000615 │ ████████████████████████████████████████ (42)
    1.000615–  1.001210 │ █ (2)
    1.001210–  1.001805 │ █ (2)
    1.001805–  1.002400 │  (1)
    1.002400–  1.002995 │ █ (2)
    1.002995–  1.003590 │ ██ (3)
    1.003590–  1.004185 │ ██ (3)
    1.004185–  1.004780 │ █ (2)
    1.004780–  1.005375 │ █ (2)
    1.005375–  1.005970 │  (0)
    1.005970–  1.006565 │  (0)
    1.006565–  1.007160 │  (1)
```
