# Cloud Cost & Quota Policy

Status: PROPOSED for the deployment phase; the ₹0 rules below are BINDING now.
Sources: provider pricing pages fetched 2026-11-03 (list in
`FREE_TIER_COMPARISON.md` §5).

## 1. Absolute financial rules (binding, directive §2)

1. ₹0 upfront spend; no billing activation; no card entry anywhere.
   - **Owner exception (2026-11-04)**: a one-time charge of **₹1–₹10 minimum
     via UPI/Paytm** is permitted where a service genuinely requires it — the
     automation agent may open the browser to the payment page, but the owner
     completes the UPI/PIN step personally (never automated, never logged).
     Every such payment must be recorded in `ACCOUNT_SETUP_LOG.md` (service,
     amount, purpose) and must be one-time — no subscriptions, no auto-renew,
     no card on file.
2. No free-trial activation where a trial auto-converts to paid.
3. Quota exhausted ⇒ stop/degrade gracefully (local AI, saved knowledge,
   read-only lists) — never generate charges.
4. Any service requiring card verification = BLOCKED, recorded in
   `CLOUD_ACCOUNT_INVENTORY.md` (currently: AWS by owner decision, Koyeb, GCP
   billing activation, any domain purchase).

## 2. Per-provider quota cards (verified 2026-11-03)

| Provider | Free quota | Exhaustion behavior |
|---|---|---|
| Cloudflare Pages | 500 builds/mo, 1 concurrent, 100 projects | Future builds blocked until next month window |
| Cloudflare Workers | 100k req/day (00:00 UTC reset), 10 ms CPU | HTTP **1027** to all further requests that day; Page can be fail-open (bypasses Worker — frontend keeps serving) or fail-closed (secure criticals) |
| Cloudflare Pages Functions | Counted against the same Workers quota | Same as Workers |
| Neon (proposed) | 100 CU-hrs/project/mo, scale-to-zero | Project suspends only on quota exhaustion; data persists |
| Supabase (reference) | 500 MB DB, 2 projects | **1-week inactivity pause** (mitigation: keep at least one scheduled project activity or run heartbeat queries if this provider is ever chosen) |
| Prisma Postgres (reference) | 200k operations/mo, 2 GB | Overage only on paid plans — Free simply hits the cap (safe) |
| Netlify (reference) | 300 credits/mo (~20 deploys, ~15 GB bandwidth) | Deploys blocked at credit cap |
| Vercel Hobby (reference) | 100 GB transfer, 1M CDN req | Hard caps, no overage billing — BUT non-commercial clause makes it ineligible for public MyFarmAI |

## 3. Graceful degradation ladder (MyFarmAI behavior when quota hits)

1. **Cloud AI quota (§10 directive)**: 20 successful cloud queries/user/10h
   rolling window, enforced server-side and atomically in Postgres. When it
   hits: local AI answers, saved conversation retrieval, non-generative
   offline fallback. Failed/erroring requests consume nothing.
2. **Workers 1027 day**: static Pages content still serving (fail-open route
   mode for anything non-security-critical).
3. **Neon CU-hours exhausted**: app shows read-only mode for farmer data saved
   locally (local-first architecture guarantees offline function); writes
   queue locally and sync when quota resets (see `DATA_SYNCHRONIZATION_POLICY.md`).
4. **Build quota exhausted**: existing deployed site keeps running; deploys
   resume next window.

## 4. Monitoring (to implement when the backend has a public host)

- Server-side counters per user per window (atomic UPDATE ... WHERE remaining>0).
- Admin-visible usage dashboard before public launch.
- Zero-tolerance checklist before every change: no new paid flags in provider
  consoles; no spend notifications configured = constant reminder that only
  Free exists.

### 4.1 Cloud-AI quota counter — IMPLEMENTED 2026-11-04 (MF-C-Q01)

The §10 counter is implemented (works: `backend/app/services/ai_quota.py`,
table: `ai_quota_counters`, migration: `c8d9e0f1a2b3`; coverage:
`backend/tests/test_ai_quota.py`).

- Table: one row per `(user_id, window_start)`; window_start is an aligned
  UTC bucket (`epoch // window_hours`), so windows are stable, indexable and
  settled (the "rolling window" is approximated by aligned buckets — fixed
  boundaries, not a sliding start; documented limitation).
- Atomicity: single `INSERT ... ON CONFLICT (user_id, window_start)
  DO UPDATE SET used_count = used_count + 1 WHERE used_count < limit` —
  admission decided by affected-rowcount; no read-then-increment race.
  Supported dialects: PostgreSQL + SQLite (same statement shape).
- Activation flag: `cloud_ai_enabled` (default **False**) — flag-off, the
  counter never runs and nothing changes for today's local-Ollama path.
  Defaults: `cloud_ai_quota_limit=20`, `cloud_ai_quota_window_hours=10`.
- Endpoint wiring: `/api/v1/chat` consumes a slot before generation;
  denial → HTTP 429 `AI_QUOTA_EXCEEDED`; quota-counter DB failure →
  HTTP 503 `AI_QUOTA_UNAVAILABLE` (fail-closed — an uncounted cloud call is
  never allowed).
- Known limitation (disclosed in the service docstring): the slot is
  consumed just before generation, so it counts *intent*, not confirmed
  success. §10's "successful queries" exactness (decrement on failure)
  lands when the cloud-LLM provider is wired.
- Test evidence 2026-11-04: `test_ai_quota.py` 11/11 pass;
  `test_chat.py` 13/13 pass (no wiring regression). Full-suite evidence
  pending in the session log (272-test baseline).
- **Admin usage view (§4 "admin-visible usage dashboard", API level — added
  2026-11-04)**: `GET /api/v1/admin/ai-quota` (admin role enforced
  server-side, same gate as the selfie review queue) returns per-user
  usage for the current window (`used` / `remaining` / `limit`) plus the
  window metadata. Service query: `ausage_rows()`. A UI dashboard on top of
  this endpoint remains a pre-launch item. Coverage: 3 async-mode tests in
  `test_ai_quota.py` (14/14 total after this addition).

## 5. Trial/credit register

- GCP: **no trial started** ($300 banner dismissed, billing never activated).
- Nothing else holds credits; no cards on file anywhere.
