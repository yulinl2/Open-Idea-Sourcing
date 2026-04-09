# Paper Idea Mindmap

## Core Problem
- Develop finite-sample uncertainty quantification methods for individual treatment effects that handle covariate shift between study and target populations while leveraging the fact that one potential outcome is observed for study subjects.

## Key Observations from References
- Weighted conformal prediction can handle covariate shift when likelihood ratios are known/estimable (Ref: arxiv-1904.06019)
- Standard conformal prediction requires exchangeability, but weighted versions can work under "weighted exchangeability" 
- Conformal methods for individual treatment effects exist but don't address covariate shift or leverage observed outcomes optimally (Ref: arxiv-2006.01474)
- Inverse propensity weighting is the standard tool in causal inference for handling treatment selection bias
- The fundamental challenge is that we never observe both potential outcomes for any individual

## Proposed Approach

### Main Idea
- Develop a **doubly-weighted conformal prediction** framework that combines:
  1. **Propensity weights** to handle treatment assignment bias (standard in causal inference)
  2. **Covariate shift weights** to handle population shift between study and target (from weighted conformal prediction)
- For study subjects: construct intervals for the unobserved counterfactual outcome, then combine with the observed outcome
- For new subjects: construct intervals for both potential outcomes using the doubly-weighted approach

### Sub-ideas

#### Doubly-Weighted Conformal Scores
- Define nonconformity scores that incorporate both treatment propensity weights w₁(x) = 1/π(x) and covariate shift weights w₂(x) = dP_target/dP_study(x)
- Combined weight: w(x,t) = w₁(x)^t × w₂(x) where t indicates treatment status
- This handles both treatment selection and population shift simultaneously

#### Separate Procedures for Study vs. New Subjects  
- **Study subjects**: Use observed outcome Y_obs and predict counterfactual Y_cf using weighted conformal prediction on the opposite treatment group
- **New subjects**: Predict both Y(0) and Y(1) using doubly-weighted conformal prediction, then form interval for τ = Y(1) - Y(0)
- Leverage the partial observability advantage for study subjects

#### Doubly Robust Extensions
- Incorporate outcome regression models μ₀(x), μ₁(x) alongside the weighting
- Use residual-based scores: |Y - μₜ(X)| weighted by w(X,T)
- Achieve robustness: valid inference when either propensity model or outcome model is correct

#### Adaptive Weight Estimation
- Estimate propensity scores π̂(x) using logistic regression or more flexible methods
- Estimate covariate shift ratios using density ratio estimation or discriminative methods
- Handle uncertainty in weight estimation through cross-fitting or sample splitting

## Theoretical Grounding
- Weighted conformal prediction theory (Tibshirani et al.) provides foundation for handling known covariate shifts
- Doubly robust estimation theory suggests combining propensity weighting with outcome modeling
- The key insight: treatment assignment creates one type of "covariate shift" (treated vs. control distributions differ), while study-target population differences create another
- Both can be handled through appropriate weighting in the conformal framework

## Potential Challenges

#### Challenge 1: Weight Estimation Errors
- **Problem**: Estimated weights may be highly variable or biased
- **Solution**: Use cross-fitting to reduce overfitting, implement weight trimming/stabilization, develop theory for estimated weights following recent conformal literature

#### Challenge 2: Finite Sample Performance
- **Problem**: Double weighting may lead to high variance in small samples
- **Solution**: Develop adaptive procedures that blend weighted and unweighted approaches based on effective sample size, implement variance reduction techniques

#### Challenge 3: Strong Overlap Assumptions
- **Problem**: Method requires overlap in both treatment assignment and covariate distributions
- **Solution**: Develop diagnostic tools for overlap assessment, provide guidance on when method is applicable, extend to partial identification when overlap fails

## Connections to Existing Work

#### Extension of Tibshirani et al. (arxiv-1904.06019)
- Their weighted conformal prediction handles covariate shift between train/test distributions
- Our approach extends this by recognizing that causal inference involves an additional "shift" between treatment groups
- We combine their covariate shift weighting with propensity-based weighting from causal inference

#### Extension of Kivaranovic et al. (arxiv-2006.01474) 
- Their work provides conformal intervals for individual treatment effects but assumes exchangeable data
- Our approach handles the more realistic setting where study population differs from target population
- We also leverage the partial observability structure they don't fully exploit (one outcome is observed for study subjects)

#### Novel Contribution
- First to combine weighted conformal prediction with causal inference
- Addresses the fundamental covariate shift problem inherent in counterfactual inference
- Provides both finite-sample and asymptotic theory for this challenging setting
- Offers practical guidance for when different assumptions (overlap, consistency) are needed