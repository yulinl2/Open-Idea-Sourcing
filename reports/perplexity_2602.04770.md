---
title: Geo-Perplexity Analysis
target: "Generative Modeling via Drifting"
source: "https://arxiv.org/pdf/2602.04770"
models: ['gpt-5.4', 'gpt-4o']
generated: 2026-04-01 17:26 UTC
---

# Geo-Perplexity Analysis: Generative Modeling via Drifting

## Overview

- **Target paper**: Generative Modeling via Drifting
- **Source**: `https://arxiv.org/pdf/2602.04770`
- **Models evaluated**: gpt-5.4, gpt-4o
- **Cited references found**: 63
- **References with extracted text**: 55
- **Generated**: 2026-04-01 17:26 UTC

## Methodology

Perplexity is estimated using conditional generation logprobs:
1. Context paper text placed in system message (~4K tokens)
2. First ~40% of target paper as prompt prefix
3. Model generates continuation with `logprobs=True`
4. PPL = exp(-mean(token_logprobs))

**Interpretation**: Lower PPL → target is more predictable given context → less novel. Higher PPL → more surprising → more novel.

## Results: gpt-5.4

### Self-Perplexity (baseline)

PPL(target | target) = **∞ (error)**
- Avg logprob: -inf
- Tokens evaluated: 0
- Error: Connection error.

### Cited Reference Perplexities

**Statistics** (n=0 valid of 55 total):
- Mean: 0.00
- Median: 0.00
- Std: 0.00
- Min: 0.00
- Max: 0.00

| Rank | PPL | Avg LogProb | Tokens | Reference |
|------|-----|-------------|--------|-----------|
| 1 | ∞ (error) | -inf | 0 | Improved Mean Flows: On the Challenges of Fastforward Genera... ⚠️ |
| 2 | ∞ (error) | -inf | 0 | Adversarial Flow Models ⚠️ |
| 3 | ∞ (error) | -inf | 0 | PixelDiT: Pixel Diffusion Transformers for Image Generation ⚠️ |
| 4 | ∞ (error) | -inf | 0 | There is No VAE: End-to-End Pixel-Space Generative Modeling ... ⚠️ |
| 5 | ∞ (error) | -inf | 0 | Contrastive Flow Matching ⚠️ |
| 6 | ∞ (error) | -inf | 0 | Mean Flows for One-step Generative Modeling ⚠️ |
| 7 | ∞ (error) | -inf | 0 | Inductive Moment Matching ⚠️ |
| 8 | ∞ (error) | -inf | 0 | Reconstruction vs. Generation: Taming Optimization Dilemma i... ⚠️ |
| 9 | ∞ (error) | -inf | 0 | Normalizing Flows are Capable Generative Models ⚠️ |
| 10 | ∞ (error) | -inf | 0 | Simpler Diffusion (SiD2): 1.5 FID on ImageNet512 with pixel-... ⚠️ |
| 11 | ∞ (error) | -inf | 0 | One Step Diffusion via Shortcut Models ⚠️ |
| 12 | ∞ (error) | -inf | 0 | Representation Alignment for Generation: Training Diffusion ... ⚠️ |
| 13 | ∞ (error) | -inf | 0 | Flow map matching with stochastic interpolants: A mathematic... ⚠️ |
| 14 | ∞ (error) | -inf | 0 | Score identity Distillation: Exponentially Fast Distillation... ⚠️ |
| 15 | ∞ (error) | -inf | 0 | One-Step Diffusion with Distribution Matching Distillation ⚠️ |
| 16 | ∞ (error) | -inf | 0 | Improved Techniques for Training Consistency Models ⚠️ |
| 17 | ∞ (error) | -inf | 0 | Diff-Instruct: A Universal Approach for Transferring Knowled... ⚠️ |
| 18 | ∞ (error) | -inf | 0 | Stochastic Interpolants: A Unifying Framework for Flows and ... ⚠️ |
| 19 | ∞ (error) | -inf | 0 | Scaling up GANs for Text-to-Image Synthesis ⚠️ |
| 20 | ∞ (error) | -inf | 0 | Diffusion policy: Visuomotor policy learning via action diff... ⚠️ |
| 21 | ∞ (error) | -inf | 0 | Understanding Diffusion Objectives as the ELBO with Simple D... ⚠️ |
| 22 | ∞ (error) | -inf | 0 | simple diffusion: End-to-end diffusion for high resolution i... ⚠️ |
| 23 | ∞ (error) | -inf | 0 | ConvNeXt V2: Co-designing and Scaling ConvNets with Masked A... ⚠️ |
| 24 | ∞ (error) | -inf | 0 | Scalable Diffusion Models with Transformers ⚠️ |
| 25 | ∞ (error) | -inf | 0 | Flow Matching for Generative Modeling ⚠️ |
| 26 | ∞ (error) | -inf | 0 | Flow Straight and Fast: Learning to Generate and Transfer Da... ⚠️ |
| 27 | ∞ (error) | -inf | 0 | Classifier-Free Diffusion Guidance ⚠️ |
| 28 | ∞ (error) | -inf | 0 | StyleGAN-XL: Scaling StyleGAN to Large Diverse Datasets ⚠️ |
| 29 | ∞ (error) | -inf | 0 | High-Resolution Image Synthesis with Latent Diffusion Models ⚠️ |
| 30 | ∞ (error) | -inf | 0 | Masked Autoencoders Are Scalable Vision Learners ⚠️ |
| 31 | ∞ (error) | -inf | 0 | Diffusion Models Beat GANs on Image Synthesis ⚠️ |
| 32 | ∞ (error) | -inf | 0 | RoFormer: Enhanced Transformer with Rotary Position Embeddin... ⚠️ |
| 33 | ∞ (error) | -inf | 0 | Learning Transferable Visual Models From Natural Language Su... ⚠️ |
| 34 | ∞ (error) | -inf | 0 | Taming Transformers for High-Resolution Image Synthesis ⚠️ |
| 35 | ∞ (error) | -inf | 0 | Score-Based Generative Modeling through Stochastic Different... ⚠️ |
| 36 | ∞ (error) | -inf | 0 | Exploring Simple Siamese Representation Learning ⚠️ |
| 37 | ∞ (error) | -inf | 0 | An Image is Worth 16x16 Words: Transformers for Image Recogn... ⚠️ |
| 38 | ∞ (error) | -inf | 0 | Query-Key Normalization for Transformers ⚠️ |
| 39 | ∞ (error) | -inf | 0 | Denoising Diffusion Probabilistic Models ⚠️ |
| 40 | ∞ (error) | -inf | 0 | Improved Baselines with Momentum Contrastive Learning ⚠️ |
| 41 | ∞ (error) | -inf | 0 | A Simple Framework for Contrastive Learning of Visual Repres... ⚠️ |
| 42 | ∞ (error) | -inf | 0 | GLU Variants Improve Transformer ⚠️ |
| 43 | ∞ (error) | -inf | 0 | Root Mean Square Layer Normalization ⚠️ |
| 44 | ∞ (error) | -inf | 0 | Large Scale GAN Training for High Fidelity Natural Image Syn... ⚠️ |
| 45 | ∞ (error) | -inf | 0 | Representation Learning with Contrastive Predictive Coding ⚠️ |
| 46 | ∞ (error) | -inf | 0 | Group Normalization ⚠️ |
| 47 | ∞ (error) | -inf | 0 | The Unreasonable Effectiveness of Deep Features as a Percept... ⚠️ |
| 48 | ∞ (error) | -inf | 0 | Coulomb GANs: Provably Optimal Nash Equilibria via Potential... ⚠️ |
| 49 | ∞ (error) | -inf | 0 | Density estimation using Real NVP ⚠️ |
| 50 | ∞ (error) | -inf | 0 | Deep Residual Learning for Image Recognition ⚠️ |
| 51 | ∞ (error) | -inf | 0 | Variational Inference with Normalizing Flows ⚠️ |
| 52 | ∞ (error) | -inf | 0 | Training generative neural networks via Maximum Mean Discrep... ⚠️ |
| 53 | ∞ (error) | -inf | 0 | Deep Unsupervised Learning using Nonequilibrium Thermodynami... ⚠️ |
| 54 | ∞ (error) | -inf | 0 | Batch Normalization: Accelerating Deep Network Training by R... ⚠️ |
| 55 | ∞ (error) | -inf | 0 | Generative Moment Matching Networks ⚠️ |

## Results: gpt-4o

### Self-Perplexity (baseline)

PPL(target | target) = **∞ (error)**
- Avg logprob: -inf
- Tokens evaluated: 0
- Error: Connection error.

### Cited Reference Perplexities

**Statistics** (n=0 valid of 55 total):
- Mean: 0.00
- Median: 0.00
- Std: 0.00
- Min: 0.00
- Max: 0.00

| Rank | PPL | Avg LogProb | Tokens | Reference |
|------|-----|-------------|--------|-----------|
| 1 | ∞ (error) | -inf | 0 | Improved Mean Flows: On the Challenges of Fastforward Genera... ⚠️ |
| 2 | ∞ (error) | -inf | 0 | Adversarial Flow Models ⚠️ |
| 3 | ∞ (error) | -inf | 0 | PixelDiT: Pixel Diffusion Transformers for Image Generation ⚠️ |
| 4 | ∞ (error) | -inf | 0 | There is No VAE: End-to-End Pixel-Space Generative Modeling ... ⚠️ |
| 5 | ∞ (error) | -inf | 0 | Contrastive Flow Matching ⚠️ |
| 6 | ∞ (error) | -inf | 0 | Mean Flows for One-step Generative Modeling ⚠️ |
| 7 | ∞ (error) | -inf | 0 | Inductive Moment Matching ⚠️ |
| 8 | ∞ (error) | -inf | 0 | Reconstruction vs. Generation: Taming Optimization Dilemma i... ⚠️ |
| 9 | ∞ (error) | -inf | 0 | Normalizing Flows are Capable Generative Models ⚠️ |
| 10 | ∞ (error) | -inf | 0 | Simpler Diffusion (SiD2): 1.5 FID on ImageNet512 with pixel-... ⚠️ |
| 11 | ∞ (error) | -inf | 0 | One Step Diffusion via Shortcut Models ⚠️ |
| 12 | ∞ (error) | -inf | 0 | Representation Alignment for Generation: Training Diffusion ... ⚠️ |
| 13 | ∞ (error) | -inf | 0 | Flow map matching with stochastic interpolants: A mathematic... ⚠️ |
| 14 | ∞ (error) | -inf | 0 | Score identity Distillation: Exponentially Fast Distillation... ⚠️ |
| 15 | ∞ (error) | -inf | 0 | One-Step Diffusion with Distribution Matching Distillation ⚠️ |
| 16 | ∞ (error) | -inf | 0 | Improved Techniques for Training Consistency Models ⚠️ |
| 17 | ∞ (error) | -inf | 0 | Diff-Instruct: A Universal Approach for Transferring Knowled... ⚠️ |
| 18 | ∞ (error) | -inf | 0 | Stochastic Interpolants: A Unifying Framework for Flows and ... ⚠️ |
| 19 | ∞ (error) | -inf | 0 | Scaling up GANs for Text-to-Image Synthesis ⚠️ |
| 20 | ∞ (error) | -inf | 0 | Diffusion policy: Visuomotor policy learning via action diff... ⚠️ |
| 21 | ∞ (error) | -inf | 0 | Understanding Diffusion Objectives as the ELBO with Simple D... ⚠️ |
| 22 | ∞ (error) | -inf | 0 | simple diffusion: End-to-end diffusion for high resolution i... ⚠️ |
| 23 | ∞ (error) | -inf | 0 | ConvNeXt V2: Co-designing and Scaling ConvNets with Masked A... ⚠️ |
| 24 | ∞ (error) | -inf | 0 | Scalable Diffusion Models with Transformers ⚠️ |
| 25 | ∞ (error) | -inf | 0 | Flow Matching for Generative Modeling ⚠️ |
| 26 | ∞ (error) | -inf | 0 | Flow Straight and Fast: Learning to Generate and Transfer Da... ⚠️ |
| 27 | ∞ (error) | -inf | 0 | Classifier-Free Diffusion Guidance ⚠️ |
| 28 | ∞ (error) | -inf | 0 | StyleGAN-XL: Scaling StyleGAN to Large Diverse Datasets ⚠️ |
| 29 | ∞ (error) | -inf | 0 | High-Resolution Image Synthesis with Latent Diffusion Models ⚠️ |
| 30 | ∞ (error) | -inf | 0 | Masked Autoencoders Are Scalable Vision Learners ⚠️ |
| 31 | ∞ (error) | -inf | 0 | Diffusion Models Beat GANs on Image Synthesis ⚠️ |
| 32 | ∞ (error) | -inf | 0 | RoFormer: Enhanced Transformer with Rotary Position Embeddin... ⚠️ |
| 33 | ∞ (error) | -inf | 0 | Learning Transferable Visual Models From Natural Language Su... ⚠️ |
| 34 | ∞ (error) | -inf | 0 | Taming Transformers for High-Resolution Image Synthesis ⚠️ |
| 35 | ∞ (error) | -inf | 0 | Score-Based Generative Modeling through Stochastic Different... ⚠️ |
| 36 | ∞ (error) | -inf | 0 | Exploring Simple Siamese Representation Learning ⚠️ |
| 37 | ∞ (error) | -inf | 0 | An Image is Worth 16x16 Words: Transformers for Image Recogn... ⚠️ |
| 38 | ∞ (error) | -inf | 0 | Query-Key Normalization for Transformers ⚠️ |
| 39 | ∞ (error) | -inf | 0 | Denoising Diffusion Probabilistic Models ⚠️ |
| 40 | ∞ (error) | -inf | 0 | Improved Baselines with Momentum Contrastive Learning ⚠️ |
| 41 | ∞ (error) | -inf | 0 | A Simple Framework for Contrastive Learning of Visual Repres... ⚠️ |
| 42 | ∞ (error) | -inf | 0 | GLU Variants Improve Transformer ⚠️ |
| 43 | ∞ (error) | -inf | 0 | Root Mean Square Layer Normalization ⚠️ |
| 44 | ∞ (error) | -inf | 0 | Large Scale GAN Training for High Fidelity Natural Image Syn... ⚠️ |
| 45 | ∞ (error) | -inf | 0 | Representation Learning with Contrastive Predictive Coding ⚠️ |
| 46 | ∞ (error) | -inf | 0 | Group Normalization ⚠️ |
| 47 | ∞ (error) | -inf | 0 | The Unreasonable Effectiveness of Deep Features as a Percept... ⚠️ |
| 48 | ∞ (error) | -inf | 0 | Coulomb GANs: Provably Optimal Nash Equilibria via Potential... ⚠️ |
| 49 | ∞ (error) | -inf | 0 | Density estimation using Real NVP ⚠️ |
| 50 | ∞ (error) | -inf | 0 | Deep Residual Learning for Image Recognition ⚠️ |
| 51 | ∞ (error) | -inf | 0 | Variational Inference with Normalizing Flows ⚠️ |
| 52 | ∞ (error) | -inf | 0 | Training generative neural networks via Maximum Mean Discrep... ⚠️ |
| 53 | ∞ (error) | -inf | 0 | Deep Unsupervised Learning using Nonequilibrium Thermodynami... ⚠️ |
| 54 | ∞ (error) | -inf | 0 | Batch Normalization: Accelerating Deep Network Training by R... ⚠️ |
| 55 | ∞ (error) | -inf | 0 | Generative Moment Matching Networks ⚠️ |

## Model Comparison

| Metric | gpt-5.4 | gpt-4o |
|--------|------|------|
| Self PPL | ∞ (error) | ∞ (error) |
| Random PPL | ∞ (error) | ∞ (error) |
| Mean Cited PPL | ∞ (error) | ∞ (error) |

## Errors

- **gpt-5.4** | Target paper (self): Connection error.
- **gpt-4o** | Target paper (self): Connection error.
- **gpt-5.4** | Improved Mean Flows: On the Challenges o: Connection error.
- **gpt-4o** | Improved Mean Flows: On the Challenges o: Connection error.
- **gpt-5.4** | Adversarial Flow Models: Connection error.
- **gpt-4o** | Adversarial Flow Models: Connection error.
- **gpt-5.4** | PixelDiT: Pixel Diffusion Transformers f: Connection error.
- **gpt-4o** | PixelDiT: Pixel Diffusion Transformers f: Connection error.
- **gpt-5.4** | There is No VAE: End-to-End Pixel-Space : Connection error.
- **gpt-4o** | There is No VAE: End-to-End Pixel-Space : Connection error.
- **gpt-5.4** | Contrastive Flow Matching: Connection error.
- **gpt-4o** | Contrastive Flow Matching: Connection error.
- **gpt-5.4** | Mean Flows for One-step Generative Model: Connection error.
- **gpt-4o** | Mean Flows for One-step Generative Model: Connection error.
- **gpt-5.4** | Inductive Moment Matching: Connection error.
- **gpt-4o** | Inductive Moment Matching: Connection error.
- **gpt-5.4** | Reconstruction vs. Generation: Taming Op: Connection error.
- **gpt-4o** | Reconstruction vs. Generation: Taming Op: Connection error.
- **gpt-5.4** | Normalizing Flows are Capable Generative: Connection error.
- **gpt-4o** | Normalizing Flows are Capable Generative: Connection error.
- **gpt-5.4** | Simpler Diffusion (SiD2): 1.5 FID on Ima: Connection error.
- **gpt-4o** | Simpler Diffusion (SiD2): 1.5 FID on Ima: Connection error.
- **gpt-5.4** | One Step Diffusion via Shortcut Models: Connection error.
- **gpt-4o** | One Step Diffusion via Shortcut Models: Connection error.
- **gpt-5.4** | Representation Alignment for Generation:: Connection error.
- **gpt-4o** | Representation Alignment for Generation:: Connection error.
- **gpt-5.4** | Flow map matching with stochastic interp: Connection error.
- **gpt-4o** | Flow map matching with stochastic interp: Connection error.
- **gpt-5.4** | Score identity Distillation: Exponential: Connection error.
- **gpt-4o** | Score identity Distillation: Exponential: Connection error.
- **gpt-5.4** | One-Step Diffusion with Distribution Mat: Connection error.
- **gpt-4o** | One-Step Diffusion with Distribution Mat: Connection error.
- **gpt-5.4** | Improved Techniques for Training Consist: Connection error.
- **gpt-4o** | Improved Techniques for Training Consist: Connection error.
- **gpt-5.4** | Diff-Instruct: A Universal Approach for : Connection error.
- **gpt-4o** | Diff-Instruct: A Universal Approach for : Connection error.
- **gpt-5.4** | Stochastic Interpolants: A Unifying Fram: Connection error.
- **gpt-4o** | Stochastic Interpolants: A Unifying Fram: Connection error.
- **gpt-5.4** | Scaling up GANs for Text-to-Image Synthe: Connection error.
- **gpt-4o** | Scaling up GANs for Text-to-Image Synthe: Connection error.
- **gpt-5.4** | Diffusion policy: Visuomotor policy lear: Connection error.
- **gpt-4o** | Diffusion policy: Visuomotor policy lear: Connection error.
- **gpt-5.4** | Understanding Diffusion Objectives as th: Connection error.
- **gpt-4o** | Understanding Diffusion Objectives as th: Connection error.
- **gpt-5.4** | simple diffusion: End-to-end diffusion f: Connection error.
- **gpt-4o** | simple diffusion: End-to-end diffusion f: Connection error.
- **gpt-5.4** | ConvNeXt V2: Co-designing and Scaling Co: Connection error.
- **gpt-4o** | ConvNeXt V2: Co-designing and Scaling Co: Connection error.
- **gpt-5.4** | Scalable Diffusion Models with Transform: Connection error.
- **gpt-4o** | Scalable Diffusion Models with Transform: Connection error.
- **gpt-5.4** | Flow Matching for Generative Modeling: Connection error.
- **gpt-4o** | Flow Matching for Generative Modeling: Connection error.
- **gpt-5.4** | Flow Straight and Fast: Learning to Gene: Connection error.
- **gpt-4o** | Flow Straight and Fast: Learning to Gene: Connection error.
- **gpt-5.4** | Classifier-Free Diffusion Guidance: Connection error.
- **gpt-4o** | Classifier-Free Diffusion Guidance: Connection error.
- **gpt-5.4** | StyleGAN-XL: Scaling StyleGAN to Large D: Connection error.
- **gpt-4o** | StyleGAN-XL: Scaling StyleGAN to Large D: Connection error.
- **gpt-5.4** | High-Resolution Image Synthesis with Lat: Connection error.
- **gpt-4o** | High-Resolution Image Synthesis with Lat: Connection error.
- **gpt-5.4** | Masked Autoencoders Are Scalable Vision : Connection error.
- **gpt-4o** | Masked Autoencoders Are Scalable Vision : Connection error.
- **gpt-5.4** | Diffusion Models Beat GANs on Image Synt: Connection error.
- **gpt-4o** | Diffusion Models Beat GANs on Image Synt: Connection error.
- **gpt-5.4** | RoFormer: Enhanced Transformer with Rota: Connection error.
- **gpt-4o** | RoFormer: Enhanced Transformer with Rota: Connection error.
- **gpt-5.4** | Learning Transferable Visual Models From: Connection error.
- **gpt-4o** | Learning Transferable Visual Models From: Connection error.
- **gpt-5.4** | Taming Transformers for High-Resolution : Connection error.
- **gpt-4o** | Taming Transformers for High-Resolution : Connection error.
- **gpt-5.4** | Score-Based Generative Modeling through : Connection error.
- **gpt-4o** | Score-Based Generative Modeling through : Connection error.
- **gpt-5.4** | Exploring Simple Siamese Representation : Connection error.
- **gpt-4o** | Exploring Simple Siamese Representation : Connection error.
- **gpt-5.4** | An Image is Worth 16x16 Words: Transform: Connection error.
- **gpt-4o** | An Image is Worth 16x16 Words: Transform: Connection error.
- **gpt-5.4** | Query-Key Normalization for Transformers: Connection error.
- **gpt-4o** | Query-Key Normalization for Transformers: Connection error.
- **gpt-5.4** | Denoising Diffusion Probabilistic Models: Connection error.
- **gpt-4o** | Denoising Diffusion Probabilistic Models: Connection error.
- **gpt-5.4** | Improved Baselines with Momentum Contras: Connection error.
- **gpt-4o** | Improved Baselines with Momentum Contras: Connection error.
- **gpt-5.4** | A Simple Framework for Contrastive Learn: Connection error.
- **gpt-4o** | A Simple Framework for Contrastive Learn: Connection error.
- **gpt-5.4** | GLU Variants Improve Transformer: Connection error.
- **gpt-4o** | GLU Variants Improve Transformer: Connection error.
- **gpt-5.4** | Root Mean Square Layer Normalization: Connection error.
- **gpt-4o** | Root Mean Square Layer Normalization: Connection error.
- **gpt-5.4** | Large Scale GAN Training for High Fideli: Connection error.
- **gpt-4o** | Large Scale GAN Training for High Fideli: Connection error.
- **gpt-5.4** | Representation Learning with Contrastive: Connection error.
- **gpt-4o** | Representation Learning with Contrastive: Connection error.
- **gpt-5.4** | Group Normalization: Connection error.
- **gpt-4o** | Group Normalization: Connection error.
- **gpt-5.4** | The Unreasonable Effectiveness of Deep F: Connection error.
- **gpt-4o** | The Unreasonable Effectiveness of Deep F: Connection error.
- **gpt-5.4** | Coulomb GANs: Provably Optimal Nash Equi: Connection error.
- **gpt-4o** | Coulomb GANs: Provably Optimal Nash Equi: Connection error.
- **gpt-5.4** | Density estimation using Real NVP: Connection error.
- **gpt-4o** | Density estimation using Real NVP: Connection error.
- **gpt-5.4** | Deep Residual Learning for Image Recogni: Connection error.
- **gpt-4o** | Deep Residual Learning for Image Recogni: Connection error.
- **gpt-5.4** | Variational Inference with Normalizing F: Connection error.
- **gpt-4o** | Variational Inference with Normalizing F: Connection error.
- **gpt-5.4** | Training generative neural networks via : Connection error.
- **gpt-4o** | Training generative neural networks via : Connection error.
- **gpt-5.4** | Deep Unsupervised Learning using Nonequi: Connection error.
- **gpt-4o** | Deep Unsupervised Learning using Nonequi: Connection error.
- **gpt-5.4** | Batch Normalization: Accelerating Deep N: Connection error.
- **gpt-4o** | Batch Normalization: Accelerating Deep N: Connection error.
- **gpt-5.4** | Generative Moment Matching Networks: Connection error.
- **gpt-4o** | Generative Moment Matching Networks: Connection error.
