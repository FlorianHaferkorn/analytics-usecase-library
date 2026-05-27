"""Shared model types for report quality checks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Severity = Literal["critical", "warning", "info"]


@dataclass(frozen=True)
class Violation:
    """A single quality violation with a file-oriented pointer."""

    check: str
    severity: Severity
    pointer: str
    message: str
    expected: object | None = None
    actual: object | None = None

    def __str__(self) -> str:
        expected = f" expected={self.expected!r}" if self.expected is not None else ""
        actual = f" actual={self.actual!r}" if self.actual is not None else ""
        return f"[{self.severity.upper()}] {self.check} @ {self.pointer}: {self.message}{expected}{actual}"


def violations_summary(violations: list[Violation]) -> dict[str, int]:
    """Count violations by severity."""

    return {
        "critical": sum(1 for v in violations if v.severity == "critical"),
        "warning": sum(1 for v in violations if v.severity == "warning"),
        "info": sum(1 for v in violations if v.severity == "info"),
    }
