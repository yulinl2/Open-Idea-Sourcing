# Reconstruction Dispatch Summary

**Timestamp:** run04-lei-candes-quick  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  
**Papers:** 1  
**Version:** staged_reconstruct_v0_3_0  

## Paper: 2103.04984
URL: https://arxiv.org/abs/2103.04984  
Text source: pdf

### Condition: `with_refs`

| Mode | Status | Chars | Tokens (in/out) | Time | Score |
|------|--------|-------|-----------------|------|-------|
| abstract | OK | 2,260 | 754/434 | 9.5s | 3.2 |
| mindmap | OK | 4,038 | 876/863 | 20.2s | 3.7 |

### Condition: `no_refs`

| Mode | Status | Chars | Tokens (in/out) | Time | Score |
|------|--------|-------|-----------------|------|-------|
| abstract | OK | 2,050 | 602/388 | 9.5s | 3.5 |
| mindmap | OK | 4,881 | 724/1,001 | 22.8s | 3.3 |

### Comparison: `with_refs` vs `no_refs`

| Mode | Score (with_refs) | Score (no_refs) | Delta | Ref Impact |
|------|-----------|-----------|-------|------------|
| abstract | 3.2 | 3.5 | -0.3 | ≈ |
| mindmap | 3.7 | 3.3 | +0.4 | + |

### Novelty Gap Analysis

**abstract:** The student misses the paper's actual contribution: using conformal inference directly for counterfactual and ITE prediction intervals, not creating a new 'doubly robust conformal' method. The original paper applies weighted conformal inference to handle covariate shift and shows this naturally inherits doubly robust properties through the weighting scheme, rather than proposing a novel combination of doubly robust estimation with conformal prediction.

**mindmap:** The student correctly identifies the use of weighted conformal prediction for causal inference but misses the paper's specific innovation: using weighted split-CQR (conformal quantile regression) rather than general conformal prediction, and the particular way the paper handles the two distinct challenges of counterfactual inference for in-study vs out-of-study subjects. The paper's actual contribution is more nuanced than just 'combining weighted conformal with causal inference.'
