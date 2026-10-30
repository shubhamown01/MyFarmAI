# MyFarmAI — Third-Party Notices

This file documents the licenses of all third-party software, models, and services used by MyFarmAI.

> **Authoritative versions:** Python dependency versions are pinned in `backend/uv.lock`; web dependency versions in `web/package-lock.json`; Android in `android/yarn.lock` (or equivalent). The tables below are indicative snapshots — the lockfiles are the source of truth.

---

## Runtime Dependencies

### Backend (Python)

| Package | Version | License | Source |
|---------|---------|---------|--------|
| fastapi | 0.115.0 | MIT | PyPI |
| uvicorn[standard] | 0.34.0 | BSD-3-Clause | PyPI |
| httpx | 0.28.1 | MIT | PyPI |
| pydantic-settings | 2.9.0 | MIT | PyPI |
| aiosqlite | 0.20.0 | MIT | PyPI |
| sqlalchemy | 2.0.36 | MIT | PyPI |
| asyncpg | 0.29.0 | MIT | PyPI |
| alembic | 1.13.1 | MIT | PyPI |
| psycopg[binary] | 3.2.5 | LGPL-3.0-or-later | PyPI |
| psycopg-pool | 3.2.2 | LGPL-3.0-or-later | PyPI |
| python-multipart | latest | MIT | PyPI |

**Development Dependencies:**
| Package | Version | License |
|---------|---------|---------|
| pytest | 8.3.4 | MIT |
| pytest-asyncio | 0.25.3 | MIT |
| pytest-cov | 6.0.0 | MIT |
| ruff | 0.9.0 | MIT |
| mypy | 1.14.0 | MIT |

---

### Frontend — Web (Node.js)

| Package | Version | License |
|---------|---------|---------|
| next | 15.5.28 | MIT |
| react | 18.3.0 | MIT |
| react-dom | 18.3.0 | MIT |
| @tanstack/react-query | 5.x | MIT |
| zustand | 4.5.0 | MIT |
| lucide-react | 0.400.0 | ISC |
| clsx | 2.1.0 | MIT |
| tailwind-merge | 2.3.0 | MIT |
| motion | 14.3.0 | MIT |

**Development Dependencies:**
| Package | Version | License |
|---------|---------|---------|
| typescript | 5.3.x | Apache-2.0 |
| eslint | 8.57.0 | MIT |
| jest | 30.5.2 | MIT |
| @testing-library/react | 16.3.3 | MIT |
| @testing-library/jest-dom | 7.0.1 | MIT |
| @axe-core/playwright | 4.14.0 | MPL-2.0 |
| tailwindcss | 3.4.x | MIT |
| postcss | 8.4.x | MIT |

---

### Frontend — Android (Expo/React Native)

| Package | Version | License |
|---------|---------|---------|
| expo | ~51.0.0 | MIT |
| expo-router | ~3.5.0 | MIT |
| expo-secure-store | ~13.0.0 | MIT |
| expo-speech | ~12.0.0 | MIT |
| expo-speech-recognition | ~1.0.0 | MIT |
| react-native | 0.74.0 | MIT |
| react-native-paper | 5.12.0 | MIT |
| react-native-reanimated | ~3.10.0 | MIT |
| react-native-gesture-handler | ~2.16.0 | MIT |
| react-native-safe-area-context | 4.10.0 | MIT |
| react-native-screens | 3.31.1 | MIT |
| @react-navigation/native | 6.1.x | MIT |
| @react-navigation/stack | 6.3.x | MIT |
| zustand | 4.5.0 | MIT |

---

## AI Models & Services

### Ollama Models (served locally)

| Model | Version/Tag | Parameters | Quantization | License | Source |
|-------|-------------|------------|--------------|---------|--------|
| qwen3 | 0.6b | 751M | Q4_K_M | **Apache-2.0** | Alibaba Cloud |
| qwen3 | 4b | 4.0B | Q4_K_M | **Apache-2.0** | Alibaba Cloud |
| qwen3-vl | 2b | 2.1B | Q4_K_M | **Apache-2.0** | Alibaba Cloud |
| qwen3-embedding | 0.6b | 595M | Q8_0 | **Apache-2.0** | Alibaba Cloud |
| nomic-embed-text | latest | 137M | F16 | **Apache-2.0** | Nomic AI |
| phi | latest | 3B | Q4_0 | **MIT** | Microsoft Research |
| gemma | latest | 9B | Q4_0 | **Gemma Terms of Use** | Google |
| mistral | latest | 7.2B | Q4_K_M | **Apache-2.0** | Mistral AI |
| deepseek-r1 | latest | 8.2B | Q4_K_M | **MIT** | DeepSeek |
| deepseek-coder | latest | 1B | Q4_0 | **MIT** | DeepSeek |
| qwen2.5-coder | 3b | 3.1B | Q4_K_M | **Apache-2.0** | Alibaba Cloud |

> **Note:** All Ollama models are served from `/data/SentinelAI/ollama/models` (shared with SentinelAI project). MyFarmAI default is `qwen3:0.6b` (522 MB) for hardware compatibility (2 GB VRAM).

---

### Local Model Assets (`/data/MyFarmAI-models`)

| Asset | Size | License | Verification |
|-------|------|---------|--------------|
| **SROTA Hinglish ASR** (Qwen3-ASR-0.6B finetune) | 1.56 GB | **Apache-2.0** | README.md front-matter |
| **PolyWhisper Hinglish Router** | 6.5 MB | **UNVERIFIED** | No LICENSE file found |
| **Whisper Small** (OpenAI) | 3.7 GB | **Apache-2.0** | README.md |
| **IndicTrans2 indic-indic-dist-320M** | 2.56 GB (dup) | **MIT** | LICENSE file + README |
| **IndicConformer Multilingual 600M** | 2.52 GB | **UNVERIFIED** | No LICENSE in .nemo archive |
| **AI4Bharat Indic-TTS FastPitch en+hi** | 1.3 GB (dup) | **MIT** | LICENSE.txt |
| **AI4Bharat Indic-TTS HiFi-GAN en+hi** | 2.0 GB (dup) | **MIT** | LICENSE.txt |

> **Duplication Note:** Whisper Small, IndicTrans2, and TTS checkpoints exist in both `.bin`/`.safetensors` and duplicate directory structures (~4.9 GB total). Preserved pending owner decision.

---

## Infrastructure Services

| Service | Version | License | Notes |
|---------|---------|---------|-------|
| **SearXNG** | latest | **AGPL-3.0** | Network-use obligations if modified/distributed. Secret externalized to `.env`. |
| **Ollama** | latest | **MIT** | Local model runtime |
| **PostgreSQL** | 17 | **PostgreSQL License** (MIT-like) | Planned for Phase 2 |
| **Open-Meteo API** | N/A | **Non-commercial only** | Weather data — not for commercial use without permission |
| **Docker** | latest | **Apache-2.0** | Container runtime |
| **Caddy** | latest | **Apache-2.0** | Planned reverse proxy (Phase 1/8) |

---

## License Compliance Notes

### AGPL-3.0 Obligations (SearXNG)
- SearXNG is licensed under AGPL-3.0
- If MyFarmAI modifies SearXNG source, corresponding source must be offered to users
- Current deployment uses unmodified `searxng/searxng:latest` image
- Configuration secret managed via `.env` (not in image)

### Gemma Terms of Use
- Google's Gemma models have custom terms (not standard OSI license)
- Review `https://ai.google.dev/gemma/terms` before redistribution

### Open-Meteo Non-Commercial Restriction
- Weather data from `api.open-meteo.com` restricted to non-commercial use
- ADR-011 documents this constraint; commercial licensing decision deferred to Phase 5

---

## Attribution

This project includes software developed by:
- The FastAPI contributors
- The Next.js contributors  
- The Expo team
- The React Native community
- Alibaba Cloud (Qwen models)
- Nomic AI (nomic-embed-text)
- Microsoft Research (Phi)
- Google (Gemma)
- Mistral AI
- DeepSeek
- OpenAI (Whisper)
- AI4Bharat (Indic models)
- The SearXNG community (searxng project)
- Ollama project
- Open-Meteo team

---

*Generated 2026-10-24 as part of Phase 1 governance gate G2 completion.*
