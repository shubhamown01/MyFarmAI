# MyFarmAI — Resource Budget & AI Concurrency Guide (P4-09)

**Recorded:** 2026-10-29 · **Host:** dev machine, ~7 GB RAM, 2 GB GPU VRAM, models on `/data` HDD
**Scope:** how the AI gateway and Ollama are bounded so the host stays usable; what to change when hardware changes.

## Hard limits (current)

| Resource | Limit | Where set | Effect when exceeded |
|---|---|---|---|
| Simultaneous in-flight AI chats | **2** | `OllamaGateway._gate` semaphore (`app/ai/gateway.py`) | 3rd+ request waits in queue |
| Queued waiters | **10** (`ai_max_queue_depth`) | Settings | Waiter beyond depth → immediate `503 AI_BUSY` |
| Per-request timeout | **120 s** | Settings (`ollama_timeout`) | `504 OLLAMA_TIMEOUT` |
| Request message length | **2000 chars** | `ChatRequest` schema | `422` |
| Ollama loaded models | **1** | systemd `OLLAMA_MAX_LOADED_MODELS=1` | Serial inference; model swaps evict the previous model |
| Ollama parallelism | **1** | `OLLAMA_NUM_PARALLEL=1` | One generate stream at a time |
| GPU VRAM | 2048 MiB | hardware | Models > ~2 GB partially offload to CPU (much slower) |
| RAM | ~7 GB | hardware | Ollama + postgres + backend must coexist |

## Why serial inference matters operationally

With `MAX_LOADED_MODELS=1`, **only one model is resident at a time**. Consequences:

1. Every model swap costs load time (first request after a swap absorbs it).
2. **Never run two Ollama workloads concurrently** (e.g., evals while a benchmark runs) — the second blocks until timeout. Recorded as a lesson in FCL-036.
3. Benchmark latencies (`MODEL_BENCHMARKS.md`) include swap loads — treat them as comparative.

## Model sizing rule of thumb

- A model fits VRAM only if weights + KV cache < 2 GB. `qwen3:0.6b` (~0.5 GB) fits comfortably.
- `qwen3:4b` (2.5 GB) **does not fit** — benchmark: 4/5 prompts timed out at 180 s. It stays **disabled** (`app/ai/registry.py`); enablement would require different hardware (owner decision).
- Adding a model: register in `app/ai/registry.py` (status `installed`), benchmark with `backend/scripts/benchmark_models.py <tag>`, run `run_evals.py`, verify the model-card license — only then flip to `enabled`.

## Degradation contract

- Ollama down / model missing / timeout → mapped API errors (`API.md` error table); no silent fallback, no automatic model switching (registry-governed per-request selection only).
- Queue overload → immediate `503 AI_BUSY` (no unbounded waiting).
- Client disconnects cancel the in-flight request (async path).

## Verification commands

```bash
# Gateway bounds + error mapping tests
cd backend && uv run pytest tests/test_ai_gateway.py tests/test_chat.py -q
# Benchmark (serial — do not run other Ollama work concurrently)
cd backend && uv run python scripts/benchmark_models.py [tags...]
# Eval set
cd backend && uv run python scripts/run_evals.py [model]
```
