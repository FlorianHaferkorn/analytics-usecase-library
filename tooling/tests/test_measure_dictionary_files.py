"""Guards for the machine-readable measure-dictionary SSOT (Phase A, slice 2).

The source of truth for measures is one file per measure under
``core/semantic_models/domains/<Domain>/measures/<measure_id>.yaml``. Each
``Measure_Dictionary_<Domain>.md`` is a *generated view*. These tests ensure the
two never silently diverge and that every per-measure file validates against the
measure-dictionary entry schema.

Comparison is element-wise/ordered (not keyed) because measure names are not
unique within a domain — duplicate-name entries are preserved faithfully.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
DOMAINS = REPO / "core/semantic_models/domains"
SCHEMA = REPO / "tooling/generator/schemas/measure_dictionary_entry.schema.json"


def _dict_paths() -> list[Path]:
    return sorted(DOMAINS.glob("*/Measure_Dictionary_*.md"))


def _block(md: Path) -> list:
    body = md.read_text(encoding="utf-8").split("```yaml", 1)[1].rsplit("```", 1)[0]
    return yaml.safe_load(body)


def _files(md: Path) -> list:
    # Resolve $ref shared-measure references the same way render/check/the
    # generator do, so the view-match and schema checks see real measures.
    from codegen.measure_dictionary_files import load_resolved_measures

    return load_resolved_measures(md)


def _raw_files(md: Path) -> list:
    mdir = md.parent / "measures"
    order = yaml.safe_load((mdir / "_index.yaml").read_text(encoding="utf-8"))["order"]
    return [yaml.safe_load((mdir / f"{s}.yaml").read_text(encoding="utf-8")) for s in order]


def test_dictionaries_discovered():
    assert len(_dict_paths()) == 15, "expected 15 domain measure dictionaries"


def test_view_matches_per_measure_files():
    for md in _dict_paths():
        block, files = _block(md), _files(md)
        assert len(block) == len(files), f"{md.parent.name}: count drift"
        drift = [i for i, (a, b) in enumerate(zip(block, files)) if a != b]
        assert not drift, (
            f"{md.parent.name}: entry #{drift[0]} drifted — regenerate with "
            "python tooling/codegen/measure_dictionary_files.py render"
        )


def test_index_covers_all_files_exactly():
    for md in _dict_paths():
        mdir = md.parent / "measures"
        order = yaml.safe_load((mdir / "_index.yaml").read_text(encoding="utf-8"))["order"]
        on_disk = {p.stem for p in mdir.glob("*.yaml") if p.name != "_index.yaml"}
        assert set(order) == on_disk, f"{md.parent.name}: {set(order) ^ on_disk}"
        assert len(order) == len(set(order)), f"{md.parent.name}: duplicate id in _index"


def test_shared_refs_resolve():
    """Every ``$ref`` per-measure file points at an existing shared definition,
    and only the expected per-domain leaves are overridden."""
    shared_dir = REPO / "core/semantic_models/shared/measures"
    allowed_overrides = {"$ref", "semantic_model", "documentation", "governance"}
    dangling = {}
    for md in _dict_paths():
        for raw in _raw_files(md):
            if "$ref" not in raw:
                continue
            if not (shared_dir / f"{raw['$ref']}.yaml").is_file():
                dangling[f"{md.parent.name}/{raw['$ref']}"] = "shared file missing"
            extra = set(raw) - allowed_overrides
            if extra:
                dangling[f"{md.parent.name}/{raw['$ref']}"] = f"unexpected override keys: {extra}"
    assert not dangling, dangling


def test_all_measure_files_schema_valid():
    pytest.importorskip("jsonschema")
    from jsonschema import Draft202012Validator

    validator = Draft202012Validator(json.loads(SCHEMA.read_text(encoding="utf-8")))
    bad = {}
    for md in _dict_paths():
        for entry in _files(md):
            errs = list(validator.iter_errors(entry))
            if errs:
                bad[f"{md.parent.name}/{entry.get('measure_name')}"] = errs[0].message
    assert not bad, f"schema-invalid measure files: {bad}"
