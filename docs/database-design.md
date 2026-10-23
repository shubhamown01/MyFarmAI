# Database Design (verified 2026-10-23)

## Two schemas — important distinction

| Layer | Schema | Location | Status |
|-------|--------|----------|--------|
| **Runtime (production data)** | `conversations`, `messages` | created by `app/db/connection.py` via `CREATE TABLE IF NOT EXISTS` | Active — used by chat endpoints |
| **Phase 2 target model** | 13 tables (below) | `alembic/versions/6cd2bffd9881_initial_schema.py` + SQLAlchemy 2 models | Migration defined; **not yet applied** to canonical SQLite |

Canonical file decision: `backend/data/app.db` (G1 — decision recorded, owner approval pending; see `docs/engineering/DECISION_REGISTER.md`). Legacy copy at `data/app.db` is preserved untouched and ignored by Git.

## Runtime tables

- `conversations(id, language, crop, location, ...)`
- `messages(id, conversation_id, role, content, created_at)`

Access via `app/db/conversations.py` + `app/db/repositories.py`.

## Phase 2 target tables (Alembic `6cd2bffd9881`)

`users · farms · farm_members · crops · crop_cycles · sessions · refresh_tokens · conversations · messages · research_queries · research_sources · citations · audit_events`

Highlights:
- `users`: email unique, role enum (USER/ADMIN), preferred_language, no auth wiring yet.
- `crops`: category enum, temperature/rainfall/optimal-growing-window fields.
- `research_queries/research_sources/citations`: Phase 6 research pipeline (SearXNG + citations).
- `sessions`/`refresh_tokens`: Phase 3 auth groundwork (unused today).
- All keyed relations via UUID + FKs; UUID types imply PostgreSQL-leaning choices that must be evaluated when applying to SQLite (Part of Phase 2 scope, not yet done).

## Migrations

```bash
cd backend && uv run alembic upgrade head       # apply
uv run alembic revision --autogenerate -m "..." # create
```

⚠️ Do not run migrations against `backend/data/app.db` without G1 approval and a verified backup (drill procedure: `docs/engineering/BACKUP_AUDIT.md`.

## Safety & backup

- Both `data/` and `backend/data/` are Git-ignored; nothing containing user data is tracked (verified `git ls-files`).
- Backup drill (2026-10-22): `VACUUM INTO` copies + SHA-256 + integrity_check — passed; pending owner acceptance (G5).
- never delete or relocate either SQLite file without explicit approval.
