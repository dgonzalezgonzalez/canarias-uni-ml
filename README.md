# Canarias Jobs Scraper

Python scraper for job postings in the Canary Islands from multiple sources:

- Servicio Canario de Empleo (`sce`) - API directa pública (JWT + JSON)
- Turijobs (`turijobs`) - sitemap + detalle de oferta
- Indeed (`jobspy_indeed`) - scraping masivo vía `python-jobspy`

## Status

| Source | Status | Notes |
|--------|--------|-------|
| SCE | ✅ Working | API JWT, número de ofertas variable |
| Turijobs | ✅ Working | Sitemap + detail pages |
| Indeed (JobSpy) | ✅ Working | Fuente principal para escalado |
| InfoJobs | ⛔ Out of scope | Excluido del pipeline actual |

## Environment Variables

```bash
# JobSpy (Indeed), opcional si quieres proxies
export JOBSPY_PROXIES='["user:pass@host:port"]'
```

## Quickstart

```bash
# Crear entorno
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium

# Modo normal (50 jobs por fuente)
python -m src.canarias_jobs.cli --limit-per-source 50

# Modo escala (objetivo hasta 40.000, con mayoría de Indeed)
python -m src.canarias_jobs.cli --scale --time-limit 45 --max-total 40000

# Solo SCE (rápido, ~184 jobs)
python -m src.canarias_jobs.cli --sce-only

# Fusionar CSVs existentes
python -m src.canarias_jobs.cli --merge
```

Parámetros de distribución en `--scale`:

- `--indeed-share` (default `0.82`)
- `--sce-share` (default `0.13`)
- `--turijobs-share` (default `0.05`)

Si SCE/Turijobs no alcanzan cuota, el remanente se rellena con Indeed hasta `--max-total`.

## Output

```text
data/processed/canarias_jobs.csv
```

## Project Layout

```
src/canarias_jobs/
├── cli.py           # CLI principal
├── scale.py         # Escalado con cuotas por fuente + limpieza/deduplicación
├── models.py        # JobRecord schema
├── utils.py         # Helpers de limpieza y parsing
└── spiders/
    ├── sce.py           # SCE API (JWT)
    ├── turijobs.py      # Turijobs sitemap + detail
    ├── jobspy_spider.py # JobSpy wrapper para Indeed
    ├── indeed.py        # Indeed via Playwright (experimental)
    └── indeed_api.py    # Indeed parser alternativo
```

## Rate Limits

- **Indeed**: fuente principal. El volumen final depende de bloqueos y latencia.
- **Turijobs**: sitemap accesible, detalle más lento.
- **SCE**: API directa y rápida.

## Data Schema

| Field | Type | Description |
|-------|------|-------------|
| source | str | Origen (p.ej. `jobspy_indeed`, `sce`, `turijobs`) |
| external_id | str | ID externo del origen |
| title | str | Título del puesto |
| company | str | Nombre de la empresa |
| description | str | Descripción completa |
| salary_text | str | Rango salarial formateado |
| province | str | Provincia (Las Palmas / Santa Cruz de Tenerife) |
| island | str | Isla |
| source_url | str | URL original |
