# ADR-016: Voice-First Experience via Client-Platform Speech APIs (PROPOSED — awaiting owner acceptance)

**Date:** 2026-10-31 · **Status:** PROPOSED (resolves the P5F "Model 6 gate" architecture decision) · **Supersedes:** the legacy unauthenticated `ai/voice/` FastAPI service (never committed to this tree; Phase 0 containment finding closed as moot)

## Context

P5F calls for a voice-first experience: speech-to-text (Hindi/English/Hinglish) and text-to-speech. The original approach — a separate FastAPI voice service — was a Phase 0 finding: it bound `0.0.0.0:8001` with **no authentication**. That service does not exist in the current tree.

Constraints that shape this decision:

- **Hardware:** 7 GiB RAM, 2 GiB VRAM, ~5 GB free on `/` (SSD). Server-side STT/TTS models (whisper, piper) mean hundreds of MB–GB of model downloads; the HDD-first storage policy requires explicit owner permission for SSD writes, and `/data`-hosted models served by a backend container add mounting complexity.
- **Ollama hosts no STT/TTS models** — the existing AI infrastructure cannot serve voice.
- **Client platforms already ship speech engines:** Android has `SpeechRecognizer` (supports hi-IN/en-IN) and `TextToSpeech`; web browsers have the Web Speech API (where available). The Android app already wires these hooks (`useSpeechRecognition`, `useSpeechSynthesis`).

## Decision (PROPOSED)

1. **MVP voice = client-platform speech APIs.** Android uses `SpeechRecognizer` + `TextToSpeech`; web uses the Web Speech API with graceful fallback to text input. The backend never sees audio; only the recognized text crosses the API boundary (as ordinary chat messages).
2. **No server-side voice service.** This eliminates the unauthenticated-network-service class of findings entirely, avoids model downloads the current hardware/storage cannot comfortably host, and keeps the backend surface small.
3. **Backend exposes a capabilities endpoint** (`GET /api/v1/voice/capabilities`) so clients can query server-side voice support explicitly instead of hard-coding assumptions: `{ "server_stt": false, "server_tts": false, "client_platform_voice": true, "note": "…" }`.
4. **Server-side voice is deferred, not forbidden.** If a demonstrated need arises (e.g., persistent audio transcripts for accessibility, or web clients without any speech engine), the owner must approve: the model choice, model storage on `/data`, and an authenticated, loopback-bound design. FastAPI native (same process, auth'd endpoint, streaming STT) is the preferred shape over resurrecting a separate unauthenticated service.

## Consequences

- (+) No new attack surface, no unauthenticated listeners, no model downloads, no storage-policy conflicts.
- (+) Hindi/English voice works today on Android via platform engines (Hinglish falls back to engine defaults — honest limitation).
- (−) Browser support for Web Speech API is uneven; voice on unsupported browsers degrades to text (documented in-app behavior, not a defect).
- (−) Server-side transcription/testing requirements in the Phase 5 final-testing prompt (section 7) are **NOT APPLICABLE** under this decision — no server audio path exists to test. Only the capabilities endpoint and client-side hooks are testable.
- Retention/deletion testing for audio: N/A — no audio is ever received or stored server-side.

## Verification plan (if accepted)

- Capabilities endpoint unit tests (auth, shape).
- Android: existing speech hooks exercised manually on a device; recorded as owner-side manual QA (no emulator in this environment).
