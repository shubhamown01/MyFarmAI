# Cloud Account Inventory (live-verified)

Owner account: `sb95146@gmail.com` (Gmail session authenticated in the automation
browser). Updated: 2026-11-03 (Phase A discovery run). Nothing below is assumed;
each entry states the verification method.

## Provider-by-provider state

| Provider | Verified via | State | Notes |
|---|---|---|---|
| Google Cloud (`console.cloud.google.com`) | Automation browser (2026-11-03) | ✅ Authenticated | GCP ToS accepted (owner-approved); project **`myfarmai-513615`** exists (created this date); billing NOT enabled; OAuth client "Web client 1" + test user live; the $300 free-trial dialog was dismissed and never activated — no trial credits, no billing |
| Cloudflare (`dash.cloudflare.com`) | Automation browser (2026-11-03) | ✅ **Account created** | Owner approved SSO signup (Cloudflare ToS gate); path: sign-up → Continue with Google → chooser → consent (name/profile/email) → **Account home live** — "Sb95146@gmail.com's Account", account ID `5b769d9f3898d979c35200c5c22fc897`. No Cloudflare terms screen was shown during Google SSO signup (disclosed honestly — SSO signup itself implies the terms; owner approval recorded in this run). No password was created (SSO identity). Pages/Workers free quotas still to inspect. |
| AWS (`console.aws.amazon.com`) | Automation browser (2026-11-03) | ⛔ RULED OUT by owner | Console navigation hung >60s ×3 and crashed the automation session earlier; owner instructed (2026-11-03) that AWS discovery is **ruled out — do not retry**. AWS stays BLOCKED/UNVERIFIED for the deployment plan; an AWS sign-in tab exists in the user's browser untouched. Any future AWS use requires a fresh owner decision. |
| Neon (`neon.com` / `console.neon.tech`) | Automation browser (2026-11-03) | ✅ **Account created** | Owner approved SSO signup; no card/billing touched. Path: signup page → Google SSO (`sb95146@gmail.com`) → consent (name/profile, email) → Console live, org id `org-fragrant-cell-14431918`. No verification screen encountered; signup page's ToS notice ("By creating an account you agree…") constitutes agreement (disclosed honestly). **No project/database created** — needs separate approval per the deployment plan. Onboarding wizard untouched. |
| GitHub (`github.com`) | GitHub MCP (2026-11-04) | ✅ **Authenticated** | Account **`shubhamown01`** (id 199487470, Shubham Baghel; created 2025-02-16 — pre-existing, no duplicate signup needed). Owner instruction: `sb95146@gmail.com` is the sign-in identity for every service. MCP token configured (scope to be verified at first repo push). |
| Supabase (`supabase.com`) | Not yet inspected | ❔ | Phase C target |
| Prisma Postgres (`console.prisma.io`) | Not yet inspected | ❔ | Evaluated as alternative |
| Koyeb / Netlify / Vercel / HF Spaces / UppCoder | Not yet inspected | ❔ | Priority-5 evaluation target |
| Zoho Catalyst (`console.catalyst.zoho.in`) | Automation browser (2026-11-03/04) | ✅ **Account + first project created** | SSO as `sb95146@gmail.com`, org id `60094539808`. Onboarding wizard completed 2026-11-04 (no payment plan selected — the $250-credits "configure payment method" prompt was left untouched, card required → policy-BLOCKED). **Project-Rainfall** created (id `90779000000015001`, Development env; services: Slate, Serverless, Cloud Scale, Zia, Pipelines, CodeLib). Student terms verified from official pages: $250/6-month usage, no card, no subscription, app *stopped* (never auto-charged) at threshold; free tier "Card required: None", monthly renewal forever. ⚠️ Overage risk: ₹300/month minimum billing per project if free limits exceeded — keep usage in free tier, delete unused projects. **AppSail `myfarmai-backend` deployed 2026-11-04** (id `90779000000018005`, custom runtime, port 8000, 2048 MB default): staging URL `https://myfarmai-backend-50047414881.development.catalystappsail.in`, `/health/live` = 200. DB endpoints 503 until Neon `DATABASE_URL` wiring. Deploy via CLI docker-archive Path B (93 MB tar, 25-min window). Test apps `smoke-test`/`smoke-test-2` deleted. |

## Repositories of truth inside the project

- Runner scripts: `RUN_/STOP_/RESTART_/STATUS_MYFARMAI.sh` exist and are verified
  (docs/runner-guide.md, 2026-11-03). **`BACKUP_MYFARMAI.sh` and `DEPLOY_MYFARMAI.sh` do not exist yet.**
- `backend/.env` (git-ignored) holds: `OAUTH_GOOGLE_CLIENT_ID/SECRET` (Google OAuth,
  Testing mode — only the listed test user `sb95146@gmail.com` can sign in).
- `docs/deployment/` — created this phase (this file is the first entry).
- Docker Compose stack: postgres + backend (loopback-only 8000), web dev server on
  host :3000, host Ollama reused via docker0 bridge. Secrets model: pg password via
  compose secret file, OAuth creds via git-ignored env file.

## Known constraints (measured)

- Host RAM: 7 GiB total, ~6.6 GiB in use with the dev stack running (tight; no
  room for heavyweight additional AI models — `qwen3:0.6b` current).
- Disk `/data`: 98 GiB free of 274 GiB — no disk pressure.
- GPG available (`/usr/bin/gpg`); `~/Desktop` does not exist yet — Phase B creates
  `~/Desktop/MyFarmAI_Secure_Backup/` only after owner request.

## Incident log (transparency)

- 2026-11-03: AWS console navigation hung (3 navigation timeouts at 30–60 s) and
  the shared automation browser session dropped its tabs (recovered functional but
  on a fresh context). User-facing tabs were on a real profile; no data was
  deleted, but the session reset may require the owner to re-focus their Chrome
  window. AWS discovery deferred pending owner input or a retry approval.
