# MyFarmAI — PentAGI / Dynamic Test Results (V1.0.0)

- **Date:** 2026-11-10
- **Environments:** local backend `http://127.0.0.1:8000`, staging backend
  `https://myfarmai-backend-50047414881.development.catalystappsail.in`
- **Mode:** non-intrusive verification only; no exploitation, DoS, persistence,
  or data exfiltration.

## 1. PentAGI status

**Not deployed.** Reasons:

1. PentAGI is a Docker-compose platform with its own PostgreSQL, worker, and
   agent stack. The host had 686 MB free RAM (2.6 GB available) and heavily used
   swap during the audit; adding the stack risked destabilizing the existing
   backend/Postgres/Ollama services.
2. It requires an external LLM provider key and network egress; no dedicated
   isolated environment was authorized for autonomous exploitation.
3. The audit did not require autonomous exploitation to meet its goals: the
   confirmed High findings were reproducible with a single HTTP request and
   static review, and the remaining checks are covered by the matrix below.

This is a documented limitation, not a claim that PentAGI ran. The equivalent
open-source toolchain and manual tests are listed here with their actual results.

## 2. Executed test matrix

| # | Test | Method | Result |
|---|---|---|---|
| 1 | Staging health | `GET /health/live` | **PASS** — 200, JSON, provider HTTPS + HSTS |
| 2 | Unauthenticated feedback list | `GET /api/v1/feedback?limit=2` on staging | **FAIL (finding)** — 200 with rows; fixed in source, staging pending redeploy |
| 3 | Protected resource without session | `GET /api/v1/resources` on staging | **PASS** — 401 |
| 4 | Protected resource with session | backend test client | **PASS** — 200 |
| 5 | Login / refresh / logout | `tests/test_auth_api.py`, `test_auth_matrix.py` | **PASS** — cookie contract, revocation, idle timeout |
| 6 | Account lockout | `tests/test_auth_api.py` | **PASS** — lockout after configured failures |
| 7 | OTP request/verify/replay | `tests/test_email_otp.py` | **PASS** — single-use, expiry, max attempts, resend cooldown |
| 8 | OAuth state/nonce/replay | `tests/test_oauth_api.py` | **PASS** — state single-use, nonce mismatch rejected, issuer/audience checked |
| 9 | OAuth account-linking protection | `tests/test_oauth_api.py` | **PASS** — active account never silently merged (409) |
| 10 | Admin selfie queue/decision/raw | `tests/test_selfie_admin.py` | **PASS** — anonymous 401, non-admin 403, raw file deleted on decision |
| 11 | Feedback admin gate (new) | `tests/test_feedback.py`, `test_feedback_list.py` | **PASS** — anonymous 401, non-admin 403, admin 200 |
| 12 | Selfie upload validation | `tests/test_selfie.py` | **PASS** — magic bytes, size, dimensions (pre-decode), EXIF strip, 0600 |
| 13 | Oversized-dimension decode guard (new) | `tests/test_selfie.py` | **PASS** — 4097×4097 → 422 without full decode |
| 14 | CSRF origin enforcement | `tests/test_security_middleware.py` | **PASS** — cross-origin cookie-authenticated writes rejected |
| 15 | Request body limit | `tests/test_security_middleware.py` | **PASS** — oversized bodies rejected |
| 16 | Rate limiting | `tests/test_security_middleware.py` | **PASS** — per-IP window + 429 `Retry-After` |
| 17 | Client IP spoof resistance | `tests/test_security_middleware.py` | **PASS** — `X-Forwarded-For` honored only from trusted proxies |
| 18 | Error envelope / no stack traces | `tests/test_security.py` | **PASS** — structured `error_code` responses |
| 19 | User isolation (farms/conversations/chat) | `tests/test_farms_api.py`, `test_conversation_ownership.py`, `test_chat.py` | **PASS** — cross-user access rejected |
| 20 | Web token storage | source grep + `web` tests | **PASS** — no auth tokens in localStorage/sessionStorage; HttpOnly cookie |
| 21 | Web security headers | `node` evaluation of `next.config.js` | **PASS** — five headers returned for all routes |
| 22 | Android token storage | source review | **PASS** — `expo-secure-store` for session/refresh/conversations |
| 23 | Android release manifest | generated manifest review | **FAIL (finding)** — `SYSTEM_ALERT_WINDOW` + `allowBackup`; permission fixed in config |
| 24 | Secret scan | gitleaks | **PASS** — one false positive (localStorage key) |
| 25 | Dependency scan | pip-audit, npm audit, osv-scanner, Trivy | **PASS with findings** — see `DEPENDENCY_AUDIT.md` |

## 3. Live staging observations

```text
GET /health/live
HTTP/1.1 200
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Strict-Transport-Security: max-age=64072000; includeSubDomains; preload

GET /api/v1/feedback?limit=2
HTTP/1.1 200
{"items":[...],"count":...}      # pre-fix; authorization failure
```

The staging `Set-Cookie` observed on `/health/live` is the Catalyst platform
cookie (`zalb_*`, `ZD_CSRF_TOKEN`), not the MyFarmAI session cookie. The app
session cookie flag could not be verified live without a synthetic login on the
deployed build; the source-level finding SEC-005 is recorded from the
`ENVIRONMENT` configuration.

## 4. Not performed

- Active exploitation (SQLi, XSS payloads, auth bypass attempts).
- Denial-of-service or load testing.
- Authenticated staging fuzzing (no staging test account was used).
- ZAP/burp scan.
- Production testing.
- Android APK dynamic instrumentation (no rebuild during the audit).

## 5. Conclusion

The non-intrusive test matrix passed everywhere except the two confirmed
authorization/manifest findings, both fixed in source. PentAGI's autonomous
exploitation phase remains an optional follow-up once an isolated environment
with sufficient memory and explicit approval is available.
