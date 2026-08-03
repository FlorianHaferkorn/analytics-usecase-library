"""Alle dist-Reports tragen dasselbe aktive Theme — inhaltlich, nicht byteweise.

Gefunden am 03.08.2026: 16 Reports setzten `valueAxis.start = 0` global auf `*`/`*`,
COM-001_Sales_Performance nur fuer `areaChart` und `lineChart`. BC-CHART-09 verlangt die
Nullbasis fuer **Balken** — COM-001 war damit der einzige Report ohne diese Zusage, und
KEIN Pruefer konnte das sehen: `check_zero_based_axes.py` liest `visual.json`, die
Zusage steht im Theme.

Der Test vergleicht den geparsten Inhalt, nicht die Bytes: Einrueckung und
Schluesselreihenfolge sind keine Aussage ueber das Aussehen eines Reports, und ein Test,
der daran scheitert, erzieht zum Ignorieren.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tooling" / "validation"))
sys.path.insert(0, str(REPO))

_DIST = REPO / "products/fabric/powerbi/dist"


def _aktive_themes() -> dict[str, dict]:
    from check_palette_monochrome import aktives_theme

    out: dict[str, dict] = {}
    for report in sorted(_DIST.glob("*.Report")):
        if (tj := aktives_theme(report)) is not None:
            out[report.name] = json.loads(tj.read_text(encoding="utf-8"))
    return out


def _kanonisch(d: dict) -> str:
    return json.dumps(d, sort_keys=True, ensure_ascii=False)


def test_every_report_carries_the_same_active_theme():
    themes = _aktive_themes()
    assert len(themes) >= 10, f"nur {len(themes)} Reports mit aufloesbarem Theme"
    fassungen: dict[str, list[str]] = {}
    for name, theme in themes.items():
        fassungen.setdefault(_kanonisch(theme), []).append(name)
    assert len(fassungen) == 1, (
        "Theme-Kopien auseinandergelaufen: "
        + " | ".join(f"{len(v)}× {sorted(v)[0]}…" for v in fassungen.values())
        + ". Ein Report mit abweichendem Theme traegt andere governte Zusagen als die "
          "uebrigen — und kein visual.json-Pruefer sieht das.")


def test_zero_based_axis_is_promised_globally():
    """Die Nullbasis steht auf `*`/`*` — damit gilt sie fuer Balken (BC-CHART-09).

    Steht sie nur auf einzelnen Chart-Typen, sind ausgerechnet die Balken ausgenommen,
    fuer die die Regel geschrieben ist. Genau das war in COM-001 der Fall.
    """
    for name, theme in _aktive_themes().items():
        stern = ((theme.get("visualStyles") or {}).get("*") or {}).get("*") or {}
        achse = (stern.get("valueAxis") or [{}])[0]
        assert achse.get("start") == 0, (
            f"{name}: `valueAxis.start` nicht global auf 0 — Balken waeren von der "
            f"Nullbasis ausgenommen, und check_zero_based_axes.py sieht das nicht, "
            f"weil es nur visual.json liest.")
