# MyFarmAI — Go-Live Runbook (Public Exposure)

Status: **PROPOSED — not approved, not executed.** Owner decisions in §1 gate
every step that follows. Staging facts below are verified (see
`ACCOUNT_SETUP_LOG.md`, 2026-11-06/07); go-live steps are not.

Verified staging baseline:
- AppSail `myfarmai-backend` (`https://myfarmai-backend-50047414881.development.catalystappsail.in`,
  project `90779000000015001`, app id `90779000000018005`): `/health/live` 200,
  `/health/ready` 200 (Neon `ok`, Ollama `disabled`), POST endpoints work
  through the edge proxy (401 auth gate; chunked-body cap stream-enforced),
  rate limiter engages and ignores spoofed `X-Forwarded-For`, 256 MB memory.
- Neon Postgres (org `org-fragrant-cell-14431918`, project `holy-shadow-54756094`,
  branch `br-young-fire-a1ll0fm0`): 28 tables, alembic head `c8d9e0f1a2b3`.
- Next.js dashboard proxy (`next.config.js`) reaches staging with env-only
  wiring (`MYFARMAI_API_ORIGIN`); login round-trip verified 2026-11-07.

## 1. Owner decisions required (blockers)

| # | Decision | Notes |
|---|---|---|
| D1 | Approve public exposure | Lifts the public-exposure gate (currently staging-only) |
| D2 | Choose the public domain | Registrar ≈ Cloudflare (account live; no payment) |
| D3 | Where the dashboard is hosted | Not yet decided — options: local-only, Vercel free, or owner server. Dashboard deployment is out of scope of this runbook until D3 |
| D4 | Confirm non-commercial use stands | Open-Meteo CC-BY 4.0 attribution already shipped; `LICENSING_DECISIONS.md` D-1 |

## 2. Environment variables to set on AppSail (Configuration → Environment Variables)

Staging currently runs **development-profile defaults** (no `ENVIRONMENT` set).
Production validation (`app/core/config_profiles.py::validate_production_settings`)
enforces the items below once `ENVIRONMENT=production` is present — the app
will refuse to start with healthy config if any is missing, which is the
intended guard.

| Variable | Value | Why |
|---|---|---|
| `ENVIRONMENT` | `production` | Enables prod profile + validation |
| `DATABASE_PATH` | *(keep existing Neon pooler URL — already set, never echoed)* | |
| `OLLAMA_BASE_URL` | *(keep existing `""`)* | Cloud host has no Ollama |
| `ALLOWED_HOSTS` | `<D2 domain>`, `myfarmai-backend-50047414881.development.catalystappsail.in` | TrustedHostMiddleware; localhost-only default rejects all real traffic |
| `CORS_ALLOWED_ORIGINS` | `https://<dashboard origin>` (per D3) | Prod profile default is empty + validation rejects empty |
| `TRUSTED_PROXY_CIDRS` | ⚠ **OPEN ITEM** — see §3 | Do **not** blindly set; empty is fail-safe for spoofing |

No server-side token-signing secret exists (ADR-008: opaque tokens, SHA-256
hashed server-side) — the only rotatable app secrets are OAuth client secrets
(E2, disabled until configured) and the Neon DB password (provider-managed;
rotate in Neon console if ever exposed).

## 3. OPEN ITEM: trusted proxy CIDRs behind AppSail

On staging, the AppSail edge proxy's socket peer is **not** a trusted CIDR, so
XFF is ignored (verified anti-spoof behavior — Phase 0 finding closed). At
go-live:

- If `TRUSTED_PROXY_CIDRS` stays **empty**: spoof-proof stays guaranteed, but
  all clients behind Zoho's edge may share limiter buckets keyed by the proxy
  hop IP(s) — observed staging behavior suggests multiple proxy egress IPs
  (a 14-burst split 5×401 / 9×429, implying ≥2 buckets). Real-user impact:
  occasional collective 429s under load; auth brute-force window is tight
  either way.
- If Zoho publishes AppSail proxy egress ranges, set them in
  `TRUSTED_PROXY_CIDRS` to restore per-real-client keying. **Verify with the
  spoof test** (§5 step 6) after any change — a mis-set CIDR re-opens the
  Phase 0 bypass.
- Recommendation: ship empty, measure, only widen if collective 429s become a
  real user complaint.

## 4. Procedure (after D1–D4 approvals)

1. **DNS (Cloudflare)**: create A/CNAME record for D2 domain → AppSail
   app URL. Confirm proxy/TLS mode (AppSail terminates TLS already;
   Cloudflare proxying is optional — record the choice here when made).
2. **Custom domain on Zoho**: bind the domain to the AppSail app (console →
   AppSail → Domains). Verify Zoho's cert issuance.
3. **Set env vars** (§2 table) on AppSail; save → app restarts.
4. **Verify** (§5). If startup fails, validation errors list the exact missing
   variable — fix and let it restart.
5. **Execute `PRODUCTION_SECURITY_CHECKLIST.md`** — all sections; the checklist
   is the acceptance record, not this runbook.
6. **Smoke-test with a real signup** through the dashboard (first real user).

Non-goals during go-live: schema changes, voice service exposure (remains
uncontained/local-only), Ollama exposure, any cloud-AI provider enablement
(`cloud_ai_enabled` stays off until a provider is approved; §10 quota counter
stays flag-off).

## 5. Post-change verification (paste results into `ACCOUNT_SETUP_LOG.md`)

1. `GET /health/live` and `/health/ready` → 200 with `database: ok`.
2. Wrong-credential `POST /api/v1/auth/login` → 401 `INVALID_CREDENTIALS`.
3. Burst ≥11 logins → 429s present; spoofed-XFF attempts → still 429.
4. `GET /` from the real domain → 200 (allowed_hosts correct; a 400 means the
   domain listing in `ALLOWED_HOSTS` is wrong).
5. Frontend origin page fetches API through its proxy → 200s (no CORS errors
   in the browser console — CORS origin misconfiguration shows as browser
   console errors even when curl works).
6. Repeat the staged spoof test from 2026-11-07 to confirm anti-spoof holds
   with the new `TRUSTED_PROXY_CIDRS` value (if set).
7. Token lifecycle: register → verify OTP → login → refresh → logout; refresh
   token single-use rotation observed in audit rows.

## 6. Rollback

Set `ENVIRONMENT` back to development defaults (remove the production-only
vars), save → restart, and repoint DNS back to staging-only access. No
destructive step exists in this runbook; the risky directions are all
"expose more", so rollback is always "expose less".
