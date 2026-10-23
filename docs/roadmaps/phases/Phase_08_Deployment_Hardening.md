# Phase 8 — Deployment, Security Hardening and Operations

## Objective

Make deployment repeatable and recoverable, with least privilege, controlled network exposure and documented operational procedures.

## Entry conditions
- Deployment target is explicitly selected.
- Authentication and authorization are implemented for exposed services.
- Licence, data retention and secret-management decisions are recorded.

## Workstreams

### 1. Container and Compose configuration
- Use a canonical Compose configuration and pin image versions.
- Add health checks and meaningful dependency readiness conditions.
- Run non-root where practical.
- Use named persistent volumes and document their locations.
- Use internal networks for databases, Ollama and search services.
- Publish only required ports.
- Avoid host networking unless an approved requirement justifies it.
- Set resource limits after measurement.
- Keep development overrides separate from production configuration.

### 2. Secrets and configuration
- Use placeholder-only `.env.example`.
- Ensure actual secrets are ignored by Git.
- Do not bake credentials into images or logs.
- Document secret rotation and access policy.
- Rotate any previously hardcoded secret using an approved plan; do not merely delete its source value and leave the old secret active.

### 3. Network and TLS
- Use Caddy or Nginx as approved reverse proxy.
- Configure HTTPS for remote clients.
- Restrict database/admin interfaces to internal networks.
- Configure trusted hosts and CORS explicitly.
- Confirm deployment-specific firewall and port exposure before launch.

### 4. Backup and recovery
- Define backup frequency, retention, encryption and destination.
- Test restore to an isolated environment.
- Monitor disk capacity, log growth and backup failures.
- Document recovery steps and responsible operator actions.
- Avoid storing all backups on the same failing disk.

### 5. Observability
- Start with structured application logs and request IDs.
- Do not log passwords, tokens, private conversation content or sensitive farm/location data unnecessarily.
- Add metrics/tracing only where useful and within resource limits.
- Configure log rotation and retention.

### 6. Supply-chain and operations
- Scan dependencies and images.
- Review image/package provenance and licences.
- Document upgrades, maintenance windows, incident response and service health.
- Test fresh deployment without relying on undocumented machine state.

## Deliverables
- Deployment profiles and configuration guide.
- Secret-handling and rotation procedure.
- Backup/restore runbook and test evidence.
- Security hardening checklist.
- Operations and incident-response notes.

## Acceptance criteria
- [ ] Deployment can be reproduced from documentation.
- [ ] Only intended ports are exposed.
- [ ] Internal services are not unnecessarily public.
- [ ] Containers use least privilege where practical.
- [ ] Secrets are not committed or baked into images.
- [ ] Backups can be restored and verified.
- [ ] Logs are bounded and privacy-aware.
- [ ] Disk/RAM constraints are monitored.

## Exit gate
Deployment and security review accepts configuration, exposure, recovery and operational evidence before public launch.
