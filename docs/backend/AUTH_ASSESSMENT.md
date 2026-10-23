# MyFarm AI Backend — Authentication Assessment

## Current State

**No authentication implemented.** The backend is a public prototype with no authentication or authorization.

## Threat Model

### Assets to Protect
- Conversation history (user messages, AI responses)
- Agricultural context (crop, location, language preferences)
- User behavior patterns

### Threat Actors
- **External attackers**: Unauthorized access to conversation data
- **Abusive users**: Rate limiting bypass, resource exhaustion
- **Internal threats**: Accidental data exposure

### Attack Vectors
| Vector | Likelihood | Impact | Mitigation |
|--------|------------|--------|------------|
| Conversation enumeration | Medium | Low | No auth, but no PII in conversations |
| Rate limit bypass | Medium | Medium | In-memory rate limiting (prototype only) |
| Data scraping | Low | Low | Public API, no sensitive data |
| Conversation injection | Low | Medium | Input validation, parameterized SQL |

## Current Defenses

### Implemented
- ✅ Input validation (Pydantic schemas)
- ✅ Rate limiting (60 requests/minute per IP)
- ✅ Input sanitization (Pydantic validators)
- ✅ SQL injection prevention (parameterized queries)
- ✅ CORS restrictions (configurable origins)
- ✅ Structured logging with request IDs
- ✅ No sensitive data in logs
- ✅ Error responses without stack traces

### Missing
- ❌ Authentication (JWT/OIDC)
- ❌ Authorization (resource ownership)
- ❌ Distributed rate limiting
- ❌ Encryption at rest (SQLite file)
- ❌ Encryption in transit (HTTPS via reverse proxy)
- ❌ Session management
- ❌ Audit logging

## Deployment Context Assessment

### Current: Prototype (Local Network)
- **Scope**: Single developer, local testing
- **Network**: localhost / private LAN
- **Users**: Single user (developer)
- **Data sensitivity**: Low (test conversations)

**Assessment**: Authentication NOT required for current prototype phase.

### Next: Private Network Deployment
- **Scope**: Team testing, internal demo
- **Network**: VPN / private cloud VPC
- **Users**: Known team members (5-10)
- **Data sensitivity**: Low-Medium

**Recommendation**: Add simple API key authentication or IP allowlist before team deployment.

### Future: Public Deployment
- **Scope**: Public internet access
- **Network**: Public internet
- **Users**: Anonymous farmers, general public
- **Data sensitivity**: Medium (location, crop data)

**Requirement**: Full authentication required before public launch.

## Recommended Authentication Strategy

### Phase 1: Prototype (Current) - No Auth
- Keep public endpoints
- Document as known limitation
- Monitor for abuse via logs

### Phase 2: Team/Private Deployment - API Key
- Simple header-based API key
- Store keys in environment/secrets
- Per-user rate limits
- No user management UI needed

### Phase 3: Public Launch - OIDC/JWT
- Integrate with identity provider (Google, Microsoft, or Keycloak)
- JWT tokens with short expiry
- Refresh token rotation
- User profile management
- Role-based access (farmer, extension officer, admin)

## Implementation Priority

| Feature | Effort | Priority | Blocking |
|---------|--------|----------|----------|
| API Key auth | Low | Medium | Private deploy |
| JWT/OIDC | High | High | Public launch |
| User profiles | Medium | High | Public launch |
| Role-based access | Medium | Low | Post-launch |
| Session revocation | Medium | Medium | Public launch |

## Data Privacy Considerations

### Current Data Collected
- Conversation text (user messages, AI responses)
- Metadata: crop, location (optional), language
- Timestamps, request IDs
- IP addresses (rate limiting, logs)

### PII Assessment
- **No direct PII**: No names, emails, phone numbers
- **Indirect PII**: Location + crop could identify farmer
- **GDPR/PDPB**: May apply if deployed in EU/India

### Recommendations
1. Add privacy policy before public launch
2. Implement data retention policy (auto-delete after 90 days)
3. Add data export/deletion endpoints
4. Document lawful basis for processing
5. Consider data minimization (don't store location if not needed)

## Decision Matrix

| Deployment Target | Auth Required | Recommended Approach |
|-------------------|---------------|----------------------|
| Local development | No | None |
| Team demo (VPN) | Yes | API Key |
| Staging (private) | Yes | API Key |
| Public beta | Yes | OIDC (Google/GitHub) |
| Production | Yes | OIDC + MFA option |

## Next Steps

1. **Before team deployment**: Implement API key middleware
2. **Before public beta**: Integrate OIDC provider
3. **Before production**: Add MFA, session management, audit logs
4. **Ongoing**: Regular security reviews, dependency scanning

## Conclusion

**For the current prototype phase, no authentication is required.** The application is designed for local development and testing. The threat model shows low risk given the deployment context (local/private network, no PII, no sensitive data).

**Before any network-exposed deployment**, implement at minimum API key authentication. Before public internet exposure, full OIDC/JWT authentication with proper session management is required.

---

*Document version: 1.0*  
*Date: 2026-10-18*  
*Status: Assessment complete - no action required for prototype phase*