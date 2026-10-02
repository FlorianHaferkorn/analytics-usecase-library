"""Gold target of the Trf layer (ALUCA ADR-0024, amended 02.10.2026).

`gold_target: lakehouse | warehouse` in config.yaml. Recommendation lakehouse, default warehouse
(unchanged behaviour for configs without the key). Pins what each choice provisions and which
dbt adapter the generated skeleton targets.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

pytest.importorskip("typer", reason="orchestrator deps (see products/fabric/orchestrator/requirements.txt)")
pytest.importorskip("rich", reason="orchestrator deps")
pytest.importorskip("msal", reason="orchestrator deps")

_ORCH = Path(__file__).resolve().parents[1] / "orchestrator.py"


def _load():
    spec = importlib.util.spec_from_file_location("_orchestrator_gold_target", _ORCH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


orch = _load()


class _Config:
    def __init__(self, data: dict):
        self._data = data

    def get(self, key_path: str, default=None):
        cur = self._data
        for part in key_path.split("."):
            if not isinstance(cur, dict) or part not in cur:
                return default
            cur = cur[part]
        return cur


def test_default_is_warehouse_and_recommendation_is_lakehouse():
    assert orch.resolve_gold_target(_Config({})) == "warehouse" == orch.DEFAULT_GOLD_TARGET
    assert orch.RECOMMENDED_GOLD_TARGET == "lakehouse"
    assert orch.resolve_gold_target(_Config({"gold_target": "Lakehouse"})) == "lakehouse"


def test_unknown_gold_target_is_rejected():
    with pytest.raises(orch.ConfigurationError, match="gold_target"):
        orch.resolve_gold_target(_Config({"gold_target": "warehouse_dbt"}))


@pytest.mark.parametrize("target,item", [(None, "Warehouse"), ("warehouse", "Warehouse"),
                                         ("lakehouse", "Lakehouse")])
def test_trf_item_follows_gold_target(target, item):
    cfg = _Config({} if target is None else {"gold_target": target})
    prov = orch.ItemProvisioner(api=None, config=cfg)
    assert prov._get_layer_items("Trf") == [item]
    assert prov._get_layer_items("Src") == ["Lakehouse"]


def test_explicit_layer_items_override_still_wins():
    cfg = _Config({"gold_target": "lakehouse",
                   "item_provisioner": {"layer_items": {"Trf": ["Warehouse", "Notebook"]}}})
    assert orch.ItemProvisioner(api=None, config=cfg)._get_layer_items("Trf") == ["Warehouse", "Notebook"]


def test_warehouse_skeleton_uses_dbt_fabric_unchanged():
    gen = orch.TemplateGenerator(_Config({}))
    cfg = gen._build_dbt_project_configs("Sales")
    dev = cfg["profiles"]["fabric"]["outputs"]["dev"]
    assert dev["type"] == "fabric"
    assert dev["server"] == "sales-trf-dev.datawarehouse.fabric.microsoft.com"
    assert cfg["dbt_project"]["models"]["sales_dbt"]["gold"]["+schema"] == "gold"
    assert "GETDATE()" in cfg["fact_sql"]


def test_lakehouse_skeleton_uses_dbt_fabricspark_over_livy():
    gen = orch.TemplateGenerator(_Config({"gold_target": "lakehouse"}))
    cfg = gen._build_dbt_project_configs("Sales")
    outputs = cfg["profiles"]["fabricspark"]["outputs"]
    assert set(outputs) == {"dev", "test", "prod"}
    dev = outputs["dev"]
    assert dev["type"] == "fabricspark" and dev["method"] == "livy"
    assert dev["lakehouse"] == dev["schema"] == "sales_trf"  # no-schema lakehouse: two-part naming
    assert "FABRIC_TRF_LAKEHOUSE_ID_DEV" in dev["lakehouseid"]
    assert dev["authentication"] == "SPN"
    assert cfg["dbt_project"]["profile"] == "fabricspark"
    assert "+schema" not in cfg["dbt_project"]["models"]["sales_dbt"]["gold"]
    # Spark SQL, not T-SQL
    assert "GETDATE" not in cfg["fact_sql"] and "DATEADD" not in cfg["fact_sql"]
    assert "add_months(current_date(), -24)" in cfg["fact_sql"]


def test_explicit_argument_overrides_config():
    gen = orch.TemplateGenerator(_Config({"gold_target": "lakehouse"}))
    assert gen._build_dbt_project_configs("Sales", "warehouse")["profiles"]["fabric"]
