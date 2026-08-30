# Wave 1 — Bug & Breaking-Point Fixes (Release Report)

**Date:** 2026-08-30 · **Status:** AWAITING YOUR APPROVAL · **Nothing pushed yet.**
Scope: fix the correctness bugs + deployment breaking points first (your instruction), not new features.

---

## Quality gate (all green, run in the review sandbox)

| Check | Result | Evidence |
|-------|--------|----------|
| Backend lint (`ruff check .`) | ✅ Pass | 18 unused-import fixes auto-applied, `All checks passed!` |
| Backend tests (`pytest tests/`) | ✅ **22 passed** | classifier, email matching, matcher, cover-letter fallback, migration-content |
| Migrations apply | ✅ `upgrade head` → head `a2b3c4d5e6f7` | fresh SQLite, all 8 tables + `message_id` present |
| App import smoke | ✅ `JobPilot API v1.1.0`, 13 API routes | `/pipeline/run`, `/pipeline/status`, `/responses`, `/applications` all registered |
| Frontend `npm ci && npm run build` | ✅ Builds clean | entry 90 kB / 29 kB gzip (was 816 kB / 238 kB); vendor chunks split |
| Docker compose | ⚠️ YAML valid | **Stack not run** — no Docker in sandbox. Must verify on your machine. |

---

## Fixes applied

### 🔴 Critical correctness (these broke the promised loop)

| ID | What was wrong | Fix | Files |
|----|---------------|-----|-------|
| **C2** | Emails never marked `\Seen` → re-processed every 6h, duplicate responses + status flapping | Mark `\Seen` after processing + **Message-ID dedupe** (new column) | `engine/email_tracker.py`, `models/response.py`, migration `a2b3c4d5e6f7` |
| **C3** | Email→app matching unsafe (matched on raw sender string, then **fell back to "latest application"**) → replies attached to the **wrong job** | Rewrote: parse sender, match by **company domain + display name**; **removed the unsafe fallback** (unmatched emails are logged for review, never mis-attached) | `engine/email_tracker.py` |
| **C4** | Pipeline grabbed the **first** active resume — "auto pick best resume" never happened | Each job now selects its **best resume** via `select_best_resume` | `scheduler/jobs.py` |
| **C5** | `pending`/`needs_manual_action`/`failed` weren't on the Kanban → manual-action jobs were **invisible** | Surfaced on the board + added to `VALID_STATUSES` | `pages/Kanban.jsx`, `api/routes/applications.py` |
| **C6** | `OLLAMA_BASE_URL=host.docker.internal` wrong in-container → AI cover letters silently fell back to generic template | Default to in-network `http://ollama:11434` | `.env.example`, `docker-compose.yml`, `Settings.jsx` |
| **C1/M5** | Nginx didn't serve the frontend & backend ran `--reload` on a source mount → the promised "single `docker compose up`" was untrue | Frontend baked into an nginx image (`docker/frontend.Dockerfile`) serving the SPA + proxy `/api`; backend image runs `alembic upgrade head` + uvicorn (no reload/mount) | `docker/frontend.Dockerfile`, `nginx/nginx.conf`, `docker/backend.Dockerfile`, `docker-compose.yml` |

### 🟡 Hygiene / correctness (small, safe)

| ID | Fix |
|----|-----|
| **M1** | Removed duplicate `DashboardStats`; wired `daily_applies`/`daily_cap` |
| **M3/M4** | Pipeline now runs as a **background task**; POST returns immediately; GET `/pipeline/status`; errors are HTTP errors (was 200-with-error shown as success); Settings polls real status |
| **M2/M9** | Hardcoded candidate name (`kuldeep yadav`) removed → now `CANDIDATE_NAME` setting (env), auto-detect from resume; dashboard header neutralized |
| **M10** | Pydantic `class Config` → `model_config` (removes deprecation warning) |
| quality | Made `PlaywrightApplyEngine` import lazy (app runs/tests without a browser installed) |

---

## New files added
- `backend/migrations/versions/a2b3c4d5e6f7_add_message_id_to_responses.py` (append-only, forward migration)
- `backend/tests/` — `conftest.py`, `test_classifier.py`, `test_email_matching.py`, `test_matcher.py`, `test_cover_letter.py`, `test_migrations.py`
- `backend/requirements-dev.txt`, `backend/pyproject.toml` (ruff)
- `.github/workflows/ci.yml` (backend lint+tests, frontend build), `.pre-commit-config.yaml`
- `docker/frontend.Dockerfile`
- `docs/WAVE1_FIXES_REPORT.md`, continuity pack (`project-continuity/00–05`)

## Migration (you apply, I push code after)
One forward migration that adds a column — apply it and confirm before I push:
```bash
docker exec -it jobpilot_backend sh -c "alembic upgrade head"
# or, since the backend image now auto-runs `alembic upgrade head` on start, just restart the backend:
docker compose restart backend
```
Expected output: `Running upgrade 03d3d0cc6aed -> a2b3c4d5e6f7`.

---

## What I need from you
1. **Approve this batch** (Wave 1) so I can commit + push.
2. **Run `docker compose build && docker compose up -d`** on your machine — I can't verify the container stack here. Confirm `/` serves the dashboard and `/health` returns ok.
3. **The apply-gate decision** (still open, affects whether "production" sends real applications): **Option A** default still requires you to flip an explicit setting to actually submit (safest), **Option B** fully autonomous once `ENVIRONMENT=production`.

## Note on the apply engine
I did **not** change the existing SAFE MODE / real-send behavior in this wave. The dry-run vs. autonomous question is deliberately left for your call — it's the one place I need your preference before writing that code.

---

**CURRENT STAGE: Phase 5 (Staged Building) — Wave 1 complete & gated | NEXT STAGE: your approval → push → live verification.**
