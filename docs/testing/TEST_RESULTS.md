# MyFarmAI — Test Results (public live deployment)

Updated: **2026-11-08**. Evidence-first: every claim links to an observed
output. Honest gaps are labeled. Companion: `../deployment/DEPLOYMENT_RUNBOOK.md`,
`../security/PUBLIC_DEPLOYMENT_SECURITY_CHECKLIST.md`.

## Gates (master prompt §11)

| Gate | Verdict | Evidence |
|---|---|---|
| A. Frontend build & public access | **PASS** | Slate deploy success; live: `/` 200, `/auth/login` 200, `/auth/register` 200, `/landing` 200, `/legal/privacy` 200, `/legal/terms` 200 (2026-11-08). |
| B. Backend tests & public API health | **PASS** | Backend suite **293/293** (2026-11-08, includes logout + downloads regressions); live `/health/live` 200, `/health/ready` 200 `database: ok`, `ollama: disabled`. |
| C. Database persistence after restart | **PASS (indirect)** | Postgres branch persists (28 tables); `/health/ready` `database: ok` across multiple redeploys 2026-11-07→08. Direct data-survival check after a destructive DB restart NOT exercised (managed provider, restarts are painless). |
| D. Authentication & user isolation | **PASS (partial)** | Login 401/422 contracts live-verified; logout cookie-clear verified live (both domains, `Secure` in production mode); web session = httponly cookie; per-user row isolation enforced by backend (tests). Full register→login e2e for a NEW tester account blocked on OTP retrieval (below). |
| E. AI request & quota tests | **PASS (server-side)** | Quota enforced backend-side (20/10 h per user, `core/config.py`, `services/ai_quota.py`, admin view live); AI on staging = cloud-mediated, Ollama disabled. Live successful chat run with a real account NOT performed (no tester account yet — same OTP blocker). |
| F. Android APK installation & launch | **NOT TESTED (on device)** | Release APK built + verified structurally (62 MB, arm64, staging URL embedded in Hermes bundle, `aapt2` checks). `adb install` + launch pending owner phone pairing. |
| G. Mobile browser testing | **NOT TESTED (real device)** | Pages are responsive by Tailwind classes; external-phone browsing pending. Desktop-level responsiveness verified by build. |
| H. HTTPS & security checks | **PASS with conditions** | security-engineer review `ses_e46e85410ffeI05Fj8JY7nn39k`: PASS with conditions — cookie `Secure` now ON (verified live post-prod-flip); CORS explicit (no wildcard-with-credentials); rate limiting in place; CSRF origin middleware; checklist doc created. |
| I. Backup & recovery test | **NOT DONE** | No DB backup executed: requires Neon credentials (console-only) + owner approval. Names of failures documented in `../deployment/ACCOUNT_SETUP_LOG.md`. |
| J. External tester workflow | **BLOCKED** | Public URLs + tester guide exist; a NEW user cannot finish registration because OTP delivery is dev-mode (code lands in container logs) — needs real SMTP or a provisioned test account. |

## Registration e2e trace (what works, what's blocked)

- `POST /api/v1/auth/register/email/request-otp` → 200 with
  `delivery_mode: "dev"` (live, 2026-11-08).
- Dev adapter (`services/delivery.py:34-59`, owner-approved 2026-11-01):
  logs `DEV-MODE OTP — NOT ACTUALLY DELIVERED: destination=… code=…` and
  writes `/tmp/opencode/dev_otp_outbox.txt` **inside the AppSail
  container**. The OTP is stored hashed in the DB (`verification.py:119`)
  — irrecoverable from there.
- **Unblock options (owner)**: (1) read AppSail console logs after a
  request and enter the code; (2) configure real SMTP creds; (3) manually
  provision a test account in the DB (ADR-008 admin-created path).

## Feature verifications (live, 2026-11-08)

| Check | Result | Evidence |
|---|---|---|
| Web proxy health through public URL | PASS | `GET https://…onslate.in/api/v1/health` → `{"status":"ok","service":"backend"}` |
| Bad login rejected | PASS | `INVALID_CREDENTIALS` 401 (both direct + proxied), no info leak |
| Logout clears cookie | PASS | 204 + `set-cookie: myfarmai_session=""; Max-Age=0; SameSite=lax; Secure` (both direct + proxied) |
| Pre-flip cookie lacked Secure | FIXED | Root cause fixed in `71737f5`; verified Secure appears post-prod-image |
| APK download | PASS | 200, 65,007,414 bytes, `cmp` byte-identical to build artifact; also via web proxy |
| Landing + legal public | PASS | `/landing`, `/legal/privacy`, `/legal/terms` → 200 |
| Rate limiting | PASS (code) | global 60/min + auth prefix 10/min + AI concurrency (live brute-force test not run) |

## Known limitations (honest)
1. New-user registration is dev-mode OTP → testers need owner-provided
   accounts until SMTP configured (gate J blocked for NEW users).
2. No feedback endpoint/table yet (needs DB backup + owner approval).
3. Privacy/terms are DRAFTS labeled as such — owner approval pending.
4. On-device (mobile) tests pending phone pairing.
5. Backend AI = cloud path only on staging; local Ollama never exposed
   publicly (policy, not a defect).
