# Reconstruction: full_guided
**Paper:** 2006.06138  
**Condition:** no_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Set-Valued Prediction with Finite-Sample Loss Control

## Abstract

Many machine learning applications require algorithms to output sets of predictions rather than single predictions, such as multi-label classification, object detection, and structured prediction tasks. While existing methods like conformal prediction provide coverage guarantees for single predictions, they do not directly address the challenge of controlling expected loss for set-valued predictions under arbitrary loss functions. We propose **Loss-Controlled Set Prediction (LCSP)**, a post-hoc calibration method that takes any pre-trained model and constructs prediction sets with finite-sample guarantees on user-specified expected loss. Our approach uses empirical risk minimization over a discrete optimization problem on a held-out calibration set, combined with concentration inequalities to provide distribution-free guarantees. LCSP accommodates any loss function, requires no model retraining, and provides $1-\delta$ confidence bounds on expected loss with only $O(\log(1/\delta))$ calibration samples. We establish theoretical foundations showing that our method achieves the desired loss control while maintaining computational efficiency through greedy approximation algorithms.

## 1. Introduction

Modern machine learning increasingly demands algorithms that output structured predictions—sets of labels, bounding boxes, segmentation masks, or other complex objects. Unlike traditional single-prediction scenarios, these applications require principled methods for constructing prediction sets that balance coverage and efficiency while providing formal guarantees about performance.

Consider multi-label classification where an image may contain multiple objects, or medical diagnosis where multiple conditions may be present simultaneously. Traditional approaches either output fixed-size sets without guarantees, or rely on ad-hoc thresholding schemes that lack theoretical foundations. While conformal prediction provides elegant coverage guarantees for single predictions, extending these ideas to set-valued predictions with arbitrary loss functions remains challenging.

The key difficulty lies in controlling expected loss rather than just coverage. In many applications, different types of errors have different costs—missing a rare disease is more costly than a false positive, or failing to detect certain objects may be more critical than others. We need methods that can incorporate these application-specific preferences through user-defined loss functions while maintaining formal guarantees.

Our contributions are:
• **Loss-Controlled Set Prediction (LCSP)**: A post-hoc method that constructs prediction sets with finite-sample expected loss guarantees for arbitrary loss functions
• **Distribution-free theoretical guarantees**: Formal bounds showing our method controls expected loss with high confidence under minimal assumptions
• **Computational efficiency**: Greedy algorithms that make the approach practical for real applications
• **Broad applicability**: A framework that works with any pre-trained model and any loss function without requiring retraining

## 2. Related Work

**Conformal Prediction.** The conformal prediction framework provides distribution-free coverage guarantees for single predictions by constructing prediction sets that contain the true label with probability $1-\alpha$. Extensions to multi-label settings typically focus on marginal coverage per label rather than joint loss control across the entire prediction set.

**Set-Valued Prediction.** Various approaches exist for multi-label and structured prediction, including threshold-based methods, probabilistic approaches, and energy-based models. However, these typically lack finite-sample guarantees and focus on accuracy rather than controlling user-specified loss functions.

**Risk Control.** Recent work has explored controlling various notions of risk beyond coverage, including false discovery rate control and selective prediction. These methods provide inspiration but do not directly address the challenge of loss control for arbitrary set-valued predictions.

**Post-hoc Calibration.** Methods like Platt scaling and temperature scaling calibrate model confidence but do not provide loss guarantees. Our work extends post-hoc approaches to provide stronger guarantees about expected performance.

The gap our work fills is providing a unified framework for set-valued prediction that: (1) works with arbitrary pre-trained models, (2) accommodates user-specified loss functions, (3) provides finite-sample guarantees, and (4) remains computationally tractable.

## 3. Problem Formulation

Let $\mathcal{X}$ denote the input space and $\mathcal{Y}$ the output space. We observe a calibration dataset $\{(X_i, Y_i)\}_{i=1}^n$ drawn i.i.d. from some unknown distribution $P$, and have access to a pre-trained model that produces scores $f(x) \in \mathbb{R}^{|\mathcal{Y}|}$ for any input $x$.

Our goal is to construct a prediction function $C: \mathcal{X} \rightarrow 2^{\mathcal{Y}}$ that maps inputs to subsets of the output space. For a test point $(X_{n+1}, Y_{n+1})$ drawn from the same distribution, we want to control the expected loss:

$$\mathbb{E}[\ell(C(X_{n+1}), Y_{n+1})] \leq \alpha$$

where $\ell: 2^{\mathcal{Y}} \times \mathcal{Y} \rightarrow \mathbb{R}_+$ is a user-specified loss function.

**Key assumptions:**
- The calibration and test data are exchangeable
- The loss function $\ell$ is known and can be evaluated
- We have access to model scores $f(x)$ but cannot retrain the model

**Objective:** Design an algorithm that uses the calibration data to construct prediction sets $C(x)$ such that with probability at least $1-\delta$, the expected loss on test data is bounded by $\alpha$.

## 4. Methodology

### 4.1 Core Algorithm

Our approach consists of two phases: (1) learning a threshold function on the calibration set, and (2) applying this function to construct prediction sets for test inputs.

**Phase 1: Threshold Learning**
For each calibration example $(X_i, Y_i)$, we solve the optimization problem:
$$\tau_i^* = \arg\min_{\tau} \ell(S_\tau(X_i), Y_i)$$
where $S_\tau(x) = \{y : f_y(x) \geq \tau\}$ is the prediction set formed by thresholding the model scores.

**Phase 2: Threshold Selection**
We select the final threshold as:
$$\hat{\tau} = \text{Quantile}_{1-\alpha-\epsilon_n}(\{\tau_1^*, \ldots, \tau_n^*\})$$
where $\epsilon_n = \sqrt{\frac{\log(1/\delta)}{2n}}$ is a finite-sample correction term.

**Phase 3: Prediction**
For a test input $x$, we output the prediction set $C(x) = S_{\hat{\tau}}(x)$.

### 4.2 Handling Complex Loss Functions

When the optimization in Phase 1 is computationally challenging, we propose a greedy approximation:

```
Algorithm: Greedy Set Construction
Input: scores f(x), true label y, loss function ℓ
1. Initialize S = ∅, candidates = {all labels}
2. While candidates is not empty:
   3. For each label ỹ in candidates:
      4. Compute loss ℓ(S ∪ {ỹ}, y)
   5. Add label with minimum loss to S
   6. Remove added label from candidates
   7. If loss stops decreasing, break
8. Return S
```

This greedy approach provides a practical approximation while maintaining the overall theoretical framework.

### 4.3 Theoretical Properties

The key insight is that by using empirical quantiles with appropriate finite-sample corrections, we can transfer the empirical loss control on the calibration set to expected loss control on test data.

**Theorem 1 (Finite-Sample Loss Control):** Under the exchangeability assumption, with probability at least $1-\delta$:
$$\mathbb{E}[\ell(C(X_{n+1}), Y_{n+1})] \leq \alpha + \epsilon_n$$

The proof relies on concentration inequalities for order statistics and the exchangeability of calibration and test data.

## 5. Theoretical Analysis

### 5.1 Main Theoretical Result

**Theorem 1 (Loss Control Guarantee):** Let $(X_1, Y_1), \ldots, (X_n, Y_n), (X_{n+1}, Y_{n+1})$ be exchangeable random variables. Let $C$ be the prediction function constructed by our algorithm with parameters $\alpha$ and $\delta$. Then with probability at least $1-\delta$:

$$\mathbb{E}[\ell(C(X_{n+1}), Y_{n+1})] \leq \alpha + \sqrt{\frac{\log(1/\delta)}{2n}}$$

**Proof Sketch:** 
1. By exchangeability, the empirical loss on calibration data is an unbiased estimator of the expected loss.
2. The quantile-based threshold selection ensures that the empirical loss is bounded by $\alpha$ with appropriate probability.
3. Hoeffding's inequality provides the finite-sample correction term.
4. The union bound over all possible threshold values completes the argument.

### 5.2 Computational Complexity

**Theorem 2 (Efficiency):** For $|\mathcal{Y}| = k$ labels and $n$ calibration examples:
- Exact algorithm: $O(nk \log k)$ time complexity
- Greedy approximation: $O(nk^2)$ time complexity
- Memory complexity: $O(n + k)$

### 5.3 Approximation Quality

**Theorem 3 (Greedy Approximation):** If the loss function $\ell$ is submodular, the greedy algorithm achieves a $(1-1/e)$-approximation to the optimal solution.

This result provides theoretical backing for using the greedy approach when exact optimization is intractable.

### 5.4 Extensions to Structured Outputs

The framework naturally extends to structured prediction by treating $\mathcal{Y}$ as the space of all possible structures (e.g., parse trees, segmentation masks) and defining appropriate loss functions over sets of structures.

## 6. Experimental Design

We would evaluate LCSP across several domains to demonstrate its versatility and effectiveness:

### 6.1 Multi-Label Classification
**Datasets:** CIFAR-100, MS-COCO, Pascal VOC
**Baselines:** Threshold-based methods, conformal prediction adaptations, probabilistic approaches
**Metrics:** Expected loss (various loss functions), set size, coverage
**Loss functions:** Hamming loss, F1-based loss, precision-recall trade-offs

### 6.2 Object Detection
**Datasets:** COCO, Pascal VOC, Open Images
**Setup:** Use pre-trained YOLO/R-CNN models, construct bounding box sets
**Loss functions:** IoU-based loss, detection/localization trade-offs
**Evaluation:** Expected loss vs. number of boxes, computational time

### 6.3 Medical Diagnosis
**Datasets:** Multi-label medical datasets (e.g., chest X-ray diagnosis)
**Setup:** Different costs for false positives vs. false negatives
**Loss functions:** Cost-sensitive loss reflecting clinical priorities
**Metrics:** Expected cost, diagnostic coverage, practical utility

### 6.4 Natural Language Processing
**Datasets:** Multi-label text classification, named entity recognition
**Setup:** Use pre-trained BERT/RoBERTa models
**Loss functions:** Token-level F1, entity-level precision/recall
**Evaluation:** Loss control across different text domains

### 6.5 Ablation Studies
- Effect of calibration set size on guarantee tightness
- Comparison of exact vs. greedy optimization
- Sensitivity to loss function specification
- Performance under distribution shift

### 6.6 Computational Efficiency
- Runtime comparison with baseline methods
- Scalability to large label spaces
- Memory usage analysis

## 7. Discussion

### 7.1 Expected Strengths

**Generality:** LCSP works with any pre-trained model and any loss function, making it broadly applicable across domains. The post-hoc nature means it can be applied to existing systems without retraining.

**Theoretical Rigor:** The finite-sample guarantees provide formal confidence about performance, which is crucial for safety-critical applications like medical diagnosis or autonomous driving.

**Practical Efficiency:** The greedy approximation makes the method scalable to large label spaces while maintaining theoretical backing through submodularity analysis.

### 7.2 Expected Limitations

**Calibration Data Requirements:** The method requires a held-out calibration set, which may be expensive in domains with limited labeled data. The quality of guarantees depends on the size of this set.

**Exchangeability Assumption:** Real-world distribution shift between calibration and test data may violate the exchangeability assumption, potentially weakening the guarantees.

**Loss Function Specification:** Users must specify appropriate loss functions, which requires domain expertise and may be challenging in some applications.

**Conservative Bounds:** The finite-sample corrections may lead to conservative prediction sets, potentially reducing practical utility in favor of theoretical guarantees.

### 7.3 Broader Impact

**Positive Impact:** Enables deployment of ML systems with formal guarantees in high-stakes applications. Could improve trust and adoption of ML in critical domains like healthcare, finance, and safety systems.

**Potential Concerns:** May provide false sense of security if assumptions are violated. Could be misused to justify deployment in inappropriate contexts.

**Fairness Considerations:** The method inherits biases from the underlying model and loss function specification. Careful consideration needed for fairness-aware loss functions.

## 8. Conclusion

We have presented Loss-Controlled Set Prediction (LCSP), a principled framework for constructing prediction sets with finite-sample expected loss guarantees. Our approach addresses a fundamental gap in set-valued prediction by providing distribution-free guarantees that work with arbitrary pre-trained models and user-specified loss functions.

The key contributions include: (1) a post-hoc calibration method with formal theoretical guarantees, (2) efficient algorithms for practical implementation, and (3) broad applicability across diverse machine learning domains. The theoretical analysis demonstrates that our method achieves the desired loss control with high confidence while remaining computationally tractable.

**Open Questions and Future Work:**
- Extending to non-exchangeable settings with distribution shift guarantees
- Developing adaptive methods that adjust to observed performance
- Investigating connections to online learning and multi-armed bandits
- Exploring applications to reinforcement learning and sequential decision making
- Developing methods for automatic loss function specification

The framework opens new directions for reliable machine learning in structured prediction tasks, providing a foundation for deploying ML systems with formal performance guarantees in real-world applications.

## References

[Note: As no references were provided, this section would typically include citations to relevant papers in conformal prediction, set-valued prediction, risk control, and related areas in the format [Author, Year].]
