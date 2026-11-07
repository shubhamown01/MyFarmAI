# Production Security Checklist

Status: LIVE gate for any public exposure. Nothing here is certified yet —
every item must be checked with evidence before the E6 refuse-public gate is
lifted. Phase 0 findings that spawned this list are referenced inline.

## 1. Identity & access

- [ ] Authentication/authorization present for **every** API route — today
      there is none (Phase 0). Test evidence: negative tests hitting protected
      routes without a session must return 401/403.
- [ ] Email OTP: rate-limit per-address + per-IP; codes expire; single-use.
- [ ] OAuth (Google, then Microsoft-Entra B1): state param validated; redirect
      URI allowlist exact; OAuth app out of "Testing" mode before public users.
- [ ] Session cookies: Secure, HttpOnly, SameSite, server-side expiry/revocation.

## 2. Network & services

- [ ] Voice service contained: currently unauthenticated on `0.0.0.0:8001`
      (Phase 0) — must be loopback-only or authenticated before any exposure.
- [ ] No service binds `0.0.0.0` without auth (audit compose + services).
- [ ] HTTPS enforced end-to-end on the public host (Pages SSL automatic for
      the proposed frontend; backend TLS at its chosen host).
- [ ] CORS: only the known frontend origins.

## 3. Rate limiting & abuse

- [ ] Rate limiting that **cannot** be bypassed by `X-Forwarded-For` spoofing
      (Phase 0 finding): key on the resolved socket peer or a trusted-proxy
      allowlist, not raw forwarded headers.
- [ ] Cloud AI quota (§10): 20 cloud queries/user/10h enforced **server-side,
      atomically** before any public AI feature ships.
- [ ] Brute-force limits on login/register/OTP endpoints.

## 4. Secrets & sensitive data

- [ ] Secrets only in git-ignored `.env` / provider secret stores (policy:
      `SECURE_CREDENTIAL_MANAGEMENT.md`); repo secret-scan clean at release.
- [ ] **Selfie/face data**: verification artifacts transient only — never
      written to persistent storage, backups, or logs; retention = session
      lifetime. Confirm with a data-flow trace before go-live.
- [ ] Logs contain no passwords, tokens, OTP codes, selfies (existing runner
      guarantee extended to the public host's logs).

## 5. Supply chain & config

- [x] SearXNG **AGPL-3.0** legal review **resolved** — owner-approved
      2026-11-03 via `deployment/LICENSING_DECISIONS.md` **D-2**
      (conditional: SearXNG stays internal; source-link duty recorded in the
      doc if it ever goes public; secret externalized by commit `97f913e`).
- [x] Open-Meteo **non-commercial** licensing **resolved** — owner-approved
      2026-11-03 via `LICENSING_DECISIONS.md` **D-1** (conditional: app
      stays free of subscriptions/ads; CC-BY 4.0 attribution note
      "Weather data by Open-Meteo" — **executed** in both weather UI
      surfaces 2026-11-03, with all web gates green: typecheck, 40/40
      tests, lint, build).
- [ ] No hardcoded secrets anywhere — `infra/searxng/config/settings.yml`
      now reads `${SEARXNG_SECRET}` from the environment (Phase 0 finding
      remediated by commit `97f913e`; compose `.env` file is git-ignored
      and password verified never echoed by runner scripts).
- [ ] Dependency audit clean at release; no model weights in Git.

## 6. Data safety

- [ ] One canonical database (owner decision pending); no dual-DB writes.
- [ ] Backup verified by restore drill (`BACKUP_MYFARMAI.sh --verify`) within
      7 days before go-live.
- [ ] The `7 failing chat tests` on clean DB (Phase 0) fixed and green.
- [ ] Quota-exhaustion degradation paths tested (offline ladder intact).

## 7. Go-live procedure

1. Owner explicitly lifts the E6 public-exposure gate (recorded in
   `CLOUD_DEPLOYMENT_PLAN.md §6`).
2. Every box above checked with a linked test/log/statement.
3. Staging soak on preview deployments → production promote.
