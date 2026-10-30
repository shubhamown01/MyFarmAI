# Hardware, Storage, and Deployment Assessment

**Phase:** 0 — read-only  
**Date:** 2026-10-24 (updated from 2026-10-21 with actual measurements)  
**Constraint source:** Verified with read-only commands; not assumed.  
**Related:** [`TARGET_BACKEND_ARCHITECTURE.md`](TARGET_BACKEND_ARCHITECTURE.md), [`ARCHITECTURE_DECISIONS.md`](ARCHITECTURE_DECISIONS.md)

---

## 1. Verified host state

| Item | Observed value | Evidence | Classification |
|---|---|---|---|
| OS | Ubuntu 26.04.1 LTS | `/etc/os-release` | Verified |
| Kernel | `7.0.0-38-generic` | `uname -r` | Verified |
| CPU/RAM | 7.0 GiB total; 4.8 GiB used; **2.2 GiB available** | `free -h` | Verified 2026-10-24 |
| Swap | 4.0 GiB total; **4.0 GiB used; 6.9 MiB free (SATURATED)** | `free -h` | Verified 2026-10-24 |
| GPU | NVIDIA GeForce MX250, 2048 MiB VRAM, 2 MiB used | `nvidia-smi` | Verified |
| GPU driver | 580.178.04 | `nvidia-smi` | Verified |
| Root disk | `/dev/nvme0n1p5`, **163 GB, 82 GB used, 74 GB free (55%)** | `df -h /` | Verified 2026-10-24 |
| Data disk | `/dev/sda2`, 274 GB, 163 GB used, **98 GB free (37%)** | `df -h /data` | Verified 2026-10-24 |
| Docker version | 29.9.1, overlayfs | `docker info` | Verified |
| Docker root | `/var/lib/docker` on `/` | `docker info` | Verified |
| Docker images | 25 images, 16.39 GB, 7.25 GB reclaimable | `docker system df` | Verified |
| Docker volumes | 9 volumes, 23.84 GB | `docker system df` | Verified |
| Docker build cache | 34 entries, 1.66 GB, 222 MB reclaimable | `docker system df` | Verified |
| Running containers | 17, including unrelated Langfuse/Sentinel stacks; **MyFarmAI containers stopped** | `docker ps` | Verified |
| Ollama | `/usr/local/bin/ollama`, listening on `127.0.0.1:11434` | `ss`, `ollama list` | Verified |
| Ollama model store | `/data/SentinelAI/ollama/models`, 44 GB (shared with SentinelAI) | systemd unit, `du` | Verified |
| **Configured model (default)** | **`qwen3:0.6b`, Q4_K_M, 751M params, 522 MB, context 40960** | `ollama show`, config.py | **Verified 2026-10-24** |
| Other models present | `qwen3:4b` (2.5 GB), `qwen3-vl:2b` (1.9 GB), `qwen3-embedding:0.6b` (639 MB), `nomic-embed-text` (274 MB), `phi`, `gemma`, `mistral`, `deepseek-r1`, `deepseek-coder`, `qwen2.5-coder` variants | `ollama list` | Verified |
| Voice service | **STOPPED, removed from Compose, port 8001 unpublished** | `docker ps`, `ss` | Verified 2026-10-24 |
| SearXNG | **STOPPED** (container Exited 137) | `docker ps -a` | Verified 2026-10-24 |
| Backend | **Running** (local dev), listener on 127.0.0.1:8000 | `ss` | Verified 2026-10-24 |
| Python | System/local 3.12.14 (uv); container 3.12 | interpreter, Dockerfile | Verified |

**Important:** host usage is a snapshot. Other projects' containers (Langfuse/Sentinel) are consuming most RAM and Docker disk. MyFarmAI containers are now stopped. Estimates below are for MyFarmAI-only profile.

## 2. Constraints and implications

### 2.1 RAM

- 7.0 GiB total; **4.8 GiB used by host+Langfuse/Sentinel; 2.2 GiB available**
- **Swap is SATURATED (4.0/4.0 GiB used, 6.9 MiB free)** — any additional memory pressure will cause heavy swapping
- Unrelated Langfuse ClickHouse, worker, Postgres, MinIO, Redis, and Sentinel containers consume RAM that MyFarmAI cannot rely on
- **Recommendation:** Measure MyFarmAI-only profile with Langfuse/Sentinel stopped; use `qwen3:0.6b` (522 MB) which fits in available RAM without swap pressure

### 2.2 VRAM

- 2 GiB VRAM **comfortably holds `qwen3:0.6b` Q4_K_M (522 MB weights)** with ample headroom for KV cache
- `qwen3:0.6b` runs fully in VRAM with no CPU offload needed — optimal latency
- `qwen3:4b` (2.5 GB) exceeds VRAM; would require CPU offload and swap (not recommended given swap saturation)
- `qwen3-embedding:0.6b` (639 MB) fits well if embeddings are needed later
- `gemma` (5 GB), `mistral` (4.4 GB), `deepseek-r1` (5.2 GB), `qwen3-vl` (6.1 GB), `qwen3-embedding:latest` (4.7 GB) do not fit VRAM
- **Default model `qwen3:0.6b` meets latency targets** — benchmarked < 10 s for agricultural prompts

### 2.3 Disk

- `/` has **74 GB free (55%)** — ample headroom for Docker builds and images
- `/data` has **98 GB free (37%)** and already holds 44 GB of Ollama models (shared with SentinelAI), the repo, and SQLite data
- Docker volumes are on `/`, not `/data`. With 74 GB free, build risk is **LOW**
- **Options (no immediate action needed):**
  1. Move Docker's data-root to `/data/docker` (daemon restart required) — optional
  2. Prune unused images/build cache (7.25 GB + 222 MB reclaimable) — optional
  3. Keep MyFarmAI images small and store Postgres data/backups on `/data` via bind mounts
- Do not delete models, volumes, or images without owner approval

### 2.4 Storage placement

| Data | Recommended location | Rationale |
|---|---|---|
| Source code | `/data/MyFarmAI` (current) | Already on the large HDD; acceptable for a single-user dev machine. |
| Ollama models | `/data/.../ollama/models` (current) | Large; 44 GB already; keep off the SSD. |
| PostgreSQL data | `/data/myfarmai/postgres` bind mount or named volume on `/data` | Persistent, large, backup-friendly. |
| Backups | `/data/myfarmai/backups` (separate from DB) | Survives DB corruption; copy off-host later. |
| Docker images/build cache | Prefer `/data/docker` | `/` is nearly full. |
| Logs | `/data/myfarmai/logs` with rotation | Avoid filling `/`. |
| Temp uploads | Size-limited tmpfs or `/data` temp dir | Avoid memory/disk exhaustion. |

## 3. Service resource estimates

These are **estimates** for planning, not measurements. Measure each service on this host before setting limits.

| Service | Idle RAM (estimate) | Active RAM (estimate) | Disk (estimate) | Notes |
|---|---:|---:|---:|---|
| FastAPI backend | 100–200 MB | 200–400 MB | <100 MB image | Python + Uvicorn; no model in process. |
| PostgreSQL 17 | 100–200 MB | 300–600 MB | 200 MB image + data | `shared_buffers` default 128 MB; tune down for 7 GB host. |
| SearXNG | 100–200 MB | 300–500 MB | ~200 MB image + cache | Current container is limited to 768 MiB. |
| Voice (faster-whisper small, int8) | ~20 MB before model load | ~0.6–1.2 GB | 464 MB model cache + image | Lazy load; first request slow. |
| Ollama runtime | ~100–300 MB | 3–4.5 GB with `qwen3:4b` | 2.5 GB model | Depends on GPU/CPU split and context. |
| Caddy | 20–50 MB | 50–100 MB | ~50 MB | TLS termination. |
| Valkey (deferred) | 10–30 MB | 50–200 MB | small | Only if background jobs are justified. |
| Qdrant (deferred) | 50–150 MB | 200–500 MB | model/collection dependent | Defer until benchmarks. |

**Minimum AI-enabled profile:** backend + PostgreSQL + Ollama with one small model + Caddy. This already likely exceeds the currently available 2.3 GiB if `qwen3:4b` is loaded. A non-AI profile (backend + Postgres + Caddy) fits more comfortably.

**Degraded profile:** if Ollama is unavailable, chat returns 503/504 while weather/resources remain available. This should be the documented fallback.

## 4. Ollama feasibility (verified 2026-10-24)

| Question | Assessment |
|---|---|
| Can `qwen3:0.6b` run? | **YES** — verified, runs fully in 2 GiB VRAM, no swap pressure |
| Can it fit fully in 2 GiB VRAM? | **YES** — 522 MB weights, ample headroom for KV cache |
| Does it meet interactive latency? | **YES** — benchmarked < 10 s for 3 agricultural prompts |
| Can multiple concurrent chats run? | **Limited** — single model instance; add concurrency limit for production |
| Alternatives | `qwen3:4b` (candidate for Phase 2 if quality justifies 5× latency); `qwen3-embedding:0.6b` ready for retrieval |
| Embeddings | `qwen3-embedding:0.6b` (639 MB) fits in VRAM; defer until ADR-007 approved |

> **Stage 1 complete:** `qwen3:0.6b` smoke test, backend integration, and regression all pass.

## 5. Deployment assessment

### 5.1 Current Compose (updated 2026-10-24)

| Issue | Status | Impact |
|---|---|---|
| `network_mode: host` for backend | **UNCHANGED** | Removes network isolation; exposes port 8000 on all host interfaces when running; makes proxy/network policy harder. |
| Voice publishes `0.0.0.0:8001` | **FIXED** | Voice service removed from Compose, port 8001 unpublished (G6 approved) |
| No healthchecks | **PENDING** (Phase 2) | `depends_on` only waits for container start; restart loops are invisible. |
| No resource limits | **PENDING** (Phase 2) | A runaway chat request can exhaust host RAM. |
| Root containers | **PENDING** (Phase 2) | Higher impact if compromised. |
| Floating images | **PENDING** (Phase 2) | Non-reproducible builds. |
| Bind-mounted `.env` | **ACCEPTED** for dev | Simple for dev; production should use secrets. |
| SQLite bind mount | **FIXED** (F2) | Now mounts `./backend/data:/app/data` → canonical DB |
| No reverse proxy/TLS | **PENDING** (Phase 8) | Plain HTTP; no HSTS/security headers. |
| SearXNG | **STOPPED** | Container Exited; removed from default profile |

### 5.2 Recommended initial topology (single host)

```text
Internet/LAN
    |
 Caddy (TLS, rate limits, body limits)
    |
 backend (FastAPI, non-root, internal network)
    |            \
 PostgreSQL      Ollama (localhost/host-gateway)
    |
 /data/myfarmai/postgres
```

- Keep Ollama on the host (already installed) and reach it via a controlled host gateway or a private Docker network; avoid host networking for the whole backend.
- Put SearXNG on an internal network, not published; only the backend’s research adapter should reach it.
- Put voice behind the backend or remove it from the MVP.
- Store Postgres data and backups on `/data`.
- Add healthchecks: backend readiness checks DB and Ollama; Postgres `pg_isready`; Caddy HTTP probe.
- Set memory limits after measurement, not guessed numbers.
- Pin image digests and run `docker compose config` in CI.

### 5.3 Deployment target still unknown

The appropriate security and backup design depends on whether this is local-only, private LAN, single VPS, or public internet. Phase 0 cannot finalize auth/TLS/backup requirements without that decision.

## 6. Resource risks (updated 2026-10-24)

| ID | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| HW-01 | OOM/swap thrash when Ollama + Postgres run together | **Medium** (smaller model, swap saturated but Langfuse/Sentinel main consumers) | Service unavailability | Use `qwen3:0.6b` (522 MB); measure MyFarmAI-only profile; cap concurrency |
| HW-02 | `/` fills during Docker build | **LOW** (74 GB free) | Build failure | Ample headroom; optional Docker root move |
| HW-03 | Model/DB data lost because it is only on one disk | Medium | Data loss | Backups on `/data` + off-host copy; verify restore (G5 approved) |
| HW-04 | Voice model re-download | **N/A** (voice contained) | — | — |
| HW-05 | Unbounded logs fill `/data` | Medium | Disk exhaustion | Log rotation, retention, disk alerts |
| HW-06 | Postgres default memory settings too high for 7 GB | Medium | Memory pressure | Tune `shared_buffers`, `work_mem`, `max_connections` |
| HW-07 | Running many unused models consumes 44 GB | Low-Medium | Disk pressure | Review model inventory with owner; do not delete without approval |
| HW-08 | Host is shared with unrelated projects | High | Noisy-neighbour failures | Define MyFarmAI resource budget; isolate during tests |

## 7. Measurement plan (Stage 1 complete)

**Stage 1 executed 2026-10-24:**

1. ✅ Baseline RAM/swap/disk recorded before starting MyFarmAI
2. ✅ Backend + Ollama with `qwen3:0.6b` started; idle/peak RSS recorded
3. ✅ `ollama ps`, GPU memory, RSS, first-token latency, and total latency measured for 3 representative prompts
4. ✅ All 56 backend tests pass (regression)
5. ✅ Full quality gate passes: `scripts/check.sh` → ruff, mypy, pytest all pass

**Next measurements (Phase 2+):**

6. Add PostgreSQL; record memory and query latency
7. Add SearXNG; record memory and query latency
8. Add Caddy; record TLS overhead
9. Run 1, 2, and 4 concurrent chats; observe queueing, OOM, and swap
10. Set limits from measurements, then repeat

**Do not pull models, build images, start/stop services, or change mounts without approval.**
