"""layer_tools.packs.base — tool-specific domain-rule packs (task I-5.4, G7).

A **pack** is an additive, platform-specific rule set (Official-First) that layers
on TOP of the generic engines (I-5.3) — the generic rules always remain, so
disabling a pack is a clean rollback (DoD I-5.4: "Rollback: generische Regeln
bleiben"). Each pack ships the publicly-documented *static* rules that can be
checked against the canonical model today; every check that needs a live platform
API (Unity Catalog / Purview / dbt artifacts) is declared in ``planned`` and
surfaced as a ``PACK_PLANNED`` info — never silently dropped (DoD: "API-Zugang
fehlt → Pack als 'geplant'"; no silent caps).

Contract: a ``PackRule.check(canonical) -> list[str]`` returns the names of
offending objects (empty = pass) — pure/deterministic (Invariant I2). Mirrors the
engine seam (`engines/base.py`) so the two compose.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Literal

from tooling.superversion.canonical_contract import CanonicalModel

Severity = Literal["info", "warn", "error"]
Status = Literal["active", "planned", "disabled"]


class PackContractError(ValueError):
    """A pack or its output violates the pack contract."""


@dataclass(frozen=True)
class PackRule:
    code: str
    severity: Severity
    detail: str  # human template; offending names are appended
    check: Callable[[CanonicalModel], list[str]]


@dataclass(frozen=True)
class PackFinding:
    severity: Severity
    code: str
    detail: str


@dataclass(frozen=True)
class Pack:
    id: str
    platform: str
    label: str
    rules: tuple[PackRule, ...] = ()
    planned: tuple[str, ...] = ()  # API-dependent checks deferred ("geplant")
    status: Status = "active"


@dataclass(frozen=True)
class PackReport:
    pack_id: str
    platform: str
    status: Status
    findings: list[PackFinding] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(f.severity == "error" for f in self.findings)

    def counts(self) -> dict[str, int]:
        out = {"info": 0, "warn": 0, "error": 0}
        for f in self.findings:
            out[f.severity] += 1
        return out


REGISTRY: dict[str, Pack] = {}


def register(pack: Pack, *, replace: bool = False) -> Pack:
    if not pack.id:
        raise PackContractError("Pack.id must be non-empty")
    if pack.id in REGISTRY and not replace:
        raise PackContractError(f"pack '{pack.id}' already registered; pass replace=True")
    REGISTRY[pack.id] = pack
    return pack


def get(pack_id: str) -> Pack:
    if pack_id not in REGISTRY:
        raise KeyError(f"Unknown pack '{pack_id}'. Available: {available()}")
    return REGISTRY[pack_id]


def available() -> list[str]:
    return sorted(REGISTRY)


def evaluate(pack_id: str, canonical: CanonicalModel) -> PackReport:
    """Run a pack's static rules + surface its planned (API-dependent) checks.

    A ``disabled`` pack (rollback) returns an empty report — the generic engine
    rules still apply, so coverage degrades gracefully rather than breaking."""
    pack = get(pack_id)
    if pack.status == "disabled":
        return PackReport(pack.id, pack.platform, "disabled", [])
    findings: list[PackFinding] = []
    for rule in pack.rules:
        offenders = rule.check(canonical)
        if not isinstance(offenders, list):
            raise PackContractError(f"rule '{rule.code}'.check() must return list[str]")
        for name in offenders:
            findings.append(PackFinding(rule.severity, rule.code, f"{rule.detail}: '{name}'"))
    for item in pack.planned:
        findings.append(PackFinding("info", "PACK_PLANNED",
                                    f"geplant (braucht Plattform-API): {item}"))
    return PackReport(pack.id, pack.platform, pack.status, findings)
