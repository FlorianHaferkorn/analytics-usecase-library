"""Prognose-Measures aus den Forecast-Ausloesern der Action Codes (ADR-0028 §7.1, 30.10.2026).

Ein Action Code mit `trigger.type: Forecast` nennt drei Measures (`forecast.forecast_measure`,
`band.lower_measure`, `band.upper_measure`). Dieses Modul erzeugt sie in jedem Modell, das das
Measure der Trigger-KPI fuehrt -- so wie `comparison_measures.py` die Vergleichs-Measures aus den
Brackets erzeugt. Kein Katalog-Eintrag: eine Prognose ist keine eigene KPI (ADR-0028, Option c
verworfen), und die DSL kennt weder Monatsverschiebung noch Perzentil.

Verfahren (Entscheidung Florian 30.10.2026), Monatsraster ueber `dim_date[Year]`/`[MonthNumber]`
(Monatsindex-Muster wie `comparison_measures` und `action_trigger_dax`; dim_date ist keine
markierte Datumstabelle):

* Punkt fuer den Monat nach dem letzten ausgewaehlten Monat M (Horizont 1 Monat): Mittel der
  Monatswerte M-2..M (`PUNKT_MONATE`), nur wenn alle drei Monate einen Wert haben.
* Historische Ein-Monats-Fehler e(k) = Wert(k) - Mittel(Wert(k-3..k-1)) fuer k in M-23..M
  (`FEHLER_MONATE`), nur Monate mit vollstaendigem Fenster; weniger als `MIN_FEHLER` (12)
  Fehler -> leer.
* Band: Punkt + Perzentil der Fehler, (1 - level) / 2 und (1 + level) / 2 aus `band.level`
  (80 % -> 10. und 90. Perzentil, `PERCENTILEX.INC`).

Andere Filter (Kategorie, Region) bleiben stehen; entfernt wird nur `dim_date`.

CLI:
    python -m tooling.codegen.forecast_measures            # Abweichungen melden (rc 1)
    python -m tooling.codegen.forecast_measures --write    # dist/ nachziehen
"""
from __future__ import annotations

import argparse
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
DIST = REPO / "products" / "fabric" / "powerbi" / "dist"
ACTION_CODES = REPO / "core" / "action_codes"

PUNKT_MONATE = 3
FEHLER_MONATE = 24
MIN_FEHLER = 12
ORDNER = "9_Forecast"
MARKE = "ALUCA_Generated"
WERT = "forecast_measures"
_NS = uuid.UUID("2f6d5a8e-3c1b-4e7a-9a4f-0d8b6c2e1f37")


class Fehler(ValueError):
    """Ein Forecast-Ausloeser, aus dem sich keine ehrliche Prognose bauen laesst."""


@dataclass(frozen=True)
class Prognose:
    code: str
    kpi_id: str
    punkt: str
    unten: str
    oben: str
    level: float


def _tag(*teile: str) -> str:
    return str(uuid.uuid5(_NS, "/".join(teile)))


def prognosen() -> list[Prognose]:
    out = []
    for f in sorted(ACTION_CODES.rglob("*.yaml")):
        ac = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        trig = ac.get("trigger") or {}
        if not isinstance(trig, dict) or trig.get("type") != "Forecast":
            continue
        fc = trig.get("forecast") or {}
        h = fc.get("horizon") or {}
        if (h.get("length"), h.get("unit")) != (1, "months"):
            raise Fehler(f"{ac.get('id')}: Horizont {h} -- erzeugt wird nur 1 Monat")
        band = fc.get("band") or {}
        if band.get("kind") != "prediction_interval":
            raise Fehler(f"{ac.get('id')}: band.kind {band.get('kind')!r} unbekannt")
        kpis = (ac.get("kpis") or {}).get("trigger_kpis") or []
        if len(kpis) != 1:
            raise Fehler(f"{ac.get('id')}: genau eine Trigger-KPI erwartet, nicht {kpis}")
        out.append(Prognose(str(ac["id"]), kpis[0], fc["forecast_measure"], band["lower_measure"],
                            band["upper_measure"], float(band["level"])))
    return out


def _monat(basis: str, k: str) -> str:
    return (f"CALCULATE ( {basis}, REMOVEFILTERS ( 'dim_date' ), FILTER ( ALL ( 'dim_date' ), "
            f"'dim_date'[Year] * 12 + 'dim_date'[MonthNumber] = {k} ) )")


_IDX = "VAR _idx = MAX ( 'dim_date'[Year] ) * 12 + MAX ( 'dim_date'[MonthNumber] )"


def punkt_dax(basis: str) -> str:
    return (f"{_IDX} VAR _w = SELECTCOLUMNS ( GENERATESERIES ( _idx - {PUNKT_MONATE - 1}, _idx ), \"@k\", [Value] ) "
            f"VAR _v = ADDCOLUMNS ( _w, \"@v\", VAR _k = [@k] RETURN {_monat(basis, '_k')} ) "
            f"RETURN IF ( COUNTROWS ( FILTER ( _v, NOT ISBLANK ( [@v] ) ) ) = {PUNKT_MONATE}, "
            f"AVERAGEX ( _v, [@v] ) )")


def rand_dax(basis: str, punkt: str, quantil: float) -> str:
    vor = (f"SELECTCOLUMNS ( GENERATESERIES ( _k - {PUNKT_MONATE}, _k - 1 ), \"@j\", [Value] )")
    fehler = (f"ADDCOLUMNS ( SELECTCOLUMNS ( GENERATESERIES ( _idx - {FEHLER_MONATE - 1}, _idx ), \"@k\", [Value] ), "
              f"\"@e\", VAR _k = [@k] VAR _ist = {_monat(basis, '_k')} "
              f"VAR _vor = ADDCOLUMNS ( {vor}, \"@v\", VAR _j = [@j] RETURN {_monat(basis, '_j')} ) "
              f"RETURN IF ( NOT ISBLANK ( _ist ) && "
              f"COUNTROWS ( FILTER ( _vor, NOT ISBLANK ( [@v] ) ) ) = {PUNKT_MONATE}, "
              f"_ist - AVERAGEX ( _vor, [@v] ) ) )")
    return (f"{_IDX} VAR _p = [{punkt}] VAR _e = FILTER ( {fehler}, NOT ISBLANK ( [@e] ) ) "
            f"RETURN IF ( NOT ISBLANK ( _p ) && COUNTROWS ( _e ) >= {MIN_FEHLER}, "
            f"_p + PERCENTILEX.INC ( _e, [@e], {round(quantil, 4)} ) )")


def _block(model: str, name: str, dax: str, fmt: str | None, zweck: str) -> str:
    z = [f"\t/// Purpose: {zweck}", f"\tmeasure '{name}' = {dax}"]
    if fmt:
        z.append(f"\t\tformatString: {fmt}")
    z += [f"\t\tdisplayFolder: {ORDNER}", f"\t\tlineageTag: {_tag(model, 'measure', name)}", "",
          f'\t\tannotation {MARKE} = "{WERT}"', ""]
    return "\n".join(z) + "\n"


def bloecke(model: str, p: Prognose, basis_name: str, fmt: str | None) -> str:
    basis = f"[{basis_name}]"
    q_u, q_o = (1 - p.level) / 2, (1 + p.level) / 2
    pz = int(round(p.level * 100))
    return "".join([
        _block(model, p.punkt, punkt_dax(basis), fmt,
               f"Prognose von {basis_name} fuer den Monat nach dem letzten ausgewaehlten (Mittel der letzten "
               f"{PUNKT_MONATE} Monate; {p.code}, ADR-0028)."),
        _block(model, p.unten, rand_dax(basis, p.punkt, q_u), fmt,
               f"Unterer Rand des {pz}-%-Intervalls: Punkt + {round(q_u * 100)}. Perzentil der Ein-Monats-Fehler "
               f"der letzten {FEHLER_MONATE} Monate (mind. {MIN_FEHLER}); {p.code}."),
        _block(model, p.oben, rand_dax(basis, p.punkt, q_o), fmt,
               f"Oberer Rand des {pz}-%-Intervalls: Punkt + {round(q_o * 100)}. Perzentil der Ein-Monats-Fehler "
               f"der letzten {FEHLER_MONATE} Monate (mind. {MIN_FEHLER}); {p.code}."),
    ])


def _einfuegen(text: str, block: str) -> str:
    """Eigene Bloecke ersetzen. Sie stehen vor den Vergleichs-Measures (`comparison_measures`
    haengt seine Bloecke ans Ende): so sind beide Generatoren reihenfolgeunabhaengig stabil."""
    from tooling.codegen.comparison_measures import MARKE as CM_MARKE, _ohne_generierte
    basis = _ohne_generierte(text, WERT)
    if not block:
        return basis
    anker = f'annotation {CM_MARKE} = "comparison_measures"'
    if anker not in basis:
        return basis.rstrip("\n") + "\n\n" + block
    # Bloecke wie in comparison_measures._ohne_generierte; vor den ersten Vergleichs-Block
    zeilen, start, akt = basis.split("\n"), [], 0
    for i, z in enumerate(zeilen):
        if (z.startswith("\t///") or z.startswith("\tmeasure ")) and i and not zeilen[i - 1].startswith("\t///"):
            start.append(akt)
            akt = i
    start.append(akt)
    grenzen = start[1:] + [len(zeilen)]
    for von, bis in zip(start, grenzen):
        if anker in "\n".join(zeilen[von:bis]):
            return "\n".join(zeilen[:von]) + "\n" + block + "\n".join(zeilen[von:])
    raise AssertionError("unerreichbar")


def soll(model_dir: Path, ps: list[Prognose], loader=None) -> str | None:
    """Soll-Text von `_Measures.tmdl` (None: Modell ohne _Measures)."""
    from tooling.codegen.comparison_measures import _format_string, _loader
    mt = model_dir / "definition" / "tables" / "_Measures.tmdl"
    if not mt.exists():
        return None
    loader = loader or _loader()
    namen = loader.measure_map_for_model(model_dir)
    definiert = set(loader._model_symbols_for_dir(model_dir).measure_names)
    block = "".join(bloecke(model_dir.name, p, namen[p.kpi_id], _format_string(model_dir, namen[p.kpi_id]))
                    for p in ps if namen.get(p.kpi_id) in definiert)
    return _einfuegen(mt.read_text(encoding="utf-8"), block)


def pruefe(schreiben: bool = False) -> list[str]:
    from tooling.codegen.comparison_measures import _loader
    loader, ps, drift = _loader(), prognosen(), []
    for model_dir in sorted(DIST.glob("*.SemanticModel")):
        mt = model_dir / "definition" / "tables" / "_Measures.tmdl"
        s = soll(model_dir, ps, loader)
        if s is None or s == mt.read_text(encoding="utf-8"):
            continue
        drift.append(mt.relative_to(REPO).as_posix())
        if schreiben:
            mt.write_text(s, encoding="utf-8", newline="\n")
    return drift


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--write", action="store_true", help="dist/ nachziehen")
    a = ap.parse_args(argv)
    drift = pruefe(a.write)
    if drift and not a.write:
        print(f"[forecast-measures] weicht ab ({len(drift)}): {', '.join(drift)} -- --write", file=sys.stderr)
        return 1
    print(f"[forecast-measures] {'geschrieben' if drift else 'aktuell'}: {len(drift)} Datei(en), "
          f"{len(prognosen())} Forecast-Ausloeser")
    return 0


if __name__ == "__main__":
    sys.exit(main())
