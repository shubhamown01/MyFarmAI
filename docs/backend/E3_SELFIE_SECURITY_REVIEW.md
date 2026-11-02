# E3 Selfie/Liveness Verification — Security Design Review

**Task:** MF-E3-SEC · **Reviewer:** @security-engineer · **Date:** 2026-11-02
**Status:** REVIEW COMPLETE — implementation-bound requirements below. Not a code review; E3 code does not exist yet.
**Read-only review.** Evidence gathered from: `MYFARMAI_FINAL_PHASE_STATUS.md`, `backend/app/api/v1/auth.py`, `backend/app/services/verification.py`, `backend/app/services/auth.py`, `backend/app/services/oauth.py` (E2 claim flow), `backend/app/db/models/identity.py`, `backend/app/api/v1/vision.py` (upload-validation precedent), `backend/app/core/config.py`, `backend/app/middleware/csrf.py`, `backend/app/middleware/rate_limit.py`, `docs/engineering/AUTHZ_MATRIX.md`.

**Note on directive §5:** the owner's directive text (§5 LIVE SELFIE AND LIVENESS VERIFICATION) is **not present verbatim in the repo**; only the paraphrase in `MYFARMAI_FINAL_PHASE_STATUS.md` §2.4/§4.4 exists. This review enforces the paraphrase plus the E3 invariants listed in the task brief. If the full directive text is imported later, re-check §5.3 bullet-by-bullet (Section D).

---

## A. Threat Model (STRIDE-aligned abuse cases)

| # | Threat | Description | Primary controls (per Section C) |
|---|--------|-------------|-----------------------------------|
| T1 | **Replay of an old photo** | Attacker uploads a photo taken earlier (their own or someone else's) instead of a fresh capture. | Server-issued single-use challenge bound to session; **honest statement:** with no automated liveness on 2 GiB VRAM, freshness cannot be cryptographically proven server-side. The challenge raises attacker cost (must be performed interactively at capture time); the human reviewer verifies the challenge was actually performed in the frame. This is the directive-approved control; it must be documented as such, never claimed as cryptographic liveness. |
| T2 | **Screenshot-of-screen / picture-of-picture** | Attacker displays a photo/video on another screen or printed paper and captures that. | Randomized two-action challenge combos (hard to satisfy with a static image); reviewer inspects for moiré/angle artifacts; qwen3-vl assist may flag (hint only, non-decisive). |
| T3 | **Deepfake / injected video stream** | Virtual camera or real-time face swap presented as a `getUserMedia` frame. | Out of detection scope for this hardware tier. Controls: reviewer judgment, challenge compliance, retry cap + manual lock. Must be documented as a known, accepted limitation — do NOT claim defense. |
| T4 | **IDOR on other users' selfies** | User A reads or writes user B's capture/verification state. | All selfie rows carry `user_id`; every non-admin query filters by the session user in SQL (deny-by-default, per AUTHZ_MATRIX pattern); cross-user access returns **404**, not 403. Admin endpoints are a separate role-gated surface with per-view audit. |
| T5 | **Admin-queue abuse** | Admin (or anyone who gets the admin session) silently approves identities, or browses the selfie archive without accountability. | Role check server-side (`admin` role → else 403, mirroring `auth.py:259-263`); **every** admin image view, approval, and rejection is an audit event with actor id + review id + decision + reason; raw-file deletion is itself audited. |
| T6 | **Storage exposure** | Selfies readable via web root, repo, backups, or world-readable paths. | Storage outside repo and outside any web-served volume; random unguessable filenames (uuid4 + content-hash suffix); `0700` dir / `0600` files; never returned as URL/path in any API response; explicitly excluded from backup scope for raw captures (only decisions + audit persist past TTL). |
| T7 | **Timing / enumeration** | Attacker learns account states (who is pending, who was rejected) or probes selfie endpoints for other users. | Uniform error envelopes; no state distinction in responses to the user; selfie-upload responses are identical regardless of internal review state ("received, pending review"); no user listing exposed; 404 semantics for cross-user ids. |
| T8 | **Upload DoS / resource exhaustion** | Giant files, decompression bombs, upload floods, challenge-endpoint floods. | Existing 10 MB body cap (`max_request_body_size`, config.py:177) + 5 MiB application cap; magic-byte sniffing before decode (vision.py:39-45 pattern); Pillow decode with explicit `Image.MAX_IMAGE_PIXELS` guard; dimension bounds; per-user single in-flight pending capture; per-user + per-IP rate limits on both the challenge and upload endpoints (existing `RateLimitMiddleware` + new route-specific limits). |
| T9 | **Consent bypass** | Capture/upload proceeds without a durable consent record. | Upload endpoint rejects (422 `CONSENT_REQUIRED`) unless a matching `consent_records` row exists for this user + policy_version, checked server-side before accepting bytes. |
| T10 | **Challenge replay/reuse** | Same challenge id used for multiple uploads; challenge obtained by one user reused by another. | Challenge rows: single-use, consumed atomically on upload, bound to `user_id` + session, short TTL, server-generated random selection from pool. |
| T11 | **Prompt-injection via image** | Image content instructs the qwen assist to output "approved". | Assist is flag-only (enum), non-decisive, never auto-approves/rejects; output stored as a hint on the review row, labeled as machine hint; its text (if any) is fixed-enum, never free-form rendered to the reviewer as instruction. |

Residual risk accepted by design (must appear in the user-facing policy text and ADR): automated liveness is **not claimed**; final integrity control is a human reviewer.

---

## B. Verdict per Proposed-Flow Element

| Flow step | Verdict | Notes |
|---|---|---|
| 1. After E1 email-OTP verify / E2 OAuth → account in `pending_verification` | **MODIFIED** | Semantics in code today: E1 `verify_email_otp` sets `is_active=True` (verification.py:181) and E2 activates immediately too — sessions are already live at that point. E3 must add a `verification_status` lifecycle (`pending` → `approved` / `rejected` / `locked`) that **gates farmer features and onboarding progression while keeping the session usable** (the selfie upload itself needs an authenticated session). Do not reuse `is_active` for this — it is consumed by `validate_session` (auth.py:496) and flipping it would log pending users out. Where the status lives (column on `users` vs. derived from latest `selfie_verifications` row) must be settled in the migration; a derived column on `users` is recommended for query simplicity. Owner-pre-approved schema tables are `selfie_verifications`, `verification_events`, `consent_records`; a small `users` alteration may still be needed — confirm with the owner (Section F, Q1). |
| 2. Consent disclosure + `consent_records` | **REQUIRED** | Server-side enforcement, not just UI (see C-7). |
| 3. Camera request at verification time, one fresh frame | **REQUIRED** | Client-side obligation; server cannot verify permission timing. Client requirements in C-3; the *enforceable* server half is the challenge (step 4). |
| 4. Server-issued challenge BEFORE capture; upload carries challenge id | **REQUIRED — with tightening** | See C-4: single-use, session-bound, short TTL, two-action randomized combos, atomic consumption, never pre-revealed beyond the issuing response. |
| 5. qwen3-vl:2b sanity assist | **MODIFIED (narrowed)** | Hint-only enum output (`ok` / `flag_picture_of_picture` / `flag_low_quality` / `error`), stored on the review row, displayed to the reviewer as a labeled machine hint. Never auto-approve, never auto-reject, never a free-text field, never exposed to the user. If the model is unavailable, proceed with review anyway (assist is optional). |
| 6. Manual-review queue; approval activates; rejection keeps pending + N retries | **REQUIRED — with tightening** | Retry cap N (recommend 3) then `locked` requiring admin reset; every transition audited; admin image access through a dedicated authenticated endpoint that streams bytes, never a static file URL (see C-9). |
| 7. Retention: raw selfie deleted after decision + TTL; decision + audit persist | **REQUIRED** | Recommend TTL = 7 days post-decision (owner may shorten; do not lengthen without DPDP justification). Hard-delete job + deletion audit event; see C-11. |

Nothing in the proposed flow is rejected outright; every element needed tightening only.

---

## C. Implementation Requirements (numbered, testable)

### Endpoints & contracts

**C-1. `POST /api/v1/verification/selfie/challenge`** — authenticated session of an account with `verification_status='pending'`. Issues one challenge: `{challenge_id, actions: [action_1, action_2], expires_in}`. Server-side: random selection of exactly 2 distinct actions from a pool of ≥6 (e.g., turn-head-left, turn-head-right, blink, raise-hand, show-N-fingers with N=random 1–5 embedded in the action text, nod); row stores `user_id`, `issued_at`, `expires_at` (TTL 5 min), `consumed_at=NULL`. Rate limit: 10/hour/user and existing per-IP limit. Approved accounts calling this → `409 VERIFICATION_NOT_PENDING`. Not authenticated → 401.

**C-2. `POST /api/v1/verification/selfie`** — multipart upload, authenticated pending-account session, body fields: `challenge_id` + file. Server order of operations (all before persistence):
1. Consent check: a `consent_records` row exists for (user, `selfie_liveness`, current `policy_version`) — else `422 CONSENT_REQUIRED`.
2. Challenge check: row exists, unconsumed, unexpired, `user_id` matches the session user, account still pending — else `422 CHALLENGE_INVALID` (uniform error for expired/used/wrong-user/missing; no distinctions that aid probing).
3. Read bytes into memory; enforce ≤ **5 MiB** (reuse `_MAX_IMAGE_BYTES`); magic-byte sniff for jpeg/png/webp (reuse `vision.py:_sniff_format`); reject otherwise `415`.
4. Decode with Pillow to validate **min 512×512, max 4096×4096** actual pixel dimensions; set `Image.MAX_IMAGE_PIXELS` guard (≤ 30 MP) against decompression bombs → `422 IMAGE_DIMENSIONS_INVALID`.
5. Strip metadata: re-encode the image (dropping EXIF incl. GPS) before writing to disk. If re-encoding fails → `422 IMAGE_UNPROCESSABLE`.
6. Atomically consume the challenge (single UPDATE ... WHERE consumed_at IS NULL; zero rows → `CHALLENGE_INVALID`).
7. Write file (C-6), create `selfie_verifications` row (user_id, challenge_id, storage_filename, byte_size, dimensions, status=`pending_review`, assist_hint), audit event, return **200** `{"status": "received", "review_state": "pending_review"}` — identical shape for every accepted upload.
Only one unconsumed/pending capture per user at a time; a new challenge invalidates the prior unconsumed one.
**Rejected/not-pending accounts** uploading → uniform `409 VERIFICATION_NOT_PENDING`.

**C-3. Client obligations (web + Android, spec'd into APP_FLOW/onboarding docs):** camera permission is requested **only** after the consent screen and challenge display; no photo-picker/gallery path exists in the verification UI; the challenge actions are displayed before and during capture; the capture is taken from the live camera stream; on upload failure the client discards the frame (no local persistence of the raw frame beyond the in-flight upload).

**C-4. Challenge hardening:** never return the challenge actions in any list/log/audit payload beyond the issuing response to that session; expired/unconsumed challenges are deleted or nulled by the retention job (keep only the counter). Challenge selection uses `secrets`-grade randomness.

**C-5. Status endpoint `GET /api/v1/verification/selfie/status`** — returns own status only: `{verification_status, retries_remaining}`. Never returns reviewer names, reasons visible to the user beyond a generic rejection message, timestamps of review, or any file reference.

### Upload validation summary (testable limits)

**C-6.** max bytes 5 MiB · MIME by magic bytes only (jpeg/png/webp) · dimensions 512–4096 px square-bounded · EXIF stripped on ingest · `Image.MAX_IMAGE_PIXELS` guard set at import. Content-Type headers are untrusted (vision.py precedent).

### Storage

**C-7.** Raw captures live under a configured path, default `/data/MyFarmAI-data/selfies/` (outside the repo, outside any volume that nginx/Caddy serves, not inside `backend/`). Directory `0700` owned by the backend container user; files `0600`; filenames = `uuid4()` (never derived from user id/email; the challenge id is never the filename). The path is a `Settings` field with a production validator asserting the directory is not inside the repo root and not under any static-mount path. Files are never served by any router, never copied to tmpfs-shared locations, and any transient processing happens in memory only.

### Encryption at rest

**C-8. Single-host Docker deployment — recommended: encrypted volume (LUKS/dm-crypt on the host volume holding `/data/MyFarmAI-data`), not application-level encryption.** Trade-off, stated honestly:
- *Encrypted volume:* transparent to app code, no key-handling bugs, protects against disk/backup theft and off-host exposure. Does **not** protect against root compromise of the same host (key is in RAM). This is the honest limit for a single-host zero-cost deployment.
- *Application-level AES-GCM:* adds key-management burden (key from Docker secret/env, same host → mostly security theater against host compromise), plus code risk for marginal gain.
- Backup target for raw captures must be on the same encrypted volume or excluded entirely (raw captures die at TTL anyway — prefer excluded).
If the host disk is already fully encrypted, an additional volume is unnecessary; record which is true in the deployment docs. Do not claim "encrypted at rest" in user-facing policy beyond what is actually deployed.

### Consent records schema requirements

**C-9.** `consent_records`: `id`, `user_id` (FK, NOT NULL), `consent_type` (e.g. `selfie_liveness`), `policy_version` (string, NOT NULL — e.g. `"2026-11-e3.1"`), `granted_at` (tz-aware, server time), `client_ip` (from `_client_ip`, trusted-proxy-aware), optional `user_agent`. Append-only (no updates/deletes); a new policy version creates a new row. **Server enforces** consent before upload (C-2 step 1); the consent UI must present, before registration proceeds and before the camera opens: (a) that a live selfie with a liveness challenge is **mandatory**, (b) purpose (identity verification only), (c) who reviews it (human admin), (d) retention period and deletion promise, (e) that it is never used for model training, advertising, or public display. Directive requires this disclosure **BEFORE registration** — i.e., the mandatory-step disclosure is shown at the start of the signup flow, and the granular consent screen immediately before capture; both must record the `policy_version` they displayed.

### Audit events (via `AuditRepository`, flat ADR-009 envelope conventions)

**C-10.** Required events, with actor id and object id only (no biometric data, no file paths, no image bytes in payloads):
`SELFIE_CHALLENGE_ISSUED`, `SELFIE_UPLOADED` (user), `SELFIE_CONSENT_GRANTED` (user; include policy_version), `SELFIE_REVIEW_VIEWED` (admin — **per image view**), `SELFIE_APPROVED` (admin + reason optional), `SELFIE_REJECTED` (admin + reason category), `SELFIE_RETRIES_LOCKED`, `SELFIE_RAW_DELETED` (job + actor context), `SELFIE_STATUS_LOCKED_RESET` (admin).

### Admin review queue authorization

**C-11.** Queue + decision endpoints under `/api/v1/admin/verification/...`, role `admin` enforced server-side (403 otherwise — mirror `auth.py:259-263`). Image access via `GET /api/v1/admin/verification/selfies/{id}/image` which authenticates, checks role, streams bytes from the storage path, and audits `SELFIE_REVIEW_VIEWED` — **no static file serving, no presigned URLs, no public or guessable URL ever exists.** Decision endpoint accepts `{decision: approve|reject, reason_category, note?}`. CSRF: existing `CSRFOriginMiddleware` (Origin/Referer rejection on cookie-carrying unsafe requests) applies to admin web use automatically; the Android admin path uses bearer auth and is outside cookie scope. Approval/rejection flip `verification_status` and audit per C-10; approval must also emit the onboarding-unblock event consumed by the E5 state machine.

### Rate limits

**C-12.** Per-user: challenge 10/hour; uploads 10/hour; retries (rejections) cap at 3 then `locked`. Per-IP: reuse existing middleware limits; both routes must be explicitly included in the auth-tier rate-limit set (they are pre-auth-of-feature but post-auth-of-session). Global body cap 10 MB already enforced by middleware — verify chunked-encoding bypass behavior is covered by existing tests.

### Never returned in any API response

**C-13.** Storage paths or filenames; any URL to a raw image (including relative ones); image bytes to the uploading user; other users' verification data; challenge action lists outside the issuing response; reviewer identity; assist-hint details; the reason text of a rejection beyond a fixed generic message. Error envelopes follow the flat ADR-009 shape with the existing generic `error_code` discipline.

### Retention / deletion job

**C-14.** A periodic job (same scheduling pattern as the existing nightly backups): finds `selfie_verifications` rows with a terminal status (`approved`/`rejected`) older than the TTL (default 7 days, `Settings` field), deletes the file (unlink; log-and-continue on missing file), nulls/overwrites the storage reference, and audits `SELFIE_RAW_DELETED`. The job must also purge expired unconsumed challenges. Deletion must be verified by a test asserting the file is gone and the row's reference is cleared while the decision + audit persist. A failed deletion retries and alerts; it must never silently count as deleted.

---

## D. DPDP / Directive §5.3 Checklist

| §5.3 requirement (paraphrase) | Mapped requirement | Status |
|---|---|---|
| Camera permission only at verification time | C-3 client obligations; no camera code outside verification flow | Design-level (client); verify at implementation QA |
| Purpose disclosure before capture | C-9 consent screen content (a)–(e) | REQUIRED |
| Fresh capture, never a gallery photo | C-3 (no picker in UI) + C-4/C-5 challenge binding; honest limit: server cannot cryptographically prove freshness — human review of challenge compliance is the control | REQUIRED + documented limitation |
| Format/dimension/size validation | C-6 | REQUIRED |
| Secure transmission | HTTPS at the reverse proxy (RS-1 conditions, 6K/9 deployment); `secure` cookies in production already enforced (`auth.py:155`); HSTS at proxy | REQUIRED at deployment |
| Temp-file protection | No temp files: in-memory processing only (vision.py precedent); storage per C-7 with 0600 | REQUIRED |
| Informed consent | C-9 append-only `consent_records`, server-enforced | REQUIRED |
| Encryption in transit and at rest | In transit: TLS (deployment). At rest: C-8 encrypted volume — record actual mechanism; no over-claiming in policy text | REQUIRED (mechanism: owner confirm) |
| Restricted access | C-11 admin-gated streaming endpoint; C-7 filesystem perms; no public URLs | REQUIRED |
| Minimal retention + deletion periods | C-14 TTL 7 days post-decision (default); purge of challenges | REQUIRED |
| No model-training / advertising reuse | Consent text (C-9(e)); assist model sees the image for flagging only — this limited use must itself be disclosed in the consent screen | REQUIRED |
| No public selfie URLs | C-13/C-11: no URL is ever minted; bytes only via authenticated streaming | REQUIRED |
| Verification status + audit events | C-5 status endpoint; C-10 event set | REQUIRED |
| Secure deletion | C-14 unlink + verified test; on encrypted volume this is adequate for the threat model | REQUIRED |
| Account stays pending on failure; never silently bypass | B-6 verdict: rejection keeps pending; retry cap → `locked`; no code path sets `approved` without an admin action; tests D-7/D-8 | REQUIRED |
| Mandatory-step disclosure BEFORE registration | C-9: disclosure at signup-flow start, before account creation | REQUIRED (client + policy_version recorded) |
| No government-ID verification claims | No ID document intake exists in E3 — keep it that way; onboarding copy must not claim "government ID verification" | REQUIRED (negative constraint) |
| No face recognition for identification | No embedding store, no comparison against other users' captures, no 1:N matching anywhere; qwen assist compares nothing across users | REQUIRED (negative constraint) |

---

## E. Test Requirements (negative tests that MUST exist)

1. Upload **without** a consent row → 422 `CONSENT_REQUIRED`, no bytes written.
2. Upload with expired / consumed / foreign-`user_id` / nonexistent challenge → uniform 422 `CHALLENGE_INVALID`, no bytes written, challenge not consumed on failure.
3. Double-upload with the same challenge id → second attempt fails `CHALLENGE_INVALID`.
4. File > 5 MiB → 413; chunked-encoding oversize → rejected by the existing body-cap middleware (add a regression test naming this route).
5. Non-image bytes with an image extension (and image bytes with a wrong extension) → 415 (magic bytes decide).
6. Decompression-bomb image (declared-small JPEG with huge pixel canvas) → rejected by the `MAX_IMAGE_PIXELS` guard, process survives.
7. Rejection by admin → user `verification_status` remains `pending`; no code path (including assist output) flips it to `approved`; retries decrement; exceeding the cap → `locked`.
8. Approval **only** via admin endpoint; a non-admin session on the admin queue → 403; anonymous → 401.
9. Cross-user: user A cannot fetch status/image of user B's selfie → 404; admin image endpoint audits `SELFIE_REVIEW_VIEWED` on every fetch.
10. Any API response (including errors, admin queue JSON, status endpoint) contains no storage path, filename, or image URL — assert over the OpenAPI-documented response bodies and the error envelope.
11. Retention job: file unlinked, storage reference cleared, decision + audit rows persist, missing-file case does not crash the job.
12. Rate limits: 11th challenge request in the hour → 429; per-IP limit fires for unauthenticated probing.
13. Consent rows are append-only: attempting an update/delete via the service layer is not possible (no such method); new policy version → new row, and uploads under the old version are refused once the version bumps.
14. EXIF/GPS stripped: upload an image with GPS EXIF, read back the stored bytes via the admin endpoint, assert no EXIF payload present.

---

## F. Open Questions for the Owner

- **Q1 (blocking):** E2 OAuth signups currently activate immediately (no pending state). Directive says the selfie step is mandatory. Confirm that **OAuth-created accounts also enter `pending_verification`** and complete E3 before features unlock — this changes E2 code, so it needs an explicit owner decision. Related: the `verification_status` storage location (column on `users` vs. derived) may exceed the pre-approved table list — confirm the small `users` alteration is in scope for the E3 migration.
- **Q2:** Retry cap N — 3 recommended; and confirm `locked` accounts are unlocked only by admin reset.
- **Q3:** Retention TTL — 7 days post-decision recommended; shorter is acceptable, longer requires justification in the DPDP review (ADR-015).
- **Q4:** Encryption at rest — is the host disk already encrypted? If yes, no extra mechanism needed (record it); if no, approve an encrypted volume for `/data/MyFarmAI-data`.
- **Q5:** Pillow as a new backend dependency (dimension validation + EXIF strip) requires classification under `DEPENDENCY_POLICY.md` — approve.
- **Q6:** Import the verbatim directive §5 text into the repo (or link its authoritative location) so the DPDP checklist (Section D) can be verified against source rather than paraphrase — B7 requires this review to be checkable.

---

### Sign-off (design-stage)

- [x] All proposed-flow elements reviewed with REQUIRED/MODIFIED verdicts; none rejected
- [x] Hard rules (consent, retention, no-public-URLs, no-false-success, pending-on-failure) preserved and made testable
- [x] Known limitations stated honestly (no cryptographic liveness at 2 GiB VRAM)
- [ ] Q1 must be answered before E3 implementation starts
- Reviewer: @security-engineer
- Date: 2026-11-02
