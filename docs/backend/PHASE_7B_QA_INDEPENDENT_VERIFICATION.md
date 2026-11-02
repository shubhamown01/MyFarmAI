# Phase 7B Independent QA Verification — Crop Planning

**Auditor:** QA Reviewer (independent subagent; not the implementation session)
**Date:** 2026-11-02
**Commits audited:** 6c4fcaa (7B-1 + gitignore fix), 679d54d (7B-2), 190f10c (7B-3), ee96bd2 (7B-4), 3f43917 (7B-5)
**Method:** Every claim re-executed or re-read from the working tree at HEAD = 3f43917. Implementation reports were not trusted; commands were run fresh and outputs captured. Read-only except test execution (pytest/jest/eslint/tsc/build, plus the migration cycle on a throwaway container). The canonical database was never touched.

---

## 1. Git state

| Claim | Command | Actual result | Verdict |
|---|---|---|---|
| 5 commits exist in order | `git log --oneline -12` | 6c4fcaa → 679d54d → 190f10c → ee96bd2 → 3f43917, exactly on top of 566f565 (7B plan) | VERIFIED |
| Zero uncommitted tracked changes | `git status --porcelain` | Only untracked entries: `.orchestrator/`, `resources/`, `opencode.json.backup-*` (×3), root `package.json`/`package-lock.json`, `test-*.js` (×5) — all on the expected-owner-files list, untouched | VERIFIED |

## 2. Gitignore fix (6c4fcaa)

| Claim | Command | Actual result | Verdict |
|---|---|---|---|
| Full ORM package tracked incl. crop_plan.py | `git ls-files backend/app/db/models/` | 10 files: `__init__.py, audit.py, base.py, conversation.py, crop.py, crop_plan.py, farm.py, research.py, session.py, user.py`. **Note: the task brief said "9 files"; actual count is 10.** The package is fully tracked either way; the 9-vs-10 discrepancy is in the claim wording, not the tree | VERIFIED (count discrepancy noted) |
| `/models/` scoped at root; no `**/models/` | `grep -n "models" .gitignore` | Single line 25: `/models/`. No `**/models/` anywhere | VERIFIED |
| crop_plan.py not ignored | `git check-ignore backend/app/db/models/crop_plan.py; echo $?` | Exit 1 (not ignored) | VERIFIED |

## 3. Migration a7c1e409f2b3

| Claim | Command | Actual result | Verdict |
|---|---|---|---|
| 3 tables, down_revision 6cd2bffd9881, downgrade drops tables | Read `backend/alembic/versions/a7c1e409f2b3_crop_plans_tables_p7b.py` | `crop_plans`, `crop_plan_tasks`, `crop_plan_revisions` created with FKs (CASCADE/SET NULL) + indexes; `down_revision = '6cd2bffd9881'`; downgrade drops all 3 tables + both enums (`cropplantasksource`, `cropplantaskstatus`) | VERIFIED |
| Migration cycle clean on isolated postgres | **Re-executed**, not just by record: `docker run postgres:17` (throwaway, port 55432, `DATABASE_URL` override) → `alembic upgrade head` → `downgrade -1` → `upgrade head` | All three steps clean: `6cd2bffd9881 → a7c1e409f2b3` up, `a7c1e409f2b3 → 6cd2bffd9881` down, re-up clean. Exit 0. Container removed afterwards. Canonical DB untouched | VERIFIED (upgraded from BY-RECORD: independently reproduced with docker) |

## 4. Backend

| Claim | Command | Actual result | Verdict |
|---|---|---|---|
| 9 crop-plan tests pass | `uv run pytest tests/test_crop_plans.py -q` | `9 passed, 1 warning in 3.86s` | VERIFIED |
| Tests really assert the claimed semantics | Read `backend/tests/test_crop_plans.py` (246 lines) | Auth 401 (`cookies.clear()` → 401); non-member → 404 `FARM_NOT_FOUND`; cycle from another farm → 422 `CROP_PLAN_INVALID`; milestones dated from growing-day ranges (2026-06-01 + 90 → `2026-08-30`, +120 → `2026-09-29`, exact dates); no cycle → `milestones == []`; assumptions asserted non-empty **plus** the key phrase `"generic growing-day ranges"` as a substring (backend test does not assert the entire string character-for-character; the web test does — see §6); patch → 2 revisions, both snapshots capture `variety == "Cherry"` **before** the change; soft-cancel → task still in GET response; patch with `"source": "suggested"` → stays `"user"`; viewer reads 200, patches → 403 `FARM_FORBIDDEN` | VERIFIED (assumptions "verbatim" is substring-strength in backend, full-string in web) |
| Full gate | `bash scripts/check.sh` from repo root | pytest line: `209 passed, 24 warnings in 46.26s`. **Exit code 0** | VERIFIED |
| mypy non-blocking gate weakness | `grep mypy scripts/check.sh` | Line 16: `uv run mypy app --exclude app/orchestrator \|\| true`. mypy actually reported **99 errors in 23 files** while the gate passed — 21 of them in 7B files (`crop_plan.py` service/schemas/models/api, all `no-untyped-def`/`type-arg`/`no-untyped-call`). Pre-existing pattern (chat.py carries the same class of errors), but the "All checks passed!" banner is genuinely misleading | VERIFIED (weakness confirmed, flagged) |

## 5. Security spot-check (read-only)

| Claim | Evidence | Actual result | Verdict |
|---|---|---|---|
| Farm authz on every route | Read `services/crop_plan.py` + `api/v1/crop_plans.py` | Every service entry calls `FarmService._authorized_farm` (directly, or via `_authorized_plan` for plan-scoped routes); all 7 API routes `Depends(get_current_user_id)` | VERIFIED |
| Viewer read-only | Same files | Reads use `_ALL_ROLES` (owner/member/viewer); all mutations use `_WRITE_ROLES` via `require_member=True`/`require=_WRITE_ROLES` | VERIFIED |
| Non-member 404, no existence leak | Same files + tests | `FarmNotFoundError` → 404 `FARM_NOT_FOUND` on every route; task-not-found deliberately mapped to the same 404 as plan-not-found (`raise _not_found(detail="crop plan or task not found")`) | VERIFIED |
| Task source forced USER | Same files | `add_task` hardcodes `CropPlanTaskSource.USER`; `update_task` does `fields.pop("source", None)` — the API can never set or change source | VERIFIED |
| No raw SQL / secrets / external calls (zero-cost policy) | Same files + `git show 679d54d --stat` diff surface | All data access via SQLAlchemy repositories/ORM; no HTTP clients, no API keys, milestones are pure `timedelta` arithmetic | VERIFIED |

## 6. Web (190f10c)

| Claim | Command | Actual result | Verdict |
|---|---|---|---|
| typecheck clean | `npm run typecheck` | `tsc --noEmit`, exit 0 | VERIFIED |
| 35/35 tests | `npm test -- --runInBand --ci` | `Tests: 35 passed, 35 total` (6 suites), exit 0 | VERIFIED |
| lint clean | `npm run lint` | "No ESLint warnings or errors", exit 0 | VERIFIED |
| build succeeds | `npm run build` | Next.js build completed, exit 0 | VERIFIED |
| Test coverage is real | Read `web/src/__tests__/crop-planning.test.tsx` (257 lines) | Plans render (`Lokwan wheat` + View plan); no-plans empty state w/ create CTA; no-farm empty state (0 farms) **and** 404 `FARM_NOT_FOUND` → same empty state; error alert + "Try again"; assumptions asserted as the **full exact string** (lines 119, 212); create flow asserts exact payload `{variety, planting_date, crop_cycle_id: null, tasks: []}`; soft-cancel — pre-cancelled task stays visible + `updateCropPlanTask` called with `{status: 'cancelled'}`; revision history renders ("plan created"); exactly one `axe()` full-page check with `toHaveNoViolations()` | VERIFIED |
| web/package.json unchanged since 8dfc055 | `git diff 8dfc055 HEAD -- web/package.json` | Empty diff, exit 0 | VERIFIED |

## 7. Android (ee96bd2)

| Claim | Command | Actual result | Verdict |
|---|---|---|---|
| typecheck clean | `npm run typecheck` | `tsc --noEmit`, exit 0 | VERIFIED |
| lint clean | `npm run lint` | `eslint . --ext .ts,.tsx`, exit 0 | VERIFIED |
| 401 → token clear + signed-out; 404 → no-farm | Read `src/hooks/useCropPlans.ts` | 401 → `clearSessionTokens()` + `setStatus('signed-out')`; 404 + `FARM_NOT_FOUND` → `setStatus('no-farm')`; plus `offline`/`error` states consistent with the dashboard status machine | VERIFIED |
| 7 client methods; envelope normalization superset | Read `src/lib/api/client.ts` | Exactly 7: `getCropPlans, createCropPlan, getCropPlan, updateCropPlan, getCropPlanRevisions, addCropPlanTask, updateCropPlanTask`, all through the shared `this.request<T>()` wrapper that handles the ADR-009 envelope — superset of the web client's needs. **Reviewed, not behavioral-tested** (no jest infra on android) | VERIFIED (static review only) |
| android/package.json unchanged since 8dfc055 | `git diff 8dfc055 HEAD -- android/package.json` | Empty diff, exit 0 | VERIFIED |
| Device QA | — | **NOT TESTED** — no emulator/device available to this session; no jest infra exists for android. CHANGELOG itself discloses "device QA still pending" | NOT TESTED (honestly disclosed) |

## 8. Documentation (3f43917)

| Claim | Evidence | Actual result | Verdict |
|---|---|---|---|
| API.md "Crop Plans (P7B)" consistent with schemas | Read API.md §505+ vs `schemas/crop_plan.py` | Section states: farm-members-only, non-member 404, flat ADR-009 envelope, viewer read-only, milestones derived locally (no external services), assumptions verbatim, `source: "user"` immutable, soft cancel, append-only before-change revisions — all matching the schemas (PlanTaskCreate/Update/Response, MilestoneResponse, CropPlanCreate/Update/Response, CropPlanRevisionResponse) and the behavior verified in §4–5 | VERIFIED |
| APP_FLOW.md §3b present + accurate | `sed -n '77,100p' docs/product/APP_FLOW.md` | §3b "Crop Planning Flow (P7B)" present; 5-step flow matches verified behavior (local milestone derivation, verbatim assumptions, soft cancel, revision history, web/Android parity, no-farm empty state) | VERIFIED |
| FCL-080..085 present | grep FILE_CHANGE_LEDGER.md | FCL-080 (L1508), 081 (L1522), 082 (L1537), 083 (L1552), 084 (L1566), 085 (L1580) | VERIFIED |
| CHANGELOG lists 7B-1..7B-5 | grep CHANGELOG.md | All five entries present (L18–22) | VERIFIED |

## 9. Dependency policy (zero-cost)

| Claim | Command | Actual result | Verdict |
|---|---|---|---|
| No new deps anywhere in 7B | `git diff 566f565..HEAD --stat \| grep -iE "package.json\|pyproject\|uv.lock"` | grep exit 1 — **zero** dependency-manifest changes across all 5 commits. jest-axe was already present (web tests import it without a manifest change) | VERIFIED |

---

## Exceptions & Limitations (skeptic's ledger)

1. **Android device/emulator QA: NOT TESTED.** No emulator or physical device in this session; no jest infra exists in `android/`. Only static code review + typecheck/lint. Disclosed in CHANGELOG as "device QA still pending."
2. **mypy gate weakness (pre-existing):** `scripts/check.sh` line 16 ends in `|| true`; 99 mypy errors currently suppressed (21 in 7B files — missing annotations/generic params, cosmetic-to-moderate, no behavioral evidence of defects). The "All checks passed!" banner prints despite these errors. Recommend removing `|| true` or adding an error-count budget in a future phase.
3. **Assumptions "verbatim" claim is tiered:** the web test asserts the full exact string; the backend test asserts non-empty + the key phrase as a substring. The full string does match `ASSUMPTIONS_TEXT` in `services/crop_plan.py` by inspection, so the claim holds, but backend coverage of it is substring-strength.
4. **Claim-wording discrepancies (cosmetic):** the 7B-1 models package is 10 tracked files, not 9 as stated in the audit brief; envelope normalization on Android is reviewed statically, not exercised by any test.
5. **CI pipeline:** still absent repo-wide (pre-existing gap from the Phase 0 baseline; unchanged by 7B).
6. **Playwright critical flows for crop planning were not run in this session** (the task's verification list for 7B did not request them; web coverage is via the 10 jest scenarios including axe). Noted for completeness, not counted against 7B.

## Verdict

**CONFIRMED WITH EXCEPTIONS.**

All reproducible claims were independently reproduced and passed: git/gits state, gitignore fix, migration cycle (re-run clean on a throwaway postgres:17 — the recorded claim is now independently verified, not just by record), 9/9 backend tests with real assertions, full gate 209 passed exit=0, security semantics confirmed by source read, web 35/35 + typecheck/lint/build clean with genuine test coverage, android typecheck/lint clean with correct 401/404 handling, docs accurate, zero new dependencies.

The exceptions are: android device QA untested (no hardware/jest — disclosed), the pre-existing mypy `|| true` gate weakness (confirmed live: 99 suppressed errors), and two cosmetic claim-wording discrepancies. No failures, no concealment found.

QA: @qa-reviewer (independent)
Date: 2026-11-02
Tree left uncommitted except this report file.
