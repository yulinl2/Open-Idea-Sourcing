# Reconstruction Dispatch Summary

**Timestamp:** run05-full-eval  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  
**Papers:** 3  
**Version:** staged_reconstruct_v0_3_0  

## Paper: 2006.06138
URL: https://arxiv.org/abs/2006.06138  
Text source: abstract_fallback

### Condition: `with_refs`

| Mode | Status | Chars | Tokens (in/out) | Time | Score |
|------|--------|-------|-----------------|------|-------|
| abstract | OK | 2,032 | 655/376 | 10.2s | 3.7 |
| mindmap | OK | 3,540 | 777/743 | 17.9s | 4.0 |
| problem | OK | 4,839 | 709/1,458 | 26.8s | 4.7 |
| problem_method | OK | 8,214 | 726/2,658 | 47.8s | 4.5 |
| full_guided | OK | 18,907 | 857/5,216 | 93.1s | 4.0 |
| full_freestyle | OK | 20,277 | 723/4,933 | 90.5s | 4.0 |

### Condition: `no_refs`

| Mode | Status | Chars | Tokens (in/out) | Time | Score |
|------|--------|-------|-----------------|------|-------|
| abstract | OK | 2,025 | 503/399 | 10.1s | 3.3 |
| mindmap | OK | 4,445 | 625/916 | 23.0s | 3.8 |
| problem | OK | 4,447 | 557/1,295 | 23.1s | 3.8 |
| problem_method | OK | 7,593 | 574/2,625 | 43.6s | 4.3 |
| full_guided | OK | 17,931 | 705/4,650 | 88.1s | 3.8 |
| full_freestyle | OK | 18,168 | 571/4,587 | 86.7s | 4.3 |

### Comparison: `with_refs` vs `no_refs`

| Mode | Score (with_refs) | Score (no_refs) | Delta | Ref Impact |
|------|-----------|-----------|-------|------------|
| abstract | 3.7 | 3.3 | +0.4 | + |
| mindmap | 4.0 | 3.8 | +0.2 | ≈ |
| problem | 4.7 | 3.8 | +0.9 | + |
| problem_method | 4.5 | 4.3 | +0.2 | ≈ |
| full_guided | 4.0 | 3.8 | +0.2 | ≈ |
| full_freestyle | 4.0 | 4.3 | -0.3 | ≈ |

### Novelty Gap Analysis

**abstract:** The student incorrectly frames this as extending conformal prediction to loss control, when the actual paper develops a simpler threshold-based calibration method that directly controls expected loss without using conformal prediction machinery. The paper adjusts prediction sets via a single threshold parameter calibrated on holdout data, not through conformity scores and conformal quantiles.

**mindmap:** The student correctly identifies extending conformal prediction to loss control, but misses the paper's key insight of using a single threshold parameter calibrated on holdout data. The actual paper's approach is simpler and more elegant - it doesn't require complex loss quantile estimation or adaptive weighting, just threshold calibration to control expected loss directly.

**problem:** The student correctly identifies the core innovation of moving from coverage to general risk control, but doesn't fully capture that the key insight is using a single threshold parameter calibrated on holdout data to adjust prediction sets. The abstract emphasizes this threshold-based approach as the central mechanism, which the student's formulation doesn't explicitly highlight.

**problem_method:** The student correctly identifies the core innovation of controlling expected loss rather than just coverage, but may have over-specified the threshold-based approach. The original paper likely presents a more general framework that works for 'any underlying model' without necessarily requiring a specific threshold parameterization.

**full_guided:** The student correctly identifies the core concept of controlling expected loss for prediction sets but misses the paper's key insight about adjusting sets via a single threshold parameter calibrated on holdout data. The student's 'Conformal Risk Control' framing and algorithm are more complex than the actual paper's elegant single-threshold approach. The actual paper likely uses a simpler threshold adjustment mechanism rather than the student's threshold selection over all possible score values.

**full_freestyle:** The student correctly identifies the core concept of controlling expected loss for prediction sets, but misses the key simplicity of the original approach. The actual paper uses a single threshold parameter calibrated on a holdout set, while the student develops a more complex conformal framework with quantile-based methods. The original's elegance lies in its directness - adjusting one threshold to control loss - rather than the elaborate conformal machinery the student constructs.

## Paper: 2602.04770
URL: https://arxiv.org/abs/2602.04770  
Text source: abstract_fallback

### Condition: `with_refs`

| Mode | Status | Chars | Tokens (in/out) | Time | Score |
|------|--------|-------|-----------------|------|-------|
| abstract | OK | 1,997 | 684/367 | 8.9s | 3.3 |
| mindmap | OK | 3,616 | 806/724 | 17.5s | 3.7 |
| problem | OK | 5,303 | 738/1,676 | 31.8s | 4.7 |
| problem_method | OK | 8,234 | 755/2,747 | 49.1s | 4.0 |
| full_guided | OK | 25,518 | 886/6,475 | 121.0s | 4.0 |
| full_freestyle | OK | 23,764 | 752/5,577 | 107.9s | 4.2 |

### Condition: `no_refs`

| Mode | Status | Chars | Tokens (in/out) | Time | Score |
|------|--------|-------|-----------------|------|-------|
| abstract | OK | 1,997 | 532/363 | 9.0s | 3.3 |
| mindmap | OK | 3,819 | 654/781 | 20.7s | 3.5 |
| problem | OK | 5,970 | 586/1,884 | 33.1s | 4.5 |
| problem_method | OK | 8,214 | 603/2,756 | 47.6s | 3.8 |
| full_guided | OK | 29,832 | 734/7,036 | 137.7s | 3.8 |
| full_freestyle | OK | 19,827 | 600/4,757 | 87.2s | 3.7 |

### Comparison: `with_refs` vs `no_refs`

| Mode | Score (with_refs) | Score (no_refs) | Delta | Ref Impact |
|------|-----------|-----------|-------|------------|
| abstract | 3.3 | 3.3 | +0.0 | ≈ |
| mindmap | 3.7 | 3.5 | +0.2 | ≈ |
| problem | 4.7 | 4.5 | +0.2 | ≈ |
| problem_method | 4.0 | 3.8 | +0.2 | ≈ |
| full_guided | 4.0 | 3.8 | +0.2 | ≈ |
| full_freestyle | 4.2 | 3.7 | +0.5 | + |

### Novelty Gap Analysis

**abstract:** The student missed the key insight of jointly training a regression model and score function by minimizing a differentiable approximation to interval length. Instead, they proposed a bi-level optimization with coverage constraints and a safety fallback mechanism, which differs from the paper's approach of maintaining coverage through a conformal calibration step after optimization.

**mindmap:** The student proposes a meta-learning framework with fallback mechanisms and ensemble approaches, while the actual paper directly optimizes a differentiable approximation to interval length jointly with the regression model. The student missed the key insight of using a soft surrogate loss for interval length that enables end-to-end training.

**problem:** The student correctly identifies learning score functions as the key innovation but doesn't capture the specific approach of 'optimizing a differentiable approximation to interval length' or the joint training of regression model and score function mentioned in the abstract. The formulation is more general than the paper's specific method.

**problem_method:** The student proposes a data-splitting approach for score learning, while the actual paper optimizes a differentiable approximation to interval length and jointly trains the regression model and score function. The student missed the key insight about joint optimization and the soft surrogate for prediction interval length.

**full_guided:** The student proposes a two-stage meta-learning approach with separate auxiliary data for learning score functions, while the original paper jointly trains regression and score functions by optimizing a differentiable approximation to interval length. The student missed the key insight of joint training and soft surrogate optimization, instead proposing a more conservative approach that separates score learning from the main task.

**full_freestyle:** The student's bi-level optimization framework with separate validation/calibration sets differs from the original's joint training of regression model and score function. The original optimizes a differentiable approximation to interval length, while the student proposes a more complex two-phase approach that may not capture the paper's actual unified optimization strategy.

## Paper: 2103.04984
URL: https://arxiv.org/abs/2103.04984  
Text source: pdf

### Condition: `with_refs`

| Mode | Status | Chars | Tokens (in/out) | Time | Score |
|------|--------|-------|-----------------|------|-------|
| abstract | OK | 1,975 | 707/370 | 8.1s | 3.5 |
| mindmap | OK | 3,689 | 829/827 | 17.2s | 3.5 |
| problem | OK | 5,778 | 761/1,732 | 34.1s | 4.0 |
| problem_method | OK | 8,796 | 778/2,770 | 48.8s | 3.3 |
| full_guided | OK | 18,928 | 909/4,871 | 90.7s | 3.2 |
| full_freestyle | OK | 31,565 | 775/8,095 | 139.3s | 4.3 |

### Condition: `no_refs`

| Mode | Status | Chars | Tokens (in/out) | Time | Score |
|------|--------|-------|-----------------|------|-------|
| abstract | OK | 2,037 | 555/380 | 10.0s | 3.3 |
| mindmap | OK | 4,114 | 677/893 | 19.3s | 3.3 |
| problem | OK | 5,187 | 609/1,469 | 29.7s | 3.8 |
| problem_method | OK | 8,683 | 626/3,070 | 52.6s | 3.2 |
| full_guided | OK | 17,008 | 757/4,030 | 75.2s | 3.3 |
| full_freestyle | OK | 30,009 | 623/8,192 | 146.3s | 3.8 |

### Comparison: `with_refs` vs `no_refs`

| Mode | Score (with_refs) | Score (no_refs) | Delta | Ref Impact |
|------|-----------|-----------|-------|------------|
| abstract | 3.5 | 3.3 | +0.2 | ≈ |
| mindmap | 3.5 | 3.3 | +0.2 | ≈ |
| problem | 4.0 | 3.8 | +0.2 | ≈ |
| problem_method | 3.3 | 3.2 | +0.1 | ≈ |
| full_guided | 3.2 | 3.3 | -0.1 | ≈ |
| full_freestyle | 4.3 | 3.8 | +0.5 | + |

### Novelty Gap Analysis

**abstract:** The student correctly identifies the doubly robust property and conformal inference combination, but misses the paper's specific contribution of using conformal quantile regression (CQR) rather than generic conformal prediction. The original paper's key insight is adapting weighted split-CQR specifically for counterfactual inference, with careful treatment of the likelihood ratio weighting scheme for different inferential targets.

**mindmap:** The student correctly identifies the need for conformal prediction in causal inference but misses the paper's actual key insight: using weighted conformal inference to handle the covariate shift between treated/control groups (not between factual/counterfactual). The paper doesn't frame counterfactual inference as a covariate shift problem in the way the student suggests, but rather recognizes that observing Y(1) requires reweighting from P(X|T=1) to the target distribution.

**problem:** The student correctly identifies the need for distribution-free prediction intervals but misses the paper's key insight about using weighted conformal inference to handle propensity score weighting. They also don't capture the doubly robust property - that coverage holds if either the outcome model OR propensity score is well-estimated, not requiring both.

**problem_method:** The student proposes doubly robust pseudo-outcomes as the core innovation, but the actual paper's key insight is applying weighted conformal quantile regression (CQR) directly to observed outcomes in treated/control groups. The paper doesn't construct pseudo-outcomes but rather uses weighted CQR with propensity score-based weights to handle covariate shift between treatment groups and target populations. The student missed that the 'doubly robust' property refers to coverage validity when either propensity scores OR conditional quantiles are well-estimated, not to constructing doubly robust estimators.

**full_guided:** The student missed the paper's core innovation: using conformal inference to construct prediction intervals for counterfactuals and ITEs with finite-sample coverage guarantees. Instead, they proposed a doubly robust estimation approach in Stage 1, which is standard in causal inference. The original paper's key insight is applying weighted conformal quantile regression (CQR) directly to the counterfactual inference problem, not combining doubly robust estimation with conformal prediction.

**full_freestyle:** The student correctly identifies the core innovation of applying conformal prediction to causal inference, but misses some key technical details from the original paper: (1) the specific formulation of weighted split-CQR for handling propensity scores, (2) the precise doubly robust property that provides coverage (not just consistency) when either model is correct, and (3) the theoretical analysis showing near-exact coverage under bounded likelihood ratios. The student's 'pseudo-outcome approach' is conceptually similar but less sophisticated than the original's direct application of weighted conformal quantile regression.
