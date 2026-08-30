# 01 — Project State

## What it is
Self-hosted, local-first job-hunting automation: scrape Internshala + Naukri → score vs resumes → AI cover letter → apply → track responses → dashboard.

## Technical state (reviewed 2026-08-30)
- **Reviewed commit:** `f2444f8` (a single squashed merge commit; no granular history preserved).
- **Backend:** Python (image `mcr.microsoft.com/playwright/python:v1.40.0-jammy`), FastAPI 0.104.1, SQLAlchemy 2.0.23, Alembic, APScheduler, Playwright 1.40, scikit-learn 1.3.2, pdfplumber, python-docx, loguru, httpx.
- **Frontend:** React 18, Vite 5, Tailwind v4, React Query 5, Recharts, @hello-pangea/dnd.
- **DB:** PostgreSQL 15.5.
- **Scheduler:** APScheduler background, interval from `SCHEDULER_INTERVAL_HOURS`, single worker thread, coalesce.

## Applied migrations (per repo; confirm against live DB before assuming)
- `f1d8e212e1f4` — initial schema (all 8 tables)
- `03d3d0cc6aed` — add `apply_log`

## Verified features (by static code review)
- All 8 models mapped; Alembic migrations present.
- Scrapers for Internshala + Naukri (card parse + JD enrichment).
- Resume parsing (PDF/DOCX) + hybrid match (70% keyword coverage + 30% TF-IDF).
- Smart-route apply (email / portal / manual), per-portal daily cap, dev SAFE MODE.
- Ollama cover-letter generator + deterministic fallback.
- IMAP response scan + keyword classifier + status update.
- API: jobs, applications, resumes, analytics, pipeline, responses, settings (cookie-health).
- UI: Dashboard, Feed, Kanban, Resumes, Responses, Analytics, Settings.

## Progress (Wave 1 — correctness + deployment, applied to working tree, NOT yet committed/pushed)
See `docs/WAVE1_FIXES_REPORT.md` for the full step/result/evidence report.
- **C2/C3** — response tracking rewritten: strict company-domain matching, Message-ID dedupe, marks messages `\Seen`. New migration `a2b3c4d5e6f7` (+ `message_id` column).
- **C4** — apply pipeline now picks the best resume per job via `select_best_resume`.
- **C5** — `pending`/`needs_manual_action`/`failed` now surfaced in Kanban + API.
- **C6** — Ollama in-network URL (`http://ollama:11434`) in `.env.example` + compose default.
- **C1/M5** — single-command deployment fixed: frontend built into an nginx image (`docker/frontend.Dockerfile`), nginx serves SPA + proxies `/api`; backend image runs `alembic upgrade head` + uvicorn (no `--reload`, no source mount).
- **M1–M4, M9, M10** — duplicate `DashboardStats` removed (+ daily fields wired), pipeline now background + `/pipeline/status`, hardcoded personal name removed, Settings reflects real errors.

## Quality gate (functional)
- `ruff check .` → passes (18 unused-import fixes applied).
- `pytest tests/` → **22 passed** (classifier, email matching, matcher, cover-letter fallback, migration-content).
- `npm ci && npm run build` → builds clean; vendor chunks split (entry 90 kB / 29 kB gzip).

## Still open / not verified
- **Docker build + `docker compose up` not run** (Docker unavailable in the review sandbox) — must be verified on your machine.
- **No Prometheus/Grafana containers** (still absent; `/metrics` endpoint present).
- **No auth** (deferred: local-only personal tool — revisit if ever exposed beyond localhost).
- **Scrapers never live-validated** against current portal DOM.
- Full pointer review of the fix batch in `docs/WAVE1_FIXES_REPORT.md`.
