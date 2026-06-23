"""Tests for the superversion pin-drift sensor (task I-2.4).

Pure cores are netz-frei and unit-tested directly (Meridian D-238 pattern); the
end-to-end run is smoke-tested against the real vendored PIN.json. Doctrine:
the sensor REPORTS drift and never bumps.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

import pytest

from scripts import check_superversion_pins as sensor

REPO = Path(__file__).resolve().parents[3]
VENDOR = REPO / "tooling" / "superversion" / "vendor" / "meridian"


# ---- pure cores ----------------------------------------------------------- #

def test_staleness_days_math():
    assert sensor.staleness_days("2026-06-01", dt.date(2026, 6, 23)) == 22
    assert sensor.staleness_days("2026-06-23", dt.date(2026, 6, 23)) == 0


def test_staleness_days_unparseable():
    assert sensor.staleness_days("", dt.date(2026, 6, 23)) is None
    assert sensor.staleness_days("not-a-date", dt.date(2026, 6, 23)) is None


def test_verify_integrity_detects_ok_missing_and_diverged(tmp_path):
    good = tmp_path / "a.txt"
    good.write_text("hello", encoding="utf-8")
    good_sha = hashlib.sha256(b"hello").hexdigest()
    pin = {"files": [
        {"path": "a.txt", "sha256": good_sha},                 # ok
        {"path": "b.txt", "sha256": "deadbeef"},               # missing
        {"path": "c.txt", "sha256": "0" * 64},                 # diverged
    ]}
    (tmp_path / "c.txt").write_text("changed", encoding="utf-8")
    out = {r["path"]: r["status"] for r in sensor.verify_integrity(pin, tmp_path)}
    assert out == {"a.txt": "ok", "b.txt": "missing", "c.txt": "diverged"}


def test_has_drift():
    assert sensor.has_drift([{"path": "x", "status": "ok", "detail": ""}]) is False
    assert sensor.has_drift([{"path": "x", "status": "diverged", "detail": ""}]) is True
    assert sensor.has_drift([{"path": "x", "status": "missing", "detail": ""}]) is True


def test_pin_provenance_flags_unknown_commit_and_staleness():
    pin = {"source": {"ref": "main", "commit": "UNKNOWN — archive", "synced_at": "2026-01-01"}}
    prov = sensor.pin_provenance(pin, dt.date(2026, 6, 23))
    assert prov["commit_pinned"] is False
    assert prov["stale"] is True  # > 60 days
    pin2 = {"source": {"ref": "main", "commit": "abc1234", "synced_at": "2026-06-23"}}
    prov2 = sensor.pin_provenance(pin2, dt.date(2026, 6, 23))
    assert prov2["commit_pinned"] is True and prov2["stale"] is False


def test_build_report_levels():
    clean = [{"path": "f", "status": "ok", "detail": "x"}]
    prov_ok = {"ref": "main", "commit_pinned": True, "synced_at": "2026-06-23",
               "staleness_days": 0, "stale": False}
    level, _ = sensor.build_report({}, clean, prov_ok, True, "n/a")
    assert level == "OK"

    prov_adv = {**prov_ok, "commit_pinned": False}
    level, _ = sensor.build_report({}, clean, prov_adv, True, "n/a")
    assert level == "ADVISORY"

    diverged = [{"path": "f", "status": "diverged", "detail": "x"}]
    level, _ = sensor.build_report({}, diverged, prov_ok, True, "n/a")
    assert level == "DRIFT"


# ---- end-to-end against the real vendored pin ----------------------------- #

def test_sensor_run_on_real_pin_advisory_exit0():
    """The vendored pin is intact (so no hard drift) but synced from an archive
    (commit UNKNOWN) → advisory, exit 0 even under --strict (no hard drift)."""
    if not sensor.PIN_PATH.exists():
        pytest.skip("vendored Meridian pin absent")
    assert sensor.main([]) == 0
    assert sensor.main(["--strict"]) == 0  # advisory-only, no hard drift


def test_sensor_json_output(tmp_path):
    if not sensor.PIN_PATH.exists():
        pytest.skip("vendored Meridian pin absent")
    out = tmp_path / "status.json"
    assert sensor.main(["--json", str(out)]) == 0
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["level"] in {"OK", "ADVISORY", "DRIFT"}
    assert all(r["status"] == "ok" for r in data["integrity"]), "vendored files must be intact"
