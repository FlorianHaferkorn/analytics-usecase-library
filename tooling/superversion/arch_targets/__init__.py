"""arch_targets — ArchitectureBlueprint → per-stack scaffolding (ADR-0015 / T4+T7).

Parallel to `tooling/superversion/targets` (ADR-0006) but one layer up: the emitters
here consume an `ArchitectureBlueprint` (the five OneLake patterns) instead of a
`CanonicalModel`. Same contract shape — ``emit(blueprint) -> {relative_path: content}``
— so a new stack is a module + one ``register(...)`` call, no core change.

Plan-only by default (emits runbooks/plans, not live provisioning); live `fab`
provisioning stays tenant-gated (see the IR spec §"Still open").
"""
from tooling.superversion.arch_targets.base import (
    ArchAdapter,
    ArchContractError,
    REGISTRY,
    available,
    get,
    register,
    render,
)
from tooling.superversion.arch_targets import fabric as _fabric  # noqa: F401  (registers "fabric")
from tooling.superversion.arch_targets import databricks as _databricks  # noqa: F401  (registers "databricks")
from tooling.superversion.arch_targets import snowflake as _snowflake  # noqa: F401  (registers "snowflake")

__all__ = [
    "ArchAdapter", "ArchContractError", "REGISTRY",
    "available", "get", "register", "render",
]
