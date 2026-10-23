# PersonaPlex 7B v1 Integration Roadmap

**Status:** Planning — model access **BLOCKED** pending Hugging Face approval  
**Model:** NVIDIA PersonaPlex 7B v1 (`nvidia/personaplex-7b-v1`)  
**Shared location:** `/data/AI-Models/personaplex-7b-v1`  
**Hugging Face cache:** `/data/AI-Models/huggingface-cache`  
**Hugging Face CLI env:** `/data/AI-Models/hf-download-venv`  
**NVIDIA Repository:** https://github.com/NVIDIA/personaplex  
**Hugging Face Model Card:** https://huggingface.co/nvidia/personaplex-7b-v1  
**License:** NVIDIA Open Model License Agreement + CC-BY-4.0 (base model)

---

## 1. Current Status (Verified)

| Item | Status | Evidence |
|------|--------|----------|
| Model weights on disk | ✅ Present | `/data/AI-Models/personaplex-7b-v1/model.safetensors` (16.7 GB) |
| Model weights verified | ❌ NOT VERIFIED | No SHA-256 checksum recorded |
| Hugging Face approval | ❌ BLOCKED | Model download returned access-denied; gated repository |
| HF token configured | ✅ Configured | `/data/AI-Models/hf-download-venv` authenticated |
| Local inference tested | ❌ NOT VERIFIED | No runtime installed; no benchmark run |
| Hardware suitability | ❌ NOT SUITABLE | MX250 2 GB VRAM < 16.7 GB model weights; 7 GiB RAM insufficient |
| License reviewed | ⚠️ PARTIAL | NVIDIA Open Model License + CC-BY-4.0 base; commercial use claimed ready |

**Critical Blocker:** Model download from Hugging Face returns access-denied. Model is gated and requires explicit approval from NVIDIA. No local inference has been verified.

---

## 2. Architecture Summary

PersonaPlex is a **full-duplex speech-to-speech conversational model** (7B parameters, based on Moshi/Mimi architecture). It operates on continuous audio streams at 24 kHz, enabling real-time interruption, barge-in, and smooth turn-taking.

### Integration Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        MyFarmAI Application                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │   Web App    │  │  Android App │  │   Other Projects     │  │
│  │  (Next.js)   │  │  (Expo/RN)   │  │   (ATHENA, etc.)     │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘  │
│         │                 │                      │              │
│         └─────────────────┼──────────────────────┘              │
│                           ▼                                     │
│              ┌────────────────────────┐                         │
│              │   Shared AI Gateway    │                         │
│              │  (Provider-independent)│                         │
│              │  • Text → Ollama       │                         │
│              │  • Voice → PersonaPlex │                         │
│              │  • AuthZ, Rate limit   │                         │
│              │  • Session ownership   │                         │
│              └───────────┬────────────┘                         │
│                         │                                        │
│         ┌───────────────┼───────────────┐                       │
│         ▼               ▼               ▼                       │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               │
│  │   Ollama    │ │ PersonaPlex │ │  SearXNG/   │               │
│  │  (Text LLM) │ │ (Voice)     │ │  Research   │               │
│  └─────────────┘ └─────────────┘ └─────────────┘               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Phase Index

| Phase | Name | Status | Depends On |
|-------|------|--------|------------|
| **P0** | Feasibility & Access | ❌ BLOCKED | — |
| **P1** | Shared Model Storage & Lifecycle | ⏳ READY | P0 (access) |
| **P2** | Inference Runtime Prototype | ⏳ READY | P1 |
| **P3** | Hardware Deployment Strategy | ⏳ READY | P2 (benchmark) |
| **P4** | Reusable Voice Service | ⏳ READY | P2, P3 |
| **P5** | AI Gateway Integration | ⏳ READY | P4, Phase 3 (auth) |
| **P6** | MyFarmAI Web Integration | ⏳ READY | P5, Phase 7 (web) |
| **P7** | Android Integration | ⏳ READY | P5, Phase 8 (Android) |
| **P8** | Agricultural Conversational Behavior | ⏳ READY | P5, Phase 5 (ag) |
| **P9** | Security, Privacy & Compliance | ⏳ READY | P4, Phase 3 |
| **P10** | Performance & Reliability | ⏳ READY | P4, P10 |
| **P11** | Production Readiness & Reuse | ⏳ READY | P5–P10 |

---

## 4. Key Blockers & Decisions

| Blocker | Resolution Required |
|---------|---------------------|
| **HF model approval** | Request access from NVIDIA via Hugging Face; document approval status |
| **Hardware unsuitability** | Define minimum GPU (Ampere/Hopper class); current MX250 inadequate |
| **Model license** | Verify NVIDIA Open Model License + CC-BY-4.0 base compatibility with MyFarmAI distribution model |
| **Model weight verification** | Record SHA-256 of `model.safetensors`; verify against Hugging Face |
| **Runtime environment** | Define PyTorch/CUDA version pinned to NVIDIA tested configs (Ampere/Hopper) |
| **Voice service replacement** | PersonaPlex replaces current `faster-whisper` STT-only service; full-duplex vs STT-only |
| **Project reuse boundary** | Define shared `/data/AI-Models/` convention; isolate project-specific sessions/prompts |

---

## 5. Hardware Reality Check

| Resource | Available | PersonaPlex 7B Requirement | Gap |
|----------|-----------|---------------------------|-----|
| GPU VRAM | 2 GB (MX250) | ≥ 16 GB (A100/H100 class) | **Cannot run** |
| System RAM | 7 GiB total, ~2 GiB free | ≥ 32 GiB recommended | **Insufficient** |
| Disk (`/data`) | 176 GB free | ~20 GB (weights + cache) | ✅ Sufficient |
| Disk (`/`) | 5.3 GB free | Runtime, containers, cache | ⚠️ Tight |

**Conclusion:** Current development machine **cannot run PersonaPlex 7B** for real-time inference. A separate GPU workstation (Ampere/Hopper class, ≥ 24 GB VRAM, ≥ 32 GiB RAM) or approved remote GPU infrastructure is required for P2+.

---

## 6. Integration Points with Existing Roadmap

| Existing Phase | PersonaPlex Impact |
|----------------|-------------------|
| **Phase 3 (Auth)** | Voice sessions require authenticated sessions/tokens before exposure |
| **Phase 4 (Local AI)** | PersonaPlex adds voice modality to AI gateway; separate from Ollama text path |
| **Phase 5 (Ag Integrations)** | Voice passes farmer questions to ag reasoning; preserve citations/uncertainty |
| **Phase 6 (Research)** | Voice can trigger research; results spoken back with citations |
| **Phase 7 (Web)** | Opt-in voice UI; microphone permissions; fallback to text chat |
| **Phase 8 (Android)** | Audio capture/playback; emulator networking; audio focus management |
| **Phase 9 (Security)** | Voice-specific: consent, audio retention, spoofing, consent indicators |
| **Phase 10 (CI/Release)** | Voice service contract tests; model upgrade compatibility checks |

---

## 6. Next Steps

1. **Resolve P0:** Request NVIDIA model approval on Hugging Face; record decision
2. **Execute P1:** Define shared model storage lifecycle; verify checksums
3. **Defer P2+:** Until suitable hardware is available and approved
4. **Update main roadmaps:** Add PersonaPlex as optional gated capability in Phase 4+
5. **Document decisions:** Record all approvals/blockers in phase documents

---

**Next Action:** Resolve P0 (Hugging Face approval) before any runtime work begins.