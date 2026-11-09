# MyFarmAI — Test Results (public live deployment)

Updated: **2026-11-09**. Evidence-first: every claim links to an observed output. Honest gaps are labeled. Companion: `../deployment/DEPLOYMENT_RUNBOOK.md`, `../security/PUBLIC_DEPLOYMENT_SECURITY_CHECKLIST.md`.

## Gates (master prompt §11) — honest verdicts

| Gate | Verdict | Note |
|---|---|---|
| A. Frontend build & public access | **PASS** | Slate deploy + 6 public routes 200 |
| B. Backend tests & public API health | **PASS** | 305/305 tests pass (293 + 12 feedback tests) |
| C. DB persistence after restart | **PASS (indirect)** | Neon branch survives redeploys; managed, no data loss observed |
| D. Auth & user isolation | **PASS (partial)** | Login/logout/cookie/401/422 verified; **register e2e BLOCKED on OTP** (dev-mode, code in container logs only) |
| E. AI quota & request | **PASS (server)** | 20/10 h enforced backend; AI path cloud-only on staging |
| F. APK install & launch | **NOT TESTED** | APK built & hosted; needs owner phone pairing |
| G. Mobile browser | **NOT TESTED** | Responsive by design; external phone pending |
| H. HTTPS & security | **PASS with conditions** | Cookie `Secure` now PRODUCTION-LIVE; CORS explicit; CSRF middleware; rate limits; checklist doc created |
| I. Backup & recovery | **NOT DONE** | Requires Neon creds (console) + owner approval |
| J. External tester workflow | **BLOCKED** | New user registration needs OTP (dev-mode) → needs real SMTP or provisioned test account |

## Feature verification - feedback endpoint (E1)

| Feature | Verified | Evidence |
|---|---|---|
| Submit feedback (anonymous) | ✅ | `/api/v1/feedback/submit` → 200 with valid JSON |
| Submit feedback (with email) | ✅ | `/api/v1/feedback/submit` with email → 200 |
| Category validation | ✅ | 422 for invalid categories |
| Message length validation | ✅ | 422 for messages <5 chars |
| Email validation | ✅ | 422 for invalid email format |
| App version validation | ✅ | 422 for invalid version length |
| List feedback (read-only) | ✅ | `/api/v1/feedback` → 200 with items count and list |
| Pagination | ✅ | `limit`/`offset` parameters work correctly |

## Known limitations (do not overclaim)

1. **New-user registration** — OTP dev-mode only (codes in AppSail logs). Testers must use pre-provisioned accounts until SMTP configured.
2. **Feedback endpoint** — fully implemented and tested, but requires owner approval for DB backup + migration to persist data.
3. **Privacy/Terms** — current pages marked **DRAFT**; owner text pending.
4. **On-device testing** — APK built & hosted; needs owner phone pairing (USB debugging or `adb pair`).
5. **AI on staging** — cloud-mediated only; local Ollama never exposed publicly (policy).

**All production code changes are committed (`9abb2d6`). The feedback feature is implemented, tested, and ready for owner approval on DB backup and migration.**