# geo-perplexity

Measure academic paper novelty through **conditional perplexity analysis**.

## Concept

Given a target paper, this pipeline computes how "predictable" its content is
when conditioned on different reference contexts:

| Context | What it measures |
|---------|-----------------|
| **Each cited paper** | How much does knowing reference *i* reduce surprise about the target? |
| **Target itself** (self-PPL) | Baseline — the model's intrinsic confidence on this text |
| **Random field reference** | Control — a topically related but non-cited paper |

Lower perplexity = more predictable = less novel contribution beyond the context.

## Method

**Exact conditional perplexity** via verbatim-echo with `logprobs=True`:

1. Reference paper text → system message (~6K tokens)
2. Target paper text is chunked into ~800-token windows
3. Model is instructed to **reproduce each chunk verbatim**
4. `logprobs=True` returns P(token_i | context, token_1..i-1) for each echoed token
5. **PPL = exp(−(1/N) Σ log p(token_i))**

This gives us the true conditional probability P(entire target | entire ref),
not a continuation-based approximation.

**Text extraction** uses an agentic multi-turn LLM parser: a first pass
extracts structured JSON from the PDF text, and if confidence is low, a
second refinement pass feeds additional pages to fill gaps.

## Pipeline

```
Stage 1: Ingest target paper (PDF / arXiv URL)
Stage 2: Fetch ALL cited references (Semantic Scholar, paginated, 100+)
Stage 3: Batch full-text extraction (arXiv PDF → LLM parser)
Stage 4: Find 1 random non-cited field reference
Stage 5: Compute PPL(target | context) for each (context, model) pair
Stage 6: Generate Markdown report with statistics and distribution
```

## Quickstart

```bash
# Install
pip install -r requirements.txt

# Set API key
export OPENAI_API_KEY=your_key_here

# Single paper
python run_analysis.py https://arxiv.org/abs/2006.06138

# Batch
python run_analysis.py --papers-file data/test_papers.ndjson

# Specific models
python run_analysis.py https://arxiv.org/abs/2006.06138 --models gpt-4o

# Both models (default)
python run_analysis.py https://arxiv.org/abs/2006.06138 --models gpt-5.4 gpt-4o
```

## Output

Reports are written to `reports/` as Markdown files containing:

- Self-perplexity baseline
- Random reference baseline
- Per-cited-reference perplexity table (sorted)
- Summary statistics (mean, median, std, min, max)
- Text histogram of perplexity distribution
- Model comparison table (when using multiple models)

## CI

The GitHub Actions workflow (`.github/workflows/geo-perplexity.yml`) can be
triggered manually via `workflow_dispatch` or automatically on push to the
`geo-perplexity` branch. It requires the `OPENAI_API_KEY` repository secret.

## Dependencies

- `openai>=1.0.0` — LLM API client
- `tiktoken>=0.7.0` — Token counting for context truncation
- `pdfplumber>=0.10.0` — PDF text extraction
- `python-dotenv>=1.0.0` — Environment variable loading
