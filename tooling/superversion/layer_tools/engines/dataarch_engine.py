"""engines.dataarch_engine — data-architecture audit (Beta, task I-5.3).

Beta stand-in for Meridian's ``dataarch_engine`` (not vendored yet). Audits the
canonical model's shape: relationships (star schema), table naming, a date table.
"""
from __future__ import annotations

from tooling.superversion.canonical_contract import CanonicalModel
from tooling.superversion.layer_tools.engines.base import (
    EngineAdapter,
    EngineFinding,
    Mode,
    register,
)


def run(canonical: CanonicalModel, mode: Mode) -> list[EngineFinding]:
    f: list[EngineFinding] = []
    sm = canonical.semantic
    if len(sm.tables) > 1 and not sm.relationships:
        f.append(EngineFinding("warn", "ARCH_NO_RELATIONSHIPS",
                               f"{len(sm.tables)} tables but no relationships (no star schema)"))
    for t in sm.tables:
        if not (t.name.startswith("fact_") or t.name.startswith("dim_")):
            f.append(EngineFinding("info", "ARCH_TABLE_NAMING",
                                   f"table '{t.name}' not prefixed fact_/dim_"))
    if not any(getattr(t, "is_date_table", False) for t in sm.tables):
        f.append(EngineFinding("info", "ARCH_NO_DATE_TABLE",
                               "no date table marked (time intelligence relies on one)"))
    return f


register(EngineAdapter(id="dataarch", label="Data-architecture audit (Beta)", run=run, status="beta"))
