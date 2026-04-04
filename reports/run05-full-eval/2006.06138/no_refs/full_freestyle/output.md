# Reconstruction: full_freestyle
**Paper:** 2006.06138  
**Condition:** no_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Risk-Controlling Prediction Sets: A Distribution-Free Framework for Set-Valued Predictions

## Abstract

We introduce Risk-Controlling Prediction Sets (RCPS), a distribution-free framework for constructing prediction sets that provide finite-sample guarantees on expected loss. Unlike existing conformal prediction methods that control coverage, RCPS directly controls the expected value of any user-specified loss function over prediction sets. Our approach works with arbitrary underlying models and loss functions, requiring only exchangeability of calibration and test data. We provide theoretical guarantees showing that RCPS controls expected loss with high probability, and demonstrate computational efficiency through a simple threshold-based construction. Experimental validation across computer vision and natural language processing tasks confirms the effectiveness of our method for multi-label classification, object detection, and semantic segmentation. RCPS offers practitioners a principled tool for risk management in set prediction problems without requiring model retraining or strong distributional assumptions.

## 1. Introduction

Modern machine learning applications increasingly require models to output sets of predictions rather than single point predictions. In multi-label image classification, multiple objects may be present in a single image. In medical diagnosis, patients may have multiple conditions. In object detection, multiple objects must be localized simultaneously. These set prediction tasks present a fundamental challenge: how can we provide formal guarantees about the quality of prediction sets?

Existing approaches typically focus on coverage guarantees—ensuring that the true label is contained in the prediction set with high probability. While coverage is important, practitioners often care more directly about controlling the expected loss or risk associated with their predictions. For instance, in medical applications, we may want to ensure that the expected number of missed diagnoses remains below a critical threshold. In autonomous driving, we may need to bound the expected severity of missed object detections.

This paper introduces Risk-Controlling Prediction Sets (RCPS), a distribution-free framework that directly controls the expected loss of set-valued predictions. Our key contributions are:

1. **Theoretical Framework**: We develop a general theory for constructing prediction sets with finite-sample guarantees on expected loss, requiring only exchangeability of data.

2. **Algorithmic Solution**: We provide a computationally efficient algorithm based on conformal prediction principles that works with arbitrary models and loss functions.

3. **Broad Applicability**: We demonstrate the framework's effectiveness across diverse domains including computer vision and natural language processing.

4. **Practical Impact**: Our method requires only a holdout calibration set and provides intuitive risk control without model retraining.

The core insight behind RCPS is to leverage the martingale properties of conformal prediction while directly optimizing for loss control rather than coverage. This shift in perspective enables practitioners to specify their risk tolerance directly in terms of the loss function that matters for their application.

## 2. Related Work

### 2.1 Conformal Prediction

Conformal prediction, introduced by Vovk et al., provides distribution-free coverage guarantees for prediction sets. The framework constructs prediction sets that contain the true label with probability at least $1-\alpha$ for any exchangeable data sequence. Recent advances have extended conformal prediction to complex scenarios including classification [Sadinle et al., 2019], regression [Lei et al., 2018], and structured prediction [Stutz et al., 2022].

While conformal prediction excels at coverage control, it does not directly address loss minimization. Coverage guarantees ensure the true label is included but provide no control over the size or quality of prediction sets beyond this constraint.

### 2.2 Set-Valued Prediction

Set-valued prediction has been studied across multiple domains. In multi-label classification, threshold-based methods select labels exceeding confidence scores [Zhang & Zhou, 2014]. In object detection, non-maximum suppression produces sets of bounding boxes [Girshick et al., 2014]. These approaches typically optimize surrogate objectives rather than directly controlling the loss of interest.

### 2.3 Risk-Sensitive Learning

Risk-sensitive learning aims to control various notions of risk in machine learning models [García & Herrera, 2009]. Most work focuses on modifying training objectives or model architectures. In contrast, our approach works with pre-trained models and provides post-hoc risk control.

### 2.4 Statistical Learning Theory

Our theoretical analysis builds on concentration inequalities and martingale theory. The exchangeability assumption connects our work to online learning and sequential prediction [Cesa-Bianchi & Lugosi, 2006]. Unlike PAC-Bayes approaches that require prior distributions, our framework makes minimal assumptions about data generation.

## 3. Problem Formulation

### 3.1 Setup and Notation

Let $\mathcal{X}$ denote the input space and $\mathcal{Y}$ the label space. We observe a sequence of examples $(X_1, Y_1), \ldots, (X_n, Y_n), (X_{n+1}, Y_{n+1}), \ldots$ that are exchangeable. The first $n$ examples form our calibration set, while subsequent examples constitute the test set.

For each input $X_i$, we seek to construct a prediction set $\hat{S}(X_i) \subseteq \mathcal{Y}$. Let $\ell: \mathcal{Y} \times 2^{\mathcal{Y}} \rightarrow \mathbb{R}_{\geq 0}$ denote a loss function that measures the cost of predicting set $\hat{S}$ when the true label is $y$. We assume $\ell$ is bounded: $\ell(y, S) \leq M$ for some constant $M$.

### 3.2 Risk Control Objective

Our goal is to construct prediction sets such that the expected loss is controlled:

$$\mathbb{E}[\ell(Y_{n+1}, \hat{S}(X_{n+1}))] \leq \alpha$$

for a user-specified risk level $\alpha \geq 0$. This should hold with high probability based on finite calibration data, without assumptions beyond exchangeability.

### 3.3 Examples of Loss Functions

Our framework accommodates diverse loss functions:

**Set Size Loss**: $\ell(y, S) = |S|$ penalizes large prediction sets.

**False Negative Loss**: $\ell(y, S) = \mathbf{1}[y \notin S]$ counts missed labels.

**Hamming Loss**: For multi-label problems, $\ell(y, S) = |y \triangle S|$ where $\triangle$ denotes symmetric difference.

**Weighted Loss**: $\ell(y, S) = \sum_{s \in S} w(s) + \lambda \mathbf{1}[y \notin S]$ combines set size and coverage penalties.

**Detection Loss**: For object detection, $\ell$ can incorporate both localization errors and false positive/negative rates.

## 4. Risk-Controlling Prediction Sets

### 4.1 Core Algorithm

Our algorithm builds on conformal prediction but optimizes for loss control rather than coverage. Given a pre-trained model that outputs scores $f(x, y)$ for each input-label pair, we construct prediction sets using a data-dependent threshold.

**Algorithm 1: Risk-Controlling Prediction Sets**

*Input*: Calibration data $(X_1, Y_1), \ldots, (X_n, Y_n)$, model $f$, loss function $\ell$, risk level $\alpha$

1. **Compute conformity scores**: For each calibration example $i$:
   $$R_i = f(X_i, Y_i)$$

2. **Compute losses for threshold candidates**: For each $i \in \{1, \ldots, n\}$:
   $$L_i(\tau) = \ell(Y_i, \{y : f(X_i, y) \geq \tau\})$$

3. **Find optimal threshold**: 
   $$\hat{\tau} = \arg\min_{\tau} \left\{ \frac{1}{n} \sum_{i=1}^n L_i(\tau) : \frac{1}{n} \sum_{i=1}^n L_i(\tau) \leq \alpha \right\}$$

4. **Construct prediction sets**: For test input $x$:
   $$\hat{S}(x) = \{y : f(x, y) \geq \hat{\tau}\}$$

### 4.2 Theoretical Guarantees

Our main theoretical result provides finite-sample control of expected loss.

**Theorem 1** (Risk Control Guarantee): *Let $(X_1, Y_1), \ldots, (X_n, Y_n), (X_{n+1}, Y_{n+1})$ be exchangeable random variables. Let $\hat{S}$ be the prediction set constructed by Algorithm 1. Then for any $\delta \in (0, 1)$:*

$$\mathbb{P}\left[\mathbb{E}[\ell(Y_{n+1}, \hat{S}(X_{n+1})) | \mathcal{F}_n] \leq \alpha + \sqrt{\frac{M^2 \log(2/\delta)}{2n}}\right] \geq 1 - \delta$$

*where $\mathcal{F}_n$ is the sigma-algebra generated by the first $n$ examples and $M$ is the bound on the loss function.*

**Proof Sketch**: The key insight is that the sequence $Z_i = L_i(\hat{\tau}) - \alpha$ forms a martingale difference sequence under exchangeability. By Azuma-Hoeffding inequality and the optional stopping theorem, we can bound the deviation of the empirical average from its expectation. The threshold selection ensures that the empirical risk is at most $\alpha$, and concentration bounds control the gap to population risk.

### 4.3 Computational Efficiency

Algorithm 1 requires solving an optimization problem over threshold values. However, this can be implemented efficiently:

1. **Finite candidate set**: We only need to consider thresholds corresponding to conformity scores in the calibration set, giving $O(n)$ candidates.

2. **Efficient loss computation**: For many loss functions, the loss $L_i(\tau)$ can be computed efficiently as $\tau$ varies.

3. **Caching**: Prediction scores $f(X_i, y)$ can be precomputed and cached.

The overall complexity is $O(n \cdot |\mathcal{Y}| + n \log n)$ where $|\mathcal{Y}|$ is the label space size, making the approach practical for large-scale applications.

### 4.4 Connection to Conformal Prediction

RCPS generalizes conformal prediction in a natural way. When the loss function is $\ell(y, S) = \mathbf{1}[y \notin S]$ (false negative loss), our algorithm reduces to standard conformal prediction with risk level $\alpha$ corresponding to miscoverage rate $\alpha$.

However, RCPS enables much richer risk control. By choosing appropriate loss functions, practitioners can balance multiple objectives such as set size, coverage, and application-specific costs.

## 5. Extensions and Variants

### 5.1 Adaptive Risk Control

In many applications, the acceptable risk level may depend on the input. For instance, in medical diagnosis, higher risk may be acceptable for routine screenings than for emergency cases. We extend RCPS to handle input-dependent risk levels $\alpha(x)$.

**Algorithm 2: Adaptive RCPS**

The key modification is to use input-dependent thresholds $\hat{\tau}(x)$ computed by solving:

$$\hat{\tau}(x) = \arg\min_{\tau} \left\{ \frac{1}{n} \sum_{i=1}^n L_i(\tau) w_i(x) : \frac{1}{n} \sum_{i=1}^n L_i(\tau) w_i(x) \leq \alpha(x) \right\}$$

where $w_i(x)$ weights calibration examples based on similarity to test input $x$.

### 5.2 Multi-Objective Risk Control

Practitioners often care about multiple loss functions simultaneously. For example, in object detection, we may want to control both false positive and false negative rates. RCPS can be extended to handle multiple constraints:

$$\mathbb{E}[\ell_j(Y_{n+1}, \hat{S}(X_{n+1}))] \leq \alpha_j \quad \text{for } j = 1, \ldots, k$$

This leads to a multi-constraint optimization problem that can be solved using standard techniques.

### 5.3 Online Risk Control

For streaming applications, we may want to update our prediction sets as new data arrives. We develop an online variant of RCPS that maintains risk control guarantees while adapting to distribution shift.

## 6. Experimental Evaluation

### 6.1 Experimental Setup

We evaluate RCPS across three domains: computer vision, natural language processing, and structured prediction. Our experiments compare RCPS against baseline methods including standard conformal prediction, threshold-based approaches, and task-specific methods.

**Datasets**:
- **CIFAR-10/100**: Multi-label classification with synthetic multi-label targets
- **MS-COCO**: Object detection and semantic segmentation
- **Reuters-21578**: Multi-label text classification
- **CoNLL-2003**: Named entity recognition

**Models**: We use pre-trained models including ResNet, BERT, and task-specific architectures. Importantly, RCPS works with any model that produces confidence scores.

**Metrics**: We measure both risk control (expected loss) and efficiency (prediction set size). We also evaluate robustness to distribution shift and computational overhead.

### 6.2 Multi-Label Classification Results

On CIFAR-10 with synthetic multi-label targets, RCPS successfully controls various loss functions while maintaining competitive prediction set sizes. When controlling Hamming loss, RCPS achieves the target risk level within statistical error, while baseline methods either exceed the risk budget or produce unnecessarily large sets.

For weighted loss functions that penalize certain label errors more heavily, RCPS adapts the prediction sets appropriately, demonstrating the flexibility of our framework.

### 6.3 Object Detection Results

In MS-COCO object detection, we define loss functions that combine localization errors with false positive/negative penalties. RCPS constructs bounding box sets that satisfy the risk constraints while maintaining reasonable detection performance.

Compared to standard non-maximum suppression, RCPS provides principled risk control at the cost of slightly larger prediction sets. The trade-off is tunable through the choice of loss function and risk level.

### 6.4 Text Classification Results

On Reuters-21578, RCPS effectively controls various text classification loss functions. For applications where missing certain categories is particularly costly, RCPS appropriately adjusts prediction sets to minimize high-cost errors.

The method scales well to large label vocabularies and demonstrates robustness across different text domains.

### 6.5 Computational Performance

Across all experiments, RCPS adds minimal computational overhead. Threshold computation requires only a single pass through the calibration data, and prediction set construction is efficient for most loss functions.

Memory requirements scale linearly with calibration set size, making the approach practical for production systems.

## 7. Discussion and Limitations

### 7.1 Strengths

RCPS offers several advantages over existing approaches:

1. **Direct risk control**: Unlike coverage-based methods, RCPS directly optimizes the loss function of interest.

2. **Model-agnostic**: The framework works with any model that produces confidence scores.

3. **Distribution-free**: Only exchangeability is required, making the method robust to distribution shift.

4. **Computational efficiency**: The algorithm scales well to large datasets and label spaces.

5. **Interpretability**: Risk levels have direct meaning in terms of expected loss.

### 7.2 Limitations

Several limitations should be noted:

1. **Exchangeability assumption**: While weaker than i.i.d., exchangeability may not hold in all applications.

2. **Calibration data requirement**: The method requires a holdout calibration set, reducing available training data.

3. **Loss function choice**: Performance depends on choosing appropriate loss functions for the application.

4. **Finite-sample effects**: Guarantees become tighter with larger calibration sets.

### 7.3 Future Directions

Several extensions could enhance RCPS:

1. **Distribution shift adaptation**: Developing methods that maintain guarantees under covariate shift.

2. **Active learning**: Using RCPS to guide data collection for improved risk control.

3. **Federated learning**: Extending RCPS to distributed settings with privacy constraints.

4. **Theoretical improvements**: Tightening finite-sample bounds and extending to weaker assumptions.

## 8. Conclusion

We have introduced Risk-Controlling Prediction Sets, a distribution-free framework for constructing prediction sets with formal guarantees on expected loss. RCPS addresses a fundamental need in machine learning applications where practitioners require direct control over risk rather than just coverage.

Our theoretical analysis provides finite-sample guarantees under minimal assumptions, while our algorithmic approach ensures computational tractability. Experimental validation across diverse domains confirms the practical effectiveness of RCPS for various set prediction tasks.

The framework's flexibility in accommodating arbitrary loss functions makes it broadly applicable across machine learning domains. By shifting focus from coverage to risk control, RCPS provides practitioners with a principled tool for managing uncertainty in set-valued predictions.

Future work will explore extensions to handle distribution shift, multi-objective optimization, and online learning scenarios. We believe RCPS represents an important step toward practical uncertainty quantification in modern machine learning systems.

## References

[Cesa-Bianchi & Lugosi, 2006] N. Cesa-Bianchi and G. Lugosi. *Prediction, Learning, and Games*. Cambridge University Press, 2006.

[García & Herrera, 2009] S. García and F. Herrera. An extension on "statistical comparisons of classifiers over multiple data sets" for all pairwise comparisons. *Journal of Machine Learning Research*, 9:2677-2694, 2009.

[Girshick et al., 2014] R. Girshick, J. Donahue, T. Darrell, and J. Malik. Rich feature hierarchies for accurate object detection and semantic segmentation. In *CVPR*, 2014.

[Lei et al., 2018] J. Lei, M. G'Sell, A. Rinaldo, R. J. Tibshirani, and L. Wasserman. Distribution-free predictive inference for regression. *Journal of the American Statistical Association*, 113(523):1094-1111, 2018.

[Sadinle et al., 2019] M. Sadinle, J. Lei, and L. Wasserman. Least ambiguous set-valued classifiers with bounded error levels. *Journal of the American Statistical Association*, 114(525):223-234, 2019.

[Stutz et al., 2022] D. Stutz, K. Dvijotham, A. T. Cemgil, and A. Doucet. Learning optimal conformal classifiers. In *ICLR*, 2022.

[Zhang & Zhou, 2014] M.-L. Zhang and Z.-H. Zhou. A review on multi-label learning algorithms. *IEEE Transactions on Knowledge and Data Engineering*, 26(8):1819-1837, 2014.
