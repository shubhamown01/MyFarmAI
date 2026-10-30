# MyFarmAI Task Decompose Skill

**Skill ID:** `myfarmai-task-decompose`  
**Version:** 1.0.0  
**Category:** Planning  
**Description:** Decomposes high-level objectives into atomic, verifiable tasks with clear dependencies, constraints, and acceptance criteria.

## Overview

This skill breaks down complex objectives into the smallest possible tasks that:
- Have a single accountable owner
- Can be verified independently
- Have explicit acceptance criteria
- Respect resource constraints and Phase 0 findings
- Follow the project's document-first engineering policy

## Usage

```bash
# Decompose an objective into tasks
opencode skill myfarmai-task-decompose --objective "Add user authentication" --phase "P3"

# Decompose with specific constraints
opencode skill myfarmai-task-decompose --objective "Optimize API latency" --constraints "postgresql,redis,<100ms"

# Output to file for review
opencode skill myfarmai-task-decompose --objective "Refactor chat service" --output tasks.json
```

## Commands

### `decompose`

Main decomposition command.

**Options:**
- `--objective` (required): High-level objective to decompose
- `--phase`: Phase identifier (e.g., "P1", "P2", "AUTO")
- `--constraints`: Comma-separated constraints
- `--max-tasks`: Maximum number of tasks to generate (default: 20)
- `--output`: Output file (JSON)
- `--format`: Output format (json, yaml, markdown)

### `analyze`

Analyze an objective without full decomposition.

**Options:**
- `--objective` (required): Objective to analyze
- `--detail`: Show detailed capability analysis

### `validate`

Validate a task decomposition for completeness.

**Options:**
- `--input`: Task decomposition file to validate
- `--strict`: Strict validation (fail on warnings)

## Decomposition Principles

### 1. Single Responsibility
Each task should have one clear objective that can be completed by a single agent.

### 2. Verifiable Output
Every task must have explicit verification criteria with runnable commands.

### 3. Explicit Dependencies
Task dependencies must be declared and form a valid DAG.

### 4. Resource Awareness
Tasks must declare resource requirements (model slots, docker builds, test slots).

### 5. Document-First
Tasks that change code must include documentation updates in their scope.

### 6. Phase 0 Compliance
Tasks must not violate Phase 0 gates:
- No database migration without approval
- No secret rotation without approval
- No voice service changes without approval
- No non-loopback exposure without auth

## Task Template

Each decomposed task follows this structure:

```json
{
  "id": "MF-P1-001",
  "objective": "Create FastAPI app factory with configuration profiles",
  "files_involved": [
    "backend/app/factory.py",
    "backend/app/core/config.py",
    "backend/app/main.py"
  ],
  "dependencies": [],
  "constraints": [
    "Python 3.12",
    "uv package manager",
    "No breaking changes to existing API"
  ],
  "expected_output": "Working app factory with dev/test/prod profiles",
  "verification_criteria": {
    "tests": "uv run pytest tests/test_factory.py -v",
    "typecheck": "uv run mypy backend/app/factory.py",
    "lint": "uv run ruff check backend/app/factory.py"
  },
  "owner": "backend-engineer",
  "priority": "high",
  "parallel_group": 0
}
```

## Capability Mapping

The skill maps objectives to capability areas:

| Objective Keywords | Capability Area | Primary Agent |
|-------------------|-----------------|---------------|
| api, endpoint, fastapi, backend | backend | backend-engineer |
| ui, component, react, nextjs, tailwind | frontend | frontend-engineer |
| android, mobile, expo, react native | android | android-engineer |
| model, ollama, inference, qwen | ai_ml | ai-ml-engineer |
| research, search, searxng, citation | research | research-engineer |
| security, auth, secret, vulnerability | security | security-engineer |
| test, qa, lint, typecheck, coverage | qa | qa-reviewer |
| deploy, docker, ci, cd, vercel | deployment | deployment-engineer |
| doc, readme, documentation | documentation | docs-writer |
| architecture, design, adr, decision | architecture | architect-reviewer |
| debug, error, fix, bug, crash | debugging | debugger |
| performance, optimize, slow, latency | performance | performance-engineer |

## Constraints Handling

The skill automatically applies these constraints based on Phase 0 findings:

### Hardware Constraints
- **RAM**: 7 GiB total, ~2.3 GiB available → Limit concurrent memory-intensive tasks
- **VRAM**: 2 GiB MX250 → Max 1 concurrent model inference
- **Disk**: 5.3 GiB free on `/`, 176 GiB on `/data` → Use `/data` for large outputs

### Licensing Constraints
- **Open-Meteo**: Non-commercial only → Flag for commercial use review
- **SearXNG**: AGPL-3.0 → Legal review required for distribution
- **Models**: Check model licenses before integration

### Security Constraints
- **No auth**: Backend binds to 127.0.0.1 only until Phase 3
- **Voice service**: Unauthenticated on 0.0.0.0:8001 → Containment required
- **SearXNG secret**: Hardcoded in config → Rotation required
- **Rate limiting**: Bypassable via X-Forwarded-For → Hardening required

### Data Constraints
- **Two SQLite DBs**: `backend/data/app.db` (122/315) and `data/app.db` (35/74) → Canonical undecided
- **7 clean-DB test failures**: Must be fixed in Phase 1
- **No backup procedure**: Must be established before data changes

## Output Formats

### JSON (Default)
Machine-readable task list with full metadata.

### YAML
Human-readable with comments.

### Markdown
Documentation-ready task list with checkboxes.

## Integration

Works with:
- `myfarmai-orchestrate` - Main orchestration workflow
- `myfarmai-capability-scan` - Discovers available capabilities
- `ce-plan` - Compound Engineering plan creation
- `ce-work` - Compound Engineering plan execution

## Examples

### Example 1: Phase 1 Backend Foundation
```bash
opencode skill myfarmai-task-decompose \
  --objective "Establish reproducible FastAPI foundation with tests, linting, health endpoints" \
  --phase "P1" \
  --constraints "python312,uv,sqlite,no-auth,loopback-only" \
  --output phase1-tasks.json
```

### Example 2: AI Model Integration
```bash
opencode skill myfarmai-task-decompose \
  --objective "Integrate Qwen 4B model via Ollama with agricultural prompt templates" \
  --phase "P4" \
  --constraints "2gb-vram,7gb-ram,ollama,local-only" \
  --max-tasks 10
```

### Example 3: Security Hardening
```bash
opencode skill myfarmai-task-decompose \
  --objective "Implement authentication, rate limiting, and secret management" \
  --phase "P3" \
  --constraints "security,auth,rate-limit,secrets,no-breaking-changes"
```

## Validation Rules

The skill validates decompositions against:

1. **Task ID Format**: `MF-<phase>-<seq>` (e.g., `MF-P1-001`)
2. **Dependency DAG**: No circular dependencies
3. **Owner Assignment**: Every task has an assigned agent
4. **Verification Criteria**: Every task has runnable verification commands
5. **File Ownership**: No overlapping file ownership without coordination
6. **Resource Limits**: Total resource requirements within budget
7. **Phase 0 Gates**: No tasks violating unresolved approval gates
8. **Documentation**: Code changes include doc updates

## Error Handling

- **Over-constrained**: Reduces task granularity or suggests parallelization
- **Missing Capability**: Flags capability gaps for Tier 3 approval
- **Circular Dependency**: Reorders or splits tasks
- **Resource Overflow**: Suggests sequential execution or resource increase