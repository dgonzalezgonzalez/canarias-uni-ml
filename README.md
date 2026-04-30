# canarias-uni-ml

Python pipeline for Canary Islands job postings plus Spanish university degree catalogs and alignment scoring based on text embeddings.

## Status

| Surface | Status | Notes |
|--------|--------|-------|
| SCE | ✅ Working | API JWT, número de ofertas variable |
| Turijobs | ✅ Working | Sitemap + detail pages |
| Indeed (JobSpy) | ✅ Working | Fuente principal para escalado |
| Geography / contract normalization | ✅ Working | Canonical + raw fields coexist |
| Degree catalog | 🧪 Working baseline | Fixture/live ANECA + university enrichments |
| Embeddings | 🧪 Working baseline | OpenAI + Ollama providers with cache |
| Alignment DB | 🧪 New | Candidate-gated cosine similarity in SQLite |

## Environment Variables

```bash
export JOBSPY_PROXIES='["user:pass@host:port"]'   # optional
export OPENAI_API_KEY='sk-...'                      # required for OpenAI embeddings
export GROQ_API_KEY='...'                           # optional experiments
export OLLAMA_BASE_URL='http://127.0.0.1:11434'    # local testing provider
export OLLAMA_EMBEDDING_MODEL='nomic-embed-text'   # local embedding model
```

Important: ChatGPT subscription and OpenAI API billing are separate. API usage must be configured on `platform.openai.com`.

## Quickstart

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium

# Scrape jobs
python -m src.canarias_uni_ml.cli jobs scrape --limit-per-source 50

# Build degree catalog from fixture
python -m src.canarias_uni_ml.cli degrees catalog --fixture tests/fixtures/degrees_catalog_fixture.json

# Embedding dry run
python -m src.canarias_uni_ml.cli embed build --input tests/fixtures/semantic_corpus.jsonl --dry-run

# Alignment only (local Ollama by default)
python -m src.canarias_uni_ml.cli align run --provider ollama

# Full master pipeline in one command
python -m src.canarias_uni_ml.cli pipeline run --provider ollama

# Scale run with OpenAI
python -m src.canarias_uni_ml.cli pipeline run --provider openai --model text-embedding-3-small
```

Legacy job-only commands still route through compatibility wrapper in `src.canarias_jobs.cli`.

## Outputs

- `data/processed/canarias_jobs.csv`
- `data/processed/canarias_jobs.db`
- `data/processed/degrees_catalog.csv`
- `data/processed/embeddings_manifest.json`
- `data/processed/program_job_alignment.db`

## Project Layout

```text
src/canarias_uni_ml/
├── cli.py                # Multi-domain CLI
├── config.py             # Settings and output paths
├── io.py                 # CSV/JSONL writers
├── jobs/                 # Job scraping pipeline
├── degrees/              # Degree catalog pipeline
├── embeddings/           # Provider abstraction + cached vectors
├── alignment/            # Pairing + cosine similarity + DB persistence
├── pipeline/             # Master orchestration command
└── normalization/        # Canonical geography / contract type
```

## Job Data Contract

Canonical and raw values both persist:

- `province`, `municipality`, `island`, `contract_type`: canonical values
- `province_raw`, `municipality_raw`, `island_raw`, `contract_type_raw`: original scraped values
- `raw_location`: original free-text location

## Nightly Daemon

- Command: `python -m src.canarias_uni_ml.cli jobs daemon`
- Default schedule: `22:00` to `07:30` (`Europe/Madrid`)
- Behavior:
  - process stays alive and only scrapes inside configured window
  - writes canonical state to SQLite (`data/processed/canarias_jobs.db`)
  - exports snapshot CSV after each cycle (`data/processed/canarias_jobs.csv`)
  - avoids duplicates across nights
  - on repeated jobs, updates row only when payload changed; unchanged rows are skipped

Production deployment guide: `docs/operations/remote-nightly-deploy.md`

## Alignment Notes

- Similarity is computed only on sensible candidate pairs from rule-based mapping fields.
- Embeddings are cached by normalized text hash + provider + model to skip rerun cost.
- Local testing path should prefer Ollama; OpenAI path is ready for scaled runs.
- See `docs/alignment-pipeline.md` for details.
