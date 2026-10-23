# Security and Privacy Audit

**Phase:** 0 — static, read-only  
**Date:** 2026-10-21  
**Reference framework:** OWASP API Security Top 10 (2023), plus LLM-specific risks where applicable.  
**Related:** [`API_CONTRACT_INVENTORY.md`](API_CONTRACT_INVENTORY.md), [`DATABASE_ASSESSMENT.md`](DATABASE_ASSESSMENT.md), [`INTEGRATION_AND_COST_AUDIT.md`](INTEGRATION_AND_COST_AUDIT.md)

---

## 1. Scope and method

Reviewed backend source, schemas, configuration, Dockerfiles, Compose, voice service, client API code, infrastructure configuration, tests, and documentation. Also inspected file permissions, Git ignore rules, running container exposure, and database metadata.

**Not performed:** exploitation, fuzzing, authenticated/unauthenticated live probing, dependency CVE scanning, container image scanning, TLS testing, firewall testing, penetration testing, or review of third-party infrastructure. This is a static baseline, not a certification.

**Severity rubric:**

| Severity | Meaning |
|---|---|
| Critical | Direct, likely compromise of all users/data, or trivially exploitable remote code execution. |
| High | Serious data exposure, authorization bypass, unauthenticated expensive resource abuse, or a production blocker. |
| Medium | Exploitable under plausible conditions, defence-in-depth gap, or significant operational risk. |
| Low | Limited impact, hygiene issue, or requires unusual preconditions. |

## 2. Findings

### S-01 — No authentication on any endpoint

- **Severity:** High (Critical if internet-exposed)
- **Confidence:** Verified
- **Evidence:** `backend/app/main.py:36-111`; all `backend/app/api/v1/*.py`; `ai/voice/main.py`
- **Impact:** Anyone who can reach the service can create conversations, consume Ollama/CPU/GPU resources, call weather, and upload audio. No accountability or abuse control.
- **Likelihood:** Certain for any reachable deployment.
- **OWASP:** API1 (BOLA), API2 (Broken Authentication), API4 (Unrestricted Resource Consumption), API6 (Sensitive Business Flows).
- **Remediation:** Before any network exposure, add authentication (server-side sessions for web; revocable bearer tokens for Android). Protect all routes except liveness/readiness. Add per-user and per-IP rate limits. Document the trust boundary.

### S-02 — No ownership or tenant boundary

- **Severity:** High
- **Confidence:** Verified
- **Evidence:** `backend/app/db/connection.py:31-54` (no user/farm columns); `backend/app/db/conversations.py:28-40` (lookup by ID only); `backend/app/services/chat.py:44-50`
- **Impact:** A conversation ID acts as a bearer token. If an ID appears in logs, screenshots, analytics, or a shared device, another party can continue the conversation. There is no way to list, delete, or scope conversations by user/farm.
- **Likelihood:** Medium (IDs are UUIDv4 and no list endpoint exists, but leakage paths are plausible).
- **OWASP:** API1 (BOLA), API3 (Broken Object Property Level Authorization).
- **Remediation:** Introduce users/farms/memberships; enforce ownership in the service layer for every read/write; add authorization tests for cross-user and cross-farm access. Do not rely on UI filtering.

### S-03 — Unauthenticated, unbounded voice upload endpoint

- **Severity:** High
- **Confidence:** Verified
- **Evidence:** `ai/voice/main.py:18-53`; `ai/voice/Dockerfile` (no `USER`); `docker inspect myfarmai-voice` (`User=`, port `0.0.0.0:8001`); `docker stats` (container running)
- **Impact:** Any reachable client can upload arbitrarily large audio, causing memory/disk/CPU exhaustion, and trigger Whisper inference. There is no file-size, duration, MIME-type, or rate limit. The container runs as root. The model is loaded lazily and the first request can be very slow. Temp files are deleted in `finally`, but a crash or full disk can leave them.
- **Likelihood:** High if port 8001 is reachable; the container publishes on all interfaces.
- **OWASP:** API4 (Unrestricted Resource Consumption), API8 (Security Misconfiguration).
- **Remediation:** Put voice behind the authenticated backend or an internal network; enforce max upload size, allowed MIME types, duration limits, and rate limits; run as non-root with a read-only root filesystem and a size-limited `/tmp`; add timeouts and a queue/concurrency cap; or remove voice from the MVP.

### S-04 — Hardcoded SearXNG secret in configuration

- **Severity:** High
- **Confidence:** Verified
- **Evidence:** `infra/searxng/config/settings.yml:7` (a 64-hex `server.secret_key`); `infra/searxng/.env` (separate secret, git-ignored, mode `600`). The value is not reproduced here.
- **Impact:** The secret is stored in a file that is not git-ignored and could be committed. It may be used for session/CSRF signing depending on SearXNG configuration. Exposure enables forgery or session-related attacks against the search service.
- **Likelihood:** Medium (currently local-only, but one `git add infra/` would commit it).
- **OWASP:** API8 (Security Misconfiguration), secrets management.
- **Remediation:** Rotate the secret now; remove it from the YAML; read `SEARXNG_SECRET` from the environment/secret store; add secret scanning to pre-commit and CI; verify Git history does not contain the value before publishing the repository.

### S-05 — Conversation database is untracked but not ignored

- **Severity:** High (privacy)
- **Confidence:** Verified
- **Evidence:** `git status` shows `?? backend/data/`; `git check-ignore -v backend/data/app.db` returns nothing; `.gitignore:29` only ignores root `data/*`. The file contains 122 conversations / 315 messages.
- **Impact:** A broad `git add .` could commit user conversations, crop/location metadata, and AI responses. This is a data-protection and reputational risk.
- **Likelihood:** High during routine commits.
- **Remediation:** Add `backend/data/`, `**/*.db`, `**/*.sqlite*`, and `infra/searxng/data/` to `.gitignore` before any commit; confirm no DB file is already tracked; review Git history before publishing; back up the DB outside the repo.

### S-06 — No backup or restore procedure

- **Severity:** High (availability/data loss)
- **Confidence:** Verified
- **Evidence:** Repository search found no backup/restore scripts, cron, volume snapshot, or runbook; `DATABASE_ASSESSMENT.md` §7.
- **Impact:** Disk failure, accidental deletion, ransomware, or a bad migration destroys all conversations with no recovery path. Two divergent DB files increase the chance of restoring the wrong one.
- **Likelihood:** Certain over time.
- **Remediation:** Define RPO/RTO; implement encrypted, access-controlled backups outside the repository; test restoration; document ownership and retention. For SQLite use a consistent online backup; for PostgreSQL use `pg_dump` + WAL archiving as needed.

### S-07 — Rate-limit bypass and unbounded in-memory state

- **Severity:** Medium
- **Confidence:** Verified
- **Evidence:** `backend/app/middleware/rate_limit.py:21-29` trusts the first `X-Forwarded-For` value without a trusted-proxy check; `self._requests` is a `defaultdict(list)` keyed by client IP with no eviction of idle keys (`:19`, `:31-65`).
- **Impact:** A client can rotate/spoof `X-Forwarded-For` to bypass limits. Many distinct IPs grow memory without bound (slow DoS). The limit is global per IP, not per route; an expensive `/chat` call has the same budget as a cheap `/resources` call.
- **Likelihood:** Medium.
- **OWASP:** API4.
- **Remediation:** Only trust forwarded headers from a configured proxy; use the socket peer otherwise. Bound the map (LRU/TTL) or use a shared store (Valkey) when multiple workers exist. Add route-specific limits for chat/transcription/login. Return `Retry-After` (already done) and log throttling metrics.

### S-08 — No request-body size or AI concurrency limit

- **Severity:** Medium
- **Confidence:** Verified
- **Evidence:** `backend/app/main.py` (no body limit middleware); `backend/app/schemas/chat.py:5-9` caps only the `message` field after parsing; `backend/app/services/chat.py:61` calls Ollama without a semaphore; `backend/app/services/ollama.py:15-18` creates a client with a timeout but no connection/concurrency limit.
- **Impact:** Large request bodies are buffered before validation. Multiple concurrent chat requests can exhaust RAM/VRAM and make the service unavailable. Ollama itself may queue or OOM.
- **Likelihood:** Medium for a public deployment; low for localhost.
- **OWASP:** API4.
- **Remediation:** Enforce a reverse-proxy body limit and an application-level max; add a bounded semaphore/queue for AI calls; return 429/503 with `Retry-After`; set per-model context and output limits; monitor queue depth.

### S-09 — CORS, host, and transport configuration gaps

- **Severity:** Medium
- **Confidence:** Verified for configuration; exposure depends on deployment
- **Evidence:** `backend/app/main.py:42-48` (`allow_credentials=True`, methods GET/POST/OPTIONS, all headers); `backend/app/core/config_validation.py:40-45` only warns about `*` in production; no `TrustedHostMiddleware`; no TLS in Compose; backend uses host networking.
- **Impact:** If an operator sets a wildcard origin with credentials, browser security assumptions break. Without TrustedHost, Host-header attacks are possible behind a misconfigured proxy. Plain HTTP exposes prompts, tokens (future), and audio.
- **Likelihood:** Medium (configuration-dependent).
- **OWASP:** API8.
- **Remediation:** Use explicit production origins; disable credentials unless cookies are used; add `TrustedHostMiddleware`; terminate TLS at Caddy/Nginx; forward only from a trusted proxy; add HSTS and standard security headers at the proxy.

### S-10 — Inconsistent error contract and verbose logging

- **Severity:** Medium (contract), Low (information disclosure)
- **Confidence:** Verified
- **Evidence:** `backend/app/api/v1/chat.py:39-69` and `weather.py:36-53` nest an error object inside `detail`; `backend/app/schemas/chat.py:45-47` documents a flat object; `backend/app/main.py:83-90` logs `str(e)` and a stack trace for every unhandled exception; request logs include client IP and path.
- **Impact:** Clients misparse errors (Android displays `[object Object]`). Stack traces may include internal paths or upstream details if logs are exposed. IP addresses are personal data in some jurisdictions.
- **Likelihood:** High for client misparse; low for log exposure.
- **OWASP:** API8, privacy.
- **Remediation:** Define one error envelope (`code`, `message`, `request_id`, optional field errors); add exception handlers; never return stack traces to clients; redact secrets/PII from logs; document log retention and access.

### S-11 — No retention, deletion, or export policy

- **Severity:** Medium (privacy)
- **Confidence:** Verified
- **Evidence:** No delete/export endpoints; `messages`/`conversations` grow indefinitely; `DATABASE_ASSESSMENT.md` §6.
- **Impact:** User messages, crop/location, and AI responses are stored indefinitely. This conflicts with data-minimisation and subject-access/deletion expectations in many jurisdictions.
- **Likelihood:** Certain over time.
- **OWASP:** Privacy / API9 (inventory).
- **Remediation:** Define retention by data class; add user-initiated deletion/export; implement cascading deletion (with FK enforcement); document lawful basis and privacy policy before public launch; include backups in deletion policy.

### S-12 — Container hardening gaps

- **Severity:** Medium
- **Confidence:** Verified
- **Evidence:** `backend/Dockerfile` and `ai/voice/Dockerfile` have no `USER`, no `HEALTHCHECK`, no pinned digest; Compose has no `read_only`, `security_opt`, `cap_drop`, memory/CPU limits, or healthchecks; backend uses `network_mode: host`; voice publishes `0.0.0.0:8001`.
- **Impact:** Container compromise yields root in the container and easier host/network access; host networking removes network isolation; resource exhaustion affects the whole host; no health-based restart.
- **Likelihood:** Medium.
- **OWASP:** API8; supply chain.
- **Remediation:** Non-root users, read-only root filesystems where possible, `cap_drop: [ALL]`, `no-new-privileges`, explicit memory/CPU limits after measurement, internal networks, healthchecks, pinned images, and a minimal runtime image.

### S-13 — Unpinned dependencies and no supply-chain gates

- **Severity:** Medium
- **Confidence:** Verified
- **Evidence:** `backend/requirements.txt` and `ai/voice/requirements.txt` have no versions; `python:3.12-slim` and `searxng/searxng:latest` are floating; no CI, SBOM, or dependency scan; no `LICENSE` file.
- **Impact:** A compromised or breaking upstream release can enter production silently; licence obligations are unknown.
- **Likelihood:** Medium over time.
- **OWASP:** API9 (Improper Inventory Management), supply chain.
- **Remediation:** Lock dependencies (`uv.lock`), pin image digests, add `pip-audit`/OSV and image scanning, generate an SBOM, add a licence policy, and require review for upgrades.

### S-14 — Prompt-injection and model-safety exposure

- **Severity:** Medium
- **Confidence:** Possible/verified design gap
- **Evidence:** `backend/app/services/chat.py:29-34` interpolates `language`, `crop`, and `location` into the system prompt without delimiting untrusted values; user text is appended directly (`:56`); no output validation or safety filter; no tools are exposed.
- **Impact:** A user can override instructions or inject conflicting context. Because the model has no tools or data access, the impact is currently limited to misleading agricultural advice and reputational harm, not remote code execution or data exfiltration. Future research/citation features would raise the impact sharply.
- **Likelihood:** High for prompt override; medium for harmful advice.
- **OWASP:** LLM01 (Prompt Injection), LLM09 (Misinformation).
- **Remediation:** Treat user and retrieved content as untrusted data; delimit and label it; keep system policy separate; validate structured outputs; add safety disclaimers and escalation guidance; never let retrieved web content authorize tools/actions. Add prompt-injection regression tests before Phase 6.

### S-15 — SSRF surface is currently absent but imminent

- **Severity:** Informational now / High later
- **Confidence:** Verified absence
- **Evidence:** No URL-fetching code in the backend; SearXNG is not called; no crawler. `INTEGRATION_AND_COST_AUDIT.md` INT-06.
- **Impact:** Phase 6 research will fetch arbitrary URLs. Without controls, it can reach loopback, private ranges, link-local metadata endpoints, and redirect chains.
- **Likelihood:** Not applicable today; high when research is implemented.
- **OWASP:** API7 (SSRF).
- **Remediation:** Implement an allowlist of schemes/ports, DNS revalidation, private/reserved IP blocking at connect time, redirect revalidation, response-size/time limits, and content-type checks. Add SSRF tests before enabling research.

### S-16 — Secret file permissions

- **Severity:** Low
- **Confidence:** Verified
- **Evidence:** `/data/MyFarmAI/.env` mode `664`; `infra/searxng/.env` mode `600`.
- **Impact:** Other local users/groups can read runtime configuration. No paid API key was found, but future secrets would be exposed.
- **Likelihood:** Low on a single-user workstation; higher on shared hosts.
- **Remediation:** `chmod 600` the root `.env`; use a secret manager or Docker secrets in production; never bake secrets into images.

### S-17 — SQL injection

- **Severity:** Low
- **Confidence:** Verified (no exploitable dynamic SQL in application code)
- **Evidence:** `backend/app/db/conversations.py` uses parameterized `?` queries for all user-controlled values; no string interpolation of SQL identifiers/values in application code.
- **Impact:** Current risk is low. Future raw SQL or dynamic sort/filter parameters could reintroduce risk.
- **Likelihood:** Low.
- **OWASP:** API8 / injection.
- **Remediation:** Continue using bound parameters; add lint/review rules against f-string SQL; rely on SQLAlchemy for the PostgreSQL migration.

### S-18 — Unauthenticated resource consumption via chat/weather

- **Severity:** Medium
- **Confidence:** Verified
- **Evidence:** No auth; chat calls local Ollama; weather calls Open-Meteo per request with no cache (`services/weather.py:77-81`); rate limit is global and bypassable.
- **Impact:** An attacker can keep the GPU/CPU busy, exhaust swap, and consume Open-Meteo’s free daily quota (10,000/day), causing denial of service for legitimate users and possible provider blocking.
- **Likelihood:** Medium if exposed.
- **OWASP:** API4, API6.
- **Remediation:** Auth, per-route quotas, caching, timeouts, concurrency limits, and monitoring. Respect provider rate limits.

## 3. OWASP API Security Top 10 mapping

| OWASP category | Applicable findings | Status |
|---|---|---|
| API1 — Broken Object Level Authorization | S-01, S-02 | **Open / High** |
| API2 — Broken Authentication | S-01 | **Open / High** |
| API3 — Broken Object Property Level Authorization | S-02 | Open; no property filtering by role |
| API4 — Unrestricted Resource Consumption | S-03, S-07, S-08, S-18 | **Open / High** |
| API5 — Broken Function Level Authorization | S-01 | Open; no roles |
| API6 — Unrestricted Access to Sensitive Business Flows | S-01, S-18 | Open |
| API7 — Server Side Request Forgery | S-15 | Not present; future risk |
| API8 — Security Misconfiguration | S-04, S-09, S-10, S-12, S-13 | Open |
| API9 — Improper Inventory Management | S-11, S-13 | Open |
| API10 — Unsafe Consumption of APIs | Weather upstream; future SearXNG | Partial: timeouts exist; no schema/caching controls |

## 4. Privacy assessment

**Data collected:** message text, AI responses, optional crop/location, language, conversation timestamps, request IDs, client IP in logs, and optional audio/transcript in the voice service.

**Potential PII:** location + crop + free-text messages can identify a farmer or farm, even without an account. Audio can contain voices and background speech. IP addresses are personal data in some jurisdictions.

**Current controls:** local-only AI, no analytics/telemetry found in web/android/backend, `.env` not tracked, SQLite file local, voice temp file deleted.

**Gaps:** no privacy notice, lawful basis, retention schedule, deletion/export, access control, encryption at rest, or data-processing register. No evidence of GDPR/India DPDP Act compliance assessment.

**Recommendation:** Complete a data-classification and retention exercise before public launch; minimise location precision; avoid logging message content; document subprocessors (Open-Meteo, future search engines); provide deletion/export; include backups in retention.

## 5. What this audit does not prove

- The backend is **not** claimed to be secure. A limited static review cannot prove the absence of vulnerabilities.
- No exploit was attempted; severity is based on code and configuration.
- No dependency CVE scan, container scan, TLS scan, or penetration test was performed.
- Firewall state could not be read without interactive sudo; external reachability of ports 8000/8001 is unknown.
- No live authentication/authorization tests exist because authentication is not implemented.

## 6. Prioritised remediation

| Order | Action | Findings |
|---|---|---|
| 1 | Remove/rotate the hardcoded SearXNG secret; add secret scanning | S-04 |
| 2 | Ignore/back up the conversation DB; prevent committing data | S-05, S-06 |
| 3 | Secure or disable the voice endpoint | S-03 |
| 4 | Add authentication and ownership before any network exposure | S-01, S-02 |
| 5 | Add backup/restore and retention/deletion | S-06, S-11 |
| 6 | Fix rate limiting, body limits, and AI concurrency | S-07, S-08, S-18 |
| 7 | Harden CORS/host/TLS and containers | S-09, S-12 |
| 8 | Standardise errors/logging and add CI supply-chain checks | S-10, S-13 |
| 9 | Add prompt-injection and SSRF controls before AI research | S-14, S-15 |
| 10 | Restrict `.env` permissions and document secret management | S-16 |
