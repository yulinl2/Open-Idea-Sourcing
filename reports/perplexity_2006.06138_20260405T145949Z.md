---
title: Geo-Perplexity Analysis
target: "Conformal Inference"
source: "https://arxiv.org/abs/2006.06138"
models: ['gpt-4o']
generated: 2026-04-05 14:59 UTC
---

# Geo-Perplexity Analysis: Conformal Inference

## Overview

- **Target paper**: Conformal Inference
- **Source**: `https://arxiv.org/abs/2006.06138`
- **Models evaluated**: gpt-4o
- **Cited references found**: 92
- **References with extracted text**: 65
- **Generated**: 2026-04-05 14:59 UTC

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

PPL(target | target) = **1.000008**
- Avg logprob: -0.0000
- Tokens echoed: 1697 across 3 chunks
- Context tokens: 1697

### Cited Reference Perplexities

**Statistics** (n=65 valid, 0 errored):
- Mean PPL: 1.000610
- Median PPL: 1.000200
- Std: 0.000831
- Range: [1.000006, 1.003886]
- Mean PPL/self ratio: 1.000602
- Max PPL/self ratio: 1.003878

| Rank | PPL | PPL/self | Ctx Tokens | Echo Tokens | Source | Reference |
|------|-----|---------|------------|-------------|--------|-----------|
| 1 | 1.000006 | 0.999998 | 1614 | 922 | full-text(LLM) | Conformal prediction intervals for the individual … ⚠ |
| 2 | 1.000013 | 1.000005 | 2714 | 1697 | full-text(LLM) | Causal inference by using invariant prediction: id… |
| 3 | 1.000013 | 1.000005 | 1068 | 1697 | full-text(LLM) | Orthogonal Statistical Learning |
| 4 | 1.000014 | 1.000006 | 471 | 1697 | abstract | Evaluation of Differences in Individual Treatment … |
| 5 | 1.000015 | 1.000007 | 1681 | 1697 | full-text(LLM) | Automated versus Do-It-Yourself Methods for Causal… |
| 6 | 1.000016 | 1.000008 | 2492 | 1697 | full-text(LLM) | A tutorial on conformal prediction |
| 7 | 1.000018 | 1.000010 | 817 | 1697 | full-text(LLM) | Estimation and Inference of Heterogeneous Treatmen… |
| 8 | 1.000019 | 1.000011 | 1210 | 1697 | full-text(LLM) | Demystifying Double Robustness: A Comparison of Al… |
| 9 | 1.000020 | 1.000011 | 829 | 1697 | full-text(LLM) | Metalearners for estimating heterogeneous treatmen… |
| 10 | 1.000020 | 1.000012 | 734 | 1697 | full-text(LLM) | Assessing Treatment Effect Variation in Observatio… |
| 11 | 1.000020 | 1.000012 | 2722 | 1697 | full-text(LLM) | Overlap in observational studies with high-dimensi… |
| 12 | 1.000020 | 1.000012 | 614 | 1697 | full-text(LLM) | bartMachine: Machine Learning with Bayesian Additi… |
| 13 | 1.000022 | 1.000013 | 3046 | 1697 | full-text(LLM) | Cross-conformal predictors |
| 14 | 1.000023 | 1.000015 | 3172 | 1532 | full-text(LLM) | The Augmented Synthetic Control Method ⚠ |
| 15 | 1.000027 | 1.000019 | 872 | 1697 | full-text(LLM) | Quasi-oracle estimation of heterogeneous treatment… |
| 16 | 1.000028 | 1.000020 | 1888 | 1697 | full-text(LLM) | Least Ambiguous Set-Valued Classifiers With Bounde… |
| 17 | 1.000028 | 1.000020 | 266 | 1697 | full-text(LLM) | External Validity: From Do-Calculus to Transportab… |
| 18 | 1.000032 | 1.000024 | 207 | 1697 | abstract | A national experiment reveals where a growth minds… |
| 19 | 1.000033 | 1.000025 | 1111 | 1697 | full-text(LLM) | Predictive inference with the jackknife+ |
| 20 | 1.000035 | 1.000027 | 1429 | 1697 | full-text(LLM) | Classification with Valid and Adaptive Coverage |
| 21 | 1.000036 | 1.000028 | 685 | 1697 | full-text(LLM) | Conformalized Quantile Regression |
| 22 | 1.000039 | 1.000031 | 1354 | 1697 | full-text(LLM) | Distribution-Free Predictive Inference for Regress… |
| 23 | 1.000059 | 1.000051 | 636 | 1697 | full-text(LLM) | Robust Inference Using Inverse Probability Weighti… |
| 24 | 1.000065 | 1.000056 | 188 | 1697 | abstract | Inference on finite-population treatment effects u… |
| 25 | 1.000073 | 1.000064 | 30 | 1697 | S2-TLDR | Estimating Heterogeneous Treatment Effects with Ob… |
| 26 | 1.000086 | 1.000078 | 572 | 1697 | full-text(LLM) | Generalized random forests |
| 27 | 1.000093 | 1.000085 | 48 | 1697 | S2-TLDR | Efficient estimation of average treatment effects … |
| 28 | 1.000101 | 1.000092 | 35 | 1697 | S2-TLDR | Quantile Regression |
| 29 | 1.000108 | 1.000099 | 403 | 1697 | abstract | Use of directed acyclic graphs (DAGs) in applied h… |
| 30 | 1.000111 | 1.000102 | 521 | 1697 | full-text(LLM) | Confidence intervals for random forests: the jackk… |
| 31 | 1.000113 | 1.000105 | 1670 | 1697 | full-text(LLM) | A comparison of some conformal quantile regression… |
| 32 | 1.000131 | 1.000123 | 3458 | 1697 | full-text(LLM) | Comment: Demystifying Double Robustness: A Compari… |
| 33 | 1.000200 | 1.000192 | 840 | 1697 | full-text(LLM) | Synthetic Difference In Differences |
| 34 | 1.000215 | 1.000206 | 669 | 1697 | full-text(LLM) | Bayesian regression tree models for causal inferen… |
| 35 | 1.000308 | 1.000300 | 67 | 1697 | S2-TLDR | NBER WORKING PAPER SERIES MATRIX COMPLETION METHOD… |
| 36 | 1.000345 | 1.000337 | 2973 | 1697 | full-text(LLM) | Conditional validity of inductive conformal predic… |
| 37 | 1.000354 | 1.000346 | 1003 | 1697 | full-text(LLM) | Towards optimal doubly robust estimation of hetero… |
| 38 | 1.000436 | 1.000428 | 244 | 1697 | abstract | The conditional permutation test for independence … |
| 39 | 1.000510 | 1.000502 | 1757 | 1697 | full-text(LLM) | Conformal Prediction Under Covariate Shift |
| 40 | 1.000645 | 1.000637 | 916 | 1697 | full-text(LLM) | The limits of distribution-free conditional predic… |
| 41 | 1.000674 | 1.000666 | 52 | 1542 | S2-TLDR | Transductive conformal predictors |
| 42 | 1.000694 | 1.000686 | 368 | 950 | full-text(LLM) | Semiparametric efficiency in GMM models with auxil… |
| 43 | 1.000755 | 1.000747 | 383 | 1542 | full-text(LLM) | Augmented minimax linear estimation |
| 44 | 1.000801 | 1.000792 | 328 | 1542 | full-text(LLM) | On-line predictive linear regression |
| 45 | 1.000850 | 1.000841 | 282 | 1542 | full-text(LLM) | BART: Bayesian Additive Regression Trees |
| 46 | 1.000892 | 1.000884 | 48 | 1542 | S2-TLDR | Causal Inference in Statistics: A Primer |
| 47 | 1.000903 | 1.000895 | 37 | 1542 | S2-TLDR | Quantile Regression Forests |
| 48 | 1.001006 | 1.000998 | 42 | 950 | S2-TLDR | Estimating Heterogeneous Treatment Effects and the… |
| 49 | 1.001018 | 1.001010 | 27 | 950 | abstract | The Book of Why: The New Science of Cause and Effe… |
| 50 | 1.001051 | 1.001042 | 152 | 950 | abstract | Causal Processes in Psychology Are Heterogeneous |
| 51 | 1.001063 | 1.001054 | 249 | 950 | abstract | The use of propensity scores to assess the general… |
| 52 | 1.001075 | 1.001067 | 721 | 950 | full-text(LLM) | Hedging Predictions in Machine Learning: The Secon… |
| 53 | 1.001172 | 1.001164 | 29 | 950 | S2-TLDR | Who Benefits Most from College? |
| 54 | 1.001189 | 1.001180 | 34 | 950 | S2-TLDR | Causation, Prediction, and Search |
| 55 | 1.001205 | 1.001196 | 40 | 950 | S2-TLDR | Distribution‐free prediction bands for non‐paramet… |
| 56 | 1.001238 | 1.001230 | 63 | 950 | S2-TLDR | Toward a perception-based theory of probabilistic … |
| 57 | 1.001284 | 1.001275 | 38 | 1542 | S2-TLDR | Estimation and Accuracy After Model Selection |
| 58 | 1.001399 | 1.001391 | 32 | 950 | S2-TLDR | Book Reviews : Discovering Causal Structure: Artif… |
| 59 | 1.001451 | 1.001442 | 48 | 950 | S2-TLDR | Conformal Prediction for Reliable Machine Learning… |
| 60 | 1.001467 | 1.001459 | 48 | 950 | S2-TLDR | Algorithmic Learning in a Random World |
| 61 | 1.001606 | 1.001598 | 60 | 950 | S2-TLDR | Maternal pesticide exposure from multiple sources … |
| 62 | 1.001822 | 1.001813 | 58 | 795 | S2-TLDR | Single World Intervention Graphs ( SWIGs ) : A Uni… |
| 63 | 1.003157 | 1.003149 | 45 | 795 | S2-TLDR | Distribution-Free Prediction Sets |
| 64 | 1.003537 | 1.003529 | 38 | 795 | S2-TLDR | Conditional validity of inductive conformal predic… |
| 65 | 1.003886 | 1.003878 | 48 | 795 | S2-TLDR | Greedy function approximation: A gradient boosting… |

### Distribution of PPL / self ratio

Values >1 mean the reference makes the target harder to predict than itself.

```
  PPL/self
    0.999998–  1.000321 │ ████████████████████████████████████████ (35)
    1.000321–  1.000644 │ █████ (5)
    1.000644–  1.000968 │ ████████ (7)
    1.000968–  1.001291 │ ███████████ (10)
    1.001291–  1.001615 │ ████ (4)
    1.001615–  1.001938 │ █ (1)
    1.001938–  1.002261 │  (0)
    1.002261–  1.002585 │  (0)
    1.002585–  1.002908 │  (0)
    1.002908–  1.003231 │ █ (1)
    1.003231–  1.003555 │ █ (1)
    1.003555–  1.003878 │ █ (1)
```

### Distribution of raw PPL

```
  PPL
    1.000006–  1.000329 │ ████████████████████████████████████████ (35)
    1.000329–  1.000653 │ █████ (5)
    1.000653–  1.000976 │ ████████ (7)
    1.000976–  1.001299 │ ███████████ (10)
    1.001299–  1.001623 │ ████ (4)
    1.001623–  1.001946 │ █ (1)
    1.001946–  1.002269 │  (0)
    1.002269–  1.002593 │  (0)
    1.002593–  1.002916 │  (0)
    1.002916–  1.003240 │ █ (1)
    1.003240–  1.003563 │ █ (1)
    1.003563–  1.003886 │ █ (1)
```

## Errors (2 total)

- **gpt-4o** | Conformal prediction intervals for the individual : chunk 1/3: Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-YHtdLrQ8KAel6oYw0LVgAlx7 on tokens per min (TPM): Limit 30000, Used 27299, Requested 3024. Please try again in 646ms. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}
- **gpt-4o** | The Augmented Synthetic Control Method: chunk 3/3: Error code: 429 - {'error': {'message': 'Rate limit reached for gpt-4o in organization org-YHtdLrQ8KAel6oYw0LVgAlx7 on tokens per min (TPM): Limit 30000, Used 29216, Requested 3596. Please try again in 5.624s. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}
