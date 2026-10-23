# Phase P5 — AI Gateway Integration

**Status:** ⏳ READY (awaits P4 service + Phase 3 auth)  
**Prerequisite:** P4 service deployed; Phase 3 (Auth) complete  
**Blocks:** P6–P11

---

## 1. Objective

Extend the existing provider-independent AI gateway (Phase 4) to route voice requests to the PersonaPlex service while preserving text chat routing to Ollama. The gateway remains the single application-level interface for all AI capabilities.

---

## 2. Current AI Gateway Architecture (Phase 4)

```python
# Existing interface (from Phase 4)
class AIProvider(Protocol):
    async def chat(self, messages: list[ChatMessage], **kwargs) -> ChatResult
    async def embed(self, texts: list[str]) -> list[list[float]]
    async def health_check() -> HealthStatus
```

---

## 2. Extended Interface for Voice

### New Voice Capability
```python
from typing import AsyncIterator, Optional
from pydantic import BaseModel
from enum import Enum

class VoiceSessionConfig(BaseModel):
    voice_id: str
    text_prompt: str
    language: str = "en-IN"
    sample_rate: int = 24000

class VoiceEvent(BaseModel):
    type: str  # "audio", "text", "end", "error"
    data: Optional[bytes] = None  # audio chunk
    text: Optional[str] = None    # transcript or agent text
    session_id: str
    timestamp: float

class VoiceProvider(Protocol):
    async def create_session(
        self,
        config: VoiceSessionConfig,
        user_id: str
    ) -> str:  # returns session_id
        ...

    async def stream_session(
        self,
        session_id: str,
        audio_chunks: AsyncIterator[bytes]
    ) -> AsyncIterator[VoiceEvent]:
        ...

    async def interrupt_session(self, session_id: str, reason: str) -> None:
        ...

    async def close_session(self, session_id: str) -> None:
        ...

    async def list_voices(self) -> list[VoiceInfo]:
        ...

    async def health_check(self) -> HealthStatus:
        ...
```

---

## 3. Gateway Routing Logic

```python
class AIGateway:
    def __init__(
        self,
        text_provider: AIProvider,      # Ollama adapter
        voice_provider: VoiceProvider,   # PersonaPlex adapter
    ):
        self.text = text_provider
        self.voice = voice_provider

    # Text chat (existing)
    async def chat(self, request: ChatRequest, user_id: str) -> ChatResponse:
        return await self.text.chat(request.to_messages(), user_id=user_id)

    # Voice session (new)
    async def create_voice_session(
        self,
        config: VoiceSessionConfig,
        user_id: str
    ) -> VoiceSessionResponse:
        # Validate user has voice permission
        # Check concurrent session limit
        session_id = await self.voice.create_session(config, user_id)
        return VoiceSessionResponse(session_id=session_id, ws_url=...)

    async def stream_voice(
        self,
        session_id: str,
        audio_stream: AsyncIterator[bytes],
        user_id: str
    ) -> AsyncIterator[VoiceEvent]:
        # Verify session ownership
        # Stream to PersonaPlex, yield events
        async for event in self.voice.stream_session(session_id, audio_stream):
            yield event

    async def interrupt_voice(self, session_id: str, user_id: str, reason: str):
        # Verify ownership, forward interrupt
        await self.voice.interrupt_session(session_id, reason)

    async def close_voice_session(self, session_id: str, user_id: str):
        await self.voice.close_session(session_id)
```

---

## 4. API Endpoints (Backend)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/ai/chat` | POST | Text chat (existing) |
| `/api/v1/ai/voice/sessions` | POST | Create voice session |
| `/api/v1/ai/voice/sessions/{id}/stream` | WS | Full-duplex streaming |
| `/api/v1/ai/voice/sessions/{id}/interrupt` | POST | Barge-in signal |
| `/api/v1/ai/voice/sessions/{id}` | DELETE | Close session |
| `/api/v1/ai/voice/voices` | GET | List available voices |
| `/api/v1/ai/health` | GET | Gateway + providers health |

---

## 3. Authentication & Authorization

| Resource | Auth Required | Permission Check |
|----------|---------------|------------------|
| Text chat | Yes | User owns conversation |
| Voice session create | Yes | `voice:create` permission |
| Voice stream | Yes | Session ownership |
| Voice interrupt | Yes | Session ownership |
| Voice list voices | Yes | `voice:read` permission |

---

## 4. Degradation & Fallback

| Scenario | Behavior |
|----------|----------|
| PersonaPlex unavailable | Return 503 `VOICE_UNAVAILABLE`; text chat unaffected |
| GPU OOM | Return 503 `VOICE_OVERLOADED`; queue or reject new sessions |
| Network partition | Buffer audio locally (5 sec); reconnect or terminate gracefully |
| Model load failure | Health check fails; gateway returns 503 for voice only |

---

## 4. Configuration

```yaml
ai_gateway:
  text:
    provider: "ollama"
    ollama:
      base_url: "http://host.docker.internal:11434"
      model: "qwen3:4b"
      timeout_seconds: 120
      concurrency_limit: 2

  voice:
    enabled: true
    provider: "personaplex"
    personaplex:
      base_url: "http://personaplex-voice:8002"
      timeout_seconds: 30
      max_concurrent_sessions: 2
      default_voice: "default_female"
      default_language: "en-IN"
      default_text_prompt: "You are an agricultural assistant for Indian farmers..."
```

---

## 5. Acceptance Criteria

- [ ] `AIGateway` routes text to Ollama, voice to PersonaPlex
- [ ] Voice sessions require auth and ownership validation
- [ ] Text chat works when voice service is down
- [ ] Voice service down returns 503 (not 500) with `VOICE_UNAVAILABLE`
- [ ] Concurrent session limits enforced at gateway level
- [ ] OpenAPI spec includes voice endpoints
- [ ] Integration tests cover: create→stream→interrupt→close flow
- [ ] Load test: 2 concurrent voice + 10 text concurrent

---

## 4. Status Tracking

| Task | Status | Verified | Notes |
|------|--------|----------|-------|
| VoiceProvider interface | NOT STARTED | ❌ | |
| PersonaPlex adapter | NOT STARTED | ❌ | |
| Gateway routing | NOT STARTED | ❌ | |
| Auth integration | NOT STARTED | ❌ | Needs Phase 3 |
| Fallback logic | NOT STARTED | ❌ | |
| Config schema | NOT STARTED | ❌ | |
| OpenAPI spec | NOT STARTED | ❌ | |
| Integration tests | NOT STARTED | ❌ | |

---

## 5. Dependencies

- **Requires:** P4 (PersonaPlex service), Phase 3 (auth)
- **Blocks:** P6 (web), P7 (Android), P8 (ag behavior)