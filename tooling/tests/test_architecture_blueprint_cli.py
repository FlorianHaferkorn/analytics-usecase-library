"""
test_architecture_blueprint_cli.py — ADR-0015 follow-up (standalone workflow).

Guards the one-command orchestrator: derive → audit → ground → render, writing all
artifacts, deterministic, with a red-conformance non-zero exit.
"""
from __future__ import annotations

import json

from tooling.superversion.architecture_blueprint_cli import run, main

_INPUTS = {
    "stack": "fabric",
    "silver_contract_ref": "core/data_contracts/domains/commercial.yaml",
    "domains": [
        {
            "name": "Commercial",
            "gold_products": [{"name": "fact_sales", "kind": "fact"}],
            "sources": [{"source": "crm", "source_system": "Dynamics 365"}],
            "endorsement": "certified",
        }
    ],
}


def test_run_writes_all_artifacts(tmp_path):
    summary = run(_INPUTS, tmp_path, "fabric")
    for name in ("blueprint.json", "hitl.json", "CONFORMANCE.md",
                 "mcp_grounding.json", "retrieval_decisions.md"):
        assert (tmp_path / name).is_file()
    assert (tmp_path / "render" / "fabric" / "PROVISIONING_PLAN.md").is_file()
    assert summary["conformance_ok"] is True
    bp = json.loads((tmp_path / "blueprint.json").read_text())
    assert bp["schema_version"] == "0.1.0"


def test_main_exit_zero_on_clean(tmp_path):
    inp = tmp_path / "inputs.json"
    inp.write_text(json.dumps(_INPUTS), encoding="utf-8")
    rc = main(["--inputs", str(inp), "--dest", str(tmp_path / "out"), "--stack", "fabric"])
    assert rc == 0


def test_main_exit_nonzero_on_red(tmp_path):
    # a domain with a copy source lacking rationale → P1 red → exit 2
    bad = {
        "stack": "fabric", "silver_contract_ref": "x.yaml",
        "domains": [{"name": "D", "gold_products": [{"name": "fact_y", "kind": "fact"}],
                     "sources": [{"source": "s", "source_system": "db", "access_mode": "copy"}]}],
    }
    inp = tmp_path / "bad.json"
    inp.write_text(json.dumps(bad), encoding="utf-8")
    rc = main(["--inputs", str(inp), "--dest", str(tmp_path / "out"), "--stack", "fabric"])
    assert rc == 2


def test_run_is_deterministic(tmp_path):
    a = run(_INPUTS, tmp_path / "a", "fabric")
    b = run(_INPUTS, tmp_path / "b", "fabric")
    assert a["conformance"] == b["conformance"]
    assert (tmp_path / "a" / "blueprint.json").read_text() == (tmp_path / "b" / "blueprint.json").read_text()


# -- feeding answered source introspections back in ---------------------------------


_ROWS = ("TABLE_SCHEMA,TABLE_NAME,COLUMN_NAME,DATA_TYPE,IS_NULLABLE\n"
         "dbo,Orders,OrderId,int,NO\n"
         "dbo,Orders,ChangedOn,datetime2,YES\n")


def test_results_directory_is_read_and_grounds_the_schema(tmp_path):
    results = tmp_path / "results"
    results.mkdir()
    (results / "crm.csv").write_text(_ROWS, encoding="utf-8")

    summary = run(_INPUTS, tmp_path / "out", "fabric", results)
    assert summary["source_schemas_answered"] == ["crm"]
    schema = json.loads((tmp_path / "out" / "render" / "fabric" / "source_schema"
                         / "schemas" / "crm.json").read_text(encoding="utf-8"))
    assert schema["source"] == "crm"


def test_without_results_the_question_is_still_emitted(tmp_path):
    summary = run(_INPUTS, tmp_path / "out", "fabric")
    assert summary["source_schemas_answered"] == []
    assert (tmp_path / "out" / "render" / "fabric" / "source_schema"
            / "queries" / "crm.sql").is_file()


def test_non_result_files_are_ignored(tmp_path):
    """The emitted questions (.sql/.md) live next to the answers in a real workflow;
    feeding a query back in as if it were a result would produce a bogus schema."""
    from tooling.superversion.architecture_blueprint_cli import read_source_schema_results

    results = tmp_path / "r"
    results.mkdir()
    (results / "crm.csv").write_text(_ROWS, encoding="utf-8")
    (results / "crm.sql").write_text("SELECT 1", encoding="utf-8")
    (results / "_SOURCE_SCHEMA.md").write_text("# readme", encoding="utf-8")
    assert set(read_source_schema_results(results)) == {"crm"}


def test_missing_results_directory_is_an_error_not_a_silent_skip(tmp_path):
    """A typo'd path must not look like "no sources answered yet"."""
    import pytest

    from tooling.superversion.architecture_blueprint_cli import read_source_schema_results

    with pytest.raises(FileNotFoundError, match="source-schema-results"):
        read_source_schema_results(tmp_path / "nope")


def test_main_accepts_the_flag(tmp_path):
    results = tmp_path / "results"
    results.mkdir()
    (results / "crm.csv").write_text(_ROWS, encoding="utf-8")
    inp = tmp_path / "inputs.json"
    inp.write_text(json.dumps(_INPUTS), encoding="utf-8")
    rc = main(["--inputs", str(inp), "--dest", str(tmp_path / "out"),
               "--source-schema-results", str(results)])
    assert rc == 0
