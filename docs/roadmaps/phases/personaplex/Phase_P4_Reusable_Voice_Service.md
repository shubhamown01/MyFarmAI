# Phase P4 — Reusable Voice Service

**Status:** ⏳ READY (awaits P3 target selection)  
**Prerequisite:** P3 complete (deployment target selected)  
**Blocks:** P5–P11

---

## 1. Objective

Build a production-ready, reusable PersonaPlex voice inference service that:
- Exposes a clean, versioned API for full-duplex speech-to-speech
- Runs on the selected deployment target (P3)
- Enforces authentication, authorization, rate limits, and resource bounds
- Provides health/readiness, graceful degradation, and observability
- Can be shared by MyFarmAI, ATHENA, and future projects without merging repos

---

## 2. Service Boundary

```
┌─────────────────────────────────────────────────────────────────┐
│                      PersonaPlex Voice Service                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                  FastAPI Application                         │  │
│  │  • /health/live       — Process alive                       │  │
│  │  • /health/ready      — Model loaded, GPU available         │  │
│  │  • /v1/sessions       — Session lifecycle (WS)              │  │
│  │  • /v1/sessions/{id}/stream — Full-duplex WebSocket        │  │
│  │  • /v1/sessions/{id}/interrupt — Barge-in signal           │  │
│  │  • /v1/voices         — List available voice prompts        │  │
│  │  • /v1/model/info     — Model version, device, capabilities │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              PersonaPlex Inference Engine                  │  │
│  │  • Model: personaplex-7b-v1 (16.7 GB safetensors)         │  │
│  │  • Codec: Mimi (24 kHz, streaming encoder/decoder)        │  │
│  │  • Runtime: PyTorch + CUDA (Ampere/Hopper)                │  │
│  │  • Concurrency: Bounded semaphore (configurable)          │  │
│  │  • Audio: 24 kHz, 16-bit PCM, WAV/WebAudio                │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. API Specification

### Authentication
- **Web:** HttpOnly Secure cookie session (via AI gateway)
- **Android:** Bearer token (short-lived) + refresh token
- **Service-to-service:** mTLS or shared secret (configurable)

### Endpoints

#### `GET /health/live`
```json
{ "status": "ok", "service": "personaplex-voice", "check_type": "liveness" }
```

#### `GET /health/ready`
```json
{
  "status": "ok",
  "service": "personaplex-voice",
  "check_type": "readiness",
  "dependencies": {
    "model": "loaded",
    "gpu": "available",
    "vram_free_gb": 12.5
  }
}
```

#### `GET /v1/model/info`
```json
{
  "model_id": "nvidia/personaplex-7b-v1",
  "version": "v1.0",
  "architecture": "Moshi/Mimi",
  "parameters": "7B",
  "device": "cuda:0",
  "dtype": "bfloat16",
  "vram_used_gb": 16.2,
  "vram_total_gb": 40,
  "supported_sample_rate": 24000,
  "capabilities": ["full_duplex", "interruption", "barge_in", "voice_prompting"]
}
```

#### `GET /v1/voices`
```json
{
  "voices": [
    { "id": "default_female", "name": "Default Female", "language": "en" },
    { "id": "default_male", "name": "Default Male", "language": "en" },
    { "id": "indian_female", "name": "Indian Female", "language": "en-IN" }
  ],
  "default": "default_female"
}
```

#### `POST /v1/sessions` — Create Session
**Request:**
```json
{
  "voice_id": "default_female",
  "text_prompt": "You are an agricultural assistant for Indian farmers...",
  "language": "en-IN",
  "sample_rate": 24000
}
```
**Response:**
```json
{
  "session_id": "uuid",
  "ws_url": "wss://voice.myfarmai.local/v1/sessions/{session_id}/stream",
  "expires_at": "2026-10-21T12:00:00Z",
  "voice_id": "default_female"
}
```

#### `WS /v1/sessions/{session_id}/stream`
**Protocol:** Full-duplex WebSocket (binary audio frames + control messages)

**Client → Server (binary):**
- Audio frames: 24 kHz, 16-bit PCM, 20 ms chunks (480 samples)
- Control: `{"type": "interrupt"}`, `{"type": "end"}`

**Server → Client (binary):**
- Audio frames: 24 kHz, 16-bit PCM, 20 ms chunks
- Events: `{"type": "text", "text": "..."}`, `{"type": "end", "reason": "completed"}`

#### `POST /v1/sessions/{session_id}/interrupt`
```json
{ "reason": "user_barge_in" }
```

#### `DELETE /v1/sessions/{session_id}`
- Terminates session, releases resources

---

## 3. Resource Management

| Resource | Limit | Config | Enforcement |
|----------|-------|--------|-------------|
| Concurrent sessions | 2 (A100 40GB) / 4 (80GB) | `MAX_SESSIONS` | Semaphore |
| Max session duration | 30 min | `MAX_SESSION_SECONDS` | Auto-terminate |
| Audio chunk size | 20 ms (480 samples) | Fixed | Validation |
| Max audio buffer | 5 min | `MAX_AUDIO_BUFFER_SECONDS` | Ring buffer |
| VRAM per session | ~8 GB | Monitored | Pre-admission check |
| Request timeout | 30 sec | `REQUEST_TIMEOUT` | Cancel on timeout |

---

## 3. Session Lifecycle

```
CREATE → INITIALIZING (load voice prompt) → READY
                                            │
                                            ▼
                                      STREAMING ←→ INTERRUPTED
                                            │
                                            ▼
                                      TERMINATING → TERMINATED
```

---

## 4. Error Responses

| Code | Scenario | Body |
|------|----------|------|
| 401 | Invalid/missing auth | `{ "detail": "Unauthorized", "error_code": "UNAUTHORIZED" }` |
| 403 | No permission for voice | `{ "detail": "Voice access denied", "error_code": "FORBIDDEN" }` |
| 404 | Session not found | `{ "detail": "Session not found", "error_code": "SESSION_NOT_FOUND" }` |
| 409 | Session limit reached | `{ "detail": "Max concurrent sessions", "error_code": "SESSION_LIMIT" }` |
| 413 | Audio too large | `{ "detail": "Audio buffer exceeded", "error_code": "AUDIO_TOO_LARGE" }` |
| 429 | Rate limited | `{ "detail": "Rate limited", "error_code": "RATE_LIMITED", "retry_after": 30 }` |
| 503 | Model not loaded | `{ "detail": "Voice service unavailable", "error_code": "MODEL_NOT_READY" }` |
| 504 | Inference timeout | `{ "detail": "Inference timed out", "error_code": "INFERENCE_TIMEOUT" }` |

---

## 4. Configuration

```yaml
# config.yaml
service:
  host: "0.0.0.0"
  port: 8002
  workers: 1
  log_level: "INFO"

model:
  path: "/data/AI-Models/personaplex-7b-v1"
  device: "cuda:0"
  dtype: "bfloat16"
  compile: true  # torch.compile

resources:
  max_sessions: 2
  max_session_seconds: 1800
  max_audio_buffer_seconds: 300
  vram_per_session_gb: 8
  request_timeout_seconds: 30

audio:
  sample_rate: 24000
  chunk_ms: 20
  format: "pcm16"
  codec: "mimi"

auth:
  enabled: true
  jwt_secret: "${VOICE_JWT_SECRET}"
  mttls_enabled: true
```

---

## 5. Health & Observability

| Metric | Type | Source |
|--------|------|--------|
| `personaplex_sessions_active` | Gauge | App |
| `personaplex_sessions_total` | Counter | App |
| `personaplex_vram_used_gb` | Gauge | App (nvidia-smi) |
| `personaplex_inference_latency_ms` | Histogram | App |
| `personaplex_audio_latency_ms` | Histogram | App |
| `personaplex_interruption_latency_ms` | Histogram | App |
| `personaplex_errors_total` | Counter | App |

**Logging:** Structured JSON with `request_id`, `session_id`, `latency_ms`, `vram_mb`

---

## 6. Container Specification

```dockerfile
# Dockerfile
FROM nvidia/cuda:12.4-devel-ubuntu22.04

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 python3.11-venv ffmpeg libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --frozen --no-dev

COPY . .
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8002
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s \
  CMD curl -f http://localhost:8002/health/ready || exit 1

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
```

---

## 6. Acceptance Criteria

- [ ] Service starts and `/health/ready` passes with model loaded
- [ ] Single session full-duplex conversation works (30 sec test)
- [ ] Interruption handling verified (user barge-in stops generation)
- [ ] Concurrent sessions respect `MAX_SESSIONS` limit (429 when exceeded)
- [ ] Authentication enforced (401 without, 200 with valid token)
- [ ] Rate limiting returns 429 with `Retry-After`
- [ ] VRAM usage stays within configured per-session budget
- [ ] Graceful shutdown on SIGTERM (drain sessions, save state)
- [ ] Metrics exported and scrapeable
- [ ] Container runs non-root, health check passes
- [ ] OpenAPI spec generated and versioned

---

## 6. Status Tracking

| Task | Status | Verified | Notes |
|------|--------|----------|-------|
| API spec defined | VERIFIED | ✅ | Documented above |
| Config schema | NOT STARTED | ❌ | |
| FastAPI service | NOT STARTED | ❌ | |
| WebSocket streaming | NOT STARTED | ❌ | |
| Session management | NOT STARTED | ❌ | |
| Resource limits | NOT STARTED | ❌ | |
| Auth integration | NOT STARTED | ❌ | Needs Phase 3 |
| Metrics/observability | NOT STARTED | ❌ | |
| Dockerfile | NOT STARTED | ❌ | |
| Tests written | NOT STARTED | ❌ | |

---

## 7. Dependencies

- **Requires:** P3 (deployment target), Phase 3 (auth)
- **Blocks:** P5 (gateway integration), P6/P7 (client integration)