"""Native transport validation, exact binding declarations and released outputs."""
import base64
import copy
import json

import pytest
import yaml
from jsonschema import Draft202012Validator, FormatChecker

from tooling.superversion.project_package.automation import read_automation, run_automation
from tooling.superversion.project_package.item_compile import build_item_output, compile_item_plan, item_target
from tooling.superversion.project_package.hashes import canonical_sha256
from tooling.superversion.project_package.migrations import migrate_project_package
from tooling.superversion.project_package.repository import ProjectPackageRevisionRepository
from tooling.superversion.project_package.release import release_input
from tooling.superversion.project_package.adapters.decision_proposals import adapt_decision_proposals
from tooling.tests.test_project_architecture_compile import compiler, compile_architecture, ROOT, SCHEMAS
from tooling.tests.test_project_package import _proposal


def part(path, content):
    text = content if isinstance(content, str) else json.dumps(content)
    return {"path": path, "payload": base64.b64encode(text.encode()).decode(), "payloadType": "InlineBase64"}


def native_item(kind="Notebook", id="notebook_prepare", depends=None):
    definitions = {
        "Notebook": {"format": "FabricGitSource", "parts": [part("notebook-content.py", "# Fabric notebook source\nprint('Supplied definition')\n")]},
        "DataPipeline": {"parts": [part("pipeline-content.json", {"properties": {"activities": [], "parameters": {"environment": {"type": "String", "defaultValue": "dev"}}}})]},
        "SemanticModel": {"format": "TMSL", "parts": [part("definition.pbism", {"version": "1.0"}), part("model.bim", {"compatibilityLevel": 1600, "model": {}})]},
        "Report": {"format": "PBIR", "parts": [part("definition.pbir", {"version": "4.0", "datasetReference": {"byConnection": {"connectionString": "supplied fixture connection"}}}), part("definition/report.json", {"themeCollection": {}}), part("definition/version.json", {"version": "2.0.0"})]},
    }
    return {"id": id, "name": id, "type": kind, "workspace_ref": "workspace_gold_dev", "environment": "dev",
            "decision_refs": ["decision_environment_model"], "depends_on": depends or [], "environment_bindings": [], "definition": definitions[kind]}


def data():
    value = compiler()
    value["modules"]["architecture_input"]["physical_items"] = [native_item("DataPipeline", "pipeline_prepare", ["notebook_prepare"]), native_item()]
    return value


@pytest.mark.parametrize("kind", ["Notebook", "DataPipeline", "SemanticModel", "Report"])
def test_supplied_native_types_have_explicit_transport_not_semantic_claim(kind):
    value = data()
    value["modules"]["architecture_input"]["physical_items"] = [native_item(kind)]
    before = copy.deepcopy(value)
    plan = compile_item_plan(value)
    assert value == before
    assert plan["validation_scope"] == "native_definition_transport_and_declared_dependencies"
    assert not plan["apply_ready"]
    assert not plan["ordered_items"][0]["tenant_bindings_verified"]
    assert item_target(value)["status"] == "ready"


def legacy_report(format="PBIR-Legacy"):
    item = native_item("Report")
    pbir = item["definition"]["parts"][0]
    item["definition"] = {"parts": [pbir, part("report.json", {"sections": []})]}
    if format is not None:
        item["definition"]["format"] = format
    return item


@pytest.mark.parametrize("format", ["PBIR-Legacy", None, "PBIR"])
def test_pbir_legacy_report_is_rejected_with_save_as_pbir_hint(format):
    """PBIR only: a declared PBIR-Legacy format or a root report.json fails closed."""
    value = data()
    value["modules"]["architecture_input"]["physical_items"] = [legacy_report(format)]
    with pytest.raises(ValueError, match="PBIR-Legacy wird nicht mehr akzeptiert.*als PBIR speichern"):
        compile_item_plan(value)
    assert item_target(value)["status"] == "blocked"


def test_report_without_pbir_definition_folder_is_rejected():
    value = data()
    report = native_item("Report")
    report["definition"]["parts"] = report["definition"]["parts"][:1]
    value["modules"]["architecture_input"]["physical_items"] = [report]
    with pytest.raises(ValueError, match="PBIR definition/ folder"):
        compile_item_plan(value)


def test_dependency_order_is_deterministic():
    value = data()
    assert [item["id"] for item in compile_item_plan(value)["ordered_items"]] == ["notebook_prepare", "pipeline_prepare"]
    value["modules"]["architecture_input"]["physical_items"].reverse()
    assert [item["id"] for item in compile_item_plan(value)["ordered_items"]] == ["notebook_prepare", "pipeline_prepare"]


def test_architecture_graph_projects_exact_ownership_and_dependencies_without_payload():
    value = data()
    graph = compile_architecture(value, "a" * 64)["graph"]
    notebook = next(node for node in graph["nodes"] if node["id"] == "item:notebook_prepare")
    assert notebook["kind"] == "native_item"
    assert "definition" not in notebook["details"]
    assert notebook["details"]["definition_parts"] == ["notebook-content.py"]
    assert all("payload" not in json.dumps(node["details"]) for node in graph["nodes"])
    assert any(edge["source"] == "workspace:workspace_gold_dev" and edge["target"] == "item:notebook_prepare" and edge["kind"] == "ownership" for edge in graph["edges"])
    assert any(edge["source"] == "item:notebook_prepare" and edge["target"] == "item:pipeline_prepare" and edge["kind"] == "dependency" for edge in graph["edges"])
    value["modules"]["architecture_input"]["physical_items"][0]["workspace_ref"] = "unknown"
    with pytest.raises(ValueError, match="workspace or environment"):
        compile_architecture(value, "a" * 64)


@pytest.mark.parametrize("mutation", ["cycle", "missing", "environment", "duplicate", "name", "workspace", "decision", "base64", "path", "duplicate_part", "format", "platform"])
def test_incomplete_or_conflicting_definitions_fail_closed(mutation):
    value = data()
    items = value["modules"]["architecture_input"]["physical_items"]
    notebook = items[1]
    if mutation == "cycle": notebook["depends_on"] = ["pipeline_prepare"]
    if mutation == "missing": notebook["depends_on"] = ["unknown"]
    if mutation == "environment": notebook["environment"] = "prod"
    if mutation == "duplicate": items.append(copy.deepcopy(notebook))
    if mutation == "name": notebook["name"] = items[0]["name"]
    if mutation == "workspace": notebook["workspace_ref"] = "unknown"
    if mutation == "decision": notebook["decision_refs"] = ["unapproved"]
    if mutation == "base64": notebook["definition"]["parts"][0]["payload"] = "garbage!"
    if mutation == "path": notebook["definition"]["parts"][0]["path"] = "../outside.py"
    if mutation == "duplicate_part": notebook["definition"]["parts"] *= 2
    if mutation == "format": notebook["definition"]["format"] = "ipynb"
    if mutation == "platform": notebook["definition"]["parts"].append(part(".platform", {"metadata": {"displayName": "other", "type": "Notebook"}}))
    with pytest.raises(ValueError): compile_item_plan(value)
    assert item_target(value)["status"] == "blocked"


def test_json_binding_checks_exact_field_not_incidental_text():
    value = data()
    pipeline = value["modules"]["architecture_input"]["physical_items"][0]
    pipeline["environment_bindings"] = [{"part_path": "pipeline-content.json", "json_pointer": "/properties/parameters/environment/defaultValue", "expected_value": "dev", "authority_ref": "fixture:environment"}]
    assert compile_item_plan(value)
    pipeline["environment_bindings"][0]["json_pointer"] = "/properties/activities"
    with pytest.raises(ValueError, match="exact JSON-pointer"):
        compile_item_plan(value)


def test_source_code_bindings_require_parser_even_when_value_is_present():
    value = data()
    notebook = value["modules"]["architecture_input"]["physical_items"][1]
    notebook["environment_bindings"] = [{"part_path": "notebook-content.py", "json_pointer": "", "expected_value": "Supplied definition", "authority_ref": "fixture:environment"}]
    with pytest.raises(ValueError, match="supported parser"):
        compile_item_plan(value)


def test_optional_schema_is_backward_compatible_and_definition_is_not_arbitrary():
    validator = Draft202012Validator(json.loads((SCHEMAS / "project_architecture_input.schema.json").read_text(encoding="utf-8")), format_checker=FormatChecker())
    assert not list(validator.iter_errors(compiler()["modules"]["architecture_input"]))
    architecture = data()["modules"]["architecture_input"]
    assert not list(validator.iter_errors(architecture))
    architecture["physical_items"][0]["type"] = "UnsupportedMagicTool"
    assert list(validator.iter_errors(architecture))


def full_repository(tmp_path):
    package = migrate_project_package(ROOT / "tooling/tests/fixtures/project_package/v1", tmp_path / "input", SCHEMAS)
    manifest = yaml.safe_load((package / "package.yaml").read_text(encoding="utf-8"))
    document = data()
    decisions = adapt_decision_proposals([_proposal()])
    instance = decisions["instances"][0]
    instance["id"] = "decision_environment_model"
    instance["selection"]["state"] = "confirmed"
    instance["approval"] = {"state": "approved", "proposed_by": "fixture", "decided_by": "fixture", "rationale": "Explicit fixture environment decision"}
    decision_path = package / "discovery/decision_set.yaml"
    decision_path.write_text(yaml.safe_dump(decisions), encoding="utf-8")
    for module in manifest["modules"]:
        if module["module_type"] == "decision_set": module["sha256"] = canonical_sha256(decisions)
    for kind in ("architecture_input", "use_case_delivery"):
        module = document["modules"][kind]
        (package / f"{kind}.yaml").write_text(yaml.safe_dump(module), encoding="utf-8")
        schema = json.loads((SCHEMAS / f"project_{kind}.schema.json").read_text(encoding="utf-8"))
        manifest["modules"].append({"module_type": kind, "path": f"{kind}.yaml", "schema_id": schema["$id"], "sha256": canonical_sha256(module)})
    manifest["state"] = "approved"
    (package / "package.yaml").write_text(yaml.safe_dump(manifest), encoding="utf-8")
    repository = ProjectPackageRevisionRepository(tmp_path / "repositories/project_demo", SCHEMAS)
    record = repository.commit(package)
    return repository, record


def test_three_target_actual_repository_release_to_saved_artifacts(tmp_path):
    repository, record = full_repository(tmp_path)
    with pytest.raises(ValueError, match="no explicit release"):
        build_item_output(repository, "project_demo", record.revision_hash)
    release_input(repository, "project_demo", record.revision_hash, actor="fixture", rationale="Release exact neutral definitions for transport test.")
    status = read_automation(repository, "project_demo", record.revision_hash)
    # Drei Ziele -- so heisst der Test, und so listet sie der Lauf unten auf. Seit
    # `batch_ingestion` dazukam, gibt es ein viertes: es steht hier auf `blocked`,
    # weil diese Fixture bewusst KEINEN Batch-Ingestion-Vertrag speichert. Das ist
    # das richtige Verhalten, nicht der Fehlerfall.
    #
    # Vorher stand hier `all(... == "ready")` -- eine Zusage, die das Modul mit dem
    # vierten Ziel nicht mehr halten konnte und auch nicht halten SOLL. Die Zeile
    # prueft jetzt, was der Test behauptet: die drei genannten sind bereit, das
    # vierte nennt seinen Grund. Damit faellt der Test wieder, wenn eines der drei
    # kippt -- und meldet nicht mehr Alarm, wenn ein neues Ziel korrekt blockiert.
    zustand = {t["id"]: t for t in status["targets"]}
    for ziel in ("architecture_bundle", "fabric_workspace_requests", "fabric_item_requests"):
        assert zustand[ziel]["status"] == "ready", zustand[ziel]
    assert zustand["batch_ingestion_bundle"]["status"] == "blocked"
    assert "batch_ingestion" in zustand["batch_ingestion_bundle"]["reason"]
    output = build_item_output(repository, "project_demo", record.revision_hash)
    body = json.loads(next(file["content"] for file in output["files"] if file["path"] == "fabric/items/notebook_prepare.request.json"))
    assert body["definition"] == native_item()["definition"]
    assert set(body) == {"displayName", "type", "definition"}
    run = run_automation(repository, "project_demo", record.revision_hash, actor="fixture", confirm_generation=True)
    assert run["report"]["targets"] == ["architecture_bundle", "fabric_item_requests", "fabric_workspace_requests"]
    assert not run["report"]["delivery_complete"]
    assert any(file["path"].startswith("fabric_item_requests/") for file in run["files"])
    repository.verify()
