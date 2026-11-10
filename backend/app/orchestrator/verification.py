"""
MyFarmAI Orchestrator - Verification & Security Gate

Runs relevant tests, linting, type checks, builds, dependency checks, and security scans.
Verifies actual command exit codes and outputs. Prevents task completion without evidence.
"""

import asyncio
import os
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from .core import OrchestratorCore
from .models import (
    OrchestrationConfig,
    ProjectMemory,
    Task,
    TaskEventType,
    TaskHistoryEntry,
    VerificationCheckType,
    VerificationGate,
    VerificationResult,
)


class GateType(Enum):
    """Types of verification gates."""

    QUALITY = "quality"  # Code quality (lint, typecheck, tests)
    SECURITY = "security"  # Security scans
    CONTRACT = "contract"  # API contract tests
    BUILD = "build"  # Build verification
    DEPENDENCY = "dependency"  # Dependency audit
    CUSTOM = "custom"  # Custom checks


@dataclass
class VerificationCheck:
    """Definition of a verification check."""

    name: str
    check_type: VerificationCheckType
    gate_type: GateType
    command: str
    working_dir: str
    timeout_seconds: int = 300
    required: bool = True
    description: str = ""
    environment: dict[str, str] = field(default_factory=dict)
    success_codes: list[int] = field(default_factory=lambda: [0])


@dataclass
class GateResult:
    """Result of a verification gate."""

    gate_type: GateType
    passed: bool
    checks: list[VerificationResult]
    failed_required: list[str]
    skipped: list[str]
    duration_ms: int
    evidence: dict[str, Any]


class VerificationSecurityGate:
    """
    Runs verification gates and enforces quality/security standards.

    Quality Gate Checks (All Must Pass):
    - Backend tests, type check, lint
    - Frontend type check, tests, lint, build
    - Android type check, lint
    - Secret scan, dependency audit, OpenAPI diff

    Security Gate (Security-Engineer Review Required):
    - Authentication/authorization changes
    - Secret/credential handling
    - API endpoint exposure changes
    - Database schema changes affecting permissions
    - File upload/processing changes
    - Dependency additions with known CVEs
    """

    def __init__(
        self,
        config: OrchestrationConfig,
        core: OrchestratorCore,
        memory: ProjectMemory,
        security_review_callback: Callable[[Task], Awaitable[bool]] | None = None,
    ):
        self.config = config
        self.core = core
        self.memory = memory
        self.security_review_callback = security_review_callback

        # Define standard verification checks
        self.quality_checks = self._define_quality_checks()
        self.security_checks = self._define_security_checks()
        self.contract_checks = self._define_contract_checks()
        self.build_checks = self._define_build_checks()
        self.dependency_checks = self._define_dependency_checks()

        # All checks by type
        self.all_checks = (
            self.quality_checks
            + self.security_checks
            + self.contract_checks
            + self.build_checks
            + self.dependency_checks
        )

        # Check cache
        self._check_cache: dict[str, VerificationResult] = {}
        self._cache_ttl = 300  # 5 minutes

    def _define_quality_checks(self) -> list[VerificationCheck]:
        """Define code quality verification checks."""
        return [
            # Backend
            VerificationCheck(
                name="backend_tests",
                check_type=VerificationCheckType.UNIT_TEST,
                gate_type=GateType.QUALITY,
                command="uv run pytest -q",
                working_dir=str(self.config.backend_path),
                timeout_seconds=120,
                required=True,
                description="Run backend unit and integration tests",
            ),
            VerificationCheck(
                name="backend_typecheck",
                check_type=VerificationCheckType.TYPE_CHECK,
                gate_type=GateType.QUALITY,
                command="uv run mypy .",
                working_dir=str(self.config.backend_path),
                timeout_seconds=60,
                required=True,
                description="Run mypy type checking on backend",
            ),
            VerificationCheck(
                name="backend_lint",
                check_type=VerificationCheckType.LINT,
                gate_type=GateType.QUALITY,
                command="uv run ruff check .",
                working_dir=str(self.config.backend_path),
                timeout_seconds=60,
                required=True,
                description="Run ruff linting on backend",
            ),
            VerificationCheck(
                name="backend_format",
                check_type=VerificationCheckType.LINT,
                gate_type=GateType.QUALITY,
                command="uv run ruff format --check .",
                working_dir=str(self.config.backend_path),
                timeout_seconds=30,
                required=True,
                description="Check backend code formatting",
            ),
            # Frontend
            VerificationCheck(
                name="frontend_typecheck",
                check_type=VerificationCheckType.TYPE_CHECK,
                gate_type=GateType.QUALITY,
                command="npm run typecheck",
                working_dir=str(self.config.web_path),
                timeout_seconds=60,
                required=True,
                description="Run TypeScript type checking on frontend",
            ),
            VerificationCheck(
                name="frontend_tests",
                check_type=VerificationCheckType.UNIT_TEST,
                gate_type=GateType.QUALITY,
                command="npm test",
                working_dir=str(self.config.web_path),
                timeout_seconds=120,
                required=True,
                description="Run frontend tests",
            ),
            VerificationCheck(
                name="frontend_lint",
                check_type=VerificationCheckType.LINT,
                gate_type=GateType.QUALITY,
                command="npm run lint",
                working_dir=str(self.config.web_path),
                timeout_seconds=60,
                required=True,
                description="Run ESLint on frontend",
            ),
            VerificationCheck(
                name="frontend_build",
                check_type=VerificationCheckType.BUILD,
                gate_type=GateType.QUALITY,
                command="npm run build",
                working_dir=str(self.config.web_path),
                timeout_seconds=180,
                required=True,
                description="Build frontend for production",
            ),
            # Android
            VerificationCheck(
                name="android_typecheck",
                check_type=VerificationCheckType.TYPE_CHECK,
                gate_type=GateType.QUALITY,
                command="npm run typecheck",
                working_dir=str(self.config.android_path),
                timeout_seconds=60,
                required=True,
                description="Run TypeScript type checking on Android",
            ),
            VerificationCheck(
                name="android_lint",
                check_type=VerificationCheckType.LINT,
                gate_type=GateType.QUALITY,
                command="npm run lint",
                working_dir=str(self.config.android_path),
                timeout_seconds=60,
                required=True,
                description="Run ESLint on Android",
            ),
        ]

    def _define_security_checks(self) -> list[VerificationCheck]:
        """Define security verification checks."""
        return [
            VerificationCheck(
                name="secret_scan",
                check_type=VerificationCheckType.SECRET_SCAN,
                gate_type=GateType.SECURITY,
                command="gitleaks detect --source . --verbose",
                working_dir=str(self.config.project_root),
                timeout_seconds=60,
                required=True,
                description="Scan for secrets in codebase",
            ),
            VerificationCheck(
                name="dependency_audit_python",
                check_type=VerificationCheckType.DEPENDENCY_AUDIT,
                gate_type=GateType.SECURITY,
                command="uv run pip-audit",
                working_dir=str(self.config.backend_path),
                timeout_seconds=60,
                required=True,
                description="Audit Python dependencies for vulnerabilities",
            ),
            VerificationCheck(
                name="dependency_audit_web",
                check_type=VerificationCheckType.DEPENDENCY_AUDIT,
                gate_type=GateType.SECURITY,
                command="npm audit --audit-level=high",
                working_dir=str(self.config.web_path),
                timeout_seconds=60,
                required=False,  # May have false positives
                description="Audit npm dependencies for vulnerabilities (web)",
            ),
            VerificationCheck(
                name="dependency_audit_android",
                check_type=VerificationCheckType.DEPENDENCY_AUDIT,
                gate_type=GateType.SECURITY,
                command="npm audit --audit-level=high",
                working_dir=str(self.config.android_path),
                timeout_seconds=60,
                required=False,
                description="Audit npm dependencies for vulnerabilities (android)",
            ),
        ]

    def _define_contract_checks(self) -> list[VerificationCheck]:
        """Define API contract verification checks."""
        return [
            VerificationCheck(
                name="openapi_diff",
                check_type=VerificationCheckType.OPEN_API_DIFF,
                gate_type=GateType.CONTRACT,
                command='diff -u docs/api/openapi.json <(uv run python -c "from backend.app.main import app; import json; print(json.dumps(app.openapi(), indent=2))")',
                working_dir=str(self.config.project_root),
                timeout_seconds=30,
                required=True,
                description="Verify OpenAPI spec matches implementation",
            ),
        ]

    def _define_build_checks(self) -> list[VerificationCheck]:
        """Define build verification checks."""
        return [
            VerificationCheck(
                name="docker_compose_config",
                check_type=VerificationCheckType.CUSTOM,
                gate_type=GateType.BUILD,
                command="docker compose config",
                working_dir=str(self.config.project_root),
                timeout_seconds=30,
                required=True,
                description="Validate Docker Compose configuration",
            ),
            VerificationCheck(
                name="dockerfile_syntax",
                check_type=VerificationCheckType.CUSTOM,
                gate_type=GateType.BUILD,
                command="hadolint backend/Dockerfile",
                working_dir=str(self.config.project_root),
                timeout_seconds=30,
                required=False,
                description="Lint Dockerfile (if hadolint available)",
            ),
        ]

    def _define_dependency_checks(self) -> list[VerificationCheck]:
        """Define dependency verification checks."""
        return [
            VerificationCheck(
                name="uv_lock_check",
                check_type=VerificationCheckType.CUSTOM,
                gate_type=GateType.DEPENDENCY,
                command="uv lock --check",
                working_dir=str(self.config.backend_path),
                timeout_seconds=30,
                required=True,
                description="Verify uv.lock is up to date",
            ),
        ]

    async def run_verification_gate(
        self,
        task: Task,
        gate_types: list[GateType] | None = None,
        custom_checks: list[VerificationCheck] | None = None,
    ) -> VerificationGate:
        """
        Run verification gate for a task.

        Args:
            task: Task to verify
            gate_types: Specific gate types to run (default: all)
            custom_checks: Additional custom checks

        Returns:
            VerificationGate with all results
        """
        gate_types = gate_types or [GateType.QUALITY, GateType.CONTRACT, GateType.BUILD]

        # Determine which checks to run based on task
        checks_to_run = self._select_checks_for_task(task, gate_types)

        if custom_checks:
            checks_to_run.extend(custom_checks)

        # Run checks
        results = []
        for check in checks_to_run:
            result = await self._run_check(check, task)
            results.append(result)

        # Create gate
        gate = VerificationGate(task_id=task.id, results=results)
        gate.evaluate()

        # Record in memory
        self.memory.add_history(
            TaskHistoryEntry(
                task_id=task.id,
                event=TaskEventType.COMPLETED if gate.overall_passed else TaskEventType.FAILED,
                details={
                    "verification_gate": {
                        "passed": gate.overall_passed,
                        "failed_checks": gate.failed_checks,
                        "check_count": len(results),
                    }
                },
            )
        )

        return gate

    def _select_checks_for_task(
        self, task: Task, gate_types: list[GateType]
    ) -> list[VerificationCheck]:
        """Select relevant checks based on task type and gate types."""
        selected = []

        # Always run quality checks for code changes
        if GateType.QUALITY in gate_types:
            if any("backend" in f for f in task.files_involved):
                selected.extend([c for c in self.quality_checks if "backend" in c.name])
            if any("web" in f or "frontend" in f for f in task.files_involved):
                selected.extend([c for c in self.quality_checks if "frontend" in c.name])
            if any("android" in f for f in task.files_involved):
                selected.extend([c for c in self.quality_checks if "android" in c.name])
            # If no specific area, run all quality checks
            if not any(
                [
                    any("backend" in f for f in task.files_involved),
                    any("web" in f for f in task.files_involved),
                    any("android" in f for f in task.files_involved),
                ]
            ):
                selected.extend(self.quality_checks)

        # Security checks for security-sensitive tasks
        if GateType.SECURITY in gate_types or self._is_security_sensitive(task):
            selected.extend(self.security_checks)

        # Contract checks for API changes
        if GateType.CONTRACT in gate_types or self._is_api_change(task):
            selected.extend(self.contract_checks)

        # Build checks for deployment/config changes
        if GateType.BUILD in gate_types or self._is_build_change(task):
            selected.extend(self.build_checks)

        # Dependency checks for dependency changes
        if GateType.DEPENDENCY in gate_types or self._is_dependency_change(task):
            selected.extend(self.dependency_checks)

        # Deduplicate
        seen = set()
        unique = []
        for check in selected:
            if check.name not in seen:
                seen.add(check.name)
                unique.append(check)

        return unique

    async def _run_check(self, check: VerificationCheck, task: Task) -> VerificationResult:
        """Run a single verification check."""
        start_time = datetime.now()

        # Check cache
        cache_key = f"{check.name}:{hash(check.command)}"
        if cache_key in self._check_cache:
            cached = self._check_cache[cache_key]
            if (datetime.now() - cached.timestamp).total_seconds() < self._cache_ttl:
                return cached

        # Prepare environment
        env = os.environ.copy()
        env.update(check.environment)

        try:
            # Run command
            proc = await asyncio.create_subprocess_shell(
                check.command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=check.working_dir,
                env=env,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=check.timeout_seconds
                )
            except TimeoutError:
                proc.kill()
                await proc.communicate()
                return VerificationResult(
                    task_id=task.id,
                    check_name=check.name,
                    check_type=check.check_type,
                    command=check.command,
                    exit_code=-1,
                    stdout="",
                    stderr=f"Timeout after {check.timeout_seconds}s",
                    passed=False,
                    evidence={"timeout": True},
                    duration_ms=int((datetime.now() - start_time).total_seconds() * 1000),
                )

            exit_code = proc.returncode
            passed = exit_code in check.success_codes

            result = VerificationResult(
                task_id=task.id,
                check_name=check.name,
                check_type=check.check_type,
                command=check.command,
                exit_code=exit_code,
                stdout=stdout.decode()[:5000] if stdout else "",
                stderr=stderr.decode()[:5000] if stderr else "",
                passed=passed,
                evidence={
                    "required": check.required,
                    "gate_type": check.gate_type.value,
                    "description": check.description,
                },
                duration_ms=int((datetime.now() - start_time).total_seconds() * 1000),
            )

            # Cache successful results
            if passed:
                self._check_cache[cache_key] = result

            return result

        except Exception as e:
            return VerificationResult(
                task_id=task.id,
                check_name=check.name,
                check_type=check.check_type,
                command=check.command,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                passed=False,
                evidence={"error": str(e), "required": check.required},
                duration_ms=int((datetime.now() - start_time).total_seconds() * 1000),
            )

    async def run_security_review(self, task: Task) -> bool:
        """
        Run security review for sensitive tasks.
        Requires security-engineer approval.
        """
        if not self._is_security_sensitive(task):
            return True  # Not security-sensitive, auto-pass

        if self.security_review_callback:
            return await self.security_review_callback(task)

        # Default: require explicit approval (would integrate with security-engineer agent)
        self.memory.add_history(
            TaskHistoryEntry(
                task_id=task.id,
                event=TaskEventType.BLOCKED,
                details={
                    "security_review_required": True,
                    "reason": "Task involves security-sensitive changes",
                },
            )
        )

        return False  # Block until reviewed

    def _is_security_sensitive(self, task: Task) -> bool:
        """Check if task involves security-sensitive changes."""
        security_patterns = [
            "auth",
            "secret",
            "password",
            "token",
            "credential",
            "security",
            "vulnerability",
            "encryption",
            "tls",
            "ssl",
            "permission",
            "authorization",
            "rbac",
            "oauth",
            "login",
            "session",
            "cookie",
            "csrf",
            "xss",
            "sql injection",
        ]
        text = (
            f"{task.objective} {' '.join(task.files_involved)} {' '.join(task.constraints)}".lower()
        )
        return any(pattern in text for pattern in security_patterns)

    def _is_api_change(self, task: Task) -> bool:
        """Check if task modifies API contracts."""
        api_patterns = [
            "api",
            "endpoint",
            "route",
            "handler",
            "contract",
            "openapi",
            "swagger",
            "schema",
            "serializer",
        ]
        text = f"{task.objective} {' '.join(task.files_involved)}".lower()
        return any(pattern in text for pattern in api_patterns)

    def _is_build_change(self, task: Task) -> bool:
        """Check if task modifies build configuration."""
        build_patterns = [
            "docker",
            "dockerfile",
            "compose",
            "build",
            "ci",
            "cd",
            "workflow",
            "pipeline",
            "deploy",
            "vercel",
            "kubernetes",
        ]
        text = f"{task.objective} {' '.join(task.files_involved)}".lower()
        return any(pattern in text for pattern in build_patterns)

    def _is_dependency_change(self, task: Task) -> bool:
        """Check if task modifies dependencies."""
        dep_patterns = [
            "dependency",
            "requirements",
            "package.json",
            "pyproject",
            "uv.lock",
            "package-lock",
            "add",
            "install",
            "upgrade",
        ]
        text = f"{task.objective} {' '.join(task.files_involved)}".lower()
        return any(pattern in text for pattern in dep_patterns)

    def get_gate_summary(self) -> dict[str, Any]:
        """Get summary of available verification gates."""
        return {
            "quality_checks": len(self.quality_checks),
            "security_checks": len(self.security_checks),
            "contract_checks": len(self.contract_checks),
            "build_checks": len(self.build_checks),
            "dependency_checks": len(self.dependency_checks),
            "total_checks": len(self.all_checks),
            "checks": [
                {
                    "name": c.name,
                    "type": c.check_type.value,
                    "gate": c.gate_type.value,
                    "required": c.required,
                    "description": c.description,
                }
                for c in self.all_checks
            ],
        }

    def add_custom_check(self, check: VerificationCheck) -> None:
        """Add a custom verification check."""
        self.all_checks.append(check)

    def clear_cache(self) -> None:
        """Clear verification cache."""
        self._check_cache.clear()
