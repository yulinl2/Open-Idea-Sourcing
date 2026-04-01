---
title: Geo-Perplexity Analysis
target: "Conformal Inference"
source: "https://arxiv.org/abs/2006.06138"
models: ['gpt-5.4', 'gpt-4o']
generated: 2026-04-01 16:58 UTC
---

# Geo-Perplexity Analysis: Conformal Inference

## Overview

- **Target paper**: Conformal Inference
- **Source**: `https://arxiv.org/abs/2006.06138`
- **Models evaluated**: gpt-5.4, gpt-4o
- **Cited references found**: 93
- **References with extracted text**: 44
- **Generated**: 2026-04-01 16:58 UTC

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

**Statistics** (n=0 valid of 44 total):
- Mean: 0.00
- Median: 0.00
- Std: 0.00
- Min: 0.00
- Max: 0.00

| Rank | PPL | Avg LogProb | Tokens | Reference |
|------|-----|-------------|--------|-----------|
| 1 | ∞ (error) | -inf | 0 | Classification with Valid and Adaptive Coverage ⚠️ |
| 2 | ∞ (error) | -inf | 0 | Conformal prediction intervals for the individual treatment ... ⚠️ |
| 3 | ∞ (error) | -inf | 0 | Towards optimal doubly robust estimation of heterogeneous ca... ⚠️ |
| 4 | ∞ (error) | -inf | 0 | Use of directed acyclic graphs (DAGs) in applied health rese... ⚠️ |
| 5 | ∞ (error) | -inf | 0 | Evaluation of Differences in Individual Treatment Response i... ⚠️ |
| 6 | ∞ (error) | -inf | 0 | A comparison of some conformal quantile regression methods ⚠️ |
| 7 | ∞ (error) | -inf | 0 | Inference on finite-population treatment effects under limit... ⚠️ |
| 8 | ∞ (error) | -inf | 0 | A national experiment reveals where a growth mindset improve... ⚠️ |
| 9 | ∞ (error) | -inf | 0 | Assessing Treatment Effect Variation in Observational Studie... ⚠️ |
| 10 | ∞ (error) | -inf | 0 | Predictive inference with the jackknife+ ⚠️ |
| 11 | ∞ (error) | -inf | 0 | Conformalized Quantile Regression ⚠️ |
| 12 | ∞ (error) | -inf | 0 | Conformal Prediction Under Covariate Shift ⚠️ |
| 13 | ∞ (error) | -inf | 0 | Causal Processes in Psychology Are Heterogeneous ⚠️ |
| 14 | ∞ (error) | -inf | 0 | The limits of distribution-free conditional predictive infer... ⚠️ |
| 15 | ∞ (error) | -inf | 0 | Orthogonal Statistical Learning ⚠️ |
| 16 | ∞ (error) | -inf | 0 | Synthetic Difference In Differences ⚠️ |
| 17 | ∞ (error) | -inf | 0 | The Augmented Synthetic Control Method ⚠️ |
| 18 | ∞ (error) | -inf | 0 | Robust Inference Using Inverse Probability Weighting ⚠️ |
| 19 | ∞ (error) | -inf | 0 | The conditional permutation test for independence while cont... ⚠️ |
| 20 | ∞ (error) | -inf | 0 | The Book of Why: The New Science of Cause and Effect ⚠️ |
| 21 | ∞ (error) | -inf | 0 | Quasi-oracle estimation of heterogeneous treatment effects ⚠️ |
| 22 | ∞ (error) | -inf | 0 | Augmented minimax linear estimation ⚠️ |
| 23 | ∞ (error) | -inf | 0 | Overlap in observational studies with high-dimensional covar... ⚠️ |
| 24 | ∞ (error) | -inf | 0 | Automated versus Do-It-Yourself Methods for Causal Inference... ⚠️ |
| 25 | ∞ (error) | -inf | 0 | Bayesian regression tree models for causal inference: regula... ⚠️ |
| 26 | ∞ (error) | -inf | 0 | Metalearners for estimating heterogeneous treatment effects ... ⚠️ |
| 27 | ∞ (error) | -inf | 0 | Generalized random forests ⚠️ |
| 28 | ∞ (error) | -inf | 0 | Least Ambiguous Set-Valued Classifiers With Bounded Error Le... ⚠️ |
| 29 | ∞ (error) | -inf | 0 | Distribution-Free Predictive Inference for Regression ⚠️ |
| 30 | ∞ (error) | -inf | 0 | Estimation and Inference of Heterogeneous Treatment Effects ... ⚠️ |
| 31 | ∞ (error) | -inf | 0 | Causal inference by using invariant prediction: identificati... ⚠️ |
| 32 | ∞ (error) | -inf | 0 | External Validity: From Do-Calculus to Transportability Acro... ⚠️ |
| 33 | ∞ (error) | -inf | 0 | bartMachine: Machine Learning with Bayesian Additive Regress... ⚠️ |
| 34 | ∞ (error) | -inf | 0 | Confidence intervals for random forests: the jackknife and t... ⚠️ |
| 35 | ∞ (error) | -inf | 0 | Conditional validity of inductive conformal predictors ⚠️ |
| 36 | ∞ (error) | -inf | 0 | Cross-conformal predictors ⚠️ |
| 37 | ∞ (error) | -inf | 0 | The use of propensity scores to assess the generalizability ... ⚠️ |
| 38 | ∞ (error) | -inf | 0 | BART: Bayesian Additive Regression Trees ⚠️ |
| 39 | ∞ (error) | -inf | 0 | Comment: Demystifying Double Robustness: A Comparison of Alt... ⚠️ |
| 40 | ∞ (error) | -inf | 0 | Demystifying Double Robustness: A Comparison of Alternative ... ⚠️ |
| 41 | ∞ (error) | -inf | 0 | A tutorial on conformal prediction ⚠️ |
| 42 | ∞ (error) | -inf | 0 | Semiparametric efficiency in GMM models with auxiliary data ⚠️ |
| 43 | ∞ (error) | -inf | 0 | Hedging Predictions in Machine Learning: The Second Computer... ⚠️ |
| 44 | ∞ (error) | -inf | 0 | On-line predictive linear regression ⚠️ |

## Results: gpt-4o

### Self-Perplexity (baseline)

PPL(target | target) = **∞ (error)**
- Avg logprob: -inf
- Tokens evaluated: 0
- Error: Connection error.

### Cited Reference Perplexities

**Statistics** (n=0 valid of 44 total):
- Mean: 0.00
- Median: 0.00
- Std: 0.00
- Min: 0.00
- Max: 0.00

| Rank | PPL | Avg LogProb | Tokens | Reference |
|------|-----|-------------|--------|-----------|
| 1 | ∞ (error) | -inf | 0 | Classification with Valid and Adaptive Coverage ⚠️ |
| 2 | ∞ (error) | -inf | 0 | Conformal prediction intervals for the individual treatment ... ⚠️ |
| 3 | ∞ (error) | -inf | 0 | Towards optimal doubly robust estimation of heterogeneous ca... ⚠️ |
| 4 | ∞ (error) | -inf | 0 | Use of directed acyclic graphs (DAGs) in applied health rese... ⚠️ |
| 5 | ∞ (error) | -inf | 0 | Evaluation of Differences in Individual Treatment Response i... ⚠️ |
| 6 | ∞ (error) | -inf | 0 | A comparison of some conformal quantile regression methods ⚠️ |
| 7 | ∞ (error) | -inf | 0 | Inference on finite-population treatment effects under limit... ⚠️ |
| 8 | ∞ (error) | -inf | 0 | A national experiment reveals where a growth mindset improve... ⚠️ |
| 9 | ∞ (error) | -inf | 0 | Assessing Treatment Effect Variation in Observational Studie... ⚠️ |
| 10 | ∞ (error) | -inf | 0 | Predictive inference with the jackknife+ ⚠️ |
| 11 | ∞ (error) | -inf | 0 | Conformalized Quantile Regression ⚠️ |
| 12 | ∞ (error) | -inf | 0 | Conformal Prediction Under Covariate Shift ⚠️ |
| 13 | ∞ (error) | -inf | 0 | Causal Processes in Psychology Are Heterogeneous ⚠️ |
| 14 | ∞ (error) | -inf | 0 | The limits of distribution-free conditional predictive infer... ⚠️ |
| 15 | ∞ (error) | -inf | 0 | Orthogonal Statistical Learning ⚠️ |
| 16 | ∞ (error) | -inf | 0 | Synthetic Difference In Differences ⚠️ |
| 17 | ∞ (error) | -inf | 0 | The Augmented Synthetic Control Method ⚠️ |
| 18 | ∞ (error) | -inf | 0 | Robust Inference Using Inverse Probability Weighting ⚠️ |
| 19 | ∞ (error) | -inf | 0 | The conditional permutation test for independence while cont... ⚠️ |
| 20 | ∞ (error) | -inf | 0 | The Book of Why: The New Science of Cause and Effect ⚠️ |
| 21 | ∞ (error) | -inf | 0 | Quasi-oracle estimation of heterogeneous treatment effects ⚠️ |
| 22 | ∞ (error) | -inf | 0 | Augmented minimax linear estimation ⚠️ |
| 23 | ∞ (error) | -inf | 0 | Overlap in observational studies with high-dimensional covar... ⚠️ |
| 24 | ∞ (error) | -inf | 0 | Automated versus Do-It-Yourself Methods for Causal Inference... ⚠️ |
| 25 | ∞ (error) | -inf | 0 | Bayesian regression tree models for causal inference: regula... ⚠️ |
| 26 | ∞ (error) | -inf | 0 | Metalearners for estimating heterogeneous treatment effects ... ⚠️ |
| 27 | ∞ (error) | -inf | 0 | Generalized random forests ⚠️ |
| 28 | ∞ (error) | -inf | 0 | Least Ambiguous Set-Valued Classifiers With Bounded Error Le... ⚠️ |
| 29 | ∞ (error) | -inf | 0 | Distribution-Free Predictive Inference for Regression ⚠️ |
| 30 | ∞ (error) | -inf | 0 | Estimation and Inference of Heterogeneous Treatment Effects ... ⚠️ |
| 31 | ∞ (error) | -inf | 0 | Causal inference by using invariant prediction: identificati... ⚠️ |
| 32 | ∞ (error) | -inf | 0 | External Validity: From Do-Calculus to Transportability Acro... ⚠️ |
| 33 | ∞ (error) | -inf | 0 | bartMachine: Machine Learning with Bayesian Additive Regress... ⚠️ |
| 34 | ∞ (error) | -inf | 0 | Confidence intervals for random forests: the jackknife and t... ⚠️ |
| 35 | ∞ (error) | -inf | 0 | Conditional validity of inductive conformal predictors ⚠️ |
| 36 | ∞ (error) | -inf | 0 | Cross-conformal predictors ⚠️ |
| 37 | ∞ (error) | -inf | 0 | The use of propensity scores to assess the generalizability ... ⚠️ |
| 38 | ∞ (error) | -inf | 0 | BART: Bayesian Additive Regression Trees ⚠️ |
| 39 | ∞ (error) | -inf | 0 | Comment: Demystifying Double Robustness: A Comparison of Alt... ⚠️ |
| 40 | ∞ (error) | -inf | 0 | Demystifying Double Robustness: A Comparison of Alternative ... ⚠️ |
| 41 | ∞ (error) | -inf | 0 | A tutorial on conformal prediction ⚠️ |
| 42 | ∞ (error) | -inf | 0 | Semiparametric efficiency in GMM models with auxiliary data ⚠️ |
| 43 | ∞ (error) | -inf | 0 | Hedging Predictions in Machine Learning: The Second Computer... ⚠️ |
| 44 | ∞ (error) | -inf | 0 | On-line predictive linear regression ⚠️ |

## Model Comparison

| Metric | gpt-5.4 | gpt-4o |
|--------|------|------|
| Self PPL | ∞ (error) | ∞ (error) |
| Random PPL | ∞ (error) | ∞ (error) |
| Mean Cited PPL | ∞ (error) | ∞ (error) |

## Errors

- **gpt-5.4** | Target paper (self): Connection error.
- **gpt-4o** | Target paper (self): Connection error.
- **gpt-5.4** | Classification with Valid and Adaptive C: Connection error.
- **gpt-4o** | Classification with Valid and Adaptive C: Connection error.
- **gpt-5.4** | Conformal prediction intervals for the i: Connection error.
- **gpt-4o** | Conformal prediction intervals for the i: Connection error.
- **gpt-5.4** | Towards optimal doubly robust estimation: Connection error.
- **gpt-4o** | Towards optimal doubly robust estimation: Connection error.
- **gpt-5.4** | Use of directed acyclic graphs (DAGs) in: Connection error.
- **gpt-4o** | Use of directed acyclic graphs (DAGs) in: Connection error.
- **gpt-5.4** | Evaluation of Differences in Individual : Connection error.
- **gpt-4o** | Evaluation of Differences in Individual : Connection error.
- **gpt-5.4** | A comparison of some conformal quantile : Connection error.
- **gpt-4o** | A comparison of some conformal quantile : Connection error.
- **gpt-5.4** | Inference on finite-population treatment: Connection error.
- **gpt-4o** | Inference on finite-population treatment: Connection error.
- **gpt-5.4** | A national experiment reveals where a gr: Connection error.
- **gpt-4o** | A national experiment reveals where a gr: Connection error.
- **gpt-5.4** | Assessing Treatment Effect Variation in : Connection error.
- **gpt-4o** | Assessing Treatment Effect Variation in : Connection error.
- **gpt-5.4** | Predictive inference with the jackknife+: Connection error.
- **gpt-4o** | Predictive inference with the jackknife+: Connection error.
- **gpt-5.4** | Conformalized Quantile Regression: Connection error.
- **gpt-4o** | Conformalized Quantile Regression: Connection error.
- **gpt-5.4** | Conformal Prediction Under Covariate Shi: Connection error.
- **gpt-4o** | Conformal Prediction Under Covariate Shi: Connection error.
- **gpt-5.4** | Causal Processes in Psychology Are Heter: Connection error.
- **gpt-4o** | Causal Processes in Psychology Are Heter: Connection error.
- **gpt-5.4** | The limits of distribution-free conditio: Connection error.
- **gpt-4o** | The limits of distribution-free conditio: Connection error.
- **gpt-5.4** | Orthogonal Statistical Learning: Connection error.
- **gpt-4o** | Orthogonal Statistical Learning: Connection error.
- **gpt-5.4** | Synthetic Difference In Differences: Connection error.
- **gpt-4o** | Synthetic Difference In Differences: Connection error.
- **gpt-5.4** | The Augmented Synthetic Control Method: Connection error.
- **gpt-4o** | The Augmented Synthetic Control Method: Connection error.
- **gpt-5.4** | Robust Inference Using Inverse Probabili: Connection error.
- **gpt-4o** | Robust Inference Using Inverse Probabili: Connection error.
- **gpt-5.4** | The conditional permutation test for ind: Connection error.
- **gpt-4o** | The conditional permutation test for ind: Connection error.
- **gpt-5.4** | The Book of Why: The New Science of Caus: Connection error.
- **gpt-4o** | The Book of Why: The New Science of Caus: Connection error.
- **gpt-5.4** | Quasi-oracle estimation of heterogeneous: Connection error.
- **gpt-4o** | Quasi-oracle estimation of heterogeneous: Connection error.
- **gpt-5.4** | Augmented minimax linear estimation: Connection error.
- **gpt-4o** | Augmented minimax linear estimation: Connection error.
- **gpt-5.4** | Overlap in observational studies with hi: Connection error.
- **gpt-4o** | Overlap in observational studies with hi: Connection error.
- **gpt-5.4** | Automated versus Do-It-Yourself Methods : Connection error.
- **gpt-4o** | Automated versus Do-It-Yourself Methods : Connection error.
- **gpt-5.4** | Bayesian regression tree models for caus: Connection error.
- **gpt-4o** | Bayesian regression tree models for caus: Connection error.
- **gpt-5.4** | Metalearners for estimating heterogeneou: Connection error.
- **gpt-4o** | Metalearners for estimating heterogeneou: Connection error.
- **gpt-5.4** | Generalized random forests: Connection error.
- **gpt-4o** | Generalized random forests: Connection error.
- **gpt-5.4** | Least Ambiguous Set-Valued Classifiers W: Connection error.
- **gpt-4o** | Least Ambiguous Set-Valued Classifiers W: Connection error.
- **gpt-5.4** | Distribution-Free Predictive Inference f: Connection error.
- **gpt-4o** | Distribution-Free Predictive Inference f: Connection error.
- **gpt-5.4** | Estimation and Inference of Heterogeneou: Connection error.
- **gpt-4o** | Estimation and Inference of Heterogeneou: Connection error.
- **gpt-5.4** | Causal inference by using invariant pred: Connection error.
- **gpt-4o** | Causal inference by using invariant pred: Connection error.
- **gpt-5.4** | External Validity: From Do-Calculus to T: Connection error.
- **gpt-4o** | External Validity: From Do-Calculus to T: Connection error.
- **gpt-5.4** | bartMachine: Machine Learning with Bayes: Connection error.
- **gpt-4o** | bartMachine: Machine Learning with Bayes: Connection error.
- **gpt-5.4** | Confidence intervals for random forests:: Connection error.
- **gpt-4o** | Confidence intervals for random forests:: Connection error.
- **gpt-5.4** | Conditional validity of inductive confor: Connection error.
- **gpt-4o** | Conditional validity of inductive confor: Connection error.
- **gpt-5.4** | Cross-conformal predictors: Connection error.
- **gpt-4o** | Cross-conformal predictors: Connection error.
- **gpt-5.4** | The use of propensity scores to assess t: Connection error.
- **gpt-4o** | The use of propensity scores to assess t: Connection error.
- **gpt-5.4** | BART: Bayesian Additive Regression Trees: Connection error.
- **gpt-4o** | BART: Bayesian Additive Regression Trees: Connection error.
- **gpt-5.4** | Comment: Demystifying Double Robustness:: Connection error.
- **gpt-4o** | Comment: Demystifying Double Robustness:: Connection error.
- **gpt-5.4** | Demystifying Double Robustness: A Compar: Connection error.
- **gpt-4o** | Demystifying Double Robustness: A Compar: Connection error.
- **gpt-5.4** | A tutorial on conformal prediction: Connection error.
- **gpt-4o** | A tutorial on conformal prediction: Connection error.
- **gpt-5.4** | Semiparametric efficiency in GMM models : Connection error.
- **gpt-4o** | Semiparametric efficiency in GMM models : Connection error.
- **gpt-5.4** | Hedging Predictions in Machine Learning:: Connection error.
- **gpt-4o** | Hedging Predictions in Machine Learning:: Connection error.
- **gpt-5.4** | On-line predictive linear regression: Connection error.
- **gpt-4o** | On-line predictive linear regression: Connection error.
