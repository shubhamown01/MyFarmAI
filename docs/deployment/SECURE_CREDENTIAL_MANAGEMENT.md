# Secure Credential Management

Status: ACTIVE policy for the deployment phase (₹0, local-first). Evidence-based:
reflects what actually exists in this repo today (verified 2026-11-03).

## 1. Where credentials live today

| Credential | Storage | In Git? | Notes |
|---|---|---|---|
| Google OAuth client ID/secret | `backend/.env` (git-ignored) via compose `env_file` | ❌ verified | Only sb95146 can sign in while Google OAuth app is in Testing mode |
| Postgres password | compose `.env` (git-ignored) | ❌ | Compose injects; never echoed by `BACKUP_MYFARMAI.sh` |
| Dev OTP codes | `backend/data/dev_otp_outbox.txt` (clearly marked, dev only) | ❌ git-ignored data dir | Never a real delivery channel |
| No passwords created for cloud accounts | SSO identities only (Google accounts: GCP, Cloudflare) | n/a | Nothing to store yet |

Verification: `git status`/`git check-ignore backend/.env` — ignore rules active;
secret scans across the repo came back clean earlier this phase.

## 2. Rules (binding)

1. **Never** in Git, `docs/`, `.env.*` committed files, logs, screenshots, or
   chat. Logs never contain passwords, tokens, OTP values, or raw selfies.
2. New passwords → Google Password Manager on the owner's device (Chrome
   suggest-strong-password flow), **then** an encrypted GPG backup:
   - Backup file: `~/Desktop/MyFarmAI_Secure_Backup/MyFarmAI_Cloud_Credentials.txt.gpg`
   - Passphrase: entered **only** by the owner, privately — never logged,
     displayed, emailed, or typed into any tool. If lost, the backup is
     unrecoverable by design.
3. Server credentials (future: Neon connection string, SMTP app password) go in
   the provider's own secret store or the running host's environment — never in
   the frontend bundle, never in client-fetchable code.
4.-OAuth client secrets are backend-only; the Next.js app talks to the backend
   via same-origin `/api/v1` and never sees client secrets.
5. Rotation: any credential that ever appears in a log, screenshot, or repo is
   rotated the same day (OAuth: delete + recreate client; DB: update `.env` +
   recreate containers).

## 3. Phase B (pending): GPG backup setup

Blocked on: `~/Desktop/MyFarmAI_Secure_Backup/` directory creation (owner's
home) and the owner entering the GPG passphrase privately. Steps when
approved:

1. `mkdir -p ~/Desktop/MyFarmAI_Secure_Backup`
2. Owner composes the plaintext credential list **themselves** (or dictates
   entries while the agent looks away) — the agent never reads/writes the
   plaintext if it contains anything sensitive.
3. Owner runs `gpg -c MyFarmAI_Cloud_Credentials.txt && shred the plaintext`
   themselves. This script/agent records only: file exists, encrypted, EXIT 0.

## 4. What is deliberately NOT stored

- Selfies / face embeddings beyond the transient verification flow (see
  `PRODUCTION_SECURITY_CHECKLIST.md §4`).
- OTP delivery keys or provider token caches.
- Any cloud-account password (SSO only so far).
