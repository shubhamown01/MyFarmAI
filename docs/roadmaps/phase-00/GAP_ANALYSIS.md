# Gap Analysis

**Phase:** 0 — read-only  
**Date:** 2026-10-21  
**Purpose:** Convert audit findings into an ordered, verifiable gap register that links evidence to work, acceptance, and approval.  
**Related:** [`CURRENT_STATE_AUDIT.md`](CURRENT_STATE_AUDIT.md), [`SECURITY_AND_PRIVACY_AUDIT.md`](SECURITY_AND_PRIVACY_AUDIT.md), [`ARCHITECTURE_DECISIONS.md`](ARCHITECTURE_DECISIONS.md), [`PHASE_01_IMPLEMENTATION_PLAN.md`](PHASE_01_IMPLEMENTATION_PLAN.md)

---

## 1. Priority definitions

| Priority | Meaning | Trigger |
|---|---|---|
| **P0** | Stop-ship: data loss, secret exposure, unauthenticated exposure, false quality signal, or a blocker for a safe commit/build. | Must be closed before the triggering event: commit, build, network exposure, or commercial launch. Not all P0 items are Phase 1 work. |
| **P1** | Required for a trustworthy foundation and the Phase 1 exit gate. | Close in Phase 1 unless explicitly deferred with approval. |
| **P2** | Required before the relevant product capability ships. | Phases 2–7, tied to the roadmap. |
| **P3** | Optional or future; no current evidence justifies the work. | Revisit only with measurements or a new requirement. |

**Important:** “P0” does not mean “all must be fixed in Phase 1.” Authentication (GAP-007) is a P0 for any non-loopback deployment but is scheduled for Phase 3. Until then, the backend must remain loopback-only. Weather licensing (GAP-010) is a P0 for commercial launch but is a Phase 5 decision.

## 2. Summary

| Priority | Count | Theme |
|---|---:|---|
| P0 | 15 | Data safety, secrets, exposure, test integrity, licensing, disk |
| P1 | 12 | Reproducibility, migrations, contracts, observability, hardening |
| P2 | 7 | Domain model, AI gateway, research, privacy at feature level, operations |
| P3 | 3 | Encryption at rest, vector search, enterprise/HA options |
| **Total** | **37** | |

No gap is closed by this audit. The register records desired state and verification only.

## 3. P0 — stop-ship gaps

| ID | Gap | Evidence | Desired state / exit condition | Impact if unaddressed | Related | Target |
|---|---|---|---|---|---|---|
| GAP-001 | Working tree has no remote or verified backup; one commit with large uncommitted work | `CURRENT_STATE_AUDIT.md` §1.1 | Work is committed on a branch and backed up (remote or verified bundle) before bulk changes | A disk error or bad command destroys unrecoverable work | CS §1.1 | Phase 1, first action |
| GAP-002 | `backend/data/app.db` is untracked but not ignored | S-05, DB-S02 | Database/cache patterns ignored; no DB tracked; history checked | Conversations and location data could be committed/published | S-05, DB-S02 | Phase 1, first action |
| GAP-003 | Two divergent SQLite files; canonical source undecided | DB-S03, `DATABASE_ASSESSMENT.md` §2 | Owner records the canonical file and whether data must be preserved | Wrong file migrated/backed up; silent data loss | DB-S03 | Phase 1 decision; Phase 2 migration |
| GAP-004 | No backup or restore procedure | S-06, DB §7 | Documented backup, checksum, integrity check, and a successful restore drill | Total loss on disk failure or bad migration | S-06, HW-03 | Phase 1 |
| GAP-005 | Hardcoded SearXNG secret in a non-ignored file | S-04, INT-F03 | Secret rotated, removed from YAML, loaded from environment/secret store; scan added | Secret exposure and possible session/CSRF forgery | S-04, INT-F03 | Phase 1 (approval for restart) |
| GAP-006 | Voice endpoint unauthenticated, unbounded, root, published on `0.0.0.0:8001` | S-03, INT-F05, S-12 | Voice not published; default profile excludes it, or it is authenticated and limited | Remote resource exhaustion; root container exposure | S-03, INT-F05, S-12 | Phase 1 containment; Phase 4 decision |
| GAP-007 | No authentication, authorization, or ownership | S-01, S-02, DB-S01 | Every private route authenticates; ownership enforced in service layer; auth matrix passes | Anyone can use chat/weather and a leaked ID grants conversation access | S-01, S-02, DB-S01 | Phase 3; blocks any non-loopback deployment |
| GAP-008 | Test suite is not hermetic; 7 chat tests fail on a clean DB; 56/56 claim is false | CS §10, `API_CONTRACT_INVENTORY.md` §7 | App factory + per-test DB; clean run 56/56; tests never touch dev DB | False quality signal; dev data corruption; regressions unnoticed | CS §10 | Phase 1 |
| GAP-009 | Android client builds relative URLs; configured base URL unused | API-C-04, INT-F07 | Android uses an absolute base URL and passes an emulator/device smoke test | Android cannot reach the backend | API-C-04 | Phase 1 client task |
| GAP-010 | Open-Meteo free tier is non-commercial only | INT-01, INT-F01 | Provider decision recorded; commercial use has a licensed path or is blocked | Legal/commercial risk; possible provider blocking | INT-01 | Phase 5; blocks commercial launch |
| GAP-011 | No TLS, reverse proxy, TrustedHost, or production CORS policy | S-09 | Caddy terminates TLS; explicit origins; trusted hosts; HTTP→HTTPS; security headers | Credentials/prompts exposed; host-header attacks | S-09 | Phase 1 config; Phase 8 production |
| GAP-012 | Dependencies/images unpinned; no lockfile, CI, or scans | DEP-01..05, S-13 | `uv.lock`, pinned digests, CI checks, dependency/secret/image scans | Non-reproducible builds; silent compromise/breakage | DEP-01..05, S-13 | Phase 1 |
| GAP-013 | Rate limiter trusts `X-Forwarded-For` and grows unbounded | S-07 | Trusted-proxy configuration; socket peer by default; TTL/LRU bound; route limits | Limit bypass and slow memory exhaustion | S-07 | Phase 1 |
| GAP-014 | No request-body size limit; no AI concurrency cap | S-08, S-18 | Proxy + app body limits; bounded AI semaphore; 429/503 with `Retry-After` | Memory/VRAM exhaustion; denial of service | S-08, S-18 | Phase 1 middleware; Phase 4 AI cap |
| GAP-015 | `/` has 5.3 GB free; Docker root and images/volumes are on `/` | HW-02, HW-07 | Approved cleanup or relocation; build preflight requires documented headroom | Image build fails; host instability | HW-02, HW-07 | Phase 1 preflight |

### 3.1 P0 work, complexity, and verification

| ID | Work summary | Complexity | Verification | Approval needed |
|---|---|---|---|---|
| GAP-001 | Create a branch, commit the audited work in logical commits, create a verified bundle/remote; tag the Phase 0 baseline | S | `git bundle verify`; clone/restore; commit hashes recorded | Owner (history and commit scope) |
| GAP-002 | Add `backend/data/`, `**/*.db`, `**/*.sqlite*`, `infra/searxng/data/`, model caches; verify no tracked DB | S | `git check-ignore -v`; `git ls-files` contains no DB; secret scan clean | Owner |
| GAP-003 | Owner selects canonical DB; write a one-page decision; do not merge | S | Signed decision record with file path, counts, preservation requirement | Data owner |
| GAP-004 | Add a backup script and runbook; back up current files; restore to a disposable path; verify counts | M | Checksum matches; `PRAGMA integrity_check=ok`; row counts match; restore smoke test | Owner (backup location) |
| GAP-005 | Rotate secret, replace YAML value with env reference, restart SearXNG, add secret scan | S | `git grep` finds no secret; container healthy; old secret rejected/rotated | Operations (restart) |
| GAP-006 | Remove published port and/or stop voice; exclude from default Compose; document decision | S | `docker port`/`ss` shows no 8001; Compose config has no public voice; no consumer breaks | Owner (service impact) |
| GAP-007 | Build auth/users/sessions, ownership columns, authorization checks, tests | L | Anonymous write denied; cross-user/cross-farm access 404; expired/revoked sessions fail; CSRF test | Security review; product registration policy |
| GAP-008 | App factory, settings injection, temp DB per test, schema init, regression test | M | Clean run 56/56; dev DB mtime unchanged; tests pass in random order | Engineering |
| GAP-009 | Prefix requests with configured base URL; add a smoke test | S | Emulator/device request succeeds; no relative URL remains | Client owner |
| GAP-010 | Record terms; add adapter/cache/attribution; decide commercial path | M | Terms/decision record; attribution visible; cache test; no commercial launch without licence | Product/legal |
| GAP-011 | Caddy config, TLS, TrustedHost, explicit CORS, security headers | M | Only 443 exposed; HTTP redirects; CORS allowlist test; headers present | Operations/domain |
| GAP-012 | `pyproject.toml` + `uv.lock`, pin digests, `scripts/check.sh`, CI, scans | M | `uv lock --check`; CI green; scan reports reviewed; image digest pinned | Engineering |
| GAP-013 | Trusted-proxy setting, bounded limiter, route-specific quotas | S/M | Spoofed XFF does not bypass; map size bounded; 429 + `Retry-After` | Engineering |
| GAP-014 | Body-limit middleware/proxy; AI semaphore; overload response | M | Oversize body 413; concurrency returns 429/503; memory stable under load | Engineering |
| GAP-015 | Measure free space; prune/relocate Docker with approval; document preflight | S/M | `df` headroom recorded; image build succeeds; no data loss | Owner (destructive cleanup) |

## 4. P1 — foundation gaps

| ID | Gap | Evidence | Desired state | Related | Phase |
|---|---|---|---|---|---|
| GAP-016 | No migration tool; startup `CREATE TABLE IF NOT EXISTS`; FK enforcement off; weak constraints | DB §3–4, DB-S08 | Alembic-only schema; FKs and checks enforced; deterministic timestamps; UUID/`TIMESTAMPTZ` | DB-S08, API-C-03 | 2 |
| GAP-017 | Nested vs flat error contract; Android `[object Object]` | S-10, API-C-01 | One flat envelope; stable codes; validation errors included; clients updated | S-10, API-C-01 | 1 |
| GAP-018 | No readiness; health does not check dependencies; logs are plain text and may include PII | CS §2.3, S-10 | `/health/live` + `/health/ready`; JSON logs; request IDs; redaction | S-10, DB-S06 | 1 |
| GAP-019 | Stale docs, version drift, no OpenAPI artifact, inconsistent resource semantics | CS §11, API-C-08/10/11 | Docs match code; one version source; generated OpenAPI reviewed; semantics documented | API-C-08/10/11 | 1 |
| GAP-020 | Containers run as root; no health checks/limits; host networking; test tooling in runtime image | S-12, DEP-03 | Non-root, minimal runtime, health checks, internal network, limits after measurement | S-12, DEP-03 | 1/8 |
| GAP-021 | `qwen3:4b` does not fit 2 GiB VRAM; latency/concurrency unmeasured; Postgres settings untuned | HW §4, INT-03, HW-06 | Benchmark report; chosen model/context; measured limits; tuned DB | HW-01/06/08, INT-03 | 1/4 |
| GAP-022 | Voice model downloads from HuggingFace at runtime; cache lost on recreate | INT-F04, DEP-07, HW-04 | Pre-baked/pinned model or persistent cache; no runtime HF dependency | INT-F04, DEP-07 | 4 (if voice retained) |
| GAP-023 | No project licence; AGPL-3.0 obligations for SearXNG unreviewed | S-13, DEP-06 | `LICENSE`, third-party notices, legal decision on AGPL/distribution | S-13, DEP-06 | 1 |
| GAP-024 | No retention, deletion, or export; indefinite storage | S-11, DB-S05 | Documented retention; user deletion/export; cascading delete; backups age out | S-11, DB-S05 | 2/3 |
| GAP-025 | History ordering ties; no idempotency; follow-up context resets | API-C-05/06/07 | Deterministic `(created_at,id)`; idempotency key; stored context reused | API-C-05/06/07 | 2/4 |
| GAP-026 | No weather cache/attribution; upstream schema unvalidated | INT-F02, API-C-09 | Bounded cache; attribution; schema validation with fixtures; quota backoff | INT-F02, API-C-09 | 5 |
| GAP-027 | Root `.env` mode 664; DB file mode 644; secret handling undocumented | S-16, DB-S07 | `600` for secret files; documented secret management; no secrets in images | S-16, DB-S07 | 1 |

### 4.1 P1 work and verification

| ID | Work summary | Complexity | Verification |
|---|---|---|---|
| GAP-016 | SQLAlchemy models + Alembic baseline; enable FKs in SQLite tests; constraints/indexes | L | `alembic upgrade head`; constraint/negative tests; migration-parity test |
| GAP-017 | Error envelope, handlers, request ID, client updates | M | Contract tests; web/Android parse same shape; no stack traces |
| GAP-018 | Health split, JSON logging, correlation, redaction | M | Readiness fails when DB/Ollama down; logs contain request ID, no prompts/secrets |
| GAP-019 | Correct docs, single version source, OpenAPI artifact, resource semantics | S/M | Docs review; OpenAPI diff; version test |
| GAP-020 | Multi-stage/non-root image, `.dockerignore`, health checks, internal network | M | `docker inspect` user ≠ root; health check passes; no public ports |
| GAP-021 | Benchmark model/context/concurrency; tune Postgres; record limits | M | Report with latency/RAM/VRAM; limits applied only after measurement |
| GAP-022 | Pre-download/pin model; mount cache; remove runtime download | S/M | No outbound HF call at request time; cache survives recreate |
| GAP-023 | Choose licence; add notices; legal review of AGPL and model/data licences | S | `LICENSE` present; notices complete; decision recorded |
| GAP-024 | Retention policy, delete/export endpoints, cascade tests, backup expiry | M | Delete removes owned data; export works; backups expire; policy published |
| GAP-025 | Ordering tie-breaker, idempotency key, context persistence | M | Tie-order test; retry does not duplicate; follow-up keeps context |
| GAP-026 | Cache, attribution, upstream schema validation, backoff | M | Cache hit/miss; stale/limit handling; attribution present; fixture tests |
| GAP-027 | Restrict file modes; document secret handling; scan images | S | `stat` shows 600; no secret in image/Git; runbook exists |

## 5. P2 — capability gaps (before the relevant feature ships)

| ID | Gap | Evidence | Desired state | Target |
|---|---|---|---|---|
| GAP-028 | No outbound egress allowlist/policy | INT-F06 | Documented required egress; deny-by-default where platform permits; proxy logs | Phase 8 |
| GAP-029 | No farm/crop/crop-cycle domain model or APIs | Roadmap Phase 2/5; CS §5 | Confirmed MVP workflows modeled with ownership and constraints | Phase 2/5 |
| GAP-030 | No AI gateway abstraction, prompt versioning, or evaluation set | CS §7 | Provider-neutral gateway; template versions; agriculture eval and regression tests | Phase 4 |
| GAP-031 | No search client, extraction, provenance, or citations | Roadmap Phase 6 | Research pipeline with citations and stored provenance | Phase 6 |
| GAP-032 | No SSRF or prompt-injection controls | S-14, S-15 | SSRF-safe fetcher; delimited untrusted content; injection regression tests | Phase 4/6 |
| GAP-033 | No background jobs/notifications | Roadmap Phase 7 | Only if measured; queue with retries, idempotency, DLQ, status | Phase 7 |
| GAP-034 | No metrics/alerting/log rotation | HW-05, HW-08 | Disk/health alerts, log rotation, basic metrics; no heavy stack | Phase 8 |

## 6. P3 — deferred or optional

| ID | Gap | Why deferred |
|---|---|---|
| GAP-035 | No encryption at rest for the SQLite/Postgres data | Prefer host disk encryption or Postgres volume encryption when the deployment target is known; application-level encryption adds key-management complexity. |
| GAP-036 | No vector search or embeddings | PostgreSQL FTS is untested for the research use case; add only after a retrieval evaluation. |
| GAP-037 | No OIDC/SSO, HA, multi-region, or object storage | No requirement or measured scale; would add cost and operational burden. |

## 7. Traceability — audit findings to gaps

| Finding family | Gap(s) |
|---|---|
| S-01, S-02 | GAP-007 |
| S-03 | GAP-006 |
| S-04 | GAP-005 |
| S-05 | GAP-002 |
| S-06 | GAP-001, GAP-004 |
| S-07 | GAP-013 |
| S-08, S-18 | GAP-014 |
| S-09 | GAP-011 |
| S-10 | GAP-017, GAP-018 |
| S-11 | GAP-024 |
| S-12 | GAP-006, GAP-020 |
| S-13 | GAP-012, GAP-023 |
| S-14, S-15 | GAP-032 |
| S-16 | GAP-027 |
| S-17 | No gap; control retained (parameterized SQL/ORM, regression tests in GAP-016) |
| DB-S01 | GAP-007 |
| DB-S02 | GAP-002 |
| DB-S03 | GAP-003 |
| DB-S04 | GAP-035 |
| DB-S05 | GAP-024 |
| DB-S06 | GAP-018, GAP-024 |
| DB-S07 | GAP-027 |
| DB-S08 | GAP-016 |
| INT-F01 | GAP-010 |
| INT-F02 | GAP-026 |
| INT-F03 | GAP-005 |
| INT-F04 | GAP-022 |
| INT-F05 | GAP-006 |
| INT-F06 | GAP-028 |
| INT-F07 | GAP-009 |
| INT-F08 | GAP-019, GAP-023 |
| DEP-01, DEP-02 | GAP-012 |
| DEP-03 | GAP-020 |
| DEP-04, DEP-05 | GAP-012 |
| DEP-06 | GAP-023 |
| DEP-07 | GAP-022 |
| DEP-08, DEP-09, DEP-10 | GAP-012, GAP-019 |
| API-C-01 | GAP-017 |
| API-C-02 | GAP-007 |
| API-C-03 | GAP-016, GAP-025 |
| API-C-04 | GAP-009 |
| API-C-05, C-06, C-07 | GAP-025 |
| API-C-08, C-10, C-11 | GAP-019 |
| API-C-09 | GAP-026 |
| API-C-12 | GAP-006 |
| HW-01 | GAP-021 |
| HW-02 | GAP-015 |
| HW-03 | GAP-004 |
| HW-04 | GAP-022 |
| HW-05, HW-08 | GAP-034 |
| HW-06 | GAP-021 |
| HW-07 | GAP-015 |

All security, database, integration, dependency, API, and hardware findings in the Phase 0 documents are mapped to at least one gap, except S-17 (control present) and informational items explicitly marked out of scope.

## 8. Phase 1 exit mapping

Phase 1 closes the P1 gaps and the P0 gaps that are safe to address without auth or a production deployment:

| Phase 1 task | Gaps closed or advanced |
|---|---|
| Repository/data safety | GAP-001, GAP-002, GAP-003 (decision), GAP-004 |
| Secret and voice containment | GAP-005, GAP-006 |
| Reproducible environment | GAP-012, GAP-019 (part) |
| Contracts/observability | GAP-017, GAP-018, GAP-019 |
| Middleware hardening | GAP-013, GAP-014 |
| Test isolation | GAP-008 |
| Container baseline | GAP-020 |
| Disk preflight | GAP-015 |
| Licence decision | GAP-023 |
| Voice model (if retained) | GAP-022 (deferred with voice) |

**Not closed in Phase 1:** GAP-007 (auth, Phase 3), GAP-009 (client, coordinated), GAP-010 (weather, Phase 5), GAP-016 (migrations, Phase 2), GAP-024 (retention, Phase 2/3), GAP-025/026 (feature-level), GAP-028+ (later phases).

## 9. Assumptions and limits

- Effort is indicative and assumes one developer familiar with the codebase; it excludes approvals, legal review, and waiting time.
- The host remains shared with unrelated projects; resource estimates are not guarantees.
- No gap is closed until its verification evidence exists. A merged change without the stated verification is not “done.”
- Priorities may change if the deployment target, commercial status, or data-preservation requirement changes. Those decisions are tracked in [`README.md`](README.md) §6.

---

**Status:** Gap register complete for Phase 0. No gap has been remediated, and no implementation has started.
