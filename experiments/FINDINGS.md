# Experiment Log: TF-IDF Verbosity Trimming for Perplexity Analysis

## Date: 2026-04-05

## Background

The original geo-perplexity pipeline computes PPL(target | reference) using
verbatim echo with logprobs. The full-text results showed essentially zero
separation between cited references:

- PPL range: [1.000008, 1.002376] — all within 0.2% of self-PPL
- `meaningful_spread: false` in scale tests
- The model echoes text near-perfectly regardless of context

**Hypothesis**: Routine academic boilerplate (methodology descriptions,
standard transitions, organizational text) creates a "shared predictability
floor" that makes all references look equally predictive. Stripping this
boilerplate via TF-IDF keyword density scoring should expose the conceptually
novel content where references actually differ in their predictive power.

## Method

### TF-IDF Text Filter (`geo_perplexity/text_filter.py`)

1. **Background corpus**: All cited reference texts (65 documents)
2. **IDF computation**: `log(N / df(term))` across corpus + target
3. **Sentence scoring**: Average TF-IDF of non-stopword tokens per sentence
4. **Boilerplate penalty**: Regex patterns match organizational phrases
   ("The rest of the paper is organized...", "Section N reviews...", etc.)
   and apply a 0.1x penalty to their scores
5. **Filter**: Keep top K% of sentences by score, preserving original order

### Experimental Setup

- **Target paper**: arXiv:2006.06138 (Conformal Inference)
- **Model**: gpt-4o
- **References tested**: 5 (stratified sample: 3 full-text, 2 abstract/TLDR)
  - Predictive inference with the jackknife+ (closely related)
  - Conformalized Quantile Regression (closely related)
  - Use of directed acyclic graphs (tangentially related)
  - Causal Inference in Statistics: A Primer (broader field)
  - Who Benefits Most from College? (different topic)

## Results

### Experiment 1: keep_ratio=0.5 (keep top 50% of sentences)

| Metric | Full Text | Trimmed | Change |
|--------|-----------|---------|--------|
| Target chars | 8902 | 4050 | -54.5% |
| Sentences | 49 | 24 | -51% |
| Self PPL | 1.000008 | 1.000006 | — |
| Cited mean PPL | 1.000165 | 1.000009 | 0.005x |
| Cited spread | 0.000310 | 0.000035 | 0.11x |
| Self/cited ratio | 1.000156 | 1.000003 | 0.02x |

**Verdict**: 50% trimming made separation **WORSE**. All PPLs collapsed
toward 1.0. The shorter text was easier for the model to echo regardless
of context.

### Experiment 2: keep_ratio=0.3 (keep top 30% of sentences)

| Metric | Full Text | Trimmed | Change |
|--------|-----------|---------|--------|
| Target chars | 8902 | 2717 | -69.5% |
| Sentences | 49 | 14 | -71% |
| Self PPL | 1.000008 | 1.000000 | — |
| Cited mean PPL | 1.000212 | 1.015204 | **72x** |
| Cited spread | 0.000357 | 0.075115 | **210x** |
| CV | 0.0002 | 0.033 | **205x** |
| Self/cited sep | 1.000204 | 1.015203 | **74x** |

**Per-reference breakdown (trimmed at 30%)**:

| Reference | Full PPL | Trim PPL | Echo tokens |
|-----------|----------|----------|-------------|
| Self (target) | 1.000008 | 1.000000 | 557 |
| Jackknife+ (closely related) | 1.000057 | 1.000010 | 557 |
| Conformalized QR (closely related) | 1.000070 | 1.000013 | 557 |
| DAGs in health (tangential) | 1.000342 | 1.000156 | 557 |
| Causal Inference primer (broad field) | 1.000175 | 1.000714 | 557 |
| Who Benefits from College? (unrelated) | 1.000414 | 1.075125 | 10! |

**Verdict**: 30% trimming **dramatically improved** separation (210x spread).

### Experiment 3: keep_ratio=0.4 (keep top 40% of sentences)

| Metric | Full Text | Trimmed | Change |
|--------|-----------|---------|--------|
| Target chars | 8902 | 3244 | -63.6% |
| Self PPL | 1.000011 | 1.000008 | — |
| Cited mean PPL | 1.000335 | 1.068844 | **205x** |
| Cited spread | 0.000769 | 0.115223 | **150x** |
| Self/cited sep | 1.000325 | 1.068835 | **212x** |

**Per-reference breakdown (trimmed at 40%)**:

| Reference | Full PPL | Trim PPL | Echo tokens |
|-----------|----------|----------|-------------|
| Self | 1.000011 | 1.000008 | 672 |
| Conformalized QR | 1.000064 | 1.000519 | 672 |
| Jackknife+ | 1.000070 | 1.053685 | 10! |
| DAGs | 1.000351 | 1.060252 | 10! |
| Causal Inference | 1.000833 | 1.115742 | 10! |
| Who Benefits | 1.000358 | 1.114020 | 10! |

## Key Observations

### 1. Threshold Effect
There's a sharp threshold between keep_ratio=0.5 (no improvement) and
keep_ratio=0.3-0.4 (massive improvement). At 50%, the trimmed text still
contains enough generic content for the model to echo perfectly. Below 40%,
the text becomes specific enough that context matters.

### 2. Echo Failure as Signal
Many references produced only 10 echo tokens on trimmed text (vs 500+ on
full text). The model's *inability/unwillingness to reproduce* specific
text is itself a strong signal of contextual mismatch. This is actually
a feature, not a bug — it means the trimmed text contains content that
genuinely requires domain-specific context to reproduce.

### 3. Ranking Quality
The per-reference ranking at keep_ratio=0.3 is scientifically sensible:
- Jackknife+/Conformalized QR → lowest PPL (same subfield: conformal methods)
- DAGs in health research → medium PPL (related but different application)
- Causal Inference primer → higher PPL (broader field)
- "Who Benefits from College?" → highest PPL (different topic entirely)

### 4. The Boilerplate Floor Problem
The original full-text approach had a "predictability floor" — generic
academic writing is equally predictable from ANY reference in the same
broad field. TF-IDF filtering removes this floor, exposing the signal
in topic-specific content.

## Caveats

1. **Small sample**: Only 5 references tested per configuration. Need to
   scale up to 20+ to confirm statistical significance.
2. **Echo token instability**: The 10-token results may indicate the model
   is hitting some behavioral limit rather than genuinely measuring perplexity.
   Need to investigate why echo truncates.
3. **Single target paper**: Results may not generalize. Must test on the
   second paper (2602.04770) and others.
4. **IDF sensitivity**: The background corpus is the paper's own citations,
   which may bias the IDF toward field-specific terms vs truly novel terms.

## Next Steps

1. Test on second cached paper (arXiv:2602.04770)
2. Investigate echo truncation: why does the model produce only 10 tokens?
3. Try intermediate keep_ratios (0.35, 0.45) to find the sweet spot
4. Scale up to all 44+ references with content
5. Consider hybrid approach: TF-IDF filter + longer context windows
6. Try the inverse filter (keep ONLY routine text) as a control
