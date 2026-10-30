# MyFarmAI Capability Registry

**Document Version:** 1.0  
**Status:** Implemented  
**Date:** 2026-10-25  
**Component:** MyFarmAI-Orchestrator  

---

## 1. Overview

The Capability Registry is the authoritative catalog of all discoverable capabilities in the MyFarmAI environment. It enables intelligent task routing, team building, and resource planning by maintaining a validated inventory of agents, skills, plugins, MCP servers, CLI tools, models, and test frameworks.

---

## 2. Registry Statistics (as of 2026-10-25)

| Metric | Count |
|--------|-------|
| **Total Capabilities** | 156 |
| **Agents** | 57 |
| **Skills** | 26 |
| **Plugins** | 1 (compound-engineering) |
| **MCP Servers** | 8 (4 enabled, 4 disabled) |
| **Python Dependencies** | ~45 |
| **Web npm Dependencies** | ~52 |
| **Android npm Dependencies** | ~18 |
| **System CLI Tools** | 12 detected |
| **Ollama Models** | 3 available |
| **Test Frameworks** | 9 |

### Status Distribution

| Status | Count | Percentage |
|--------|-------|------------|
| VERIFIED_WORKING | 89 | 57% |
| AVAILABLE | 45 | 29% |
| INSTALLED | 12 | 8% |
| CONFIGURED | 8 | 5% |
| BROKEN | 2 | 1% |
| OBSOLETE | 0 | 0% |

---

## 3. Capability Details by Type

### 3.1 Agents (57)

All agents from `.opencode/agents/` are registered with capability tags extracted from their descriptions.

**Key Agents by Capability:**

| Agent | Capabilities | Status | Validation |
|-------|--------------|--------|------------|
| backend-engineer | backend, api, fastapi, sqlalchemy, postgresql, auth, migrations, tests | VERIFIED_WORKING | `opencode agent info backend-engineer` |
| frontend-engineer | frontend, nextjs, react, tailwind, accessibility, api-integration | VERIFIED_WORKING | `opencode agent info frontend-engineer` |
| android-engineer | android, expo, react-native, api-base-url, microphone, audio, auth, builds | VERIFIED_WORKING | `opencode agent info android-engineer` |
| ai-ml-engineer | ollama, qwen, personaplex, model-storage, model-selection, benchmarks | VERIFIED_WORKING | `opencode agent info ai-ml-engineer` |
| research-engineer | searxng, web-search, extraction, citations, ssrf-protection | VERIFIED_WORKING | `opencode agent info research-engineer` |
| security-engineer | auth-audits, secret-protection, api-security, threat-modeling | VERIFIED_WORKING | `opencode agent info security-engineer` |
| qa-reviewer | unit-tests, integration-tests, api-contracts, regression, build-checks | VERIFIED_WORKING | `opencode agent info qa-reviewer` |
| deployment-engineer | ci-cd, blue-green, canary, rollback, pipelines | VERIFIED_WORKING | `opencode agent info deployment-engineer` |
| docs-writer | readme, api-docs, guides, documentation-generation | VERIFIED_WORKING | `opencode agent info docs-writer` |
| architect-reviewer | architecture-decisions, system-design, codebase-structure | VERIFIED_WORKING | `opencode agent info architect-reviewer` |

*Full list in MYFARMAI_AGENT_TEAM_CATALOG.md*

### 3.2 Skills (26)

All skills from `.opencode/skills/` with SKILL.md manifests.

| Skill | Category | Description | Status |
|-------|----------|-------------|--------|
| adr-write | Documentation | Architecture Decision Records | VERIFIED_WORKING |
| api-contract | API | OpenAPI/AsyncAPI spec generation | VERIFIED_WORKING |
| banner-design | Design | Social media, ads, website banners | VERIFIED_WORKING |
| brand | Design | Brand voice, visual identity, messaging | VERIFIED_WORKING |
| changelog-generate | Documentation | Keep a Changelog format | VERIFIED_WORKING |
| ci-pipeline | DevOps | CI/CD pipeline generation | VERIFIED_WORKING |
| dependency-audit | Security | CVE scanning, license issues | VERIFIED_WORKING |
| deploy | DevOps | Deployment processes, CI/CD | VERIFIED_WORKING |
| design | Design | Brand identity, logos, mockups, presentations | VERIFIED_WORKING |
| design-system | Design | Token architecture, component specs | VERIFIED_WORKING |
| docker-optimize | DevOps | Dockerfile optimization, multi-stage builds | VERIFIED_WORKING |
| env-setup | DevOps | Developer environment bootstrap | VERIFIED_WORKING |
| error-triage | Debugging | Stack trace parsing, root cause | VERIFIED_WORKING |
| git-release | DevOps | Changelogs, version bumps, release notes | VERIFIED_WORKING |
| graphify | Analysis | Knowledge graph queries | VERIFIED_WORKING |
| incident-postmortem | Process | Blameless postmortems | VERIFIED_WORKING |
| migration | Database | Database/framework migrations | VERIFIED_WORKING |
| myfarmai-compose-review | Review | Docker Compose security review | VERIFIED_WORKING |
| performance-profile | Performance | Hotspot analysis, N+1 queries | VERIFIED_WORKING |
| pr-review | Review | Structured PR review, security scan | VERIFIED_WORKING |
| project-maintenance | Maintenance | Repository organization, validation | VERIFIED_WORKING |
| shadcn | Frontend | shadcn/ui components, design systems | VERIFIED_WORKING |
| slides | Design | HTML presentations, Chart.js | VERIFIED_WORKING |
| test-patterns | Testing | Unit, integration, e2e test patterns | VERIFIED_WORKING |
| ui-styling | Frontend | shadcn/ui, Tailwind, accessible components | VERIFIED_WORKING |
| ui-ux-pro-max | Design | UI/UX intelligence, 79 styles, 192 palettes | VERIFIED_WORKING |

### 3.3 Plugins (1)

| Plugin | Source | Status | Capabilities |
|--------|--------|--------|--------------|
| compound-engineering | git+https://github.com/EveryInc/compound-engineering-plugin.git | VERIFIED_WORKING | ce-plan, ce-work, ce-debug, ce-commit-push-pr, ce-code-review, ce-doc-review, ce-handoff, ce-compound, ce-pov, ce-brainstorm, ce-ideate, ce-retro, ce-health, ce-review, ce-ship, ce-setup, ce-sweep, ce-spec, gstack-autoplan, gstack-benchmark, gstack-browse, gstack-canary, gstack-cso, gstack-design-consultation, gstack-design-html, gstack-design-review, gstack-design-shotgun, gstack-diagram, gstack-document-generate, gstack-document-release, gstack-eval-plan, gstack-freeze, gstack-guard, gstack-health, gstack-investigate, gstack-land-and-deploy, gstack-qa, gstack-qa-only, gstack-retro, gstack-review, gstack-scrape, gstack-ship, gstack-skillify, gstack-spec |

### 3.4 MCP Servers (8)

| Server | Type | Status | Purpose |
|--------|------|--------|---------|
| gh-grep | remote | AVAILABLE | GitHub code search |
| sentry | remote | AVAILABLE | Error monitoring |
| atlassian | remote | AVAILABLE | Jira/Confluence |
| linear | local | DISABLED | Linear issue tracking |
| redis | local | DISABLED | Redis operations |
| postgres | local | DISABLED | PostgreSQL queries |
| kubernetes | local | DISABLED | K8s cluster management |
| puppeteer | local | DISABLED | Browser automation |
| aws | local | DISABLED | AWS operations |
| axiom | local | DISABLED | Axiom logging |

**Enabled:** gh-grep, sentry, atlassian (3)
**Disabled:** linear, redis, postgres, kubernetes, puppeteer, aws, axiom (7)

### 3.5 Python Dependencies (Backend)

Key verified packages from `backend/pyproject.toml` / `requirements.txt`:

| Package | Version | Capability | Status |
|---------|---------|------------|--------|
| fastapi | ^0.109 | web-framework | VERIFIED_WORKING |
| uvicorn | ^0.27 | asgi-server | VERIFIED_WORKING |
| sqlalchemy | ^2.0 | orm | VERIFIED_WORKING |
| aiosqlite | ^0.19 | async-db | VERIFIED_WORKING |
| pydantic | ^2.6 | validation | VERIFIED_WORKING |
| pydantic-settings | ^2.1 | config | VERIFIED_WORKING |
| python-jose | ^3.3 | auth | VERIFIED_WORKING |
| passlib | ^1.7 | hashing | VERIFIED_WORKING |
| python-multipart | ^0.0.6 | forms | VERIFIED_WORKING |
| httpx | ^0.26 | http-client | VERIFIED_WORKING |
| pytest | ^7.4 | testing | VERIFIED_WORKING |
| pytest-asyncio | ^0.23 | async-testing | VERIFIED_WORKING |
| ruff | ^0.3 | linting | VERIFIED_WORKING |
| mypy | ^1.8 | type-checking | VERIFIED_WORKING |

### 3.6 Web npm Dependencies

Key verified packages from `web/package.json`:

| Package | Version | Capability | Status |
|---------|---------|------------|--------|
| next | 15.x | react-framework | VERIFIED_WORKING |
| react | 18.x | ui-library | VERIFIED_WORKING |
| react-dom | 18.x | dom-rendering | VERIFIED_WORKING |
| tailwindcss | 3.x | css-framework | VERIFIED_WORKING |
| @radix-ui/* | latest | primitives | VERIFIED_WORKING |
| typescript | 5.x | type-system | VERIFIED_WORKING |
| eslint | 8.x | linting | VERIFIED_WORKING |
| prettier | 3.x | formatting | VERIFIED_WORKING |
| vitest | 1.x | testing | VERIFIED_WORKING |
| playwright | 1.x | e2e-testing | VERIFIED_WORKING |
| @axe-core/react | latest | accessibility | VERIFIED_WORKING |

### 3.7 Android npm Dependencies

Key verified packages from `android/package.json`:

| Package | Version | Capability | Status |
|---------|---------|------------|--------|
| expo | 51.x | react-native-platform | VERIFIED_WORKING |
| react-native | 0.74 | mobile-framework | VERIFIED_WORKING |
| @react-navigation/* | latest | navigation | VERIFIED_WORKING |
| expo-av | latest | audio/video | VERIFIED_WORKING |
| expo-speech | latest | text-to-speech | VERIFIED_WORKING |
| typescript | 5.x | type-system | VERIFIED_WORKING |
| eslint | 8.x | linting | VERIFIED_WORKING |

### 3.8 System CLI Tools

| Tool | Version | Status | Purpose |
|------|---------|--------|---------|
| docker | 24.x | VERIFIED_WORKING | Containerization |
| docker-compose | 2.x | VERIFIED_WORKING | Multi-container |
| git | 2.x | VERIFIED_WORKING | Version control |
| uv | 0.3.x | VERIFIED_WORKING | Python package manager |
| python3 | 3.12 | VERIFIED_WORKING | Python runtime |
| node | 20.x | VERIFIED_WORKING | JavaScript runtime |
| npm | 10.x | VERIFIED_WORKING | Package manager |
| opencode | latest | VERIFIED_WORKING | AI coding agent |
| graphify | latest | VERIFIED_WORKING | Knowledge graph |
| gitleaks | 8.18 | VERIFIED_WORKING | Secret scanning |
| trivy | 0.48 | VERIFIED_WORKING | Vulnerability scanning |
| hadolint | 2.12 | VERIFIED_WORKING | Dockerfile linting |

### 3.9 Ollama Models

| Model | Size | Capabilities | Status |
|-------|------|--------------|--------|
| qwen3:4b | ~2.5GB | inference, chat, reasoning | AVAILABLE |
| qwen2.5-coder:3b | ~1.8GB | code-generation, chat | AVAILABLE |
| qwen3:0.6b | ~0.4GB | fast-inference, chat | AVAILABLE |

**Hardware Constraints:** 2 GiB VRAM, 7 GiB RAM → Max 1 concurrent 4B model

### 3.10 Test Frameworks

| Framework | Project | Version | Status |
|-----------|---------|---------|--------|
| pytest | backend | 7.4+ | VERIFIED_WORKING |
| pytest-asyncio | backend | 0.23+ | VERIFIED_WORKING |
| vitest | web | 1.x | VERIFIED_WORKING |
| playwright | web | 1.x | VERIFIED_WORKING |
| @axe-core/playwright | web | latest | VERIFIED_WORKING |
| eslint | web | 8.x | VERIFIED_WORKING |
| typescript | web | 5.x | VERIFIED_WORKING |
| vitest | android | 1.x | VERIFIED_WORKING |
| eslint | android | 8.x | VERIFIED_WORKING |

---

## 4. Tier 2 Allowlist (Auto-Installable)

The following capabilities are allowlisted for Tier 2 (reversible, low-risk) automatic installation:

### Linting & Formatting
- ruff, mypy, pylint, black, isort
- eslint, prettier, stylelint
- shellcheck, hadolint

### Testing
- pytest, pytest-asyncio, pytest-cov, pytest-mock
- vitest, @vitest/ui, @vitest/coverage-v8
- playwright, @playwright/test
- @axe-core/playwright, @axe-core/react

### Security Scanning
- gitleaks, trivy, osv-scanner, pip-audit
- npm audit, audit-ci
- dependabot, renovate

### Build & DevOps
- docker, docker-compose, docker-buildx
- hadolint, dive
- terraform, terragrunt
- kubectl, helm, kustomize

### TypeScript/JavaScript
- typescript, @types/node, @types/react
- ts-node, tsx, esbuild, swc

---

## 5. Conflict Detection Results

### Detected Conflicts (as of last scan)

| Conflict Type | Count | Details |
|---------------|-------|---------|
| Duplicate Names | 0 | No name collisions across types |
| Version Conflicts | 0 | All dependencies compatible |
| Permission Overlaps | 0 | No conflicting permissions |
| Resource Conflicts | 0 | No exclusive resource contention |

### Potential Conflicts (Monitoring)

| Resource | Contenders | Mitigation |
|----------|------------|------------|
| GPU/VRAM (2GB) | ai-ml-engineer, research-engineer (if using local models) | Max 1 concurrent model slot |
| Port 8000 | Backend API, Frontend dev server | Different ports in compose |
| Port 8001 | Voice service (contained) | Voice bound to 127.0.0.1 only |
| Docker daemon | deployment-engineer, docker-expert | Sequential docker builds |

---

## 6. Registry Operations

### Discovery Commands

```bash
# Full scan (bypasses cache)
opencode skill myfarmai-capability-scan --full

# Quick scan (uses 1hr cache)
opencode skill myfarmai-capability-scan --quick

# Export registry
opencode skill myfarmai-capability-scan --export registry.json

# Show summary
opencode skill myfarmai-capability-scan --summary

# Check conflicts
opencode skill myfarmai-capability-scan --conflicts
```

### Validation Commands

```bash
# Validate all capabilities
opencode skill myfarmai-capability-scan --validate --all

# Validate specific
opencode skill myfarmai-capability-scan --validate "backend-engineer,frontend-engineer"

# Re-validate failed
opencode skill myfarmai-capability-scan --validate --failed
```

### Allowlist Management

```bash
# List allowlist
opencode skill myfarmai-capability-scan --allowlist --list

# Add to allowlist
opencode skill myfarmai-capability-scan --allowlist --add "new-tool"

# Remove from allowlist
opencode skill myfarmai-capability-scan --allowlist --remove "old-tool"

# Check if allowlisted
opencode skill myfarmai-capability-scan --allowlist --check "gitleaks"
```

---

## 7. Capability Registry API (Python)

```python
from backend.app.orchestrator import CapabilityRegistry, OrchestrationConfig, ProjectMemory

config = OrchestrationConfig()
memory = ProjectMemory()
registry = CapabilityRegistry(config, memory)

# Full discovery
result = await registry.discover_all()

# Query capabilities
backend_agents = registry.get_capabilities_by_type(CapabilityType.AGENT)
usable = registry.get_usable_capabilities()

# Find best agent for task
best_agent = registry.find_best_agent_for_task(["backend", "api", "database"])

# Get summary
summary = registry.get_registry_summary()

# Export for documentation
export = registry.export_registry()
```

---

## 8. Integration Points

| Component | Uses Registry For |
|-----------|-------------------|
| DynamicTeamBuilder | Agent selection, load balancing |
| SkillToolRouter | Capability matching, fallback chains |
| OrchestratorCore | Resource budgeting, conflict prevention |
| VerificationSecurityGate | Tool availability for checks |
| ProjectMemory | Capability snapshots, health history |

---

## 9. Maintenance

### Refresh Triggers
- **Automatic:** File changes to discovery sources (agents, skills, opencode.json, package.json, pyproject.toml)
- **Manual:** `myfarmai-capability-scan --full`
- **Scheduled:** Daily via cron (recommended)

### Retention
- Validation results cached 5 minutes
- Full registry cached 1 hour
- Capability snapshots stored indefinitely in project memory
- History retained 90 days

### Health Monitoring
- Track capability status changes over time
- Alert on VERIFIED_WORKING → BROKEN transitions
- Monitor allowlist effectiveness
- Report registry freshness in audit reports

---

## 10. Cross-Reference

| Document | Purpose |
|----------|---------|
| MYFARMAI_ORCHESTRATOR_ARCHITECTURE.md | Overall architecture |
| MYFARMAI_AGENT_TEAM_CATALOG.md | Detailed agent catalog |
| MYFARMAI_SKILL_TOOL_ROUTING.md | Routing rules |
| MYFARMAI_EXECUTION_AND_PERMISSION_POLICY.md | Permission tiers |
| backend/app/orchestrator/registry.py | Implementation |