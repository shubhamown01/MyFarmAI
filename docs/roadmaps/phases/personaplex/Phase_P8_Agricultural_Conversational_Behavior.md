# Phase P8 — Agricultural Conversational Behavior

**Status:** ⏳ READY (awaits P5 gateway + Phase 5 ag integrations)  
**Prerequisite:** P5 complete; Phase 5 (Ag integrations) in progress  
**Blocks:** P10, P11

---

## 1. Objective

Define how the PersonaPlex voice interface passes farmer questions to agricultural reasoning and research layers while:
- Preserving source citations and uncertainty disclosures
- Avoiding fabricated weather, crop diagnoses, or government schemes
- Requesting clarification when critical context is missing
- Deferring to qualified agricultural expertise for high-risk decisions

---

## 2. Core Principles

| Principle | Implementation |
|-----------|----------------|
| **Evidence over generation** | Voice answers must cite sources when claiming facts |
| **Uncertainty disclosure** | "I'm not certain" / "This is an estimate" spoken explicitly |
| **Context-aware** | Use farm location, crop, season from user profile |
| **No fabrication** | Never invent weather, prices, schemes, diagnoses |
| **Safe escalation** | "For pesticide decisions, consult your local KVK" spoken |
| **Language support** | Hindi, English, regional languages as configured |

---

## 3. Voice Prompt Template

```python
VOICE_SYSTEM_PROMPT = """You are an agricultural voice assistant for Indian farmers.

CORE BEHAVIOR:
- Speak naturally in the farmer's language ({language})
- If crop specified ({crop}), tailor advice to that crop
- If location specified ({location}), consider regional context
- NEVER invent weather, prices, government schemes, or disease diagnoses
- When uncertain: "I'm not certain about that. Let me check." or "This is an estimate."
- For high-risk decisions (pesticides, loans, seeds): "Please consult your local KVK or agricultural officer."

CONVERSATIONAL STYLE:
- Use conversational Hindi/English mix as appropriate
- Keep responses concise (2-3 sentences max per turn)
- Acknowledge interruptions naturally: "Yes, go ahead."
- Use backchannels: "हाँ", "ठीक है", "समझ गया"

AGRICULTURAL SAFETY:
- Never recommend specific pesticide brands or dosages
- Never diagnose plant diseases from audio description alone
- Never quote specific government scheme amounts or deadlines
- Always distinguish: "Government data says..." vs "I estimate..."
- For urgent issues: "This sounds urgent. Contact your local KVK at..."
"""
```

---

## 3. Context Passing to Agricultural Layers

### Voice → Gateway → Ag Reasoning Flow

```
User Voice → STT (PersonaPlex) → Text Query → AI Gateway → 
  → Text LLM (Ollama) with Ag Context → Structured Response
        ↓
    PersonaPlex TTS → Audio Response
```

### Context Enrichment

```python
async def enrich_voice_query(
    user_text: str,
    user_id: str,
    session: VoiceSession
) -> EnrichedQuery:
    # Get user's farm context
    farms = await farm_repo.get_user_farms(user_id)
    active_farm = session.farm_id or farms[0] if farms else None
    
    # Get current crop cycle
    crop_cycle = None
    if active_farm:
        crop_cycle = await crop_repo.get_active_cycle(active_farm.id)
    
    # Get recent weather
    weather = None
    if active_farm:
        weather = await weather_service.get_current(active_farm.latitude, active_farm.longitude)
    
    return EnrichedQuery(
        original_text=user_text,
        user_id=user_id,
        farm_id=active_farm.id if active_farm else None,
        crop=active_farm.current_crop if active_farm else None,
        crop_cycle_stage=crop_cycle.stage if crop_cycle else None,
        location=active_farm.location if active_farm else None,
        weather_summary=weather.summary if weather else None,
        season=get_current_season(),
        language=session.language,
    )
```

---

## 3. Response Generation with Citations

### Text LLM Response Format (for TTS)

```json
{
  "answer": "For wheat in Punjab this season, the recommended sowing time is mid-October to mid-November. Government data from ICAR suggests using 100-125 kg seed per hectare.",
  "citations": [
    {
      "source": "ICAR Punjab Package of Practices 2024",
      "url": "https://icar.org.in/punjab-wheat-2024",
      "claim": "Sowing time mid-Oct to mid-Nov, seed rate 100-125 kg/ha"
    }
  ],
  "uncertainties": [],
  "escalation": null,
  "spoken_form": "गेहूं के लिए पंजाब में इस मौसम में बुवाई का सही समय मध्य अक्टूबर से मध्य नवंबर तक है। सरकारी डेटा के अनुसार, बीज दर 100 से 125 किलोग्राम प्रति हेक्टेयर होनी चाहिए।"
}
```

### TTS Formatting Rules

| Element | Spoken Form |
|---------|-------------|
| Citations | "According to [source]..." or "सरकारी डेटा के अनुसार..." |
| Uncertainty | "मैं पूरी तरह sure नहीं हूँ..." / "यह एक अनुमान है..." |
| Escalation | "यह फैसला महत्वपूर्ण है। कृपया अपने KVK से सलाह लें।" |
| Numbers | Spoken naturally: "एक सौ पच्चीस किलोग्राम" not "125 kg" |
| Units | Spoken: "हेक्टेयर", "किलोग्राम", "डिग्री सेल्सियस" |

---

## 4. Agricultural Intent Classification

| Intent | Trigger | Handler | Response Style |
|--------|---------|---------|----------------|
| `weather_query` | "मौसम कैसा है", "बारिश कब होगी" | Weather service | Spoken forecast + uncertainty |
| `crop_advice` | "गेहूं कैसे लगाएं", "धान की बीमारी" | Ag reasoning + citations | Spoken advice + source |
| `scheme_query` | "किसान योजना क्या है", "सब्सिडी कितनी" | Scheme service | Official data + "check official portal" |
| `market_price` | "गेहूं का रेट", "मंडी भाव" | Market service | "Current rate X, but check local mandi" |
| `disease_diagnosis` | "पत्ते पीले हो रहे" | **ESCALATE** | "यह diagnosis के लिए expert चाहिए" |
| `pesticide_recommendation` | "कौन सी दवा डालें" | **ESCALATE** | "दवा के लिए KVK से पूछें" |
| `loan_scheme` | "किसान क्रेडिट कार्ड" | Scheme service | Official info + "bank से confirm करें" |
| `soil_test` | "मिट्टी की जांच" | Ag service | "KVK में free soil testing होता है" |

---

## 5. Escalation Patterns

| Risk Level | Trigger | Spoken Response |
|------------|---------|-----------------|
| **HIGH** | Pesticide dosage, disease diagnosis, seed treatment | "यह फैसला फसल और सेहत के लिए बहुत महत्वपूर्ण है। कृपया अपने निकटतम KVK या कृषि अधिकारी से सलाह लें। मैं उनका नंबर दे सकता हूँ।" |
| **MEDIUM** | Specific variety recommendation, fertilizer ratio | "यह सामान्य सलाह है। आपके खेत की मिट्टी और पानी के हिसाब से बदल सकती है। KVK से मिट्टी जांच करवाएँ।" |
| **LOW** | General sowing time, general irrigation | Normal cited response |

---

## 5. Language Support

| Language | Code | Voice Support | Notes |
|----------|------|---------------|-------|
| Hindi | `hi` | ✅ Primary | Devanagari TTS |
| English (India) | `en-IN` | ✅ Primary | Indian accent |
| Punjabi | `pa` | ⚠️ Planned | Gurmukhi script |
| Marathi | `mr` | ⚠️ Planned | Devanagari |
| Tamil | `ta` | ⚠️ Planned | Tamil script |
| Telugu | `te` | ⚠️ Planned | Telugu script |
| Bengali | `bn` | ⚠️ Planned | Bengali script |

---

## 5. Acceptance Criteria

- [ ] Voice prompt enforces agricultural safety rules
- [ ] Context enrichment pulls farm/crop/weather automatically
- [ ] Responses include spoken citations ("सरकारी डेटा के अनुसार...")
- [ ] Uncertainty spoken explicitly ("मैं पूरी तरह sure नहीं हूँ")
- [ ] High-risk topics trigger spoken escalation ("KVK से सलाह लें")
- [ ] No fabricated weather, prices, schemes, or diagnoses
- [ ] Language switching works (Hindi ↔ English-IN)
- [ ] Regional context used (Punjab wheat vs Maharashtra cotton)
- [ ] Season-aware advice (kharif vs rabi)

---

## 5. Status Tracking

| Task | Status | Verified | Notes |
|------|--------|----------|-------|
| Voice prompt template | VERIFIED | ✅ | Documented above |
| Context enrichment | NOT STARTED | ❌ | Needs Phase 5 |
| Citation speech format | NOT STARTED | ❌ | |
| Escalation patterns | NOT STARTED | ❌ | |
| Intent classification | NOT STARTED | ❌ | |
| Language support | NOT STARTED | ❌ | Hindi/English first |
| Safety testing | NOT STARTED | ❌ | Adversarial tests |

---

## 6. Dependencies

- **Requires:** P5 (gateway), Phase 5 (ag domain models, weather, schemes)
- **Blocks:** P10 (performance), P11 (production)