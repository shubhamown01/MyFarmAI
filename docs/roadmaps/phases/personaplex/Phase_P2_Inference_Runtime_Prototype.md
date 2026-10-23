# Phase P2 — Inference Runtime Prototype

**Status:** ⏳ READY (awaits P1 complete)  
**Prerequisite:** P1 complete (verified weights, checksums, provenance)  
**Blocks:** P3–P11  
**Hardware Requirement:** NVIDIA Ampere/Hopper GPU (≥ 24 GB VRAM), ≥ 32 GiB RAM, Linux

---

## 1. Objective

Reproduce the official NVIDIA PersonaPlex inference runtime, verify it starts correctly, and measure baseline performance on target hardware. This is a **prototype** — not production service.

---

## 2. Prerequisites (Entry Gate)

- [ ] P0 complete: HF approval, model downloaded, checksums verified
- [ ] P1 complete: Weights verified, checksums match, provenance recorded
- [ ] Hardware available: NVIDIA Ampere/Hopper GPU (≥ 24 GB VRAM), ≥ 32 GiB RAM
- [ ] NVIDIA PersonaPlex repository cloned at known revision
- [ ] PyTorch + CUDA versions pinned to NVIDIA-tested combo

---

## 3. Upstream Reference

- **Repository:** https://github.com/NVIDIA/personaplex
- **Model:** `nvidia/personaplex-7b-v1` (7B params, Moshi/Mimi architecture)
- **Runtime:** PyTorch + CUDA (tested on A100 80 GB, H100)
- **Audio:** 24 kHz sample rate, Mimi codec (Mimi Speech Encoder/Decoder)
- **Pipeline:** Streaming speech understanding + generation (dual-stream)

---

## 3. Prototype Goals

| Goal | Success Criteria |
|------|------------------|
| Environment setup | Conda/venv with pinned PyTorch, CUDA, torchaudio, moshi dependencies |
| Model loading | Load `model.safetensors` + tokenizer + voices without OOM |
| Health check | `/health` endpoint returns model status, device, memory usage |
| Single inference | Process 5-second audio clip → generate response audio + text |
| Streaming test | Simulate 30-second conversation with interruptions |
| Resource measurement | Record RAM, VRAM, startup time, first-audio latency |
| Failure modes | Test OOM, GPU disconnect, model corruption, invalid audio |

---

## 4. Environment Specification

### P2-01: Pinned Dependencies
```yaml
# environment.yaml or requirements.txt
python: "3.10"  # or 3.11 per upstream
pytorch: "2.3.0+cu121"  # or cu124 per upstream tested
cuda: "12.1"  # or 12.4
torchaudio: "2.3.0+cu121"
transformers: "4.40.0"
accelerate: "0.30.0"
safetensors: "0.4.3"
moshi: "git+https://github.com/kyutai-labs/moshi@<pinned_rev>"
# PersonaPlex may require specific moshi fork
```

### P2-02: CUDA/PyTorch Compatibility Matrix
| PyTorch | CUDA | Tested by NVIDIA |
|---------|------|------------------|
| 2.3.0   | 12.1 | ✅ A100/H100 |
| 2.4.0   | 12.4 | ⚠️ Verify |

**Decision:** Pin to NVIDIA-tested combination; document in `ENVIRONMENT.md`.

---

## 4. Prototype Implementation Tasks

### P2-03: Minimal Inference Script
```python
# prototype_inference.py
import torch
from pathlib import Path
from moshi.models import loaders
from moshi.models.moshi import Moshi

def load_personaplex(model_dir: Path, device: str = "cuda"):
    """Load PersonaPlex 7B with Mimi codec."""
    # Load Mimi codec (speech encoder/decoder)
    mimi = loaders.get_mimi(device=device)
    
    # Load PersonaPlex (Moshi-based)
    model = Moshi.from_pretrained(
        model_dir,
        device=device,
        dtype=torch.bfloat16,  # or float16 per upstream
    )
    return model, mimi

def run_inference(model, mimi, audio_path: Path, voice_prompt: Path, text_prompt: str):
    """Run full-duplex inference on audio file."""
    # Load and encode audio
    # Run streaming inference
    # Return generated audio + text
    pass
```

### P2-04: FastAPI Prototype Service
```python
# prototype_service.py
from fastapi import FastAPI, UploadFile, File, WebSocket
from pydantic import BaseModel

app = FastAPI(title="PersonaPlex Prototype")

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "model_loaded": MODEL is not None,
        "device": str(DEVICE),
        "vram_used_gb": torch.cuda.memory_allocated() / 1e9,
        "ram_used_gb": psutil.Process().memory_info().rss / 1e9,
    }

@app.post("/inference")
async def inference(audio: UploadFile = File(...), voice_prompt: UploadFile = File(...), text_prompt: str = ""):
    # Run streaming inference
    # Return audio response + text
    pass

@app.websocket("/stream")
async def stream(ws: WebSocket):
    # Full-duplex WebSocket streaming
    pass
```

---

## 5. Benchmark Protocol

### P2-05: Baseline Metrics to Record
| Metric | Method | Target (A100 80GB reference) |
|--------|--------|------------------------------|
| Model load time | `time` model init | < 30 sec |
| VRAM peak (idle) | `nvidia-smi` after load | ~16 GB |
| VRAM peak (active) | `nvidia-smi` during inference | < 24 GB |
| System RAM peak | `psutil` during inference | < 32 GB |
| First-audio latency | Timestamp: request → first audio chunk | < 500 ms |
| End-to-end latency | User stop → agent start | < 800 ms |
| Interruption latency | User interrupt → agent stop | < 300 ms |
| Startup time | Container/service start → `/health` ok | < 60 sec |
| Concurrent sessions | Max before OOM | ≥ 2 (A100 80GB) |

### P2-06: Test Audio Corpus
| Test Case | Duration | Description |
|-----------|----------|-------------|
| Short query | 3 sec | "What's the weather?" |
| Medium query | 10 sec | Farmer describes crop symptoms |
| Long monologue | 30 sec | Detailed crop cycle question |
| Interruption | 15 sec | User barges in mid-response |
| Backchannel | 20 sec | "uh-huh", "right" during agent speech |
| Silence | 5 sec | Leading/trailing silence handling |

---

## 6. Failure Mode Testing

| Failure | Test Method | Expected Behavior |
|---------|-------------|-------------------|
| OOM (VRAM) | Load 2nd model instance | Graceful error, no crash |
| GPU disconnect | `nvidia-smi` reset during inference | Clean error, cleanup |
| Corrupted weights | Flip bit in `model.safetensors` | Load fails with clear error |
| Invalid audio | Upload text file as audio | 400 error, clear message |
| Empty audio | 0-byte WAV | 400 error |
| Long audio (>5 min) | 10-minute WAV | Timeout or chunked processing |
| Concurrent overload | 10 parallel requests | Queue/429, no OOM |

---

## 7. Deliverables

| Artifact | Description |
|----------|-------------|
| `ENVIRONMENT.md` | Pinned dependencies, CUDA/PyTorch versions, install steps |
| `prototype_inference.py` | Minimal working inference script |
| `prototype_service.py` | FastAPI service with `/health`, `/inference`, `/stream` |
| `BENCHMARK_RESULTS.md` | All metrics from §5 with hardware specs |
| `FAILURE_MODE_REPORT.md` | Results from §6 with screenshots/logs |
| `HARDWARE_VERDICT.md` | Explicit: "Runs on X hardware" or "Requires Y hardware" |

---

## 7. Exit Gate

**Phase P2 complete only when:**

- [ ] Environment reproduces NVIDIA-tested PyTorch/CUDA combo
- [ ] Model loads without OOM on target hardware
- [ ] `/health` returns model status, device, memory
- [ ] Single inference produces valid audio + text output
- [ ] Streaming test handles interruption/backchannel
- [ ] All benchmark metrics recorded with hardware specs
- [ ] Failure modes tested and documented
- [ ] **Explicit hardware verdict:** "Runs on X" or "Requires Y"

**No production service work (P4+) may begin until P2 exit gate is VERIFIED.**

---

## 8. Status Tracking

| Task | Status | Verified | Notes |
|------|--------|----------|-------|
| P2-01: Pinned env | NOT STARTED | ❌ | Requires P1 |
| P2-02: CUDA matrix | NOT STARTED | ❌ | |
| P2-03: Inference script | NOT STARTED | ❌ | |
| P2-04: FastAPI service | NOT STARTED | ❌ | |
| P2-05: Benchmarks | NOT STARTED | ❌ | |
| P2-06: Test corpus | NOT STARTED | ❌ | |
| Failure mode tests | NOT STARTED | ❌ | |
| Deliverables written | NOT STARTED | ❌ | |

---

## 8. Hardware Reality Check (Reiteration)

| Hardware | Minimum for Prototype | Recommended for Production |
|----------|----------------------|---------------------------|
| GPU | A100 40 GB / H100 | A100 80 GB / H100 80 GB |
| VRAM | 24 GB | 40–80 GB |
| System RAM | 32 GiB | 64+ GiB |
| Disk | 50 GB free | 100+ GB free |
| CUDA | 12.1 / 12.4 | Match PyTorch build |

**Current MX250 (2 GB VRAM) cannot run this prototype.** A separate GPU workstation or approved remote GPU is required before P2 can begin.

---

## 9. References

- NVIDIA PersonaPlex Repo: https://github.com/NVIDIA/personaplex
- Moshi Repo: https://github.com/kyutai-labs/moshi
- Mimi Codec: https://github.com/kyutai-labs/mimi
- FullDuplexBench: https://arxiv.org/abs/2503.04721
- PersonaPlex Paper: https://arxiv.org/abs/2602.06053