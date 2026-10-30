# MyFarmAI — Model Inventory (P4-03)

**Recorded from live host:** 2026-10-29 (read-only inspection; no models pulled or changed)
**Ollama:** `/usr/local/bin/ollama`, service `ollama.service` active, API `http://localhost:11434`

## Storage (HDD-first verified)

- **Model storage:** `/data/SentinelAI/ollama/models` (44 GB, on `/data` HDD) — set via `OLLAMA_MODELS` in the systemd unit. **HDD-first policy: COMPLIANT** — future `ollama pull` writes go to `/data`, not the SSD. No SSD-permission gate needed for model pulls.
- `~/.ollama` contains only ~48 KB (stale config leftovers; no model blobs). Not touched.
- Disk headroom: `/data` 99 GB free; `/` 74 GB free.

## Hardware budget

| Resource | Value |
|---|---|
| VRAM | **2048 MiB** (models larger than ~2 GB cannot fully fit; they offload to CPU) |
| RAM | 7 GiB |
| `OLLAMA_MAX_LOADED_MODELS=1`, `OLLAMA_NUM_PARALLEL=1` (unit env) — serial inference, aligns with the app-level `ai_max_concurrent_requests=2` + queue bound |

## Installed models (from `/api/tags`, 2026-10-29)

| Model | Size | Params | Quant | Fits 2 GiB VRAM? | License (verify against model card before selection) |
|---|---|---|---|---|---|
| `qwen3:0.6b` | 0.52 GB | 0.75B | Q4_K_M | ✅ | Apache-2.0 (Qwen3 family) — **current chat default** |
| `nomic-embed-text:latest` | 0.27 GB | 137M | F16 | ✅ | Apache-2.0 (embeddings) |
| `qwen3-embedding:0.6b` | 0.64 GB | 596M | Q8_0 | ✅ | Apache-2.0 |
| `deepseek-coder:latest` | 0.78 GB | 1B | Q4_0 | ✅ | MIT-class (verify) — code-tuned, not agri-targeted |
| `qwen3-embedding:latest` | 4.68 GB | 7.6B | Q4_K_M | ❌ (CPU) | Apache-2.0 |
| `qwen3:4b` | 2.5 GB | 4.0B | Q4_K_M | ❌ (partial offload) | Apache-2.0 |
| `qwen3-vl:2b` | 1.89 GB | 2.1B | Q4_K_M | ⚠️ borderline | Apache-2.0 (vision-language) |
| `qwen2.5-coder:3b` | 1.93 GB | 3.1B | Q4_K_M | ⚠️ borderline | Apache-2.0 (code) |
| `qwen2.5-coder:1.5b-base` | 0.99 GB | 1.5B | Q4_K_M | ✅ | Apache-2.0 (code) |
| `phi:latest` | 1.6 GB | 3B | Q4_0 | ⚠️ borderline | MIT (Microsoft Phi) |
| `qwen3:latest` | 5.23 GB | 8.2B | Q4_K_M | ❌ (CPU) | Apache-2.0 |
| `deepseek-r1:latest` | 5.23 GB | 8.2B | Q4_K_M | ❌ (CPU) | MIT (DeepSeek-R1) |
| `mistral:latest` | 4.37 GB | 7.2B | Q4_K_M | ❌ (CPU) | Apache-2.0 |
| `gemma:latest` | 5.01 GB | 9B | Q4_0 | ❌ (CPU) | **Gemma Terms of Use** (not OSI; restricts some uses) |
| `qwen3-vl:latest` | 6.14 GB | 8.8B | Q4_K_M | ❌ (CPU) | Apache-2.0 (vision-language) |

## Notes for P4-04 (benchmarks)

- VRAM-fitting candidates for chat benchmarking: `qwen3:0.6b` (default), `qwen2.5-coder:1.5b-base`, `deepseek-coder:latest`, plus `phi:latest` / `qwen3-vl:2b` as borderline cases worth measuring (partial offload cost).
- Larger models may be benchmarked for reference but should be recorded as CPU-tier (higher latency); do not select them as chat default without owner-visible tradeoff evidence.
- Gemma: license is restrictive relative to others — flag in any selection decision.
- License column is from general model-family knowledge — **verify against each model's actual card** (`ollama show <model>`) before recording a selection decision in the benchmark doc.
