# Jobs Daemon Operations

## Purpose

Run the jobs scraper as a long-lived process that only executes inside a nightly window.

## Command

```bash
.venv/bin/python -m src.canarias_uni_ml.cli jobs daemon \
  --window-start 22:00 \
  --window-end 07:30 \
  --timezone Europe/Madrid \
  --cooldown-minutes 10
```

## Runtime Signals

- `SIGTERM` / `SIGINT`: daemon stops gracefully after current step.

## Locking

- Lock file prevents concurrent daemon instances.
- Default lock path: `data/processed/canarias_jobs.lock`

## Outputs

- Canonical DB: `data/processed/canarias_jobs.db`
- Snapshot CSV: `data/processed/canarias_jobs.csv`

## Preflight

```bash
.venv/bin/python -m src.canarias_uni_ml.cli jobs daemon --run-once
```

Use run-once preflight before enabling unattended service mode.
