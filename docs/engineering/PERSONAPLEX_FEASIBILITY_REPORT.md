# MyFarmAI — NVIDIA PersonaPlex Feasibility Report

**Document ID:** MYFARMAI-PPX-FEAS-001  
**Version:** 1.0  
**Date:** 2026-10-22  
**Status:** Research & Design — No Implementation Authorized  
**Scope:** Evaluation of NVIDIA PersonaPlex for future MyFarmAI voice integration  
**Gate:** Requires explicit owner approval before any implementation

---

## 1. Executive Summary

| Aspect | Finding |
|--------|---------|
| **Technology** | NVIDIA PersonaPlex — 7B parameter real-time, full-duplex speech-to-speech model |
| **Architecture** | Based on Moshi (Kyutai), audio-to-audio streaming transformer, Mimi neural codec |
| **Code License** | MIT (permissive) |
| **Weights License** | NVIDIA Open Model License (commercial use permitted) |
| **Hugging Face Model** | `nvidia/personaplex-7b-v1` (8B params, BF16) |
| **Hardware Requirements** | **Minimum 16 GB VRAM** (A100 80 GB tested); RTX 4090 recommended; CPU offload possible via `accelerate` |
| **Latency** | ~170ms on high-end GPUs; higher on consumer hardware |
| **Languages** | English only (model card: "English") — **No Hindi support** |
| **Integration** | Python/Moshi server on port 8998; Web UI at localhost:8998 |
| **MyFarmAI Compatibility** | **Significant gaps** — Hindi not supported, VRAM exceeds 2 GiB, English-only |

**Recommendation:** **DEFER** — PersonaPlex does not meet MyFarmAI's core requirements (Hindi support, 2 GiB VRAM constraint, agricultural domain). Re-evaluate when Hindi support or quantized variants become available.

---

## 2. Source Evidence Summary

### Primary Sources
| Source | URL | Access Date | Key Information |
|--------|-----|-------------|-----------------|
| GitHub Repository | https://github.com/NVIDIA/personaplex | 2026-10-22 | MIT code license, architecture, deployment |
| Hugging Face Model Card | https://huggingface.co/nvidia/personaplex-7b-v1 | 2026-10-22 | NVIDIA Open Model License, 7B params, English only, commercial use |
| README.md | https://raw.githubusercontent.com/NVIDIA/personaplex/main/README.md | 2026-10-22 | Installation, voices, prompting, CPU offload |
| Dockerfile | https://raw.githubusercontent.com/NVIDIA/personaplex/main/Dockerfile | 2026-10-22 | CUDA 12.4.1, Ubuntu 22.04, Python 3.12, port 8998 |
| docker-compose.yaml | https://raw.githubusercontent.com/NVIDIA/personaplex/main/docker-compose.yaml | 2026-10-22 | GPU reservation, port 8998, volume for cache |
| NVIDIA Open Model License | https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-license/ | 2026-10-22 | Commercial use permitted |
| Model Card License Section | https://huggingface.co/nvidia/personaplex-7b-v1 | 2026-10-22 | "This model is ready for commercial use" |

### Key Technical Specifications (from verified sources)
| Parameter | Value | Source |
|-----------|-------|--------|
| Model Parameters | 7B (8B on HF card) | HF Model Card |
| Architecture | Moshi-based, Mimi codec | HF Model Card, README |
| Sample Rate | 24 kHz mono | HF Model Card |
| Latency | ~170ms on A100 80GB | HF Model Card, NVIDIA blog |
| VRAM Requirement | **16 GB minimum** | NVIDIA blog, HF Model Card |
| GPU Support | Ampere (A100), Hopper (H100) | HF Model Card |
| CPU Offload | Supported via `accelerate` | README |
| Language | English only | HF Model Card ("English") |
| Voices | 18 fixed (NAT/VAR, male/female) | README |
| Streaming | Full-duplex, audio-to-audio | All sources |

---

## 3. Compatibility Assessment vs MyFarmAI Requirements

### 3.1 Hard Constraints (Must Meet)

| Requirement | PersonaPlex | Status | Evidence |
|-------------|-------------|--------|----------|
| **Hindi language support** | ❌ English only | **BLOCKER** | HF Model Card: "Language: English" |
| **≤2 GiB VRAM** | ❌ 16 GB minimum | **BLOCKER** | NVIDIA blog: "16GB VRAM minimum" |
| **Local deployment** | ✅ Yes | PASS | Docker, CPU offload supported |
| **No paid API** | ✅ Yes | PASS | Local weights, NVIDIA Open Model License |
| **Open source code** | ✅ MIT | PASS | LICENSE-MIT |
| **Commercial use** | ✅ Permitted | PASS | NVIDIA Open Model License |

### 3.2 Functional Requirements (PRD/APP_FLOW)

| Requirement | PersonaPlex | Status | Notes |
|-------------|-------------|--------|-------|
| Agricultural Q&A voice | ⚠️ Possible | PARTIAL | English only; domain not tested |
| Real-time conversation | ✅ Full-duplex | PASS | Core feature |
| Persona/role control | ✅ Text + voice prompts | PASS | Core feature |
| Voice conditioning | ✅ 18 fixed voices | PASS | NAT/VAR male/female |
| Interruption handling | ✅ Benchmarked | PASS | FullDuplexBench scores |
| Integration with Ollama | ❌ Separate stack | BLOCKER | Different runtime (Moshi vs Ollama) |
| Integration with FastAPI | ⚠️ Via HTTP | PARTIAL | Moshi server on port 8998 |

### 3.3 Hardware Compatibility (MyFarmAI Host: 7 GiB RAM, 2 GiB VRAM)

| Resource | MyFarmAI Host | PersonaPlex Requirement | Gap |
|----------|---------------|-------------------------|-----|
| **GPU VRAM** | 2 GiB (MX250) | 16 GB minimum | **8x shortfall** |
| **System RAM** | 7 GiB | Model + OS + PyTorch | Likely insufficient |
| **GPU Architecture** | Pascal (MX250) | Ampere/Hopper preferred | Generation gap |
| **CPU Offload** | Possible | Supported via `accelerate` | **Only viable path** |

**CPU Offload Analysis:**
- README: "If your GPU has insufficient memory, use the `--cpu-offload` flag"
- Requires `accelerate` package
- HF Model Card: "Test Hardware: NVIDIA A100 80 GB" — no CPU-only benchmarks
- **Risk:** Unmeasured latency on 7 GiB RAM / MX250; likely >5s response times

---

## 4. Licensing Assessment

### 4.1 Code License
- **MIT License** (LICENSE-MIT in repository)
- Permissive: use, copy, modify, merge, publish, distribute, sublicense, sell
- Compatible with MyFarmAI's Apache-2.0 (recommended) or any OSI license

### 4.2 Weights License
- **NVIDIA Open Model License** (https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-license/)
- HF Model Card: "This model is ready for commercial use"
- Base model (Moshi): CC-BY-4.0 (kyutai/moshiko-pytorch-bf16)
- **Assessment:** Compatible with commercial MyFarmAI deployment

### 4.3 License Compatibility Matrix

| Component | License | MyFarmAI Apache-2.0 Compatible? |
|-----------|---------|--------------------------------|
| PersonaPlex code | MIT | ✅ Yes |
| PersonaPlex weights | NVIDIA Open Model | ✅ Yes (commercial permitted) |
| Moshi base (Mimi codec) | CC-BY-4.0 | ✅ Yes (attribution required) |
| Moshi weights (moshiko) | CC-BY-4.0 | ✅ Yes |

---

## 5. Proposed Architecture (Subject to Approval)

```
┌─────────────────────────────────────────────────────────────────────┐
│                        MyFarmAI Application                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   Web UI     │  │  Android App │  │  FastAPI     │              │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘              │
│         │                 │                 │                      │
│         └─────────────────┼─────────────────┘                      │
│                           ▼                                        │
│              ┌────────────────────────┐                            │
│              │   Voice Adapter        │                            │
│              │   (New Module)         │                            │
│              │  - Session management  │                            │
│              │  - Audio streaming     │                            │
│              │  - Persona config      │                            │
│              │  - Timeout/retry       │                            │
│              └───────────┬────────────┘                            │
│                           │                                        │
│              ┌────────────▼────────────┐                            │
│              │   PersonaPlex Runtime   │                            │
│              │   (Moshi Server)        │                            │
│              │   Port 8998 (internal)  │                            │
│              │   GPU/CPU offload       │                            │
│              └─────────────────────────┘                            │
└─────────────────────────────────────────────────────────────────────┘
```

### Integration Points
| Interface | Protocol | Direction | Notes |
|-----------|----------|-----------|-------|
| MyFarmAI → PersonaPlex | WebSocket/HTTP | Outbound | Audio streaming, persona config |
| PersonaPlex → MyFarmAI | WebSocket/HTTP | Inbound | Audio stream, text transcript |
| PersonaPlex ↔ Ollama | None | N/A | Separate runtimes |

### Required MyFarmAI Changes
1. **New `voice` module** in `backend/app/modules/voice/`
2. **Persona configuration** for agricultural assistant role
3. **Audio streaming** handling (WebRTC or WebSocket)
4. **Session isolation** per user/farm
4. **Resource limits** (CPU offload config, timeout)
5. **Error handling** for model unavailability

---

## 5. Resource & Storage Estimates

| Resource | Estimate | Notes |
|----------|----------|-------|
| **Model Weights** | ~16 GB (BF16, 8B params) | HF: "Model size: 8B params, Tensor type: BF16" |
| **GPU VRAM (inference)** | 16 GB minimum | NVIDIA blog |
| **System RAM (CPU offload)** | 20-30 GB | Model + PyTorch + OS |
| **Disk Storage** | 20 GB | Weights + PyTorch + dependencies |
| **Docker Image** | ~12 GB | CUDA 12.4.1 base + Moshi + weights |
| **Model Cache** | ~/.cache/huggingface | ~16 GB |

**MyFarmAI Host Impact:**
- `/` (SSD): 5.3 GB free — **insufficient for Docker image build**
- `/data` (HDD): 176 GB free — sufficient for weights/cache
- **Docker root relocation required** (HW-02) before any build

---

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **No Hindi support** | Certain | Blocks primary user base | Defer until Hindi variant exists |
| **VRAM insufficient** | Certain | Cannot run on MX250 | CPU offload untested latency |
| **CPU offload latency** | High | >5s response, unusable | Benchmark required before commit |
| **English-only model** | Certain | Excludes Hindi-speaking farmers | Defer |
| **Separate runtime stack** | Certain | Moshi + PyTorch vs Ollama + FastAPI | Operational complexity |
| **Model size (16 GB weights)** | High | Disk pressure on `/` | Requires Docker root move to `/data` |
| **No agricultural domain eval** | Unknown | May hallucinate on farming topics | Domain evaluation needed |
| **NVIDIA license dependency** | Low | Permissive but vendor-controlled | Monitor license changes |
| **Hugging Face token required** | Medium | Operational friction | Pre-download weights |

---

## 6. Test Plan (If Approved)

| Test | Method | Acceptance Criteria |
|------|--------|---------------------|
| **Model Load** | `python -m moshi.server --cpu-offload` | Loads without OOM on 7 GiB RAM |
| **Latency Benchmark** | `moshi.offline` with test audio | <3s end-to-end on CPU offload |
| **Hindi Detection** | Input Hindi audio | Graceful fallback (not hallucination) |
| **Persona Config** | Agricultural prompt test | Stays in role, relevant responses |
| **Interruption** | Simulated barge-in | Stops speaking, acknowledges |
| **Resource Monitor** | `nvidia-smi` + `ps` during inference | RAM < 6 GiB, no OOM |
| **Integration** | FastAPI → Moshi HTTP/WebSocket | Audio round-trip < 5s |
| **Failover** | Kill Moshi server | FastAPI returns 503 gracefully |

---

## 7. Comparison: PersonaPlex vs Current Voice (faster-whisper)

| Aspect | faster-whisper (current) | PersonaPlex (proposed) |
|--------|-------------------------|------------------------|
| **Function** | STT only (Hindi) | Full-duplex STT+TTS+Persona |
| **Language** | Hindi (forced) | English only |
| **VRAM** | ~1 GB (int8, small) | 16 GB minimum |
| **Latency** | ~2-5s (CPU) | ~170ms (GPU), unknown CPU |
| **Model Size** | 464 MB | 16 GB |
| **License** | MIT | MIT (code) + NVIDIA Open Model (weights) |
| **Integration** | Simple HTTP | WebSocket/HTTP streaming |
| **MyFarmAI Fit** | **Matches requirements** | **Multiple blockers** |

---

## 8. Recommendation

### Decision: **DEFER**

**Rationale:**
1. **Critical Blocker: No Hindi Support** — MyFarmAI's primary user base requires Hindi; PersonaPlex is English-only with no announced Hindi roadmap.
2. **Critical Blocker: VRAM Requirement** — 16 GB minimum vs 2 GiB available; CPU offload latency unmeasured but likely unusable for real-time conversation.
3. **Architecture Mismatch** — PersonaPlex requires separate Moshi/PyTorch runtime, adding operational complexity vs current Ollama-only stack.
3. **No Agricultural Evaluation** — Model not tested on farming domain; hallucination risk high.
4. **Operational Overhead** — 16 GB weights, separate Docker service, Hugging Face token management.

### Alternative Paths
| Option | Description | Timeline |
|--------|-------------|----------|
| **Defer** | Wait for Hindi support, quantized variants (4-bit/8-bit), or CPU-optimized builds | 6-18 months |
| **Hybrid** | Keep faster-whisper for STT; add lightweight TTS (Piper, Coqui) for Hindi | 1-2 months |
| **Cloud API** | Use NVIDIA NIM or third-party for voice (requires paid approval) | Immediate (if budget approved) |

---

## 9. Decision Required

| Decision Point | Options | Recommendation |
|----------------|---------|----------------|
| **Proceed with PersonaPlex evaluation?** | Yes / No / Defer | **Defer** |
| **If Yes:** Allocate hardware budget for 16+ GB VRAM GPU? | Yes / No | Requires budget approval |
| **If Yes:** Accept English-only for Phase 2? | Yes / No | Conflicts with PRD |
| **Alternative:** Investigate Hindi TTS + faster-whisper STT pipeline? | Yes / No | **Recommended path** |

---

## 10. Documentation Updates Required (If Approved)

| Document | Update Required |
|----------|-----------------|
| `docs/product/TRD.md` | Add PersonaPlex to AI Runtime section |
| `docs/product/APP_FLOW.md` | Add voice conversation flow |
| `docs/product/flows/AGRICULTURAL_QA_FLOW.md` | Add voice path |
| `docs/roadmaps/phase-00/ARCHITECTURE_DECISIONS.md` | Add ADR-XXX for PersonaPlex |
| `docs/engineering/FILE_CHANGE_LEDGER.md` | Record new files |
| `docs/engineering/FILE_DOCS/backend/SERVICES.md` | Document voice adapter |
| `docker-compose.yml` | Add personaplex service (internal network) |
| `backend/pyproject.toml` | Add moshi, accelerate dependencies |

---

## 11. File Change Ledger Entry

| Field | Value |
|-------|-------|
| **Change ID** | FCL-008 |
| **Date/Time** | 2026-10-22T14:30:00+05:30 |
| **Task Ref** | PersonaPlex Feasibility Research |
| **File Path** | `docs/engineering/PERSONAPLEX_FEASIBILITY_REPORT.md` |
| **Operation** | CREATE |
| **Reason** | Document PersonaPlex evaluation for future voice integration decision |
| **Authority** | NVIDIA PersonaPlex Future Voice Integration mandate |
| **Previous State** | No PersonaPlex evaluation document |
| **Changes Made** | Created comprehensive feasibility report with licensing, hardware, compatibility, risk assessment, and recommendation |
| **Affected Interfaces** | Future voice architecture decisions |
| **Tests/Checks** | Web search verification, source document retrieval |
| **Risks/Rollback** | None (documentation only); rollback = delete file |
| **Approval** | NOT REQUIRED (research/documentation only) |
| **Status** | COMPLETE |

---

## 12. Next Steps

1. **Owner reviews** this feasibility report
2. **Owner decides**: Adopt / Defer / Reject / Alternative
3. **If Defer/Reject**: Close evaluation; preserve report for future reference
4. **If Adopt**: Create ADR, allocate hardware budget, begin prototype (requires Phase 1 gates + new approvals)
5. **If Alternative**: Initiate Hindi TTS + STT pipeline investigation

---

**Final Note:** This report is **research and design only**. No implementation, model downloads, Docker changes, or service modifications have been performed. All Phase 1 governance gates (G1-G6) remain authoritative and unchanged. PersonaPlex integration requires separate explicit approval beyond current Phase 1 scope.