# Agent Skill Routing Matrix

**Project:** MyFarmAI  
**Generated:** 2026-10-25  
**Source:** awesome-opencode (weisser-dev/awesome-opencode) + custom MyFarmAI agents

---

## Overview

This matrix maps task types to the lead orchestrator, specialist agents, relevant skills, MCP tools, and verification criteria for the MyFarmAI project.

---

## Routing Matrix

| Task Category | Task Type | Lead Agent | Specialist Agent | Primary Skill(s) | MCP Tools | Verification Criteria |
|---------------|-----------|------------|------------------|------------------|-----------|----------------------|
| **Backend Development** | FastAPI endpoint creation | myfarmai-orchestrator | backend-engineer | api-contract, test-patterns | filesystem, git | pytest passes, OpenAPI spec valid |
| | Database migration | myfarmai-orchestrator | backend-engineer | migration, docker-optimize | filesystem, git, postgres (disabled) | Migration runs, no data loss |
| | Authentication/Authorization | myfarmai-orchestrator | backend-engineer + security-engineer | api-contract, pr-review | filesystem, git | Auth flow works, security review PASS |
| | Performance optimization | myfarmai-orchestrator | backend-engineer + performance-engineer | performance-profile, docker-optimize | filesystem, git | Benchmarks improved, no regressions |
| **Frontend Development** | Next.js page/component | myfarmai-orchestrator | frontend-engineer | test-patterns, ui-styling | filesystem, git, playwright | Typecheck, lint, build, tests pass |
| | Accessibility compliance | myfarmai-orchestrator | frontend-engineer + accessibility-tester | ui-ux-pro-max, web-design-guidelines | filesystem, playwright | WCAG 2.1 AA verified |
| | Responsive design | myfarmai-orchestrator | frontend-engineer | ui-ux-pro-max, design-system | filesystem, playwright | Mobile/desktop breakpoints work |
| **Mobile Development** | Expo/React Native feature | myfarmai-orchestrator | android-engineer | test-patterns, env-setup | filesystem, git | Typecheck, lint pass, builds on device |
| | Microphone/Audio integration | myfarmai-orchestrator | android-engineer | env-setup, docker-optimize | filesystem, git | Audio records/plays on device |
| **AI/ML Integration** | Ollama model deployment | myfarmai-orchestrator | ai-ml-engineer | docker-optimize, env-setup | filesystem, git | Model loads, inference works |
| | PersonaPlex feasibility | myfarmai-orchestrator | ai-ml-engineer + research-engineer | research-analyst, llm-architect | filesystem, git, gh-grep | Feasibility report with evidence |
| | Model selection/benchmarking | myfarmai-orchestrator | ai-ml-engineer | performance-profile, dependency-audit | filesystem, git, gh-grep | Benchmark results documented |
| **Research & Documentation** | Web search & extraction | myfarmai-orchestrator | research-engineer | error-triage, adr-write | gh-grep, searxng (local) | Citations verified, sources ranked |
| | Architecture Decision Records | myfarmai-orchestrator | research-engineer + architect-reviewer | adr-write, api-contract | filesystem, git | ADR follows Nygard template |
| | Technical documentation | myfarmai-orchestrator | docs-writer | changelog-generate, git-release | filesystem, git | Docs match implementation |
| **Security & Quality** | Security audit | myfarmai-orchestrator | security-engineer | pr-review, dependency-audit | filesystem, git, gh-grep | No critical vulnerabilities |
| | Penetration testing | myfarmai-orchestrator | penetration-tester | incident-postmortem, error-triage | filesystem, git | Findings documented, remediated |
| | Code review | myfarmai-orchestrator | code-reviewer | pr-review, test-patterns | filesystem, git | Review checklist PASS |
| | Dependency audit | myfarmai-orchestrator | dependency-manager | dependency-audit, changelog-generate | filesystem, git, gh-grep | CVE report, license compliance |
| **Testing & QA** | Unit/Integration tests | myfarmai-orchestrator | qa-reviewer | test-patterns, test-automator | filesystem, git, playwright | Coverage targets met |
| | E2E browser testing | myfarmai-orchestrator | qa-reviewer | test-patterns, test-automator | playwright, filesystem | Critical paths verified |
| | Regression testing | myfarmai-orchestrator | qa-reviewer | test-patterns, changelog-generate | filesystem, git | No regressions detected |
| **Release & Deployment** | Release preparation | myfarmai-orchestrator | release-coordinator | git-release, changelog-generate | filesystem, git | Version bumped, changelog updated |
| | Quality gate execution | myfarmai-orchestrator | release-coordinator + qa-reviewer | pr-review, ci-pipeline | filesystem, git, github | All gates PASS |
| | Deployment verification | myfarmai-orchestrator | release-coordinator + devops-engineer | deploy, docker-optimize | filesystem, git, docker | Health checks pass |

---

## Skill-to-Agent Mapping

### Core MyFarmAI Specialist Agents

| Agent | Primary Skills | Secondary Skills |
|-------|---------------|------------------|
| backend-engineer | api-contract, test-patterns, migration | docker-optimize, performance-profile |
| frontend-engineer | test-patterns, ui-styling, ui-ux-pro-max | design-system, accessibility-tester |
| android-engineer | test-patterns, env-setup | docker-optimize, performance-profile |
| ai-ml-engineer | docker-optimize, env-setup, performance-profile | dependency-audit, llm-architect |
| research-engineer | adr-write, error-triage | research-analyst, search-specialist |
| security-engineer | pr-review, dependency-audit | incident-postmortem, penetration-tester |
| qa-reviewer | test-patterns, test-automator | changelog-generate, performance-profile |
| release-coordinator | git-release, changelog-generate, pr-review | ci-pipeline, deploy |

### Supporting Agents (from awesome-opencode)

| Agent | Skills | Use Case |
|-------|--------|----------|
| architect-reviewer | adr-write, api-contract | Architecture decisions |
| performance-engineer | performance-profile, docker-optimize | Performance bottlenecks |
| penetration-tester | incident-postmortem, error-triage | Security testing |
| dependency-manager | dependency-audit, changelog-generate | Dependency management |
| code-reviewer | pr-review, test-patterns | Code quality |
| devops-engineer | deploy, ci-pipeline, docker-optimize | CI/CD pipelines |
| test-automator | test-patterns, test-automator | Test framework design |
| llm-architect | performance-profile, dependency-audit | LLM system design |

---

## MCP Tool Availability

| MCP Server | Status | Available To | Use Cases |
|------------|--------|--------------|-----------|
| gh-grep | ✅ Active | All agents | Code search, pattern finding |
| sentry | ✅ Active | All agents | Error monitoring |
| atlassian | ✅ Active | All agents | Jira/Confluence integration |
| linear | ⚠️ Disabled | - | Linear API (needs key) |
| redis | ⚠️ Disabled | - | Redis access (needs URL) |
| postgres | ⚠️ Disabled | - | PostgreSQL (needs URL) |
| kubernetes | ⚠️ Disabled | - | K8s management |
| puppeteer | ⚠️ Disabled | - | Browser automation (use playwright) |
| aws | ⚠️ Disabled | - | AWS management |
| axiom | ⚠️ Disabled | - | Axiom logging (needs token) |

**Recommended additions for MyFarmAI:**
- `context7` - Library documentation (already in global config)
- `playwright` - Browser testing (available via gstack)
- `filesystem` - Local file access (built-in)
- `git` - Git operations (built-in)

---

## Delegation Rules

1. **Lead Orchestrator Only** creates tasks and delegates to specialists
2. **Specialists** execute assigned tasks and report findings
3. **No recursive delegation** - specialists don't delegate to other specialists
4. **Parallel execution** for independent read-only tasks
5. **Sequential execution** for dependent or write-heavy tasks
6. **Security gate** - security-engineer reviews all security-sensitive changes
7. **Quality gate** - qa-reviewer verifies all implementations
8. **Documentation gate** - docs updated before task completion

---

## Verification Checklist per Task

- [ ] Task ID assigned (format: MF-<phase>-<seq>)
- [ ] Specialist agent selected and invoked
- [ ] Required skills identified and available
- [ ] MCP tools accessible
- [ ] Dependencies resolved
- [ ] Tests executed and passing
- [ ] Security review (if applicable)
- [ ] Documentation updated
- [ ] Git diff reviewed
- [ ] No secrets in changes
- [ ] Evidence recorded

---

## Notes

- All 15 awesome-opencode skills are installed in `.opencode/skills/`
- All 108 awesome-opencode agents are available in `.opencode/agents/`
- 7 custom MyFarmAI agents extend the base capabilities
- Compound Engineering plugin provides additional orchestration skills
- gstack skills available globally via `~/.config/opencode/skills/`