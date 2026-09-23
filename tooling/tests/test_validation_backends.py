"""Tests for the pluggable validation backends and capability tiers (ADR 0001)."""

from __future__ import annotations

import json
import types
from pathlib import Path

import pytest

from tooling.report_quality import backends as bk
from tooling.report_quality.backends import (
    ALLOW_EXTERNAL_ENV,
    MicrosoftReportAuthorBackend,
    NativeBackend,
    active_backends,
    active_tier,
    external_allowed,
    tier_report,
)


# ── external_allowed: the compliance gate ─────────────────────────────────────


@pytest.mark.parametrize("value", ["1", "true", "TRUE", "yes", "on", " On "])
def test_external_allowed_truthy(value: str) -> None:
    assert external_allowed({ALLOW_EXTERNAL_ENV: value}) is True


@pytest.mark.parametrize("value", ["", "0", "false", "no", "off", "nope"])
def test_external_allowed_falsey(value: str) -> None:
    assert external_allowed({ALLOW_EXTERNAL_ENV: value}) is False


def test_external_allowed_missing_key_is_false() -> None:
    assert external_allowed({}) is False


# ── Tier 0 floor is always available ──────────────────────────────────────────


def test_native_backend_always_available() -> None:
    native = NativeBackend()
    assert native.tier == 0
    assert native.is_available(allow_external=False) is True
    status = native.status(allow_external=False)
    assert status.available is True
    assert status.tier == 0


def test_active_tier_is_zero_in_compliance_mode() -> None:
    # Default (no opt-in): only the Tier 0 floor is active.
    assert active_tier(allow_external=False) == 0
    active = active_backends(allow_external=False)
    assert [b.name for b in active] == ["native"]


# ── Tier 1 external backend: off by default, on only when opted in + on PATH ───


def test_external_backend_inactive_without_optin(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(bk.shutil, "which", lambda _cli: "/usr/bin/powerbi-report-author")
    backend = MicrosoftReportAuthorBackend()
    # Even though the CLI is "on PATH", compliance mode keeps it inactive.
    assert backend.is_available(allow_external=False) is False
    status = backend.status(allow_external=False)
    assert status.available is False
    assert ALLOW_EXTERNAL_ENV in status.detail


def test_external_backend_inactive_when_not_on_path(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(bk.shutil, "which", lambda _cli: None)
    backend = MicrosoftReportAuthorBackend()
    assert backend.is_available(allow_external=True) is False
    assert "not found on PATH" in backend.status(allow_external=True).detail


def test_external_backend_active_when_optin_and_on_path(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(bk.shutil, "which", lambda _cli: "/usr/bin/powerbi-report-author")
    backend = MicrosoftReportAuthorBackend()
    assert backend.is_available(allow_external=True) is True
    assert backend.status(allow_external=True).available is True
    assert active_tier(allow_external=True) == 1


def test_tier_report_lists_every_backend() -> None:
    report = tier_report(allow_external=False)
    assert [s.name for s in report] == ["native", "powerbi-report-author"]
    assert [s.tier for s in report] == [0, 1]


# ── validate(): graceful skip and exit-code mapping ───────────────────────────


def test_validate_skips_without_optin(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv(ALLOW_EXTERNAL_ENV, raising=False)

    def _explode(*_args: object, **_kwargs: object) -> None:  # pragma: no cover - must not run
        raise AssertionError("subprocess must not be invoked when not opted in")

    monkeypatch.setattr(bk.subprocess, "run", _explode)
    assert MicrosoftReportAuthorBackend().validate(tmp_path) == []


def _fake_proc(returncode: int, stdout: str = "", stderr: str = "") -> types.SimpleNamespace:
    return types.SimpleNamespace(returncode=returncode, stdout=stdout, stderr=stderr)


_PASSED_ENVELOPE = json.dumps({"data": {"result": "passed", "errorCount": 0, "warningCount": 0, "diagnostics": {}}})


def _diag_envelope(severity: str = "error") -> str:
    abs_file = "/abs/X.Report/definition/pages/P/visuals/V/visual.json"
    return json.dumps(
        {
            "data": {
                "result": "failed",
                "diagnostics": {
                    "PBIR_ROLE_UNKNOWN": {
                        "severity": severity,
                        "items": [
                            {
                                "message": f'Unknown role "Data" for visualType "textbox": {abs_file}',
                                "file": abs_file,
                                "path": "Data",
                            }
                        ],
                    }
                },
            }
        }
    )


def _wire_external(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, proc: types.SimpleNamespace) -> None:
    monkeypatch.setenv(ALLOW_EXTERNAL_ENV, "1")
    monkeypatch.setattr(bk.shutil, "which", lambda _cli: "/usr/bin/powerbi-report-author")
    monkeypatch.setattr("tooling.report_quality.pbir.iter_report_dirs", lambda _root: [tmp_path / "X.Report"])
    monkeypatch.setattr(bk.subprocess, "run", lambda *a, **k: proc)


def test_validate_parses_clean_report_to_no_violations(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _wire_external(monkeypatch, tmp_path, _fake_proc(0, stdout=_PASSED_ENVELOPE))
    assert MicrosoftReportAuthorBackend().validate(tmp_path) == []


def test_validate_parses_diagnostics_to_violations(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _wire_external(monkeypatch, tmp_path, _fake_proc(1, stdout=_diag_envelope("error")))
    violations = MicrosoftReportAuthorBackend().validate(tmp_path)
    assert len(violations) == 1
    v = violations[0]
    assert v.check == "powerbi-report-author.PBIR_ROLE_UNKNOWN"
    assert v.severity == "critical"  # official 'error' -> critical (opt-in tier)
    assert "Unknown role" in v.message
    assert "/abs/X.Report" not in v.message  # trailing absolute path stripped
    assert v.pointer.endswith("#Data")


def test_validate_maps_warning_severity(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _wire_external(monkeypatch, tmp_path, _fake_proc(0, stdout=_diag_envelope("warning")))
    violations = MicrosoftReportAuthorBackend().validate(tmp_path)
    assert [v.severity for v in violations] == ["warning"]


def test_validate_unparseable_output_falls_back(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _wire_external(monkeypatch, tmp_path, _fake_proc(1, stdout="not json", stderr="boom\n"))
    violations = MicrosoftReportAuthorBackend().validate(tmp_path)
    assert len(violations) == 1
    assert violations[0].severity == "warning"
    assert violations[0].check == "backend.powerbi-report-author"


def test_validate_handles_missing_binary_gracefully(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    report_dir = tmp_path / "X.Report"
    monkeypatch.setenv(ALLOW_EXTERNAL_ENV, "1")
    monkeypatch.setattr(bk.shutil, "which", lambda _cli: "/usr/bin/powerbi-report-author")
    monkeypatch.setattr("tooling.report_quality.pbir.iter_report_dirs", lambda _root: [report_dir])

    def _raise(*_a: object, **_k: object) -> None:
        raise OSError("boom")

    monkeypatch.setattr(bk.subprocess, "run", _raise)
    violations = MicrosoftReportAuthorBackend().validate(tmp_path)
    assert len(violations) == 1
    assert violations[0].severity == "info"
    assert "could not run" in violations[0].message


# ── authoring-metadata snapshot loader ────────────────────────────────────────


def test_loader_reads_custom_snapshot(tmp_path: Path) -> None:
    from tooling.report_quality import authoring_metadata as am

    snap = tmp_path / "snap.json"
    snap.write_text(
        json.dumps(
            {
                "_meta": {},
                "visualTypes": {
                    "lineChart": {"requiredRoles": ["Category", "Y"], "roles": {"Category": "Grouping", "Y": "Measure"}}
                },
            }
        )
    , encoding="utf-8")
    assert am.is_available(path=snap) is True
    assert am.required_roles("lineChart", path=snap) == ["Category", "Y"]
    assert am.is_known_role("lineChart", "Y", path=snap) is True
    assert am.is_known_role("lineChart", "Data", path=snap) is False
    assert am.known_visual_types(path=snap) == ["lineChart"]
    assert am.required_roles("unknownType", path=snap) == []


def test_loader_missing_snapshot_is_graceful(tmp_path: Path) -> None:
    from tooling.report_quality import authoring_metadata as am

    missing = tmp_path / "does_not_exist.json"
    assert am.is_available(path=missing) is False
    assert am.required_roles("lineChart", path=missing) == []
    assert am.roles("lineChart", path=missing) == {}


def test_vendored_snapshot_matches_known_roles() -> None:
    """The committed snapshot carries authoritative roles for the types we use."""
    from tooling.report_quality import authoring_metadata as am

    assert am.is_available() is True  # default vendored path
    assert am.required_roles("lineChart") == ["Category", "Y"]
    assert am.required_roles("cardVisual") == ["Data"]
    assert am.is_known_role("tableEx", "Values") is True
    assert am.is_known_role("pivotTable", "Rows") is True
