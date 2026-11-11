# Backup and Restore Procedure (Gate F)

**Applies to:** MyFarmAI production PostgreSQL database
**Audience:** Project owner / operator
**Status:** **BLOCKED — procedure written, restore drill not executed.**

A backup is not verified until a restore drill passes. Until then, treat the
production database as having no tested recovery path.

---

## 1. Rules

- Backups live **outside the Git repository**, on encrypted storage you control.
- Backup files contain personal data (email addresses, farm locations, chat
  transcripts). Restrict access: directory `0700`, files `0600`, owned by the
  operator account.
- **Never print the connection string.** Read it from the environment or a
  secret manager into a variable and pass it to `pg_dump` via `PGPASSWORD` /
  `--dbname`, never via `echo`.
- Never commit a backup. `*.dump`, `*.sql`, `*.sql.gz` are not source.
- Never restore over production. A drill runs against a **separate test
  database** only.
- Record the timestamp, size, and result of every backup attempt.

## 2. Take a backup

Set the connection string from your secret manager into the environment for the
current shell only. Do not paste it into a command line, a file, or a chat.

```bash
# Values come from the platform secret manager / operator vault.
export PGHOST="$DB_HOST"
export PGPORT="${DB_PORT:-5432}"
export PGUSER="$DB_USER"
export PGPASSWORD="$DB_PASSWORD"
export PGDATABASE="$DB_NAME"

BACKUP_DIR="/data/MyFarmAI-backups"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$BACKUP_DIR"
chmod 700 "$BACKUP_DIR"

pg_dump --format=custom --no-owner --no-privileges \
  --file="$BACKUP_DIR/myfarmai-$STAMP.dump"

chmod 600 "$BACKUP_DIR/myfarmai-$STAMP.dump"
ls -l "$BACKUP_DIR/myfarmai-$STAMP.dump"
```

Record the result:

```bash
printf '%s  %s  %s\n' "$STAMP" "$(stat -c %s "$BACKUP_DIR/myfarmai-$STAMP.dump")" "ok" \
  >> "$BACKUP_DIR/backup-log.txt"
chmod 600 "$BACKUP_DIR/backup-log.txt"
```

Expected: `pg_dump` exits `0`, the file is non-empty, and `pg_restore --list`
can read it:

```bash
pg_restore --list "$BACKUP_DIR/myfarmai-$STAMP.dump" | head
```

If any step fails, record `failed` in the log and do not delete the previous
backup.

## 3. Retention

| Tier | Keep | Rationale |
|---|---|---|
| Daily | 7 | Recover from a bad deploy or data error within the week. |
| Weekly | 4 | Recover from a slow-burn problem. |
| Monthly | 3 | Baseline for longer outages. |

Delete only after a newer backup of the same tier has been verified with
`pg_restore --list`. Never delete the most recent backup, and never delete
backups to free space without owner approval.

## 4. Restore drill (required to close Gate F)

**Never run this against the production database.** Create a separate test
database first, for example `myfarmai_restore_test`.

```bash
export PGHOST="$DB_HOST" PGPORT="${DB_PORT:-5432}" \
       PGUSER="$DB_USER" PGPASSWORD="$DB_PASSWORD"
export PGDATABASE="myfarmai_restore_test"   # NOT the production database

pg_restore --clean --if-exists --no-owner --no-privileges \
  --dbname="$PGDATABASE" "$BACKUP_DIR/myfarmai-$STAMP.dump"
```

Verify:

```sql
-- Schema and tables
\dt
-- Expected core tables present:
--   users, sessions, refresh_tokens, farms, farm_plots, farmer_profiles,
--   conversations, messages, audit_events, verification_events

-- Indexes restored
SELECT count(*) FROM pg_indexes WHERE schemaname = 'public';

-- Row counts match the source snapshot
SELECT count(*) FROM users;
SELECT count(*) FROM farms;
SELECT count(*) FROM conversations;

-- The application can read restored data: point a throwaway backend at the
-- test database and call /health/ready, then log in with a known test account.
```

Record the drill outcome next to the backup log:

```
<timestamp>  restore-drill  source=<dump file>  target=myfarmai_restore_test  result=pass|fail
```

Close Gate F only when a drill passes and the production database was not
touched.

## 5. What is still missing

- **No automated schedule exists.** Backups are manual until a scheduled job is
  added.
- **No restore drill has been run.** Gate F stays **BLOCKED**.
- **No off-host copy is configured.** A backup on the same host as the database
  does not survive host loss.
- The application has no automated restore test in CI.

## 6. Minimum bar before public launch

1. One successful manual backup with a recorded log entry.
2. One successful restore drill into a separate test database, with the checks
   in §4 passing.
3. A schedule (cron or provider job) that runs daily and logs results.
4. A copy stored off the database host.
