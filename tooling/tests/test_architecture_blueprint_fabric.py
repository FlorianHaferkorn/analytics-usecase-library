"""
test_architecture_blueprint_fabric.py — ADR-0015 / T4.

Guards the Fabric arch-target renderer:
  - it emits the expected plan artifacts from a derived blueprint;
  - the shortcut/mirror plan reflects ingestion access modes (P1);
  - rendering is deterministic;
  - the gold data-product name-set in the output matches the blueprint (cross-target
    parity, analogous to targets/test_cross_target_equivalence);
  - render(dest) actually writes the files.
"""
from __future__ import annotations

import json

from tooling.superversion.architecture_blueprint import derive_blueprint
from tooling.superversion import arch_targets

_FIXTURE = {
    "stack": "fabric",
    "silver_contract_ref": "core/data_contracts/domains/commercial.yaml",
    "domains": [
        {
            "name": "Commercial",
            "gold_products": [
                {"name": "dim_customer", "kind": "dimension"},
                {"name": "fact_sales", "kind": "fact"},
            ],
            "sources": [
                {"source": "crm_orders", "source_system": "Dynamics 365"},
                {"source": "web_events", "source_system": "ADLS Gen2"},
            ],
            "endorsement": "certified",
        }
    ],
}


def _bp():
    return derive_blueprint(_FIXTURE)["blueprint"]


_TOPOLOGY = {
    "fabric/PROVISIONING_PLAN.md",
    "fabric/workspaces.json",
    "fabric/ingestion_plan.json",
    "fabric/medallion.json",
    "fabric/semantic_binding.json",
}


def test_emits_expected_artifacts():
    out = arch_targets.render("fabric", _bp())
    assert _TOPOLOGY <= set(out)
    ws = json.loads(out["fabric/workspaces.json"])
    names = {w["name"] for d in ws for w in d["workspaces"]}
    assert "ws-commercial-gold" in names and "ws-commercial-reporting" in names


def test_mirrored_meridian_layer_is_emitted_alongside_the_topology():
    """The topology layer alone was never the whole Fabric scaffold — governance,
    monitoring, lifecycle, connectivity and operability come from the mirrored Meridian
    emitters (SHARED_SUBSTANCE.md class A) instead of a second implementation here."""
    from tooling.superversion._dataarch_vendor import available

    out = arch_targets.render("fabric", _bp())
    if not available():
        # A broken/absent mirror must degrade loudly, not silently.
        assert "**Not emitted**" in out["fabric/PROVISIONING_PLAN.md"]
        assert set(out) == _TOPOLOGY
        return

    extra = set(out) - _TOPOLOGY
    assert extra, "mirror is available but contributed nothing"
    for prefix in ("fabric/governance/", "fabric/monitoring/", "fabric/lifecycle/",
                   "fabric/connectivity/"):
        assert any(p.startswith(prefix) for p in extra), f"no artifact under {prefix}"
    # And the runbook must name what it emitted, so the plan stays self-describing.
    plan = out["fabric/PROVISIONING_PLAN.md"]
    assert "mirrored Meridian emitters" in plan


def test_ingestion_access_modes():
    out = arch_targets.render("fabric", _bp())
    plan = {e["source"]: e["access_mode"] for e in json.loads(out["fabric/ingestion_plan.json"])}
    assert plan == {"crm_orders": "mirror", "web_events": "shortcut"}


def test_medallion_no_layer_skip_and_grounding():
    out = arch_targets.render("fabric", _bp())
    med = json.loads(out["fabric/medallion.json"])
    assert med["no_layer_skip"] is True
    assert "gold" in out["fabric/PROVISIONING_PLAN.md"].lower()
    assert "never bronze" in out["fabric/PROVISIONING_PLAN.md"]


def test_render_is_deterministic():
    a = arch_targets.render("fabric", _bp())
    b = arch_targets.render("fabric", _bp())
    assert a == b


def test_gold_name_parity_with_blueprint():
    bp = _bp()
    out = arch_targets.render("fabric", bp)
    med = json.loads(out["fabric/medallion.json"])
    out_names = sorted(p["name"] for p in med["gold"]["data_products"])
    bp_names = sorted(p["name"] for p in bp["medallion"]["gold"]["data_products"])
    assert out_names == bp_names == ["dim_customer", "fact_sales"]


def test_render_writes_files(tmp_path):
    written = arch_targets.render("fabric", _bp(), dest=tmp_path)
    for rel in written:
        assert (tmp_path / rel).is_file()
    assert (tmp_path / "fabric" / "PROVISIONING_PLAN.md").read_text(encoding="utf-8").startswith(
        "# Fabric Provisioning Plan"
    )


def test_fabric_is_registered():
    assert "fabric" in arch_targets.available()


# -- source introspection (mirrored, two-phase) --------------------------------------


_ROWS = ("TABLE_SCHEMA,TABLE_NAME,COLUMN_NAME,DATA_TYPE,IS_NULLABLE\n"
         "dbo,Orders,OrderId,int,NO\n"
         "dbo,Orders,ChangedOn,datetime2,YES\n")


def test_phase_one_ships_without_being_asked():
    """The introspection question costs nothing and is the step that gets forgotten, so
    it is emitted on every render — not behind a flag."""
    out = arch_targets.render("fabric", _bp())
    assert "fabric/source_schema/queries/crm_orders.sql" in out
    assert "INFORMATION_SCHEMA.COLUMNS" in out["fabric/source_schema/queries/crm_orders.sql"]


def test_unanswered_sources_are_named_in_the_runbook():
    plan = arch_targets.render("fabric", _bp())["fabric/PROVISIONING_PLAN.md"]
    assert "not answered yet" in plan
    assert "--source-schema-results" in plan


def test_answered_source_becomes_a_grounded_schema():
    out = arch_targets.render("fabric", _bp(), source_schema_results={"crm_orders": _ROWS})
    schema = json.loads(out["fabric/source_schema/schemas/crm_orders.json"])
    assert schema["source"] == "crm_orders"
    assert {c["name"] for c in schema["schema"][0]["properties"]} == {"OrderId", "ChangedOn"}
    # answered → the runbook stops asking for it
    assert "not answered yet" not in out["fabric/PROVISIONING_PLAN.md"]


def test_a_file_source_gets_a_note_not_a_sql_statement():
    """ADLS has no catalogue to query; emitting a SELECT against it would be theatre."""
    out = arch_targets.render("fabric", _bp())
    assert "fabric/source_schema/queries/web_events.md" in out
    assert "fabric/source_schema/queries/web_events.sql" not in out


def test_unsupported_option_names_itself():
    import pytest

    with pytest.raises(arch_targets.ArchContractError, match="nonsense"):
        arch_targets.render("fabric", _bp(), nonsense=1)


# -- gold target per domain (ADR-0024) -------------------------------------------------


def test_default_gold_target_is_byte_identical_to_no_option():
    """`warehouse_dbt` is the default: naming it changes nothing, byte for byte. This is the
    regression guard for every input file written before the field existed."""
    from tooling.superversion.architecture_blueprint import gold_targets

    inputs = {**_FIXTURE, "domains": [{**_FIXTURE["domains"][0], "gold_target": "warehouse_dbt"}]}
    assert gold_targets(inputs) == {}
    assert arch_targets.render("fabric", _bp()) == arch_targets.render(
        "fabric", derive_blueprint(inputs)["blueprint"])


def test_mlv_domain_gets_views_and_loses_its_gold_transforms():
    from tooling.superversion._dataarch_vendor import available

    if not available():
        return
    out = arch_targets.render("fabric", _bp(), gold_targets={"Commercial": "mlv"})
    assert {"fabric/mlv/commercial/dim_customer.mlv.sql", "fabric/mlv/commercial/fact_sales.mlv.sql",
            "fabric/mlv/_MLV.md", "fabric/mlv/refresh_schedule.json"} <= set(out)
    # one store per product: no notebook and no CTAS for the MLV products
    assert not any(p.startswith("fabric/transforms/commercial/silver_to_gold__") for p in out)
    assert not any(p.startswith("fabric/notebooks/nb_gold_") for p in out)
    # MLV needs a schema-enabled lakehouse, so the whole run is schema-enabled
    assert "enableSchemas=true" in out["fabric/provision.sh"]
    plan = json.loads(out["fabric/apply/APPLY_PLAN.json"])
    actions = [op["action"] for op in plan]
    assert "schedule_mlv_refresh" in actions
    assert {op["artifact"] for op in plan if op["action"] == "run_sql_ddl"} == {
        "mlv/commercial/dim_customer.mlv.sql", "mlv/commercial/fact_sales.mlv.sql"}
    assert "Gold target per domain (ADR-0024): Commercial → **mlv**" in out["fabric/PROVISIONING_PLAN.md"]


def test_graph_schedule_adds_the_execution_definition():
    from tooling.superversion._dataarch_vendor import available

    if not available():
        return
    out = arch_targets.render("fabric", _bp(), gold_targets={"Commercial": "mlv"},
                              mlv_zeitplan="graph")
    assert "fabric/mlv/execution_definition.json" in out
    schedule = json.loads(out["fabric/mlv/refresh_schedule.json"])
    assert "mlvExecutionDefinitionId" in schedule["executionData"]
    actions = [op["action"] for op in json.loads(out["fabric/apply/APPLY_PLAN.json"])]
    assert actions.index("create_mlv_execution_definition") < actions.index("schedule_mlv_refresh")


def test_onelake_role_mode_reaches_the_apply_plan_without_mlv():
    from tooling.superversion._dataarch_vendor import available

    if not available():
        return
    for modus, verb in (("gesamt", "PUT"), ("einzeln", "POST")):
        out = arch_targets.render("fabric", _bp(), onelake_rollen_modus=modus)
        step = next(op for op in json.loads(out["fabric/apply/APPLY_PLAN.json"])
                    if op["action"] == "apply_onelake_roles")
        assert verb in step["tool"], (modus, step["tool"])
        assert f"mode **{modus}**" in out["fabric/PROVISIONING_PLAN.md"]


def test_mlv_options_without_an_mlv_domain_are_refused():
    import pytest

    for kw in ({"mlv_refresh_hints": True}, {"mlv_zeitplan": "graph"}, {"governed_catalog": {}}):
        with pytest.raises(arch_targets.ArchContractError, match="only take effect"):
            arch_targets.render("fabric", _bp(), **kw)


def test_bad_gold_targets_are_refused_by_name():
    import pytest

    with pytest.raises(arch_targets.ArchContractError, match="unknown target"):
        arch_targets.render("fabric", _bp(), gold_targets={"Commercial": "lakeview"})
    with pytest.raises(arch_targets.ArchContractError, match="does not have"):
        arch_targets.render("fabric", _bp(), gold_targets={"Nowhere": "mlv"})
    with pytest.raises(arch_targets.ArchContractError, match="mlv_zeitplan"):
        arch_targets.render("fabric", _bp(), gold_targets={"Commercial": "mlv"}, mlv_zeitplan="nightly")
    with pytest.raises(arch_targets.ArchContractError, match="onelake_rollen_modus"):
        arch_targets.render("fabric", _bp(), onelake_rollen_modus="alle")


def test_a_product_cannot_live_in_two_gold_stores():
    import pytest

    two = {**_FIXTURE, "domains": [
        _FIXTURE["domains"][0],
        {"name": "Finance", "gold_products": [{"name": "fact_sales", "kind": "fact"}]},
    ]}
    bp = derive_blueprint(two)["blueprint"]
    with pytest.raises(arch_targets.ArchContractError, match="one gold store per product"):
        arch_targets.render("fabric", bp, gold_targets={"Commercial": "mlv"})


def test_other_stacks_refuse_the_gold_target():
    """Databricks and Snowflake have no MLV — the choice must not pass silently there."""
    import pytest

    for stack in ("databricks", "snowflake"):
        with pytest.raises(arch_targets.ArchContractError, match="gold_targets"):
            arch_targets.render(stack, _bp(), gold_targets={"Commercial": "mlv"})
