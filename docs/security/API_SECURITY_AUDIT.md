# MyFarmAI — API Security Audit (V1.0.0)

- **Date:** 2026-11-10
- **Scope:** FastAPI application (`backend/app`), middleware, auth, authorization,
  input handling, and the web/Android clients' API usage.
- **Method:** source review, route inventory, OpenAPI inspection, hermetic tests,
  and targeted live checks against staging.

## 1. Authentication model

| Client | Credential | Storage | Validation |
|---|---|---|---|
| Web | Opaque session ID in `myfarmai_session` cookie | HttpOnly, SameSite=Lax, `Secure` when `ENVIRONMENT=production` | `AuthService.validate_session` (expiry, revocation, idle timeout) |
| Android | Bearer session token | `expo-secure-store` | Same session validator; refresh token rotation |
| OAuth (web) | Session cookie after provider callback | HttpOnly cookie | state + nonce + id_token signature/issuer/audience |
| Admin | Same session + `users.role = admin` | — | Server-side role lookup on every admin route |

Positive controls:

- Passwords hashed with Argon2id; login lockout after repeated failures.
- OTP: single-use, expiry, max attempts, resend cooldown, hashed codes.
- Session refresh tokens rotate; logout revokes and clears the cookie.
- OAuth state is single-use and nonce-bound; active accounts are never silently
  linked to a provider identity.
- No auth token is written to web `localStorage`/`sessionStorage`.

## 2. Route authorization matrix

| Route group | Authentication | Authorization / notes |
|---|---|---|
| `GET /health`, `/health/live`, `/health/ready` | Public | Liveness/readiness only |
| `POST /api/v1/feedback/submit` | Public (by design) | Rate-limited; validated category/message; optional email |
| `GET /api/v1/feedback` | **Admin only (fixed)** | Was public — SEC-001 |
| `GET /api/v1/downloads/{name}` | Public | Filename allowlist + resolved path containment |
| `GET /api/v1/app-updates/latest` | Public | Static version metadata only |
| `/api/v1/auth/login`, `/token/refresh`, OTP, OAuth | Public | Stricter rate limit; CSRF origin check on cookie writes |
| `GET/PATCH /api/v1/auth/me`, `/preferences` | Session | Self only |
| `POST /api/v1/auth/admin/users` | Session + admin | Role checked in route |
| Farms, plots, crop cycles/plans, dashboard, conversations, chat | Session | Repository queries scoped by `user_id`/farm membership |
| `POST /api/v1/vision/analyze`, `/selfie/*` | Session | Pending-verification and consent gates; upload validation |
| `GET /api/v1/research`, `/weather*`, `/resources*` | Session | Fixed upstream URLs (no user-supplied URL fetch) |
| `/api/v1/verification/admin/selfies*` | Session + admin | `_require_admin` on all three routes |
| `GET /api/v1/admin/ai-quota` | Session + admin | `_require_admin` |
| `/api/v1/voice/capabilities` | Session | Capability metadata |

User isolation was exercised by `test_farms_api.py`,
`test_conversation_ownership.py`, `test_chat.py`, and the conversation tests:
cross-user reads/writes are rejected with 404/403.

## 3. Transport, cookies, CSRF, CORS

- HTTPS is terminated by the platform; the backend gateway sends HSTS,
  `X-Content-Type-Options`, and `X-Frame-Options`. The Next.js app now sends its
  own baseline headers (SEC-006).
- Session cookie: HttpOnly, SameSite=Lax, path `/`; `Secure` depends on
  `ENVIRONMENT` (SEC-005, owner console action).
- CSRF: `CSRFOriginMiddleware` rejects unsafe requests that carry the session
  cookie and present a disallowed Origin/Referer. Bearer-token Android requests
  carry no cookie and are unaffected.
- CORS: no wildcard with credentials; production validation requires explicit
  `CORS_ALLOWED_ORIGINS`.
- Trusted hosts: `TrustedHostMiddleware` is enabled when `ALLOWED_HOSTS` is set.

## 4. Rate limiting and abuse controls

- General limiter (default 60 req/60 s per client IP) plus a stricter auth-prefix
  limiter (10 req/60 s).
- Client IP is derived from `X-Forwarded-For` only when the socket peer is a
  trusted proxy; otherwise the peer address is used.
- Body size capped by `RequestBodyLimitMiddleware`.
- In-process counters (SEC-012): effective on the current single-worker
  deployment, bypassable if horizontally scaled; move to a shared store before
  scaling.
- Feedback submission is public but rate-limited; spam/abuse is an accepted
  design risk (SEC-019).

## 5. Input validation and file handling

- Pydantic models enforce types, lengths, and email format; error responses use a
  structured `{detail, error_code}` envelope with no stack traces.
- Selfie upload: magic-byte sniff (JPEG/PNG), 5 MiB cap, 512–4096 px dimension
  gate **before decode** (SEC-007), EXIF/metadata stripped by re-encode,
  `0700` directory / `0600` file, random filename, raw file deleted after review.
- Vision upload: content-type and size validation; image sent to the local Ollama
  service, not to a third party.
- Downloads: fixed allowlist (`app-release.apk` and documented assets), resolved
  path checked with `Path.resolve()` and `is_file()`.
- Research: the backend queries a fixed SearXNG endpoint; no user-controlled URL
  is fetched, so classic SSRF is not reachable. Result URLs are returned as text
  and are not server-fetched.
- Weather: fixed provider base URL from settings.

## 6. Authorization findings

### Confirmed and fixed

- **SEC-001 (High):** `GET /api/v1/feedback` exposed all submissions without
  authentication. Fixed with a session + admin role gate and regression tests
  (anonymous 401, non-admin 403, admin 200). Staging still runs the old build;
  redeploy required.

### Open

- **SEC-003 (Medium):** OAuth `redirect_uri` is not allowlisted server-side.
- **SEC-004 (Medium):** Microsoft email claim trusted without `email_verified`.
- **SEC-005 (Medium):** cookie `Secure` flag depends on the unset production env.
- **SEC-012 (Medium/Low):** in-process rate-limit counters.

## 7. Positive observations

- Admin routes consistently use a server-side role lookup; the feedback route was
  the single exception and is now fixed.
- Error handling does not leak stack traces or SQL details.
- The web app uses a same-origin `/api/v1` proxy, so no credentialed cross-origin
  API calls are needed.
- Secrets are injected via environment/Docker secrets; `.dockerignore` excludes
  `.env` files and local data.

## 8. Verification

```bash
cd backend && ./scripts/check.sh          # ruff, mypy baseline, 310 tests
cd web && npm run typecheck && npm run lint && npm test -- --runInBand
```

Live checks (staging): `/health/live` 200 with HSTS; `/api/v1/resources` 401;
`/api/v1/feedback` returned 200 pre-fix and 401 post-fix (2026-11-10 redeploy).
No intrusive payloads were sent.
