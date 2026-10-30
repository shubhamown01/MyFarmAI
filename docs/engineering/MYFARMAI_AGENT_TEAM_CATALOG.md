# MyFarmAI Agent Team Catalog

**Document Version:** 1.0  
**Status:** Implemented  
**Date:** 2026-10-25  
**Component:** MyFarmAI-Orchestrator  

---

## 1. Overview

This catalog documents all 57 specialist agents available in the MyFarmAI OpenCode environment, organized by capability area. The DynamicTeamBuilder selects from these agents based on task requirements, availability, and specialization.

---

## 2. Agent Inventory by Category

### 2.1 Backend & API Development (6 agents)

| Agent | Mode | Steps | Key Capabilities | Best For |
|-------|------|-------|------------------|----------|
| `backend-engineer` | subagent | 15 | FastAPI, SQLAlchemy, PostgreSQL, auth, migrations, tests | Primary backend development |
| `fastapi-developer` | subagent | 15 | FastAPI async, Pydantic, dependency injection, OpenAPI | FastAPI-specific work |
| `backend-developer` | subagent | 15 | Scalable APIs, databases, backend systems | General backend |
| `database-administrator` | subagent | 15 | Replication, backup, recovery, capacity planning | Database operations |
| `postgres-pro` | subagent | 15 | Advanced queries, extensions, performance tuning | PostgreSQL expertise |
| `sql-pro` | subagent | 15 | Window functions, CTEs, query optimization, migrations | Complex SQL |

### 2.2 Frontend & Web Development (6 agents)

| Agent | Mode | Steps | Key Capabilities | Best For |
|-------|------|-------|------------------|----------|
| `frontend-engineer` | subagent | 15 | Next.js, React, Tailwind, accessibility, API integration | Primary frontend development |
| `frontend-developer` | subagent | 15 | React, Vue, Angular, modern web development | General frontend |
| `nextjs-developer` | subagent | 15 | Next.js 14+, App Router, Server Actions, RSC | Next.js-specific work |
| `react-specialist` | subagent | 15 | React 18+, hooks, server components, Suspense | React patterns |
| `typescript-pro` | subagent | 15 | Strict typing, generics, utility types, declaration files | TypeScript expertise |
| `javascript-pro` | subagent | 15 | ES2024+, async patterns, module systems, runtime optimization | JavaScript expertise |

### 2.3 Android & Mobile Development (3 agents)

| Agent | Mode | Steps | Key Capabilities | Best For |
|-------|------|-------|------------------|----------|
| `android-engineer` | subagent | 15 | Expo/React Native, API base URL, microphone/audio, auth, builds | Primary Android development |
| `mobile-developer` | subagent | 15 | React Native, Flutter, native iOS/Android | Cross-platform mobile |
| `mobile-app-developer` | subagent | 15 | Native iOS/Android, app store deployment | App store deployment |

### 2.4 AI/ML & Model Integration (5 agents)

| Agent | Mode | Steps | Key Capabilities | Best For |
|-------|------|-------|------------------|----------|
| `ai-ml-engineer` | subagent | 15 | Ollama gateway, Qwen models, PersonaPlex, model storage | Primary AI/ML integration |
| `llm-architect` | subagent | 15 | LLM systems, RAG pipelines, fine-tuning, prompt engineering | LLM architecture |
| `machine-learning-engineer` | subagent | 15 | Model training, optimization, production deployment | ML model lifecycle |
| `nlp-engineer` | subagent | 15 | Tokenization, embeddings, transformer models | NLP systems |
| `ai-engineer` | subagent | 15 | Model selection, deployment architecture, ML pipelines | AI systems design |

### 2.5 Research & Search (5 agents)

| Agent | Mode | Steps | Key Capabilities | Best For |
|-------|------|-------|------------------|----------|
| `research-engineer` | subagent | 15 | SearXNG, web search, extraction, citations, SSRF protection | Primary research engine |
| `search-specialist` | subagent | 15 | Advanced query strategies, source curation | Search optimization |
| `data-researcher` | subagent | 15 | Dataset discovery, quality evaluation, statistical analysis | Data research |
| `scientific-literature-researcher` | subagent | 15 | Literature search, evidence synthesis, citation analysis | Academic research |
| `research-analyst` | subagent | 15 | Comprehensive research, source evaluation, synthesis | General research |

### 2.6 Security & Compliance (4 agents)

| Agent | Mode | Steps | Key Capabilities | Best For |
|-------|------|-------|------------------|----------|
| `security-engineer` | subagent | 15 | Auth audits, secret protection, API/upload security, threat modeling | Primary security |
| `penetration-tester` | subagent | 15 | Ethical hacking, OWASP methodology, vulnerability exploitation | Pen testing |
| `security-auditor` | subagent | 15 | Security audits, vulnerability identification, dependency risks | Security audits |
| `compliance-auditor` | subagent | 15 | GDPR, SOC2, HIPAA, OSS license compliance | Compliance |

### 2.7 Quality Assurance & Testing (5 agents)

| Agent | Mode | Steps | Key Capabilities | Best For |
|-------|------|-------|------------------|----------|
| `qa-reviewer` | subagent | 15 | Unit/integration tests, API contracts, regression, build checks | Primary QA |
| `test-automator` | subagent | 15 | E2E, integration, CI-integrated test frameworks | Test automation |
| `test-writer` | subagent | 15 | Test writing, coverage, edge cases, maintainability | Test creation |
| `accessibility-tester` | subagent | 10 | WCAG 2.1 AA/AAA, inclusive design | Accessibility |
| `code-reviewer` | subagent | 15 | Quality, security, performance, maintainability | Code review |

### 2.8 DevOps, Deployment & Infrastructure (6 agents)

| Agent | Mode | Steps | Key Capabilities | Best For |
|-------|------|-------|------------------|----------|
| `deployment-engineer` | subagent | 15 | Blue/green, canary, rollback, deployment pipelines | Deployment |
| `devops-engineer` | subagent | 15 | CI/CD pipelines, build automation, environment config | DevOps |
| `platform-engineer` | subagent | 15 | Internal developer platforms, golden paths, self-service | Platform engineering |
| `docker-expert` | subagent | 15 | Dockerfiles, compose stacks, container security | Docker |
| `kubernetes-specialist` | subagent | 15 | K8s clusters, Helm charts, service mesh, orchestration | Kubernetes |
| `sre-engineer` | subagent | 15 | SLIs/SLOs, observability, incident response | SRE |

### 2.9 Architecture & Design (4 agents)

| Agent | Mode | Steps | Key Capabilities | Best For |
|-------|------|-------|------------------|----------|
| `architect-reviewer` | subagent | 15 | Architecture decisions, system design, codebase structure | Architecture review |
| `cloud-architect` | subagent | 15 | Multi-cloud (AWS/GCP/Azure), cost optimization, resilience | Cloud architecture |
| `microservices-architect` | subagent | 15 | Service boundaries, communication patterns, decomposition | Microservices |
| `system-architect` | subagent | 15 | Distributed systems, scalability, reliability | System design |

### 2.10 Documentation & Technical Writing (3 agents)

| Agent | Mode | Steps | Key Capabilities | Best For |
|-------|------|-------|------------------|----------|
| `docs-writer` | subagent | 10 | README, API docs, guides, documentation generation | Documentation |
| `technical-writer` | subagent | 10 | Technical documentation, API guides, tutorials | Technical writing |
| `content-marketer` | subagent | 10 | SEO content, developer marketing, technical blogging | Marketing content |

### 2.11 Debugging & Diagnostics (3 agents)

| Agent | Mode | Steps | Key Capabilities | Best For |
|-------|------|-------|------------------|----------|
| `debugger` | subagent | 20 | Log analysis, stack traces, code flow debugging | Debugging |
| `error-detective` | subagent | 15 | Error log analysis, pattern identification, systemic issues | Error analysis |
| `error-coordinator` | subagent | 10 | Cross-system error handling, recovery strategies | Error coordination |

### 2.12 Performance & Optimization (3 agents)

| Agent | Mode | Steps | Key Capabilities | Best For |
|-------|------|-------|------------------|----------|
| `performance-engineer` | subagent | 15 | Profiling, memory, CPU, latency, throughput optimization | Performance |
| `vercel-optimize` | subagent | 15 | Vercel cost/performance, Next.js, SvelteKit, Edge | Vercel optimization |
| `database-optimizer` | subagent | 15 | Schema, queries, indexes, connection management | Database perf |

### 2.13 Process & Management (4 agents)

| Agent | Mode | Steps | Key Capabilities | Best For |
|-------|------|-------|------------------|----------|
| `project-manager` | subagent | 8 | Timelines, risks, stakeholder coordination | Project management |
| `product-manager` | subagent | 10 | Product strategy, roadmaps, prioritization | Product management |
| `scrum-master` | subagent | 8 | Agile ceremonies, team coaching, impediment removal | Scrum |
| `git-workflow-manager` | subagent | 8 | Branching strategies, commit hygiene, Git automation | Git workflow |

### 2.14 Orchestration & Coordination (4 agents)

| Agent | Mode | Steps | Key Capabilities | Best For |
|-------|------|-------|------------------|----------|
| `myfarmai-orchestrator` | primary | 20 | Project-wide coordination, delegation, integration | **Primary orchestrator** |
| `agent-organizer` | subagent | 5 | Multi-agent team routing, task assignment | Agent coordination |
| `multi-agent-coordinator` | subagent | 10 | Complex multi-agent workflows, dependency management | Multi-agent |
| `workflow-orchestrator` | subagent | 10 | Multi-step task decomposition, agent delegation | Workflow orchestration |

### 2.15 Specialized Domain Agents (4 agents)

| Agent | Mode | Steps | Key Capabilities | Best For |
|-------|------|-------|------------------|----------|
| `azure-infra-engineer` | subagent | 15 | ARM/Bicep, AKS, Azure DevOps | Azure infrastructure |
| `spring-boot-engineer` | subagent | 15 | Spring Boot 3+, WebFlux, Security, Data JPA | Spring Boot |
| `django-developer` | subagent | 15 | Django 4+, ORM, REST, Celery, signals | Django |
| `laravel-specialist` | subagent | 15 | Laravel 10+, Eloquent, Livewire, queues | Laravel |

---

## 3. Agent Selection Matrix

### By Task Type

| Task Type | Primary Agent | Fallback 1 | Fallback 2 | Required Skills |
|-----------|--------------|------------|------------|-----------------|
| Backend API | backend-engineer | fastapi-developer | backend-developer | api-contract |
| Database Migration | database-administrator | postgres-pro | sql-pro | migration |
| Frontend Component | frontend-engineer | react-specialist | nextjs-developer | shadcn, ui-styling |
| Android Feature | android-engineer | mobile-developer | flutter-expert | vercel-react-native-skills |
| AI Model Integration | ai-ml-engineer | llm-architect | machine-learning-engineer | google-agents-cli-adk-code |
| Research Pipeline | research-engineer | search-specialist | data-researcher | searxng, context7-mcp |
| Security Audit | security-engineer | penetration-tester | security-auditor | gstack-cso, dependency-audit |
| QA/Testing | qa-reviewer | test-automator | test-writer | test-patterns, webapp-testing |
| Deployment | deployment-engineer | devops-engineer | platform-engineer | deploy-to-vercel, docker-build-strategies |
| Documentation | docs-writer | technical-writer | content-marketer | document-generate, changelog-generate |
| Architecture Decision | architect-reviewer | cloud-architect | platform-engineer | adr-write, ce-pov |
| Debugging | debugger | error-detective | error-coordinator | ce-debug, systematic-debugging |
| Performance | performance-engineer | vercel-optimize | database-optimizer | performance-profile |

### By Capability Tags

Each agent has capability tags extracted from their description:

```
backend-engineer:       [backend, api, fastapi, sqlalchemy, postgresql, auth, migrations, tests]
frontend-engineer:      [frontend, nextjs, react, tailwind, accessibility, api-integration, responsive]
android-engineer:       [android, expo, react-native, api-base-url, microphone, audio, auth, builds]
ai-ml-engineer:         [ollama, qwen, personaplex, model-storage, model-selection, benchmarks, inference]
research-engineer:      [searxng, web-search, extraction, citations, ssrf-protection, agricultural-workflows]
security-engineer:      [auth-audits, secret-protection, api-security, upload-security, threat-modeling]
qa-reviewer:            [unit-tests, integration-tests, api-contracts, regression, build-checks, migrations]
deployment-engineer:    [ci-cd, blue-green, canary, rollback, pipelines, automation]
docs-writer:            [readme, api-docs, guides, documentation-generation]
architect-reviewer:     [architecture-decisions, system-design, codebase-structure, maintainability]
debugger:               [log-analysis, stack-traces, code-flow, root-cause, debugging]
performance-engineer:   [profiling, memory, cpu, latency, throughput, bottlenecks, optimization]
```

---

## 4. Agent Permissions (from opencode.json)

### myfarmai-orchestrator (Primary)
```json
{
  "mode": "primary",
  "permission": {
    "task": {
      "*": "deny",
      "myfarmai-*": "allow",
      "backend-engineer": "allow",
      "frontend-engineer": "allow",
      "android-engineer": "allow",
      "ai-ml-engineer": "allow",
      "research-engineer": "allow",
      "security-engineer": "allow",
      "qa-reviewer": "allow",
      "release-coordinator": "allow",
      "explore": "allow"
    }
  }
}
```

### All Specialist Agents (Subagents)
```json
{
  "mode": "subagent",
  "steps": 10-20,
  "permission": { "task": { "*": "allow" } }
}
```

---

## 5. Agent Load Management

The DynamicTeamBuilder tracks agent load to prevent overload:

- **Max concurrent tasks per agent:** 3
- **Load balancing:** Prefers less loaded agents when scores are close
- **Specialization bonus:** +0.1 score for exact capability match
- **Availability check:** Agent must be VERIFIED_WORKING in registry

### Current Agent Load (Example)
```
backend-engineer:        2/3 tasks
frontend-engineer:       1/3 tasks
android-engineer:        0/3 tasks
ai-ml-engineer:          1/3 tasks
research-engineer:       0/3 tasks
security-engineer:       0/3 tasks
qa-reviewer:             1/3 tasks
deployment-engineer:     0/3 tasks
docs-writer:             0/3 tasks
architect-reviewer:      0/3 tasks
```

---

## 6. Capability Gaps (Identified)

| Missing Capability | Current Workaround | Tier 3 Approval Needed |
|-------------------|-------------------|------------------------|
| GraphQL API development | Use REST patterns | Yes, if GraphQL required |
| gRPC services | Not in scope | Yes, if needed |
| Mobile native (Swift/Kotlin) | React Native/Expo | Yes, if native required |
| Data pipeline (Airflow/Dagster) | Not in scope | Yes, if needed |
| Message queue (Kafka/RabbitMQ) | Not in scope | Yes, if needed |
| Time-series DB (InfluxDB/TimescaleDB) | PostgreSQL | Yes, if needed |

---

## 7. Agent Health Monitoring

The CapabilityRegistry validates agents periodically:

| Check | Command | Frequency |
|-------|---------|-----------|
| Agent loads | `opencode agent info <name>` | On demand + 1hr cache |
| Skill availability | `opencode skill info <name>` | On demand + 1hr cache |
| Permission verification | Check opencode.json | On config change |

### Status Indicators
- 🟢 **VERIFIED_WORKING** - Agent loads and responds correctly
- 🟡 **AVAILABLE** - Agent configured, not recently validated
- 🔴 **BROKEN** - Agent fails to load or validate
- ⚪ **OBSOLETE** - Superseded by newer agent/skill

---

## 8. Adding New Agents

### Tier 3 Process (Explicit Approval Required)

1. **Identify Gap** - Document missing capability with use cases
2. **Design Agent** - Create `.opencode/agents/<name>.md` with:
   - Description
   - Mode (subagent)
   - Steps (10-20)
   - Permissions
3. **Register** - Add to opencode.json agents section
4. **Validate** - Run capability scan to verify
5. **Document** - Update this catalog

### Agent Template
```markdown
---
description: <one-line description>
mode: subagent
steps: 15
temperature: 0.3
permission:
  task:
    "*": "allow"
---

You are a <Specialty> Specialist. Your role is to <specific responsibility>.

## Core Responsibilities
1. <Responsibility 1>
2. <Responsibility 2>
3. <Responsibility 3>

## Tools & Technologies
- <Tool 1>
- <Tool 2>

## Standards
- Follow project conventions
- Update documentation
- Write tests for new code
```

---

## 9. Deprecated/Obsolete Agents

None currently. All 57 agents are active and maintained.

---

## 10. Cross-Reference

| Document | Purpose |
|----------|---------|
| MYFARMAI_ORCHESTRATOR_ARCHITECTURE.md | Overall architecture |
| MYFARMAI_CAPABILITY_REGISTRY.md | Full capability registry (agents + skills + tools) |
| MYFARMAI_SKILL_TOOL_ROUTING.md | Routing rules mapping tasks to agents/skills |
| MYFARMAI_EXECUTION_AND_PERMISSION_POLICY.md | Permission tiers and execution policies |
| opencode.json | Authoritative agent configuration |