# 02 — Decisions Log

| Date | Decision | Why | State left in |
|------|----------|-----|---------------|
| 2026-08-30 | Assess existing repo before any changes; clone + full code read, no modification | Working rules: understand before acting; research before feature debates | Baseline documented in `docs/CURRENT_STATE_REPORT.md`; continuity pack created |
| 2026-08-30 | Treat the original design doc as the product spec; the repo is a v2 prototype of it | The doc is the client requirement; repo is the partial implementation | Deviations tracked in `04_PLAN_DEVIATIONS.md` |
| 2026-08-30 | No code changed yet — assessment only; awaiting the user's original plan + approval before fixes | Release/approval protocol: nothing ships without explicit approval | Awaiting user |
| 2026-08-30 | **User confirmed the plan** = the pasted design doc; it's a **personal, local-only, single-user** job-hunting tool (not a deployed SaaS). Fixed `kuldeepyadav001/jobpilot` as source of truth. | Reduces auth priority; keeps everything else. | Local-only scope adopted |
| 2026-08-30 | **Deploy key provided.** SSH keypair generated in sandbox (`~/.ssh/id_ed25519`, private key OUTSIDE repo tree); public key pasted as repo **deploy key with write access**; remote switched to `git@github.com:...`; access verified. | Narrowest blast radius, revocable, single repo only. | Push access ready |
| 2026-08-30 | **Order of work:** fix bugs/breaking points first, features later (per user). Implemented Wave 1 correctness + deployment fixes; **not yet committed** — awaiting approval for the push. | Release protocol: report, then STOP and wait. | Working tree modified, uncommitted |
