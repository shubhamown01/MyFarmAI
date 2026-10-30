"""
MyFarmAI Orchestrator - Capability Registry

Discovers, catalogs, and validates all available capabilities:
agents, skills, plugins, MCP servers, CLI tools, models, test frameworks.
"""

import asyncio
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .models import (
    Capability,
    CapabilityStatus,
    CapabilityType,
    OrchestrationConfig,
    ProjectMemory,
)


@dataclass
class DiscoveryResult:
    """Result of a capability discovery scan."""

    capabilities: list[Capability]
    errors: list[str]
    warnings: list[str]
    scan_duration_ms: int
    scanned_at: datetime


class CapabilityRegistry:
    """
    Registry of all discovered capabilities in the MyFarmAI environment.

    Discovers from:
    - .opencode/agents/*.md (agent definitions)
    - .opencode/skills/*/SKILL.md (skill manifests)
    - opencode.json (plugins, MCP servers, model config)
    - backend/pyproject.toml or requirements.txt (Python deps)
    - web/package.json (npm deps)
    - android/package.json (npm deps)
    - Graphify knowledge graph (code relationships)
    """

    def __init__(self, config: OrchestrationConfig, memory: ProjectMemory | None = None):
        self.config = config
        self.memory = memory or ProjectMemory()
        self.capabilities: dict[str, Capability] = {}
        self._discovery_cache: DiscoveryResult | None = None
        self._allowlist: set[str] = set()  # Tier 2 allowlisted capabilities
        self._load_allowlist()

    def _load_allowlist(self) -> None:
        """Load Tier 2 allowlist from config or defaults."""
        # Default allowlist for reversible, low-risk additions
        self._allowlist = {
            "ruff",
            "mypy",
            "pytest",
            "pip-audit",
            "gitleaks",
            "trivy",
            "osv-scanner",
            "hadolint",
            "shellcheck",
            "prettier",
            "eslint",
            "typescript",
            "vitest",
            "playwright",
        }

    async def discover_all(self, force_refresh: bool = False) -> DiscoveryResult:
        """Run full capability discovery across all sources."""
        start_time = datetime.now()
        all_capabilities: list[Capability] = []
        errors: list[str] = []
        warnings: list[str] = []

        # Discovery methods in order
        discovery_methods = [
            ("agents", self._discover_agents),
            ("skills", self._discover_skills),
            ("plugins", self._discover_plugins),
            ("mcp_servers", self._discover_mcp_servers),
            ("python_deps", self._discover_python_dependencies),
            ("web_npm_deps", self._discover_web_npm_dependencies),
            ("android_npm_deps", self._discover_android_npm_dependencies),
            ("cli_tools", self._discover_cli_tools),
            ("models", self._discover_models),
            ("test_frameworks", self._discover_test_frameworks),
        ]

        for name, method in discovery_methods:
            try:
                caps = await method()
                all_capabilities.extend(caps)
            except Exception as e:
                errors.append(f"{name}: {str(e)}")

        # Deduplicate by name (keep highest status)
        deduped = self._deduplicate_capabilities(all_capabilities)

        # Validate capabilities
        validated = await self._validate_capabilities(deduped)

        # Detect conflicts
        conflicts = self._detect_conflicts(validated)
        for conflict in conflicts:
            warnings.append(f"Conflict: {conflict}")

        # Update registry
        self.capabilities = {cap.name: cap for cap in validated}

        # Snapshot to memory
        for cap in validated:
            self.memory.snapshot_capability(cap)

        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        result = DiscoveryResult(
            capabilities=validated,
            errors=errors,
            warnings=warnings,
            scan_duration_ms=duration_ms,
            scanned_at=datetime.now(),
        )
        self._discovery_cache = result

        return result

    def _deduplicate_capabilities(self, capabilities: list[Capability]) -> list[Capability]:
        """Deduplicate capabilities by name, keeping the best status."""
        by_name: dict[str, list[Capability]] = {}
        for cap in capabilities:
            by_name.setdefault(cap.name, []).append(cap)

        result = []
        for name, caps in by_name.items():
            if len(caps) == 1:
                result.append(caps[0])
            else:
                # Prefer VERIFIED_WORKING > AVAILABLE > CONFIGURED > INSTALLED > BROKEN > OBSOLETE
                status_order = {
                    CapabilityStatus.VERIFIED_WORKING: 6,
                    CapabilityStatus.AVAILABLE: 5,
                    CapabilityStatus.AUTHENTICATED: 4,
                    CapabilityStatus.CONFIGURED: 3,
                    CapabilityStatus.INSTALLED: 2,
                    CapabilityStatus.BROKEN: 1,
                    CapabilityStatus.OBSOLETE: 0,
                }
                best = max(caps, key=lambda c: status_order.get(c.status, 0))
                # Merge capabilities lists
                all_caps = set()
                for c in caps:
                    all_caps.update(c.capabilities)
                best.capabilities = list(all_caps)
                result.append(best)
        return result

    def _detect_conflicts(self, capabilities: list[Capability]) -> list[str]:
        """Detect capability conflicts: duplicates, version mismatches, permission overlaps."""
        conflicts = []

        # Check for duplicate names with different types
        by_name: dict[str, list[Capability]] = {}
        for cap in capabilities:
            by_name.setdefault(cap.name, []).append(cap)

        for name, caps in by_name.items():
            if len(caps) > 1:
                types = [c.type.value for c in caps]
                if len(set(types)) > 1:
                    conflicts.append(f"'{name}' has multiple types: {types}")

        # Check for version conflicts in Python deps
        python_deps = [
            c
            for c in capabilities
            if c.type == CapabilityType.CLI and c.metadata.get("source") == "python"
        ]
        # Would need requirements.txt parsing for full version conflict detection

        return conflicts

    async def _validate_capabilities(self, capabilities: list[Capability]) -> list[Capability]:
        """Run validation commands for capabilities that have them."""
        validated = []
        for cap in capabilities:
            if cap.validation_command:
                try:
                    # Run validation with timeout
                    proc = await asyncio.create_subprocess_shell(
                        cap.validation_command,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                        cwd=self.config.project_root,
                    )
                    stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)

                    cap.validation_result = {
                        "exit_code": proc.returncode,
                        "stdout": stdout.decode()[:1000],
                        "stderr": stderr.decode()[:1000],
                        "validated_at": datetime.now().isoformat(),
                    }

                    if proc.returncode == 0:
                        cap.status = CapabilityStatus.VERIFIED_WORKING
                    else:
                        cap.status = CapabilityStatus.BROKEN

                    cap.last_verified = datetime.now()
                except TimeoutError:
                    cap.validation_result = {
                        "error": "Validation timeout",
                        "validated_at": datetime.now().isoformat(),
                    }
                    cap.status = CapabilityStatus.BROKEN
                except Exception as e:
                    cap.validation_result = {
                        "error": str(e),
                        "validated_at": datetime.now().isoformat(),
                    }
                    cap.status = CapabilityStatus.BROKEN
            validated.append(cap)
        return validated

    # =========================================================================
    # Discovery Methods
    # =========================================================================

    async def _discover_agents(self) -> list[Capability]:
        """Discover agents from .opencode/agents/*.md"""
        capabilities = []
        agents_dir = Path(self.config.project_root) / ".opencode" / "agents"

        if not agents_dir.exists():
            return capabilities

        for agent_file in agents_dir.glob("*.md"):
            name = agent_file.stem
            try:
                content = agent_file.read_text()
                # Parse frontmatter for metadata
                metadata = self._parse_agent_frontmatter(content)

                # Convert permissions dict to list of strings for Pydantic compatibility
                perm_dict = metadata.get("permission", {}) or metadata.get("permissions", {}) or {}
                perm_list = []
                if isinstance(perm_dict, dict):
                    for key, value in perm_dict.items():
                        if isinstance(value, dict):
                            for subkey, subvalue in value.items():
                                perm_list.append(f"{key}.{subkey}:{subvalue}")
                        else:
                            perm_list.append(f"{key}:{value}")
                elif isinstance(perm_dict, list):
                    perm_list = [str(p) for p in perm_dict]

                cap = Capability(
                    name=name,
                    type=CapabilityType.AGENT,
                    location=str(agent_file),
                    capabilities=self._extract_agent_capabilities(content, metadata),
                    permissions=perm_list,
                    dependencies=[],
                    status=CapabilityStatus.AVAILABLE,  # Changed from INSTALLED to make usable immediately
                    validation_command=f"opencode agent info {name}",
                    metadata={
                        "source": "opencode_agents",
                        "mode": metadata.get("mode", "subagent"),
                        "steps": metadata.get("steps", 10),
                        "description": metadata.get("description", ""),
                    },
                )
                capabilities.append(cap)
            except Exception:
                # Skip malformed agent files
                pass

        return capabilities

    def _parse_agent_frontmatter(self, content: str) -> dict[str, Any]:
        """Parse YAML frontmatter from agent markdown file."""
        import yaml

        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                try:
                    return yaml.safe_load(parts[1]) or {}
                except:
                    pass
        return {}

    def _extract_agent_capabilities(self, content: str, metadata: dict) -> list[str]:
        """Extract capabilities from agent description and metadata."""
        caps = []
        desc = metadata.get("description", "").lower()

        # Keyword-based capability extraction
        capability_keywords = {
            "backend": [
                "fastapi",
                "sqlalchemy",
                "postgresql",
                "api",
                "backend",
                "database",
                "migration",
            ],
            "frontend": [
                "next.js",
                "react",
                "tailwind",
                "frontend",
                "ui",
                "component",
                "accessibility",
            ],
            "android": ["expo", "react native", "android", "mobile", "microphone", "audio"],
            "ai_ml": ["ollama", "qwen", "model", "inference", "personaplex", "ml", "ai"],
            "research": ["searxng", "search", "extraction", "citation", "ssrf", "web search"],
            "security": ["auth", "secret", "threat", "vulnerability", "penetration", "security"],
            "qa": ["test", "unit", "integration", "regression", "contract", "build", "lint"],
            "deployment": ["docker", "ci/cd", "deploy", "vercel", "kubernetes", "infrastructure"],
            "documentation": ["doc", "readme", "api doc", "guide", "tutorial"],
            "architecture": ["architecture", "design", "adr", "decision", "review"],
            "debugging": ["debug", "error", "trace", "log", "investigate"],
        }

        for cap_name, keywords in capability_keywords.items():
            if any(kw in desc for kw in keywords):
                caps.append(cap_name)

        return caps

    async def _discover_skills(self) -> list[Capability]:
        """Discover skills from .opencode/skills/*/SKILL.md"""
        capabilities = []
        skills_dir = Path(self.config.project_root) / ".opencode" / "skills"

        if not skills_dir.exists():
            return capabilities

        for skill_dir in skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue
            skill_file = skill_dir / "SKILL.md"
            if not skill_file.exists():
                continue

            name = skill_dir.name
            try:
                content = skill_file.read_text()
                # Parse skill description
                description = self._extract_skill_description(content)

                cap = Capability(
                    name=name,
                    type=CapabilityType.SKILL,
                    location=str(skill_dir),
                    capabilities=[name, description.lower()[:100]],
                    permissions=[],
                    dependencies=[],
                    status=CapabilityStatus.INSTALLED,
                    validation_command=f"opencode skill info {name}",
                    metadata={
                        "source": "opencode_skills",
                        "description": description,
                        "has_references": (skill_dir / "references").exists(),
                    },
                )
                capabilities.append(cap)
            except Exception:
                pass

        return capabilities

    def _extract_skill_description(self, content: str) -> str:
        """Extract first paragraph as description."""
        lines = content.split("\n")
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#") and not line.startswith("---"):
                return line[:200]
        return ""

    async def _discover_plugins(self) -> list[Capability]:
        """Discover plugins from opencode.json"""
        capabilities = []
        opencode_json = Path(self.config.project_root) / "opencode.json"

        if not opencode_json.exists():
            return capabilities

        try:
            config = json.loads(opencode_json.read_text())
            plugins = config.get("plugin", [])

            for plugin in plugins:
                if isinstance(plugin, str):
                    # Git plugin format: "name@git+https://..."
                    if "@git+" in plugin:
                        name, url = plugin.split("@git+", 1)
                    else:
                        name = plugin
                        url = ""

                    cap = Capability(
                        name=name,
                        type=CapabilityType.PLUGIN,
                        location=url or "opencode.json",
                        capabilities=[name],
                        permissions=[],
                        dependencies=[],
                        status=CapabilityStatus.INSTALLED,
                        validation_command=None,
                        metadata={
                            "source": "opencode_plugins",
                            "plugin_spec": plugin,
                            "is_git_plugin": "@git+" in plugin,
                        },
                    )
                    capabilities.append(cap)
        except Exception:
            pass

        return capabilities

    async def _discover_mcp_servers(self) -> list[Capability]:
        """Discover MCP servers from opencode.json"""
        capabilities = []
        opencode_json = Path(self.config.project_root) / "opencode.json"

        if not opencode_json.exists():
            return capabilities

        try:
            config = json.loads(opencode_json.read_text())
            mcp_servers = config.get("mcp", {}).get("servers", {})

            for name, server_config in mcp_servers.items():
                disabled = server_config.get("disabled", False)
                server_type = server_config.get("type", "unknown")

                cap = Capability(
                    name=f"mcp_{name}",
                    type=CapabilityType.MCP,
                    location=f"opencode.json:mcp.servers.{name}",
                    capabilities=[name, server_type],
                    permissions=[],
                    dependencies=[],
                    status=CapabilityStatus.CONFIGURED if not disabled else CapabilityStatus.BROKEN,
                    validation_command=None,  # MCP validation would need connection test
                    metadata={
                        "source": "opencode_mcp",
                        "server_type": server_type,
                        "disabled": disabled,
                        "config": server_config,
                    },
                )
                capabilities.append(cap)
        except Exception:
            pass

        return capabilities

    async def _discover_python_dependencies(self) -> list[Capability]:
        """Discover Python dependencies from pyproject.toml or requirements.txt"""
        capabilities = []
        backend_path = Path(self.config.backend_path)

        # Try pyproject.toml first
        pyproject = backend_path / "pyproject.toml"
        requirements = backend_path / "requirements.txt"

        deps = {}
        if pyproject.exists():
            try:
                import tomli

                content = pyproject.read_text()
                data = tomli.loads(content)
                # Project dependencies
                project = data.get("project", {})
                for dep in project.get("dependencies", []):
                    name = dep.split(">=")[0].split("==")[0].split("[")[0].strip()
                    deps[name] = dep
                # Optional dependencies
                for group, dep_list in project.get("optional-dependencies", {}).items():
                    for dep in dep_list:
                        name = dep.split(">=")[0].split("==")[0].split("[")[0].strip()
                        deps[name] = dep
            except Exception:
                pass
        elif requirements.exists():
            try:
                content = requirements.read_text()
                for line in content.split("\n"):
                    line = line.strip()
                    if line and not line.startswith("#"):
                        name = line.split(">=")[0].split("==")[0].split("[")[0].strip()
                        deps[name] = line
            except Exception:
                pass

        for name, spec in deps.items():
            cap = Capability(
                name=f"py_{name}",
                type=CapabilityType.CLI,
                location=str(pyproject if pyproject.exists() else requirements),
                capabilities=[name],
                permissions=[],
                dependencies=[],
                status=CapabilityStatus.INSTALLED,
                validation_command=f'uv run python -c "import {name.replace("-", "_")}"',
                metadata={"source": "python", "spec": spec, "package_name": name},
            )
            capabilities.append(cap)

        return capabilities

    async def _discover_web_npm_dependencies(self) -> list[Capability]:
        """Discover npm dependencies from web/package.json"""
        capabilities = []
        package_json = Path(self.config.web_path) / "package.json"

        if not package_json.exists():
            return capabilities

        try:
            data = json.loads(package_json.read_text())
            all_deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}

            for name, version in all_deps.items():
                cap = Capability(
                    name=f"npm_web_{name}",
                    type=CapabilityType.CLI,
                    location=str(package_json),
                    capabilities=[name],
                    permissions=[],
                    dependencies=[],
                    status=CapabilityStatus.INSTALLED,
                    validation_command=f"cd {self.config.web_path} && npm list {name}",
                    metadata={"source": "npm_web", "version": version, "package_name": name},
                )
                capabilities.append(cap)
        except Exception:
            pass

        return capabilities

    async def _discover_android_npm_dependencies(self) -> list[Capability]:
        """Discover npm dependencies from android/package.json"""
        capabilities = []
        package_json = Path(self.config.android_path) / "package.json"

        if not package_json.exists():
            return capabilities

        try:
            data = json.loads(package_json.read_text())
            all_deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}

            for name, version in all_deps.items():
                cap = Capability(
                    name=f"npm_android_{name}",
                    type=CapabilityType.CLI,
                    location=str(package_json),
                    capabilities=[name],
                    permissions=[],
                    dependencies=[],
                    status=CapabilityStatus.INSTALLED,
                    validation_command=f"cd {self.config.android_path} && npm list {name}",
                    metadata={"source": "npm_android", "version": version, "package_name": name},
                )
                capabilities.append(cap)
        except Exception:
            pass

        return capabilities

    async def _discover_cli_tools(self) -> list[Capability]:
        """Discover globally installed CLI tools relevant to the project."""
        capabilities = []

        cli_tools = [
            ("docker", "docker --version"),
            ("docker-compose", "docker-compose --version"),
            ("git", "git --version"),
            ("uv", "uv --version"),
            ("python3", "python3 --version"),
            ("node", "node --version"),
            ("npm", "npm --version"),
            ("opencode", "opencode --version"),
            ("graphify", "graphify --version"),
            ("gitleaks", "gitleaks version"),
            ("trivy", "trivy --version"),
            ("hadolint", "hadolint --version"),
        ]

        for name, cmd in cli_tools:
            try:
                proc = await asyncio.create_subprocess_shell(
                    cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )
                stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=10)

                if proc.returncode == 0:
                    version = stdout.decode().strip().split("\n")[0]
                    cap = Capability(
                        name=name,
                        type=CapabilityType.CLI,
                        location="system",
                        capabilities=[name],
                        permissions=[],
                        dependencies=[],
                        status=CapabilityStatus.VERIFIED_WORKING,
                        validation_command=cmd,
                        metadata={"source": "system_cli", "version": version},
                    )
                    capabilities.append(cap)
            except Exception:
                cap = Capability(
                    name=name,
                    type=CapabilityType.CLI,
                    location="system",
                    capabilities=[name],
                    permissions=[],
                    dependencies=[],
                    status=CapabilityStatus.BROKEN,
                    validation_command=cmd,
                    metadata={"source": "system_cli", "missing": True},
                )
                capabilities.append(cap)

        return capabilities

    async def _discover_models(self) -> list[Capability]:
        """Discover available Ollama models."""
        capabilities = []

        try:
            proc = await asyncio.create_subprocess_shell(
                "ollama list", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10)

            if proc.returncode == 0:
                lines = stdout.decode().strip().split("\n")[1:]  # Skip header
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 2:
                        name = parts[0]
                        size = parts[1]
                        cap = Capability(
                            name=f"ollama_{name.replace(':', '_').replace('.', '_')}",
                            type=CapabilityType.MODEL,
                            location="ollama",
                            capabilities=["inference", "chat", "embedding"],
                            permissions=[],
                            dependencies=["ollama"],
                            status=CapabilityStatus.AVAILABLE,
                            validation_command=f"ollama run {name} --help",
                            metadata={
                                "source": "ollama",
                                "model_name": name,
                                "size": size,
                                "runtime": "ollama",
                            },
                        )
                        capabilities.append(cap)
        except Exception:
            pass

        return capabilities

    async def _discover_test_frameworks(self) -> list[Capability]:
        """Discover test frameworks and their status."""
        capabilities = []

        frameworks = [
            ("pytest", "cd /data/MyFarmAI/backend && uv run pytest --version", "backend"),
            ("vitest", "cd /data/MyFarmAI/web && npx vitest --version", "web"),
            ("playwright", "cd /data/MyFarmAI/web && npx playwright --version", "web"),
            ("eslint", "cd /data/MyFarmAI/web && npx eslint --version", "web"),
            ("typescript", "cd /data/MyFarmAI/web && npx tsc --version", "web"),
        ]

        for name, cmd, project in frameworks:
            try:
                proc = await asyncio.create_subprocess_shell(
                    cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=15)

                if proc.returncode == 0:
                    version = stdout.decode().strip()
                    cap = Capability(
                        name=f"test_{name}_{project}",
                        type=CapabilityType.TEST_FRAMEWORK,
                        location=f"{project}/{name}",
                        capabilities=["test", "validation"],
                        permissions=[],
                        dependencies=[],
                        status=CapabilityStatus.VERIFIED_WORKING,
                        validation_command=cmd,
                        metadata={
                            "source": f"test_framework_{project}",
                            "framework": name,
                            "project": project,
                            "version": version,
                        },
                    )
                else:
                    cap = Capability(
                        name=f"test_{name}_{project}",
                        type=CapabilityType.TEST_FRAMEWORK,
                        location=f"{project}/{name}",
                        capabilities=["test", "validation"],
                        permissions=[],
                        dependencies=[],
                        status=CapabilityStatus.BROKEN,
                        validation_command=cmd,
                        metadata={
                            "source": f"test_framework_{project}",
                            "framework": name,
                            "project": project,
                            "error": stderr.decode()[:200],
                        },
                    )
                capabilities.append(cap)
            except Exception as e:
                cap = Capability(
                    name=f"test_{name}_{project}",
                    type=CapabilityType.TEST_FRAMEWORK,
                    location=f"{project}/{name}",
                    capabilities=["test", "validation"],
                    permissions=[],
                    dependencies=[],
                    status=CapabilityStatus.BROKEN,
                    validation_command=cmd,
                    metadata={
                        "source": f"test_framework_{project}",
                        "framework": name,
                        "project": project,
                        "error": str(e),
                    },
                )
                capabilities.append(cap)

        return capabilities

    # =========================================================================
    # Query Methods
    # =========================================================================

    def get_capability(self, name: str) -> Capability | None:
        """Get a capability by name."""
        return self.capabilities.get(name)

    def get_capabilities_by_type(self, cap_type: CapabilityType) -> list[Capability]:
        """Get all capabilities of a specific type."""
        return [c for c in self.capabilities.values() if c.type == cap_type]

    def get_usable_capabilities(self) -> list[Capability]:
        """Get all capabilities that are usable (available/verified)."""
        return [c for c in self.capabilities.values() if c.is_usable()]

    def find_capabilities_for_task(self, required_capabilities: list[str]) -> list[Capability]:
        """Find capabilities that match required capabilities."""
        matches = []
        for cap in self.get_usable_capabilities():
            for req in required_capabilities:
                if req.lower() in [c.lower() for c in cap.capabilities]:
                    matches.append(cap)
                    break
        return matches

    def find_best_agent_for_task(self, required_capabilities: list[str]) -> Capability | None:
        """Find the best agent for a task based on required capabilities."""
        agents = self.get_capabilities_by_type(CapabilityType.AGENT)
        usable_agents = [a for a in agents if a.is_usable()]

        if not usable_agents:
            return None

        # Score agents by capability match
        scored = []
        for agent in usable_agents:
            match_count = sum(
                1
                for req in required_capabilities
                if any(req.lower() in c.lower() for c in agent.capabilities)
            )
            score = match_count / max(len(required_capabilities), 1)
            scored.append((score, agent))

        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[0][1] if scored and scored[0][0] > 0 else None

    def get_registry_summary(self) -> dict[str, Any]:
        """Get a summary of the registry state."""
        by_type: dict[str, int] = {}
        by_status: dict[str, int] = {}

        for cap in self.capabilities.values():
            by_type[cap.type.value] = by_type.get(cap.type.value, 0) + 1
            by_status[cap.status.value] = by_status.get(cap.status.value, 0) + 1

        return {
            "total_capabilities": len(self.capabilities),
            "by_type": by_type,
            "by_status": by_status,
            "usable_count": len(self.get_usable_capabilities()),
            "last_scan": self._discovery_cache.scanned_at.isoformat()
            if self._discovery_cache
            else None,
            "scan_duration_ms": self._discovery_cache.scan_duration_ms
            if self._discovery_cache
            else None,
        }

    def is_allowlisted(self, capability_name: str) -> bool:
        """Check if a capability is in the Tier 2 allowlist."""
        # Check base name without prefixes
        base_name = capability_name
        for prefix in ["py_", "npm_web_", "npm_android_", "test_", "ollama_", "mcp_"]:
            if base_name.startswith(prefix):
                base_name = base_name[len(prefix) :]
                break
        return base_name in self._allowlist

    def add_to_allowlist(self, name: str) -> None:
        """Add a capability to the Tier 2 allowlist."""
        self._allowlist.add(name)

    def export_registry(self) -> dict[str, Any]:
        """Export registry for documentation/reporting."""
        return {
            "capabilities": {
                name: {
                    "type": cap.type.value,
                    "status": cap.status.value,
                    "version": cap.version,
                    "location": cap.location,
                    "capabilities": cap.capabilities,
                    "permissions": cap.permissions,
                    "dependencies": cap.dependencies,
                    "last_verified": cap.last_verified.isoformat() if cap.last_verified else None,
                    "metadata": cap.metadata,
                }
                for name, cap in self.capabilities.items()
            },
            "summary": self.get_registry_summary(),
            "allowlist": list(self._allowlist),
        }
