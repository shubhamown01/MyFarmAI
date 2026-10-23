# MyFarmAI OpenCode Agent Team

## Overview

This document describes the professional, reusable OpenCode agent team configured for the MyFarmAI repository. The team enables delegated development while preserving project safety, documentation standards, free/open-source preferences, and existing work.

## Agent Roster

| Agent | Mode | Description | Primary Scope |
|-------|------|-------------|---------------|
| **myfarmai-orchestrator** | Primary | Coordinates project-wide development, reads roadmaps, delegates to specialists, integrates results, updates documentation | All phases, cross-cutting |
| **backend-engineer** | Subagent | FastAPI, Python, API contracts, SQLAlchemy, PostgreSQL, auth, migrations, tests | `backend/**` |
| **frontend-engineer** | Subagent | Next.js, React, Tailwind, accessibility, responsive design, API integration | `web/**` |
| **android-engineer** | Subagent | Expo/React Native, API base URL, emulator/device, microphone/audio, builds | `android/**` |
| **ai-ml-engineer** | Subagent | Ollama gateway, Qwen models, PersonaPlex feasibility, benchmarks, model storage | `backend/app/services/ollama.py`, `chat.py` |
| **research-engineer** | Subagent | SearXNG, web search, extraction, citations, SSRF protection, agricultural workflows | `backend/app/services/research*.py`, `infra/searxng/**` |
| **security-engineer** | Subagent (read-only) | Auth audits, secrets, PII, API/upload security, threat modeling, Phase 0 remediation | Review only |
| **qa-reviewer** | Subagent (test execution) | Unit/integration tests, API contracts, regression, frontend/Android builds, release readiness | Test execution + verification |
| **release-coordinator** | Subagent (read-only) | Diff review, quality-gate execution, documentation-impact check, integration readiness | Review + verification |

## Configuration Files

| File | Purpose |
|------|---------|
| `.opencode/agents/myfarmai-orchestrator.md` | Orchestrator definition |
| `.opencode/agents/backend-engineer.md` | Backend specialist |
| `.opencode/agents/frontend-engineer.md` | Frontend specialist |
| `.opencode/agents/android-engineer.md` | Android specialist |
| `.opencode/agents/ai-ml-engineer.md` | AI/ML specialist |
| `.opencode/agents/research-engineer.md` | Research specialist |
| `.opencode/agents/security-engineer.md` | Security reviewer (read-only) |
| `.opencode/agents/qa-reviewer.md` | QA verification |
| `.opencode/agents/release-coordinator.md` | Release/integration verification |
| `opencode.json` | Agent registration, default agent, task permissions, subagent depth |
| `docs/AGENT_TEAM_DELEGATION.md` | Delegation workflow and handoff protocol |
| `docs/ADK_EVALUATION.md` | Google ADK adoption decision |
| `docs/PERSONAPLEX_BOUNDARY.md` | Voice service boundary |

## Quick Start

### 1. Verify Configuration

```bash
cd /data/MyFarmAI
opencode debug config  # Shows resolved config including agents
```

### 2. Invoke Orchestrator

In OpenCode TUI/CLI, the **myfarmai-orchestrator** is the default agent (press Tab to cycle).

```
@myfarmai-orchestrator Start Phase 1 backend foundation per roadmap
```

### 3. Direct Specialist Invocation

```
@backend-engineer Fix the 7 clean-DB test failures in test_chat.py
@frontend-engineer Fix TypeScript errors in Card.tsx and providers.tsx
@android-engineer Fix relative API URLs to use absolute base URL
@security-engineer Review current .gitignore for backend/data/
@qa-reviewer Run full backend test suite and report results
```

## Delegation Workflow

See `docs/AGENT_TEAM_DELEGATION.md` for full protocol.

**Summary**:
1. Orchestrator reads roadmaps → creates Task Cards (MF-<phase>-<seq>)
2. Delegates to specialist via `@agent-name`
3. Specialist implements → runs verification commands
4. Security gate (if applicable) → `@security-engineer`
5. Quality gate → `@qa-reviewer`
6. Orchestrator integrates → updates docs → next task

## Phase 0 Context (Preserved)

Critical findings from `docs/roadmaps/phase-00/` that all agents must respect:

- **Two SQLite DBs**: `backend/data/app.db` (122 convos) and `data/app.db` (35 convos) — canonical undecided
- **7 test failures**: Clean-DB run fails in `test_chat.py` — fix test isolation
- **Voice service**: Unauthenticated on `0.0.0.0:8001`, unbounded upload, runs as root
- **SearXNG secret**: Hardcoded in `infra/searxng/config/settings.yml` — rotate, env-only
- **No auth**: All endpoints public — required before network exposure
- **Rate limit bypass**: `X-Forwarded-For` spoofing — trusted proxy only
- **Hardware**: 7 GiB RAM, 2 GiB VRAM, ~5 GB free on `/`
- **Licensing**: Open-Meteo non-commercial, SearXNG AGPL-3.0 — decisions needed
- **Preserve**: All uncommitted/untracked work

## Permissions Model

| Agent | Edit | Shell | Task Delegation | Web Fetch |
|-------|------|-------|-----------------|-----------|
| myfarmai-orchestrator | allow | allow | myfarmai-*, specialists, explore | allow |
| backend-engineer | backend/**, tests/**, alembic/** | backend cmds | deny | deny |
| frontend-engineer | web/**, docs/frontend/** | web cmds | deny | deny |
| android-engineer | android/**, docs/integration/ANDROID* | android cmds | deny | deny |
| ai-ml-engineer | ollama.py, chat.py, config.py | ollama, curl | deny | deny |
| research-engineer | research*.py, infra/searxng/** | curl | deny | deny |
| security-engineer | **deny** | grep, git diff, cat | deny | deny |
| qa-reviewer | test files only | test cmds | deny | deny |

## Verification Commands

### Backend
```bash
cd /data/MyFarmAI/backend
pytest -v --tb=short
ruff check app tests
mypy --strict app
```

### Frontend
```bash
cd /data/MyFarmAI/web
npm run typecheck
npm test -- --runInBand
npm run lint
npm run build
npx playwright test
```

### Android
```bash
cd /data/MyFarmAI/android
npm run typecheck
npm run lint
npm test
```

## Model Provider Configuration

- **Default**: Uses globally configured OpenCode model
- **Local preference**: Ollama (`qwen3:4b`) for backend inference
- **No paid APIs**: No OpenAI, Anthropic, Gemini keys required
- **Model storage**: `/data/AI-Models/` (outside Git)

## ADK Decision

**Deferred.** See `docs/ADK_EVALUATION.md`.

Current FastAPI + direct Ollama meets Phase 0–4 needs. ADK adds complexity without benefit. Re-evaluate at Phase 6 if research orchestration demands it.

## PersonaPlex Boundary

**Separate service.** See `docs/PERSONAPLEX_BOUNDARY.md`.

- Weights not downloaded (HF approval pending)
- Hardware (MX250 2GB VRAM) insufficient for responsive 7B inference
- Voice service in `ai/voice/` (faster-whisper STT only)
- No coupling to agent team
- Text-only path preserved

## Safety & Project Protection

- **No destructive commands** without explicit authorization
- **No secret exposure** — `.env` files never printed
- **No model weights in Git** — `/data/AI-Models/` excluded
- **No database deletion** — both SQLite files preserved
- **No forced git operations** — `git reset --hard`, `git clean` prohibited
- **No public exposure** — services stay local until auth/TLS/rate limits reviewed

## Documentation Standards

- **No code change without documentation** (project rule)
- Update `CHANGELOG.md` for material changes
- Update relevant `docs/**` files
- Record verification evidence in task handoffs
- Report failures/blockers honestly

## Troubleshooting

### Agents Not Discoverable
```bash
# Check agent files exist
ls -la /data/MyFarmAI/.opencode/agents/

# Validate config
opencode debug config
```

### Permission Denied
- Check agent's `permission.edit` glob patterns match target files
- Orchestrator needs `permission.task` to delegate

### Subagent Depth
- `subagent_depth: 2` in `opencode.json` allows orchestrator → specialist → (security/qa)
- Increase if deeper nesting needed

## Related Documents

- `docs/roadmaps/MyFarmAI_Backend_Roadmap.md`
- `docs/roadmaps/MyFarmAI_Frontend_Dashboard_Roadmap.md`
- `docs/roadmaps/phase-00/` (13 Phase 0 documents)
- `docs/backend/ARCHITECTURE.md`
- `docs/backend/AUTH_ASSESSMENT.md`
- `docs/integration/ANDROID_INTEGRATION.md`
- `docs/AGENT_TEAM_DELEGATION.md`
- `docs/ADK_EVALUATION.md`
- `docs/PERSONAPLEX_BOUNDARY.md`
- `SECURITY.md`