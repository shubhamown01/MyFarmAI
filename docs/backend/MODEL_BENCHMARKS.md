# MyFarmAI — Model Benchmarks (P4-04)

**Recorded:** 2026-10-29 · **Harness:** `backend/scripts/benchmark_models.py` (results: `backend/benchmark_results.json`)
**Hardware/conditions:** host Ollama 0.33.2, `/data` HDD model storage, VRAM 2048 MiB, RAM ~6–7 GB, `OLLAMA_MAX_LOADED_MODELS=1` (serial), cold-ish start per model (first prompt includes load/eviction swaps). Absolute numbers include model-load time on first prompt; treat as comparative, not production latency.

## Prompts (5, fixed in harness)

1. `qa-simple-en` — English agricultural QA (crop rotation)
2. `qa-simple-hi` — Hindi agricultural QA (yellowing tomato leaves)
3. `qa-refusal` — unsafe request (exceeding pesticide label limits) — should decline/deflect
4. `qa-low-confidence` — no-symptom diagnosis request — should express uncertainty
5. `qa-structured` — JSON-array output request

## Results (2026-10-29)

| Model | Size | OK/5 | Failed | Avg (s) | Max (s) | Notes |
|---|---|---|---|---|---|---|
| **`qwen3:0.6b`** (current chat default) | 0.52 GB | **5/5** | 0 | 11.84 | 16.31 | All prompts completed incl. Hindi, refusal, structured |
| `qwen2.5-coder:1.5b-base` | 0.99 GB | 4/5 | **1** (ReadTimeout at 180 s on refusal prompt) | 15.62 | 40.91 | Code-tuned; not suitable as agri chat default |
| `deepseek-coder:latest` | 0.78 GB | 5/5 | 0 | **5.66** | 15.64 | Fastest; code-tuned — quality/relevance for agri QA unproven (eval set P4-08 required before any selection claim) |
| `phi:latest` | 1.6 GB | 5/5 | 0 | 21.16 | 56.85 | Slowest; borderline VRAM fit |

## Interpretation (evidence-bounded)

- **`qwen3:0.6b` remains the chat default** — it completed all 5 prompt classes without failure and is the smallest fitting model. **Not claimed**: output quality, groundedness, refusal adequacy, or Hindi accuracy — these require the versioned evaluation set (P4-08) with human-reviewed criteria; latency/failure metrics alone do not establish quality.
- `deepseek-coder` latency advantage is real but model purpose (code) mismatches agricultural QA; benchmarking it was for reference only.
- The 180 s timeout failure on `qwen2.5-coder` demonstrates the harness catches hangs — the gateway's own timeouts (120 s default) would surface this as `504 OLLAMA_TIMEOUT` in production.
- No model was enabled, disabled, or selected differently as a result of this run; the existing default is unchanged.

## Re-run instructions

```bash
cd backend && uv run python scripts/benchmark_models.py            # default 4 candidates
uv run python scripts/benchmark_models.py qwen3:4b                 # any installed tag
```

Results land in `backend/benchmark_results.json`; update this file when re-running for a selection decision.


---

## Model 2 benchmark — `qwen3:4b` (2026-10-29, master prompt §6 Model 2 gate)

| Model | OK/5 | Avg (s) | Max (s) | Result |
|---|---|---|---|---|
| `qwen3:4b` | **1/5** | 130.97 | 130.97 | **4 failures** (ReadTimeout at 180 s on hi/refusal/low-confidence/structured); partial CPU offload expected (2.5 GB weights vs 2 GB VRAM) |
| `qwen3:0.6b` (same run) | 5/5 | 13.61 | 21.95 | Control — consistent with the first run |

**Decision (evidence-bounded): `qwen3:4b` stays DISABLED.** It does not fit the 2 GB VRAM budget: 4 of 5 prompts timed out at 180 s under serial inference. Latency alone is ~10× the default. No quality comparison is possible at this latency — the eval set is moot for this model on this hardware. Re-evaluation would require different hardware (owner decision) and is not recommended for this host.

## Eval set results — `qwen3:0.6b` (P4-08, 2026-10-29)

- Runner: `backend/scripts/run_evals.py`; set: `backend/evals/eval_set_v1.json` (version "1"); raw: `backend/eval_results.json`.
- **Machine-checkable criteria: 4/4 PASS** (Hindi→Devanagari response, pesticide-overdose refusal, no-symptom uncertainty, valid JSON array).
- **2 items REQUIRE MANUAL REVIEW** (`eval-en-agri-1`, `eval-en-agri-2` — groundedness/factuality): not scored automatically; an owner-visible human review is required before any groundedness/quality claim. The runner refuses to make that claim by design.
- Checker self-checks pass (9 assertions on marker/JSON logic).

---

## Model 4 — embedding candidate benchmark (2026-10-30)

Harness: `backend/scripts/benchmark_embeddings.py` (raw: `backend/embedding_benchmark_results.json`). 4 texts (EN short/long/technical + HI), `/api/embed`, cold first request includes model load.

| Model | Dims | Consistent | Warm avg | Note |
|---|---|---|---|---|
| `qwen3-embedding:0.6b` | 1024 | yes | ~0.4 s | Qwen3 family — multilingual (Hindi expected, unverified for retrieval quality) |
| `nomic-embed-text:latest` | 768 | yes | ~0.07 s | ~6× faster warm; primarily English-focused — Hindi retrieval quality unproven |

**Decision: deferred, not made.** Dimensions/latency recorded only. Choosing a candidate requires (a) a documented multilingual agricultural retrieval eval set (per master prompt Model 4 requirements) and (b) a vector-store decision — the master prompt forbids introducing a new vector database without documented need + owner approval. Model 3 (vision) remains **blocked on product scope**: no image-upload API exists; building one is an owner-approval product change. No integration work started for either model.

---

## Model 6 — ASR asset evaluation (2026-10-30, read-only)

- **Local asset:** `ai/voice/` (16 KB code only — `main.py`, `Dockerfile`, `requirements.txt`): faster-whisper `small`, CPU, int8, `/transcribe` upload endpoint. No model weights in the repo; `faster-whisper` would fetch "small" weights on first run (**HDD-first + no-auto-pull rules apply** before any integration).
- **License:** faster-whisper is MIT; Whisper "small" weights are MIT (OpenAI) — **verify the actual model card before enabling** (project rule).
- **Containment status:** port 8001 **not listening** and service absent from `docker-compose.yml` — the Phase 0 finding ("voice service unauthenticated on 0.0.0.0:8001") is not currently live. The service itself has **no authentication** — it must not be exposed or wired into the backend without the Phase 3 auth pattern.
- **Other candidates:** no SROTA or AI4Bharat IndicConformer assets found locally (searched `/data/SentinelAI`, repo).
- **Decision: not integrated.** Integration would be an architecture decision (separate service vs backend-native) + auth requirements — owner input required. WER measurements require a documented test set (master prompt §6 Model 6); none exists locally.
