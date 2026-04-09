# Reconstruction Dispatch Summary

**Timestamp:** run06-v0.4-antileak  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  
**Papers:** 2  
**Version:** staged_reconstruct_v0_3_1  

## Paper: 2006.06138
URL: https://arxiv.org/abs/2006.06138  
Text source: pdf

### References provided to student

- **arxiv-1904.06019**: Conformal Prediction Under Covariate Shift (2020, NeurIPS) — [https://arxiv.org/abs/1904.06019](https://arxiv.org/abs/1904.06019)
- **arxiv-2006.01474**: Conformal Prediction Intervals for the Individual Treatment Effect (2020, arXiv) — [https://arxiv.org/abs/2006.01474](https://arxiv.org/abs/2006.01474)

### Condition: `with_refs`

| Mode | Status | Chars | Tokens (in/out) | Time | Score |
|------|--------|-------|-----------------|------|-------|
| abstract | OK | 2,427 | 9,040/424 | 13.4s | 3.3 |
| mindmap | OK | 4,299 | 9,162/949 | 25.7s | 3.7 |
| problem | OK | 5,957 | 9,094/1,791 | 36.2s | 4.3 |
| problem_method | OK | 10,685 | 9,111/3,471 | 64.4s | 3.3 |
| full_guided | OK | 20,547 | 9,242/5,391 | 97.7s | 3.8 |
| full_freestyle | OK | 31,265 | 9,108/8,192 | 145.9s | 3.5 |

### Condition: `no_refs`

| Mode | Status | Chars | Tokens (in/out) | Time | Score |
|------|--------|-------|-----------------|------|-------|
| abstract | OK | 2,075 | 615/363 | 9.0s | 3.2 |
| mindmap | OK | 4,057 | 737/799 | 18.9s | 3.5 |
| problem | OK | 6,501 | 669/1,736 | 35.9s | 3.8 |
| problem_method | OK | 10,445 | 686/3,226 | 55.5s | 3.2 |
| full_guided | OK | 25,398 | 817/6,245 | 113.0s | 3.5 |
| full_freestyle | OK | 27,183 | 683/6,342 | 118.6s | 3.5 |

### Comparison: `with_refs` vs `no_refs`

| Mode | Score (with_refs) | Score (no_refs) | Delta | Ref Impact |
|------|-----------|-----------|-------|------------|
| abstract | 3.3 | 3.2 | +0.1 | ≈ |
| mindmap | 3.7 | 3.5 | +0.2 | ≈ |
| problem | 4.3 | 3.8 | +0.5 | + |
| problem_method | 3.3 | 3.2 | +0.1 | ≈ |
| full_guided | 3.8 | 3.5 | +0.3 | ≈ |
| full_freestyle | 3.5 | 3.5 | +0.0 | ≈ |

### Novelty Gap Analysis

**abstract:** The student misses the paper's dual focus on both counterfactual inference and ITE prediction as separate challenges, and doesn't capture the doubly robust property that allows either propensity scores OR conditional quantiles to be well-estimated. The actual paper emphasizes conformal quantile regression (CQR) specifically, not just general conformal prediction.

**mindmap:** The student correctly identifies the use of weighted conformal prediction for causal inference but misses the paper's specific innovation of using it for counterfactual inference first, then extending to ITE. The paper's key insight is the two-step approach: (1) intervals for counterfactuals when one outcome is observed, (2) intervals for ITE when both outcomes are missing. The student also doesn't capture the paper's emphasis on different coverage criteria (ATE, ATT, ATC) and the connection to IPW through propensity scores.

**problem:** The student correctly identifies the core challenge of constructing prediction intervals for ITE but slightly underemphasizes the paper's key insight about the two distinct challenges: (1) intervals for subjects in the study with one observed outcome, and (2) intervals for new subjects with both outcomes missing. The paper's novelty lies in recognizing this distinction and showing how counterfactual inference reduces to a covariate shift problem solvable via weighted conformal inference.

**problem_method:** The student missed the paper's key innovation of using conformal quantile regression (CQR) with specific quantile-based nonconformity scores. Instead, they proposed simple absolute residuals |y - μ̂(x)|, which is a much more basic approach. The original paper's insight was to use max{q̂_αlo(x) - y, y - q̂_αhi(x)} as scores, enabling tighter intervals by leveraging conditional quantile information rather than just conditional means.

**full_guided:** The student correctly identifies conformal prediction for ITE but misses the paper's specific two-stage approach: first constructing counterfactual intervals, then combining them for ITE. The original paper's key insight is using weighted conformal inference to handle covariate shift between treatment groups, which the student captures but doesn't emphasize as the central novelty. The paper also introduces a doubly robust property for coverage that the student mentions but doesn't develop.

**full_freestyle:** The student missed the paper's key innovation: using conformal inference specifically for counterfactual inference and individual treatment effects with doubly robust properties. Instead, they presented a more generic application of conformal prediction to causal inference, focusing on CATE uncertainty rather than the paper's emphasis on prediction intervals for individual counterfactuals Y(1) and Y(0). The original paper's sophisticated use of weighted conformal inference to handle propensity score weighting and achieve finite-sample guarantees even under model misspecification was reduced to a standard covariate shift problem.

## Paper: 2602.04770
URL: https://arxiv.org/abs/2602.04770  
Text source: pdf

### References provided to student

- **arxiv-1904.06019**: Conformal Prediction Under Covariate Shift (2020, NeurIPS) — [https://arxiv.org/abs/1904.06019](https://arxiv.org/abs/1904.06019)
- **arxiv-2006.01474**: Conformal Prediction Intervals for the Individual Treatment Effect (2020, arXiv) — [https://arxiv.org/abs/2006.01474](https://arxiv.org/abs/2006.01474)

### Condition: `with_refs`

| Mode | Status | Chars | Tokens (in/out) | Time | Score |
|------|--------|-------|-----------------|------|-------|
| abstract | OK | 2,441 | 8,943/421 | 13.1s | 3.2 |
| mindmap | OK | 4,678 | 9,065/914 | 25.7s | 2.5 |
| problem | OK | 7,026 | 8,997/1,970 | 39.4s | 3.5 |
| problem_method | OK | 8,383 | 9,014/2,801 | 52.5s | 2.7 |
| full_guided | OK | 21,481 | 9,145/5,351 | 103.1s | 3.7 |
| full_freestyle | OK | 20,397 | 9,011/4,900 | 91.7s | 3.0 |

### Condition: `no_refs`

| Mode | Status | Chars | Tokens (in/out) | Time | Score |
|------|--------|-------|-----------------|------|-------|
| abstract | OK | 1,790 | 518/321 | 9.0s | 2.5 |
| mindmap | OK | 5,042 | 640/980 | 25.5s | 3.0 |
| problem | OK | 6,209 | 572/1,930 | 34.1s | 3.5 |
| problem_method | OK | 8,195 | 589/2,625 | 53.2s | 2.7 |
| full_guided | OK | 19,224 | 720/4,446 | 87.9s | 3.0 |
| full_freestyle | OK | 19,841 | 586/5,099 | 95.0s | 3.7 |

### Comparison: `with_refs` vs `no_refs`

| Mode | Score (with_refs) | Score (no_refs) | Delta | Ref Impact |
|------|-----------|-----------|-------|------------|
| abstract | 3.2 | 2.5 | +0.7 | + |
| mindmap | 2.5 | 3.0 | -0.5 | − |
| problem | 3.5 | 3.5 | +0.0 | ≈ |
| problem_method | 2.7 | 2.7 | +0.0 | ≈ |
| full_guided | 3.7 | 3.0 | +0.7 | + |
| full_freestyle | 3.0 | 3.7 | -0.7 | − |

### Novelty Gap Analysis

**abstract:** The student completely missed the core innovation of 'drifting' - the idea of evolving the pushforward distribution during training time through a drifting field that governs sample movement. Instead, they proposed a standard flow matching approach with importance weighting, which is conceptually very different from the original paper's training-time evolution paradigm.

**mindmap:** The student completely missed the paper's actual contribution of drifting fields that evolve the pushforward distribution during training time. Instead, they proposed using conformal prediction for generative modeling, which is entirely unrelated to the paper's approach of using attraction/repulsion dynamics and kernel-based drifting fields.

**problem:** The student formulates this as a general single-step generation problem with complexity transfer to training time, missing the paper's core insight: the 'drifting' concept where the pushforward distribution evolves during training through a drifting field that governs sample movement. The paper's key innovation is not just about single-step generation, but specifically about how the distribution drifts during training iterations until reaching equilibrium.

**problem_method:** The student completely missed the paper's core contribution of 'drifting fields' that evolve the pushforward distribution during training time. Instead, they proposed a conformal prediction-based approach, which is conceptually unrelated. The original paper introduces a training-time evolution paradigm with anti-symmetric drifting fields, kernel-based sample interactions, and feature-space losses. The student's approach using conformity scores and coverage guarantees is a fundamentally different direction.

**full_guided:** The student proposed Flow Matching based on ODE vector field regression and optimal transport, completely missing the actual paper's key insight of 'drifting' - a training-time evolution of the pushforward distribution through attraction/repulsion forces using kernel-based mean-shift vectors. The actual paper introduces a contrastive-like loss with positive/negative samples and anti-symmetric drifting fields, not continuous normalizing flows.

**full_freestyle:** The student completely missed the core innovation of Drifting Models. The original paper introduces a paradigm where the pushforward distribution evolves during training time through a drifting field that governs sample movement, achieving equilibrium when distributions match. Instead, the student reconstructed Flow Matching - a different existing method that learns vector fields for continuous normalizing flows. The key missing insight is the training-time evolution of the pushforward distribution and the attraction-repulsion mechanism based on positive/negative samples.
