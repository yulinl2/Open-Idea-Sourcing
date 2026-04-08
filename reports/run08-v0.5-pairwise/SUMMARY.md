# Reconstruction Dispatch Summary

**Timestamp:** run08-v0.5-pairwise  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  
**Papers:** 1  
**Version:** staged_reconstruct_v0_5_0  

## Paper: 2602.04770
URL: https://arxiv.org/abs/2602.04770  
Text source: pdf

### Condition: `with_refs`

| Mode | Status | Chars | Tokens (in/out) | Time | Score |
|------|--------|-------|-----------------|------|-------|
| abstract | OK | 2,214 | 9,077/388 | 11.5s | 2.4 |
| mindmap | OK | 4,735 | 9,199/1,037 | 26.5s | 2.8 |
| problem | OK | 6,677 | 9,131/2,049 | 38.2s | 2.6 |
| problem_method | OK | 7,974 | 9,148/2,475 | 45.9s | 3.0 |
| full_guided | OK | 23,217 | 9,279/5,706 | 106.7s | 3.6 |
| full_freestyle | OK | 16,381 | 9,145/4,314 | 78.4s | 2.8 |

### Condition: `no_refs`

| Mode | Status | Chars | Tokens (in/out) | Time | Score |
|------|--------|-------|-----------------|------|-------|
| abstract | OK | 2,082 | 652/378 | 15.1s | 2.8 |
| mindmap | OK | 4,815 | 774/997 | 25.0s | 3.0 |
| problem | OK | 6,347 | 706/1,751 | 31.0s | 2.6 |
| problem_method | OK | 8,675 | 723/2,774 | 47.3s | 2.6 |
| full_guided | OK | 19,460 | 854/4,676 | 89.2s | 3.0 |
| full_freestyle | OK | 19,380 | 720/4,627 | 84.5s | 3.2 |

### Comparison: `with_refs` vs `no_refs`

| Mode | Score (with_refs) | Score (no_refs) | Delta | Ref Impact |
|------|-----------|-----------|-------|------------|
| abstract | 2.4 | 2.8 | -0.4 | − |
| mindmap | 2.8 | 3.0 | -0.2 | ≈ |
| problem | 2.6 | 2.6 | +0.0 | ≈ |
| problem_method | 3.0 | 2.6 | +0.4 | + |
| full_guided | 3.6 | 3.0 | +0.6 | + |
| full_freestyle | 2.8 | 3.2 | -0.4 | − |

### Novelty Gap Analysis

**abstract:** The paper introduces drifting fields that evolve the pushforward distribution during training through attraction/repulsion dynamics. The student's approach uses conformal prediction theory with coverage guarantees - an entirely different mathematical framework with no conceptual overlap with the drifting mechanism.

**mindmap:** The paper introduces drifting fields V_p,q that govern sample movement during training, with anti-symmetric properties ensuring equilibrium at distribution matching. The student's conformal approach focuses on accept/reject sampling with coverage guarantees - missing the entire concept of training-time distribution evolution through sample drifting.

**problem:** The paper introduces a drifting field V_p,q that evolves the pushforward distribution during training through attraction to data samples and repulsion from generated samples, with anti-symmetric properties ensuring equilibrium. The student instead proposes standard flow matching with conditional flows and vector field learning, completely missing the novel drifting mechanism.

**problem_method:** The paper introduces a drifting field V that moves samples during training iterations, with anti-symmetric properties ensuring equilibrium at distribution matching. The student instead proposes static importance weighting without any notion of sample movement or training-time evolution. The paper's core innovation of xi+1 = xi + V(xi) and the associated fixed-point training objective is completely absent.

**full_guided:** The paper introduces a drifting field V that moves samples during training time, with anti-symmetric properties ensuring equilibrium when distributions match. The student instead uses weighted conformal prediction sets and coverage guarantees - a statistical framework rather than the paper's dynamical system approach with explicit sample movement.

**full_freestyle:** The paper introduces drifting fields that evolve the pushforward distribution during training through attraction/repulsion dynamics. The student's CFN approach uses conformal prediction with coverage guarantees - a fundamentally different statistical framework with no connection to the paper's training-time distribution evolution or equilibrium concepts.
