# MyFarmAI — Product Requirements Document (PRD)

**Document Version:** 1.0  
**Status:** Draft — Owner Review Required  
**Product:** MyFarmAI  
**Product Type:** AI-powered agriculture platform  
**Target Platforms:** Web and Android  
**Primary Goal:** Deliver reliable, accessible, secure, and practical AI-assisted agricultural information and workflows.

---

## 1. Executive Summary

MyFarmAI is an AI-powered agriculture platform intended to help farmers access agricultural knowledge, research farming problems, and make better-informed decisions using accessible digital tools.

The platform will combine a web application, an Android application, a backend API, AI-assisted workflows, and a research engine capable of retrieving relevant online information with source citations.

The product will prioritize open-source technologies, explainable information retrieval, data protection, maintainability, and a lightweight deployment strategy.

MyFarmAI must not present AI-generated recommendations as guaranteed agricultural outcomes. Important recommendations should communicate uncertainty, relevant limitations, and source information.

## 2. Product Vision

Build a dependable digital agricultural assistant that makes useful agricultural knowledge easier to access, understand, and apply.

### 2.1 Product objectives

1. Provide a consistent agricultural experience on web and Android.
2. Offer AI-assisted answers to agricultural questions.
3. Retrieve and synthesize relevant agricultural research from permitted online sources.
4. Present source citations so users can inspect the evidence behind answers.
5. Establish a secure, maintainable backend and documented API.
6. Prefer free and open-source software wherever practical.
7. Support future expansion without unnecessary architectural complexity.
8. Protect user data and preserve existing project data during development.

### 2.2 Success principles

- Accuracy over unsupported confidence.
- Evidence and citations over unexplained claims.
- Security and privacy by design.
- Mobile accessibility and low-bandwidth awareness.
- Documented decisions and reproducible deployments.
- Measurable acceptance criteria rather than subjective completion claims.

## 3. Target Users

### 3.1 Primary users

**Farmers**
- Ask questions about crops, cultivation, pests, diseases, irrigation, and soil.
- Need understandable, practical information.
- May use mobile devices and have limited connectivity.

**Agricultural students and learners**
- Research farming methods and agricultural concepts.
- Need structured explanations and traceable sources.

**Agricultural advisors and experts**
- Need a research assistant to gather relevant information.
- Need to review the evidence before advising others.

### 3.2 Administrative users

Authorized administrators may manage platform configuration, access controls, service health, and operational monitoring. Administrative functionality must be defined separately from ordinary user capabilities and must enforce role-based permissions.

These user groups are proposed product audiences; final personas and their priorities require owner validation.

## 4. Product Scope

### 4.1 Proposed MVP scope

| Module | Requirements |
|---|---|
| Web application | Responsive interface for agricultural questions, answers, research results, and account workflows where approved |
| Android application | Mobile-friendly access to the same core product capabilities |
| Backend API | Validated, versioned API with structured errors and documented endpoints |
| AI orchestration | Manage requests to supported AI providers and local models |
| Research engine | Search, retrieve, extract, rank, and summarize permitted public information |
| Citations | Associate claims or research results with accessible source references |
| Data layer | Persistent storage with controlled schema migrations and integrity checks |
| Security | Authentication, authorization, input validation, rate limits, and secret management |
| Observability | Structured logs, health checks, and operational error reporting |
| Testing | Unit, integration, security, and client compatibility tests |
| Deployment | Reproducible environment configuration, documented startup, backups, and recovery procedures |

Final MVP inclusion depends on the approved SRS, existing implementation, reviewed ADRs, and owner-approved scope.

### 4.2 Out of scope unless separately approved

- Autonomous purchases or financial transactions.
- Guaranteed crop-yield predictions.
- Automatic pesticide or fertilizer prescriptions without appropriate evidence and safeguards.
- Unreviewed changes to production data.
- Unapproved third-party paid services.
- Unrestricted web crawling or bypassing access controls.
- Autonomous deployment or destructive infrastructure changes.
- Features not supported by the approved requirements.

## 5. Core User Journeys

### Journey A: Ask an agricultural question

1. User opens MyFarmAI.
2. User enters a question about farming.
3. The client sends a validated request to the backend.
4. The backend determines whether AI generation, web research, or both are appropriate.
5. The system returns an understandable response with relevant limitations and citations where applicable.
6. The user can inspect sources and ask a follow-up question.

**Acceptance criteria**
- Valid requests produce a documented response structure.
- Invalid requests return safe, actionable errors.
- The interface distinguishes unavailable results from successful answers.
- Citations link to the actual retrieved sources and are not fabricated.

### Journey B: Research an agricultural topic

1. User submits a research question.
2. The research engine queries configured search sources.
3. Results are filtered, retrieved, and ranked.
4. Accessible content is extracted within configured limits.
5. The system generates a synthesis based on retrieved evidence.
6. The response includes source titles, URLs, and other available metadata.

**Acceptance criteria**
- Failed search providers do not crash the entire API.
- Source failures and partial results are reported accurately.
- The system applies timeouts, size limits, and SSRF protections.
- The research engine respects applicable access restrictions and source terms.
- Retrieved content is treated as untrusted data, not executable instructions.

### Journey C: Operate and maintain the platform

1. An authorized operator starts the documented services.
2. Health checks indicate which dependencies are available.
3. Operators inspect structured logs and service status.
4. Database backups can be created and restoration can be verified.
5. A failed deployment can be rolled back using documented procedures.

**Acceptance criteria**
- Health endpoints distinguish service liveness from dependency readiness.
- Secrets are not exposed in logs or committed configuration.
- Backup and restore procedures are tested and documented.
- No deployment is described as production-ready without recorded verification.

## 6. Functional Requirements

### FR-01: API foundation

The backend must provide a versioned API, request validation, consistent response schemas, centralized error handling, and generated API documentation.

### FR-02: Authentication and authorization

Where accounts are part of the approved scope, the platform must implement secure authentication, session or token lifecycle controls, and server-enforced authorization.

Password storage, token handling, account recovery, and administrative access must follow documented security requirements.

### FR-03: Agricultural question answering

The platform must accept agricultural questions and return structured responses. Responses should distinguish retrieved evidence, model-generated synthesis, and uncertainty where relevant.

### FR-04: AI provider management

The backend must use a defined provider interface for supported models, including local Ollama integration where configured. Provider timeouts, unavailable models, and inference failures must be handled gracefully.

The system must not silently switch to an unapproved provider or transmit private data to an external service without authorization.

### FR-05: Research engine

The research engine must support configurable search providers, source retrieval, content extraction, deduplication, relevance ranking, and synthesis.

SearXNG is the proposed metasearch component. Additional retrieval or indexing components must be introduced only where justified by approved requirements.

### FR-06: Source citations

Research responses must include verifiable source references. The backend must not invent titles, URLs, publication dates, quotations, or evidence.

### FR-07: Persistent storage

Persistent data must use a clearly defined schema and documented migration process. Database transactions, integrity constraints, and appropriate indexes must be applied where needed.

**Critical constraint:** The canonical database location and migration approach must be approved before any database relocation, merge, deletion, or migration is performed.

### FR-08: Web client

The web client must provide a responsive interface, clear loading and error states, accessible controls, and reliable API integration.

The proposed web stack is Next.js and Tailwind CSS, subject to confirmation against the existing repository and approved architecture.

### FR-09: Android client

The Android client must support the approved core user journeys, clear network-error handling, appropriate loading states, and secure communication with the backend.

React Native with Expo is the proposed stack, subject to repository and architecture verification.

### FR-10: Operational monitoring

The platform must provide health endpoints, structured application logs, error reporting, and sufficient operational information to diagnose service failures without exposing secrets or sensitive user content.

### FR-11: Configuration

Environment-specific settings must be externalized. Committed example configuration must contain placeholders rather than real credentials.

### FR-12: Documentation

Every significant architectural or implementation change must have corresponding documentation. API contracts, environment setup, migrations, tests, backup and recovery, and deployment instructions must remain synchronized with the implementation.

## 7. Non-Functional Requirements

### NFR-01: Security

- Apply least-privilege access.
- Validate all untrusted inputs.
- Protect authentication credentials and secrets.
- Implement rate limiting and resource limits appropriate to the endpoint.
- Mitigate SQL injection, cross-site scripting, cross-site request forgery where applicable, SSRF, and insecure direct object references.
- Apply safe CORS and network policies.
- Treat retrieved web content and uploaded content as untrusted.
- Run security checks and remediate critical findings before production release.

### NFR-02: Performance

- Establish measurable latency and throughput targets through representative baseline testing.
- Apply timeouts and bounded concurrency to expensive AI and research operations.
- Avoid loading large datasets into memory unnecessarily.
- Support pagination and appropriate database indexing.
- Do not promise fixed AI response times until target hardware and model performance are measured.

### NFR-03: Reliability

- Handle unavailable dependencies and transient failures gracefully.
- Use bounded retries only where safe.
- Prevent duplicate side effects when retrying operations.
- Define recovery objectives and test restoration.
- Separate liveness from readiness checks.

### NFR-04: Scalability

Use modular components and clear interfaces so the platform can grow without requiring a complete redesign. Avoid introducing distributed infrastructure until measured requirements justify it.

### NFR-05: Maintainability

- Enforce consistent code style and static analysis.
- Maintain typed interfaces where supported.
- Keep automated tests for critical behavior.
- Document architectural decisions.
- Require review for security-sensitive and data-changing modifications.

### NFR-06: Accessibility and usability

- Use readable typography and clear navigation.
- Support keyboard interaction on web.
- Provide meaningful labels and accessible error messages.
- Keep the mobile experience usable on small screens.
- Design for potentially unreliable network connectivity.

### NFR-07: Privacy

Collect only necessary user data. Define retention, deletion, access, and logging policies. Disclose whether AI requests are processed locally or sent to external providers.

### NFR-08: Cost and resource efficiency

Prefer free and open-source components, local inference where practical, bounded resource usage, and efficient storage. Any proposed paid dependency requires explicit approval.

## 8. Proposed Technical Architecture

The following is the proposed direction, not a substitute for reviewing the current repository or approving architecture decisions.

| Layer | Proposed technology | Responsibility |
|---|---|---|
| Web | Next.js, Tailwind CSS | Responsive browser experience |
| Android | React Native, Expo | Mobile application |
| API | Python, FastAPI | Business logic and API contracts |
| Database | PostgreSQL | Persistent application data |
| Migrations | Alembic | Versioned schema changes |
| ORM | SQLAlchemy | Database access |
| Local AI | Ollama | Local model inference |
| Search | SearXNG | Metasearch |
| Research | Controlled retrieval and extraction services | Source discovery, ranking, citations |
| Deployment | Docker Compose | Reproducible service deployment |
| Testing | Pytest and appropriate client-side test tools | Automated verification |
| CI | Repository-compatible CI workflow | Repeatable quality checks |

The existing project also contains a SQLite database decision that remains unresolved. PostgreSQL as the proposed long-term database does not authorize deleting, migrating, merging, or replacing existing SQLite data.

## 9. Data Requirements

The final data model must be derived from the approved SRS, existing schema, and reviewed ADRs.

Potential data categories include:

- User and access-control records, if accounts are approved.
- Agricultural questions and conversation records, if persistence is approved.
- Research jobs and retrieved source metadata.
- Model/provider configuration references without embedded secrets.
- Operational audit events.
- Application settings and feature configuration.

For each entity, document ownership, sensitivity, retention, validation rules, relationships, and deletion behavior.

Do not introduce a new schema or alter existing data merely because an entity appears in this proposed PRD.

## 10. Security and Governance Requirements

The following controls are mandatory:

1. Inspect the current repository, instructions, SRS, ADRs, tests, and owner approvals before implementation.
2. Resolve outstanding approval gates before starting restricted work.
3. Never overwrite, delete, merge, relocate, or migrate databases without explicit owner approval.
4. Never rotate or modify existing secrets without approval and a verified rollout plan.
5. Do not restart or change the voice service while its containment investigation remains approval-gated.
6. Do not execute destructive Docker commands without explaining the exact impact and receiving explicit confirmation.
7. Pin deployment image versions and use appropriate health checks, resource limits, non-root execution, and network isolation where feasible.
8. Keep real secrets out of source control and logs.
9. Document security-sensitive decisions and the evidence used to verify them.
10. Treat external content as untrusted, including content that attempts to influence system behavior.

## 11. Testing and Quality Assurance

### Required test categories

- Unit tests for business logic and validation.
- API integration tests.
- Database tests using controlled test data.
- Authentication and authorization tests, where applicable.
- Research-engine tests covering malformed URLs, timeouts, SSRF defenses, and unavailable providers.
- AI integration tests with deterministic mocks and separately identified live-model tests.
- Web and Android API compatibility tests.
- Migration tests using disposable test databases.
- Security scanning and dependency vulnerability checks.
- Deployment health-check tests.
- Backup and restore verification.

### Quality gates

A release candidate must not pass merely because the application starts.

Required evidence includes:
- Automated test results.
- Static analysis and type-check results.
- Migration verification.
- Security findings and their disposition.
- Health-check results.
- Backup and restore evidence.
- Documented rollback steps.
- A list of known limitations and unresolved risks.

Existing reported test results must be rerun when relevant; historical claims are not proof of the current state.

## 12. Acceptance Criteria for MVP

The MVP is accepted only when:

1. Approved core user journeys work end to end.
2. Web and Android clients use documented backend contracts.
3. AI and research failures produce safe, understandable responses.
4. Citations correspond to actual retrieved sources.
5. Security controls pass their defined tests.
6. Data migrations and persistence behavior are verified in a disposable test environment.
7. Backup and restoration are demonstrated using the approved procedure.
8. Deployment and recovery documentation matches the actual configuration.
9. No unauthorized database, secret, or infrastructure changes have occurred.
10. Outstanding defects and limitations are documented and accepted by the owner.
11. The owner approves the release scope and production deployment.

## 13. Delivery Plan

### Stage 0 — Discovery and governance

- Inventory the repository and current implementation.
- Review the SRS, ADRs, and existing tests.
- Resolve the canonical database decision.
- Select and approve the project license.
- Draft and individually review the six required ADRs: ADR-001, ADR-002, ADR-009, ADR-010, ADR-013, and ADR-014.
- Revise and approve Phase 1 scope.
- Verify the backup and recovery approach at `/data/MyFarmAI-backups`.
- Record outstanding security and infrastructure risks.

**Exit criterion:** All required prerequisites are resolved and the owner explicitly authorizes the next phase.

### Stage 1 — Backend foundation

- Establish approved configuration and API structure.
- Implement validated API contracts and error handling.
- Implement the approved data layer and migration process.
- Add health endpoints, logging, and automated tests.
- Establish secure development and deployment configuration.

### Stage 2 — AI and research capabilities

- Implement the provider abstraction and configured Ollama integration.
- Implement the approved search and retrieval pipeline.
- Add extraction limits, source ranking, citations, and SSRF defenses.
- Test provider failures and partial research results.

### Stage 3 — Client integration

- Connect the web and Android clients to the documented API.
- Implement the approved user journeys.
- Verify loading, offline, validation, and error states.

### Stage 4 — Hardening and release preparation

- Run full automated and security test suites.
- Verify database migrations, backup restoration, and rollback.
- Review deployment configuration and operational documentation.
- Produce a release-candidate report with evidence.
- Obtain explicit owner approval before production deployment.

Stages beyond Stage 0 must not be interpreted as authorized implementation work until the applicable governance gates are satisfied.

## 14. Success Metrics

Metrics must be instrumented and measured rather than assumed.

| Metric | Measurement approach |
|---|---|
| API reliability | Successful requests divided by eligible requests |
| API latency | p50, p95, and p99 latency by endpoint |
| Research quality | Human-reviewed relevance and source validity |
| Citation integrity | Percentage of citations that resolve to retrieved sources |
| Error rate | Failures categorized by endpoint and dependency |
| Test reliability | Pass/fail results and flaky-test rate |
| Recovery readiness | Successful restoration in a controlled test |
| Client compatibility | Successful completion of approved journeys on supported clients |
| Resource use | CPU, memory, storage, and inference utilization |

Numeric targets must be agreed after baseline measurements and workload definition.

## 15. Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Conflicting database locations | Resolve and document the canonical location before data changes |
| Unreviewed architectural decisions | Require individually reviewed ADRs |
| Fabricated or weak citations | Validate citations against retrieved source records |
| SSRF through research URLs | Apply strict URL and IP validation, egress controls, and redirect revalidation |
| Local AI resource constraints | Benchmark on target hardware and limit concurrency |
| Search-provider failure | Use timeouts, partial-result handling, and controlled fallbacks |
| Secret leakage | Use approved secret management and redact sensitive logs |
| Unsafe deployment configuration | Harden containers and verify health checks and rollback |
| Unverified production readiness | Require evidence-based release gates |
| Scope expansion | Use an owner-approved scope and change-control process |

## 16. Open Decisions Requiring Owner Approval

- Canonical SQLite database: `backend/data/app.db` versus `data/app.db`.
- Project license.
- Review and approval of ADR-001, ADR-002, ADR-009, ADR-010, ADR-013, and ADR-014.
- Revised Phase 1 scope and authorization.
- Backup and recovery verification for `/data/MyFarmAI-backups`.
- SearXNG secret rotation plan.
- Voice-service containment investigation.
- Final production hosting, domain, and deployment topology.
- User account, data retention, and privacy policies.
- Performance targets and supported client versions.

These decisions must not be silently inferred by implementation agents.

## 17. Definition of Done

A feature is done only when:

- Its requirements and scope are approved.
- Its implementation matches the documented design.
- Tests and relevant static checks pass.
- Security and failure paths are addressed.
- Documentation is updated.
- No unauthorized data or infrastructure changes have occurred.
- Verification evidence is recorded.
- Any remaining limitations are disclosed.

**Production-ready** means the release has passed its agreed functional, security, operational, recovery, and deployment gates. It does not simply mean that the code compiles or the application runs locally.

## 18. Approval Record

**Document status:** Draft — Owner Review Required

**Owner decision:** Pending

**Approved scope:** Pending

**Architecture decisions:** Pending required reviews

**Phase 1 authorization:** Not authorized until outstanding prerequisites are resolved and the owner explicitly approves commencement.

**Production release approval:** Not granted by this document.

---

**End of MyFarmAI PRD v1.0**
