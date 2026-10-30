# MyFarmAI — Authorization Matrix & Threat Model

**Status:** Implemented (Phase 3, P3-17) — reflects code as verified by `bash scripts/check.sh` (113 tests)  
**Related:** ADR-008, `AUTHENTICATION_FLOW.md`, `docs/api/openapi.json`, FCL-019..024

## 1. Authorization Model

- **Roles:** `user`, `admin` (`users.role`). Admins are seeded/admin-created; no privilege-escalation endpoint exists.
- **Ownership:** user-owned rows carry `user_id`; repository methods **require** `user_id` and filter in SQL (deny-by-default). Cross-user access returns **404** (not 403) to avoid resource enumeration.
- **Legacy data:** pre-auth rows owned by sentinel `00000000-…` are invisible to real users; not reassigned.

## 2. Endpoint Matrix

| Endpoint | Method | Auth required | Role | Scope |
|---|---|---|---|---|
| `/api/v1/auth/login` | POST | No (rate-limited 10/min/IP + lockout) | — | — |
| `/api/v1/auth/logout` | POST | Yes (session) | user | Own session only |
| `/api/v1/auth/me` | GET | Yes (session/bearer) | user | Own record only |
| `/api/v1/auth/token/refresh` | POST | Refresh token | user | Own token chain |
| `/api/v1/auth/admin/users` | POST | Yes | **admin** | — |
| `/api/v1/chat` | POST | Yes | user | Own conversations only (cross-user → 404) |
| `/api/v1/weather*`, `/api/v1/resources*`, `/health*`, `/` | GET | Currently open | — | Read-only, no user data; to be gated when they expose per-user state |

## 3. Threat Model (STRIDE, MVP-relevant)

| Threat | Mitigation (implemented) |
|---|---|
| Credential brute force | Argon2id (~114 ms), per-IP limit 10/min on auth, per-account lockout 5/15min → 429, generic errors (no enumeration) |
| Token theft / replay | Opaque 256-bit tokens; only hashes stored; single-use refresh rotation; reuse → chain + all-sessions revocation + audit event |
| Session fixation | Server-generated tokens only; HttpOnly + SameSite=Lax + Secure-in-prod cookie; server-side revocation on logout |
| CSRF | SameSite=Lax + Origin/Referer rejection (403) on cookie-carrying unsafe requests; bearer clients immune (no cookie) |
| IP spoofing to evade limits | X-Forwarded-For honored only from configured trusted proxies; peer address otherwise authoritative |
| Cross-user data access (IDOR) | Ownership predicates in SQL at repository layer; 404 semantics; tested at service and API levels |
| Privilege escalation | Admin endpoints check role server-side; no role-change endpoint; non-admin → 403, anonymous → 401 |
| Resource exhaustion | Body-size limit (10 MB cap incl. chunked-encoding rejection), bounded rate-limit counters, AI-request semaphore (`ai_max_concurrent_requests=2`), DB-level request limits |
| SQL injection | SQLAlchemy ORM, parameterized queries throughout |
| Secrets in audit logs | Audit payloads limited to ids, categories, generic descriptions, IP, UA |

## 4. Known Limitations (accepted for MVP)

- Lockout and rate-limit state is **process-local** (single-worker uvicorn; multi-worker needs a shared store).
- Unknown-email login failures are lockout-tracked but not audited (no user subject).
- Middleware error bodies are flat `{detail, error_code}` vs. endpoint-nested envelopes — normalization tracked.
- Audit-log retention and alerting pipeline: not yet defined (S-11/ADR-015).
- **Account-lockout DoS:** 5 failed logins lock any known email for 15 min; unauthenticated third parties can weaponize this against known addresses (MVP tradeoff, per exit-gate review 2026-10-29).
- **Refresh-chain revocation (fast-follow ≤ Phase 4):** reuse detection currently revokes the direct chain; a token ≥2 generations old leaves the newest descendant live — planned fix: revoke all of the user's refresh tokens on reuse. Exit-gate finding, medium.
