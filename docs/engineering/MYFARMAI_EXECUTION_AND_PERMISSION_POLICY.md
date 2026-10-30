# MyFarmAI Execution & Permission Policy

**Document Version:** 1.0  
**Status:** Implemented  
**Date:** 2026-10-25  
**Component:** MyFarmAI-Orchestrator  

---

## 1. Overview

This document defines the execution policies, permission tiers, resource budgets, and safety guardrails for the MyFarmAI Orchestrator. All orchestration activities must comply with these policies.

---

## 2. Permission Tier System

### 2.1 Tier Definitions

| Tier | Name | Description | Approval Required | Examples |
|------|------|-------------|-------------------|----------|
| **1** | TIER1_EXISTING | Existing trusted tools within granted permissions | None (auto) | All 57 agents, 26 skills, configured MCPs, installed CLIs |
| **2** | TIER2_REVERSIBLE | Reversible, low-risk additions from allowlist | Auto if allowlisted + within resource limits | ruff, mypy, pytest, gitleaks, trivy, hadolint, prettier |
| **3** | TIER3_NEW | New capabilities, security-sensitive changes | Explicit user approval | New agents, new skills, new MCPs, auth changes, deployment config |
| **4** | TIER4_DESTRUCTIVE | Destructive, irreversible, high-impact operations | Explicit authorization + safeguards + rollback plan | DB migrations, secret rotation, production deploy, volume deletion |

### 2.2 Tier Enforcement Matrix

| Action | Tier | Check | Enforcement |
|--------|------|-------|-------------|
| Use existing agent | 1 | Agent in opencode.json, VERIFIED_WORKING | Automatic |
| Use existing skill | 1 | Skill in .opencode/skills/, VERIFIED_WORKING | Automatic |
| Use configured MCP | 1 | MCP in opencode.json, not disabled | Automatic |
| Run installed CLI | 1 | Tool in PATH, VERIFIED_WORKING | Automatic |
| Install allowlisted tool | 2 | Tool in allowlist, resource budget OK | Automatic |
| Create new agent | 3 | Explicit approval, valid use case | Manual gate |
| Create new skill | 3 | Explicit approval, real gap | Manual gate |
| Add MCP server | 3 | Explicit approval, auth configured | Manual gate |
| Modify auth system | 3 | Security review passed | Manual gate |
| Change deployment | 3 | Security review, staging test | Manual gate |
| Run DB migration | 4 | Authorization, backup verified, rollback plan | Manual gate |
| Rotate secrets | 4 | Authorization, rollback plan, audit log | Manual gate |
| Deploy to production | 4 | Authorization, all gates passed, rollback | Manual gate |
| Delete volumes/data | 4 | Authorization, impact explained, confirmation | Manual gate |

### 2.3 Approval Workflow

```
Tier 3 Request:
1. Orchestrator identifies Tier 3 need
2. Presents: capability needed, why, alternatives considered, resource impact
3. User reviews and approves/rejects
4. If approved: capability added, registry updated, audit logged
5. If rejected: task blocked, alternative suggested

Tier 4 Request:
1. Orchestrator identifies Tier 4 need
2. Presents: operation, exact impact, data affected, rollback plan, safeguards
3. User reviews, confirms understanding, explicitly authorizes
4. If authorized: operation executed with monitoring, audit logged
5. If rejected: operation blocked, reason recorded
```

---

## 3. Resource Budgets

Based on Phase 0 hardware assessment (7 GiB RAM, 2 GiB VRAM, 5.3 GiB free on `/`, 176 GiB on `/data`):

### 3.1 Concurrency Limits

| Resource | Limit | Rationale |
|----------|-------|-----------|
| Max parallel agents | 4 | CPU cores, context switching overhead |
| Max concurrent model inferences | 1 | 2 GiB VRAM (4B model needs ~2.5GB) |
| Max concurrent Docker builds | 1 | Disk I/O bottleneck on `/` (5.3 GB free) |
| Max concurrent test runs | 2 | RAM pressure (pytest + vitest + playwright) |
| Max concurrent file operations | 8 | File descriptor limits |

### 3.2 Memory Budgets

| Component | Budget | Monitoring |
|-----------|--------|------------|
| Orchestrator core | 50 MB | Process RSS |
| Agent subprocesses | 500 MB each | cgroup limits |
| Model inference | 3 GB VRAM + 2 GB RAM | nvidia-smi, /proc/meminfo |
| Docker build | 2 GB RAM | docker stats |
| Test runners | 1 GB each | Process RSS |
| **Total reserved** | **~6 GB RAM** | **Leaves 1 GB buffer** |

### 3.3 Disk Budgets

| Location | Budget | Purpose |
|----------|--------|---------|
| `/` (SSD) | 1 GB | OS, Docker daemon, temp builds |
| `/data` (HDD) | 50 GB | Project artifacts, models, caches, backups |
| `.orchestrator/` | 2 GB | Checkpoints, memory, logs, cache |

### 3.4 Resource Acquisition Protocol

```python
# Before task execution
async def acquire_resources(task: Task) -> bool:
    budget = config.resource_budget
    
    # Agent slot
    if len(active_agents) >= budget.max_parallel_agents:
        return False
    
    # Model slot
    if needs_model(task) and active_models >= budget.max_concurrent_models:
        return False
    
    # Docker slot
    if needs_docker(task) and active_docker_builds >= budget.max_concurrent_docker_builds:
        return False
    
    # Test slot
    if needs_test(task) and active_test_runs >= budget.max_concurrent_test_runs:
        return False
    
    # Acquire slots
    active_agents.add(task.assigned_agent)
    if needs_model(task): active_models += 1
    if needs_docker(task): active_docker_builds += 1
    if needs_test(task): active_test_runs += 1
    
    return True

# After task completion
def release_resources(task: Task):
    active_agents.discard(task.assigned_agent)
    if needs_model(task): active_models = max(0, active_models - 1)
    if needs_docker(task): active_docker_builds = max(0, active_docker_builds - 1)
    if needs_test(task): active_test_runs = max(0, active_test_runs - 1)
```

---

## 4. Execution Policies

### 4.1 Task Lifecycle

```
PLANNED → READY → RUNNING → [BLOCKED] → REVIEW → PASSED/FAILED
                    ↓
              [RETRY] → READY (max 3 retries, exponential backoff)
                    ↓
              [CANCELLED] → Terminal
```

### 4.2 State Transitions

| From | To | Condition | Action |
|------|-----|-----------|--------|
| PLANNED | READY | All deps PASSED, resources available | Auto |
| READY | RUNNING | Agent assigned, worktree created | Auto |
| RUNNING | BLOCKED | Blocker reported (dep, resource, perm) | Auto |
| BLOCKED | READY | Blocker resolved, re-verified | Auto |
| RUNNING | REVIEW | Agent reports completion | Auto |
| REVIEW | PASSED | Verification gate PASSED, integration clean | Auto |
| REVIEW | FAILED | Verification gate FAILED or integration conflict | Auto |
| REVIEW | BLOCKED | Security gate requires review | Auto |
| FAILED | READY | Retry < max_retries, backoff complete | Auto |
| FAILED | CANCELLED | Max retries exceeded or manual cancel | Auto |
| * | CANCELLED | Manual cancellation | Manual |

### 4.3 Retry Policy

| Parameter | Value |
|-----------|-------|
| Max retries | 3 |
| Base delay | 2 seconds |
| Max delay | 60 seconds |
| Backoff | Exponential (2^retry) + jitter (0-1s) |
| Retryable errors | Network timeout, resource contention, flaky test |
| Non-retryable | Compilation error, test logic error, security violation |

### 4.4 Checkpoint & Resume

- **Checkpoint frequency:** After each phase (PREPARING, DELEGATING, EXECUTING, VERIFYING, INTEGRATING)
- **Storage:** `.orchestrator/checkpoints/<task-id>.json`
- **Resume capability:** Full state restoration including agent assignment, worktree, outputs
- **Cleanup:** Checkpoints deleted on PASSED, retained on FAILED/BLOCKED for debugging

### 4.5 File Ownership & Conflict Prevention

- Each file tracked in `FileOwnershipTracker`
- Task claims ownership before RUNNING
- Conflicts detected: same file, multiple RUNNING tasks
- Resolution: Block later task, suggest dependency or merge
- Release: Ownership released on PASSED/FAILED/CANCELLED

---

## 5. Verification & Quality Gates

### 5.1 Mandatory Quality Gates (All Code Changes)

| Gate | Checks | Required | Evidence |
|------|--------|----------|----------|
| Backend | pytest, mypy, ruff check, ruff format | Yes | Exit codes, stdout |
| Frontend | typecheck, test, lint, build | Yes | Exit codes, stdout |
| Android | typecheck, lint | Yes | Exit codes, stdout |
| Security | gitleaks, pip-audit, npm audit | Yes | Exit codes, stdout |
| Contract | OpenAPI diff | Yes | Diff output |
| Build | docker compose config, hadolint | Yes | Exit codes |
| Dependency | uv lock --check | Yes | Exit codes |

### 5.2 Security Gate (Security-Sensitive Changes)

**Triggers:** auth, secret, password, token, credential, security, vulnerability, encryption, tls, permission, authorization, rbac, oauth

**Process:**
1. Task status → REVIEW
2. Security-engineer agent reviews:
   - Code changes (diff)
   - Threat model impact
   - Secret handling
   - Permission boundaries
3. Decision: Approve → continue; Reject → FAILED with notes
4. All reviews logged in project memory

### 5.3 Evidence Requirements

**Every verification MUST capture:**
- Command executed (full command line)
- Working directory
- Exit code (actual, not simulated)
- Stdout (truncated to 5000 chars)
- Stderr (truncated to 5000 chars)
- Duration (wall-clock ms)
- Timestamp (ISO 8601)
- Environment variables (sanitized)

**Storage:** `.orchestrator/verification/<task-id>-<gate>.json`

---

## 6. Safety Guardrails

### 6.1 Destructive Command Prevention

The following require Tier 4 authorization with explicit confirmation:

| Command | Impact | Confirmation Required |
|---------|--------|----------------------|
| `docker system prune -a` | All images, containers, volumes, networks | Yes, with `--force` flag |
| `docker volume rm` | Persistent data loss | Yes, per volume |
| `docker network rm` | Network connectivity loss | Yes |
| `rm -rf` on project dirs | Source code loss | Yes, with path verification |
| `git reset --hard` | Uncommitted changes lost | Yes, with branch verification |
| `alembic downgrade` | Schema rollback, data risk | Yes, with backup verification |
| `kubectl delete` | Production resources | Yes, with namespace verification |

### 6.2 Secret Protection

- **Never** log secrets, tokens, passwords, API keys
- **Never** commit secrets to Git (pre-commit hook: gitleaks)
- **Never** include secrets in verification evidence
- **Always** use environment variables or secret managers
- **Rotate** compromised secrets immediately (Tier 4)

### 6.3 Data Protection

- **Never** delete/modify databases without Tier 4 authorization
- **Never** migrate production data without backup verification
- **Always** use disposable test databases for testing
- **Always** verify backup/restore before relying on backup

### 6.4 Network Safety

- **Never** expose services on 0.0.0.0 without authentication (Phase 0 gate)
- **Always** bind dev services to 127.0.0.1
- **Validate** all outbound URLs (SSRF protection)
- **Use** internal Docker networks for service communication

---

## 7. Audit & Compliance

### 7.1 Required Audit Trail

Every orchestration run logs:

| Event | Logged Data |
|-------|-------------|
| Run start | Run ID, timestamp, objective, tasks |
| Task start | Task ID, agent, phase, resources |
| Delegation | Handoff protocol, agent, skill |
| Verification | Gate, checks, results, evidence refs |
| Integration | Conflicts, resolutions, review queue |
| Task complete | Status, duration, findings, evidence |
| Run complete | Summary, success/fail, artifacts |

### 7.2 Compliance Checks

| Check | Frequency | Tool |
|-------|-----------|------|
| Secret scan | Every run | gitleaks |
| Dependency audit | Every run | pip-audit, npm audit |
| License compliance | On dependency change | dependency-audit skill |
| Security review | On security-sensitive task | security-engineer |
| Backup verification | Weekly | ProjectMemory audit |

---

## 8. Incident Response

### 8.1 Failure Categories

| Category | Response | Escalation |
|----------|----------|------------|
| Task FAILED (code error) | Auto-retry (3x), then block | Manual debug |
| Task BLOCKED (resource) | Wait for resource, auto-resume | Manual if >30min |
| Task BLOCKED (conflict) | Integration review, manual resolve | Architect review |
| Security REVIEW | Security-engineer review | Manual approval |
| Verification FAILED | Evidence preserved, task blocked | Manual fix |
| System ERROR | Checkpoint preserved, run stopped | Manual recovery |

### 8.2 Recovery Procedures

1. **Checkpoint Recovery:** Load `.orchestrator/checkpoints/<task-id>.json`, resume from phase
2. **Worktree Recovery:** `git worktree list`, merge or remove orphaned worktrees
3. **Resource Recovery:** `active_agents`, `active_models` counters reset on startup
4. **State Recovery:** ProjectMemory loads from JSON/JSONL, task graph reconstructed

---

## 9. Cross-Reference

| Document | Purpose |
|----------|---------|
| MYFARMAI_ORCHESTRATOR_ARCHITECTURE.md | Overall architecture |
| MYFARMAI_AGENT_TEAM_CATALOG.md | Agent permissions |
| MYFARMAI_CAPABILITY_REGISTRY.md | Capability tiers |
| MYFARMAI_SKILL_TOOL_ROUTING.md | Routing rules with tiers |
| backend/app/orchestrator/execution.py | Execution implementation |
| backend/app/orchestrator/verification.py | Verification implementation |
| backend/app/orchestrator/integration.py | Integration implementation |