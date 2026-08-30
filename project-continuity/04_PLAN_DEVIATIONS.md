# 04 — Plan vs. Actually-Built Deviations

Original product plan (the design doc) vs. current repo (commit `f2444f8`).

| Planned | Built | Gap |
|---------|-------|-----|
| Kanban status board | ✅ drag & drop | none |
| Resume–JD matching score | ✅ hybrid (70% keyword + 30% TF-IDF) | heuristic; document honestly |
| Auto pick best resume | ⚠️ only in `score_unmatched_jobs`; pipeline uses `.first()` | apply path missing |
| Auto form fill per portal | ⚠️ Internshala only; Naukri → manual | Naukri portal apply not built |
| Application analytics (response rate, best portal, best resume, time-to-response) | ⚠️ counts only | mostly missing |
| One profile → all portals | ⚠️ scrapes both, applies only via Internshala | partial |
| Email response → auto status | ⚠️ exists, unsafe matching + duplicate ingest | brittle |
| Browser session reuse | ✅ cookies + health check | silent-fail risk |
| Resume version management | ⚠️ `version` col only | no UI/logic |
| Blacklist | ⚠️ DB flag only | no control surface |
| Cover letter via local Ollama | ✅ + fallback | Ollama URL bug (C6) |
| Single-command deployment | ⚠️ backend+db+ollama+nginx only | frontend not served; monitoring missing |
| Prometheus + Grafana | ❌ not in compose | missing |
| Local-only / no exposure | ⚠️ yes by default, but **no auth** | security gap |
| Settings page (criteria, threshold, email, interval) | ⚠️ cookie-health + trigger only | missing |
