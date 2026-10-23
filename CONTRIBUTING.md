# Contributing to MyFarmAI

Thank you for contributing to MyFarmAI! This guide covers the development workflow, coding standards, and pull request process.

## Table of Contents

1. [Development Workflow](#development-workflow)
2. [Coding Standards](#coding-standards)
3. [Commit Messages](#commit-messages)
4. [Pull Request Process](#pull-request-process)
5. [Testing Requirements](#testing-requirements)
6. [Documentation](#documentation)
7. [Architecture Decisions](#architecture-decisions)

---

## Development Workflow

### 1. Start from Main

```bash
git checkout main
git pull origin main
```

### 2. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

### 3. Make Changes

Follow the coding standards below. Run checks frequently:

```bash
# Web
cd web && npm run typecheck && npm run lint && npm test

# Android
cd android && npm run typecheck && npm run lint

# Backend
cd backend && source .venv/bin/activate && python -m ruff check app && python -m mypy app && python -m pytest tests
```

### 4. Update Documentation

**Rule: No code change without documentation.**

Update relevant files in `docs/`:
- API changes → `docs/backend/API.md`
- Architecture changes → `docs/backend/ARCHITECTURE.md`
- UI/UX changes → `docs/frontend/DESIGN_SYSTEM.md`
- New features → Update roadmap if applicable

### 5. Run Maintenance Check

```bash
./scripts/maintenance.sh
```

### 6. Commit and Push

```bash
git add .
git commit -m "feat: add your feature description"
git push origin feature/your-feature-name
```

### 7. Create Pull Request

Use the PR template (auto-populated). Ensure:
- All checks pass
- Documentation updated
- No unrelated changes

---

## Coding Standards

### General Principles

1. **Minimal changes** — Solve the problem with the least code
2. **Reuse existing patterns** — Follow established conventions in the codebase
3. **No duplication** — Extract shared logic to utilities/hooks/services
4. **Type safety** — Strict TypeScript / MyPy compliance required
5. **Security first** — Validate inputs, never expose secrets

### TypeScript (Web & Android)

```typescript
// ✅ Good: Explicit types, no any
interface ChatRequest {
  message: string;
  conversation_id?: string;
  language?: string;
  crop?: string;
  location?: string;
}

// ✅ Good: Compound components over boolean props
<Chat.Provider>
  <Chat.Header />
  <Chat.MessageList />
  <Chat.InputArea>
    <Chat.TextInput />
    <Chat.SendButton />
  </Chat.InputArea>
</Chat.Provider>

// ❌ Bad: Boolean prop explosion
<ChatInterface showHeader={true} showVoice={true} isLoading={false} />
```

- Use `vercel-composition-patterns` skill patterns
- Follow `vercel-react-best-practices` for performance
- Use `clsx` + `tailwind-merge` for class composition
- Prefer `interface` over `type` for object shapes

### Python (Backend)

```python
# ✅ Good: Type hints, Pydantic models, async
async def generate_chat_response(
    request: ChatRequest,
    db: AsyncSession,
    ollama: OllamaClient
) -> ChatResponse:
    ...

# ✅ Good: Structured error handling
raise HTTPException(
    status_code=503,
    detail="Ollama connection failed",
    headers={"X-Error-Code": "OLLAMA_CONNECTION_FAILED"}
)
```

- Use `async`/`await` throughout
- Pydantic models for all request/response validation
- Structured error responses with error codes
- Ruff for linting, MyPy for type checking

### CSS / Styling

- Use Tailwind utilities; avoid custom CSS
- Design tokens via CSS variables (see `docs/frontend/COLOR_SYSTEM.md`)
- Follow `myfarmai-color-system` and `design-system` skills
- Dark mode via `prefers-color-scheme` media query

---

## Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Types

| Type | Description |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `style` | Formatting, no logic change |
| `refactor` | Code restructuring |
| `test` | Adding/updating tests |
| `chore` | Maintenance, deps, config |
| `perf` | Performance improvement |

### Examples

```
feat(chat): add conversation history to chat endpoint

fix(weather): handle Open-Meteo timeout gracefully

docs(frontend): update design system color tokens

refactor(api): extract chat orchestration to service

test(backend): add integration tests for resources endpoint
```

### Scope Guidelines

- `backend` — FastAPI backend
- `web` — Next.js web frontend
- `android` — React Native/Expo app
- `voice` — Voice service
- `infra` — Docker, deployment, infrastructure
- `docs` — Documentation
- `design` — Design system, tokens, components

---

## Pull Request Process

### Before Opening PR

- [ ] All type checks pass (`npm run typecheck` / `mypy`)
- [ ] All lint checks pass (`npm run lint` / `ruff`)
- [ ] All tests pass (`npm test` / `pytest`)
- [ ] Production build succeeds (`npm run build`)
- [ ] Documentation updated
- [ ] No unrelated changes (check `git diff`)

### PR Template

```markdown
## Summary
Brief description of changes.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactor
- [ ] Performance improvement

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing completed (describe)

## Documentation
- [ ] API docs updated
- [ ] Architecture docs updated
- [ ] Design system docs updated
- [ ] README/CHANGELOG updated

## Checklist
- [ ] No secrets or credentials in changes
- [ ] No breaking changes (or documented)
- [ ] Follows existing code patterns
- [ ] Accessibility considered (WCAG 2.1 AA)
```

### Review Process

1. Automated checks must pass (CI)
2. At least one code review approval
3. Author addresses all review comments
4. Maintainer merges after verification

---

## Testing Requirements

### Backend (Pytest)

```bash
cd backend
source .venv/bin/activate
python -m pytest tests -v --cov=app --cov-report=term-missing
```

- Test all endpoints (success + error cases)
- Mock external services (Ollama, Open-Meteo)
- Use fixtures for database, client, settings
- Target: >80% coverage for new code

### Web (Jest + React Testing Library)

```bash
cd web
npm test -- --runInBand --coverage
```

- Test component rendering and interactions
- Test custom hooks
- Accessibility tests with `axe-core`
- Mock API calls with MSW or manual mocks

### Android (Jest)

```bash
cd android
npm test
```

- Test component rendering
- Test hooks and utilities
- Mock Expo modules and native dependencies

### E2E (Playwright)

```bash
cd web
npx playwright test
```

- Critical user flows only
- Test at multiple viewports
- Accessibility checks in browser

---

## Documentation

### Required Updates

| Change Type | Files to Update |
|-------------|-----------------|
| New API endpoint | `docs/backend/API.md`, `docs/backend/ARCHITECTURE.md` |
| Schema change | `docs/backend/API.md`, integration guides |
| New UI component | `docs/frontend/DESIGN_SYSTEM.md` |
| Color/token change | `docs/frontend/COLOR_SYSTEM.md`, `docs/frontend/DESIGN_SYSTEM.md` |
| Interaction change | `docs/frontend/INTERACTION_GUIDELINES.md` |
| New feature | Relevant roadmap, CHANGELOG.md |

### Documentation Standards

- Use relative links within `docs/`
- Keep examples runnable and current
- Mark planned vs implemented features clearly
- Update `CHANGELOG.md` under `[Unreleased]`

---

## Architecture Decisions

### Architecture Decision Records (ADRs)

For significant architectural decisions, create an ADR in `docs/adr/`:

```
docs/adr/
├── 001-use-fastapi-for-backend.md
├── 002-use-sqlite-for-dev.md
├── 003-use-ollama-for-llm.md
├── 004-use-tailwind-for-web.md
├── 005-use-expo-for-android.md
└── ...
```

### ADR Template

```markdown
# ADR XXX: Title

## Status
Proposed | Accepted | Superseded

## Context
What problem are we solving?

## Decision
What did we decide?

## Consequences
### Positive
- ...

### Negative
- ...

## Alternatives Considered
- Alternative 1: reason rejected
- Alternative 2: reason rejected
```

### When to Create ADR

- New major dependency or framework
- Significant architectural pattern change
- Database or storage technology change
- Authentication/authorization approach
- Cross-platform strategy decisions

---

## Getting Help

- Check existing issues and PRs
- Review `AGENTS.md` for agent/skill workflows
- Consult `docs/` for architecture and design references
- Ask in team channel or create a GitHub issue

---

*Last updated: 2026-10-21*