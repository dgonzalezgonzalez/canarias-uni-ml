# Repository Guidelines

## Project Structure & Module Organization
This repository contains a Python job-scraping pipeline for the Canary Islands. Keep the layout simple and source-oriented:

- `src/canarias_jobs/` for shared models, CLI entrypoint, and utilities.
- `src/canarias_jobs/spiders/` for one scraper per source: `sce.py`, `turijobs.py`, `indeed.py`, `infojobs.py`.
- `data/raw/` for temporary captures if needed during debugging. Do not commit dumps.
- `data/processed/` for generated outputs such as `canarias_jobs.csv`.
- `docs/` for source notes, API findings, and scraping constraints.

Keep normalization in shared code and source-specific extraction logic inside each spider.

## Build, Test, and Development Commands
Use a local virtual environment:

- `python3 -m venv .venv && source .venv/bin/activate` creates the environment.
- `.venv/bin/pip install -r requirements.txt` installs dependencies.
- `.venv/bin/python -m playwright install chromium` installs the browser runtime used by Playwright sources.
- `.venv/bin/python -m src.canarias_jobs.cli --limit-per-source 50` runs the scraper and writes `data/processed/canarias_jobs.csv`.
- `.venv/bin/python -m compileall src` is the current lightweight code sanity check.

If tests are added later, prefer `pytest`.

## Coding Style & Naming Conventions
Use Python with 4-space indentation and follow PEP 8. Name modules and files in `snake_case`, classes in `PascalCase`, and constants in `UPPER_SNAKE_CASE`. Keep scraping selectors and extraction rules close to the site-specific module that owns them.

Avoid hardcoding secrets, cookies, or local machine paths. API credentials must come from environment variables.

## Testing Guidelines
Use sample-based tests where possible because live job sites are unstable and anti-bot protections vary. Name test files `test_<module>.py`. Prefer:

- one parsing test per supported site
- one normalization test for the common job schema
- one regression test for any selector fix

## Commit & Pull Request Guidelines
Use short imperative commit messages such as `Add SCE API scraper` or `Switch Turijobs to sitemap detail flow`.

Pull requests should include:

- a brief summary of the source or parser affected
- sample output or a short schema example
- notes on rate limits, robots rules, or anti-bot constraints
- linked issue or task, if one exists

## Security & Data Handling
Respect each site's terms, robots policy, and rate limits before scraping. Store credentials in `.env`, never in code. Do not commit large raw dumps unless they are necessary test fixtures.

## Source Notes
- `sce` works via a JWT extracted from the public Angular iframe and then a JSON API call.
- `turijobs` works best from `active-offers.xml` plus detail pages, not the paginated listing UI.
- `indeed` is currently blocked from this environment by Cloudflare even in Playwright. Treat it as best-effort unless network conditions change.
- `infojobs` is implemented against the official API and requires `INFOJOBS_CLIENT_ID` and `INFOJOBS_CLIENT_SECRET`.
