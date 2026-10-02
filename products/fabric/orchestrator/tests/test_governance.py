"""GovernanceManager — pins the *official* contract, not our earlier guesses.

Regression cover for two invented surfaces that used to live here:
  * ``POST workspaces/{ws}/governanceLabels`` — does not exist. Sensitivity labels are
    written by the Fabric admin API ``POST /v1/admin/items/bulkSetLabels`` (Learn
    ``rest/api/fabric/admin/labels/bulk-set-labels``, read 01.10.2026), keyed by label
    **GUID**, with ``{id, type}`` per item, user identities only (no service principal).
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

LABEL_GUID = "fe472f5e-636e-4c10-a1c6-7e9edc0b542d"
USER_GUID = "796ce6ad-9163-4c16-9559-c68192a251de"
R1 = "fe472f5e-636e-4c10-a1c6-7e9edc0b542c"
SM1 = "fe472f5e-636e-4c10-a1c6-7e9edc0b542e"
LH1 = "476fcafe-b514-495d-b13f-ca9a4f0b1d8f"


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


class _UserAuth:
    IDENTITY_KIND = "user"


class _Api:
    """Records calls instead of issuing them. Defaults to a *user* identity."""

    def __init__(self, response=None, auth=None):
        self.calls: list[dict] = []
        self._response = response
        self.auth = auth if auth is not None else _UserAuth()

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


def test_purview_mode_never_calls_the_api():
    api = _Api()
    mgr = _mgr(api, {"mode": "purview_policy", "prod": "Confidential"})
    assert mgr.apply_sensitivity_labels({"Report": [R1]}, "prod") is True
    assert api.calls == []


def test_unconfigured_environment_is_a_noop():
    api = _Api()
    mgr = _mgr(api, {"mode": "admin_api"})
    assert mgr.apply_sensitivity_labels({"Report": [R1]}, "staging") is True
    assert api.calls == []


def test_unknown_mode_is_rejected():
    api = _Api()
    mgr = _mgr(api, {"mode": "yolo", "dev": "General"})
    with pytest.raises(orch.ConfigurationError):
        mgr.declare_workspace_labeling("ws-1", "dev")


# -- admin_api mode: exact documented request (Fabric bulkSetLabels) ----------------


def _ok(*pairs):
    return {"itemsChangeLabelStatus": [
        {"id": i, "type": t, "status": st} for i, t, st in pairs]}


def test_bulksetlabels_request_matches_official_contract():
    api = _Api(_ok((R1, "Report", "Succeeded"), (LH1, "Lakehouse", "Succeeded")))
    mgr = _mgr(api, {"mode": "admin_api", "prod": LABEL_GUID})

    assert mgr.apply_sensitivity_labels({"Report": [R1], "Lakehouse": [LH1]}, "prod") is True

    call = api.calls[0]
    assert call["endpoint"] == "admin/items/bulkSetLabels"
    # Fabric host and Fabric audience — the client defaults, no Power BI override.
    assert call["base"] is None
    assert call["scopes"] is None
    # 'labelId' (GUID); flat 'items' list of {id, type}, never Power BI 'artifacts' buckets.
    assert call["json"] == {
        "items": [{"id": R1, "type": "Report"}, {"id": LH1, "type": "Lakehouse"}],
        "labelId": LABEL_GUID,
        "assignmentMethod": "Standard",
    }


def test_source_no_longer_calls_the_power_bi_setlabels_api():
    src = _ORCH.read_text(encoding="utf-8")
    assert '"admin/informationprotection/setLabels"' not in src
    assert "api.powerbi.com/v1.0/myorg" not in src


def test_non_power_bi_item_types_are_labelable():
    """Lakehouse/Notebook/Warehouse were refused under the old API; Fabric covers them."""
    api = _Api(_ok((LH1, "Notebook", "Succeeded")))
    mgr = _mgr(api, {"mode": "admin_api", "prod": LABEL_GUID})
    assert mgr.apply_sensitivity_labels({"Notebook": [LH1]}, "prod") is True


def test_label_name_rejected_in_admin_api_mode():
    """bulkSetLabels takes a GUID; a display name would be NotFound at runtime."""
    api = _Api()
    mgr = _mgr(api, {"mode": "admin_api", "prod": "Confidential"})
    with pytest.raises(orch.ConfigurationError, match="GUID"):
        mgr.apply_sensitivity_labels({"Report": [R1]}, "prod")
    assert api.calls == []


def test_unknown_item_type_rejected():
    """Old Power BI bucket names and undocumented types fail closed."""
    api = _Api()
    mgr = _mgr(api, {"mode": "admin_api", "prod": LABEL_GUID})
    with pytest.raises(orch.ConfigurationError, match="reports"):
        mgr.apply_sensitivity_labels({"reports": [R1]}, "prod")
    assert api.calls == []


def test_non_guid_item_id_rejected():
    api = _Api()
    mgr = _mgr(api, {"mode": "admin_api", "prod": LABEL_GUID})
    with pytest.raises(orch.ConfigurationError, match="UUID"):
        mgr.apply_sensitivity_labels({"Report": ["r1"]}, "prod")
    assert api.calls == []


def test_batch_cap_enforced_before_the_call():
    api = _Api()
    mgr = _mgr(api, {"mode": "admin_api", "prod": LABEL_GUID})
    ids = [f"00000000-0000-0000-0000-{i:012d}" for i in range(2001)]
    with pytest.raises(orch.ConfigurationError, match="2000"):
        mgr.apply_sensitivity_labels({"Report": ids}, "prod")
    assert api.calls == []


def test_batch_of_exactly_2000_is_allowed():
    ids = [f"00000000-0000-0000-0000-{i:012d}" for i in range(2000)]
    api = _Api(_ok(*[(i, "Report", "Succeeded") for i in ids]))
    mgr = _mgr(api, {"mode": "admin_api", "prod": LABEL_GUID})
    assert mgr.apply_sensitivity_labels({"Report": ids}, "prod") is True
    assert len(api.calls[0]["json"]["items"]) == 2000


def test_service_principal_identity_fails_closed_with_manual_step():
    """Learn: Service principal and Managed identities — No. No doomed call is issued."""
    api = _Api(auth=object.__new__(orch.AuthProvider))
    mgr = _mgr(api, {"mode": "admin_api", "prod": LABEL_GUID})
    assert mgr.apply_sensitivity_labels({"Report": [R1]}, "prod") is False
    assert api.calls == []
    assert any("service principal" in s and "bulkSetLabels" in s for s in mgr.manual_steps)


def _manual_body(step: str) -> dict:
    """The JSON body embedded in the manual step: from the first '{' line to the end of it."""
    import json
    start = step.index("\n{")
    depth, end = 0, None
    for pos in range(start + 1, len(step)):
        if step[pos] == "{":
            depth += 1
        elif step[pos] == "}":
            depth -= 1
            if depth == 0:
                end = pos + 1
                break
    return json.loads(step[start + 1:end])


def test_manual_step_hands_the_admin_everything_for_the_call():
    """Owner decision 01.10.2026: no user sign-in; the SPN path ends in a manual step that a
    Fabric admin can execute as is (Learn bulk-set-labels, read 01.10.2026)."""
    api = _Api(auth=object.__new__(orch.AuthProvider))
    mgr = _mgr(api, {"mode": "admin_api", "prod": LABEL_GUID})
    assert mgr.apply_sensitivity_labels({"Report": [R1], "SemanticModel": [SM1]}, "prod") is False
    (step,) = [s for s in mgr.manual_steps if "bulkSetLabels" in s]
    assert "POST https://api.fabric.microsoft.com/v1/admin/items/bulkSetLabels" in step
    assert "Fabric Administrator" in step and "Tenant.ReadWrite.All" in step
    assert "25 requests per hour" in step and "2000 items" in step
    assert "'Succeeded'" in step and "itemsChangeLabelStatus" in step
    body = _manual_body(step)
    assert body["labelId"] == LABEL_GUID
    assert body["items"] == [{"id": R1, "type": "Report"}, {"id": SM1, "type": "SemanticModel"}]
    assert "delegatedPrincipal" not in body
    assert '"delegatedPrincipal"' in step            # named as the optional field
    for secret_word in ("Bearer", "access_token", "client_secret", "Authorization"):
        assert secret_word not in step


def test_manual_step_body_carries_delegated_principal_when_given():
    api = _Api(auth=object.__new__(orch.AuthProvider))
    mgr = _mgr(api, {"mode": "admin_api", "prod": LABEL_GUID})
    mgr.apply_sensitivity_labels({"Report": [R1]}, "prod", delegated_user_id=USER_GUID)
    (step,) = [s for s in mgr.manual_steps if "bulkSetLabels" in s]
    assert _manual_body(step)["delegatedPrincipal"] == {"id": USER_GUID, "type": "User"}


def test_identity_without_declaration_counts_as_service_principal():
    api = _Api(auth=object())
    mgr = _mgr(api, {"mode": "admin_api", "prod": LABEL_GUID})
    assert mgr.apply_sensitivity_labels({"Report": [R1]}, "prod") is False
    assert api.calls == []


def test_delegated_principal_added_only_when_given():
    api = _Api(_ok((R1, "Report", "Succeeded")))
    mgr = _mgr(api, {"mode": "admin_api", "prod": LABEL_GUID})
    mgr.apply_sensitivity_labels({"Report": [R1]}, "prod")
    assert "delegatedPrincipal" not in api.calls[0]["json"]
    mgr.apply_sensitivity_labels({"Report": [R1]}, "prod", delegated_user_id=USER_GUID)
    assert api.calls[1]["json"]["delegatedPrincipal"] == {"id": USER_GUID, "type": "User"}


def test_delegated_principal_must_be_a_guid():
    api = _Api()
    mgr = _mgr(api, {"mode": "admin_api", "prod": LABEL_GUID})
    with pytest.raises(orch.ConfigurationError, match="object ID"):
        mgr.apply_sensitivity_labels({"Report": [R1]}, "prod", delegated_user_id="a@b.c")
    assert api.calls == []


def test_http_200_with_partial_success_is_not_success():
    """The API returns 200 even when individual items failed — read the statuses."""
    api = _Api(_ok((R1, "Report", "Succeeded"), (SM1, "SemanticModel", "InsufficientUsageRights")))
    mgr = _mgr(api, {"mode": "admin_api", "prod": LABEL_GUID})
    assert mgr.apply_sensitivity_labels({"Report": [R1], "SemanticModel": [SM1]}, "prod") is False


@pytest.mark.parametrize("status", ["Failed", "FailedToGetUsageRights", "NotFound"])
def test_every_documented_failure_status_is_failure(status):
    api = _Api(_ok((R1, "Report", status)))
    mgr = _mgr(api, {"mode": "admin_api", "prod": LABEL_GUID})
    assert mgr.apply_sensitivity_labels({"Report": [R1]}, "prod") is False


def test_item_missing_from_response_is_not_success():
    api = _Api(_ok((R1, "Report", "Succeeded")))
    mgr = _mgr(api, {"mode": "admin_api", "prod": LABEL_GUID})
    assert mgr.apply_sensitivity_labels({"Report": [R1], "SemanticModel": [SM1]}, "prod") is False


def test_response_without_status_list_is_not_success():
    api = _Api({})
    mgr = _mgr(api, {"mode": "admin_api", "prod": LABEL_GUID})
    assert mgr.apply_sensitivity_labels({"Report": [R1]}, "prod") is False


def test_old_power_bi_response_shape_is_not_success():
    api = _Api({"reports": [{"id": R1, "status": "Succeeded"}]})
    mgr = _mgr(api, {"mode": "admin_api", "prod": LABEL_GUID})
    assert mgr.apply_sensitivity_labels({"Report": [R1]}, "prod") is False


def test_dry_run_response_is_success():
    api = _Api({"dry_run": True})
    mgr = _mgr(api, {"mode": "admin_api", "prod": LABEL_GUID})
    assert mgr.apply_sensitivity_labels({"Report": [R1]}, "prod") is True


def test_empty_item_set_is_a_noop():
    api = _Api()
    mgr = _mgr(api, {"mode": "admin_api", "prod": LABEL_GUID})
    assert mgr.apply_sensitivity_labels({"Report": []}, "prod") is True
    assert api.calls == []


def test_off_mode_short_circuits_everything():
    api = _Api()
    mgr = _mgr(api, {"mode": "off", "prod": "Confidential"})
    assert mgr.declare_workspace_labeling("ws-1", "prod") is True
    assert mgr.apply_sensitivity_labels({"Report": [R1]}, "prod") is True
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
