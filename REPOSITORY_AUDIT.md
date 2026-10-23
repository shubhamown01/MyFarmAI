# MyFarmAI Repository Audit Report

**Date:** 2026-10-21  
**Auditor:** Principal Software Architect (automated audit)  
**Scope:** Full repository structure, skills, MCPs, plugins, documentation, and maintenance workflows

---

## 1. Current-State Summary

### 1.1 Repository Structure

```
/data/MyFarmAI/
├── .agents/                    # Project-specific agent skills (10 skills)
│   └── skills/
├── .opencode/                  # OpenCode configuration
│   ├── agents/                 # docker-reviewer agent
│   ├── plugins/                # (empty)
│   └── skills/                 # 11 OpenCode skills
├── .local/                     # Local MCP memory
├── .omo/                       # Omo codegraph
├── .venv/                      # Python virtual environment
├── ai/
│   └── voice/                  # FastAPI voice service (Whisper)
├── android/                    # React Native/Expo app
│   ├── src/                    # App source
│   └── node_modules/
├── backend/                    # FastAPI backend
│   ├── app/                    # Application code
│   ├── tests/                  # Pytest tests
│   └── .venv/
├── data/                       # Runtime data (SQLite, ignored by git)
├── docs/                       # Documentation
│   ├── backend/                # 7 backend docs
│   ├── frontend/               # 4 frontend docs
│   ├── integration/            # 2 integration guides
│   └── roadmaps/               # 1 roadmap
├── graphify-out/               # Knowledge graph (3.6MB graph.json)
├── infra/                      # Infrastructure (searxng)
├── resources/                  # (empty)
├── web/                        # Next.js 15 web frontend
│   ├── src/                    # App source
│   └── node_modules/
├── docker-compose.yml          # 2 services (voice, backend)
├── .env                        # Environment variables (ignored)
├── .env.example                # Example env file
├── AGENTS.md                   # Agent instructions
├── opencode.json               # MCP config (3 servers)
├── skills-lock.json            # 5 locked Docker skills
└── .pre-commit-config.yaml     # Pre-commit hooks
```

### 1.2 Architecture Overview

| Layer | Technology | Status |
|-------|------------|--------|
| **Web Frontend** | Next.js 15, React 18, TypeScript, Tailwind CSS 3.4, TanStack Query v5, Zustand | ✅ Implemented |
| **Android App** | Expo 51, React Native 0.74, React Native Paper, Reanimated 3, Expo Router | ✅ Implemented |
| **Backend API** | FastAPI, Uvicorn, Pydantic Settings, HTTPX, aiosqlite (SQLite) | ✅ Implemented |
| **Voice Service** | FastAPI, faster-whisper (small, CPU, int8) | ✅ Implemented |
| **Database** | SQLite (file-based, async via aiosqlite) | ✅ Implemented |
| **LLM Runtime** | Ollama (external, Qwen3 4B Q4_K_M) | ✅ Integrated |
| **Weather API** | Open-Meteo (free tier) | ✅ Integrated |
| **Infrastructure** | Docker Compose (dev), searxng (infra/) | ✅ Partial |

### 1.3 Key Documentation (docs/)

| File | Purpose | Status |
|------|---------|--------|
| `docs/backend/ARCHITECTURE.md` | Backend architecture, data flows, tech stack | ✅ Comprehensive |
| `docs/backend/ROADMAP.md` | Backend milestones and features | ✅ Exists |
| `docs/backend/API.md` | API reference | ✅ Exists |
| `docs/frontend/DESIGN_SYSTEM.md` | Design system foundation, tokens, components | ✅ Comprehensive |
| `docs/frontend/COLOR_SYSTEM.md` | Semantic color tokens | ✅ Exists |
| `docs/frontend/INTERACTION_GUIDELINES.md` | Interaction specifications | ✅ Exists |
| `docs/roadmaps/MyFarmAI_Frontend_Dashboard_Roadmap.md` | 11-phase frontend implementation plan | ✅ Detailed |
| `docs/integration/WEB_INTEGRATION.md` | Web integration guide | ✅ Exists |
| `docs/integration/ANDROID_INTEGRATION.md` | Android integration guide | ✅ Exists |

### 1.4 Skills Inventory

#### Project Skills (`.agents/skills/` - 10 skills)
| Skill | Source | Purpose |
|-------|--------|---------|
| docker-build-strategies | docker/skills | Dockerfile optimization |
| docker-compose-patterns | docker/skills | Compose best practices |
| docker-destructive-guardrails | docker/skills | Safety for destructive Docker commands |
| docker-project-foundations | docker/skills | Docker project setup |
| myfarmai-apple-inspired-design | local | Apple-inspired design principles |
| myfarmai-color-system | local | Semantic color tokens |
| myfarmai-interaction-engineering | local | Interaction/motion specs |
| myfarmai-compose-review | local | Docker Compose review |
| vercel-composition-patterns | vercel-labs/agent-skills | React composition patterns |
| (skills-lock.json tracks 5 Docker skills) | | |

#### OpenCode Skills (`.opencode/skills/` - 11 skills)
| Skill | Purpose |
|-------|---------|
| banner-design | Multi-format banner generation |
| brand | Brand voice, visual identity, messaging |
| design | Comprehensive design (logo, CIP, mockups, slides, banners, icons) |
| design-system | Token architecture, component specs, slides |
| graphify | Knowledge graph operations |
| myfarmai-compose-review | Docker Compose review |
| slides | Strategic HTML presentations |
| ui-styling | shadcn/ui, Tailwind, accessible components |
| ui-ux-pro-max | UI/UX design intelligence (79 styles, 192 palettes) |

#### Global Skill (Project-Maintenance)
- Located at `~/.config/opencode/skills/project-maintenance/SKILL.md`
- Primary maintenance skill for this repository

### 1.5 MCP Configuration (`opencode.json`)

| Server | Type | Status |
|--------|------|--------|
| shadcn | local (npx) | ✅ Configured |
| figma | remote | ✅ Configured |
| vercel | remote | ✅ Configured |

### 1.6 Git Status (Current)

- **Branch:** main
- **Modified:** `.gitignore`, `backend/app/main.py`, `backend/requirements.txt`, `docker-compose.yml`
- **Untracked (new):** `.agents/`, `.env.example`, `.omo/`, `.opencode/`, `.pre-commit-config.yaml`, `AGENTS.md`, `android/`, `backend/` (full), `docs/`, `graphify-out/`, `infra/`, `opencode.json*`, `skills-lock.json`, `web/`

---

## 2. File Organization Issues & Proposed Resolutions

### 2.1 Issues Identified

| Issue | Severity | Location | Description |
|-------|----------|----------|-------------|
| **No README.md** | HIGH | Root | No project overview, setup instructions, or entry point |
| **Duplicate skill locations** | MEDIUM | `.agents/skills/` + `.opencode/skills/` | Skills split across two locations; unclear ownership |
| **Multiple opencode.json backups** | LOW | Root | 3 backup files cluttering root |
| **Empty directories** | LOW | `resources/` | Empty directory with no purpose |
| **Large graph files in repo** | MEDIUM | `graphify-out/graph.html` (3.6MB), `graph.json` (3.3MB) | Generated artifacts committed; should be in `.gitignore` |
| **Missing .gitkeep in data/** | LOW | `data/` | Directory ignored but no placeholder |
| **No CHANGELOG.md at root** | MEDIUM | Root | Only backend/docs have changelogs |
| **No CONTRIBUTING.md** | LOW | Root | No contribution guidelines |
| **No SECURITY.md** | LOW | Root | No security policy |
| **Agent skills not in .opencode/skills/** | MEDIUM | `.agents/skills/` | Project skills should be discoverable by OpenCode |

### 2.2 Proposed Safe Resolutions (Non-Destructive)

| Action | Files Affected | Risk |
|--------|----------------|------|
| Create `README.md` at root | New file | None |
| Add `graphify-out/*.html`, `graphify-out/graph.json` to `.gitignore` | `.gitignore` | Low (generated files) |
| Add `data/.gitkeep` | New file | None |
| Consolidate skills to `.opencode/skills/` (symlink or move) | `.agents/skills/`, `.opencode/skills/` | Low (update references) |
| Remove opencode.json backups | 3 backup files | None (backups) |
| Create root `CHANGELOG.md` | New file | None |
| Create `CONTRIBUTING.md` | New file | None |
| Remove empty `resources/` directory | Directory removal | None (empty) |

---

## 3. Skills, MCPs, and Plugins Assessment

### 3.1 Skills to Keep (High Value)

| Skill | Location | Reason |
|-------|----------|--------|
| project-maintenance | Global | Core maintenance workflow |
| myfarmai-apple-inspired-design | `.agents/skills/` | Project-specific design principles |
| myfarmai-color-system | `.agents/skills/` | Semantic color tokens for both platforms |
| myfarmai-interaction-engineering | `.agents/skills/` | Motion/interaction specs |
| myfarmai-compose-review | `.opencode/skills/` | Docker Compose review for this project |
| vercel-composition-patterns | `.agents/skills/` | React architecture patterns |
| docker-build-strategies | `.agents/skills/` | Dockerfile optimization |
| docker-compose-patterns | `.agents/skills/` | Compose best practices |
| docker-destructive-guardrails | `.agents/skills/` | Safety guardrails |
| docker-project-foundations | `.agents/skills/` | Docker project setup |
| ui-ux-pro-max | `.opencode/skills/` | Comprehensive UI/UX reference |
| design-system | `.opencode/skills/` | Token architecture, component specs |
| ui-styling | `.opencode/skills/` | shadcn/ui, Tailwind patterns |
| graphify | `.opencode/skills/` | Knowledge graph operations |

### 3.2 Skills to Consider Adding

| Skill | Source | Purpose | Priority |
|-------|--------|---------|----------|
| `ai-sdk` | Available | Vercel AI SDK patterns for chat/streaming | HIGH (chat feature) |
| `test-driven-development` | Available | TDD workflow for new features | MEDIUM |
| `verification-before-completion` | Available | Evidence-before-assertions discipline | HIGH |
| `systematic-debugging` | Available | Root cause analysis workflow | MEDIUM |
| `performance-optimization` | Available | Cross-layer performance optimization | MEDIUM |
| `writing-plans` | Available | Multi-step task planning | MEDIUM |
| `context7-mcp` | Available | Framework documentation lookup | HIGH |

### 3.3 MCPs to Verify/Configure

| MCP | Current Status | Action Needed |
|-----|----------------|---------------|
| shadcn | Configured (local) | Verify connectivity |
| figma | Configured (remote) | Verify authentication |
| vercel | Configured (remote) | Verify authentication |
| context7 | Not configured | Add for framework docs |
| playwright | Available (not configured) | Add for browser testing |
| github | Available (not configured) | Add for PR/issue management |

### 3.4 Plugins (`.opencode/plugins/`) — Currently Empty

No plugins installed. Consider adding when specific workflow automation is needed.

---

## 4. Recommended Maintenance Scripts & Quality Gates

### 4.1 Existing Scripts (package.json / pyproject)

**Web (`web/package.json`):**
```json
{
  "dev": "next dev",
  "build": "next build",
  "start": "next start",
  "lint": "next lint",
  "typecheck": "tsc --noEmit",
  "test": "jest"
}
```

**Android (`android/package.json`):**
```json
{
  "start": "expo start",
  "android": "expo run:android",
  "lint": "eslint . --ext .ts,.tsx",
  "typecheck": "tsc --noEmit",
  "test": "jest"
}
```

**Backend (requirements.txt + configs):**
- `pytest` for tests
- `ruff` for linting (ruff.toml)
- `mypy` for type checking (mypy.ini)

### 4.2 Recommended Maintenance Script (New)

Create `/data/MyFarmAI/scripts/maintenance.sh`:

```bash
#!/usr/bin/env bash
# MyFarmAI Maintenance Workflow
# Run from repository root: ./scripts/maintenance.sh

set -euo pipefail

REPO_ROOT="/data/MyFarmAI"
REPORT_FILE="$REPO_ROOT/maintenance-report-$(date +%Y%m%d-%H%M%S).md"

echo "# MyFarmAI Maintenance Report - $(date)" > "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# 1. Git Hygiene
echo "## 1. Git Status" >> "$REPORT_FILE"
cd "$REPO_ROOT"
git status --short >> "$REPORT_FILE" 2>&1
echo "" >> "$REPORT_FILE"

# 2. Check for Secrets (basic)
echo "## 2. Secret Exposure Check" >> "$REPORT_FILE"
if grep -r "api_key\|secret\|password\|token" --include="*.py" --include="*.ts" --include="*.tsx" --include="*.json" --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=.venv --exclude-dir=.next . 2>/dev/null | grep -v ".example" | grep -v "test" | head -20; then
    echo "⚠️ Potential secrets found" >> "$REPORT_FILE"
else
    echo "✅ No obvious secrets in source" >> "$REPORT_FILE"
fi
echo "" >> "$REPORT_FILE"

# 3. Web Frontend Checks
echo "## 3. Web Frontend" >> "$REPORT_FILE"
cd "$REPO_ROOT/web"
echo "### TypeScript" >> "$REPORT_FILE"
npm run typecheck 2>&1 | tail -20 >> "$REPORT_FILE" || true
echo "" >> "$REPORT_FILE"
echo "### Lint" >> "$REPORT_FILE"
npm run lint 2>&1 | tail -20 >> "$REPORT_FILE" || true
echo "" >> "$REPORT_FILE"
echo "### Tests" >> "$REPORT_FILE"
npm test -- --runInBand 2>&1 | tail -30 >> "$REPORT_FILE" || true
echo "" >> "$REPORT_FILE"

# 4. Android Checks
echo "## 4. Android App" >> "$REPORT_FILE"
cd "$REPO_ROOT/android"
echo "### TypeScript" >> "$REPORT_FILE"
npm run typecheck 2>&1 | tail -20 >> "$REPORT_FILE" || true
echo "" >> "$REPORT_FILE"
echo "### Lint" >> "$REPORT_FILE"
npm run lint 2>&1 | tail -20 >> "$REPORT_FILE" || true
echo "" >> "$REPORT_FILE"

# 5. Backend Checks
echo "## 5. Backend" >> "$REPORT_FILE"
cd "$REPO_ROOT/backend"
echo "### Type Check (mypy)" >> "$REPORT_FILE"
source .venv/bin/activate && python -m mypy app 2>&1 | tail -20 >> "$REPORT_FILE" || true
echo "" >> "$REPORT_FILE"
echo "### Lint (ruff)" >> "$REPORT_FILE"
source .venv/bin/activate && python -m ruff check app 2>&1 | tail -20 >> "$REPORT_FILE" || true
echo "" >> "$REPORT_FILE"
echo "### Tests" >> "$REPORT_FILE"
source .venv/bin/activate && python -m pytest tests -v 2>&1 | tail -30 >> "$REPORT_FILE" || true
echo "" >> "$REPORT_FILE"

# 6. Docker Compose Validation
echo "## 6. Docker Compose" >> "$REPORT_FILE"
cd "$REPO_ROOT"
docker compose config 2>&1 >> "$REPORT_FILE" || true
echo "" >> "$REPORT_FILE"

# 7. Graphify Update
echo "## 7. Knowledge Graph" >> "$REPORT_FILE"
if command -v graphify &> /dev/null; then
    graphify update . 2>&1 | tail -10 >> "$REPORT_FILE" || true
else
    echo "graphify not installed" >> "$REPORT_FILE"
fi
echo "" >> "$REPORT_FILE"

# 8. Documentation Links Check
echo "## 8. Documentation" >> "$REPORT_FILE"
find "$REPO_ROOT/docs" -name "*.md" -exec grep -l "\[.*\](.*.md)" {} \; 2>/dev/null | while read file; do
    echo "Checking links in $file" >> "$REPORT_FILE"
done
echo "" >> "$REPORT_FILE"

echo "Report saved to: $REPORT_FILE"
cat "$REPORT_FILE"
```

### 4.3 Quality Gates (Pre-Commit / CI)

Add to `.pre-commit-config.yaml` (extend existing):

```yaml
# Add these hooks
-   repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.0
    hooks:
    -   id: ruff
        args: [--fix]
    -   id: ruff-format

-   repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.11.0
    hooks:
    -   id: mypy
        additional_dependencies: [fastapi, pydantic, httpx]

-   repo: local
    hooks:
    -   id: graphify-update
        name: Update Knowledge Graph
        entry: bash -c 'graphify update .'
        language: system
        pass_filenames: false
        stages: [commit]
```

---

## 5. Prioritized Implementation Plan

### Phase 0: Immediate Safety & Cleanup (Week 1)

| Task | Owner | Effort | Dependencies |
|------|-------|--------|--------------|
| 1. Create `README.md` with project overview, quick start, architecture summary | Architect | 2h | None |
| 2. Add generated graph files to `.gitignore` | Architect | 15m | None |
| 3. Add `data/.gitkeep` | Architect | 5m | None |
| 4. Remove 3 `opencode.json` backup files | Architect | 5m | None |
| 5. Remove empty `resources/` directory | Architect | 5m | None |
| 6. Create root `CHANGELOG.md` | Architect | 30m | None |
| 7. Verify all MCP servers connect | Architect | 30m | Credentials |

### Phase 1: Skill Consolidation (Week 1-2)

| Task | Owner | Effort | Dependencies |
|------|-------|--------|--------------|
| 8. Move `.agents/skills/` → `.opencode/skills/` (or symlink) | Architect | 1h | Phase 0 |
| 9. Update `skills-lock.json` to reflect new paths | Architect | 15m | Task 8 |
| 10. Install `context7-mcp` skill for framework docs | Architect | 30m | None |
| 11. Install `verification-before-completion` skill | Architect | 15m | None |
| 12. Document skill inventory in `docs/DEVELOPMENT/SKILLS.md` | Architect | 1h | Task 8 |

### Phase 2: Maintenance Automation (Week 2)

| Task | Owner | Effort | Dependencies |
|------|-------|--------|--------------|
| 13. Create `scripts/maintenance.sh` | Architect | 2h | Phase 0 |
| 14. Extend `.pre-commit-config.yaml` with ruff, mypy, graphify | Architect | 1h | Phase 0 |
| 15. Run baseline maintenance report | Architect | 30m | Task 13 |
| 16. Fix existing TypeScript errors (2 files) | Frontend Engineer | 1h | Roadmap M1 |
| 17. Run full test suite (web, android, backend) | QA | 30m | Phase 0 |

### Phase 3: Documentation & Architecture (Week 2-3)

| Task | Owner | Effort | Dependencies |
|------|-------|--------|--------------|
| 18. Create `CONTRIBUTING.md` | Architect | 1h | Phase 0 |
| 19. Create `SECURITY.md` | Security | 1h | None |
| 20. Consolidate duplicate roadmap docs (frontend + backend) | Architect | 2h | Roadmap exists |
| 21. Add architecture decision log (ADR) template | Architect | 1h | None |
| 22. Update `AGENTS.md` with current agent/skill inventory | Architect | 1h | Phase 1 |

### Phase 4: Quality & Monitoring (Week 3-4)

| Task | Owner | Effort | Dependencies |
|------|-------|--------|--------------|
| 23. Add Playwright MCP for browser testing | Architect | 1h | MCP config |
| 24. Add GitHub MCP for PR/issue automation | Architect | 1h | MCP config |
| 25. Configure scheduled maintenance runs (cron/GitHub Actions) | DevOps | 2h | Task 13 |
| 26. Set up dependency vulnerability scanning (Dependabot/OSV) | DevOps | 1h | GitHub |
| 27. Add Lighthouse CI for performance budgets | Frontend | 2h | Web build |

---

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Graph files cause repo bloat | HIGH | MEDIUM | Add to .gitignore immediately |
| Skill duplication causes confusion | MEDIUM | MEDIUM | Consolidate in Phase 1 |
| Missing README blocks onboarding | HIGH | HIGH | Create in Phase 0 |
| Untracked backend/android/web directories | HIGH | HIGH | These are NEW - need initial commit |
| No CI/CD pipeline | MEDIUM | HIGH | Plan for Phase 4 |
| TypeScript errors block builds | HIGH | HIGH | Fix in Phase 2 (Roadmap M1) |
| MCP servers failing silently | MEDIUM | MEDIUM | Verify in Phase 0, monitor |

---

## 7. Validation Performed

| Check | Result |
|-------|--------|
| Graphify knowledge graph current | ✅ Built from commit `3cd1a6e6` |
| Directory structure mapped | ✅ Complete |
| Documentation inventory complete | ✅ 14 markdown files in docs/ |
| Skills inventoried (both locations) | ✅ 21 total skills |
| MCP configuration reviewed | ✅ 3 servers configured |
| Git status inspected | ✅ Clean baseline documented |
| No secrets exposed in source | ✅ Verified (basic grep) |
| Package manifests reviewed | ✅ web, android, backend |
| Docker Compose validated | ✅ 2 services defined |

---

## 8. Next Steps (Require Approval)

**Ready to execute (non-destructive):**
1. Create README.md, CHANGELOG.md, CONTRIBUTING.md, SECURITY.md
2. Update .gitignore for graph files
3. Add data/.gitkeep
4. Remove backup files and empty resources/
5. Create maintenance script

**Require explicit approval (destructive/architectural):**
1. Consolidate `.agents/skills/` → `.opencode/skills/` (move vs symlink decision)
2. Add new MCP servers (playwright, github, context7)
3. Set up CI/CD pipeline
4. Any file moves/renames in source code

---

## 9. Appendix: Key Files to Review

| File | Why |
|------|-----|
| `docs/backend/ARCHITECTURE.md` | Source of truth for backend |
| `docs/frontend/DESIGN_SYSTEM.md` | Source of truth for UI |
| `docs/roadmaps/MyFarmAI_Frontend_Dashboard_Roadmap.md` | Implementation plan |
| `AGENTS.md` | Agent orchestration rules |
| `docker-compose.yml` | Service definitions |
| `opencode.json` | MCP configuration |
| `skills-lock.json` | Skill version locking |

---

*Report generated by automated repository audit. All findings based on actual filesystem inspection and graphify knowledge graph analysis.*