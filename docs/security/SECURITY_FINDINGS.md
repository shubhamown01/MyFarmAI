# MyFarmAI — Security Findings (V1.0.0)

- **Audit date:** 2026-11-10
- **Scope:** see `SECURITY_AUDIT_PLAN.md`
- **Status legend:** `FIXED` (verified in source/tests) · `OPEN` (owner action) · `DEFERRED` (owner decision) · `FALSE POSITIVE` · `OUT OF SCOPE`

## Summary

| Severity | Total | Fixed | Open/deferred | Accepted | False positive / N/A |
|---|---:|---:|---:|---:|---:|
| Critical | 0 | 0 | 0 | 0 | 0 |
| High | 2 | 2 | 0 | 0 | 0 |
| Medium | 13 | 5 | 8 | 0 | 0 |
| Low | 12 | 0 | 6 | 2 | 4 |
| Info | 3 | 0 | 0 | 0 | 3 |

No unresolved Critical finding was identified. Both High findings are fixed in
source; one still requires redeployment to staging/production before the exposure
is closed in a running environment.

---

## High

### SEC-001 — Unauthenticated feedback listing exposed all submissions

- **Component:** Backend API, feedback
- **File:** `backend/app/api/v1/feedback.py:61-72` (pre-fix `GET ""`)
- **Severity:** High · **Confidence:** Confirmed · **Status:** `FIXED` (deployed and re-tested 2026-11-10)
- **Reproduction (pre-fix):**
  `curl -s "https://myfarmai-backend-50047414881.development.catalystappsail.in/api/v1/feedback?limit=2"`
  returned HTTP 200 with `{"items":[...],"count":N}` and no authentication.
- **Evidence:** staging response captured 2026-11-10 (`/tmp/opencode/audit/staging_resp.json`); local source review confirmed the route had no `Depends(get_current_user_id)` and no admin role check. The docstring itself stated it "should be toggled behind admin auth before production release".
- **Impact:** Anyone who knew the URL could read every tester feedback message and optional reply email. Low direct account impact, but real PII/confidentiality exposure and a clear authorization failure.
- **Likelihood:** High (no preconditions; staging was live).
- **Repair:** `GET /api/v1/feedback` now requires an authenticated session and the `admin` role (`ADMIN_REQUIRED`), reusing the `get_current_user_id` dependency and the user role model. Submission remains public by design.
- **Regression test:** `backend/tests/test_feedback.py` (anonymous → 401, non-admin → 403, admin → 200) and `backend/tests/test_feedback_list.py`.
- **Verification:** 310 backend tests pass. After redeploy, live anonymous
  `GET /api/v1/feedback` returns `401 NOT_AUTHENTICATED` (2026-11-10).

### SEC-002 — Vulnerable Starlette/FastAPI stack (multipart and request-parsing DoS)

- **Component:** Backend dependencies
- **File:** `backend/uv.lock` (pre-fix `starlette 0.38.6`, `fastapi 0.115.0`)
- **Severity:** High · **Confidence:** Confirmed · **Status:** `FIXED` (deployed); residual Medium documented
- **Advisories affecting the pre-fix stack:**
  - CVE-2024-47874 — multipart form DoS (fixed 0.40.0)
  - CVE-2025-54121 — large multipart file rollover blocks the event loop (fixed 0.47.2)
  - CVE-2025-62727 — O(n²) Range-header processing in `FileResponse` (fixed 0.49.1)
  - CVE-2026-54283 — urlencoded form limits ignored (fixed 1.3.1)
  - CVE-2026-48710 / CVE-2026-54282 — `request.url` path reconstruction issues (fixed 1.0.1/1.3.0)
  - CVE-2026-48817/48818 — HTTPEndpoint method dispatch / Windows StaticFiles UNC SSRF (not applicable: no `HTTPEndpoint`, Linux)
- **Evidence:** `pip-audit` on the exported production lock; `npm`/OSV cross-check. Reproduced after the first upgrade attempt: `fastapi==0.115.0` pins `starlette<0.39.0`, so a simple lockfile bump was impossible.
- **Impact:** Unauthenticated multipart/urlencoded requests could exhaust CPU or block the event loop; upload endpoints (selfie/vision) were the most exposed.
- **Repair:** Upgraded `fastapi` 0.115.0 → 0.115.14 and `starlette` 0.38.6 → 0.46.2 (the newest pair allowed by FastAPI 0.115). This fixes CVE-2024-47874 and the 0.40+ issues. Full remediation of the remaining 0.46.2 advisories requires FastAPI 0.162.x + Starlette ≥1.3.1 (major dependency decision; deferred to owner).
- **Residual risk:** CVE-2025-54121 (authenticated upload rollover; 5 MiB body cap + rate limit), CVE-2025-62727 (admin-only `FileResponse` raw selfie), CVE-2026-54283 (global body-size middleware caps urlencoded bodies), CVE-2026-48710/54282 (routing does not rely on `request.url.path` security checks). Assessed Medium/Low, not exploitable without auth in the current app.
- **Regression test:** full backend suite (310 tests), including upload and admin routes.
- **Verification:** `./scripts/check.sh` passes; `pip-audit` no longer reports CVE-2024-47874.

---

## Medium

### SEC-003 — OAuth `redirect_uri` is not server-side allowlisted

- **Component:** Backend OAuth
- **File:** `backend/app/services/oauth.py:172-183`, `backend/app/api/v1/auth.py:373-412`
- **Severity:** Medium · **Confidence:** Confirmed gap; exploitation conditional · **Status:** `OPEN`
- **Details:** The authorize and callback endpoints accept `redirect_uri` from the caller and pass it to the provider. Google/Microsoft only honor registered redirect URIs, and the token exchange must reuse the same value, so this is not directly exploitable without a provider misconfiguration or an open redirect at the provider.
- **Impact:** Defense-in-depth gap; could become an open-redirect/token-leak chain if provider settings change.
- **Repair:** Add a configured allowlist (web origin + `/auth/callback` path) and reject unknown values with `OAUTH_INVALID_REDIRECT_URI`. Requires a new setting and deployment env update, so it is deferred rather than rushed.
- **Regression test:** To add with the fix.

### SEC-004 — Microsoft OAuth email claim trusted without `email_verified`

- **Component:** Backend OAuth identity linking
- **File:** `backend/app/services/oauth.py:274-280`
- **Severity:** Medium · **Confidence:** Suspected (provider-dependent) · **Status:** `OPEN`
- **Details:** The code rejects `email_verified is False` but accepts a missing claim, and falls back to `preferred_username`. Microsoft id_tokens commonly omit `email_verified`; guest/tenant accounts can carry an email-shaped UPN. Account-linking protections (active accounts are never silently merged; only pending/inactive accounts are claimable) reduce impact.
- **Impact:** Potential account pre-hijack/identity confusion in multi-tenant Microsoft scenarios.
- **Repair:** For Microsoft, require `xms_edov == true` or a verified-email signal before treating the address as proven; otherwise create an unverified account that must complete OTP. Coordinate with provider app registration.
- **Regression test:** OAuth claim-matrix tests.

### SEC-005 — Session cookie `Secure` flag off when `ENVIRONMENT != production`

- **Component:** Backend session cookies on AppSail
- **File:** `backend/app/api/v1/auth.py:151-159, 348-356, 470-478`
- **Severity:** Medium (deployment configuration) · **Confidence:** Confirmed · **Status:** `FIXED` (deployed image sets `ENVIRONMENT=production`; live `Set-Cookie` not re-captured)
- **Details:** `secure=settings.environment == "production"`. The public deployment checklist records that `ENVIRONMENT=production` is not yet set on AppSail, so the session cookie is sent without `Secure` over HTTPS. HttpOnly and SameSite=Lax are set; provider HTTPS and HSTS are present.
- **Impact:** If a browser ever makes an HTTP request to the domain, the cookie could be sent in clear text (HSTS reduces but does not eliminate first-visit risk).
- **Repair:** Set `ENVIRONMENT=production` (plus `ALLOWED_HOSTS` and `CORS_ALLOWED_ORIGINS`) per `docs/deployment/GO_LIVE_RUNBOOK.md`; re-verify `Set-Cookie` includes `Secure`.
- **Verification:** Deployed image reports `environment=production` and
  `validate_for_environment() == []`; `secure=` is therefore true. The live
  `Set-Cookie` was not re-captured because no live credentials were used.

### SEC-006 — Web app lacked baseline security headers (CSP still absent)

- **Component:** Next.js web app
- **File:** `web/next.config.js:9-24`
- **Severity:** Medium · **Confidence:** Confirmed · **Status:** `FIXED` (headers deployed); CSP `OPEN` (Low)
- **Details:** No `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`, or HSTS from the Next.js app. The Catalyst backend gateway already sends some of these, but the web origin did not.
- **Impact:** Clickjacking and MIME-sniffing exposure on the web origin; no CSP defense-in-depth against XSS.
- **Repair:** Added the five headers for all routes. CSP was deliberately not added because Next.js injects inline bootstrap scripts and the app uses a static theme script with `dangerouslySetInnerHTML`; a nonce-based CSP is a follow-up.
- **Regression test:** Config evaluated with Node (`headers()` output verified). Web typecheck/lint/tests pass.
- **Residual:** CSP `OPEN` (Low); see SEC-030.

### SEC-007 — Selfie decode before dimension validation (memory-DoS)

- **Component:** Backend selfie upload
- **File:** `backend/app/api/v1/verification.py:194-208`
- **Severity:** Medium · **Confidence:** Confirmed · **Status:** `FIXED`
- **Details:** `img.load()` decoded the full image before checking the 512–4096 px bounds. A 5 MiB compressed image within Pillow's decompression-bomb threshold could allocate hundreds of MB per request; concurrent authenticated pending users could exhaust memory.
- **Impact:** Authenticated memory/CPU DoS on the verification flow.
- **Repair:** Read `img.size` and enforce the dimension gate before `img.load()`; preserve the existing 415/422 error contract.
- **Regression test:** `backend/tests/test_selfie.py::test_oversized_dimensions_rejected` (4097×4097 → 422 `IMAGE_DIMENSIONS`).

### SEC-008 — Android release included `SYSTEM_ALERT_WINDOW`

- **Component:** Android manifest / Expo config
- **File:** `android/app.json:29-33`; generated `android/android/app/src/main/AndroidManifest.xml:7`
- **Severity:** Medium · **Confidence:** Confirmed · **Status:** `FIXED` (rebuilt APK verified)
- **Details:** The generated release merged manifest contained `android.permission.SYSTEM_ALERT_WINDOW`, although the app has no overlay feature. Debug builds already declare it separately, so development tooling is unaffected.
- **Impact:** Unnecessary "draw over other apps" capability; Play policy scrutiny; potential UI redress/overlay abuse if the permission were granted.
- **Repair:** Added `expo.android.blockedPermissions` for the permission and removed it from the local generated main manifest. The native tree is gitignored and regenerated by `expo prebuild`, so `app.json` is the persistent source of truth.
- **Verification:** `expo prebuild` regenerated the manifest with
  `tools:node="remove"`; the rebuilt release APK is signed by
  `CN=MyFarmAI Release` and `aapt dump permissions` shows no
  `SYSTEM_ALERT_WINDOW`. The hosted APK is byte-identical to the rebuild.

### SEC-009 — Android `allowBackup="true"`

- **Component:** Android manifest
- **File:** generated `android/android/app/src/main/AndroidManifest.xml:22`
- **Severity:** Medium/Low · **Confidence:** Confirmed · **Status:** `OPEN` (owner decision)
- **Details:** Android Auto Backup is enabled. All sensitive local data (session/refresh tokens, conversations) is stored in `expo-secure-store`, whose values are Keystore-encrypted and not restorable on another device; no AsyncStorage or plaintext token store was found.
- **Impact:** Backup metadata/encrypted blobs may be included; practical token recovery is not possible. Low residual confidentiality risk.
- **Repair:** Set `android.allowBackup=false` (or add `dataExtractionRules` excluding app data) if the owner accepts losing backup/restore of local app state. Not changed without product sign-off.

### SEC-010 — Android framework is EOL with known advisories

- **Component:** Android dependencies
- **File:** `android/package.json` (`expo ~51`, `react-native 0.74`, `@react-navigation ^6.1`)
- **Severity:** Medium · **Confidence:** Confirmed · **Status:** `OPEN` (upgrade plan)
- **Details:** `npm audit` reports 57 advisories (1 critical `tar`, 18 high, 29 moderate, 9 low). The critical and most high findings are in build/dev tooling (`@expo/cli`, `tar`, `cacache`, `postcss`); runtime exposure is limited to navigation/deep-link parsing (`query-string`/`decode-uri-component`) and framework hygiene. Expo 51/RN 0.74 no longer receive security patches.
- **Impact:** Supply-chain/build risk and eventual unpatched runtime issues; not a direct server compromise.
- **Repair:** Plan an Expo SDK/RN upgrade (SDK 54+ or current) with a full regression pass. Do not attempt a blind major bump during the V1 security freeze.

### SEC-011 — GitHub Actions pinned to mutable tags

- **Component:** CI/CD
- **File:** `.github/workflows/ci.yml`, `.github/workflows/release.yml` (16 `uses:` entries)
- **Severity:** Medium · **Confidence:** Confirmed · **Status:** `FIXED`
- **Details:** Actions used `@v4`/`@v5` tags. A compromised or retagged action could execute with repository token permissions (release workflow has `contents: write`).
- **Impact:** Supply-chain compromise of CI/release artifacts.
- **Repair:** Pinned all 16 `uses:` entries to full commit SHAs
  (`actions/checkout`, `setup-node`, `setup-java`, `upload-artifact`,
  `astral-sh/setup-uv`) with the original tag in a comment. Workflow
  permissions and review requirements remain a repo-settings decision.
- **Verification:** Each SHA resolves to a commit on the upstream repository
  (GitHub API 200); both workflow files parse as YAML.

### SEC-012 — Rate limiting is in-process only

- **Component:** Backend middleware
- **File:** `backend/app/middleware/rate_limit.py:27`
- **Severity:** Medium/Low · **Confidence:** Confirmed · **Status:** `OPEN`
- **Details:** Counters live in a per-process `defaultdict`. A single uvicorn worker is used today, so limits work per instance; horizontal scaling (multiple AppSail instances/replicas) multiplies the effective limit. The eviction loop only removes empty buckets, so a flood of unique IPs can grow memory until entries age out on their next request.
- **Impact:** Brute-force/abuse limits can be bypassed by scaling; minor memory growth under spoofed-source floods.
- **Repair:** Move counters to a shared store (Postgres/Redis) when scaling, and evict the oldest buckets, not just empty ones.

### SEC-013 — Nested PostCSS 8.4.31 in Next.js build chain

- **Component:** Web build dependencies
- **File:** `web/package-lock.json` (nested `postcss 8.4.31` under `next@15.5.28`; top-level is 8.5.31)
- **Severity:** Medium (build-time) · **Confidence:** Confirmed · **Status:** `OPEN`
- **Details:** `npm audit` flags one high advisory group: unescaped `</style>` in stringify output and arbitrary `.map` file reads via attacker-controlled `sourceMappingURL`. These occur while processing CSS at build time; the app does not process user-supplied CSS at runtime.
- **Impact:** Build-chain risk if untrusted CSS enters the build; no direct runtime exposure identified.
- **Repair:** Upgrade to Next 16 (major) or add a tested npm `overrides` entry for `postcss` and re-run the web build/tests. Deferred to avoid a framework major during the freeze.

### SEC-014 — Voice service container runs as root without a healthcheck

- **Component:** `ai/voice` container
- **File:** `ai/voice/Dockerfile:1-24`
- **Severity:** Medium · **Confidence:** Confirmed · **Status:** `OPEN`
- **Details:** The Dockerfile has no `USER` directive and no `HEALTHCHECK`; the
  process runs as root inside the container. It binds `127.0.0.1:8001`, so it is
  not directly reachable from other hosts, and the service is not part of
  `docker-compose.yml` (not running during the audit).
- **Impact:** A voice-service compromise would yield root inside the container and
  weaken defense in depth; no healthcheck means failed starts can go unnoticed.
- **Repair:** Add a non-root user, `USER`, and a `HEALTHCHECK`; mount only the
  required model/cache directories with correct ownership. Validate the audio
  pipeline after the change (ffmpeg/libsndfile permissions).

### SEC-027 — Release build silently falls back to the debug signing key

- **Component:** Android Gradle signing
- **File:** `android/android/app/build.gradle:120-145` (generated from the Expo project; the signing block is not in `app.json`)
- **Severity:** Medium · **Confidence:** Confirmed · **Status:** `OPEN` (process guard)
- **Details:** If `MYFARMAI_KEYSTORE_PATH`/`MYFARMAI_KEYSTORE_PASSWORD` are unset,
  the `release` signing config falls back to the publicly known Android debug
  keystore. The release workflow says it produces an "unsigned" artifact and the
  owner re-signs, but Gradle actually emits a debug-signed APK in that case.
- **Impact:** A debug-signed APK could be mistaken for a release artifact, or
  sideloaded updates could be signed with a publicly known key.
- **Repair:** Fail the release build when the signing env vars are absent (e.g.
  `throw new GradleException(...)` in the `release` block), or add an explicit
  `unsignedRelease` variant for CI. Keep the owner signing procedure as the only
  publication path.

---

## Low

| ID | Finding | File | Status |
|---|---|---|---|
| SEC-030 | No Content-Security-Policy on web (headers otherwise added) | `web/next.config.js` | `OPEN` |
| SEC-015 | `pytest 8.3.4` dev-only tmpdir advisory (PYSEC-2026-1845) | `backend/uv.lock` | `OPEN` |
| SEC-016 | `uv` dependency cooldown not configured (supply chain) | `backend/pyproject.toml:38` | `OPEN` |
| SEC-017 | Android legacy `READ/WRITE_EXTERNAL_STORAGE` permissions declared | generated manifest | `OPEN` |
| SEC-018 | Android production API default is a placeholder host | `android/src/config/api.ts:24-28` | `OPEN` |
| SEC-019 | Feedback stores optional email in plaintext and is publicly submittable | `backend/app/services/feedback.py` | `ACCEPTED` (design; rate-limited) |
| SEC-020 | Bandit B104 `0.0.0.0` bind | `backend/app/main.py:11` | `FALSE POSITIVE` (container bind; host port is loopback-only) |
| SEC-021 | Bandit B108 temp-dir usage | `backend/app/core/config.py:227`, `backend/app/services/delivery.py:23` | `FALSE POSITIVE` (system temp for non-secret scratch/outbox) |
| SEC-022 | Semgrep 0700 chmod and CSRF format-string warnings | `backend/app/api/v1/verification.py`, `backend/app/middleware/csrf.py` | `FALSE POSITIVE` (0700 is stricter than suggested; JSON response is not a format string) |
| SEC-023 | gitleaks hit `myfarmai_recent_questions_v1` | `web/src/hooks/useRecentQuestions.ts:11` | `FALSE POSITIVE` (localStorage key, not a secret) |
| SEC-028 | Voice `/transcribe` has no auth or size limit (loopback-only, not deployed) | `ai/voice/main.py:23-53` | `OPEN` |
| SEC-029 | Indirect prompt injection via user/retrieved text has no tool execution path | `backend/app/ai/prompts.py` | `ACCEPTED` (output rendered as text; safety rules pinned) |

### Info

- **SEC-024 — `mcp`/`opentelemetry` advisories in the backend virtualenv:** these
  packages are not declared in `backend/uv.lock` and are not present in the
  production image; not an app finding.
- **SEC-025 — `resources/opencode/**` vendored tooling advisories:** third-party
  audit tooling, outside the MyFarmAI application scope.
- **SEC-026 — Docker data root on SSD:** operational/storage-policy deviation,
  not a security defect; unchanged during this audit.

---

## False-positive and accepted-risk notes

- The local backend container returned 404 for `/api/v1/feedback` because its image
  predates the route; staging returned 200. The finding was confirmed against
  staging and source, not inferred from the stale container.
- Platform headers from Catalyst (`X-Catalyst-*`, `Server: ZGS`) are provider
  behavior and were not treated as app findings.
- The feedback submission endpoint is intentionally public (tester flow). It is
  rate-limited and stores only category/message/optional email/app version. This
  is recorded as an accepted design risk, not a vulnerability.
