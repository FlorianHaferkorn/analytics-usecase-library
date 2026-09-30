"""Base theme = what the pinned official CLI scaffolds (Meridian D-587, 30.09.2026).

Two layers:

* **Offline** (always runs): the vendored copy exists and names itself correctly, the
  pin constant equals the CI install pin, no generator source carries its own base
  theme literal, and every dist report references and ships exactly the vendored theme.
* **Against the package** (``braucht_pbir_cli``): ``scaffold --offline`` of the pinned
  CLI must produce the same name, ``reportVersionAtImport`` and bytes as the vendored
  copy. Without the CLI this skips (locally no finding); with
  ``ALUCA_PBIR_CLI_PFLICHT=1`` a missing CLI is red (root ``conftest.py``). A CLI in a
  different version than the pin is not a comparison against the pin: it skips with that
  reason locally and is red in Pflicht mode -- "nicht gelaufen" is never "gruen".

Refresh after a pin bump: ``python -m tooling.report_quality.refresh_authoring_metadata
--base-theme-only``, adjust the constants in ``tooling/report_quality/base_theme.py``,
then ``python -m products.fabric.powerbi.tooling.apply_report_theme --sync-base-theme
--batch "products/fabric/powerbi/dist/*.Report"`` (``--check`` only reports drift).
"""
from __future__ import annotations

import json
import os
import re
import shutil
from pathlib import Path

import pytest

from tooling.report_quality import base_theme as bt

REPO = Path(__file__).resolve().parents[2]
_DIST = REPO / "products/fabric/powerbi/dist"
_WORKFLOW = REPO / ".github/workflows/superversion.yml"
_THEME_LITERAL = re.compile(r"CY\d{2}SU\d{2}")

#: Generator/emitter code that writes report.json themeCollection or BaseThemes.
_GENERATOR_SOURCES = (
    "products/fabric/powerbi/tooling/page_scaffold_generator/pbip_writer.py",
    "products/fabric/powerbi/tooling/page_scaffold_generator/generate_full_report.py",
    "products/fabric/powerbi/tooling/adapters/pbip.py",
    "products/fabric/powerbi/tooling/apply_report_theme.py",
    "products/fabric/powerbi/tooling/apply_report_theme.ps1",
    "tooling/superversion/targets/pbir.py",
    "tooling/report_quality/refresh_authoring_metadata.py",
)


def test_vendored_base_theme_names_itself() -> None:
    data = json.loads(bt.vendored_path().read_text(encoding="utf-8"))
    assert data["name"] == bt.BASE_THEME_NAME
    assert data.get("dataColors"), "vendored base theme has no dataColors -- not a theme file"


def test_pin_constant_matches_ci_install_pin() -> None:
    text = _WORKFLOW.read_text(encoding="utf-8")
    pins = set(re.findall(re.escape(bt.CLI_PACKAGE) + r"@([0-9][0-9.]*)", text))
    assert pins == {bt.CLI_VERSION_PIN}, (
        f"{_WORKFLOW.name} installs {pins}, base_theme.CLI_VERSION_PIN is {bt.CLI_VERSION_PIN}: "
        "a pin bump must refresh the vendored base theme (see module docstring)")


def test_theme_name_lives_in_one_place() -> None:
    hits = [f"{rel}: {m}" for rel in _GENERATOR_SOURCES
            for m in _THEME_LITERAL.findall((REPO / rel).read_text(encoding="utf-8"))]
    assert not hits, f"base theme literal outside tooling/report_quality/base_theme.py: {hits}"


def _reports() -> list[Path]:
    reports = sorted(_DIST.glob("*.Report"))
    assert reports, "keine dist-Reports -- Test hat seinen Gegenstand verloren"
    return reports


def test_every_dist_report_carries_the_pinned_base_theme() -> None:
    wrong = []
    for report in _reports():
        data = json.loads((report / "definition" / "report.json").read_text(encoding="utf-8"))
        if data["themeCollection"]["baseTheme"] != bt.base_theme_entry():
            wrong.append(f"{report.name}: themeCollection.baseTheme")
        items = [it for pkg in data.get("resourcePackages") or [] for it in pkg.get("items") or []
                 if it.get("type") == "BaseTheme"]
        if items != [bt.shared_resources_item()]:
            wrong.append(f"{report.name}: BaseTheme items {items}")
        shipped = report / "StaticResources" / "SharedResources" / bt.resource_path()
        if not shipped.is_file() or shipped.read_bytes() != bt.vendored_bytes():
            wrong.append(f"{report.name}: {bt.resource_path()} missing or not the vendored bytes")
        stale = sorted(p.name for p in shipped.parent.glob("*.json")
                       if _THEME_LITERAL.fullmatch(p.stem) and p.stem != bt.BASE_THEME_NAME)
        if stale:
            wrong.append(f"{report.name}: unreferenced base theme files {stale}")
    assert not wrong, (
        "dist drifts from the pinned base theme -- run apply_report_theme --sync-base-theme:\n  "
        + "\n  ".join(wrong))


@pytest.mark.braucht_pbir_cli
def test_vendored_base_theme_equals_pinned_cli_scaffold() -> None:
    from tooling.report_quality.refresh_authoring_metadata import cli_version, scaffold_base_theme

    cli = shutil.which("powerbi-report-author")
    version = cli_version(cli)
    if version != bt.CLI_VERSION_PIN:
        grund = (f"powerbi-report-author {version} != Pin {bt.CLI_VERSION_PIN}: "
                 "kein Vergleich gegen den Pin")
        if os.environ.get("ALUCA_PBIR_CLI_PFLICHT", "") == "1":
            pytest.fail(grund, pytrace=False)
        pytest.skip(grund)

    got = scaffold_base_theme(cli)
    assert got["name"] == bt.BASE_THEME_NAME
    assert got["reportVersionAtImport"] == bt.BASE_THEME_REPORT_VERSION_AT_IMPORT
    assert got["content"] == bt.vendored_bytes(), (
        "vendored base theme differs from the CLI scaffold -- "
        "refresh_authoring_metadata.py --base-theme-only")
