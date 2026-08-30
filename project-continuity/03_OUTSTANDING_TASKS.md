# 03 — Outstanding Tasks

> The approved work queue. Each item is scoped to one approval cycle. Ref labels match `docs/CURRENT_STATE_REPORT.md`.

## Wave 1 — Make the promised loop actually work (critical correctness)  ✅ DONE (pending approval/push)
- **W1.0 (C6)** Ollama URL → `http://ollama:11434` (in-network), compose default + `.env.example`. ⏳ TODO: verify real LLM path is hit on live run.
- **W1.1 (C2)** Marks messages `\Seen` + Message-ID dedupe (new `message_id` column, migration `a2b3c4d5e6f7`).
- **W1.2 (C3)** Rewrote matching: strict company-domain/display-name scoring; removed unsafe "latest application" fallback.
- **W1.3 (C4)** Apply pipeline uses `select_best_resume` per job.
- **W1.4 (C5)** `pending`/`needs_manual_action`/`failed` exposed in Kanban + API.

## Wave 2 — Real single-command deployment  ✅ MOSTLY DONE
- **W2.1 (C1)** ✅ Frontend baked into nginx image (`docker/frontend.Dockerfile`), served + `/api` proxied. ⏳ Verify `docker compose up` on a machine with Docker.
- **W2.2 (H4)** ⏳ Still open — prometheus + grafana containers not added.
- **W2.3 (M5)** ✅ Removed `--reload` + source mount; image auto-runs `alembic upgrade head`.

## Wave 3 — Security
- **W3.1 (H1)** Add auth (API token / login) at minimum on `/pipeline`, `/applications`, `/resumes`, `/settings`. Use `SECRET_KEY` (currently dead).
- **W3.2 (M2/M9)** Candidate name from settings/env; remove hardcoded personal data from backend + frontend.
- **W3.3 (M-upload)** Upload validation: size cap, MIME sniff, filename sanitization, path traversal guard.

## Wave 4 — Reliability of automation
- **W4.1 (H5/H6)** Live-validate + harden scrapers (retries, `networkidle`, explicit cookie-expiry alert). No silent "guest mode" — log + set a visible `cookie_expired` signal.
- **W4.2 (M3/M4)** Pipeline as background task; return immediately; frontend polls run status; errors must be HTTP errors, not 200-with-error.
- **W4.3 (M7)** Document match scoring as heuristic; optionally calibrate.
- **W4.4 (M12)** Prevent double-apply to the same company.

## Wave 5 — Quality gate (mandatory)
- **W5.1 (H2/H3)** Convert `test_*.py` to real pytest suite (unit + integration w/ test DB) + GitHub Actions CI + pre-commit hooks. ✅ DONE — pytest suite (22 tests) + `requirements-dev.txt` + `backend/pyproject.toml` (ruff) + `.github/workflows/ci.yml` + `.pre-commit-config.yaml`.
- **W5.2** Frontend lint + build + component test. ✅ Build wired into CI. ⏳ Add `npm run lint` script + at least one component test (e.g. Kanban render).

## Wave 6 — Dashboard completeness
- **W6.1 (H7/M13)** Settings: search keywords, match threshold, scheduler interval, daily cap, candidate name, blacklist mgmt.
- **W6.2** Feed: manual-apply override + blacklist-company buttons.
- **W6.3 (M8)** Analytics: per-portal response rate, best resume, time-to-response, rejection rate.

## Wave 7 — Docs & operations
- **W7.1** Real `.env.example`, deployment guide, operational runbook (cookie refresh procedure), content-collection guide, API docs.
- **W7.2 (M11)** Remove leftover Vite assets.

### Entry criteria for each wave
Local implementation → full quality gate → report (table: step / result / evidence) → **await approval** → migration-first (if any) → deploy → independent production verification.
