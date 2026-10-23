# Database and Migration Assessment

**Phase:** 0 — read-only  
**Date:** 2026-10-21  
**Related:** [`ARCHITECTURE_DECISIONS.md`](ARCHITECTURE_DECISIONS.md) ADR-004, [`API_CONTRACT_INVENTORY.md`](API_CONTRACT_INVENTORY.md)

---

## 1. Summary

MyFarmAI currently uses **SQLite 3.46.1** through the Python standard library and `aiosqlite==0.22.1`. There is no ORM, no migration tool, and no schema versioning. The schema is created with `CREATE TABLE IF NOT EXISTS` at application startup. Two separate database files exist with different data volumes, and no backup/restore procedure was found.

This is adequate for a single-user prototype. It is not sufficient for multi-user production, ownership-based authorization, reliable concurrent writes, or auditable schema changes.

## 2. Verified database state

| Item | `backend/data/app.db` | `data/app.db` |
|---|---|---|
| Size | 98,304 bytes | 40,960 bytes |
| Last modified | 2026-10-21 10:33:31 | 2026-10-19 11:07:54 |
| Conversations | 122 | 35 |
| Messages | 315 | 74 |
| `PRAGMA integrity_check` | `ok` | `ok` |
| Tables | `conversations`, `messages`, `sqlite_sequence` | same |
| Indexes | `idx_messages_conversation_id`, PK autoindexes | same |
| Used by | Local runs from `backend/` (default `data/app.db` relative to CWD) | Docker Compose bind mount `./data:/app/data` |
| Git status | Untracked, **not ignored** | Untracked, ignored by `data/*` |

**Both files are plausible sources of user data.** Neither was opened to display message content. The row counts, sizes, and schema were inspected read-only.

`backend/data/app.db` is the file a developer reaches when running Uvicorn or pytest from `backend/` with the default configuration. `data/app.db` is the file the Compose deployment mounts. They are not synchronized by any code in the repository.

## 3. Schema

### 3.1 `conversations`

```sql
CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    language TEXT DEFAULT 'en',
    crop TEXT,
    location TEXT
);
```

- `id`: UUIDv4 string generated in `backend/app/db/conversations.py:12`.
- `created_at` / `updated_at`: SQLite `CURRENT_TIMESTAMP` (UTC, second resolution).
- `language`: free text with default `en`; no `CHECK` constraint.
- `crop`, `location`: free text; no length constraints at the DB layer.
- No owner/user/farm columns.

### 3.2 `messages`

```sql
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations (id) ON DELETE CASCADE
);
```

- `role`: free text; no `CHECK (role IN ('user','assistant','system'))`.
- `content`: unbounded text.
- FK is declared, but SQLite foreign-key enforcement is **off by default per connection** and `get_db_connection` does not execute `PRAGMA foreign_keys = ON` (`backend/app/db/connection.py:18-23`). The cascade therefore does not currently run.
- `created_at` is second-resolution; concurrent messages and fast tests can share a timestamp.

### 3.3 Index

```sql
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id
ON messages (conversation_id);
```

No index on `(conversation_id, created_at)`, `conversations.updated_at`, or `messages.created_at`.

## 4. Access patterns and transactions

| Operation | Implementation | Notes |
|---|---|---|
| Create conversation | `INSERT` + commit | One connection per call |
| Get conversation | `SELECT *` by id | No ownership filter |
| Add message | `INSERT` + `UPDATE conversations.updated_at` + commit | Same connection, one transaction |
| Recent messages | `SELECT ... ORDER BY created_at DESC LIMIT ?`, then reversed | Tie ordering is undefined; limit clamped 1–50, otherwise 10 |
| Startup schema | `CREATE TABLE IF NOT EXISTS` | No version table, no migration history |

Every operation opens a new `aiosqlite` connection and closes it. There is no connection pool, no WAL mode, no busy-timeout configuration, and no retry on `database is locked`. For low traffic this works; under concurrent chat requests it can produce lock errors or serialized latency.

## 5. Data relationships and integrity

- One conversation → many messages, declared cascade delete. **Not enforced** without `PRAGMA foreign_keys=ON`.
- No users, farms, memberships, crops, research sources, audit events, or sessions exist.
- No uniqueness constraint beyond the conversation ID.
- No `CHECK` constraints for role, language, or content length.
- No soft-delete or retention columns.
- No database-level `updated_at` trigger; it is updated manually only in `add_message`.

## 6. Security and privacy observations

| ID | Observation | Evidence | Impact |
|---|---|---|---|
| DB-S01 | Conversation data has no owner | schema | Cannot enforce cross-user isolation |
| DB-S02 | `backend/data/app.db` contains 122 conversations and is not git-ignored | `git status`, `.gitignore` | Accidental commit of user conversations |
| DB-S03 | Two divergent DB files | file inspection | Wrong file may be backed up/migrated; data loss |
| DB-S04 | No encryption at rest | SQLite file | Host/disk access exposes conversations |
| DB-S05 | No retention or deletion procedure | repository search | Indefinite storage of messages, crop, location |
| DB-S06 | IP addresses logged; conversation metadata can be indirect PII | `main.py:62-90`, schema | Privacy obligations may apply |
| DB-S07 | SQLite file permissions are OS-dependent | `backend/data/app.db` mode `644` | Group/world read risk on multi-user host |
| DB-S08 | DB content is not validated at the boundary beyond API schemas | `schemas/chat.py` | Oversized/odd values possible if DB is written by other tools |

No message content, credentials, or personal records were printed during this audit.

## 7. Backups and recovery

**Verified:** no backup script, cron job, volume snapshot, `pg_dump`, `VACUUM INTO`, or restore runbook exists in the repository. Docker named volumes are not used for MyFarmAI’s SQLite file; it is a host bind mount.

Consequences:

- A disk failure, accidental deletion, or bad migration can destroy all conversations.
- There is no tested recovery point objective (RPO) or recovery time objective (RTO).
- No integrity verification or retention policy exists.

**Minimum recommendation for Phase 1/2:** stop writes (or use SQLite’s online backup), copy the DB with a timestamp and SHA-256, store it on `/data` outside the repo, verify `PRAGMA integrity_check` on the copy, and perform a restore drill into a disposable path. For PostgreSQL, use scheduled `pg_dump` plus WAL archiving if the RPO requires it, and test restore quarterly.

## 8. SQLite-to-PostgreSQL assessment

### 8.1 Is PostgreSQL appropriate?

**Yes, for production**, because MyFarmAI needs:

- Multiple users and farm-scoped ownership checks.
- Concurrent writes from web/mobile clients.
- Enforced foreign keys, `CHECK` constraints, and transactional migrations.
- Reliable backup/restore and point-in-time recovery.
- Full-text search (PostgreSQL FTS) before adding a separate search service.
- A path to row-level security or service-layer tenancy.

SQLite remains appropriate for **unit tests and local development**, provided tests use an isolated file or in-memory DB and never touch the developer’s data.

### 8.2 Compatibility gaps

| SQLite usage | PostgreSQL change |
|---|---|
| `?` placeholders | `$1` placeholders or SQLAlchemy bound parameters |
| `INTEGER PRIMARY KEY AUTOINCREMENT` | `BIGINT GENERATED BY DEFAULT AS IDENTITY` / `BIGSERIAL` |
| `TEXT` UUID | `UUID` (or `TEXT` if compatibility is preferred) |
| `TIMESTAMP DEFAULT CURRENT_TIMESTAMP` | `TIMESTAMPTZ DEFAULT now()` |
| `cursor.lastrowid` | `INSERT ... RETURNING id` |
| `PRAGMA foreign_keys` | Always enforced; no pragma |
| `CREATE TABLE IF NOT EXISTS` startup DDL | Alembic versioned migrations |
| SQLite date strings | `TIMESTAMPTZ`; serialize ISO-8601 with timezone |
| `ORDER BY created_at` ties | `ORDER BY created_at, id` |
| Case-insensitive category matching in Python | Keep in Python or use `citext`/`lower()` consistently |
| No JSON columns | `JSONB` only if a real requirement appears |

The current SQL is simple and parameterized; there are no SQLite-specific functions, triggers, views, or `INSERT OR REPLACE` statements. This keeps migration risk **low**.

### 8.3 Schema changes likely required in Phase 2

Not part of Phase 0; proposed only:

- `users` (id, email/phone, password hash or external identity, status, timestamps).
- `farms` (id, name, location, coordinates, owner_id, timestamps).
- `farm_members` (farm_id, user_id, role, unique pair).
- Add `user_id`/`farm_id` to conversations (nullable during migration, then NOT NULL after backfill).
- `sessions` or `refresh_tokens` for auth.
- `audit_events` for security-sensitive actions.
- `research_sources` / `citations` when Phase 6 begins.
- `CHECK` constraints for `role`, `language`, and coordinate ranges.
- Index `(conversation_id, created_at, id)` and `(user_id, updated_at)`.

### 8.4 Data migration strategy (recommended, not executed)

1. **Freeze writes** to the backend (maintenance window).
2. **Choose the canonical DB** with the owner. Do not merge blindly. If both contain real data, define a merge rule (e.g., import both with a `legacy_source` tag) and deduplicate by conversation ID.
3. **Back up** the chosen file with `VACUUM INTO` or a filesystem copy after stopping writes; compute SHA-256; run `PRAGMA integrity_check` on the copy.
4. **Export** conversations and messages to CSV/JSON with stable ordering (`created_at, id`).
5. **Transform** timestamps to UTC `TIMESTAMPTZ`, validate roles and lengths, and assign a migration owner (`legacy_import`) if no user exists.
6. **Load** into PostgreSQL in a transaction using `COPY`; preserve original IDs.
7. **Reset** identity sequences; verify counts and per-conversation message counts.
8. **Validate** with checksums (row counts, min/max timestamps, per-conversation counts) and spot-check a small number of non-sensitive records with owner approval.
9. **Cut over** the application to PostgreSQL; keep SQLite read-only until acceptance.
10. **Rollback:** revert the application to SQLite and restore the pre-migration file. Any messages written after cutover would be lost; prefer forward-fix after new writes begin.

### 8.5 Row counts and validation baseline

| Metric | `backend/data/app.db` | `data/app.db` |
|---|---:|---:|
| Conversations | 122 | 35 |
| Messages | 315 | 74 |
| Orphan messages (FK check needed) | Not checked due FK disabled; query can be run read-only | same |
| Integrity | ok | ok |
| Schema version | none | none |

**Do not treat 122+35 or 315+74 as a merge target.** The canonical source is an owner decision.

### 8.6 Downtime and cutover

With <1,000 rows, export/import should take seconds to minutes. A short maintenance window is simpler and safer than dual-write. Requirements:

- Announce/maintenance page.
- Stop backend writes.
- Final backup and export.
- Migrate and validate.
- Start backend against PostgreSQL.
- Smoke-test chat creation/continuation, weather, resources.
- Keep SQLite file and backup until acceptance.
- Document the exact rollback command.

### 8.7 Frontend/API compatibility

- Conversation IDs remain strings; clients already treat them as opaque.
- `created_at`/`updated_at` are not currently returned by the API, so timestamp format changes are internal.
- Response shapes should not change during migration.
- Chat error codes should remain stable.
- If auth adds ownership, clients must send credentials; this is a breaking change and requires coordinated client updates.

### 8.8 Acceptance criteria for a future migration

- [ ] Canonical source chosen and documented.
- [ ] Pre-migration backup exists, checksum recorded, integrity check passes.
- [ ] PostgreSQL schema created by Alembic from empty.
- [ ] Row counts and per-conversation counts match the source.
- [ ] No orphan messages; FK and role checks pass.
- [ ] Chat create/continue works against PostgreSQL.
- [ ] Weather/resources unaffected.
- [ ] Restore drill succeeds on a disposable database.
- [ ] Rollback procedure documented and rehearsed.
- [ ] No frontend API contract change without a versioned plan.

## 9. Recommendations

| Priority | Recommendation |
|---|---|
| P0 | Decide the canonical SQLite file; back it up before any change; add `backend/data/` and `**/*.db` to `.gitignore`. |
| P0 | Add a documented backup/restore procedure with a tested restore. |
| P1 | Enable foreign keys in SQLite connections immediately if SQLite remains in use. |
| P1 | Fix message ordering with a deterministic tie-breaker. |
| P1 | Make tests use an isolated database and run schema initialization. |
| P2 | Adopt PostgreSQL 17 + SQLAlchemy 2 + Alembic for production; keep SQLite for tests. |
| P2 | Add ownership columns and constraints in Phase 2, before public auth launch. |
| P3 | Consider encryption at rest or disk encryption for host-level protection. |

No migration, schema change, backup, or restore was executed in Phase 0.
