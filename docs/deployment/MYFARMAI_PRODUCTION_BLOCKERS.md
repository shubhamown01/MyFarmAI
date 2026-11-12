# MyFarmAI — Production Blocker Register

Status: **OPEN — B7 resolved by the architecture lock; all other blockers open.**
Prepared 2026-11-12 from read-only investigation. Every fix below requires owner
approval before execution.

Companion evidence: [`MYFARMAI_POST_AUDIT_STAGE_2.md`](MYFARMAI_POST_AUDIT_STAGE_2.md).

Binding architecture: [`../architecture/MYFARMAI_CLOUD_V1_LOCK.md`](../architecture/MYFARMAI_CLOUD_V1_LOCK.md)
— resolves B7 (R2 not adopted), D3 (Brevo SMTP) and D4 (production AI disabled).
Nothing here authorises a deploy, billing change, credential change, or data
operation.

## 1. Register

| ID | Blocker | Severity | Evidence | Owner action | Acceptance test |
|---|---|---|---|---|---|
| **B1** | AppSail quota and billing state unknown | **Critical (financial)** | 900 GB-min/month = 7.5 h at 2048 MB; USD 5 minimum bill per project; $250 credit state invisible via MCP | Read console usage/credits/amount due (Stage 2 §1.5), report five numbers | Known GB-min used, known credit balance, known amount due; memory decision made from data |
| **B2** | Live production backend logs full OTP codes and delivers nothing | **Critical (security)** | Deployed image predates `903a418`/`be2c6ed`; old `DevModeEmailDelivery` logs `code=%s`; `ENVIRONMENT=production` is baked in | Approve backend redeploy with SMTP; rotate anything sensitive in logs | Platform log shows no OTP code; a real code arrives by email and is accepted once |
| **B3** | Deployed backend is not HEAD | **Critical** | Image built 2026-11-10 18:09Z from `0a75e26` + pre-commit `f9c5eeb`; live `/` reports 0.1.0; no `SmtpEmailDelivery`; `downloads.py` GET-only | Approve rebuild + redeploy from `6393c2b` | Image digest recorded; `/` reports 1.0.0; `HEAD` APK returns headers with no body; SMTP adapter present |
| **B4** | Slate bundle is stale | **High** | `modified_time` 2026-11-08; live chunk hashes differ from local build `ZRPkfioLGrLtf5GbxRdQv` | Approve `zcatalyst-cli deploy slate` | `modified_time` updates; live chunk hashes match a fresh build; web fixes visible |
| **B5** | Neon credential sits in plaintext in AppSail config | **High** | Only reference is `DATABASE_PATH`; repo/git/image/temp are clean (Stage 2 §2.1). Re-confirmed 2026-11-12: read-only `Get_AppSail` returns the password in clear text (value not recorded) | Rotate in Neon, update AppSail, restart | `/health/ready` 200 `database: ok`; old password invalid; repo pattern scan still 0 |
| **B6** | No off-site backup; PITR only 6 h | **High** | Neon Free PITR = 6 h; `/data/MyFarmAI-backups` (191 MB) is on the app host | Approve destination, encryption key custody, restore rehearsal | Dump encrypted off-host, checksum recorded, restore into a branch passes health + row-count checks |
| **B7** | R2 requires an R2 subscription checkout | Medium | Official R2 get-started requires completing checkout | **RESOLVED — not adopted** under `MYFARMAI-CLOUD-V1`; do not create an R2 resource | Decision recorded; no bucket created |
| **B8** | `/openapi.json` is public (53 paths) | Low | 200, 82 KB; `/docs` and `/redoc` are 404 | Decide: keep public or disable `openapi_url` in production | Either an intentional decision or a 404 |
| **B9** | AppSail outbound SMTP is untested | **High** | No credentials configured; no send attempted; Render equivalent blocks 587 | Approve one test send after deploy | OTP email arrives within 60 s from a real signup |
| **B10** | Proxy trust for rate limiting is assumed, not measured | Medium | `TRUSTED_PROXY_CIDRS=10/8,172.16/12,192.168/16` baked into the image; no live XFF test this pass | Approve a controlled spoof test at low volume | Spoofed `X-Forwarded-For` does not create a fresh limiter bucket |
| **B11** | AI disabled in production | Medium (product) | `/health/ready` → `ollama: disabled`; no cloud adapter exists | Decide Gemini free tier vs stay disabled | Either chat/research returns a real answer within quota, or the limitation is published |
| **B12** | Release tag and deployed artifacts disagree | Medium | `v1.0.0` = `84f34fc`, **24 commits behind** HEAD `f0a5b63`; deployed image predates the tag's fixes | Decide the authoritative release commit; retag only with approval | Tag, image digest, Slate bundle and HEAD documented as one consistent set |
| **B13** | Selfie uploads land on ephemeral AppSail disk | Medium | `SELFIE_STORAGE_DIR=/data/myfarmai-selfies`, 256 MB disk, lost on redeploy | Decide: disable selfie flow, or move to approved object storage | Either the endpoint is disabled in prod, or uploads survive a redeploy |

## 2. Sequencing (dependency-correct)

```
A. Evidence + decisions (no writes)
   B1 console numbers ─┬─> memory decision (256 vs 512 vs 2048)
   B5 rotation approval ─> rotate BEFORE next deploy (deploy would reuse secret)
   B7/B6 backup decision
   B12 release-commit decision
        │
B. Backend rebuild + redeploy  (requires B1 decision, B3/B9 approval, SMTP creds)
   fixes B2, B3, B9; partially B13; keeps B5 rotated
        │
C. Slate redeploy (B4)  — after the backend URL is confirmed unchanged
        │
D. Backups (B6) + optional R2 (B7) — independent of B/C
        │
E. Hardening (B8, B10, B11, B12, B13)
```

Rules:
- **Do not deploy before B1 and B5.** Deploying first re-bakes the old secret path
  and may change billing behaviour while the quota state is unknown.
- **Do not change memory before the console numbers exist.** No benchmark can tell
  you what the platform is actually charging.
- **Do not rotate the Neon password and the AppSail image in the same window**
  without a rollback plan; if readiness fails, you must be able to tell which change
  caused it.

## 3. Deployment gate (what exactly to approve)

| Approval | Scope | Not included |
|---|---|---|
| A1 | Read Catalyst billing/usage console (read-only) | Any payment-method change |
| A2 | Rotate Neon role password and update `DATABASE_PATH` | Any other Neon setting |
| A3 | Rebuild backend image from `6393c2b` and deploy to AppSail | Slate deploy, DNS, domain |
| A4 | Set SMTP variables and send one real OTP | Bulk mail, marketing email |
| A5 | Redeploy Slate from the current local build | Custom domain |
| A6 | Create an encrypted off-host backup + rehearse restore on a Neon branch | Production restore |
| A7 | Enable R2 subscription (only if the owner accepts the billing surface) | Any paid storage tier |
| A8 | **EXECUTED 2026-11-12** — `52a8e88` (HEAD route) and `f0a5b63` (docs) pushed to `origin/phase-01-foundation` | Release retag unless separately approved |

## 4. Exact rollback for the backend deploy

1. Keep the current image tar/tag (`prod-20261110`) until the new one passes all
   checks; `docker save` it if it is not already archived.
2. Redeploy the previous image if `/health/ready` fails or OTP delivery breaks.
3. Environment variables are not reverted by an image rollback — record the old
   values in the owner's secret store before editing.
4. If the database migration at startup fails, the new image will not become
   healthy; the old image does not run new migrations, so rollback is safe as long
   as no migration was applied. **Check `alembic current` before and after.**

## 5. What is explicitly out of scope here

- Provider migration (AWS/GCP/Render/Vercel) — rejected, unchanged.
- Billing activation, paid plans, custom domains.
- Production database reset or destructive migration.
- Publishing a release or changing DNS.
- Any action on the Neon credential value by this agent.

## 6. Owner decisions, restated

1. **D1** — report AppSail GB-minutes, credits, amount due, memory allocation,
   instance count (B1).
2. **D2** — approve Neon password rotation (B5).
3. **D3** — **RESOLVED**: Brevo SMTP, per `MYFARMAI-CLOUD-V1`. Remaining work is
   account setup, credential entry and one verified send (B9).
4. **D4** — **RESOLVED**: production AI stays disabled; Ollama + Qwen are local and
   test only. Publishing the limitation (B11) remains open.
5. **D5** — backup destination + encryption key custody; approve/reject R2.
6. **D6** — authoritative release commit for the next deploy (B12); candidate is
   HEAD `f0a5b63`.
7. **D7** — publish the undeployed HEAD fix and Slate bundle (B3/B4/A8).

Until D1–D3 are answered, the only safe next action is **read-only console
inspection**.
