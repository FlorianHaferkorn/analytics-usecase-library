"""Regression test for the PBIR CustomTheme naming convention, verified against the
official pbir-cli validator (`powerbi-report-author validate`) over the dist and
mirrored in the Meridian dist: a RegisteredResources/CustomTheme item must carry the
theme's `.json` filename in BOTH `name` and `path`, matching
`themeCollection.customTheme.name` and the theme file's internal `name` — all four
identical. (This is unlike the SharedResources/BaseTheme item, whose `name` is the bare
id.) A bare-stem CustomTheme name is flagged PBIR_THEME_NAME_MISSING_JSON_EXT; a name
that mismatches the referenced file is flagged PBIR_THEME_FILE_NAME_MISMATCH.
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from products.fabric.powerbi.tooling.apply_report_theme import (
    DEFAULT_BASE_THEME,
    _ensure_resource_packages,
    sync_base_theme,
)
from tooling.report_quality import base_theme as bt


def test_registered_custom_theme_item_name_matches_json_filename():
    data: dict = {}
    _ensure_resource_packages(data, base_theme=DEFAULT_BASE_THEME, custom_theme_filename="Aurora_Theme.json")

    shared = next(p for p in data["resourcePackages"] if p["type"] == "SharedResources")
    registered = next(p for p in data["resourcePackages"] if p["type"] == "RegisteredResources")
    base_item = shared["items"][0]
    custom_item = next(i for i in registered["items"] if i["type"] == "CustomTheme")

    # SharedResources/BaseTheme item: name is the bare id, path has the extension.
    assert base_item["name"] == DEFAULT_BASE_THEME
    assert base_item["path"] == f"BaseThemes/{DEFAULT_BASE_THEME}.json"

    # RegisteredResources/CustomTheme item: name == path == the .json filename.
    assert custom_item["name"] == "Aurora_Theme.json"
    assert custom_item["path"] == "Aurora_Theme.json"


def test_reapplying_theme_replaces_the_existing_entry_not_duplicates_it():
    data: dict = {}
    _ensure_resource_packages(data, base_theme=DEFAULT_BASE_THEME, custom_theme_filename="Aurora_Theme.json")
    _ensure_resource_packages(data, base_theme=DEFAULT_BASE_THEME, custom_theme_filename="Aurora_Theme.json")

    registered = next(p for p in data["resourcePackages"] if p["type"] == "RegisteredResources")
    custom_items = [i for i in registered["items"] if i["type"] == "CustomTheme"]
    assert len(custom_items) == 1


def test_reapplying_over_a_pre_fix_buggy_entry_replaces_it_by_path_not_name():
    """Migration case: a report.json written by the OLD buggy code has `name` == the
    bare stem (no .json). Re-running must replace that stale entry — identified by its
    stable `path` — rather than leaving it behind alongside a second, now-correct entry."""
    data = {
        "resourcePackages": [
            {
                "name": "RegisteredResources",
                "type": "RegisteredResources",
                "items": [
                    {"name": "Aurora_Theme", "path": "Aurora_Theme.json", "type": "CustomTheme"},
                ],
            }
        ]
    }
    _ensure_resource_packages(data, base_theme=DEFAULT_BASE_THEME, custom_theme_filename="Aurora_Theme.json")

    registered = next(p for p in data["resourcePackages"] if p["type"] == "RegisteredResources")
    custom_items = [i for i in registered["items"] if i["type"] == "CustomTheme"]
    assert len(custom_items) == 1
    assert custom_items[0]["name"] == "Aurora_Theme.json"


def test_default_base_theme_is_the_pinned_cli_theme():
    assert DEFAULT_BASE_THEME == bt.BASE_THEME_NAME


def test_new_base_theme_replaces_the_previous_base_item():
    data = {"resourcePackages": [{"name": "SharedResources", "type": "SharedResources",
                                  "items": [{"name": "CY25SU10", "path": "BaseThemes/CY25SU10.json",
                                             "type": "BaseTheme"}]}]}
    _ensure_resource_packages(data, base_theme=DEFAULT_BASE_THEME, custom_theme_filename="A.json")
    shared = next(p for p in data["resourcePackages"] if p["type"] == "SharedResources")
    assert [i["name"] for i in shared["items"] if i["type"] == "BaseTheme"] == [DEFAULT_BASE_THEME]


def _old_report(root: Path) -> Path:
    """A report as dist carried it before D-587 (CY25SU10 + a custom theme)."""
    report = root / "X.Report"
    (report / "definition").mkdir(parents=True)
    base_dir = report / "StaticResources" / "SharedResources" / "BaseThemes"
    base_dir.mkdir(parents=True)
    (base_dir / "CY25SU10.json").write_text('{"name": "CY25SU10"}\n', encoding="utf-8")
    (base_dir / "Unrelated.json").write_text("{}\n", encoding="utf-8")
    old = {"visual": "2.1.0", "report": "3.0.0", "page": "2.3.0"}
    data = {
        "themeCollection": {
            "baseTheme": {"name": "CY25SU10", "reportVersionAtImport": old, "type": "SharedResources"},
            "customTheme": {"name": "A.json", "reportVersionAtImport": old, "type": "RegisteredResources"},
        },
        "resourcePackages": [
            {"name": "SharedResources", "type": "SharedResources",
             "items": [{"name": "CY25SU10", "path": "BaseThemes/CY25SU10.json", "type": "BaseTheme"}]},
            {"name": "RegisteredResources", "type": "RegisteredResources",
             "items": [{"name": "A.json", "path": "A.json", "type": "CustomTheme"}]},
        ],
    }
    (report / "definition" / "report.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return report


def test_sync_base_theme_moves_report_onto_pinned_theme_and_is_idempotent(tmp_path):
    report = _old_report(tmp_path)
    assert sync_base_theme(report, check=True), "check must see the drift"
    assert (report / "StaticResources/SharedResources/BaseThemes/CY25SU10.json").exists(), "check wrote"

    assert sync_base_theme(report)
    data = json.loads((report / "definition" / "report.json").read_text(encoding="utf-8"))
    assert data["themeCollection"]["baseTheme"] == bt.base_theme_entry()
    assert data["themeCollection"]["customTheme"]["name"] == "A.json"  # untouched
    shared = next(p for p in data["resourcePackages"] if p["type"] == "SharedResources")
    assert shared["items"] == [bt.shared_resources_item()]
    base_dir = report / "StaticResources" / "SharedResources" / "BaseThemes"
    assert (base_dir / f"{bt.BASE_THEME_NAME}.json").read_bytes() == bt.vendored_bytes()
    assert not (base_dir / "CY25SU10.json").exists(), "old referenced base theme must go"
    assert (base_dir / "Unrelated.json").exists(), "only formerly referenced files are removed"

    assert sync_base_theme(report) == []
    assert sync_base_theme(report, check=True) == []


_TOOL_DIR = Path(__file__).resolve().parents[1]
_PY_SCRIPT = _TOOL_DIR / "apply_report_theme.py"
_PS1_SCRIPT = _TOOL_DIR / "apply_report_theme.ps1"
_PWSH = os.environ.get("ALUCA_PWSH") or shutil.which("pwsh")


def _run(cmd, cwd):
    # PYTHONPATH cleared: the script must find the repo root itself, not inherit it from pytest.
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    return subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, encoding="utf-8", timeout=120)


def test_runs_as_standalone_script_from_foreign_cwd(tmp_path):
    """Regression (30.09.2026): as a script it died with ModuleNotFoundError: products."""
    proc = _run([sys.executable, str(_PY_SCRIPT), "--help"], cwd=tmp_path)
    assert proc.returncode == 0, proc.stderr
    assert "--sync-base-theme" in proc.stdout


def test_script_sync_base_theme_check_reports_drift_then_clean(tmp_path):
    report = _old_report(tmp_path)
    cmd = [sys.executable, str(_PY_SCRIPT), str(report), "--sync-base-theme"]
    assert _run(cmd + ["--check"], cwd=tmp_path).returncode == 1
    assert _run(cmd, cwd=tmp_path).returncode == 0
    assert _run(cmd + ["--check"], cwd=tmp_path).returncode == 0


@pytest.mark.skipif(not _PWSH, reason="pwsh not installed (set ALUCA_PWSH or put pwsh on PATH)")
def test_ps1_wrapper_sync_base_theme_from_foreign_cwd(tmp_path):
    report = _old_report(tmp_path)
    base = [_PWSH, "-NoProfile", "-NonInteractive", "-File", str(_PS1_SCRIPT), "-Report", str(report),
            "-SyncBaseTheme"]
    first = _run(base + ["-Check"], cwd=tmp_path)
    assert first.returncode == 1, first.stdout + first.stderr
    synced = _run(base, cwd=tmp_path)
    assert synced.returncode == 0, synced.stdout + synced.stderr
    again = _run(base + ["-Check"], cwd=tmp_path)
    assert again.returncode == 0, again.stdout + again.stderr
