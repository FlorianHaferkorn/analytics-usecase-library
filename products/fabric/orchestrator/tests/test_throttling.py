"""HTTP 429 handling of the orchestrator, split by Fabric `errorCode` (I-21 W2.8).

Source: Microsoft Learn `rest/api/fabric/articles/throttling` (read 30.09.2026):
  * `RequestBlocked`        → wait exactly `Retry-After`.
  * `CapacityLimitExceeded` → exponential backoff; an immediate retry is pointless.

Regression cover: `_calculate_retry_delay` tested `if response and ...` — a
`requests.Response` is falsy for every 4xx/5xx, so `Retry-After` was never honored on the
429s that carry it; the client fell back to 1 s/2 s/4 s.

Runs without `msal` (CI has none): a stand-in module is inserted only when the real one
is missing, because only `AuthProvider` touches it and these tests never do.
"""
from __future__ import annotations

import importlib.util
import json
import sys
import types
from pathlib import Path

import pytest

pytest.importorskip("typer", reason="orchestrator deps (see products/fabric/orchestrator/requirements.txt)")
pytest.importorskip("rich", reason="orchestrator deps")
pytest.importorskip("requests", reason="orchestrator deps")

_ORCH = Path(__file__).resolve().parents[1] / "orchestrator.py"


@pytest.fixture(scope="module")
def orch():
    stubbed = False
    if importlib.util.find_spec("msal") is None:
        stub = types.ModuleType("msal")
        stub.ConfidentialClientApplication = object
        sys.modules["msal"] = stub
        stubbed = True
    try:
        spec = importlib.util.spec_from_file_location("_orchestrator_throttling", _ORCH)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        yield mod
    finally:
        if stubbed:
            sys.modules.pop("msal", None)


def _body(code: str) -> str:
    return json.dumps({"errorCode": code, "message": "x"})


# -- pure decision -----------------------------------------------------------------


def test_request_blocked_waits_exactly_retry_after(orch):
    p = orch.RetryPolicy()
    delay, reason = orch.retry_delay(p, 0, 429, {"Retry-After": "55"}, _body("RequestBlocked"))
    assert (delay, reason) == (55.0, "request_blocked")


def test_request_blocked_retry_after_as_http_date(orch):
    from datetime import datetime, timezone
    now = datetime(2026, 2, 18, 22, 44, 9, tzinfo=timezone.utc)
    assert orch.parse_retry_after({"Retry-After": "Wed, 18 Feb 2026 22:45:04 GMT"}, now=now) == 55.0


def test_retry_after_beyond_limit_gives_up(orch):
    p = orch.RetryPolicy(max_retry_after=60)
    delay, reason = orch.retry_delay(p, 0, 429, {"Retry-After": "600"}, _body("RequestBlocked"))
    assert delay is None and reason == "retry_after_exceeds_limit"


def test_capacity_limit_backs_off_exponentially_with_jitter_and_cap(orch):
    p = orch.RetryPolicy(capacity_initial_delay=30, capacity_max_delay=100, backoff_multiplier=2)
    body = _body("CapacityLimitExceeded")
    lo = [orch.retry_delay(p, a, 429, {}, body, rand=lambda: 0.0)[0] for a in range(4)]
    hi = [orch.retry_delay(p, a, 429, {}, body, rand=lambda: 1.0)[0] for a in range(4)]
    # step = min(100, 30 * 2**a) = 30, 60, 100, 100; delay in [step/2, step]
    assert lo == [15.0, 30.0, 50.0, 50.0]
    assert hi == [30.0, 60.0, 100.0, 100.0]
    assert orch.retry_delay(p, 0, 429, {}, body)[1] == "capacity_limit_exceeded"


def test_capacity_limit_never_retries_immediately(orch):
    p = orch.RetryPolicy()
    delay, _ = orch.retry_delay(p, 0, 429, {"Retry-After": "0"}, _body("CapacityLimitExceeded"),
                                rand=lambda: 0.0)
    assert delay >= p.capacity_initial_delay / 2 > 0


def test_capacity_limit_respects_a_longer_retry_after(orch):
    p = orch.RetryPolicy()
    delay, _ = orch.retry_delay(p, 0, 429, {"Retry-After": "120"}, _body("CapacityLimitExceeded"))
    assert delay == 120.0


def test_other_transient_errors_keep_plain_backoff(orch):
    p = orch.RetryPolicy(initial_delay=1, backoff_multiplier=2)
    assert orch.retry_delay(p, 2, 503, {}, "")[0] == 4.0
    assert orch.retry_delay(p, 0, None)[0] == 1.0


def test_policy_reads_config_with_defaults(orch):
    p = orch.RetryPolicy.from_config({"max_retries": 5, "capacity_max_delay": 90})
    assert (p.max_retries, p.capacity_max_delay, p.capacity_initial_delay) == (5, 90.0, 30.0)


# -- wired through FabricApiClient._make_request -------------------------------------


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


class _Auth:
    def get_token(self, force_refresh=False, scopes=None):
        return "tok"


class _Resp:
    def __init__(self, status, body=None, headers=None):
        self.status_code, self.headers, self.reason = status, headers or {}, "x"
        self.content = json.dumps(body).encode() if body is not None else b""
        self.text = self.content.decode()
        self._body = body

    def json(self):
        return self._body

    def __bool__(self):  # mirrors requests.Response: falsy for >= 400
        return self.status_code < 400


def _client(orch, monkeypatch, responses, retry=None):
    queue = list(responses)
    sleeps: list[float] = []
    monkeypatch.setattr(orch.requests, "request", lambda **kw: queue.pop(0))
    monkeypatch.setattr(orch.time, "sleep", sleeps.append)
    api = orch.FabricApiClient(_Config({"retry": retry or {}}), _Auth())
    return api, sleeps


def test_make_request_honors_retry_after_on_request_blocked(orch, monkeypatch):
    api, sleeps = _client(orch, monkeypatch, [
        _Resp(429, {"errorCode": "RequestBlocked", "message": "m"}, {"Retry-After": "55"}),
        _Resp(200, {"ok": True}),
    ])
    assert api.get("workspaces") == {"ok": True}
    assert sleeps == [55.0]


def test_make_request_backs_off_on_capacity_limit(orch, monkeypatch):
    monkeypatch.setattr(orch.random, "random", lambda: 0.5)
    api, sleeps = _client(orch, monkeypatch, [
        _Resp(429, {"errorCode": "CapacityLimitExceeded", "message": "m"}),
        _Resp(429, {"errorCode": "CapacityLimitExceeded", "message": "m"}),
        _Resp(200, {"ok": True}),
    ], retry={"capacity_initial_delay": 10, "capacity_max_delay": 300})
    assert api.get("workspaces") == {"ok": True}
    assert sleeps == [7.5, 15.0]  # step 10, 20 → step/2 + 0.5*step/2


def test_make_request_capacity_exhausted_names_the_cause(orch, monkeypatch):
    monkeypatch.setattr(orch.random, "random", lambda: 0.0)
    body = {"errorCode": "CapacityLimitExceeded", "message": "m"}
    api, sleeps = _client(orch, monkeypatch, [_Resp(429, body)] * 4, retry={"max_retries": 3})
    with pytest.raises(orch.FabricApiError, match="CapacityLimitExceeded") as ei:
        api.get("workspaces")
    assert ei.value.status_code == 429
    assert len(sleeps) == 3 and all(s > 0 for s in sleeps)


def test_make_request_does_not_sleep_through_an_excessive_retry_after(orch, monkeypatch):
    api, sleeps = _client(orch, monkeypatch, [
        _Resp(429, {"errorCode": "RequestBlocked", "message": "m"}, {"Retry-After": "3600"}),
    ], retry={"max_retry_after": 300})
    with pytest.raises(orch.FabricApiError, match="RequestBlocked"):
        api.get("workspaces")
    assert sleeps == []
