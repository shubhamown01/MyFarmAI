# MyFarmAI — Post-Audit Stage 2: Production Risk Resolution

Status: **COMPLETE for read-only investigation; PROPOSED for every change.**
No deployment, DNS change, billing activation, credential rotation, memory change,
bucket creation, or data migration was performed. No password value was read,
copied, logged, or written.

- Date: **2026-11-12**
- Repository: `/data/MyFarmAI`, branch `phase-01-foundation`, HEAD `6393c2b`
- Selected architecture (unchanged): Catalyst Slate (web) + Catalyst AppSail
  (FastAPI) + Neon PostgreSQL. AWS stays rejected. R2 conditional.
- Method: Catalyst MCP read-only calls, logged-out official-doc fetches, live
  read-only HTTP probes, local Docker image inspection and a memory benchmark.

## 0. Executive summary

| # | Finding | Severity | Status |
|---|---|---|---|
| F1 | AppSail bills **GB-minutes = memory GB × minutes**; the 900 GB-min/month free allowance is **450 minutes at 2 GB**, not a full month | Critical (financial) | **BLOCKED** — plan/usage only visible in the console |
| F2 | The live backend image is **older than HEAD**: no SMTP adapter, no OTP redaction, no HEAD route, no version fix | Critical | CONFIRMED |
| F3 | Because of F2, the live production backend **logs full OTP codes and never delivers them** — registration is dead and any log reader could take over accounts | Critical (security) | CONFIRMED |
| F4 | Slate serves a **stale bundle** (2026-11-08) that does not match the local build | High | CONFIRMED |
| F5 | Neon credential lives **only** in AppSail config; repo, git history, image layers and temp files are clean | High | CONFIRMED (rotation still required) |
| F6 | 256 MB RAM is **plausible** (measured 146–149 MiB idle) but not proven under Postgres + image handling | Medium | PARTIAL |
| F7 | SMTP needs **no code change** — the adapter exists on HEAD; it is missing only from the deployed image | Medium | CONFIRMED |
| F8 | Neon Free PITR is **6 hours**; no off-site backup exists | High | CONFIRMED |
| F9 | Cloudflare R2 requires an **R2 subscription checkout** — a billing surface, so policy-BLOCKED until the owner approves | Medium | CONFIRMED |
| F10 | `/openapi.json` is public (53 paths) while `/docs` and `/redoc` are 404 | Low | CONFIRMED |
| F11 | Release tag `v1.0.0` is **22 commits behind HEAD**; deployed artifacts do not correspond to the tag | Medium | CONFIRMED |

## 1. Task 1 — AppSail quota investigation

### 1.1 What the 900 GB-minute allowance measures

Official pricing-calculation doc (fetched 2026-11-12) states AppSail's unit is
**instances per minute**, priced by allocated memory:

| Memory | USD per minute | GB-minutes consumed per minute |
|---|---|---|
| 256 MB | 0.000325 | 0.25 |
| 512 MB | 0.00065 | 0.5 |
| 1 GB | 0.0013 | 1 |
| 2 GB | 0.0026 | 2 |

The doc also states the free-tier GB-second/GB-minute limits **"are not
cumulative"** and the free-tier page states allowances are **account-wide** and
**refreshed monthly**, not per project.

Therefore, with a 900 GB-minute monthly allowance:

| Allocated memory | Continuous runtime covered by the free tier |
|---|---|
| **2048 MB (current)** | **450 min = 7.5 hours/month** |
| 1024 MB | 900 min = 15 hours/month |
| 512 MB | 1,800 min = 30 hours/month |
| 256 MB | 3,600 min = 60 hours/month |

**No configuration fits 24/7 within the free allowance.** A full always-on month
consumes 86,400 GB-minutes at 2 GB (96× the allowance) or 10,800 at 256 MB (12×).

### 1.2 What happens after the allowance is exhausted

- Pay-as-you-go billing starts for that resource only, with a **minimum bill of
  USD 5 (~₹300–420) per project per month** once any resource exceeds its limit
  (official pay-as-you-go doc, fetched 2026-11-12).
- First-time accounts receive a **one-time USD 250 credit** that is consumed after
  the free tier (official billing intro). The pricing page advertises a 180-day
  trial. The account's remaining credit is **not visible through the Catalyst MCP**
  and must be read in the console.
- At list price, an always-on 2 GB instance costs **$0.0026 × 43,200 =
  $112.32/month**, i.e. the $250 credit would last roughly two months if nothing
  else is consumed. An always-on 256 MB instance costs **$14.04/month**.
- Whether the service stops, throttles, or keeps billing when no payment method is
  attached is **not documented** and was not tested. Treat "no card on file" as
  *no billing guarantee*, not as a spending cap.

### 1.3 Idle behaviour, restarts, availability

- AppSail docs say Catalyst "spawns server instances … as needed, and scales them
  up or down based on the traffic". This describes elasticity, **not** a documented
  scale-to-zero policy; no idle timeout, no minimum instance count, and no
  post-quota behaviour are stated anywhere in the AppSail documentation fetched.
- Live evidence is suggestive only: the first `/health/live` request after a quiet
  period took **6.61 s**, the next readiness call **1.79 s**. That is consistent
  with a cold instance, but it is **not proof**.
- **UNVERIFIED:** idle scale-to-zero, restart-on-quota-exhaustion, and what the
  user-facing failure looks like.

### 1.4 Is 256 MB enough? (local benchmark, real image)

Ran the deployed image `myfarmai-backend:prod-20261110` locally with SQLite,
`ENVIRONMENT=development`, `OLLAMA_BASE_URL=`:

| Measurement | RSS |
|---|---|
| Idle after startup (uvicorn + app + Pillow + libs) | **146.2 MiB** |
| After 5 requests to `/health/live` | **148.6 MiB** |

Interpretation: 256 MB leaves ~105 MB headroom for the base process. That is
plausible for low traffic, but **not proven**, because the benchmark did not cover:

- asyncpg connection pool + Alembic startup against Neon,
- selfie upload decode/re-encode (Pillow peak memory scales with pixel dimensions),
- concurrent requests and the AI queue.

Recommendation: **do not change memory yet.** If the console confirms 2048 MB is a
real allocation, 512 MB is the safer first step (30 h/month free, more room for
image handling); 256 MB only after a Postgres-backed load test.

### 1.5 Owner console instructions (exact)

Record the **numbers only**; do not paste URLs, keys, or credentials.

1. Open <https://console.catalyst.zoho.com> → organisation `60094539808` →
   project **Project-Rainfall**.
2. **Billing**: *Billing → Usage / Reports* (or *Billing Settings*). Capture:
   - AppSail **GB-minutes consumed this cycle**,
   - the cycle start/end dates and the free-tier bar,
   - current **credit balance** and any **amount due**,
   - whether a payment method is attached.
3. **AppSail → myfarmai-backend → Configurations → App Execution Settings**:
   capture allocated **memory (MB)** and **disk**, and whether the field shows a
   value or a ceiling.
4. **AppSail → myfarmai-backend → Instances**: capture how many instances are
   running now and whether any "always on"/minimum-instance option exists.
5. **Zoho Store → Billing** if the console links there: capture invoice status.
6. Report back: five numbers (GB-min, memory, credits, amount due, instances) and
   nothing else. This resolves F1 and unblocks any memory change.

## 2. Task 2 — Neon credential remediation

### 2.1 Exposure inventory (no values read)

Searched for the Neon password pattern without printing matches:

| Location | Result |
|---|---|
| Tracked files (`git grep`) | **0 files** |
| Git history (`git log -S` on the pattern prefix) | **0 commits** |
| Entire working tree incl. untracked and all `.env*` files | **0 files** |
| Docker image layers (`docker history`, current prod image) | **0 layers** |
| Local deploy/temp artifacts (`/tmp/opencode`) | **0 files** |

**Only reference:** the AppSail environment variable `DATABASE_PATH` (value visible
in the Catalyst console and in console/API responses to project collaborators), and
the Neon console itself (source of truth). `DATABASE_PASSWORD_FILE` exists in
`backend/app/core/config.py` as a secret-file option, but AppSail documents env vars
only — no file-secret mount is documented, so it is **not** a viable alternative
today. **UNVERIFIED** whether AppSail supports mounted secret files.

Note: the value appeared once in tool output during the prior audit. Rotation is
required regardless of the clean repository, because the exposure was to a screen
transcript, not to Git.

### 2.2 Rotation procedure (owner-executed; agent must not see the value)

1. **Create the replacement** in Neon: Console → project → **Roles** → role
   `neondb_owner` → *Reset password*. Copy the new value directly into a password
   manager. Never paste it into chat, a ticket, a doc, or a commit.
2. **Update AppSail**: *Project-Rainfall → AppSail → myfarmai-backend →
   Configurations → Environment Variables* → edit `DATABASE_PATH`, replacing only
   the password segment (URL-encode `@ : / ? # [ ] %` if present). Save.
3. **Restart** the AppSail service (save/redeploy or the console restart action) so
   the new env value is picked up — env changes are applied at instance spawn.
4. **Verify connectivity**: `GET /health/ready` must return 200 with
   `"database":"ok"`. If it returns 500/503, read the platform log line from
   `factory.py` ("Database manager initialized with postgresql://host/db") — it is
   redacted, so it is safe to read.
5. **Functional check**: `POST /api/v1/auth/login` with a known-good test account →
   expect 200/session cookie, not 500. If no test account exists, use a fresh OTP
   registration once SMTP is live (Task 4), not before.
6. **Retire the old credential**: Neon keeps only the current password per role, so
   the reset already invalidates the old one. Confirm no other consumer breaks:
   search local `.env` files and compose configs for the **hostname** (not the
   password) and confirm they use the local Compose database, not Neon.
7. **Re-verify hygiene**: file names only — `git grep -lE 'npg_[A-Za-z0-9]{8,}'`
   (expect none), `git log -S'npg_' | wc -l` (expect 0), and confirm the platform
   log shows no DSN with a password. `factory.py` already strips credentials before
   logging; do not add logging that prints the URL.

Expected impact: a few seconds of failed connections during instance restart.
No data change. No migration.

## 3. Task 3 — Existing deployment verification

### 3.1 Exact deployed backend source (fingerprint)

| Property | Evidence |
|---|---|
| Image | `myfarmai-backend:prod-20261110` (id `6aa7a79655ae`), built **2026-11-10 18:09:31Z** = 23:39 IST |
| AppSail deploy | **2026-11-10 23:58 IST** (Catalyst MCP `Get_AppSail`) |
| Base commit | **`0a75e26`** (2026-11-10 22:30 IST) — file-by-file diff of `/app/app` matched except two files |
| Uncommitted delta | `api/v1/feedback.py` (admin gate) and `api/v1/verification.py` (dimension gate before decode) — the pre-commit state of `f9c5eeb` |
| Excluded from image | HEAD route fix (`downloads.py` is `@router.get` only), `46defc4` version fix, `903a418` OTP redaction, `be2c6ed` SMTP adapter |

Proof of the version gap: the image hardcodes `app_version = "0.1.0"` and the live
`GET /` returns `{"project":"My Farm AI","version":"0.1.0","status":"running"}` —
`46defc4` (2026-11-11 09:52) is not deployed.

### 3.2 Runtime environment baked into the image

`docker inspect` of the deployed image shows these are **image ENV**, not console
variables: `ENVIRONMENT=production`, `ALLOWED_HOSTS=myfarmai-backend-…catalystappsail.in,localhost`,
`CORS_ALLOWED_ORIGINS=https://myfarmai-web-zwpytbwu.onslate.in`,
`TRUSTED_PROXY_CIDRS=10.0.0.0/8,172.16.0.0/12,192.168.0.0/16`, `PUBLIC_DIR=/app/public`.
Only `DATABASE_PATH` and `OLLAMA_BASE_URL` come from the console.

Consequence: the earlier audit's statement that "production refuses to start without
SMTP" is true for **HEAD**, not for the deployed image — the startup SMTP gate
landed in `be2c6ed`, which is not deployed. **Correction recorded.**

### 3.3 Slate bundle compatibility

- Catalyst MCP: `myfarmai-web`, `app_type cli`, Node 22, `modified_time`
  **2026-11-08 01:36**.
- Local build `web/.next/BUILD_ID` = `ZRPkfioLGrLtf5GbxRdQv`, built 2026-11-11 14:27.
- Live HTML references chunks `255-e8efc13ba0f4f3b0.js`, `4bd1b696-21f374d1156f834a.js`;
  the local build contains `255-b1e2483a7e02feee.js`, `4bd1b696-c023c6e3521b1417.js`.
  Shared chunks (`43-…`, `461-…`, `583-…`) match, which is normal: hashes only change
  when content changes.
- **Verdict: the deployed web bundle is not the local build and predates the
  2026-11-11 web fixes** (`d15e1b0`, `f65269c`, `e8b1502`).

### 3.4 Live endpoint matrix (2026-11-12)

| Check | Result | Verdict |
|---|---|---|
| `GET /health/live` | 200 `{"status":"ok",…}` (6.61 s cold) | PASS |
| `GET /health/ready` | 200 `{"database":"ok","ollama":"disabled"}` | PASS |
| `GET /api/v1/downloads/app-release.apk` (Range 0-15) | 206, `application/octet-stream`, `PK\x03\x04` | PASS |
| `HEAD /api/v1/downloads/app-release.apk` | 200 with **31-byte JSON body** | **FAIL — fix not deployed** |
| Web→API rewrite `GET https://<slate>/api/v1/resources/categories` | 401 JSON `NOT_AUTHENTICATED`, backend `x-request-id` present | PASS (proxy works) |
| `GET /api/v1/auth/me` unauthenticated | 401 `NOT_AUTHENTICATED` | PASS |
| `POST /api/v1/auth/login` wrong password | 401 `INVALID_CREDENTIALS` | PASS |
| `POST /api/v1/auth/login` reserved-TLD email | 422 email-validator rejection | PASS (validation live) |
| HSTS / `nosniff` / `X-Frame-Options` on API | `max-age=64072000; includeSubDomains; preload`, `nosniff`, `DENY` | PASS |
| `GET /openapi.json` | 200, 82,112 bytes, **53 paths** | Info exposure |
| `GET /docs`, `/redoc` | 404 | PASS |

Auth compatibility conclusion: the live API speaks the same `/api/v1` contract the
Android client and web app expect (`login`, `auth/me`, refresh, downloads all
present). The only compatibility defect is the undeployed HEAD route.

## 4. Task 4 — SMTP and registration readiness

### 4.1 Exact remaining changes

`backend/app/services/delivery.py` on HEAD already contains a complete
`SmtpEmailDelivery` (stdlib `smtplib`, STARTTLS, `asyncio.to_thread`, generic
failure logging, no credential/OTP leakage) and `get_email_delivery()` selects it
when `email_delivery_mode='smtp'`. The production validator already refuses to
start without `smtp_host`/`smtp_from`.

**Therefore: zero application-code changes are required.** The blocker is that the
**deployed image predates the adapter**. Remaining work:

1. Rebuild the backend image from current HEAD (also delivers the OTP redaction,
   version fix and HEAD route).
2. Set the SMTP variables (names in §4.2) in AppSail.
3. Deploy and run the OTP delivery test.

### 4.2 Variables required

`EMAIL_DELIVERY_MODE=smtp`, `SMTP_HOST`, `SMTP_PORT` (587), `SMTP_USER`,
`SMTP_PASSWORD`, `SMTP_FROM`, `SMTP_STARTTLS=true` (optional:
`SMTP_TIMEOUT_SECONDS`). Values are entered by the owner only.

### 4.3 Provider recommendation (eligibility verified 2026-11-12)

| Provider | Free allowance | Card | Fit | Evidence |
|---|---|---|---|---|
| **Brevo Free** | **300 emails/day**, resets daily | **No card** required for the free plan | **Recommended** — transactional relay, SMTP + API, sender verification only | Brevo Help Center FAQ + Brevo pricing (fetched 2026-11-12) |
| Gmail app password | Provider does not publish a consumer SMTP quota on the app-password page; commonly cited ~500 recipients/day (**UNVERIFIED**) | No card (existing account) | Acceptable fallback for owner testing only; requires 2-Step Verification and revokes app passwords on password change | Google Account Help (fetched 2026-11-12) |
| Catalyst Mail | 100 emails/month | No card | Too small for OTP at any real signup volume | Prior audit |

Recommendation: **Brevo Free** as the production relay (300/day is ample for OTP;
per-user rate limits already exist), with Gmail as the owner-only fallback.

### 4.4 Unverified risk that must be measured first

**AppSail outbound port 587 is untested.** No credentials were configured and no
test was attempted (per instructions). The verification is one real OTP send after
deploy: request a code for an owner mailbox and confirm arrival within 60 s. If it
fails with a timeout, the fallback is a provider HTTP API over HTTPS — which *would*
require a new adapter (not authorised now).

## 5. Task 5 — Backup readiness

### 5.1 Neon capabilities (official docs, fetched 2026-11-12)

- **Instant restore / PITR:** Free plan retains a **6-hour** history window
  (Launch 7 days, Scale 30 days).
- **`pg_dump` / `pg_restore`:** supported for manual backups.
- **Automated dumps:** Neon documents a GitHub Actions workflow that exports to S3
  on a schedule, including retention.

Gap: 6 hours of PITR does not cover "we noticed a bad migration three days later",
and there is currently **no off-site copy**: `/data/MyFarmAI-backups` is 191 MB on
the same host as the repository.

### 5.2 Cloudflare R2 requirements

Official R2 "Get started" (fetched 2026-11-12) requires a Cloudflare account **with
an R2 subscription** and completing a **checkout flow** to add it. Free monthly usage
(10 GB-month, 1M Class A, 10M Class B, free egress) applies, but the subscription
checkout is a billing surface.

**Verdict: R2 is POLICY-BLOCKED until the owner explicitly approves an R2
subscription checkout.** Do not create a bucket, do not enable R2, do not add a
payment method as part of this work.

### 5.3 Proposed backup procedure (PROPOSED — not executed)

```bash
# Daily, from the owner machine or CI, secret passed via env only:
docker exec -e PGURL="$NEON_DATABASE_URL" myfarmai-postgres \
  pg_dump "$PGURL" --format=custom --no-owner --no-acl \
  | age -r "$BACKUP_AGE_PUBLIC_KEY" \
  > myfarmai-$(date +%F).dump.age

# Checksum + copy off-host
sha256sum myfarmai-$(date +%F).dump.age >> myfarmai-sha256.txt
```

Rules:
- Encrypt **before** it leaves the host; the dump contains personal data.
- Store off the application host (owner-approved destination).
- Never commit dumps or keys; never publish them to a public bucket or release.

### 5.4 Restore procedure (must be rehearsed, not assumed)

1. Create a **Neon branch** from the current production branch (no production writes).
2. `pg_restore --clean --if-exists --no-owner --no-acl` into the branch.
3. Run `alembic current` / `alembic upgrade head` on the branch and compare row
   counts for `users`, `sessions`, `farms`, `plots`, `crop_plans`, `chat_messages`.
4. Point a throwaway backend at the branch and pass `/health/ready` + one
   authenticated read.
5. Record duration and any errors; only then is the backup "verified".

### 5.5 Retention recommendation

| Tier | Retention | Rationale |
|---|---|---|
| Neon PITR | 6 h (free ceiling) | Undo accidental writes/DDL within the same day |
| Daily encrypted dump | 7 copies | Covers a week of undetected corruption |
| Weekly encrypted dump | 4 copies | Covers a month / bad migration |
| Pre-migration dump | Keep until the migration is proven | Rollback point for schema changes |
| Release-time dump | Keep with the release tag | Reproducible state at v1.0.0 |

### 5.6 Access protection and owner approvals

- Encryption key custody with the owner (age or GPG); a lost key means an
  unreadable backup — record the recovery method.
- Least-privilege storage credential, write-only where supported, no public access.
- **Approvals needed:** destination + cost (must stay ₹0), encryption tool/key
  custody, and permission to rehearse a restore on a Neon branch. R2 requires the
  separate subscription decision.

## 6. Evidence log (all fetched/observed 2026-11-12)

| Source | What it established |
|---|---|
| `docs.catalyst.zoho.com/.../pricing-calculations/` | AppSail GB-minute formula and per-memory rates; allowances not cumulative |
| `docs.catalyst.zoho.com/.../free-tier/` | account-wide, monthly refresh, per-resource overage |
| `docs.catalyst.zoho.com/.../pay-as-you-go-model/` | USD 5 minimum bill per project once any limit is exceeded |
| `docs.catalyst.zoho.com/.../billing/introduction/` | one-time USD 250 credit consumed after free tier |
| `docs.catalyst.zoho.com/.../appsail/introduction/` and `.../appsail-configurations/` | "scales up or down based on traffic"; memory/disk defaults; no idle policy documented |
| Catalyst MCP `Get_AppSail`, `Get_Slate_App` | live memory 2048 MB, disk 256 MB, deploy time, Slate bundle date |
| `neon.com/docs/manage/backups` | Free PITR = 6 h; pg_dump/restore supported |
| `developers.cloudflare.com/r2/get-started/` | R2 requires subscription checkout |
| Brevo Help Center FAQ + Brevo pricing | 300 emails/day free, no card |
| `support.google.com/accounts/answer/185833` | app passwords require 2-Step Verification |
| Live HTTP probes + `docker inspect`/`docker history` + local image diff | deployment fingerprint, HEAD failure, auth behaviour, memory baseline |

## 7. Explicit limitations

1. AppSail plan, credit balance, current GB-minute usage and payment-method state
   are **not accessible via the Catalyst MCP** — BLOCKED on the console.
2. AppSail idle/scale-to-zero and post-quota behaviour are **not documented**.
3. 256 MB sufficiency is measured on SQLite only; Postgres + Pillow peaks untested.
4. AppSail outbound SMTP is **NOT TESTED**.
5. R2 enablement and any card requirement were not attempted (policy).
6. No restore rehearsal was performed; the procedure is untested.
7. No load, latency, or concurrency measurement was made.
