---
title: Geo-Perplexity Analysis
target: "Conformal Inference"
source: "https://arxiv.org/abs/2006.06138"
models: ['gpt-4o']
generated: 2026-04-05 08:26 UTC
---

# Geo-Perplexity Analysis: Conformal Inference

## Overview

- **Target paper**: Conformal Inference
- **Source**: `https://arxiv.org/abs/2006.06138`
- **Models evaluated**: gpt-4o
- **Cited references found**: 92
- **References with extracted text**: 65
- **Generated**: 2026-04-05 08:26 UTC

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

PPL(target | target) = **1.000012**
- Avg logprob: -0.0000
- Tokens echoed: 1697 across 3 chunks
- Context tokens: 1697

### Cited Reference Perplexities

**Statistics** (n=65 valid, 0 errored):
- Mean PPL: 1.000584
- Median PPL: 1.000122
- Std: 0.000745
- Range: [1.000011, 1.003182]
- Mean PPL/self ratio: 1.000572
- Max PPL/self ratio: 1.003170

| Rank | PPL | PPL/self | Ctx Tokens | Echo Tokens | Source | Reference |
|------|-----|---------|------------|-------------|--------|-----------|
| 1 | 1.000011 | 0.999999 | 1429 | 1697 | full-text(LLM) | Classification with Valid and Adaptive Coverage |
| 2 | 1.000011 | 0.999999 | 734 | 1697 | full-text(LLM) | Assessing Treatment Effect Variation in Observatio… |
| 3 | 1.000011 | 0.999999 | 2714 | 1697 | full-text(LLM) | Causal inference by using invariant prediction: id… |
| 4 | 1.000015 | 1.000003 | 1681 | 1697 | full-text(LLM) | Automated versus Do-It-Yourself Methods for Causal… |
| 5 | 1.000016 | 1.000004 | 3172 | 1697 | full-text(LLM) | The Augmented Synthetic Control Method |
| 6 | 1.000018 | 1.000006 | 2973 | 1697 | full-text(LLM) | Conditional validity of inductive conformal predic… |
| 7 | 1.000019 | 1.000007 | 817 | 1697 | full-text(LLM) | Estimation and Inference of Heterogeneous Treatmen… |
| 8 | 1.000020 | 1.000008 | 1614 | 1697 | full-text(LLM) | Conformal prediction intervals for the individual … |
| 9 | 1.000021 | 1.000009 | 1757 | 1697 | full-text(LLM) | Conformal Prediction Under Covariate Shift |
| 10 | 1.000023 | 1.000011 | 614 | 1697 | full-text(LLM) | bartMachine: Machine Learning with Bayesian Additi… |
| 11 | 1.000023 | 1.000011 | 207 | 1697 | abstract | A national experiment reveals where a growth minds… |
| 12 | 1.000024 | 1.000012 | 1068 | 1697 | full-text(LLM) | Orthogonal Statistical Learning |
| 13 | 1.000025 | 1.000013 | 48 | 1697 | S2-TLDR | Efficient estimation of average treatment effects … |
| 14 | 1.000027 | 1.000015 | 872 | 1697 | full-text(LLM) | Quasi-oracle estimation of heterogeneous treatment… |
| 15 | 1.000028 | 1.000016 | 3046 | 1697 | full-text(LLM) | Cross-conformal predictors |
| 16 | 1.000028 | 1.000016 | 1003 | 1697 | full-text(LLM) | Towards optimal doubly robust estimation of hetero… |
| 17 | 1.000032 | 1.000020 | 840 | 1697 | full-text(LLM) | Synthetic Difference In Differences |
| 18 | 1.000032 | 1.000020 | 1354 | 1697 | full-text(LLM) | Distribution-Free Predictive Inference for Regress… |
| 19 | 1.000032 | 1.000020 | 2492 | 1697 | full-text(LLM) | A tutorial on conformal prediction |
| 20 | 1.000034 | 1.000022 | 266 | 1697 | full-text(LLM) | External Validity: From Do-Calculus to Transportab… |
| 21 | 1.000036 | 1.000024 | 2722 | 1697 | full-text(LLM) | Overlap in observational studies with high-dimensi… |
| 22 | 1.000049 | 1.000037 | 669 | 1697 | full-text(LLM) | Bayesian regression tree models for causal inferen… |
| 23 | 1.000050 | 1.000038 | 35 | 1697 | S2-TLDR | Quantile Regression |
| 24 | 1.000065 | 1.000053 | 685 | 1697 | full-text(LLM) | Conformalized Quantile Regression |
| 25 | 1.000065 | 1.000053 | 30 | 1697 | S2-TLDR | Estimating Heterogeneous Treatment Effects with Ob… |
| 26 | 1.000068 | 1.000056 | 829 | 1697 | full-text(LLM) | Metalearners for estimating heterogeneous treatmen… |
| 27 | 1.000068 | 1.000056 | 1210 | 1697 | full-text(LLM) | Demystifying Double Robustness: A Comparison of Al… |
| 28 | 1.000070 | 1.000058 | 1111 | 1697 | full-text(LLM) | Predictive inference with the jackknife+ |
| 29 | 1.000077 | 1.000065 | 1888 | 1697 | full-text(LLM) | Least Ambiguous Set-Valued Classifiers With Bounde… |
| 30 | 1.000092 | 1.000080 | 572 | 1697 | full-text(LLM) | Generalized random forests |
| 31 | 1.000106 | 1.000094 | 42 | 1697 | S2-TLDR | Estimating Heterogeneous Treatment Effects and the… |
| 32 | 1.000114 | 1.000102 | 521 | 1697 | full-text(LLM) | Confidence intervals for random forests: the jackk… |
| 33 | 1.000122 | 1.000110 | 403 | 1697 | abstract | Use of directed acyclic graphs (DAGs) in applied h… |
| 34 | 1.000167 | 1.000155 | 3458 | 1697 | full-text(LLM) | Comment: Demystifying Double Robustness: A Compari… |
| 35 | 1.000222 | 1.000210 | 721 | 1697 | full-text(LLM) | Hedging Predictions in Machine Learning: The Secon… |
| 36 | 1.000346 | 1.000334 | 34 | 1697 | S2-TLDR | Causation, Prediction, and Search |
| 37 | 1.000414 | 1.000402 | 471 | 1697 | abstract | Evaluation of Differences in Individual Treatment … |
| 38 | 1.000417 | 1.000405 | 636 | 1697 | full-text(LLM) | Robust Inference Using Inverse Probability Weighti… |
| 39 | 1.000500 | 1.000488 | 188 | 1542 | abstract | Inference on finite-population treatment effects u… |
| 40 | 1.000599 | 1.000587 | 916 | 1697 | full-text(LLM) | The limits of distribution-free conditional predic… |
| 41 | 1.000616 | 1.000604 | 244 | 1542 | abstract | The conditional permutation test for independence … |
| 42 | 1.000720 | 1.000708 | 328 | 1542 | full-text(LLM) | On-line predictive linear regression |
| 43 | 1.000756 | 1.000744 | 383 | 1542 | full-text(LLM) | Augmented minimax linear estimation |
| 44 | 1.000758 | 1.000746 | 368 | 950 | full-text(LLM) | Semiparametric efficiency in GMM models with auxil… |
| 45 | 1.000813 | 1.000801 | 152 | 950 | abstract | Causal Processes in Psychology Are Heterogeneous |
| 46 | 1.000877 | 1.000865 | 282 | 1542 | full-text(LLM) | BART: Bayesian Additive Regression Trees |
| 47 | 1.000904 | 1.000892 | 249 | 950 | abstract | The use of propensity scores to assess the general… |
| 48 | 1.001003 | 1.000991 | 48 | 1542 | S2-TLDR | Causal Inference in Statistics: A Primer |
| 49 | 1.001028 | 1.001016 | 1670 | 1542 | full-text(LLM) | A comparison of some conformal quantile regression… |
| 50 | 1.001032 | 1.001020 | 60 | 950 | S2-TLDR | Maternal pesticide exposure from multiple sources … |
| 51 | 1.001067 | 1.001055 | 48 | 950 | S2-TLDR | Greedy function approximation: A gradient boosting… |
| 52 | 1.001071 | 1.001059 | 37 | 1542 | S2-TLDR | Quantile Regression Forests |
| 53 | 1.001132 | 1.001120 | 67 | 1542 | S2-TLDR | NBER WORKING PAPER SERIES MATRIX COMPLETION METHOD… |
| 54 | 1.001148 | 1.001136 | 63 | 950 | S2-TLDR | Toward a perception-based theory of probabilistic … |
| 55 | 1.001308 | 1.001296 | 38 | 1542 | S2-TLDR | Estimation and Accuracy After Model Selection |
| 56 | 1.001375 | 1.001363 | 29 | 950 | S2-TLDR | Who Benefits Most from College? |
| 57 | 1.001442 | 1.001430 | 48 | 950 | S2-TLDR | Conformal Prediction for Reliable Machine Learning… |
| 58 | 1.001449 | 1.001437 | 58 | 950 | S2-TLDR | Single World Intervention Graphs ( SWIGs ) : A Uni… |
| 59 | 1.001470 | 1.001458 | 32 | 950 | S2-TLDR | Book Reviews : Discovering Causal Structure: Artif… |
| 60 | 1.001487 | 1.001475 | 48 | 950 | S2-TLDR | Algorithmic Learning in a Random World |
| 61 | 1.001852 | 1.001840 | 40 | 950 | S2-TLDR | Distribution‐free prediction bands for non‐paramet… |
| 62 | 1.002219 | 1.002207 | 27 | 795 | abstract | The Book of Why: The New Science of Cause and Effe… |
| 63 | 1.002297 | 1.002285 | 52 | 795 | S2-TLDR | Transductive conformal predictors |
| 64 | 1.002876 | 1.002864 | 45 | 795 | S2-TLDR | Distribution-Free Prediction Sets |
| 65 | 1.003182 | 1.003170 | 38 | 795 | S2-TLDR | Conditional validity of inductive conformal predic… |

### Distribution of PPL / self ratio

Values >1 mean the reference makes the target harder to predict than itself.

```
  PPL/self
    0.999999–  1.000263 │ ████████████████████████████████████████ (35)
    1.000263–  1.000527 │ ████ (4)
    1.000527–  1.000792 │ █████ (5)
    1.000792–  1.001056 │ ████████ (7)
    1.001056–  1.001320 │ ████ (4)
    1.001320–  1.001584 │ █████ (5)
    1.001584–  1.001849 │ █ (1)
    1.001849–  1.002113 │  (0)
    1.002113–  1.002377 │ ██ (2)
    1.002377–  1.002641 │  (0)
    1.002641–  1.002906 │ █ (1)
    1.002906–  1.003170 │ █ (1)
```

### Distribution of raw PPL

```
  PPL
    1.000011–  1.000275 │ ████████████████████████████████████████ (35)
    1.000275–  1.000539 │ ████ (4)
    1.000539–  1.000804 │ █████ (5)
    1.000804–  1.001068 │ ████████ (7)
    1.001068–  1.001332 │ ████ (4)
    1.001332–  1.001596 │ █████ (5)
    1.001596–  1.001861 │ █ (1)
    1.001861–  1.002125 │  (0)
    1.002125–  1.002389 │ ██ (2)
    1.002389–  1.002653 │  (0)
    1.002653–  1.002918 │ █ (1)
    1.002918–  1.003182 │ █ (1)
```
