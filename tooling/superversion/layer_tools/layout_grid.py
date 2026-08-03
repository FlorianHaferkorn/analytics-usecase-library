"""layer_tools.layout_grid — der EINE Leser des governten Rasters.

Warum es diese Datei gibt
-------------------------
Gemessen am 02.08.2026 hatte die Leinwandgroesse **sieben** unabhaengige Meinungen im
Repo, davon zwei mit verschiedenen Werten als Default (1280 und 1920). Genau daraus
sind an diesem Tag zwei Fehler entstanden:

  * **L13** — `_OVERVIEW_LAYOUT` war gegen 1920x1080 geschrieben, `layout_grid.yaml`
    rechnete gegen 1280x720. Auf der design_base lag der erste Slot ausserhalb des
    Rasters.
  * **L8** — die Seite deklarierte 1280x720, ihre Visuals waren gegen 1920x1080
    aufgeloest. Der offizielle Validator meldete `PBIR_LAYOUT_OUT_OF_BOUNDS_WIDTH`.

Beide Male hatte jede Seite recht ueber sich und unrecht ueber die andere. Das ist die
Signatur einer Dublette, nicht eines Rechenfehlers — und sie wiederholt sich, solange es
mehr als eine Stelle gibt, die die Antwort kennt.

Warum HIER
----------
Neben `visual_library.py` (Visual-Vokabular) und `design_tokens.py` (Farb-/Typo-Tokens):
Layer-Tools sind im Repo bereits die Schicht, die governte YAML liest und auswertbar
macht. Ein weiteres Muster dafuer waere ein weiteres Silo gewesen.

Kein stiller Default
--------------------
`config_loader.load_layout_grid()` gab bei Fehler ein leeres Dict zurueck — „caller uses
defaults". Das ist dieselbe Verdeckungsmechanik wie die drei `TREND_LINE`-Fallbacks:
es sieht aus wie Robustheit und ist Blindheit. Hier bricht ein fehlendes oder kaputtes
Raster ab, statt eine plausible Zahl zu erfinden.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[3]
GRID_YAML = _REPO_ROOT / "core" / "templates" / "page_templates" / "tokens" / "layout_grid.yaml"


class LayoutGridError(ValueError):
    """Das governte Raster fehlt oder ist unvollstaendig."""


@dataclass(frozen=True)
class GridParams:
    """Rasterparameter EINER Leinwand. Alles, was zum Aufloesen noetig ist."""
    cols: int
    rows: int
    gutter: float
    outer: float
    width: int
    height: int

    @property
    def lu_w(self) -> float:
        return (self.width - 2 * self.outer - (self.cols - 1) * self.gutter) / self.cols

    @property
    def lu_h(self) -> float:
        return (self.height - 2 * self.outer - (self.rows - 1) * self.gutter) / self.rows


_PFLICHT = ("cols", "rows", "gutter", "outer_margin")


def load(profile: str = "production", path: Path | None = None) -> GridParams:
    """Raster + Leinwand eines Profils. Bricht ab statt zu raten.

    `profile` waehlt aus `canvas:` — heute `design_base` (1280x720) oder
    `production` (1920x1080). Der Default ist **production**, weil das die Leinwand
    ist, gegen die die Emitter tatsaechlich rendern (`pbip.py`, `from_aluca`).

    Der Pfad wird zur LAUFZEIT aufgeloest, nicht als Default-Argument gebunden.
    Ein `path: Path = GRID_YAML` haette den Wert bei Funktionsdefinition eingefroren —
    die Konstante waere damit nicht mehr ersetzbar gewesen, weder fuer Tests noch fuer
    einen abweichenden Rasterstand. Gefunden hat das der Wirksamkeits-Test aus L8, der
    genau diese Ersetzbarkeit prueft.
    """
    path = path or GRID_YAML
    if not path.exists():
        raise LayoutGridError(f"governtes Raster fehlt: {path}")
    doc: dict[str, Any] = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    grid, spacing, canvas = doc.get("grid") or {}, doc.get("spacing") or {}, doc.get("canvas") or {}

    fehlend = [k for k in _PFLICHT if k not in {**grid, **spacing}]
    if fehlend:
        raise LayoutGridError(
            f"{path.name} unvollstaendig — fehlend: {', '.join(fehlend)}. "
            "Ein halbes Raster ergibt Positionen, die plausibel aussehen und falsch sind."
        )
    if profile not in canvas:
        raise LayoutGridError(
            f"unbekanntes Canvas-Profil '{profile}'. Bekannt: {sorted(canvas)}")

    c = canvas[profile]
    return GridParams(
        cols=int(grid["cols"]), rows=int(grid["rows"]),
        gutter=float(spacing["gutter"]), outer=float(spacing["outer_margin"]),
        width=int(c["width"]), height=int(c["height"]),
    )


def to_pixels(col: float, row: float, cs: float, rs: float,
              params: GridParams) -> dict[str, float]:
    """Logical Units → Pixel. Die einzige Aufloesungsstelle im Repo.

    Spiegelt `core/templates/page_templates/preview/src/grid/slot-pos.ts`:
        left   = outer + col * (lu_w + gutter)
        top    = outer + row * (lu_h + gutter)
        width  = cs  * lu_w + (cs - 1) * gutter
        height = rs  * lu_h + (rs - 1) * gutter

    Entscheidend ist, dass `gutter` und `outer` HIER eingehen. Ihre Absolutheit neben
    skalierenden Bruechen war der Defekt aus L13.
    """
    return {
        "x": params.outer + col * (params.lu_w + params.gutter),
        "y": params.outer + row * (params.lu_h + params.gutter),
        "width": cs * params.lu_w + (cs - 1) * params.gutter,
        "height": rs * params.lu_h + (rs - 1) * params.gutter,
    }
