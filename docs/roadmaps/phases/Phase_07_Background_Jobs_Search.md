# Phase 7 — Optional Background Jobs and Search Upgrades

## Objective

Introduce asynchronous infrastructure only when real workload measurements show the request-response model is insufficient.

## Entry conditions
- Phases 1–6 are stable enough to measure.
- A documented bottleneck or asynchronous requirement exists.
- Added RAM, disk and operational burden are acceptable.

## Decision gate: do we need a queue?
Measure request latency, timeout rates, workload duration, concurrency and retry needs. Do not add a queue just because the architecture diagram includes one.

Potential workloads:
- Multi-page research.
- Document extraction/indexing.
- Scheduled refresh of licensed data.
- Long-running AI requests.
- Notifications.

## Optional implementation
If justified and approved:
- Evaluate Valkey and a maintained worker framework.
- Keep queue access internal.
- Define idempotency keys, retry limits, backoff and terminal failure handling.
- Persist job status and expose safe status APIs.
- Make duplicate delivery safe.
- Ensure worker shutdown and restart behavior is documented.
- Prevent unbounded queues and runaway retries.

## Vector search decision
- Benchmark PostgreSQL full-text search and simpler retrieval approaches first.
- Add Qdrant only if a defined evaluation demonstrates material improvement.
- Record embedding model, vector dimensions, collection schema, versioning and reindexing process.
- Keep embeddings local where possible and avoid paid embedding APIs.
- Measure memory/disk cost and backup implications.

## Deliverables
- Benchmark report and approved decision.
- Optional queue/job architecture and failure model.
- Idempotency/retry tests.
- Search evaluation and vector-store ADR, if applicable.
- Operational runbook for optional services.

## Acceptance criteria
- [ ] A measured requirement justifies each additional service.
- [ ] Resource usage is measured on target hardware.
- [ ] Jobs are bounded, observable and safe to retry.
- [ ] Duplicate execution does not corrupt data.
- [ ] Search upgrade demonstrates measurable value.
- [ ] Optional services can be disabled cleanly if designed as optional.

## Exit gate
Approve each optional component independently. If no measured need exists, document the deferral and finish the phase without adding it.
