# MyFarmAI — Public Deployment Security Checklist

Created 2026-11-08 from the security-engineer review of the public Slate +
AppSail exposure (session `ses_e46e85410ffeI05Fj8JY7nn39k`, verdict:
**PASS with conditions**). Master prompt: `docs/deployment/PUBLIC_DEPLOYMENT_PLAN.md`.

Live endpoints: web `https://myfarmai-web-zwpytbwu.onslate.in`
(same-origin `/api/v1` proxy) → backend
`https://myfarmai-backend-50047414881.development.catalystappsail.in` → Neon Postgres.

## Status legend: [x] satisfied (evidence) · [!] condition on owner action · [ ] pending

### Transport & session
- [x] HTTPS everywhere: provider-managed certs on both domains; no app HTTP listener publicly.
- [!] Cookie `Secure` flag: currently **off** because `ENVIRONMENT=production` is not yet set on AppSail (`auth.py:156,177,353,475` use `secure=environment=="production"`; MED). Flips on automatically with the P3 prod-env change. Mitigations meanwhile: httponly + samesite=lax + provider HTTPS.
- [x] Tokens never in web storage: grep shows no localStorage/sessionStorage of auth tokens (`useChat.ts` stores chat transcript only); session is httponly cookie.
- [x] Same-origin proxy: `/api/v1/:path*` rewrite only (`next.config.js`), no open-proxy behavior (review item 2).

### Authentication & authorization
- [x] Login → httponly session cookie (`auth.py`; `_login_response` places nothing secret in body for web flows; Android uses Bearer).
- [x] Logout clears cookie (fix `71737f5`, verified live on both domains: `set-cookie: myfarmai_session=""; Max-Age=0` in the 204).
- [x] Clean error contract: 401 `{error_code: NOT_AUTHENTICATED}`, 422 field errors — no stack traces (live-verified).
- [x] Rate limiting: general limiter (60 req/60 s, `factory.py:209-225`) + stricter auth prefix limiter **10 req/60 s per IP** (`factory.py:226-233`) covering `/auth/login` and `/auth/register/*`; spoof-resistant client IP (`core/client_ip.py` + `trusted_proxy_cidrs`).
- [x] CSRF/origin enforcement for cookie-authenticated state changes (`CSRFOriginMiddleware`, `factory.py:236-241`).
- [!] Registration OTP **dev-mode**: codes go to container log/outbox only, never emailed (owner-approved 2026-11-01). Realistic risk now LOW (only owner reads AppSail logs), MED-MED+ once testers expect real mail — requires real SMTP before any production launch. Arbitrary-email account creation allowed during testing (synthetic accounts only).

### CORS & network
- [x] No wildcard `Access-Control-Allow-Origin` with credentials (live OPTIONS check: no ACAO header emitted for the Slate origin — safe because the web app uses the same-origin proxy, not cross-origin calls).
- [!] **P3 prod-env flip pending (owner console)**: set `ENVIRONMENT=production`, `ALLOWED_HOSTS` (backend + slate domains), `CORS_ALLOWED_ORIGINS` (Slate origin) per `GO_LIVE_RUNBOOK.md`; production validation refuses to boot without CORS explicitly set (`config.py:355-358`). Re-verify cookie Secure + CORS headers after the flip.
- [x] No public DB ports: Neon is reached only via the backend's env config; no direct DB exposure.
- [x] Secrets not in repo: `.dockerignore` excludes `.env`, `.env.*`, `data/`; AppSail env holds connection strings; git secret-scanned every commit.

### Platform headers (informational)
- Catalyst platform headers (`X-Catalyst-Function-Name`, etc.) on backend responses — not app-controlled, LOW, non-actionable.

### Pending items (owner / later phases)
1. `ENVIRONMENT=production` flip + CORS/ALLOWED_HOSTS (P3) → then re-verify items marked `!`.
2. Real SMTP for OTP (before any production/external-mailer launch).
3. Privacy policy + terms page (owner-approved text).
4. Tester feedback endpoint (DB backup + migration approval).
5. APK public hosting decision (B-3) — candidate: AppSail static route.
