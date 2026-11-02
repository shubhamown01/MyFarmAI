# MyFarm AI — Zero-Cost & Open-Source Dependency Policy (Owner Directive, 2026-11-01)

**Directive:** MyFarm AI must be independently operable without mandatory paid APIs, subscriptions, commercial quotas, or recurring infrastructure charges. Local mode must keep the core application fully functional when all optional external integrations are unavailable.

**Classification legend:** CORE-SELF-HOSTED · OPTIONAL-OPEN-SOURCE · OPTIONAL-FREE-EXTERNAL · PAID-PROHIBITED · LICENSE-RESTRICTED · REQUIRES-OWNER-APPROVAL

## 1. Service & platform classification (as implemented)

| Dependency | Role | License (verified posture) | Cost | Failure behavior | Class |
|---|---|---|---|---|---|
| PostgreSQL 17 (docker, local volume) | Primary DB | PostgreSQL Licence (permissive) | ₹0 self-host | App degrades; not a runtime external call | CORE-SELF-HOSTED |
| SQLite (canonical historical DB) | Dev/legacy DB | Public domain | ₹0 | — | CORE-SELF-HOSTED |
| Ollama + qwen3:0.6b (chat) | Primary AI inference | Ollama MIT; model: Apache-2.0 per Ollama model card (recorded at adoption — re-verify model card before any public release) | ₹0, local GPU/CPU | Chat returns 503 AI_UNAVAILABLE; never falls back to paid APIs (rule 8) | CORE-SELF-HOSTED |
| Ollama + qwen3-vl:2b (vision) | Image analysis | Same posture as above | ₹0 local | Vision 503 VISION_MODEL_UNAVAILABLE (registry gate); chat unaffected | CORE-SELF-HOSTED |
| SearXNG (loopback container) | Web search/metasearch for research flow | AGPL-3.0 — self-hosted, **unmodified** upstream image; source is publicly available upstream; no MyFarm code linked into it | ₹0 self-host | Research flow returns a no-results/grounded fallback; chat, vision, weather unaffected | OPTIONAL-OPEN-SOURCE (LICENSE-RESTRICTED caveat: AGPL — do not modify and serve it as a public service without complying with §13; unmodified private deployment is the current and intended posture) |
| Open-Meteo | Weather data for farm context | Free tier, **non-commercial** (owner accepted 2026-10-31); CC-BY-SA-style attribution per provider terms | ₹0 within free quota | **Fail-open:** chat proceeds with no weather block and the prompt forbids inventing conditions; weather endpoints return an explicit unavailable state. Core functionality never depends on it (rule 6) | OPTIONAL-FREE-EXTERNAL |
| DuckDNS (planned, 6K) | Free subdomain for TLS | Free community service | ₹0 | App remains reachable on LAN/IP; TLS is an availability upgrade, not a core dependency | OPTIONAL-FREE-EXTERNAL |
| Caddy (planned, 6K) | Reverse proxy + DNS-01 TLS | Apache-2.0 | ₹0 | — | CORE-SELF-HOSTED |

**PAID-PROHIBITED currently in use: none.**
**REQUIRES-OWNER-APPROVAL queue:** any future Oracle/AWS free-tier hosting (owner decision 2026-10-31: this machine first, portability-first design); any translation/speech API (Android uses on-device expo-speech + expo-speech-recognition — no cloud speech API).

## 2. Code dependency stacks (direct, pinned)

| Stack | Direct deps (pinned) | Licenses (family) | Cost | Class |
|---|---|---|---|---|
| Backend (`backend/pyproject.toml`) | fastapi, uvicorn, httpx, pydantic-settings, aiosqlite, sqlalchemy, asyncpg, alembic, psycopg, argon2-cffi, email-validator, python-multipart, pyjwt (E2 OAuth id_token verification), cryptography (JWKS/RSA — pyjwt[crypto]) | BSD/MIT/Apache-2.0 family; argon2-cffi is CN-CC0/aladdin-style permissive for use; PyJWT MIT; cryptography Apache-2.0/BSD-3 | ₹0 | CORE-SELF-HOSTED |
| Dev backend | pytest, pytest-asyncio, pytest-cov, ruff, mypy | MIT family | ₹0 | OPTIONAL-OPEN-SOURCE |
| Web (`web/package.json`) | next, react, react-dom, @tanstack/react-query, zustand, clsx, lucide-react, motion, tailwind-merge | MIT family (next/react MIT) | ₹0 | CORE-SELF-HOSTED |
| Android (`android/package.json`) | expo, expo-router, expo-secure-store, expo-speech, expo-speech-recognition, react-native, react-native-paper, navigation/reanimated/screens, zustand | MIT family (Expo EULA for managed tooling is free for this use) | ₹0 | CORE-SELF-HOSTED |
| Infra | docker, docker compose, postgres:17 image, socat bridge to host Ollama | Apache-2.0 / PostgreSQL License | ₹0 | CORE-SELF-HOSTED |

Transitive license audit is delegated to tooling and recorded as a follow-up (rule 13 full audit): `pip-licenses` / `license-checker` runs are queued for the pre-launch checklist; pip-audit (2026-10-31) reported **no known vulnerabilities**.

## 3. Policy conformance check (current features)

| Rule | Status | Evidence |
|---|---|---|
| 1–4 zero-cost / open-source / self-host / local-AI | PASS | All services above self-hosted; AI = local Ollama |
| 5 no paid API dependency | PASS | None present |
| 6 no free-tier dependency for core function | PASS | Chat/vision/resources/auth work with Open-Meteo and SearXNG unreachable (fail-open chat, explicit unavailable states) — verified in code paths (`chat.py` weather fail-open; research fallback) |
| 7 no billing activation | PASS | Nothing activated; owner decisions recorded |
| 8 no automatic paid fallback | PASS | No paid fallback exists anywhere in the codebase |
| 9 provider independence | PASS | SQLAlchemy dual-dialect (sqlite/postgres), portability-first deployment decision, web build with configurable API URL |
| 10–11 data ownership & privacy | PASS | Farmer data stays in local Postgres/SQLite; no third-party AI egress; backups under `/data/MyFarmAI-backups` (owner-controlled, cron active) |
| 14 resource awareness | PASS | Concurrency gate + queue-depth limits (503 AI_BUSY), 2 GiB VRAM serial constraint enforced host-side |
| 15 graceful degradation | PASS | Weather fail-open; SearXNG fallback; AI 503/504 mapped errors |
| 17 security | PASS | No published DB/model ports; compose internal network; M1 auth on weather/resources (FCL-068/069) |
| 18 documentation | THIS DOC + FCL | — |

## 4. Acceptance-rule consequence

No COMPLETE feature currently requires an external free quota for its essential functionality. Weather-enriched farm context and research grounding are enhancements that degrade explicitly. This document is the required classification record for Phase 6 acceptance criterion 12 (privacy/licensing documentation).
