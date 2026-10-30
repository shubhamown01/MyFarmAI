# Phase 3 Implementation Plan — Authentication, Authorization & Application Security

**Phase:** 3 — authorized, not started
**Date:** 2026-10-28
**Status:** PLAN APPROVED (owner blanket approval 2026-10-28; ADR-008 review APPROVE in `ADR_REVIEWS.md`)
**Prerequisites:** Phase 1 complete (56/56 tests, all gates), Phase 2 rehearsal complete, P1-14 container baseline COMPLETE (FCL-019)
**Roadmap:** [`../phases/Phase_03_Authentication_Security.md`](../phases/Phase_03_Authentication_Security.md)
**Related:** `ADR_REVIEWS.md` §8 (ADR-008), `DECISION_REGISTER.md` (Blanket row), `docs/product/flows/AUTHENTICATION_FLOW.md` (Conditional Draft — to be aligned and finalized in P3-10)

---

## 1. Objectives

Per the roadmap workstreams and ADR-008:

1. Threat model and authorization matrix (document deliverable)
2. Authentication lifecycle: registration, login, logout, expiry, revocation (Argon2id, opaque sessions)
3. Ownership enforcement for farms, conversations, research records
4. Abuse controls: bounded bodies, rate limits, trusted-proxy handling
5. Deployment/secret security hardening
6. Voice service: stays deferred (ADR-014, G6 approved) — no work needed, restate decision

**Key architecture facts (already in place):**
- `User`, `Session` (hashed opaque `session_id_hash`, expiry, revocation fields), `RefreshToken` models exist (P2-05/P2-14)
- `FarmMember` has farm roles; `AuditEvent` exists for security events
- Quality gate `scripts/check.sh` runs on every change
- **No argon2 dependency yet; no auth code exists**

**MVP policy decision (per ADR-008 "deployment-dependent" clause):** private deployment → **admin-created accounts, no public registration, admin-assisted password reset**. Documented here; revisit only if scope changes.

## 2. Task Checklist

### 2.1 Primitives
- [x] **P3-01** Add `argon2-cffi` (+ `argon2-cffi-types`) to `pyproject.toml`/`uv.lock`; verify import in container build
- [x] **P3-02** `app/core/security.py` password service: `hash_password`, `verify_password`, transparent rehash when params change; params tuned to ≈100–300 ms on this host (measure and record); unit tests (round-trip, wrong-password, tampered-hash, rehash trigger)
- [x] **P3-03** `app/core/security.py` token service: `generate_session_id()` / `generate_refresh_token()` via `secrets.token_urlbytes(32)`, `hash_token()` (SHA-256; ADR-008 stores hashes only). Unit tests (uniqueness, constant-time compare)

### 2.2 Services & Repositories
- [x] **P3-04** `app/services/auth.py`: login (verify → create session, rotate), session validate (expiry + revocation + idle timeout), logout (revoke with reason), refresh rotation (old refresh single-use), session cleanup helper. No credentials/tokens in logs
- [x] **P3-05** Repositories: `UserRepository` (get_by_email, create), `SessionRepository` (get_by_hash, create, revoke, purge_expired). Ownership predicates: conversation/farm/research query methods take `user_id` and filter in SQL (deny-by-default)

### 2.3 API & Middleware
- [x] **P3-06** Alembic migration for any schema deltas (sessions table exists from P2 — verify, add only what is missing, e.g. idle-expiry column if adopted)
- [x] **P3-07** `app/api/v1/auth.py`: `POST /auth/login` (web: sets `HttpOnly`/`Secure`/`SameSite=Lax` cookie; Android: returns access token + refresh token), `POST /auth/logout`, `GET /auth/me`, `POST /auth/token/refresh` (Android rotation). Generic errors (no account-existence disclosure). Admin account-creation endpoint (`POST /admin/users`, admin role only) — no public registration
- [x] **P3-08** Auth dependency `get_current_principal` on every private endpoint; web-cookie path and Android `Authorization: Bearer` path; 401 vs 404 semantics per ADR-008 (cross-user → 404)
- [x] **P3-09** Wire ownership into chat/conversations/farms/research endpoints; **replace chat legacy-user fallback (`00000000-...`) with real user attribution; unauthenticated chat becomes 401**
- [x] **P3-10** CSRF/Origin enforcement for state-changing web requests; trusted-host middleware stays

### 2.4 Abuse Controls
- [x] **P3-11** Rate limiting: dedicated stricter limits for `/auth/login` and token refresh (per-IP and per-account); **fix `X-Forwarded-For` spoofing** — trust client IP only from the configured reverse proxy (Caddy) or fall back to socket peer; document the trust config
- [x] **P3-12** Request body size bounds and AI-request concurrency bound (existing rate-limit middleware audit; replace unbounded in-memory counters with bounded strategy)

### 2.5 Audit, Tests, Docs
- [x] **P3-13** Audit events on login success/failure, logout, revocation, admin user creation (no sensitive payloads) via existing `AuditEvent`
- [x] **P3-14** **Auth-matrix tests**: anonymous → 401; expired → 401; revoked → 401; cross-user conversation/farm/research → 404; cross-farm → 404/403 per matrix; refresh reuse detected → revoke family; CSRF/Origin rejection; rate-limit spoofing resistance
- [x] **P3-15** **Async integration regression test**: chat write survives the request in async mode (guards the FCL-019 data-loss class)
- [x] **P3-16** Docs: update `AUTHENTICATION_FLOW.md` (align to approved ADR-008 + admin-accounts decision), `docs/api/openapi.json` regenerate, `API.md`, `BACKEND_AUDIT.md`, `ARCHITECTURE.md`; FCL entry; CHANGELOG; DECISION_REGISTER Phase 3 gate row
- [x] **P3-17** Threat model + authorization matrix document (`docs/engineering/AUTHZ_MATRIX.md`): map every private endpoint → required role/ownership

## 3. Acceptance Criteria (from roadmap — verified, not asserted)

- [x] Every private endpoint has an explicit auth policy (P3-08/P3-17)
- [x] Cross-user and cross-farm access tests denied (P3-14)
- [x] Session/token expiry and revocation tested (P3-14)
- [x] Passwords use Argon2id with recorded timing (P3-02)
- [x] Rate limits cannot be bypassed via spoofed `X-Forwarded-For` (P3-11)
- [x] Request sizes and expensive workloads bounded (P3-12)
- [x] No credentials in source, logs, or responses (P3-04/P3-13 + secret scan)
- [x] Security events logged without sensitive payloads (P3-13)

**Exit gate:** security-engineer review of the auth implementation + quality gate green before any non-loopback exposure.

## 4. Constraints & Notes

- **Canonical DB / migration discipline:** schema changes via Alembic only; never touch `backend/data/app.db` directly
- **Web + Android dual client:** keep web cookie session and Android opaque bearer tokens separate as ADR-008 specifies; no JWT
- **Hardware:** Argon2id timing measured on the 7 GiB host; do not raise defaults without measurement
- **Secrets:** none introduced; `.pg_password` handling unchanged; no credentials in logs (verify with a log-capture test)
- **Preserve pre-existing uncommitted work** (android/, web/, opencode.json); file ownership: auth files are new; `factory.py`, `chat.py`, `services/chat.py`, rate-limit middleware are edited only per tasks above
- **Legacy-user data:** migrated conversations owned by the nil UUID remain readable only by admin for support purposes (decision recorded in P3-09)
