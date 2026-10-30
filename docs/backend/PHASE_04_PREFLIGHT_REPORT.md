# Phase 4 Preflight Report

**Date:** 2026-10-29 · **Executor:** Phase Orchestrator (OpenCode) · **Mode:** read-only inspection, then incremental implementation under blanket approval

## Gate table

| # | Gate | Status | Evidence |
|---|------|--------|----------|
| 1 | Repo root `/data/MyFarmAI` | **PASS** | All session work executed there; git repo confirmed |
| 2 | Git state inspected | **PASS** | Branch `phase-01-foundation`; HEAD `2d8b8ad`; **uncommitted user work present and preserved** (`android/*`, `backend/Dockerfile`, `alembic/env.py`, `app/orchestrator/*`, `opencode.json`, `backend/file:test`, `.opencode/agents/*`) — never reset/clean |
| 3–4 | ADRs located | **PASS** | ADR-003/004/005 **APPROVED 2026-10-24** (`phase-00/ARCHITECTURE_DECISIONS.md`); ADR-008 (auth) approved via review record; ADR-014 loopback binding maintained |
| 5 | Phase 0/1 baseline | **PASS** | Quality gate `scripts/check.sh` ALL PASS — **119 tests** (current session evidence, not historical claim) |
| 6 | Phase 2/3 complete + approved | **PASS** | P2: postgres schema stamped `6cd2bffd9881` (fresh volume; rehearsal-data restore = pending owner decision). P3: **COMPLETE** — exit gate = security-engineer **APPROVE-WITH-CONDITIONS**, both pre-exposure conditions remediated (FCL-026), fast-follows closed (FCL-027); non-loopback exposure still gated on owner sign-off |
| 7 | Canonical DB verified | **PASS** | `backend/data/app.db` canonical (CANONICAL_DB_DECISION.md Option A, approved); SQLite test-only per ADR-003/004; postgres container up, fresh/empty, never touched destructively |
| 8 | Ollama + hardware | **PASS** | Ollama **0.33.2** active on 11434; **16 models (44 GB) on `/data/SentinelAI/ollama/models`** (HDD — HDD-first compliant); `qwen3:0.6b` (chat default) installed; VRAM **2048 MiB**; RAM ~6–7 GB (`OLLAMA_MAX_LOADED_MODELS=1`, `NUM_PARALLEL=1`); disk: `/data` 99 GB free, `/` 74 GB free |
| 9 | Licenses | **PASS (with caveat)** | Inventory recorded in `docs/backend/MODEL_INVENTORY.md`; Gemma flagged non-OSI; per-model-card verification required **before any selection/enabling decision** |

## Unknowns / open items

- Whether `qwen2.5-coder:1.5b-base` currently loaded (~950 MB VRAM at inspection) was left by the interrupted benchmark run — evicted automatically on next model load (`MAX_LOADED_MODELS=1`).
- Model-card license verification per model (required before enabling anything beyond the existing default).
- Owner decisions pending (not blocking Model 1 work): exposure sign-off; rehearsal-data restore; login-UI coordination before image rebuild.

## Blockers

**None for Phase 4A/4B/Model 1.** All prerequisite gates pass.

## Dependency map (incremental order)

1. **4A Gateway** — DONE (P4-01/P4-02, FCL-029/030): `AIGateway` protocol + Ollama adapter, timeouts, concurrency semaphore (2) + queue bound (10) → 503 `AI_BUSY`, degraded-mode contract.
2. **4B Registry/routing** — inventory exists (FCL-031); registry/routing modes to build per this master prompt.
3. **Model 1** `qwen3:0.6b` — benchmark (P4-04, in flight) + functional/failure/ownership regression matrix → acceptance gate.
4. Models 2–9 — strictly after Model 1's gate, one capability at a time.
