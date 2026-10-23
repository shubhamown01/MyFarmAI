# Phase 1 Implementation Plan — Backend Foundation

**Phase:** 0 deliverable — **proposed, not executed**  
**Date:** 2026-10-21  
**Status:** Awaiting approval. No Phase 1 task has started.  
**Roadmap:** [`../MyFarmAI_Backend_Roadmap.md`](../MyFarmAI_Backend_Roadmap.md) §5, Phase 1  
**Related:** [`GAP_ANALYSIS.md`](GAP_ANALYSIS.md), [`ARCHITECTURE_DECISIONS.md`](ARCHITECTURE_DECISIONS.md), [`TARGET_BACKEND_ARCHITECTURE.md`](TARGET_BACKEND_ARCHITECTURE.md)

---

## 1. Authorization and scope

This document proposes Phase 1 only. It does **not** authorize Phase 1. Work may begin only after the approval checklist in §11 is completed.

**Phase 1 goal:** establish a reproducible, testable, safely operable FastAPI foundation without changing the product’s API surface beyond the approved error contract and health endpoints.

**Phase 1 exit gate (from the roadmap):** a clean environment setup works; tests, linting, type checks, health endpoints, and the local quality script pass; the backend runs non-root and is not publicly exposed.

### 1.1 In scope

- Repository and data safety before any bulk change.
- Secret remediation and voice exposure containment.
- Python 3.12 + `uv` + lockfile; dependency groups.
- App factory, configuration profiles, and module boundaries.
- Consistent error envelope and request correlation.
- `/health/live` and `/health/ready`; legacy `/health` retained.
- Structured logs with redaction.
- Request body limits, trusted-proxy handling, bounded rate limiting.
- Hermetic tests and a single local/CI check entrypoint.
- OpenAPI artifact, docs correction, version single-source.
- Non-root container baseline and Compose validation.
- Backup/restore drill for the current SQLite data.
- Licence/third-party notice decision.
- Disk/build preflight.
- Optional benchmark of the selected model (gate for Phase 4).

### 1.2 Out of scope (do not start in Phase 1)

| Excluded | Why / phase |
|---|---|
| Authentication, sessions, ownership enforcement | Phase 3; until then the backend binds to `127.0.0.1` only. |
| PostgreSQL production deployment and data migration | Phase 2 (ADR-003/004/005). |
| Farm/crop domain APIs | Phase 5. |
| AI gateway refactor, prompt evaluation, streaming | Phase 4. |
| Research pipeline, SearXNG client, citations | Phase 6. |
| Weather provider replacement or commercial licensing | Phase 5 decision. |
| Voice feature work, model pre-baking (unless retained) | Deferred (ADR-014). |
| Public TLS deployment, production hardening, backup automation | Phase 8; Caddy configuration may be prepared but not exposed. |
| Deleting models, images, volumes, or databases | Requires separate destructive-change approval. |
| Pulling new models or installing GPU/system packages | Separate approval. |

**Hard rule:** no non-loopback exposure until Phase 3 authentication is complete and verified. Phase 1 may prepare Caddy/Compose configuration, but must not publish the backend.

## 2. Prerequisites and decisions

| # | Prerequisite | Owner | Needed by |
|---|---|---|---|
| 1 | Approve Phase 0 documents and ADR-001, 002, 009, 010, 013, 014 | Project owner | Before start |
| 2 | Approve committing the existing work and creating a branch/remote or verified bundle | Owner | P1-01 |
| 3 | Confirm Phase 1 deployment target is **local-only** (loopback) | Owner | Before start |
| 4 | Choose canonical SQLite file or confirm no data must be preserved | Data owner | P1-01 |
| 5 | Approve secret rotation and SearXNG restart | Operations | P1-02 |
| 6 | Confirm voice has no active consumer; approve unpublishing/stopping it | Product/operations | P1-03 |
| 7 | Approve backup location on `/data` and retention for the drill | Owner | P1-01 |
| 8 | Choose project licence direction or explicitly defer with a date | Owner/legal | P1-16 |
| 9 | Choose CI platform and remote (GitHub/GitLab/other) | Engineering | P1-12 |
| 10 | Approve disk cleanup or Docker root relocation if preflight fails | Owner | P1-15 |
| 11 | Approve the error-envelope change and coordinated web/Android release | Client owners | P1-07 |

If any prerequisite is unresolved, the dependent task is blocked; the rest of Phase 1 may proceed only if it does not assume the decision.

## 3. Task plan

Complexity: **S** ≤ 0.5 day, **M** 1–2 days, **L** 3–5 days (indicative, one developer).

### P1-01 — Baseline, repository safety, and data backup

**Gaps:** GAP-001, GAP-002, GAP-003, GAP-004  
**Complexity:** M  
**Depends on:** prerequisites 2, 4, 7

Work:

1. Record the current commit and working-tree state.
2. Create a branch (for example `phase-01-foundation`) and commit the existing work in logical commits after owner review. Do not rewrite history.
3. Create a verified Git bundle and/or configure a remote; verify a restore clone.
4. Add ignore rules for `backend/data/`, `**/*.db`, `**/*.sqlite*`, `infra/searxng/data/`, model caches, coverage, and local env files. Confirm no database is tracked and review history for accidental data.
5. Write a one-page canonical-database decision (file, counts, preservation requirement, owner).
6. Back up both SQLite files with `VACUUM INTO` or a stop-writes copy; compute SHA-256; run `PRAGMA integrity_check` on the copies; restore the chosen file to a disposable path and compare counts.

Acceptance criteria:

- [ ] Working tree is committed on a branch and restorable from a bundle/remote.
- [ ] `git check-ignore -v backend/data/app.db` matches.
- [ ] `git ls-files` contains no `*.db`/`*.sqlite*`.
- [ ] Canonical DB decision is recorded and signed by the owner.
- [ ] Backup checksum and integrity check pass; restore drill row counts match.
- [ ] No secret or user data is printed in logs/evidence.

Verification: `git bundle verify`, restore clone, `git check-ignore`, `sqlite3 ... "PRAGMA integrity_check;"`, count queries on source and restored copy.

Rollback: the backup is the rollback; do not delete source files until acceptance.

---

### P1-02 — Secret remediation and file permissions

**Gaps:** GAP-005, GAP-027  
**Complexity:** S  
**Depends on:** prerequisite 5

Work:

1. Rotate the SearXNG `server.secret_key`.
2. Remove the literal from `infra/searxng/config/settings.yml`; load it from `SEARXNG_SECRET`/the existing env file/secret store.
3. Set restrictive permissions (600) on `.env` files; document secret handling.
4. Add a secret scan to the check script (for example gitleaks or an equivalent maintained scanner).
5. Verify Git history does not contain the old value before any publication; if it does, plan history remediation with the owner.

Acceptance criteria:

- [ ] No secret value exists in tracked files; `git grep` and the scanner are clean.
- [ ] SearXNG starts and serves locally with the environment-provided secret.
- [ ] `.env` files are mode 600; no secret is baked into an image.
- [ ] Rotation and rollback steps are documented without reproducing the value.

Verification: secret scan, `stat -c '%a %n'`, container health, local SearXNG request.

Rollback: restore the previous configuration only if the new secret fails; never commit either value.

---

### P1-03 — Contain the voice service

**Gaps:** GAP-006  
**Complexity:** S  
**Depends on:** prerequisite 6

Work:

1. Confirm no backend/client code calls `/transcribe`.
2. Remove the `8001:8001` publication and exclude voice from the default Compose profile; or stop the container if the owner prefers.
3. Document the decision and the conditions for reintroducing voice (ADR-014).
4. If voice must stay running, bind it to `127.0.0.1` only and add the Phase 4 hardening tasks to the backlog; do not leave it on `0.0.0.0`.

Acceptance criteria:

- [ ] No listener on `0.0.0.0:8001` from MyFarmAI.
- [ ] Default Compose has no publicly reachable voice service.
- [ ] No code path depends on voice; text chat/weather/resources unaffected.
- [ ] Reintroduction criteria are documented.

Verification: `docker port`, `ss -ltnp`, `docker compose config`, smoke test of unaffected routes.

Rollback: re-enable the service on loopback only; do not restore public publication.

---

### P1-04 — Python 3.12, `uv`, and dependency locking

**Gaps:** GAP-012  
**Complexity:** M  
**Depends on:** P1-01

Work:

1. Add `pyproject.toml` targeting Python 3.12; define runtime and dev dependency groups.
2. Generate and commit `uv.lock`. Remove duplicate/unused dependencies (`httpx` duplicate, backend `python-multipart` if no form route).
3. Recreate the local environment with 3.12; document `uv sync --frozen`.
4. Split test/lint/type tooling out of the runtime image.
5. Pin the base image by digest (or record the exact digest and update policy).

Acceptance criteria:

- [ ] `uv lock --check` passes.
- [ ] `uv sync --frozen` works on a clean checkout with Python 3.12.
- [ ] Runtime image installs `--no-dev`; test tools are absent.
- [ ] No duplicate dependency entries; version policy documented.
- [ ] Local, CI, and container Python versions match.

Verification: clean venv sync, `python --version`, `uv tree`, image inspection.

Rollback: keep the old `requirements.txt` until the new path passes; revert the commit if needed.

---

### P1-05 — Configuration profiles and safe defaults

**Gaps:** GAP-011 (config portion), GAP-019  
**Complexity:** M  
**Depends on:** P1-04

Work:

1. Define `development`, `test`, and `production` profiles with explicit required values.
2. Fail fast in production on wildcard CORS, missing trusted hosts, debug mode, default secrets, or a non-loopback bind without auth.
3. Add `TrustedHostMiddleware`, explicit CORS origins, and a documented proxy-trust setting.
4. Keep `.env.example` placeholder-only; ensure no real values.
5. Add config validation tests for unsafe combinations.

Acceptance criteria:

- [ ] Unsafe production config refuses to start with a clear, secret-free error.
- [ ] Development defaults bind to `127.0.0.1`.
- [ ] CORS/trusted hosts are explicit and tested.
- [ ] `.env.example` contains no real secret and documents every required variable.
- [ ] No settings are read at import time in a way that prevents test overrides.

Verification: config unit tests, startup failure tests, `docker compose config`.

Rollback: profiles are additive; revert the commit if a profile blocks local development.

---

### P1-06 — App factory and module boundaries

**Gaps:** GAP-008 (enablement), GAP-019  
**Complexity:** M  
**Depends on:** P1-04, P1-05

Work:

1. Introduce `create_app(settings)` and dependency injection for settings/DB/client lifetimes.
2. Keep existing route paths and response shapes (except the approved error envelope).
3. Move route-independent logic out of handlers; remove import-time global clients where practical.
4. Document the module dependency rules and add an import-boundary check if cheap (for example a lint rule or a small test).
5. Preserve shutdown cleanup for HTTP clients.

Acceptance criteria:

- [ ] Tests can create an app with isolated settings without mutating global state.
- [ ] Existing routes still respond with the same success shapes.
- [ ] No router contains SQL or provider-specific calls.
- [ ] Lifespan startup/shutdown is covered by a test.
- [ ] Module boundaries are documented.

Verification: app-factory tests, route smoke tests, import review.

Rollback: the factory is additive; keep a compatibility `app = create_app(settings)` entrypoint.

---

### P1-07 — Consistent error envelope and request IDs

**Gaps:** GAP-017  
**Complexity:** M  
**Depends on:** P1-06; prerequisite 11

Work:

1. Implement the flat envelope from ADR-009: `detail`, `error_code`, `request_id`, optional `errors[]`.
2. Add exception handlers for HTTP, validation, upstream, and unexpected errors; never return stack traces.
3. Generate/propagate `X-Request-ID`; include it in logs and responses.
4. Define stable codes and document them.
5. Update web and Android parsers in the same release; add contract tests.
6. Keep status codes compatible where possible (422 for validation).

Acceptance criteria:

- [ ] Every error path returns the same envelope.
- [ ] Validation errors include field-level `errors[]`.
- [ ] `X-Request-ID` is present and matches logs.
- [ ] No response contains a stack trace, SQL, secret, or raw upstream body.
- [ ] Web and Android parse all tested codes; no `[object Object]`.
- [ ] Contract tests cover 400/401/403/404/409/422/429/503/504.

Verification: API contract tests, client unit tests, manual error matrix.

Rollback: version the change with the clients; the old nested shape is not retained long-term.

---

### P1-08 — Health endpoints and structured logging

**Gaps:** GAP-018  
**Complexity:** M  
**Depends on:** P1-06

Work:

1. Add `/health/live` (process only) and `/health/ready` (DB and Ollama checks with short timeouts). Keep `/health` as a liveness alias for existing clients.
2. Return `200` when ready, `503` with component status when not; never expose credentials or internal URLs.
3. Add JSON logging with timestamp, level, request ID, route, status, latency, and safe client metadata.
4. Redact secrets, tokens, message content, and precise location; document retention.
5. Add log rotation guidance for operators (implementation in Phase 8 if not container-level).

Acceptance criteria:

- [ ] Liveness stays 200 when the DB/Ollama are down.
- [ ] Readiness returns 503 and identifies the failed dependency.
- [ ] Readiness recovers automatically when dependencies return.
- [ ] Logs are valid JSON and contain no prompts/message bodies/tokens.
- [ ] Request IDs correlate logs and responses.
- [ ] Health checks have short timeouts and do not hang.

Verification: dependency-down tests, log parsing test, redaction test.

Rollback: keep `/health` unchanged until clients migrate.

---

### P1-09 — Request hardening: body limits, proxy trust, bounded rate limiting

**Gaps:** GAP-013, GAP-014  
**Complexity:** M  
**Depends on:** P1-05, P1-06

Work:

1. Enforce a maximum request body size at the proxy and in the app (chat message limit remains, but the whole body is bounded before buffering).
2. Only trust `X-Forwarded-For`/`Forwarded` from configured proxy addresses; use the socket peer otherwise.
3. Replace the unbounded `defaultdict(list)` with a TTL/LRU-bounded limiter; add route-specific limits for chat and future auth.
4. Return `429` with `Retry-After`; log throttling without flooding.
5. Add a bounded AI semaphore (full AI gateway in Phase 4).

Acceptance criteria:

- [ ] Oversize bodies return `413` before full buffering where the proxy supports it.
- [ ] Spoofed `X-Forwarded-For` from an untrusted peer does not change the bucket.
- [ ] Limiter memory is bounded under many distinct keys.
- [ ] Chat has a stricter limit than cheap read routes.
- [ ] `429` includes `Retry-After`; tests cover boundary cases.

Verification: spoof test, memory-bound test, body-limit test, concurrency test.

Rollback: limits are configurable; restore previous values if legitimate traffic is blocked.

---

### P1-10 — Hermetic test suite

**Gaps:** GAP-008  
**Complexity:** M  
**Depends on:** P1-06

Work:

1. Replace the global test client/settings with fixtures that create an isolated DB per test and initialize the schema.
2. Ensure tests never read/write `backend/data/app.db` or `data/app.db`; add a guard assertion.
3. Run the suite in random order and in parallel where safe.
4. Fix the 7 chat tests; preserve their intent (success, continuation, validation, upstream errors).
5. Add regression tests for the error envelope, health semantics, and request limits.
6. Remove the deprecated custom event loop fixture; use the current pytest-asyncio mode.

Acceptance criteria:

- [ ] Clean run: **56/56 pass**, zero skipped for environment reasons.
- [ ] Dev DB mtime/hash unchanged after the suite.
- [ ] Tests pass in random order.
- [ ] No test depends on the developer’s `.env` or a running Ollama.
- [ ] Coverage report is generated; critical modules have meaningful tests.

Verification: `uv run pytest -q`, random-order run, before/after DB hash.

Rollback: keep the old suite until the new fixtures pass; do not delete tests to make the suite green.

---

### P1-11 — Local quality gate

**Gaps:** GAP-012, GAP-019  
**Complexity:** S/M  
**Depends on:** P1-04, P1-10

Work:

1. Add `scripts/check.sh` (or a Makefile target) that runs format check, lint, type check, tests, OpenAPI check, Compose validation, and secret scan.
2. Fix `mypy.ini` (TOML syntax in INI, duplicate overrides) or move configuration to `pyproject.toml`.
3. Set formatting/lint rules once; do not reformat unrelated code without a separate commit.
4. Add a coverage report; set a modest floor after the baseline, with higher expectations for security-critical modules.
5. Document the command in the developer README.

Acceptance criteria:

- [ ] `scripts/check.sh` passes on a clean checkout.
- [ ] Ruff format/check and mypy run with no config warnings.
- [ ] The script fails on a deliberately broken test/lint/type error.
- [ ] CI can call the same script without duplication.
- [ ] Runtime and dev dependencies are separated.

Verification: run the script, inject a failure, confirm non-zero exit.

Rollback: keep individual commands documented if the script is too rigid.

---

### P1-12 — CI and supply-chain checks

**Gaps:** GAP-012  
**Complexity:** M  
**Depends on:** P1-04, P1-10, P1-11; prerequisite 9

Work:

1. Add CI configuration for the chosen platform: install with `uv sync --frozen`, run `scripts/check.sh`, build the image, validate Compose.
2. Add dependency auditing (pip-audit or OSV-Scanner), secret scanning, and image scanning (Trivy or equivalent).
3. Pin GitHub Actions/CI images by commit SHA where applicable.
4. Generate an SBOM if the tooling supports it cheaply; otherwise document the gap.
5. Require the checks for merges once a remote is configured.

Acceptance criteria:

- [ ] CI passes on a clean branch and fails on a seeded lint/test/secret failure.
- [ ] Dependency, secret, and image scans run and their findings are reviewed.
- [ ] The same `scripts/check.sh` runs locally and in CI.
- [ ] No CI job requires a paid service or a personal credential for the core checks.
- [ ] Build artifacts are reproducible enough to identify the source commit.

Verification: CI run logs, seeded failure, scan reports.

Rollback: disable a noisy scanner only with a documented reason and a follow-up date.

---

### P1-13 — OpenAPI artifact and documentation correction

**Gaps:** GAP-019  
**Complexity:** S/M  
**Depends on:** P1-06, P1-07, P1-08

Work:

1. Generate `docs/api/openapi.json` from the app in a deterministic script; review and commit it.
2. Add a CI check that regenerating produces no diff (or fails with instructions).
3. Correct stale docs: `docs/backend/BACKEND_AUDIT.md`, `ARCHITECTURE.md`, `API.md`, `ROADMAP.md`; align version with `settings.app_version`.
4. Document error codes, health semantics, auth expectations, and the resource category behaviour.
5. Add a developer setup guide (clean checkout, Python 3.12, `uv`, tests, local run).

Acceptance criteria:

- [ ] OpenAPI artifact matches the running app.
- [ ] CI detects an undocumented API change.
- [ ] Docs no longer claim “no DB/chat/weather,” a 404 `/health`, 56/56 without evidence, or a different version.
- [ ] Error/health docs match ADR-009 and P1-08.
- [ ] A new developer can set up and run tests from the README alone.

Verification: regenerate/diff, docs review, fresh-setup walkthrough.

Rollback: docs are versioned with code; revert the commit if the artifact is wrong.

---

### P1-14 — Container baseline

**Gaps:** GAP-020  
**Complexity:** M  
**Depends on:** P1-04, P1-08, P1-15

Work:

1. Multi-stage Dockerfile: build dependencies separate from runtime; non-root user; no test tooling; `PYTHONDONTWRITEBYTECODE`, no cache.
2. Add `.dockerignore` (databases, env files, tests, caches, docs unless needed).
3. Add a `HEALTHCHECK` that calls liveness (not readiness).
4. Update Compose: no host networking; no public backend/DB/search/voice ports; internal network; `restart: unless-stopped`; `cap_drop`, `no-new-privileges`, read-only root where practical; resource limits only after measurement.
5. Keep the production TLS/Caddy deployment for Phase 8; validate the config now.

Acceptance criteria:

- [ ] Image runs as a non-root UID.
- [ ] Image contains no dev dependencies, `.env`, DB, or Git metadata.
- [ ] `docker compose config` passes; only intended ports are published.
- [ ] Health check reports healthy; a failing app becomes unhealthy.
- [ ] Container restart preserves data only through documented volumes.
- [ ] No secret is present in image layers.

Verification: `docker build`, `docker inspect`, `docker compose config`, port scan, image history/secret scan.

Rollback: keep the previous image tag until the new one passes; do not publish either.

---

### P1-15 — Disk and build preflight

**Gaps:** GAP-015  
**Complexity:** S  
**Depends on:** prerequisite 10

Work:

1. Measure free space on `/` and `/data`; record the minimum headroom required for images/build cache/Postgres.
2. Identify reclaimable Docker images/build cache; do **not** delete without owner approval.
3. Recommend and, if approved, move Docker’s data-root to `/data/docker` or prune specific unused artifacts.
4. Document the preflight in the developer/operations guide.

Acceptance criteria:

- [ ] A documented headroom threshold exists (for example ≥10 GB free on the Docker root).
- [ ] A backend image build succeeds without exhausting `/`.
- [ ] No model, volume, or unrelated project data is deleted without explicit approval.
- [ ] The chosen mitigation and its rollback are recorded.

Verification: `df -h`, `docker system df`, successful build, post-build free space.

Rollback: relocation requires a daemon restart; document the original data-root and restore path.

---

### P1-16 — Licence and third-party notices

**Gaps:** GAP-023  
**Complexity:** S (plus legal review)  
**Depends on:** prerequisite 8

Work:

1. Choose the project licence or record a dated deferral.
2. Add `LICENSE` and a third-party notices file covering SearXNG (AGPL-3.0), models, Python packages, and clients.
3. Review AGPL network-use obligations if SearXNG is modified or distributed.
4. Document the policy for adding dependencies: licence, maintenance, cost, and data-sharing review.

Acceptance criteria:

- [ ] `LICENSE` exists or a signed deferral is recorded.
- [ ] Third-party notices list the actual runtime dependencies and model licences.
- [ ] AGPL obligations are understood and documented.
- [ ] No dependency with an incompatible licence is added silently.

Verification: legal/owner sign-off; dependency inventory cross-check.

Rollback: not applicable; a licence choice can be revised with a new record.

---

### P1-17 — Model and host benchmark (Phase 4 gate, optional in Phase 1)

**Gaps:** GAP-021  
**Complexity:** M  
**Depends on:** P1-15, owner approval to load models

Work:

1. Benchmark `qwen3:4b` and at least one smaller candidate on representative prompts at the intended context size.
2. Measure first-token and total latency, peak RAM/VRAM, swap, and behaviour at 1/2/4 concurrent requests.
3. Tune PostgreSQL memory settings only after Postgres exists (Phase 2); record provisional limits.
4. Produce a report with a go/no-go recommendation and a chosen model/context.

Acceptance criteria:

- [ ] Measurements are reproducible and recorded with host state.
- [ ] A model/context recommendation is made, or the feature is explicitly blocked.
- [ ] No model is pulled without approval; no unrelated stack is stopped without approval.
- [ ] Results feed Phase 4 planning.

Verification: benchmark log, `nvidia-smi`, `ollama ps`, latency table.

Rollback: stop the benchmark process; leave models as found.

---

### P1-18 — Android base URL fix (client task, coordinated)

**Gaps:** GAP-009  
**Complexity:** S  
**Depends on:** client owner; P1-07 for error parsing

Work:

1. Prefix every request with the configured absolute base URL.
2. Wire `EXPO_PUBLIC_API_BASE_URL` or the existing config; remove dead code.
3. Add a smoke test or documented emulator check.
4. Update the Android error parser for the flat envelope.

Acceptance criteria:

- [ ] No relative `fetch` remains.
- [ ] Emulator/device reaches `/health` and chat/weather/resources.
- [ ] Errors display a readable message, not `[object Object]`.
- [ ] Configuration is documented; no secret is embedded in the app.

Verification: emulator/device smoke test, typecheck/lint, request log.

Rollback: keep the old config until the new one is verified on a device.

## 4. Sequencing

| Wave | Tasks | Purpose |
|---|---|---|
| **0 — Safety** | P1-01, P1-02, P1-03, P1-15 | Protect data, remove exposed secret/service, confirm disk headroom. |
| **1 — Reproducibility** | P1-04, P1-05, P1-10, P1-11 | Python/uv, config, hermetic tests, local quality gate. |
| **2 — Contract/runtime** | P1-06, P1-07, P1-08, P1-09 | App factory, errors, health/logging, request hardening. |
| **3 — Delivery** | P1-12, P1-13, P1-14, P1-16 | CI/scans, OpenAPI/docs, container baseline, licence. |
| **Parallel/gate** | P1-17, P1-18 | Model benchmark and client fix; neither blocks the backend exit gate, but P1-18 blocks mobile testing. |

Do not start Wave 1 before Wave 0 data safety is complete. P1-07 must be coordinated with both clients before release.

## 5. Phase 1 exit checklist

- [ ] Clean checkout + Python 3.12 + `uv sync --frozen` succeeds.
- [ ] `scripts/check.sh` passes: format, lint, type check, tests, OpenAPI diff, Compose config, secret scan.
- [ ] Test suite is 56/56 on a clean DB; dev DB untouched; tests pass in random order.
- [ ] `/health/live` and `/health/ready` behave correctly with dependencies up/down; legacy `/health` retained.
- [ ] Error envelope is consistent; web and Android parse it; request IDs correlate.
- [ ] Body limits, trusted-proxy handling, and bounded rate limiting are tested.
- [ ] Container runs non-root, has a health check, and publishes no backend/DB/search/voice port.
- [ ] Secret scan is clean; no DB is tracked; backup/restore drill evidence exists.
- [ ] OpenAPI artifact matches the app; stale docs corrected; version has one source.
- [ ] Licence decision/third-party notices recorded.
- [ ] No non-loopback exposure, no production deploy, no data migration, no destructive cleanup without separate approval.
- [ ] Phase 0 decisions that remain open are recorded with owners and dates.

## 6. Risks and mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Disk fills during image build | High (`/` 5.3 GB free) | Build failure/host instability | P1-15 preflight; build after cleanup/relocation approval |
| Test refactor changes behaviour | Medium | Hidden regression | Characterization tests first; keep route success shapes |
| Error-contract change breaks clients | Medium | Web/Android errors | Coordinate release; contract tests; update both parsers |
| `uv`/Python 3.12 migration breaks a dependency | Medium | Setup failure | Lockfile, CI, keep old requirements until green |
| Secret rotation disrupts SearXNG sessions | Low | Search unavailable briefly | Expected; restart and verify; document |
| Voice stop affects an unknown consumer | Low | Feature loss | Confirm no callers; keep code; loopback-only fallback |
| CI platform/remote not chosen | Medium | P1-12 blocked | Local `scripts/check.sh` first; add CI when decided |
| Scope creep into auth/DB | Medium | Phase 1 slips | Enforce §1.2; new work needs approval |
| Shared host contention | High | Flaky benchmarks/tests | Measure with a controlled profile; avoid unrelated stacks |

## 7. Deliverables

1. Committed baseline and verified backup/bundle.
2. Canonical-database decision record.
3. `pyproject.toml`, `uv.lock`, Python 3.12 setup guide.
4. App factory, config profiles, error envelope, health endpoints, structured logging.
5. Request-hardening middleware with tests.
6. Hermetic test suite (56/56) and `scripts/check.sh`.
7. CI configuration and scan reports (platform-dependent).
8. `docs/api/openapi.json` and corrected backend docs.
9. Non-root Dockerfile, `.dockerignore`, validated Compose baseline.
10. Backup/restore drill evidence.
11. Licence and third-party notices, or a dated deferral.
12. Model benchmark report (if P1-17 approved).
13. Android base-URL fix and smoke-test evidence (if P1-18 approved).

## 8. Approval checklist

- [ ] Phase 0 documents reviewed and accepted.
- [ ] Phase 1 scope in §1 accepted; exclusions in §1.2 accepted.
- [ ] Prerequisites in §2 resolved or explicitly deferred.
- [ ] ADR-001, 002, 009, 010, 013, 014 accepted.
- [ ] Commit/branch/remote or bundle approach approved.
- [ ] Secret rotation and voice containment approved.
- [ ] Canonical database decision recorded.
- [ ] Backup location and drill approved.
- [ ] Licence direction approved or deferred with a date.
- [ ] CI platform/remote decision recorded.
- [ ] Disk mitigation approved if needed.
- [ ] Phase 1 start date and reviewer assigned.

## 9. Explicit non-execution statement

**No Phase 1 task has been executed.** This plan is a proposal. No source code, configuration, dependency, database, container, or deployment was changed in Phase 0. The only intentional writes were the Phase 0 documents in this directory and an isolated test database under `/tmp/opencode`; ignored tool caches may have been refreshed.

**Next step:** approve, approve with changes, or reject this plan and the decisions in [`README.md`](README.md) §6.
