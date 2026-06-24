"""engines.gov_engine — governance audit (Beta, task I-5.3).

Beta stand-in for Meridian's ``gov_engine`` (not vendored yet). Audits the
canonical model for governance hygiene: documented measures + the presence of
governance roles. Replaced by the real engine on the same contract when vendored.
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
    for table in sm.tables:
        for m in table.measures:
            if not (m.description or "").strip():
                f.append(EngineFinding("warn", "GOV_MEASURE_UNDOCUMENTED",
                                       f"measure '{m.name}' has no business description"))
    if not sm.roles:
        f.append(EngineFinding("warn", "GOV_NO_ROLES",
                               "model defines no governance/security roles"))
    if mode == "greenfield":
        f.append(EngineFinding("info", "GOV_GREENFIELD",
                               "greenfield: define ownership + RLS roles before first publish"))
    return f


register(EngineAdapter(id="gov", label="Governance audit (Beta)", run=run, status="beta"))
