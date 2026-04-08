# Archive: v0.3.1 — Abstract-Fallback Runs (2026-04-04)

## Code Version

- **Implementation ID:** `staged_reconstruct_v0_3_1`
- **Commit range:** `6298e97..ebdb2bd` (v0.1 through PR #100)
- **Student model:** claude-sonnet-4-20250514 (Anthropic) / gpt-4o (OpenAI)
- **Teacher model:** claude-opus-4-20250514 (Anthropic) / gpt-5.4 (OpenAI)

## What's in this archive

| Run | Papers | Conditions | Modes | Eval? | Notes |
|-----|--------|-----------|-------|-------|-------|
| run01 | 2006.06138 | with_refs only | 6 | No | First single-paper smoke test |
| run02 | 2602.04770 | with_refs only | 6 | No | Second paper smoke test |
| run03 | 2006.06138, 2602.04770 | with_refs + no_refs | 6 | No | First dual-condition run, pre-eval |
| run04 | 2103.04984 | with_refs + no_refs | 2 (abstract, mindmap) | Yes | Quick test after adding Lei-Candes PDF |
| run05 | All 3 papers | with_refs + no_refs | 6 | Yes | Full baseline with novelty gap analysis |

## Known technical caveats — read before interpreting results

### 1. Abstract-only text for 2 of 3 test papers

Papers **2006.06138** and **2602.04770** were processed using **abstract text only** as
the teacher's source material. Only **2103.04984** (Lei-Candes) had full PDF text cached.

**Scientific implication:** The teacher hint for abstract-only papers is derived almost
entirely from the abstract, which *describes the paper's approach*. This means the hint
likely **leaks the solution** to the student — the teacher cannot separate "problem setup"
from "novel contribution" when both are intertwined in a single abstract paragraph.

Scores for these papers (3.3–4.7) are therefore **inflated** relative to what a
properly-informed teacher would produce. The novelty gap analysis for these papers
reflects the student's ability to elaborate on an already-revealed approach, not genuine
problem-solving from first principles.

### 2. Teacher hint quality is bottlenecked by source text

With full text, the teacher prompt explicitly separates problem context from the paper's
solution. With abstract-only text, this separation is impossible. Consequently:

- **with_refs vs no_refs deltas** are attenuated for abstract-only papers (the hint
  already contains most of the signal, so references add less marginal information)
- **Cross-paper comparisons** (e.g., 2103.04984 vs 2006.06138) are confounded by text
  availability, not just paper difficulty

### 3. No reference paper full text

The reference paper **1904.06019** (Tibshirani et al., "Conformal Prediction Under
Covariate Shift") was provided to the student as metadata only (title, authors, abstract).
Full text was not available. This limits the student's ability to leverage reference
content for reconstruction, further attenuating the with_refs/no_refs contrast.

### 4. Single-run, no repetition

All results are from single LLM calls with no repetition or averaging. Score variance
across runs is unknown. Small deltas (< 0.5) should be interpreted cautiously.

### 5. Teacher evaluation is self-referential for abstract-only papers

When the teacher evaluates using only the abstract, it is essentially checking whether
the student's output matches the abstract's description — not whether it matches the
actual paper's full methodology. This creates a ceiling effect where students who
closely paraphrase the abstract score well, regardless of methodological depth.

### 6. Hallucinated paper metadata (discovered during archival)

The previous Claude session fabricated ALL paper metadata (titles, authors,
abstracts) in `test_papers.ndjson` instead of fetching the real papers at the
user-specified URLs. The original URLs from `main` branch were correct:

| URL | Actual Paper | What v0.3.1 Fabricated |
|---|---|---|
| `2006.06138` | Lei & Candès, "Conformal Inference of Counterfactuals and ITEs" | "Distribution-Free, Risk-Controlling Prediction Sets" (Bates et al.) — wrong title, wrong authors, wrong abstract |
| `2602.04770` | Deng et al., "Generative Modeling via Drifting" | "Conformal Prediction with Learned Features" (Gui & Barber) — completely fabricated paper |
| `2103.04984` (added in v0.2) | Huang et al., "Pair-Density-Wave in the Holstein-Hubbard model" (condensed matter physics) | "Conformal Inference of Counterfactuals" (Lei & Candès) — real paper, wrong ID |

**Impact on archived results:** The pipeline fell back to the fabricated
abstracts for 2006.06138 and 2602.04770, so the student reconstructed from
fictional problem descriptions. For 2103.04984, the previous session cached
the Lei & Candès PDF (which was really the paper at 2006.06138) and the
teacher produced hints from it — so only run04/run05 results for that paper
are scientifically meaningful, but under the wrong paper ID.

The reference paper (`1904.06019`) was always correct.

## What changes in the next version

The next round of runs will use **full paper text** (fetched from ar5iv HTML / arxiv
source) for all 3 test papers and the reference paper. This should:

1. Enable proper problem/solution separation in teacher hints
2. Produce more discriminative with_refs vs no_refs comparisons
3. Allow the teacher to evaluate against the actual methodology, not just the abstract
4. Give a more honest signal of the student's problem-solving capability
