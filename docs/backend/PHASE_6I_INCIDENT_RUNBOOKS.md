# Phase 6I — Operational Runbooks (Incident Response)

**Status:** OPERATIONAL DOCUMENTATION (procedures take effect when production deployment exists) · **Date:** 2026-10-31

Severity model: **S1** = service down / data exposure / data loss; **S2** = degraded core flow (chat, auth, weather); **S3** = degraded auxiliary flow (research, vision); **S4** = cosmetic/log noise.

Detection: compose healthchecks, CI, and (once 6H lands) monitoring alerts. Every incident gets: detect → contain → recover → verify → document (append to an incident log in `docs/engineering/incidents/`).

## 1. Backend outage (S1)
- **Detect:** `GET /health` failing; compose healthcheck failing; users report errors.
- **Contain:** none needed (read-only outage); if the container is crash-looping, `docker compose logs backend` first — do not delete volumes.
- **Recover:** `docker compose up -d backend` (or host restart if the host is down). If a bad release: `docker compose up -d --build backend` on the previous git tag.
- **Verify:** `/health`, `/api/v1/health`, login round-trip, one chat turn.
- **Document:** timeline, root cause, restart reason.

## 2. Database outage (S1)
- **Detect:** backend 500s with `OperationalError`/connection errors; `pg_isready` failing.
- **Contain:** stop writes (`docker compose stop backend`) to avoid half-written state.
- **Recover:** if the postgres container is unhealthy: inspect logs; if the volume is corrupt: restore latest backup per Runbook 9 (Phase 6L drill). **Never** run destructive migration/vacuum commands against the live volume without a verified backup.
- **Verify:** row counts vs last backup record; login + farm creation round-trip.
- **Document:** data-loss window = time since last successful backup (RPO).

## 3. AI model unavailable (S2)
- **Detect:** chat 503 `AI_UNAVAILABLE` / `VISION_MODEL_UNAVAILABLE`; `curl 127.0.0.1:11434/api/tags` fails.
- **Contain:** none (chat already fails open with clear errors).
- **Recover:** restart Ollama on the host; confirm `api/tags` lists enabled models; one warm-up request (first call may time out on cold load — known).
- **Verify:** one chat turn + one vision call (serial — never concurrent Ollama workloads).

## 4. Weather provider unavailable (S3)
- **Detect:** `GET /weather` errors; chat proceeds without weather block (by design — 5C fail-open).
- **Contain/recover:** none required; Open-Meteo outages degrade gracefully. If persistent, check rate-limit/quota on the Open-Meteo account tier.
- **Verify:** one weather call after recovery; confirm chat re-gains the weather block.

## 5. Search provider unavailable (S3)
- **Detect:** `GET /research` → 503 `RESEARCH_UNAVAILABLE`.
- **Recover:** restart the SearXNG container (loopback/internal only); confirm JSON format still enabled in settings; one search round-trip.
- **Verify:** results carry verbatim http(s) URLs + `retrieved_at`.

## 6. Storage exhaustion (S2)
- **Detect:** disk alerts (6H) or `df -h` below ~10% on `/` or `/data`.
- **Contain:** stop backup rotation before deleting anything; identify top consumers (`docker system df`, `backend/data`, logs).
- **Recover:** prune only approved caches; never delete `postgres_data` volume, `/data/MyFarmAI-backups`, or model assets without owner approval.

## 7. Authentication incident (S1)
- **Detect:** spike in 401s/auth failures, unknown sessions, audit-log anomalies (FARM_MEMBER_* events by unexpected actors).
- **Contain:** revoke the affected sessions (sessions table / session revocation), rotate any exposed credentials, if needed stop backend to freeze state.
- **Recover:** force password resets for affected users; review audit log for lateral movement.
- **Verify:** login works; suspicious sessions rejected.
- **Document:** NEVER disclose internal incident details publicly without owner authorization.

## 8. Suspected data exposure (S1)
- **Detect:** unusual read patterns, external reports, logs showing data leaks.
- **Contain:** stop the leaking component (often backend or proxy); revoke sessions; snapshot logs as evidence BEFORE rotating them.
- **Recover:** fix the leak, assess scope (which users/farms/conversations), notify owner first — user communication only on owner instruction.
- **Document:** full timeline + evidence preserved; owner decides external disclosure.

## 9. Failed deployment (S2)
- **Detect:** healthcheck failing post-deploy; error-rate spike.
- **Recover:** rollback = previous image/tag via `docker compose up -d --build` at the previous git commit; database migrations (if any) rolled back per the migration's downgrade path — never hand-edit the production schema.
- **Verify:** health + one core flow (login, chat).

## 10. Backup failure (S2)
- **Detect:** nightly pg_dump cron reports non-zero / missing file.
- **Contain:** none; **do not** delete old backups to "make space" without owner approval.
- **Recover:** fix root cause (disk full, credentials), re-run backup manually, verify with a test restore into a scratch database.
- **Verify:** `pg_restore --list` succeeds on the new dump.
