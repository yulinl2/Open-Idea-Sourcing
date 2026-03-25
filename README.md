# OpenIdeaS

## Dev Status
- Project still under exploratory stage; multiple implementations attempted, each with their own deficits and highlights, the latter to be cherrypicked and aggregated to a brand new rebuild
- Sometimes Copilot agent memory is hindering independent revamps = =||
- Next ver roadmap: https://github.com/yulinl2/Open-Idea-Sourcing/issues/42#issue-4133103018

<details>
<summary>
See high-level pipeline (ideal structure)
</summary>

> > ## Ideal Architecture (From Scratch)
> > ```
> > [Stage 1 — Ingest]
> >   Input: paper URL / file
> >   Output: PaperDigest {title, abstract, full_text, source_url, arxiv_id}
> >   Swap point: PDF parser, arXiv API, manual input
> > 
> > [Stage 2 — Understand]
> >   Input: PaperDigest
> >   Output: IdeaDecomposition {core_concept, sub_ideas, assumptions, limitations}
> >   LLM prompt: independently versioned, separately testable
> > 
> > [Stage 3 — Retrieve]
> >   Input: PaperDigest + IdeaDecomposition
> >   Sub-stages (parallel, each independently togglable):
> >     3a. BundledReferenceSearch (TF-IDF over data/references.json)
> >     3b. OnlineReferenceSearch (Semantic Scholar: arXiv refs + keyword)
> >     3c. LLMQueryGenerator (conceptual queries from decomposition)
> >     3d. DomainRefFinder (LLM identifies key domain references)
> >   Output: ReferenceStore (merged, deduplicated, with source tags)
> > 
> > [Stage 4 — Compare]
> >   Input: PaperDigest + IdeaDecomposition + top-K from ReferenceStore
> >   Output: list[SimilarityAnnotation] {paper, score, overlap, differences, derivation}
> >   LLM prompt: has full decomposition context — grounds comparisons structurally
> > 
> > [Stage 5 — Evaluate]  ← can be parallelized; each pass is independent
> >   Input: PaperDigest + IdeaDecomposition + list[SimilarityAnnotation]
> >   5a. DuplicationCheck   → {verdict, explanation, citations[]}
> >   5b. CombinationCheck   → {verdict, explanation, citations[]}
> >   5c. EquivalenceCheck   → {verdict, explanation, citations[]}
> >   Key change: each prompt explicitly requires citation references by ID
> > 
> > [Stage 6 — Synthesize]
> >   Input: all Stage 5 outputs
> >   Output: {overall_verdict, summary, confidence, cited_evidence[]}
> >   Key change: every sentence maps to a specific annotation or decomposition item
> > 
> > [Stage 7 — Render]
> >   Input: PaperDigest + IdeaDecomposition + NoveltyReport
> >   Output: Markdown / JSON / PDF (same data, different views)
> > ```

</details>



## Core Algorithms

### Novelty Metric
- Textual similarity (TF-IDF cosine similarity (0–1)) is actually effective -- as long as the reference is given; 
    - see [score 0.40 over provided ideal ref](https://github.com/yulinl2/Open-Idea-Sourcing/blob/reports/Conformal_Inference_of_Counterfactuals_and_ITF/v2.1.0/Conformal_Inference_of_Counterfactuals_and_Individual_Treatm_2026-03-25T170229.md#reference-annotations)
    - compared to [score <0.25 over 10 searched refs](https://github.com/yulinl2/Open-Idea-Sourcing/blob/reports/Conformal_Inference_of_Counterfactuals_and_ITF/v2.0.0/Conformal_Inference_of_Counterfactuals_and_Individual_Treatm_2026-03-25T092516.md#reference-annotations)
    - [score <0.30 over 10 searched refs](https://github.com/yulinl2/Open-Idea-Sourcing/blob/reports/Conformal_Inference_of_Counterfactuals_and_ITF/v2.1.0/Conformal_Inference_of_Counterfactuals_and_Individual_Treatm_2026-03-25T170246.md#most-similar-reference-papers)

### Pipeline Bottleneck

**[Stage 3: Retrieval]** 
- Issue: 
    - ↑ So the main bottleneck is still scientific understanding in ref search/retrieval 
    - More specific prompts didn't seem to help?
    - Time filtering is also needed -- gotta filter out [successors in time](https://github.com/yulinl2/Open-Idea-Sourcing/blob/reports/Conformal_Inference_of_Counterfactuals_and_ITF/v2.1.0/Conformal_Inference_of_Counterfactuals_and_Individual_Treatm_2026-03-25T170246.md#most-similar-reference-papers) during search
- Solution: 
    - Try OpenScholar (closer to WisPaper functionality) at some point
    - Optimize search query and iterative refinement strategy

**[Stage 4&5: Annotation & Evaluation]** 
- Issue: 
    - ↑ Annotation is still bad as well -- (score: 0.40 over provided ref, but not identified as derivation)
    - Can probably be the model capability issue again
- Solution: 
   - easy immediate fix: more powerful model
   - ideal long-term goal: powerful pipeline empowering weak models)

**[Stage 2: Ingestion]** 
- Issue: 
    - LLM model choice seems to matter a lot for effectiveness of idea decomposition (beyond shallow format fit) 
    - gpt-4o is verbose but not targeting the true key tech element (doing worse than the Copilot example lol)
        - See [gpt-4o execution](https://github.com/yulinl2/Open-Idea-Sourcing/blob/reports/Conformal_Inference_of_Counterfactuals_and_ITF/v2.0.0/Conformal_Inference_of_Counterfactuals_and_Individual_Treatm_2026-03-25T092516.md#concept-tree)
        - Still [by gpt-4o](https://github.com/yulinl2/Open-Idea-Sourcing/blob/reports/Conformal_Inference_of_Counterfactuals_and_ITF/v2.1.0/Conformal_Inference_of_Counterfactuals_and_Individual_Treatm_2026-03-25T170246.md#concept-tree): a slightly deeper version (which actually pushed the verdict towards "novel - high confidence" lol)
        - See Copilot template example: https://github.com/yulinl2/Open-Idea-Sourcing/issues/41#issuecomment-4124145000
- Solution: 
    - trying to change API models (o-series for reasoning capability)
    - may attempt Claude for ablation

**[Stage 1: Parser]** 
- Issue: [Paper parser very bad](https://github.com/yulinl2/Open-Idea-Sourcing/blob/reports/Conformal_Inference_of_Counterfactuals_and_ITF/v2.0.0/Conformal_Inference_of_Counterfactuals_and_Individual_Treatm_2026-03-25T092516.md#pipeline-job-log)
- Solution: probably needed an LLM agent 

# HAN
Next week theory goal (to ease Stat presentation): 
- post as a statistical error bounding problem against **some target logical function** over some **abstract concept space** with basic distance metrics
