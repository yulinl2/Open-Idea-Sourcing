# PROJECT_INSTRUCTIONS_AGENT.md

Charter for the **agent track** of Open-Idea-Sourcing. This document guides coding agents, review agents, and human maintainers. Read it before touching any agent-track branch.

---

## 1. Mission

Build an automated **research-IP judge**: given a target paper and access to searchable literature, determine whether its contribution is genuinely novel or largely derivable from prior work, identify the likely source ingredients, and isolate the true irreducible residual.

The output is not a related-work summary. It is a **derivation audit**:
- what came from where,
- what was merely assembled,
- what is equivalent in substance under reframing,
- and what, if anything, is the irreducible new residual.

---

## 2. Judgment standard

Judge **technical substance**, not surface novelty.

Do not reward:
- new terminology or framing alone,
- longer sections or more citations,
- low textual similarity,
- a new application domain by itself.

Judge:
- what problem is actually being solved,
- what mechanism does the core work,
- which assumptions are load-bearing,
- what specific algorithmic, proof, or implementation device creates the leap,
- and whether that device is already reconstructible from prior work.

---

## 3. Track split

Three independent, branch-local tracks — three separate worlds, not one shared ontology:

| Track | Branch | Character |
|-------|--------|-----------|
| `agent-e2e` | `agent-e2e` | End-to-end autonomous baseline: hand the agent a paper and let it drive its own tool loop with no externally imposed stage ordering. |
| `agent-linear` | `agent-linear` | Staged, auditable baseline: explicit ordered checkpoints, each serialised so any stage can be re-run independently. |
| `agent-reconstruct` | `agent-reconstruct` | Reconstruction track: teacher extracts a problem hint; student tries to reconstruct the methodology from the hint and an allowed reference set alone — no access to the paper's solution. The intuition is that reconstruction difficulty is a signal of genuine novelty. v1 produces a qualitative verdict (`MATCHED / PARTIAL / DIVERGED`). |

> **Long-term scientific aspiration (not a v1 goal):** The reconstruction-difficulty signal could eventually be formalised as a distance metric between a paper and its prior-work hull — analogous to a Wasserstein distance measured through reconstruction effort rather than embedding similarity. How to formulate and compute this rigorously is an open research question. v1 does not attempt it.

---

## 4. Branch and infra philosophy

- One orphan `infra-base` branch holds the shared execution shell (`infra/`). It is infrastructure, not methodology.
- Three clean track branches hold the actual methodologies. Track branches cherry-pick from `infra-base`; they never merge into each other or back into `main`.
- Each track branch is a self-contained world. Do not prematurely canonise speculative roles or future abstractions in shared modules.

---

## 5. Versioning

- The active implementation always keeps the canonical filename: `agent.py`.
- Frozen snapshots sit beside it: `agent_e2e_v1_0_0.py`.
- Every `agent.py` declares `AGENT_IMPL_ID = "e2e_v1_0_0"` at the top; this identifier is echoed in every `report.md` front matter.
- Milestones are marked by adjacent frozen copies and Git tags (`agent-e2e-v1.0.0`).
- No directory reorganisation is needed to preserve a snapshot.

---

## 6. Audit-first output

Optimise for **audit elegance**, not framework elegance.

- GitHub-first, phone-friendly.
- Minimum hidden state. Everything important is visible in files.
- One canonical `report.md` per run. No separate sidecar databases.
- The repo behaves like a lab notebook.

### `report.md` required structure

Every run must produce one `report.md` with:

| Section | Purpose |
|---------|---------|
| YAML front matter | Run metadata (see §7) |
| Table of contents | Clickable navigation |
| Executive summary | One-paragraph verdict summary |
| Final verdict | `NOVEL / COMBINATION / EQUIVALENT / DUPLICATE` with confidence |
| Technical contribution decomposition | Break the paper's contribution into units |
| Strongest prior-work evidence | Top 3–5 references with derivation notes |
| Derivation map | Table: component → likely source paper → derivation type |
| Residual novelty | What is genuinely new, if anything |
| Uncertainties | What was not found, what could not be verified |
| Audit appendix | Tool calls, search queries, timestamps |

---

## 7. Required run metadata

Every `report.md` YAML front matter must include:

```
track, impl_id, paper_id, paper_source, model, tool_list,
start_time, finish_time, git_commit,
final_verdict, confidence, main_cited_evidence
```

Optionally: `response_id` when the SDK returns a run/response ID.

This enables later comparison across runs, branches, and frozen snapshots from the file alone.

---

## 8. Tool philosophy: maximally agentic

Use the model's **native `web_search` tool** as the primary literature discovery mechanism. Let the agent decide what to search, in what order, and when it has enough evidence. Do not build custom retrieval pipelines for what the model can do natively.

`infra/search_tools.py` (Semantic Scholar, arXiv) exists as a **last-resort fallback only** — for when structured citation metadata (canonical IDs, citation counts) is genuinely needed and native search is insufficient.

The one deliberate exception: the `agent-reconstruct` student agent has **no search tools by design** — its task is reconstruction from the provided reference set alone, not open retrieval.

The runtime is a support layer. The product is the derivation audit.

---

## 9. What the agent must produce

For each target paper:

1. Identify the actual technical contribution.
2. Decompose it into meaningful technical units.
3. Search broadly for plausible prior-work sources.
4. Compare the target against the strongest candidates.
5. Build a derivation map: component → likely source.
6. Judge: duplication / recombination / equivalence / novelty.
7. Isolate the residual genuine contribution.
8. Explicitly flag uncertainty where retrieval or evidence is weak.

---

## 10. Anti-goals

Do **not** build:
- a crowded global role taxonomy,
- premature version-folder forests,
- framework ornament that hides what the agent actually did,
- or a monolithic main branch mixing incompatible partial designs.

Do **not** confuse:
- surface novelty with real novelty,
- low textual overlap with conceptual originality,
- or implementation busyness with scientific contribution.

---

## 11. Success criteria

The agent track is working if:

- each track branch is clean, self-explanatory, and independently runnable,
- every run can be fully audited from one `report.md`,
- implementation identity is always logged and cross-run comparison is trivial,
- and a domain expert reads the report and says: *"Yes, this is the derivation story I wanted to know."*

---

## 12. One-sentence charter

Build a GitHub-first, audit-readable, branch-isolated **agentic research-IP judge** whose baseline tracks are cleanly comparable, whose reconstruction track can evolve toward a rigorous novelty signal, and whose implementation history stays visible through adjacent frozen snapshots rather than hidden framework state.
