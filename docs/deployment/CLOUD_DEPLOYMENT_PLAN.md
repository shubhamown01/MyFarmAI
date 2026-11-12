# Cloud Deployment Plan (provisional — PROPOSED, not owner-approved)

> Superseded as the provider decision input on 2026-11-12 by
> [`MYFARMAI_CLOUD_PROVIDER_AUDIT.md`](MYFARMAI_CLOUD_PROVIDER_AUDIT.md). This file
> is retained as the historical 2026-11-03 record.

Status: **PROPOSED**. Prepared 2026-11-03 from verified free-tier facts
(see `FREE_TIER_COMPARISON.md` for sources and dates). No provider decision is
final until the owner approves; section 6 lists the pending approvals.
No production deployment has occurred; the E6 refuse-public gate stays active.

## 1. Architecture target (hybrid, provider-independent)

| Layer | Component | Provisional home | Rationale (verified facts) |
|---|---|---|---|
| Frontend (Next.js) | Public web app | **Cloudflare Pages (Free)** | Live account; 500 builds/mo, 100 projects, 20k files — ample for one site; global CDN + free SSL |
| Lightweight edge ops | Cookies/redirect helpers if needed | Cloudflare Workers (Free) if necessary | 100k req/day, 10 ms CPU — but only for trivial logic; Must NOT host business logic |
| Backend (FastAPI) | API, auth, farm ops, AI gateway | **Zoho Catalyst AppSail** (provisional, pending owner's student verification) — deep-fetched official docs 2026-11-03 confirm AppSail runs Python managed runtimes AND custom OCI-image runtimes | Free tier gives AppSail **900 GB-minutes/mo ≈ 60 h of a 256 MB instance — NOT enough for a 24/7 backend**; a continuous backend fits only via the student program's $250 usage (owner does identity verification personally; general $250 credits require a card → policy-BLOCKED). Other candidates remain blocked: Workers no Python, Prisma Compute TS-only, Koyeb paid, AWS ruled out, GCP needs billing. Fallback if owner is not an eligible student: backend stays local/sandbox until funding (E6) |
| Database (Postgres) | Accounts, farms, sync, quotas | **Neon Free** — **account now LIVE** (Google SSO 2026-11-03, org `org-fragrant-cell-14431918`); **no project/database created** — empty-project dry run + any migration still need separate owner approval | Permanent free, no card, 100 projects, 1 GB/project, **no inactivity pause** (best-for-persistence trait, vs Supabase's 1-week pause) |
| File/object storage | Farmer uploads (selfies are NOT stored long-term — see security checklist) | **Cloudflare R2** (10 GB/month free egress — verify limits before use) or defer | R2 free tier exists; quota verification pending |
| AI | Local-first (device Ollama/SQLite knowledge) + throttled cloud AI | Operator plan §9 | Cloud AI quota (§10, 20 queries/10h/user) **implemented server-side 2026-11-04** (`services/ai_quota.py`, flag-off); activates the moment the cloud provider is wired and the backend gets its public home |

## 2. Constraints observed (Phase A, evidence-based)

- Host: 7 GiB RAM (~6.6 used with dev stack), 2 GiB VRAM — GPU inference stays on `qwen3:0.6b`-class models.
- ₹0 policy: no card/billing anywhere; card-required services marked BLOCKED (AWS, GCP billing activation, Koyeb).
- Existing DB is Compose Postgres locally; **no migration without owner approval** (governance gate).
- Open-Meteo non-commercial licensing + SearXNG AGPL-3.0 remain open legal questions (Phase 0 gates).

## 3. Environment topology

1. **Local dev (today, running)**: docker compose (postgres + backend on loopback), web dev on :3000. Runner scripts cover start/stop/restart/status/backup/deploy-local.
2. **Staging (proposed)**: Cloudflare Pages preview deployments (unlimited, free) per PR; Neon branch (10 branches free) for DB staging.
3. **Production (proposed, blocked on §6 approvals + E6)**: Pages production domain + custom domain — **no domain purchase allowed** (₹0); initial URL would be the `*.pages.dev` subdomain unless the owner supplies an owned domain.

## 4. Rollout order (each step gated)

1. Owner approves DB provider (Neon) → create **empty** project; run migrations against it from a scratch environment; verify; only then migrate data (distinct owner approval).
2. Owner approves backend host (see §6 decision) → deploy FastAPI with secrets via provider's secret storage (never in Git).
3. Frontend deploy to Pages preview → verify auth flows against staging DB → production promote after security checklist.
4. Quota enforcement (§10 cloud AI 20/10h) **IMPLEMENTED AND TESTED 2026-11-04 (MF-C-Q01 — see `CLOUD_COST_AND_QUOTA_POLICY.md` §4.1)**: server-side atomic counter active only when `cloud_ai_enabled` is turned on; 11/11 quota tests + full 283/283 suite green; migration `c8d9e0f1a2b3` applied to the dev DB. The §20/10h counter runs before any generation — done before public exposure as required. Admin-visible usage dashboard remains a pre-launch item.
5. Backup cadence: `BACKUP_MYFARMAI.sh --verify` for local; provider automatic backups verified by restore test before go-live.

## 5. Renewal & migration calendar (directive §12)

- T-30 days before any provider policy change/expiry: re-check eligibility, run provider restore drill, prepare alternative.
- Quarterly: full export (pg_dump from Neon into `/data/MyFarmAI-backups/`), restore drill into throwaway container (the script's `--verify` path does exactly this).
- Migration readiness: keep connection string in one config surface (per-provider env), schema changes via Alembic only, so a swap to a paid Postgres later is a connection-string change, not a code change.

## 6. Pending owner approvals (blockers)

1. DB provider choice (Neon proposed).
2. Backend host decision — options and their gates:
   a. Zoho Catalyst student program — you verify student status (identity/academic gate).
   b. GCP Always-Free — requires billing-enabled account (₹0 policy conflict → currently BLOCKED).
   c. Keep backend local until a paid provider is chosen later (safe default).
3. Database migration approval (after an empty-project dry run).
4. Public exposure may proceed only after `PRODUCTION_SECURITY_CHECKLIST.md` is satisfied and the E6 gate is lifted by explicit owner decision.
