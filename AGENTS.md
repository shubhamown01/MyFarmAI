## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

When the user types `/graphify`, use the installed graphify skill or instructions before doing anything else.

Rules:
- When graphify-out/graph.json exists, run `graphify query "<question>"` before your first grep, search or source-file read for a codebase question, and put this rule in every subagent prompt that explores code. Read raw files only for lines the graph or an earlier read already located. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- Dirty graphify-out/ files are expected after hooks or incremental updates; dirty graph files are not a reason to skip graphify. Only skip graphify if the task is about stale or incorrect graph output, or the user explicitly says not to use it.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
- A committed graphify-out/graph.json is rewritten whole on every build, so a large diff to it in a pull request is expected. Do not flag it as churn or suggest skipping the graph rebuild or its hooks.

## Automatic Skill Orchestration

For every task, automatically discover and use the relevant installed skills before implementation.

### Mandatory workflow
1. Read this AGENTS.md and follow all project rules.
2. For codebase questions, follow the Graphify rules above before searching or reading source files.
3. Identify relevant skills in `.opencode/skills/`, `.agents/skills/`, `~/.config/opencode/skills/`, and `~/.agents/skills/`.
4. Inspect skill descriptions and load the complete instructions for every skill relevant to the task, using the available skill-loading tool when supported.
5. Combine compatible skills when they provide distinct value. Do not load unrelated skills merely because they are installed.
6. If a relevant skill is unavailable or cannot be loaded, state that limitation and continue safely.
7. Follow MyFarmAI architecture, existing conventions, security requirements, and documentation rules. Do not invent APIs, dependencies, or live data.
8. Prefer minimal, maintainable changes. Avoid unnecessary abstractions, dependencies, and rewrites. Preserve existing working behavior.
9. Use connected MCP tools when they materially help the task. Do not call every MCP tool automatically.
10. Before modifying files, summarize the intended approach for substantial changes. Do not deploy, delete data, expose secrets, or perform destructive operations without explicit authorization.
11. After changes, run appropriate checks such as type checking, linting, tests, and browser verification when applicable.
12. Follow the Graphify update rule after code changes.

### Skill selection by task
- UI and frontend: UI/UX Pro Max, frontend-design or frontend-ui-engineering, web-design-guidelines, React best practices, composition patterns, and relevant MyFarmAI design skills.
- React and Next.js: React best practices, composition patterns, performance optimization, and relevant framework guidance.
- Backend and APIs: relevant API design, security, testing, and backend-specific skills that are actually installed.
- Docker and infrastructure: Docker build, Compose, project-foundation, and destructive-operation guardrail skills when relevant.
- Testing and debugging: webapp-testing, Playwright-related instructions, debugging, and verification skills when relevant.
- Performance: performance-optimization and vercel-optimize when relevant.
- Deployment: deployment skills only when deployment is explicitly requested; review their instructions and risk before executing.
- Branding and visual assets: brand, design-system, banner-design, and other relevant design skills when applicable.
- Documentation and planning: relevant project-review, planning, and documentation skills.

### Skill conflict and safety rules
- Prefer task-specific project skills alongside applicable general skills.
- Follow security and destructive-operation guardrails over convenience.
- If skills conflict, prioritize explicit user requirements, project instructions, security, and correctness; explain material conflicts.
- Do not claim a skill, plugin, MCP tool, test, or verification ran unless it actually did.
- Do not execute every skill at once. Select the complete relevant set for the current task.

---

## MANDATORY DOCUMENT-FIRST ENGINEERING POLICY

**Repository:** `/data/MyFarmAI`

**Purpose:** Ensure every development task, code change, refactor, test, architecture decision, and documentation update follows the approved MyFarmAI project requirements and governance records.

### 1. Mandatory rule before starting any work

Before performing any task in MyFarmAI, you MUST:

1. Confirm the repository root is `/data/MyFarmAI`.
2. Read the authoritative `PHASE_01_IMPLEMENTATION_PLAN.md` and the current Owner Approval Record. Locate their actual paths; do not assume their location.
3. Read relevant Architecture Decision Records (ADRs), governance decisions, and approval records.
4. Read the applicable product documents under `docs/product/`.
5. Inspect the relevant existing code, configuration, tests, and Git status.
6. Determine whether the requested task is authorized, blocked, or restricted.
7. Identify every document that the proposed task may affect.
8. Establish the task scope, dependencies, risks, acceptance criteria, and verification steps before implementation.

**Never start coding based only on the latest user message, a previous conversation, or an assumption about the repository.** Read the current source of truth first.

For a small task, perform a focused review of the authoritative governance documents and directly relevant product documents. For a broad project change, architecture change, or full-project implementation, review the complete product documentation set.

If a required document is missing, conflicting, or unclear, investigate the repository and record the gap. Do not invent its contents or pretend it was reviewed.

### 2. Authoritative product documentation

Use the following directory as the primary product-documentation reference:

```text
/data/MyFarmAI/docs/product/
├── PRD.md
├── TRD.md
├── APP_FLOW.md
├── UI_UX_DESIGN_BRIEF.md
├── UI_UX_DESIGN_SYSTEM.md
├── BACKEND_SCHEMA.md
├── IMPLEMENTATION_PLAN.md
└── flows/
    ├── APPLICATION_ENTRY_FLOW.md
    ├── AGRICULTURAL_QA_FLOW.md
    ├── RESEARCH_FLOW.md
    ├── AUTHENTICATION_FLOW.md
    └── ERROR_RECOVERY_FLOW.md
```

Use `IMPLEMENTATION_PLAN.md` as the standardized filename. If the repository currently contains `MPLEMENTATION_PLAN.md`, inspect it and preserve its contents and history when correcting references.

#### Document responsibilities

- `PRD.md`: product purpose, users, requirements, scope, priorities, and acceptance criteria.
- `TRD.md`: technical architecture, technology choices, interfaces, security, and deployment.
- `APP_FLOW.md`: overall application navigation and user journeys.
- `UI_UX_DESIGN_BRIEF.md`: design goals, user needs, and visual direction.
- `UI_UX_DESIGN_SYSTEM.md`: design tokens, typography, colors, components, and interaction states.
- `BACKEND_SCHEMA.md`: proposed logical data model, entities, relationships, and constraints.
- `IMPLEMENTATION_PLAN.md`: delivery stages, task dependencies, approval gates, and verification criteria.
- `flows/APPLICATION_ENTRY_FLOW.md`: application startup and initial routing.
- `flows/AGRICULTURAL_QA_FLOW.md`: agricultural question-and-answer workflow.
- `flows/RESEARCH_FLOW.md`: research retrieval, evidence, source handling, and citations.
- `flows/AUTHENTICATION_FLOW.md`: authentication and session workflows, if in scope.
- `flows/ERROR_RECOVERY_FLOW.md`: errors, retries, fallbacks, and recovery behavior.

These documents must remain consistent with one another and with the approved governance records.

### 3. Source-of-truth precedence

When requirements or documents disagree, apply this order:

1. Explicit owner-approved governance decisions and approval records.
2. Approved ADRs and formally approved scope.
3. Approved product requirements and technical decisions.
4. The current product documentation.
5. Existing source code and tests as evidence of current behavior.
6. Engineering proposals, clearly labeled as proposed and not approved.

Do not treat an existing implementation as proof that its design was approved.

Do not silently reconcile conflicting requirements. Record the conflict, affected documents, risks, and recommended resolution. Obtain approval when the decision requires owner authorization.

### 4. Update all affected documents for every task

Before implementation, create a documentation impact list.

After implementation, update every document materially affected by the change. Do not update unrelated documents just to create activity.

Examples:

- A change to product scope requires a PRD update and, where applicable, an implementation-plan update.
- An API or service architecture change requires a TRD update and relevant API documentation.
- A screen, navigation, or user interaction change requires the relevant application-flow and UI/UX documentation updates.
- A database model change requires a backend-schema update, architecture review, and migration documentation where authorized.
- An agricultural answer workflow change requires an agricultural QA flow update.
- A research or citation change requires a research flow and technical-design update.
- An authentication change requires an authentication flow and security documentation update.
- An error-handling change requires an error-recovery flow update and corresponding tests.
- A deployment, dependency, configuration, or infrastructure change requires the relevant operational documentation updates.
- A change to delivery order or completion status requires an implementation-plan update.

For each change, verify that documentation accurately describes the implementation. Never document a proposed feature as implemented or a planned test as passed.

**No code change without corresponding documentation updates.**

### 5. Preserve the Phase 1 governance gates

Phase 1 must remain blocked until the required governance gates are explicitly resolved and approved.

Current known gates include:

1. Canonical SQLite database location decision.
2. Project license selection.
3. Individual review and approval of ADR-001, ADR-002, ADR-009, ADR-010, ADR-013, and ADR-014.
4. Revised Phase 1 scope and approval.
5. Verified backup and recovery procedure for `/data/MyFarmAI-backups`.
6. Voice-service containment approval, including consumer-dependency verification.

Verify the current status from authoritative records every time; do not assume a gate has been resolved because it appeared in a previous conversation.

While a gate is unresolved:

- Continue safe discovery, analysis, planning, and documentation work when permitted.
- Clearly identify implementation tasks blocked by that gate.
- Prepare decision records and verification plans when useful.
- Do not mark the gate complete without evidence and the required approval.
- Do not begin Phase 1 implementation merely because this policy has been added.

This policy does not itself authorize database changes, migrations, secret rotation, voice-service shutdown, destructive Docker operations, production deployment, or other restricted activities.

### 6. Protect existing data and services

Before any operation that may affect data, services, secrets, or infrastructure:

1. Identify the exact target and potential impact.
2. Inspect the current state using non-destructive methods.
3. Check the applicable approval requirements.
4. Explain the risk and required authorization.
5. Proceed only when authorized.
6. Record the outcome and verification evidence.

Never assume the canonical database path. Never delete, overwrite, merge, migrate, or relocate an existing database without the required explicit approval.

Do not claim a backup, restore, service containment, security scan, test suite, or deployment is verified unless it was actually performed and evidence was recorded.

### 7. Required workflow for every task

Follow this workflow in order:

**A. Read** — Read the governing records and relevant product documents.

**B. Inspect** — Inspect the affected code, dependencies, configuration, tests, and Git status.

**C. Classify** — Identify authorization status, scope, risks, dependencies, and blocked operations.

**D. Plan** — List intended changes, affected files and documents, tests, and acceptance criteria.

**E. Implement** — Make only authorized, scoped changes. Preserve unrelated work.

**F. Document** — Update the affected product, architecture, operational, and implementation documents.

**G. Verify** — Execute safe, relevant tests and checks. Record actual results.

**H. Review** — Inspect the diff, check for accidental changes and secrets, and confirm documentation consistency.

**I. Report** — Summarize changes, evidence, unresolved issues, and the next authorized tasks.

If a step is blocked, report why and continue independent work only where safe and authorized.

### 8. Task completion report

At the end of each meaningful task, report:

- Task and authorization status.
- Governance and product documents reviewed.
- Code and configuration files changed.
- Documentation created or updated.
- Tests and checks actually executed.
- Results and evidence.
- Risks, failures, and unresolved decisions.
- Remaining work and next authorized step.

Use these status labels consistently:

- `PASS — verified with evidence`
- `FAIL — verification failed`
- `BLOCKED — approval or dependency required`
- `NOT TESTED — not verified`
- `PROPOSED — not approved`
- `COMPLETE — acceptance criteria verified`

### 9. Make this policy persistent

Add this policy to the repository's applicable agent-instruction file, preferably `/data/MyFarmAI/AGENTS.md`, after inspecting whether one already exists.

If an instruction file already exists, preserve its valid content and merge this policy without overwriting unrelated project instructions.

If OpenCode uses additional repository-specific instruction files, inspect its actual configuration and follow the supported mechanism. Do not assume that editing one file automatically configures every tool or every global OpenCode project.

Keep the policy concise enough for agents to follow, but preserve all mandatory governance, document-first, data-protection, and verification rules.

### 10. Initial execution

Begin by:

1. Inspecting Git status and the current repository structure.
2. Locating and reading `PHASE_01_IMPLEMENTATION_PLAN.md` and the Owner Approval Record.
3. Reading the current product documents and existing agent-instruction files.
4. Identifying conflicting instructions, missing documents, and unresolved gates.
5. Preparing a safe change plan for installing this policy.
6. Updating the appropriate persistent instruction file and any necessary documentation.
7. Verifying the final diff and reporting what was actually changed.

Do not begin unrelated product implementation during this task.

**Final principle: Every task starts with the authoritative documents, every implementation follows approved requirements, every material change updates affected documentation, and every completion claim is supported by evidence.**