# Administrator Account Procedure

**Applies to:** MyFarmAI v1.0.0 and later
**Audience:** Project owner / operator

Administrators are the only accounts that can approve pending registrations.
There is no default administrator, no seeded password, and no API route that
creates one — by design. This document is the only supported way to create or
recover an administrator.

---

## 1. Create the first administrator

Run this on a machine that can reach the production database, from `backend/`:

```bash
.venv/bin/python scripts/create_admin.py --email owner@example.com
```

You will be prompted for a password twice. It must be 8–128 characters. The
password is never echoed, never passed as a command-line argument, and never
printed.

Expected output:

```
Created administrator: owner@example.com (id=<uuid>)
```

The account is created `active`, `email_verified=true`, with `role=ADMIN`, so it
is not blocked by the verification gate it operates.

## 2. Recover access (promote an existing account)

The same command is the recovery path. If the email already exists, the account
is **promoted** and its password **reset**:

```bash
.venv/bin/python scripts/create_admin.py --email owner@example.com
```

Expected output:

```
Promoted administrator: owner@example.com (id=<uuid>)
```

Use this when the only administrator loses access. Do not create a second
account with a shared password.

## 3. Non-interactive use

For automation, pipe exactly one line on stdin from your secret manager:

```bash
printf '%s\n' "$ADMIN_PASSWORD" | .venv/bin/python scripts/create_admin.py --email owner@example.com
```

Never put the password in the command line, a shell history file, a repository
file, or a chat message.

## 4. Approve or reject pending users

Self-registered accounts start as `pending_verification` and cannot create
farms, plots, or a farmer profile until approved.

List the queue:

```bash
curl -s -b "myfarmai_session=<admin-session>" \
  https://<api-host>/api/v1/verification/admin/pending-users
```

Approve:

```bash
curl -s -X POST -b "myfarmai_session=<admin-session>" \
  -H 'Content-Type: application/json' \
  -d '{"approved": true}' \
  https://<api-host>/api/v1/verification/admin/users/<user-id>/decision
```

Reject (a reason is mandatory):

```bash
curl -s -X POST -b "myfarmai_session=<admin-session>" \
  -H 'Content-Type: application/json' \
  -d '{"approved": false, "reason": "identity could not be confirmed"}' \
  https://<api-host>/api/v1/verification/admin/users/<user-id>/decision
```

Server-side rules, all enforced regardless of client:

| Rule | Result |
|---|---|
| Caller is not an administrator | 403 `ADMIN_REQUIRED` |
| Caller targets their own account | 403 `SELF_APPROVAL` |
| Target is not `pending_verification` | 409 `INVALID_TRANSITION` |
| Rejection without a reason | 422 `REASON_REQUIRED` |
| Target does not exist | 404 `USER_NOT_FOUND` |

Every decision writes a `VerificationEvent` (`VERIFICATION_APPROVED` or
`VERIFICATION_REJECTED`) containing `method: admin_approval`, the reviewer id,
the target user id, and the reason when rejecting.

## 5. What an administrator can and cannot do

Can:
- list and decide pending registrations;
- review selfie-verification rows (`/verification/admin/selfies`) if that flow
  is ever used;
- read feedback submissions (`GET /api/v1/feedback`).

Cannot:
- approve their own account;
- change another user's data;
- read another user's password hash or session token through any API.

## 6. Operational notes

- Administrator accounts are **not** subject to the verification gate. A
  compromised administrator is therefore equivalent to full approval authority;
  protect the credential accordingly.
- There is no password-reset email flow for administrators. Recovery is §2.
- Do not create administrators through the public registration form; it always
  produces an ordinary pending user.
