# MyFarmAI — Cloud V1 Architecture Lock

Status: **LOCKED** — owner directive, 2026-11-12. Identifier:
`MYFARMAI-CLOUD-V1`.
Scope: the production architecture for MyFarmAI V1. This record fixes the stack,
the provider responsibilities, the restrictions, the decision history and the
change-control rules. It does not authorise any deployment or infrastructure
change.

Companion evidence:
[`../deployment/MYFARMAI_PRODUCTION_BLOCKERS.md`](../deployment/MYFARMAI_PRODUCTION_BLOCKERS.md),
[`../deployment/MYFARMAI_POST_AUDIT_STAGE_2.md`](../deployment/MYFARMAI_POST_AUDIT_STAGE_2.md),
[`../deployment/MYFARMAI_CLOUD_PROVIDER_AUDIT.md`](../deployment/MYFARMAI_CLOUD_PROVIDER_AUDIT.md).

## 1. Fixed stack

| Layer | Component | Role |
|---|---|---|
| Web | **Next.js 15** | Public web application |
| Android | **React Native + Expo** | Mobile client |
| Backend | **Python FastAPI** | API, auth, domain logic |
| Database | **Neon PostgreSQL** | Persistent database of record |
| App hosting | **Zoho Catalyst Slate + AppSail** | Web bundle and API runtime |
| DNS / CDN | **Cloudflare** | DNS and CDN only |
| Source / releases | **GitHub** | Source of truth and APK releases |
| Local AI | **Ollama + Qwen** | Development and testing only |
| Production email | **Brevo SMTP** | Transactional email, after owner setup and verification |
| Research | **SearXNG** | Research integration |
| Database recovery | **Neon backup / export** | Backup and restore |
| Packaging | **Docker** | Portable deployment artifacts |

## 2. Provider responsibilities

- **Catalyst** — application hosting only: Slate serves the Next.js bundle,
  AppSail runs the FastAPI container. It is not a database, object store, email
  provider or CDN decision point.
- **Neon** — the only production database. Recovery is through Neon's own
  backup/export capability; no second database provider is approved.
- **Cloudflare** — DNS and CDN. No application hosting.
- **GitHub** — repository, release tags and APK distribution.
- **Brevo** — outbound transactional email (OTP, verification). Enabled only
  after the owner completes account setup and verifies one real send.
- **Ollama + Qwen** — developer machine and test environment only. V1 production
  does not include a hosted LLM; Gemini and other cloud LLM paths are not part of
  the locked stack.
- **Docker** — build and portability format; not a hosting provider.

## 3. Provider restrictions

- AWS and Google Cloud are **not selected**. No accounts, migrations or renewed
  provider comparisons.
- Do **not** add Vercel, Render, Supabase, R2 or other hosting providers without
  a demonstrated technical blocker **and** explicit owner approval. R2 is not a
  fallback for object storage under this lock.
- No second database, no second application host, no parallel deployment path.
- No provider change may be made automatically by an agent.

## 4. Financial policy (binding)

- Zero-cost-first.
- No international cards.
- No paid resources.
- No billing activation.
- No automatic payment mandates.
- No unexpected charges.
- Use only existing eligible free allowances.

## 5. Known open conflict — AppSail quota

`MYFARMAI-CLOUD-V1` was approved with AppSail as the API host. The 2026-11-12
read-only audit found that the free AppSail allowance (900 GB-minutes/month) does
**not** cover continuous runtime at any memory setting: 2048 MB covers 7.5 h/month,
256 MB covers 60 h/month. A 24/7 month exceeds the allowance by 12× at 256 MB and
96× at 2048 MB.

This is an **open production blocker (B1)**, not a reason to change the locked
host. It must be resolved by the owner from console evidence (usage, credits,
amount due, memory allocation) before any deploy. Options are limited to free-tier
behaviour that stays inside the allowance, or an explicitly approved billing
decision that supersedes §4. No agent may choose either.

## 6. Decision history

| Date | Decision | Record |
|---|---|---|
| 2026-11-03 | AWS ruled out (account lifetime, card requirement, prior owner ruling) | Provider audit §3.1 |
| 2026-11-12 | AWS and Google Cloud re-confirmed as not selected | Provider audit §3 |
| 2026-11-12 | Catalyst Slate + AppSail retained as application host, conditional on quota evidence | Provider audit §1, Stage 2 §1 |
| 2026-11-12 | Neon retained as database of record | Provider audit §1, live `/health/ready` |
| 2026-11-12 | Brevo selected as production SMTP path (supersedes the Gmail/Brevo open choice in D3) | This lock |
| 2026-11-12 | V1 production AI remains disabled; Ollama + Qwen are local/test only (supersedes the Gemini option in D4) | This lock |
| 2026-11-12 | R2 not adopted; database recovery via Neon backup/export (B7 closed as rejected under this lock) | This lock |
| 2026-11-12 | `MYFARMAI-CLOUD-V1` locked as the long-term architecture | This document |

## 7. Change-control policy

An architecture change is considered only when the current stack is
**demonstrably incapable** of meeting a required technical or zero-cost
condition. A proposal must contain all of:

1. Evidence of the blocker (command output, provider doc, measured failure).
2. The exact affected component.
3. Migration cost and effort.
4. Data-preservation plan.
5. Financial impact.
6. Owner approval requirement.

No change is executed automatically. Until the owner approves a superseding
record, this document wins over newer informal proposals, and the restriction in
§3 stands.

## 8. Current production state (2026-11-12)

The deployed backend predates `HEAD`; the Slate bundle is stale; the live backend
logs OTP codes and delivers no email; the Neon credential sits in AppSail config;
no off-site backup exists. The 13-item blocker register and its dependency-ordered
sequencing are the authoritative work list:

[`../deployment/MYFARMAI_PRODUCTION_BLOCKERS.md`](../deployment/MYFARMAI_PRODUCTION_BLOCKERS.md)

Order of work (from the register):

1. **Evidence and owner decisions, no writes** — B1 console numbers; B5 rotation
   approval; B6 backup decision; B12 release-commit decision.
2. **Backend rebuild and redeploy** — after B1 and B5; fixes B2, B3, B9.
3. **Slate redeploy** — B4, after the backend URL is confirmed unchanged.
4. **Backups** — B6.
5. **Hardening** — B8, B10, B11, B13.

## 9. What this lock does not authorise

- No deployment, rebuild, DNS change, credential rotation, billing action, data
  migration or release publication.
- No change to the blocker register's approval gates.
- No claim that the current stack is operating inside the free allowance.
