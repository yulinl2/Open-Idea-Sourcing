# Reconstruction Dispatch Summary

**Timestamp:** 2026-04-08T10-44-36Z  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  
**Papers:** 1  
**Version:** staged_reconstruct_v0_6_0  

## Paper: 2006.06138
URL: https://arxiv.org/abs/2006.06138  
Text source: pdf

### Condition: `with_refs`

| Mode | Status | Chars | Tokens (in/out) | Time | Score |
|------|--------|-------|-----------------|------|-------|
| abstract | OK (3R) | 2,507 | — | — | 3.2 |
| mindmap | OK (4R) | 4,229 | — | — | 4.2 |
| problem | OK (5R) | 7,123 | — | — | 3.4 |
| problem_method | OK (5R) | 10,979 | — | — | 3.2 |

### Iterative Refinement Trajectories

**with_refs/abstract** (3 rounds): 2.8 -> 3.2 -> 3.2 | score plateau (delta=0.00) and hint stable

**with_refs/mindmap** (4 rounds): 3.8 -> 3.8 -> 3.0 -> 4.2 | teacher recommended stop

**with_refs/problem** (5 rounds): 3.0 -> 3.4 -> 3.0 -> 3.4 -> 3.4 | reached max rounds (5)

**with_refs/problem_method** (5 rounds): 2.8 -> 3.0 -> 2.8 -> 2.8 -> 3.2 | reached max rounds (5)
