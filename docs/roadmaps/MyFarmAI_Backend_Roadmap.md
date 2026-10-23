# MyFarmAI Backend Roadmap

**Goal:** Deliver a secure, maintainable, self-hostable backend for MyFarmAI using local AI and open-source components, without mandatory paid APIs or paid SaaS dependencies.

## Target architecture

```text
Next.js Web Client       Expo / React Native Android
          \                         /
                   HTTPS / JSON
                        |
                     FastAPI
                        |
       +----------------+----------------+
       |                |                |
   API schemas     Application       Auth / Policy
       |             services             |
       +----------------+----------------+
                        |
                 Domain modules
                        |
         +--------------+---------------------+
         |              |                     |
    PostgreSQL      Ollama gateway        Integration adapters
         |              |                 /       |        \
   Alembic ORM      Local models       Weather  Search   Public data
                                     |                   |
                              SearXNG / extraction     |
                                                     Optional:
                                                    PersonaPlex Voice
                                                      (gated)
```

Optional later: Valkey + workers; Qdrant only if retrieval tests justify it.
PersonaPlex full-duplex voice is an **optional, gated capability** requiring:
- Hugging Face model approval (nvidia/personaplex-7b-v1)
- Suitable GPU hardware (Ampere/Hopper class, ≥24 GB VRAM)
- Explicit approval before any runtime work begins
```

## Phases

| Phase | Name | Main outcome |
|---|---|---|
| 0 | Read-only audit | Verified current-state evidence, risks, architecture proposal, approval decisions |
| 1 | Backend foundation | Reproducible FastAPI app, settings, health, errors, tests, CI baseline |
| 2 | Database architecture | Versioned schema, PostgreSQL readiness, tested migration and recovery plan |
| 3 | Authentication and security | User identity, sessions/tokens, authorization, privacy and abuse controls |
| 4 | Local AI | Provider-independent gateway to Ollama, bounded inference, evaluations |
| 5 | Agriculture integrations | Domain APIs and licensed, provenance-aware public data adapters |
| 6 | Research engine | Search, safe extraction, source ranking, citations, prompt-injection defenses |
| 7 | Optional jobs and search upgrades | Background processing and vector search only when measured need exists |
| 8 | Deployment hardening | Least privilege, network boundaries, TLS, backups, operations runbooks |
| 9 | CI and release readiness | Repeatable tests, security checks, release gates, recovery validation |

### PersonaPlex Voice Integration (Optional, Gated)

| Phase | Name | Main outcome | Depends On |
|---|---|---|---|
| P0 | Feasibility & Access | Model approval, license review, hardware gate | — |
| P1 | Shared Model Storage | Verified weights, checksums, provenance, lifecycle | P0 |
| P2 | Inference Runtime Prototype | Working runtime on target hardware, benchmarks | P1 |
| P3 | Hardware Deployment Strategy | Three deployment targets, cost models, migration | P2 |
| P4 | Reusable Voice Service | Production voice service with API, auth, resource limits | P3, Phase 3 |
| P5 | AI Gateway Integration | Voice routed through gateway, text fallback | P4, Phase 3 |
| P6 | Web Integration | Opt-in voice UI, consent, fallback to text | P5, Phase 7 |
| P7 | Android Integration | Audio capture/playback, permissions, networking | P5, Phase 8 |
| P8 | Agricultural Conversational Behavior | Safe ag voice responses, citations, escalation | P5, Phase 5 |
| P9 | Security, Privacy & Compliance | Consent, data minimization, spoofing, license, DPDP | P4, Phase 3 |
| P10 | Performance & Reliability | Benchmarks, reliability targets, chaos testing | P4, P8, P9 |
| P11 | Production Readiness & Reuse | Deployment package, multi-project reuse, CI/CD | P10 |

## Execution order and hard gates

- Phase 0 must be complete and reviewed before implementation.
- Phase 1 must not begin until explicit approval is recorded.
- Preserve the pre-existing uncommitted work and both SQLite databases until their roles and canonical data source are approved.
- Investigate the reported seven clean-database test failures before declaring the test baseline reliable.
- Contain the unauthenticated voice service and remediate the hardcoded SearXNG secret through an approved, recoverable change plan.
- Do not expose services publicly until authentication, authorization, TLS, host/CORS configuration, and rate limiting are reviewed.
- Do not select a commercial weather provider until its licence and terms permit the intended use.
- Test any SQLite-to-PostgreSQL migration on a disposable copy before touching canonical data.
- Defer voice, Valkey, workers, Qdrant, and additional observability unless approved and justified by measurements.

### PersonaPlex-specific gates
- **PersonaPlex P0 (Access)** must be complete (HF approval, license review, hardware gate) before any runtime work.
- **PersonaPlex P2 (Runtime)** must pass benchmarks on target hardware before service work (P4+).
- **PersonaPlex P3 (Hardware)** deployment target must be selected and approved before service deployment.
- **PersonaPlex P4 (Service)** requires Phase 3 (Auth) complete before deployment.
- **PersonaPlex P9 (Security)** must pass security/privacy review before any voice exposure.
- **PersonaPlex P10 (Reliability)** must pass benchmarks and chaos tests before production.
- **PersonaPlex voice is an optional, gated capability** — not part of core MVP; requires explicit approval at each gate.

## Technology direction (subject to audit and approval)

- FastAPI, Pydantic, Python 3.12 and `uv` with a committed lockfile.
- SQLAlchemy 2 and Alembic.
- PostgreSQL for production after compatibility and migration verification.
- SQLite for isolated tests only if that strategy is approved and the application supports it.
- Ollama behind a provider-independent AI gateway.
- **NVIDIA PersonaPlex 7B v1** for optional full-duplex voice (gated; requires Ampere/Hopper GPU).
- SearXNG for self-hosted search; PostgreSQL full-text search initially.
- Docker Compose, non-root containers, internal networks, health checks and explicit resource budgets.
- Pytest, Ruff, type checking, dependency/license checks, and security regression tests.

## Global Definition of Done

A phase is complete only when its deliverables exist, acceptance tests pass, evidence is recorded, security and licensing implications are reviewed, documentation is updated, unresolved issues are marked, and the phase exit gate is explicitly accepted.
