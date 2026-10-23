# Hardware, Storage, and Deployment Assessment

**Phase:** 0 — read-only  
**Date:** 2026-10-21  
**Constraint source:** user-reported development machine (≈7 GB RAM, MX250 2 GB VRAM, Ubuntu, HDD at `/data`, limited SSD). These were re-checked with read-only commands; they are not assumed.  
**Related:** [`TARGET_BACKEND_ARCHITECTURE.md`](TARGET_BACKEND_ARCHITECTURE.md), [`ARCHITECTURE_DECISIONS.md`](ARCHITECTURE_DECISIONS.md)

---

## 1. Verified host state

| Item | Observed value | Evidence | Classification |
|---|---|---|---|
| OS | Ubuntu 26.04.1 LTS | `/etc/os-release` | Verified |
| Kernel | `7.0.0-38-generic` | `uname -r` | Verified |
| CPU/RAM | 7.0 GiB total; 4.7 GiB used; 2.3 GiB available | `free -h` | Verified at audit time |
| Swap | 4.0 GiB total; 3.6 GiB used; 373 MiB free | `free -h` | Verified at audit time |
| GPU | NVIDIA GeForce MX250, 2048 MiB VRAM, 2 MiB used | `nvidia-smi` | Verified at audit time |
| GPU driver | 580.178.04 | `nvidia-smi` | Verified |
| Root disk | `/dev/nvme0n1p5`, 126 GB, 115 GB used, **5.3 GB free (96%)** | `df -h /` | Verified |
| Data disk | `/dev/sda2`, 274 GB, 85 GB used, **176 GB free (33%)** | `df -h /data` | Verified |
| Docker version | 29.9.1, overlayfs | `docker info` | Verified |
| Docker root | `/var/lib/docker` on `/` | `docker info` | Verified |
| Docker images | 25 images, 16.39 GB, 7.25 GB reclaimable | `docker system df` | Verified |
| Docker volumes | 9 volumes, 23.84 GB | `docker system df` | Verified |
| Docker build cache | 34 entries, 1.66 GB, 222 MB reclaimable | `docker system df` | Verified |
| Running containers | 17, including unrelated Langfuse/Sentinel stacks, `myfarmai-voice`, `myfarmai-searxng` | `docker ps` | Verified |
| Ollama | `/usr/local/bin/ollama`, listening on `127.0.0.1:11434` | `ss`, `ollama list` | Verified |
| Ollama model store | `/data/SentinelAI/ollama/models`, 44 GB | systemd unit, `du` | Verified |
| Configured model | `qwen3:4b`, Q4_K_M, 4.0B params, 2.5 GB, context 262144 | `ollama show` | Verified |
| Other models | `qwen3-embedding:0.6b` (639 MB), `gemma` (5.0 GB), `phi` (1.6 GB), `mistral` (4.4 GB), `deepseek-coder` (776 MB), `deepseek-r1` (5.2 GB), `qwen3-embedding:latest` (4.7 GB), `qwen3-vl` (6.1 GB) | `ollama list` | Verified |
| Voice service | Running, 0.0.0.0:8001, root user, no healthcheck, ~20 MB idle RSS (model lazy) | `docker inspect`, `docker stats` | Verified |
| SearXNG | Running, 127.0.0.1:8890, 2.3 MB idle RSS, memory limit 768 MiB | `docker inspect`, `docker stats` | Verified |
| Backend | Not running at audit time; no listener on 8000 | `ss`, `docker ps` | Verified |
| Python | System/local 3.14.4; container 3.12 | interpreter, Dockerfile | Verified |

**Important:** host usage is a snapshot. Other projects’ containers are consuming most RAM and Docker disk. Estimates below are ranges, not guarantees.

## 2. Constraints and implications

### 2.1 RAM

- 7.0 GiB total is below the sum of a typical Postgres + Ollama + SearXNG + voice + backend stack.
- Only 2.3 GiB was available, and swap was already 3.6 GiB used. Starting a 2.5 GB model plus Postgres and SearXNG is likely to cause heavy swapping and latency.
- Unrelated Langfuse ClickHouse (~720 MB), Langfuse worker (~451 MB), Postgres, MinIO, Redis, and Sentinel containers consume RAM that MyFarmAI cannot rely on.
- **Recommendation:** measure a MyFarmAI-only profile; stop unrelated stacks during AI development only with owner approval; otherwise use a smaller model or an on-demand inference workflow.

### 2.2 VRAM

- 2 GiB VRAM cannot fully hold `qwen3:4b` Q4_K_M (2.5 GB weights alone).
- Ollama will offload some layers to CPU/system RAM. Expect lower throughput and higher RAM use. The exact split depends on Ollama version, context size, batch, and KV cache.
- `qwen3-embedding:0.6b` (639 MB) is a much better fit if embeddings are needed later.
- `gemma` (5 GB), `mistral` (4.4 GB), `deepseek-r1` (5.2 GB), `qwen3-vl` (6.1 GB), and `qwen3-embedding:latest` (4.7 GB) do not fit VRAM and should not be run concurrently.
- **Do not assume `qwen3:4b` meets latency targets.** Benchmark prompt sizes representative of farmer questions, with the intended context window.

### 2.3 Disk

- `/` has 5.3 GB free. Docker’s root is on `/`, with 16.39 GB of images and 23.84 GB of volumes. A new backend image, Postgres image, Caddy image, and build cache could consume the remaining space.
- `/data` has 176 GB free and already holds 44 GB of Ollama models, the repo, and SQLite data.
- Docker volumes are on `/`, not `/data`. This is the largest storage risk.
- **Options (require approval):**
  1. Move Docker’s data-root to `/data/docker` (daemon restart required).
  2. Prune unused images/build cache (7.25 GB + 222 MB reclaimable) after confirming no project needs them.
  3. Keep MyFarmAI images small and store Postgres data/backups on `/data` via bind mounts.
- Do not delete models, volumes, or images during Phase 0.

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

## 4. Ollama feasibility

| Question | Assessment |
|---|---|
| Can `qwen3:4b` run at all? | Likely yes with CPU offload, if enough system RAM is free and swap is available. Not verified by a benchmark in Phase 0. |
| Can it fit fully in 2 GiB VRAM? | **No.** Weights alone are 2.5 GB at Q4_K_M. Partial offload is expected. |
| Will it meet interactive latency? | Unknown. Must measure time-to-first-token and total response time for 1–2k-token prompts. CPU offload on this host may be slow. |
| Can multiple concurrent chats run? | Very unlikely without a queue. Add a concurrency limit and measure. |
| Alternatives | A smaller model already present (`phi`, 1.6 GB) or a future smaller Qwen model; quality trade-offs must be evaluated on agriculture questions. Do not pull models in Phase 0. |
| Embeddings | `qwen3-embedding:0.6b` fits better; defer until retrieval is designed. |

## 5. Deployment assessment

### 5.1 Current Compose

| Issue | Impact |
|---|---|
| `network_mode: host` for backend | Removes network isolation; exposes port 8000 on all host interfaces when running; makes proxy/network policy harder. |
| Voice publishes `0.0.0.0:8001` | Unauthenticated endpoint reachable from the LAN. |
| No healthchecks | `depends_on` only waits for container start; restart loops are invisible. |
| No resource limits | A runaway chat/voice request can exhaust host RAM. |
| Root containers | Higher impact if compromised. |
| Floating images | Non-reproducible builds. |
| Bind-mounted `.env` | Simple for dev; production should use secrets, not a file in the repo tree. |
| SQLite bind mount | Single-host only; no HA; backup must be external. |
| No reverse proxy/TLS | Plain HTTP; no HSTS/security headers. |

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

## 6. Resource risks

| ID | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| HW-01 | OOM/swap thrash when Ollama + Postgres + voice run together | High on current host | Service unavailability, disk I/O storm | Measure; cap concurrency; stop unrelated stacks; use a smaller model. |
| HW-02 | `/` fills during Docker build | High (5.3 GB free) | Build failure; host instability | Move Docker root to `/data` or prune after approval; keep images small. |
| HW-03 | Model/DB data lost because it is only on one disk | Medium | Data loss | Backups on `/data` + off-host copy; verify restore. |
| HW-04 | Voice model re-download on container recreate | High | 464 MB download, startup delay, HF dependency | Pre-bake model or mount cache. |
| HW-05 | Unbounded logs fill `/data` | Medium | Disk exhaustion | Log rotation, retention, disk alerts. |
| HW-06 | Postgres default memory settings too high for 7 GB | Medium | Memory pressure | Tune `shared_buffers`, `work_mem`, `max_connections`. |
| HW-07 | Running many unused models consumes 44 GB | Low-Medium | Disk pressure | Review model inventory with owner; do not delete without approval. |
| HW-08 | Host is shared with unrelated projects | High | Noisy-neighbour failures | Define a MyFarmAI resource budget and isolate during tests. |

## 7. Measurement plan (not executed)

When approved, measure on this host with a controlled profile:

1. Record baseline RAM/swap/disk before starting MyFarmAI.
2. Start backend + Postgres + Caddy only; record idle and peak RSS for 10 minutes.
3. Start Ollama with one model; record `ollama ps`, GPU memory, RSS, first-token latency, and total latency for 5 representative prompts at the intended context size.
4. Add SearXNG; record memory and query latency.
5. Add voice; record first-request model load time and peak RSS.
6. Run 1, 2, and 4 concurrent chats; observe queueing, OOM, and swap.
7. Set limits from measurements, then repeat.

Do not pull models, build images, start/stop services, or change mounts during Phase 0.
