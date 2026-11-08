# MyFarmAI — Deployment Runbook (public live testing)

Status: **ACTIVE** (2026-11-08). Companion: `PUBLIC_DEPLOYMENT_PLAN.md`,
`ROLLBACK_PLAN.md`, `../security/PUBLIC_DEPLOYMENT_SECURITY_CHECKLIST.md`.

## Live URLs
| Piece | URL |
|---|---|
| Web | `https://myfarmai-web-zwpytbwu.onslate.in` (landing `/landing`, legal `/legal/privacy`, `/legal/terms`) |
| Backend | `https://myfarmai-backend-50047414881.development.catalystappsail.in` |
| APK | `https://myfarmai-backend-50047414881.development.catalystappsail.in/api/v1/downloads/app-release.apk` (same-origin via web: `/api/v1/downloads/app-release.apk`) |

## Web deploy (Catalyst Slate, ~2 min)
```bash
cd /data/MyFarmAI/deploy/catalyst-staging
npx -y zcatalyst-cli deploy slate myfarmai-web
```
Requirements beforehand: `web/` builds clean (`npm run typecheck && npm run
lint && npm run build` in `web/`). The `/api/v1` proxy target is baked at
build time (`web/next.config.js`: `MYFARMAI_API_ORIGIN` env or the
production fallback to the AppSail URL — change that constant if the
backend URL changes).

## Backend deploy (Catalyst AppSail, ~15–25 min, detached)
1. Build the app image from the repo (APK binary is NOT in git; copy it in
   at build time for the derived layer):
```bash
cd /data/MyFarmAI/backend
docker build --platform linux/amd64 -t myfarmai-backend:c<AISHORT> -f Dockerfile .
# Optional public-APK layer (B-3):
mkdir -p /tmp/opencode/apibuild/public
cp /data/MyFarmAI/android/android/app/build/outputs/apk/release/app-release.apk \
   /tmp/opencode/apibuild/public/
cat > /tmp/opencode/apibuild/Dockerfile <<'EOF'
FROM myfarmai-backend:c<AISHORT>
ENV ENVIRONMENT=production \
    ALLOWED_HOSTS=<backend-host>,localhost \
    CORS_ALLOWED_ORIGINS=https://<slate-host> \
    TRUSTED_PROXY_CIDRS=10.0.0.0/8,172.16.0.0/12,192.168.0.0/16 \
    PUBLIC_DIR=/app/public
USER appuser
COPY --chown=10001:10001 public /app/public
EOF
cd /tmp/opencode/apibuild && docker build --platform linux/amd64 -t myfarmai-backend:prod-<AISHORT> .
docker save myfarmai-backend:prod-<AISHORT> --output /tmp/opencode/backend-image-prod.tar
```
2. Smoke-validate before deploying (seconds): run the image's python with
   `Settings(database_path='postgresql://u:p@127.0.0.1/db',
   ollama_base_url='')` and confirm `validate_for_environment() == []`.
3. Deploy (detached — do not run to completion in a foreground shell):
```bash
cd /data/MyFarmAI/deploy/catalyst-staging
NODE_OPTIONS="--dns-result-order=ipv4first" setsid nohup timeout 4500 \
  npx -y zcatalyst-cli deploy appsail --name myfarmai-backend \
  --source docker-archive:///tmp/opencode/backend-image-prod.tar \
  --port 8000 > /tmp/opencode/appsail-deploy.log 2>&1 < /dev/null &
```
4. Verify (all must be observed):
   - `GET /health/live` + `GET /health/ready` → 200, `database: ok`, `ollama: disabled`.
   - `POST /api/v1/auth/logout` → 204 with `Set-Cookie: myfarmai_session=…; Secure` (prod flag).
   - `POST /api/v1/auth/login` with wrong creds → 401 `INVALID_CREDENTIALS`.
   - With APK layer: `GET /api/v1/downloads/app-release.apk` → 200 and `cmp` vs the built APK passes.

## Secrets handling
Connection strings/OTP settings live ONLY in the AppSail console
(Configuration → Environment Variables). Never commit anything from there.
The built image contains NO user data (`.dockerignore` blocks `.env`,
`.env.*`, `data/`).

## Android APK build
See `docs/testing/ANDROID_TESTING_MASTER_PLAN.md` for the full recipe; short form:
```bash
cd /data/MyFarmAI/android/android
EXPO_PUBLIC_API_BASE_URL=<backend-url> JAVA_HOME=/data/JDKs/jdk-17.0.21+9 \
GRADLE_USER_HOME=/data/gradle setsid nohup ./gradlew assembleRelease \
  -PreactNativeArchitectures=arm64-v8a --no-daemon \
  -Dorg.gradle.jvmargs="-Xmx2048m -XX:MaxMetaspaceSize=512m" \
  -Dkotlin.compiler.execution.strategy=in-process -Dorg.gradle.workers.max=2 \
  > /tmp/opencode/gradle-release.log 2>&1 < /dev/null &
```
Artifact: `android/android/app/build/outputs/apk/release/app-release.apk`.
