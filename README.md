# canarias-uni-ml

Python pipeline for Canary Islands job postings plus Spanish university degree catalogs and embedding-ready text artifacts.

## Status

| Surface | Status | Notes |
|--------|--------|-------|
| SCE | ✅ Working | API JWT, número de ofertas variable |
| Turijobs | ✅ Working | Sitemap + detail pages |
| Indeed (JobSpy) | ✅ Working | Fuente principal para escalado |
| Geography / contract normalization | ✅ Working | Canonical + raw fields coexist |
| Degree catalog | 🧪 Scaffolded | Fixture-driven ANECA/RUCT parser path |
| Embeddings | 🧪 Scaffolded | OpenAI dry-run + manifest generation |

## Environment Variables

```bash
export JOBSPY_PROXIES='["user:pass@host:port"]'   # optional
export OPENAI_API_KEY='sk-...'                      # required for live embeddings
export GROQ_API_KEY='...'                           # optional fallback experiments
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

# Scale jobs
python -m src.canarias_uni_ml.cli jobs scale --time-limit 45 --max-total 40000

# Build degree catalog from fixture
python -m src.canarias_uni_ml.cli degrees catalog --fixture tests/fixtures/degrees_catalog_fixture.json

# Live ANECA grado catalog with extracted report text
python -m src.canarias_uni_ml.cli degrees catalog --live-aneca --limit 20 --with-report-text

# Embedding dry run
python -m src.canarias_uni_ml.cli embed build --input tests/fixtures/semantic_corpus.jsonl --dry-run
```

Legacy job-only commands still route through compatibility wrapper in `src.canarias_jobs.cli`.

## Outputs

- `data/processed/canarias_jobs.csv`
- `data/processed/degrees_catalog.csv`
- `data/processed/embeddings_manifest.json`

## Project Layout

```text
src/canarias_uni_ml/
├── cli.py                # Multi-domain CLI
├── config.py             # Settings and output paths
├── io.py                 # CSV/JSONL writers
├── jobs/                 # Job scraping pipeline
├── degrees/              # Degree catalog scaffolding
├── embeddings/           # Provider abstraction + manifests
└── normalization/        # Canonical geography / contract type
```

## Job Data Contract

Canonical and raw values both persist:

- `province`, `municipality`, `island`, `contract_type`: canonical values
- `province_raw`, `municipality_raw`, `island_raw`, `contract_type_raw`: original scraped values
- `raw_location`: original free-text location

## Notes

- Degree catalog supports live ANECA grado ingestion; RUCT remains fixture-backed until its public contract is hardened.
- Embedding pipeline currently supports dry-run manifests and live OpenAI requests; Groq remains placeholder until embedding compatibility is verified.
- Tests are sample-based by default because live sites and PDF sources are unstable.
