# MyFarmAI — Security Audit Plan (V1.0.0)

- **Date:** 2026-11-10
- **Repository:** `/data/MyFarmAI`
- **Baseline:** branch `phase-01-foundation`, HEAD `0a75e26`, `VERSION` 1.0.0
- **Audit type:** source, configuration, dependency, container, API, Android, and AI security review with safe dynamic verification
- **Status:** COMPLETE (with documented limitations; see §7)

## 1. Authorization and scope

Authorized:

- MyFarmAI source tree and local development environment.
- Local Docker containers (`myfarmai-backend`, `myfarmai-postgres`).
- The owner-designated staging deployment:
  - backend `https://myfarmai-backend-50047414881.development.catalystappsail.in`
  - web `https://myfarmai-web-zwpytbwu.onslate.in`

Not authorized / not performed:

- Production systems other than the owner-designated staging URLs.
- Intrusive exploitation, DoS, persistence, lateral movement, or data exfiltration.
- Scanning of unrelated hosts or third-party services.
- Database schema changes, data deletion, secret rotation, signing-key changes.
- Ubuntu package upgrades (separate approval required).

Only synthetic accounts and data were used. No real tester, farmer, or owner data
was accessed beyond the minimum needed to confirm the public feedback exposure
(two synthetic-looking rows returned by the staging endpoint; contents not
retained in this repository).

## 2. Objectives

1. Identify and classify security defects in the V1.0.0 code and deployment.
2. Confirm exploitability where safe; distinguish confirmed, suspected, and false positives.
3. Fix low-risk confirmed issues with regression tests.
4. Produce evidence for the V1 release security gates.
5. Record residual risk and owner decisions without suppressing findings.

## 3. Methodology

| Phase | Activity | Tooling |
|---|---|---|
| P0 | Governance, scope, and prior-audit review | Manual review of `docs/governance/`, `docs/security/`, `docs/roadmaps/phase-00/SECURITY_AND_PRIVACY_AUDIT.md` |
| P1 | Secret scanning | gitleaks 8.18.0 |
| P2 | Static analysis (Python, JS/TS, Docker, IaC) | Semgrep 1.185.0, Bandit 1.9.4 |
| P3 | Dependency and container review | pip-audit 2.10.1, osv-scanner 2.7.1, npm audit, Trivy 0.76.2 |
| P4 | Manual source review | Auth, sessions, CSRF, rate limiting, uploads, OAuth, admin routes, repositories, web client, Android manifest/signing |
| P5 | Safe dynamic verification | `curl` against local backend and staging; ASGI test client; no active exploitation |
| P6 | Remediation and regression tests | Backend pytest suite, web Jest, Android typecheck/lint |
| P7 | Reporting and release gate assessment | This document set |

PentAGI orchestration was evaluated but not deployed: it requires an isolated
Docker environment and an external LLM provider, and the host had insufficient
free memory during the audit (see `PENTAGI_TEST_RESULTS.md`). The same phases
were executed with the open-source toolchain above plus manual review.

## 4. Environments and constraints

- Host memory: 7.1 GB total, ~0.7–2.6 GB available during testing; swap heavily used.
- Docker root: `/var/lib/docker` (SSD). This is a pre-existing deviation from the
  HDD-first policy; it was not changed during the audit.
- Audit tools were installed under `/data/tools` (HDD).
- The local backend container image was stale (`0a440615a94f`) relative to source
  HEAD `0a75e26`; source review and tests reflect the V1.0.0 tree, and staging
  reflects a newer deployed build. This discrepancy is recorded, not hidden.
- No production credentials or signing keys were used.

## 5. Severity model

| Severity | Meaning |
|---|---|
| Critical | Unauthenticated compromise of accounts/data, RCE, or full tenant isolation failure |
| High | Practical account/data exposure, auth bypass, or remotely triggerable serious DoS |
| Medium | Exploitable with preconditions, defense-in-depth gaps, or supply-chain risk with real impact |
| Low | Limited impact, build/dev-only exposure, or hardening opportunity |
| Info | Observation, false positive, or accepted platform behavior |

Each finding records: ID, component, file:line, reproduction, evidence, impact,
likelihood, severity, repair, regression test, and verification status.

## 6. Deliverables

- `SECURITY_AUDIT_PLAN.md` (this file)
- `SECURITY_FINDINGS.md`
- `PENTAGI_TEST_RESULTS.md`
- `DEPENDENCY_AUDIT.md`
- `API_SECURITY_AUDIT.md`
- `ANDROID_SECURITY_AUDIT.md`
- `AI_SECURITY_AUDIT.md`
- `REMEDIATION_LOG.md`
- `V1_RELEASE_SECURITY_CHECKLIST.md`

## 7. Limitations

- No ZAP/burp active scan; dynamic checks were targeted and non-intrusive.
- No PentAGI autonomous exploitation run (resource constraint).
- No production deployment testing; staging only.
- Android release APK was not rebuilt during this audit; findings are based on the
  committed Expo config, the generated manifest, and prior release evidence.
- Full `pg_dump` backup verification remains owner-console dependent (pre-existing gate).
- Third-party provider consoles (Google/Microsoft OAuth, Catalyst, Neon) were not audited.

## 8. Exit criteria

The audit is complete when every planned phase has evidence, every confirmed
finding is fixed or explicitly accepted/deferred by the owner, and the V1 release
checklist records a verdict for each gate. Completion does not imply the
application is "fully secure"; it means the defined scope was examined and the
residual risk is documented.
