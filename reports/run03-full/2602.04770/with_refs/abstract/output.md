# Reconstruction: abstract
**Paper:** 2602.04770  
**Condition:** with_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Learning Optimal Conformal Score Functions via Risk-Constrained Optimization

Conformal prediction provides finite-sample marginal coverage guarantees for prediction intervals, but the efficiency of these intervals critically depends on the choice of score function used to quantify prediction uncertainty. While existing methods typically rely on heuristic score functions such as absolute residuals or quantile-based measures, there is no principled framework for learning score functions that minimize interval width while preserving the essential coverage guarantee.

We propose a novel approach that frames optimal score function learning as a risk-constrained optimization problem. Our method, called Conformal Score Learning (CSL), jointly optimizes a parametric score function and a prediction model by minimizing expected interval width subject to an empirical coverage constraint. The key insight is to use a smooth approximation of the coverage violation that enables gradient-based optimization while maintaining theoretical guarantees. We employ a Lagrangian formulation with adaptive penalty weighting that automatically balances coverage validity against interval efficiency.

Our approach extends naturally to handle covariate shift by incorporating importance weighting in both the objective and constraint, building upon recent advances in weighted conformal prediction. We establish theoretical properties showing that our learned score functions achieve asymptotic optimality—converging to the shortest possible intervals among all valid conformal predictors as sample size increases. The method is computationally efficient, requiring only standard gradient-based optimization, and can be integrated with any differentiable prediction model.

The primary contributions include: (1) a principled framework for learning optimal conformal score functions, (2) finite-sample coverage guarantees with asymptotic efficiency, (3) extension to covariate shift settings, and (4) practical algorithms with theoretical backing.
