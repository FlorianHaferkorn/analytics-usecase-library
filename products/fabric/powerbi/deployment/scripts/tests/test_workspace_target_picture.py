"""Workspace target picture in fabric_setup.py (I-21 W1.9, W1.11, W1.12), pinned.

Golden fixtures are the `--target-picture` output for dev and prd. Regenerate after an
intended change with:

    python products/fabric/powerbi/deployment/scripts/fabric_setup.py \
        --environment prd --target-picture > .../tests/fixtures/target_picture_prd.json

and review the diff. The cross-checks below hold the declared values against the things they
depend on (environment JSON, OAP support, the release script's default item types), so a change
on one side cannot silently drift from the other. No Fabric tenant, no network.

Microsoft Learn sources (read 01.10.2026):
- fabric/security/workspace-outbound-access-protection-overview, …-semantic-models,
  …-power-bi-reports, fabric/cicd/cicd-security
- fabric/enterprise/surge-protection (workspace level: preview, portal steps only, no API)
- fabric/governance/fabric-policies-overview, fabric-policies-item-creation
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

_SCRIPTS = Path(__file__).resolve().parents[1]
_FIXTURES = Path(__file__).resolve().parent / "fixtures"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import fabric_setup as setup  # noqa: E402

ENVIRONMENTS = ("dev", "tst", "prd")

#: Item types Learn lists as OAP-supported (overview table) that ALUCA's layers can hold.
#: Reports are deliberately absent: the overview says Power BI items other than semantic models
#: are unsupported; the report page (preview) allows them only bound to a same-workspace model.
OAP_SUPPORTED = {"Lakehouse", "Notebook", "DataPipeline", "SemanticModel",
                 "SparkJobDefinition", "Environment", "Warehouse"}


def _definition(environment: str) -> dict:
    definition = setup.load_env_definition(environment)
    assert definition, f"environment JSON for {environment} did not load"
    return definition


@pytest.mark.parametrize("environment", ["dev", "prd"])
def test_cli_output_matches_golden_fixture(environment):
    out = subprocess.run(
        [sys.executable, str(_SCRIPTS / "fabric_setup.py"), "--environment", environment,
         "--target-picture"],
        capture_output=True, text=True, encoding="utf-8", check=True,
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    ).stdout
    golden = json.loads((_FIXTURES / f"target_picture_{environment}.json").read_text("utf-8"))
    assert json.loads(out) == golden


@pytest.mark.parametrize("environment", ENVIRONMENTS)
def test_every_configured_layer_has_a_declared_stance_and_type_list(environment):
    layers = [k for k, v in _definition(environment)["layers"].items() if isinstance(v, dict)]
    assert set(layers) <= set(setup.NETWORK_STANCE_BY_LAYER)
    assert set(layers) <= set(setup.ALLOWED_ITEM_TYPES_BY_LAYER)


def test_oap_stances_use_the_declared_vocabulary():
    for layer, stance in setup.NETWORK_STANCE_BY_LAYER.items():
        assert stance["outbound_access_protection"] in setup.OAP_STANCES, layer
        if stance["outbound_access_protection"] == "on_with_rules":
            assert stance["connection_rules"], f"{layer}: OAP on without any rule blocks refresh"


def test_w19_cut_bi_off_dm_on_with_rules():
    assert setup.NETWORK_STANCE_BY_LAYER["BI"]["outbound_access_protection"] == "off"
    dm = setup.NETWORK_STANCE_BY_LAYER["DM"]
    assert dm["outbound_access_protection"] == "on_with_rules"
    rules = " ".join(dm["connection_rules"])
    assert "SQL Server" in rules and "ADLS Gen2" in rules


def test_protected_layers_only_allow_oap_supported_item_types():
    """OAP cannot be enabled while an unsupported item sits in the workspace, and such items
    cannot be created afterwards — the allowed list must not contradict the OAP stance."""
    for layer, stance in setup.NETWORK_STANCE_BY_LAYER.items():
        if stance["outbound_access_protection"] != "on_with_rules":
            continue
        allowed = setup.ALLOWED_ITEM_TYPES_BY_LAYER[layer]
        assert allowed is not None, f"{layer}: protected but item types unrestricted"
        assert set(allowed) <= OAP_SUPPORTED, f"{layer}: {set(allowed) - OAP_SUPPORTED}"


@pytest.mark.parametrize("environment", ENVIRONMENTS)
def test_configured_items_stay_inside_the_target_picture(environment):
    assert setup.item_type_violations(_definition(environment)) == []


def test_violation_is_reported_not_swallowed():
    definition = {"layers": {"BI": {"items": {"Report": [], "Lakehouse": []}}}}
    assert setup.item_type_violations(definition) == [
        "BI: item type 'Lakehouse' not in ['Report']"]


def test_allowed_types_cover_the_release_default_item_types():
    """fabric_release.py publishes DEFAULT_ITEM_TYPES; each must have a home workspace type."""
    src = (_SCRIPTS / "fabric_release.py").read_text(encoding="utf-8")
    default = re.search(r'^DEFAULT_ITEM_TYPES = "([^"]+)"', src, re.M).group(1).split(",")
    allowed = {t for types in setup.ALLOWED_ITEM_TYPES_BY_LAYER.values() if types for t in types}
    assert set(default) <= allowed


def test_surge_class_per_environment():
    assert setup.SURGE_CLASS_BY_ENVIRONMENT == {
        "dev": "capped", "tst": "capped", "prd": "mission_critical"}
    for environment in ENVIRONMENTS:
        surge = setup.workspace_target_picture(_definition(environment))["surge_protection"]
        assert surge["mechanism"] == "manual"  # no documented API on Learn (01.10.2026)
        if surge["class"] == "capped":
            assert "workspace_cu_limit_pct" in surge


def test_cu_limit_is_a_gap_until_set_never_a_guess():
    for environment in ("dev", "tst"):
        surge = setup.workspace_target_picture(_definition(environment))["surge_protection"]
        assert surge["workspace_cu_limit_pct"] is None


def test_unknown_environment_fails_loudly():
    with pytest.raises(ValueError):
        setup.workspace_target_picture({"generic": {"environment_name": "qa"}, "layers": {}})


def test_item_creation_rules_keep_other_workspaces_unrestricted():
    """One allow rule turns the capacity policy into an allow list; the catch-all must name
    exactly the restricted workspaces, otherwise every other workspace is blocked."""
    picture = setup.workspace_target_picture(_definition("prd"))
    rules = picture["item_creation_policy"]["rules"]
    restricted = [r["workspaces"]["AnyOf"][0] for r in rules if "AnyOf" in r["workspaces"]]
    catch_all = [r for r in rules if "NoneOf" in r["workspaces"]]
    assert len(catch_all) == 1 and catch_all[0]["workspaces"]["NoneOf"] == restricted
    assert "item_type" not in catch_all[0]
    assert len(rules) <= 50  # capacity-scoped policies: up to 50 rules (Learn)
    assert "West Europe" in picture["item_creation_policy"]["unsupported_regions"]
