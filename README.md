# Canarias Jobs Scraper

Python scraper for job postings in the Canary Islands from multiple sources:

- Servicio Canario de Empleo (`sce`) - **API directa, ~184 jobs**
- Turijobs (`turijobs`) - **Scraping de detalle, ~300+ jobs**
- Indeed (`jobspy`) - **Scraping via JobSpy library, ~1000+ jobs en 15 min**
- InfoJobs - **No disponible** (registro de apps cerrado)

## Status

| Source | Status | Notes |
|--------|--------|-------|
| SCE | ✅ Working | API JWT, ~184 jobs disponibles |
| Turijobs | ✅ Working | Sitemap + detail pages |
| Indeed (JobSpy) | ✅ Working | python-jobspy library |
| InfoJobs | ❌ Blocked | Registro de apps cerrado temporalmente |

## Environment Variables

```bash
# JobSpy (Indeed) - solo si quieres proxies
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

# Modo escala (máximo jobs en tiempo)
python -m src.canarias_jobs.cli --scale --time-limit 45

# Solo SCE (rápido, ~184 jobs)
python -m src.canarias_jobs.cli --sce-only

# Fusionar CSVs existentes
python -m src.canarias_jobs.cli --merge
```

## Output

```text
data/processed/canarias_jobs.csv
```

## Project Layout

```
src/canarias_jobs/
├── cli.py           # CLI con --scale, --merge, --sce-only
├── scale.py         # Modo de escalado para scraping masivo
├── models.py        # JobRecord schema
├── utils.py         # Helpers de limpieza y parsing
└── spiders/
    ├── sce.py           # SCE API (JWT)
    ├── turijobs.py      # Turijobs sitemap + detail
    ├── jobspy_spider.py # JobSpy wrapper para Indeed
    ├── indeed.py        # Indeed (Playwright, puede fallar)
    ├── indeed_api.py    # Indeed API
    └── infojobs.py      # InfoJobs (no funciona actualmente)
```

## Rate Limits

- **Indeed**: Se bloquea después de ~1000 requests. Usar `--scale` con time limit.
- **Turijobs**: Sitemap accesible, detalle puede ser lento.
- **SCE**: Sin límites, API directa.

## Data Schema

| Field | Type | Description |
|-------|------|-------------|
| source | str | Origen (jobspy_indeed, sce, turijobs) |
| external_id | str | ID externo del origen |
| title | str | Título del puesto |
| company | str | Nombre de la empresa |
| description | str | Descripción completa |
| salary_text | str | Rango salarial formateado |
| province | str | Provincia (Las Palmas / Santa Cruz de Tenerife) |
| island | str | Isla |
| source_url | str | URL original |
