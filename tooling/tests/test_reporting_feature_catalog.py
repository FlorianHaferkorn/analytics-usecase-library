"""Reporting Feature Catalog (A-31 R7): what users expect from reporting, BI and decision
intelligence, each feature traced to the research corpus, placed in a module, and — once built —
measured by a test. The fields carry the claims; these tests check them without reading prose."""
from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
CATALOG = REPO / "core" / "reporting_features" / "catalog.yaml"
SCHEMA = REPO / "tooling" / "generator" / "schemas" / "reporting_feature_catalog.schema.json"
CORPUS = REPO / "docs" / "architecture" / "research" / "2026-09-30_visual-stack-r1"
FREELANCING = REPO.parent / "Freelancing"


@pytest.fixture(scope="module")
def catalog() -> dict:
    return yaml.safe_load(CATALOG.read_text(encoding="utf-8"))


def _corpus_ids() -> set[str]:
    ids: set[str] = set()
    for f in CORPUS.glob("*.yaml"):
        data = yaml.safe_load(f.read_text(encoding="utf-8"))
        rows = data if isinstance(data, list) else (data or {}).get("rules") or (data or {}).get("entries") or []
        ids |= {str(r.get("id") or r.get("rule_id")) for r in rows if isinstance(r, dict)}
    return ids


def test_catalog_matches_its_schema(catalog):
    jsonschema.validate(catalog, json.loads(SCHEMA.read_text(encoding="utf-8")))


def test_ids_are_unique(catalog):
    ids = [f["id"] for f in catalog["features"]]
    assert len(ids) == len(set(ids))


def test_every_source_exists_in_the_research_corpus(catalog):
    known = _corpus_ids()
    missing = sorted({s for f in catalog["features"] for s in f["sources"]} - known)
    assert not missing, f"sources not in the corpus: {missing}"


def test_built_features_name_tests_that_exist(catalog):
    for f in catalog["features"]:
        for path in f.get("tests") or []:
            if path.startswith("freelancing:"):
                if FREELANCING.is_dir():
                    assert (FREELANCING / path.split(":", 1)[1]).is_file(), f"{f['id']}: {path}"
            else:
                assert (REPO / path).is_file(), f"{f['id']}: {path}"


def test_must_haves_without_a_module_state_why(catalog):
    for f in catalog["features"]:
        if f["must_have"] and f["meridian_module"] is None:
            assert f.get("gap_reason"), f"{f['id']}: must-have without module and without gap_reason"
