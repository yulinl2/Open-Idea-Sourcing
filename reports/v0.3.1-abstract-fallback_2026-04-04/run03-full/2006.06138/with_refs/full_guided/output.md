# Reconstruction: full_guided
**Paper:** 2006.06138  
**Condition:** with_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Set-Valued Prediction with Controlled Expected Loss

## Abstract

Many machine learning applications require outputting sets of predictions rather than single predictions, such as multi-label classification, object detection, and protein structure prediction. Existing methods either lack formal guarantees or are restricted to specific loss functions. We propose a general framework for constructing prediction sets that control the expected loss at a user-specified level, working with any pre-trained model and any loss function. Our approach builds on conformal prediction principles but extends beyond coverage guarantees to arbitrary loss control. We provide finite-sample guarantees that hold under minimal distributional assumptions, requiring only that calibration and test data are exchangeable. The method is computationally efficient, requiring only sorting operations, and can handle covariate shift through importance weighting. Our framework unifies and generalizes several existing approaches while providing the first general solution to loss-controlled set prediction with finite-sample guarantees.

## 1. Introduction

Machine learning applications increasingly require algorithms that output sets of predictions rather than single point predictions. In multi-label classification, an image may belong to multiple categories simultaneously. In object detection, multiple objects may be present in a scene. In medical diagnosis, multiple conditions may explain a patient's symptoms. In each case, we need principled methods to construct prediction sets that balance informativeness with reliability.

The fundamental challenge is providing formal guarantees about prediction set performance. Traditional approaches either lack theoretical backing or are restricted to specific settings. Coverage-based methods like conformal prediction ensure that prediction sets contain the true label with high probability, but this may not align with the practitioner's actual objective. For instance, in medical applications, we may care more about controlling the expected number of missed diagnoses than about coverage per se.

We address this gap by proposing a general framework for constructing prediction sets with controlled expected loss. Our contributions include:

• A unified framework for loss-controlled set prediction that works with any pre-trained model and any loss function
• Finite-sample guarantees on expected loss under minimal distributional assumptions  
• Extension to handle covariate shift through importance weighting
• Computational efficiency requiring only sorting operations
• Theoretical analysis establishing validity and optimality properties
• Demonstration that our framework generalizes conformal prediction and other existing methods

## 2. Related Work

**Conformal Prediction.** The conformal prediction framework [Vovk et al., 2005] provides distribution-free coverage guarantees for prediction sets. Given a miscoverage level α, conformal methods construct sets that contain the true label with probability at least 1-α. However, conformal prediction focuses specifically on coverage and does not directly control other loss functions of interest.

**Set-Valued Classification.** Several approaches have been developed for multi-label and set-valued prediction. Structured prediction methods [Tsochantaridis et al., 2004] can handle set outputs but typically lack finite-sample guarantees. Threshold-based methods select prediction sets by thresholding model scores, but choosing appropriate thresholds remains challenging without formal guidance.

**Loss-Aware Prediction.** Some work has considered prediction methods that directly optimize for specific loss functions. However, these typically require retraining models or are restricted to particular loss function families. Our work differs by providing a post-hoc calibration approach that works with any pre-trained model.

**Covariate Shift.** The challenge of distribution shift between training and test data has received significant attention. Tibshirani et al. [2020] extended conformal prediction to handle covariate shift through importance weighting, providing valid coverage under distributional shift. We build on this insight to handle covariate shift in the loss control setting.

**Gap Identification.** While existing methods address specific aspects of set-valued prediction, no prior work provides a general framework for controlling arbitrary loss functions with finite-sample guarantees. Our approach fills this gap by extending conformal prediction principles beyond coverage to general loss control.

## 3. Problem Formulation

Let $(X, Y)$ denote a data point where $X \in \mathcal{X}$ is the input and $Y \in \mathcal{Y}$ is the label. We assume access to a pre-trained model that produces scores $s(x, y)$ for each possible label $y \in \mathcal{Y}$. Our goal is to construct a prediction function $\hat{C}: \mathcal{X} \rightarrow 2^{\mathcal{Y}}$ that maps inputs to subsets of the label space.

Let $\ell: 2^{\mathcal{Y}} \times \mathcal{Y} \rightarrow \mathbb{R}_+$ be a loss function that measures the cost of predicting set $S$ when the true label is $y$. We assume $\ell$ is monotonic: if $S_1 \subseteq S_2$, then $\ell(S_1, y) \geq \ell(S_2, y)$ for all $y$. This captures the intuition that larger prediction sets should incur lower loss.

Given a target loss level $\alpha > 0$, our objective is to construct $\hat{C}$ such that:
$$\mathbb{E}[\ell(\hat{C}(X), Y)] \leq \alpha$$

We work in the finite-sample setting with a calibration dataset $\{(X_i, Y_i)\}_{i=1}^n$ drawn exchangeably with the test point $(X_{n+1}, Y_{n+1})$. The challenge is to provide finite-sample guarantees without strong distributional assumptions.

**Key Assumptions:**
1. Exchangeability: $(X_1, Y_1), \ldots, (X_{n+1}, Y_{n+1})$ are exchangeable
2. Monotonicity: The loss function $\ell$ is monotonic in the prediction set
3. Finite label space: $|\mathcal{Y}| < \infty$ (can be extended to infinite spaces)

## 4. Methodology

Our approach builds on the insight that we can construct a conformal-style score that directly relates to the loss function of interest. The key innovation is defining a loss-based nonconformity score that enables us to control expected loss rather than just coverage.

**Loss-Based Nonconformity Score.** For a data point $(x, y)$ and threshold $t$, define the prediction set:
$$S_t(x) = \{y' \in \mathcal{Y} : s(x, y') \geq t\}$$

The loss incurred by this set is $\ell(S_t(x), y)$. We define our nonconformity score as:
$$R(x, y) = \inf\{t : \ell(S_t(x), y) \leq \alpha\}$$

This score captures the minimum threshold needed to achieve loss at most $\alpha$ for the given example.

**Algorithm.** Given calibration data $\{(X_i, Y_i)\}_{i=1}^n$ and target loss level $\alpha$:

1. Compute nonconformity scores: $R_i = R(X_i, Y_i)$ for $i = 1, \ldots, n$
2. Compute the $(1-\alpha)$-quantile: $\hat{q} = \text{Quantile}(\{R_1, \ldots, R_n\}, \lceil (n+1)(1-\alpha) \rceil / n)$
3. For test input $x$, predict: $\hat{C}(x) = S_{\hat{q}}(x)$

**Theoretical Properties.** The following theorem establishes the validity of our approach:

**Theorem 1 (Loss Control).** Under the exchangeability assumption, the prediction sets satisfy:
$$\mathbb{E}[\ell(\hat{C}(X_{n+1}), Y_{n+1})] \leq \alpha + \frac{1}{n+1}$$

The proof follows the standard conformal prediction argument but applied to our loss-based score. The key insight is that by construction, $R(X_{n+1}, Y_{n+1}) \leq \hat{q}$ with probability at least $1-\alpha$, which translates to loss control.

**Extension to Covariate Shift.** Following Tibshirani et al. [2020], we can handle covariate shift by incorporating importance weights. If we have importance weights $w_i = p_{\text{test}}(X_i) / p_{\text{cal}}(X_i)$, we modify the quantile computation:
$$\hat{q} = \text{WeightedQuantile}(\{R_1, \ldots, R_n\}, \{w_1, \ldots, w_n\}, 1-\alpha)$$

This maintains validity under covariate shift with appropriate weight estimation.

## 5. Theoretical Analysis

**Proof of Theorem 1.** By exchangeability, $(X_1, Y_1), \ldots, (X_{n+1}, Y_{n+1})$ are identically distributed. The rank of $R_{n+1}$ among $\{R_1, \ldots, R_{n+1}\}$ is uniformly distributed over $\{1, 2, \ldots, n+1\}$.

Let $\hat{q}$ be the $\lceil (n+1)(1-\alpha) \rceil$-th smallest value among $\{R_1, \ldots, R_n\}$. Then:
$$P(R_{n+1} \leq \hat{q}) \geq \frac{\lceil (n+1)(1-\alpha) \rceil}{n+1} \geq 1-\alpha$$

By construction of the nonconformity score, $R_{n+1} \leq \hat{q}$ implies $\ell(\hat{C}(X_{n+1}), Y_{n+1}) \leq \alpha$. Therefore:
$$\mathbb{E}[\ell(\hat{C}(X_{n+1}), Y_{n+1})] \leq \alpha \cdot 1 + L_{\max} \cdot \frac{1}{n+1} \leq \alpha + \frac{1}{n+1}$$

where the last inequality assumes $L_{\max} \leq 1$ (can be normalized).

**Optimality Properties.** Our method produces the smallest prediction sets subject to the loss constraint in expectation. This follows from the monotonicity of the loss function and the construction of our nonconformity score.

**Computational Complexity.** The algorithm requires $O(n \log n)$ time for sorting the nonconformity scores and $O(|\mathcal{Y}|)$ time per prediction. For large label spaces, approximate methods using top-$k$ predictions can reduce this to $O(k)$.

**Connection to Conformal Prediction.** When $\ell(S, y) = \mathbf{1}[y \notin S]$ (the 0-1 loss for coverage), our method reduces exactly to standard conformal prediction. This shows that conformal prediction is a special case of our more general framework.

## 6. Experimental Design

We would evaluate our framework across diverse domains to demonstrate its generality and effectiveness:

**Datasets and Tasks:**
- Multi-label image classification: CIFAR-100, ImageNet with multiple labels per image
- Object detection: COCO dataset with bounding box predictions
- Natural language processing: Multi-intent classification, named entity recognition
- Medical diagnosis: Symptom-to-disease prediction with multiple possible conditions
- Protein structure prediction: Multiple valid conformations per sequence

**Baseline Methods:**
- Standard conformal prediction (for coverage-based losses)
- Threshold-based methods with cross-validation for threshold selection
- Platt scaling and temperature scaling for calibrated probabilities
- Domain-specific methods for each application area

**Loss Functions:**
- Coverage loss: $\ell(S, y) = \mathbf{1}[y \notin S]$
- Set size loss: $\ell(S, y) = |S|$ if $y \in S$, else $|S| + \lambda$
- Precision/recall trade-offs: $\ell(S, y) = \alpha |S \setminus \{y\}| + \beta \mathbf{1}[y \notin S]$
- Application-specific losses (e.g., medical cost functions)

**Evaluation Metrics:**
- Empirical loss on test sets
- Prediction set sizes
- Coverage rates (when applicable)
- Computational efficiency
- Robustness to covariate shift

**Experimental Protocol:**
- Split data into train/calibration/test sets
- Use pre-trained models (ResNet, BERT, etc.) without retraining
- Vary calibration set sizes to study finite-sample behavior
- Test robustness to hyperparameter choices
- Evaluate under natural and synthetic covariate shift

**Ablation Studies:**
- Effect of calibration set size on loss control
- Comparison of different scoring functions $s(x, y)$
- Sensitivity to loss function parameters
- Performance under model misspecification

## 7. Discussion

**Expected Strengths:**
Our framework provides the first general solution to loss-controlled set prediction with finite-sample guarantees. The method's generality allows practitioners to directly optimize for their objective rather than proxies like coverage. The computational efficiency makes it practical for large-scale applications. The theoretical guarantees provide confidence in real-world deployment.

**Limitations:**
The method requires a finite label space, though extensions to continuous spaces are possible. The quality of results depends on the underlying model's score function. The exchangeability assumption may be violated in practice, though the covariate shift extension helps address this. Large prediction sets may still occur when the model is poorly calibrated.

**Broader Impact:**
This work could improve decision-making in high-stakes applications like medical diagnosis and autonomous systems by providing formal guarantees about prediction quality. However, practitioners must carefully specify loss functions to align with their true objectives. Misspecified loss functions could lead to suboptimal or harmful decisions.

**Future Directions:**
Extensions to infinite label spaces, adaptive loss functions that depend on the input, and integration with active learning represent promising research directions. Combining our approach with model training rather than treating it as pure post-processing could yield further improvements.

## 8. Conclusion

We have presented a general framework for constructing prediction sets with controlled expected loss. Our approach extends conformal prediction beyond coverage to arbitrary loss functions while maintaining finite-sample guarantees under minimal assumptions. The method works with any pre-trained model, accommodates any monotonic loss function, and handles covariate shift through importance weighting.

Key contributions include: (1) the first general solution to loss-controlled set prediction, (2) finite-sample theoretical guarantees, (3) computational efficiency, and (4) unification of existing approaches. Our work opens new possibilities for principled set-valued prediction across diverse machine learning applications.

Open questions include extensions to infinite label spaces, optimal design of scoring functions for loss control, and integration with model training. The framework provides a solid foundation for future research in reliable and loss-aware machine learning.

## References

[Tibshirani et al., 2020] Ryan J. Tibshirani, Rina Foygel Barber, Emmanuel J. Candes, and Aaditya Ramdas. Conformal prediction under covariate shift. In NeurIPS, 2020.

[Tsochantaridis et al., 2004] Ioannis Tsochantaridis, Thomas Hofmann, Thorsten Joachims, and Yasemin Altun. Support vector machine learning for interdependent and structured output spaces. In ICML, 2004.

[Vovk et al., 2005] Vladimir Vovk, Alex Gammerman, and Glenn Shafer. Algorithmic Learning in a Random World. Springer, 2005.
