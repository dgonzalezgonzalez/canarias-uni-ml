# Remote Nightly Deploy

## Remote run order (safe)

Run in this exact order on the remote host:

0. Pull latest code first (required for secondary merge dedupe rule)
```bash
git pull
```

1. Backup current DB
```bash
cp data/processed/canarias_jobs.db data/processed/canarias_jobs.$(date +%F).bak.db
```

2. Stop daemon/service
```bash
sudo systemctl stop canarias-jobs-daemon.service
```

3. Compact DB (drop logical duplicates, keep latest row per job)
```bash
.venv/bin/python -m src.canarias_uni_ml.cli jobs compact --db-path data/processed/canarias_jobs.db
```

4. Preflight one cycle
```bash
.venv/bin/python -m src.canarias_uni_ml.cli jobs daemon --run-once --strategy scale --time-limit-minutes 45
```

5. Start nightly daemon
```bash
sudo systemctl start canarias-jobs-daemon.service
```

6. Monitor health/logs
```bash
sudo systemctl status canarias-jobs-daemon.service
sudo journalctl -u canarias-jobs-daemon.service -f
```

## 1) Bootstrap machine

```bash
git clone <repo-url>
cd canarias-uni-ml
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
```

Set required env vars in service environment (or `.env`):

- `INFOJOBS_CLIENT_ID`
- `INFOJOBS_CLIENT_SECRET`
- optional proxy variables for JobSpy/Indeed

## 2) Preflight check (mandatory)

```bash
.venv/bin/python -m src.canarias_uni_ml.cli jobs daemon --run-once
```

Expected:

- command exits `0`
- logs include cycle summary with `strategy/scraped/inserted/updated/unchanged`
- files created:
  - `data/processed/canarias_jobs.db`
  - `data/processed/canarias_jobs.csv`

## 2b) One-time dedupe for existing DB

If DB has legacy duplicates, stop daemon and compact:

```bash
.venv/bin/python -m src.canarias_uni_ml.cli jobs compact --db-path data/processed/canarias_jobs.db
```

Take backup before first compaction:

```bash
cp data/processed/canarias_jobs.db data/processed/canarias_jobs.$(date +%F).bak.db
```

## 3) Continuous nightly mode

```bash
.venv/bin/python -m src.canarias_uni_ml.cli jobs daemon \
  --window-start 22:00 \
  --window-end 07:30 \
  --timezone Europe/Madrid \
  --strategy scale \
  --time-limit-minutes 45 \
  --cooldown-minutes 5 \
  --stagnation-cycles 6 \
  --fail-on-stagnation
```

## 4) Service mode (`systemd`)

Install template from `deploy/systemd/canarias-jobs-daemon.service` and adjust:

- `User`
- `WorkingDirectory`
- `EnvironmentFile`

Enable service:

```bash
sudo cp deploy/systemd/canarias-jobs-daemon.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now canarias-jobs-daemon.service
```

## 5) Monitoring and stop

```bash
sudo systemctl status canarias-jobs-daemon.service
sudo journalctl -u canarias-jobs-daemon.service -f
sudo systemctl stop canarias-jobs-daemon.service
```

Watch for stagnation signals:
- repeated `[warn] non-productive cycle`
- `[warn] stagnation threshold reached`
- `[error] exiting non-zero to allow supervisor restart`

## 6) Git flow

- branch naming: `feat/canarias-*`
- include code + tests + docs in same change set
