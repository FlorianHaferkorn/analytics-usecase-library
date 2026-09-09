"""Real deterministic row processing, fail-closed state, no platform simulation."""
import copy
import inspect
import json
import hashlib
import subprocess
import sys

import pytest
from jsonschema import Draft202012Validator

from tooling.superversion.project_package import batch_ingestion as core
from tooling.superversion.project_package.batch_ingestion import BatchIngestionError, describe_contract, run_batch, validate_contract


def contract(mode="incremental"):
    return {"schema_version": "1.0.0", "id": "sales_batch", "domain": "sales",
            "source": {"kind": "csv_landing", "object_name": "orders", "landing_path": "Files/landing/orders.csv"},
            "target": {"schema": "source_sales", "table": "orders"}, "environments": ["dev", "test", "prod"],
            "columns": [{"name": "order_id", "type": "integer", "nullable": False}, {"name": "version", "type": "integer", "nullable": False},
                        {"name": "amount", "type": "decimal", "nullable": False}, {"name": "name", "type": "string", "nullable": True}],
            "keys": ["order_id"], "load": {"mode": mode, "watermark_column": "version" if mode == "incremental" else None,
                                          "delete_behavior": "retain", "schema_drift": "fail", "bad_rows": "fail_batch"},
            "naming": {"namespace": "demo"}}


def row(key=1, version=1, amount="10.00", name="First"):
    return {"order_id": key, "version": version, "amount": amount, "name": name}


def test_schema_and_valid_contract():
    Draft202012Validator.check_schema(json.loads(core.SCHEMA.read_text(encoding="utf-8")))
    assert validate_contract(contract()) == []


def test_two_real_batches_updates_boundary_and_retains_deletions():
    config = contract()
    first = run_batch(config, [row(1), row(2)], batch_id="batch_1")
    before = copy.deepcopy(first["state"])
    second = run_batch(config, [row(2, 2, "25"), row(3, 2, "30")], first["state"], batch_id="batch_2")
    assert first["state"] == before
    assert second["state"]["rows"] == [row(1, amount="10"), row(2, 2, "25"), row(3, 2, "30")]
    assert second["counts"] == {"received": 2, "inserted": 1, "updated": 1, "unchanged": 0, "retained": 1, "deleted": 0}
    assert second["watermark"] == 2
    boundary = run_batch(config, [row(3, 2, "30"), row(4, 2, "40")], second["state"], batch_id="batch_3")
    assert boundary["counts"]["inserted"] == boundary["counts"]["unchanged"] == 1
    assert boundary["watermark"] == 2
    assert boundary["evidence_kind"] == "local_check"
    assert boundary["tenant_actions_performed"] is False


def test_repeat_is_idempotent_and_input_order_is_irrelevant():
    config, rows = contract(), [row(1), row(2)]
    first = run_batch(config, rows, batch_id="batch_1")
    replay = run_batch(config, rows[::-1], first["state"], batch_id="batch_1")
    assert replay["replayed"] is True
    assert replay["state"] == first["state"]
    assert replay["counts"]["inserted"] == replay["counts"]["updated"] == 0
    with pytest.raises(BatchIngestionError, match="different content"):
        run_batch(config, [row(1, amount="20")], first["state"], batch_id="batch_1")


def test_old_receipt_replays_after_newer_commit():
    config = contract()
    first = run_batch(config, [row()], batch_id="one")
    second = run_batch(config, [row(version=3)], first["state"], batch_id="two")
    replay = run_batch(config, [row()], second["state"], batch_id="one")
    assert replay["state"] == second["state"]


@pytest.mark.parametrize("bad", [[row(1), row(1)], [row(amount=0.1)], [dict(row(), extra="unexpected")],
                                  [row(version=True)], [row(name=123)], [row(amount="NaN")], [row(amount="1e2")],
                                  [row(amount="01")], [row(amount="1.00000000001")], [row(key=None)], [row(version=-1)]])
def test_bad_batch_never_advances_or_mutates_state(bad):
    config = contract()
    first = run_batch(config, [row()], batch_id="one")
    before = copy.deepcopy(first["state"])
    with pytest.raises(BatchIngestionError):
        run_batch(config, bad, first["state"], batch_id="bad")
    assert first["state"] == before


@pytest.mark.parametrize("payload, message", [([row(2, 0)], "Stale"), ([row(1, 1, "20")], "Ambiguous")])
def test_stale_backfill_and_ambiguous_equal_version_rejected(payload, message):
    first = run_batch(contract(), [row()], batch_id="one")
    with pytest.raises(BatchIngestionError, match=message):
        run_batch(contract(), payload, first["state"], batch_id="two")


def test_new_version_at_global_boundary_can_update_an_older_key():
    first = run_batch(contract(), [row(1, 1), row(2, 2)], batch_id="one")
    second = run_batch(contract(), [row(1, 2, "50")], first["state"], batch_id="two")
    assert second["counts"]["updated"] == 1


def test_empty_incremental_is_a_receipt_not_a_delete():
    first = run_batch(contract(), [row()], batch_id="one")
    second = run_batch(contract(), [], first["state"], batch_id="two")
    assert second["state"]["rows"] == first["state"]["rows"]
    assert second["watermark"] == 1
    assert second["counts"]["retained"] == 1


def test_full_snapshot_replaces_only_when_nonempty_and_explicit():
    config = contract("full")
    first = run_batch(config, [row(1), row(2)], batch_id="one")
    second = run_batch(config, [row(2, amount="20")], first["state"], batch_id="two")
    assert second["state"]["rows"] == [row(2, amount="20")]
    assert second["counts"]["deleted"] == second["counts"]["updated"] == 1
    assert second["watermark"] is None
    with pytest.raises(BatchIngestionError, match="Empty full"):
        run_batch(config, [], second["state"], batch_id="empty")


def test_contract_change_cannot_reuse_state():
    first = run_batch(contract(), [row()], batch_id="one")
    changed = contract()
    changed["domain"] = "changed"
    with pytest.raises(BatchIngestionError, match="Contract changed"):
        run_batch(changed, [row()], first["state"], batch_id="two")


@pytest.mark.parametrize("change", [
    lambda c: c.update(id="Bad-Id"), lambda c: c.update(extra="untrusted"),
    lambda c: c["source"].update(landing_path="../Files/data.csv"), lambda c: c["source"].update(landing_path="Files/a/../data.csv"),
    lambda c: c["source"].update(landing_path="Files\\data.csv"), lambda c: c["source"].update(landing_path="https://host/file.csv"),
    lambda c: c["source"].update(kind="sql_server"), lambda c: c.update(environments=["prod", "dev"]),
    lambda c: c.update(keys=[]), lambda c: c.update(keys=["unknown"]), lambda c: c.update(keys=["version"]),
    lambda c: c["columns"][0].update(nullable=True), lambda c: c["columns"].append(copy.deepcopy(c["columns"][0])),
    lambda c: c["load"].update(watermark_column="name"), lambda c: c["load"].update(delete_behavior="delete"),
    lambda c: c["load"].update(mode="full"), lambda c: c["naming"].update(namespace="a"*49),
])
def test_invalid_or_unsupported_contract_blocks_all_execution(change):
    config = contract()
    change(config)
    assert validate_contract(config)
    assert describe_contract(config)["valid"] is False
    with pytest.raises(BatchIngestionError):
        run_batch(config, [row()], batch_id="one")


@pytest.mark.parametrize("kind,value,good", [
    ("boolean", True, True), ("boolean", 1, False), ("integer", False, False), ("integer", 9007199254740992, False),
    ("date", "2024-02-29", True), ("date", "2025-02-29", False), ("date", "2024-2-9", False),
    ("timestamp", "2026-09-08T12:30:00Z", True), ("timestamp", "2026-09-08T12:30:00+00:00", False),
    ("timestamp", "2026-09-08T25:30:00Z", False), ("decimal", "-0.000", True), ("decimal", float("nan"), False),
])
def test_types_are_explicit_no_coercion(kind, value, good):
    config = contract()
    config["columns"][3]["type"] = kind
    if good:
        result = run_batch(config, [row(name=value)], batch_id="one")
        assert result["state"]["rows"][0]["name"] == ("0" if kind == "decimal" else value)
    else:
        with pytest.raises(BatchIngestionError):
            run_batch(config, [row(name=value)], batch_id="one")


def test_nullability_and_exact_decimal_precision():
    result = run_batch(contract(), [row(amount="1234567890123456789012345678.1234567890", name=None)], batch_id="one")
    assert result["state"]["rows"][0]["amount"] == "1234567890123456789012345678.123456789"
    assert result["state"]["rows"][0]["name"] is None


@pytest.mark.parametrize("state", [{}, {"state_hash": "bad"}, None])
def test_state_integrity(state):
    if state is None:
        state = run_batch(contract(), [row()], batch_id="one")["state"]
        state["rows"][0]["amount"] = "999"
    with pytest.raises(BatchIngestionError):
        run_batch(contract(), [row()], state, batch_id="two")


def test_state_semantics_checked_even_when_hash_is_recomputed():
    state = run_batch(contract(), [row()], batch_id="one")["state"]
    state.pop("state_hash")
    state["watermark"] = 999
    core._seal(state)
    with pytest.raises(BatchIngestionError, match="inconsistent"):
        run_batch(contract(), [row()], state, batch_id="two")


def test_row_and_string_and_json_limits(monkeypatch):
    monkeypatch.setattr(core, "MAX_ROWS", 1)
    with pytest.raises(BatchIngestionError, match="at most"):
        run_batch(contract(), [row(1), row(2)], batch_id="one")
    with pytest.raises(BatchIngestionError):
        run_batch(contract(), [row(name="x" * 4097)], batch_id="one")
    with pytest.raises(BatchIngestionError):
        run_batch(contract(), [row(name={"not": "json scalar"})], batch_id="one")


def test_result_and_ledger_limits_preserve_old_state(monkeypatch):
    first = run_batch(contract(), [row()], batch_id="one")
    monkeypatch.setattr(core, "MAX_ROWS", 1)
    with pytest.raises(BatchIngestionError, match="Result exceeds"):
        run_batch(contract(), [row(2)], first["state"], batch_id="two")
    monkeypatch.setattr(core, "MAX_BATCHES", 1)
    with pytest.raises(BatchIngestionError, match="ledger limit"):
        run_batch(contract(), [], first["state"], batch_id="two")
    assert run_batch(contract(), [row()], first["state"], batch_id="one")["replayed"]


def test_description_reacts_to_names_mode_and_environment():
    first = describe_contract(contract())
    assert first["names"]["workspaces"]["test"] == "demo_sales_bronze_test"
    assert len(first["graph"]["nodes"]) == 9
    assert len([e for e in first["graph"]["edges"] if e["kind"] == "promotion"]) == 2
    changed = contract("full")
    changed["environments"] = ["dev", "prod"]
    changed["naming"]["namespace"] = "client"
    second = describe_contract(changed)
    assert second["contract_hash"] != first["contract_hash"]
    assert second["names"]["workspaces"]["prod"] == "client_sales_bronze_prod"
    assert len(second["graph"]["nodes"]) == 6
    assert any("replaces" in impact["detail"] for impact in second["impact"])


def test_no_tenant_or_source_execution_imports():
    source = inspect.getsource(core)
    for forbidden in ["import requests", "import subprocess", "import socket", "import azure", "import pyodbc", "exec(", "eval("]:
        assert forbidden not in source


def provenance(config):
    return {"project_ref": "neutral_batch", "revision_hash": "a" * 64, "contract_hash": core.canonical_sha256(config),
            "compiler_input_sha256": "b" * 64, "release_record_sha256": "c" * 64}


def test_exported_runtime_runs_independently_and_checks_manifest(tmp_path):
    config = contract()
    bundle = core.export_bundle(config, provenance(config))
    for path, content in bundle.items():
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8", newline="")
    manifest = json.loads(bundle["bundle-manifest.json"])
    for item in manifest["files"]:
        assert hashlib.sha256((tmp_path / item["path"]).read_bytes()).hexdigest() == item["sha256"]
    request = {"contract": config, "rows": [row(1), row(2)], "batch_id": "one"}
    first = subprocess.run([sys.executable, str(tmp_path / "run_local_batch.py")], input=json.dumps(request), text=True, capture_output=True, cwd=tmp_path, timeout=15)
    assert first.returncode == 0, first.stderr
    value = json.loads(first.stdout)["value"]
    assert value["counts"]["inserted"] == 2
    request["state"] = value["state"]
    replay = subprocess.run([sys.executable, str(tmp_path / "run_local_batch.py")], input=json.dumps(request), text=True, capture_output=True, cwd=tmp_path, timeout=15)
    assert replay.returncode == 0
    assert json.loads(replay.stdout)["value"]["state"] == value["state"]
    request["rows"] = [row(amount="99")]
    failure = subprocess.run([sys.executable, str(tmp_path / "run_local_batch.py")], input=json.dumps(request), text=True, capture_output=True, cwd=tmp_path, timeout=15)
    assert failure.returncode == 2
    assert json.loads(failure.stdout)["ok"] is False
    assert "Traceback" not in failure.stderr
    assert not list(tmp_path.glob("state*"))


@pytest.mark.parametrize("change", [lambda p: p.update(tenant_actions_performed=True), lambda p: p.update(contract_hash="d"*64),
                                   lambda p: p.update(revision_hash="unknown"), lambda p: p.update(project_ref="../customer")])
def test_export_rejects_inconsistent_or_unbounded_provenance(change):
    config = contract()
    evidence = provenance(config)
    change(evidence)
    with pytest.raises(BatchIngestionError):
        core.export_bundle(config, evidence)


@pytest.mark.parametrize("project_ref", ["550e8400-e29b-41d4-a716-446655440000", "Project-Alpha_1", "9-existing-project", "a" * 64])
def test_export_preserves_supported_package_ids_without_relaxing_names(project_ref):
    config = contract()
    evidence = {**provenance(config), "project_ref": project_ref}
    bundle = core.export_bundle(config, evidence)
    assert json.loads(bundle["provenance.json"])["project_ref"] == project_ref
    invalid_name = copy.deepcopy(config)
    invalid_name["naming"]["namespace"] = "Project-Alpha"
    assert validate_contract(invalid_name)


@pytest.mark.parametrize("project_ref", ["../customer", "/customer", "C:/customer", "C:\\customer", "customer/path", "customer\\path", ".hidden", "-leading", "", "a" * 65])
def test_export_rejects_path_or_invalid_package_ids(project_ref):
    config = contract()
    with pytest.raises(BatchIngestionError, match="exact approved project"):
        core.export_bundle(config, {**provenance(config), "project_ref": project_ref})
