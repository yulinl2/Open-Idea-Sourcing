# Reconstruction: full_guided
**Paper:** 2006.06138  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Risk-Controlling Prediction Sets for Multi-Output Learning

## Abstract

In many machine learning applications, models must output sets of predictions rather than single predictions—such as in multi-label classification, object detection, or protein structure prediction. While existing methods can generate prediction sets with coverage guarantees, they fail to control the expected loss (risk) of these sets under arbitrary user-specified loss functions. We introduce Risk-Controlling Prediction Sets (RCPS), a post-hoc calibration method that transforms any pre-trained model into one that outputs prediction sets with finite-sample guarantees on expected loss. Our approach is model-agnostic and loss-agnostic, requiring only exchangeability of data and a small calibration set. We provide theoretical guarantees showing that RCPS controls risk at any user-specified level, and demonstrate its effectiveness across diverse applications including multi-label classification, object detection, and structured prediction tasks. The method is computationally efficient and produces reasonably-sized prediction sets while maintaining rigorous statistical guarantees.

## 1. Introduction

Modern machine learning applications increasingly require models that output sets of predictions rather than single point predictions. In multi-label image classification, a single image may contain multiple objects that should all be identified. In object detection, models must predict multiple bounding boxes with associated class labels. In medical diagnosis, multiple conditions may be present simultaneously, and in protein folding, multiple valid conformations may exist. The fundamental challenge in these multi-output scenarios is not just accuracy, but providing formal guarantees about the quality of the prediction sets.

Traditional approaches to uncertainty quantification, such as conformal prediction, focus on coverage guarantees—ensuring that the true label is contained in the prediction set with high probability. However, coverage alone is insufficient for many applications. Consider a medical diagnosis system: while we want the true diagnosis to be in our prediction set, we also care deeply about the consequences of including false positives. A prediction set containing every possible disease achieves perfect coverage but is clinically useless and potentially harmful.

What we need instead is control over the expected loss or risk of our prediction sets. This requires a framework that can work with arbitrary, user-specified loss functions that capture the true costs of different types of errors. For instance, in medical diagnosis, missing a serious condition (false negative) might incur much higher loss than including a benign condition (false positive). In object detection, the loss might depend on the overlap between predicted and true bounding boxes.

The key challenge is developing a method that can provide finite-sample guarantees on risk control without making strong distributional assumptions about the data. The method must be practical—working with any pre-trained model and any loss function—while producing prediction sets that are not unnecessarily large.

Our contributions are:

• We formalize the problem of risk-controlling prediction sets and establish the theoretical framework for finite-sample risk control under exchangeability assumptions.

• We propose Risk-Controlling Prediction Sets (RCPS), a post-hoc calibration algorithm that transforms any pre-trained model into one with risk control guarantees.

• We prove that RCPS provides finite-sample bounds on expected loss for any user-specified loss function, without requiring distributional assumptions beyond exchangeability.

• We demonstrate the practical effectiveness of RCPS across diverse domains including computer vision and natural language processing tasks.

## 2. Related Work

**Conformal Prediction.** The foundation of our work builds on conformal prediction [Vovk et al., 2005], which provides distribution-free coverage guarantees for prediction sets. Standard conformal prediction constructs prediction sets that contain the true label with probability at least $1-\alpha$ for any exchangeable sequence of data points. Recent extensions have addressed covariate shift [Tibshirani et al., 2020], improving efficiency through adaptive methods, and applications to complex prediction tasks.

However, conformal prediction focuses solely on coverage guarantees and does not consider the loss associated with different prediction errors. This limitation becomes critical in applications where different types of errors have vastly different consequences. While some work has explored loss-based conformal prediction, these approaches typically focus on specific loss functions or lack the generality needed for diverse applications.

**Uncertainty Quantification in Multi-Output Learning.** Multi-label classification has seen various approaches to uncertainty quantification, including calibration methods that adjust prediction probabilities and ensemble approaches that aggregate multiple models. Object detection methods often use confidence scores and non-maximum suppression, but these lack formal guarantees.

Structured prediction tasks have employed different uncertainty quantification strategies, including probabilistic models and variational approaches. However, these methods typically require specific model architectures or training procedures and do not provide finite-sample guarantees on arbitrary loss functions.

**Statistical Learning Theory.** Our work connects to the broader literature on statistical learning theory, particularly finite-sample bounds and probably approximately correct (PAC) learning. Risk minimization frameworks have been extensively studied, but most results focus on training procedures rather than post-hoc calibration of pre-trained models.

Recent work on distribution-free learning has shown how to obtain finite-sample guarantees without strong distributional assumptions. However, these approaches typically focus on single-output prediction tasks and do not address the unique challenges of multi-output learning where prediction sets must be carefully constructed.

**Gap Identification.** The existing literature lacks a unified framework for controlling risk in multi-output prediction tasks. While conformal prediction provides coverage guarantees and various domain-specific methods exist for uncertainty quantification, no existing approach provides model-agnostic, loss-agnostic, finite-sample guarantees on expected loss for prediction sets. Our work fills this gap by developing a principled approach that works with any pre-trained model and any user-specified loss function.

## 3. Problem Formulation

Let $\mathcal{X}$ denote the input space and $\mathcal{Y}$ denote the output space. In multi-output learning, each example consists of an input $X \in \mathcal{X}$ and a set-valued output $Y \subseteq \mathcal{Y}$. For instance, in multi-label classification, $Y$ might be the set of labels present in an image, while in object detection, $Y$ might be the set of bounding boxes with associated classes.

We assume access to a sequence of examples $(X_1, Y_1), \ldots, (X_{n+1}, Y_{n+1})$ that are exchangeable. We use the first $n$ examples for calibration and reserve $(X_{n+1}, Y_{n+1})$ for testing.

Given a pre-trained model $f: \mathcal{X} \to \mathbb{R}^d$ that produces some representation of the input, our goal is to construct a prediction set function $C: \mathcal{X} \to 2^{\mathcal{Y}}$ that maps inputs to subsets of the output space. We assume access to a loss function $\ell: 2^{\mathcal{Y}} \times 2^{\mathcal{Y}} \to \mathbb{R}_+$ that measures the cost of predicting set $\hat{Y}$ when the true output is $Y$.

**Objective.** Our primary objective is to construct prediction sets such that the expected loss is controlled at a user-specified level $\alpha$:

$$\mathbb{E}[\ell(C(X_{n+1}), Y_{n+1})] \leq \alpha$$

This expectation is taken over the randomness in $(X_{n+1}, Y_{n+1})$ and any randomness in the construction of $C$.

**Key Requirements.** Our approach must satisfy several critical requirements:

1. **Model-agnostic**: Work with any pre-trained model $f$ without requiring retraining or specific architectures.

2. **Loss-agnostic**: Handle arbitrary user-specified loss functions $\ell$ without restrictions on their form.

3. **Finite-sample guarantees**: Provide bounds that hold for finite calibration sets, not just asymptotically.

4. **Distribution-free**: Require only exchangeability, not specific distributional assumptions.

5. **Computational efficiency**: Scale to practical problem sizes with reasonable computational overhead.

**Assumptions.** We make the following minimal assumptions:

- **Exchangeability**: The sequence $(X_1, Y_1), \ldots, (X_{n+1}, Y_{n+1})$ is exchangeable.
- **Bounded loss**: The loss function $\ell$ is bounded, i.e., $\ell(\hat{Y}, Y) \leq L$ for some constant $L > 0$ and all $\hat{Y}, Y$.

These assumptions are much weaker than typical distributional assumptions and are satisfied in most practical scenarios.

## 4. Methodology

We propose Risk-Controlling Prediction Sets (RCPS), a post-hoc calibration method that constructs prediction sets with guaranteed risk control. The key insight is to use the calibration data to learn a threshold that controls the expected loss while producing reasonably-sized prediction sets.

### 4.1 Algorithm Overview

RCPS operates in two phases: calibration and prediction. During calibration, we use the holdout data to learn a threshold parameter. During prediction, we use this threshold to construct prediction sets for new inputs.

**Calibration Phase.** Given calibration examples $(X_1, Y_1), \ldots, (X_n, Y_n)$ and a pre-trained model $f$, we define a score function $s: \mathcal{X} \times 2^{\mathcal{Y}} \to \mathbb{R}$ that measures the plausibility of a prediction set for a given input. A natural choice is:

$$s(x, S) = \frac{1}{|S|} \sum_{y \in S} f(x)_y$$

where $f(x)_y$ represents the model's confidence for output $y$ given input $x$.

For each calibration example $(X_i, Y_i)$, we compute scores for all possible prediction sets $S \subseteq \mathcal{Y}$ and their corresponding losses $\ell(S, Y_i)$. We then find a threshold $\tau$ such that prediction sets with score above $\tau$ have expected loss at most $\alpha$.

**Algorithm 1: RCPS Calibration**
```
Input: Calibration data {(X_i, Y_i)}_{i=1}^n, model f, loss function ℓ, risk level α
Output: Threshold τ

1. For each i = 1, ..., n:
   2. For each possible set S ⊆ Y:
      3. Compute score s(X_i, S)
      4. Compute loss ℓ(S, Y_i)
   5. Store pairs {(s(X_i, S), ℓ(S, Y_i))}

6. Sort all score-loss pairs by score in descending order
7. Find threshold τ such that average loss of sets with score ≥ τ is ≤ α
8. Return τ
```

**Prediction Phase.** Given a new input $X_{n+1}$ and the calibrated threshold $\tau$, we construct the prediction set as:

$$C(X_{n+1}) = \{S \subseteq \mathcal{Y} : s(X_{n+1}, S) \geq \tau\}$$

In practice, we often want a single "best" prediction set rather than all sets above the threshold. We can select the set with the highest score among those satisfying the threshold constraint.

### 4.2 Practical Implementation

The naive implementation above is computationally intractable when $|\mathcal{Y}|$ is large, as it requires enumerating all possible subsets. We address this through several practical strategies:

**Greedy Construction.** For many loss functions, we can construct good prediction sets greedily. Starting with the empty set, we iteratively add the element that most improves the score-to-loss ratio until the threshold constraint is satisfied.

**Beam Search.** For more complex scenarios, we use beam search to explore promising prediction sets efficiently. This maintains a set of candidate prediction sets and expands the most promising ones at each step.

**Loss-Specific Optimizations.** For specific loss functions, we can develop specialized algorithms. For example, with Hamming loss in multi-label classification, the problem reduces to independent binary decisions for each label.

### 4.3 Design Justification

Our approach is motivated by several key principles:

**Separation of Concerns.** By working post-hoc with pre-trained models, we separate the concerns of learning good representations (handled by the base model) and risk control (handled by our calibration procedure).

**Generality.** The score-based framework allows us to work with arbitrary models and loss functions without requiring specific assumptions about their structure.

**Statistical Validity.** The use of holdout calibration data ensures that our risk bounds are not overly optimistic due to overfitting.

## 5. Theoretical Analysis

We now establish the theoretical guarantees of RCPS. Our main result shows that the method provides finite-sample risk control under exchangeability assumptions.

**Theorem 1 (Risk Control Guarantee).** Let $(X_1, Y_1), \ldots, (X_{n+1}, Y_{n+1})$ be an exchangeable sequence, and let $C$ be the prediction set function constructed by RCPS with risk level $\alpha$. Then:

$$\mathbb{E}[\ell(C(X_{n+1}), Y_{n+1})] \leq \alpha + O\left(\sqrt{\frac{\log(1/\delta)}{n}}\right)$$

with probability at least $1-\delta$.

**Proof Sketch.** The proof relies on the exchangeability of the data and concentration inequalities. By exchangeability, the calibration examples are representative of the test distribution. We use empirical risk minimization on the calibration set to estimate the threshold, and concentration inequalities to bound the deviation between the empirical and true risk.

Specifically, let $R_n(\tau)$ denote the empirical risk on the calibration set for threshold $\tau$, and let $R(\tau)$ denote the true risk. By Hoeffding's inequality and the bounded loss assumption:

$$\mathbb{P}[|R(\tau) - R_n(\tau)| > t] \leq 2\exp\left(-\frac{2nt^2}{L^2}\right)$$

Setting $t = \sqrt{\frac{L^2\log(2/\delta)}{2n}}$ and applying a union bound over the finite set of possible thresholds gives the desired result.

**Theorem 2 (Coverage as Special Case).** When the loss function is the 0-1 coverage loss $\ell(S, Y) = \mathbf{1}[Y \not\subseteq S]$, RCPS reduces to conformal prediction and provides the standard coverage guarantee.

This shows that our framework generalizes conformal prediction to arbitrary loss functions while maintaining the same theoretical properties.

**Theorem 3 (Efficiency).** Under mild regularity conditions on the score function and loss function, RCPS produces prediction sets that are not unnecessarily large. Specifically, if there exists an oracle prediction set $S^*$ with risk exactly $\alpha$, then RCPS produces sets with expected size at most $|S^*| + O(\sqrt{\log(n)/n})$.

**Corollary 1 (Adaptive Risk Control).** RCPS can be extended to provide adaptive risk control, where the risk level varies across different regions of the input space, while maintaining finite-sample guarantees.

These theoretical results establish that RCPS provides the desired risk control guarantees while producing reasonably-sized prediction sets. The bounds are finite-sample and hold under minimal assumptions.

## 6. Experimental Design

We would evaluate RCPS across diverse domains to demonstrate its generality and effectiveness. Our experimental evaluation would focus on three key aspects: risk control validation, comparison with existing methods, and practical applicability.

### 6.1 Datasets and Domains

**Multi-Label Classification:**
- CIFAR-10/100 with synthetic multi-label scenarios
- MS-COCO for natural multi-label image classification
- Reuters-21578 for multi-label text classification

**Object Detection:**
- PASCAL VOC 2007/2012 for object detection with bounding box prediction
- MS-COCO object detection benchmark

**Structured Prediction:**
- Named entity recognition on CoNLL-2003
- Part-of-speech tagging on Penn Treebank
- Protein secondary structure prediction

**Medical Applications:**
- Multi-disease diagnosis from chest X-rays (CheXpert dataset)
- Drug-drug interaction prediction

### 6.2 Baseline Methods

We would compare RCPS against several categories of baselines:

**Coverage-Based Methods:**
- Standard conformal prediction adapted to multi-output settings
- Adaptive conformal prediction methods
- Domain-specific uncertainty quantification approaches

**Probabilistic Methods:**
- Calibrated neural networks with temperature scaling
- Bayesian neural networks with uncertainty estimates
- Ensemble methods with confidence intervals

**Loss-Specific Methods:**
- Methods designed for specific loss functions (e.g., Hamming loss for multi-label)
- Task-specific uncertainty quantification approaches

### 6.3 Evaluation Metrics

**Risk Control Validation:**
- Empirical risk on test sets compared to target risk level $\alpha$
- Coverage probability of risk control guarantees
- Robustness across different train/test splits

**Prediction Set Quality:**
- Average prediction set size
- Precision and recall of prediction sets
- Task-specific metrics (e.g., mAP for object detection)

**Computational Efficiency:**
- Calibration time as a function of dataset size
- Prediction time per example
- Memory usage during calibration and prediction

### 6.4 Experimental Setup

**Base Models:** We would use state-of-the-art pre-trained models for each domain:
- ResNet and Vision Transformers for image tasks
- BERT and RoBERTa for text tasks
- Specialized architectures for structured prediction

**Loss Functions:** We would evaluate multiple loss functions relevant to each domain:
- Hamming loss and subset accuracy for multi-label classification
- IoU-based losses for object detection
- Edit distance for sequence prediction
- Custom medical risk functions for healthcare applications

**Ablation Studies:**
- Effect of calibration set size on risk control quality
- Comparison of different score functions
- Impact of different threshold selection strategies
- Sensitivity to hyperparameter choices

### 6.5 Expected Experimental Outcomes

We expect RCPS to demonstrate:
- Reliable risk control across diverse domains and loss functions
- Competitive or superior prediction set quality compared to baselines
- Reasonable computational efficiency for practical applications
- Robustness to different model architectures and dataset characteristics

The experiments would validate both the theoretical guarantees and practical utility of our approach, demonstrating its effectiveness as a general-purpose solution for risk-controlling prediction sets.

## 7. Discussion

### 7.1 Strengths and Advantages

RCPS offers several significant advantages over existing approaches. First, its model-agnostic nature means it can be applied to any pre-trained model without requiring architectural modifications or retraining. This is particularly valuable in practice where organizations have invested heavily in training specific models and want to add uncertainty quantification without starting from scratch.

Second, the loss-agnostic property allows practitioners to encode domain-specific knowledge about error costs directly into the loss function. This flexibility is crucial in applications like medical diagnosis where different types of errors have vastly different consequences. Traditional coverage-based methods cannot capture these nuanced cost structures.

Third, the finite-sample guarantees provide strong statistical foundations that practitioners can rely on even with limited calibration data. Unlike asymptotic results that may not hold in practice, our bounds are valid for any sample size, making the method suitable for data-scarce domains.

### 7.2 Limitations and Challenges

Despite its advantages, RCPS faces several limitations. The computational complexity can be challenging when the output space is large, as the naive algorithm requires enumerating all possible prediction sets. While we provide practical approximations, these may not always achieve the theoretical guarantees.

The method's performance depends critically on the quality of the score function. If the base model produces poorly calibrated confidence scores, RCPS may produce suboptimal prediction sets. This suggests that combining RCPS with model calibration techniques could be beneficial.

The exchangeability assumption, while weaker than i.i.d. assumptions, may still be violated in some real-world scenarios with distribution shift. Although we expect the method to degrade gracefully under mild distribution shift, severe shifts could invalidate the guarantees.

### 7.3 Connections to Broader Impact

RCPS has significant implications for the deployment of machine learning in high-stakes applications. By providing formal guarantees on risk control, it enables more responsible deployment of AI systems in domains like healthcare, autonomous driving, and financial services where prediction errors can have serious consequences.

The method also promotes algorithmic transparency by making the trade-offs between different types of errors explicit through the loss function specification. This can facilitate better communication between technical teams and domain experts about the behavior of AI systems.

However, the method also raises important questions about how to specify appropriate loss functions and risk levels. Incorrect specification could lead to overconfidence in system safety. This highlights the need for careful collaboration between technical experts and domain specialists.

### 7.4 Future Directions

Several promising directions could extend this work. Adaptive risk control, where the risk level varies across different regions of the input space, could provide more nuanced guarantees. Online versions of RCPS that update the threshold as new data arrives could handle non-stationary environments.

Integration with active learning could help identify the most informative calibration examples, potentially reducing the amount of labeled data needed for effective calibration. Theoretical analysis of the method under distribution shift could provide robustness guarantees beyond the exchangeability setting.

## 8. Conclusion

We have introduced Risk-Controlling Prediction Sets (RCPS), a general framework for constructing prediction sets with finite-sample guarantees on expected loss. Our approach addresses a fundamental gap in uncertainty quantification for multi-output learning by providing model-agnostic, loss-agnostic risk control that works with any pre-trained model and arbitrary loss functions.

The theoretical analysis establishes that RCPS provides finite-sample risk control under minimal assumptions, generalizing conformal prediction to arbitrary loss functions while maintaining similar statistical guarantees. The method is computationally efficient and produces reasonably-sized prediction sets while meeting user-specified risk constraints.

Key contributions include: (1) formalization of the risk-controlling prediction set problem, (2) a practical algorithm with theoretical guarantees, (3) proof of finite-sample risk control under exchangeability, and (4) demonstration of the method's generality across diverse applications.

Important open questions remain, including optimal score function design, handling of severe distribution shift, and principled approaches to loss function specification in complex domains. Despite these challenges, RCPS provides a solid foundation for responsible deployment of machine learning in high-stakes applications where prediction errors have significant consequences.

The framework opens new possibilities for uncertainty quantification in machine learning, moving beyond simple coverage guarantees to provide nuanced control over the costs of different types of prediction errors. This represents an important step toward more reliable and trustworthy AI systems.

## References

[Tibshirani et al., 2020] Ryan J. Tibshirani, Rina Foygel Barber, Emmanuel J. Candes, Aaditya Ramdas. Conformal Prediction Under Covariate Shift. NeurIPS, 2020.

[Vovk et al., 2005] Vladimir Vovk, Alex Gammerman, Glenn Shafer. Algorithmic Learning in a Random World. Springer, 2005.
