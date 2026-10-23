# MyFarmAI — Application Flow Document

**Document ID:** MYFARMAI-APPFLOW-001  
**Version:** 1.0  
**Status:** Draft — Owner Review Required  
**Platforms:** Web and Android  
**Related Documents:** PRD, TRD, SRS, Architecture Decision Records

## 1. Purpose

This document defines the navigation structure, user journeys, application states, and service interactions for MyFarmAI.

It serves as the reference for frontend developers, backend developers, UI/UX designers, testers, and OpenCode implementation agents.

The flow must be reconciled with the existing repository and approved requirements before implementation. Proposed screens do not automatically authorize new features.

## 2. Application Entry Flow

<CodeBlock language="mermaid" editable>
flowchart TD
    A[Launch MyFarmAI] --> B[Initialize Application]
    B --> C{Configuration Valid?}
    C -- No --> D[Show Configuration Error]
    C -- Yes --> E[Check Backend Availability]
    E --> F{Backend Reachable?}
    F -- No --> G[Show Connection State and Retry]
    G --> E
    F -- Yes --> H[Load Application Home]
    H --> I[Ask Agricultural Question]
    H --> J[Explore Research]
    H --> K[Open Settings]
</CodeBlock>

### Flow rules

- The application must not display a successful backend state when the service is unavailable.
- Network failures must produce a recoverable error state.
- Retry operations must be bounded and must not create duplicate side effects.
- Authentication screens are included only if account functionality is approved.

## 3. Main Navigation Structure

The proposed navigation model is:

<CodeBlock language="mermaid" editable>
flowchart TD
    HOME[Home]
    ASK[Ask MyFarmAI]
    RESEARCH[Research Results]
    HISTORY[Conversation History]
    SETTINGS[Settings]
    DETAIL[Answer or Research Detail]

    HOME --> ASK
    HOME --> RESEARCH
    HOME --> HISTORY
    HOME --> SETTINGS

    ASK --> DETAIL
    RESEARCH --> DETAIL
    HISTORY --> DETAIL
    DETAIL --> ASK
</CodeBlock>

History, saved results, and settings subfeatures must be retained or implemented only when supported by the approved scope and current product design.

## 4. Agricultural Question-and-Answer Flow

### 4.1 User journey

1. The user opens the home screen.
2. The user enters an agricultural question.
3. The client validates required input.
4. The client submits a request to the backend API.
5. The backend validates the request and applies applicable access and rate limits.
6. The AI orchestrator determines the approved processing route.
7. The system obtains an answer from the configured model and, when appropriate, the research engine.
8. The backend validates the response structure and source metadata.
9. The client displays the answer, citations, and relevant limitations.
10. The user may submit a follow-up question.

<CodeBlock language="mermaid" editable>
sequenceDiagram
    actor User
    participant App as Web or Android
    participant API as FastAPI
    participant AI as AI Orchestrator
    participant Model as Ollama
    participant Research as Research Engine

    User->>App: Submit agricultural question
    App->>API: POST /api/v1/ai/answer
    API->>API: Validate and authorize request
    API->>AI: Process approved request
    AI->>Model: Request model inference
    Model-->>AI: Model response
    opt Research required and enabled
        AI->>Research: Retrieve supporting evidence
        Research-->>AI: Sources and retrieval status
    end
    AI-->>API: Answer and source metadata
    API-->>App: Structured response
    App-->>User: Display answer and citations
</CodeBlock>

### 4.2 UI states

The question-and-answer interface must support:

- **Idle:** Ready to accept a question.
- **Validating:** Checking user input.
- **Submitting:** Request has been sent.
- **Processing:** Waiting for AI or research results.
- **Success:** A valid answer has been returned.
- **Partial result:** Some dependencies or sources were unavailable.
- **Empty result:** No usable answer was returned.
- **Error:** Request failed.
- **Cancelled:** Request was cancelled, if cancellation is supported.

The interface must distinguish a partial answer from a complete successful result.

## 5. Research Flow

### 5.1 Research lifecycle

<CodeBlock language="mermaid" editable>
flowchart TD
    A[Research Query] --> B[Validate Query]
    B --> C{Valid?}
    C -- No --> D[Show Validation Error]
    C -- Yes --> E[Search with SearXNG]
    E --> F[Normalize and Deduplicate]
    F --> G[Rank Candidate Sources]
    G --> H[Validate URLs and Destinations]
    H --> I[Retrieve Permitted Content]
    I --> J[Extract Text and Metadata]
    J --> K[Generate Evidence-Based Synthesis]
    K --> L[Validate Citations]
    L --> M[Return Results]
    M --> N[Display Summary and Sources]
</CodeBlock>

### 5.2 Research requirements

- Search and retrieval operations must use configured providers.
- Retrieved URLs must pass SSRF and destination validation.
- Content retrieval must enforce timeouts and response-size limits.
- Failed sources must not be represented as successfully retrieved.
- Citations must correspond to real source records.
- Partial results must identify relevant retrieval limitations.
- Untrusted web content must never override system instructions or access controls.

## 6. Backend Request Lifecycle

All client requests must follow a consistent lifecycle.

<CodeBlock language="mermaid" editable>
flowchart TD
    A[Client Request] --> B[API Routing]
    B --> C[Schema Validation]
    C --> D{Valid Request?}
    D -- No --> E[Structured 4xx Error]
    D -- Yes --> F[Authorization and Rate Limits]
    F --> G{Allowed?}
    G -- No --> H[Safe Error Response]
    G -- Yes --> I[Application Service]
    I --> J[Required AI, Research, or Data Service]
    J --> K[Normalize Result]
    K --> L[Structured API Response]
</CodeBlock>

Internal stack traces, credentials, and sensitive configuration must not be returned to clients.

## 7. Authentication Flow

**Status:** Conditional — requires an approved account and authentication requirement.

If authentication is approved, the flow should be:

1. User opens the sign-in screen.
2. User submits credentials or completes the approved identity flow.
3. Backend validates identity.
4. Backend issues or establishes the approved session.
5. Client stores credentials using the appropriate platform security mechanism.
6. Protected requests include valid authentication.
7. Expired or revoked sessions are handled safely.
8. Sign-out invalidates the relevant session or credentials.

Authorization must be enforced by the backend. Hiding a frontend control is not sufficient security.

## 8. Error and Recovery Flows

| Failure | Expected application behavior |
|---|---|
| Backend unavailable | Show connection error and controlled retry |
| Invalid question | Explain the validation issue |
| AI model unavailable | Report model unavailability; do not fabricate success |
| Research provider unavailable | Return a clear error or valid partial result |
| No sources found | Explain that no usable sources were found |
| Source blocked or timed out | Mark retrieval as unsuccessful |
| Authentication expired | Request reauthentication if accounts are enabled |
| Rate limit exceeded | Explain the limit and provide retry guidance when available |
| Unexpected backend failure | Show a safe error and correlation identifier |
| Network interrupted | Preserve recoverable user input where safe |

Retries must respect request idempotency and resource limits.

## 9. Settings and Administration

### User settings

Only approved settings should appear in the user interface. Possible options include language, display preferences, and model or research preferences when supported by the product requirements.

### Administration

Administrative operations should use a separate authorized access path. The backend must enforce roles and permissions, and security-sensitive changes must be auditable.

Model administration, provider secrets, database maintenance, and deployment controls must not be exposed as ordinary user actions.

## 10. Web and Android Flow Parity

Both clients should implement the same approved core journeys and API contracts.

| Area | Web | Android |
|---|---|---|
| Question input | Responsive web form | Mobile-friendly input |
| Request status | Loading and progress state | Loading and progress state |
| Research results | Source list and answer view | Source list and answer view |
| Failure handling | Accessible error state | Network-aware error state |
| Authentication | Approved web session flow | Approved mobile session flow |
| Configuration | Environment-specific API configuration | Environment-specific API configuration |

Platform-specific navigation and storage must follow the appropriate security and usability conventions.

## 11. Flow-Level Testing

The implementation must verify:

1. Application startup with valid configuration.
2. Application behavior when the backend is unavailable.
3. Successful agricultural question submission.
4. Invalid request rejection.
5. Successful AI response rendering.
6. Research result rendering with verified citations.
7. Partial results when some sources fail.
8. AI and search-provider timeout handling.
9. Authentication and authorization where applicable.
10. Duplicate submission and retry behavior.
11. Web and Android API contract compatibility.
12. Safe error display without sensitive internal details.

Each test must identify its expected result and recorded outcome.

## 12. Implementation Constraints

- Inspect the current repository before creating or restructuring screens.
- Reuse existing routes, components, and API contracts when appropriate.
- Follow the approved PRD, TRD, SRS, and ADRs.
- Do not implement optional flows solely because they appear in this document.
- Do not modify or migrate databases without owner approval.
- Do not rotate secrets or change the voice service without approval.
- Do not run destructive Docker commands without explicit confirmation.
- Update documentation when application behavior changes.
- Mark unimplemented flows and unverified tests accurately.

## 13. Completion Criteria

The application flow implementation is complete when:

- Every approved screen has a documented entry and exit path.
- Every approved user journey has a defined success and failure path.
- API contracts match the implemented backend.
- Loading, empty, partial, error, and success states are covered.
- Web and Android flows pass their applicable tests.
- Accessibility and security requirements are verified.
- Documentation matches the implemented application.
- Outstanding limitations are documented and owner-approved.

**Document status:** Draft — Owner Review Required.

**Phase 1 authorization:** Not granted by this document.

---

**End of MyFarmAI Application Flow Document v1.0**
