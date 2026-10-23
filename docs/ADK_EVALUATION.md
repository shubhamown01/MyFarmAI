# Google ADK Evaluation for MyFarmAI

## Executive Summary

**Recommendation: Defer ADK adoption.** The current FastAPI backend with direct Ollama integration meets Phase 0–4 requirements. ADK adds complexity without demonstrated benefit for the current architecture. Re-evaluate at Phase 6 (Research Engine) if multi-agent orchestration becomes necessary.

## Current Architecture (Phase 0–3 Complete)

```
Next.js Web ←→ FastAPI (/api/v1) ←→ Ollama (qwen3:4b)
                    ↓
              SQLite → PostgreSQL (Phase 2)
                    ↓
              Open-Meteo Weather
                    ↓
              Static Resources Catalogue
```

- Single chat endpoint: `POST /api/v1/chat`
- System prompt construction in `backend/app/services/chat.py`
- Conversation persistence in SQLite
- No authentication yet (Phase 3)
- No vector search, no RAG, no web research (Phase 6)

## What ADK Provides

| Capability | ADK Offering | MyFarmAI Current State |
|------------|--------------|------------------------|
| Multi-agent orchestration | `LlmAgent`, `SequentialAgent`, `ParallelAgent` | Single chat service |
| Tool calling | Built-in function calling, MCP integration | None (direct Ollama chat) |
| Session/memory | `InMemorySessionService`, `VertexAiSessionService` | SQLite conversations |
| Evaluation | `AgentEvaluator`, CI/CD integration | Pytest only |
| Deployment | Cloud Run, Agent Engine, GKE | Docker Compose, self-hosted |
| Tracing/observability | Cloud Trace, Vertex AI | Structured logging only |

## Evaluation Criteria

### 1. Does MyFarmAI Need Runtime Multi-Agent Orchestration?

**Current need: No.**
- Single chat flow: user message → system prompt + history → Ollama → response
- No tool use, no agent handoff, no parallel subtasks
- Agricultural context injected via system prompt (crop, location, language)

**Future need (Phase 6+): Maybe.**
- Research engine: search → extract → rank → cite → synthesize
- Could map to: `SearchAgent` → `ExtractionAgent` → `RankingAgent` → `SynthesisAgent`
- But deterministic code (pipeline) may be simpler and more auditable

### 2. Local Model Compatibility

**ADK + Ollama: Partial support.**
- ADK designed for Vertex AI / Gemini primarily
- LiteLLM bridge exists but adds dependency
- `qwen3:4b` tool calling capability: **untested** (Qwen3 supports tools but Ollama integration varies)
- Streaming: ADK expects specific chunk format; Ollama format differs

**Risk**: Investing in ADK only to find local model tool calling unreliable.

### 3. Provider Independence

**Requirement**: No mandatory paid APIs, no cloud-only services.

| ADK Component | Dependency | Verdict |
|---------------|------------|---------|
| Core orchestration | Pure Python | ✅ Local |
| `VertexAiSessionService` | Google Cloud | ❌ Avoid |
| `InMemorySessionService` | Local only | ✅ OK for dev |
| Cloud Trace | Google Cloud | ❌ Avoid |
| Agent Engine deployment | Google Cloud | ❌ Avoid |
| Evaluation framework | Local (LLM-as-judge) | ✅ Can use local judge |

**Conclusion**: Can use ADK core locally, but lose managed services. Must build own session store, tracing, deployment.

### 4. Security & Supply Chain

**ADK Status (2026-10-21)**:
- `google-adk` PyPI package: relatively new, frequent breaking changes
- Dependencies: `google-genai`, `pydantic`, `httpx`, `websockets`, etc.
- No known critical CVEs, but supply chain risk for new framework
- Must pin versions, run `pip-audit`, track advisories

**MyFarmAI Policy**: Lockfile (`uv.lock`), pin Docker digests, no unpinned deps. ADK adds ~15 transitive deps.

### 5. Integration with Existing Backend

**Option A: ADK as separate module**
```
backend/app/ai/agents/
  ├── __init__.py
  ├── router_agent.py      # Routes to crop/weather/research
  ├── crop_agent.py
  ├── research_agent.py
  └── citation_agent.py
```
- FastAPI calls `AgentRunner.run(agent, session, message)`
- Keeps `/api/v1/chat` contract stable
- Adds ADK as internal implementation detail

**Option B: Replace chat service with ADK**
- Higher risk, more rewriting
- Loses current working SQLite conversation logic

**Option C: No ADK — deterministic pipeline**
```
ResearchPipeline:
  1. search(searxng, query)
  2. extract(pages, max_chars)
  3. rank(sources, credibility)
  4. cite(evidence, format)
  5. synthesize(prompt + citations)
```
- Pure Python, testable, auditable
- No framework lock-in
- Easier to secure (no prompt injection via agent instructions)

## Proposed ADK Architecture (If Adopted Later)

If Phase 6 research complexity justifies it, isolate in:

```
backend/app/ai/agents/
├── agricultural_router.py      # LlmAgent: routes to specialist
├── crop_guidance_agent.py      # LlmAgent: crop Q&A with RAG
├── research_agent.py           # SequentialAgent: search→extract→rank→cite
├── evidence_verifier_agent.py  # LlmAgent: checks citations, hallucinations
└── response_composer_agent.py  # LlmAgent: formats final answer
```

**Guardrails required**:
- Deterministic router (keyword/intent classification) for simple cases
- Timeouts: 30s per agent, 120s total
- Bounded retries: max 2
- Tracing: OpenTelemetry to local collector
- Fallback: direct Ollama call if agent chain fails
- No shared memory across agents/sessions without auth
- Retrieved content never overrides system instructions
- Input/output validation on every agent boundary

## Decision Matrix

| Factor | Weight | Deterministic Pipeline | ADK Orchestration |
|--------|--------|------------------------|-------------------|
| Current Phase 0–4 fit | High | ✅ Excellent | ❌ Over-engineered |
| Phase 6 research complexity | Medium | ✅ Adequate | ✅ Good |
| Local model tool calling | High | N/A | ⚠️ Unverified |
| Provider independence | High | ✅ Full | ⚠️ Partial (no managed svcs) |
| Security auditability | High | ✅ High | ⚠️ Lower (prompt-driven) |
| Team expertise | Medium | ✅ High (Python) | ⚠️ Learning curve |
| Maintenance burden | Medium | ✅ Low | ⚠️ Higher (framework churn) |
| Evaluation framework | Low | Build own | ✅ Built-in |

## Prerequisites Before ADK Adoption

If re-evaluating at Phase 6, require:

1. **Local tool-calling benchmark**: `qwen3:4b` + Ollama + ADK tool calling works reliably
2. **Security review**: Prompt injection testing on agent instructions
3. **Session store**: PostgreSQL-backed session service (not in-memory)
4. **Tracing**: OpenTelemetry integration working locally
5. **Fallback tested**: Agent chain failure → direct Ollama works
6. **Cost/benefit documented**: Measured complexity reduction vs. framework cost

## Current Recommendation

**Do not install ADK now.** 

Continue with:
- Deterministic Python pipelines for research (Phase 6)
- Direct Ollama integration with provider-independent gateway interface
- SQLite → PostgreSQL migration (Phase 2)
- Authentication/authorization (Phase 3)

**Re-evaluate trigger**: When research engine requires >3 sequential LLM calls with branching logic that becomes unmaintainable as pure Python.

## References

- [Google ADK Python](https://github.com/google/adk-python)
- [ADK Documentation](https://adk.dev/)
- [LiteLLM Ollama Integration](https://docs.litellm.ai/docs/providers/ollama)
- MyFarmAI Backend Roadmap: `docs/roadmaps/MyFarmAI_Backend_Roadmap.md`
- Phase 0 Security Audit: `docs/roadmaps/phase-00/SECURITY_AND_PRIVACY_AUDIT.md`