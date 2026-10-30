# Phase 6A — Production Architecture Review

**Date:** 2026-10-31 · **Status:** REVIEW ONLY (no infrastructure changed) · **Inputs:** docker-compose.yml @ `2ad11fc`, backend/app/core/config.py, web/next.config.js, android/, scripts/, live host inspection

## 1. Current architecture (as inspected)

```
[Android app]──HTTP──┐
                     │        ┌─────────────────────────────────────────────┐
[Web: Next.js]──rewrite(/api/v1)──►│ backend (FastAPI, compose, non-root)      │
                     │        │  ├─ PostgreSQL 17 (compose, secrets-file)   │
                     │        │  ├─ Ollama via socat bridge → host loopback │
                     │        │  └─ ./backend/data bind mount (sqlite refs) │
```

- **Backend**: Docker Compose, non-root host-UID user, `myfarmai-internal` bridge network, healthcheck, `restart: unless-stopped`. No published port visible in compose (reached via dev rewrites / local run).
- **Database**: PostgreSQL 17 container, password via Docker secrets file (`POSTGRES_PASSWORD_FILE`), named volume `postgres_data`, internal network only, `pg_isready` healthcheck. (Canonical historical SQLite DBs in `backend/data/` remain on the bind mount.)
- **AI**: host-run Ollama (127.0.0.1-only), bridged into compose via socat (`scripts/ollama-bridge.sh` → 172.22.0.1:11434). Registry-gated models: qwen3:0.6b (chat), qwen3-vl:2b (vision).
- **Web**: Next.js dev-mode rewrites `/api/v1/*` → `NEXT_PUBLIC_API_BASE_URL`. **No standalone/production output config; no Dockerfile.**
- **Android**: Expo/React Native, HTTP client hooks; release/signing config not yet audited (6G).
- **Research**: SearXNG — settings env-wired, **no compose service, not deployed**.
- **CI/CD**: none (no .github/workflows).
- **Backups**: ad-hoc only — `/data/MyFarmAI-backups/` holds manual DB copies + a Phase-2 rehearsal; **no scheduled pg_dump, no restore drill, no RPO/RTO targets**.
- **Monitoring**: none (no metrics, no alerting).
- **Host capacity (measured 2026-10-31)**: `/` 74 GiB free, `/data` 99 GiB free — the Phase 0 "~5 GB free" constraint has lifted.

## 2. Proposed production architecture (single-host, OSS, zero-cost — matches budget)

```
Internet ── HTTPS ──► Caddy (reverse proxy, auto-TLS)  ← only published 80/443
                        ├─► web: Next.js standalone build (Node container)
                        └─► /api/* → backend: FastAPI (uvicorn, 1-2 workers)
                                       ├─► postgres:17 (internal net, secrets-file pw)
                                       ├─► searxng (internal net, loopback-style, env secret)
                                       └─► host Ollama (127.0.0.1, never published)
                       [pgdump cron → /data/MyFarmAI-backups, nightly + offsite copy option]
                       [cAdvisor/node-exporter-lite or compose health alerts → owner]
```

- Single VPS or the existing host behind a domain + Caddy (free, auto-HTTPS). Postgres/SearXNG/Ollama stay off the public internet.
- Backend: uvicorn workers behind proxy, prod env (`environment=production`), trusted-proxy CIDRs configured (rate-limit XFF already requires it), CORS pinned to the real domain.
- Web: `output: "standalone"` build served by its own container (small image), no rewrites at runtime (public API URL baked at build).
- Backups: nightly `pg_dump` to `/data/MyFarmAI-backups` + integrity check; restore drill in Phase 6L.

## 3. Deployment dependency map

web (build) → backend API URL; backend → postgres (health-gated), → Ollama host bridge, → SearXNG (optional, degrade-tolerant), → Open-Meteo (egress); android → published API URL; Caddy → web+backend; backups → postgres + volume.

## 4. Security boundary diagram (target)

- Public: 80/443 (Caddy) only.
- Private (never published): postgres, searxng, ollama (host-loopback), admin endpoints.
- Trust boundary: Caddy (trusted proxy CIDR for backend rate limiting) → backend auth session → repo-level user scoping → registry-gated models. Secrets: Docker secrets files + `.env` (gitignored); no inline secrets in compose (verified).

## 5. Cost & resource assessment

Zero licensing cost (OSS only). Fit on the existing host: backend+postgres+web+searxng ≈ 1.5–2 GiB RAM alongside Ollama (~1.5 GiB with qwen3:0.6b loaded) — fits 7 GiB with ~2 GiB headroom; VRAM 2 GiB serves one small model (serial only). Alternatives if remote hosting is chosen: entry VPS ~US$5–10/mo (owner approval + budget decision required). No paid services introduced.

## 6. Deployment risk register (top items)

| # | Risk | Sev | Mitigation |
|---|---|---|---|
| R1 | No backups/restore drill → data loss on failure | High | 6D/6L: nightly pg_dump + isolated restore test before any production use |
| R2 | No TLS/domain yet; traffic would be plaintext | High | 6K: Caddy auto-TLS before any exposure |
| R3 | No CI → regressions ship silently | Medium | 6J: GitHub Actions lint+test+build with mandatory gates |
| R4 | No monitoring → silent outages (Ollama/SearXNG/Open-Meteo) | Medium | 6H: health-based alerts on measured baselines |
| R5 | Web has no production build path | Medium | 6F: standalone output + container |
| R6 | Single-host SPOF (app+db+AI colocated) | Low | Accepted for budget; documented RPO/RTO; nightly offsite copy option |
| R7 | 5I notifications absent | Low | Scoped to Phase 6 per plan |
| R8 | Ollama bridge IP drift (documented in compose) | Low | Pin subnet or switch to host networking in 6B |

## 7. Owner approvals required before any of this executes

Domain/DNS, TLS exposure (publishing ports), any hosting decision (existing host vs VPS), backup schedule acceptance, and everything gated in sections 14–15 of the master prompt. **No changes have been made** — this is the review deliverable only.
