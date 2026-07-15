"""arch_targets.base — the ArchitectureBlueprint target-adapter contract + registry.

Mirrors `tooling/superversion/targets/base.py` (ADR-0006) field-for-field, but the
emit input is an `ArchitectureBlueprint` dict (validated by
`tooling/generator/schemas/architecture_blueprint.schema.json`).

  - one contract: ``emit(blueprint) -> {relative_path: content}`` (pure, deterministic)
  - a registry + generic ``render(stack_id, blueprint, dest)`` dispatch
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Protocol, runtime_checkable

__all__ = [
    "ArchEmitter", "ArchAdapter", "ArchContractError",
    "REGISTRY", "register", "get", "available", "render",
]


class ArchContractError(ValueError):
    """An adapter or its emit() output violates the arch-target contract."""


@runtime_checkable
class ArchEmitter(Protocol):
    def __call__(self, blueprint: dict) -> dict[str, str]: ...


@dataclass(frozen=True)
class ArchAdapter:
    id: str
    label: str
    emit: Callable[[dict], dict]
    status: str = "live"  # plan-only renderers are still "live" adapters


REGISTRY: dict[str, ArchAdapter] = {}


def register(adapter: ArchAdapter, *, replace: bool = False) -> ArchAdapter:
    if adapter.id in REGISTRY and not replace:
        raise ArchContractError(f"arch-target id already registered: {adapter.id!r}")
    REGISTRY[adapter.id] = adapter
    return adapter


def get(stack_id: str) -> ArchAdapter:
    if stack_id not in REGISTRY:
        raise ArchContractError(f"no arch-target registered for {stack_id!r}; have {available()}")
    return REGISTRY[stack_id]


def available() -> list[str]:
    return sorted(REGISTRY)


def _validate_emit(out: dict) -> dict[str, str]:
    if not isinstance(out, dict) or not out:
        raise ArchContractError("emit() must return a non-empty {path: content} dict")
    for path, content in out.items():
        if not isinstance(path, str) or path.startswith("/") or ".." in path:
            raise ArchContractError(f"emit() produced an unsafe relative path: {path!r}")
        if not isinstance(content, str):
            raise ArchContractError(f"emit() content for {path!r} must be str")
    return out


def render(stack_id: str, blueprint: dict, dest: Path | None = None) -> dict[str, str]:
    """Emit the scaffolding for a stack. If ``dest`` is given, also write the files.

    Returns the ``{relative_path: content}`` map (pure output), so callers can test
    without touching disk.
    """
    out = _validate_emit(get(stack_id).emit(blueprint))
    if dest is not None:
        dest = Path(dest)
        for rel, content in out.items():
            target = dest / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
    return out
