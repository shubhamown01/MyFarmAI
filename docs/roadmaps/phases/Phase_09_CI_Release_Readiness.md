# Phase 9 — CI, Quality Gates and Release Readiness

## Objective

Make changes repeatable, reviewable and releasable with automated quality gates and tested recovery procedures.

## Entry conditions
- Core API, database, security and integration contracts are stable.
- The team has agreed on the baseline and handling of known failures.
- Deployment and backup procedures exist.

## CI quality gates
1. Formatting and linting.
2. Type checking.
3. Unit tests.
4. Integration tests using a disposable PostgreSQL instance.
5. API/OpenAPI contract checks.
6. Migration-from-empty checks.
7. Migration/recovery rehearsal checks where feasible.
8. Authentication and authorization regression tests.
9. Security tests for request limits, rate limits, SSRF and prompt injection as relevant.
10. Dependency and licence policy checks.
11. Secret scanning.
12. Container build and Compose validation.
13. Documentation consistency checks.

Do not claim a check passes unless it actually ran and the result was recorded. Do not hide known failures by using developer-local data.

## Release process
- Every feature has acceptance criteria and test evidence.
- Every schema change has a reviewed migration.
- Every new integration has licence/terms review and a failure strategy.
- Every security-sensitive change has a threat review.
- Configuration changes include upgrade/recovery notes.
- Release notes identify changes, known issues and migration steps.
- Releases are tagged only through an approved workflow.
- No unreviewed local changes are accidentally included.

## Operational readiness
- Health/readiness checks have documented meanings.
- Logs and error responses support diagnosis without leaking sensitive data.
- Backup restoration is tested.
- Dependency/image update process is documented.
- Resource usage and disk capacity are checked.
- Incident and rollback/forward-fix procedures are available.

## Deliverables
- CI workflow and quality gate definitions.
- Test matrix and baseline report.
- Release checklist and changelog policy.
- Security/dependency scanning policy.
- Verified deployment and restore evidence.

## Acceptance criteria
- [ ] CI checks run deterministically.
- [ ] Known failures are visible and assigned.
- [ ] Migrations and contracts are checked.
- [ ] Secret and dependency scans are included.
- [ ] Documentation matches actual commands/configuration.
- [ ] Release artifact and steps are reproducible.
- [ ] Recovery and operational readiness are demonstrated.

## Exit gate
Release readiness is explicitly approved by the designated project owner. Passing CI alone is not authorization to deploy publicly.
