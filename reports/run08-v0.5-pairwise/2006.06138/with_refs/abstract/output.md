# Reconstruction: abstract
**Paper:** 2006.06138  
**Condition:** with_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

**Conformal Prediction for Individual Treatment Effects with Distribution-Free Coverage Guarantees**

Estimating heterogeneous treatment effects is crucial for personalized decision-making in medicine and policy, yet existing machine learning approaches for conditional average treatment effects (CATE) provide poor uncertainty quantification. The fundamental challenge is that individual treatment effects are never directly observable—we only see one potential outcome per individual. Current methods either rely on strong parametric assumptions or fail to provide valid coverage guarantees, limiting their reliability in high-stakes applications.

We propose **Weighted Conformal Causal Prediction**, a novel framework that extends conformal prediction to provide distribution-free prediction intervals for individual treatment effects. Our approach leverages the weighted conformal methodology of Tibshirani et al. (2020) but addresses the unique challenges of causal inference. For individuals within the study, we construct prediction intervals for the unobserved potential outcome using propensity score reweighting to handle treatment assignment imbalances. For new individuals, we develop a doubly-weighted procedure that accounts for both treatment assignment probabilities and covariate shift between study and target populations.

The key innovation is a **causal conformity score** that measures how well an individual's observed outcome conforms to others with similar covariates and treatment status, weighted by inverse propensity scores. We prove that our intervals achieve exact finite-sample coverage under randomized experiments and maintain approximate validity under unconfoundedness in observational studies. The method requires no parametric assumptions about outcome models and is robust to CATE estimation errors.

Our framework provides the first distribution-free approach for individual treatment effect uncertainty quantification with theoretical guarantees, enabling reliable personalized treatment recommendations even when underlying models are misspecified. The method handles both within-study inference and generalization to new populations, addressing critical gaps in current causal machine learning methodology.
