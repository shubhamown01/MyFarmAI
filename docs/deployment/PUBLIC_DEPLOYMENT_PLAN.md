# MyFarmAI — Public Deployment Plan (₹0, external-tester ready)

Status: **ACTIVE** (created 2026-11-08). Companion documents:
`PUBLIC_LIVE_TESTING_AUDIT.md` (blockers B-1..B-6), `GO_LIVE_RUNBOOK.md`
(owner decisions + prod env vars), `ROLLBACK_PLAN.md`, `DEPLOYMENT_RUNBOOK.md`.

## Owner decision status (updates GO_LIVE_RUNBOOK D1–D4)

| Decision | Status |
|---|---|
| D1 public exposure | **RESOLVED by owner** — public-testing master prompt issued 2026-11-08 |
| D2 custom domain | Deferred — provider-managed HTTPS subdomains accepted |
| D3 dashboard hosting | **This document** (Slate vs Cloudflare below) |
| D4 non-commercial confirmation | Still owner's declaration (controls Open-Meteo free tier) |

## Target architecture (modular, replaceable providers retained)

```
[Phone/anywhere] --HTTPS--> Web frontend (Next.js 15, SSR) --same-origin /api/v1--> 
Funding legs:
  Frontend: Catalyst Slate  OR  Cloudflare Pages   (decided below)
  API:      Zoho Catalyst AppSail myfarmai-backend (existing, verified 200)
  DB:       Neon Postgres branch br-young-fire-a1ll0fm0 (existing, verified)
  AI:       backend gateway (Ollama NEVER publicly exposed; disabled on staging)
  Weather:  Open-Meteo free tier (non-commercial restriction — B-5)
```

## Provider decision — frontend

| Criterion | Catalyst Slate (existing Zoho acct) | Cloudflare Pages (acct created 2026-11-03, no local creds) |
|---|---|---|
| ₹0 / no card | ✅ (already consuming ₹0 for AppSail) | ✅ free tier (no card documented) |
| CLI authenticated | ✅ `zcatalyst-cli whoami` = owner's account | ❌ no API token locally — **owner action needed** |
| Next.js support | ✅ `slate:link --framework` + preview deploys | ✅ via @cloudflare/next-on-pages adapter |
| Risk | Slate stack is newer; verify SSR + proxy rewrites during deploy | adapter adds build complexity |
| Decision | **PRIMARY — try first** | fallback |

**Selected: Catalyst Slate** — CLI already authenticated to the owner's
account, zero new accounts, zero cost; fallback to Cloudflare Pages only if
Slate cannot serve the Next.js standalone build or the same-origin proxy.
Both choices keep the backend untouched (replaceable per modular rule).

## Phases (executed in order, each verified before the next)

| Phase | Work | Verification |
|---|---|---|
| P0b | Finish release APK (bg build, embedded staging bundle) | `aapt2 dump badging` + unzip bundle check |
| P1 | This plan + runbook + rollback | committed docs |
| P2 | `slate:link web/ --framework nextjs` → build + deploy → public HTTPS URL | `curl` from external network proxy; `/api/v1/health` via proxy |
| P2.5 | CORS: add Slate origin to `CORS_ALLOWED_ORIGINS` on AppSail env (cookie flows are same-origin via Next proxy; direct browser→API calls still need CORS) | actual 200 responses |
| P3 | Prod env hardening on AppSail per GO_LIVE_RUNBOOK step list (ENVIRONMENT=production, ALLOWED_HOSTS incl. provider subdomains, CORS_ALLOWED_ORIGINS) — **restart changes env; executes only after P2 origin known** | prod-validation boot + 7-step runbook checks |
| P4 | Tester feedback endpoint (new small table + endpoint, migration with backup), privacy/terms pages (owner-approved text), logout wiring in web | unit/integration tests + e2e smoke |
| P5 | Android: install release APK on owner's phone (USB/wireless adb), full REAL_DEVICE_TEST_PLAN pass | per-gate evidence, honest NOT-RUN where blocked |
| P6 | Security checklist walk (security-engineer review), monitoring doc, gates A–J verdicts, TEST_RESULTS | recorded evidence |

Never-modify rules: no database migration without backup (§4 of master
prompt); no secrets to Git; no Play publishing (B-3 respects explicit approval).

## Known limitations to state publicly (do not overclaim)

- Staging AI: Ollama disabled → server-mediated AI only, quota 20/10 h; the
  web + APK speak to the same backend so quota is shared and honest.
- Free-tier limits (honest, not unverifiable claims): Neon free DB branch
  sizes/rates per Neon docs; AppSail memory per project config; Slate
  bandwidth per Catalyst docs — linked in DEPLOYMENT_RUNBOOK, re-verified at
  deploy time (never padded).
