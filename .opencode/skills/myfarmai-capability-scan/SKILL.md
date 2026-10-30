# MyFarmAI Capability Scan Skill

**Skill ID:** `myfarmai-capability-scan`  
**Version:** 1.0.0  
**Category:** Discovery  
**Description:** Discovers, catalogs, and validates all available capabilities in the MyFarmAI environment including agents, skills, plugins, MCP servers, CLI tools, models, and test frameworks.

## Overview

This skill provides comprehensive capability discovery for the MyFarmAI Orchestrator. It scans multiple sources and produces a validated capability registry that enables intelligent task routing and team building.

## Usage

```bash
# Full capability scan
opencode skill myfarmai-capability-scan --full

# Quick scan (cached)
opencode skill myfarmai-capability-scan --quick

# Scan specific capability types
opencode skill myfarmai-capability-scan --types agent,skill,mcp

# Validate specific capabilities
opencode skill myfarmai-capability-scan --validate "backend-engineer,frontend-engineer"

# Export registry
opencode skill myfarmai-capability-scan --export registry.json

# Show summary
opencode skill myfarmai-capability-scan --summary
```

## Commands

### `scan`

Main discovery command.

**Options:**
- `--full`: Force full refresh (default: uses cache if < 1 hour old)
- `--quick`: Use cached results only
- `--types`: Comma-separated capability types to scan (agent,skill,plugin,mcp,cli,model,test_framework)
- `--validate`: Validate specific capabilities by name
- `--export`: Export registry to file (JSON)
- `--summary`: Show summary table
- `--conflicts`: Show detected conflicts only

### `list`

List discovered capabilities.

**Options:**
- `--type`: Filter by capability type
- `--status`: Filter by status (installed, configured, authenticated, available, verified_working, broken, obsolete)
- `--usable`: Show only usable capabilities
- `--format`: Output format (table, json, yaml)

### `validate`

Run validation commands for capabilities.

**Options:**
- `--name`: Capability name to validate
- `--all`: Validate all capabilities
- `--failed`: Re-validate previously failed capabilities

### `allowlist`

Manage Tier 2 allowlist for auto-installation.

**Options:**
- `--add`: Add capability to allowlist
- `--remove`: Remove capability from allowlist
- `--list`: Show current allowlist
- `--check`: Check if capability is allowlisted

## Discovery Sources

| Source | Path | Capability Types |
|--------|------|------------------|
| OpenCode Agents | `.opencode/agents/*.md` | agent |
| OpenCode Skills | `.opencode/skills/*/SKILL.md` | skill |
| OpenCode Plugins | `opencode.json` plugin array | plugin |
| MCP Servers | `opencode.json` mcp.servers | mcp |
| Python Dependencies | `backend/pyproject.toml` or `requirements.txt` | cli |
| Web npm Dependencies | `web/package.json` | cli |
| Android npm Dependencies | `android/package.json` | cli |
| System CLI Tools | `PATH` | cli |
| Ollama Models | `ollama list` | model |
| Test Frameworks | Project configs | test_framework |

## Capability Status Lifecycle

```
INSTALLED → CONFIGURED → AUTHENTICATED → AVAILABLE → VERIFIED_WORKING
                ↓              ↓              ↓
             BROKEN        BROKEN         BROKEN
                ↓              ↓              ↓
             OBSOLETE      OBSOLETE       OBSOLETE
```

- **INSTALLED**: Discovered but not yet validated
- **CONFIGURED**: Configuration found (e.g., MCP server configured)
- **AUTHENTICATED**: Credentials/tokens configured (for MCP, APIs)
- **AVAILABLE**: Ready to use, validation not yet run
- **VERIFIED_WORKING**: Validation command succeeded
- **BROKEN**: Validation failed or dependency missing
- **OBSOLETE**: Superseded or deprecated

## Validation Commands

Each capability type has standard validation:

| Type | Validation Command |
|------|-------------------|
| agent | `opencode agent info <name>` |
| skill | `opencode skill info <name>` |
| plugin | Check plugin loads |
| mcp | Connection test to MCP server |
| cli (python) | `uv run python -c "import <module>"` |
| cli (npm) | `npm list <package>` |
| cli (system) | `<command> --version` |
| model | `ollama run <model> --help` |
| test_framework | `<framework> --version` |

## Conflict Detection

The scanner detects:

1. **Duplicate Names**: Same name, different types (e.g., "backend-engineer" as agent and skill)
2. **Version Conflicts**: Multiple versions of same dependency
3. **Permission Overlaps**: Capabilities requesting conflicting permissions
4. **Resource Conflicts**: Multiple capabilities requiring exclusive resources (GPU, ports)

## Output

### Registry Export (JSON)
```json
{
  "capabilities": {
    "backend-engineer": {
      "type": "agent",
      "status": "verified_working",
      "version": "1.0",
      "location": ".opencode/agents/backend-engineer.md",
      "capabilities": ["backend", "api", "fastapi", "sqlalchemy"],
      "permissions": ["task:backend-engineer", "task:*"],
      "dependencies": [],
      "last_verified": "2026-10-25T10:30:00Z",
      "metadata": {"source": "opencode_agents", "mode": "subagent", "steps": 15}
    }
  },
  "summary": {
    "total_capabilities": 156,
    "by_type": {"agent": 57, "skill": 26, "plugin": 1, "mcp": 8, "cli": 52, "model": 3, "test_framework": 9},
    "by_status": {"verified_working": 89, "available": 45, "broken": 22},
    "usable_count": 134
  },
  "allowlist": ["ruff", "mypy", "pytest", "gitleaks", ...]
}
```

### Summary Table
```
┌─────────────────────┬──────────┬─────────────────┬────────────────┬─────────────┐
│ Name                │ Type     │ Status          │ Version        │ Capabilities│
├─────────────────────┼──────────┼─────────────────┼────────────────┼─────────────┤
│ backend-engineer    │ agent    │ verified_working│ 1.0            │ 6           │
│ frontend-engineer   │ agent    │ verified_working│ 1.0            │ 5           │
│ shadcn              │ skill    │ verified_working│ 1.0            │ 1           │
│ gitleaks            │ cli      │ verified_working│ 8.18.0         │ 1           │
│ ollama_qwen3_4b     │ model    │ available       │ -              │ 3           │
└─────────────────────┴──────────┴─────────────────┴────────────────┴─────────────┘
```

## Integration

Used by:
- `myfarmai-orchestrate` - For capability-aware task routing
- `myfarmai-task-decompose` - For identifying capability gaps
- `myfarmai-verify` - For validation gate capabilities
- `SkillToolRouter` (backend/app/orchestrator/router.py) - Internal routing engine

## Caching

- Full scan results cached for 1 hour (`.orchestrator/cache/capabilities.json`)
- Validation results cached for 5 minutes
- Use `--full` to bypass cache
- Cache invalidated on file changes to discovery sources

## Permission Tiers

Capabilities are classified by permission tier:

| Tier | Description | Examples |
|------|-------------|----------|
| TIER1_EXISTING | Auto-use within granted permissions | All existing agents, skills, configured MCPs |
| TIER2_REVERSIBLE | Auto-install if allowlisted | ruff, mypy, pytest, gitleaks, trivy |
| TIER3_NEW | Explicit approval required | New agents, new skills, new MCP servers |
| TIER4_DESTRUCTIVE | Explicit authorization + safeguards | Database migrations, secret rotation, production deploy |

## Examples

### Example 1: Full Scan for New Session
```bash
opencode skill myfarmai-capability-scan --full --export .orchestrator/registry.json
```

### Example 2: Quick Check Before Task
```bash
opencode skill myfarmai-capability-scan --quick --summary
```

### Example 3: Validate Specific Agents
```bash
opencode skill myfarmai-capability-scan --validate "backend-engineer,security-engineer,qa-reviewer"
```

### Example 4: Check for Conflicts
```bash
opencode skill myfarmai-capability-scan --conflicts
```

## Error Handling

- **Source Unavailable**: Log warning, continue with other sources
- **Validation Timeout**: Mark as BROKEN, record timeout
- **Parse Error**: Skip file, log error, continue
- **Network Error** (MCP/Ollama): Mark as BROKEN, retry on next scan