# MyFarmAI — root tasks (safe, documented commands only)
# Run: make help

.PHONY: help backend-check backend-dev web-check web-build android-check docker-up docker-down docker-logs graph-update

help:
	@echo "MyFarmAI — available tasks"
	@echo ""
	@echo "  make backend-check   — ruff + mypy + pytest (backend quality gate)"
	@echo "  make backend-dev     — run FastAPI on 127.0.0.1:8000 (loopback only)"
	@echo "  make web-check       — web typecheck + lint + tests"
	@echo "  make web-build       — web production build"
	@echo "  make android-check   — android typecheck + lint"
	@echo "  make docker-up       — start backend container (voice contained, unpublished)"
	@echo "  make docker-down     — stop containers"
	@echo "  make docker-logs     — tail container logs"
	@echo "  make graph-update    — refresh knowledge graph (AST-only)"

backend-check:
	./scripts/check.sh

backend-dev:
	cd backend && uv run uvicorn app.main:app --host 127.0.0.1 --reload

web-check:
	cd web && npm run typecheck && npm run lint && npm test -- --runInBand

web-build:
	cd web && npm run build

android-check:
	cd android && npm run typecheck && npm run lint

docker-up:
	docker compose up -d

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f

graph-update:
	graphify update .
