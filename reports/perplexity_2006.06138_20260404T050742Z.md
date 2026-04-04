---
title: Geo-Perplexity Analysis
target: "Conformal Inference"
source: "https://arxiv.org/abs/2006.06138"
models: ['gpt-4o']
generated: 2026-04-04 05:07 UTC
---

# Geo-Perplexity Analysis: Conformal Inference

## Overview

- **Target paper**: Conformal Inference
- **Source**: `https://arxiv.org/abs/2006.06138`
- **Models evaluated**: gpt-4o
- **Cited references found**: 92
- **References with extracted text**: 44
- **Generated**: 2026-04-04 05:07 UTC

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
- Tokens echoed: 1697 across 3 chunks
- Context tokens: 1697

### Random Field Reference (control)

PPL(target | random) = **1.000229** (ratio vs self: 1.000223)
- Reference: Adaptive Conformal Inference Under Distribution Shift
- Source: full-text(LLM)
- Avg logprob: -0.0002
- Tokens echoed: 1697 across 3 chunks
- Context tokens: 984

### Cited Reference Perplexities

**Statistics** (n=44 valid, 0 errored):
- Mean PPL: 1.000285
- Median PPL: 1.000062
- Std: 0.000468
- Range: [1.000008, 1.002376]
- Mean PPL/self ratio: 1.000280
- Max PPL/self ratio: 1.002371

| Rank | PPL | PPL/self | Ctx Tokens | Echo Tokens | Source | Reference |
|------|-----|---------|------------|-------------|--------|-----------|
| 1 | 1.000008 | 1.000003 | 2948 | 1697 | full-text(LLM) | Conditional validity of inductive conformal predic… |
| 2 | 1.000012 | 1.000006 | 2665 | 1697 | full-text(LLM) | The Augmented Synthetic Control Method |
| 3 | 1.000016 | 1.000010 | 1669 | 1697 | full-text(LLM) | Automated versus Do-It-Yourself Methods for Causal… |
| 4 | 1.000016 | 1.000011 | 614 | 1697 | full-text(LLM) | bartMachine: Machine Learning with Bayesian Additi… |
| 5 | 1.000020 | 1.000014 | 950 | 1697 | full-text(LLM) | Cross-conformal predictors |
| 6 | 1.000023 | 1.000017 | 1645 | 1697 | full-text(LLM) | Conformal prediction intervals for the individual … |
| 7 | 1.000023 | 1.000018 | 2502 | 1697 | full-text(LLM) | A tutorial on conformal prediction |
| 8 | 1.000026 | 1.000021 | 207 | 1697 | abstract | A national experiment reveals where a growth minds… |
| 9 | 1.000026 | 1.000021 | 734 | 1697 | full-text(LLM) | Assessing Treatment Effect Variation in Observatio… |
| 10 | 1.000027 | 1.000022 | 383 | 1697 | full-text(LLM) | Augmented minimax linear estimation |
| 11 | 1.000028 | 1.000023 | 1105 | 1697 | full-text(LLM) | Classification with Valid and Adaptive Coverage |
| 12 | 1.000030 | 1.000024 | 730 | 1697 | full-text(LLM) | Synthetic Difference In Differences |
| 13 | 1.000030 | 1.000025 | 921 | 1697 | full-text(LLM) | Estimation and Inference of Heterogeneous Treatmen… |
| 14 | 1.000033 | 1.000027 | 403 | 1697 | abstract | Use of directed acyclic graphs (DAGs) in applied h… |
| 15 | 1.000034 | 1.000029 | 1072 | 1697 | full-text(LLM) | Orthogonal Statistical Learning |
| 16 | 1.000035 | 1.000029 | 266 | 1697 | full-text(LLM) | External Validity: From Do-Calculus to Transportab… |
| 17 | 1.000040 | 1.000034 | 2864 | 1697 | full-text(LLM) | Predictive inference with the jackknife+ |
| 18 | 1.000049 | 1.000044 | 2714 | 1697 | full-text(LLM) | Causal inference by using invariant prediction: id… |
| 19 | 1.000053 | 1.000047 | 2897 | 1697 | full-text(LLM) | The limits of distribution-free conditional predic… |
| 20 | 1.000054 | 1.000049 | 572 | 1697 | full-text(LLM) | Generalized random forests |
| 21 | 1.000056 | 1.000050 | 770 | 1697 | full-text(LLM) | Metalearners for estimating heterogeneous treatmen… |
| 22 | 1.000058 | 1.000052 | 1351 | 1697 | full-text(LLM) | Distribution-Free Predictive Inference for Regress… |
| 23 | 1.000065 | 1.000060 | 1101 | 1697 | full-text(LLM) | Hedging Predictions in Machine Learning: The Secon… |
| 24 | 1.000075 | 1.000069 | 643 | 1697 | full-text(LLM) | Bayesian regression tree models for causal inferen… |
| 25 | 1.000077 | 1.000071 | 2616 | 1697 | full-text(LLM) | Conformal Prediction Under Covariate Shift |
| 26 | 1.000137 | 1.000131 | 2441 | 1697 | full-text(LLM) | Overlap in observational studies with high-dimensi… |
| 27 | 1.000150 | 1.000144 | 1550 | 1697 | full-text(LLM) | A comparison of some conformal quantile regression… |
| 28 | 1.000179 | 1.000174 | 3458 | 1697 | full-text(LLM) | Comment: Demystifying Double Robustness: A Compari… |
| 29 | 1.000180 | 1.000175 | 689 | 1697 | full-text(LLM) | Conformalized Quantile Regression |
| 30 | 1.000187 | 1.000182 | 521 | 1697 | full-text(LLM) | Confidence intervals for random forests: the jackk… |
| 31 | 1.000221 | 1.000216 | 1003 | 1697 | full-text(LLM) | Towards optimal doubly robust estimation of hetero… |
| 32 | 1.000281 | 1.000275 | 1942 | 1697 | full-text(LLM) | Least Ambiguous Set-Valued Classifiers With Bounde… |
| 33 | 1.000313 | 1.000307 | 629 | 1697 | full-text(LLM) | Quasi-oracle estimation of heterogeneous treatment… |
| 34 | 1.000343 | 1.000337 | 471 | 1697 | abstract | Evaluation of Differences in Individual Treatment … |
| 35 | 1.000409 | 1.000404 | 503 | 1542 | full-text(LLM) | On-line predictive linear regression |
| 36 | 1.000440 | 1.000434 | 636 | 1697 | full-text(LLM) | Robust Inference Using Inverse Probability Weighti… |
| 37 | 1.000586 | 1.000580 | 188 | 1542 | abstract | Inference on finite-population treatment effects u… |
| 38 | 1.000709 | 1.000703 | 745 | 950 | full-text(LLM) | Demystifying Double Robustness: A Comparison of Al… |
| 39 | 1.000756 | 1.000751 | 371 | 1542 | full-text(LLM) | Semiparametric efficiency in GMM models with auxil… |
| 40 | 1.000855 | 1.000849 | 282 | 1542 | full-text(LLM) | BART: Bayesian Additive Regression Trees |
| 41 | 1.000949 | 1.000944 | 27 | 950 | abstract | The Book of Why: The New Science of Cause and Effe… |
| 42 | 1.001023 | 1.001018 | 249 | 950 | abstract | The use of propensity scores to assess the general… |
| 43 | 1.001539 | 1.001534 | 244 | 795 | abstract | The conditional permutation test for independence … |
| 44 | 1.002376 | 1.002371 | 152 | 795 | abstract | Causal Processes in Psychology Are Heterogeneous |

### Distribution of PPL / self ratio

Values >1 mean the reference makes the target harder to predict than itself.

```
  PPL/self
    1.000003–  1.000200 │ ████████████████████████████████████████ (30)
    1.000200–  1.000397 │ █████ (4)
    1.000397–  1.000595 │ ████ (3)
    1.000595–  1.000792 │ ██ (2)
    1.000792–  1.000989 │ ██ (2)
    1.000989–  1.001187 │ █ (1)
    1.001187–  1.001384 │  (0)
    1.001384–  1.001582 │ █ (1)
    1.001582–  1.001779 │  (0)
    1.001779–  1.001976 │  (0)
    1.001976–  1.002174 │  (0)
    1.002174–  1.002371 │ █ (1)
```

### Distribution of raw PPL

```
  PPL
    1.000008–  1.000206 │ ████████████████████████████████████████ (30)
    1.000206–  1.000403 │ █████ (4)
    1.000403–  1.000600 │ ████ (3)
    1.000600–  1.000798 │ ██ (2)
    1.000798–  1.000995 │ ██ (2)
    1.000995–  1.001192 │ █ (1)
    1.001192–  1.001390 │  (0)
    1.001390–  1.001587 │ █ (1)
    1.001587–  1.001784 │  (0)
    1.001784–  1.001982 │  (0)
    1.001982–  1.002179 │  (0)
    1.002179–  1.002376 │ █ (1)
```
