# Changelog

All notable changes to MyFarmAI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Apache-2.0 LICENSE (governance gate G2 approved; decision recorded in `docs/engineering/DECISION_REGISTER.md`)
- `docs/repository-audit.md` — full 2026-10-23 audit: structure, governance status, risks, staged mapping plan
- Phase 6 documentation set verified against code: `docs/project-overview.md`, `docs/architecture.md`, `docs/setup-guide.md`, `docs/api-documentation.md`, `docs/database-design.md`, `docs/demo-guide.md`
- Root `Makefile` (backend-check/dev, web-check/build, android-check, docker up/down/logs, graph-update)
- VS Code workspace config: `.vscode/{settings,tasks,launch,extensions}.json` (tracked via .gitignore exceptions)
- Historical: `REPOSITORY_AUDIT.md` (2026-10-21 audit), `.agents/` project skills, `.opencode/` skills + agents config
- Baseline commits: `ea9d109` (docs/governance/tooling), `c4aece2` (web: Next.js 15 dashboard), `1f543a9` (android: Expo 51 + brand assets)

### Changed
- README: corrected voice-service containment status, Python 3.12 + uv tooling, `CORS_ALLOWED_ORIGINS`, backend uv commands, Apache-2.0 license reference
- `.gitignore`: track selected `.vscode` files; ignore `*.egg-info/`, `*.tsbuildinfo`, entire `graphify-out/` (rebuildable)

### Removed
- Stray scratch files `web/test.ts`, `web/test.tsx`, `web/test-component.tsx`
- Stale `opencode.json` backup files (consistent with prior CHANGELOG claim)
- Root maintenance reports relocated to `docs/engineering/`

### Added
- Repository audit and maintenance workflow (2026-10-21)
- README.md with project overview and quick start
- CONTRIBUTING.md with development workflow
- SECURITY.md with vulnerability reporting
- Maintenance script (scripts/maintenance.sh)
- Extended pre-commit hooks (ruff, mypy, graphify-update)
- Graphify generated artifacts added to .gitignore
- data/.gitkeep placeholder

### Changed
- Updated .gitignore to exclude generated graph files
- Dashboard/web: removed oversized hero and decorative Smart Farming illustrations from the Home dashboard; added compact welcome with "Ask the AI Assistant" and "Check Crop Health" actions (`docs/ui/MODERN_DASHBOARD_AND_UX.md`)

### Fixed
- Removed obsolete opencode.json backup files
- Removed empty resources/ directory

## [0.1.0] - 2026-10-18

### Added
- Initial backend architecture with FastAPI
- Chat endpoint with Ollama integration
- Weather endpoint with Open-Meteo integration
- Agricultural resources catalogue (12 verified Indian resources)
- SQLite async database with conversation persistence
- Voice service with faster-whisper (Hindi/English)
- Docker Compose development environment
- Web frontend foundation (Next.js 15, Tailwind, TanStack Query)
- Android app foundation (Expo, React Native Paper)
- Design system documentation (principles, tokens, components)
- Graphify knowledge graph initialization

### Backend
- REST API v1 with health, chat, weather, resources endpoints
- Pydantic Settings configuration with .env support
- Ollama client with connection pooling and error handling
- Weather client with WMO code mapping
- Conversation CRUD with SQLite

### Frontend (Web)
- Next.js 15 App Router with TypeScript
- Tailwind CSS 3.4 with custom primary scale
- Chat interface with voice input/output
- Weather card component
- Resources list with category filtering
- TanStack Query v5 for server state
- Zustand for client state

### Frontend (Android)
- Expo Router v3 file-based routing
- React Native Paper v5 (Material 3)
- React Native Reanimated 3 for animations
- Expo Speech / Speech Recognition for voice
- Expo SecureStore for local persistence
- Shared API client and types with web

### Documentation
- Backend architecture, API reference, roadmap
- Frontend design system, color system, interaction guidelines
- Integration guides for web and Android
- Frontend dashboard development roadmap

## [0.0.1] - 2026-10-17

### Added
- Initial project structure
- Basic FastAPI application skeleton
- Docker Compose with backend service
- Basic Next.js web application
- Basic Expo Android application