# Phase 3 — Authentication, Authorization and Application Security

## Objective

Protect user identity and private farm, conversation and research data. Authentication and ownership enforcement are release blockers before any public deployment.

## Entry conditions
- Database ownership model is approved.
- Session/token and account-lifecycle design is approved.
- Voice-service containment/remediation scope is approved.

## Workstreams

### 1. Threat model and access matrix
- Define user roles and resource ownership.
- Document permitted actions for each resource and role.
- Map every private endpoint to authentication and authorization requirements.
- Treat identifiers as references, never as authorization secrets.
- Ensure authorization is enforced server-side, not only in the client.

### 2. Authentication lifecycle
- Specify registration, login, logout, password reset, session expiry and account deletion.
- Hash passwords using Argon2id through a maintained library.
- Select web session handling and Android token handling separately where necessary.
- Use secure cookie attributes for browser sessions where suitable.
- Define refresh, revocation, rotation and device/session invalidation.
- Avoid logging credentials or tokens.

### 3. Authorization
- Add ownership checks for farms, conversations, files, research records and other private resources.
- Deny access by default.
- Test direct-object reference attacks and cross-user access.
- Avoid relying on unpredictable IDs as a replacement for authorization.

### 4. Abuse controls
- Bound request bodies, uploads, execution time and AI concurrency.
- Add rate limits for authentication, password reset, research and expensive model requests.
- Do not trust `X-Forwarded-For` unless the request comes from a configured trusted proxy.
- Replace unbounded in-memory counters with a bounded strategy appropriate to the deployment.
- Return consistent errors without leaking account existence or internal details.

### 5. Deployment and secret security
- Remove hardcoded secrets through an approved rotation and configuration procedure.
- Restrict CORS, trusted hosts and exposed ports.
- Do not publish internal services directly.
- Keep secrets out of Git, images, logs and issue reports.
- Define audit-event policy and privacy-aware retention.

### 6. Voice service decision
- Default recommendation: defer voice from MVP.
- If retained, require explicit authentication, strict upload size/type limits, timeouts, concurrency limits, non-root execution and private network exposure.
- Do not expose an unauthenticated voice endpoint publicly.

## Deliverables
- Threat model and authorization matrix.
- Authentication flow documentation.
- Secure session/token implementation plan and approved changes.
- Access-control tests and abuse-control tests.
- Secret rotation and service exposure remediation records.

## Acceptance criteria
- [ ] Every private endpoint has an explicit auth policy.
- [ ] Cross-user and cross-farm access tests are denied.
- [ ] Session/token expiry and revocation are tested.
- [ ] Passwords use a modern password hash.
- [ ] Rate limits cannot be trivially bypassed through spoofed headers.
- [ ] Request sizes and expensive workloads are bounded.
- [ ] No credentials are exposed in source, logs or responses.
- [ ] Security events are logged without sensitive payloads.

## Exit gate
Security review accepts authentication, authorization, rate limiting, secret handling and the voice-service decision before external exposure.
