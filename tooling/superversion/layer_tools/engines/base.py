"""layer_tools.engines.base — gov/eng/arch engine-adapter contract (task I-5.3).

Meridian owns the real ``gov_engine`` / ``dataarch_engine`` / ``dataeng_engine``
(dual-modal: ingest existing + greenfield). They are NOT vendored yet (only
``pbi_engine`` is), so I-5.3 ships the **seam** they dock onto — a registry +
generic dispatch mirroring the target-adapter contract (ADR-0006) — plus honest
**Beta** engines that run against the canonical model today. When the real
engines are vendored, they replace the Beta runners on the same contract
("dock, don't rebuild"); until then status stays ``beta`` (Ehrlichkeit v3:
never label a stub ready).

Contract: ``run(canonical, mode) -> list[EngineFinding]`` — pure, deterministic
(Invariant I2). Each engine runs standalone against a bare CanonicalModel AND
integrates via the registry (Invariant I4).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Literal, Protocol, runtime_checkable

from tooling.superversion.canonical_contract import CanonicalModel

Mode = Literal["ingest", "greenfield"]
Severity = Literal["info", "warn", "error"]
Status = Literal["beta", "ready", "disabled"]


class EngineContractError(ValueError):
    """An engine or its output violates the engine contract."""


@dataclass(frozen=True)
class EngineFinding:
    severity: Severity
    code: str
    detail: str


@dataclass(frozen=True)
class EngineReport:
    engine_id: str
    mode: Mode
    status: Status
    findings: list[EngineFinding] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        """No error-severity finding. Beta engines surface warnings, not errors,
        so a Beta run is `ok` unless it hits a hard error."""
        return not any(f.severity == "error" for f in self.findings)

    def counts(self) -> dict[str, int]:
        out = {"info": 0, "warn": 0, "error": 0}
        for f in self.findings:
            out[f.severity] += 1
        return out


@runtime_checkable
class EngineRunner(Protocol):
    def __call__(self, canonical: CanonicalModel, mode: Mode) -> list[EngineFinding]: ...


@dataclass(frozen=True)
class EngineAdapter:
    id: str
    label: str
    run: Callable[[CanonicalModel, Mode], list[EngineFinding]]
    modes: tuple[Mode, ...] = ("ingest", "greenfield")
    status: Status = "beta"


REGISTRY: dict[str, EngineAdapter] = {}


def register(adapter: EngineAdapter, *, replace: bool = False) -> EngineAdapter:
    if not adapter.id:
        raise EngineContractError("EngineAdapter.id must be non-empty")
    if adapter.id in REGISTRY and not replace:
        raise EngineContractError(f"engine '{adapter.id}' already registered; pass replace=True")
    REGISTRY[adapter.id] = adapter
    return adapter


def get(engine_id: str) -> EngineAdapter:
    if engine_id not in REGISTRY:
        raise KeyError(f"Unknown engine '{engine_id}'. Available: {available()}")
    return REGISTRY[engine_id]


def available() -> list[str]:
    return sorted(REGISTRY)


def run(engine_id: str, canonical: CanonicalModel, mode: Mode = "ingest") -> EngineReport:
    """Generic dispatch: run a registered engine and wrap its findings in a report.

    A ``disabled`` engine (rollback) returns an empty report without running."""
    adapter = get(engine_id)
    if mode not in adapter.modes:
        raise EngineContractError(f"engine '{engine_id}' does not support mode '{mode}' "
                                  f"(modes: {adapter.modes})")
    if adapter.status == "disabled":
        return EngineReport(engine_id, mode, "disabled", [])
    findings = adapter.run(canonical, mode)
    if not isinstance(findings, list) or any(not isinstance(f, EngineFinding) for f in findings):
        raise EngineContractError(f"engine '{engine_id}'.run() must return list[EngineFinding]")
    return EngineReport(engine_id, mode, adapter.status, findings)
