# Reconstruction: problem
**Paper:** 2006.06138  
**Condition:** with_refs  
**Student model:** claude-sonnet-4-20250514  
**Teacher model:** claude-opus-4-20250514  

---

# Problem Formulation

## Notation and Setup

Let $(\mathcal{X}, \mathcal{Y})$ denote the covariate and outcome spaces, where $\mathcal{X} \subseteq \mathbb{R}^d$ and $\mathcal{Y} \subseteq \mathbb{R}$. We observe $n$ units with covariates $X_i \in \mathcal{X}$ and binary treatment assignments $T_i \in \{0,1\}$ for $i = 1, \ldots, n$. For each unit $i$, we observe the realized outcome $Y_i \in \mathcal{Y}$ corresponding to the received treatment.

Following the potential outcomes framework, let $Y_i(0)$ and $Y_i(1)$ denote the potential outcomes for unit $i$ under control and treatment, respectively. The fundamental problem of causal inference is that we only observe $Y_i = T_i Y_i(1) + (1-T_i) Y_i(0)$ for each unit, never both potential outcomes simultaneously.

Define the individual treatment effect (ITE) for unit $i$ as:
$$\tau_i = Y_i(1) - Y_i(0)$$

Let $P$ denote the joint distribution of $(X_i, Y_i(0), Y_i(1), T_i)$, and let $P_X$ denote the marginal distribution of covariates. We consider both randomized experiments where treatment assignment is independent of potential outcomes given covariates, and observational studies under unconfoundedness.

For a new unit with covariates $x \in \mathcal{X}$, our goal is to construct a prediction interval $\mathcal{C}_n(x) \subseteq \mathcal{Y}$ for the individual treatment effect $\tau(x)$ that provides reliable uncertainty quantification.

## Formal Problem Statement

**Given:** 
- Training data $\mathcal{D}_n = \{(X_i, T_i, Y_i)\}_{i=1}^n$
- A new covariate vector $x \in \mathcal{X}$  
- A desired coverage level $1-\alpha$ for $\alpha \in (0,1)$

**Find:** A prediction interval $\mathcal{C}_n(x) \subseteq \mathbb{R}$ such that:
$$\mathbb{P}[\tau(x) \in \mathcal{C}_n(x)] \geq 1-\alpha$$

**Constraints:**
- The coverage guarantee must hold in finite samples without asymptotic approximations
- The method should be robust to model misspecification
- The guarantee should hold regardless of the dimensionality $d$ or complexity of the underlying relationships

## Objective and Formal Guarantee

Our primary objective is to construct a distribution-free prediction interval that satisfies:

$$\liminf_{n \to \infty} \mathbb{P}[\tau(X_{n+1}) \in \mathcal{C}_n(X_{n+1})] \geq 1-\alpha$$

where $(X_{n+1}, Y_{n+1}(0), Y_{n+1}(1))$ is an independent draw from the same distribution as the training data.

More precisely, we seek a procedure that produces intervals $\mathcal{C}_n(x)$ satisfying the finite-sample guarantee:
$$\mathbb{P}[\tau(X_{n+1}) \in \mathcal{C}_n(X_{n+1}) \mid \mathcal{D}_n] \geq 1-\alpha - \delta_n$$

where $\delta_n \to 0$ as $n \to \infty$, and ideally $\delta_n = O(n^{-1})$.

Additionally, we desire that the intervals have reasonable efficiency properties:
$$\mathbb{E}[|\mathcal{C}_n(X_{n+1})|] = O_P(n^{-\beta})$$

for some $\beta > 0$, where $|\mathcal{C}_n(x)|$ denotes the length of the interval.

## Technical Assumptions

**A1. Exchangeability/Sampling:** The observed data $(X_i, T_i, Y_i)_{i=1}^{n+1}$ are exchangeable, or alternatively, satisfy a weighted exchangeability condition when covariate distributions differ between training and test populations.

**A2. Treatment Assignment:** Either:
- (Randomized) $T_i \perp (Y_i(0), Y_i(1)) \mid X_i$ with known propensity scores $e(x) = \mathbb{P}[T_i = 1 \mid X_i = x]$ bounded away from 0 and 1, or  
- (Observational) Unconfoundedness holds: $(Y_i(0), Y_i(1)) \perp T_i \mid X_i$ with overlap: $0 < e(x) < 1$ for all $x$ in the support of $P_X$.

**A3. Outcome Boundedness:** The potential outcomes satisfy $Y_i(t) \in [y_{\min}, y_{\max}]$ for $t \in \{0,1\}$ and some known or estimable bounds, ensuring that individual treatment effects are bounded: $|\tau_i| \leq y_{\max} - y_{\min}$.

**A4. Covariate Shift (when applicable):** When training and test covariate distributions differ, we assume absolute continuity $\tilde{P}_X \ll P_X$ with a known or estimable likelihood ratio $w(x) = d\tilde{P}_X/dP_X(x)$.

**A5. Score Function Regularity:** Any conformity score function $S((x,t,y), \mathcal{D})$ used in the construction is symmetric with respect to permutations of the data points in $\mathcal{D}$.

These assumptions are justified as follows: A1 enables the application of conformal prediction methodology; A2 ensures identifiability of treatment effects; A3 provides the boundedness needed for finite-sample guarantees; A4 allows extension to distribution shift scenarios common in practice; A5 ensures the exchangeability properties required for conformal inference are preserved.

## Connection to Prior Work

Classical approaches to heterogeneous treatment effect estimation focus on consistency and convergence rates of point estimators, typically relying on machine learning methods like causal forests, T-learners, or meta-learners. However, these methods provide limited uncertainty quantification, often requiring strong parametric assumptions or asymptotic approximations that may fail in finite samples.

Recent work on conformal prediction, particularly Tibshirani et al. (2020), demonstrates how to construct distribution-free prediction intervals under covariate shift by weighting the empirical distribution of nonconformity scores. However, this framework has not been extended to the causal inference setting where the fundamental challenge is the missing counterfactual outcomes.

Our formulation addresses the gap between these literatures by extending conformal prediction methodology to handle the inherent missingness structure in causal inference problems. Unlike existing approaches that focus on average treatment effects or require strong modeling assumptions, our framework provides individual-level uncertainty quantification that is robust to model misspecification while maintaining finite-sample validity guarantees. This represents a significant advance in making causal inference methods more reliable for high-stakes decision-making applications.
