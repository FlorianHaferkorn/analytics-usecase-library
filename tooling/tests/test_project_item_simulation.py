"""Deterministic, tenant-free adapter seam and fail-closed binding rehearsals."""
import ast
import base64
import copy
import inspect
import json

import pytest

from tooling.superversion.project_package import item_simulation
from tooling.superversion.project_package.item_simulation import simulate_item_contract
from tooling.tests.test_project_item_compile import data, native_item, part


def fixture():
    compiler = data()
    pipeline = compiler["modules"]["architecture_input"]["physical_items"][0]
    pipeline["definition"]["parts"] = [part("pipeline-content.json", {"properties": {
        "activities": [{"notebookId": "LOCAL_NOTEBOOK_BINDING"}],
        "workspaceId": "LOCAL_WORKSPACE_BINDING", "unrelated": "LOCAL_NOTEBOOK_BINDING",
        "parameters": {"environment": {"type": "String", "defaultValue": "dev"}},
    }})]
    pipeline["environment_bindings"] = [{"part_path": "pipeline-content.json", "json_pointer": "/properties/parameters/environment/defaultValue", "expected_value": "dev", "authority_ref": "fixture:environment"}]
    mapping = [{"workspace_ref": "workspace_gold_dev", "environment": "dev", "physical_id": "sim_workspace_dev"}]
    bindings = [{"item_ref": "pipeline_prepare", "part_path": "pipeline-content.json", "json_pointer": "/properties/activities/0/notebookId", "expected_value": "LOCAL_NOTEBOOK_BINDING", "target_kind": "item", "target_ref": "notebook_prepare"},
                {"item_ref": "pipeline_prepare", "part_path": "pipeline-content.json", "json_pointer": "/properties/workspaceId", "expected_value": "LOCAL_WORKSPACE_BINDING", "target_kind": "workspace", "target_ref": "workspace_gold_dev"}]
    return compiler, mapping, bindings


def test_create_bind_repeat_and_no_input_mutations():
    compiler, mapping, bindings = fixture()
    before = copy.deepcopy((compiler, mapping, bindings))
    first = simulate_item_contract(compiler, mapping, bindings)
    assert first["status"] == "simulated"
    assert [op["status"] for op in first["operations"]] == ["created", "created"]
    assert all(op["physical_id"].startswith("sim_item_") for op in first["operations"])
    assert first["resolved_bindings"][0]["resolved_value"] == first["operations"][0]["physical_id"]
    assert first["resolved_bindings"][1]["resolved_value"] == "sim_workspace_dev"
    old_state = copy.deepcopy(first["state"])
    repeat = simulate_item_contract(compiler, mapping, bindings, first["state"])
    assert repeat["status"] == "simulated"
    assert all(op["status"] == "noop" and not op["attempted"] for op in repeat["operations"])
    assert repeat["state"] == old_state == first["state"]
    assert (compiler, mapping, bindings) == before
    assert first == simulate_item_contract(compiler, mapping, bindings)


@pytest.mark.parametrize("kind", ["Notebook", "DataPipeline", "SemanticModel", "Report"])
def test_supported_transport_never_claims_native_runtime_validation(kind):
    compiler, mapping, _ = fixture()
    compiler["modules"]["architecture_input"]["physical_items"] = [native_item(kind)]
    result = simulate_item_contract(compiler, mapping, [])
    assert result["status"] == "simulated"
    assert result["evidence_kind"] == "simulation"
    assert not result["tenant_actions_performed"]
    assert not result["live_apply_allowed"]
    assert not result["accepted_by_fabric"]
    assert any("semantics" in limitation for limitation in result["limitations"])


def test_changed_definition_conflict_is_preflight_without_new_attempts():
    compiler, mapping, bindings = fixture()
    first = simulate_item_contract(compiler, mapping, bindings)
    compiler["modules"]["architecture_input"]["physical_items"][1]["description"] = "Changed supplied definition"
    result = simulate_item_contract(compiler, mapping, bindings, first["state"])
    assert result["status"] == "blocked"
    assert "conflicts" in result["reason"]
    assert not result["operations"]
    assert result["state"] == first["state"]


def test_uncertain_attempt_stops_dependents_and_can_never_auto_retry():
    compiler, mapping, bindings = fixture()
    first = simulate_item_contract(compiler, mapping, bindings, uncertain_item_id="notebook_prepare")
    assert first["status"] == "reconciliation_required"
    assert len(first["operations"]) == 1
    assert first["operations"][0]["status"] == "uncertain"
    assert first["operations"][0]["attempted"]
    repeat = simulate_item_contract(compiler, mapping, bindings, first["state"])
    assert repeat["status"] == "reconciliation_required"
    assert len(repeat["operations"]) == 1
    assert not repeat["operations"][0]["attempted"]
    assert repeat["state"] == first["state"]


def test_uncertain_second_item_preserves_created_predecessor():
    compiler, mapping, bindings = fixture()
    first = simulate_item_contract(compiler, mapping, bindings, uncertain_item_id="pipeline_prepare")
    repeat = simulate_item_contract(compiler, mapping, bindings, first["state"])
    assert [op["status"] for op in repeat["operations"]] == ["reconciliation_required"]
    assert repeat["state"]["records"]["notebook_prepare"]["status"] == "created"
    assert not any(op["attempted"] for op in repeat["operations"])


def test_uncertain_batch_blocks_new_unrelated_items_until_reconciliation():
    compiler, mapping, bindings = fixture()
    first = simulate_item_contract(compiler, mapping, bindings, uncertain_item_id="pipeline_prepare")
    compiler["modules"]["architecture_input"]["physical_items"].append(native_item(id="aaa_new_item"))
    repeated = simulate_item_contract(compiler, mapping, bindings, first["state"])
    assert repeated["status"] == "reconciliation_required"
    assert not any(operation["attempted"] for operation in repeated["operations"])
    assert "aaa_new_item" not in repeated["state"]["records"]


@pytest.mark.parametrize("mutation", ["real_id", "missing_mapping", "wrong_env", "unknown_workspace", "duplicate_mapping", "duplicate_physical", "extra_mapping_field", "cycle", "unresolved_dependency", "cross_env", "unsupported_kind", "invalid_base64", "bad_environment_assertion"])
def test_invalid_transport_and_workspace_scope_fail_closed(mutation):
    compiler, mapping, bindings = fixture()
    items = compiler["modules"]["architecture_input"]["physical_items"]
    if mutation == "real_id": mapping[0]["physical_id"] = "11111111-1111-4111-8111-111111111111"
    if mutation == "missing_mapping": mapping.clear()
    if mutation == "wrong_env": mapping[0]["environment"] = "prod"
    if mutation == "unknown_workspace": mapping[0]["workspace_ref"] = "unknown"
    if mutation == "duplicate_mapping": mapping.append(copy.deepcopy(mapping[0]))
    if mutation == "duplicate_physical":
        ws = copy.deepcopy(compiler["modules"]["architecture_input"]["physical_workspaces"][0])
        ws["id"] = "second_workspace"
        ws["name"] = "second_workspace"
        compiler["modules"]["architecture_input"]["physical_workspaces"].append(ws)
        mapping.append({**mapping[0], "workspace_ref": "second_workspace", "environment": ws["environment"]})
    if mutation == "extra_mapping_field": mapping[0]["token"] = "not_allowed"
    if mutation == "cycle": items[1]["depends_on"] = [items[0]["id"]]
    if mutation == "unresolved_dependency": items[0]["depends_on"] = ["missing"]
    if mutation == "cross_env": items[1]["environment"] = "prod"
    if mutation == "unsupported_kind": items[1]["type"] = "Lakehouse"
    if mutation == "invalid_base64": items[1]["definition"]["parts"][0]["payload"] = "notbase64!"
    if mutation == "bad_environment_assertion": items[0]["environment_bindings"][0]["expected_value"] = "prod"
    result = simulate_item_contract(compiler, mapping, bindings)
    assert result["status"] == "blocked"
    assert not result["operations"]
    assert not result["tenant_actions_performed"]


@pytest.mark.parametrize("mutation", ["wrong_pointer", "mismatch", "numeric_expected", "root", "bad_escape", "leading_zero_index", "out_of_range", "missing_part", "unknown_source", "unknown_target", "unsupported_target", "wrong_workspace", "not_dependency", "extra_field", "duplicate", "source_code", "tmdl"])
def test_binding_is_exact_closed_and_json_only(mutation):
    compiler, mapping, bindings = fixture()
    binding = bindings[0]
    if mutation == "wrong_pointer": binding["json_pointer"] = "/properties/missing"
    if mutation == "mismatch": binding["expected_value"] = "different"
    if mutation == "numeric_expected": binding["expected_value"] = 1
    if mutation == "root": binding["json_pointer"] = ""
    if mutation == "bad_escape": binding["json_pointer"] = "/properties/~3"
    if mutation == "leading_zero_index": binding["json_pointer"] = "/properties/activities/00/notebookId"
    if mutation == "out_of_range": binding["json_pointer"] = "/properties/activities/9/notebookId"
    if mutation == "missing_part": binding["part_path"] = "missing.json"
    if mutation == "unknown_source": binding["item_ref"] = "missing"
    if mutation == "unknown_target": binding["target_ref"] = "missing"
    if mutation == "unsupported_target": binding["target_kind"] = "connection"
    if mutation == "wrong_workspace": bindings[1]["target_ref"] = "other_workspace"
    if mutation == "not_dependency": compiler["modules"]["architecture_input"]["physical_items"][0]["depends_on"] = []
    if mutation == "extra_field": binding["command"] = "never execute"
    if mutation == "duplicate": bindings.append(copy.deepcopy(binding))
    if mutation == "source_code": binding["part_path"] = "notebook-content.py"
    if mutation == "tmdl": binding["part_path"] = "definition/model.tmdl"
    result = simulate_item_contract(compiler, mapping, bindings)
    assert result["status"] == "blocked"
    assert not result["operations"]


@pytest.mark.parametrize("mutation", ["project", "workspace", "state_scope", "state_extra", "record_id", "record_status"])
def test_prior_state_cannot_cross_scope(mutation):
    compiler, mapping, bindings = fixture()
    first = simulate_item_contract(compiler, mapping, bindings)
    state = copy.deepcopy(first["state"])
    if mutation == "project": compiler["package"]["project_ref"] = "another_project"
    if mutation == "workspace": mapping[0]["physical_id"] = "sim_workspace_different"
    if mutation == "state_scope": state["scope_sha256"] = "0" * 64
    if mutation == "state_extra": state["trusted"] = True
    if mutation == "record_id": state["records"]["notebook_prepare"]["physical_id"] = "sim_item_other"
    if mutation == "record_status": state["records"]["notebook_prepare"]["status"] = "tenant_verified"
    result = simulate_item_contract(compiler, mapping, bindings, state)
    assert result["status"] == "blocked"
    assert not result["operations"]
    assert result["state"] == state


def test_json_escape_pointer_is_supported_without_global_replacement():
    compiler, mapping, bindings = fixture()
    pipeline = compiler["modules"]["architecture_input"]["physical_items"][0]
    document = json.loads(base64.b64decode(pipeline["definition"]["parts"][0]["payload"]))
    document["properties"]["a/b~c"] = "LOCAL_NOTEBOOK_BINDING"
    pipeline["definition"]["parts"] = [part("pipeline-content.json", document)]
    bindings[0]["json_pointer"] = "/properties/a~1b~0c"
    result = simulate_item_contract(compiler, mapping, bindings)
    assert result["status"] == "simulated"
    assert len(result["resolved_bindings"]) == 2
    assert result["resolved_bindings"][0]["json_pointer"] == "/properties/a~1b~0c"


def test_same_environment_is_not_enough_for_cross_workspace_item_binding():
    compiler, mapping, bindings = fixture()
    architecture = compiler["modules"]["architecture_input"]
    workspace = copy.deepcopy(next(ws for ws in architecture["physical_workspaces"] if ws["id"] == "workspace_gold_dev"))
    workspace["id"] = "workspace_other_dev"
    workspace["name"] = "workspace_other_dev"
    architecture["physical_workspaces"].append(workspace)
    architecture["physical_items"][1]["workspace_ref"] = workspace["id"]
    mapping.append({"workspace_ref": workspace["id"], "environment": "dev", "physical_id": "sim_workspace_other_dev"})
    result = simulate_item_contract(compiler, mapping, bindings)
    assert result["status"] == "blocked"
    assert "Cross-workspace" in result["reason"]
    assert not result["operations"]


def test_replacement_changes_only_the_asserted_fields(monkeypatch):
    compiler, mapping, bindings = fixture()
    observed = []
    original_hash = item_simulation.canonical_sha256

    def capture_hash(value):
        if isinstance(value, dict) and value.get("item", {}).get("id") == "pipeline_prepare":
            observed.append(copy.deepcopy(value["item"]))
        return original_hash(value)

    monkeypatch.setattr(item_simulation, "canonical_sha256", capture_hash)
    result = simulate_item_contract(compiler, mapping, bindings)
    assert result["status"] == "simulated"
    document = json.loads(base64.b64decode(observed[0]["definition"]["parts"][0]["payload"]))
    assert document["properties"]["unrelated"] == "LOCAL_NOTEBOOK_BINDING"
    assert document["properties"]["activities"][0]["notebookId"].startswith("sim_item_")
    assert document["properties"]["parameters"]["environment"]["defaultValue"] == "dev"


def test_module_has_no_execution_or_network_imports():
    source = inspect.getsource(item_simulation)
    tree = ast.parse(source)
    imports = [node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
    imports += [alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names]
    assert not {"subprocess", "requests", "urllib", "http", "socket", "os", "fabric_client", "deployment"}.intersection(imports)
    assert "FabWorkspaceClient" not in source
