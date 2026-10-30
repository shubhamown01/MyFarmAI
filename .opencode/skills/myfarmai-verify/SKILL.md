# MyFarmAI Verify Skill

**Skill ID:** `myfarmai-verify`  
**Version:** 1.0.0  
**Category:** Quality Assurance  
**Description:** Runs verification gates (quality, security, contract, build, dependency checks) and enforces evidence-based completion criteria. Prevents tasks from being marked complete without verified test results.

## Overview

This skill implements the Verification & Security Gate for MyFarmAI. It runs all relevant checks and requires actual command output evidence before allowing task completion.

## Usage

```bash
# Run full verification gate for a task
opencode skill myfarmai-verify --task-id "MF-P1-001" --gate all

# Run specific gate types
opencode skill myfarmai-verify --task-id "MF-P1-001" --gate quality,security

# Run with custom checks
opencode skill myfarmai-verify --task-id "MF-P1-001" --custom-checks "custom_check.sh"

# Security review for sensitive tasks
opencode skill myfarmai-verify --task-id "MF-P1-001" --security-review

# Show verification history
opencode skill myfarmai-verify --history --task-id "MF-P1-001"
```

## Commands

### `verify`

Run verification gate.

**Options:**
- `--task-id` (required): Task ID to verify
- `--gate`: Gate types to run (quality, security, contract, build, dependency, all)
- `--custom-checks`: Path to custom check script
- `--security-review`: Require security-engineer review
- `--no-cache`: Bypass verification cache
- `--output`: Output results to file (JSON)

### `gate`

Run a specific gate type independently.

**Options:**
- `--type`: Gate type (quality, security, contract, build, dependency)
- `--project`: Project area (backend, web, android, all)
- `--output`: Output file

### `security-review`

Request security-engineer review.

**Options:**
- `--task-id` (required): Task ID requiring review
- `--reason`: Reason for security review
- `--approver`: Specific reviewer (default: security-engineer)

### `history`

Show verification history.

**Options:**
- `--task-id`: Filter by task
- `--gate`: Filter by gate type
- `--failed`: Show only failed verifications
- `--since`: Show since date (ISO format)

## Gate Definitions

### Quality Gate (Required for all code changes)
| Check | Command | Project | Required |
|-------|---------|---------|----------|
| Backend Tests | `uv run pytest -q` | backend | Yes |
| Backend Type Check | `uv run mypy .` | backend | Yes |
| Backend Lint | `uv run ruff check .` | backend | Yes |
| Backend Format | `uv run ruff format --check .` | backend | Yes |
| Frontend Type Check | `npm run typecheck` | web | Yes |
| Frontend Tests | `npm test` | web | Yes |
| Frontend Lint | `npm run lint` | web | Yes |
| Frontend Build | `npm run build` | web | Yes |
| Android Type Check | `npm run typecheck` | android | Yes |
| Android Lint | `npm run lint` | android | Yes |

### Security Gate (Required for security-sensitive changes)
| Check | Command | Project | Required |
|-------|---------|---------|----------|
| Secret Scan | `gitleaks detect --source . --verbose` | root | Yes |
| Python Dependency Audit | `uv run pip-audit` | backend | Yes |
| Web Dependency Audit | `npm audit --audit-level=high` | web | No* |
| Android Dependency Audit | `npm audit --audit-level=high` | android | No* |

*May have false positives; warnings only

### Contract Gate (Required for API changes)
| Check | Command | Project | Required |
|-------|---------|---------|----------|
| OpenAPI Diff | `diff openapi.json <(generated)` | root | Yes |

### Build Gate (Required for deployment/config changes)
| Check | Command | Project | Required |
|-------|---------|---------|----------|
| Docker Compose Config | `docker compose config` | root | Yes |
| Dockerfile Lint | `hadolint backend/Dockerfile` | backend | No* |

*If hadolint available

### Dependency Gate (Required for dependency changes)
| Check | Command | Project | Required |
|-------|---------|---------|----------|
| UV Lock Check | `uv lock --check` | backend | Yes |

## Verification Result Format

```json
{
  "task_id": "MF-P1-001",
  "gate_results": {
    "quality": {
      "passed": true,
      "checks": [
        {
          "name": "backend_tests",
          "type": "unit_test",
          "command": "uv run pytest -q",
          "exit_code": 0,
          "stdout": "56 passed in 12.34s",
          "stderr": "",
          "passed": true,
          "duration_ms": 12340
        }
      ],
      "failed_required": [],
      "duration_ms": 45670
    },
    "security": {
      "passed": true,
      "checks": [...],
      "failed_required": [],
      "duration_ms": 12340
    }
  },
  "overall_passed": true,
  "completed_at": "2026-10-25T10:30:00Z",
  "evidence_refs": [
    ".orchestrator/verification/MF-P1-001-quality.json",
    ".orchestrator/verification/MF-P1-001-security.json"
  ]
}
```

## Evidence Requirements

**Every verification MUST produce:**
1. **Exit code** - Actual process exit code
2. **Stdout** - Full command output (truncated to 5000 chars)
3. **Stderr** - Full error output (truncated to 5000 chars)
4. **Duration** - Wall-clock time in milliseconds
5. **Timestamp** - ISO 8601 completion time

**No verification passes without:**
- Actual command execution (not simulated)
- Real exit code capture
- Output preserved for audit

## Security Review Process

For tasks requiring security review:

1. **Detection**: Skill automatically detects security-sensitive patterns:
   - Authentication/authorization changes
   - Secret/credential handling
   - API endpoint exposure changes
   - Database schema permission changes
   - File upload/processing
   - Dependencies with known CVEs

2. **Blocking**: Task status → `REVIEW`, added to security review queue

3. **Review**: Security-engineer agent reviews:
   - Code changes
   - Threat model impact
   - Secret handling
   - Permission boundaries

4. **Decision**: Approve → task continues; Reject → task fails with notes

5. **Audit**: All reviews logged in project memory

## Cache Behavior

- Verification results cached for 5 minutes by default
- Cache key: `<check_name>:<command_hash>`
- Use `--no-cache` to force fresh execution
- Cache stored in `.orchestrator/verification/cache/`

## Integration

Used by:
- `myfarmai-orchestrate` - Automatic gate execution after task completion
- `ExecutionManager` (backend/app/orchestrator/execution.py) - Phase 4 verification
- `VerificationSecurityGate` (backend/app/orchestrator/verification.py) - Internal engine
- `security-engineer` agent - For security reviews

## Examples

### Example 1: Standard Verification
```bash
opencode skill myfarmai-verify --task-id "MF-P1-007" --gate all --output verification-MF-P1-007.json
```

### Example 2: Security Review Required
```bash
opencode skill myfarmai-verify --task-id "MF-P3-001" --gate quality,security --security-review
```

### Example 3: Quick Quality Check
```bash
opencode skill myfarmai-verify --gate quality --project backend
```

### Example 4: CI Integration
```bash
# In CI pipeline
opencode skill myfarmai-verify --gate all --no-cache --output ci-verification.json
# Exit code 0 if all passed, 1 if any required check failed
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All required checks passed |
| 1 | One or more required checks failed |
| 2 | Security review required (blocked) |
| 3 | Task not found or invalid |
| 4 | Configuration error |

## Configuration

Quality standards defined in `backend/app/orchestrator/verification.py`:

- **Timeout**: 300s default per check
- **Cache TTL**: 300s (5 minutes)
- **Required vs Optional**: Per-check `required` flag
- **Success Codes**: Per-check acceptable exit codes (default: [0])

## Error Handling

- **Timeout**: Check fails, recorded as timeout
- **Command Not Found**: Check fails with error
- **Permission Denied**: Check fails, may indicate environment issue
- **Partial Output**: Stdout/stderr truncated but preserved
- **Network Issues**: For external checks (npm audit), recorded as warning