# Source Notes (Current Pipeline)

## Active Sources

- `indeed` (via `jobspy_indeed`): fuente principal para volumen.
- `sce`: fuente pública oficial del Servicio Canario de Empleo.
- `turijobs`: fuente complementaria para hostelería/turismo.

## Excluded Source

- `infojobs`: fuera del alcance actual del pipeline.

## Scaling Strategy

El modo de escala (`--scale`) usa un máximo configurable de filas (`--max-total`) con cuotas objetivo por fuente:

- `--indeed-share` (default `0.82`)
- `--sce-share` (default `0.13`)
- `--turijobs-share` (default `0.05`)

Si una fuente secundaria no alcanza su cuota (normalmente SCE/Turijobs), el remanente pasa a Indeed.

## Recommended Command

```bash
.venv/bin/python -m src.canarias_jobs.cli --scale --time-limit 45 --max-total 40000
```

## Data Cleanup in Scale Mode

Al final del scraping escalado, el pipeline aplica:

- normalización de texto/campos clave
- inferencia de provincia desde isla cuando falta
- deduplicación por `source_url` con fallback por `source + external_id`
- recorte al máximo total solicitado
