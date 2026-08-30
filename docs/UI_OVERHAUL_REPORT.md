# UI Overhaul 0→100 — Release Report

**Date:** 2026-08-30 · **Released commit:** `e30eb69` (remote `main`)
**Reference used:** Edu Future dashboard (light SaaS) + Perplexity landing (cinematic dark).

---

## What I built (a real design system, not a reskin)

### 1. Design tokens (`frontend/src/index.css`)
- CSS variables for the whole palette, mapped into Tailwind via `@theme` → usable as `bg-surface`, `text-ink`, `text-ink-soft`, `border-line`, `text-brand`, `bg-brand-soft`, etc.
- **Light theme** (EdTech lavender): soft `#f2f1fb` bg, white cards, violet primary `#6e5bf1`, teal accent.
- **Dark theme** (Perplexity night): `#0c0b16` bg, deep surfaces, lighter ink.
- **Class-based dark mode**: toggling `.dark` on `<html>` flips everything automatically; persisted to `localStorage`.
- Shared `.card`, `.btn-primary`, `.btn-ghost`, `.input`, `.label`, `.tag` component classes.

### 2. Cinematic Landing (`/`) — Perplexity style
- Dark hero with layered radial gradients + animated SVG "field" swirl + subtle grain — **no heavy assets** (fast).
- Product name + tagline ("Where applications begin."), feature cards, **Launch Dashboard** CTA.

### 3. Layout (sidebar + topbar)
- Gradient brand mark, sidebar nav with active "pill" highlight, bottom user block.
- Topbar: **search that routes to the Feed** (e.g. `#/feed?q=python`), **working light/dark toggle**, notifications bell, user avatar.

### 4. Pages retokened to the system (all functional)
- **Dashboard** — gradient "Welcome Back" hero (working **Trigger Pipeline** button with live spinner), **clickable KPI cards** (navigate to Feed/Kanban/Responses/Analytics), activity chart, system-status card.
- **Kanban** — search/filter bar, per-status color coding, editable **notes** (new `PATCH /applications/{id}/notes`), richer detail modal.
- **Analytics** — KPI grid, activity line chart, portal donut.
- **Feed** — reads the URL search param, cleaner cards, pagination.
- **Resumes** — upload + tag cards.
- **Responses** — styled response cards + "Scan Inbox Now".
- **Settings** — one-click pipeline trigger with real dry-run/real status badge + confirm prompt, cookie status, env summary.
- **Monitoring** — NEW page: live health cards (DB/AI/Scheduler/Pipeline), uptime, cookie badges, **Prometheus metrics viewer**, Grafana link. Backed by new `/api/system/health`.

### 5. Monitoring infra (not just UI)
- `prometheus` + `grafana` added to `docker-compose.yml` (with a provisioned JobPilot Grafana dashboard + datasource).
- `/metrics` exposed via nginx + enriched gauges.

### 6. Apply-gate bug fix (caught in review)
- `MATCH_SCORE_THRESHOLD` default is now **0** (soft floor off) + new `APPLY_TARGET_COUNT` (top-N). This un-blocks the silent "threshold 20 blocks every apply" problem you'd have hit.

---

## Quality gate
| Check | Result |
|-------|--------|
| Backend `ruff` | ✅ clean |
| Backend `pytest` | ✅ 31 passed |
| Frontend `npm ci && npm run build` | ✅ builds (entry ~34 kB gzip) |
| Vite dev server boot | ✅ serves the app |
| `docker-compose.yml` | ✅ valid YAML; `prometheus`/`grafana` present |

---

## What to do on your machine
```bash
cd C:\Users\kuldeep yadav\jobpilot
git pull
docker compose build      # rebuild the nginx/frontend image with the new UI
docker compose up -d
docker compose up -d      # if prometheus/grafana are new, this starts them too
```
Hard-refresh browser (Ctrl+Shift+R) at **http://localhost** → you'll land on the new **Landing** page. Click **Launch Dashboard**.

Then:
- Toggle **Light/Dark** in the topbar.
- **Monitoring** tab → live health + Grafana at `http://localhost:3001` (admin/admin).
- **Settings → Run Full Pipeline** → with `APPLY_MODE=real` set it prompts before real submissions.
- Set `MATCH_SCORE_THRESHOLD=0` in `.env` (already the new default) so top-N apply selection works.

## Note (honest)
Docker isn't in my sandbox, so I verified the UI via build + vite boot + backend tests, **not** the running Docker stack. After you rebuild, confirm the Landing page renders, dashboard loads real data, and the Monitoring tab shows green cards. If anything looks off, tell me exactly what you see on which page and I'll fix it.

**CURRENT STAGE: Phase 5 — UI overhaul complete & on `main` | NEXT STAGE: scraper live-validation + score calibration ("increase the percentage") when you're ready.**
