# Phase 4 — Local AI Gateway and Ollama

## Objective

Provide local AI capabilities without coupling business logic to a single model or requiring paid inference APIs.

## Entry conditions
- Local AI use cases and data privacy rules are approved.
- Hardware/resource budget is measured.
- Authentication and workload limits are in place for user-facing AI endpoints.

## Workstreams

### 1. Provider-independent interface
Define a stable internal interface for:
- Chat completion.
- Structured output tasks.
- Embeddings, if required.
- Health/capability checks.
- Model metadata and error mapping.

Keep Ollama-specific HTTP behavior inside its adapter.

### 2. Model configuration and evaluation
- Inventory installed models and licenses.
- Benchmark candidates on representative MyFarmAI tasks.
- Measure latency, memory, VRAM, output quality and failure rate.
- Consider regional-language questions, agricultural advice, refusal behavior and low-confidence answers.
- Choose a default model only after evidence; do not assume a model fits based on parameter count alone.

### 3. Reliability
- Set connect/read/overall timeouts.
- Limit concurrent inference and queue depth.
- Handle model missing, server unavailable, timeout, invalid output and out-of-memory conditions.
- Support cancellation where feasible.
- Do not automatically fall back to a paid provider.
- Provide a clear degraded response if local inference is unavailable.

### 4. Prompts and structured outputs
- Version prompt templates.
- Validate structured model output against schemas.
- Treat model output as untrusted input.
- Separate system policy from user prompts and retrieved content.
- Never let model output independently authorize privileged actions.

### 5. Conversations and privacy
- Persist conversation/message metadata only under approved retention rules.
- Record model and prompt-template versions where useful.
- Do not log full private conversations by default.
- Support deletion/export policies where required.

### 6. Evaluation
- Build a small, versioned evaluation set.
- Test groundedness, factuality, citation requirements, language behavior and unsafe advice handling.
- Compare model changes before replacing the default.

## Deliverables
- AI gateway interface and Ollama adapter.
- Model configuration and resource-budget guide.
- Evaluation dataset and results.
- Error/degraded-mode behavior.
- Privacy and logging policy.

## Acceptance criteria
- [ ] Core AI paths work without paid API keys.
- [ ] Model/provider specifics do not leak into domain modules.
- [ ] Timeouts and concurrency are bounded.
- [ ] Invalid structured output is rejected safely.
- [ ] Failure behavior is tested.
- [ ] Model selection is supported by recorded benchmarks.
- [ ] Private prompts and conversations are handled under approved retention rules.

## Exit gate
The AI gateway passes reliability, resource, privacy and evaluation review on the target hardware.
