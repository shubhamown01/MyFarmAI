# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | ✅ Current development |
| < 0.1.0 | ❌ Not supported |

## Reporting a Vulnerability

**Do not report security vulnerabilities via public GitHub issues.**

Instead, please report them via email to: **security@myfarmai.internal**

Include the following information:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

We will acknowledge receipt within 48 hours and provide a status update within 5 business days.

## Security Considerations

### Current Phase (0.x - Prototype)

| Area | Status | Notes |
|------|--------|-------|
| Authentication | ❌ Not implemented | Public prototype, no auth |
| Authorization | ❌ Not implemented | No role-based access |
| Rate Limiting | ❌ Not implemented | No API throttling |
| Input Validation | ✅ Pydantic models | Message length ≤ 2000 chars |
| CORS | ✅ Configured | Restricted to configured origins |
| Secrets Management | ✅ .env files | Not committed to git |
| SQL Injection | ✅ Parameterized | SQLite via aiosqlite |
| XSS Prevention | ✅ React default | Auto-escaping in JSX |
| Dependency Scanning | 🔄 Manual | Run `npm audit` / `pip-audit` |

### Planned for Production (1.0+)

- [ ] JWT/OIDC authentication
- [ ] Role-based access control (RBAC)
- [ ] API rate limiting (per-user, per-endpoint)
- [ ] Request/response logging (audit trail)
- [ ] Secrets manager integration (AWS/GCP/Azure)
- [ ] PostgreSQL with encryption at rest
- [ ] TLS termination at load balancer
- [ ] WAF rules for common attacks
- [ ] Automated dependency vulnerability scanning (Dependabot/OSV)
- [ ] Security headers (CSP, HSTS, etc.)
- [ ] Penetration testing

## Secure Development Practices

### For Contributors

1. **Never commit secrets** — Use `.env.example` for templates
2. **Validate all inputs** — Pydantic (backend), Zod/TypeScript (frontend)
3. **Use parameterized queries** — Never string-concatenate SQL
4. **Sanitize user content** — React auto-escapes; verify any `dangerouslySetInnerHTML`
5. **Keep dependencies updated** — Run `npm audit` / `pip-audit` regularly
6. **Follow least privilege** — Services run as non-root in containers

### For Reviewers

Check for:
- [ ] No hardcoded secrets, API keys, passwords
- [ ] Input validation on all endpoints
- [ ] Proper error handling (no stack traces to clients)
- [ ] CORS configured correctly
- [ ] Dependencies have no known critical vulnerabilities
- [ ] File uploads validated (type, size, content)
- [ ] Authentication/authorization on protected endpoints

## Threat Model (Prototype)

### Assets to Protect
- User conversation history (SQLite)
- Agricultural query data
- Voice audio uploads (temporary)

### Attack Vectors
| Vector | Likelihood | Impact | Mitigation |
|--------|------------|--------|------------|
| Prompt injection | MEDIUM | LOW | System prompt constraints, input length limits |
| Ollama model manipulation | LOW | MEDIUM | Model runs locally, no external API |
| SQLite injection | LOW | HIGH | Parameterized queries via aiosqlite |
| Voice file upload abuse | LOW | MEDIUM | Temp files auto-deleted, size limits |
| CORS misconfiguration | LOW | MEDIUM | Explicit origin allowlist |
| Dependency vulnerabilities | MEDIUM | MEDIUM | Regular scanning, locked versions |

### Current Defenses
- Input validation via Pydantic (all endpoints)
- Message length limit (2000 chars)
- Coordinate bounds validation (weather)
- Temporary file cleanup (voice service)
- CORS origin restriction
- Non-root containers (Docker)
- `.env` excluded from git

## Incident Response

### If You Discover a Breach

1. **Contain** — Stop affected services if needed
2. **Assess** — Determine scope and data exposed
3. **Notify** — Email security@myfarmai.internal immediately
4. **Document** — Record timeline, evidence, actions
5. **Remediate** — Apply fix, rotate compromised credentials
6. **Review** — Post-incident analysis within 7 days

### Contact

- **Security Team:** security@myfarmai.internal
- **Emergency:** Create private GitHub security advisory

---

## Compliance Notes

- **GDPR:** Not applicable (prototype, no EU users)
- **HIPAA:** Not applicable (no health data)
- **PCI-DSS:** Not applicable (no payment processing)
- **Agricultural Data:** No regulated agricultural data collected

---

*Last updated: 2026-10-21*
*Review date: 2027-01-21*