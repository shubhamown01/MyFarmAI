# MyFarmAI — Owner Readiness Checklist & Production Gate

Status: **PREPARED — awaiting owner answers. Nothing here has been executed.**
Prepared 2026-11-12 by a read-only local pass. No commit, push, deploy, credential
rotation, console change, email send, or cloud resource creation was performed.

Authority:
[`../architecture/MYFARMAI_CLOUD_V1_LOCK.md`](../architecture/MYFARMAI_CLOUD_V1_LOCK.md).
Work list:
[`MYFARMAI_PRODUCTION_BLOCKERS.md`](MYFARMAI_PRODUCTION_BLOCKERS.md).
Evidence:
[`MYFARMAI_POST_AUDIT_STAGE_2.md`](MYFARMAI_POST_AUDIT_STAGE_2.md),
[`MYFARMAI_CLOUD_PROVIDER_AUDIT.md`](MYFARMAI_CLOUD_PROVIDER_AUDIT.md).

Label mapping: checklist **D1–D4** are the owner actions requested in this
readiness pass. They correspond to register items as follows: D1 → register D1,
D2 → register D2, D3 → register D5, D4 → register D6/D7 and approval A8. Register
D3 (Brevo SMTP) and D4 (production AI disabled) were resolved by the architecture
lock and are not open here.

## 1. Repository state (observed 2026-11-12)

| Item | Value |
|---|---|
| Repository | `/data/MyFarmAI` |
| Branch | `phase-01-foundation` |
| HEAD | `6393c2b680bb13734a407b4f74f1bd9050e80e89` (`6393c2b`) |
| HEAD date / subject | 2026-11-11 15:55 +05:30 — `docs(release): record shipped commit and exact owner deployment procedure` |
| Upstream | `origin/phase-01-foundation`, **in sync** (0 ahead / 0 behind) |
| Working tree | **dirty — intentional, preserved, not committed** |

Changed (tracked):

| File | Change |
|---|---|
| `backend/app/api/v1/downloads.py` | 1 line — `GET` route becomes `GET`+`HEAD` |
| `backend/tests/test_downloads.py` | +16 lines — HEAD returns headers, empty body |
| `CHANGELOG.md` | +36 lines — Unreleased entries for audit, blockers, lock |
| `docs/deployment/CLOUD_DEPLOYMENT_PLAN.md` | +4 lines — superseded-by-audit note |
| `docs/deployment/FREE_TIER_COMPARISON.md` | +5 lines — re-check note |

Untracked (new):

| File | Purpose |
|---|---|
| `docs/architecture/MYFARMAI_CLOUD_V1_LOCK.md` | Locked architecture record |
| `docs/deployment/MYFARMAI_CLOUD_DEPLOYMENT_RUNBOOK.md` | Proposed deploy procedure |
| `docs/deployment/MYFARMAI_CLOUD_PROVIDER_AUDIT.md` | Provider decision evidence |
| `docs/deployment/MYFARMAI_POST_AUDIT_STAGE_2.md` | Quota/credential/deploy evidence |
| `docs/deployment/MYFARMAI_PRODUCTION_BLOCKERS.md` | 13-item blocker register |
| `docs/deployment/MYFARMAI_OWNER_READINESS_CHECKLIST.md` | This document |

Nothing was discarded, reset, stashed, or overwritten.

## 2. Local verification evidence

Run on 2026-11-12 on the working tree above. These checks prove the **local
source** is ready; they do not change any production blocker status.

| Check | Command | Result |
|---|---|---|
| Download + email OTP + config tests | `backend/.venv/bin/python -m pytest tests/test_downloads.py tests/test_email_otp.py tests/test_config_profiles.py -q` | **21 passed in 11.29 s** |
| SMTP delivery + production gate tests | `pytest tests/test_smtp_delivery.py -q` | **17 passed in 0.35 s** |
| Production config gate (dev email mode) | `Settings(environment="production", …).validate_for_environment()` | **1 error**, `email_delivery_mode must be 'smtp' in production` — gate present |
| Production config gate (complete SMTP) | same, with `email_delivery_mode="smtp"`, `smtp_host`, `smtp_from` | **0 errors** |
| Frontend type check | `cd web && npm run typecheck` | **PASS**, no output |
| Frontend lint | `cd web && npm run lint` | **PASS**, "No ESLint warnings or errors" |
| Frontend production build | `cd web && npm run build` | **PASS**, 21 routes, shared JS 103 kB |
| Build artifact | `web/.next/BUILD_ID` | `z291W15L99Xdg7mZI1VT9`, built 2026-11-12 13:19 +05:30 |
| Chunk parity | shared chunk names | `255-b1e2483a7e02feee.js`, `4bd1b696-c023c6e3521b1417.js` — **identical to the recorded 2026-11-11 local build**, so source content is unchanged since that build |
| Live backend origin (read-only GET) | `GET …/health/ready` | **HTTP 200**, 8.42 s (cold) |

Non-blocking build warnings: `next lint` is deprecated in Next 16; Next inferred the
workspace root from a second lockfile (`/data/MyFarmAI/package-lock.json`). Neither
affects the artifact.

Config-gate note: the SMTP gate is enforced at startup in
`app/factory.py:147` (`RuntimeError` when `validate_for_environment()` returns
errors), not inside `validate_production_settings()` alone. Tests of the latter
function will not exercise the email gate.

### Security / secret scan (masked; filenames only)

| Scan | Result |
|---|---|
| `git grep -lE 'npg_[A-Za-z0-9]{8,}'` (Neon key pattern) | **0 files** |
| `git log -S'npg_'` | **0 commits** |
| `git grep -lE 'BEGIN (RSA \|EC \|OPENSSH )?PRIVATE KEY'` | **0 files** |
| `git grep -lE 'xsmtpsib-'` (Brevo SMTP key prefix) | **0 files** |
| DB URLs with embedded password, tracked files | only placeholders (masked `<host-user>-<placeholder>` and local `u:***@127.0.0.1` examples) in docs/skill templates — **no real credential** |
| Tracked `.env*` files | `.env.example`, `android/.env.example` only; `web/.env.local` is git-ignored and contains a relative dev URL only |

No secret value was printed. The documented Neon exposure remains the AppSail
`DATABASE_PATH` value (console-visible), which is why rotation is still required.

## 3. D1 — Catalyst Console readings (owner, read-only)

The agent cannot read billing/usage: the Catalyst MCP exposes no billing tool. This
is the first hard gate; **no deploy may start before it is answered.**

Open <https://console.catalyst.zoho.com> → organisation `60094539808` → project
**Project-Rainfall**. Record numbers only — no URLs, keys, or credentials.

| # | Reading | Where |
|---|---|---|
| D1.1 | AppSail **GB-minutes used this cycle** | Billing → Usage / Reports |
| D1.2 | Cycle start/end and free-tier bar | Billing → Usage / Reports |
| D1.3 | Allocated **memory (MB)** (allocation vs ceiling) | AppSail → `myfarmai-backend` → App Execution Settings |
| D1.4 | **Remaining credits** | Billing → credits |
| D1.5 | **Amount due** and payment-method state | Billing / Zoho Store |
| D1.6 | **Instance count** now; any always-on/min-instance option | AppSail → `myfarmai-backend` → Instances |

Forbidden during D1: logging in to any other service, changing settings, resizing,
restarting, redeploying, enabling billing or a trial, attaching a payment method.

Acceptance: all six readings recorded below. Then the memory decision is made from
data; the 900 GB-minutes/month vs 24/7 hosting conflict stays **OPEN** until the
owner explicitly resolves it.

| Reading | Owner value |
|---|---|
| D1.1 GB-minutes used | |
| D1.2 cycle / free-tier state | |
| D1.3 memory MB | |
| D1.4 credits | |
| D1.5 amount due / payment method | |
| D1.6 instances / always-on | |

## 4. D2 — Neon credential rotation (explicit approval required)

**Why:** the database password was exposed to a screen transcript during the prior
audit. The repository, git history, image layers and temp files are clean, but the
credential must be rotated regardless. It currently lives only in the AppSail
`DATABASE_PATH` environment variable.

**What the owner approves:** permission to rotate the `neondb_owner` role password
in Neon and replace the password segment of `DATABASE_PATH` in AppSail, then restart
the AppSail instance and verify readiness.

**Rules:**
- The owner performs the rotation. **Never paste the password into chat, a ticket, a
  document, a commit, or a log.**
- Copy the new value directly into a password manager, and from there into the
  AppSail console field.
- Change nothing else in Neon (no project, branch, plan, or billing change).
- Do not rotate and deploy a new image in the same window: if readiness fails, the
  cause must be unambiguous (register §2 rule).
- Keep the old env value recorded in the owner's secret store until the new one
  verifies, because an image rollback does not restore environment variables.

**Verification after rotation:** `GET /health/ready` returns 200 with
`"database":"ok"`, then one authenticated login succeeds. The old password is
invalid by definition of the reset.

Exact steps: `MYFARMAI_POST_AUDIT_STAGE_2.md` §2.2.

**Approval:** ☐ approved  ☐ declined  — date: ________  owner: ________

## 5. D3 — Backup custody (owner decision)

Required because Neon Free PITR is only **6 hours** and the only local copy
(`/data/MyFarmAI-backups`, 191 MB) is on the application host.

The owner must choose and record:

| Item | Owner decision |
|---|---|
| **Destination** (off the app host; must stay ₹0) | |
| **Encryption** (age or GPG) | |
| **Key custody** (who holds the private key, where) | |
| **Key-loss recovery method** | |
| **Retention** (proposed: 7 daily, 4 weekly, pre-migration, release-time) | |
| **Restore rehearsal** on a Neon branch — approved? | |
| **R2** | **Not adopted** under `MYFARMAI-CLOUD-V1` — do not enable or create a bucket |

Rules: encrypt before the dump leaves the host; never commit dumps or keys; never
publish to a public bucket or release; do not activate a paid service, subscription,
trial, or recurring payment. A restore rehearsal writes only to a throwaway Neon
branch, never production.

Procedure and retention detail: `MYFARMAI_POST_AUDIT_STAGE_2.md` §5.3–§5.5.

**Approval:** ☐ approved  ☐ declined  — date: ________  owner: ________

## 6. D4 — Release commit approval (explicit approval required)

**Nothing has been committed or pushed.** Current state:

- HEAD: `6393c2b680bb13734a407b4f74f1bd9050e80e89`, in sync with
  `origin/phase-01-foundation`.
- Working tree: 5 modified files, 6 untracked documents (see §1).
- Diff summary: `5 files changed, 62 insertions(+), 1 deletion(-)` across tracked
  files, plus the new documents; the only code change is the one-line `HEAD` route
  in `downloads.py` with its test.

**Evidence that the change is ready:** 38 backend tests passed, frontend
typecheck/lint/build passed, production SMTP gate verified, secret scan clean
(§2).

**Proposed commit scope after approval (two commits, no push of anything else):**

1. `fix(api): serve HEAD for APK downloads` — `downloads.py`,
   `tests/test_downloads.py`.
2. `docs(deploy): lock cloud v1 architecture and record readiness evidence` —
   `CHANGELOG.md`, the 2 superseded-note edits, the 5 new deployment/architecture
   documents, and this checklist.

**What approval authorises:** `git add` of the listed files, the two commits, and
`git push` to `origin/phase-01-foundation`. **Not** authorised: retagging
`v1.0.0`, force-push, deployment, or any change to GitHub releases/settings.

**Approval:** ☐ approved  ☐ declined  — date: ________  owner: ________

## 7. Production blockers (unchanged by this pass)

Local tests passing **closes nothing**. Status against the register:

| Blocker | Status |
|---|---|
| B1 AppSail quota / billing unknown | **OPEN** — needs D1 |
| B2 Live backend logs OTP codes, delivers nothing | **OPEN** — needs backend redeploy |
| B3 Deployed backend not HEAD | **OPEN** — fix is local and tested, not deployed |
| B4 Stale Slate bundle | **OPEN** — needs Slate deploy |
| B5 Neon credential in AppSail config | **OPEN** — needs D2 |
| B6 No off-site backup (6 h PITR) | **OPEN** — needs D3 |
| B7 R2 subscription surface | **RESOLVED — not adopted** (architecture lock) |
| B8 Public `/openapi.json` | **OPEN** — decision |
| B9 AppSail outbound SMTP untested | **OPEN** — needs one real send after deploy |
| B10 Proxy trust for rate limiting unmeasured | **OPEN** |
| B11 AI disabled in production | **OPEN** — publish the limitation |
| B12 Release tag vs deployed artifacts | **OPEN** — needs D4 + release decision |
| B13 Selfie uploads on ephemeral disk | **OPEN** |
| AppSail 900 GB-minutes vs 24/7 hosting | **OPEN** — owner must resolve explicitly after D1 |

## 8. Gate order after approval

1. **D1 answered** → memory decision from console data (B1).
2. **D2 approved and executed** → rotation verified on `/health/ready`.
3. **D4 approved** → commit + push.
4. **D3 approved** → encrypted off-host backup + restore rehearsal.
5. Only then: backend rebuild/redeploy from the approved commit (A3), one real OTP
   send (A4/B9), Slate deploy (A5/B4), hardening (B8, B10, B11, B13).

Steps 1–3 are the minimum before any deploy. Each action remains separately gated;
approval of one item does not authorise the next.

## 9. Sign-off

| Decision | Answer | Date | Owner |
|---|---|---|---|
| D1 Catalyst readings + memory decision | | | |
| D2 Neon rotation | | | |
| D3 Backup destination + custody | | | |
| D4 Commit and push | | | |
