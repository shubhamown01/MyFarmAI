# Phase 4 Implementation Plan — Local AI Gateway and Ollama

**Phase:** 4 — authorized (owner blanket approval 2026-10-28), not started beyond FCL-027/028
**Date:** 2026-10-29
**Status:** PLAN DRAFTED — awaiting owner review; work may proceed under blanket approval with per-task verification
**Prerequisites:** Phase 3 COMPLETE (exit gate: security-engineer APPROVE-WITH-CONDITIONS, both conditions remediated in FCL-026; fast-follows closed in FCL-027; 114 tests green)
**Roadmap:** [`../phases/Phase_04_Local_AI_Ollama.md`](../phases/Phase_04_Local_AI_Ollama.md)
**Related:** ADR-006 (prompt/AI policy), ADR-007 (research/SSRF, later phases), `docs/engineering/AUTHZ_MATRIX.md`, `docs/product/flows/AGRICULTURAL_QA_FLOW.md`

---

## 1. Objectives

Per the roadmap workstreams:

1. Provider-independent AI gateway interface; Ollama-specific behavior confined to its adapter
2. Model inventory, licenses, and recorded benchmarks on target hardware before default-model selection
3. Reliability: timeouts, bounded concurrency + queue depth, cancellation, degraded mode (no paid fallback)
4. Versioned prompt templates; structured-output schema validation; model output treated as untrusted
5. Conversation privacy under approved retention rules; no full-conversation logging by default
6. Small versioned evaluation set; groundedness/language/unsafe-advice checks before model changes

**Already complete (absorbed from Phase 3 exit gate, FCL-026/027):**
- [x] AI-request concurrency bound (`ai_max_concurrent_requests=2` semaphore in async chat path)
- [x] Bounded rate-limit counters and lockout tracking
- [x] Full revocation of a user's refresh tokens on refresh reuse
- [x] Unified flat error envelope `{detail, error_code}` (single exception handler)
- [x] `openapi.json` regenerated (FCL-028)

**Current state:** `OllamaClient` (services/ollama.py) is a thin chat client with typed errors (timeout/connection/model-not-found) and health check; chat service calls it directly — no gateway interface, no queue-depth bound, no structured-output path, no prompt versioning, no eval set.

## 2. Tasks

- [x] **P4-01** AI gateway interface (`app/ai/gateway.py`): protocol with `chat`, `health/capability`, model metadata, error mapping; Ollama adapter wrapping `OllamaClient` so Ollama specifics never leave the adapter; chat service depends on the interface only. Update `docs/backend/ARCHITECTURE.md` + FCL
- [x] **P4-02** Reliability hardening in adapter/gateway: connect/read/overall timeouts (existing) + bounded **queue depth** (reject with 503 `AI_BUSY` when the semaphore backlog exceeds N) + request cancellation on client disconnect; degraded-mode response contract documented in `ERROR_RECOVERY_FLOW.md`
- [x] **P4-03** Model inventory + license check: list installed models on host (`ollama list`), record sizes/families/licenses in `docs/backend/MODEL_INVENTORY.md`; confirm nothing requires paid APIs
- [x] **P4-04** Benchmark harness (`backend/scripts/benchmark_models.py`, results in `docs/backend/MODEL_BENCHMARKS.md`): representative agricultural QA prompts; measure latency, RAM/VRAM, failure rate per model on the 2 GiB VRAM host; **recorded results before any default-model change** (ties to P1-17)
- [x] **P4-05** Prompt templates versioned (`app/ai/prompts/`): `build_system_prompt` moved/versioned; system policy separated from user content; template version recorded on conversations where useful
- [ ] **P4-06** Structured-output validation (when structured tasks arrive): schema-validated; invalid output rejected safely (retry bounded, then degrade) — model output never triggers privileged actions
- [x] **P4-07** Privacy: no full conversations in logs (audit current chat logging); conversation retention/deletion per ADR-015 owner decision; record model+template version on messages where useful — **audit clean (FCL-037); ADR-015 retention remains owner-pending; prompt-version persistence deferred (needs approved migration)**
- [x] **P4-08** Evaluation set (small, versioned, in repo `backend/evals/`): groundedness, language behavior, unsafe-advice refusal; run before any default-model change; results recorded
- [x] **P4-09** Docs pass: `AGRICULTURAL_QA_FLOW.md` alignment, `ARCHITECTURE.md` AI section, resource-budget guide, FCL/CHANGELOG per change

## 3. Acceptance Criteria (from roadmap — verified, not asserted)

- [ ] Core AI paths work without paid API keys (P4-01..P4-03)
- [ ] Model/provider specifics do not leak into domain modules (P4-01)
- [ ] Timeouts and concurrency are bounded — incl. queue depth (P4-02)
- [ ] Invalid structured output is rejected safely (P4-06, when applicable)
- [ ] Failure behavior is tested (P4-02 + existing error-path tests)
- [x] Model selection is supported by recorded benchmarks (P4-03/P4-04/P4-08)
- [ ] Private prompts and conversations handled under approved retention rules (P4-07, ADR-015)

**Exit gate:** AI gateway passes reliability, resource, privacy and evaluation review on the target hardware (security-engineer + qa-reviewer evidence).

## 4. Constraints & Notes

- **Hardware:** 7 GiB RAM, 2 GiB VRAM, ~5 GB free on `/`; models must fit 2 GiB VRAM or run CPU-tier with latency recorded; model downloads go to `/data` per HDD-first policy (Ollama storage location must be verified before any pull)
- **Ponytail/minimal-change discipline:** smallest complete change per task; no abstraction beyond the gateway protocol
- **Owner decisions pending (not blockers for P4-01/02/05):** exposure sign-off; rehearsal-data restore; login-UI coordination before image rebuild
- **Quality gate:** `bash scripts/check.sh` (exact flags; `--exclude app/orchestrator`); pytest from `backend/` only; never bare ruff
- Conventions: `uuid.UUID` never `str`; `_aware()` datetimes; `AuditEventType` members only; no code change without documentation + FCL entry


## Model 1 acceptance statement (`qwen3:0.6b` — recorded 2026-10-29)

**ACCEPTED** as the lightweight chat baseline, per the Phase 4 master prompt §6 Model 1 gate:
- Responses validated through the gateway (FCL-029): error mapping, timeouts, bounded concurrency (2) + queue depth (10) → 503 `AI_BUSY`.
- Full functional/failure matrix green (FCL-032): create/continue conversation, invalid ID, language validation, empty/missing/oversized message → 422, Ollama connection/timeout/model-not-found, auth 401, cross-user isolation, async persistence, bounded context (10 most recent messages).
- Latency measured on the actual host (FCL-033): 5/5 prompt classes OK, avg 11.84 s / max 16.31 s (includes model-load swaps; comparative only).
- Machine-checkable eval criteria pass (FCL-036): 4/4. Groundedness claims explicitly deferred to human review of `eval-en-agri-*` items.
- Registry status: `enabled` for capability `chat` (FCL-034). No other model enabled.


---

## Phase 4 execution report

Final report written to `docs/backend/PHASE_04_EXECUTION_REPORT.md` (2026-10-30): **PARTIAL — by design** (all in-scope workstreams complete and gated; Models 3–9 are future gated work). Exit gate: security-engineer APPROVE-WITH-CONDITIONS (zero Critical/High, all conditions closed, FCL-041); qa-reviewer independent verification (130 tests). 3 blockers + 5 owner decisions recorded in the report.

## Proposed follow-up (not approved scope — PROPOSED, awaiting owner)

- **FOLLOWUP-MYPY-AUTH:** mypy is script-declared non-blocking but reports 20 errors in auth code (17 `arg-type` UUID-vs-str in `app/services/auth.py`, 2 `no-untyped-def` + 1 `unused-ignore` in `app/api/v1/auth.py`) — flagged by qa-reviewer during the Phase 4 exit gate (2026-10-30). Safe fast-follow; not started to keep Phase 4 closure minimal.
