# JobPilot — Continuity Pack (READ ME FIRST)

> The LIVE repo + this pack are the source of truth. If an old plan doc disagrees with the deployed reality, reality wins.

## Repo
- **Source:** `https://github.com/kuldeepyadav001/jobpilot` (reviewed at commit `f2444f8`, 2026-08-30)

## How to resume work
1. Run the full-quality gate **before** touching code (see 05 for commands). Reinstall pinned toolchain first; verify `node --version`/`python --version` match the pin.
2. Read `01_PROJECT_STATE.md` (current technical reality) then `03_OUTSTANDING_TASKS.md` (the work queue).
3. Never re-litigate settled decisions — check `02_DECISIONS_LOG.md` and `04_PLAN_DEVIATIONS.md` first.
4. **Nothing ships without explicit human approval.** Do the fix locally → run gate → report → WAIT.

## Non-negotiable working rules
1. **No auth tokens/keys/secrets in repo, logs, or chat.** Env-var NAMES only. Verify `git history` is clean.
2. **Migrations are append-only**, versioned, timestamped, transaction-wrapped. Never edit a released migration; fix forward.
3. **No invented stats/testimonials/results.** Placeholders must say they're placeholders.
4. **Tests are non-negotiable** (unit + component + migration-content), wired to CI + pre-commit.
5. **Silent fallbacks must be logged** — a fallback that hides a real failure (e.g. AI/Ollama down) is a bug.
6. **Production verification is independent** (HTTP + content-presence on the live URL), not just "Vercel/docker says OK".

## Current status (one line)
Working v2 prototype. Full stack present; **not yet production-grade**. Critical items C2–C6 (see `docs/CURRENT_STATE_REPORT.md`) must be fixed before it can reliably run the full automation loop unattended.
