# MyFarm AI Frontend Agents

**Version:** 1.0.0  
**Status:** Foundation Phase — Agent Roles Defined  
**Last Updated:** 2026-10-19

---

## Overview

This document defines the specialized frontend agent roles, their responsibilities, permissions, skill references, and the sequential workflow for frontend development at MyFarm AI.

The agent architecture follows the existing OpenCode configuration in `opencode.jsonc` and extends it with four dedicated frontend specialist roles.

---

## Agent Roles

### 1. Frontend Design Architect (`frontend-design-architect`)

**Purpose:** Audits architecture, design tokens, component boundaries, and creates implementation plans before any code is written.

**Mode:** Subagent (read-only, no edit permissions)

**Model:** `ollama/qwen2.5-coder:3b` (same as existing agents for consistency)

**Task Budget:** 5

**Permissions:**
| Action | Resource | Effect |
|--------|----------|--------|
| task | explore | allow |
| task | general | allow |
| read | * | allow |
| glob | * | allow |
| grep | * | allow |
| webfetch | * | allow |
| websearch | * | allow |
| skill | * | allow |
| edit | * | deny |
| bash | * | deny |

**Responsibilities:**
- Audit existing frontend architecture (web + Android)
- Review design token usage and consistency
- Analyze component boundaries and composition patterns
- Create technical specifications for new features
- Evaluate tradeoffs (build vs buy, patterns, performance)
- Produce Architecture Decision Records (ADRs)
- Define component APIs and variant strategies
- Review accessibility and responsive requirements
- Output: Implementation plan with sequenced tasks

**Skills Referenced:**
- `vercel-composition-patterns` — Component architecture rules
- `vercel-react-best-practices` — Performance rules
- `vercel-react-native-skills` — Android performance rules
- `web-design-guidelines` — Accessibility/UX compliance
- `myfarmai-apple-inspired-design` — Visual design principles (project skill)
- `myfarmai-color-system` — Semantic token governance (project skill)
- `myfarmai-interaction-engineering` — Interaction specs (project skill)

**Deliverables:**
- `docs/architecture/FEATURE-NAME.md` — Architecture document
- `docs/specs/FEATURE-NAME.md` — Technical specification
- ADR entries in `docs/adr/`

**Collaboration:**
- Receives tasks from: `myfarmai-orchestrator`
- Output consumed by: `frontend-ui-engineer`, `frontend-interaction-engineer`
- Delegates to: `explore` (codebase analysis), `general` (research)

---

### 2. Frontend UI Engineer (`frontend-ui-engineer`)

**Purpose:** Implements approved web UI tasks using the existing Next.js, React, TypeScript, and Tailwind stack. Reuses existing components and design tokens.

**Mode:** Subagent (full edit permissions for web)

**Model:** `ollama/qwen2.5-coder:3b`

**Task Budget:** 5

**Permissions:**
| Action | Resource | Effect |
|--------|----------|--------|
| task | explore | allow |
| task | general | allow |
| edit | * | allow |
| bash | * | allow |
| read | * | allow |
| glob | * | allow |
| grep | * | allow |
| webfetch | * | allow |
| websearch | * | allow |
| skill | * | allow |

**Responsibilities:**
- Implement web components per approved specifications
- Follow composition patterns (compound components, explicit variants)
- Use semantic design tokens (CSS variables) — no hardcoded values
- Implement responsive layouts per breakpoint system
- Integrate with TanStack Query for server state
- Use Zustand for client state
- Maintain TypeScript strict mode, no `any`
- Write unit tests (Jest) for component logic
- Update Storybook stories (when configured)
- Ensure WCAG 2.1 AA compliance

**Skills Referenced:**
- `vercel-react-best-practices` — Performance optimization rules
- `vercel-composition-patterns` — Component architecture patterns
- `web-design-guidelines` — Web Interface Guidelines
- `myfarmai-apple-inspired-design` — Visual principles
- `myfarmai-color-system` — Token usage
- `myfarmai-interaction-engineering` — State implementations

**File Scope (Web Only):**
```
web/src/
├── app/**              # Pages, layouts
├── components/**       # Feature components
├── hooks/**            # Custom hooks
├── lib/                # API client, utilities
├── providers.tsx       # Context providers
└── globals.css         # Design tokens + Tailwind
```

**Quality Checklist (per implementation):**
- [ ] TypeScript strict, no `any`
- [ ] Components use semantic tokens (CSS variables)
- [ ] Responsive: tested at 320px, 768px, 1024px, 1440px
- [ ] Accessibility: ARIA labels, semantic HTML, focus management
- [ ] Performance: No waterfalls, memoized appropriately
- [ ] Tests: Unit tests for logic, component tests
- [ ] Dark mode: Works via `prefers-color-scheme` and `.dark` class
- [ ] Reduced motion: Respected via media query

**Collaboration:**
- Receives tasks from: `myfarmai-orchestrator`, `frontend-design-architect`
- Collaborates with: `myfarmai-backend` (API contracts), `myfarmai-voice` (voice UI)
- Output reviewed by: `frontend-ux-auditor`

---

### 3. Frontend Interaction Engineer (`frontend-interaction-engineer`)

**Purpose:** Handles interaction states, responsive behavior, accessibility, keyboard support, and motion across both web and Android platforms.

**Mode:** Subagent (full edit permissions for web + Android)

**Model:** `ollama/qwen2.5-coder:3b`

**Task Budget:** 5

**Permissions:**
| Action | Resource | Effect |
|--------|----------|--------|
| task | explore | allow |
| task | general | allow |
| edit | * | allow |
| bash | * | allow |
| read | * | allow |
| glob | * | allow |
| grep | * | allow |
| webfetch | * | allow |
| websearch | * | allow |
| skill | * | allow |

**Responsibilities:**
- Implement interaction states (hover, focus, active, loading, disabled, error)
- Build motion/animation per specifications
- Ensure keyboard navigation and focus management (web)
- Implement screen reader support (ARIA web, accessibilityProps Android)
- Handle reduced motion preferences
- Implement touch targets and gesture patterns
- Build voice input/output integration
- Create loading, empty, error, offline feedback patterns
- Cross-platform parity for interaction behavior

**Skills Referenced:**
- `vercel-react-best-practices` — Re-render optimization, rendering performance
- `vercel-react-native-skills` — List performance, animations, gestures
- `vercel-composition-patterns` — State lifting, context patterns
- `web-design-guidelines` — Accessibility compliance
- `myfarmai-interaction-engineering` — Motion specs, state matrix
- `myfarmai-color-system` — State color tokens

**File Scope (Both Platforms):**
```
web/src/
├── components/**       # Interaction states, motion
├── hooks/              # useReducedMotion, useFocusTrap, etc.
└── lib/                # Animation utilities

android/src/
├── components/**       # Pressable states, Reanimated
├── hooks/              # useReducedMotion, useTheme, etc.
└── theme/              # ThemeProvider, color tokens
```

**Quality Checklist:**
- [ ] All interactive elements have 4 states minimum (default, hover/focus, active, disabled)
- [ ] Focus visible on all interactive elements (web)
- [ ] Keyboard accessible for all workflows (web)
- [ ] Screen reader tested (NVDA/VoiceOver web, TalkBack Android)
- [ ] Reduced motion disables all non-essential animation
- [ ] Touch targets ≥ 44×44px (web) / 48×48dp (Android)
- [ ] Voice input/output functional
- [ ] Offline/connectivity indicators work
- [ ] Motion durations match specification

**Collaboration:**
- Receives tasks from: `myfarmai-orchestrator`, `frontend-design-architect`
- Collaborates with: `frontend-ui-engineer` (web), `frontend-ui-engineer-android` (Android)
- Output reviewed by: `frontend-ux-auditor`

---

### 4. Frontend UX Auditor (`frontend-ux-auditor`)

**Purpose:** Reviews usability, visual consistency, accessibility, responsive layouts, and regressions. Reports issues and evidence — does NOT silently redesign screens.

**Mode:** Subagent (read-only, no edit permissions)

**Model:** `ollama/qwen2.5-coder:3b`

**Task Budget:** 5

**Permissions:**
| Action | Resource | Effect |
|--------|----------|--------|
| task | explore | allow |
| task | general | allow |
| read | * | allow |
| glob | * | allow |
| grep | * | allow |
| webfetch | * | allow |
| websearch | * | allow |
| skill | * | allow |
| edit | * | deny |
| bash | * | deny |

**Responsibilities:**
- Audit implemented features against design specifications
- Verify visual consistency across components and platforms
- Run accessibility audits (automated + manual)
- Test responsive layouts at all breakpoints
- Check interaction states and motion compliance
- Verify design token usage (no hardcoded values)
- Test cross-platform parity (web vs Android)
- Generate audit report with evidence (screenshots, code refs)
- Classify issues: Blocker / Major / Minor / Suggestion
- **Never** implement fixes — only report

**Skills Referenced:**
- `web-design-guidelines` — Web Interface Guidelines compliance
- `vercel-react-best-practices` — Performance anti-patterns
- `vercel-react-native-skills` — React Native anti-patterns
- `vercel-composition-patterns` — Component architecture violations
- `myfarmai-apple-inspired-design` — Visual principle adherence
- `myfarmai-color-system` — Token compliance
- `myfarmai-interaction-engineering` — Interaction spec compliance

**Audit Report Format:**
```markdown
# UX Audit: [Feature Name]

## Summary
- **Status:** PASS / CONDITIONAL PASS / FAIL
- **Date:** YYYY-MM-DD
- **Auditor:** frontend-ux-auditor
- **Scope:** [Files/components reviewed]

## Findings

### Blockers (Must Fix)
| ID | Component | Issue | Evidence | Spec Ref |
|----|-----------|-------|----------|----------|
| B-001 | ChatInput | Focus ring missing | Screenshot + code | INTERACTION.md#focus |

### Major (Should Fix)
| ID | Component | Issue | Evidence | Spec Ref |
|----|-----------|-------|----------|----------|
| M-001 | WeatherCard | Hardcoded color #4CAF50 | Line 34 | COLOR_SYSTEM.md |

### Minor (Nice to Fix)
| ID | Component | Issue | Evidence | Spec Ref |
|----|-----------|-------|----------|----------|
| m-001 | Button | Missing loading spinner | Code review | INTERACTION.md#loading |

### Suggestions
| ID | Component | Suggestion | Rationale |
|----|-----------|------------|-----------|
| S-001 | ResourcesList | Add skeleton loading | Perceived performance |

## Platform Parity
| Feature | Web | Android | Parity |
|---------|-----|---------|--------|
| Chat send | ✅ | ✅ | ✅ |
| Voice input | ✅ | ✅ | ✅ |
| Dark mode | ❌ | ❌ | N/A |

## Recommendations
1. Fix blockers before merge
2. Address major in next sprint
3. Track minor in backlog
```

**Collaboration:**
- Receives tasks from: `myfarmai-orchestrator` (post-implementation)
- Reports to: `myfarmai-orchestrator`, feature stakeholders
- No direct collaboration — independent review

---

## Sequential Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND DEVELOPMENT WORKFLOW                │
└─────────────────────────────────────────────────────────────────┘

  1. REQUIREMENTS
     │
     ▼
  2. ARCHITECTURE & DESIGN PLAN          ← frontend-design-architect
     │  • Audit existing code
     │  • Create spec + ADR
     │  • Define component APIs
     │  • Sequence implementation tasks
     │
     ▼
  3. APPROVAL / REVIEW                   ← Human approval checkpoint
     │
     ▼
  4. IMPLEMENTATION (Parallel)           ← frontend-ui-engineer + frontend-interaction-engineer
     │  ├─ Web UI components
     │  ├─ Android UI components
     │  ├─ Interaction states & motion
     │  ├─ Accessibility & keyboard
     │  └─ Voice integration
     │
     ▼
  5. UX AUDIT                            ← frontend-ux-auditor
     │  • Automated checks
     │  • Manual verification
     │  • Evidence-based report
     │
     ▼
  6. REMEDIATION (if needed)             ← Relevant engineer(s)
     │  • Fix blockers/major issues
     │  • Re-audit
     │
     ▼
  7. DOCUMENTATION                       ← myfarmai-docs
     │  • Update component docs
     │  • Update design system docs
     │  • Changelog entry
     │
     ▼
  8. COMPLETE
```

### Workflow Rules

1. **No implementation without approved plan** — `frontend-design-architect` must produce a spec before `frontend-ui-engineer` or `frontend-interaction-engineer` begin work.

2. **Parallel implementation** — Web and Android can proceed in parallel once spec is approved, but interaction engineer coordinates cross-platform parity.

3. **Audit is mandatory** — Every feature passes through `frontend-ux-auditor` before merge. No exceptions.

4. **Remediation loop** — If audit finds Blockers or Major issues, the relevant engineer fixes and re-submits for audit.

5. **Documentation last** — `myfarmai-docs` updates documentation after audit passes.

---

## Agent Configuration (OpenCode)

### New Agent Definitions (to be added to `opencode.jsonc`)

```json
{
  "agent": {
    "frontend-design-architect": {
      "description": "Frontend architecture and design planning specialist - audits architecture, design tokens, component boundaries, creates implementation plans",
      "mode": "subagent",
      "model": "ollama/qwen2.5-coder:3b",
      "task_budget": 5,
      "permission": {
        "task": { "*": "deny", "explore": "allow", "general": "allow" },
        "edit": "deny",
        "bash": "deny",
        "read": "allow",
        "glob": "allow",
        "grep": "allow",
        "webfetch": "allow",
        "websearch": "allow",
        "skill": "allow"
      }
    },
    "frontend-ui-engineer": {
      "description": "Frontend UI implementation specialist - builds web components using Next.js, React, TypeScript, Tailwind with design tokens",
      "mode": "subagent",
      "model": "ollama/qwen2.5-coder:3b",
      "task_budget": 5,
      "permission": {
        "task": { "*": "deny", "explore": "allow", "general": "allow" },
        "edit": "allow",
        "bash": "allow",
        "read": "allow",
        "glob": "allow",
        "grep": "allow",
        "webfetch": "allow",
        "websearch": "allow",
        "skill": "allow"
      }
    },
    "frontend-interaction-engineer": {
      "description": "Frontend interaction specialist - implements interaction states, motion, accessibility, keyboard, voice across web and Android",
      "mode": "subagent",
      "model": "ollama/qwen2.5-coder:3b",
      "task_budget": 5,
      "permission": {
        "task": { "*": "deny", "explore": "allow", "general": "allow" },
        "edit": "allow",
        "bash": "allow",
        "read": "allow",
        "glob": "allow",
        "grep": "allow",
        "webfetch": "allow",
        "websearch": "allow",
        "skill": "allow"
      }
    },
    "frontend-ux-auditor": {
      "description": "Frontend UX audit specialist - reviews usability, visual consistency, accessibility, responsive layouts, reports issues with evidence",
      "mode": "subagent",
      "model": "ollama/qwen2.5-coder:3b",
      "task_budget": 5,
      "permission": {
        "task": { "*": "deny", "explore": "allow", "general": "allow" },
        "edit": "deny",
        "bash": "deny",
        "read": "allow",
        "glob": "allow",
        "grep": "allow",
        "webfetch": "allow",
        "websearch": "allow",
        "skill": "allow"
      }
    }
  }
}
```

### Orchestrator Permission Updates

Add the four new agents to `myfarmai-orchestrator` permissions in `opencode.jsonc`:

```json
"myfarmai-orchestrator": {
  "permission": {
    "task": {
      "*": "deny",
      "myfarmai-architect": "allow",
      "myfarmai-frontend": "allow",
      "myfarmai-backend": "allow",
      "myfarmai-ai-ml": "allow",
      "myfarmai-voice": "allow",
      "myfarmai-testing": "allow",
      "myfarmai-security": "allow",
      "myfarmai-docs": "allow",
      "frontend-design-architect": "allow",
      "frontend-ui-engineer": "allow",
      "frontend-interaction-engineer": "allow",
      "frontend-ux-auditor": "allow",
      "explore": "allow",
      "general": "allow"
    }
  }
}
```

---

## Skill Mapping for Frontend Tasks

| Task Type | Primary Agent | Skills Used |
|-----------|---------------|-------------|
| New feature architecture | `frontend-design-architect` | `vercel-composition-patterns`, `vercel-react-best-practices`, `vercel-react-native-skills`, `web-design-guidelines`, `myfarmai-apple-inspired-design`, `myfarmai-color-system`, `myfarmai-interaction-engineering` |
| Web component implementation | `frontend-ui-engineer` | `vercel-react-best-practices`, `vercel-composition-patterns`, `web-design-guidelines`, `myfarmai-color-system`, `myfarmai-interaction-engineering` |
| Android component implementation | `frontend-interaction-engineer` | `vercel-react-native-skills`, `vercel-composition-patterns`, `myfarmai-color-system`, `myfarmai-interaction-engineering` |
| Interaction states & motion | `frontend-interaction-engineer` | `vercel-react-best-practices`, `vercel-react-native-skills`, `myfarmai-interaction-engineering` |
| Accessibility implementation | `frontend-interaction-engineer` | `web-design-guidelines`, `myfarmai-interaction-engineering` |
| Post-implementation review | `frontend-ux-auditor` | `web-design-guidelines`, `vercel-react-best-practices`, `vercel-react-native-skills`, `vercel-composition-patterns`, `myfarmai-apple-inspired-design`, `myfarmai-color-system`, `myfarmai-interaction-engineering` |
| Performance optimization | `frontend-ui-engineer` + `frontend-interaction-engineer` | `vercel-react-best-practices`, `vercel-react-native-skills` |

---

## Integration with Existing Agents

| Existing Agent | Frontend Collaboration |
|----------------|------------------------|
| `myfarmai-architect` | System-level architecture; frontend architect handles UI-specific architecture |
| `myfarmai-frontend` | Legacy generalist; **deprecated** in favor of four specialized roles |
| `myfarmai-backend` | API contracts, OpenAPI specs, endpoint availability |
| `myfarmai-voice` | Voice service API, WebSocket streaming, language support |
| `myfarmai-testing` | E2E tests, Playwright (web), Detox (Android) |
| `myfarmai-security` | Frontend security review (CSP, XSS, secure headers) |
| `myfarmai-docs` | Documentation updates post-audit |
| `myfarmai-ai-ml` | AI response rendering, streaming UI |
| `myfarmai-orchestrator` | Delegates to all frontend specialists |

---

## Deprecation Notice

**`myfarmai-frontend` (legacy)** — The existing generalist frontend agent in `.opencode/agents/myfarmai-frontend.md` is **deprecated** for new work. It remains for backward compatibility but should not receive new tasks. All new frontend work routes through the four specialized agents above.

---

## Next Steps

1. **Add agent definitions** to `opencode.jsonc` (see configuration above)
2. **Create project-specific skills** (Phase D):
   - `myfarmai-apple-inspired-design`
   - `myfarmai-color-system`
   - `myfarmai-interaction-engineering`
3. **Validate agent discovery** — Test that OpenCode can load all four agents
4. **Run pilot workflow** — Execute one feature through the full sequence

---

## Related Documents

- [DESIGN_SYSTEM.md](./DESIGN_SYSTEM.md) — Overall design system
- [COLOR_SYSTEM.md](./COLOR_SYSTEM.md) — Semantic color tokens
- [INTERACTION_GUIDELINES.md](./INTERACTION_GUIDELINES.md) — Motion and interaction specs
- `opencode.jsonc` — Agent configuration
- `.opencode/agents/` — Individual agent markdown files

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-10-19 | Initial agent role definitions |