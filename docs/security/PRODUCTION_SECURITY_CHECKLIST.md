# MyFarmAI — Production Security Checklist (v1.0.0)

**Document ID:** MYFARMAI-SEC-012
**Version:** 1.0
**Date:** 2026-11-11
**Scope:** the v1.0.0 release surface — web app, API, database, Android client, artifact distribution
**Companions:** `docs/security/V1_RELEASE_SECURITY_CHECKLIST.md` (detailed findings),
`docs/security/DEPENDENCY_AUDIT.md`, `docs/security/API_SECURITY_AUDIT.md`,
`docs/security/ANDROID_SECURITY_AUDIT.md`

This checklist records what was **observed**. It does not assert that the system is
secure; it states which controls were verified and which remain open.

## 1. Transport and headers

| Control | Status | Evidence (2026-11-11) |
|---|---|---|
| HTTPS on web | **PASS** | `https://myfarmai-web-zwpytbwu.onslate.in/landing` → 200 over TLS |
| HTTPS on API | **PASS** | `https://myfarmai-backend-50047414881.development.catalystappsail.in/health/ready` → 200 |
| HSTS (web) | **PASS** | `strict-transport-security: max-age=31536000` |
| HSTS (API) | **PASS** | `max-age=64072000; includeSubDomains; preload` |
| `X-Frame-Options` | **PASS** | `DENY` on both origins |
| `X-Content-Type-Options` | **PASS** | `nosniff` on both origins |
| `Referrer-Policy` (web) | **PASS** | `strict-origin-when-cross-origin` |
| `Permissions-Policy` (web) | **PASS (with note)** | `geolocation=(self), camera=(), microphone=()` — see §7 gap 2 |
| Content-Security-Policy | **FAIL (open)** | No CSP header on the web origin. Tracked as a v1.0.1 hardening item. |

## 2. Session and credential handling

| Control | Status | Evidence |
|---|---|---|
| Session cookie `HttpOnly` | **PASS** | Live `Set-Cookie` on logout: `myfarmai_session=""; HttpOnly; Max-Age=0; Path=/; SameSite=lax; Secure` |
| Session cookie `Secure` | **PASS** | Same live header |
| Session cookie `SameSite` | **PASS** | `Lax` |
| Opaque server-side sessions | **PASS** | Session id is random; revocation on logout (204) |
| Password hashing | **PASS** | Argon2id, rehash-on-login (`app/core/security.py`) |
| Account lockout | **PASS** | 5 failures / 15 min → 429 `ACCOUNT_LOCKED`, covered by tests |
| Refresh-token rotation + reuse detection | **PASS** | Android path, covered by tests |
| Password required at OTP verification | **PASS (repo only)** | Added in `6976a3f` (MFAI-022); **not deployed** |
| Password reset | **PARTIAL** | Only via OTP verify; requires working email delivery |
| Secrets in Git | **PASS** | gitleaks clean on the release diff; only test fixtures, explicitly allow-listed |
| Secrets in clients | **PASS** | APK bundle inspected: one backend host, no keys, no dev URLs |

## 3. Authorization and data isolation

| Control | Status | Evidence |
|---|---|---|
| Server-side authorization on every resource | **PASS** | `test_auth_matrix`, per-resource ownership tests |
| Farm/plot/crop-plan ownership | **PASS** | `test_farms_api`, `test_land_api`, `test_crop_plans`, `test_crop_cycles_api` |
| Conversation ownership | **PASS** | `test_conversation_ownership`, `test_p5g_conversations` |
| Cross-tenant access denied | **PASS (repo)** | 313 backend tests; live two-account test **not run** |
| Admin-only endpoints gated by role | **PASS** | `/admin/*` require `role == admin` |
| Live isolation test with two synthetic accounts | **NOT TESTED** | Needs a working registration path |

## 4. Input, upload and abuse controls

| Control | Status | Evidence |
|---|---|---|
| Request validation | **PASS** | Pydantic schemas; bounded query params (`q` 2–200, `limit` 1–20) |
| Rate limiting | **PASS** | Global + 10 req/min/IP on `/auth/*`; trusted-proxy CIDR list prevents `X-Forwarded-For` spoofing |
| CSRF | **PASS** | Origin/Referer check on unsafe cookie requests; SameSite=Lax |
| CORS | **PASS** | Allow-list of the Slate origin only |
| Upload size/type validation | **PASS** | Vision: 5 MiB cap, magic-byte check, in-memory only. Selfie: re-encoded, EXIF stripped, `0700` dir |
| SSRF in research | **PASS** | No user-supplied URL is fetched; SearXNG base URL is operator-configured |
| Prompt injection | **ACCEPTED RISK** | Model output rendered as text; no tool-execution path (SEC-029) |

## 5. Infrastructure and data

| Control | Status | Evidence |
|---|---|---|
| Database not publicly reachable | **PASS** | Managed Neon, private endpoint; no DB port exposed by this host |
| Database credentials server-side only | **PASS** | `DATABASE_PATH` in the container environment |
| No developer laptop / Docker socket / Ollama exposed | **PASS** | No inbound tunnel or port-forward is configured |
| Backups | **BLOCKED** | No automated `pg_dump`; no restore drill. **Gate F.** |
| Data export | **NOT IMPLEMENTED** | No endpoint |
| Account deletion | **NOT IMPLEMENTED** | No endpoint |
| Log hygiene | **PASS (by design)** | Auth audit events exclude passwords/tokens/hashes |

## 6. Dependency and artifact integrity

| Control | Status | Evidence |
|---|---|---|
| Dependency vulnerabilities | **PASS (remediated)** | pip-audit, osv-scanner, npm audit, Trivy — `docs/security/DEPENDENCY_AUDIT.md` |
| Residual advisories | **ACCEPTED RISK** | SEC-002 Starlette Medium/Low, not exploitable without an authenticated session; owner acknowledgement required |
| APK signature | **PASS** | `apksigner verify` → valid; `CN=MyFarmAI Release`; cert SHA-256 `cfa4f1d7…3bdf48` |
| APK checksum published and matching | **PASS** | 67,884,479 B → `352020c5…c465` |
| APK debug build shipped by mistake | **PASS (not shipped)** | Signature is the release key, not the debug key |
| Android `allowBackup` | **OPEN** | SEC-009, owner decision |
| EOL Android framework | **ACCEPTED RISK** | SEC-010 — no runtime patch stream until the Expo/RN upgrade |
| Dynamic scan (OWASP ZAP) | **NOT RUN** | Required before the next public exposure |

## 7. Gaps that affect functionality or security

1. **No CSP.** The web origin sends no `Content-Security-Policy`. Add one before the next
   public release.
2. **`camera=()` blocks `getUserMedia`.** The web policy denies camera access to the
   origin. The selfie flow has no capture UI today (MFAI-025), so nothing breaks yet — but
   any future in-browser camera capture must amend this header first.
3. **Selfie verification is unreachable and unapprovable** (MFAI-025). This is a
   functional blocker with a security dimension: the identity gate cannot be satisfied or
   waived.
4. **Registration cannot complete** because no email provider is configured.
5. **Backup/restore is unverified** (gate F).

## 8. Sign-off

| Role | Decision | Date |
|---|---|---|
| Automated security review | **Conditional** — no open Critical/High code finding; blocked on backup/restore (F), ZAP, and the MFAI-025 owner decision | 2026-11-11 |
| Owner | _pending_ | |

**No public-launch security approval is claimed.** The controls above are verified; the
open items are listed rather than waived.
