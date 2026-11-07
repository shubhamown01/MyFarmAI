# PersonaPlex Integration Boundary

## Status: Separate, Optional Voice Service

PersonaPlex is **not part of** the MyFarmAI OpenCode agent team. It remains an independent, optional voice service with a clear boundary.

## Model Artifacts

| Item | Value |
|------|-------|
| Model Directory | `/data/AI-Models/personaplex-7b-v1` |
| Model Source | Hugging Face (approval pending) |
| Current Status | **Weights not downloaded** |
| Size | ~7B parameters |

## Hardware Reality

| Constraint | Value | Implication |
|------------|-------|-------------|
| GPU | NVIDIA MX250 | 2 GB VRAM |
| System RAM | 7 GiB total, ~2 GiB available | Tight for 7B model |
| Inference | CPU-only likely | Not responsive for real-time |

**Conclusion**: Current hardware cannot support responsive real-time PersonaPlex 7B inference. Do not plan for it in Phase 0–4.

## Architectural Boundary

```
┌─────────────────────────────────────────────────────────────┐
│                      MyFarmAI System                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │   Web App    │  │ Android App  │  │  Backend API     │  │
│  │  (Next.js)   │  │  (Expo/RN)   │  │  (FastAPI)       │  │
│  └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘  │
│         │                 │                     │            │
│         └─────────────────┼─────────────────────┘            │
│                           ▼                                  │
│                  ┌──────────────────┐                        │
│                  │   Ollama Gateway │                        │
│                  │   (qwen3:4b)     │                        │
│                  └──────────────────┘                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    PersonaPlex Service (Separate)            │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │  STT (Whisper)   │  │  TTS (Piper)     │  ← Future      │
│  │  Port 8001       │  │  Port 8002       │                │
│  └──────────────────┘  └──────────────────┘                │
│         ▲                         ▲                         │
│         │                         │                         │
│  ┌──────┴──────┐           ┌──────┴──────┐                 │
│  │  Web Audio  │           │ Android     │                 │
│  │  Capture    │           │ Microphone  │                 │
│  └─────────────┘           └─────────────┘                 │
└─────────────────────────────────────────────────────────────┘
```

## Integration Rules

### DO NOT
- ❌ Couple PersonaPlex to OpenCode agent team
- ❌ Assume weights are downloaded
- ❌ Start PersonaPlex server in docker-compose for MVP
- ❌ Route chat through PersonaPlex for text-only path
- ❌ Share conversation memory between text and voice without auth

### DO
- ✅ Keep voice service in `ai/voice/` (current: faster-whisper STT only)
- ✅ Document voice as optional Phase 5+ feature
- ✅ Preserve text-only chat path as primary
- ✅ Design backend API to accept optional `audio` field in future
- ✅ Keep model storage at `/data/AI-Models/` (outside Git)

## Current Voice Service (`ai/voice/`)

- **STT only**: faster-whisper, Hindi/English
- **Port**: 8001 — **loopback-bounded: CMD binds `127.0.0.1:8001`** (contained 2026-11-03, owner-approved; Phase 0 finding S-03 partially remediated at the network layer). The service is not in `docker-compose.yml` and port 8001 is verified not listening — finding not live.
- **Auth**: None — **security finding S-03** (still open: do not expose or wire into the backend before the Phase 3 auth pattern)
- **Upload**: Unbounded — **security finding S-03**
- **Container**: Runs as root — **security finding S-12**

**Containment note (2026-11-03)**: If the voice service is ever added to
Compose, a loopback bind inside the container blocks cross-container reach
too — that is intentional for an unauthenticated service. Wiring it up
requires S-03 remediation (backend-side auth proxy, upload limits) first.

## Remediation Required Before Voice Integration

From Phase 0 Security Audit (`SECURITY_AND_PRIVACY_AUDIT.md`):

| Finding | Remediation |
|---------|-------------|
| S-03 Unauthenticated voice upload | Put behind authenticated backend or internal network; enforce max upload size, MIME types, duration limits, rate limits; run as non-root |
| S-08 No request-body size / AI concurrency limit | Add body limit middleware, bounded semaphore for inference |
| S-12 Container hardening | Non-root user, read-only root FS, cap_drop, memory/CPU limits, healthchecks |

## Future Integration Pattern (When Ready)

```
Frontend (Web/Android)
       │
       ▼
Backend API: POST /api/v1/chat
       │
       ├── text message → Ollama → text response
       │
       └── audio message (future)
              │
              ▼
       Backend validates: size, type, duration, rate limit
              │
              ▼
       Backend proxies to internal voice service (not public)
              │
              ▼
       Voice service: STT → text → Ollama → text → TTS → audio
              │
              ▼
       Backend returns: { text_response, audio_response? }
```

## OpenCode Agent Team Boundary

- **No agent** manages PersonaPlex
- **No task** includes PersonaPlex setup
- **Orchestrator** tracks voice as "deferred — hardware/approval pending"
- **AI/ML Engineer** may evaluate feasibility but does not operate it
- **Security Engineer** audits voice service separately

## Documentation References

- Phase 0 Security Audit: `docs/roadmaps/phase-00/SECURITY_AND_PRIVACY_AUDIT.md` (S-03, S-08, S-12)
- Backend Roadmap Phase 5: `docs/roadmaps/MyFarmAI_Backend_Roadmap.md` (Voice & Multilingual)
- Android Integration: `docs/integration/ANDROID_INTEGRATION.md` (Speech section)
- ADK Evaluation: `docs/ADK_EVALUATION.md` (Voice separate from agent orchestration)