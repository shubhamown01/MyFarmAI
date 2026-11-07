# Local-First AI Architecture

Status: PROPOSED architecture for the zero-cost deployment phase; the local
components it describes are what already runs on this machine (verified).

## 1. Principle

MyFarmAI must remain usable with **zero cloud dependency** for its core value
(Q&A about the farmer's own farm, saved advisory lists, weather cached). The
cloud is an accelerator, never a requirement. This also keeps the free-tier
quota exposure small (see `CLOUD_COST_AND_QUOTA_POLICY.md`).

## 2. Local stack (running today)

| Layer | Local implementation | Resource footprint |
|---|---|---|
| LLM inference | Ollama on the host, `qwen3:0.6b`-class models only | 2 GiB VRAM cap — GPU inference fits; bigger models are out of scope |
| AI bridge | `scripts/ollama-bridge.sh`; backend reaches host Ollama (DEPLOY health-gate: "backend reaches host Ollama") | CPU-light |
| Database | Compose Postgres (local, docker volume) | Canonical DB location is still an open governance gate — do not assume |
| Web app | Next.js on :3000 → same-origin `/api/v1` proxy → backend :8000 | Dev loop verified end-to-end |
| Diagrams/tooling | `graphify-out/` knowledge graph (per AGENTS.md) | none at runtime |

## 3. Where the cloud slots in (only when quota exists)

1. **Web search / research answers**: SearXNG self-hosted, or throttled cloud
   search later — subject to the Open-Meteo/SearXNG licensing gates (still
   open, Phase 0).
2. **Stronger answers**: cloud LLM later, gated hard by §10 quota
   (20 cloud queries/user/10h, server-side atomic). Local Qwen answers remain
   the always-available default.
3. **Public frontend**: Cloudflare Pages serves the Next.js bundle; it is
   stateless and degrades to "local mode" banners when the backend host is
   unreachable.

## 4. Offline/online behavior ladder

1. **Full offline**: local Ollama + local DB + cached advisory data. Works
   with internet down entirely.
2. **Local-only mode (cloud quota gone)**: per the degradation ladder in
   `CLOUD_COST_AND_QUOTA_POLICY.md §3` — local AI answers, saved retrievals,
   writes queue locally for sync.
3. **Online**: research/search features and (future) cloud AI on top of the
   same local data.

## 5. Constraints honored

- Host: 7 GiB RAM / 2 GiB VRAM / ~5 GB free on `/` — no model downloads beyond
  the small-tier Qwen models; no DB duplication; backups live on
  `/data/MyFarmAI-backups/` (HDD), not `/`.
- No model weights in Git (`PRODUCTION_SECURITY_CHECKLIST.md §6`).
