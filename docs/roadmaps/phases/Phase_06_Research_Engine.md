# Phase 6 — Open-Source Research Engine

## Objective

Build a source-backed research pipeline using self-hosted search and safe extraction, with traceable citations and no mandatory paid search API.

## Entry conditions
- Security controls and workload limits are implemented.
- Research use cases, data retention and permitted source handling are approved.
- SearXNG licensing and distribution implications have been reviewed.

## Workstreams

### 1. Search
- Operate SearXNG as an internal service.
- Define a search adapter independent of the engine.
- Bound request time, result count and concurrency.
- Record source URLs and search metadata where permitted.
- Handle unavailable engines and empty results gracefully.

### 2. Safe extraction
- Fetch only allowed HTTP/HTTPS URLs.
- Block loopback, private, link-local, reserved and otherwise disallowed IP ranges.
- Revalidate DNS resolution and redirects to mitigate DNS rebinding/SSRF.
- Restrict ports and protocols.
- Apply response-size, redirect-count and timeout limits.
- Do not forward credentials or internal headers to target sites.
- Treat page text as untrusted data and strip active content.

### 3. Ranking and source quality
Rank retrieved sources using documented, testable criteria such as relevance, freshness, source quality, geographic applicability and query intent. Do not invent authority scores without evaluation.

### 4. Citations and answer generation
- Store canonical URL, title, publisher/domain, timestamps, extraction status and attribution/licence information as appropriate.
- Require answer claims to map to retrieved evidence when the feature promises citations.
- Distinguish source-derived claims from model synthesis.
- Return a useful “insufficient evidence” response when sources are weak or conflicting.
- Do not present model-generated text as a source.

### 5. Prompt-injection defense
- Treat web content as untrusted.
- Retrieved instructions must not override system policy or authorize tools.
- Keep browsing/extraction separate from privileged execution.
- Apply least privilege to research components.
- Add adversarial tests for malicious pages, instructions and redirect chains.

### 6. Search/index storage
- Start with PostgreSQL full-text search where suitable.
- Respect robots directives, site terms, copyright and rate limits.
- Do not assume searchability permits bulk copying or long-term retention.
- Benchmark before adopting vector storage.

## Deliverables
- Research API and pipeline.
- Citation/provenance model.
- Source ranking rules and evaluation set.
- SSRF and prompt-injection test suite.
- Retention and permitted-source policy.

## Acceptance criteria
- [ ] Citations resolve to evidence actually retrieved.
- [ ] SSRF and redirect protections are tested.
- [ ] Response size and time are bounded.
- [ ] Malicious retrieved instructions cannot authorize actions.
- [ ] Weak or conflicting evidence is represented honestly.
- [ ] Source use and retention comply with reviewed terms.
- [ ] Search works without a mandatory paid API.

## Exit gate
Security, product and research-quality reviews accept citation correctness, source handling and adversarial test results.
