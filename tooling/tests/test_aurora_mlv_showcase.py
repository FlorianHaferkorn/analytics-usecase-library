"""
test_aurora_mlv_showcase.py — ADR-0024: the Aurora showcase with gold as MLV in one domain.

One run of the standalone workflow over the committed Aurora inputs
(`showcases/aurora_group/architecture/aurora_architecture_inputs.json`: Commercial → `mlv`,
Finance → default) and the governed catalog exported from the data contracts. The emitted
MLV DDL is checked against the expectations of Meridian D-621/D-622 and MS Learn as quoted
in the mirrored emitter:

* `REFRESH_HINT` as its **own** parenthesised block after the constraints;
* `PARTITIONED BY` only on a declared low-cardinality period column, never a day-level date;
* Change Data Feed in the TBLPROPERTIES of every view;
* `mlv/_MLV.md` present; every hinted view has its uniqueness test in `dq/`.

No golden file: the assertions are the expectation, so a changed mirror shows up as a
named failure instead of a regenerated snapshot.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
import yaml

from tooling.generator.export_governed_catalog import build_governed_catalog
from tooling.superversion._dataarch_vendor import available
from tooling.superversion.architecture_blueprint_cli import run

REPO = Path(__file__).resolve().parents[2]
INPUTS = REPO / "showcases" / "aurora_group" / "architecture" / "aurora_architecture_inputs.json"

pytestmark = pytest.mark.skipif(not available(), reason="mirrored Meridian emitters unavailable")

# the period names the mirrored rule accepts (provision_transforms._MLV_PERIODEN_NAMEN/-ENDUNGEN)
_PERIOD = re.compile(r"^(year|month|period|fiscal_year|fiscal_period|gjahr|monat|poper)$"
                     r"|_(year|month|period)$")


@pytest.fixture(scope="module")
def showcase(tmp_path_factory):
    dest = tmp_path_factory.mktemp("aurora_mlv")
    catalog = dest / "governed_catalog.json"
    catalog.write_text(json.dumps(build_governed_catalog(REPO)), encoding="utf-8")
    inputs = json.loads(INPUTS.read_text(encoding="utf-8"))
    summary = run(inputs, dest / "out", "fabric", governed_catalog=catalog,
                  mlv_refresh_hints=True, mlv_zeitplan="graph")
    return summary, dest / "out" / "render" / "fabric"


def _views(root: Path) -> dict[str, str]:
    return {p.stem.removesuffix(".mlv"): p.read_text(encoding="utf-8")
            for p in sorted((root / "mlv").rglob("*.mlv.sql"))}


def test_only_the_mlv_domain_gets_views(showcase):
    summary, root = showcase
    assert summary["gold_targets"] == {"Commercial": "mlv"}
    assert summary["conformance_ok"] is True
    assert set(_views(root)) == {"dim_customer", "dim_date", "dim_product", "fact_experience",
                                 "fact_sales"}
    assert not (root / "mlv" / "finance").exists()
    # Finance keeps its gold path; Commercial's gold is not built twice
    assert (root / "transforms" / "finance" / "silver_to_gold__fact_finance.sql").is_file()
    assert not (root / "transforms" / "commercial").exists()


def test_refresh_hint_is_its_own_block(showcase):
    _, root = showcase
    views = _views(root)
    hinted = {n for n, sql in views.items() if "REFRESH_HINT" in sql}
    # dimensions with a declared key + the fact whose contract declares its grain key
    assert hinted == {"dim_customer", "dim_date", "dim_product", "fact_experience"}
    for name in hinted:
        sql = views[name]
        # `( CONSTRAINT … )` closes, then a separate `( REFRESH_HINT … UNIQUE (…) )` opens
        assert re.search(r"ON MISMATCH \w+\n\) \(\n    REFRESH_HINT \w+ UNIQUE \([^)]+\)\n\)", sql), name
    # fact_sales declares no key in its contract: no hint, nothing guessed
    assert "REFRESH_HINT" not in views["fact_sales"]


def test_partition_only_by_a_period_column(showcase):
    _, root = showcase
    # the clause itself, not the TODO comment that states the rule where no column qualifies
    parts = {n: re.findall(r"^PARTITIONED BY \(([^)]+)\)$", sql, flags=re.M)
             for n, sql in _views(root).items()}
    assert parts["dim_date"] == ["`Fiscal Period`"]
    for name, cols in parts.items():
        for col in cols:
            norm = re.sub(r"[^0-9a-z]+", "_", col.strip("`").lower()).strip("_")
            assert _PERIOD.search(norm), (name, col)
    assert not any(parts[n] for n in parts if n != "dim_date")


def test_every_view_carries_change_data_feed(showcase):
    _, root = showcase
    for name, sql in _views(root).items():
        assert "'delta.enableChangeDataFeed' = 'true'" in sql, name
        assert sql.count("CREATE OR REPLACE MATERIALIZED LAKE VIEW gold.") == 1, name


def test_mlv_doc_schedule_and_execution_definition(showcase):
    _, root = showcase
    assert (root / "mlv" / "_MLV.md").is_file()
    schedule = json.loads((root / "mlv" / "refresh_schedule.json").read_text(encoding="utf-8"))
    assert "mlvExecutionDefinitionId" in schedule["executionData"]
    assert (root / "mlv" / "execution_definition.json").is_file()


def test_every_hint_has_its_uniqueness_test(showcase):
    _, root = showcase
    models = {m["name"]: m for m in
              yaml.safe_load((root / "dq" / "commercial" / "schema.yml").read_text(encoding="utf-8"))["models"]}
    for name, key in (("dim_customer", "CustomerKey"), ("dim_date", "DateKey"),
                      ("dim_product", "ProductKey"), ("fact_experience", "Complaint ID")):
        model = models[f"gold_{name}"]
        tests = [t for c in model.get("columns", []) if c["name"] == key for t in c.get("tests", [])]
        assert "unique" in tests, (name, key, model.get("columns"))
