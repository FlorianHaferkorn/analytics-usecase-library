"""targets — Superversion target (stack) adapter contract + registry (ADR-0006).

Mirror of Meridian's target-adapter pattern (its ADR-0036,
`core/pbi_engine/target/registry.py`), brought into ALUCA as its own contract so
the Superversion layer can emit stack syntax FROM the canonical model:

  - one contract: ``emit(canonical) -> {relative_path: content}``
  - a registry + generic ``render(stack_id, canonical, dest)`` dispatch
  - a new stack = a module with ``emit()`` + one ``register(...)`` call — no core change

This module defines the **contract only** (task I-3.1). Concrete adapters are
separate tasks: TMDL/semantic emit (I-3.2), PBIR report via the official MS skill
(I-3.3). The registry therefore starts empty here.

Field names + the `emit` signature are kept IDENTICAL to Meridian's `TargetAdapter`
so the seam is 1:1 portable when ALUCA docks onto Meridian (ADR-0005 "dock, don't
rebuild"). `CanonicalModel` is imported through the contract seam
(`canonical_contract`), never `core.pbi_engine` directly (ADR-0005 rule 4).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Protocol, runtime_checkable

from tooling.superversion.canonical_contract import CanonicalModel

__all__ = [
    "TargetEmitter", "TargetAdapter", "TargetContractError",
    "REGISTRY", "register", "get", "available", "render",
]


class TargetContractError(ValueError):
    """An adapter or its emit() output violates the target contract."""


@runtime_checkable
class TargetEmitter(Protocol):
    """The emit contract: pure map from the canonical model to files.

    Returns ``{relative_path: text_content}`` — deterministic (Invariant I2), no
    side effects, no I/O. The registry's ``render()`` does the writing.
    """

    def __call__(self, canonical: CanonicalModel) -> dict[str, str]: ...


@dataclass(frozen=True)
class TargetAdapter:
    """A registered stack target. Field names mirror Meridian's `TargetAdapter`
    (ADR-0036) for 1:1 portability; `status` defaults to ``geplant`` because ALUCA
    registers concrete adapters only from I-3.2 onward."""
    id: str
    label: str
    fmt: str
    emit: Callable[[CanonicalModel], dict]
    data_platform: str = "beliebig"
    visualization: str = ""
    status: str = "geplant"  # geplant | live


REGISTRY: dict[str, TargetAdapter] = {}


def register(adapter: TargetAdapter, *, replace: bool = False) -> TargetAdapter:
    """Register a target adapter by id.

    Raises on an id collision (two stacks shadowing each other is a silent bug, SA
    review m3) unless ``replace=True`` is passed deliberately.
    """
    if not adapter.id:
        raise TargetContractError("TargetAdapter.id must be non-empty")
    if adapter.id in REGISTRY and not replace:
        raise TargetContractError(
            f"target id '{adapter.id}' already registered; pass replace=True to override"
        )
    REGISTRY[adapter.id] = adapter
    return adapter


def get(stack_id: str) -> TargetAdapter:
    if stack_id not in REGISTRY:
        raise KeyError(f"Unknown target stack '{stack_id}'. Available: {available()}")
    return REGISTRY[stack_id]


def available() -> list[str]:
    return sorted(REGISTRY)


def render(stack_id: str, canonical: CanonicalModel, dest: Path) -> list[Path]:
    """Generic dispatch: emit via the registered adapter, write under ``dest``.

    Validates the emit contract (``{str: str}``) before writing — a contract
    breach fails loudly (`TargetContractError`) rather than writing garbage.
    Returns the written paths in deterministic (emit-insertion) order.
    """
    emitted = get(stack_id).emit(canonical)
    if not isinstance(emitted, dict):
        raise TargetContractError(
            f"adapter '{stack_id}'.emit() must return a dict, got {type(emitted).__name__}"
        )
    dest = Path(dest).resolve()
    written: list[Path] = []
    for rel, content in emitted.items():
        if not isinstance(rel, str) or not isinstance(content, str):
            raise TargetContractError(
                f"adapter '{stack_id}'.emit() must return {{str: str}}; "
                f"got key {type(rel).__name__}, value {type(content).__name__}"
            )
        # Containment: emit keys are relative paths under dest — reject absolute
        # paths and `..` traversal so a buggy adapter cannot write outside dest.
        p = (dest / rel).resolve()
        if Path(rel).is_absolute() or dest not in p.parents and p != dest:
            raise TargetContractError(
                f"adapter '{stack_id}'.emit() path '{rel}' escapes the destination"
            )
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8", newline="\n")
        written.append(p)
    return written
