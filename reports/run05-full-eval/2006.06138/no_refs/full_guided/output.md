# Reconstruction: full_guided
**Paper:** 2006.06138  
**Condition:** no_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Risk-Controlled Prediction Sets via Calibrated Loss Control

## Abstract

Machine learning systems increasingly require outputting prediction sets rather than single predictions, particularly in safety-critical applications like medical diagnosis and autonomous driving. However, existing methods for controlling the risk of prediction sets either require strong distributional assumptions, lack finite-sample guarantees, or are computationally prohibitive. We propose Calibrated Loss Control (CLC), a post-hoc method that provides finite-sample guarantees on the expected loss of prediction sets under minimal assumptions. CLC works by learning a threshold on a calibration set that ensures the expected loss on future test data remains below a user-specified level with high probability. Our approach is model-agnostic, computationally efficient, and only requires exchangeability between calibration and test data. We provide theoretical guarantees showing that CLC controls expected loss with probability at least $1-\delta$ for any user-specified confidence level $\delta$, and demonstrate its effectiveness across diverse applications including multi-label classification, object detection, and semantic segmentation.

## 1. Introduction

Modern machine learning applications often require systems to output sets of predictions rather than single point predictions. In medical diagnosis, a model might need to identify all potential conditions affecting a patient. In autonomous driving, perception systems must detect all relevant objects in a scene. In content moderation, systems need to flag all applicable policy violations. These scenarios share a common challenge: how to control the risk or expected loss of prediction sets in a principled, reliable manner.

Traditional approaches to this problem suffer from significant limitations. Methods based on Bonferroni correction or other multiple testing procedures can be overly conservative. Approaches that rely on asymptotic guarantees may fail in finite samples. Model-specific techniques require retraining or architectural modifications, limiting their practical applicability.

Recent work in conformal prediction has shown promise for providing distribution-free guarantees on prediction sets, but existing methods primarily focus on controlling coverage or size rather than arbitrary loss functions. Meanwhile, the broader literature on risk control often makes strong distributional assumptions that may not hold in practice.

Our contributions are:

• We propose Calibrated Loss Control (CLC), a post-hoc method for controlling expected loss of prediction sets with finite-sample guarantees
• We prove that CLC provides $(1-\delta)$-probability control of expected loss under only exchangeability assumptions
• We demonstrate computational efficiency through a simple thresholding procedure that scales linearly with calibration set size
• We show broad applicability across diverse domains and loss functions without requiring model retraining
• We provide a unified framework that encompasses various set prediction tasks including multi-label classification, object detection, and segmentation

## 2. Related Work

**Conformal Prediction.** Conformal prediction provides distribution-free guarantees for prediction sets by using a calibration set to determine appropriate thresholds. Classical conformal prediction [Vovk et al., 2005] and split conformal prediction [Lei et al., 2018] focus primarily on controlling coverage probability. Recent extensions have addressed conditional coverage [Romano et al., 2019] and efficiency [Angelopoulos et al., 2021]. However, these methods are designed for coverage control rather than arbitrary loss functions.

**Risk Control and PAC-Bayes.** The PAC-Bayes framework [McAllester, 1999] provides finite-sample bounds on expected risk but typically requires choosing the predictor before seeing data. Recent work on risk-controlling prediction sets [Bates et al., 2021] has begun to address post-hoc risk control, but with limited scope. Our work extends these ideas to general loss functions and set prediction tasks.

**Multi-label Classification.** In multi-label settings, various approaches have been proposed for controlling precision, recall, or F1 score [Zhang & Zhou, 2014]. Threshold optimization methods [Pillai et al., 2013] learn optimal decision boundaries but typically lack theoretical guarantees. Conformal prediction has been extended to multi-label settings [Sadinle et al., 2019], but again focuses on coverage rather than loss control.

**Object Detection and Segmentation.** Post-processing methods like Non-Maximum Suppression (NMS) are standard in object detection [Girshick, 2015] but lack principled risk control. Recent work on conformal object detection [Angelopoulos et al., 2022] provides coverage guarantees for bounding boxes but does not address general loss functions.

**Gap Identification.** While existing methods provide valuable guarantees for specific metrics (coverage, precision, etc.), there is no unified framework for controlling arbitrary loss functions over prediction sets with finite-sample guarantees. Our work fills this gap by providing a general, theoretically grounded approach that works across diverse applications and loss functions.

## 3. Problem Formulation

Let $\mathcal{X}$ denote the input space and $\mathcal{Y}$ the output space. We consider prediction tasks where the output is a set $S \subseteq \mathcal{Y}$ rather than a single element. Let $f: \mathcal{X} \to \mathbb{R}^{|\mathcal{Y}|}$ be a pre-trained model that outputs scores for each possible output element.

Given a loss function $\ell: 2^{\mathcal{Y}} \times \mathcal{Y} \to \mathbb{R}_+$ that measures the cost of predicting set $S$ when the true output is $y$, our goal is to construct prediction sets with controlled expected loss.

**Assumptions:**
1. We have access to a calibration set $\{(X_i, Y_i)\}_{i=1}^n$ drawn exchangeably with test data $(X_{n+1}, Y_{n+1})$
2. The model $f$ is fixed (pre-trained) and not modified during calibration
3. The loss function $\ell$ is user-specified and can be arbitrary

**Objective:** For a user-specified risk level $\alpha > 0$ and confidence level $\delta \in (0,1)$, construct a prediction rule $C: \mathcal{X} \to 2^{\mathcal{Y}}$ such that:

$$\mathbb{P}\left[\mathbb{E}[\ell(C(X_{n+1}), Y_{n+1})] \leq \alpha\right] \geq 1 - \delta$$

where the probability is over the randomness in the calibration set and the expectation is over the test distribution.

**Prediction Set Construction:** We parameterize prediction sets using a threshold $\lambda \geq 0$:
$$C_\lambda(x) = \{y \in \mathcal{Y} : f(x)_y \geq \lambda\}$$

where $f(x)_y$ denotes the score assigned by model $f$ to output $y$ given input $x$.

## 4. Methodology

### 4.1 Calibrated Loss Control Algorithm

Our approach learns an appropriate threshold $\lambda$ on the calibration set to ensure expected loss control on test data. The key insight is that under exchangeability, the empirical loss distribution on the calibration set provides a valid upper bound for the expected test loss.

**Algorithm 1: Calibrated Loss Control**

1. **Input:** Calibration set $\{(X_i, Y_i)\}_{i=1}^n$, model $f$, loss function $\ell$, risk level $\alpha$, confidence $\delta$
2. **Threshold candidates:** $\Lambda = \{f(X_i)_y : i \in [n], y \in \mathcal{Y}\} \cup \{0\}$
3. **For each** $\lambda \in \Lambda$:
   - Compute $\hat{R}(\lambda) = \frac{1}{n} \sum_{i=1}^n \ell(C_\lambda(X_i), Y_i)$
4. **Select threshold:** $\hat{\lambda} = \max\{\lambda \in \Lambda : \hat{R}(\lambda) + B_n(\delta) \leq \alpha\}$
5. **Output:** Prediction rule $C_{\hat{\lambda}}$

where $B_n(\delta)$ is a confidence bound defined as:
$$B_n(\delta) = \sqrt{\frac{\log(2|\Lambda|/\delta)}{2n}}$$

### 4.2 Theoretical Justification

The choice of $B_n(\delta)$ is motivated by Hoeffding's inequality and a union bound over all candidate thresholds. The key theoretical insight is that under exchangeability, the calibration set provides an unbiased estimate of test performance, and concentration inequalities allow us to bound the deviation.

**Intuition:** The algorithm searches over all meaningful thresholds (those corresponding to model scores on the calibration set) and selects the one with lowest threshold such that the upper confidence bound on empirical risk remains below $\alpha$. This ensures that with high probability, the true expected risk on test data will also be below $\alpha$.

### 4.3 Computational Efficiency

The algorithm's computational complexity is $O(n|\mathcal{Y}| \log(n|\mathcal{Y}|))$ due to sorting the candidate thresholds and computing empirical risk for each. This is practical for most applications, as it scales linearly in the calibration set size and output space size.

For large output spaces, we can use approximation techniques such as:
- Sampling a subset of candidate thresholds
- Using quantile-based threshold selection
- Hierarchical search procedures

## 5. Theoretical Analysis

**Theorem 1 (Risk Control Guarantee):** Under the exchangeability assumption, the Calibrated Loss Control algorithm satisfies:
$$\mathbb{P}\left[\mathbb{E}[\ell(C_{\hat{\lambda}}(X_{n+1}), Y_{n+1})] \leq \alpha\right] \geq 1 - \delta$$

**Proof Sketch:** 
1. By exchangeability, for any fixed $\lambda$, $\hat{R}(\lambda)$ is an unbiased estimator of $\mathbb{E}[\ell(C_\lambda(X_{n+1}), Y_{n+1})]$
2. Hoeffding's inequality gives: $\mathbb{P}[|\hat{R}(\lambda) - \mathbb{E}[\ell(C_\lambda(X_{n+1}), Y_{n+1})]| \geq t] \leq 2e^{-2nt^2}$
3. A union bound over $|\Lambda|$ candidate thresholds yields the confidence bound $B_n(\delta)$
4. The algorithm's threshold selection ensures that if $\hat{\lambda}$ is chosen, then $\hat{R}(\hat{\lambda}) + B_n(\delta) \leq \alpha$
5. With probability at least $1-\delta$, this implies $\mathbb{E}[\ell(C_{\hat{\lambda}}(X_{n+1}), Y_{n+1})] \leq \alpha$

**Theorem 2 (Consistency):** As $n \to \infty$, if there exists $\lambda^*$ such that $\mathbb{E}[\ell(C_{\lambda^*}(X), Y)] < \alpha$, then $\hat{\lambda} \to \lambda^*$ and the prediction sets achieve the target risk level.

**Corollary 1 (Adaptive Risk Control):** The method automatically adapts to the difficulty of the problem—when the model is well-calibrated and the task is easier, larger prediction sets (lower thresholds) are selected to achieve the risk target.

The key strength of our theoretical analysis is that it requires no distributional assumptions beyond exchangeability, making it robust to distribution shift and applicable in realistic deployment scenarios.

## 6. Experimental Design

We would evaluate Calibrated Loss Control across three main domains to demonstrate its broad applicability and effectiveness.

### 6.1 Multi-label Classification

**Datasets:** We would use PASCAL VOC 2012, MS-COCO, and Amazon product categorization datasets with varying numbers of labels and class imbalances.

**Models:** Pre-trained ResNet-50 and Vision Transformer models, as well as BERT-based models for text classification tasks.

**Loss Functions:** 
- Hamming loss: $\ell(S,y) = |S \triangle y|$ where $\triangle$ denotes symmetric difference
- F1-based loss: $\ell(S,y) = 1 - \text{F1}(S,y)$
- Precision-recall trade-off: $\ell(S,y) = \alpha_p(1-\text{Precision}(S,y)) + \alpha_r(1-\text{Recall}(S,y))$

**Baselines:** Threshold tuning via cross-validation, Bonferroni correction, and existing conformal prediction methods adapted to multi-label settings.

### 6.2 Object Detection

**Datasets:** COCO 2017, PASCAL VOC, and Open Images datasets with varying object densities and scales.

**Models:** Pre-trained YOLO, R-CNN, and DETR models using standard architectures.

**Loss Functions:**
- Detection loss combining localization and classification errors
- False positive/negative weighted loss: $\ell(S,y) = \alpha_{fp}|S \setminus y| + \alpha_{fn}|y \setminus S|$
- IoU-based loss for bounding box quality

**Evaluation:** We would measure actual risk achieved versus target risk levels, computational overhead, and prediction set sizes across different confidence levels.

### 6.3 Semantic Segmentation

**Datasets:** Cityscapes, ADE20K, and medical imaging datasets (when available).

**Models:** Pre-trained U-Net, DeepLab, and Transformer-based segmentation models.

**Loss Functions:**
- Pixel-wise accuracy loss
- IoU-based segmentation loss
- Class-weighted loss for handling imbalanced segmentation tasks

### 6.4 Ablation Studies

We would conduct ablations on:
- Effect of calibration set size on risk control quality
- Sensitivity to choice of confidence bound $B_n(\delta)$
- Comparison of different threshold selection strategies
- Robustness to distribution shift between calibration and test sets

### 6.5 Evaluation Metrics

- **Risk Control:** Empirical coverage of the risk guarantee across multiple test sets
- **Efficiency:** Average prediction set size and computational runtime
- **Adaptivity:** Performance across different model qualities and task difficulties
- **Robustness:** Stability under distribution shift and varying calibration set sizes

## 7. Discussion

### 7.1 Strengths

**Theoretical Rigor:** CLC provides finite-sample guarantees without strong distributional assumptions, making it suitable for real-world deployment where data distributions may shift.

**Model Agnosticism:** The method works with any pre-trained model and requires no architectural modifications or retraining, enabling easy integration into existing pipelines.

**Loss Function Flexibility:** Unlike methods that control specific metrics like coverage or precision, CLC works with arbitrary user-defined loss functions, allowing practitioners to encode domain-specific preferences.

**Computational Efficiency:** The linear scaling in calibration set size makes the method practical for large-scale applications.

### 7.2 Limitations

**Calibration Set Requirement:** The method requires a held-out calibration set, which reduces the amount of data available for training. However, this is a common requirement for post-hoc calibration methods.

**Conservative Bounds:** The union bound over candidate thresholds may lead to conservative risk control, particularly when the output space is large. Adaptive or data-dependent bounds could potentially improve efficiency.

**Exchangeability Assumption:** While weaker than i.i.d. assumptions, exchangeability may still be violated in some real-world scenarios with temporal dependencies or systematic distribution shifts.

**Threshold Discretization:** The method is limited to thresholds corresponding to observed model scores, which may miss optimal intermediate values.

### 7.3 Broader Impact

**Positive Impact:** CLC enables safer deployment of ML systems in high-stakes applications by providing formal risk guarantees. This could improve trust and adoption of AI systems in domains like healthcare, autonomous vehicles, and financial services.

**Potential Concerns:** The method's conservatism might lead to overly large prediction sets in some applications, potentially reducing system utility. Additionally, the risk control guarantee only holds under the exchangeability assumption, which practitioners must carefully verify.

## 8. Conclusion

We have presented Calibrated Loss Control, a principled approach for controlling the expected loss of prediction sets with finite-sample guarantees. Our method addresses a critical gap in the literature by providing a unified framework that works across diverse applications and loss functions while requiring only minimal assumptions about data distribution.

The key contributions include: (1) finite-sample risk control guarantees under exchangeability, (2) model-agnostic applicability without requiring retraining, (3) computational efficiency suitable for practical deployment, and (4) flexibility to handle arbitrary loss functions and set prediction tasks.

**Open Questions:** Several directions warrant future investigation:
- Developing adaptive confidence bounds that are less conservative for large output spaces
- Extending the framework to handle conditional risk control based on input features  
- Investigating the method's behavior under various forms of distribution shift
- Exploring connections to other uncertainty quantification approaches like Bayesian methods

The proposed framework opens new possibilities for reliable and principled risk control in machine learning systems, particularly in safety-critical applications where formal guarantees are essential.

## References

[Angelopoulos et al., 2021] A. Angelopoulos, S. Bates, M. Jordan, and J. Malik. Uncertainty sets for image classifiers using conformal prediction. ICLR, 2021.

[Angelopoulos et al., 2022] A. Angelopoulos, S. Bates, A. Fisch, L. Lei, and T. Schuster. Conformal risk control. UAI, 2022.

[Bates et al., 2021] S. Bates, A. Angelopoulos, L. Lei, J. Malik, and M. Jordan. Distribution-free, risk-controlling prediction sets. JASA, 2021.

[Girshick, 2015] R. Girshick. Fast R-CNN. ICCV, 2015.

[Lei et al., 2018] J. Lei, M. G'Sell, A. Rinaldo, R. Tibshirani, and L. Wasserman. Distribution-free predictive inference for regression. JASA, 2018.

[McAllester, 1999] D. McAllester. PAC-Bayesian model averaging. COLT, 1999.

[Pillai et al., 2013] I. Pillai, G. Fumera, and F. Roli. Threshold optimization for multi-label classifiers. Pattern Recognition, 2013.

[Romano et al., 2019] Y. Romano, E. Patterson, and E. Candes. Conformalized quantile regression. NeurIPS, 2019.

[Sadinle et al., 2019] M. Sadinle, J. Lei, and L. Wasserman. Least ambiguous set-valued classifiers with bounded error levels. JASA, 2019.

[Vovk et al., 2005] V. Vovk, A. Gammerman, and G. Shafer. Algorithmic Learning in a Random World. Springer, 2005.

[Zhang & Zhou, 2014] M. Zhang and Z. Zhou. A review on multi-label learning algorithms. IEEE TKDE, 2014.
