# Phase P7 — Android Integration

**Status:** ⏳ READY (awaits P5 gateway + Phase 8 Android)  
**Prerequisite:** P5 complete; Phase 8 (Android app structure) in progress  
**Blocks:** P8, P10

---

## 1. Objective

Add voice interaction to the MyFarmAI Android (Expo/React Native) app with:
- Proper audio capture/playback on Android
- Correct API base URL configuration (fixing the existing relative URL bug)
- Microphone permissions, audio focus, and lifecycle handling
- Secure token storage and session management
- Offline/background behavior handling

---

## 2. Current Android State (from Phase 0 Audit)

| Issue | Status | Fix Required |
|-------|--------|--------------|
| Relative URL fetch | ❌ BROKEN | Use `EXPO_PUBLIC_API_BASE_URL` + endpoint |
| `getApiBaseUrl()` unused | ❌ UNUSED | Wire to all API calls |
| Voice integration | ❌ MISSING | New implementation |
| Audio permissions | ❌ MISSING | Add `RECORD_AUDIO`, `MODIFY_AUDIO_SETTINGS` |
| Secure token storage | ✅ EXISTS | `expo-secure-store` available |

---

## 2. Required Permissions (AndroidManifest.xml)

```xml
<!-- Audio recording -->
<uses-permission android:name="android.permission.RECORD_AUDIO" />
<uses-permission android:name="android.permission.MODIFY_AUDIO_SETTINGS" />

<!-- Foreground service for background audio -->
<uses-permission android:name="android.permission.FOREGROUND_SERVICE" />
<uses-permission android:name="android.permission.FOREGROUND_SERVICE_MICROPHONE" />

<!-- Network -->
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
```

---

## 3. Audio Implementation (Expo AV)

```typescript
// hooks/useVoiceAudio.ts
import { Audio } from 'expo-av';
import { AudioRecorder, AudioRecorderStatus } from 'expo-audio-recorder';

interface VoiceAudioConfig {
  sampleRate: 24000;
  channels: 1;
  bitRate: 128000;
  format: 'wav' | 'pcm';
}

class VoiceAudioManager {
  private recorder: AudioRecorder | null = null;
  private sound: Audio.Sound | null = null;
  private isRecording = false;
  private isPlaying = false;

  async startRecording(config: VoiceAudioConfig): Promise<void> {
    await Audio.setAudioModeAsync({
      allowsRecordingIOS: true,
      playsInSilentModeIOS: true,
      staysActiveInBackground: true,
      shouldDuckAndroid: true,
      playThroughEarpieceAndroid: false,
    });

    this.recorder = await AudioRecorder.createAsync({
      sampleRate: config.sampleRate,
      channels: config.channels,
      bitRate: config.bitRate,
      format: config.format,
    });

    await this.recorder.startAsync();
    this.isRecording = true;
  }

  async stopRecording(): Promise<string> { // returns file URI
    if (!this.recorder) throw new Error('Not recording');
    const uri = await this.recorder.stopAsync();
    await this.recorder.disposeAsync();
    this.recorder = null;
    this.isRecording = false;
    return uri;
  }

  async playAudio(uri: string): Promise<void> {
    this.sound = new Audio.Sound();
    await this.sound.loadAsync({ uri });
    await this.sound.playAsync();
    this.isPlaying = true;
  }

  async stopPlayback(): Promise<void> {
    if (this.sound) {
      await this.sound.stopAsync();
      await this.sound.unloadAsync();
      this.sound = null;
      this.isPlaying = false;
    }
  }

  async cleanup(): Promise<void> {
    await this.stopRecording();
    await this.stopPlayback();
  }
}
```

---

## 3. WebSocket Client (React Native)

```typescript
// hooks/useVoiceSession.ts
import { WebSocket } from 'react-native';

interface VoiceSession {
  sessionId: string;
  ws: WebSocket;
  sendAudio: (chunk: ArrayBuffer) => void;
  interrupt: () => void;
  close: () => void;
  onEvent: (event: VoiceEvent) => void;
}

async function createVoiceSession(
  config: VoiceSessionConfig,
  token: string
): Promise<VoiceSession> {
  const baseUrl = getApiBaseUrl(); // FIXED: uses EXPO_PUBLIC_API_BASE_URL
  
  // 1. Create session via REST
  const resp = await fetch(`${baseUrl}/api/v1/ai/voice/sessions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(config),
  });
  const { session_id, ws_url } = await resp.json();

  // 2. Convert HTTP to WS URL
  const wsUrl = ws_url.replace(/^http/, 'ws');

  // 3. Connect WebSocket
  const ws = new WebSocket(ws_url, {
    headers: { Authorization: `Bearer ${token}` },
  });
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

## 3. API Base URL Fix (Critical)

```typescript
// config/api.ts — CRITICAL FIX
const getApiBaseUrl = (): string => {
  // Priority: ENV > Manifest > Default
  if (__DEV__) {
    return Constants.expoConfig?.extra?.EXPO_PUBLIC_API_BASE_URL 
      || 'http://10.0.2.2:8000'; // Android emulator -> host
  }
  return Constants.expoConfig?.extra?.EXPO_PUBLIC_API_BASE_URL 
    || 'https://api.myfarmai.example.com';
};

// All API calls MUST use this:
export const apiFetch = async (endpoint: string, options: RequestInit = {}) => {
  const baseUrl = getApiBaseUrl();
  const url = `${baseUrl}${endpoint.startsWith('/') ? '' : '/'}${endpoint}`;
  return fetch(url, options);
};

// Old broken pattern (DO NOT USE):
// fetch(endpoint)  // ❌ Relative URL fails on Android
```

---

## 4. Android-Specific Audio Handling

| Scenario | Handling |
|----------|----------|
| Incoming call | Pause recording/playback; resume after |
| Notification sound | Duck audio (`AudioManager.STREAM_MUSIC` duck) |
| Headphones plugged/unplugged | `AudioManager.OnAudioFocusChangeListener` |
| Background/foreground | Foreground service for background recording |
| Do Not Disturb | Respect; pause if needed |

```typescript
// Audio focus management
import { AudioManager } from 'expo-av';

Audio.setAudioModeAsync({
  allowsRecordingIOS: true,
  playsInSilentModeIOS: true,
  staysActiveInBackground: true,
  shouldDuckAndroid: true,
  playThroughEarpieceAndroid: false,
});
```

---

## 4. Background/Foreground Handling

```typescript
// services/VoiceForegroundService.ts
import { TaskManager } from 'expo-task-manager';
import { BackgroundFetch } from 'expo-background-fetch';

TaskManager.defineTask('VOICE_RECORDING_TASK', async () => {
  // Continue recording in background
  // Upload chunks periodically
  // Stop if max duration reached
});

BackgroundFetch.registerTaskAsync('VOICE_RECORDING_TASK', {
  minimumInterval: 60, // seconds
  stopOnTerminate: false,
  startOnBoot: true,
});
```

---

## 4. Token Storage (Secure)

```typescript
// utils/secureTokenStorage.ts
import * as SecureStore from 'expo-secure-store';

const TOKEN_KEY = 'myfarmai_access_token';
const REFRESH_KEY = 'myfarmai_refresh_token';

export const tokenStorage = {
  async getAccessToken(): Promise<string | null> {
    return SecureStore.getItemAsync(TOKEN_KEY);
  },
  async setTokens(access: string, refresh: string): Promise<void> {
    await SecureStore.setItemAsync(TOKEN_KEY, access);
    await SecureStore.setItemAsync(REFRESH_KEY, refresh);
  },
  async clearTokens(): Promise<void> {
    await SecureStore.deleteItemAsync(TOKEN_KEY);
    await SecureStore.deleteItemAsync(REFRESH_KEY);
  },
};
```

---

## 4. UI Components

| Component | Purpose |
|----------|---------|
| `VoiceChatButton` | Toggle voice mode in chat header |
| `VoicePermissionPrompt` | Request mic permission with rationale |
| `VoiceRecordingIndicator` | Pulsing mic icon + timer |
| `VoicePlaybackController` | Play/pause/stop agent audio |
| `VoiceTranscriptView` | Real-time transcript (user + agent) |
| `VoiceErrorBanner` | Connection/permission errors with retry |

---

## 4. Acceptance Criteria

- [ ] `EXPO_PUBLIC_API_BASE_URL` used for all API calls (no relative URLs)
- [ ] Microphone permission requested with clear rationale
- [ ] Audio recording works on Android emulator and physical device
- [ ] Audio playback works (agent speech)
- [ ] WebSocket connects to gateway voice endpoint
- [ ] Foreground service keeps recording in background
- [ ] Audio focus handled (calls, notifications, headphones)
- [ ] Tokens stored in `expo-secure-store` (not AsyncStorage)
- [ ] Network errors show retry banner with exponential backoff
- [ ] Works on Android emulator (`10.0.2.2`) and physical device
- [ ] No audio data persisted to device storage

---

## 5. Status Tracking

| Task | Status | Verified | Notes |
|------|--------|----------|-------|
| API base URL fix | NOT STARTED | ❌ | CRITICAL - existing bug |
| Permissions manifest | NOT STARTED | ❌ | |
| Audio recording | NOT STARTED | ❌ | |
| Audio playback | NOT STARTED | ❌ | |
| WebSocket client | NOT STARTED | ❌ | |
| Foreground service | NOT STARTED | ❌ | |
| Token storage | NOT STARTED | ❌ | Uses expo-secure-store |
| UI components | NOT STARTED | ❌ | |
| Emulator testing | NOT STARTED | ❌ | `10.0.2.2:8000` |
| Device testing | NOT STARTED | ❌ | Physical device required |

---

## 5. Dependencies

- **Requires:** P5 (gateway), Phase 8 (Android structure)
- **Blocks:** P8 (ag behavior), P10 (performance)