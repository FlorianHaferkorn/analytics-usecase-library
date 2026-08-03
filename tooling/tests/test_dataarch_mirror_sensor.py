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


# -- the SQL→logical type table (the alias the mirror depends on) --------------------


def test_sql_type_map_is_actually_extracted():
    """A regex that matches nothing makes both sides equal and the check vacuous — which
    is exactly how this comparison first shipped. Pin that it finds real entries."""
    pairs = sensor.sql_type_map(_ALUCA_ODCS.read_text(encoding="utf-8"))
    assert pairs, "type table not extracted — the comparison would silently pass"
    assert ["^(tinyint|smallint|int|integer|bigint)\\b", "integer"] in pairs
    assert {logical for _, logical in pairs} == {"integer", "number", "boolean", "date"}


def test_sql_type_map_drift_is_reported():
    """ALUCA does not vendor a second `odcs.py` — the mirrored `source_schema` uses
    ALUCA's own `_logical_type`. If Meridian reclassifies a type, introspected columns
    would get different logical types in each repo without any name changing."""
    mer, alu = _contract(), _contract()
    mer["odcs"] = {"api_version": "v3.0.0", "public_api": ["to_odcs"],
                   "sql_type_map": [["^(bit|bool)\\b", "boolean"]]}
    alu["odcs"] = {"api_version": "v3.0.0", "public_api": ["to_odcs"],
                   "sql_type_map": [["^(bit|bool)\\b", "string"]]}
    assert any("odcs" in ln for ln in sensor._diff(mer, alu))


def test_sql_type_map_survives_a_table_without_entries():
    assert sensor.sql_type_map("nothing here") == []


# -- MIRRORED_FILES is the decision, PIN.json is derived from it --------------------


def test_mirrored_files_matches_the_pin():
    pin = sensor.vendor_pin()
    assert pin is not None
    assert [e["path"] for e in pin["files"]] == list(sensor.MIRRORED_FILES)


def test_declared_but_unmirrored_file_is_reported(tmp_path: Path, monkeypatch):
    """Adding a module to MIRRORED_FILES must show up as drift until --write ran —
    otherwise the declaration would be decorative."""
    monkeypatch.setattr(sensor, "MIRRORED_FILES",
                        sensor.MIRRORED_FILES + ("brand_new_module.py",))
    (tmp_path / "brand_new_module.py").write_text("x = 1\n", encoding="utf-8")
    pin = sensor.vendor_pin()
    findings = sensor.vendor_upstream_drift(pin, tmp_path)
    assert any("brand_new_module.py" in f and "not mirrored yet" in f for f in findings)


def test_undeclared_but_mirrored_file_is_reported(tmp_path: Path, monkeypatch):
    """The reverse: a module dropped from the declaration but still lying in the mirror."""
    monkeypatch.setattr(sensor, "MIRRORED_FILES",
                        tuple(n for n in sensor.MIRRORED_FILES if n != "naming.py"))
    findings = sensor.vendor_upstream_drift(sensor.vendor_pin(), tmp_path)
    assert any("naming.py" in f and "no longer declared" in f for f in findings)


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
