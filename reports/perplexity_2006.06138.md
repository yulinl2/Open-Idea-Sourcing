---
title: Geo-Perplexity Analysis
target: "Conformal Inference"
source: "https://arxiv.org/abs/2006.06138"
models: ['gpt-5.4', 'gpt-4o']
generated: 2026-04-01 22:40 UTC
---

# Geo-Perplexity Analysis: Conformal Inference

## Overview

- **Target paper**: Conformal Inference
- **Source**: `https://arxiv.org/abs/2006.06138`
- **Models evaluated**: gpt-5.4, gpt-4o
- **Cited references found**: 93
- **References with extracted text**: 44
- **Generated**: 2026-04-01 22:40 UTC

## Methodology

**Exact conditional perplexity** via verbatim-echo with logprobs:

1. Reference paper text → system message (~6K tokens context)
2. Target paper text is chunked into ~800-token windows
3. Model is instructed to reproduce each chunk **verbatim**
4. `logprobs=True` returns P(token_i | context, token_1..i-1) for each echoed token
5. **PPL = exp(−(1/N) Σ log p(token_i))** — exact, not approximate

**Interpretation**: Lower PPL → target is more predictable given that reference → reference explains more of the target's content. Higher PPL → target says something the reference doesn't prepare you for.

## Results: gpt-5.4

### Self-Perplexity (lower bound)

PPL(target | target) = **—**
- Avg logprob: —
- Tokens: 0 across 5 chunks
- ⚠ Partial: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.

### Cited Reference Perplexities

**No valid perplexity scores** (44 errors)

| Rank | PPL | Avg LogProb | Tokens | Chunks | Reference |
|------|-----|-------------|--------|--------|-----------|
| 1 | — | — | 0 | 5 | Classification with Valid and Adaptive Coverage ⚠ |
| 2 | — | — | 0 | 5 | Conformal prediction intervals for the individual treat… ⚠ |
| 3 | — | — | 0 | 5 | Towards optimal doubly robust estimation of heterogeneo… ⚠ |
| 4 | — | — | 0 | 5 | Use of directed acyclic graphs (DAGs) in applied health… ⚠ |
| 5 | — | — | 0 | 5 | Evaluation of Differences in Individual Treatment Respo… ⚠ |
| 6 | — | — | 0 | 5 | A comparison of some conformal quantile regression meth… ⚠ |
| 7 | — | — | 0 | 5 | Inference on finite-population treatment effects under … ⚠ |
| 8 | — | — | 0 | 5 | A national experiment reveals where a growth mindset im… ⚠ |
| 9 | — | — | 0 | 5 | Assessing Treatment Effect Variation in Observational S… ⚠ |
| 10 | — | — | 0 | 5 | Predictive inference with the jackknife+ ⚠ |
| 11 | — | — | 0 | 5 | Conformalized Quantile Regression ⚠ |
| 12 | — | — | 0 | 5 | Conformal Prediction Under Covariate Shift ⚠ |
| 13 | — | — | 0 | 5 | Causal Processes in Psychology Are Heterogeneous ⚠ |
| 14 | — | — | 0 | 5 | The limits of distribution-free conditional predictive … ⚠ |
| 15 | — | — | 0 | 5 | Orthogonal Statistical Learning ⚠ |
| 16 | — | — | 0 | 5 | Synthetic Difference In Differences ⚠ |
| 17 | — | — | 0 | 5 | The Augmented Synthetic Control Method ⚠ |
| 18 | — | — | 0 | 5 | Robust Inference Using Inverse Probability Weighting ⚠ |
| 19 | — | — | 0 | 5 | The conditional permutation test for independence while… ⚠ |
| 20 | — | — | 0 | 5 | The Book of Why: The New Science of Cause and Effect ⚠ |
| 21 | — | — | 0 | 5 | Quasi-oracle estimation of heterogeneous treatment effe… ⚠ |
| 22 | — | — | 0 | 5 | Augmented minimax linear estimation ⚠ |
| 23 | — | — | 0 | 5 | Overlap in observational studies with high-dimensional … ⚠ |
| 24 | — | — | 0 | 5 | Automated versus Do-It-Yourself Methods for Causal Infe… ⚠ |
| 25 | — | — | 0 | 5 | Bayesian regression tree models for causal inference: r… ⚠ |
| 26 | — | — | 0 | 5 | Metalearners for estimating heterogeneous treatment eff… ⚠ |
| 27 | — | — | 0 | 5 | Generalized random forests ⚠ |
| 28 | — | — | 0 | 5 | Least Ambiguous Set-Valued Classifiers With Bounded Err… ⚠ |
| 29 | — | — | 0 | 5 | Distribution-Free Predictive Inference for Regression ⚠ |
| 30 | — | — | 0 | 5 | Estimation and Inference of Heterogeneous Treatment Eff… ⚠ |
| 31 | — | — | 0 | 5 | Causal inference by using invariant prediction: identif… ⚠ |
| 32 | — | — | 0 | 5 | External Validity: From Do-Calculus to Transportability… ⚠ |
| 33 | — | — | 0 | 5 | bartMachine: Machine Learning with Bayesian Additive Re… ⚠ |
| 34 | — | — | 0 | 5 | Confidence intervals for random forests: the jackknife … ⚠ |
| 35 | — | — | 0 | 5 | Conditional validity of inductive conformal predictors ⚠ |
| 36 | — | — | 0 | 5 | Cross-conformal predictors ⚠ |
| 37 | — | — | 0 | 5 | The use of propensity scores to assess the generalizabi… ⚠ |
| 38 | — | — | 0 | 5 | BART: Bayesian Additive Regression Trees ⚠ |
| 39 | — | — | 0 | 5 | Comment: Demystifying Double Robustness: A Comparison o… ⚠ |
| 40 | — | — | 0 | 5 | Demystifying Double Robustness: A Comparison of Alterna… ⚠ |
| 41 | — | — | 0 | 5 | A tutorial on conformal prediction ⚠ |
| 42 | — | — | 0 | 5 | Semiparametric efficiency in GMM models with auxiliary … ⚠ |
| 43 | — | — | 0 | 5 | Hedging Predictions in Machine Learning: The Second Com… ⚠ |
| 44 | — | — | 0 | 5 | On-line predictive linear regression ⚠ |

## Results: gpt-4o

### Self-Perplexity (lower bound)

PPL(target | target) = **—**
- Avg logprob: —
- Tokens: 0 across 5 chunks
- ⚠ Partial: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.

### Cited Reference Perplexities

**No valid perplexity scores** (44 errors)

| Rank | PPL | Avg LogProb | Tokens | Chunks | Reference |
|------|-----|-------------|--------|--------|-----------|
| 1 | — | — | 0 | 5 | Classification with Valid and Adaptive Coverage ⚠ |
| 2 | — | — | 0 | 5 | Conformal prediction intervals for the individual treat… ⚠ |
| 3 | — | — | 0 | 5 | Towards optimal doubly robust estimation of heterogeneo… ⚠ |
| 4 | — | — | 0 | 5 | Use of directed acyclic graphs (DAGs) in applied health… ⚠ |
| 5 | — | — | 0 | 5 | Evaluation of Differences in Individual Treatment Respo… ⚠ |
| 6 | — | — | 0 | 5 | A comparison of some conformal quantile regression meth… ⚠ |
| 7 | — | — | 0 | 5 | Inference on finite-population treatment effects under … ⚠ |
| 8 | — | — | 0 | 5 | A national experiment reveals where a growth mindset im… ⚠ |
| 9 | — | — | 0 | 5 | Assessing Treatment Effect Variation in Observational S… ⚠ |
| 10 | — | — | 0 | 5 | Predictive inference with the jackknife+ ⚠ |
| 11 | — | — | 0 | 5 | Conformalized Quantile Regression ⚠ |
| 12 | — | — | 0 | 5 | Conformal Prediction Under Covariate Shift ⚠ |
| 13 | — | — | 0 | 5 | Causal Processes in Psychology Are Heterogeneous ⚠ |
| 14 | — | — | 0 | 5 | The limits of distribution-free conditional predictive … ⚠ |
| 15 | — | — | 0 | 5 | Orthogonal Statistical Learning ⚠ |
| 16 | — | — | 0 | 5 | Synthetic Difference In Differences ⚠ |
| 17 | — | — | 0 | 5 | The Augmented Synthetic Control Method ⚠ |
| 18 | — | — | 0 | 5 | Robust Inference Using Inverse Probability Weighting ⚠ |
| 19 | — | — | 0 | 5 | The conditional permutation test for independence while… ⚠ |
| 20 | — | — | 0 | 5 | The Book of Why: The New Science of Cause and Effect ⚠ |
| 21 | — | — | 0 | 5 | Quasi-oracle estimation of heterogeneous treatment effe… ⚠ |
| 22 | — | — | 0 | 5 | Augmented minimax linear estimation ⚠ |
| 23 | — | — | 0 | 5 | Overlap in observational studies with high-dimensional … ⚠ |
| 24 | — | — | 0 | 5 | Automated versus Do-It-Yourself Methods for Causal Infe… ⚠ |
| 25 | — | — | 0 | 5 | Bayesian regression tree models for causal inference: r… ⚠ |
| 26 | — | — | 0 | 5 | Metalearners for estimating heterogeneous treatment eff… ⚠ |
| 27 | — | — | 0 | 5 | Generalized random forests ⚠ |
| 28 | — | — | 0 | 5 | Least Ambiguous Set-Valued Classifiers With Bounded Err… ⚠ |
| 29 | — | — | 0 | 5 | Distribution-Free Predictive Inference for Regression ⚠ |
| 30 | — | — | 0 | 5 | Estimation and Inference of Heterogeneous Treatment Eff… ⚠ |
| 31 | — | — | 0 | 5 | Causal inference by using invariant prediction: identif… ⚠ |
| 32 | — | — | 0 | 5 | External Validity: From Do-Calculus to Transportability… ⚠ |
| 33 | — | — | 0 | 5 | bartMachine: Machine Learning with Bayesian Additive Re… ⚠ |
| 34 | — | — | 0 | 5 | Confidence intervals for random forests: the jackknife … ⚠ |
| 35 | — | — | 0 | 5 | Conditional validity of inductive conformal predictors ⚠ |
| 36 | — | — | 0 | 5 | Cross-conformal predictors ⚠ |
| 37 | — | — | 0 | 5 | The use of propensity scores to assess the generalizabi… ⚠ |
| 38 | — | — | 0 | 5 | BART: Bayesian Additive Regression Trees ⚠ |
| 39 | — | — | 0 | 5 | Comment: Demystifying Double Robustness: A Comparison o… ⚠ |
| 40 | — | — | 0 | 5 | Demystifying Double Robustness: A Comparison of Alterna… ⚠ |
| 41 | — | — | 0 | 5 | A tutorial on conformal prediction ⚠ |
| 42 | — | — | 0 | 5 | Semiparametric efficiency in GMM models with auxiliary … ⚠ |
| 43 | — | — | 0 | 5 | Hedging Predictions in Machine Learning: The Second Com… ⚠ |
| 44 | — | — | 0 | 5 | On-line predictive linear regression ⚠ |

## Model Comparison

| Metric | gpt-5.4 | gpt-4o |
|--------|--------|--------|
| Self PPL | — | — |
| Random PPL | — | — |
| Mean Cited PPL | — | — |
| Median Cited PPL | — | — |

## Errors (90 total)

- **gpt-5.4** | Target paper (self): chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-4o** | Target paper (self): chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-5.4** | Classification with Valid and Adaptive Coverage: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-4o** | Classification with Valid and Adaptive Coverage: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-5.4** | Conformal prediction intervals for the individual : chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-4o** | Conformal prediction intervals for the individual : chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-5.4** | Towards optimal doubly robust estimation of hetero: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-4o** | Towards optimal doubly robust estimation of hetero: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-5.4** | Use of directed acyclic graphs (DAGs) in applied h: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-4o** | Use of directed acyclic graphs (DAGs) in applied h: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-5.4** | Evaluation of Differences in Individual Treatment : chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-4o** | Evaluation of Differences in Individual Treatment : chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-5.4** | A comparison of some conformal quantile regression: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-4o** | A comparison of some conformal quantile regression: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-5.4** | Inference on finite-population treatment effects u: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-4o** | Inference on finite-population treatment effects u: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-5.4** | A national experiment reveals where a growth minds: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-4o** | A national experiment reveals where a growth minds: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-5.4** | Assessing Treatment Effect Variation in Observatio: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-4o** | Assessing Treatment Effect Variation in Observatio: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-5.4** | Predictive inference with the jackknife+: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-4o** | Predictive inference with the jackknife+: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-5.4** | Conformalized Quantile Regression: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-4o** | Conformalized Quantile Regression: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-5.4** | Conformal Prediction Under Covariate Shift: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-4o** | Conformal Prediction Under Covariate Shift: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-5.4** | Causal Processes in Psychology Are Heterogeneous: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-4o** | Causal Processes in Psychology Are Heterogeneous: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-5.4** | The limits of distribution-free conditional predic: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-4o** | The limits of distribution-free conditional predic: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-5.4** | Orthogonal Statistical Learning: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-4o** | Orthogonal Statistical Learning: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-5.4** | Synthetic Difference In Differences: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-4o** | Synthetic Difference In Differences: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-5.4** | The Augmented Synthetic Control Method: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-4o** | The Augmented Synthetic Control Method: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-5.4** | Robust Inference Using Inverse Probability Weighti: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-4o** | Robust Inference Using Inverse Probability Weighti: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-5.4** | The conditional permutation test for independence : chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-4o** | The conditional permutation test for independence : chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-5.4** | The Book of Why: The New Science of Cause and Effe: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-4o** | The Book of Why: The New Science of Cause and Effe: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-5.4** | Quasi-oracle estimation of heterogeneous treatment: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-4o** | Quasi-oracle estimation of heterogeneous treatment: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-5.4** | Augmented minimax linear estimation: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-4o** | Augmented minimax linear estimation: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-5.4** | Overlap in observational studies with high-dimensi: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-4o** | Overlap in observational studies with high-dimensi: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-5.4** | Automated versus Do-It-Yourself Methods for Causal: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-4o** | Automated versus Do-It-Yourself Methods for Causal: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-5.4** | Bayesian regression tree models for causal inferen: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-4o** | Bayesian regression tree models for causal inferen: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-5.4** | Metalearners for estimating heterogeneous treatmen: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-4o** | Metalearners for estimating heterogeneous treatmen: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-5.4** | Generalized random forests: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-4o** | Generalized random forests: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-5.4** | Least Ambiguous Set-Valued Classifiers With Bounde: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-4o** | Least Ambiguous Set-Valued Classifiers With Bounde: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-5.4** | Distribution-Free Predictive Inference for Regress: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-4o** | Distribution-Free Predictive Inference for Regress: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-5.4** | Estimation and Inference of Heterogeneous Treatmen: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-4o** | Estimation and Inference of Heterogeneous Treatmen: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-5.4** | Causal inference by using invariant prediction: id: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-4o** | Causal inference by using invariant prediction: id: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-5.4** | External Validity: From Do-Calculus to Transportab: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-4o** | External Validity: From Do-Calculus to Transportab: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-5.4** | bartMachine: Machine Learning with Bayesian Additi: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-4o** | bartMachine: Machine Learning with Bayesian Additi: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-5.4** | Confidence intervals for random forests: the jackk: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-4o** | Confidence intervals for random forests: the jackk: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-5.4** | Conditional validity of inductive conformal predic: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-4o** | Conditional validity of inductive conformal predic: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-5.4** | Cross-conformal predictors: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-4o** | Cross-conformal predictors: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-5.4** | The use of propensity scores to assess the general: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-4o** | The use of propensity scores to assess the general: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-5.4** | BART: Bayesian Additive Regression Trees: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-4o** | BART: Bayesian Additive Regression Trees: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-5.4** | Comment: Demystifying Double Robustness: A Compari: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-4o** | Comment: Demystifying Double Robustness: A Compari: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-5.4** | Demystifying Double Robustness: A Comparison of Al: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-4o** | Demystifying Double Robustness: A Comparison of Al: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-5.4** | A tutorial on conformal prediction: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-4o** | A tutorial on conformal prediction: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-5.4** | Semiparametric efficiency in GMM models with auxil: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-4o** | Semiparametric efficiency in GMM models with auxil: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-5.4** | Hedging Predictions in Machine Learning: The Secon: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-4o** | Hedging Predictions in Machine Learning: The Secon: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-5.4** | On-line predictive linear regression: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
- **gpt-4o** | On-line predictive linear regression: chunk 1/5: Connection error.; chunk 2/5: Connection error.; chunk 3/5: Connection error.; chunk 4/5: Connection error.; chunk 5/5: Connection error.
