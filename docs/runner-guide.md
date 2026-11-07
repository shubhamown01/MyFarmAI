# MyFarmAI Runner Guide — one-command local stack

**Status: verified 2026-11-03** (start / stop / restart / status / AI inference — see end of file for evidence notes).

One VS Code folder (`/data/MyFarmAI`), one command:

```bash
./RUN_MYFARMAI.sh            # start everything (mode: local)
./RUN_MYFARMAI.sh --open-browser   # ... and open http://localhost:3000
./STOP_MYFARMAI.sh           # stop (data preserved)
./RESTART_MYFARMAI.sh        # safe restart
./STATUS_MYFARMAI.sh         # health dashboard
./BACKUP_MYFARMAI.sh [--verify]    # pg_dump + repo snapshot to /data/MyFarmAI-backups
./DEPLOY_MYFARMAI.sh         # rebuild + restart local stack with preflight/health gates
```

From VS Code: `Terminal → Run Task…` → "MyFarmAI: Start complete application" (plus stop/restart/status/log/test tasks in `.vscode/tasks.json`).

## What runs (architecture — unchanged, only orchestrated)

| Service | Where | Address | Notes |
|---------|-------|---------|-------|
| PostgreSQL 17 | Docker Compose | internal only (never published) | volume `postgres_data`; password via Docker secret `backend/.pg_password` |
| FastAPI backend | Docker Compose | http://127.0.0.1:8000 | **loopback-only** host port; `/health/live`, `/health/ready`, docs at `/docs` |
| Web (Next.js) | host dev server | http://localhost:3000 | proxies `/api/v1` → backend; log `logs/web-dev.log` |
| Ollama + `qwen3:4b` | **host, reused** | http://127.0.0.1:11434 | never duplicated; bridged into Docker by `scripts/ollama-bridge.sh` (socat on the docker0 gateway; backend uses `host.docker.internal:11434`) |
| Android (Expo) | separate process, **not** started by the runner | see below | own lifecycle |

Startup order: PostgreSQL → health → Alembic migrations → backend (live+ready gates) → web (HTTP gate) → integration checks → **real AI inference smoke test**.

## Modes (directive §13)

- `local` (default) / `development` — everything above. Nothing is exposed publicly.
- `public-demo` / `production` — **refuse to run** until the owner completes the E6 gates: configured domain (DuckDNS or similar), TLS reverse proxy (Caddy / Cloudflare Tunnel), and security review. Public exposure always requires an explicit separate action.

## Environment variables

`.env` (gitignored) is created from `.env.example` on first run if missing. Defaults work out of the box for local mode. Owner-supplied values (never invented by scripts):

- `OLLAMA_MODEL` (default `qwen3:4b`), `OLLAMA_TIMEOUT_SECONDS`
- `CORS_ALLOWED_ORIGINS` — lock down before any public exposure
- `OAUTH_GOOGLE_CLIENT_ID` / `..._SECRET`, `OAUTH_MICROSOFT_...` — empty keeps OAuth disabled (owner blocker B1)
- `EMAIL_DELIVERY_MODE=dev` — OTP codes are logged, never actually emailed (owner blocker B2)
- Web: `web/.env.local` → `NEXT_PUBLIC_API_BASE_URL` (default `/api/v1` same-origin proxy)

Never print or commit secrets. `backend/.pg_password` is a Docker secret file.

## Troubleshooting

| Symptom | Check / fix |
|---------|-------------|
| `docker: permission denied` | `sudo usermod -aG docker $USER`, re-login |
| Port 8000/3000 already in use | runner reuses the running service; kill the other process if unintended: `ss -tlnp \| grep -E '3000\|8000'` |
| AI smoke test fails | `ollama serve` running? `ollama pull qwen3:4b`? bridge listening? `bash scripts/ollama-bridge.sh`, then `docker compose logs backend` |
| Backend unhealthy | `docker compose logs backend`; migrations log: `logs/migrations.log` |
| Web not responding | `tail -50 logs/web-dev.log` |
| DB "did not become healthy" | `docker compose logs postgres`; data is in volume `postgres_data` — never use `down -v` |
| Model missing / disk low | runner warns and refuses risky pulls; check `df -h /data` and `free -h` |
| "OTP did not arrive" | Dev mode (**default until owner provides a provider**) sends NO real email — the code is written to `backend/data/dev_otp_outbox.txt` on the host and logged in backend logs. The register page shows this hint. Real email = owner supplies SMTP creds (blocker B2). |
| "Could not send the code" | Backend returned an error: `docker compose logs backend --since 5m`. A 429 means the 60 s resend cooldown is active — use the Resend button countdown. |
| Signed in but `/onboarding` keeps redirecting to login (401 on `/me/onboarding`) | Session cookie was not set: in dev, `web/.env.local` must use a RELATIVE `NEXT_PUBLIC_API_BASE_URL=/api/v1` (same-origin proxy). An absolute `http://localhost:8000/...` is cross-origin from :3000, so the browser drops the Set-Cookie (SameSite=Lax). The proxy target is `MYFARMAI_API_ORIGIN` in `next.config.js`. |

## Android development (separate)

```bash
cd android && npm install && npm start   # Expo dev server — own lifecycle
```

Backend address for Android (`android/src/config/api.ts`): emulator → `http://10.0.2.2:8000`, physical phone → your laptop's LAN IP (`ip -4 addr`), public deployment → the approved HTTPS URL. **Never `localhost` on a physical device.** Starting the web stack does not install or launch the Android app.

## Log locations

`logs/` — `web-dev.log`, `docker.log`, `migrations.log`, `ai-smoke.log`. Logs never intentionally contain passwords, tokens, OTP values, or raw selfies (dev OTP outbox: `/tmp/opencode/dev_otp_outbox.txt`, clearly marked).

## Evidence (2026-11-03, all executed on this repository)

- **RUN from fully-stopped state** — EXIT=0, 17/17 checks OK, zero warnings: preflight, postgres healthy, migrations idempotent, backend live+ready, web live, frontend→backend proxy 200, **real AI inference** (Tier 1 container→Ollama bridge 200 + Tier 2 actual `qwen3:0.6b` generation), DB read test. Model verified is whatever `OLLAMA_MODEL` in `.env` specifies (currently `qwen3:0.6b`; preflight checks it and never auto-pulls).
- **RUN from partial state** (postgres already up) — PASS, services reused not duplicated.
- **Repeated RUN** — idempotent (three consecutive cycles).
- **STOP** — compose containers `Exited (0)`; `myfarmai_postgres_data` volume preserved; unrelated host containers byte-identical before/after; web dev server fully killed (cwd-verified process-group kill — port 3000 released).
- **RESTART** — PASS twice (EXIT=0, 20 OK each).
- **DB persistence across restart** — marker row survived three stop/start cycles, then removed (net-zero change; no user data touched).
- **AI note**: `/api/v1/chat` is auth-gated (Phase 3). The runner verifies bridge connectivity + real model inference; full end-to-end authenticated chat through the API runs when `MYFARMAI_SMOKE_EMAIL`/`MYFARMAI_SMOKE_PASSWORD` are set in `.env` (documented above) or via the web UI.
- **Web gate**: typecheck ✓ · 40 jest tests ✓ · ESLint ✓ · production build ✓ (routes: `/auth/login`, `/auth/register`, `/auth/callback`, `/onboarding`).
- **Backend gate**: 270 pytest passed; mypy 111 pre-existing (0 in new files).
- Scripts: `bash -n` clean on all six.
