"""Guards for the machine-readable KPI SSOT (Phase A streamline refactor).

The source of truth for KPIs is one file per KPI under
``core/kpi_catalog/kpis/<kpi_id>.yaml``. ``KPI_Catalog.md`` is a *generated
view*. These tests ensure the two never silently diverge and that every
per-entity file validates against the KPI schema.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
KPIS = REPO / "core/kpi_catalog/kpis"
MD = REPO / "core/kpi_catalog/KPI_Catalog.md"
SCHEMA = REPO / "tooling/generator/schemas/kpi_definition.schema.json"


def _md_entries() -> dict:
    block = MD.read_text(encoding="utf-8").split("```yaml", 1)[1].rsplit("```", 1)[0]
    return {e["kpi_id"]: e for e in yaml.safe_load(block)}


def _file_entries() -> dict:
    order = yaml.safe_load((KPIS / "_index.yaml").read_text(encoding="utf-8"))["order"]
    return {kid: yaml.safe_load((KPIS / f"{kid}.yaml").read_text(encoding="utf-8")) for kid in order}


def test_view_matches_per_entity_files():
    md, files = _md_entries(), _file_entries()
    assert md.keys() == files.keys(), (
        f"id mismatch — only_view={md.keys() - files.keys()} only_files={files.keys() - md.keys()}"
    )
    drift = [k for k in md if md[k] != files[k]]
    assert not drift, (
        f"KPI_Catalog.md drifted from kpis/*.yaml: {drift[:5]} — "
        "regenerate with: python tooling/codegen/kpi_catalog_files.py render"
    )


def test_index_covers_all_files_exactly():
    order = yaml.safe_load((KPIS / "_index.yaml").read_text(encoding="utf-8"))["order"]
    on_disk = {p.stem for p in KPIS.glob("*.yaml") if p.name != "_index.yaml"}
    assert set(order) == on_disk, f"index/_files mismatch: {set(order) ^ on_disk}"
    assert len(order) == len(set(order)), "duplicate kpi_id in _index.yaml"


def test_all_kpi_files_schema_valid():
    pytest.importorskip("jsonschema")
    from jsonschema import Draft202012Validator

    validator = Draft202012Validator(json.loads(SCHEMA.read_text(encoding="utf-8")))
    bad = {}
    for kid, entry in _file_entries().items():
        errs = list(validator.iter_errors(entry))
        if errs:
            bad[kid] = errs[0].message
    assert not bad, f"schema-invalid KPI files: {bad}"
