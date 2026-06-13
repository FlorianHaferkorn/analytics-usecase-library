"""Guards for Domain Evidence Packs (core/usecases/core/<UC>/Domain_Evidence_Pack.yaml).

Evidence packs are an SSOT for the domain grounding behind each use case, but
until now nothing validated them — which let portfolio scores, source-category
coverage, and gap-status vocabulary drift. These tests pin:

  * structural validity against domain_evidence_pack.schema.json, and
  * the arithmetic invariants JSON Schema cannot express:
      - each source's total_score == sum of its five 1-3 sub-scores
      - summary.portfolio_score == round(mean(total_score), 1)
      - summary.total_sources == len(sources)
      - summary.categories_covered == the set of categories actually present
      - every SRC-xxx referenced (benchmark_source_id / source_id) exists
      - source ids are unique
"""
from __future__ import annotations

import json
import re
import statistics
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
PACKS = sorted((REPO / "core/usecases/core").glob("*/Domain_Evidence_Pack.yaml"))
SCHEMA = REPO / "tooling/generator/schemas/domain_evidence_pack.schema.json"

_REF_RE = re.compile(r"(?:benchmark_source_id|source_id):\s*(SRC-\d+)")


def _load(p: Path) -> dict:
    return yaml.safe_load(p.read_text(encoding="utf-8"))


def test_packs_present():
    assert PACKS, "no Domain_Evidence_Pack.yaml files found under core/usecases/core"


@pytest.mark.parametrize("path", PACKS, ids=lambda p: p.parent.name)
def test_evidence_pack_schema_valid(path: Path):
    pytest.importorskip("jsonschema")
    from jsonschema import Draft202012Validator

    validator = Draft202012Validator(json.loads(SCHEMA.read_text(encoding="utf-8")))
    errs = sorted(validator.iter_errors(_load(path)), key=lambda e: e.path)
    assert not errs, f"{path.parent.name}: " + "; ".join(
        f"{list(e.path)} {e.message}" for e in errs[:5]
    )


@pytest.mark.parametrize("path", PACKS, ids=lambda p: p.parent.name)
def test_evidence_pack_invariants(path: Path):
    d = _load(path)
    inv = d["source_inventory"]
    sources = inv["sources"]
    summary = inv["summary"]
    uc = path.parent.name

    # 1. total_score == sum of the five sub-scores
    bad = [s["id"] for s in sources if sum(s["scores"].values()) != s["total_score"]]
    assert not bad, f"{uc}: total_score != sum(scores) for {bad}"

    # 2. unique source ids
    ids = [s["id"] for s in sources]
    assert len(ids) == len(set(ids)), f"{uc}: duplicate source ids"

    # 3. total_sources matches
    assert summary["total_sources"] == len(sources), (
        f"{uc}: total_sources {summary['total_sources']} != {len(sources)}"
    )

    # 4. portfolio_score == round(mean(total_score), 1)
    mean = statistics.mean(s["total_score"] for s in sources)
    assert abs(summary["portfolio_score"] - mean) <= 0.05, (
        f"{uc}: portfolio_score {summary['portfolio_score']} != round(mean,1) {round(mean, 1)}"
    )

    # 5. categories_covered == categories actually present
    present = {s["category"] for s in sources}
    assert set(summary["categories_covered"]) == present, (
        f"{uc}: categories_covered {sorted(summary['categories_covered'])} != present {sorted(present)}"
    )

    # 6. no dangling source references
    refs = set(_REF_RE.findall(path.read_text(encoding="utf-8")))
    assert refs <= set(ids), f"{uc}: dangling source refs {sorted(refs - set(ids))}"
