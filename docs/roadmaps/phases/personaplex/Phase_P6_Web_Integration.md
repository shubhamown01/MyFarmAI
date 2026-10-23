# Phase P6 — MyFarmAI Web Integration

**Status:** ⏳ READY (awaits P5 gateway + Phase 7 web)  
**Prerequisite:** P5 complete (gateway routes voice); Phase 7 (web) in progress  
**Blocks:** P7, P8

---

## 1. Objective

Add opt-in, accessible voice interaction to the MyFarmAI Next.js web application that:
- Requests microphone permission with clear consent UI
- Connects to the AI gateway voice WebSocket
- Provides real-time audio visualization and status
- Gracefully falls back to text chat when voice unavailable
- Preserves existing text chat experience unchanged

---

## 2. User Experience Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        Chat Interface                            │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  [💬 Text Chat]  [🎤 Voice Chat]  [🔊 Mic: OFF]  [⚙️]    │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  When [🎤 Voice Chat] clicked:                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  🎤 "Allow microphone access?"                             │  │
│  │  [Allow]  [Deny]  [Remember]                               │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  If Allowed:                                                    │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  🎤 Listening...  [🔴 Stop]  [⏸️ Pause]                   │  │
│  │  ████████░░░░░░░░░░  (audio level meter)                   │  │
│  │                                                             │  │
│  │  User: "What crop should I plant in Punjab?"               │  │
│  │  🎤 Agent: "For Punjab in October, wheat is..."            │  │
│  │                                                             │  │
│  │  [User interrupts] "What about rice?"                      │  │
│  │  🎤 Agent: "Rice needs more water..."                      │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Components

### `VoiceChatToggle`
- Button to switch between text/voice mode
- Shows mic status (on/off/muted)
- Tooltip explains voice capabilities

### `VoiceConsentDialog`
- Modal requesting microphone permission
- Explains: "MyFarmAI will use your microphone for voice chat. Audio is processed in real-time and not stored."
- Buttons: Allow / Deny / Remember choice

### `VoiceChatInterface`
- WebSocket connection to `/api/v1/ai/voice/sessions/{id}/stream`
- Audio level meter (visualizes input volume)
- Transcript display (user + agent text)
- Controls: Stop, Pause/Resume, Mute
- Interruption handling (user can speak while agent talking)

### `VoiceStatusIndicator`
- Connection status: Connecting / Connected / Reconnecting / Disconnected
- Model status: Ready / Loading / Unavailable
- Latency indicator (green/yellow/red)

---

## 3. Technical Implementation

### Audio Capture (Web Audio API)
```typescript
// hooks/useVoiceAudio.ts
interface VoiceAudioConfig {
  sampleRate: 24000;
  chunkSize: 480; // 20ms @ 24kHz
  echoCancellation: true;
  noiseSuppression: true;
  autoGainControl: true;
}

async function createAudioStream(config: VoiceAudioConfig): Promise<MediaStream> {
  return navigator.mediaDevices.getUserMedia({
    audio: {
      sampleRate: config.sampleRate,
      channelCount: 1,
      echoCancellation: config.echoCancellation,
      noiseSuppression: config.noiseSuppression,
      autoGainControl: config.autoGainControl,
    },
  });
}

function createAudioProcessor(
  stream: MediaStream,
  onChunk: (chunk: ArrayBuffer) => void
): ScriptProcessorNode {
  const audioCtx = new AudioContext({ sampleRate: 24000 });
  const source = audioCtx.createMediaStreamSource(stream);
  const processor = audioCtx.createScriptProcessor(480, 1, 1);
  
  processor.onaudioprocess = (e) => {
    const input = e.inputBuffer.getChannelData(0);
    const chunk = new Int16Array(input.length);
    for (let i = 0; i < input.length; i++) {
      chunk[i] = Math.max(-32768, Math.min(32767, Math.round(input[i] * 32767)));
    }
    onChunk(chunk.buffer);
  };
  
  source.connect(processor);
  processor.connect(audioCtx.destination);
  return processor;
}
```

### WebSocket Client
```typescript
// hooks/useVoiceSession.ts
interface VoiceSession {
  sessionId: string;
  ws: WebSocket;
  sendAudio: (chunk: ArrayBuffer) => void;
  interrupt: () => void;
  close: () => void;
  onEvent: (event: VoiceEvent) => void;
}

async function createVoiceSession(config: VoiceSessionConfig): Promise<VoiceSession> {
  // 1. Create session via REST
  const resp = await fetch('/api/v1/ai/voice/sessions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
    body: JSON.stringify(config),
  });
  const { session_id, ws_url } = await resp.json();

  // 2. Connect WebSocket
  const ws = new WebSocket(ws_url);
  ws.binaryType = 'arraybuffer';

  return {
    sessionId,
    ws,
    sendAudio: (chunk) => ws.readyState === WebSocket.OPEN && ws.send(chunk),
    interrupt: () => ws.send(JSON.stringify({ type: 'interrupt' })),
    close: () => ws.close(),
    onEvent: (cb) => { ws.onmessage = (e) => cb(JSON.parse(e.data)); },
  };
}
```

---

## 3. UI Components

| Component | Props | Responsibilities |
|-----------|-------|------------------|
| `VoiceChatToggle` | `mode: 'text' \| 'voice'`, `onChange` | Switch modes, show mic status |
| `VoiceConsentDialog` | `open`, `onAllow`, `onDeny` | Microphone permission |
| `VoiceChatInterface` | `session`, `onTranscript`, `onError` | Main voice UI |
| `AudioLevelMeter` | `level: 0-1`, `peak` | Visual feedback |
| `VoiceTranscript` | `messages: TranscriptEntry[]` | Display conversation |
| `VoiceControls` | `onStop`, `onPause`, `onMute`, `onInterrupt` | User controls |

---

## 4. Error & Edge Case Handling

| Scenario | UI Behavior |
|----------|-------------|
| Mic permission denied | Show "Microphone access required" with link to browser settings |
| Voice service unavailable | Banner: "Voice chat unavailable. Text chat available." + fallback to text |
| Connection lost | Show "Reconnecting..." with spinner; auto-reconnect 3× then show error |
| Mic disconnected | "Microphone disconnected. Reconnect to continue." |
| Permission revoked mid-session | Pause session; show "Microphone access revoked" |
| High latency | Show "High latency detected" warning; suggest text chat |

---

## 4. Accessibility (WCAG 2.1 AA)

| Requirement | Implementation |
|-------------|----------------|
| Keyboard navigation | All controls reachable via Tab; Space/Enter activates |
| Screen readers | ARIA labels on all controls; live region for transcripts |
| Color contrast | 4.5:1 minimum for all text/controls |
| Motion | Respect `prefers-reduced-motion` for audio visualizer |
| Captions | Agent text shown in transcript (not audio captions) |

---

## 5. Configuration

```typescript
// config/voice.ts
export const VOICE_CONFIG = {
  sampleRate: 24000,
  chunkMs: 20,
  maxSessionMinutes: 30,
  reconnectAttempts: 3,
  reconnectDelayMs: 1000,
  audioLevelSmoothing: 0.3,
  defaultVoiceId: 'default_female',
  defaultLanguage: 'en-IN',
  defaultPrompt: `You are an agricultural assistant for Indian farmers...`,
} as const;
```

---

## 5. Acceptance Criteria

- [ ] Voice toggle switches between text/voice modes
- [ ] Microphone consent dialog shown on first voice activation
- [ ] Real-time audio level meter responds to input
- [ ] Full-duplex conversation works (user speaks, agent responds)
- [ ] User can interrupt agent mid-response (barge-in)
- [ ] Transcript shows both user and agent text in real-time
- [ ] Graceful fallback to text chat when voice unavailable
- [ ] Connection status shown (connecting/connected/reconnecting/error)
- [ ] All controls keyboard accessible; screen reader compatible
- [ ] No audio data stored or logged
- [ ] Microphone indicator in browser tab while active

---

## 5. Status Tracking

| Task | Status | Verified | Notes |
|------|--------|----------|-------|
| UX flow designed | VERIFIED | ✅ | Documented above |
| Audio capture hook | NOT STARTED | ❌ | |
| WebSocket client | NOT STARTED | ❌ | |
| UI components | NOT STARTED | ❌ | |
| Consent dialog | NOT STARTED | ❌ | |
| Error handling | NOT STARTED | ❌ | |
| Accessibility audit | NOT STARTED | ❌ | |
| Integration tests | NOT STARTED | ❌ | |

---

## 6. Dependencies

- **Requires:** P5 (gateway), Phase 7 (web app structure)
- **Blocks:** P7 (Android), P8 (ag behavior)