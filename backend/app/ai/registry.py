"""Model registry (Phase 4B): capability/license/status metadata for models.

Governance:
- Only models with status "enabled" may be selected per-request via the gateway.
- The settings-level default model (`settings.ollama_model`) is admin-controlled
  configuration and bypasses the registry (registry governs per-request choice).
- Statuses: "enabled" (usable now), "installed" (present, not enabled for
  per-request selection), "proposed" (candidate, not yet installed/approved).
- License evidence must be verified against the actual model card before a
  model moves to "enabled" (P4-03 caveat; Gemma flagged non-OSI).
"""

from dataclasses import dataclass
from typing import Literal

Status = Literal["enabled", "installed", "proposed"]

CHAT = "chat"
EMBEDDINGS = "embeddings"
VISION = "vision"


@dataclass(frozen=True)
class ModelInfo:
    tag: str
    capability: str
    status: Status
    license: str
    license_verified: bool = False


_REGISTRY: tuple[ModelInfo, ...] = (
    ModelInfo(
        tag="qwen3:0.6b",
        capability=CHAT,
        status="enabled",
        license="Apache-2.0 (Qwen3 family; verify model card)",
    ),
    # Installed, benchmarked (MODEL_BENCHMARKS.md) but NOT enabled for
    # per-request selection: code-tuned / reference candidates.
    ModelInfo(
        tag="deepseek-coder:latest",
        capability=CHAT,
        status="installed",
        license="MIT-class (verify model card)",
    ),
    ModelInfo(
        tag="phi:latest",
        capability=CHAT,
        status="installed",
        license="MIT (Microsoft Phi; verify model card)",
    ),
    ModelInfo(
        tag="qwen2.5-coder:1.5b-base",
        capability=CHAT,
        status="installed",
        license="Apache-2.0 (verify model card)",
    ),
    # Reasoning candidate — benchmark vs default before enabling (master prompt, Model 2).
    ModelInfo(
        tag="qwen3:4b",
        capability=CHAT,
        status="installed",
        license="Apache-2.0 (verify model card)",
    ),
    # Vision model — enabled for crop-image assistance (Model 3 gate resolved:
    # qwen3-vl:2b present locally, Apache-2.0, owner approval 2026-10-31).
    ModelInfo(
        tag="qwen3-vl:2b",
        capability=VISION,
        status="enabled",
        license="Apache-2.0 (verify model card)",
    ),
    # Embedding candidates — benchmark before choosing one (Model 4).
    ModelInfo(
        tag="qwen3-embedding:0.6b",
        capability=EMBEDDINGS,
        status="installed",
        license="Apache-2.0 (verify model card)",
    ),
    ModelInfo(
        tag="nomic-embed-text:latest",
        capability=EMBEDDINGS,
        status="installed",
        license="Apache-2.0 (verify model card)",
    ),
    # License flag: Gemma Terms of Use (non-OSI) — requires owner review.
    ModelInfo(
        tag="gemma:latest",
        capability=CHAT,
        status="installed",
        license="Gemma Terms of Use (NOT OSI-approved)",
        license_verified=False,
    ),
)


class ModelNotAvailableError(Exception):
    """Requested model is not registered/enabled for this capability."""


def get(tag: str) -> ModelInfo | None:
    return next((m for m in _REGISTRY if m.tag == tag), None)


def require_enabled(tag: str, capability: str) -> ModelInfo:
    """Raise ModelNotAvailableError unless the tag is enabled for the capability."""
    info = get(tag)
    if info is None or info.status != "enabled" or info.capability != capability:
        raise ModelNotAvailableError(f"Model '{tag}' is not enabled for capability '{capability}'")
    return info


def registry_tags() -> set[str]:
    return {m.tag for m in _REGISTRY}


def drift_against_live(live_tags: set[str]) -> dict[str, set[str]]:
    """Compare registry against live /api/tags output.

    Returns {"unregistered": [...live tags missing from registry...],
             "unavailable": [...registered-installed tags missing live...]}.
    """
    return {
        "unregistered": live_tags - registry_tags(),
        "unavailable": {m.tag for m in _REGISTRY if m.status in ("enabled", "installed")}
        - live_tags,
    }
