# Canarias Jobs Scraper

Python scraper for a representative sample of job postings in the Canary Islands from four sources:

- Servicio Canario de Empleo (`sce`)
- Indeed España (`indeed`)
- Turijobs (`turijobs`)
- InfoJobs (`infojobs`)

The pipeline normalizes results into one CSV with a shared schema focused on job description plus useful metadata such as salary, publication date, province, municipality, contract type, and source URL.

## Status

- `sce`: working via JWT extracted from the public Angular iframe and JSON API.
- `turijobs`: implemented against public SSR data (`__NEXT_DATA__`), but may require HTTP/2-capable dependencies.
- `indeed`: working via embedded JSON extraction + ScrapingBee fallback for Cloudflare bypass.
- `infojobs`: requires InfoJobs Developer API credentials OR ScrapingBee (JS rendering dependent).

## Environment Variables

```bash
# Required for Indeed and InfoJobs
export SCRAPINGBEE_API_KEY=...

# Only for InfoJobs API (alternative to ScrapingBee)
export INFOJOBS_CLIENT_ID=...
export INFOJOBS_CLIENT_SECRET=...
```

## Quickstart

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
python -m src.canarias_jobs.cli --limit-per-source 50
```

Output CSV:

```text
data/processed/canarias_jobs.csv
```

Without the required environment variables, the runner skips that source and records the failure in the console summary.

## Project Layout

- `src/canarias_jobs/` shared models, normalization, CLI, and source adapters
- `src/canarias_jobs/spiders/` per-source scrapers
- `data/processed/` generated CSV output
- `docs/` implementation notes and source constraints
