"""USAGE.md's refresh contract, pinned against the deploy code.

USAGE.md ("Semantic Model Refresh After a Release") carries a `refresh_contract` YAML block
that says what the release automation does about refresh. These tests read that block and
the code as text, so the doc cannot claim "no on-demand refresh" while a script starts one,
or name a schedule step that no longer exists. They import nothing deployment-only.

Microsoft facts behind the block (Learn, checked 29.09.2026):
- the refresh-schedule request body has no table or schema field
  (rest/api/power-bi/datasets/update-refresh-schedule-in-group);
- the enhanced refresh API takes `type` and `objects` (tables/partitions), no schema-sync type
  (power-bi/connect-data/asynchronous-refresh).
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

_DEPLOYMENT = Path(__file__).resolve().parents[2]
_USAGE_MD = _DEPLOYMENT / "USAGE.md"
_ORCHESTRATOR = _DEPLOYMENT.parent / "orchestrator"

# An on-demand refresh is a call to the /refreshes collection (Power BI REST) or a Fabric job
# of type "Refresh" on a semantic model. refreshSchedule does not match (no trailing "es").
_ON_DEMAND = re.compile(r"/refreshes\b|jobType\s*[=:]\s*[\"']?Refresh\b", re.IGNORECASE)
_SCHEDULE = re.compile(r"/refreshSchedule\b")


def _contract() -> dict:
    text = _USAGE_MD.read_text(encoding="utf-8")
    for block in re.findall(r"```yaml\n(.*?)```", text, flags=re.DOTALL):
        data = yaml.safe_load(block)
        if isinstance(data, dict) and "refresh_contract" in data:
            return data["refresh_contract"]
    raise AssertionError("USAGE.md has no ```yaml block with `refresh_contract`")


def _deploy_code() -> dict[Path, str]:
    files = sorted((_DEPLOYMENT / "scripts").rglob("*.py")) + sorted(_ORCHESTRATOR.glob("*.ps1"))
    return {
        p: p.read_text(encoding="utf-8")
        for p in files
        if "tests" not in p.relative_to(_DEPLOYMENT.parent).parts
    }


def test_contract_block_has_all_fields():
    assert set(_contract()) >= {
        "on_demand_refresh_trigger",
        "schedule",
        "schedule_scope",
        "schema_sync_via_api",
        "table_refresh_via_api",
    }


def test_on_demand_trigger_claim_matches_code():
    triggers = sorted(str(p.name) for p, src in _deploy_code().items() if _ON_DEMAND.search(src))
    claim = _contract()["on_demand_refresh_trigger"]
    if claim == "none":
        assert not triggers, (
            f"USAGE.md says no on-demand refresh, but {triggers} call /refreshes — "
            f"describe the trigger in USAGE.md and update refresh_contract"
        )
    else:
        assert triggers, f"USAGE.md names an on-demand trigger ({claim!r}), the code has none"


def test_schedule_claim_points_at_the_file_that_sets_it():
    schedule_files = sorted(
        p.relative_to(_DEPLOYMENT.parent).as_posix()
        for p, src in _deploy_code().items()
        if _SCHEDULE.search(src)
    )
    assert schedule_files == [_contract()["schedule"]]


def test_scope_fields_state_the_documented_api_limits():
    c = _contract()
    assert c["schedule_scope"] == "whole_model"
    assert c["schema_sync_via_api"] == "not_documented"
    assert c["table_refresh_via_api"] == "enhanced_refresh"
