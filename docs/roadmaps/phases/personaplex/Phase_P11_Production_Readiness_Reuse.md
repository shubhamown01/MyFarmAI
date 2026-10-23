# Phase P11 — Production Readiness & Future-Project Reuse

**Status:** ⏳ READY (awaits P10 complete)  
**Prerequisite:** P10 complete (benchmarks, reliability, monitoring)  
**Blocks:** None (final phase)

---

## 1. Objective

Deliver a production-ready, reusable PersonaPlex voice service that:
- Can be deployed and operated by MyFarmAI, ATHENA, and future projects
- Has documented deployment, upgrade, rollback, and backup procedures
- Enables safe multi-project sharing without data leakage
- Meets all security, compliance, and reliability gates

---

## 2. Deployment Package

### P11-01: Deployment Artifacts

```
personaplex-voice-service/
├── docker-compose.yml           # Production compose
├── docker-compose.dev.yml       # Development override
├── Dockerfile                   # Multi-stage build
├── config/
│   ├── config.yaml              # Service config
│   ├── voices.yaml              # Voice definitions
│   └── prompts.yaml             # System prompts
├── k8s/                         # Kubernetes manifests (optional)
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   └── configmap.yaml
├── scripts/
│   ├── deploy.sh                # Deploy script
│   ├── backup.sh                # Model/config backup
│   ├── restore.sh               # Restore from backup
│   ├── upgrade.sh               # Rolling upgrade
│   ├── rollback.sh              # Rollback to previous
│   └── healthcheck.sh           # Manual health check
├── monitoring/
│   ├── prometheus-rules.yaml    # Alert rules
│   ├── grafana-dashboard.json   # Dashboard
│   └── loki-config.yaml         # Log aggregation
├── docs/
│   ├── DEPLOYMENT.md            # Deployment guide
│   ├── OPERATIONS.md            # Operations runbook
│   ├── UPGRADE.md               # Upgrade procedure
│   ├── ROLLBACK.md              # Rollback procedure
│   ├── BACKUP_RESTORE.md        # Backup/restore guide
│   ├── SECURITY.md              # Security hardening
│   └── TROUBLESHOOTING.md       # Common issues
├── tests/
│   ├── integration/             # Integration tests
│   ├── contract/                # API contract tests
│   ├── security/                # Security tests
│   └── performance/             # Benchmark scripts
├── .env.example                 # Environment template
├── .gitignore
├── README.md
├── LICENSE
├── NOTICE
├── THIRD_PARTY_LICENSES.md
└── MODEL_CHECKSUMS.md
```

---

## 2. Deployment Procedures

### P11-01: Fresh Deployment
```bash
#!/usr/bin/env bash
# deploy.sh
set -euo pipefail

# 1. Validate prerequisites
./scripts/validate_prereqs.sh

# 2. Pull model (if not present)
./scripts/pull_model.sh

# 3. Generate secrets
./scripts/generate_secrets.sh

# 4. Deploy
docker compose -f docker-compose.yml up -d

# 4. Wait for readiness
./scripts/wait_for_ready.sh

# 5. Run smoke tests
./scripts/smoke_test.sh

echo "Deployment complete. Service at https://voice.myfarmai.local"
```

### P11-02: Rolling Upgrade
```bash
#!/usr/bin/env bash
# upgrade.sh
set -euo pipefail

NEW_VERSION="${1:?Version required}"
CURRENT_VERSION=$(cat VERSION)

echo "Upgrading from $CURRENT_VERSION to $NEW_VERSION"

# 1. Backup current state
./scripts/backup.sh

# 2. Pull new image
docker compose pull

# 3. Rolling update (zero-downtime if possible)
docker compose up -d --no-deps --scale voice=2 voice

# 3. Wait for new pods ready
./scripts/wait_for_ready.sh --replicas 2

# 4. Drain old replicas
docker compose up -d --scale voice=1 voice

# 5. Verify
./scripts/smoke_test.sh

# 6. Update VERSION file
echo "$NEW_VERSION" > VERSION

echo "Upgrade complete"
```

### P11-03: Rollback
```bash
#!/usr/bin/env bash
# rollback.sh
set -euo pipefail

PREVIOUS_VERSION=$(cat PREVIOUS_VERSION)

echo "Rolling back to $PREVIOUS_VERSION"

# 1. Restore backup
./scripts/restore.sh

# 2. Deploy previous version
docker compose up -d --force-recreate

# 2. Wait and verify
./scripts/wait_for_ready.sh
./scripts/smoke_test.sh

echo "Rollback complete"
```

---

## 2. Multi-Project Reuse Model

### Shared Service Model
```
┌─────────────────────────────────────────────────────────────────┐
│                    Shared PersonaPlex Service                    │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Single Deployment (GPU Server / Cluster)                  │  │
│  │  • Shared model weights (/data/AI-Models/personaplex-7b-v1)│  │
│  │  • Single GPU resource pool                                │  │
│  │  • Shared monitoring, logging, backup                      │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
│         ┌────────────────────┼────────────────────┐             │
│         ▼                    ▼                    ▼             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐        │
│  │  MyFarmAI   │    │   ATHENA    │    │  Project C  │        │
│  │  (Project)  │    │  (Project)  │    │  (Future)   │        │
│  │             │    │             │    │             │        │
│  │ • Own auth  │    │ • Own auth  │    │ • Own auth  │        │
│  │ • Own data  │    │ • Own data  │    │ • Own data  │        │
│  │ • Own prompts│   │ • Own prompts│   │ • Own prompts│       │
│  │ • Own sessions│  │ • Own sessions│  │ • Own sessions│       │
│  └─────────────┘    └─────────────┘    └─────────────┘        │
└─────────────────────────────────────────────────────────────────┘
```

### Project Isolation
| Isolation Layer | Mechanism |
|-----------------|-----------|
| Authentication | Per-project JWT/OAuth; tokens scoped to project |
| Authorization | Per-project RBAC; `voice:create` per project |
| Sessions | Session tokens include `project_id`; validated on each request |
| Data | Per-project DB schema or row-level security |
| Prompts | Per-project system prompts stored in project config |
| Voice profiles | Per-project voice configurations |
| Audit logs | Tagged with `project_id`; isolated queries |
| Rate limits | Per-project quotas |

### Configuration per Project
```yaml
# project-configs/myfarmai.yaml
project_id: "myfarmai"
display_name: "MyFarmAI"
voice:
  enabled: true
  default_voice: "indian_female"
  default_language: "hi"
  default_prompt: "You are an agricultural assistant for Indian farmers..."
  max_concurrent_sessions: 2
  session_timeout_minutes: 30
  allowed_voices: ["indian_female", "indian_male"]
rate_limits:
  sessions_per_hour: 20
  requests_per_minute: 30
```

---

## 3. Operational Procedures

### P11-04: Backup & Restore
```bash
# backup.sh
#!/usr/bin/env bash
# Backs up: model weights, config, secrets, DB (if any)
# Stores to /data/backups/personaplex/YYYYMMDD_HHMMSS/

# restore.sh
#!/usr/bin/env bash
# Restores from timestamped backup
# Validates checksums before restore
```

### P11-02: Monitoring Setup
```yaml
# monitoring/prometheus-rules.yaml
groups:
- name: personaplex
  rules:
  - alert: PersonaPlexDown
    expr: up{job="personaplex-voice"} == 0
    for: 1m
    labels: { severity: "critical" }
    annotations:
      summary: "PersonaPlex voice service down"
  - alert: PersonaPlexHighVRAM
    expr: personaplex_vram_used_gb / personaplex_vram_total_gb > 0.9
    for: 5m
    labels: { severity: "warning" }
    annotations:
      summary: "PersonaPlex VRAM usage high"
```

---

## 3. CI/CD Pipeline

```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: uv sync --frozen
      - run: uv run ruff check .
      - run: uv run mypy .
      - run: uv run pytest -q

  contract-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: uv run pytest tests/contract/ -v

  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: aquasecurity/trivy-action@master
        with: { scan-type: 'fs', severity: 'HIGH,CRITICAL' }
      - run: uv run pip-audit

  build:
    needs: [test, contract-test, security-scan]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/build-push-action@v5
        with:
          context: .
          push: false
          tags: personaplex-voice:${{ github.sha }}
```

---

## 3. Release Checklist

| Item | Required | Verified |
|------|----------|----------|
| All tests pass (unit, integration, contract, security) | ✅ | |
| Benchmarks meet targets on target hardware | ✅ | |
| Security audit passed (no HIGH/CRITICAL) | ✅ | |
| License compliance verified | ✅ | |
| Documentation complete (DEPLOYMENT, OPERATIONS, etc.) | ✅ | |
| Runbooks for top 5 failure scenarios | ✅ | |
| Backup/restore tested | ✅ | |
| Upgrade/rollback tested | ✅ | |
| Multi-project config templates exist | ✅ | |
| OpenAPI spec published | ✅ | |
| CHANGELOG updated | ✅ | |
| VERSION bumped | ✅ | |
| CHANGELOG signed off by maintainer | ✅ | |

---

## 3. Future-Project Onboarding

### New Project Onboarding Checklist
1. [ ] Request voice access (project lead approval)
2. [ ] Create project config in `project-configs/`
3. [ ] Generate project-specific JWT secret
4. [ ] Configure project-specific prompts/voices
5. [ ] Set rate limits and quotas
6. [ ] Add project to monitoring dashboards
7. [ ] Run integration tests with project credentials
7. [ ] Document project-specific voice behaviors
8. [ ] Update project registry

---

## 4. Acceptance Criteria

- [ ] Deployment package complete with all scripts/docs
- [ ] Fresh deploy succeeds on clean target
- [ ] Rolling upgrade works zero-downtime
- [ ] Rollback restores previous version < 5 min
- [ ] Backup/restore validated with checksums
- [ ] Multi-project isolation verified (no data leakage)
- [ ] Project onboarding documented and tested
- [ ] CI/CD pipeline passes all gates
- [ ] Release checklist signed off
- [ ] Operations team trained on runbooks

---

## 4. Status Tracking

| Task | Status | Verified | Notes |
|------|--------|----------|-------|
| Deployment package | NOT STARTED | ❌ | |
| Deploy/upgrade/rollback scripts | NOT STARTED | ❌ | |
| Backup/restore | NOT STARTED | ❌ | |
| Multi-project configs | NOT STARTED | ❌ | |
| Monitoring/alerts | NOT STARTED | ❌ | |
| CI/CD pipeline | NOT STARTED | ❌ | |
| Release checklist | NOT STARTED | ❌ | |
| Documentation | NOT STARTED | ❌ | |

---

## 4. Dependencies

- **Requires:** P10 complete (all gates passed)
- **Blocks:** None (final phase)

---

## 5. Final Sign-Off

| Role | Name | Signature | Date |
|------|------|-----------|------|
| AI Architect | | | |
| Backend Lead | | | |
| Security Lead | | | |
| Operations Lead | | | |
| Project Owner | | | |

**PersonaPlex 7B v1 Integration: COMPLETE** when all phases VERIFIED and sign-offs collected.