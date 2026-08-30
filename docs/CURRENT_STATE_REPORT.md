# JobPilot — Current State Assessment Report

**Date:** 2026-08-30
**Reviewed commit:** `f2444f8` (single squashed commit, "merge: resolve remote and local conflicts")
**Goal:** Bring the project to **production-standard so the full automation loop actually runs unattended** (scrape → score → apply → track → update).

---

## 1. What JobPilot Actually Is

A self-hosted, local-first job-hunting automation system.

- **Backend:** Python 3.11, FastAPI, SQLAlchemy 2.0, Alembic, APScheduler, Playwright (Chromium), `imaplib`/`smtplib`, scikit-learn TF-IDF.
- **AI:** Ollama + `qwen2.5:1.5b` (local, free) for cover letters.
- **Frontend:** React 18 + Vite + Tailwind v4 + React Query + Recharts + `@hello-pangea/dnd`.
- **DB:** PostgreSQL 15.5.
- **Orchestration:** Docker Compose (postgres, ollama, backend, nginx). Nginx reverse-proxies `/api` + `/health` to backend **only**.

The full pipeline exists in code and is structurally sound. It is **not yet production-grade** — it is a working prototype/v2. Several core features are present but incomplete, and a handful of correctness bugs break the exact behaviors the plan promises (auto-apply, auto-response-tracking, best-resume selection, monitoring).

---

## 2. What Exists and Works (Verified in Code)

| Layer | Status | Notes |
|-------|--------|-------|
| **Data models** | ✅ Complete | All 8 tables: jobs, applications, resumes, responses, companies, status_history, analytics_snapshot, apply_log |
| **Alembic migrations** | ✅ Present | `f1d8e212e1f4` (initial) + `03d3d0cc6aed` (apply_log) |
| **Scrapers** | ✅ Built (needs live validation) | Internshala + Naukri, card parse + JD enrichment |
| **Resume engine** | ✅ Built | PDF/DOCX extraction + hybrid score (keyword coverage 70% + TF-IDF 30%) |
| **Apply engine** | ✅ Built | Smart routing (email / portal / manual), daily rate cap, SAFE MODE in dev |
| **LLM cover letter** | ✅ Built | Ollama client + deterministic fallback template |
| **Response tracker** | ⚠️ Built but brittle | IMAP scan + keyword classifier + status update |
| **API** | ✅ Complete-ish | 7 routers: jobs, applications, resumes, analytics, pipeline, responses, settings |
| **Dashboard UI** | ✅ All 7 pages present | Dashboard, Feed, Kanban, Resumes, Responses, Analytics, Settings |
| **Scheduler** | ✅ Present | APScheduler interval, single-thread, coalesce |
| **Docker Compose** | ⚠️ Partial | Missing: frontend-build service, prometheus, grafana |
| **Monitoring** | ❌ Incomplete | `/metrics` endpoint exists, but no Prometheus/Grafana containers in compose |

---

## 3. Findings by Severity

### 🔴 CRITICAL — break the primary promised outcomes

| # | Finding | Concrete Impact |
|---|---------|-----------------|
| **C1** | **Nginx does not serve the frontend.** `nginx/nginx.conf` only proxies `/api` and `/health`; there is no `frontend` service in `docker-compose.yml`, no static-build stage. | The plan's "one port, single command" is **false**. You must run `npm run dev` (port 5173) separately. Not production-usable. |
| **C2** | **Email tracker never marks the fetched message as `\Seen`.** | The same unread email is re-processed **every 6-hour cycle** → duplicate `responses` rows, repeated status writes, status flapping. |
| **C3** | **Email → application matching is unsafe.** It tries `Company.name.ilike('%<sender>%')`, where `sender` is the raw `From` header like `"Recruiter Name <rec@x.com>"` — a near-guaranteed miss. It then **falls back to "the latest application in the table."** | Recruiter emails get attached to the **wrong application**. This silently corrupts the response-tracking feature. |
| **C4** | **"Best resume" is not actually used in the pipeline.** `scheduler/jobs.py` picks `db.query(Resume).filter(is_active).first()` — a single resume. `select_best_resume()` is called only in `score_unmatched_jobs`, never for the apply decision. | The plan's headline "auto pick best resume per job" does **not** happen. |
| **C5** | **Statuses `pending`, `failed`, `needs_manual_action` are not in the Kanban board.** Board columns = applied/viewed/responded/interview/offer/rejected; API `VALID_STATUSES` excludes the others. | Any application that routed to "manual" or "failed" is **invisible** in the dashboard — exactly the "needs manual action" jobs the user must see. |
| **C6** | **Ollama `OLLAMA_BASE_URL` default is wrong for the compose network.** `.env.example` sets `http://host.docker.internal:11434`. Backend runs in a container; on Linux that host doesn't resolve without `extra_hosts`. The correct in-network URL is `http://ollama:11434`. | AI cover-letter generation silently always fails → falls back to the generic template. (Silent fallback masking failure.) |

### 🟠 HIGH — production-quality gaps

| # | Finding | Impact |
|---|---------|--------|
| **H1** | **No authentication on the API or dashboard at all.** `/pipeline/run`, resume upload (arbitrary file write), resume read/download, email dispatch — all unauthenticated. | If ever exposed beyond localhost, anyone can trigger real applications, read your resume, upload files, or read cookie status. `SECRET_KEY` is declared but **never used**. |
| **H2** | **Tests are manual scripts, not a test suite.** `test_*.py` are `main()` scripts requiring a live DB; there are **no `pytest` tests, no `test_` discovery, no CI, no pre-commit hook**. | The quality gate the rules mandate (unit + component + wired CI) is absent. |
| **H3** | **Tests never run in CI and the repo has no `.github/workflows`.** | Findings ship unverified. |
| **H4** | **Prometheus + Grafana are in the plan but not in `docker-compose.yml`.** | Monitoring is not actually running. |
| **H5** | **Portals are scraped with brittle DOM selectors accepted silently.** Scraper scripts `except` and return "guest mode" on failure; `check_session_valid` returns `True` on any error. | Scraper failures/expired cookies produce **empty or thin results with no alert** — the "fully automated" loop silently degrades. |
| **H6** | **Scraper selectors are not re-validated against live portals** (heuristic guesswork that was never run against current DOM). | High risk that scrapers return 0 jobs today. Needs a live validation pass. |
| **H7** | **The Settings page in the plan (search criteria, match threshold, blacklist, scheduler interval, email creds) is not implemented.** Only cookie health + trigger exist; everything is hardcoded in `.env`. | Not configurable from the dashboard as promised. |

### 🟡 MEDIUM

| # | Finding | Notes |
|---|---------|-------|
| **M1** | Duplicate `DashboardStats` class (twice in `api/schemas.py`). | Works by luck (last wins) but is a code smell; analytics ignores `daily_applies`/`daily_cap` fields. |
| **M2** | Cover letter default candidate name is hardcoded `"kuldeep yadav"`. | Hardcodes personal data; should come from settings/env. **Does not belong in code.** |
| **M3** | `pipeline/run` returns HTTP 200 with `{"status":"error"}` on failure. Frontend `Settings.jsx` treats any 200 as **SUCCESS** and shows a success log line. | Errors are displayed as successes. |
| **M4** | `pipeline/run` executes the **entire pipeline synchronously inside the request** (can take minutes), frontend timeout 180s. | Races the timeout; should dispatch to a background task. |
| **M5** | Backend Dockerfile runs `uvicorn --reload` and compose bind-mounts `./backend:/app`. | Live source + reload in a "production" build is wrong; uncommitted changes silently run. |
| **M6** | `record_apply` counts `needs_manual_action` toward the daily cap even though nothing was submitted. `MAX_DAILY_APPLIES = 10` is hardcoded, not configurable. | Cap logic slightly off; not env-tunable. |
| **M7** | `match_score` from TF-IDF uses `cosine * 300` (magic scaling). | Scores are heuristic, not calibrated ATS. Fine as a ranking heuristic; doc it honestly. |
| **M8** | Analytics only compute per-portal **job counts**, not the promised per-portal **response rate**, time-to-response, per-resume response rate, rejection rate. | The plan's analytics features are largely missing. |
| **M9** | Frontend hardcodes "Kuldeep Yadav / KY / Admin" avatar/name. | Personal data in code; should be configurable. |
| **M10** | `@app.on_event("startup"/"shutdown")` deprecated in favor of lifespan. | Deprecation; move to lifespan. |
| **M11** | Leftover default Vite assets (`react.svg`, `vite.svg`, `hero.png`). | Cleanup. |
| **M12** | No per-company dedup on apply; could auto-apply twice to the same company across jobs. | Guard against spam. |
| **M13** | No "manual apply override" or "blacklist company" controls in Feed (plan items). | Missing. |

---

## 4. Plan vs. Reality (Deviations)

| Planned Feature | Reality | Verdict |
|-----------------|---------|---------|
| Kanban status board | ✅ Present + drag & drop working | OK |
| Resume–JD matching score | ✅ Present (hybrid) | OK (heuristic) |
| **Auto pick best resume** | ❌ Pipeline uses first active resume | **Missing** |
| Auto form fill (per portal) | ⚠️ Only Internshala implemented; Naukri falls to manual | Partial |
| Application analytics (response rate, best portal, best resume, time-to-response) | ⚠️ Only count-based dashboard | **Missing** |
| One profile → all portals | ⚠️ Scrapes both; applies only via Internshala portal | Partial |
| Email response detection → auto status | ⚠️ Exists but matching is unsafe (C3) + duplicate on rescan (C2) | **Brittle** |
| Browser session reuse | ✅ Cookie injection + health check | OK (silent-fail risk) |
| Resume version management | ⚠️ version field exists; no UI/versioning logic | Partial |
| Blacklist companies | ⚠️ DB flag exists; no control surface | Partial |
| Cover letter via local LLM | ✅ Present (Ollama) + fallback | OK (**URL bug C6**) |
| Single `docker compose up -d` for everything | ❌ Frontend not served; monitoring missing | **Broken** |
| Prometheus + Grafana | ❌ Not in compose | **Missing** |
| Automated response tracking | ⚠️ Not wired to reliably update status | Brittle |

---

## 5. What "Production Standard / Full Automation" Requires

Workstreams, roughly in order:

1. **Make the single-command deployment real.**
   - Add a `frontend` build stage that `npm run build` → static assets served by Nginx; drop the separate dev server for prod.
   - Add `prometheus` + `grafana` services and wire `/metrics` → scrape config.
   - Remove `--reload` and the source bind-mount in the prod image; use image-only.

2. **Fix the correctness bugs that break the promised loop.**
   - (C2) Mark emails `\Seen` after processing + dedupe by message-id.
   - (C3) Rewrite email→application matching: track per-application company domain + email, match by `From` domain against applied-company domains; remove the "latest application" fallback.
   - (C4) Use `select_best_resume` in the apply pipeline; pick per-job resume.
   - (C5) Add `pending / failed / needs_manual_action` to Kanban or normalize them to a visible "Action needed" column; extend `VALID_STATUSES`.
   - (C6) Fix `OLLAMA_BASE_URL`; add `extra_hosts: host-gateway` if keeping host URL; test end-to-end.

3. **Security & hygiene.**
   - Add an auth layer (API token / basic login) — at minimum on `/pipeline`, resume endpoints, and settings.
   - Make candidate name a setting; remove hardcoded personal data from code and frontend.
   - Validate uploads (size limit, filename sanitization, MIME sniff), path traversal guard.

4. **Reliability of the automation.**
   - Live-validate + harden scrapers (retries, networkidle, structured failure alerts for when cookies expire / selector breaks).
   - Move pipeline to a background task; return immediately; frontend polls a run-status.
   - Surface a pipeline health/summary endpoint + log signal when fallbacks activate.

5. **Quality gate (mandatory per working rules).**
   - Convert `test_*.py` → real pytest suite (unit + integration with a test DB).
   - Add GitHub Actions CI (lint, type, unit, build, budgets) + pre-commit hooks.
   - Add frontend lint/build and a lightweight component test.

6. **Dashboard completeness.**
   - Settings: search keywords, match threshold, scheduler interval, daily cap, candidate name, blacklist management.
   - Feed: manual-apply override + blacklist company buttons.
   - Analytics: per-portal response rate, best resume, time-to-response, rejection rate.

7. **Docs & operations.**
   - Real `.env.example`, `.env` docs, runbook, content-collection guide, API docs, and a "how cookies are refreshed" runbook (this is the #1 operational task for a scraping tool).

---

## 6. Honest Verdict

The **architecture is right** — clean separation (scrapers / engine / ai / scheduler / api / models), sensible tech choices matching the plan, and all 8 tables plus a real dashboard render. This is a strong **v2 candidate**.

It is **not yet production-standard.** It will not currently deliver "full automation" reliably because of **C2–C6** (duplicate response ingestion, wrong-app matching, no best-resume in pipeline, hidden manual/failed applications, broken Ollama URL) and the **broken single-command deployment** (C1). The `test_*.py` files aren't tests, and the pipeline's failure modes are silent.

The path to production-grade is well-scoped and mostly additive — no rewrite needed. That is the good news.

---

*Created from a full code read of commit `f2444f8`. Companion continuity pack lives in `project-continuity/`.*
