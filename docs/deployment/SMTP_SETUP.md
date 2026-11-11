# SMTP Configuration Guide

**Applies to:** MyFarmAI v1.0.0 and later
**Audience:** Project owner / operator
**Status:** Required for public registration. Without it, no verification code is delivered.

MyFarmAI sends a 6-digit verification code by email at registration. The code
is delivered through an SMTP relay using the standard library only — no paid
provider SDK is required.

---

## 1. Required environment variables

| Variable | Required | Example | Notes |
|---|---|---|---|
| `EMAIL_DELIVERY_MODE` | yes | `smtp` | Production **fails to start** unless this is `smtp`. |
| `SMTP_HOST` | yes | `smtp.yourprovider.com` | Relay hostname. |
| `SMTP_PORT` | yes | `587` | `587` = STARTTLS, `465` = implicit TLS (see §4). |
| `SMTP_USER` | conditional | `apikey` | Leave empty only if the relay accepts unauthenticated mail. |
| `SMTP_PASSWORD` | conditional | *(secret)* | Must come from the platform secret manager. |
| `SMTP_FROM` | yes | `no-reply@yourdomain.com` | Must be an address the relay is allowed to send as. |
| `SMTP_STARTTLS` | no | `true` | Default `true`. Set `false` only for a trusted relay on a private network. |
| `SMTP_TIMEOUT_SECONDS` | no | `15` | Connect/send timeout, 1–120. |

## 2. Add the values

Use the hosting provider's secret-management interface. For Catalyst AppSail,
set them as environment variables in the AppSail console under
**Configuration → Environment Variables**. Do not write them into the
repository, a `.env` file that is committed, a Docker image, or a chat message.

After adding the variables, redeploy or restart the service so they are read at
startup.

## 3. Startup behaviour

- `EMAIL_DELIVERY_MODE=dev` in production → **startup fails** with
  `email_delivery_mode must be 'smtp' in production`.
- `EMAIL_DELIVERY_MODE=smtp` with a blank `SMTP_HOST` or `SMTP_FROM` →
  **startup fails** with `smtp_host and smtp_from must be set`.
- An unknown mode in production → **startup fails**.
- In development, `dev` writes the code to the server log and an outbox file and
  never delivers mail. The code is redacted when `ENVIRONMENT=production`.

Failing at startup is deliberate: a production instance that silently falls
back to the dev adapter accepts registrations that can never complete.

## 4. Port and TLS

The adapter uses `smtplib.SMTP` with STARTTLS, which is correct for port 587 and
most relays.

Port 465 requires implicit TLS (`SMTP_SSL`), which this adapter does not use.
If your provider only offers 465, use its 587 endpoint or a provider that
supports STARTTLS. Do not disable TLS to work around this.

`SMTP_STARTTLS=false` is only appropriate for a relay on a private network you
control. It sends credentials and codes in clear text on that network.

## 5. Verify delivery

Registration flow:

1. `POST /api/v1/auth/register/email/request-otp` with `{"email": "you@example.com"}`.
2. The response is always the same generic message, whether or not the address
   was known.
3. The email should arrive within seconds. Check the spam folder.
4. `POST /api/v1/auth/register/email/verify` with `{"email", "code", "password"}`
   activates the account and opens a session.

If the relay rejects the message, the API returns:

```
503 {"detail": "Verification email could not be sent. Try again later.",
     "error_code": "EMAIL_DELIVERY_UNAVAILABLE"}
```

The account and code are rolled back, so the user can retry immediately.

Server logs record only the exception **type** (`SMTPAuthenticationError`,
`TimeoutError`, …). The code, password, recipient address, and message body are
never logged.

## 6. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Service will not start, log says `email_delivery_mode must be 'smtp'` | `EMAIL_DELIVERY_MODE` unset or `dev` | Set it to `smtp`. |
| Service will not start, log says `smtp_host and smtp_from must be set` | Missing host or sender | Add both. |
| 503 with `SMTPAuthenticationError` in logs | Wrong username/password | Re-enter the credentials in the secret manager. |
| 503 with `TimeoutError` | Relay unreachable or port blocked | Confirm outbound access to the relay port. |
| 503 with `SMTPRecipientsRefused` | Relay refuses the recipient or sender | Verify `SMTP_FROM` is authorised; check the relay's sending rules. |
| 503 with `SMTPNotSupportedError` | Relay does not offer STARTTLS | Use a relay that does, or a 587 endpoint. |
| Email arrives but the code is rejected | Code expired (10 min) or already used | Request a new code. |

## 7. What has and has not been verified

- The adapter is covered by 17 automated tests against a fake SMTP server:
  success, missing configuration, bad credentials, timeout, server rejection,
  STARTTLS failure, safe logging, dev behaviour, and production startup refusal.
- **No real message has been sent through a real relay.** Email is not
  operational until a verification email is actually received and its code
  completes registration.
