"""
test_dataarch_mirror_sensor.py — cross-repo drift sensor for the Meridian contract mirror (Tier-3 #8).

The pure diff detects contract drift; ODCS facts extract from real source; the sensor soft-skips when
Meridian is unreachable and (when the sibling checkout is present) reports the mirror as in sync.
"""
from __future__ import annotations

from pathlib import Path

import scripts.check_dataarch_mirror as sensor

_ALUCA_ODCS = Path(__file__).resolve().parents[1] / "superversion" / "odcs.py"


def _contract() -> dict:
    return {
        "arch_default": "medallion", "arch_concepts": ["medallion"],
        "gov_default": "odcs-contract-first",
        "gov_concepts": ["dq-first", "glossary-first", "odcs-contract-first", "purview-data-product"],
        "gov_standards": {"odcs-contract-first": "odcs", "dq-first": None},
        "odcs": {"api_version": "v3.0.0", "public_api": ["to_odcs"]},
    }


def test_diff_empty_when_identical():
    c = _contract()
    assert sensor._diff(c, dict(c)) == []


def test_diff_flags_each_drifted_field():
    mer = _contract()
    alu = _contract()
    alu["arch_concepts"] = ["medallion", "data-vault"]        # Meridian added a concept, ALUCA didn't
    alu["odcs"] = {"api_version": "v3.1.0", "public_api": ["to_odcs"]}
    lines = sensor._diff(mer, alu)
    assert any("arch_concepts" in ln for ln in lines)
    assert any("odcs" in ln for ln in lines)
    assert len(lines) == 2


def test_odcs_facts_extract_from_real_source():
    facts = sensor._odcs_facts(_ALUCA_ODCS)
    assert facts["api_version"] == "v3.0.0"
    for fn in ("to_odcs", "emit_odcs", "from_odcs", "import_sql_table", "validate_odcs"):
        assert fn in facts["public_api"]


def test_soft_skip_when_meridian_absent(monkeypatch):
    monkeypatch.setattr(sensor, "_meridian_root", lambda: None)
    assert sensor.main([]) == 0
    assert sensor.main(["--strict"]) == 0        # soft-skip even under --strict (dev-only diff)


def test_in_sync_when_sibling_present():
    # in this workspace both repos are checked out side by side; the mirror should be in sync.
    if sensor._meridian_root() is None:
        return                                    # sibling not present in this env — nothing to assert
    assert sensor.main([]) == 0
    assert sensor.main(["--strict"]) == 0
