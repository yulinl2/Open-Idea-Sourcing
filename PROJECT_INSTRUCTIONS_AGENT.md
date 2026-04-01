# PROJECT_INSTRUCTIONS_AGENT.md

This document defines the **agent track** development goal for Open-Idea-Sourcing. It is meant to guide coding agents, review agents, and future human maintenance. The purpose of the agent track is **not** to imitate the old programmatic pipeline. Its purpose is to directly pursue the real scientific target: an automated **research-IP judge** that can tell whether a paper is genuinely novel or largely derivable from prior work, identify the likely source ingredients, and isolate the true residual contribution.

## 1. Mission

Given a target paper and access to searchable literature/tools, the system should determine whether the paper's contribution is:
- largely duplicated from known work,
- mainly a recombination of known ingredients,
- methodologically equivalent to prior work under reframing,
- or genuinely novel in some technically meaningful component.

The output should not be a generic related-work summary. It should be a **derivation audit**:
- what came from where,
- what was merely assembled,
- what is equivalent in substance,
- and what appears to be the irreducible new residual.

## 2. Core judgment standard

Judge **technical substance**, not wording novelty.

Do not over-reward:
- new terminology,
- new framing,
- section length,
- citation omission,
- low textual similarity,
- or a new application domain by itself.

Instead, judge:
- what problem is actually being solved,
- what mechanism actually does the work,
- which assumptions are load-bearing,
- where the real bottleneck is,
- what implementation/proof/algorithmic device creates the leap,
- and whether these pieces are already reconstructible from prior work.

## 3. Track split

The agent family is split into three branch-local tracks:

- `agent-e2e`
- `agent-linear`
- `agent-reconstruct`

These are **three separate worlds**, not one crowded ontology.

### `agent-e2e`
End-to-end autonomous review baseline.

### `agent-linear`
Checkpointed linear workflow baseline. The exact number of stages is not sacred; the point is explicit ordered checkpoints.

### `agent-reconstruct`
The real discovery track. The key intuition: if an agent can independently reconstruct a
paper's methodology from nothing but the problem statement and prior work, the paper is
likely derivative. If the reconstruction diverges significantly, the paper likely contains
genuine novel contribution.

*(Long-term vision, not a v1 formulation: this track aspires to operationalize novelty as
a Wasserstein-like distance between the paper and its prior-work hull — measured through
reconstruction difficulty rather than embedding similarity. v1 produces a qualitative
verdict only; the quantitative distance metric is future work.)*

## 4. Branch philosophy

Do **not** mix all speculative roles and future abstractions into one global module zoo.

Preferred structure:
- one small `infra-base` branch for truly shared execution shell only,
- three clean track branches for the actual methodologies,
- cherry-pick infra improvements into tracks only when needed.

Each track branch should contain only its own current worldview. If a role may disappear later, do **not** prematurely canonize it in a shared top-level taxonomy.

## 5. Versioning philosophy

Do **not** create large version-folder forests on day 1.

Preferred rule:
- the active implementation keeps the canonical filename, e.g. `agent.py`
- frozen snapshots sit beside it in the same folder, e.g. `agent_e2e_v1_0_0.py`
- the active script declares a visible implementation identifier, e.g.
  `AGENT_IMPL_ID = "e2e_v1_0_0"`
- that identifier must be automatically logged into run audit outputs

Milestones should be preserved by:
- adjacent frozen copies for local human-readable history
- Git tags when a meaningful milestone is reached

No extra rewiring should be required just to preserve an implementation snapshot.

## 6. Human-readability principle

Optimize for **audit elegance**, not framework elegance.

This means:
- GitHub-first
- phone-friendly
- minimum hidden state
- deterministic file layout
- everything important visible in files
- no requirement that humans read Python just to understand a run

The repo should behave like a lab notebook, not a black box.

## 7. Canonical run artifact

A normal run should produce **one canonical Markdown report**.

Default:
- `report.md`

Optional:
- `response.json` only when raw payload retention is genuinely useful
- attachments only when bulky debug materials are needed

The report must be structured enough that later housekeeping can reconstruct the key run state from it.

### `report.md` must contain:
- YAML front matter with run metadata
- clickable table of contents
- executive summary
- final verdict
- technical contribution decomposition
- strongest prior-work evidence
- derivation map
- residual novelty
- uncertainties
- audit appendix
- embedded machine-readable JSON blocks where useful

Principle:
- keep the **data model rich**
- keep the **file model minimal**

## 8. Required metadata in every run report

At minimum, each report must preserve:
- `track`
- `impl_id`
- `paper_id`
- `paper source`
- `model`
- `tool list`
- `response_id` if available
- start / finish timestamps
- Git commit hash if available
- final verdict
- confidence
- main cited evidence

This is necessary for later comparison across runs, branches, and frozen snapshots.

## 9. Tool/runtime philosophy

The agent track should use a programmable agentic runtime, not naive plain chat completion as the main long-term substrate. The current repo implementation was closer to a hand-built pipeline wrapped around simple completion-style calls; the agent track should move toward a run-oriented surface where one paper review is treated as a first-class task/run with auditable metadata and tool usage.

**Maximally agentic.** Do not implement custom search functions for what the model can do natively. Use the model's built-in `web_search` tool (e.g., via the OpenAI Responses API) as the primary literature discovery mechanism — let the agent decide what to search, in what order, and when it has enough evidence. Custom `infra/search_tools.py` (Semantic Scholar, arXiv) is a last-resort fallback for structured metadata, not a substitute for the model's native capabilities.

However, do **not** let framework complexity dominate readability. The runtime is a support layer, not the product. The product is the derivation audit.

## 10. What the agent must do

For each target paper, the agent must:

1. Identify the paper's actual technical contribution.
2. Break that contribution into meaningful technical units.
3. Search broadly for plausible prior-work sources.
4. Compare the target against the strongest candidate sources.
5. Build a derivation map from target components to likely source papers.
6. Judge duplication / recombination / equivalence / novelty.
7. Identify the residual genuine contribution.
8. Be explicit about uncertainty when retrieval or evidence is weak.

## 11. Anti-goals

Do **not** optimize for:
- a crowded global role taxonomy,
- premature folderized version trees,
- software-engineering ornament,
- hidden framework state,
- report archaeology across many disconnected sidecar files,
- or a giant main branch mixing incompatible partial designs.

Do **not** confuse:
- surface novelty with real novelty,
- low textual overlap with conceptual originality,
- or implementation busyness with scientific contribution.

## 12. Immediate success criteria

The current agent track is successful if:

- each branch (`agent-e2e`, `agent-linear`, `agent-reconstruct`) remains clean and self-explanatory,
- frozen copies are easy to compare beside the active implementation,
- every run can be audited mainly from one `report.md`,
- implementation identity is always logged,
- and a domain expert can read the report and say:
  "Yes, this is the real derivation story I wanted to know."

## 13. One-sentence charter

Build a GitHub-first, audit-readable, branch-local **agentic research-IP judge** whose baseline tracks are cleanly comparable, whose reconstruction track can evolve aggressively, and whose implementation history stays visible through adjacent frozen snapshots rather than hidden framework state.
