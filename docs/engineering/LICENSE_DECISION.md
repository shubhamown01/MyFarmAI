# MyFarmAI — Project License Decision

**Document ID:** MYFARMAI-LIC-001  
**Version:** 1.0  
**Date:** 2026-10-22  
**Status:** Proposed — Owner/Legal Decision Required  
**Gate:** G2 (Blocks P1-16)

---

## 1. Executive Summary

**Recommendation:** **Apache-2.0** for MyFarmAI project code.

**Rationale:** Permissive, compatible with all dependencies, provides patent protection, industry standard for open-source infrastructure projects. Accommodates SearXNG (AGPL-3.0) as unmodified dependency.

**Owner/Legal Decision Required:** Approve Apache-2.0, choose alternative (MIT, AGPL-3.0, other), or defer with date.

---

## 2. Dependency License Inventory

### Backend (Python) — Runtime Dependencies

| Package | Version | License | Classification |
|---------|---------|---------|----------------|
| fastapi | 0.115.0 | MIT | Permissive |
| uvicorn | 0.34.0 | BSD-3-Clause | Permissive |
| httpx | 0.28.1 | BSD-3-Clause | Permissive |
| python-multipart | 0.0.12 | Apache-2.0 | Permissive |
| pydantic-settings | 2.9.0 | MIT | Permissive |
| aiosqlite | 0.20.0 | MIT | Permissive |
| sqlalchemy | 2.0.36 | MIT | Permissive |
| alembic | 1.13.1 | MIT | Permissive |
| asyncpg | 0.29.0 | MIT | Permissive |
| psycopg | 3.2.5 | LGPL-3.0 | Weak Copyleft |
| psycopg-binary | 3.2.5 | LGPL-3.0 | Weak Copyleft |
| psycopg-pool | 3.2.2 | LGPL-3.0 | Weak Copyleft |
| pydantic | 2.14.1 | MIT | Permissive |
| pydantic-core | 2.50.1 | MIT | Permissive |
| pydantic-settings | 2.9.0 | MIT | Permissive |
| python-dotenv | 1.2.4 | BSD-3-Clause | Permissive |
| pyyaml | 6.0.3 | MIT | Permissive |

### Backend — Development Dependencies

| Package | Version | License | Classification |
|---------|---------|---------|----------------|
| pytest | 8.3.4 | MIT | Permissive |
| pytest-asyncio | 0.25.3 | Apache-2.0 | Permissive |
| pytest-cov | 6.0.0 | MIT | Permissive |
| coverage | 7.16.2 | Apache-2.0 | Permissive |
| mypy | 1.14.0 | MIT | Permissive |
| ruff | 0.9.0 | MIT | Permissive |
| watchfiles | 1.3.0 | MIT | Permissive |

### Infrastructure & External Services

| Component | License | Notes |
|-----------|---------|-------|
| **SearXNG** | **AGPL-3.0** | **Critical:** Network-use copyleft if modified |
| Ollama | MIT | Local inference server |
| qwen3:4b model | Apache-2.0 | Model weights |
| faster-whisper | MIT | Speech-to-text |
| PostgreSQL | PostgreSQL License | Similar to MIT/BSD |
| Docker Compose | Apache-2.0 | Tooling only |
| Caddy | Apache-2.0 | Reverse proxy (planned) |

### Web Client (Next.js/React)

| Package Category | License |
|-----------------|---------|
| Next.js, React, React DOM | MIT |
| Tailwind CSS | MIT |
| TanStack Query | MIT |
| Zustand | MIT |
| TypeScript | Apache-2.0 |
| ESLint, Prettier | MIT |

### Android Client (Expo/React Native)

| Package Category | License |
|-----------------|---------|
| Expo, React Native | MIT |
| React Native Paper | MIT |
| Expo SecureStore | MIT |
| TypeScript | Apache-2.0 |

---

## 3. License Compatibility Analysis

### SearXNG AGPL-3.0 — Key Concern

| Scenario | AGPL Obligation | MyFarmAI Impact |
|----------|-----------------|-----------------|
| Run SearXNG unmodified, no source changes | Provide SearXNG source on request | Manageable — upstream source available |
| Modify SearXNG code | Must publish modifications under AGPL-3.0 | Avoid modifications; use configuration only |
| Link SearXNG as library | Triggers AGPL for linked code | Not applicable — HTTP API only |
| Distribute MyFarmAI with SearXNG | MyFarmAI code not automatically AGPL | HTTP boundary preserves license separation |

**Conclusion:** Running unmodified SearXNG via HTTP API does **not** force MyFarmAI to be AGPL-3.0. The AGPL network-use provision applies to SearXNG itself, not clients communicating over HTTP.

### LGPL-3.0 (psycopg) — Secondary Concern

- LGPL allows linking from proprietary/permissive code
- Must allow user to swap psycopg version (dynamic linking satisfied by pip)
- No source disclosure required for MyFarmAI code
- **Compatible** with Apache-2.0 and MIT

### Overall Compatibility

All runtime dependencies are compatible with **Apache-2.0**, **MIT**, or **BSD-3-Clause** project licenses. No dependency forces a copyleft license on MyFarmAI.

---

## 4. License Options Evaluation

| License | Pros | Cons | Compatibility |
|---------|------|------|---------------|
| **Apache-2.0** (RECOMMENDED) | Patent grant, permissive, industry standard for infrastructure, explicit contributor terms | Slightly more complex than MIT | ✅ All deps |
| **MIT** | Simplest, maximum permissiveness | No patent grant | ✅ All deps |
| **BSD-3-Clause** | Permissive, no endorsement clause | No patent grant | ✅ All deps |
| **AGPL-3.0** | Matches SearXNG, strong copyleft | Viral — forces entire project AGPL if any AGPL code linked | ❌ Overkill, restricts commercial use |
| **Proprietary / No License** | Maximum control | No open-source benefits, cannot use AGPL/LGPL deps legally | ❌ Violates SearXNG AGPL |

---

## 5. Recommendation: Apache-2.0

### Why Apache-2.0 Over MIT?

1. **Patent Protection:** Explicit patent license from contributors protects users
2. **Industry Standard:** Used by Kubernetes, TensorFlow, Apache projects, major cloud infrastructure
3. **Contributor Clarity:** Clear terms for contributions (DCO/CLA compatible)
4. **Commercial Friendly:** Permits commercial use, modification, distribution
5. **Dependency Alignment:** Most deps are MIT/BSD/Apache — Apache-2.0 is a superset

### License File Template

```text
                                 Apache License
                           Version 2.0, January 2004
                        http://www.apache.org/licenses/

   TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION
   ...
   (Full Apache-2.0 text)
```

### Third-Party Notices Required

Create `THIRD_PARTY_NOTICES.md` listing:

```
MyFarmAI includes the following third-party components:

Backend Runtime:
- FastAPI (MIT) — https://github.com/tiangolo/fastapi
- Uvicorn (BSD-3-Clause) — https://github.com/encode/uvicorn
- HTTPX (BSD-3-Clause) — https://github.com/encode/httpx
- SQLAlchemy (MIT) — https://www.sqlalchemy.org/
- Alembic (MIT) — https://alembic.sqlalchemy.org/
- Pydantic (MIT) — https://github.com/pydantic/pydantic
- asyncpg (MIT) — https://github.com/MagicStack/asyncpg
- psycopg (LGPL-3.0) — https://github.com/psycopg/psycopg
- aiosqlite (MIT) — https://github.com/jreese/aiosqlite
- python-multipart (Apache-2.0) — https://github.com/andrew-d/python-multipart

Infrastructure (External Services):
- SearXNG (AGPL-3.0) — https://github.com/searxng/searxng
  NOTICE: Run unmodified via HTTP API. Source available at upstream.
- Ollama (MIT) — https://github.com/ollama/ollama
- Qwen3-4B Model (Apache-2.0) — https://huggingface.co/Qwen/Qwen3-4B
- faster-whisper (MIT) — https://github.com/SYSTRAN/faster-whisper
- PostgreSQL (PostgreSQL License) — https://www.postgresql.org/about/licence/

Web Client:
- Next.js (MIT) — https://nextjs.org/
- React (MIT) — https://react.dev/
- Tailwind CSS (MIT) — https://tailwindcss.com/
- TanStack Query (MIT) — https://tanstack.com/query
- Zustand (MIT) — https://github.com/pmndrs/zustand

Android Client:
- Expo (MIT) — https://expo.dev/
- React Native (MIT) — https://reactnative.dev/
- React Native Paper (MIT) — https://reactnativepaper.com/
```

---

## 6. Decision Options

| Option | License | Deferral | Notes |
|--------|---------|----------|-------|
| **A** | **Apache-2.0** (Recommended) | No | Create LICENSE + THIRD_PARTY_NOTICES.md |
| **B** | MIT | No | Simpler, no patent grant |
| **C** | BSD-3-Clause | No | Similar to MIT |
| **D** | AGPL-3.0 | No | Forces entire project AGPL; not recommended |
| **E** | Defer | Yes | "License decision deferred to YYYY-MM-DD; all code treated as proprietary until decided" |

---

## 7. Required Artifacts if Approved

- [ ] `LICENSE` file in repository root (Apache-2.0 full text)
- [ ] `THIRD_PARTY_NOTICES.md` in repository root
- [ ] Update `README.md` License section
- [ ] Verify no incompatible license introduced in future PRs (add to CI)

---

## 8. Owner/Legal Decision

| Field | Value |
|-------|-------|
| **Decision** | ☐ Apache-2.0 (Recommended) / ☐ MIT / ☐ BSD-3-Clause / ☐ AGPL-3.0 / ☐ Defer to: YYYY-MM-DD / ☐ Other: _______ |
| **Rationale** | |
| **Approver** | |
| **Date** | |
| **Signature** | |

---

## 9. Implementation Impact (If Approved)

- **P1-16:** Create `LICENSE` and `THIRD_PARTY_NOTICES.md`
- **CI:** Add license check to `scripts/check.sh` (reuse `pip-licenses` or similar)
- **Documentation:** Update `README.md` License section
- **Future PRs:** Require license compatibility check for new dependencies