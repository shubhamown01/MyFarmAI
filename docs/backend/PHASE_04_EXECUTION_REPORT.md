# Phase 4 Execution Report — AI Gateway and Governed AI Model Integration

**Date:** 2026-10-30 · **Executor:** Phase Orchestrator (OpenCode) · **Branch:** `phase-01-foundation` (all work uncommitted in working tree; pre-existing user work preserved)

## 1. Overall status: **PARTIAL — by design**

All Phase 4 workstreams in scope for this host are complete and gated (4A–4F + P4-01..P4-09 + exit gate). "PARTIAL" reflects the master prompt's own one-capability-at-a-time rule: Models 3–9 (vision, embeddings, research, ASR, TTS, translation, optional classifier) are future gated work, not failures. No unresolved Critical/High security findings exist.

## 2. Preflight gate table

All 9 gates **PASS** — full table with evidence in `docs/backend/PHASE_04_PREFLIGHT_REPORT.md` (2026-10-29). No blockers for 4A/4B/Model 1. Verified current: ADR-003/004/005 approved 2026-10-24; Phases 0–3 complete with current test evidence; canonical DB `backend/data/app.db`; Ollama 0.33.2, 16 models (44 GB) on `/data` HDD; VRAM 2048 MiB.

## 3. Architecture implemented

Request flow: `client → auth middleware → /api/v1/chat (auth required) → services/chat.py (async twin) → ai_gateway (AIGateway protocol) → OllamaGateway adapter → registry validation (explicit models) → Ollama (loopback:11434)`.

| File | Role |
|---|---|
| `backend/app/ai/gateway.py` | Provider-independent `AIGateway` protocol; `OllamaGateway` adapter; error types (`AIError`, `AITimeoutError`, `AIConnectionError`, `AIModelNotFoundError`, `AIBusyError`); registry hook |
| `backend/app/ai/registry.py` | Frozen model registry (tag/capability/status/license); `require_enabled`; `drift_against_live` |
| `backend/app/ai/prompts.py` | `PROMPT_TEMPLATE_VERSION="1"`; versioned system prompt; user content never interpolated |
| `backend/app/api/v1/chat.py` | Flat error envelope mapping for both error families |
| `backend/app/services/chat.py` | Async path on `ai_gateway` with concurrency gate (2) + queue bound (10) → 503 `AI_BUSY` |

## 4. Model integration matrix

| Capability | Tag | License (verify per model card before enabling) | Status | Tests | Latency (host, serial) |
|---|---|---|---|---|---|
| Chat (baseline) | `qwen3:0.6b` | Apache-2.0 (Qwen family) | **ENABLED / ACCEPTED** | Full matrix + eval 4/4 machine checks | avg 11.84 s, max 16.31 s (5/5) |
| Reasoning | `qwen3:4b` | Apache-2.0 | **DISABLED by evidence** (1/5; 4× timeout; >2 GB VRAM) | Benchmark only | avg 130.97 s |
| Chat (reference) | `deepseek-coder`, `phi`, `qwen2.5-coder` | MIT-class | installed, not enabled | Benchmark only | 5.66–21.16 s avg |
| Vision | `qwen3-vl:2b` | not yet card-verified | installed, gated (Model 3 gate not started) | — | — |
| Embeddings | `qwen3-embedding:0.6b`, `nomic-embed-text` | not yet card-verified | installed, gated (Model 4) | — | — |
| Research / ASR / TTS / translation | SearXNG (not a model) / candidates | AGPL-3.0 review pending | not started (Phases 6+) | — | — |

## 5. Security findings (security-engineer exit review, 2026-10-30: **APPROVE-WITH-CONDITIONS, zero Critical/High**)

| Sev | Finding | Resolution |
|---|---|---|
| Medium | `crop`/`location` interpolated into system role | **Closed**: accepted residual risk (bounded 100/200-char product fields) + covering test `test_prompt_slot_injection_bounded`; alternative (user-role restructure) documented as needing owner input |
| Medium | `backend/.pg_password` + `backend/file:test` untracked, not ignored | **Closed**: git-ignored (FCL-041); never committed; FCL-039 record corrected |
| Low | `MODEL_NOT_FOUND` detail leaked pull hints/model tags | **Closed**: generic client text; specifics server-side |
| Low | Persisted error assistant message embedded raw `str(e)` (base_url) | **Closed**: generic persisted text |
| Low | Broad `ValueError`→404 mapping | Accepted + documented (misclassification only) |
| Info | Concurrency gate attached at service layer | Accepted; move into `OllamaGateway` when Phase 6 adds a second consumer |
| Info | Per-request model selection impossible via chat path | Intentional (registry-governed; settings default is admin config) |

Privacy: no conversation/prompt content logged anywhere (P4-07 audit, FCL-037). Secrets scan clean. Dependency CVE scan: BLOCKED → Phase 8 (no audit tool in-repo; `uv.lock` pinned).

## 6. Test summary

| Command | Result |
|---|---|
| `bash scripts/check.sh` (repo root) | **130 passed, 0 failed** — ALL PASS (latest: 2026-10-30, independently re-run by qa-reviewer at 129 pre-condition-closure) |
| web `npm run typecheck` / `lint` / `test` | clean / clean / **19/19** |
| web `npm run build` | production build succeeded (2026-10-29) |
| android `npm run typecheck` / `lint` | clean / clean |
| Backend blocked items | none (mypy is script-declared non-blocking; 20 UUID/str `arg-type` errors in auth — qa-reviewer flagged as follow-up) |

## 7. Performance summary (host: ~7 GB RAM, 2 GB VRAM, models on `/data` HDD, serial inference)

- Gateway bounds: concurrency 2, queue 10 → immediate `503 AI_BUSY`; timeout 120 s; message ≤ 2000 chars. Full table: `docs/backend/RESOURCE_BUDGET.md`.
- `qwen3:0.6b`: 5/5 prompts, avg 11.84 s (includes model-load swaps — comparative only).
- `qwen3:4b`: does not fit VRAM — 4/5 ReadTimeout at 180 s. Disabled.

## 8. File change ledger

FCL-029 (4A gateway) · FCL-030 (queue bound + degraded-mode doc) · FCL-031 (inventory) · FCL-032 (preflight + Model 1 matrix tests) · FCL-033 (benchmarks) · FCL-034 (4B registry) · FCL-035 (versioned prompts) · FCL-036 (eval set/runner + Model 2 + Model 1 acceptance) · FCL-037 (P4-07 privacy closure) · FCL-038 (P4-09 docs pass) · FCL-039 (4D security pass + correction note) · FCL-040 (4F verification) · FCL-041 (exit-gate conditions closed) — all in `docs/engineering/FILE_CHANGE_LEDGER.md`.

## 9. Documentation updates

`docs/backend/`: PHASE_04_PREFLIGHT_REPORT.md, MODEL_INVENTORY.md, MODEL_BENCHMARKS.md, RESOURCE_BUDGET.md, ARCHITECTURE.md, API.md · `docs/api/openapi.json` (regenerated, `AI_BUSY` documented) · `docs/product/flows/AGRICULTURAL_QA_FLOW.md` · `docs/roadmaps/phases/PHASE_04_IMPLEMENTATION_PLAN.md` (P4-01..P4-09 ticked + Model 1 acceptance statement) · `docs/engineering/FILE_CHANGE_LEDGER.md` · `CHANGELOG.md` · new code: `backend/app/ai/{gateway,registry,prompts}.py`, `backend/scripts/{benchmark_models,run_evals}.py`, `backend/evals/eval_set_v1.json`, tests in `test_ai_gateway.py`/`test_chat.py`/`test_conversation_ownership.py`.

## 10. Remaining blockers: **3**

> **Addendum (2026-10-30, post-report model-gate work — FCL-042/043):** the model matrix above is extended as follows. Model 3 (vision): **BLOCKED on product scope** — no image-upload API exists. Model 4 (embeddings): candidates benchmarked — `qwen3-embedding:0.6b` 1024 dims (warm ~0.4 s), `nomic-embed-text:latest` 768 dims (warm ~0.07 s) — decision **deferred** pending a multilingual retrieval eval set + vector-store owner approval (`docs/backend/MODEL_BENCHMARKS.md`, `backend/embedding_benchmark_results.json`). Model 6 (ASR): local asset evaluated read-only — `ai/voice/` is faster-whisper "small" (no local weights, no auth); port 8001 **not listening** (Phase 0 containment finding not live); integration BLOCKED on architecture decision. Models 7–9: not started.

1. **Groundedness of `qwen3:0.6b` unproven** — 2 eval items (`eval-en-agri-1`, `eval-en-agri-2`) require human review; no quality claim is made until reviewed.
2. **Dependency vulnerability scan** — no audit tool in-repo; deferred to Phase 8 (BLOCKED, not a Phase 4 gap).
3. **Models 3–9 + routing modes** — future gated phases; per-request routing modes deferred pending product-UI approval. Gate states recorded in the addendum: Model 3 blocked on product scope; Model 4 evidence recorded, integration blocked on vector-store decision; Model 6 evaluated, blocked on architecture decision.

## 11. Owner decisions required: **5**

1. Non-loopback exposure sign-off (TLS + `environment=production` + explicit `ALLOWED_HOSTS`).
2. P2 rehearsal-data restore into fresh postgres (backup at `/data/MyFarmAI-backups/phase02-rehearsal/`) or leave empty.
3. Chat-auth login-UI coordination before image rebuild/redeploy (deployed image predates auth; `/api/v1/chat` 401s without credentials).
4. ADR-015 conversation retention policy (P4-07 documented as owner-pending).
5. Vision pipeline (Model 3) and per-request routing modes: approve product scope before implementation.

## 12. Next safe step

Commit-ready Phase 4 work sits in the working tree; the next authorized action is owner review/commit of Phase 4 (or explicit instruction to proceed to Phase 5 planning), plus the human review of the 2 groundedness eval items — the only gate blocking a quality claim for the chat baseline. Models 2 remains disabled by evidence; no re-evaluation recommended on this hardware.

**Honesty notes:** all counts/latencies above are traceable to files and command outputs recorded in the ledger; nothing is claimed beyond its evidence. The exit gate was verified by qa-reviewer (independent run) and security-engineer (independent review) subagents on 2026-10-30.
