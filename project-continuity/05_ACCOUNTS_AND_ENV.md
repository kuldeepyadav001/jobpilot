# 05 — Accounts & Environment

> **Never put secret VALUES here.** Names only. Any credential passed through chat is treated as exposed — scoped, revocable, deleted at project end.

## Providers in use
- **GitHub** (`kuldeepyadav001/jobpilot`)
- **Gmail** — used for SMTP (sending applications) + IMAP (response tracking). Use an **App Password**, never the real account password.
- **Local self-hosted:** PostgreSQL (Docker), Ollama (Docker), Playwright/Chromium (Docker).

## Env var names (from `.env.example`)
`DB_USER`, `DB_PASSWORD`, `DB_NAME`, `ENVIRONMENT`, `SECRET_KEY`, `EMAIL_ADDRESS`, `EMAIL_APP_PASSWORD`, `IMAP_SERVER`, `IMAP_PORT`, `SMTP_SERVER`, `SMTP_PORT`, `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `CANDIDATE_NAME`, `APPLY_MODE` (`real`/`dry_run`), `AUTO_APPLY`, `MATCH_SCORE_THRESHOLD`, `SCHEDULER_INTERVAL_HOURS`, `INTERNSHALA_COOKIE`, `NAUKRI_COOKIE`.

## Deploy key (sandbox → repo, for pushing)
- Private key: `~/.ssh/id_ed25519` — kept OUTSIDE the repo tree; never commit it.
- Public key registered on GitHub as a repo **deploy key with write access** on `kuldeepyadav001/jobpilot`.
- Remote: `git@github.com:kuldeepyadav001/jobpilot.git`.
- **PROJECT-END TASK:** revoke this deploy key when the project wraps up.

## Quality-gate commands (formalized)
- Backend: `ruff check .` and `pytest tests/ -q` (both wired into `.github/workflows/ci.yml`). Pre-commit hooks via `.pre-commit-config.yaml`.
- Frontend: `npm ci && npm run build` (wired into CI). `npm run lint` script still to be added.
- Docker: `docker compose config`, `docker compose build`, `docker compose up -d` (must be run on a machine with Docker).
