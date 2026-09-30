"""Copilot readiness ("Prep data for AI") for ALUCA use cases — I-21 W3.2, Meridian D-579.

Mirrored Meridian kernel + ALUCA adapter. Checked here:
  * the mirror is byte-identical to its PIN and closes over the standard library,
  * the import bridge answers only its two names,
  * the adapter fills the intermediate form from catalog, bracket, action codes, contracts,
  * Golden Thread: every KPI id in the output exists in the catalog; an unknown id fails,
  * determinism: two runs are byte-identical,
  * golden output: the committed ``dist/copilot_readiness/COM-001_*`` equals a fresh render,
  * parity: the output carries the format signature of a real Meridian run,
  * the output agrees with the generated semantic model (tables, hidden keys, measures).
"""
from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

import pytest
import yaml

from products.fabric.powerbi.tooling.copilot_readiness import _vendor, adapter, parity
from products.fabric.powerbi.tooling.copilot_readiness.__main__ import main as cli_main

REPO = Path(__file__).resolve().parents[5]
DIST = REPO / "products" / "fabric" / "powerbi" / "dist"
GOLDEN = DIST / "copilot_readiness" / "COM-001_Sales_Performance"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "copilot_readiness" / "meridian_format.json"
KPI_RE = re.compile(r"KPI-[A-Z]+-\d{3}")


@pytest.fixture(scope="module")
def com001() -> dict[str, str]:
    return adapter.render_all("COM-001")


# -- mirror + bridge ----------------------------------------------------------------


def test_mirror_is_byte_identical_to_its_pin():
    pin = _vendor.verify()
    assert [e["path"] for e in pin["files"]] == [f"{m}.py" for m in _vendor.KERNEL_MODULES]
    assert _vendor.integrity_findings(_vendor.VENDOR_DIR, pin) == []


def test_mirror_closes_over_stdlib_and_itself():
    """Every import of a mirrored module is stdlib or a mirrored sibling (measured hull)."""
    own = "products.meridian_copilot_readiness.generator"
    for path in sorted(_vendor.VENDOR_DIR.glob("*.py")):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.ImportFrom) and node.module:
                mod = node.module
            elif isinstance(node, ast.Import):
                mods = [a.name for a in node.names]
                assert all(m.split(".")[0] in sys.stdlib_module_names for m in mods), (path.name, mods)
                continue
            else:
                continue
            if mod.startswith(own):
                assert mod.rsplit(".", 1)[1] in _vendor.KERNEL_MODULES, (path.name, mod)
            else:
                assert mod.split(".")[0] in sys.stdlib_module_names | {"__future__"}, (path.name, mod)


def test_bridge_answers_only_its_two_names():
    _vendor.load_kernel()
    finder = next(f for f in sys.meta_path if isinstance(f, _vendor._VendorFinder))
    assert finder.find_spec("products.meridian_copilot_readiness") is not None
    assert finder.find_spec("products.meridian_copilot_readiness.generator") is not None
    for other in ("products", "products.fabric", "core", "products.meridian_copilot_readiness.x"):
        assert finder.find_spec(other) is None
    import products.fabric.powerbi.tooling.copilot_readiness as own  # ALUCA namespace untouched
    assert own.__name__.startswith("products.fabric")


def test_a_local_edit_makes_the_kernel_unavailable(tmp_path, monkeypatch):
    fake = tmp_path / "vendor"
    fake.mkdir()
    for f in (p for p in _vendor.VENDOR_DIR.iterdir() if p.is_file()):
        (fake / f.name).write_bytes(f.read_bytes())
    (fake / "loader.py").write_bytes((fake / "loader.py").read_bytes() + b"# hand edit\n")
    monkeypatch.setattr(_vendor, "VENDOR_DIR", fake)
    monkeypatch.setattr(_vendor, "PIN_PATH", fake / "PIN.json")
    with pytest.raises(_vendor.VendorUnavailable, match="loader.py"):
        _vendor.verify()


# -- adapter ------------------------------------------------------------------------


def test_adapter_fills_the_intermediate_form_from_governed_sources():
    core = adapter.build_core("COM-001")
    bracket = yaml.safe_load((REPO / "core/usecases/core/COM-001_Sales_Performance/UseCase_Bracket.yaml")
                             .read_text(encoding="utf-8"))
    ids = [k["id"] for k in core.kpis]
    assert ids == adapter.scope_kpi_ids(bracket)
    assert ids[0] == bracket["orchestration"]["strategic_kpi_id"] == core.north_star_kpi_id()
    by_id = {k["id"]: k for k in core.kpis}
    # Alert threshold = L1 trigger of C-S1.2 on KPI-COM-009 (lt -2.0 %), referenced, not invented.
    assert by_id["KPI-COM-009"]["targets"] == {"alert_threshold": {"value": -2.0}}
    assert by_id["KPI-COM-009"]["definition"]["unit"] == "%"
    # No strategic target/baseline exists in the catalog — none is made up.
    assert all("strategic_target" not in k["targets"] and "baseline" not in k["targets"] for k in core.kpis)
    assert by_id["KPI-COM-005"]["meta"]["owner"] == "Head of Sales"
    assert {g["term"] for g in core.glossary} == {"GM%", "Gross Margin Rate", "Bruttomarge %"}
    assert [d["name"].split()[0] for d in core.decision_calendar] == bracket["orchestration"]["action_code_ids"]


def test_every_unit_format_in_the_catalog_is_mapped():
    formats = {str((yaml.safe_load(p.read_text(encoding="utf-8")).get("business") or {}).get("unit_format") or "")
               for p in (REPO / "core/kpi_catalog/kpis").glob("KPI-*.yaml")}
    assert formats - {""} <= set(adapter.UNIT_BY_FORMAT)


def test_catalog_synonyms_reach_the_candidates(com001):
    cands = {c["kpi_id"]: c for c in json.loads(com001["verified_answer_candidates.json"])["candidates"]}
    assert cands["KPI-COM-013"]["synonyms"] == ["GM%", "Gross Margin Rate", "Bruttomarge %"]
    assert all(c["approval"]["approved"] is False and "KANDIDAT" in c["status"] for c in cands.values())
    assert all(1 <= len(c["trigger_phrases"]) <= 3 for c in cands.values())


def test_provenance_names_aluca_not_the_meridian_core(com001):
    kernel = _vendor.load_kernel()
    core = adapter.build_core("COM-001")
    assert adapter.KERNEL_PROVENANCE_PREFIX in kernel["instructions"].render_markdown(core)
    for name in ("ai_instructions.md", "ai_instructions.txt"):
        assert "Meridian Core" not in com001[name]
        assert adapter.ALUCA_PROVENANCE_PREFIX in com001[name]


# -- Golden Thread ------------------------------------------------------------------


def test_output_references_only_catalog_kpis(com001):
    catalog = {p.stem for p in (REPO / "core/kpi_catalog/kpis").glob("KPI-*.yaml")}
    found = set()
    for text in com001.values():
        found |= set(KPI_RE.findall(text))
    assert found and found <= catalog, found - catalog


def _mini_repo(tmp_path: Path, kpi_ids: list[str]) -> adapter.AlucaSources:
    root = tmp_path / "repo"
    uc = root / "core/usecases/core/TST-001_Test"
    uc.mkdir(parents=True)
    (uc / "UseCase_Bracket.yaml").write_text(yaml.safe_dump({
        "id": "TST-001", "title": "Test", "domain": "Test",
        "governance": {"owner_role": "tester"},
        "orchestration": {"strategic_kpi_id": kpi_ids[0], "influencing_kpi_ids": kpi_ids[1:],
                          "action_code_ids": []},
    }), encoding="utf-8")
    kpis = root / "core/kpi_catalog/kpis"
    kpis.mkdir(parents=True)
    (kpis / "KPI-TST-001.yaml").write_text(yaml.safe_dump({
        "kpi_id": "KPI-TST-001", "kpi_key": "Test Amount", "good_is": "higher",
        "business": {"definition": "Sum of test.", "unit_format": "eur_0"},
        "technical": {"measure_name": "Test Amount", "lineage": ["fact_test.Amount"]},
        "governance": {"business_owner": "Owner"},
    }), encoding="utf-8")
    (root / "core/action_codes").mkdir(parents=True)
    (root / "core/organization").mkdir(parents=True)
    (root / "core/organization/org_roles.yaml").write_text(
        yaml.safe_dump({"roles": [{"id": "tester", "title": "Tester"}]}), encoding="utf-8")
    contracts = root / "core/data_contracts/domains"
    contracts.mkdir(parents=True)
    (contracts / "test.yaml").write_text(yaml.safe_dump({
        "domain": "test", "owner": "Test Data Product",
        "fact": [{"name": "fact_test", "columns": [{"name": "DateKey", "type": "int", "ref": "dim_date"},
                                                   {"name": "Amount", "type": "currency", "agg": "sum"}]}],
    }), encoding="utf-8")
    (root / "products/fabric/powerbi/dist").mkdir(parents=True)
    return adapter.AlucaSources(repo_root=root)


def test_an_unknown_kpi_is_an_error_not_a_skip(tmp_path):
    src = _mini_repo(tmp_path, ["KPI-TST-001", "KPI-TST-999"])
    with pytest.raises(adapter.GoldenThreadError, match="KPI-TST-999"):
        adapter.build_core("TST-001", src)


def test_mini_repo_renders_with_derivation_from_contracts(tmp_path):
    src = _mini_repo(tmp_path, ["KPI-TST-001"])
    files = adapter.render_all("TST-001", src)
    schema = json.loads(files["ai_data_schema.json"])
    assert schema["_derivation"] == "data_architecture"
    (table,) = schema["tables"]
    assert table["name"] == "fact_test" and table["recommendation"] == "include"
    assert {f["name"]: f["recommendation"] for f in table["fields"]} == {"DateKey": "exclude", "Amount": "include"}
    assert "Test Amount (KPI-TST-001)" in files["ai_instructions.md"]


# -- determinism + golden output -----------------------------------------------------


def test_two_runs_are_byte_identical(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    assert cli_main(["-u", "COM-001", "-o", str(a)]) == 0
    assert cli_main(["-u", "COM-001", "-o", str(b)]) == 0
    names = sorted(p.name for p in a.iterdir())
    assert names == sorted(adapter.render_all("COM-001"))
    for name in names:
        assert (a / name).read_bytes() == (b / name).read_bytes(), name


def test_committed_output_is_the_current_render():
    """dist/ is generated: a stale file is a failure (regenerate, never hand-edit)."""
    assert cli_main(["-u", "COM-001", "--check"]) == 0


# -- parity with Meridian ------------------------------------------------------------


def test_format_signature_equals_a_real_meridian_run(com001):
    ref = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert ref["source_commit"] == _vendor.read_pin()["source_commit"], (
        "kernel re-mirrored: refresh the Meridian format fixture (see parity.py)")
    sig = parity.signature(com001)
    assert sig["json_key_paths"] == ref["json_key_paths"]
    assert sig["md_sections"] == ref["md_sections"]
    assert sig["txt_sections"] == ref["txt_sections"]


# -- agreement with the generated semantic model ------------------------------------


def _model_tables() -> dict[str, str]:
    out: dict[str, str] = {}
    for tmdl in sorted(DIST.glob("*.SemanticModel/definition/tables/*.tmdl")):
        out.setdefault(tmdl.stem, tmdl.read_text(encoding="utf-8"))
    return out


def _hidden_columns(tmdl: str) -> set[str]:
    hidden, current = set(), None
    for line in tmdl.splitlines():
        m = re.match(r"^\tcolumn '?([^'=]+?)'?\s*(=.*)?$", line)
        if m:
            current = m.group(1)
        elif current and line.strip() == "isHidden":
            hidden.add(current)
    return hidden


def test_schema_matches_the_generated_model(com001):
    tables = _model_tables()
    schema = json.loads(com001["ai_data_schema.json"])
    for table in schema["tables"]:
        assert table["name"] in tables, table["name"]
        hidden = _hidden_columns(tables[table["name"]])
        excluded = {f["name"] for f in table["fields"] if f["recommendation"] == "exclude"}
        assert excluded and excluded <= hidden, excluded - hidden


def test_visual_hints_name_measures_of_the_generated_model(com001):
    measures = set()
    for tmdl in DIST.glob("*.SemanticModel/definition/tables/*.tmdl"):
        measures |= set(re.findall(r"^\tmeasure '?([^'=]+?)'?\s*=", tmdl.read_text(encoding="utf-8"), re.M))
    for cand in json.loads(com001["verified_answer_candidates.json"])["candidates"]:
        m = re.search(r"Measure '([^']+)'", cand["visual_hint"])
        assert m and m.group(1) in measures, (cand["kpi_id"], cand["visual_hint"])
