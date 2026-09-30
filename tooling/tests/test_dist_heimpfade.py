"""Kein persoenlicher Home-Pfad in `products/fabric/powerbi/dist/` (30.09.2026).

Anlass: alle fuenf ausgelieferten Semantic Models trugen im Parameter `GoldDataPath` den
absoluten Windows-Pfad des Rechners, auf dem der Orchestrator zuletzt lief. Heute steht dort
der Platzhalter aus `tooling/codegen/gold_source.py`; lokal setzt man den Pfad in Power BI
Desktop (`products/fabric/powerbi/dist/README.md`).

Die Regel lebt im Kundendaten-Gate (`tooling/validation/check_kundendaten.py`, `HEIMPFAD`),
nicht hier. Dieser Test prueft sie an festen Beispielen von aussen (die Regex fuettert sich
nicht selbst) und wendet sie auf jede Textdatei unter `dist/` an. Er braucht die gitignorierte
Sperrliste nicht und laeuft deshalb auch in CI.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
DIST = REPO / "products" / "fabric" / "powerbi" / "dist"
sys.path.insert(0, str(REPO / "tooling" / "validation"))

from check_kundendaten import BINAER, heimpfade  # noqa: E402

sys.path.insert(0, str(REPO))
from tooling.codegen import gold_source as gs  # noqa: E402


@pytest.mark.parametrize("text", [
    'expression GoldDataPath = "C:/Users/jdoe/VSCode/repo/showcases/aurora_group/data/gold"',
    r'"source":  "C:\\Users\\jdoe\\VSCode\\repo\\core\\x.yaml"',
    "file:///c:/Users/jdoe/Downloads/Studio.html",
    "/Users/jane/projects/repo/dist",
    "/home/bob/repo/dist",
])
def test_ein_persoenlicher_home_pfad_wird_gefunden(text: str) -> None:
    assert heimpfade(text), text


@pytest.mark.parametrize("text", [
    'expression GoldDataPath = "<GOLD_DATA_PATH>"',
    r"C:\Users\example\AppData\Roaming\npm\powerbi-report-author.cmd",
    "C:/Users/<name>/repo",
    r"PS C:\Users\...>",
    r"C:\Users\$env:USERNAME\repo",
    "/home/user/wt/aul-goldpath",
    "/home/runner/work/repo",
    "https://www.cs.umd.edu/users/mvz/handouts/gqm.pdf",
    "http://metabase-host:3000/api/admin/users/1/password",
])
def test_platzhalter_und_generische_konten_sind_keine_treffer(text: str) -> None:
    assert heimpfade(text) == [], text


def _textdateien() -> list[Path]:
    return [p for p in sorted(DIST.rglob("*"))
            if p.is_file() and p.suffix.lower() not in BINAER]


def test_dist_traegt_keinen_persoenlichen_home_pfad() -> None:
    dateien = _textdateien()
    assert len(dateien) > 100, "dist/ fast leer -- der Test haette nichts geprueft"
    funde = []
    for p in dateien:
        for nr, zeile in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            funde += [f"{p.relative_to(REPO)}:{nr}: {t}" for t in heimpfade(zeile)]
    assert funde == [], "persoenliche Pfade in dist/ -- Quelle korrigieren, neu erzeugen:\n" + "\n".join(funde)


def test_gold_data_path_ist_in_allen_modellen_der_platzhalter() -> None:
    modelle = sorted(DIST.glob("*.SemanticModel"))
    assert len(modelle) == 5
    for m in modelle:
        text = (m / "definition" / "expressions.tmdl").read_text(encoding="utf-8")
        assert f'expression GoldDataPath = "{gs.GOLD_PATH_PLATZHALTER}" meta' in text, m.name


def test_der_generator_ersetzt_einen_rechnerpfad() -> None:
    """Gegenprobe am Generator: ein Rechnerpfad wird zum Platzhalter, nicht durchgereicht."""
    m = sorted(DIST.glob("*.SemanticModel"))[0]
    text = (m / "definition" / "expressions.tmdl").read_text(encoding="utf-8")
    alt = text.replace(f'"{gs.GOLD_PATH_PLATZHALTER}"', '"C:/Users/jdoe/repo/showcases/aurora_group/data/gold"', 1)
    assert heimpfade(alt)
    assert gs.soll(m.name, alt) == text


def test_ohne_gold_data_path_bricht_der_generator_ab() -> None:
    m = sorted(DIST.glob("*.SemanticModel"))[0]
    text = (m / "definition" / "expressions.tmdl").read_text(encoding="utf-8")
    ohne = text.replace("expression GoldDataPath =", "expression AndererName =", 1)
    with pytest.raises(ValueError, match="GoldDataPath fehlt"):
        gs.soll(m.name, ohne)
