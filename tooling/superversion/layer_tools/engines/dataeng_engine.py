"""engines.dataeng_engine — data-engineering audit (Beta STUB, task I-5.3).

The thinnest of the three (Ehrlichkeit v3: explicitly a stub, ledgered as Beta).
Beta stand-in for Meridian's ``dataeng_engine`` (not vendored yet). Today it only
flags whether tables carry an ingest definition (partition / M expression); real
pipeline/lineage analysis arrives with the vendored engine.
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
    f: list[EngineFinding] = [
        EngineFinding("info", "ENG_STUB",
                      "dataeng engine is a Beta stub — real pipeline/lineage checks "
                      "land with Meridian's vendored dataeng_engine"),
    ]
    sm = canonical.semantic
    for t in sm.tables:
        has_ingest = getattr(t, "has_partition", False) or (getattr(t, "m_expression", "") or "").strip()
        if not has_ingest:
            f.append(EngineFinding("info", "ENG_NO_INGEST_DEF",
                                   f"table '{t.name}' has no partition/M ingest definition"))
    return f


register(EngineAdapter(id="dataeng", label="Data-engineering audit (Beta stub)", run=run, status="beta"))
