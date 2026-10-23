# Dependency and Technology Inventory

**Phase:** 0 — read-only  
**Date:** 2026-10-21  
**Scope:** backend runtime, backend test/tooling, voice service, deployment infrastructure, and client/backend-relevant packages.  
**Related:** [`INTEGRATION_AND_COST_AUDIT.md`](INTEGRATION_AND_COST_AUDIT.md), [`SECURITY_AND_PRIVACY_AUDIT.md`](SECURITY_AND_PRIVACY_AUDIT.md)

---

## 1. Method and limitations

- Declared dependencies were read from `backend/requirements.txt` and `ai/voice/requirements.txt`. **No version is pinned in either file.**
- Installed versions were read from `backend/.venv` (Python 3.14.4) and the running `myfarmai-voice` container.
- Licences were checked from installed package metadata (`*.dist-info/METADATA`, `License-Expression`/classifiers), PyPI JSON metadata, and official repository licences where metadata was incomplete. Access date for online sources: **2026-10-21**.
- Licences of transitive dependencies were not exhaustively enumerated. The package-lock files were not audited package-by-package.
- No dependency was installed, removed, upgraded, or modified.

## 2. Backend runtime dependencies

| Package | Declared | Installed | Used where | Purpose | Licence | OSS | Network | Key/account/paid | MVP | Concern / action |
|---|---|---|---|---|---|---|---|---|---|---|
| `fastapi` | unpinned | 0.143.5 | `app/main.py`, `app/api/v1/*` | HTTP API, validation integration, OpenAPI | MIT (METADATA) | Yes | None directly | No | Required | Keep. Pin in lockfile. |
| `uvicorn[standard]` | unpinned | 0.54.0 | Docker CMD | ASGI server | BSD-3-Clause (METADATA) | Yes | Listens on socket | No | Required | Keep. Pin; run behind proxy. |
| `httpx` | unpinned | 0.28.1 | `services/ollama.py`, `services/weather.py` | Async HTTP client | BSD-3-Clause (METADATA) | Yes | External calls at runtime | No | Required | Keep. Centralise timeouts/limits. |
| `python-multipart` | unpinned | 0.0.32 | Backend requirements; not used by backend routes | Form/multipart parsing | Apache-2.0 (METADATA) | Yes | None | No | Unused in backend | Remove later after confirming no form endpoints; voice needs it. |
| `pydantic-settings` | unpinned | 2.16.0 | `app/core/config.py` | `.env`/environment settings | MIT (METADATA) | Yes | Reads local env | No | Required | Keep. Add validation tests. |
| `aiosqlite` | unpinned | 0.22.1 | `app/db/*` | Async SQLite driver | MIT (METADATA) | Yes | Local file only | No | Transitional | Keep for tests/local until PostgreSQL; then remove or test-only. |
| `pydantic` | transitive of FastAPI/settings | 2.14.1 | Schemas/config | Validation | MIT (METADATA) | Yes | None | No | Required | Keep. |
| `starlette` | transitive of FastAPI | 1.8.0 | Framework internals | ASGI toolkit | BSD-3-Clause (METADATA) | Yes | None | No | Required | Keep; note FastAPI/Starlette major-version coupling. |
| `anyio` | transitive | 4.15.1 | Async runtime | Async compatibility | MIT (METADATA) | Yes | None | No | Required | Keep. |
| `h11` | transitive | 0.16.0 | HTTP parsing | HTTP/1.1 protocol | MIT (METADATA) | Yes | None | No | Required | Keep. |
| `httpcore` | transitive of httpx | 1.0.9 | HTTP transport | Low-level HTTP | BSD-3-Clause (METADATA) | Yes | External when used | No | Required | Keep. |
| `httptools` | transitive of uvicorn[standard] | 0.9.0 | Server parsing | Fast HTTP parser | MIT (METADATA) | Yes | None | No | Required | Keep. |
| `uvloop` | transitive of uvicorn[standard] | 0.23.0 | Event loop | Performance | MIT / Apache-2.0 dual (METADATA) | Yes | None | No | Required on Linux | Keep; verify platform support. |
| `watchfiles` | transitive of uvicorn[standard] | 1.3.0 | Reload | File watching | MIT (PyPI) | Yes | None | No | Dev convenience | Keep; not needed in production image. |
| `websockets` | transitive of uvicorn[standard] | 17.2.0 | Server optional | WebSocket support | BSD-3-Clause (PyPI) | Yes | None | No | Unused | Keep only if needed; otherwise use `uvicorn` without extras. |
| `python-dotenv` | transitive of pydantic-settings | 1.2.4 | Env loading | `.env` parser | BSD-3-Clause (PyPI) | Yes | Local file | No | Required | Keep. |
| `idna` | transitive | 3.20 | URL handling | IDNA | BSD-3-Clause (PyPI) | Yes | None | No | Required | Keep. |
| `certifi` | transitive of httpx | 2026.7.22 | TLS trust store | CA bundle | MPL-2.0 (PyPI) | Yes | None | No | Required | Keep; MPL obligations are file-level. |
| `typing_extensions`, `typing-inspection`, `annotated-types`, `annotated-doc` | transitive | see venv | Typing | Runtime typing | MIT/PSF-style (metadata varies) | Yes | None | No | Required | Pin transitively via lockfile. |

## 3. Backend test and quality dependencies

| Package | Declared | Installed | Purpose | Licence | MVP | Concern / action |
|---|---|---|---|---|---|---|
| `pytest` | unpinned | 9.1.1 | Test runner | MIT (METADATA) | Required | Keep; pin. |
| `pytest-asyncio` | unpinned | 1.4.0 | Async tests | Apache-2.0 (METADATA) | Required | Keep; current fixtures use a deprecated custom event loop. |
| `pytest-cov` | unpinned | 7.1.0 | Coverage | MIT (METADATA) | Useful | Keep; add threshold after isolation is fixed. |
| `coverage` | transitive | 7.16.2 | Coverage engine | Apache-2.0 (METADATA) | Useful | Keep. |
| `mypy` | declared as local tool, not in requirements | 2.4.0 | Static typing | MIT (METADATA) | Required | Fix `mypy.ini` TOML-in-INI warning and 3.12 target mismatch. |
| `ruff` | declared as local tool, not in requirements | 0.17.1 | Lint/format | MIT (METADATA) | Required | Keep. |
| `httpx` (duplicate) | listed twice in requirements | 0.28.1 | Test client/async tests | BSD-3-Clause | Required | De-duplicate. |

**Note:** `pytest`, `pytest-asyncio`, `pytest-cov`, `mypy`, and `ruff` are included in the production-installed environment because the Dockerfile installs the single `requirements.txt`. Test tooling therefore ships in the runtime image. Split runtime and dev dependencies in Phase 1.

## 4. Voice service dependencies

| Package | Declared | Installed (container) | Purpose | Licence | OSS | Network | Paid | MVP | Concern / action |
|---|---|---|---|---|---|---|---|---|---|
| `faster-whisper` | unpinned | 1.2.1 | Whisper inference | MIT (PyPI/repo) | Yes | Downloads model on first use | No | Optional | Keep only if voice is in scope; pre-bake model, pin version. |
| `ctranslate2` | transitive | 4.8.3 | Inference backend | MIT (PyPI) | Yes | None | No | Optional | Keep; CPU int8. |
| `onnxruntime` | transitive | 1.31.0 | Runtime | MIT (PyPI) | Yes | None | No | Optional | Keep; large dependency. |
| `tokenizers` | transitive | 0.23.3 | Tokenisation | Apache-2.0 (PyPI) | Yes | None | No | Optional | Keep. |
| `huggingface_hub` | transitive | 2.2.0 | Model download | Apache-2.0 (PyPI) | Yes | `huggingface.co` on first use | No (public model) | Optional | Pin model revision; pre-download; no runtime dependency on HF. |
| `av` (PyAV) | transitive | 19.0.1 | Audio decode | BSD-3-Clause (repo) | Yes | None | No | Optional | Keep; ffmpeg/libsndfile in image. |
| `numpy` | transitive | 2.5.4 | Numerics | BSD-3-Clause (NumPy) | Yes | None | No | Optional | Keep. |
| `fastapi`, `uvicorn`, `python-multipart` | unpinned | 0.143.3 / 0.54.0 / 0.0.32 | HTTP API/upload | MIT / BSD-3 / Apache-2.0 | Yes | Listens on 8001 | No | Optional | Harden endpoint; pin. |
| Whisper `small` model | hardcoded | cached 464 MB in container | Speech-to-text | Model card: MIT (OpenAI Whisper) — verify before distribution | Yes | Download from HF | No | Optional | Pre-bake into image/volume; record model revision. |

The voice container has **no volume** for `/root/.cache/huggingface`; recreating the container discards the 464 MB model cache and triggers a new download. This is a reproducibility and availability risk.

## 5. Infrastructure and runtime components

| Component | Current version/evidence | Licence | Cost | Network / account | MVP | Action |
|---|---|---|---|---|---|---|
| Python container | `python:3.12-slim` (floating) | PSF-2.0 | Free | Docker Hub pull | Required | Pin digest; match local Python. |
| Ollama | `/usr/local/bin/ollama`, running on `127.0.0.1:11434` | MIT (official repo, verified 2026-10-21) | Free | Local only | Required | Keep; add health/readiness and resource limits. |
| `qwen3:4b` | Q4_K_M, 4.0B params, 2.5 GB, 262144 context | Apache-2.0 (HuggingFace model card, verified 2026-10-21) | Free | Local | Required candidate | Benchmark against 2 GiB VRAM; record model digest. |
| `qwen3-embedding:0.6b` | Q8_0, 639 MB | Apache-2.0 (same Qwen family; verify model card) | Free | Local | Deferred | Use only when embeddings are implemented. |
| Other Ollama models | `gemma`, `phi`, `mistral`, `deepseek-coder`, `deepseek-r1`, `qwen3-vl` | Varies per model | Free | Local | Unused | Do not use without licence review; reclaim only with owner approval. |
| PostgreSQL (proposed) | Not installed as a MyFarmAI service; `postgres:17` containers exist for unrelated projects | PostgreSQL Licence (verified) | Free | Local | Required for production | Add in Phase 2; pin image. |
| SQLAlchemy / Alembic (proposed) | Not installed | MIT (official repos) | Free | None | Required | Add in Phase 2. |
| asyncpg (proposed) | Not installed | Apache-2.0 (official repo) | Free | None | Recommended | Use if async SQLAlchemy is chosen. |
| psycopg 3 (proposed alternative) | Not installed | LGPL-3.0 (official repo) | Free | None | Alternative | Prefer asyncpg for simpler licence; psycopg is viable. |
| SearXNG | `searxng/searxng:latest`, running on `127.0.0.1:8890` | AGPL-3.0 (official repo, verified 2026-10-21) | Free | Outbound to search engines when queried | Deferred to Phase 6 | Keep self-hosted; pin digest; review AGPL and engine terms. |
| Caddy (proposed) | Not installed | Apache-2.0 (official repo) | Free | Public 80/443 | Recommended | Use for TLS/reverse proxy. |
| Valkey (proposed) | Not installed | BSD-3-Clause (official repo) | Free | Local | Deferred | Add only for measured background work. |
| Qdrant (proposed) | Not installed | Apache-2.0 (official repo) | Free | Local | Deferred | Add only after retrieval benchmarks. |
| Docker Compose | Docker 29.9.1 | Apache-2.0 (Docker Compose) | Free | Local | Required | Keep; harden services. |

## 6. Client dependencies (context, not fully audited)

| Client | Key packages | Licence posture | Concern |
|---|---|---|---|
| Web | Next.js 15.5.x, React 18.3, TanStack Query 5, Zustand 4, Tailwind 3.4 | Permissive (MIT/ISC/Apache-2.0) | `package-lock.json` present; npm audit not run. |
| Android | Expo 51, React Native 0.74, React Native Paper 5, Expo SecureStore | Permissive (MIT) | No lockfile observed; Android typecheck/lint failed in prior maintenance run. |

These are API consumers, not backend runtime dependencies. A full client licence/SBOM audit is outside Phase 0’s backend scope.

## 7. Dependency risks

| ID | Risk | Evidence | Impact | Recommendation |
|---|---|---|---|---|
| DEP-01 | No pinned versions or lockfile | Both `requirements*.txt` have no `==` | Builds are non-reproducible; a transitive update can break or compromise production | Adopt `pyproject.toml` + `uv.lock`; pin container digests. |
| DEP-02 | Python 3.14 local vs 3.12 container | `backend/.venv`, `backend/Dockerfile:1` | “Works locally” may fail in Docker and vice versa | Standardise on one minor version; recreate venv. |
| DEP-03 | Test tooling in production image | Dockerfile installs all requirements | Larger attack surface/image | Split runtime/dev dependency groups. |
| DEP-04 | Floating Docker tags | `python:3.12-slim`, `searxng/searxng:latest` | Silent upstream changes | Pin image digests and review updates. |
| DEP-05 | No dependency/licence scanning | No CI | Supply-chain and licence drift | Add `pip-audit`/OSV, image scanning, and a licence policy in CI. |
| DEP-06 | AGPL dependency (SearXNG) | `infra/searxng`, official licence | Network-use source obligations if modified | Legal review; keep unmodified or publish corresponding source. |
| DEP-07 | Runtime HuggingFace download | `ai/voice/Dockerfile`, cache in container | Availability/reproducibility; outbound dependency | Pre-download model at build time or mount a persistent cache. |
| DEP-08 | Unused backend `python-multipart` | `backend/requirements.txt` | Minor bloat | Remove after confirming no multipart routes. |
| DEP-09 | Duplicate `httpx` entry | `backend/requirements.txt` | Confusing resolution | De-duplicate. |
| DEP-10 | `mypy.ini` uses TOML table syntax in INI | `backend/mypy.ini:14+` | Overrides are not applied as intended | Convert to `pyproject.toml` or correct INI sections. |

## 8. Recommendation summary

**Keep now:** FastAPI, Pydantic v2, Pydantic Settings, Uvicorn, HTTPX, pytest, Ruff, mypy, Ollama, `qwen3:4b` (subject to benchmark), SQLite for tests only.

**Add in the appropriate phase:** `pyproject.toml` + `uv.lock`, PostgreSQL 17, SQLAlchemy 2, Alembic, asyncpg, Caddy, structured logging, CI scanners.

**Defer:** Valkey, background workers, Qdrant, embeddings, additional models, extra observability services.

**Replace or remove later:** unpinned `requirements.txt` as the source of truth; backend `python-multipart` if unused; runtime HuggingFace model download; Open-Meteo for commercial deployment (see integration audit).

No dependency changes were made.
