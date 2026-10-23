# Phase P9 — Security, Privacy & Compliance

**Status:** ⏳ READY (awaits P4 service + Phase 3 auth)  
**Prerequisite:** P4 service deployed; Phase 3 (Auth) complete  
**Blocks:** P10, P11

---

## 1. Objective

Define security, privacy, and compliance requirements specific to the PersonaPlex voice service, ensuring:
- Microphone consent and clear indicators
- Audio data minimization and retention controls
- Protection against voice spoofing/replay
- Compliance with applicable regulations (GDPR, India DPDP Act, etc.)
- License compliance for NVIDIA model and dependencies

---

## 2. Consent & Microphone Indicators

### Consent Flow
```
1. User clicks [🎤 Voice Chat] button
2. Consent dialog: "MyFarmAI requests microphone access for real-time voice chat. 
   Audio is processed in real-time on our servers and not stored. 
   You can stop sharing at any time."
3. Buttons: [Allow] [Deny] [Remember my choice]
4. Browser/Android permission prompt shown
5. Visual indicator in UI while microphone active
```

### Visual Indicators (Required)
| Platform | Indicator |
|----------|-----------|
| Web (Chrome/FF) | Browser mic icon in tab + custom UI pulsing mic |
| Android | System mic indicator (green dot) + app UI pulsing mic |
| iOS | System orange dot + app UI |

### Consent Storage
```typescript
interface VoiceConsent {
  userId: string;
  granted: boolean;
  timestamp: Date;
  version: string; // consent text version
  remember: boolean;
}
```

---

## 2. Audio Data Minimization

| Data Type | Retention | Storage | Purpose |
|-----------|-----------|---------|---------|
| Live audio stream | **Zero** (streaming only) | RAM only | Real-time inference |
| Transcripts (STT) | Session duration + 24h | Encrypted DB | Conversation history |
| Agent audio (TTS) | **Zero** (streaming only) | RAM only | Playback |
| Voice prompts | Model lifetime | `/data/AI-Models/` | Voice conditioning |
| Audit logs | 90 days | Encrypted DB | Security monitoring |

### Prohibited
- ❌ Raw audio recording to disk
- ❌ Audio logging to files
- ❌ Audio sent to third parties (except PersonaPlex inference)
- ❌ Voice biometric extraction/storage
- ❌ Training data collection without explicit opt-in

---

## 3. Voice Spoofing & Replay Protection

| Threat | Mitigation |
|--------|------------|
| Replay attack (recorded audio) | Short session timeouts (30 min); challenge-response for sensitive actions |
| Voice cloning | Session binding to authenticated user; rate limiting |
| Adversarial audio | Input validation (sample rate, format, duration); anomaly detection |
| Cross-session replay | Session tokens single-use; WebSocket tied to auth |

### Session Binding
```python
class VoiceSessionSecurity:
    def __init__(self):
        self.session_tokens: dict[str, SessionToken] = {}
    
    def create_session_token(self, user_id: str, session_id: str) -> str:
        # Cryptographically bound to user + session
        token = secrets.token_urlsafe(32)
        self.session_tokens[token] = SessionToken(
            user_id=user_id,
            session_id=session_id,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=30),
        )
        return token
    
    def validate(self, token: str, user_id: str, session_id: str) -> bool:
        stored = self.session_tokens.get(token)
        return (
            stored is not None
            and stored.user_id == user_id
            and stored.session_id == session_id
            and stored.expires_at > datetime.utcnow()
        )
```

---

## 3. Privacy by Design

| Principle | Implementation |
|-----------|----------------|
| Data minimization | No audio storage; transcripts only |
| Purpose limitation | Voice chat only; no analytics/training |
| Storage limitation | Auto-delete transcripts after 24h |
| Transparency | Consent dialog explains data flow |
| User control | Stop sharing anytime; delete history |
| Accuracy | User can correct transcripts |
| Security | TLS 1.3 + mTLS; encrypted DB |

### User Rights (GDPR/DPDP)
| Right | Implementation |
|-------|----------------|
| Access | Export voice transcripts + sessions |
| Rectification | Edit transcript corrections |
| Erasure | Delete all voice data on account delete |
| Portability | Export in JSON/CSV |
| Objection | Disable voice in settings |

---

## 4. License Compliance

| Component | License | Compliance Action |
|-----------|---------|-------------------|
| PersonaPlex 7B v1 | NVIDIA Open Model License | Review redistribution rights; attribute |
| Base model (Moshiko) | CC-BY-4.0 | Attribute Kyutai in credits |
| Mimi codec | Apache-2.0 / CC-BY | Include license in NOTICE |
| Moshi framework | Apache-2.0 | Include license in NOTICE |
| PyTorch | BSD-3 | Standard compliance |
| torchaudio | BSD-3 | Standard compliance |
| fastapi/uvicorn | MIT | Standard compliance |

### License Artifacts
- `NOTICE` file in distribution with all attributions
- `THIRD_PARTY_LICENSES.md` with full license texts
- Runtime license check on startup (warn if missing)

---

## 4. Regulatory Compliance

| Regulation | Applicability | Status |
|------------|---------------|--------|
| GDPR (EU) | If EU users | ⚠️ Review DPA |
| India DPDP Act 2023 | Indian users | ⚠️ Review consent/erasure |
| IT Act 2000 (India) | Audio data | ⚠️ Review |
| COPPA (US) | If <13 users | N/A (adult farmers) |
| HIPAA | Health data | N/A (agricultural) |

---

## 4. Audit Logging

| Event | Logged Fields |
|-------|---------------|
| Voice session start | user_id, session_id, voice_id, ip, user_agent |
| Voice session end | session_id, duration, bytes_in, bytes_out |
| Interrupt | session_id, timestamp, reason |
| Consent granted/denied | user_id, version, timestamp |
| Permission revoked | user_id, session_id, timestamp |
| Error | session_id, error_code, message (no audio) |

**Redacted:** Never log audio content, transcripts, or PII beyond user_id

---

## 5. Acceptance Criteria

- [ ] Consent dialog shown before first microphone access
- [ ] Visual microphone indicator while recording
- [ ] Zero raw audio persisted to disk
- [ ] Transcripts auto-deleted after 24h (configurable)
- [ ] Session tokens cryptographically bound to user
- [ ] Replay attack mitigations documented and tested
- [ ] License attribution files present in distribution
- [ ] Audit logs exclude audio content
- [ ] User can export/delete voice data
- [ ] DPDP/GDPR compliance review completed

---

## 5. Status Tracking

| Task | Status | Verified | Notes |
|------|--------|----------|-------|
| Consent flow designed | VERIFIED | ✅ | Documented |
| Visual indicators | NOT STARTED | ❌ | |
| Data retention policy | NOT STARTED | ❌ | |
| Spoofing mitigations | NOT STARTED | ❌ | |
| License audit | NOT STARTED | ❌ | |
| DPDP/GDPR review | NOT STARTED | ❌ | |
| Audit logging | NOT STARTED | ❌ | |
| User rights implementation | NOT STARTED | ❌ | |

---

## 6. Dependencies

- **Requires:** P4 (service), Phase 3 (auth)
- **Blocks:** P10, P11