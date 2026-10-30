# MyFarmAI Orchestrate Skill

**Skill ID:** `myfarmai-orchestrate`  
**Version:** 1.0.0  
**Category:** Orchestration  
**Description:** Main orchestration skill for coordinating MyFarmAI development tasks across agents, skills, and tools.

## Overview

This skill provides the primary interface for the MyFarmAI Orchestrator to:
- Decompose high-level objectives into actionable tasks
- Build optimal teams from existing specialist agents
- Route tasks to appropriate capabilities
- Execute tasks with verification gates
- Integrate results and manage conflicts
- Maintain project memory and audit trail

## Usage

```bash
# Run orchestration for a specific objective
opencode skill myfarmai-orchestrate --objective "Add user authentication to backend API" --phase "P1"

# Run with custom constraints
opencode skill myfarmai-orchestrate --objective "Optimize database queries" --constraints "postgresql,performance,no-downtime"

# Resume from checkpoint
opencode skill myfarmai-orchestrate --resume --run-id "run-20261025-123456-abc123"
```

## Commands

### `orchestrate`

Main orchestration command.

**Options:**
- `--objective` (required): High-level objective to achieve
- `--phase`: Phase identifier (e.g., "P1", "P2", "AUTO")
- `--constraints`: Comma-separated constraints (hardware, licensing, etc.)
- `--priority`: Task priority (low, medium, high, critical)
- `--max-parallel`: Maximum parallel agents (default: 4)
- `--dry-run`: Show plan without executing
- `--resume`: Resume from last checkpoint
- `--run-id`: Specific run ID to resume

### `plan`

Create a task plan without executing.

**Options:**
- `--objective` (required): High-level objective
- `--phase`: Phase identifier
- `--output`: Output file for plan (JSON)

### `status`

Show status of current or recent orchestration run.

**Options:**
- `--run-id`: Specific run ID (default: latest)
- `--detail`: Show detailed task status

### `checkpoint`

Manage execution checkpoints.

**Options:**
- `--list`: List all checkpoints
- `--clean`: Remove old checkpoints
- `--task-id`: Show checkpoint for specific task

## Integration

This skill integrates with:
- **Capability Registry** (`myfarmai-capability-scan`) - Discovers available agents/skills/tools
- **Team Builder** - Selects optimal agents for tasks
- **Skill/Tool Router** (`myfarmai-task-decompose`) - Routes tasks to capabilities
- **Verification Gate** (`myfarmai-verify`) - Runs quality and security checks
- **Project Memory** - Maintains decisions, history, learnings

## Workflow

```
1. OBJECTIVE ANALYSIS
   └── Parse objective → Identify required capabilities → Determine constraints

2. TASK DECOMPOSITION
   └── Break into atomic tasks → Build dependency graph → Assign priorities

3. TEAM BUILDING
   └── Match tasks to agents → Create parallel groups → Verify resource availability

4. EXECUTION
   └── Delegate to agents → Monitor progress → Handle retries/blocks

5. VERIFICATION
   └── Run quality gates → Security review → Contract validation

6. INTEGRATION
   └── Detect conflicts → Merge changes → Request reviews

7. COMPLETION
   └── Update memory → Generate report → Clean up checkpoints
```

## Configuration

The skill uses the following configuration files:
- `backend/app/orchestrator/models.py` - Data models
- `backend/app/orchestrator/registry.py` - Capability discovery
- `backend/app/orchestrator/core.py` - Orchestration engine
- `backend/app/orchestrator/team_builder.py` - Team building
- `backend/app/orchestrator/router.py` - Skill/tool routing
- `backend/app/orchestrator/execution.py` - Execution management
- `backend/app/orchestrator/integration.py` - Integration review
- `backend/app/orchestrator/verification.py` - Quality/security gates
- `backend/app/orchestrator/memory.py` - Project memory

## Examples

### Example 1: Backend API Feature
```bash
opencode skill myfarmai-orchestrate \
  --objective "Implement farm management CRUD API endpoints" \
  --phase "P1" \
  --constraints "postgresql,fastapi,auth-required" \
  --priority high
```

### Example 2: Frontend Component
```bash
opencode skill myfarmai-orchestrate \
  --objective "Create responsive dashboard with weather widget" \
  --phase "P2" \
  --constraints "nextjs,tailwind,accessibility" \
  --max-parallel 2
```

### Example 3: Security Audit
```bash
opencode skill myfarmai-orchestrate \
  --objective "Perform security audit of authentication flow" \
  --phase "P3" \
  --constraints "security,auth,owasp" \
  --priority critical
```

## Output

The skill produces:
- **Task Plan** (`docs/engineering/orchestration-plan-<run-id>.json`)
- **Execution Log** (`.orchestrator/logs/run-<run-id>.log`)
- **Checkpoints** (`.orchestrator/checkpoints/`)
- **Audit Report** (`docs/engineering/audit-report-<run-id>.md`)
- **Updated Project Memory** (`.orchestrator/memory/`)

## Error Handling

- **Task Failure**: Automatic retry with exponential backoff (max 3)
- **Resource Conflict**: Task blocked until resources available
- **Verification Failure**: Task marked for review, not auto-retry
- **Integration Conflict**: Requires manual resolution
- **Security Review Required**: Blocks until security-engineer approves

## Permissions

This skill operates within the MyFarmAI permission framework:
- **Tier 1**: Uses existing agents/skills automatically
- **Tier 2**: Installs allowlisted tools automatically
- **Tier 3**: Requires explicit approval for new capabilities
- **Tier 4**: Requires explicit authorization for destructive operations

## Related Skills

- `myfarmai-capability-scan` - Capability discovery
- `myfarmai-task-decompose` - Task decomposition
- `myfarmai-verify` - Verification gates
- `ce-plan` - Plan creation (compound-engineering)
- `ce-work` - Plan execution (compound-engineering)
- `ce-debug` - Debugging (compound-engineering)
- `ce-handoff` - Session continuity (compound-engineering)