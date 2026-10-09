"""Base theme of generated PBIR reports -- taken from the pinned official CLI (Meridian D-587).

Single source for the base theme NAME, its ``reportVersionAtImport`` and the vendored
file content. Every generator path (``pbip_writer``, ``adapters/pbip``, the superversion
PBIR target, ``apply_report_theme``) reads these constants; none carries its own literal.

Official-First: the content is not ours. ``@microsoft/powerbi-report-authoring-cli``
ships it with ``scaffold`` (bundled asset ``src/templates/assets/<name>.json``);
``refresh_authoring_metadata.py --base-theme-only`` vendors it byte-for-byte into
``tooling/schemas/pbir/base_themes/`` (the ADR-0001 snapshot pattern), so the
customer runtime needs no CLI. ``tooling/tests/test_base_theme_drift.py`` compares the
vendored copy, the name and ``reportVersionAtImport`` against a live ``scaffold`` of the
pinned CLI.

Measured 30.09.2026 with CLI 0.4.0 (``scaffold --offline``): baseTheme name ``CY26SU10``,
``reportVersionAtImport`` ``{visual 2.11.0, report 3.4.0, page 2.3.1}``.
Hergeleitet, ANNAHME, ungeprueft (D-587): ``CY26SU10`` is "Classic 2026", not Fluent 2.

Measured 07.10.2026 with CLI 0.5.0 (Meridian D-685): ``scaffold`` now writes ``Fluent2-CY26SU10``
(95297 bytes), ``reportVersionAtImport`` unchanged. Learn ``power-bi-reports-visual-defaults``:
Fluent 2 is the default base theme for new reports, Classic 2026 the previous one.

Pure stdlib, no side effects on import.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

#: npm package and the version pinned in ``.github/workflows/superversion.yml``
#: (D-580). The drift test holds both in step.
CLI_PACKAGE = "@microsoft/powerbi-report-authoring-cli"
CLI_VERSION_PIN = "0.5.0"

#: Base theme the pinned CLI scaffolds new reports with (D-587).
BASE_THEME_NAME = "Fluent2-CY26SU10"

#: ``themeCollection.baseTheme.reportVersionAtImport`` as written by ``scaffold`` of the pin.
BASE_THEME_REPORT_VERSION_AT_IMPORT: dict[str, str] = {
    "visual": "2.11.0",
    "report": "3.4.0",
    "page": "2.3.1",
}

_REPO = Path(__file__).resolve().parents[2]
VENDORED_DIR = _REPO / "tooling" / "schemas" / "pbir" / "base_themes"


def vendored_path(name: str = BASE_THEME_NAME) -> Path:
    """Path of the vendored base theme file for ``name``."""
    return VENDORED_DIR / f"{name}.json"


def vendored_bytes(name: str = BASE_THEME_NAME) -> bytes:
    """Byte content of the vendored base theme (raises if it is missing -- never degrade)."""
    return vendored_path(name).read_bytes()


def resource_path(name: str = BASE_THEME_NAME) -> str:
    """``resourcePackages`` item path, relative to ``StaticResources/SharedResources``."""
    return f"BaseThemes/{name}.json"


def base_theme_entry() -> dict:
    """``themeCollection.baseTheme`` block (fresh dict per call)."""
    return {
        "name": BASE_THEME_NAME,
        "reportVersionAtImport": dict(BASE_THEME_REPORT_VERSION_AT_IMPORT),
        "type": "SharedResources",
    }


def shared_resources_item() -> dict:
    """``SharedResources`` item that registers the base theme file."""
    return {"name": BASE_THEME_NAME, "path": resource_path(), "type": "BaseTheme"}


# ── Wirksames Theme: Basistheme + eigenes Theme (Meridian D-685, 08.10.2026) ──────────────
#
# Seit D-685 liefert das Basistheme Fluent2-CY26SU10 Rahmen, Schatten, Gitter und Legende; das
# eigene Theme setzt sie nicht mehr. Ein Pruefer, der nur das eigene Theme liest, saehe den
# 1-px-Rahmen nicht und waere gruen, ohne gemessen zu haben.
#
# Vorrangannahme (ANNAHME, in Desktop ungeprueft): das eigene Theme ueberschreibt das Basistheme
# **eigenschaftsweise** am selben Schluessel (Visual-Typ, Selektor, Objekt). Fuer den ersten
# Eintrag eines Objekts werden die Eigenschaften zusammengefuehrt, das eigene Theme gewinnt.
# Typ-spezifische Eintraege und ``*`` werden NICHT gegeneinander aufgeloest: jeder Schluessel
# bleibt, wie er im zusammengefuehrten Theme steht.


def wirksame_visual_styles(eigenes: dict, basis: dict | None) -> dict:
    """``visualStyles`` aus Basistheme und eigenem Theme (rein; Eingaben bleiben unveraendert)."""
    out: dict = copy.deepcopy((basis or {}).get("visualStyles") or {})
    for typ, selektoren in ((eigenes or {}).get("visualStyles") or {}).items():
        ziel_typ = out.setdefault(typ, {})
        for sel, objekte in (selektoren or {}).items():
            ziel_sel = ziel_typ.setdefault(sel, {})
            for obj, eintraege in (objekte or {}).items():
                alt = ziel_sel.get(obj)
                if (isinstance(alt, list) and alt and isinstance(alt[0], dict)
                        and isinstance(eintraege, list) and eintraege and isinstance(eintraege[0], dict)):
                    ziel_sel[obj] = [{**alt[0], **eintraege[0]}] + copy.deepcopy(eintraege[1:])
                else:
                    ziel_sel[obj] = copy.deepcopy(eintraege)
    return out


def basistheme_des_berichts(report: Path) -> dict | None:
    """Das Basistheme, das ``report.json`` nennt, aus dem Bericht selbst (nicht aus dem Vendor).

    None, wenn keines genannt oder die Datei fehlt — der Aufrufer meldet das, statt still nur
    das eigene Theme zu messen.
    """
    rj = Path(report) / "definition" / "report.json"
    if not rj.is_file():
        return None
    name = (((json.loads(rj.read_text(encoding="utf-8")) or {}).get("themeCollection") or {})
            .get("baseTheme") or {}).get("name")
    if not name:
        return None
    datei = Path(report) / "StaticResources" / "SharedResources" / resource_path(name)
    return json.loads(datei.read_text(encoding="utf-8")) if datei.is_file() else None
