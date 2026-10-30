# MyFarmAI Skill & Tool Routing

**Document Version:** 1.0  
**Status:** Implemented  
**Date:** 2026-10-25  
**Component:** MyFarmAI-Orchestrator  

---

## 1. Overview

This document defines the routing rules that map tasks to appropriate capabilities (agents, skills, MCP servers, CLI tools). The SkillToolRouter implements a priority-based routing system that ensures tasks are handled by the most suitable available capability.

---

## 2. Routing Priority Hierarchy

```
Priority 1: Existing Skill (exact task type match)
    └── Skill loaded and validated for this specific task type

Priority 2: Existing Agent + Skill (agent with relevant skill)
    └── Agent has the skill loaded or can load it

Priority 3: Existing Agent Only (built-in capability)
    └── Agent's native capabilities cover the task

Priority 4: MCP Tool (direct MCP server call)
    └── MCP server provides required functionality

Priority 5: CLI Tool (installed command-line tool)
    └── System or project CLI tool can execute the task

Priority 6: New Skill Creation (Tier 3 approval required)
    └── Only when real capability gap exists and approved
```

---

## 3. Routing Rules Table

### 3.1 Backend Development

| Rule ID | Task Patterns | Primary Agent | Primary Skill | Fallback Agents | Fallback Skills | MCP Tools | Tier |
|---------|--------------|---------------|---------------|-----------------|-----------------|-----------|------|
| RT-BACKEND-API | api, endpoint, fastapi, route, handler, rest | backend-engineer | api-contract | fastapi-developer, backend-developer | openapi, pr-review | - | 1 |
| RT-BACKEND-DB | database, sql, migration, schema, postgresql, alembic | database-administrator | migration | postgres-pro, sql-pro, backend-engineer | sql-pro, migration | postgres (if enabled) | 1 |
| RT-BACKEND-AUTH | auth, authentication, authorization, oauth, jwt, session | backend-engineer | - | security-engineer, fastapi-developer | - | - | 3* |
| RT-BACKEND-TEST | test, pytest, unit-test, integration-test, backend | qa-reviewer | test-patterns | test-automator, backend-engineer | pytest, ci-pipeline | - | 1 |

*Security-sensitive: Requires security-engineer review

### 3.2 Frontend Development

| Rule ID | Task Patterns | Primary Agent | Primary Skill | Fallback Agents | Fallback Skills | MCP Tools | Tier |
|---------|--------------|---------------|---------------|-----------------|-----------------|-----------|------|
| RT-FRONTEND-COMP | component, ui, react, nextjs, tailwind, shadcn, page | frontend-engineer | shadcn | frontend-developer, react-specialist, nextjs-developer | ui-styling, frontend-design, vercel-composition-patterns | - | 1 |
| RT-FRONTEND-STATE | state, redux, zustand, context, hook, form | frontend-engineer | - | react-specialist, javascript-pro | - | - | 1 |
| RT-FRONTEND-ACCESS | accessibility, a11y, wcag, aria, screen-reader | accessibility-tester | - | frontend-engineer | ui-styling, design-system | - | 1 |
| RT-FRONTEND-BUILD | build, bundle, webpack, vite, turbo, deploy-web | deployment-engineer | deploy-to-vercel | devops-engineer, frontend-engineer | ci-pipeline, docker-build-strategies | - | 3 |

### 3.3 Android Development

| Rule ID | Task Patterns | Primary Agent | Primary Skill | Fallback Agents | Fallback Skills | MCP Tools | Tier |
|---------|--------------|---------------|---------------|-----------------|-----------------|-----------|------|
| RT-ANDROID-FEAT | android, mobile, expo, react-native, app, device, emulator | android-engineer | vercel-react-native-skills | mobile-developer, mobile-app-developer, flutter-expert | vercel-react-native-skills | - | 1 |
| RT-ANDROID-AUDIO | microphone, audio, speech, recording, voice | android-engineer | - | mobile-developer | vercel-react-native-skills | - | 1 |
| RT-ANDROID-BUILD | build-android, apk, aab, eas, store, deploy-mobile | deployment-engineer | deploy-to-vercel | devops-engineer, android-engineer | ci-pipeline | - | 3 |

### 3.4 AI/ML Model Integration

| Rule ID | Task Patterns | Primary Agent | Primary Skill | Fallback Agents | Fallback Skills | MCP Tools | Tier |
|---------|--------------|---------------|---------------|-----------------|-----------------|-----------|------|
| RT-AI-MODEL | model, ollama, inference, qwen, llm, embedding, personaplex | ai-ml-engineer | google-agents-cli-adk-code | llm-architect, machine-learning-engineer, nlp-engineer | google-agents-cli-workflow, prompt-engineer | - | 1 |
| RT-AI-PROMPT | prompt, template, few-shot, chain-of-thought, system-prompt | prompt-engineer | google-agents-cli-adk-code | ai-ml-engineer, llm-architect | google-agents-cli-workflow | - | 1 |
| RT-AI-EVAL | eval, evaluation, benchmark, metric, quality, regression | ai-ml-engineer | google-agents-cli-eval | machine-learning-engineer, data-scientist | google-agents-cli-eval, google-agents-cli-observability | - | 1 |

### 3.5 Research & Search

| Rule ID | Task Patterns | Primary Agent | Primary Skill | Fallback Agents | Fallback Skills | MCP Tools | Tier |
|---------|--------------|---------------|---------------|-----------------|-----------------|-----------|------|
| RT-RESEARCH | research, search, searxng, citation, extraction, web-search, source | research-engineer | searxng | search-specialist, data-researcher, scientific-literature-researcher | context7-mcp, webapp-testing | searxng (local) | 1 |
| RT-DOC-LOOKUP | documentation, library, api-reference, sdk, framework | research-engineer | context7-mcp | search-specialist, technical-writer | context7-mcp | context7 | 1 |

### 3.6 Security & Compliance

| Rule ID | Task Patterns | Primary Agent | Primary Skill | Fallback Agents | Fallback Skills | MCP Tools | Tier |
|---------|--------------|---------------|---------------|-----------------|-----------------|-----------|------|
| RT-SEC-AUDIT | security, audit, vulnerability, owasp, threat, penetration | security-engineer | gstack-cso | penetration-tester, security-auditor, compliance-auditor | dependency-audit, docker-destructive-guardrails | - | 3 |
| RT-SEC-SECRETS | secret, credential, password, token, key, rotation, vault | security-engineer | - | penetration-tester | gitleaks, dependency-audit | - | 3 |
| RT-SEC-COMPLY | compliance, gdpr, soc2, hipaa, license, legal | compliance-auditor | - | security-engineer, legal-advisor | - | - | 3 |

### 3.7 Quality Assurance

| Rule ID | Task Patterns | Primary Agent | Primary Skill | Fallback Agents | Fallback Skills | MCP Tools | Tier |
|---------|--------------|---------------|---------------|-----------------|-----------------|-----------|------|
| RT-QA-TEST | test, qa, quality, coverage, regression, e2e, integration | qa-reviewer | test-patterns | test-automator, test-writer, accessibility-tester | webapp-testing, ci-pipeline | - | 1 |
| RT-QA-LINT | lint, format, style, prettier, eslint, ruff, mypy, typecheck | qa-reviewer | - | frontend-engineer, backend-engineer | test-patterns, ci-pipeline | - | 1 |
| RT-QA-CONTRACT | contract, api-contract, openapi, schema, consumer-driven | qa-reviewer | api-contract | architect-reviewer, backend-engineer | api-contract, pr-review | - | 1 |

### 3.8 Deployment & Infrastructure

| Rule ID | Task Patterns | Primary Agent | Primary Skill | Fallback Agents | Fallback Skills | MCP Tools | Tier |
|---------|--------------|---------------|---------------|-----------------|-----------------|-----------|------|
| RT-DEPLOY | deploy, release, ship, production, staging, rollout | deployment-engineer | deploy-to-vercel | devops-engineer, platform-engineer | docker-build-strategies, docker-compose-patterns, ci-pipeline | - | 3 |
| RT-DOCKER | docker, dockerfile, container, image, build, compose | docker-expert | docker-build-strategies | deployment-engineer, devops-engineer | docker-compose-patterns, docker-optimize | - | 1 |
| RT-CI-CD | ci, cd, pipeline, workflow, github-actions, gitlab-ci | devops-engineer | ci-pipeline | deployment-engineer, platform-engineer | docker-build-strategies | - | 1 |
| RT-K8S | kubernetes, k8s, helm, cluster, pod, service, ingress | kubernetes-specialist | - | platform-engineer, devops-engineer | - | kubernetes (if enabled) | 3 |

### 3.9 Documentation

| Rule ID | Task Patterns | Primary Agent | Primary Skill | Fallback Agents | Fallback Skills | MCP Tools | Tier |
|---------|--------------|---------------|---------------|-----------------|-----------------|-----------|------|
| RT-DOC-WRITE | doc, readme, documentation, guide, tutorial, api-doc | docs-writer | document-generate | technical-writer, content-marketer | changelog-generate, adr-write | - | 1 |
| RT-DOC-ARCH | architecture-decision, adr, design-doc, trade-off, rationale | architect-reviewer | adr-write | docs-writer, platform-engineer | ce-pov, ce-doc-review | - | 1 |

### 3.10 Architecture & Design

| Rule ID | Task Patterns | Primary Agent | Primary Skill | Fallback Agents | Fallback Skills | MCP Tools | Tier |
|---------|--------------|---------------|---------------|-----------------|-----------------|-----------|------|
| RT-ARCH-REVIEW | architecture, design, review, pattern, trade-off, decision | architect-reviewer | adr-write | cloud-architect, platform-engineer, microservices-architect | ce-pov, ce-doc-review, ce-plan | - | 1 |
| RT-ARCH-CLOUD | cloud, aws, gcp, azure, infrastructure, landing-zone | cloud-architect | - | platform-engineer, azure-infra-engineer | - | aws (if enabled) | 3 |

### 3.11 Debugging & Diagnostics

| Rule ID | Task Patterns | Primary Agent | Primary Skill | Fallback Agents | Fallback Skills | MCP Tools | Tier |
|---------|--------------|---------------|---------------|-----------------|-----------------|-----------|------|
| RT-DEBUG | debug, error, fix, bug, crash, failure, stack-trace, log | debugger | ce-debug | error-detective, error-coordinator | systematic-debugging, error-triage | - | 1 |
| RT-ROOT-CAUSE | root-cause, rca, investigate, analyze, why, broken | error-detective | ce-debug | debugger, error-coordinator | systematic-debugging, investigating-superpowers | - | 1 |

### 3.12 Performance Optimization

| Rule ID | Task Patterns | Primary Agent | Primary Skill | Fallback Agents | Fallback Skills | MCP Tools | Tier |
|---------|--------------|---------------|---------------|-----------------|-----------------|-----------|------|
| RT-PERF | performance, optimize, slow, latency, benchmark, profile, memory, cpu | performance-engineer | performance-profile | vercel-optimize, database-optimizer | vercel-optimize, performance-optimization | - | 1 |
| RT-PERF-WEB | web-vitals, lighthouse, core-web-vitals, bundle-size, fcp, lcp | vercel-optimize | - | performance-engineer, frontend-engineer | vercel-optimize | - | 1 |

---

## 4. Routing Algorithm

```python
def route_task(task: Task) -> RoutingResult:
    # 1. Find matching routing rules
    matched_rules = [r for r in routing_rules if r.matches(task)]
    
    if not matched_rules:
        # General routing fallback
        return general_routing(task)
    
    # 2. Select best rule by match score
    best_rule = max(matched_rules, key=lambda r: r.match_score(task))
    
    # 3. Apply rule - find primary capability
    primary_agent = registry.get_usable_agent(best_rule.preferred_agent)
    primary_skill = registry.get_usable_skill(best_rule.preferred_skill)
    
    # 4. Fallback chain
    fallback_agents = []
    for fb in best_rule.fallback_agents or []:
        agent = registry.get_usable_agent(fb)
        if agent:
            fallback_agents.append(agent)
    
    fallback_skills = []
    for fb in best_rule.fallback_skills or []:
        skill = registry.get_usable_skill(fb)
        if skill:
            fallback_skills.append(skill)
    
    # 5. Add MCP tools if relevant
    mcp_tools = registry.get_usable_mcp_tools(task.constraints)
    
    # 6. Add CLI tools
    cli_tools = registry.get_usable_cli_tools(task.constraints)[:5]
    
    # 7. Check approval requirement
    requires_approval = best_rule.tier in (PermissionTier.TIER3_NEW, PermissionTier.TIER4_DESTRUCTIVE)
    
    return RoutingResult(
        task_id=task.id,
        primary_agent=primary_agent,
        primary_skill=primary_skill,
        fallback_agents=fallback_agents,
        fallback_skills=fallback_skills,
        mcp_tools=mcp_tools,
        cli_tools=cli_tools,
        matched_rules=[best_rule.name],
        match_score=best_rule.match_score(task),
        requires_approval=requires_approval,
        approval_reason=f"Requires {best_rule.tier.value} approval" if requires_approval else None
    )
```

---

## 5. Match Scoring

### Rule Match Score (0-1)
```
score = matched_patterns / total_patterns
```
- 1.0 = All patterns match
- 0.5 = Half patterns match
- Minimum threshold: 0.3

### Agent Selection Score (0-1)
```
score = (capability_match * 0.4) + (availability * 0.3) + (load_factor * 0.2) + (specialization * 0.1)
```
- capability_match: Required capabilities / agent capabilities
- availability: 1.0 if VERIFIED_WORKING, 0.5 if AVAILABLE, 0 otherwise
- load_factor: 1.0 - (current_load / max_load)
- specialization: 1.0 if exact match, 0.5 if partial, 0 otherwise

---

## 6. Tier Enforcement

### Tier 1 - Auto-Use (Existing Trusted)
- No approval needed
- Within granted permissions in opencode.json
- Example: Using backend-engineer for API work

### Tier 2 - Allowlisted Auto-Install
- Tool must be in allowlist
- Resource limits must permit
- Example: Installing gitleaks for secret scan

### Tier 3 - Explicit Approval Required
- New agent/skill/MCP/plugin
- Security-sensitive changes
- Deployment configuration changes
- Example: Adding new MCP server

### Tier 4 - Explicit Authorization + Safeguards
- Database migrations
- Secret rotation
- Production deployment
- Destructive operations
- Example: Running alembic migration

---

## 7. Routing Examples

### Example 1: "Add user authentication to backend API"
```
Patterns matched: auth, authentication, backend, api
Rule: RT-BACKEND-AUTH (Tier 3)
Primary: backend-engineer + security-engineer review
Fallback: security-engineer, fastapi-developer
MCP: None
Approval: Required (security-sensitive)
```

### Example 2: "Create responsive dashboard component"
```
Patterns matched: component, ui, react, responsive, dashboard
Rule: RT-FRONTEND-COMP (Tier 1)
Primary: frontend-engineer + shadcn skill
Fallback: react-specialist, nextjs-developer
Skills: ui-styling, frontend-design
Approval: Not required
```

### Example 3: "Optimize database query performance"
```
Patterns matched: database, query, performance, optimize, sql
Rule: RT-BACKEND-DB + RT-PERF
Primary: database-administrator + performance-engineer
Fallback: postgres-pro, sql-pro
Skills: migration, performance-profile
MCP: postgres (if enabled)
Approval: Not required (read-only analysis)
```

### Example 4: "Deploy to production with blue-green"
```
Patterns matched: deploy, production, blue-green, release
Rule: RT-DEPLOY (Tier 4)
Primary: deployment-engineer + deploy-to-vercel
Fallback: devops-engineer, platform-engineer
Skills: docker-build-strategies, ci-pipeline
Approval: Required (production deployment)
```

---

## 8. Custom Routing Rules

Custom rules can be added dynamically:

```python
from backend.app.orchestrator import RoutingRule, RoutingStrategy, PermissionTier, CapabilityType

custom_rule = RoutingRule(
    name="custom-agricultural-ml",
    task_patterns=["agricultural", "crop", "farm", "yield", "pest", "disease"],
    required_capabilities=["ai_ml", "agricultural"],
    preferred_capability_type=CapabilityType.AGENT,
    preferred_agent="ai-ml-engineer",
    preferred_skill="google-agents-cli-adk-code",
    fallback_agents=["research-engineer", "backend-engineer"],
    fallback_skills=["searxng", "context7-mcp"],
    strategy=RoutingStrategy.MOST_SPECIALIZED,
    tier=PermissionTier.TIER1_EXISTING
)

router.add_custom_rule(custom_rule)
```

---

## 9. Routing Validation

### Automated Checks
- Rule coverage: All capability areas have at least one rule
- No duplicate rule names
- All referenced agents/skills exist in registry
- Fallback chains are valid (no circular references)
- Tier assignments consistent with security policy

### Manual Review Triggers
- New capability area added
- Agent/skill deprecated
- Security policy changes
- Hardware constraints change

---

## 10. Cross-Reference

| Document | Purpose |
|----------|---------|
| MYFARMAI_ORCHESTRATOR_ARCHITECTURE.md | Overall architecture |
| MYFARMAI_AGENT_TEAM_CATALOG.md | Agent capabilities |
| MYFARMAI_CAPABILITY_REGISTRY.md | Full capability inventory |
| MYFARMAI_EXECUTION_AND_PERMISSION_POLICY.md | Permission tiers |
| backend/app/orchestrator/router.py | Implementation |
| .opencode/skills/myfarmai-orchestrate/SKILL.md | Skill usage |