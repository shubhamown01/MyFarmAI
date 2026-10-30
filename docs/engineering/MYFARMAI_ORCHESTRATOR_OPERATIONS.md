# MyFarmAI Orchestrator Operations Guide

**Document Version:** 1.0  
**Status:** Implemented  
**Date:** 2026-10-25  
**Component:** MyFarmAI-Orchestrator  

---

## 1. Overview

This guide covers day-to-day operations, maintenance procedures, troubleshooting, and recovery for the MyFarmAI Orchestrator.

---

## 2. Quick Start

### 2.1 Prerequisites
- OpenCode installed and configured
- MyFarmAI repository at `/data/MyFarmAI`
- Python 3.12+ with `uv` package manager
- Docker and Docker Compose
- Ollama running (for AI model tasks)

### 2.2 Initialize Orchestrator
```bash
cd /data/MyFarmAI

# Full capability scan (first run or after changes)
opencode skill myfarmai-capability-scan --full --export .orchestrator/registry.json

# Verify registry
opencode skill myfarmai-capability-scan --summary

# Quick verification
opencode skill myfarmai-verify --gate quality --project backend
```

### 2.3 Run an Orchestration
```bash
# Plan and execute a task
opencode skill myfarmai-orchestrate \
  --objective "Add user authentication to backend API" \
  --phase "P3" \
  --constraints "security,auth,fastapi,postgresql" \
  --priority high

# Dry run (plan only)
opencode skill myfarmai-orchestrate \
  --objective "Optimize database queries" \
  --dry-run --output plan.json

# Resume from checkpoint
opencode skill myfarmai-orchestrate --resume --run-id "run-20261025-123456-abc123"
```

---

## 3. Common Operations

### 3.1 Capability Management

#### Full Capability Scan
```bash
# Force refresh all sources
opencode skill myfarmai-capability-scan --full

# Export for documentation
opencode skill myfarmai-capability-scan --export docs/engineering/capability-registry-$(date +%Y%m%d).json
```

#### Quick Status Check
```bash
# Summary table
opencode skill myfarmai-capability-scan --summary

# Only usable capabilities
opencode skill myfarmai-capability-scan --list --usable

# By type
opencode skill myfarmai-capability-scan --list --type agent
opencode skill myfarmai-capability-scan --list --type skill
```

#### Validate Specific Capabilities
```bash
# Validate agents before critical task
opencode skill myfarmai-capability-scan --validate "backend-engineer,security-engineer,qa-reviewer"

# Re-validate previously failed
opencode skill myfarmai-capability-scan --validate --failed
```

#### Manage Tier 2 Allowlist
```bash
# List allowlist
opencode skill myfarmai-capability-scan --allowlist --list

# Add tool (e.g., new linter)
opencode skill myfarmai-capability-scan --allowlist --add "eslint-plugin-security"

# Check if allowlisted
opencode skill myfarmai-capability-scan --allowlist --check "gitleaks"
```

### 3.2 Task Decomposition

#### Decompose Objective
```bash
# Full decomposition
opencode skill myfarmai-task-decompose \
  --objective "Implement farm management CRUD API" \
  --phase "P5" \
  --constraints "postgresql,fastapi,auth-required" \
  --output tasks-phase5.json

# Analyze only
opencode skill myfarmai-task-decompose \
  --objective "Add caching layer" \
  --analyze --detail
```

#### Validate Decomposition
```bash
opencode skill myfarmai-task-decompose --validate --input tasks-phase5.json --strict
```

### 3.3 Verification Gates

#### Run Full Verification
```bash
# For a specific task
opencode skill myfarmai-verify \
  --task-id "MF-P1-007" \
  --gate all \
  --output verification-MF-P1-007.json

# CI mode (no cache, exit code)
opencode skill myfarmai-verify --gate all --no-cache
# Exit code: 0=pass, 1=fail, 2=security review required
```

#### Run Specific Gates
```bash
# Quality only (backend)
opencode skill myfarmai-verify --gate quality --project backend

# Security review required
opencode skill myfarmai-verify \
  --task-id "MF-P3-001" \
  --gate quality,security \
  --security-review
```

#### View History
```bash
# All verifications for a task
opencode skill myfarmai-verify --history --task-id "MF-P1-007"

# Failed only
opencode skill myfarmai-verify --history --failed

# Since date
opencode skill myfarmai-verify --history --since "2026-10-20"
```

### 3.4 Orchestration Monitoring

#### Check Status
```bash
# Current run status
opencode skill myfarmai-orchestrate --status

# Detailed status
opencode skill myfarmai-orchestrate --status --detail --run-id "run-20261025-123456-abc123"
```

#### View Checkpoints
```bash
# List all checkpoints
opencode skill myfarmai-orchestrate --checkpoint --list

# Clean old checkpoints
opencode skill myfarmai-orchestrate --checkpoint --clean
```

#### View Audit Report
```bash
# Generate audit report
opencode skill myfarmai-orchestrate --audit --output audit-report-$(date +%Y%m%d).md
```

---

## 4. Maintenance Procedures

### 4.1 Daily Maintenance

```bash
#!/bin/bash
# daily-maintenance.sh

cd /data/MyFarmAI

echo "=== Daily Orchestrator Maintenance ==="

# 1. Capability scan (quick, uses cache)
echo "1. Capability scan..."
opencode skill myfarmai-capability-scan --quick --summary > .orchestrator/logs/daily-scan-$(date +%Y%m%d).log

# 2. Verify critical agents
echo "2. Validating critical agents..."
opencode skill myfarmai-capability-scan --validate "backend-engineer,frontend-engineer,android-engineer,ai-ml-engineer,research-engineer,security-engineer,qa-reviewer" >> .orchestrator/logs/daily-scan-$(date +%Y%m%d).log

# 3. Clean old checkpoints (>7 days)
echo "3. Cleaning old checkpoints..."
find .orchestrator/checkpoints -name "*.json" -mtime +7 -delete

# 4. Clean verification cache (>1 hour)
echo "4. Cleaning verification cache..."
find .orchestrator/verification/cache -name "*.json" -mmin +60 -delete

# 5. Generate audit report
echo "5. Generating audit report..."
opencode skill myfarmai-orchestrate --audit --output .orchestrator/logs/audit-$(date +%Y%m%d).md

echo "=== Maintenance Complete ==="
```

### 4.2 Weekly Maintenance

```bash
#!/bin/bash
# weekly-maintenance.sh

cd /data/MyFarmAI

echo "=== Weekly Orchestrator Maintenance ==="

# 1. Full capability scan
echo "1. Full capability scan..."
opencode skill myfarmai-capability-scan --full --export .orchestrator/registry-$(date +%Y%m%d).json

# 2. Run full quality gates on all projects
echo "2. Running quality gates..."
opencode skill myfarmai-verify --gate quality --project backend --output .orchestrator/logs/weekly-quality-backend-$(date +%Y%m%d).json
opencode skill myfarmai-verify --gate quality --project web --output .orchestrator/logs/weekly-quality-web-$(date +%Y%m%d).json
opencode skill myfarmai-verify --gate quality --project android --output .orchestrator/logs/weekly-quality-android-$(date +%Y%m%d).json

# 3. Security audit
echo "3. Security audit..."
opencode skill myfarmai-verify --gate security --output .orchestrator/logs/weekly-security-$(date +%Y%m%d).json

# 4. Dependency audit
echo "4. Dependency audit..."
opencode skill myfarmai-verify --gate dependency --output .orchestrator/logs/weekly-dependency-$(date +%Y%m%d).json

# 5. Clean project memory (>90 days)
echo "5. Cleaning old memory..."
python -c "
from backend.app.orchestrator import ProjectMemoryManager, OrchestrationConfig
config = OrchestrationConfig()
mgr = ProjectMemoryManager(config)
result = mgr.cleanup_old_data(days=90)
print(f'Removed: {result}')
"

# 6. Update documentation from registry
echo "6. Updating capability registry docs..."
opencode skill myfarmai-capability-scan --export docs/engineering/capability-registry-$(date +%Y%m%d).json

echo "=== Weekly Maintenance Complete ==="
```

### 4.3 Monthly Maintenance

- Review and update routing rules based on new patterns
- Audit Tier 2 allowlist for unused entries
- Review agent performance metrics
- Update capability registry documentation
- Test disaster recovery (backup/restore)

---

## 5. Troubleshooting

### 5.1 Common Issues

#### Issue: Agent Not Found / Not Loading
```bash
# Check agent file exists
ls -la .opencode/agents/backend-engineer.md

# Validate agent syntax
opencode agent info backend-engineer

# Check opencode.json for permission
grep -A 20 "myfarmai-orchestrator" opencode.json
```

#### Issue: Capability Scan Returns BROKEN
```bash
# Check specific capability
opencode skill myfarmai-capability-scan --validate "backend-engineer"

# Common causes:
# - Missing dependency (pip install, npm install)
# - MCP server not running
# - Ollama not running
# - Path issues
```

#### Task Stuck in BLOCKED
```bash
# Check task details
python -c "
from backend.app.orchestrator import OrchestratorCore, OrchestrationConfig, CapabilityRegistry, ProjectMemory
config = OrchestrationConfig()
memory = ProjectMemory()
registry = CapabilityRegistry(config, memory)
core = OrchestratorCore(config, registry, memory)
task = core.get_task('MF-P1-005')
print(f'Status: {task.status}')
print(f'Blockers: {task.blockers}')
print(f'Dependencies: {task.dependencies}')
"
```

#### Verification Gate Fails
```bash
# Run specific check manually
cd /data/MyFarmAI/backend
uv run pytest -q
uv run mypy .
uv run ruff check .

cd /data/MyFarmAI/web
npm run typecheck
npm test
npm run lint
npm run build
```

#### Worktree Merge Conflicts
```bash
# List worktrees
git worktree list

# Manual merge
git checkout main
git merge task/MF-P1-005

# Or abandon worktree
git worktree remove .orchestrator/worktrees/task-MF-P1-005-1234567890 --force
```

### 5.2 Error Codes

| Error | Cause | Resolution |
|-------|-------|------------|
| `AGENT_NOT_FOUND` | Agent not in opencode.json | Add agent definition |
| `SKILL_NOT_LOADED` | Skill not in .opencode/skills/ | Install skill |
| `RESOURCE_EXHAUSTED` | Max parallel agents reached | Wait or increase budget |
| `PERMISSION_DENIED` | Tier 3/4 action without approval | Request approval |
| `CHECKPOINT_CORRUPT` | JSON parse error | Delete checkpoint, restart task |
| `WORKTREE_CONFLICT` | Git merge conflict | Manual resolution |
| `VERIFICATION_TIMEOUT` | Check exceeded timeout | Increase timeout or fix hang |

---

## 6. Recovery Procedures

### 6.1 Orchestrator Crash Recovery

1. **Check for incomplete runs:**
   ```bash
   ls -la .orchestrator/checkpoints/
   ```

2. **Resume from latest checkpoint:**
   ```bash
   opencode skill myfarmai-orchestrate --resume --run-id <latest-run-id>
   ```

3. **If no checkpoint, reconstruct from memory:**
   ```bash
   python -c "
   from backend.app.orchestrator import ProjectMemoryManager, OrchestrationConfig
   config = OrchestrationConfig()
   mgr = ProjectMemoryManager(config)
   report = mgr.generate_audit_report()
   print(report)
   "
   ```

### 6.2 Database Corruption Recovery

**Note:** Orchestrator does not modify databases directly. Follow MyFarmAI backup procedures.

1. Verify backup exists at `/data/MyFarmAI-backups/`
2. Run backup verification drill
3. Restore from verified backup
4. Re-run capability scan

### 6.3 Secret Exposure Recovery

1. **Immediate:** Rotate exposed secret (Tier 4)
2. **Audit:** `gitleaks detect --source . --verbose`
3. **History:** Check Git history for exposure
4. **Remediate:** Remove from history if needed (BFG/clean)
5. **Document:** Record in project memory

### 6.4 Full System Recovery

```bash
#!/bin/bash
# disaster-recovery.sh

cd /data/MyFarmAI

echo "=== Disaster Recovery ==="

# 1. Verify Git state
git status
git log --oneline -5

# 2. Restore from backup if needed
# rsync -av /data/MyFarmAI-backups/latest/ /data/MyFarmAI/

# 3. Verify critical files
for f in opencode.json backend/pyproject.toml web/package.json android/package.json; do
    if [ -f "$f" ]; then echo "OK: $f"; else echo "MISSING: $f"; fi
done

# 4. Rebuild capability registry
opencode skill myfarmai-capability-scan --full

# 5. Run smoke tests
opencode skill myfarmai-verify --gate quality --project backend

echo "=== Recovery Complete ==="
```

---

## 7. Monitoring & Alerting

### 7.1 Key Metrics to Monitor

| Metric | Normal Range | Alert Threshold |
|--------|--------------|-----------------|
| Active orchestration runs | 0-2 | >3 |
| Task failure rate | <10% | >25% |
| Average task duration | <5 min | >30 min |
| Capability registry freshness | <1 hour | >4 hours |
| Verification gate pass rate | >95% | <80% |
| Security review queue | 0-2 | >5 |
| Disk usage (.orchestrator) | <1 GB | >2 GB |
| Memory usage | <6 GB | >6.5 GB |

### 7.2 Log Locations

| Log Type | Location |
|----------|----------|
| Orchestration runs | `.orchestrator/logs/run-*.log` |
| Capability scans | `.orchestrator/logs/daily-scan-*.log` |
| Verification gates | `.orchestrator/verification/*.json` |
| Checkpoints | `.orchestrator/checkpoints/*.json` |
| Project memory | `.orchestrator/memory/` |
| Audit reports | `.orchestrator/logs/audit-*.md` |

### 7.3 Health Check Script

```bash
#!/bin/bash
# health-check.sh

cd /data/MyFarmAI

echo "=== Orchestrator Health Check ==="

# 1. OpenCode
if opencode --version >/dev/null 2>&1; then
    echo "OK: OpenCode"
else
    echo "FAILED: OpenCode"
fi

# 2. Critical agents
for agent in backend-engineer frontend-engineer qa-reviewer security-engineer; do
    if opencode agent info "$agent" >/dev/null 2>&1; then
        echo "OK: Agent $agent"
    else
        echo "FAILED: Agent $agent"
    fi
done

# 3. Capability registry
if [ -f .orchestrator/cache/capabilities.json ]; then
    age=$(( ($(date +%s) - $(stat -c %Y .orchestrator/cache/capabilities.json)) / 60 ))
    if [ $age -lt 60 ]; then
        echo "OK: Registry cache: Fresh ($age min)"
    else
        echo "WARNING: Registry cache: Stale ($age min)"
    fi
else
    echo "FAILED: Registry cache: Missing"
fi

# 4. Disk space
disk_free=$(df -h /data/MyFarmAI | awk 'NR==2 {print $4}')
echo "OK: Disk free: $disk_free"

# 5. Memory
mem_free=$(free -h | awk 'NR==2 {print $7}')
echo "OK: Memory free: $mem_free"

echo "=== Health Check Complete ==="
```

---

## 8. Configuration Reference

### 8.1 OrchestrationConfig (Python)

```python
OrchestrationConfig(
    project_root="/data/MyFarmAI",
    backend_path="/data/MyFarmAI/backend",
    web_path="/data/MyFarmAI/web",
    android_path="/data/MyFarmAI/android",
    docs_path="/data/MyFarmAI/docs",
    graphify_path="/data/MyFarmAI/graphify-out",
    backup_path="/data/MyFarmAI-backups",
    resource_budget=ResourceBudget(
        max_parallel_agents=4,
        max_concurrent_models=1,
        max_concurrent_docker_builds=1,
        max_concurrent_test_runs=2,
        max_ram_gb=6.0,
        max_vram_gb=1.5,
        max_disk_gb=4.0
    ),
    enable_parallel=True,
    default_max_retries=3,
    verification_timeout_seconds=300,
    session_persistence=True
)
```

### 8.2 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ORCHESTRATOR_PROJECT_ROOT` | `/data/MyFarmAI` | Project root |
| `ORCHESTRATOR_MAX_PARALLEL` | `4` | Max parallel agents |
| `ORCHESTRATOR_VERIFY_TIMEOUT` | `300` | Verification timeout (s) |
| `ORCHESTRATOR_CHECKPOINT_DIR` | `.orchestrator/checkpoints` | Checkpoint directory |
| `ORCHESTRATOR_MEMORY_DIR` | `.orchestrator/memory` | Memory directory |

---

## 9. Upgrade & Migration

### 9.1 Upgrading Orchestrator Components

1. **Pull latest code:**
   ```bash
   git pull origin main
   ```

2. **Update Python dependencies:**
   ```bash
   cd /data/MyFarmAI/backend
   uv sync --frozen
   ```

3. **Update npm dependencies:**
   ```bash
   cd /data/MyFarmAI/web && npm install
   cd /data/MyFarmAI/android && npm install
   ```

4. **Re-run capability scan:**
   ```bash
   opencode skill myfarmai-capability-scan --full
   ```

5. **Run validation suite:**
   ```bash
   # Follow MYFARMAI_ORCHESTRATOR_TEST_REPORT.md
   ```

### 9.2 Migration Checklist

- [ ] Backup `.orchestrator/memory/` and `.orchestrator/checkpoints/`
- [ ] Verify all agents/skills still load
- [ ] Run capability scan
- [ ] Run verification gates
- [ ] Update documentation if APIs changed
- [ ] Test with real task

---

## 10. Support & Escalation

### 10.1 Self-Service Resources

| Resource | Location |
|----------|----------|
| Architecture | `docs/engineering/MYFARMAI_ORCHESTRATOR_ARCHITECTURE.md` |
| Agent Catalog | `docs/engineering/MYFARMAI_AGENT_TEAM_CATALOG.md` |
| Capability Registry | `docs/engineering/MYFARMAI_CAPABILITY_REGISTRY.md` |
| Routing Rules | `docs/engineering/MYFARMAI_SKILL_TOOL_ROUTING.md` |
| Permission Policy | `docs/engineering/MYFARMAI_EXECUTION_AND_PERMISSION_POLICY.md` |
| Test Report | `docs/engineering/MYFARMAI_ORCHESTRATOR_TEST_REPORT.md` |

### 10.2 Escalation Path

| Level | Contact | When |
|-------|---------|------|
| L1 - Self Service | Documentation, logs | Routine issues |
| L2 - Orchestrator | MyFarmAI-Orchestrator agent | Complex orchestration |
| L3 - Specialist | Relevant agent (security-engineer, etc.) | Domain-specific |
| L4 - Owner | Project owner | Policy, authorization, architecture |

### 10.3 Emergency Contacts

- **Security Incident:** security-engineer agent + immediate owner notification
- **Data Loss:** Database admin + owner + backup verification
- **Production Outage:** Deployment engineer + SRE + owner

---

## 11. Appendix: Command Reference

### Orchestrator Commands
```bash
# Main orchestration
opencode skill myfarmai-orchestrate [--objective] [--phase] [--constraints] [--priority] [--dry-run] [--resume] [--run-id] [--status] [--checkpoint] [--audit]

# Capability scan
opencode skill myfarmai-capability-scan [--full] [--quick] [--types] [--validate] [--export] [--summary] [--conflicts] [--list] [--allowlist]

# Task decomposition
opencode skill myfarmai-task-decompose [--objective] [--phase] [--constraints] [--max-tasks] [--output] [--format] [--analyze] [--validate]

# Verification
opencode skill myfarmai-verify [--task-id] [--gate] [--custom-checks] [--security-review] [--no-cache] [--output] [--history] [--failed] [--since]
```

### Direct Python API
```python
from backend.app.orchestrator import (
    OrchestratorCore, CapabilityRegistry, DynamicTeamBuilder,
    SkillToolRouter, ExecutionManager, IntegrationReviewManager,
    VerificationSecurityGate, ProjectMemoryManager, OrchestrationConfig
)

config = OrchestrationConfig()
memory = ProjectMemoryManager(config)
registry = CapabilityRegistry(config, memory.memory)
await registry.discover_all()

core = OrchestratorCore(config, registry, memory.memory, ...)
# Add tasks, run, monitor
```

---

## 12. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-10-25 | Initial implementation |
