"""GovernanceManager — pins the *official* contract, not our earlier guesses.

Regression cover for two invented surfaces that used to live here:
  * ``POST workspaces/{ws}/governanceLabels`` — does not exist. Sensitivity labels are
    written only by the Power BI admin API ``admin/informationprotection/setLabels``,
    on a different host and a different token audience, keyed by label **GUID**, with
    artifact IDs bucketed by type.
  * ``PATCH items/{id}/endorsement`` — does not exist either; endorsement has no
    documented write REST API, so it must degrade to a manual step.
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
    spec = importlib.util.spec_from_file_location("_orchestrator_under_test", _ORCH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


orch = _load()

LABEL_GUID = "fe472f5e-636e-4c10-a1c6-7e9edc0b542a"


class _Config:
    """Minimal ConfigLoader stand-in: dotted-path lookup over a plain dict."""

    def __init__(self, data: dict):
        self._data = data

    def get(self, key_path: str, default=None):
        cur = self._data
        for part in key_path.split("."):
            if not isinstance(cur, dict) or part not in cur:
                return default
            cur = cur[part]
        return cur


class _Api:
    """Records calls instead of issuing them."""

    def __init__(self, response=None):
        self.calls: list[dict] = []
        self._response = response

    def post(self, endpoint, json_data, base=None, scopes=None):
        self.calls.append({"endpoint": endpoint, "json": json_data, "base": base, "scopes": scopes})
        return self._response

    def patch(self, endpoint, json_data):  # pragma: no cover - must never be reached
        raise AssertionError(f"unexpected PATCH {endpoint}")


def _mgr(api, labels: dict):
    return orch.GovernanceManager(api, _Config({"governance": {"sensitivity_labels": labels}}))


# -- the invented endpoints are gone ----------------------------------------------


def test_source_contains_no_invented_endpoints():
    src = _ORCH.read_text(encoding="utf-8")
    assert "governanceLabels" not in src
    assert "items/{item_id}/endorsement" not in src


def test_workspace_creation_issues_no_label_call():
    """Labels attach to items; a fresh workspace has none. So: no API call, ever."""
    api = _Api()
    mgr = _mgr(api, {"mode": "purview_policy", "dev": "General"})
    assert mgr.declare_workspace_labeling("ws-1", "dev") is True
    assert api.calls == []
    assert mgr.manual_steps, "the unmet requirement must be reported, not swallowed"


def test_endorsement_degrades_to_manual_step():
    api = _Api()
    mgr = _mgr(api, {})
    # False = "not applied" — callers must not read this as success.
    assert mgr.set_endorsement("item-1", "SemanticModel", "Certified") is False
    assert api.calls == []
    assert any("Endorsement 'Certified'" in s for s in mgr.manual_steps)


# -- purview_policy mode is inert by design ---------------------------------------


def test_purview_mode_never_calls_setlabels():
    api = _Api()
    mgr = _mgr(api, {"mode": "purview_policy", "prod": "Confidential"})
    assert mgr.apply_sensitivity_labels({"reports": ["r1"]}, "prod") is True
    assert api.calls == []


def test_unconfigured_environment_is_a_noop():
    api = _Api()
    mgr = _mgr(api, {"mode": "admin_api"})
    assert mgr.apply_sensitivity_labels({"reports": ["r1"]}, "staging") is True
    assert api.calls == []


def test_unknown_mode_is_rejected():
    api = _Api()
    mgr = _mgr(api, {"mode": "yolo", "dev": "General"})
    with pytest.raises(orch.ConfigurationError):
        mgr.declare_workspace_labeling("ws-1", "dev")


# -- admin_api mode: exact documented payload -------------------------------------


def test_setlabels_payload_matches_official_contract():
    api = _Api({"reports": [{"id": "r1", "status": "Succeeded"}]})
    mgr = _mgr(api, {"mode": "admin_api", "prod": LABEL_GUID})

    assert mgr.apply_sensitivity_labels({"reports": ["r1"]}, "prod") is True

    call = api.calls[0]
    assert call["endpoint"] == "admin/informationprotection/setLabels"
    # Different host AND different audience than the Fabric API.
    assert call["base"] == "https://api.powerbi.com/v1.0/myorg"
    assert call["scopes"] == ["https://analysis.windows.net/powerbi/api/.default"]
    # 'labelId' (GUID), never 'labelName'; artifacts bucketed by type, never a flat list.
    assert call["json"] == {
        "artifacts": {"reports": [{"id": "r1"}]},
        "labelId": LABEL_GUID,
        "assignmentMethod": "Standard",
    }


def test_label_name_rejected_in_admin_api_mode():
    """setLabels takes a GUID; a display name would 404/NotFound at runtime."""
    api = _Api()
    mgr = _mgr(api, {"mode": "admin_api", "prod": "Confidential"})
    with pytest.raises(orch.ConfigurationError, match="GUID"):
        mgr.apply_sensitivity_labels({"reports": ["r1"]}, "prod")
    assert api.calls == []


def test_unsupported_artifact_bucket_rejected():
    """Lakehouses/notebooks/warehouses have no label-write API at all."""
    api = _Api()
    mgr = _mgr(api, {"mode": "admin_api", "prod": LABEL_GUID})
    with pytest.raises(orch.ConfigurationError, match="lakehouses"):
        mgr.apply_sensitivity_labels({"lakehouses": ["lh1"]}, "prod")
    assert api.calls == []


def test_batch_cap_enforced_before_the_call():
    api = _Api()
    mgr = _mgr(api, {"mode": "admin_api", "prod": LABEL_GUID})
    with pytest.raises(orch.ConfigurationError, match="2000"):
        mgr.apply_sensitivity_labels({"reports": [f"r{i}" for i in range(2001)]}, "prod")
    assert api.calls == []


def test_delegated_user_added_only_when_given():
    api = _Api({"reports": [{"id": "r1", "status": "Succeeded"}]})
    mgr = _mgr(api, {"mode": "admin_api", "prod": LABEL_GUID})
    mgr.apply_sensitivity_labels({"reports": ["r1"]}, "prod", delegated_user_email="a@b.c")
    assert api.calls[0]["json"]["delegatedUser"] == {"emailAddress": "a@b.c"}


def test_http_200_with_failed_artifact_is_not_success():
    """The API returns 200 even when individual artifacts failed — read the statuses."""
    api = _Api({
        "reports": [{"id": "r1", "status": "Succeeded"}],
        "datasets": [{"id": "d1", "status": "InsufficientUsageRights"}],
    })
    mgr = _mgr(api, {"mode": "admin_api", "prod": LABEL_GUID})
    assert mgr.apply_sensitivity_labels({"reports": ["r1"], "datasets": ["d1"]}, "prod") is False


def test_dry_run_response_is_success():
    api = _Api({"dry_run": True})
    mgr = _mgr(api, {"mode": "admin_api", "prod": LABEL_GUID})
    assert mgr.apply_sensitivity_labels({"reports": ["r1"]}, "prod") is True


def test_empty_artifact_set_is_a_noop():
    api = _Api()
    mgr = _mgr(api, {"mode": "admin_api", "prod": LABEL_GUID})
    assert mgr.apply_sensitivity_labels({"reports": []}, "prod") is True
    assert api.calls == []


def test_off_mode_short_circuits_everything():
    api = _Api()
    mgr = _mgr(api, {"mode": "off", "prod": "Confidential"})
    assert mgr.declare_workspace_labeling("ws-1", "prod") is True
    assert mgr.apply_sensitivity_labels({"reports": ["r1"]}, "prod") is True
    assert api.calls == []
    assert mgr.manual_steps == []


# -- the token cache must be per-audience -----------------------------------------


def test_token_cache_is_keyed_by_audience(monkeypatch):
    """One token does not serve both api.fabric.microsoft.com and api.powerbi.com."""
    issued: list[list[str]] = []

    class _App:
        def acquire_token_for_client(self, scopes):
            issued.append(list(scopes))
            return {"access_token": f"tok-{'|'.join(scopes)}", "expires_in": 3600}

    auth = object.__new__(orch.AuthProvider)
    auth.scopes = ["https://api.fabric.microsoft.com/.default"]
    auth.app = _App()
    auth._tokens = {}

    fabric = auth.get_token()
    pbi = auth.get_token(scopes=["https://analysis.windows.net/powerbi/api/.default"])

    assert fabric != pbi
    assert len(issued) == 2
    # Second read of each audience is served from cache.
    auth.get_token()
    auth.get_token(scopes=["https://analysis.windows.net/powerbi/api/.default"])
    assert len(issued) == 2
