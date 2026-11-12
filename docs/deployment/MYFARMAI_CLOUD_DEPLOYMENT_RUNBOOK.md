# MyFarmAI — Cloud Deployment Runbook (zero-cost, no laptop dependency)

Status: **PROPOSED — NOT AUTHORISED.** This document describes what *would* be
deployed and how. Nothing in it has been executed. It stops at the owner approval
gate defined in §1 and §7.

- Companion audit: [`MYFARMAI_CLOUD_PROVIDER_AUDIT.md`](MYFARMAI_CLOUD_PROVIDER_AUDIT.md)
- Existing command-level deploy notes: [`DEPLOYMENT_RUNBOOK.md`](DEPLOYMENT_RUNBOOK.md)
- Binding cost rules: [`CLOUD_COST_AND_QUOTA_POLICY.md`](CLOUD_COST_AND_QUOTA_POLICY.md)
- Prepared: 2026-11-12

## 1. Approval gate

Do **not** start §4 until all of the following are recorded in writing:

| Gate | Owner action | Current state |
|---|---|---|
| G1 | AppSail memory confirmed (2048 MB → 256 MB if allowed) and current usage checked | **BLOCKED** — console only |
| G2 | Confirm AWS remains ruled out, or supersede the 2026-11-03 ruling | **BLOCKED** — decision |
| G3 | SMTP choice + credentials supplied through the platform secret store | **BLOCKED** — credential |
| G4 | AI path chosen (Gemini free tier or stay disabled) | **BLOCKED** — decision |
| G5 | Off-site backup destination approved | **BLOCKED** — decision |
| G6 | Slate redeploy approved (bundle stale since 2026-11-08) | **BLOCKED** — publishing |
| G7 | HEAD-fix deploy approved (`backend/app/api/v1/downloads.py` is uncommitted) | **BLOCKED** — publishing |

Creating a resource, changing DNS, enabling billing, migrating data, or publishing a
release requires a separate, explicit instruction per action. Approval of this runbook
is not approval to execute it.

## 2. Target resource list (exact)

| # | Provider | Resource | Identifier / spec | Region | Cost |
|---|---|---|---|---|---|
| R1 | Catalyst | Project `Project-Rainfall` | id `90779000000015001`, org `60094539808`, env `Development` | IN (Asia/Kolkata) | ₹0 |
| R2 | Catalyst | AppSail `myfarmai-backend` | id `90779000000018005`, custom runtime, **2048 MB → target 256 MB**, disk 256 MB, port 8000 | IN | ₹0 within 900 GB-min/month |
| R3 | Catalyst | Slate `myfarmai-web` | id `37777000000005001`, Node 22, `framework: nextjs`, root `./`, build `.next` | IN | ₹0 within 300k req/month |
| R4 | Neon | Project + database `neondb` | org `org-fragrant-cell-14431918`, host `ep-calm-resonance-a1wkl7mg-pooler.ap-southeast-1.aws.neon.tech` | `ap-southeast-1` | ₹0 (100 CU-h, 1 GB) |
| R5 | Cloudflare | R2 bucket (optional) | one bucket for backups/APK, if enablement needs no card | auto | ₹0 (10 GB-month) |
| R6 | GitHub | Release assets | tag `v1.0.0`, APK `app-release.apk` (65 MB) | — | ₹0 |
| R7 | Google AI Studio | API key for Gemini free tier (optional) | key stored only in platform secrets | — | ₹0 within free tier |
| R8 | Gmail or Brevo | SMTP relay (one of) | `smtp.gmail.com:587` or Brevo relay | — | ₹0 |

Not to be created: any AWS or GCP resource, any billing account, any paid plan, any
custom domain.

## 3. Environment variables (names only — never commit values)

### Backend (AppSail → Configuration → Environment Variables)

| Variable | Required | Notes |
|---|---|---|
| `ENVIRONMENT` | yes | `production` (enables the production validation gates) |
| `DATABASE_PATH` | yes | full `postgresql://…` URL. **Currently holds a live password in plaintext** — preferred long-term fix is a platform secret reference; `DATABASE_PASSWORD_FILE` exists but file mounts on AppSail are **UNVERIFIED** |
| `ALLOWED_HOSTS` | yes | backend host + `localhost` (TrustedHostMiddleware) |
| `CORS_ALLOWED_ORIGINS` | yes | `https://myfarmai-web-zwpytbwu.onslate.in` |
| `TRUSTED_PROXY_CIDRS` | yes | required by production validation; must match the platform's actual proxy ranges — get these from Catalyst, do not guess |
| `PUBLIC_DIR` | optional | `/app/public` when the APK is baked into the image |
| `SELFIE_STORAGE_DIR` | optional | defaults to `/data/myfarmai-selfies`; on AppSail this is **not durable** — selfies should stay disabled or move to R2 |
| `EMAIL_DELIVERY_MODE` | yes | must be `smtp` in production |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`, `SMTP_STARTTLS` | yes (SMTP) | production validation refuses to start without host + from |
| `OLLAMA_BASE_URL` | yes | empty string disables the local path (current state) |
| `CLOUD_AI_ENABLED`, `CLOUD_AI_QUOTA_LIMIT`, `CLOUD_AI_QUOTA_WINDOW_HOURS` | optional | quota counter is already implemented and flag-off |
| `SEARXNG_BASE_URL` | optional | empty disables research; no SearXNG instance is deployed |
| `LOG_LEVEL` | optional | `INFO` |

### Web (Slate build-time / runtime)

| Variable | Required | Notes |
|---|---|---|
| `MYFARMAI_API_ORIGIN` | yes | server-side rewrite target; must be the exact backend origin (no `/api/v1` suffix) |

### Android (build time only)

| Variable | Required | Notes |
|---|---|---|
| `EXPO_PUBLIC_API_BASE_URL` | yes | real backend origin; the default `api.myfarmai.example.com` is a placeholder — a build with it is unusable |

Rule: values are entered by the owner in the provider console. They must never appear
in this repository, a commit, a log, or a chat transcript. If any value was ever
exposed in output, rotate it (the Neon password is the known case — see §9).

## 4. Deployment procedure (only after §1 approval)

### 4.1 Backend image

Reuse [`DEPLOYMENT_RUNBOOK.md`](DEPLOYMENT_RUNBOOK.md) §"Backend deploy" without
change: build `linux/amd64`, add the optional public-APK layer, smoke-validate
`Settings(...).validate_for_environment() == []` locally, then deploy detached via
`zcatalyst-cli deploy appsail` with a 4500 s timeout.

Before building, confirm the working tree is intentional: `backend/app/api/v1/downloads.py`
and `backend/tests/test_downloads.py` contain the **undeployed HEAD fix**; include or
exclude it deliberately, and say which in the deploy record.

### 4.2 Web

1. `cd web && npm ci && npm run typecheck && npm run lint && npm run build`
2. `cd ../deploy/catalyst-staging && npx -y zcatalyst-cli deploy slate myfarmai-web`
3. Confirm the bundle changed: Catalyst MCP `Get_Slate_App` → `modified_time` must be
   newer than 2026-11-08, and the HTML must contain a marker from the current build.

### 4.3 Database

No schema change is part of this runbook. If a migration is later required:
`alembic upgrade head` runs inside the container against `DATABASE_PATH`; never
`create_all`, never a manual `ALTER` against the live database.

### 4.4 APK

Build with the release signing config as documented in
`docs/testing/ANDROID_TESTING_MASTER_PLAN.md`, then publish to the GitHub Release and
(optionally) copy into the backend image's `public/` layer. Both copies must be
byte-identical — verify with `sha256sum`.

## 5. Verification checklist (run after any deploy; record real output)

| # | Check | Command | Expected |
|---|---|---|---|
| V1 | Liveness | `curl -sS -m 60 https://<backend>/health/live` | 200, `"status":"ok"` |
| V2 | Readiness | `curl -sS -m 60 https://<backend>/health/ready` | 200, `"database":"ok"`, `"ollama":"disabled"` |
| V3 | Web root | `curl -sS -m 60 https://<web>/` | 200, `<title>Home · MyFarmAI</title>` |
| V4 | Web→API rewrite | `curl -sS -m 60 https://<web>/api/v1/health/...` | proxied response, not 404 from Slate |
| V5 | APK GET | `curl -sS -m 120 -r 0-15 -D - -o /tmp/apk.bin https://<backend>/api/v1/downloads/app-release.apk` | 206, body starts `PK\x03\x04` |
| V6 | APK HEAD | `curl -sS -m 60 -I https://<backend>/api/v1/downloads/app-release.apk` | 200 with `Content-Length: <full size>` and **no body** (fails today) |
| V7 | APK integrity | `sha256sum` of downloaded APK vs the release asset | equal |
| V8 | Session cookie flags | `curl -sS -i -X POST https://<backend>/api/v1/auth/logout` | 204, `myfarmai_session=…; Secure` |
| V9 | Auth rejects bad creds | `POST /api/v1/auth/login` with wrong creds | 401 `INVALID_CREDENTIALS` |
| V10 | OTP delivery | request a login code for a real mailbox | email arrives, code accepted once |
| V11 | AI (if enabled) | `POST /api/v1/chat` as a test user | 200 with an answer; quota counter increments |
| V12 | Weather | `GET /api/v1/weather/current` | 200 with real data (or a documented provider error) |
| V13 | Rate limit not bypassable | send `X-Forwarded-For: 1.2.3.4` from an untrusted path | limiter ignores the spoofed header |
| V14 | Slate freshness | fetch `/auth/login`, inspect build hash/asset names | matches the build just uploaded |

V6 is the only check with a **known current failure**; it is evidence that the working
tree fix is not deployed. Only V1–V3 and V5 were executed on 2026-11-12 — V4, V7–V14
are **NOT TESTED** and must be run before any go-live claim.

## 6. SMTP bring-up (configuration only — no code change)

1. Owner creates the credential: Gmail app password (2-Step Verification required) or
   a Brevo SMTP key.
2. Set `EMAIL_DELIVERY_MODE=smtp`, `SMTP_HOST`, `SMTP_PORT=587`, `SMTP_USER`,
   `SMTP_PASSWORD`, `SMTP_FROM`, `SMTP_STARTTLS=true` in AppSail.
3. Redeploy or restart so the production config validator passes.
4. Run V10 from a mailbox the owner controls. If no mail arrives, check AppSail's
   outbound reachability on port 587 — this is the unverified risk that made Render
   unsuitable; Catalyst's behaviour is unknown and must be measured, not assumed.

Rollback: clear the SMTP variables and switch `EMAIL_DELIVERY_MODE` back to the
previous value. Registration then returns to dead-on-arrival rather than failing at
startup, which is the current live behaviour.

## 7. AI bring-up (requires code — PROPOSED, not implemented)

`backend/app/ai/gateway.py` defines `AIGateway` (`chat`, `health_check`,
`model_name`) with a single `OllamaGateway` implementation. A free-tier hosted
provider would be a second adapter:

1. New module implementing `AIGateway` against the provider's OpenAI-compatible
   endpoint; map provider errors onto `AITimeoutError`, `AIConnectionError`,
   `AIModelNotFoundError`, `AIBusyError`.
2. Select it from configuration (provider + key + model names); no domain module
   changes, because chat/research depend on the protocol only.
3. Turn on `CLOUD_AI_ENABLED` and keep the existing per-user quota (default 20 per
   10 h) as the cost brake.
4. Tests: adapter error mapping + quota gating, plus one failure-path test proving a
   provider outage returns a clean error rather than a 500.

This is the most expensive item in the plan and is **not required** to have a working
product: chat/research stay disabled, as they are today. Do it only after D4.

## 8. Backup, migration, and restore rehearsal

Current gap: backups exist only for the local Compose database
([`BACKUP_AND_RESTORE.md`](BACKUP_AND_RESTORE.md)); the live Neon database has no
verified off-site backup, and the host disk is a single point of failure.

Procedure (once G5 approves a destination):

```bash
# 1. Dump the live database without printing the secret
docker exec -e PGURL="$NEON_DATABASE_URL" myfarmai-postgres \
  pg_dump "$PGURL" --format=custom --no-owner --no-acl \
  > /data/MyFarmAI-backups/neon-$(date +%F-%H%M).dump

# 2. Restore into a throwaway Neon branch (never into production first)
docker exec -i -e PGURL="$BRANCH_DATABASE_URL" myfarmai-postgres \
  pg_restore --clean --if-exists --no-owner --no-acl -d "$PGURL" \
  < /data/MyFarmAI-backups/neon-<timestamp>.dump

# 3. Verify row counts against production for the tables that matter
#    (users, sessions, farms, plots, crop_plans, chat history)
```

Rules: the dump contains personal data — encrypt or restrict it, never commit it, and
never place it in a public bucket. A restore is only "verified" after §5 V1–V3 pass
against the restored branch. Migration off Neon (if ever needed) is the same dump into
any standard Postgres plus `alembic upgrade head`; no proprietary export is involved.

## 9. Secret handling and known exposure

- The AppSail `DATABASE_PATH` value contains the Neon password in plaintext.
  It appeared once in tool output during this audit. **Rotate the Neon role password**
  and update the env var; do not copy the old value anywhere.
- `infra/searxng/config/settings.yml` still carries a hardcoded secret (Phase 0
  finding). SearXNG is not deployed, but the secret must be rotated before it ever is.
- The repository rule stands: no secret in Git, no secret in a report, no secret in a
  console log. This runbook lists variable **names** only.

## 10. Monitoring and quota watch (manual — no free APM)

| What | Where | Threshold that triggers action |
|---|---|---|
| AppSail runtime | Catalyst console usage/billing | > 70% of 900 GB-minutes, or any ₹ amount on the bill |
| AppSail memory | Catalyst console | confirm 2048 vs 256 MB; reduce if it is a real allocation |
| Slate requests/storage | Catalyst console | > 70% of 300k requests or 500 MB |
| Neon compute/storage | Neon console | > 70% of 100 CU-hours or 1 GB |
| API errors | `/health/ready` + platform logs | readiness non-200 for 5 min |
| Certificate/hostname | both public URLs | TLS error or hostname mismatch |

If the AppSail bill shows any charge, the graceful-degradation ladder in
[`CLOUD_COST_AND_QUOTA_POLICY.md`](CLOUD_COST_AND_QUOTA_POLICY.md) applies: reduce
memory, then reduce uptime, then move the API — do not enable billing to "fix" it.

## 11. Rollback

| Layer | Rollback |
|---|---|
| AppSail | redeploy the previous image tag (`docker save` archive retained locally); env vars are unchanged by an image rollback |
| Slate | redeploy the previous build artifact; keep the prior `.next` output until the new one is verified |
| Database schema | Alembic `downgrade -1` only on a rehearsed branch; production downgrade requires a fresh dump first |
| Config | every change is a variable edit; record old values in the owner's secret store before changing |
| DNS | none in scope (no domain) |

## 12. Owner-only actions (this agent cannot perform these)

1. Read the Catalyst console billing/usage page and report the numbers (G1).
2. Decide AWS (G2), AI (G4), backups (G5).
3. Create/enter the SMTP credential (G3).
4. Approve and trigger any deploy (G6, G7) — including the detached AppSail build.
5. Rotate the Neon password and update `DATABASE_PATH`.
6. Purchase any domain (not recommended; not required).

## 13. Status summary

| Item | Status |
|---|---|
| Provider audit | **COMPLETE** — see audit doc |
| Resource list | **PROPOSED** — §2, unapproved |
| Env-var inventory | **COMPLETE** — names only, verified against `config.py` |
| Deploy procedure | **COMPLETE** — reuses the verified existing runbook |
| Live verification | **PARTIAL** — V1, V2, V3, V5 verified 2026-11-12; V6 observed failing; V4, V7–V14 NOT TESTED |
| Quota evidence | **BLOCKED** — no usage/billing tooling |
| Execution | **NOT AUTHORISED** — stop at §1 |
