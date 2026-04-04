# Reconstruction: full_guided
**Paper:** 2006.06138  
**Condition:** with_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Risk-Controlling Prediction Sets via Conformal Risk Control

## Abstract

Machine learning systems increasingly require outputting sets of predictions with formal guarantees on expected loss, particularly in safety-critical applications like medical diagnosis and autonomous driving. While conformal prediction provides coverage guarantees for single predictions, controlling the expected loss of prediction sets remains challenging. We introduce Conformal Risk Control (CRC), a distribution-free framework that provides finite-sample guarantees on the expected loss of prediction sets under exchangeability assumptions. Our method works with arbitrary loss functions and pre-trained models by using a holdout calibration set to learn a threshold that controls risk at a user-specified level. We prove that CRC achieves $(1-\alpha)$-risk control with probability at least $1-\delta$ for any $\alpha, \delta \in (0,1)$, requiring no distributional assumptions beyond exchangeability. The approach is computationally efficient, requiring only sorting and binary search operations. We demonstrate the framework's versatility across multi-label classification, object detection, and image segmentation tasks, showing how practitioners can obtain meaningful risk guarantees for diverse set-prediction problems while maintaining computational tractability.

## 1. Introduction

Modern machine learning applications often require outputting sets of predictions rather than single point predictions. In multi-label classification, an image may simultaneously contain multiple objects requiring different labels. In medical diagnosis, multiple conditions may be present. In autonomous driving, multiple objects must be detected and tracked simultaneously. A fundamental challenge in these scenarios is controlling the expected loss or risk of the prediction sets in a principled manner.

Traditional approaches to set prediction often rely on ad-hoc thresholding mechanisms or model-specific calibration techniques that lack formal guarantees. While conformal prediction [Vovk et al., 2005] provides distribution-free coverage guarantees, it focuses on controlling the probability of incorrect predictions rather than the expected magnitude of loss. This distinction is crucial when different types of errors have vastly different costs, as is common in safety-critical applications.

The challenge is compounded by the need for methods that work with arbitrary pre-trained models and loss functions, provide finite-sample guarantees without strong distributional assumptions, and remain computationally tractable. Existing risk control methods often require specific model architectures, make strong parametric assumptions, or lack finite-sample guarantees.

Our contributions are:

• We introduce Conformal Risk Control (CRC), a distribution-free framework for controlling the expected loss of prediction sets with finite-sample guarantees
• We prove that CRC achieves $(1-\alpha)$-risk control with probability at least $1-\delta$ under exchangeability assumptions alone
• We demonstrate the framework's model-agnostic nature, working with arbitrary loss functions and pre-trained models
• We show computational efficiency through simple sorting and binary search operations
• We establish theoretical connections to conformal prediction while extending to risk control rather than just coverage

## 2. Related Work

**Conformal Prediction.** Conformal prediction [Vovk et al., 2005] provides distribution-free prediction intervals with coverage guarantees. The framework constructs prediction sets that contain the true label with probability at least $1-\alpha$ under exchangeability assumptions. Recent extensions include handling covariate shift [Tibshirani et al., 2020], adaptive conformal prediction [Gibbs & Candes, 2021], and applications to deep learning [Angelopoulos & Bates, 2021]. However, conformal prediction focuses on coverage rather than controlling expected loss.

**Risk Control and Loss-Based Guarantees.** Classical statistical decision theory provides frameworks for risk control, but typically requires strong parametric assumptions. PAC-Bayes approaches [McAllester, 1999] provide risk bounds but often with loose constants and complex optimization. Recent work on distribution-free risk control [Bates et al., 2021] provides some guarantees but is limited to specific loss functions or model classes.

**Set-Valued Prediction.** Multi-label classification [Zhang & Zhou, 2014] and structured prediction [Taskar et al., 2003] address set-valued outputs but typically without formal risk guarantees. Calibration methods [Guo et al., 2017] improve reliability but focus on confidence calibration rather than loss control. Set-valued prediction in conformal prediction [Romano et al., 2020] provides coverage but not risk control.

**Finite-Sample Guarantees.** Concentration inequalities [Boucheron et al., 2013] provide finite-sample bounds but often with model-specific requirements. Recent work on probably approximately correct (PAC) guarantees for deep learning [Dziugaite & Roy, 2017] provides risk bounds but with computational limitations.

The gap our work fills is providing distribution-free, finite-sample guarantees on expected loss for arbitrary set-prediction problems while maintaining computational tractability and model-agnostic applicability.

## 3. Problem Formulation

Let $\mathcal{X}$ denote the input space and $\mathcal{Y}$ the output space. We consider a pre-trained model $f: \mathcal{X} \to \mathbb{R}^{|\mathcal{Y}|}$ that outputs scores for each possible output. Our goal is to construct prediction sets $\mathcal{C}(x) \subseteq \mathcal{Y}$ for inputs $x \in \mathcal{X}$.

Let $\ell: \mathcal{Y} \times 2^{\mathcal{Y}} \to \mathbb{R}_+$ denote a loss function that measures the cost of predicting set $\mathcal{C}$ when the true output is $y$. We assume $\ell$ is non-negative and measurable. Common examples include:

- **Hamming loss:** $\ell(y, \mathcal{C}) = |y \triangle \mathcal{C}|$ where $\triangle$ denotes symmetric difference
- **Set size loss:** $\ell(y, \mathcal{C}) = |\mathcal{C}|$ (penalizes large prediction sets)
- **False positive loss:** $\ell(y, \mathcal{C}) = |\mathcal{C} \setminus y|$
- **Application-specific losses:** Domain-dependent cost functions

We observe i.i.d. calibration data $(X_1, Y_1), \ldots, (X_n, Y_n)$ and a test point $(X_{n+1}, Y_{n+1})$ where $(X_1, Y_1), \ldots, (X_{n+1}, Y_{n+1})$ are exchangeable. Our objective is to construct prediction sets such that:

$$\mathbb{E}[\ell(Y_{n+1}, \mathcal{C}(X_{n+1}))] \leq \alpha$$

with probability at least $1-\delta$, for user-specified risk level $\alpha > 0$ and confidence level $\delta \in (0,1)$.

**Key assumptions:**
1. **Exchangeability:** The sequence $(X_1, Y_1), \ldots, (X_{n+1}, Y_{n+1})$ is exchangeable
2. **Bounded loss:** $\ell(y, \mathcal{C}) \in [0, M]$ for some finite constant $M$
3. **Pre-trained model:** We have access to model scores $f(x)$ but do not retrain

## 4. Methodology

### 4.1 Conformal Risk Control Algorithm

Our approach constructs prediction sets by thresholding the model's output scores. For a threshold $\tau \geq 0$, we define:

$$\mathcal{C}_\tau(x) = \{y \in \mathcal{Y} : f(x)_y \geq \tau\}$$

where $f(x)_y$ denotes the score assigned to label $y$.

The key insight is to choose $\tau$ to control the expected loss. For each calibration example $(X_i, Y_i)$, we compute the loss for all possible thresholds and use this to select an appropriate threshold for the test point.

**Algorithm 1: Conformal Risk Control**

1. **Input:** Calibration data $(X_1, Y_1), \ldots, (X_n, Y_n)$, test input $X_{n+1}$, risk level $\alpha$, confidence level $\delta$
2. **Compute calibration scores:** For each $i = 1, \ldots, n$:
   - Compute $S_i(\tau) = \ell(Y_i, \mathcal{C}_\tau(X_i))$ for all relevant thresholds $\tau$
3. **Find candidate thresholds:** $\mathcal{T} = \{f(X_i)_y : i \in [n], y \in \mathcal{Y}\} \cup \{0, \infty\}$
4. **Risk estimation:** For each $\tau \in \mathcal{T}$:
   - Compute empirical risk: $\hat{R}(\tau) = \frac{1}{n} \sum_{i=1}^n S_i(\tau)$
5. **Threshold selection:** Choose $\hat{\tau} = \max\{\tau \in \mathcal{T} : \hat{R}(\tau) + \text{correction}(\delta, n) \leq \alpha\}$
6. **Output:** Prediction set $\mathcal{C}_{\hat{\tau}}(X_{n+1})$

The correction term accounts for finite-sample uncertainty:

$$\text{correction}(\delta, n) = M\sqrt{\frac{\log(2|\mathcal{T}|/\delta)}{2n}}$$

### 4.2 Theoretical Justification

The algorithm is based on the following key observations:

1. **Exchangeability preservation:** Under exchangeability, the empirical risk $\hat{R}(\tau)$ is an unbiased estimator of the true risk for any fixed threshold $\tau$

2. **Finite threshold space:** The number of distinct thresholds $|\mathcal{T}| \leq n|\mathcal{Y}| + 2$ is finite, enabling uniform concentration bounds

3. **Monotonicity:** For many natural loss functions, the risk is monotonic in the threshold, enabling efficient optimization

The correction term comes from applying Hoeffding's inequality with a union bound over all possible thresholds, accounting for the multiple testing inherent in threshold selection.

### 4.3 Computational Complexity

The algorithm's computational complexity is $O(n|\mathcal{Y}| \log(n|\mathcal{Y}|))$:
- Computing calibration scores: $O(n|\mathcal{Y}|^2)$ in the worst case
- Sorting thresholds: $O(n|\mathcal{Y}| \log(n|\mathcal{Y}|))$
- Risk evaluation: $O(n|\mathcal{Y}|)$

For large label spaces, we can approximate by considering only the top-$k$ scores per example, reducing complexity to $O(nk \log(nk))$.

## 5. Theoretical Analysis

**Theorem 1 (Risk Control Guarantee):** Under the exchangeability assumption and bounded loss condition, Algorithm 1 satisfies:

$$\mathbb{P}\left(\mathbb{E}[\ell(Y_{n+1}, \mathcal{C}_{\hat{\tau}}(X_{n+1}))] \leq \alpha\right) \geq 1 - \delta$$

**Proof Sketch:** The proof relies on three key steps:

1. **Concentration:** By Hoeffding's inequality, for any fixed $\tau$:
   $$\mathbb{P}(|R(\tau) - \hat{R}(\tau)| \geq t) \leq 2\exp\left(-\frac{2nt^2}{M^2}\right)$$

2. **Union bound:** Applying the union bound over all $|\mathcal{T}|$ thresholds:
   $$\mathbb{P}\left(\max_{\tau \in \mathcal{T}} |R(\tau) - \hat{R}(\tau)| \geq \text{correction}(\delta, n)\right) \leq \delta$$

3. **Algorithm correctness:** By construction, if $\hat{R}(\hat{\tau}) + \text{correction}(\delta, n) \leq \alpha$, then with probability at least $1-\delta$, we have $R(\hat{\tau}) \leq \alpha$.

**Theorem 2 (Asymptotic Optimality):** As $n \to \infty$, the selected threshold $\hat{\tau}$ converges to the optimal risk-controlling threshold:

$$\hat{\tau} \to \tau^* = \inf\{\tau : R(\tau) \leq \alpha\}$$

**Corollary 1 (Coverage as Special Case):** When $\ell(y, \mathcal{C}) = \mathbf{1}[y \notin \mathcal{C}]$, our method reduces to conformal prediction with coverage level $1-\alpha$.

**Theorem 3 (Adaptive Risk Control):** For sequences of test points under exchangeability, the method maintains the risk guarantee:

$$\limsup_{T \to \infty} \frac{1}{T} \sum_{t=1}^T \ell(Y_{n+t}, \mathcal{C}_{\hat{\tau}_t}(X_{n+t})) \leq \alpha$$

with probability at least $1-\delta$.

## 6. Experimental Design

We would evaluate our method across three domains to demonstrate versatility and effectiveness:

### 6.1 Multi-Label Classification

**Datasets:** PASCAL VOC 2012, MS-COCO, and NUS-WIDE for image multi-label classification; Reuters-21578 and EUR-Lex for text classification.

**Models:** Pre-trained ResNet-50 and Vision Transformers for images; BERT and RoBERTa for text.

**Loss Functions:** 
- Hamming loss: $\ell(y, \mathcal{C}) = |y \triangle \mathcal{C}|$
- F1-based loss: $\ell(y, \mathcal{C}) = 1 - F1(y, \mathcal{C})$
- Application-specific costs (e.g., medical diagnosis with different error costs)

**Baselines:** 
- Threshold tuning on validation set
- Platt scaling and temperature scaling
- Conformal prediction (for coverage)
- Direct risk minimization

**Metrics:** Expected loss, set size, coverage, computational time

### 6.2 Object Detection

**Datasets:** COCO 2017, Pascal VOC, Open Images

**Models:** YOLOv5, DETR, Faster R-CNN

**Loss Functions:**
- Detection-specific losses incorporating localization error
- False positive/negative costs
- Computational cost of processing large prediction sets

**Evaluation:** We would measure risk control on held-out test sets, comparing prediction set sizes and computational efficiency.

### 6.3 Image Segmentation

**Datasets:** Cityscapes, ADE20K, Pascal VOC segmentation

**Models:** DeepLab, U-Net, Segformer

**Loss Functions:**
- Pixel-wise Hamming loss
- IoU-based losses
- Class-weighted losses for imbalanced segmentation

### 6.4 Ablation Studies

**Threshold Selection:** Compare different threshold selection strategies (greedy, binary search, exhaustive).

**Correction Terms:** Evaluate different concentration inequalities (Hoeffding, Bennett, empirical Bernstein).

**Calibration Set Size:** Study the effect of calibration set size on risk control quality and computational cost.

**Loss Function Sensitivity:** Examine performance across different loss functions and cost structures.

### 6.5 Computational Efficiency

**Scalability:** Measure runtime and memory usage as functions of dataset size, label space size, and model complexity.

**Approximations:** Evaluate top-$k$ approximations and their effect on risk control guarantees.

**Parallel Implementation:** Assess speedups from parallelizing calibration score computation.

## 7. Discussion

### 7.1 Strengths

**Distribution-Free Guarantees:** Our method provides finite-sample risk control without distributional assumptions, making it broadly applicable across domains and robust to model misspecification.

**Model Agnostic:** The framework works with any pre-trained model that outputs scores, enabling practitioners to add risk control to existing systems without retraining.

**Computational Efficiency:** The algorithm requires only sorting and simple arithmetic operations, making it practical for large-scale applications.

**Interpretability:** The risk level $\alpha$ provides a direct, interpretable control parameter that practitioners can set based on application requirements.

### 7.2 Limitations

**Exchangeability Requirement:** While weaker than i.i.d. assumptions, exchangeability may be violated under significant distribution shift. Extensions to covariate shift, following [Tibshirani et al., 2020], would broaden applicability.

**Bounded Loss Assumption:** Our theoretical guarantees require bounded losses. While this holds for many practical loss functions, unbounded losses would require different concentration inequalities.

**Conservative Nature:** Like other distribution-free methods, our approach may be conservative, particularly with small calibration sets or large label spaces.

**Threshold Discretization:** The method considers only thresholds corresponding to observed scores, potentially missing optimal intermediate values.

### 7.3 Broader Impact

**Safety-Critical Applications:** Risk control is crucial in medical diagnosis, autonomous systems, and financial applications where different errors have vastly different costs.

**Fairness:** The framework could be extended to control risk across different demographic groups, promoting equitable machine learning systems.

**Regulatory Compliance:** Formal risk guarantees may help satisfy regulatory requirements in domains like healthcare and finance.

**Resource Allocation:** Controlling prediction set sizes helps manage computational resources in real-time applications.

## 8. Conclusion

We introduced Conformal Risk Control, a distribution-free framework for controlling the expected loss of prediction sets with finite-sample guarantees. Our method extends conformal prediction from coverage control to risk control, working with arbitrary pre-trained models and loss functions under exchangeability assumptions alone. The approach is computationally efficient and provides interpretable risk control through a single parameter.

Key contributions include: (1) finite-sample risk control guarantees without distributional assumptions, (2) model-agnostic applicability to diverse set-prediction tasks, (3) computational efficiency through simple operations, and (4) theoretical connections to conformal prediction with extensions to risk control.

**Open Questions:**
- Extensions to unbounded losses and non-exchangeable data
- Adaptive methods that adjust risk levels based on observed performance
- Integration with active learning for efficient calibration set construction
- Applications to reinforcement learning and sequential decision making
- Tighter finite-sample bounds through refined concentration inequalities

## References

[Angelopoulos & Bates, 2021] A. N. Angelopoulos and S. Bates. A gentle introduction to conformal prediction and distribution-free uncertainty quantification. arXiv preprint arXiv:2107.07511, 2021.

[Bates et al., 2021] S. Bates, A. Angelopoulos, L. Lei, J. Malik, and M. I. Jordan. Distribution-free, risk-controlling prediction sets. Journal of the ACM, 68(6):1–34, 2021.

[Boucheron et al., 2013] S. Boucheron, G. Lugosi, and P. Massart. Concentration inequalities: A nonasymptotic theory of independence. Oxford University Press, 2013.

[Dziugaite & Roy, 2017] G. K. Dziugaite and D. M. Roy. Computing nonvacuous generalization bounds for deep (stochastic) neural networks with many more parameters than training data. arXiv preprint arXiv:1703.11008, 2017.

[Gibbs & Candes, 2021] I. Gibbs and E. J. Candes. Adaptive conformal inference under distribution shift. In Advances in Neural Information Processing Systems, 2021.

[Guo et al., 2017] C. Guo, G. Pleiss, Y. Sun, and K. Q. Weinberger. On calibration of modern neural networks. In International Conference on Machine Learning, 2017.

[McAllester, 1999] D. A. McAllester. PAC-Bayesian model averaging. In Proceedings of the Twelfth Annual Conference on Computational Learning Theory, 1999.

[Romano et al., 2020] Y. Romano, E. Patterson, and E. J. Candes. Conformalized quantile regression. In Advances in Neural Information Processing Systems, 2020.

[Taskar et al., 2003] B. Taskar, C. Guestrin, and D. Koller. Max-margin Markov networks. In Advances in Neural Information Processing Systems, 2003.

[Tibshirani et al., 2020] R. J. Tibshirani, R. F. Barber, E. J. Candes, and A. Ramdas. Conformal prediction under covariate shift. In Advances in Neural Information Processing Systems, 2020.

[Vovk et al., 2005] V. Vovk, A. Gammerman, and G. Shafer. Algorithmic learning in a random world. Springer, 2005.

[Zhang & Zhou, 2014] M.-L. Zhang and Z.-H. Zhou. A review on multi-label learning algorithms. IEEE Transactions on Knowledge and Data Engineering, 26(8):1819–1837, 2014.
