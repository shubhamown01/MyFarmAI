# MyFarmAI — Remediation Log (V1.0.0 Security Audit)

- **Date:** 2026-11-10
- **Baseline:** `0a75e26` (branch `phase-01-foundation`, clean tree)
- **Scope:** low-risk confirmed fixes only. No database schema changes, data
  deletion, secret rotation, production deployment, or signing-key changes.

## R-01 — Admin-gate the feedback listing (SEC-001, High)

**Files**

- `backend/app/api/v1/feedback.py`
- `backend/tests/conftest.py` (new `admin_async_client` fixture)
- `backend/tests/test_feedback.py`
- `backend/tests/test_feedback_list.py`

**Change**

`GET /api/v1/feedback` now depends on `get_current_user_id` and requires
`users.role == "admin"`, returning `403 ADMIN_REQUIRED` otherwise. Submission
(`POST /feedback/submit`) remains public by design. The obsolete docstring that
admitted the route was unauthenticated was removed.

**Regression tests**

- anonymous → 401
- authenticated non-admin → 403 `ADMIN_REQUIRED`
- admin → 200 with submitted rows and pagination

**Verification**

`pytest tests/test_feedback.py tests/test_feedback_list.py` → 14 passed.
Full backend gate → 310 passed.

**Deployment status**

Deployed to AppSail on 2026-11-10. Live anonymous `GET /api/v1/feedback`
now returns `401 NOT_AUTHENTICATED`; admin 200 is covered by tests (no live
admin credentials were used).

---

## R-02 — Validate selfie dimensions before decoding (SEC-007, Medium)

**Files**

- `backend/app/api/v1/verification.py`
- `backend/tests/test_selfie.py`

**Change**

`Image.open()` → read `img.size` → enforce 512–4096 px → only then `img.load()`.
The existing 415/422 error contract is preserved (`HTTPException` is re-raised
before the generic handler).

**Regression test**

`test_oversized_dimensions_rejected` uploads a 4097×4097 JPEG and expects
`422 IMAGE_DIMENSIONS`; the full decode no longer happens first.

**Verification**

`pytest tests/test_selfie.py` → 13 passed; full gate → 310 passed.

---

## R-03 — Upgrade FastAPI/Starlette (SEC-002, High)

**Files**

- `backend/pyproject.toml`: `fastapi==0.115.0` → `0.115.14`
- `backend/uv.lock`: `starlette 0.38.6` → `0.46.2`
- backend virtualenv synced with `uv add`

**Change**

FastAPI 0.115.14 allows Starlette 0.40–0.46. Starlette 0.46.2 fixes
CVE-2024-47874 (multipart DoS) and the 0.40+ issues. A first attempt to add
`starlette>=0.41.3` failed because FastAPI 0.115.0 pins `<0.39.0`; the FastAPI
patch upgrade was required. `uv` also refreshed the editable project entry
`myfarmai-backend` 0.1.0 → 1.0.0 to match `pyproject.toml`; no other runtime
packages changed.

**Verification**

- `./scripts/check.sh` → 310 passed, ruff and mypy baseline pass.
- `pip-audit` on the exported production lock no longer reports
  CVE-2024-47874. Residual 0.46.2 advisories are documented in
  `DEPENDENCY_AUDIT.md`.

**Rollback**

Revert `pyproject.toml`/`uv.lock` and run `uv sync --frozen`. No code depends on
0.115.14-specific behavior; tests pass on both versions.

---

## R-04 — Add baseline security headers to the web app (SEC-006, Medium)

**File:** `web/next.config.js`

**Change**

Added `headers()` for all routes:

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: geolocation=(self), camera=(), microphone=()`
- `Strict-Transport-Security: max-age=31536000`

CSP was intentionally not added (Next.js inline bootstrap + static theme script);
it remains a follow-up (SEC-030).

**Verification**

- `node -e "require('./web/next.config.js').headers()"` returns the expected
  header set.
- `npm run typecheck`, `npm run lint`, `npm test -- --runInBand` → 40 tests pass.

**Deployment status**

Deployed to Catalyst Slate on 2026-11-10. Live responses carry
`X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`,
`Referrer-Policy`, `Permissions-Policy`, and HSTS.

---

## R-05 — Remove `SYSTEM_ALERT_WINDOW` from release builds (SEC-008, Medium)

**Files**

- `android/app.json` (persistent source of truth; `android/android/` is gitignored)
- local generated `android/android/app/src/main/AndroidManifest.xml` (for the
  owner's existing build tree)

**Change**

Added `expo.android.blockedPermissions: ["android.permission.SYSTEM_ALERT_WINDOW"]`
and removed the permission from the local main manifest. The debug manifest
already declares it, so development tooling is unaffected.

**Verification**

`npm run typecheck` and `npm run lint` pass. `expo prebuild` regenerated the
manifest with `tools:node="remove"`; the release APK was rebuilt with
`JAVA_HOME=/data/JDKs/jdk-17.0.21+9`, signed by `CN=MyFarmAI Release`, and
`aapt dump permissions` shows no `SYSTEM_ALERT_WINDOW`. The APK served by
`/api/v1/downloads/app-release.apk` is byte-identical to the rebuild.

---

## R-06 — Pin GitHub Actions to commit SHAs (SEC-011, Medium)

**Files**

- `.github/workflows/ci.yml`
- `.github/workflows/release.yml`

**Change**

All 16 `uses:` entries now reference full commit SHAs for `actions/checkout`,
`actions/setup-node`, `actions/setup-java`, `actions/upload-artifact`, and
`astral-sh/setup-uv`; the original tag is kept in a trailing comment.

**Verification**

- Each SHA resolves to a commit on the upstream repository (GitHub API 200).
- Both workflow files parse with PyYAML.
- No mutable `@vN` references remain.

**Note**

Restricting `permissions:` and requiring review for workflow changes are
repository-settings decisions and remain owner actions.

---

## Documentation updated

- `docs/security/SECURITY_AUDIT_PLAN.md`
- `docs/security/SECURITY_FINDINGS.md`
- `docs/security/PENTAGI_TEST_RESULTS.md`
- `docs/security/DEPENDENCY_AUDIT.md`
- `docs/security/API_SECURITY_AUDIT.md`
- `docs/security/ANDROID_SECURITY_AUDIT.md`
- `docs/security/AI_SECURITY_AUDIT.md`
- `docs/security/REMEDIATION_LOG.md` (this file)
- `docs/security/V1_RELEASE_SECURITY_CHECKLIST.md`
- `docs/testing/TEST_RESULTS.md` (feedback list auth + new test count)

## Full verification evidence

| Check | Command | Result |
|---|---|---|
| Backend gate | `./scripts/check.sh` | **PASS** — 310 tests, ruff/mypy baseline |
| Web typecheck | `cd web && npm run typecheck` | **PASS** |
| Web lint | `cd web && npm run lint` | **PASS** |
| Web tests | `cd web && npm test -- --runInBand` | **PASS** — 40/40 |
| Android typecheck | `cd android && npm run typecheck` | **PASS** |
| Android lint | `cd android && npm run lint` | **PASS** |
| Web headers config | `node -e ...next.config.js` | **PASS** |
| Feedback regression | `pytest tests/test_feedback*.py` | **PASS** — 14/14 |
| Selfie regression | `pytest tests/test_selfie.py` | **PASS** — 13/13 |
| Live feedback gate | anonymous `GET /api/v1/feedback` | **PASS** — 401 `NOT_AUTHENTICATED` |
| Live health | `/health/ready` | **PASS** — database ok, ollama disabled |
| Live web headers | `curl -I` on Slate | **PASS** — all five headers present |
| APK signature | `apksigner verify --print-certs` | **PASS** — `CN=MyFarmAI Release` |
| APK manifest | `aapt dump permissions` | **PASS** — no `SYSTEM_ALERT_WINDOW` |
| Hosted APK | `cmp` vs rebuild | **PASS** — identical |
| Local DB backup | `bash scripts/backup.sh` | **PASS** — 80K dump + integrity check |

## Not done (requires owner authorization/action)

- Full `pg_dump` backup verification against Neon (no Neon credentials locally;
  the Dockerized dev Postgres backup was verified).
- FastAPI 0.162/Starlette 1.3.x major upgrade (SEC-002 residual).
- Next 16 upgrade / PostCSS override (SEC-013).
- OAuth redirect allowlist and Microsoft claim hardening (SEC-003/004).
