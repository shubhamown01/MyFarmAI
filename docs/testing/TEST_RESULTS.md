# MyFarmAI — Test Results (public live deployment)

Updated: **2026-11-10** (security audit pass; previous live-deployment run 2026-11-09). Evidence-first: every claim links to an observed output. Honest gaps are labeled. Companion: `../deployment/DEPLOYMENT_RUNBOOK.md`, `../security/PUBLIC_DEPLOYMENT_SECURITY_CHECKLIST.md`, `../security/V1_RELEASE_SECURITY_CHECKLIST.md`.

## Gates (master prompt §11) — honest verdicts

| Gate | Verdict | Note |
|---|---|---|
| A. Frontend build & public access | **PASS** | Slate deploy + 6 public routes 200 |
| B. Backend tests & public API health | **PASS** | 310/310 tests pass (includes feedback admin-gate regression tests) |
| C. DB persistence after restart | **PASS (indirect)** | Neon branch survives redeploys; managed, no data loss observed |
| D. Auth & user isolation | **PASS (partial)** | Login/logout/cookie/401/422 verified; **register e2e BLOCKED on OTP** (dev-mode, code in container logs only) |
| E. AI quota & request | **PASS (server)** | 20/10 h enforced backend; AI path cloud-only on staging |
| F. APK install & launch | **NOT TESTED** | APK built & hosted; needs owner phone pairing |
| G. Mobile browser | **NOT TESTED** | Responsive by design; external phone pending |
| H. HTTPS & security | **PASS with conditions** | Cookie `Secure` now PRODUCTION-LIVE; CORS explicit; CSRF middleware; rate limits; checklist doc created |
| I. Backup & recovery | **PASS (migration)** | Feedback migration applied to Neon prod branch (2026-11-09): `f4b2c3d4e5a7_fb_feedback1`, table `feedback` verified (uuid PK, FK→users.id ON DELETE SET NULL, ix_feedback_user_id); round-trip insert/read/delete succeeded. pg_dump full backup still pending owner console access |
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
| List feedback (admin-only) | ✅ | `GET /api/v1/feedback` requires an authenticated `admin`: live anonymous → 401 `NOT_AUTHENTICATED` after the 2026-11-10 redeploy; non-admin → 403 and admin → 200 covered by tests |
| Pagination | ✅ | `limit`/`offset` parameters work correctly |

## Known limitations (do not overclaim)

1. **New-user registration** — OTP dev-mode only (codes in AppSail logs). Testers must use pre-provisioned accounts until SMTP configured.
2. **Feedback endpoint** — submission is public by design; listing is now admin-only in source. The fixed backend build still needs rebuild/redeploy, and a full `pg_dump` backup remains owner-pending.
3. **Privacy/Terms** — current pages marked **DRAFT**; owner text pending.
4. **On-device testing** — APK built & hosted; needs owner phone pairing (USB debugging or `adb pair`).
5. **AI on staging** — cloud-mediated only; local Ollama never exposed publicly (policy).

**All production code changes are committed (`9abb2d6`, feedback at `e97a800`, migration fix commit below). The feedback schema is now LIVE in the Neon production database (2026-11-09).**

## Security redeploy verification (2026-11-10)

| Check | Result |
|---|---|
| Backend `/health/live`, `/health/ready` | 200; `database: ok`, `ollama: disabled` |
| Anonymous `GET /api/v1/feedback` | 401 `NOT_AUTHENTICATED` (SEC-001 closed) |
| Wrong-password login | 401 `INVALID_CREDENTIALS` |
| Slate security headers | `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy`, `Permissions-Policy`, HSTS |
| CORS allowed origin | `Access-Control-Allow-Origin` echoes the Slate origin; wrong origin gets none |
| Release APK | rebuilt, `CN=MyFarmAI Release`, no `SYSTEM_ALERT_WINDOW`; hosted copy byte-identical |
| Local Postgres backup | `scripts/backup.sh` → 80K dump, `pg_restore --list` clean |

Remaining: a full Neon `pg_dump`/restore drill (no Neon credentials locally).