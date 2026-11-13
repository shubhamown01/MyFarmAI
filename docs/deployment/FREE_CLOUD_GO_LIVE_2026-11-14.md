# MyFarmAI — Free Cloud Go-Live (Render + Slate + Neon)

Status: **READY TO DEPLOY — owner account steps required.** Prepared 2026-11-14.
This supersedes the Catalyst-only plan for the public launch because the live
AppSail backend is down (`503`) and the free allowance cannot sustain 24/7.

## 1. Why this path

- The public backend `myfarmai-backend-...catalystappsail.in` returns `503`
  (`Execution failed. Please check the startup command or port.`).
- Catalyst's free AppSail allowance is **900 GB-min/month**. At 2048 MB that is
  ~7.5 h/month; at 256 MB ~60 h/month. A 24/7 month needs 12–96× that.
- Render Free is the only no-card host verified to run the **unchanged Docker
  image** with FastAPI + Neon + outbound HTTPS. It sleeps after ~15 min idle
  (first request ~30–60 s). That is the one performance compromise.

## 2. Stack (all ₹0, no card)

| Layer | Provider | Notes |
|---|---|---|
| Web | Catalyst Slate | already live at `myfarmai-web-zwpytbwu.onslate.in` |
| API | **Render Free** (Docker) | `backend/Dockerfile`, health `/health/live` |
| DB | Neon Free | existing; copy the pooled connection string |
| Email | **Brevo Free** HTTP API | 300 emails/day; SMTP ports are blocked on Render |
| AI | **Gemini free tier** | OpenAI-compatible; key from AI Studio |
| APK | GitHub Releases | unchanged |

## 3. Code changes in this branch

- `backend/app/ai/gemini.py` + `build_gateway()` — `AI_PROVIDER=auto|gemini|ollama`.
- `backend/app/services/delivery.py` — `BrevoEmailDelivery` (`EMAIL_DELIVERY_MODE=brevo`).
- `backend/app/factory.py` — selects the gateway; readiness reports `ai`.
- `backend/app/core/config.py` — `GEMINI_*`, `BREVO_*` settings + production validation.
- `backend/Dockerfile` — listens on `$PORT` (Render injects it).
- `render.yaml` — one-click blueprint.

## 4. Owner setup (≈15 min, no card)

1. **Render** — sign in with GitHub (`shubhamown01`) → *New → Blueprint* → select
   `shubhamown01/MyFarmAI`, branch **`phase-01-foundation`**. Render reads
   `render.yaml`.
2. **Neon** — copy the pooled connection string (no `?sslmode` query) → Render env
   `DATABASE_PATH`.
3. **Gemini** — <https://aistudio.google.com/app/apikey> → create key → Render env
   `GEMINI_API_KEY`.
4. **Brevo** — <https://app.brevo.com> → create a free account → verify a sender
   (your email or domain) → *SMTP & API → API Keys* → v3 key → Render env
   `BREVO_API_KEY` and `BREVO_SENDER`.
5. Click **Apply / Deploy**. Wait for the build (Docker) and `/health/live` 200.

Render shows the final host (e.g. `myfarmai-backend-xxxx.onrender.com`). The
blueprint already allows `*.onrender.com`.

## 5. Point the web at the new API

In the Catalyst console → Slate `myfarmai-web` → Environment Variables:

```
MYFARMAI_API_ORIGIN = https://<render-host>
```

Save, then redeploy the Slate app. The Next.js proxy sends `/api/v1/*` to Render;
the browser stays same-origin, so CORS is not involved.

## 6. Verify (all must pass)

```bash
API=https://<render-host>
curl -sS $API/health/live      # 200 {"status":"ok"}
curl -sS $API/health/ready     # 200 database:ok, ai:ok (or disabled)
curl -sS $API/                 # version 1.0.0
curl -sS https://myfarmai-web-zwpytbwu.onslate.in/ | grep -o '<title>[^<]*'
curl -sS https://myfarmai-web-zwpytbwu.onslate.in/api/v1/health/ready
```

### 6.1 Create the first admin (one-time, required)

There is no seeded admin, and only an admin can approve the selfie queue. From
`backend/` with the Neon `DATABASE_PATH` exported:

```bash
DATABASE_PATH='postgresql://...' .venv/bin/python scripts/create_admin.py \
  --email sb95146@gmail.com --full-name "Owner"
```

It prompts for a password (8–128 chars), creates or promotes the account, and
sets it `active`. Log in with that account, then approve new users under
`/api/v1/verification/admin/queue` (or the admin web page).

### 6.2 Real journey

Request an OTP → receive it in the test mailbox → verify → upload the selfie
challenge → approve in the admin queue → log in → create a farm.

## 7. Known limits (state them publicly)

- Render free sleeps after ~15 min idle; the first request is slow.
- Selfies are stored on the container's ephemeral disk (`/tmp`); a restart loses
  *pending* selfies. Approved users are in Neon and unaffected.
- New accounts stay `pending_verification` until the owner approves them in the
  admin queue. This is the DPDP/biometric safeguard, not a bug.
- Gemini free tier has per-minute/day limits; the existing per-user quota
  (`CLOUD_AI_QUOTA_LIMIT=20 / 10 h`) is the cost brake.

## 8. Rollback

Render keeps the previous deploy; *Deploys → Rollback*. Repoint
`MYFARMAI_API_ORIGIN` to the previous backend if needed. Neon is unchanged.

## 9. If Render is not acceptable

The only other ₹0 option that keeps AI working is running the local stack
(`backend` + `postgres` + `ollama`, all healthy here) behind a Cloudflare Tunnel.
It requires this machine to stay on 24/7 and a stable hostname (a domain), so it
is a fallback, not the launch plan.