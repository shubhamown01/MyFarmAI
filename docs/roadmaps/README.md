# MyFarmAI Backend Roadmaps

**Status:** Planning baseline; Phase 0 audit reported complete. Phase 1 remains blocked pending explicit approval.  
**Principles:** Self-hostable, open-source-first, no mandatory paid APIs, security-first, documentation before code, preserve existing work and user data.

## Roadmap files

- [`MyFarmAI_Backend_Roadmap.md`](MyFarmAI_Backend_Roadmap.md) — overall roadmap and sequencing.
- [`phases/Phase_00_Read_Only_Audit.md`](phases/Phase_00_Read_Only_Audit.md) — audit scope, evidence, approval gate.
- [`phases/Phase_01_Backend_Foundation.md`](phases/Phase_01_Backend_Foundation.md) — API foundation and quality baseline.
- [`phases/Phase_02_Database_Architecture.md`](phases/Phase_02_Database_Architecture.md) — database design and PostgreSQL migration readiness.
- [`phases/Phase_03_Authentication_Security.md`](phases/Phase_03_Authentication_Security.md) — authentication, authorization, privacy, and abuse controls.
- [`phases/Phase_04_Local_AI_Ollama.md`](phases/Phase_04_Local_AI_Ollama.md) — provider-independent local AI gateway.
- [`phases/Phase_05_Agriculture_Integrations.md`](phases/Phase_05_Agriculture_Integrations.md) — agricultural domain and licensed data adapters.
- [`phases/Phase_06_Research_Engine.md`](phases/Phase_06_Research_Engine.md) — SearXNG-backed research, extraction, ranking, and citations.
- [`phases/Phase_07_Background_Jobs_Search.md`](phases/Phase_07_Background_Jobs_Search.md) — optional jobs and search upgrades.
- [`phases/Phase_08_Deployment_Hardening.md`](phases/Phase_08_Deployment_Hardening.md) — secure deployment, operations, and recovery.
- [`phases/Phase_09_CI_Release_Readiness.md`](phases/Phase_09_CI_Release_Readiness.md) — CI quality gates and release process.

### PersonaPlex Voice Integration (Optional, Gated)

- [`phases/personaplex/README.md`](phases/personaplex/README.md) — PersonaPlex integration overview and phase index.
- [`phases/personaplex/Phase_P0_Feasibility_and_Access.md`](phases/personaplex/Phase_P0_Feasibility_and_Access.md) — model approval, license, hardware gate.
- [`phases/personaplex/Phase_P1_Shared_Model_Storage_and_Lifecycle.md`](phases/personaplex/Phase_P1_Shared_Model_Storage_and_Lifecycle.md) — shared model storage, checksums, lifecycle.
- [`phases/personaplex/Phase_P2_Inference_Runtime_Prototype.md`](phases/personaplex/Phase_P2_Inference_Runtime_Prototype.md) — runtime prototype on target hardware.
- [`phases/personaplex/Phase_P3_Hardware_Deployment_Strategy.md`](phases/personaplex/Phase_P3_Hardware_Deployment_Strategy.md) — three deployment targets, cost models.
- [`phases/personaplex/Phase_P4_Reusable_Voice_Service.md`](phases/personaplex/Phase_P4_Reusable_Voice_Service.md) — production voice service with API.
- [`phases/personaplex/Phase_P5_AI_Gateway_Integration.md`](phases/personaplex/Phase_P5_AI_Gateway_Integration.md) — gateway routing voice + text fallback.
- [`phases/personaplex/Phase_P6_Web_Integration.md`](phases/personaplex/Phase_P6_Web_Integration.md) — web UI voice integration, consent, fallback.
- [`phases/personaplex/Phase_P7_Android_Integration.md`](phases/personaplex/Phase_P7_Android_Integration.md) — Android audio, permissions, networking.
- [`phases/personaplex/Phase_P8_Agricultural_Conversational_Behavior.md`](phases/personaplex/Phase_P8_Agricultural_Conversational_Behavior.md) — safe ag voice responses, citations.
- [`phases/personaplex/Phase_P9_Security_Privacy_Compliance.md`](phases/personaplex/Phase_P9_Security_Privacy_Compliance.md) — consent, data minimization, spoofing, license.
- [`phases/personaplex/Phase_P10_Performance_Reliability.md`](phases/personaplex/Phase_P10_Performance_Reliability.md) — benchmarks, reliability, chaos testing.
- [`phases/personaplex/Phase_P11_Production_Readiness_Reuse.md`](phases/personaplex/Phase_P11_Production_Readiness_Reuse.md) — deployment package, multi-project reuse.

## How to use this set

1. Treat Phase 0 as the audit record and planning baseline, not as authorization to change the repository.
2. Review the Phase 0 findings and the Phase 1 plan already in the repository.
3. Resolve the approval decisions listed below before implementation.
4. Execute one phase at a time. Require the phase exit gate before moving forward.
5. Keep every implementation task small, tested, documented, and explicitly scoped.
6. Do not overwrite existing files or modify uncommitted work without approval.

## Decisions that remain approval-gated

- Preservation and handling of the two divergent SQLite databases.
- Deployment exposure: local-only, private LAN, single VPS, or public internet.
- Weather/public data source licensing for commercial use.
- Python/runtime and dependency-locking policy.
- PostgreSQL production strategy and tested migration plan.
- Voice service: defer or secure and retain.
- Local model selection after benchmark.
- Project licence and SearXNG AGPL-3.0 posture.
- Whether optional Valkey, workers, Qdrant, and observability services are justified.

### PersonaPlex-specific decisions
- **NVIDIA PersonaPlex 7B v1 model approval** on Hugging Face (currently gated).
- **NVIDIA Open Model License + CC-BY-4.0 base model** compatibility with MyFarmAI distribution.
- **Hardware target**: current MX250 (2 GB VRAM) vs required Ampere/Hopper GPU (≥24 GB VRAM).
- **PersonaPlex voice in MVP**: include as optional gated capability or defer entirely.
- **PersonaPlex license compliance**: NVIDIA Open Model License + CC-BY-4.0 attribution requirements.
- **PersonaPlex voice service exposure**: never expose unauthenticated; requires Phase 3 auth first.
- **PersonaPlex model weight sharing**: `/data/AI-Models/` convention for multi-project reuse (MyFarmAI, ATHENA, future).
- **PersonaPlex voice in MVP scope**: optional gated capability — not required for core MVP.

## Global completion rules

Every phase must provide:
- Scope and acceptance criteria.
- Evidence of tests actually run.
- Security and licensing review where applicable.
- Documentation updates and architecture decisions.
- Explicit blockers and unverified items.
- No mandatory paid APIs or unapproved external integrations.

**Never report a phase complete if an exit criterion is blocked or unverified.**
