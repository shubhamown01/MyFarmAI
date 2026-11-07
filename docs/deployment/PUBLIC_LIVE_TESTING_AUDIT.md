# MyFarmAI — Public Live Testing Audit

Date: 2026-11-08. Status: **COMPLETE** (pre-deployment audit, no changes made).
Inputs: code inspection (web/, backend/), live staging probes, existing
deployment docs, subagent code-inventory (session `ses_e4869f4baffeAvR3TszN9zMx29`).

## 1. Existing architecture (verified, not rebuilt)

| Component | State | Public today? |
|---|---|---|
| Backend FastAPI (`backend/`) | LIVE on Zoho Catalyst AppSail (owner's existing account, ₹0) — `https://myfarmai-backend-50047414881.development.catalystappsail.in`; `/health/live` 200, `/health/ready` 200 `{"database":"ok","ollama":"disabled"}` | YES |
| Database | Neon Postgres (`org-fragrant-cell-14431918`, project `holy-shadow-54756094`, branch `br-young-fire-a1ll0fm0`), permanent free tier, no card, no inactivity pause; 28 tables + migrations applied | YES (via backend only) |
| Web frontend (`web/`, Next.js 15 App Router, Tailwind) | Builds; verified same-origin `/api/v1` proxy to backend (`next.config.js:9-17`, `MYFARMAI_API_ORIGIN`) | **NO — missing piece 1** |
| Android APK (`android/`) | Debug APK built & verified (`app-debug.apk`, 136 MB); release build (embedded bundle, staging URL) in progress | **NO — missing piece 2** |
| AI | Backend routes chat via AI gateway; Ollama disabled on staging (`ollama:"disabled"` in readiness). Cloud AI quota: 20 req/user/10 h enforced server-side (`core/config.py:143-150`, `services/ai_quota.py`) | via backend |
| Weather | Open-Meteo free tier (non-commercial licensing decision still pending owner per LICENSING_DECISIONS) | via backend |
| Monitoring | `/health/live`, `/health/ready`, `x-request-id` middleware (factory.py:244-265), structured logs | YES |

## 2. Feature inventory for public access (from code)

Present: email-OTP registration (`POST /auth/register/email/request-otp`,
`.../verify` at `auth.py:280,308`), login/logout/me/refresh (`auth.py:118-238`),
farms CRUD + plots + members (`farms.py`, `land.py`), chat (`chat.py:42`),
weather (`weather.py:14,58`), quota admin endpoints (`admin_quota.py`),
vision analyze (`vision.py:48`). Web pages: `/auth/login`, `/auth/register`,
`/onboarding`, `/` dashboard, `/assistant` chat, `/crops`, `/weather`,
`/history`, `/settings`, others.

Gaps for §5/§7 of the master prompt (must add before external testers):

1. **No public landing page** — `/` is the auth-gated dashboard.
2. **No logout in web client** — backend `POST /auth/logout` exists (`auth.py:163`) but no UI wiring.
3. **No privacy policy / terms document** — none found anywhere in repo.
4. **No tester feedback endpoint** — no feedback/bug-report API or table.
5. Web `/farms` UI absent (farms API exists; crops page partially covers; acceptable for testers with documented workaround — farmland flows live in `/crops` + backend).

## 3. Test baseline

- Backend tests: 56/56 hermetic refactor → historically `171 passed, 0 failed`
  (`docs/backend/ROADMAP.md:287`, `PHASE_5_FINAL_TESTING_REPORT.md:27`). The
  Phase-0 "7 clean-DB test_chat failures" finding is **already fixed on main**;
  stale references remain in `.opencode/agents/backend-engineer.md:50` (doc
  cleanup item, not a blocker).
- Mobile: 16/16 jest unit, lint/typecheck clean, debug APK installs size-verified.
- Staging integration evidence: 2026-11-07 (rate-limit spoof resistance,
  14-endpoint OpenAPI contract, web-frontend proxy verification).

## 4. ₹0 provider evaluation (existing accounts first)

Per `docs/deployment/FREE_TIER_COMPARISON.md` (verified 2026-11-03) +
current-account reality:

| Component | Selected | Why | Not selected because |
|---|---|---|---|
| Backend | **Zoho Catalyst AppSail (existing)** | already deployed + verified; owner's Zoho account; no card; ₹0 consumed so far | Koyeb/Render/Railway require card or paid plan (BLOCKED); Prisma Compute TS-only |
| Database | **Neon (existing)** | free, no card, no sleep; verified live | Supabase pauses projects weekly; Prisma op-caps |
| Web frontend | **Catalyst Slate (existing Zoho account)** vs Cloudflare Pages (account already created 2026-11-03) | both ₹0 and card-free — decide in PUBLIC_DEPLOYMENT_PLAN after Slate capability check for Next.js standalone+SSR | Vercel Hobby is non-commercial terms-risk; Netlify credit-metered |
| AI | backend gateway as-is (Ollama disabled publicly) | local-first policy; Ollama never exposed publicly | any paid LLM API |
| APK hosting | see blocker B-3 | | |

## 5. Blockers / decisions (BLOCKED until resolved)

- **B-1 Production env hardening on AppSail**: staging currently runs
  development-profile defaults (no `ENVIRONMENT=production`). Go-live requires
  `ENVIRONMENT=production`, `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`
  (GO_LIVE_RUNBOOK D1–D4 now partially resolved: D1 = owner's public-testing
  request of 2026-11-08; D2 domain = defer, provider HTTPS subdomain accepted;
  D3 = Slate/Cloudflare decision in P1; D4 non-commercial confirmation = still
  owner's declaration).
- **B-2 Voice service containment**: Phase-0 finding — voice service
  unauthenticated on `0.0.0.0:8001` — is a *local* service; not exposed by the
  public deployment. Containment approval still open (governance gate), does
  not block public web/API deployment.
- **B-3 APK public hosting**: no public download location for the APK yet
  (candidate: AppSail static route or a share link; needs a decision; no
  unused new accounts).
- **B-4 Privacy policy + terms**: required before public registration
  (§5, §9). Content must be based on actual data collected (auth identity,
  farms/crops location data, OTP email, feedback). OWNER-APPROVED text needed.
- **B-5 Open-Meteo non-commercial use**: free-tier license restricts
  commercial use; public testing with synthetic accounts is acceptable, but
  go-live commercial use needs the owner's licensing decision (documented).
- **B-6 External accounts**: creating any new provider account requires
  explicit owner approval (§13 rule). Existing: Zoho, Neon, Cloudflare.

## 6. Preserving existing work

- Git tree **clean** at audit time (branch `phase-01-foundation`, 17 commits).
- Staging DB untouched; no migrations unless required by new features
  (e.g. feedback table) — and then only with backup first.
- Release APK build running in parallel; no overlap with audit files.

## 7. Audit verdict

Proceed: **YES** — public access is achievable ₹0 with existing accounts.
Missing pieces are frontend hosting (P2), APK artifact (P0b in progress),
tester feedback + policy docs (P4), and production-environment hardening
(P3, runbook procedure). No rebuild of existing functionality required.
