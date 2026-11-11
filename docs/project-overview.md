# Project Overview

**Date:** 2026-10-23 · **Status:** verified against code

## Problem Statement

Farmers and field workers need fast, localized, trustworthy answers about crops, weather, and government schemes — often in mixed Hindi/English, often offline-capable. Generic web search is unreliable for agriculture; official advisories are scattered across dozens of portals.

## Objectives

1. Answer agricultural questions with crop/location/language-aware AI assistance.
2. Surface current weather and forecast from a free provider (Open-Meteo).
3. Provide a curated, verified catalogue of Indian government schemes and advisories.
4. Support voice interaction (Hindi/English STT) for low-literacy users.
5. Work on web (browser) and Android (Expo) clients.

## Users & Use Cases

| User | Use case |
|------|----------|
| Farmer | Ask a crop question ("मेरी फसल में पीले पत्ते क्यों?"), get actionable answer + weather context |
| Agronomist | Browse resource catalogue; check forecast before spraying |
| Field worker | Voice-ask questions; review past conversations |

## Scope

**Implemented (verified 2026-10-23):**
- Backend API: chat (Ollama/Qwen3), weather, resources, health endpoints; SQLite persistence; Alembic target schema for Phase 2.
- Web: Next.js 15 dashboard, chat 𝖨UI, weather card, resources browser.
- Android: Expo app foundation with API client config (`EXPO_PUBLIC_API_BASE_URL`).

**Contained (not exposed):** voice service (faster-whisper) — removed from Compose, port 8001 unpublished; now requires a bearer token, caps uploads at 25 MB, runs non-root, and has a healthcheck (SEC-014/SEC-028 fixed 2026-11-11). No consumer is wired yet.

**Planned (not implemented):** authentication (Phase 3), AI gateway refactor + streaming (Phase 4), farm/crop domain APIs backed by the Alembic schema (Phase 5), research pipeline with SearXNG citations (Phase 6), public TLS deployment (Phase 8).

**Non-goals:** commercial weather provider usage, paid services, cloud LLM providers.

See also: `PRD.md`, `TRD.md`, and `flows/` under `docs/product/`.
