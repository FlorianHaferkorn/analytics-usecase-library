"""Pluggable validation backends and capability tiers.

Implements the design in ADR 0001
(``docs/architecture/adr/0001-pluggable-validation-backends-and-capability-tiers.md``).

Tier 0 (:class:`NativeBackend`) is pure Python and always available -- it is the
guaranteed floor. Higher tiers wrap optional external CLIs and are OFF by
default ("compliance mode"): they activate only when explicitly opted in via the
``PBI_QUALITY_ALLOW_EXTERNAL`` environment variable AND the tool is found on
PATH.

Capability *detection* never executes anything (it only inspects PATH); only an
opted-in :meth:`ValidationBackend.validate` shells out to an external process.
This mirrors the existing graceful-skip precedent in
``products/fabric/powerbi/tooling/validation/check_with_pbi_cli.ps1``.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from .models import Severity, Violation

# Environment flag that opts in to ANY external (non-Python) backend.
# Unset / falsey == compliance mode: nothing external runs by default.
ALLOW_EXTERNAL_ENV = "PBI_QUALITY_ALLOW_EXTERNAL"
_TRUTHY = {"1", "true", "yes", "on"}


def external_allowed(env: Mapping[str, str] | None = None) -> bool:
    """Return ``True`` only when external backends are explicitly opted in."""
    source = os.environ if env is None else env
    return source.get(ALLOW_EXTERNAL_ENV, "").strip().lower() in _TRUTHY


@dataclass(frozen=True)
class BackendStatus:
    """Detection result for one backend. Producing it never executes the tool."""

    name: str
    tier: int
    available: bool
    detail: str

    def __str__(self) -> str:
        state = "active" if self.available else "inactive"
        return f"[Tier {self.tier}] {self.name}: {state} -- {self.detail}"


class ValidationBackend(ABC):
    """A source of report-quality violations, organised into a capability tier."""

    name: str = "backend"
    tier: int = -1
    requires_external: bool = False

    @abstractmethod
    def is_available(self, *, allow_external: bool) -> bool:
        """Whether this backend can run now (no side effects, no execution)."""

    @abstractmethod
    def status(self, *, allow_external: bool) -> BackendStatus:
        """Human-readable detection result for ``doctor`` output."""

    @abstractmethod
    def validate(self, dist_root: Path) -> list[Violation]:
        """Return violations for every report under ``dist_root`` (may be empty)."""


class NativeBackend(ValidationBackend):
    """Tier 0 floor: pure-Python validation. Always available, no dependencies."""

    name = "native"
    tier = 0
    requires_external = False

    def is_available(self, *, allow_external: bool = False) -> bool:
        return True

    def status(self, *, allow_external: bool = False) -> BackendStatus:
        return BackendStatus(self.name, self.tier, True, "pure-Python floor (no external dependencies)")

    def validate(self, dist_root: Path) -> list[Violation]:
        # Delegate to the canonical native validator (lazy import avoids a cycle).
        from .cli import validate as _native_validate

        return _native_validate(dist_root)


class ExternalCliBackend(ValidationBackend):
    """Base for backends that wrap an external CLI with graceful skip semantics."""

    requires_external = True
    cli: str = ""

    def _on_path(self) -> bool:
        return bool(self.cli) and shutil.which(self.cli) is not None

    def is_available(self, *, allow_external: bool) -> bool:
        return allow_external and self._on_path()

    def status(self, *, allow_external: bool) -> BackendStatus:
        on_path = self._on_path()
        if not allow_external:
            where = "found on PATH" if on_path else "not on PATH"
            detail = f"opt-in required -- set {ALLOW_EXTERNAL_ENV}=1 ({where})"
            return BackendStatus(self.name, self.tier, False, detail)
        if not on_path:
            return BackendStatus(self.name, self.tier, False, f"'{self.cli}' not found on PATH")
        return BackendStatus(self.name, self.tier, True, f"'{self.cli}' on PATH, opted in")


class MicrosoftReportAuthorBackend(ExternalCliBackend):
    """Tier 1 oracle: Microsoft's official ``powerbi-report-author`` CLI.

    Runs the official offline preflight (``--no-schema``) per ``.Report``
    directory and parses the structured ``diagnostics`` envelope into
    :class:`Violation` objects. Because this tier is opt-in, official ``error``
    diagnostics map to ``critical`` and ``warning`` to ``warning``; anything else
    is ``info``. It only ever augments -- when not opted in it returns nothing and
    never touches an external process.
    """

    name = "powerbi-report-author"
    tier = 1
    cli = "powerbi-report-author"

    # Official diagnostic severity -> our severity. Tier 1 is opt-in, so blocking
    # PBIR errors surface as critical.
    _SEVERITY_MAP: dict[str, Severity] = {"error": "critical", "warning": "warning"}

    def validate(self, dist_root: Path) -> list[Violation]:
        if not self.is_available(allow_external=external_allowed()):
            return []  # graceful skip -- never touches an external process
        from .pbir import iter_report_dirs

        violations: list[Violation] = []
        for report_dir in iter_report_dirs(dist_root):
            violations.extend(self._validate_one(report_dir))
        return violations

    def _validate_one(self, report_dir: Path) -> list[Violation]:
        try:
            proc = subprocess.run(
                [self.cli, "validate", str(report_dir), "--no-schema", "--format", "json"],
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
                encoding="utf-8", errors="replace")
        except (OSError, subprocess.SubprocessError) as exc:
            return [
                Violation(
                    check="backend.powerbi-report-author",
                    severity="info",
                    pointer=str(report_dir),
                    message=f"external validator could not run: {exc}",
                )
            ]
        return self._parse(proc, report_dir)

    def _parse(self, proc: subprocess.CompletedProcess[str], report_dir: Path) -> list[Violation]:
        try:
            data = json.loads(proc.stdout)["data"]
            diagnostics = data["diagnostics"]
        except (json.JSONDecodeError, KeyError, TypeError):
            # Unparseable output: fall back to a single advisory keyed on exit code.
            if proc.returncode == 0:
                return []
            output = (proc.stdout + proc.stderr).strip().splitlines()
            message = output[0][:200] if output else f"exit code {proc.returncode}"
            return [
                Violation(
                    check="backend.powerbi-report-author",
                    severity="warning",
                    pointer=str(report_dir),
                    message=f"official validator reported issues: {message}",
                )
            ]

        violations: list[Violation] = []
        for code, entry in (diagnostics or {}).items():
            severity = self._SEVERITY_MAP.get((entry or {}).get("severity", ""), "info")
            for item in entry.get("items") or []:
                violations.append(self._to_violation(code, severity, item, report_dir))
        return violations

    @staticmethod
    def _to_violation(code: str, severity: Severity, item: dict, report_dir: Path) -> Violation:
        file = item.get("file") or str(report_dir)
        try:
            pointer = Path(file).resolve().relative_to(Path.cwd()).as_posix()
        except ValueError:
            pointer = file
        json_path = item.get("path")
        if json_path:
            pointer = f"{pointer}#{json_path}"
        message = item.get("message", "")
        if file and file in message:  # strip the trailing absolute path the CLI appends
            message = message.split(file)[0].rstrip(": ").rstrip()
        return Violation(
            check=f"powerbi-report-author.{code}",
            severity=severity,
            pointer=pointer,
            message=message[:200] or code,
        )


def all_backends() -> list[ValidationBackend]:
    """Every known backend, ordered by ascending tier."""
    return [NativeBackend(), MicrosoftReportAuthorBackend()]


def _resolve_allow(allow_external: bool | None) -> bool:
    return external_allowed() if allow_external is None else allow_external


def tier_report(*, allow_external: bool | None = None) -> list[BackendStatus]:
    """Detection result for every backend (for ``doctor``). Never executes a tool."""
    allow = _resolve_allow(allow_external)
    return [backend.status(allow_external=allow) for backend in all_backends()]


def active_backends(*, allow_external: bool | None = None) -> list[ValidationBackend]:
    """Backends that can run right now, given the compliance opt-in state."""
    allow = _resolve_allow(allow_external)
    return [backend for backend in all_backends() if backend.is_available(allow_external=allow)]


def active_tier(*, allow_external: bool | None = None) -> int:
    """Highest tier currently active (always >= 0 because Tier 0 is the floor)."""
    return max((backend.tier for backend in active_backends(allow_external=allow_external)), default=0)
