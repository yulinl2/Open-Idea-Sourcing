# Reconstruction: mindmap
**Paper:** 2103.04984  
**Condition:** with_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Paper Idea Mindmap

## Core Problem
- Develop conformal prediction methods for individual treatment effects that provide finite-sample coverage guarantees under covariate shift, handling both in-study and out-of-study inference tasks.

## Key Observations from References
- Conformal prediction can provide distribution-free coverage guarantees but requires exchangeability (Ref: arxiv-1904.06019)
- Weighted conformal scores can correct for covariate shift and maintain marginal coverage when test/train distributions differ (Ref: arxiv-1904.06019)
- Standard conformal prediction breaks down under distributional shift, but reweighting techniques can restore validity (Ref: arxiv-1904.06019)

## Proposed Approach

### Main Idea
- Develop a "Causal Conformal Prediction" framework that combines weighted conformal prediction with causal inference to provide coverage guarantees for individual treatment effects under covariate shift.

### Sub-ideas

- **Dual Conformal Score Construction**
  - Create separate conformal scores for treated and control outcomes using residuals from flexible ML models
  - Weight scores by inverse propensity to handle selection bias and achieve doubly robust properties

- **Covariate Shift Correction for Causal Settings**
  - Extend weighted conformal prediction to handle shift from study population to target population
  - Use importance weights that account for both treatment assignment mechanism and population shift

- **Multi-task Coverage Framework**
  - Task 1 (In-study): Use observed outcome + conformal prediction on counterfactual using cross-fitted models
  - Task 2 (Out-of-study): Apply weighted conformal prediction to both potential outcomes with population shift correction

- **Doubly Robust Conformal Scores**
  - Construct scores using doubly robust estimators (outcome regression + propensity weighting)
  - Ensures coverage validity if either propensity or outcome model is well-specified

## Theoretical Grounding
- Builds on weighted conformal prediction theory showing that proper reweighting maintains exchangeability and coverage
- Leverages doubly robust estimation theory from causal inference to provide robustness against model misspecification
- Uses cross-fitting to avoid overfitting bias while maintaining coverage properties
- Coverage should hold under standard causal assumptions (SUTVA, strong ignorability) plus mild overlap conditions

## Potential Challenges

- **Challenge 1: Extreme propensity weights destabilizing coverage**
  - Address through weight trimming or overlap enforcement with theoretical analysis of coverage impact
  - Develop adaptive trimming procedures that balance bias-variance tradeoffs

- **Challenge 2: Computational complexity with cross-fitting and multiple models**
  - Implement efficient algorithms using modern ML libraries with parallel processing
  - Develop approximate methods for very large datasets while preserving theoretical guarantees

- **Challenge 3: Handling multiple types of covariate shift simultaneously**
  - Develop nested weighting schemes that separately correct for selection bias and population shift
  - Provide theoretical analysis showing when these corrections can be composed

## Connections to Existing Work

- **Extends arxiv-1904.06019's weighted conformal prediction**
  - Adapts their covariate shift correction to the causal inference setting with treatment assignment
  - Builds on their theoretical framework but requires new analysis for the causal context

- **Differs from standard CATE estimation methods**
  - Unlike point estimation approaches, provides rigorous uncertainty quantification with coverage guarantees
  - Complements existing methods by providing the "confidence" component missing from current CATE estimators

- **Bridges conformal prediction and causal inference literatures**
  - First principled approach to combine these fields for ITE uncertainty quantification
  - Opens new research direction at intersection of distribution-free inference and causal methods
