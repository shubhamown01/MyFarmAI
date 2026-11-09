# MyFarmAI Rollback Procedure

**Status:** Adopted (2026-11-09) · Worker: release engineer / DevOps

## Scope

Covers: backend (Catalyst AppSail image), web (Catalyst Slate), Android APK
(distributed as GitHub Releases assets), and the Neon production database.

## Backend

Rolled images must satisfy: **migration version ≤ the DB's current
alembic_version** (an image older than the DB schema will crash-loop on
startup).

1. Deploy an image matching a Git commit via
   `docs/deployment/DEPLOYMENT_RUNBOOK.md` (docker build + `docker save` +
   `zcatalyst-cli deploy appsail`).
2. If the target image predates the DB migration head:
   - **Never DO NOT run `alembic downgrade` blindly on production without owner approval**;
     it destroys schema/data (e.g. the `feedback` migration has a downgrade).
   - Prefer strategy B: keep the DB and only rollback code paths that do not
     need the new schema (e.g. temporarily stop the feedback router by
     building an image from an earlier commit **plus** the missing migration files
     in `backend/alembic/versions/`).
3. Verify after rollback: `/health/ready` 200, `database: ok`.

## Web (Slate)

Roll back by re-deploying the parent commit's web bundle from `web/`
(`slate:deploy` pipeline documented in runbook). Web targets are
forward-compatible with the backend (static files calling `/api/v1/…`).

## Android APK

1. Find the previous signed APK (GitHub Releases → Assets → `.apk` + `.sha256`).
2. Verify checksum; publish as a new release with updated versionCode if you
   must fix the same content; users cannot sideload a lower-version install
   without uninstalling.
3. Communicate via release notes ("roll back to vX and reinstall" if needed).

## Database (Neon Postgres)

NEVER destructive-rollback without owner approval.

1. Take a fresh `pg_dump` (from Neon console, or `pg_dump --host=<pooler>` with
   the connection string) **before** any change.
2. For a broken migration: `alembic downgrade <known-good>` (data-destructive
   ops flagged in the migration file; owner approval required) or clear the
   offending migration via a targeted `alembic stamp` + manual reverse-DDL
   script if the data loss is unacceptable.
3. Restore: `psql $DATABASE_URL < dump.sql` on a new Neon branch first
   (`init` from dump), verify, then swap branch endpoints in the deployment
   env (owner action).

## Gate: verify rollback works

After any rollback attempt, re-check `/health/ready` and the login flow
against the rolled-back artifacts BEFORE declaring the service healthy.

## History

Record every rollback in `docs/deployment/ACCOUNT_SETUP_LOG.md` with: trigger,
artifacts rolled to, DB state, verification evidence.
