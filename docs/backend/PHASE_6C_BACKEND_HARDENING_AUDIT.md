# Phase 6C — Backend Hardening Audit

**Date:** 2026-10-31 · **Type:** Read-only security audit (security-engineer subagent evidence, orchestrated per Phase 6C) · **Scope:** `backend/` at commit `700dc2d` + Dockerfile + docker-compose.yml · **Verdict: 6C PASS WITH GAPS** — no Critical/High findings; two Medium code-fix candidates.

## 1. Verified-PASS items (with evidence)

| Area | Evidence |
|---|---|
| Password hashing | Argon2id (m=131072, t=3, p=4) — `core/security.py:16` |
| Token storage | SHA-256 token hashes only; constant-time compare (`hmac.compare_digest`) — `core/security.py:53-60` |
| Cookie flags | `httponly=True`, `secure=(env=="production")`, `samesite=lax` — `api/v1/auth.py:122-130` |
| Session lifecycle | Idle timeout + absolute TTL; refresh single-use rotation with reuse-detection chain revocation — `services/auth.py:194-216, 250-274` |
| Login hygiene | Generic login errors (no account enumeration) + per-account lockout; login/logout audit events — `services/auth.py:129-148` |
| Client-IP trust | XFF-spoofing fixed (rightmost-hop trusted-proxy walk) — `core/client_ip.py:12-47` |
| Rate limiting | Global 60/min + stricter auth 10/min per-IP — `factory.py:177-191`; bounded-memory buckets |
| CSRF | Origin/Referer enforcement on unsafe methods with cookie — `middleware/csrf.py:41-50` |
| Body limits | Request size cap incl. chunked-encoding rejection — `factory.py:26-58` |
| Docs exposure | Swagger/ReDoc disabled in production — `factory.py:153-154` |
| Endpoint auth | All sensitive routers (chat, farms, crop_cycles, conversations, research, vision, voice) require `get_current_user_id`; admin-only user creation (P3-07) — `api/v1/auth.py:206-237` |
| Container | Non-root Dockerfile (uid 10001), `uv sync --frozen`, healthcheck — `Dockerfile:12-24` |
| Compose | Internal bridge network only; Postgres password via Docker secrets file; no published ports |
| Log hygiene | DSN password redacted in logs — `factory.py:87-97` |
| Dependencies | Exact pins in pyproject (floors for 3 libs, frozen by uv.lock) |

## 2. Gaps / risks

| # | Severity | Finding | Recommendation |
|---|---|---|---|
| M1 | **Medium** | `GET /api/v1/weather` and `/api/v1/resources` have **no auth** (`weather.py:13-94`, `resources.py:9-66`) — weather relays unauthenticated third-party traffic through the backend IP (S-18 lineage; only global per-IP limit applies) | Code fix: require auth, or accept + document as public read-only endpoints with strict caching/rate limits |
| M2 | **Medium** | `TrustedHostMiddleware` added only in production, but the production validator **never checks `allowed_hosts`** (`config.py:141-144, 282-309`; `config_profiles.py:52-70`) | Code fix: add `allowed_hosts` to `validate_production_settings` |
| L1 | Low | Dead code: validator checks a `secret_key` field that doesn't exist on `Settings` (`config_profiles.py:67-68`) | Remove or wire to the real field |
| L2 | Low | `logout` `delete_cookie` omits `secure/samesite` attrs (`auth.py:143`); no `__Host-` prefix | Match set-cookie attributes |
| L3 | Low | Base images pinned by tag not digest (`python:3.12-slim`, `uv:0.5` — S-13); compose lacks `read_only`/`cap_drop`/resource limits (S-12) | Digest-pin; add compose hardening in 6B follow-up |
| I1 | Info | Per-process account lockout (`services/auth.py:60-90`) enables targeted lockout DoS; in-memory, same class as accepted SEC-P5-03 | Accepted for single-host; revisit at scale-out |
| I2 | Info | CORS `allow_headers=["*"]` with credentials (`factory.py:173`) | Pin header allowlist |

## 3. Disposition

- **Code-fix candidates (no owner decision needed):** M2, L1, L2 — small, testable changes.
- **Owner decision:** M1 (auth on weather/resources changes the public surface), L3 (deployment hardening — bundle with 6B/6F), I1/I2 (accept or fix).
- Verified secure baseline: authN/Z, session management, injection defenses (`_sanitize_slot`), vision magic-bytes, research SSRF-safe construction, secrets handling all confirmed during Phases 3–5 and re-confirmed here.

**Verdict: 6C PASS WITH GAPS** — hardened baseline verified; M1/M2 are the priority fixes before public exposure.

---

## Addendum (2026-10-31, later session): code fixes applied

- **M2 FIXED** (FCL-064): `validate_production_settings` now rejects the default localhost-only `allowed_hosts` in production.
- **L1 FIXED** (FCL-064): dead `secret_key` check removed (no such Settings field — sessions are server-side tokens; no signing secret exists).
- **L2 FIXED** (FCL-064): logout `delete_cookie` now matches the login `set_cookie` attributes (environment-dependent `secure`, `httponly`, `samesite`).
- **M1 FIXED** (FCL-068, owner approved 2026-10-31): /weather, /weather/current, /resources (x2) now require authentication; 401 tests added.
- **Still open:** L3 (container hardening — bundled with deployment work), I1/I2 (owner sign-off or fix).
- Gate at time of addendum: **192 passed, all checks passed**.
