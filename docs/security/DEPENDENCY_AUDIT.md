# MyFarmAI — Dependency & Container Audit (V1.0.0)

- **Date:** 2026-11-10
- **Inputs:** `backend/uv.lock`, `backend/pyproject.toml`, `web/package-lock.json`,
  `android/package-lock.json`, Dockerfiles, CI workflows
- **Tools:** pip-audit 2.10.1, osv-scanner 2.7.1, npm audit, Trivy 0.76.2

## 1. Backend (production image)

### Before

`fastapi 0.115.0` → `starlette 0.38.6`, which carried:

| Advisory | Issue | Fixed in |
|---|---|---|
| CVE-2024-47874 | Multipart form DoS | 0.40.0 |
| CVE-2025-54121 | Large multipart rollover blocks event loop | 0.47.2 |
| CVE-2025-62727 | O(n²) Range header in `FileResponse` | 0.49.1 |
| CVE-2026-54283 | `max_fields`/`max_part_size` ignored for urlencoded forms | 1.3.1 |
| CVE-2026-48710 | Host header path injection | 1.0.1 |
| CVE-2026-54282 | `request.url` path reconstruction | 1.3.0 |
| CVE-2026-48817 | `HTTPEndpoint` method dispatch | 1.1.0 |
| CVE-2026-48818 | Windows `StaticFiles` UNC SSRF | 1.1.0 |

### Applied

- `fastapi 0.115.0 → 0.115.14`
- `starlette 0.38.6 → 0.46.2` (maximum allowed by FastAPI 0.115.14)

This removes the unauthenticated multipart DoS (CVE-2024-47874) and the 0.40+
fixes. Full backend suite: **310 passed**; `ruff` and `mypy` baseline pass.

### Residual (0.46.2)

`pip-audit` still reports 14 advisory entries (7 unique) for Starlette:

| Advisory | App exposure | Rating |
|---|---|---|
| CVE-2025-54121 (rollover) | Authenticated selfie/vision uploads; 5 MiB body cap + rate limit | Medium |
| CVE-2025-62727 (Range DoS) | Only admin `FileResponse` raw selfie endpoint | Low |
| CVE-2026-48710 / 54282 (URL path) | App does not use `request.url.path` for authz checks | Low |
| CVE-2026-54283 (urlencoded limits) | Global `RequestBodyLimitMiddleware` caps body size | Low |
| CVE-2026-48817 (HTTPEndpoint) | Not used | N/A |
| CVE-2026-48818 (Windows UNC) | Linux deployment | N/A |

**Recommendation:** plan `fastapi >= 0.162` + `starlette >= 1.3.1` as a dedicated
upgrade task with a full regression and container rebuild. Do not bundle it into
the V1 freeze.

### Dev-only

- `pytest 8.3.4` — PYSEC-2026-1845 tmpdir handling. Not shipped in the runtime
  image. Bump to a fixed pytest in the next tooling update.
- `mcp` and `opentelemetry-api` appear in the local venv but are not declared in
  `uv.lock` and are absent from the production image; not app findings.

## 2. Web (Next.js)

`npm audit` (post-change): **28 total** — 1 high, 23 moderate, 4 low.

- The high group is the nested `postcss 8.4.31` under `next@15.5.28`. Top-level
  `postcss` is 8.5.31 and is not affected. Advisories are build-time
  (`</style>` stringify, `sourceMappingURL` file reads); the app does not process
  user CSS at runtime.
- `npm audit fix` requires Next 16 (major). Deferred; track as SEC-013.
- No runtime XSS dependency chain was confirmed in `npm audit`.

## 3. Android (Expo / React Native)

`npm audit`: **57 total** — 1 critical, 18 high, 29 moderate, 9 low.

| Area | Examples | Ships in APK? | Rating |
|---|---|---|---|
| Build tooling | `tar` (critical), `@expo/cli`, `cacache`, `node-forge`, `send` | No | Medium (supply chain) |
| Build CSS | `postcss` | No | Low |
| Runtime navigation | `@react-navigation/*` → `query-string`/`decode-uri-component` | Yes | Low (deep-link parsing; DoS only) |
| Framework | Expo 51 / RN 0.74 EOL | Yes | Medium (hygiene) |

The single critical (`tar` path traversal) is a build-time archive extraction
issue; it does not execute inside the APK. The runtime advisories are low-impact
parser/DoS issues. The real issue is framework EOL: upgrade to a supported Expo
SDK with a full device regression (SEC-010).

## 4. Containers and IaC

- `backend` image: non-root (`USER 10001`), healthcheck present, Docker secret for
  Postgres password, ports bound to `127.0.0.1` in compose.
- `postgres` image: no published port; healthcheck; secret file.
- `ai/voice/Dockerfile`: **runs as root**, no `HEALTHCHECK`, binds `127.0.0.1`
  inside the container. The voice service is not part of `docker-compose.yml` and
  was not running during the audit. SEC-014.
- Trivy app-scoped totals (excluding `node_modules`, vendored `resources/`,
  virtualenvs): 1 critical, 38 high, 22 medium, 5 low. The critical is `tar` in the
  Android build lock; the highs are dominated by Android build tooling plus the
  pre-upgrade Starlette/pytest entries.
- Trivy's critical IaC finding is in vendored `resources/opencode/browser-tools`
  (`APT_KEY_DONT_WARN_ON_DANGEROUS_USAGE` env) — out of application scope.

## 5. CI/CD supply chain

- 16 `uses:` entries in `.github/workflows/ci.yml` and `release.yml` use mutable
  tags (`@v4`, `@v5`). The release workflow has `contents: write`.
- `uv` has no dependency cooldown configured (`backend/pyproject.toml:38`).
- Recommendation: pin actions to commit SHAs, enable Dependabot, and add a
  `uv` `exclude-newer` cooldown (e.g. 7 days) for new releases.

## 6. Out of scope

- `resources/opencode/**` vendored audit/browser tooling: many advisories,
  including a critical Dockerfile env finding. This is third-party tooling used to
  perform the audit, not part of MyFarmAI's runtime.
- Base-image OS packages inside the running containers were not re-scanned after
  the dependency change; rebuild and rescan before release.

## 7. Verification commands

```bash
cd backend && uv export --frozen --no-dev --no-emit-project -o /tmp/req.txt
/data/tools/venv/bin/pip-audit -r /tmp/req.txt --no-deps
/data/tools/bin/osv-scanner scan --lockfile=backend/uv.lock
cd web && npm audit
cd android && npm audit
/data/tools/bin/trivy fs --scanners vuln,misconfig,secret .
```

Raw outputs: `/tmp/opencode/audit/` (local, not committed).
