# MyFarmAI — Technical Requirements Document (TRD)

**Document ID:** MYFARMAI-TRD-001  
**Version:** 1.0  
**Status:** Draft — Owner Review Required  
**Product:** MyFarmAI  
**Platforms:** Web and Android  
**Backend:** Python / FastAPI  
**Proposed Database:** PostgreSQL  
**AI Runtime:** Ollama, subject to configuration and hardware validation  
**Research Search:** SearXNG  
**Deployment Direction:** Docker Compose  
**Precedence:** Approved SRS, owner-approved ADRs, and governance decisions take precedence over this draft.

---

## 1. Purpose

This document specifies the technical requirements and implementation constraints for MyFarmAI. It translates the product requirements into engineering requirements that developers, OpenCode agents, testers, and deployment operators can implement and verify.

The TRD defines:

- System boundaries and component responsibilities.
- Backend architecture and interfaces.
- Data persistence and migration requirements.
- AI inference and web research workflows.
- Security and privacy controls.
- Testing and quality gates.
- Deployment, observability, backup, and recovery requirements.

This document does not independently authorize implementation of restricted changes, database migrations, secret rotation, or production deployment.

## 2. Technical Objectives

1. Deliver a modular, maintainable backend.
2. Support web and Android clients through documented API contracts.
3. Provide controlled integration with local AI models.
4. Retrieve relevant research and preserve source provenance.
5. Enforce authentication, authorization, and input validation where required.
6. Support reproducible deployment and tested recovery.
7. Prefer free and open-source dependencies where practical.
8. Keep services and resource consumption appropriate to the deployment hardware.
9. Ensure every significant code change has corresponding documentation.
10. Require evidence before declaring a component production-ready.

## 3. System Architecture

### 3.1 Logical architecture

<CodeBlock language="mermaid" editable>
flowchart TB
    WEB[Next.js Web Client]
    ANDROID[React Native / Expo Android Client]

    API[FastAPI Backend]
    AUTH[Authentication and Authorization]
    APP[Application Services]
    AI[AI Orchestrator]
    RESEARCH[Research Engine]
    DATA[Data Access Layer]

    DB[(Approved Persistent Database)]
    OLLAMA[Ollama Model Runtime]
    SEARCH[SearXNG Search Service]
    FETCH[Controlled Content Retrieval]
    OBS[Logs and Health Monitoring]

    WEB --> API
    ANDROID --> API

    API --> AUTH
    API --> APP
    APP --> AI
    APP --> RESEARCH
    APP --> DATA

    AI --> OLLAMA
    RESEARCH --> SEARCH
    SEARCH --> FETCH

    DATA --> DB
    API --> OBS
    AI --> OBS
    RESEARCH --> OBS
</CodeBlock>

This is a logical target architecture. It does not establish that all components already exist or that the current repository follows this design.

### 3.2 Component boundaries

| Component | Responsibility |
|---|---|
| Web client | User interface, input validation, API consumption, error presentation |
| Android client | Mobile interface, API consumption, network and offline error handling |
| FastAPI | API routing, validation, dependency management, business workflows |
| Application services | Coordinate use cases without coupling business logic to transport |
| AI orchestrator | Select approved model providers, enforce limits, normalize responses |
| Research engine | Search, retrieve, extract, rank, and track source metadata |
| Data access layer | Database queries, transactions, and persistence |
| Database | Durable application records and integrity constraints |
| Ollama | Local model inference when enabled |
| SearXNG | Metasearch through configured search providers |
| Retrieval service | Controlled access to permitted public sources |
| Observability | Health reporting, structured logs, and error diagnostics |

## 4. Proposed Technology Stack

| Layer | Proposed technology | Technical requirement |
|---|---|---|
| Web | Next.js, Tailwind CSS | Responsive UI and typed API integration |
| Android | React Native, Expo | Supported Android application build |
| API | Python, FastAPI | Validated and documented REST API |
| Data validation | Pydantic | Request and response schemas |
| ORM | SQLAlchemy | Explicit, maintainable database access |
| Migrations | Alembic | Versioned, reviewable schema changes |
| Database | PostgreSQL | Durable relational persistence, if approved |
| Local AI | Ollama | Configurable local model inference |
| Search | SearXNG | Configurable metasearch |
| Testing | Pytest and client-appropriate test frameworks | Automated regression coverage |
| Containers | Docker and Docker Compose | Reproducible service environments |
| Quality | Ruff and strict type checking where configured | Static analysis and code consistency |

Versions must be selected after inspecting the existing lockfiles and compatibility constraints. Production images must use controlled, pinned versions or digests according to the approved dependency policy.

No paid service should be introduced without explicit approval.

## 5. Backend Architecture Requirements

### 5.1 Application structure

The backend should use clear separation of concerns. The following is a proposed logical layout, not an instruction to reorganize existing files without review.

<CodeBlock language="text" editable>
backend/
├── app/
│   ├── main.py
│   ├── api/
│   │   └── v1/
│   ├── core/
│   │   ├── config.py
│   │   ├── logging.py
│   │   └── security.py
│   ├── schemas/
│   ├── models/
│   ├── repositories/
│   ├── services/
│   │   ├── ai/
│   │   └── research/
│   ├── integrations/
│   │   ├── ollama/
│   │   └── search/
│   └── dependencies/
├── migrations/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── security/
├── pyproject.toml
└── README.md
</CodeBlock>

Before creating, moving, or renaming directories, the implementation agent must inspect the actual repository and preserve established conventions unless a reviewed change authorizes the restructuring.

### 5.2 API requirements

The API must:

- Use a consistent versioning strategy, with `/api/v1` as the proposed initial prefix.
- Validate request bodies, query parameters, and path parameters.
- Return consistent JSON response structures.
- Use appropriate HTTP status codes.
- Return safe errors without stack traces or internal secrets.
- Support request correlation identifiers.
- Document request and response schemas.
- Apply request size, timeout, and rate limits appropriate to each operation.
- Separate transport logic from application logic.
- Avoid blocking the event loop with unbounded synchronous work.

### 5.3 Error response

Proposed standard error schema:

<CodeBlock language="json" editable>
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request is invalid.",
    "request_id": "server-generated-correlation-id",
    "details": []
  }
}
</CodeBlock>

The example is a contract proposal. The final schema must match existing API conventions or an approved API decision.

### 5.4 Configuration

Configuration must be centralized, typed, validated at startup, and separated by environment.

Configuration categories include:

- Application environment and bind settings.
- Database connection configuration.
- AI provider and model configuration.
- Research provider configuration.
- Timeouts and concurrency limits.
- Logging and observability settings.
- Authentication and session settings, where applicable.

Secrets must be supplied through an approved secret-management mechanism or protected runtime environment. Real credentials must not be committed to source control, included in sample files, or written to logs.

## 6. Database and Persistence Requirements

### 6.1 Database selection

PostgreSQL is the proposed target for durable application data. However, the project has an unresolved canonical SQLite database decision:

- `backend/data/app.db`
- `data/app.db`

Until the owner resolves this decision, agents must not move, merge, overwrite, delete, or migrate either database.

The proposed PostgreSQL target does not override this restriction.

### 6.2 Data access

The persistence layer must:

- Use explicit transactions for multi-step changes.
- Enforce integrity constraints in the database where appropriate.
- Use parameterized queries or safe ORM-generated queries.
- Define transaction boundaries and rollback behavior.
- Avoid leaking database implementation details through API errors.
- Apply connection-pool limits appropriate to available resources.
- Use pagination for potentially large result sets.

### 6.3 Schema migrations

Schema changes must:

1. Be represented by version-controlled migration scripts.
2. Include a documented reason and impact analysis.
3. Be reviewed before application to non-disposable environments.
4. Be tested against a disposable database.
5. Have a recovery or forward-fix strategy.
6. Preserve data unless an explicitly approved transformation requires otherwise.

Production migration execution requires the appropriate owner approval and a verified backup/recovery procedure.

### 6.4 Data categories

The final schema must be derived from the approved SRS and existing database. Potential categories include user records, conversation records, research jobs, source metadata, model configuration references, and audit events.

Do not add or modify tables simply because they appear in this draft.

## 7. AI Orchestration Requirements

### 7.1 Provider abstraction

AI integrations must be isolated behind a documented interface so provider-specific code does not spread through application services.

The interface should support, as applicable:

- Provider and model identification.
- Request validation.
- Bounded inference timeouts.
- Output normalization.
- Token or context limits when supported by the provider.
- Cancellation where supported.
- Provider health and availability status.
- Explicit error classification.
- Usage and latency measurements.

### 7.2 Ollama integration

When enabled, the Ollama adapter must:

- Use a configurable service endpoint.
- Validate requested model names against an approved configuration.
- Detect unavailable models and return a controlled error.
- Apply concurrency and timeout limits.
- Avoid downloading models automatically during ordinary user requests.
- Avoid logging private prompts or sensitive data by default.
- Respect the deployment's CPU, memory, and GPU constraints.

Model selection must be based on benchmark results from the actual target environment. A model's availability or advertised context length does not guarantee acceptable latency or output quality.

### 7.3 Failure handling

The backend must distinguish between:

- Model unavailable.
- Request timed out.
- Context or input limit exceeded.
- Provider overloaded.
- Invalid model response.
- Internal application failure.

Retries must be bounded and used only where appropriate. The system must not silently send private prompts to an unapproved external provider as a fallback.

## 8. Research Engine Requirements

### 8.1 Pipeline

The research engine should implement the following stages:

1. Accept and validate a research query.
2. Query the configured SearXNG endpoint.
3. Normalize and deduplicate search results.
4. Rank results using documented relevance criteria.
5. Validate candidate URLs before retrieval.
6. Fetch permitted source content using controlled network access.
7. Extract useful text and available metadata.
8. Generate a synthesis grounded in retrieved evidence.
9. Attach source references to the response.
10. Return partial results or controlled failures when dependencies are unavailable.

### 8.2 Retrieval safety

The retrieval service must defend against server-side request forgery and unsafe redirects. Required controls include:

- Permit only supported URL schemes, normally HTTP and HTTPS.
- Reject loopback, private, link-local, reserved, and otherwise disallowed destinations.
- Revalidate DNS resolution and destination addresses at connection time.
- Validate every redirect destination.
- Apply connection and total-request timeouts.
- Enforce response-size and content-type limits.
- Avoid executing retrieved scripts or active content.
- Apply egress network restrictions where feasible.
- Prevent access to internal services and cloud metadata endpoints.

URL parsing alone is insufficient SSRF protection.

### 8.3 Source integrity

For each source, preserve available metadata such as:

- Title.
- Canonical URL.
- Domain.
- Retrieval time.
- Publication date, if reliably available.
- Relevant extracted passage or summary.
- Retrieval and extraction status.

A citation must refer to a real retrieved or otherwise verified source. Missing metadata must remain missing rather than being invented.

### 8.4 Untrusted content

Retrieved pages may contain malicious instructions or misleading claims. The AI layer must treat retrieved material as untrusted evidence, not as system instructions or authorization to use tools.

### 8.5 Provider failures

Search failures, blocked pages, timeouts, extraction errors, and partial result sets must be represented explicitly. The engine must not claim comprehensive research when only a subset of sources was available.

## 9. API Contract Requirements

The following endpoints are candidate contracts. They must be reconciled with the existing API and approved scope before implementation.

| Candidate endpoint | Method | Purpose |
|---|---|---|
| `/api/v1/health/live` | GET | Process liveness |
| `/api/v1/health/ready` | GET | Dependency readiness |
| `/api/v1/ai/answer` | POST | AI-assisted answer |
| `/api/v1/research` | POST | Start or perform research |
| `/api/v1/research/{id}` | GET | Retrieve research status/result, if asynchronous jobs are approved |

### 9.1 Example AI request

<CodeBlock language="json" editable>
{
  "question": "What are common signs of nitrogen deficiency in wheat?",
  "language": "en",
  "include_sources": true
}
</CodeBlock>

### 9.2 Example response

<CodeBlock language="json" editable>
{
  "answer": "Example answer generated from available evidence.",
  "sources": [
    {
      "title": "Verified source title",
      "url": "https://example.org/agriculture-reference",
      "retrieved_at": "2026-01-01T00:00:00Z"
    }
  ],
  "limitations": [],
  "request_id": "server-generated-correlation-id"
}
</CodeBlock>

The values above are illustrative only. `example.org` is not evidence for the example claim. Real responses must contain actual validated source records, and the schema must be approved before use.

## 10. Web and Android Integration Requirements

### 10.1 Web client

The web client must:

- Use documented API contracts.
- Provide loading, empty, success, partial-result, and error states.
- Avoid embedding privileged secrets in browser code.
- Validate input for usability while relying on the backend for authoritative validation.
- Display source citations clearly.
- Handle expired authentication, if accounts are implemented.
- Support accessible navigation and keyboard interaction.

### 10.2 Android client

The Android client must:

- Use the configured backend base URL for each environment.
- Communicate over HTTPS in deployed environments.
- Avoid storing credentials in plain text.
- Handle connectivity loss and request timeouts.
- Avoid uncontrolled duplicate submissions.
- Present partial research results and failure states clearly.
- Be tested on supported Android versions and device configurations.

The client must not assume that the API is reachable from `localhost` when running on a physical device or emulator.

## 11. Security Requirements

### 11.1 Identity and access

Where authentication is in scope:

- Use a well-defined authentication mechanism.
- Enforce authorization on the server.
- Apply least privilege.
- Protect tokens and sessions.
- Rate-limit login and recovery endpoints.
- Audit security-sensitive administrative actions.
- Avoid exposing whether a private account exists through unnecessary error detail.

### 11.2 Application security

- Validate and constrain untrusted input.
- Use safe query construction.
- Apply appropriate CORS policy.
- Protect browser-based authentication flows against applicable CSRF risks.
- Use secure cookie attributes where cookie sessions are used.
- Prevent unauthorized object access.
- Apply request and upload size limits.
- Redact credentials and sensitive data from logs.
- Keep dependencies updated under a documented review process.

### 11.3 Container security

Production container configuration should:

- Use pinned images.
- Run as a non-root user where feasible.
- Define health checks.
- Set CPU and memory limits appropriate to measured workload.
- Avoid host networking unless justified and approved.
- Expose only required ports.
- Use named volumes or explicitly managed persistent storage.
- Avoid placing secrets in image layers or committed Compose files.
- Use dependency health conditions where supported and appropriate.

No destructive Docker operation, volume deletion, or persistent-data reset may be performed without explaining its impact and obtaining explicit confirmation.

## 12. Observability and Operations

### 12.1 Logging

Logs must be structured and should include timestamps, severity, service, operation, and request correlation identifiers.

Logs must not expose passwords, access tokens, database credentials, API keys, or unnecessary private agricultural conversation content.

### 12.2 Health checks

- **Liveness:** Indicates whether the service process is operational.
- **Readiness:** Indicates whether required dependencies are available for the service to accept work.

Health checks must be bounded, safe, and suitable for container orchestration.

### 12.3 Resource controls

The system must define limits for:

- API request duration.
- Concurrent AI requests.
- Concurrent research operations.
- Fetched response size.
- Extracted text length.
- Database connections.
- Background task queues, if implemented.
- Log retention and persistent storage.

Specific limits must be determined through testing on the target hardware and deployment.

## 13. Testing Requirements

### 13.1 Backend tests

- Unit tests for validation, business logic, ranking, and error mapping.
- API tests for status codes and response schemas.
- Integration tests for persistence and dependency adapters.
- Transaction and rollback tests.
- Authentication and authorization tests where applicable.
- Research tests for SSRF, redirects, DNS changes, timeouts, and content limits.
- AI tests using deterministic mocks and separately labeled live integration tests.
- Regression tests for known defects.

### 13.2 Client tests

- Component and form validation tests.
- API contract tests.
- Error and loading state tests.
- Authentication-flow tests where applicable.
- End-to-end tests for approved user journeys.
- Android network failure and device compatibility tests.

### 13.3 Deployment tests

- Clean-environment startup.
- Health and readiness checks.
- Migration testing on disposable databases.
- Configuration and secret checks.
- Backup creation and restore verification.
- Rollback or recovery rehearsal.
- Container vulnerability and dependency checks.

### 13.4 Quality gate

A build must not be called production-ready merely because it compiles or starts.

Record the commands executed, environment, exit codes, test totals, failures, unresolved findings, and evidence for recovery testing. Distinguish verified results from untested or blocked checks.

## 14. Deployment and Environment Requirements

Maintain separate configuration for development, testing, staging, and production.

The deployment design must document:

- Service dependencies and startup order.
- Ports and network exposure.
- Persistent data locations.
- Configuration and secrets.
- Resource limits.
- Health checks.
- Database migration procedure.
- Backup schedule and retention.
- Restore procedure.
- Rollback procedure.
- Logging and diagnostics.

The proposed backup location is `/data/MyFarmAI-backups`. Its suitability, permissions, capacity, backup contents, and restoration procedure must be verified before it is relied on operationally.

A backup is not considered verified until a restoration test succeeds in a controlled environment.

## 15. Performance and Capacity

Before defining hard service-level objectives, benchmark:

- Typical and worst-case API latency.
- Concurrent AI inference behavior.
- Search and content retrieval latency.
- Database query performance.
- Memory, CPU, GPU, and storage utilization.
- Behavior under dependency failure.

Use p50, p95, and p99 latency, error rate, and resource utilization to establish realistic thresholds. Do not claim a capacity level that has not been measured.

## 16. Documentation Requirements

Maintain documentation for:

- System architecture and component boundaries.
- API contracts.
- Data model and migration history.
- AI provider configuration.
- Research pipeline and source handling.
- Security controls and threat model.
- Environment variables and setup.
- Docker services and resource limits.
- Automated tests and quality checks.
- Backup, restore, and rollback.
- Troubleshooting and known limitations.
- Architecture decisions and change history.

Every significant implementation change must update its associated documentation before the change is considered complete.

## 17. Implementation Governance and Existing Constraints

The project currently has unresolved approval gates. The following restrictions take precedence over the proposed technical design:

1. **Database:** Resolve the canonical SQLite location before any database relocation, merge, deletion, or migration.
2. **License:** Obtain approval for the project license.
3. **ADRs:** Draft and individually review ADR-001, ADR-002, ADR-009, ADR-010, ADR-013, and ADR-014.
4. **Scope:** Revise and approve Phase 1 scope.
5. **Recovery:** Verify the backup and recovery approach at `/data/MyFarmAI-backups`.
6. **SearXNG secret rotation:** Planning only until separately approved.
7. **Voice-service containment:** Investigation and planning only until separately approved.
8. **Docker:** No destructive commands or persistent-volume removal without explicit confirmation.

Previously reported passing tests and clean static checks must be reverified against the current repository before they are used as release evidence.

## 18. Technical Acceptance Criteria

The technical implementation is accepted when:

- The architecture matches approved decisions.
- API contracts are documented and tested.
- Data access and migrations are safe and reproducible.
- AI and research integrations handle failures predictably.
- Research retrieval enforces SSRF and resource protections.
- Citations are traceable to actual sources.
- Web and Android clients correctly handle API outcomes.
- Security and static checks have documented results.
- Deployment configuration has appropriate health checks and resource limits.
- Backup restoration and recovery procedures have been verified.
- Documentation matches the implemented system.
- Outstanding risks and exceptions are recorded.
- The owner approves the release.

## 19. Definition of Technical Completion

A component is technically complete only when its code, tests, configuration, documentation, security controls, and operational behavior meet the approved requirements.

The complete platform is production-ready only after all required release gates have passed and the owner has authorized production release.

**Current document status:** Draft — Owner Review Required.

**Phase 1 authorization:** Not granted by this document.

**Production deployment approval:** Not granted by this document.

---

**End of MyFarmAI TRD v1.0**
