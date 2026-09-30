"""Vergleichs-Measures aus den deklarierten `comparison`-Feldern der Brackets (R6.1).

Die Brackets deklarieren an 29 Stellen, wogegen eine Kennzahl gelesen wird
(`comparison: vs_target | vs_plan | vs_py`). Bis 23.09.2026 las der Generator das Feld nie:
14 von 17 Trendlinien trugen eine einzige Reihe, obwohl ihr Titel nach dem Ziel fragte.

Dieses Modul erzeugt je Modell:

- die Tabelle `fact_target` (kpi_id x Monat x Szenario), Werte vom Kunden beim Onboarding
  (Entscheidung Flo 23.09.2026: Zieltabelle je Kunde). Leer, solange keine Werte vorliegen;
  dann zeigt der Report keine Ziellinie statt einer erfundenen. Beziehung zu `dim_date`.
- je deklariertem Vergleich eine Referenz-Measure und ihre Abweichung:
  `<M> Target` / `<M> vs Target` aus `fact_target` (scenario = target),
  `<M> Plan` / `<M> vs Plan` aus `fact_target` (scenario = plan) -- nur wenn das Modell keine
  governte Plan-KPI fuehrt; sonst wird die governte genommen und nichts erzeugt,
  `<M> PY` / `<M> vs PY` per Monatsindex-Shift um zwoelf Monate, ohne neue Daten.

Zielwerte stehen in der Skala der Measure (Prozent als Anteil, 0,85 = 85 %). Aggregation
ueber Monate: Summe fuer Betraege und Zaehler, sonst Durchschnitt (aus `calc_type`).

CLI:
    python -m tooling.codegen.comparison_measures            # Abweichungen melden (rc 1)
    python -m tooling.codegen.comparison_measures --write    # dist/ nachziehen
    python -m tooling.codegen.comparison_measures --vorlage ziele.csv   # Onboarding-Vorlage
    python -m tooling.codegen.comparison_measures --laden ziele.csv     # ausgefuellt laden
"""
from __future__ import annotations

import argparse
import re
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
DIST = REPO / "products" / "fabric" / "powerbi" / "dist"
BRACKETS = REPO / "core" / "usecases" / "core"
KPIS = REPO / "core" / "kpi_catalog" / "kpis"

TABELLE = "fact_target"
# Gold-Ordner der Zieltabelle. Beim Kunden per ALUCA_GOLD_FACTS auf dessen Gold-Layer zeigen.
import os as _os
GOLD_ZIEL = Path(_os.environ.get("ALUCA_GOLD_FACTS", REPO / "showcases" / "aurora_group" / "data" / "gold" / "facts")) / TABELLE
ORDNER = "8_Comparison"
MARKE = "ALUCA_Generated"                    # Annotation, an der der Generator seine Measures erkennt
SUMME = {"amount", "count", "sum", "quantity"}
INTRINSISCH = {"waterfall", "waterfall_chart", "variance_bar"}
_NS = uuid.UUID("5b1f0c1e-6a52-4c1e-9d3b-7a0e2c6f8a10")
# Die abgeleiteten Namen, die Drift-Checks als Framework-Measures ausnehmen.
ABGELEITET = re.compile(r"^.+ (Target|vs Target|Plan \(Target Table\)|vs Plan \(Target Table\)|PY|vs PY)$")


def _tag(*teile: str) -> str:
    return str(uuid.uuid5(_NS, "/".join(teile)))


@dataclass(frozen=True)
class Vergleich:
    model: str
    kpi_id: str
    art: str            # vs_target | vs_plan | vs_py
    measure: str


def _katalog() -> dict[str, dict]:
    out = {}
    for f in sorted(KPIS.glob("*.yaml")):
        d = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        if d.get("kpi_id"):
            out[d["kpi_id"]] = d
    return out


def _loader():
    tooling = REPO / "products" / "fabric" / "powerbi" / "tooling"
    for p in (str(REPO), str(tooling)):
        if p not in sys.path:
            sys.path.insert(0, p)
    from page_scaffold_generator.config_loader import ConfigLoader
    return ConfigLoader(REPO)


def _komponenten(bracket: dict):
    p1 = (bracket.get("ux_layout_rules") or {}).get("page_1_summary") or {}
    c3 = p1.get("component_3s")
    if isinstance(c3, dict):
        yield c3
    for c in p1.get("component_30s") or []:
        if isinstance(c, dict):
            yield c


def plan_kpi(kpi_id: str, katalog: dict) -> str | None:
    """Die governte Plan-KPI zu `kpi_id`, wenn der Katalog eine fuehrt (`<basis>.plan.<einheit>`).
    Sie ist ein Pegel und darf als Referenzreihe neben der Kennzahl stehen."""
    basis, _, einheit = kpi_id.rpartition(".")
    kandidat = f"{basis}.plan.{einheit}"
    return kandidat if kandidat in katalog else None


def plan_abweichung_kpi(kpi_id: str, katalog: dict) -> str | None:
    """Die governte Plan-Abweichung zu `kpi_id` (`<basis>.vs_plan.<einheit>`), etwa
    margin.gm.vs_plan.pct aus fact_plan_sales. Sie belegt, dass ein Plan governt existiert
    (Entscheidung Flo 23.09.2026: dann keinen zweiten Plan aus der Vorlage verlangen), ist aber
    eine Abweichung und wird nie als Referenzreihe neben den Pegel gelegt."""
    basis, _, einheit = kpi_id.rpartition(".")
    kandidat = f"{basis}.vs_plan.{einheit}"
    return kandidat if kandidat in katalog else None


def _governter_plan(kid: str, katalog: dict, namen: dict[str, str], definiert: set[str]) -> bool:
    return any(k and namen.get(k) in definiert
               for k in (plan_kpi(kid, katalog), plan_abweichung_kpi(kid, katalog)))


def vergleiche() -> tuple[list[Vergleich], list[str]]:
    """Alle deklarierten Vergleiche, deren KPI im gebundenen Modell existiert, und die Luecken."""
    loader, katalog = _loader(), _katalog()
    out, luecken = [], []
    for bf in sorted(BRACKETS.glob("*/UseCase_Bracket.yaml")):
        b = yaml.safe_load(bf.read_text(encoding="utf-8")) or {}
        model_dir = loader._target_model_dir(b)
        if model_dir is None or not (DIST / f"{bf.parent.name}.Report").is_dir():
            continue                     # ohne ausgelieferten Report kein Vergleich zu zeichnen
        namen = loader.measure_map_for_model(model_dir)
        definiert = set(loader._model_symbols_for_dir(model_dir).measure_names)
        for c in _komponenten(b):
            art = c.get("comparison")
            kid = c.get("kpi_id") or ((c.get("kpi_ids") or [None])[0])
            if art not in ("vs_target", "vs_plan", "vs_py") or not isinstance(kid, str):
                continue
            if c.get("visual_type") in INTRINSISCH:
                continue                     # die Bruecke IST der Vergleich (check_reference_lines)
            if kid not in katalog:
                luecken.append(f"{b.get('id')}: {kid} ist keine Katalog-KPI ({art})")
                continue
            m = namen.get(kid)
            if m not in definiert:
                luecken.append(f"{b.get('id')}: {kid} hat im Modell {model_dir.name} kein Measure")
                continue
            if art == "vs_plan" and _governter_plan(kid, katalog, namen, definiert):
                continue                 # governter Plan vorhanden, nichts zu erzeugen
            out.append(Vergleich(model_dir.name, kid, art, m))
    return sorted(set(out), key=lambda v: (v.model, v.measure, v.art)), luecken


def _format_string(model_dir: Path, measure: str) -> str | None:
    text = (model_dir / "definition" / "tables" / "_Measures.tmdl").read_text(encoding="utf-8")
    m = re.search(r"^\tmeasure '" + re.escape(measure) + r"' =.*?(?=^\t\S|\Z)", text, re.M | re.S)
    if not m:
        return None
    f = re.search(r"^\t\tformatString: (.+)$", m.group(0), re.M)
    return f.group(1).strip() if f else None


def _measure_block(model: str, name: str, dax: str, fmt: str | None, zweck: str) -> str:
    zeilen = [f"\t/// Purpose: {zweck}",
              f"\tmeasure '{name}' = {dax}"]
    if fmt:
        zeilen.append(f"\t\tformatString: {fmt}")
    zeilen += [f"\t\tdisplayFolder: {ORDNER}",
               f"\t\tlineageTag: {_tag(model, 'measure', name)}",
               "",
               f'\t\tannotation {MARKE} = "comparison_measures"',
               ""]
    return "\n".join(zeilen) + "\n"


def referenz_name(measure: str, art: str) -> str:
    """Name der Referenz-Measure, die dieser Generator fuer (measure, art) erzeugt."""
    return {"vs_target": f"{measure} Target", "vs_plan": f"{measure} Plan (Target Table)",
            "vs_py": f"{measure} PY"}[art]


def referenzen_fuer_bracket(bracket: dict, namen: dict[str, str], definiert: set[str]) -> dict[str, str]:
    """`<kpi_id>|<art>` -> Referenz-Measure fuer die Vergleiche eines Brackets, die das Modell fuehrt.

    vs_plan nimmt die governte Plan-KPI, wo der Katalog eine fuehrt; sonst die erzeugte.
    Was das Modell nicht fuehrt, fehlt im Ergebnis -- der Seitenbauer zeichnet dann nichts.
    """
    katalog = _katalog()
    out = {}
    for c in _komponenten(bracket):
        art, kid = c.get("comparison"), c.get("kpi_id") or ((c.get("kpi_ids") or [None])[0])
        if art not in ("vs_target", "vs_plan", "vs_py") or kid not in namen:
            continue
        pk = plan_kpi(kid, katalog) if art == "vs_plan" else None
        if pk and namen.get(pk) in definiert:
            ref = namen[pk]                      # governter Plan-Pegel
        elif art == "vs_plan" and _governter_plan(kid, katalog, namen, definiert):
            continue                             # nur die Abweichung governt: keine Referenzreihe
        else:
            ref = referenz_name(namen[kid], art)
        if ref in definiert:
            out[f"{kid}|{art}"] = ref
    return out


def abweichung_name(measure: str, art: str) -> str:
    return {"vs_target": f"{measure} vs Target", "vs_plan": f"{measure} vs Plan (Target Table)",
            "vs_py": f"{measure} vs PY"}[art]


def ziel_vorhanden(kpi_id: str, szenario: str, gold: Path = GOLD_ZIEL) -> bool:
    """Fuehrt fact_target Werte fuer diese KPI? Ohne Werte zeigte eine Delta-Karte "(Blank)"."""
    import pyarrow.parquet as pq
    for f in sorted(Path(gold).glob("*.parquet")):
        t = pq.read_table(f, columns=["kpi_id", "scenario"]).to_pydict()
        if any(k == kpi_id and s == szenario for k, s in zip(t["kpi_id"], t["scenario"])):
            return True
    return False


def band_delta(bracket: dict, namen: dict[str, str], definiert: set[str],
               gold: Path = GOLD_ZIEL) -> tuple[str, str] | None:
    """(Delta-Measure, kpi_id) fuer das KPI-Band, wenn component_3s einen Vergleich deklariert
    und dieser Vergleich Daten hat: Vorjahr immer (rechnet aus der Historie), Ziel und Plan aus
    fact_target nur, wenn der Kunde Werte geliefert hat."""
    p1 = (bracket.get("ux_layout_rules") or {}).get("page_1_summary") or {}
    c3 = p1.get("component_3s")
    if not isinstance(c3, dict):
        return None
    art, kid = c3.get("comparison"), c3.get("kpi_id")
    if art not in ("vs_target", "vs_plan", "vs_py") or kid not in namen:
        return None
    if art == "vs_plan" and _governter_plan(kid, _katalog(), namen, definiert):
        return None                              # governter Plan: seine Abweichung steht im Band
    d = abweichung_name(namen[kid], art)
    if d not in definiert:
        return None
    if art != "vs_py" and not ziel_vorhanden(kid, "target" if art == "vs_target" else "plan", gold):
        return None
    return d, kid


def measures_fuer(v: Vergleich, calc_type: str, fmt: str | None) -> list[str]:
    agg = "SUM" if calc_type in SUMME else "AVERAGE"
    basis = f"[{v.measure}]"
    if v.art == "vs_py":
        ref, ref_dax, zweck = (f"{v.measure} PY",
                               "VAR _idx = SELECTCOLUMNS ( SUMMARIZE ( 'dim_date', 'dim_date'[Year], "
                               "'dim_date'[MonthNumber] ), \"i\", 'dim_date'[Year] * 12 + 'dim_date'[MonthNumber] - 12 ) "
                               f"RETURN CALCULATE ( {basis}, REMOVEFILTERS ( 'dim_date' ), FILTER ( ALL ( 'dim_date' ), "
                               "'dim_date'[Year] * 12 + 'dim_date'[MonthNumber] IN _idx ) )",
                               f"Vorjahreswert von {v.measure} (comparison: vs_py): die ausgewaehlten Monate um "
                               "zwoelf verschoben, Monatsindex-Muster wie 'CCC Days PM' (dim_date ist keine "
                               "markierte Datumstabelle, SAMEPERIODLASTYEAR liefe neben einem Monats-Slicer leer).")
        abw = abweichung_name(v.measure, "vs_py")
    else:
        szenario = "target" if v.art == "vs_target" else "plan"
        ref = referenz_name(v.measure, v.art)
        abw = abweichung_name(v.measure, v.art)
        ref_dax = (f"CALCULATE ( {agg} ( {TABELLE}[Target Value] ), "
                   f"{TABELLE}[kpi_id] = \"{v.kpi_id}\", {TABELLE}[scenario] = \"{szenario}\" )")
        zweck = (f"{'Ziel' if szenario == 'target' else 'Plan'}wert von {v.measure} aus {TABELLE} "
                 f"(comparison: {v.art}); konzernweit, auch beim Filtern auf eine Einheit; leer, "
                 f"solange der Kunde keinen Wert geliefert hat.")
    abw_dax = f"VAR _r = [{ref}] RETURN IF ( ISBLANK ( _r ), BLANK (), {basis} - _r )"
    return [
        _measure_block(v.model, ref, ref_dax, fmt, zweck),
        _measure_block(v.model, abw, abw_dax, fmt,
                       f"Abweichung {v.measure} gegen {ref}; leer ohne Referenzwert."),
    ]


def tabelle_tmdl(model: str, modus: str | None = None) -> str:
    """``fact_target`` als TMDL; die Partition folgt dem Speichermodus (D-590, ``None`` = Import)."""
    from tooling.codegen.speichermodus import gold_partition, konstanten
    modus = modus or konstanten()[1]
    spalten = [("kpi_id", "string"), ("scenario", "string"), ("DateKey", "int64"), ("Target Value", "double")]
    z = ["/// Purpose: Ziel- und Planwerte je KPI und Monat, vom Kunden beim Onboarding geliefert (R6.1).",
         "/// Leer, solange keine Werte vorliegen: dann zeigt der Report keine Ziellinie statt einer erfundenen.",
         "/// Werte in der Skala der Measure (Prozent als Anteil). Erzeugt von tooling/codegen/comparison_measures.py.",
         f"table {TABELLE}",
         f"\tlineageTag: {_tag(model, TABELLE)}",
         ""]
    for name, typ in spalten:
        q = f"'{name}'" if " " in name else name
        z += [f"\tcolumn {q}",
              f"\t\tdataType: {typ}",
              "\t\tisHidden",
              f"\t\tlineageTag: {_tag(model, TABELLE, name)}",
              "\t\tsummarizeBy: none",
              f"\t\tsourceColumn: {name}",
              ""]
    z += gold_partition(TABELLE, "facts", modus, einzug="\t\t\t\t") + [""]
    return "\n".join(z)


BEZIEHUNG = f"relationship dim_date_{TABELLE}\n\tfromColumn: {TABELLE}.DateKey\n\ttoColumn: dim_date.DateKey\n"


def _ohne_generierte(text: str) -> str:
    """Entfernt alle Measure-Bloecke mit der Generator-Annotation (samt /// davor)."""
    zeilen = text.split("\n")
    bloecke, akt = [], []
    for z in zeilen:
        oben = z.startswith("\t") and not z.startswith("\t\t")
        if oben and (z.startswith("\t///") or z.startswith("\tmeasure ") or z.startswith("\tcolumn ")
                     or z.startswith("\tpartition ")) and akt and not akt[-1].startswith("\t///"):
            bloecke.append(akt)
            akt = []
        akt.append(z)
    bloecke.append(akt)
    behalten = [b for b in bloecke if f"annotation {MARKE} = \"comparison_measures\"" not in "\n".join(b)]
    return "\n".join("\n".join(b) for b in behalten)


def soll_measures(model_dir: Path, vs: list[Vergleich], katalog: dict) -> str:
    return "".join(
        "".join(measures_fuer(v, str(katalog[v.kpi_id].get("calc_type") or ""), _format_string(model_dir, v.measure)))
        for v in vs if v.model == model_dir.name)


def _einfuegen(text: str, block: str) -> str:
    basis = _ohne_generierte(text)
    if not block:
        return basis
    i = basis.find("\n\tcolumn ")
    if i == -1:
        return basis.rstrip("\n") + "\n\n" + block
    return basis[:i + 1] + block + "\n" + basis[i + 1:]


def pruefe(schreiben: bool = False, modus: str | None = None) -> tuple[list[str], list[str]]:
    """(abweichende Dateien, Luecken). Mit `schreiben` werden die Abweichungen behoben.

    ``modus``: Speichermodus des Mandanten (D-590, ``None`` = Import); jedes Zielmodell wird
    vorher mit ``speichermodus.pruefe_modell`` gegen ihn geprueft."""
    from tooling.codegen.speichermodus import pruefe_modell
    vs, luecken = vergleiche()
    katalog = _katalog()
    drift = []
    for model_dir in sorted(DIST.glob("*.SemanticModel")):
        d = model_dir / "definition"
        if modus is not None:
            pruefe_modell(d, modus)
        soll = {
            d / "tables" / f"{TABELLE}.tmdl": tabelle_tmdl(model_dir.name, modus),
            d / "relationships" / f"dim_date_{TABELLE}.tmdl": BEZIEHUNG,
        }
        mt = d / "tables" / "_Measures.tmdl"
        soll[mt] = _einfuegen(mt.read_text(encoding="utf-8"), soll_measures(model_dir, vs, katalog))
        model = d / "model.tmdl"
        mtext = model.read_text(encoding="utf-8")
        if f"ref table {TABELLE}\n" not in mtext:
            mtext = mtext.replace("ref table _Measures\n", f"ref table _Measures\nref table {TABELLE}\n", 1)
        soll[model] = mtext
        for pfad, inhalt in soll.items():
            ist = pfad.read_text(encoding="utf-8") if pfad.exists() else None
            if ist != inhalt:
                drift.append(pfad.relative_to(REPO).as_posix())
                if schreiben:
                    pfad.parent.mkdir(parents=True, exist_ok=True)
                    pfad.write_text(inhalt, encoding="utf-8", newline="\n")
    return drift, luecken


# --- Onboarding: Vorlage fuer den Kunden und Import in fact_target (R6.1b) ---------------

VORLAGE_SPALTEN = ["kpi_id", "scenario", "measure", "angabe_als", "gilt_ab", "gilt_bis", "wert"]


def _angabe_als(kid: str, katalog: dict) -> str:
    fmt = str((katalog[kid].get("business") or {}).get("unit_format") or "")
    if fmt.startswith("percent"):
        return "Anteil (0.85 = 85 %)"
    if fmt.startswith("eur"):
        return "Betrag in EUR je Monat" if katalog[kid].get("calc_type") in SUMME else "Betrag in EUR"
    for praefix, text in (("days", "Tage"), ("hours", "Stunden"), ("index", "Indexwert"),
                          ("ratio", "Verhaeltnis (3.0 = 3x)"), ("count", "Anzahl je Monat"),
                          ("units", "Stueck je Monat")):
        if fmt.startswith(praefix):
            return text
    return fmt or "Zahl"


def vorlage_zeilen() -> list[dict]:
    """Je Ziel-/Plan-Vergleich eine Zeile. Der Kunde traegt Zeitraum und Wert ein; bekannt
    ist schon alles andere (Nicht schaetzen, wenn gefragt werden kann: vorbelegen, nur
    abfragen, was fehlt). PY braucht keine Werte und fehlt deshalb."""
    vs, _ = vergleiche()
    katalog = _katalog()
    zeilen, gesehen = [], set()
    for v in vs:
        if v.art == "vs_py" or (v.kpi_id, v.art) in gesehen:
            continue
        gesehen.add((v.kpi_id, v.art))
        zeilen.append({"kpi_id": v.kpi_id, "scenario": "target" if v.art == "vs_target" else "plan",
                       "measure": v.measure, "angabe_als": _angabe_als(v.kpi_id, katalog),
                       "gilt_ab": "", "gilt_bis": "", "wert": ""})
    return sorted(zeilen, key=lambda z: (z["kpi_id"], z["scenario"]))


def schreibe_vorlage(pfad: Path) -> int:
    import csv
    zeilen = vorlage_zeilen()
    with open(pfad, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=VORLAGE_SPALTEN, delimiter=";")
        w.writeheader()
        w.writerows(zeilen)
    return len(zeilen)


def _monatsenden(ab: str, bis: str) -> list[int]:
    import calendar
    m = re.fullmatch(r"(\d{4})-(\d{2})", ab or ""), re.fullmatch(r"(\d{4})-(\d{2})", bis or "")
    if not all(m):
        raise ValueError(f"gilt_ab/gilt_bis als JJJJ-MM erwartet, bekommen {ab!r}/{bis!r}")
    j, mo = int(m[0].group(1)), int(m[0].group(2))
    ende = (int(m[1].group(1)), int(m[1].group(2)))
    if (j, mo) > ende or not 1 <= mo <= 12 or not 1 <= ende[1] <= 12:
        raise ValueError(f"Zeitraum {ab}..{bis} ist leer oder ungueltig")
    out = []
    while (j, mo) <= ende:
        out.append(j * 10000 + mo * 100 + calendar.monthrange(j, mo)[1])
        j, mo = (j + 1, 1) if mo == 12 else (j, mo + 1)
    return out


def lies_vorlage(pfad: Path) -> list[tuple[str, str, int, float]]:
    """Ausgefuellte Vorlage -> Zeilen fuer fact_target. Bricht bei jedem Fehler ab, statt
    einen Teil zu laden: ein halb geladenes Ziel sieht im Report aus wie ein ganzes."""
    import csv
    katalog = _katalog()
    erlaubt = {(z["kpi_id"], z["scenario"]) for z in vorlage_zeilen()}
    fehler, out = [], []
    with open(pfad, encoding="utf-8", newline="") as f:
        for nr, z in enumerate(csv.DictReader(f, delimiter=";"), start=2):
            if not (z.get("wert") or "").strip():
                continue                                  # nicht ausgefuellt: kein Ziel, keine Linie
            kid, sz = (z.get("kpi_id") or "").strip(), (z.get("scenario") or "").strip()
            if (kid, sz) not in erlaubt:
                fehler.append(f"Zeile {nr}: {kid}/{sz} wird von keinem Report verglichen")
                continue
            try:
                wert = float(z["wert"].replace(",", "."))
                keys = _monatsenden(z.get("gilt_ab", "").strip(), z.get("gilt_bis", "").strip())
            except ValueError as exc:
                fehler.append(f"Zeile {nr}: {exc}")
                continue
            fmt = str((katalog[kid].get("business") or {}).get("unit_format") or "")
            if fmt.startswith("percent") and abs(wert) > 1.5:
                fehler.append(f"Zeile {nr}: {kid} ist ein Anteil, {wert} sieht nach Prozentpunkten aus "
                              f"(85 % als 0.85 angeben)")
                continue
            out += [(kid, sz, k, wert) for k in keys]
    doppelt = {(k, s, d) for k, s, d, _ in out if sum(1 for x in out if x[:3] == (k, s, d)) > 1}
    fehler += [f"{k}/{s}: Monat {d} doppelt belegt" for k, s, d in sorted(doppelt)]
    if fehler:
        raise ValueError("Vorlage nicht geladen:\n  " + "\n  ".join(fehler))
    return out


def lade_vorlage(pfad: Path, ziel: Path = GOLD_ZIEL) -> int:
    import pyarrow as pa
    import pyarrow.parquet as pq
    zeilen = lies_vorlage(pfad)
    schema = pa.schema([("kpi_id", pa.string()), ("scenario", pa.string()),
                        ("DateKey", pa.int64()), ("Target Value", pa.float64())])
    spalten = list(zip(*zeilen)) if zeilen else [[], [], [], []]
    tab = pa.table([pa.array(list(c), type=t.type) for c, t in zip(spalten, schema)], schema=schema)
    ziel.mkdir(parents=True, exist_ok=True)
    for alt in ziel.glob("*.parquet"):
        alt.unlink()
    pq.write_table(tab, ziel / "part-00000.parquet")
    return len(zeilen)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--vorlage", type=Path, help="CSV-Vorlage fuer Ziel- und Planwerte schreiben")
    ap.add_argument("--laden", type=Path, help="ausgefuellte Vorlage nach fact_target laden")
    ap.add_argument("--ziel", type=Path, default=GOLD_ZIEL, help="Gold-Ordner von fact_target")
    ap.add_argument("--blueprint", type=Path, default=None,
                    help="Bauplan des Mandanten; entscheidet den Speichermodus (D-590). "
                         "Ohne: keine Kapazitaet bekannt → Import (der Modus von dist/)")
    args = ap.parse_args(argv)
    if args.vorlage:
        print(f"{schreibe_vorlage(args.vorlage)} Zeilen -> {args.vorlage}")
        return 0
    if args.laden:
        try:
            print(f"{lade_vorlage(args.laden, args.ziel)} Monatswerte -> {args.ziel}")
        except ValueError as exc:
            print(exc, file=sys.stderr)
            return 1
        return 0
    from tooling.codegen.speichermodus import lade_bauplan, mandant_modus
    drift, luecken = pruefe(schreiben=args.write, modus=mandant_modus(lade_bauplan(args.blueprint)))
    for l in luecken:
        print(f"LUECKE  {l}")
    if not args.write:
        for d in drift:
            print(f"DRIFT   {d}")
    vs, _ = vergleiche()
    print(f"{len(vs)} Vergleiche, {len(luecken)} Luecken, {0 if args.write else len(drift)} abweichende Dateien")
    return 1 if drift and not args.write else 0


if __name__ == "__main__":
    sys.exit(main())
