# External Integration and Cost Audit

**Phase:** 0 — read-only  
**Date:** 2026-10-21  
**Rule:** MyFarmAI must not require paid AI APIs, paid inference, paid search, mandatory paid SaaS, or proprietary hosted services for core functionality.  
**Related:** [`DEPENDENCY_INVENTORY.md`](DEPENDENCY_INVENTORY.md), [`SECURITY_AND_PRIVACY_AUDIT.md`](SECURITY_AND_PRIVACY_AUDIT.md)

---

## 1. Method

Inspected source, schemas, environment templates, Dockerfiles, Compose, dependency declarations, infrastructure configuration, client code, and project documentation. No application code was executed to observe network traffic. No paid API, account, or external service was called. External terms and licence pages were read only.

**Important distinction:** a package may contain optional paid features without making the project paid. The classifications below refer to the current MyFarmAI usage, not every capability of the upstream product.

## 2. Integration register

| ID | Name | Evidence | Purpose | Network behaviour | Credentials | Cost exposure | Licence / terms | Data exposure | MVP status | Recommendation |
|---|---|---|---|---|---|---|---|---|---|---|
| INT-01 | **Open-Meteo** | `backend/app/core/config.py:52-64`; `backend/app/services/weather.py:37-157`; `backend/app/api/v1/weather.py` | Weather and 7-day forecast | External HTTPS from backend to `api.open-meteo.com` | None (no API key) | **Free tier is non-commercial only**; commercial use requires a paid subscription/key. Free limits: 10,000/day, 5,000/hour, 600/minute. Confirmed 2026-10-21 at <https://open-meteo.com/en/pricing> and <https://open-meteo.com/en/terms> | Free tier: non-commercial, CC-BY 4.0 data, attribution required. Commercial: paid plan. | Latitude, longitude, IP address, request timing. No account/user identifier. | Required for current weather feature; **commercial blocker** | **Investigate/replace for commercial use.** Keep for non-commercial prototype only, with attribution and caching. Do not make it mandatory for a commercial deployment without a licence or a suitable alternative. |
| INT-02 | **Ollama** | `backend/app/services/ollama.py`; `backend/app/core/config.py:10-22`; `.env.example`; `docker-compose.yml` (`network_mode: host`) | Local LLM inference | Local HTTP to `127.0.0.1:11434` (host network for backend) | None | Free; no paid inference | MIT (official repository, verified 2026-10-21) | Full prompt, conversation history, crop/location context, model output. Data stays on host. | Required | **Keep.** Add provider-independent gateway, timeouts, concurrency limits, readiness checks. |
| INT-03 | **`qwen3:4b` model** | `backend/app/core/config.py:15-18`; `ollama show qwen3:4b` | Chat model | Local only after model download | None | Free | Apache-2.0 (HuggingFace model card, verified 2026-10-21) | Prompts/outputs local | Required candidate | **Keep, subject to benchmark.** 2.5 GB Q4 model exceeds 2 GiB VRAM; expect partial CPU offload. Evaluate a smaller model if latency/RAM targets fail. |
| INT-04 | **HuggingFace Hub** | `ai/voice/main.py:3-9`; `ai/voice/Dockerfile`; running container cache `/root/.cache/huggingface` (464 MB) | Download `faster-whisper-small` on first use | External HTTPS to `huggingface.co` | None for public model | Free | Model/cache terms: review model card and HF terms; `faster-whisper` MIT | No user audio is sent; only model download metadata. | Optional voice | **Remove runtime dependency**: pre-download/pin model, or mount persistent cache. Do not rely on HF availability at request time. |
| INT-05 | **faster-whisper / Whisper small** | `ai/voice/main.py`; `ai/voice/requirements.txt` | Local speech-to-text, Hindi | Local inference after model download | None | Free | `faster-whisper` MIT (verified); Whisper model licence to be confirmed from the model card | Audio recording, transcript. Audio stays in container; temp file deleted. | Optional | **Keep only if voice is in MVP**; secure endpoint and pre-bake model. |
| INT-06 | **SearXNG** | `infra/searxng/config/settings.yml`; running container `myfarmai-searxng` on `127.0.0.1:8890`; no backend client | Self-hosted metasearch for future research | Local HTTP to SearXNG; SearXNG makes outbound requests to configured search engines when queried | No API key; hardcoded server secret in config | Free software; no paid search API | AGPL-3.0 (official repository, verified 2026-10-21). Individual engine terms and robots policies must be reviewed. | Future search queries, fetched URLs, page content. Not currently sent by MyFarmAI code. | Deferred (Phase 6) | **Keep self-hosted but not connected yet.** Pin image, move secret to environment, review AGPL and per-engine terms, add SSRF-safe fetcher. |
| INT-07 | **Voice service** | `ai/voice/main.py`; `docker-compose.yml` | Speech-to-text HTTP service | Local HTTP on port 8001; published on `0.0.0.0` | None | Free | Project code; dependencies as above | Audio upload, transcript. | Optional | **Secure or defer.** No auth, size/type limit, or rate limit; root container. |
| INT-08 | **Docker Hub / container registries** | `backend/Dockerfile:1`; `ai/voice/Dockerfile:1`; `docker-compose.yml`; running `searxng/searxng:latest` | Base images and service images | External pulls at build/run time | Docker Hub account not required for public images (rate limits may apply) | Free tier; Docker Hub rate limits possible | Image-specific licences; base Python PSF-2.0, SearXNG AGPL-3.0 | No user data in pulls | Required | Pin digests; document registry/rate-limit plan. |
| INT-09 | **Web client → backend** | `web/src/lib/api/client.ts`; `web/next.config.js` | Browser API access | Same-origin rewrite or direct `NEXT_PUBLIC_API_BASE_URL` | None | Free | Project code | Messages, coordinates, resource queries, request IDs. | Required | Keep; production requires HTTPS and correct CORS. |
| INT-10 | **Android client → backend** | `android/src/lib/api/client.ts`; `android/src/config/api.ts` | Mobile API access | **Broken:** relative `fetch(endpoint)`; base URL unused | None | Free | Project code | Messages, coordinates, language, location. | Required | Fix absolute base URL before any Android integration testing. |
| INT-11 | **OpenCode MCP servers (developer tooling)** | `opencode.json` | AI coding assistant integrations | External HTTPS for Context7, grep.app, Sentry, Atlassian; Linear/Axiom/Redis/Postgres via env placeholders | `LINEAR_API_KEY`, `AXIOM_TOKEN`, `REDIS_URL`, `POSTGRES_URL` are environment placeholders in the inspected config (no literal secret observed) | Sentry/Atlassian/Linear/Axiom are commercial SaaS; usage is optional developer tooling, not MyFarmAI runtime | Provider terms apply | Repository context/code may be sent to these tools when used by developers. Not part of the application. | Not runtime | **Out of runtime scope.** Do not add any of these as application dependencies. Review developer data-sharing policy separately. |
| INT-12 | **Graphify optional semantic extraction** | `maintenance-report-20261021-103253.md` (“set `GEMINI_API_KEY` or `GOOGLE_API_KEY`”) | Optional code-graph labelling | External Google API if enabled | Optional `GEMINI_API_KEY` / `GOOGLE_API_KEY` | Google Gemini may be paid/limited | Google terms | Source code snippets if enabled | Developer tooling only | **Do not enable for Phase 1.** Graphify’s AST extraction works without it. |
| INT-13 | **Langfuse stack (observed)** | `docker ps`: `langfuse-*` containers | Unrelated self-hosted observability stack on host | Local containers | Not inspected | Self-hosted; resource cost only | Langfuse licence not reviewed (not a MyFarmAI dependency) | Not used by MyFarmAI | Unrelated | **Do not couple.** It contributes to host RAM/disk pressure. |
| INT-14 | **Sentinel stack (observed)** | `docker ps`: `sentinel-*` containers | Unrelated project on host | Local containers | Not inspected | Unknown | Unknown | Not used by MyFarmAI | Unrelated | **Do not couple.** It contributes to host RAM/disk pressure. |
| INT-15 | **Open-Meteo self-hosting (option)** | Not implemented | Potential commercial-safe weather path | Would be local/self-hosted | None | Free software; data-source licences vary | Open-Meteo server is AGPL-3.0 (repository verified); underlying data licences vary | Coordinates stay local if self-hosted | Alternative | **Investigate**, including data licences and operational cost, before adoption. |
| INT-16 | **IMD / India public weather data (option)** | Not implemented; static link only (`backend/app/services/resources.py:54-58`) | Potential official weather source | Unknown | Unknown | Unknown | **Not verified** | Unknown | Alternative | **Investigate terms and API availability**; do not assume government data is unrestricted. |

## 3. Credentials and secret references

| Location | Category | Status | Action |
|---|---|---|---|
| `infra/searxng/config/settings.yml:7` | Hardcoded SearXNG `server.secret_key` (64-hex value) | **Verified secret in a non-ignored file** | Rotate; move to `SEARXNG_SECRET`/secret manager; remove from file; review git history before commit. Do not reproduce the value. |
| `infra/searxng/.env:1` | SearXNG secret | File is git-ignored and mode `600` | Keep out of Git; rotate together with the config value. |
| `/data/MyFarmAI/.env` | Local runtime configuration | Git-ignored; mode `664` (group/world readable) | Restrict to `600`; confirm no secrets; document production secret management. |
| `opencode.json` | Linear/Axiom/etc. placeholders | Values are environment placeholders in inspected config | Not application credentials; keep developer tooling scoped. |
| `backend/.env` | Not present | — | Compose mounts root `.env`; document this. |
| `web/.env.local` | Public API URL only | Git-ignored | No secret observed. |
| `android/.env.example` | Public API URL placeholder | Unused by code | Wire or remove. |

**No runtime API keys for paid services were found in the backend, voice service, or clients.** The only confirmed hardcoded secret is the SearXNG server secret.

## 4. Cost exposure summary

| Class | Integrations | Conclusion |
|---|---|---|
| Confirmed free / local | Ollama, `qwen3:4b`, faster-whisper, SearXNG software, PostgreSQL (proposed), SQLAlchemy/Alembic, Caddy, Docker Compose | Compatible with the zero-paid-API rule. |
| Confirmed conditional / paid at production scale | **Open-Meteo** free tier is non-commercial; commercial use requires a paid subscription. Docker Hub rate limits may affect CI/builds. | **Open blocker for commercial weather.** Needs a licence, replacement, or self-hosted data path. |
| Optional commercial developer tooling | Sentry, Atlassian, Linear, Axiom MCPs; optional Gemini labelling | Not required by the application. Do not make them runtime dependencies. |
| Unknown | IMD/public data APIs; individual SearXNG engine terms; some transitive package licences | Must be reviewed before production use. |

## 5. Data exposure summary

| Data | Destination | Current control |
|---|---|---|
| Chat prompts and history | Local Ollama process | Local only; no auth; persisted indefinitely in SQLite |
| Crop/location/language context | Local Ollama + local SQLite | Local only; potential indirect PII |
| Coordinates | Open-Meteo (external) | Sent on every weather request; no cache; no user identifier |
| Audio and transcript | Local voice container | Local only; unauthenticated endpoint; temp file deleted |
| Search queries/page content | SearXNG and upstream engines (future) | Not currently used; requires SSRF/terms controls |
| Request metadata/IP | Backend logs and in-memory rate limiter | IP logged; logs are plain text; no retention policy |
| Source code/context | Optional developer MCPs | Developer tooling only; review separately |

## 6. Findings and recommendations

| ID | Finding | Severity | Recommendation |
|---|---|---|---|
| INT-F01 | Open-Meteo free tier is explicitly non-commercial | High (commercial) | Keep for non-commercial prototype only. Before commercial launch: buy a commercial licence (conflicts with zero-paid requirement), self-host with licensed data, or use a suitably licensed provider. Record the decision. |
| INT-F02 | No weather caching despite `weather_cache_ttl_seconds` setting | Medium | Implement a bounded cache and attribution; reduces rate-limit and cost exposure. |
| INT-F03 | SearXNG secret is hardcoded | High | Rotate, externalise, and add secret scanning to CI. |
| INT-F04 | Voice model downloads from HuggingFace at runtime and is not persisted | Medium | Pre-bake/pin the model; mount cache; remove runtime HF dependency. |
| INT-F05 | Voice endpoint is unauthenticated and externally published | High | Bind to internal network, require auth, enforce size/type/rate limits, run non-root. |
| INT-F06 | No outbound allowlist or egress policy | Medium | Document required egress (Open-Meteo, model downloads during build only, search engines in Phase 6); block everything else in production. |
| INT-F07 | Android does not call the backend correctly | High (functional) | Use `API_BASE_URL + endpoint`; add a contract test. |
| INT-F08 | Developer MCP/SaaS tools could be confused with runtime dependencies | Low | Document the boundary; keep `opencode.json` out of deployment. |

## 7. External references

All accessed **2026-10-21**:

- Open-Meteo pricing: <https://open-meteo.com/en/pricing>
- Open-Meteo terms: <https://open-meteo.com/en/terms>
- SearXNG repository/licence: <https://github.com/searxng/searxng>
- Ollama repository/licence: <https://github.com/ollama/ollama>
- Qwen3-4B model card: <https://huggingface.co/Qwen/Qwen3-4B>
- faster-whisper repository/licence: <https://github.com/SYSTRAN/faster-whisper>
- PostgreSQL licence: <https://www.postgresql.org/about/licence/>

Claims not verified online are marked **Unknown** or **not verified** above. No paid request was made.
