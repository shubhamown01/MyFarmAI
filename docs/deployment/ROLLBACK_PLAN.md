# MyFarmAI — Rollback Plan (public live testing)

Status: **ACTIVE** (2026-11-08). Companion: `DEPLOYMENT_RUNBOOK.md`.

## Principles
- Every deploy artifact is tagged (`myfarmai-backend:c<commit>`,
  `:prod-<commit>`); the previous known-good image always stays on disk in
  `/tmp/opencode/backend-image-*.tar`.
- Rollbacks are re-deploys of the previous artifact — no manual edits.

## Backend rollback
Keep the last GOOD image tar before any new deploy. Rollback:
```bash
cd /data/MyFarmAI/deploy/catalyst-staging
NODE_OPTIONS="--dns-result-order=ipv4first" setsid nohup timeout 4500 \
  npx -y zcatalyst-cli deploy appsail --name myfarmai-backend \
  --source docker-archive:///tmp/opencode/backend-image.tar --port 8000 \
  > /tmp/opencode/appsail-deploy.log 2>&1 < /dev/null &
```
Verify with the runbook's step-4 checks. Known-good artifacts as of
2026-11-08: `c71737f5` (pre-production) and `prod-4b1acc5` (production
env + public APK route).

## Web rollback
Redeploy the previous commit of `web/`:
```bash
cd /data/MyFarmAI && git checkout <good-sha> -- web/
cd web && npm run build && cd ../deploy/catalyst-staging && \
  npx -y zcatalyst-cli deploy slate myfarmai-web
```
Known-good: `958b912` (landing + legal pages + logout wiring).

## Database
- Neon Postgres is a managed branch; never destructive op without owner
  approval and a verified backup (pgdump via Neon console — owner action).
- Migrations to date are additive only; rolling back a migration requires
  a DB-level restore by the owner (documented gate).

## Android
Uninstall the app from the device (`adb uninstall com.myfarmai.android` or
long-press → Uninstall) and re-install the good APK from the public URL.

## Common failure → action
| Symptom | Action |
|---|---|
| `/health/ready` 503 after backend deploy | Check `appsail-deploy.log` for boot errors; if a validate_for_environment error, rollback the image (the smoke-test step catches it pre-deploy). |
| Web 500 on `/api/v1/*` | Proxy target wrong → check `MYFARMAI_API_ORIGIN` / production fallback in `next.config.js`, redeploy web. |
| APK 404 | `PUBLIC_DIR` missing in the image layer → verify ENV in the running image, redeploy. |
| Cookie lacks `Secure` | `ENVIRONMENT` not `production` at runtime → verify env, redeploy. |
