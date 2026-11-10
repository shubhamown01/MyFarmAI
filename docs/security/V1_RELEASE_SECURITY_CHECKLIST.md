# MyFarmAI — V1 Release Security Checklist

- **Date:** 2026-11-10
- **Baseline:** `0a75e26` (branch `phase-01-foundation`) + audit fixes in the working tree
- **Sources:** `SECURITY_FINDINGS.md`, `REMEDIATION_LOG.md`, `DEPENDENCY_AUDIT.md`,
  `API_SECURITY_AUDIT.md`, `ANDROID_SECURITY_AUDIT.md`, `AI_SECURITY_AUDIT.md`,
  `PENTAGI_TEST_RESULTS.md`
- **Status legend:** `PASS` verified with evidence · `CONDITIONAL` source fixed,
  running environment not yet updated · `BLOCKED` requires owner action/approval ·
  `FAIL` gate not met

## Verdict

**V1.0.0 is security-ready, conditional on one operational gate.** No Critical or
High finding remains open: the backend, web app, and release APK were rebuilt,
deployed, and re-tested on 2026-11-10. The remaining **BLOCKED** gate is a full
Neon `pg_dump`/restore drill, which needs database credentials not available
locally. Residual risks below require owner acknowledgement.

## Gate matrix

| # | V1 gate | Status | Evidence / condition |
|---|---|---|---|
| 1 | No unresolved Critical finding | **PASS** | 0 Critical in `SECURITY_FINDINGS.md` |
| 2 | No unresolved High without owner acceptance | **PASS** | SEC-001 deployed: live anonymous `GET /api/v1/feedback` returns 401. SEC-002 deployed (FastAPI 0.115.14 / Starlette 0.46.2); residual Medium advisories documented as not exploitable without auth |
| 3 | No exposed secrets | **PASS** | gitleaks full-history scan: only the `myfarmai_recent_questions_v1` localStorage key (false positive). `.dockerignore` excludes `.env*`/`data/`. No keys found in Android/CI config |
| 4 | Auth/authz tests passing | **PASS** | 310 backend tests pass, including new anonymous 401 / non-admin 403 / admin 200 feedback tests. Login, logout, OTP, OAuth state, CSRF, and admin gates covered |
| 5 | User isolation verified | **PASS** | Ownership checks return 404 for cross-user access; covered by `test_farms_api.py::test_cross_user_patch_404`, `test_land_api.py::test_cross_user_plot_404`, `test_crop_cycles_api.py::test_cross_user_cycle_404`, `test_p5g_conversations.py::test_cross_user_conversation_404`, `test_conversation_ownership.py::test_user_isolation_in_listing` |
| 6 | HTTPS | **PASS (caveat)** | Provider certs + HSTS on both origins; deployed image sets `ENVIRONMENT=production` and `validate_for_environment() == []`, so session cookies are `Secure`. Live `Set-Cookie` was not re-captured (no live credentials used) |
| 7 | Dependencies/containers reviewed | **CONDITIONAL** | `pip-audit`, `npm audit`, Trivy, OSV, Bandit, Semgrep run; results in `DEPENDENCY_AUDIT.md`. Residuals: Starlette 0.46.2 advisories (Medium/Low), Android EOL Expo 51/RN 0.74 (SEC-010), PostCSS build chain (SEC-013), voice container root/no healthcheck (SEC-014) |
| 8 | Android release checks | **PASS (caveat)** | `expo prebuild` emitted `tools:node="remove"`; APK rebuilt, signed by `CN=MyFarmAI Release`, no `SYSTEM_ALERT_WINDOW`, hosted copy byte-identical. Residual owner decisions: SEC-027 debug fallback, SEC-009 `allowBackup`, SEC-017 storage permissions, SEC-018 API host |
| 9 | Backup/recovery verified | **BLOCKED** | Dockerized Postgres backup verified 2026-11-10 (80K dump, `pg_restore --list` clean). A full Neon `pg_dump`/restore drill still needs database credentials not available locally |
| 10 | Regression tests pass | **PASS** | Backend `./scripts/check.sh` → 310 passed + ruff/mypy baseline; web typecheck/lint + 40/40 tests; Android typecheck/lint pass |
| 11 | Deployment matches audited source | **PASS** | Backend redeployed (`/health/ready`: database ok), Slate redeployed (headers live), APK rebuilt/re-signed and hosted identically |

## Owner actions before public V1

1. **DONE** — backend redeployed; live anonymous `GET /api/v1/feedback` → 401,
   `/health/ready` → `database: ok`.
2. **DONE** — web redeployed; all five headers observed live.
3. **DONE via image** — `ENVIRONMENT=production`, `ALLOWED_HOSTS`, and
   `CORS_ALLOWED_ORIGINS` baked into the deployed image and smoke-validated.
   Still worth confirming the AppSail console does not override `ENVIRONMENT`,
   then capturing a live `Set-Cookie` with `Secure`.
4. **PENDING** — run and store a full Neon `pg_dump` plus a restore drill.
5. **DONE** — `expo prebuild` + release rebuild; APK signed
   `CN=MyFarmAI Release`, no `SYSTEM_ALERT_WINDOW`, hosted copy identical.
6. **OWNER DECISION** — SEC-003 OAuth redirect allowlist, SEC-004 Microsoft
   verified-email claim, SEC-009 `allowBackup`, SEC-011 CI action SHA pinning,
   SEC-027 release signing guard, and the FastAPI 0.162/Next 16 major upgrades.

## Accepted residual risk (owner acknowledgement required)

- SEC-002 residual Starlette advisories — Medium/Low, not exploitable without an
  authenticated session in the current app.
- SEC-010 EOL Android framework — no runtime patch stream until the Expo/RN
  upgrade.
- SEC-019 public feedback submission — by design, rate-limited, optional email
  stored in plaintext.
- SEC-029 prompt injection — output rendered as text; no tool execution path.

## Sign-off

| Role | Name | Date | Decision |
|---|---|---|---|
| Security audit | automated agent | 2026-11-10 | Security-ready — conditional on the blocked Neon backup gate |
| Owner | _pending_ | | |

No claim of complete security is made. This checklist records verified evidence,
known gaps, and the actions required to close them.
