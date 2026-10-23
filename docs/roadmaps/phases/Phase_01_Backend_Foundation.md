# Phase 1 — Backend Foundation

## Objective

Establish a reproducible, testable FastAPI foundation without disrupting existing MyFarmAI work or data.

## Entry conditions

- Phase 0 documents reviewed.
- Explicit approval for Phase 1 scope and relevant ADRs.
- Working tree baseline and preservation plan recorded.
- Existing SQLite files protected from accidental staging or mutation.
- The seven clean-database test failures have a documented investigation plan.
- Each planned change is small, reviewable and separately verifiable.

## Workstreams

### 1. Project and dependency baseline
- Confirm supported Python version and runtime compatibility.
- Adopt `uv` and a committed lockfile if approved.
- Pin direct dependencies and document upgrade policy.
- Separate runtime and development/test dependencies.
- Review licences and transitive dependency risks.
- Do not remove or replace existing tools without an approved plan.

### 2. Application structure
- Keep HTTP routing, request/response schemas, application services and persistence responsibilities separate.
- Establish consistent configuration loading and validation.
- Keep secrets out of source code, logs and committed environment files.
- Use a single application entry point and documented startup command.

### 3. API conventions
- Confirm API prefix/versioning strategy.
- Standardize validation errors, application errors and request IDs.
- Preserve existing client contracts unless a breaking change is approved.
- Generate and inspect OpenAPI output.
- Add `/health/live` and `/health/ready` only after confirming existing routes and clients.

### 4. Quality baseline
- Configure Pytest, Ruff and the approved type checker.
- Reproduce tests against a clean, disposable database.
- Investigate the reported seven failures; do not mask them by reusing a developer database.
- Add deterministic test setup and teardown.
- Add tests for configuration failures and health endpoints.

### 5. Container foundation
- Review existing Dockerfiles before proposing changes.
- Use a non-root runtime user where compatible.
- Add `.dockerignore` only after checking existing files.
- Pin base images and document update strategy.
- Do not build or restart containers without approval.

## Deliverables
- Approved backend structure and coding conventions.
- Reproducible environment and dependency lock.
- Health and error-handling contracts.
- Baseline tests and quality checks.
- Updated backend setup documentation.
- Change log listing exact files changed and commands/tests executed.

## Acceptance criteria
- [ ] Clean setup follows documented instructions.
- [ ] Application startup is reproducible.
- [ ] Health endpoints have documented semantics.
- [ ] OpenAPI contract is inspectable.
- [ ] Lint and type checks pass or documented exceptions are approved.
- [ ] Clean-database tests have a reliable baseline; failures are not hidden.
- [ ] No secrets or database records are added to Git.
- [ ] No mandatory paid API/service is introduced.
- [ ] All changes are reviewed and documented.

## Exit gate

A reviewer explicitly accepts the baseline, test results, dependency policy and file-level change report before Phase 2 begins.
