# MyFarmAI — Cloud Provider Audit (read-only, zero-cost-first)

Status: **COMPLETE for discovery; PROPOSED for selection.** No cloud resource was
created, changed, or deleted during this audit. No billing was enabled. No DNS was
touched. No data was migrated. Nothing was deployed.

- Audit date: **2026-11-12**
- Repository: `/data/MyFarmAI`, branch `phase-01-foundation`, HEAD `6393c2b`
- Method: repository inspection, live read-only HTTP checks against the existing
  deployment, authenticated read-only provider calls (Catalyst MCP), and logged-out
  fetches of official provider pages. Facts below carry the fetch date; anything not
  fetched or observed is marked **UNVERIFIED** and is not used to justify a decision.
- Binding rules applied: [`CLOUD_COST_AND_QUOTA_POLICY.md`](CLOUD_COST_AND_QUOTA_POLICY.md)
  (₹0, no card, no billing, no subscriptions, no paid resources) and
  [`CLOUD_ACCOUNT_INVENTORY.md`](CLOUD_ACCOUNT_INVENTORY.md).

## 1. Decision summary

| Layer | Decision | Status |
|---|---|---|
| Web (Next.js 15 standalone) | Keep **Catalyst Slate** (incumbent, free, no card) | PROPOSED — needs fresh bundle deploy |
| API (FastAPI 3.12 container) | Keep **Catalyst AppSail** custom runtime | PROPOSED — conditional on quota evidence (§5.1) |
| Database (Postgres) | Keep **Neon Free** (incumbent, permanent, no card) | COMPLETE — already live, verified 200 `database: ok` |
| Object storage (APK, uploads) | **Cloudflare R2 Free** (10 GB-month) or defer | PROPOSED — enablement/card requirement unverified |
| AI (chat/research) | Hosted free-tier LLM behind the existing `AIGateway`, or stay disabled | PROPOSED — owner privacy decision required |
| Transactional email | Gmail app-password SMTP (zero new accounts) or Brevo Free | PROPOSED — blocked on credentials only |
| DNS/CDN | Cloudflare only if a domain is ever purchased | NOT TESTED — no domain, no spend |
| **AWS** | **Rejected** | See §3.1 — 6-month account lifetime + card + prior owner ruling |
| **Google Cloud** | **Rejected** | See §3.2 — billing account/card mandatory, trial data deletion |

There is **no laptop dependency** in this topology: web, API, database, and APK
distribution all resolve to public provider endpoints. The developer machine is
needed only to *build and upload* artifacts.

## 2. What is actually running today (verified read-only, 2026-11-12)

| Check | Command | Observed |
|---|---|---|
| API liveness | `GET /health/live` | 200, `{"status":"ok","service":"backend","check_type":"liveness"}`, 6.61 s first request |
| API readiness | `GET /health/ready` | 200, `{"database":"ok","ollama":"disabled"}`, 1.79 s |
| Web root | `GET https://myfarmai-web-zwpytbwu.onslate.in/` | 200, 63,173 bytes, `<title>Home · MyFarmAI</title>`, 3.51 s |
| APK range GET | `GET /api/v1/downloads/app-release.apk` (`Range: bytes=0-15`) | 206, `application/octet-stream`, body starts `PK\x03\x04` |
| APK HEAD | `HEAD /api/v1/downloads/app-release.apk` | 200 with a 31-byte JSON body — the HEAD fix in the working tree is **not deployed** |
| Slate bundle age | Catalyst MCP `Get_Slate_App` | `modified_time` **2026-11-08 01:36**, framework `nextjs`, Node 22, `app_type cli` |
| AppSail instance | Catalyst MCP `Get_AppSail` | `myfarmai-backend` id `90779000000018005`, custom runtime, port 8000, disk 256 MB, **memory 2048 MB**, last deploy 2026-11-10 23:58 |
| Vercel MCP | `list_teams`, `list_projects` | 403 "Not authorized … scope `superstarsb98-4840`" — **no usable authenticated Vercel access** |

Consequences visible in the live state:

- `ollama: disabled` means chat and research cannot answer on the live backend.
- The Slate bundle predates the 2026-11-10 release bundle; `/auth/login` contains no
  onboarding markers, consistent with a stale build.
- Registration cannot complete on the live backend: no SMTP variables are set, and
  `EMAIL_DELIVERY_MODE` defaults to `dev` (`backend/app/core/config.py:236`).
- The APK **is** downloadable (65 MB, range requests honoured), so Android
  distribution does not need a separate host.

## 3. Rejected providers

### 3.1 AWS — rejected (technical + policy + prior ruling)

Fetched 2026-11-12 from the AWS Free Tier page:

- The current free offering is a **credit** model: `$100` at signup plus up to `$100`
  earnable, i.e. up to `$200` valid for **6 months**.
- "The account closes on its own 6 months after you open it or when your credits run
  out, whichever comes first."
- A **payment method is required** at signup.

Consequences: a permanent ₹0 service is impossible; the ceiling is a time-boxed trial
that self-terminates. This matches the existing owner ruling recorded in
[`CLOUD_ACCOUNT_INVENTORY.md`](CLOUD_ACCOUNT_INVENTORY.md) (2026-11-03): AWS is
"ruled out by owner — do not retry". **Conflict to flag:** the task brief names AWS as
"preferred if it meets all technical and zero-cost requirements". It does not, and
reinstating AWS would require a fresh, explicit owner decision that supersedes the
existing ruling. This audit does **not** treat AWS as a candidate.

### 3.2 Google Cloud — rejected (card/billing mandatory)

Fetched 2026-11-12:

- Free Tier usage requires an **active Cloud Billing account**.
- Free Trial signup requires a **credit card** for identity verification.
- If the account is not upgraded when the trial ends, trial resources are **stopped
  and then permanently deleted**.

Consequences: violates the no-card rule; also risks data deletion. GCP is not a
candidate for the database or API. Google's **Gemini API free tier** is a separate
product with a separate key and no billing account requirement — it is evaluated only
as an AI inference option (§4.7), not as hosting.

## 4. Provider findings

### 4.1 Cloudflare — DNS/CDN/object storage only

Fetched 2026-11-12 (`developers.cloudflare.com`):

| Product | Free allowance | Fit |
|---|---|---|
| Workers | 100,000 requests/day, **10 ms CPU** per invocation, 128 MB | Cannot host Next.js SSR or FastAPI. Cloudflare's own guidance puts SSR/auth workloads at 10–20 ms CPU; the Free cap is not a reliable budget. No Python runtime. |
| R2 | **10 GB-month** storage, 1M Class A + 10M Class B ops/month, **free egress** | Suitable for APK/backup/object storage. Enabling R2 may require a payment method on the account — **UNVERIFIED**; must be checked before relying on it. |
| DNS/CDN | Free plan | Only relevant if a domain is purchased (owner cost gate). |

Verdict: **eligible for R2 and DNS only.** Not a compute host under the ₹0 rules.

### 4.2 Vercel — technically capable, contractually risky

Fetched 2026-11-12:

- Hobby is free and supports Next.js 15 App Router/standalone well.
- Hobby is licensed for **non-commercial personal use only**.

MyFarmAI has no payments and no ads, so the project is arguably non-commercial today,
but the licence is a judgement call that can change with one future feature. Treating
it as the primary host would put the deployment's legitimacy on that judgement.

Verdict: **viable fallback for the frontend only**, not recommended as primary while a
no-card, no-strings alternative (Slate) is already live. No authenticated Vercel access
is available to this session (403), so nothing was configured or verified.

### 4.3 Render — not a production backend

Fetched 2026-11-12:

- Free web service: **0.1 CPU, 512 MB RAM**, spins down after **15 min** idle,
  ~1 min cold start, **ephemeral filesystem**.
- **Outbound ports 25/465/587 are blocked** — OTP email over SMTP cannot work.
- Free Postgres **expires 30 days after creation**.
- Render's own documentation says not to use free instances for production.

Verdict: **rejected for the API**; the SMTP port block alone breaks registration, and
the 30-day database deletion is disqualifying. Could host a stateless demo, not this
product.

### 4.4 Neon — database of record

Fetched 2026-11-12, already in use (readiness probe returns `database: ok`):

| Property | Value |
|---|---|
| Cost / card | Permanent Free plan, **no card** |
| Projects | 100 per account |
| Compute | 100 CU-hours per project/month, **scale-to-zero after ~5 min** |
| Storage | 1 GB per project, 20 GB per account |
| Egress | 5 GB per project/month |
| Inactivity pause | **None** — compute suspends or writes are blocked at quota; data is not deleted |

Verdict: **keep.** This is the least risky layer of the stack and needs no change.

### 4.5 Catalyst (Zoho) — incumbent web + API host

From the Catalyst MCP (read-only) and the free-tier page (2026-11-12):

| Resource | Observed / quota | Notes |
|---|---|---|
| Project | `Project-Rainfall`, id `90779000000015001`, `project_type: Live`, org `60094539808` | Development environment is the default env |
| AppSail | `myfarmai-backend`, custom runtime, port 8000, disk 256 MB, **memory 2048 MB** | 2048 MB contradicts the 256 MB recorded on 2026-11-06 |
| Slate | `myfarmai-web`, `app_type cli`, Node 22, `modified_time` 2026-11-08 | CLI-uploaded, not Git-linked → stale bundle risk |
| AppSail free | **900 GB-minutes/month** | At 2048 MB that is **7.5 h of continuous runtime per month**; at 256 MB it is **60 h** |
| Slate free | 300,000 CDN requests + 500 MB storage/month | Sufficient for a pilot |
| Mail free | 100 emails/month | Not used by the backend (which sends OTP via SMTP) |
| Data Store free | 2 GB | Not used (Postgres on Neon) |
| Overage | Exceeding free limits triggers a **₹300/month minimum bill per project** | The only realistic way this stack stops being ₹0 |

Verdict: **keep, conditional.** The platform is free forever with no card and is
already serving traffic. The unresolved question is whether the 2048 MB instance is
billed for idle time (§5.1).

### 4.6 Others considered and not adopted

| Provider | Why not |
|---|---|
| **Oracle Cloud Always Free** | Strongest card-gated option (Always Free ARM VM). Official page returned **HTTP 403** to this session → **UNVERIFIED**; card verification is required, so policy-blocked regardless. |
| **Supabase / Prisma Postgres** | Prior audit (2026-11-03) records weaker free traits than Neon (2-project cap + 1-week pause; per-operation billing). No reason to migrate a working database. |
| **Koyeb / Fly.io / Railway** | Prior audit records them as paid or card-gated for this use case; not re-fetched in this pass (would not change the outcome under the no-card rule). |
| **GitHub Releases** | Not a host, but the correct zero-cost home for the signed APK artifact. Currently the APK is also served by AppSail. |

### 4.7 AI inference

No evaluated free compute tier can host a model: AppSail's 7.5–60 h/month and Render's
0.1 CPU/512 MB cannot run Qwen-class inference, and the host has only 2 GiB VRAM.
The only ₹0 path is a hosted API behind the existing provider-independent
`AIGateway` protocol (`backend/app/ai/gateway.py`).

Gemini API pricing fetched 2026-11-12 shows a **Free** tier described as "Free input &
output tokens" with "Content used to improve our products" for several Flash models
(e.g. `gemini-3.8-flash`, `gemini-3.6-flash`, `gemini-3.1-flash-lite`). Two owner
decisions follow: (a) accept that free-tier prompts may be used to improve Google's
products — a privacy question for farmer data — and (b) approve a new adapter, since
only `OllamaGateway` exists today. Until then the live backend stays `ollama: disabled`
and **chat/research remain non-functional in production**. That is the current,
honest state.

### 4.8 Transactional email

`config.py` production validation refuses to start unless `email_delivery_mode='smtp'`
and `smtp_host`/`smtp_from` are set.

> **Correction (2026-11-12, Stage 2):** this gate exists on `HEAD` (commit
> `be2c6ed`) but **not in the deployed image**, which predates it. The live
> backend runs the old dev adapter in production mode and logs OTP codes without
> delivering them. See
> [`MYFARMAI_POST_AUDIT_STAGE_2.md`](MYFARMAI_POST_AUDIT_STAGE_2.md) §3–§4.

Two no-card options:

1. **Gmail app-password SMTP** — zero new accounts, `smtp.gmail.com:587`, ~500
   recipients/day. Requires the owner's Google account and an app password.
2. **Brevo Free** — no card; SMTP relay. The exact free send volume could not be
   confirmed from the machine-readable pricing catalogue fetched 2026-11-12, so treat
   the volume as **UNVERIFIED** until the console shows it.

AppSail's outbound SMTP reachability is **UNVERIFIED**; this must be tested with a real
send before declaring registration working (see runbook §6).

## 5. Compatibility matrix

Legend: ✅ verified compatible · ⚠️ conditional/risk · ❌ incompatible · ❔ unverified

| Requirement | Catalyst Slate | Catalyst AppSail | Neon | Vercel Hobby | Render Free | Cloudflare |
|---|---|---|---|---|---|---|
| Next.js 15 standalone | ✅ (live, stale bundle) | — | — | ✅ | ⚠️ | ❌ (10 ms CPU) |
| FastAPI 3.12 container | — | ✅ (live, custom runtime) | — | ❌ | ⚠️ (0.1 CPU, sleeps) | ❌ (no Python) |
| Managed Postgres | — | ✅ (Neon URL) | ✅ | — | ⚠️ (30-day expiry) | — |
| Persistent disk | ❌ | ⚠️ 256 MB, ephemeral on redeploy | — | ❌ | ❌ | ❌ |
| Object storage | ❌ | ⚠️ APK baked into image | — | — | ❌ | ✅ R2 10 GB |
| Session cookies / HTTPS | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Outbound SMTP (OTP) | — | ❔ untested | — | — | ❌ ports blocked | — |
| AI inference | ❌ | ❌ | — | ❌ | ❌ | ❌ (external API required) |
| Open-Meteo (non-commercial) | ✅ network egress | ✅ | — | ✅ | ✅ | ✅ |
| Android APK distribution | ✅ via backend | ✅ | — | — | — | ⚠️ R2 if enabled |
| Logs / health probes | ⚠️ limited | ✅ `/health/live`, `/health/ready` | ⚠️ console metrics | ⚠️ | ⚠️ | ⚠️ |
| Usage/billing visibility | ❔ no MCP tool | ❔ no MCP tool | ⚠️ console only | — | — | — |

## 6. Smallest viable ₹0 combination

```
Android APK  ──► GitHub Releases (artifact)  ──►  optional mirror on AppSail /api/v1/downloads
Web (Next.js)──► Catalyst Slate  ──/api/v1──►  Catalyst AppSail (FastAPI container)
                                                   │
                                                   ├──► Neon Free (Postgres, ap-southeast-1)
                                                   ├──► Gemini free tier (behind AIGateway) [PROPOSED]
                                                   ├──► Gmail/Brevo SMTP (OTP) [PROPOSED]
                                                   └──► Open-Meteo (weather, non-commercial)
```

Why this and not a rebuild elsewhere:

- It is the **only** combination verified today that is free forever, card-free, and
  already serving the product.
- Every alternative either requires a card (AWS, GCP, Oracle), forbids the workload
  (Cloudflare Workers, Render SMTP), or expires (Render Postgres, AWS 6 months).
- Each layer is independently replaceable: the API is a standard container with a
  standard `DATABASE_URL`; the web app needs only `MYFARMAI_API_ORIGIN`; the database is
  plain Postgres. Nothing is locked to a proprietary SDK.

**Single largest financial risk:** AppSail is configured at **2048 MB**. At 900
GB-minutes/month that is 7.5 hours of continuous runtime. Either the instance idles
between requests (safe) or it runs continuously and a **₹300/month minimum bill** is
accruing. This is not observable through the Catalyst MCP (no usage/billing tools).
**Verification is an owner action and a hard gate before this architecture is called
financially safe** (runbook §2, §7).

## 7. Portability requirements (what keeps the exit cheap)

| Requirement | Current state | Action |
|---|---|---|
| Containerised API | ✅ `backend/Dockerfile`, Python 3.12, uv frozen, non-root uid 10001, port 8000, healthcheck | None |
| Standard DB URL | ✅ `database_path` accepts `postgresql://…`; normalised to `postgresql+asyncpg://` | None |
| Schema migrations | ✅ Alembic, 9 revisions | Run on target, never `create_all` |
| Backups | ⚠️ [`BACKUP_AND_RESTORE.md`](BACKUP_AND_RESTORE.md) covers local Compose only; `/data/MyFarmAI-backups` is on the same host | Off-site copy needed (R2 or Releases) before any destructive change |
| Tested migration | ⚠️ No restore has been rehearsed against Neon | Rehearse on a Neon branch (§ runbook 8) |
| Env-only configuration | ✅ Pydantic settings, every knob an env var | Keep values out of the repo |
| Versioned API | ✅ `/api/v1` prefix, `/health/*` outside it | None |
| Frontend decoupling | ✅ server-side rewrite via `MYFARMAI_API_ORIGIN` | None |
| Android decoupling | ✅ `EXPO_PUBLIC_API_BASE_URL`; prod placeholder `api.myfarmai.example.com` must be replaced at build time | Build with the real host |
| Infra documentation | ⚠️ Several overlapping docs under `docs/deployment/` | This audit + runbook are the decision record; older plans stay as history |

## 8. Evidence log (fetched 2026-11-12, logged-out unless stated)

| Source | URL | Used for |
|---|---|---|
| AWS Free Tier | `https://aws.amazon.com/free/` | credit model, 6-month closure, card requirement |
| Google Cloud Free Tier | `https://cloud.google.com/free/docs/free-cloud-features` | billing account requirement |
| Google Cloud Free Trial | `https://cloud.google.com/free` | card requirement, trial resource deletion |
| Cloudflare Workers limits | `https://developers.cloudflare.com/workers/platform/limits/` | 100k req/day, 10 ms CPU, 128 MB |
| Cloudflare R2 pricing | `https://developers.cloudflare.com/r2/pricing/` | 10 GB-month, 1M Class A, 10M Class B, free egress |
| Vercel fair use | `https://vercel.com/docs/limits/fair-use-policy` | Hobby non-commercial restriction |
| Render free | `https://render.com/docs/free` | 0.1 CPU, 512 MB, 15-min spin-down, SMTP ports, 30-day Postgres |
| Neon pricing | `https://neon.com/pricing` | CU-hours, storage, egress, scale-to-zero |
| Catalyst free tier | `https://catalyst.zoho.com/pricing.html` | AppSail/Slate/Mail/Data Store allowances, ₹300 minimum |
| Gemini API pricing | `https://ai.google.dev/gemini-api/docs/pricing` | free tier exists, data-use caveat |
| Brevo pricing | `https://brevo.com/pricing.md` | no-card free plan; send volume unverified |
| Oracle Always Free | `https://www.oracle.com/cloud/free/` | **HTTP 403 — nothing verified** |
| Catalyst MCP (authenticated, read-only) | `Get_AppSail`, `Get_Slate_App`, `Get_Project_By_Id` | live instance config, bundle age, project state |

## 9. Limitations and unverified items

1. **AppSail billing/quota consumption** — not exposed via MCP; the 2048 MB figure may
   be an allocation or a ceiling. **BLOCKED.**
2. **AppSail scale-to-zero behaviour** — no documentation observed. The 6.61 s first
   response is suggestive but not proof. **UNVERIFIED.**
3. **Outbound SMTP from AppSail** — not tested; needs one real OTP send. **NOT TESTED.**
4. **R2 enablement requiring a payment method** — not checked against the account.
   **UNVERIFIED.**
5. **Oracle Always Free** — page 403; card-gated regardless. **UNVERIFIED.**
6. **Brevo free send volume** — not present in the fetched catalogue. **UNVERIFIED.**
7. **Vercel account access** — MCP returns 403 for the only visible scope. **BLOCKED.**
8. **Gemini free-tier model availability for the account** — model names come from the
   pricing page, not from an authenticated call. **UNVERIFIED.**
9. **No load, latency, or cost measurement under real traffic** was performed. All
   capacity statements are quota arithmetic, not benchmarks.

## 10. Owner decisions required (do not self-approve)

| # | Decision | Why it is the owner's |
|---|---|---|
| D1 | Accept or reduce AppSail **2048 MB** and confirm observed usage | Only the console shows runtime/billing; a ₹300/month bill may be accruing |
| D2 | Confirm **AWS stays ruled out** (or explicitly supersede the 2026-11-03 ruling) | Conflicts with the brief's "AWS preferred" instruction |
| D3 | Choose SMTP: **Gmail app password** vs **Brevo** | Requires the owner's account and a credential |
| D4 | Approve or reject **Gemini free tier** as the AI path, accepting the data-use term | Privacy decision for farmer data |
| D5 | Approve an **off-site backup destination** (R2 or Releases) | Data-retention decision; currently single-host |
| D6 | Approve a **fresh Slate bundle** deploy (stale since 2026-11-08) | Publishing action; changes the public site |
| D7 | Approve deploying the **HEAD fix** already in the working tree | Publishing action; code is currently undeployed |
| D8 | Confirm **Open-Meteo non-commercial** use and **SearXNG AGPL** exposure | Legal decisions carried from Phase 0 |

No resource creation, deployment, DNS change, billing activation, data migration, or
release publication is authorised by this document. The exact resource list and steps
are in [`MYFARMAI_CLOUD_DEPLOYMENT_RUNBOOK.md`](MYFARMAI_CLOUD_DEPLOYMENT_RUNBOOK.md),
which stops at the same gate.
