# Remote Nightly Deploy

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
- logs include scrape summary with `inserted/updated/unchanged`
- files created:
  - `data/processed/canarias_jobs.db`
  - `data/processed/canarias_jobs.csv`

## 3) Continuous nightly mode

```bash
.venv/bin/python -m src.canarias_uni_ml.cli jobs daemon \
  --window-start 22:00 \
  --window-end 07:30 \
  --timezone Europe/Madrid \
  --cooldown-minutes 10
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

## 6) Git flow

- branch naming: `feat/canarias-*`
- include code + tests + docs in same change set
