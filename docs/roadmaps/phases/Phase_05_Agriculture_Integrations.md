# Phase 5 — Agriculture Domain and Data Integrations

## Objective

Deliver prioritized agricultural workflows and dependable data adapters with clear provenance, freshness and licensing.

## Entry conditions
- Product requirements identify the highest-priority agricultural workflows.
- Database, auth and API conventions are stable.
- External data sources pass licensing and commercial-use review.

## Workstreams

### 1. Domain workflows
Implement only approved MVP use cases. Potential modules include:
- Farm profiles and locations.
- Crop and crop-cycle records.
- Seasonal and regional context.
- Advisory requests and saved recommendations.
- User preferences and notifications.

Each workflow needs acceptance criteria and API contracts before implementation.

### 2. Adapter boundaries
Create provider-independent interfaces for weather and public agriculture data. Keep provider-specific payloads and error handling in adapters.

### 3. Data quality and provenance
For each external record, retain appropriate metadata:
- Source/provider.
- Retrieval time and source timestamp.
- Geographic coverage and units.
- Freshness/expiry.
- Attribution and licence reference.
- Validation status and relevant quality flags.

Distinguish observed data, provider forecasts, user-entered facts and model-generated estimates.

### 4. Licensing and cost
- Verify commercial-use rights and attribution obligations.
- Review rate limits, caching terms, redistribution limits and availability.
- Do not treat “free tier” as equivalent to unrestricted commercial use.
- Open-Meteo's reported non-commercial restriction is a blocker until a compliant plan or alternative is approved.
- Do not make a third-party API mandatory for core operation unless approved and appropriately licensed.

### 5. Failure handling
- Validate units, timestamps, coordinates and missing fields.
- Handle stale data and provider downtime explicitly.
- Use bounded retries and timeouts.
- Cache only where provider terms permit.
- Avoid false precision in agricultural recommendations.

## Deliverables
- Prioritized domain API contracts.
- Provider adapter interfaces.
- Source registry and licensing register.
- Data validation and freshness rules.
- Integration contract tests and fallback behavior.

## Acceptance criteria
- [ ] Each workflow has documented requirements.
- [ ] Provider payloads are validated.
- [ ] Source and freshness metadata are available.
- [ ] Commercial-use and attribution terms are recorded.
- [ ] Provider failures do not crash unrelated workflows.
- [ ] Model-generated estimates are not misrepresented as verified source data.

## Exit gate
Product and technical reviewers accept the MVP workflows, data quality rules, licensing register and provider failure strategy.
