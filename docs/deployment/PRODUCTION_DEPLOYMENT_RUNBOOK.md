# MyFarmAI — Production Deployment Runbook

**Document ID:** MYFARMAI-DEP-011
**Version:** 1.0
**Date:** 2026-11-11
**Audience:** release engineer with authenticated access to the MyFarmAI Catalyst project

Companion documents: `docs/deployment/DEPLOYMENT_RUNBOOK.md` (command-level detail),
`docs/release/ROLLBACK_PROCEDURE.md`, `docs/deployment/PRODUCTION_ARCHITECTURE.md`.

## 1. Preconditions

- Catalyst CLI available and authenticated as a project member.
- Project `90779000000015001`, org `60094539808`, environment `Development`.
- Slate app `myfarmai-web` (`37777000000005001`), AppSail app `myfarmai-backend`.
- Repository at the release commit, clean tree, `VERSION` = manifest versions.
- All local gates green (§2).

## 2. Local gates before any deploy

```bash
cd backend && .venv/bin/python -m pytest tests/ -q
cd web && npm run typecheck && npm test -- --runInBand && npm run lint && npm run build
cd android && npm run typecheck && npm run lint
```

Expected: backend 313 passed; web 44 passed; typecheck/lint/build clean.
Do not deploy on a red gate.

## 3. Web deployment (Slate)

```bash
cd deploy/catalyst-staging
npx -y zcatalyst-cli deploy slate myfarmai-web
```

Notes:

- `web/next.config.js` bakes the API origin at build time (`MYFARMAI_API_ORIGIN`, else the
  AppSail fallback). If the backend hostname changes, update it first.
- Slate serves the uploaded build. It is **not** linked to Git: the app is `app_type: cli`
  and the deployment has `auto_deploy: false`. A `redeploy` re-builds the previously
  uploaded source, so it cannot pick up new commits.

## 4. Backend deployment (AppSail)

1. Build the image (`linux/amd64`) from `backend/Dockerfile`.
2. Optionally add the APK layer for `GET /api/v1/downloads/app-release.apk` (`PUBLIC_DIR`).
3. Smoke-validate settings with `Settings(...).validate_for_environment() == []`.
4. Deploy detached with the CLI (`deploy appsail --source docker-archive://… --port 8000`).
5. Verify (§5).

Environment variable **names** the production image needs (values never printed):

| Variable | Required | Purpose |
|---|---|---|
| `ENVIRONMENT` | yes | `production` enforces secure cookies and config validation |
| `DATABASE_PATH` | yes | PostgreSQL URL (normalised to `DATABASE_URL` internally) |
| `ALLOWED_HOSTS` | yes | Host header allow-list |
| `CORS_ALLOWED_ORIGINS` | yes | Slate origin only |
| `TRUSTED_PROXY_CIDRS` | yes | Makes `X-Forwarded-For` trustworthy only behind the platform proxy |
| `PUBLIC_DIR` | for APK | Directory served by the downloads router |
| `OLLAMA_BASE_URL` | for AI | Empty/absent disables AI |
| `SEARXNG_BASE_URL` | for research | Absent makes research return 503 |
| `EMAIL_DELIVERY_MODE` | yes | Must be `smtp`. **Production startup fails** for any other value. |
| `SMTP_HOST` | yes | Relay hostname. Startup fails if blank. |
| `SMTP_PORT` | yes | `587` (STARTTLS). Port 465/implicit TLS is not supported. |
| `SMTP_USER` / `SMTP_PASSWORD` | conditional | Relay credentials; omit only for an unauthenticated relay. |
| `SMTP_FROM` | yes | Sender address the relay is authorised to use. Startup fails if blank. |
| `OAUTH_GOOGLE_CLIENT_ID` / `_SECRET` | optional | OAuth sign-in |

**Deployment order is mandatory:** set the SMTP variables *before* deploying. The new
image refuses to start a production instance with `EMAIL_DELIVERY_MODE=dev` or a blank
`SMTP_HOST`/`SMTP_FROM`, so a deploy that skips this step takes the API down.
See `docs/deployment/SMTP_SETUP.md`.

### 4.1 First administrator (after the API is healthy)

There is no seeded administrator and no API route that creates one. Run once against the
production database, from `backend/`:

```bash
.venv/bin/python scripts/create_admin.py --email owner@example.com
```

Password is prompted (8–128 chars) and never printed. Full procedure:
`docs/security/ADMIN_ACCOUNT_PROCEDURE.md`.

## 5. Post-deploy verification (all must be observed)

| # | Check | Expected |
|---|---|---|
| 1 | `GET /health/live` | 200 |
| 2 | `GET /health/ready` | `database: ok` |
| 3 | `GET /` | `version: "1.0.0"` (currently reports `0.1.0` — stale image) |
| 4 | `POST /api/v1/auth/logout` | 204, `Set-Cookie: …; Secure` |
| 5 | `GET /api/v1/app-updates/latest` | `latest_version: "1.0.0"` |
| 6 | Web `/download` | 200, checksum present |
| 7 | Web `/landing` | 200 |
| 8 | APK link | 200, 67,884,479 B |
| 9 | Register → receive code by email → verify | 200 + session |
| 10 | `GET /api/v1/verification/admin/pending-users` with an admin session | 200, list |
| 11 | Web `/` response headers | `Content-Security-Policy` present |
| 12 | Chat with AI enabled | 200 with model output |

## 6. Why this host cannot deploy (evidence, 2026-11-11)

This is recorded so the blocker is not re-litigated on every release:

| Check | Result |
|---|---|
| `catalyst` / `zcatalyst-cli` on PATH | absent |
| Catalyst credentials / token file | absent |
| Slate app `myfarmai-web` | `app_type: "cli"`, `auto_deploy: false`, `build_meta: {}` |
| Slate deployment `37777000000005003` | `type: "cli"`, no repository binding |
| Slate MCP tools available | 9 — list apps, get app, list deployments, get deployment, redeploy, rollback, list/create env vars, cancel build. **No source upload.** |
| `Redeploy_a_deployment` | accepts a `commit_id`, but with no linked repo it rebuilds the same uploaded source |

**Conclusion:** deploying the current tree requires the Catalyst CLI from an authenticated
machine. The web fixes (MFAI-013/014/016/017), the auth fix (`6976a3f`), and the new
`/download` route are therefore in the repository but **not live**.

## 7. Owner actions

1. Set the SMTP variables from `docs/deployment/SMTP_SETUP.md` **before** deploying — the API will not start without them.
2. Run §3 from a machine with the Catalyst CLI authenticated.
3. Run §4 if the backend also needs updating (it does — it predates `6976a3f`).
4. Run §4.1 to create the first administrator.
5. Re-run §5 and record the results in `docs/testing/FINAL_RELEASE_TEST_RESULTS.md`.
