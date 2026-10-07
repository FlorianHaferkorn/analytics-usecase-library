"""Action-Trigger-DAX aus den Action-Codes -- die Schwelle hat genau eine Heimat.

Bis 23.09.2026 standen die Schwellen der `Action_<Code>_Text`-Measures als Literale in
einem einmaligen Patch-Skript. Gemessen gegen `core/action_codes/` widersprachen 13 von
39 dem governten Stand: andere KPI (O-O1.4: OEE statt Throughput), feste statt relativer
Schwelle (S-I1.1: DIO > 55 statt +10 % gegen die Basis), anderer Wert (F-C1.2: 33 statt
Basis + 3 Tage). Dieses Modul erzeugt den Ausdruck aus dem YAML; `--check` haelt die
ausgelieferten Modelle daran fest.

Lesart der Schwelle (Entscheidung Flo, 23.09.2026):

- `basis: absolute | target` ohne `reference` -- ein Pegel der KPI: `[M] < 0,97`.
- `basis: absolute` mit `reference: baseline` -- eine Abweichung von der Basis:
  `[M] > Basis + 3` (DSO um drei Tage schlechter).
- `basis: relative` -- eine relative Abweichung: `[M] > Basis * (1 + 10 %)`.
- `basis: band` -- ausserhalb `lower`..`upper`.
- Die Basis ist der Monatsdurchschnitt der KPI im `baseline_window` des Action-Codes
  (`impact_valuation.success_window.success_criteria.baseline_window`, etwa P90D) vor dem
  ersten Tag der Auswahl. Ohne Basis-Daten feuert die Stufe nicht.
- `unit: '%' | pp | pct` heisst: der Wert steht in Prozent (92.0 = 92 %).

Grain, Persistenz, Guardrail (R6.4b 23.09.2026, Wochen/Tage seit 07.10.2026):

- Der Zeit-Anteil des `evaluation.grain` (letztes Token: day | week | month) ist die Periode.
  Woche (ISO, Montag bis Sonntag) und Tag werden auf der eigenen Periode gerechnet: die
  Periode, die den letzten ausgewaehlten Tag enthaelt, per `'dim_date'[Date]`-Grenzen in VARs.
  Beim Monat bleibt Periode 0 die Auswahl des Berichts (er filtert monatlich).
- `persistence`: die Stufe gilt nur, wenn ihre Bedingung in den n-1 Perioden davor ebenfalls
  galt (n = `min_consecutive_periods`, die letzte Periode eingeschlossen). `window.unit` muss
  zum Grain passen, n <= `window.length`.
- `volume_guardrail` gilt je Periode (Mindestmenge des Slots), nicht nur fuer die Auswahl.
- Eine Periode ohne KPI-Wert loest nie aus (`NOT ISBLANK`): keine Daten sind keine Abweichung.
- Nicht ausgewertet, im Bericht je Code mit Grund (`Ergebnis.nicht_ausgewertet`): `grain_slot`
  (der Nicht-Zeit-Anteil, etwa lane x dc, wird nicht je Auspraegung iteriert; die Bedingung
  gilt im Filterkontext), `grain_zeit` (kein Zeit-Anteil oder `dim_date[Date]` fehlt),
  `persistence` (dann mit demselben Grund), Guardrails ohne Measure im Modell,
  `gating_rules` (Prosa, keine Bedingung).

CLI:
    python -m tooling.codegen.action_trigger_dax            # Abweichungen melden (rc 1)
    python -m tooling.codegen.action_trigger_dax --write    # dist/ nachziehen
    python -m tooling.codegen.action_trigger_dax --detail   # je Code die Gruende
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
DIST = REPO / "products" / "fabric" / "powerbi" / "dist"
ACTION_CODES = REPO / "core" / "action_codes"
KPIS = REPO / "core" / "kpi_catalog" / "kpis"

NL = "UNICHAR ( 10 )"
SEVERITY = {"L3": "\U0001f534 L3", "L2": "\U0001f7e0 L2", "L1": "\U0001f7e1 L1"}
PROZENT = {"%", "pp", "pct"}
FORMAT = {
    "percent_1": "0.0%", "percent_2": "0.00%", "days_0": "0", "days_1": "0.0", "hours_0": "0",
    "hours_1": "0.0", "eur_0": "€#,0", "eur_2": "€#,0.00", "eur_per_unit_0": "€#,0",
    "ratio_1": "0.0", "ratio_2": "0.00", "count_0": "#,0", "units_0": "#,0",
    "index_signed_0": "+0;-0", "defects_per_1k_0": "0.0",
}
# Codes, deren Stufen im YAML nur als Prosa stehen (`composite_rule.description`). Aus
# ihnen laesst sich keine Schwelle ableiten; der ausgelieferte Ausdruck bleibt unberuehrt
# und wird als nicht governt gemeldet. Grund und Datum sind Pflicht.
NICHT_ABLEITBAR = {
    "X-E3.2": ("CompositeDeviation, Stufen nur als Prosa; Schwellen 0,3/0,5/0,7 im Modell "
               "stehen in keinem Action-Code", "2026-09-23"),
    "X-E3.3": ("CompositeDeviation, Stufen nur als Prosa", "2026-09-23"),
    # Schluessel mit Modell: nur in diesem Modell nicht ableitbar.
    "Finance.SemanticModel:S-I1.2": (
        "Trigger-KPI KPI-SCM-001 fehlt im Finance-Modell (dort KPI-FIN-004); das Measure ist "
        "statischer Text und steht in keiner Active-Actions-Liste", "2026-09-23"),
}
_MEASURE_LINE = re.compile(r"^(\tmeasure '(Action_([^']+)_Text)' = )(.*)$", re.M)


class Fehler(ValueError):
    """Ein Action-Code, aus dem sich kein ehrlicher Ausdruck bauen laesst."""


@dataclass
class Ergebnis:
    modell: str
    measure: str
    code: str
    neu: str | None = None
    alt: str = ""
    fehler: str | None = None
    # Regel -> Grund, warum der Ausdruck sie nicht (oder nur teilweise) auswertet.
    nicht_ausgewertet: dict[str, str] = field(default_factory=dict)


def _kpi_formate() -> dict[str, str]:
    out = {}
    for f in sorted(KPIS.glob("*.yaml")):
        d = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        if d.get("kpi_id"):
            out[d["kpi_id"]] = (d.get("business") or {}).get("unit_format") or ""
    return out


def action_codes() -> dict[str, dict]:
    out = {}
    for f in sorted(ACTION_CODES.glob("*/*.yaml")):
        if f.name.endswith("_business_case.yaml"):
            continue
        d = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        if d.get("id"):
            out[d["id"]] = d
    return out


def _tage(iso: str) -> int:
    m = re.fullmatch(r"P(\d+)D", str(iso or ""))
    if not m:
        raise Fehler(f"baseline_window {iso!r} ist keine Tagesdauer (PnD)")
    return int(m.group(1))


def _dax_str(s: str) -> str:
    return '"' + s.replace('"', '""') + '"'


def _zahl(v: float) -> str:
    return f"{v:.10g}"


def _skaliert(th: dict, key: str, fmt: str) -> float:
    v = float(th[key])
    if str(th.get("unit") or "").strip() in PROZENT and fmt.startswith("percent"):
        return v / 100.0
    return v


def _bedingung(cond: dict, ref: str, basis_var: str, fmt: str) -> str:
    th = cond.get("threshold") or {}
    comp = cond.get("comparator")
    art = th.get("basis")
    if art == "band":
        return f"{ref} < {_zahl(_skaliert(th, 'lower', fmt))} || {ref} > {_zahl(_skaliert(th, 'upper', fmt))}"
    if th.get("value") is None:
        raise Fehler(f"Schwelle ohne Wert: {th}")
    if art == "relative":
        v = float(th["value"]) / 100.0          # relativ ist immer Prozent der Basis
        faktor = {"gt": 1 + v, "gte": 1 + v, "lt": 1 - v, "lte": 1 - v}.get(comp)
        if faktor is None:
            raise Fehler(f"relativer Vergleich {comp!r} unbekannt")
        grenze = f"{basis_var} * {_zahl(faktor)}"
        op = {"gt": ">", "gte": ">=", "lt": "<", "lte": "<="}[comp]
        return f"NOT ISBLANK ( {basis_var} ) && {ref} {op} {grenze}"
    if art in ("absolute", "target"):
        v = _skaliert(th, "value", fmt)
        if th.get("reference") == "baseline":
            grenze, schutz = f"{basis_var} + {_zahl(v)}", f"NOT ISBLANK ( {basis_var} ) && "
        else:
            grenze, schutz = _zahl(v), ""
        if comp == "abs_gt":
            return f"{schutz}ABS ( {ref} ) > {grenze}"
        op = {"gt": ">", "gte": ">=", "lt": "<", "lte": "<="}.get(comp)
        if op is None:
            raise Fehler(f"Vergleich {comp!r} unbekannt")
        return f"{schutz}{ref} {op} {grenze}"
    raise Fehler(f"basis {art!r} unbekannt")


def _braucht_basis(cond: dict) -> bool:
    th = cond.get("threshold") or {}
    return th.get("basis") == "relative" or th.get("reference") == "baseline"


def _basis_ausdruck(ref: str, tage: int) -> str:
    """Monatsdurchschnitt der KPI in den `tage` Tagen vor dem ersten Tag der Auswahl."""
    return (
        "VAR _ref = MIN ( 'dim_date'[Date] ) "
        "VAR _monate = CALCULATETABLE ( VALUES ( 'dim_date'[CalendarYearMonth] ), "
        f"REMOVEFILTERS ( 'dim_date' ), 'dim_date'[Date] >= _ref - {tage}, 'dim_date'[Date] < _ref ) "
        "RETURN AVERAGEX ( _monate, VAR _m = 'dim_date'[CalendarYearMonth] "
        f"RETURN CALCULATE ( {ref}, REMOVEFILTERS ( 'dim_date' ), 'dim_date'[CalendarYearMonth] = _m ) )"
    )


# Zeit-Anteil eines `evaluation.grain` (letztes Token): Laenge der Periode in Tagen, Monat
# ohne feste Laenge. Alles vor dem Zeit-Token ist der Slot (lane_dc_week -> lane, dc).
ZEIT = {"day": 1, "week": 7, "month": None}
_FENSTER_EINHEIT = {"days": "day", "weeks": "week", "months": "month"}
# Spalten, die die Periodenauswertung im Zielmodell braucht.
DATUM = "dim_date.Date"


def grain_teile(grain: str) -> tuple[str | None, list[str]]:
    """`lane_dc_week` -> ("week", ["lane", "dc"]); `promotion` -> (None, ["promotion"])."""
    teile = [t for t in str(grain or "").split("_") if t]
    if teile and teile[-1] in ZEIT:
        return teile[-1], teile[:-1]
    return None, teile


def _perioden_grenzen(zeit: str, n: int, eigene_periode: bool) -> list[str]:
    """VARs `_s<k>`/`_e<k>` (erster/letzter Tag der Periode k vor der letzten ausgewaehlten).

    Woche nach ISO (Montag bis Sonntag, wie `dim_date[Week]` = `%G-W%V`). Beim Monat bleibt
    Periode 0 die Auswahl des Berichts (er filtert monatlich); Grenzen braucht es dort erst
    ab Periode 1.
    """
    out = ["VAR _ende = MAX ( 'dim_date'[Date] )"]
    if zeit == "month":
        for k in range(1, n):
            out.append(f"VAR _s{k} = DATE ( YEAR ( _ende ), MONTH ( _ende ) - {k}, 1 )")
            out.append(f"VAR _e{k} = EOMONTH ( _s{k}, 0 )")
        return out
    tage = ZEIT[zeit]
    if eigene_periode:
        if zeit == "week":
            out.append("VAR _s0 = _ende - WEEKDAY ( _ende, 2 ) + 1")
            out.append("VAR _e0 = _s0 + 6")
        else:
            out.append("VAR _s0 = _ende")
            out.append("VAR _e0 = _ende")
    for k in range(1, n):
        out.append(f"VAR _s{k} = _s0 - {tage * k}")
        out.append(f"VAR _e{k} = _e0 - {tage * k}")
    return out


def _in_periode(ausdruck: str, k: int) -> str:
    return (f"CALCULATE ( {ausdruck}, REMOVEFILTERS ( 'dim_date' ), "
            f"'dim_date'[Date] >= _s{k}, 'dim_date'[Date] <= _e{k} )")


def dax_fuer(ac: dict, measure_name: dict[str, str], formate: dict[str, str],
             definiert: set[str] | None = None,
             spalten: set[str] | None = None) -> tuple[str, dict[str, str]]:
    """Den Ausdruck fuer einen Action-Code und die Regeln, die er nicht auswertet (mit Grund).

    `definiert` sind die Measures, die das Zielmodell wirklich fuehrt. Die Namenskarte
    kennt jede Katalog-KPI, auch solche, die im Modell fehlen; ohne diesen Abgleich
    zeigte der Ausdruck ins Leere. `spalten` sind die Spalten des Zielmodells als
    `tabelle.spalte`; `None` heisst ungeprueft (synthetische Tests).
    """
    code = ac["id"]
    trigger = ac.get("trigger") or {}
    levels = trigger.get("levels") or {}
    if not all(isinstance(levels.get(L), dict) for L in ("L1", "L2", "L3")):
        raise Fehler(f"{code}: trigger.levels fuehrt nicht L1 bis L3")
    refs: dict[str, str] = {}
    for L in ("L3", "L2", "L1"):
        kid = (levels[L].get("condition") or {}).get("metric_kpi_id")
        if kid not in measure_name or (definiert is not None and measure_name[kid] not in definiert):
            raise Fehler(f"{code} {L}: KPI {kid!r} hat im Modell kein Measure")
        if kid not in refs:
            refs[kid] = f"[{measure_name[kid]}]"
    idx = {kid: i for i, kid in enumerate(refs)}
    fenster = ((((ac.get("impact_valuation") or {}).get("success_window") or {})
                .get("success_criteria") or {}).get("baseline_window"))
    mit_basis = {kid for kid in refs
                 if any(_braucht_basis(levels[L].get("condition") or {})
                        and levels[L]["condition"].get("metric_kpi_id") == kid for L in levels)}
    if mit_basis and not fenster:
        raise Fehler(f"{code}: relative Schwelle, aber kein baseline_window")

    ev = trigger.get("evaluation") or {}
    offen: dict[str, str] = {}

    # --- Grain: Zeit-Anteil und Slot ------------------------------------------------------
    # Die Stufe wird je Periode des Grains geprueft (Woche, Tag, Monat). Der Slot (lane x dc)
    # wird nicht je Auspraegung iteriert: die Bedingung gilt im Filterkontext des Berichts.
    # Das ist eine Luecke und steht als Feld im Bericht, nicht still im Ausdruck.
    grain = str(ev.get("grain") or "")
    zeit, slot = grain_teile(grain)
    if slot:
        offen["grain_slot"] = (f"Slot {' x '.join(slot)} aus grain {grain!r} nicht je Auspraegung "
                               "ausgewertet; Bedingung gilt im Filterkontext des Berichts")
    if zeit is None:
        offen["grain_zeit"] = f"grain {grain!r} hat keinen Zeit-Anteil (day/week/month)"
    elif spalten is not None and DATUM not in spalten:
        offen["grain_zeit"] = f"Spalte {DATUM} fehlt im Modell; Periode {zeit} nicht abbildbar"
        zeit = None

    # --- Persistenz: die Stufe gilt nur, wenn sie in n Perioden in Folge gilt -------------
    pers = ev.get("persistence") or {}
    n = int(pers.get("min_consecutive_periods") or 1) if pers.get("required") else 1
    if n > 1:
        fe = ev.get("window") or {}
        einheit = str(fe.get("unit") or "periods")
        laenge = fe.get("length")
        if zeit is None:
            offen["persistence"] = offen["grain_zeit"]
        elif einheit != "periods" and _FENSTER_EINHEIT.get(einheit) != zeit:
            offen["persistence"] = f"window.unit {einheit!r} passt nicht zu grain {grain!r}"
        elif laenge is not None and n > int(laenge):
            offen["persistence"] = f"min_consecutive_periods {n} > window.length {laenge}"
        if "persistence" in offen:
            n = 1
    # Woche und Tag rechnen auch Periode 0 auf der eigenen Periode, nicht auf der Auswahl.
    eigene_periode = zeit in ("week", "day")
    if eigene_periode and mit_basis:
        raise Fehler(f"{code}: Basis ist ein Monatsdurchschnitt; gegen eine {zeit}-Periode "
                     "nicht vergleichbar (Basis je Periode nicht definiert)")

    # --- Mengen-Guardrail: je Periode, unter der Mindestmenge ist es Rauschen -------------
    vg = (ev.get("minimum_data") or {}).get("volume_guardrail") or {}
    guard = None
    if vg.get("enabled"):
        gk = vg.get("metric_kpi_id")
        op = {"gte": ">=", "gt": ">", "lte": "<=", "lt": "<"}.get(vg.get("comparator"))
        if gk in measure_name and (definiert is None or measure_name[gk] in definiert) and op:
            guard = (f"[{measure_name[gk]}]", op, _zahl(float(vg["value"])))
        else:
            offen["volume_guardrail"] = (f"Guardrail-KPI {gk!r} hat im Modell kein Measure"
                                         if op else f"Vergleich {vg.get('comparator')!r} unbekannt")

    # --- Variablen: Grenzen, dann Werte je Periode ---------------------------------------
    vars_: list[str] = []
    if eigene_periode or n > 1:
        vars_ += _perioden_grenzen(zeit, n, eigene_periode)

    def wert(ausdruck: str, k: int) -> str:
        return _in_periode(ausdruck, k) if (k > 0 or eigene_periode) else ausdruck

    def suffix(k: int) -> str:
        return f"_{k}" if k else ""

    for kid, i in idx.items():
        for k in range(n):
            vars_.append(f"VAR _v{i}{suffix(k)} = {wert(refs[kid], k)}")
            if kid in mit_basis:
                # geklammert: der Basis-Ausdruck hat eigene VARs und ein eigenes RETURN
                b = f"( {_basis_ausdruck(refs[kid], _tage(fenster))} )"
                vars_.append(f"VAR _b{i}{suffix(k)} = {wert(b, k)}")
    if guard:
        for k in range(n):
            vars_.append(f"VAR _g{suffix(k)} = {wert(guard[0], k)}")

    steps = ((ac.get("operational_execution") or {}).get("steps")) or []
    schritte = (" & " + NL + " & ").join(_dax_str("→ " + " ".join(str(s).split())) for s in steps)
    periode = {"week": " & \" (week of \" & FORMAT ( _s0, \"yyyy-mm-dd\" ) & \")\"",
               "day": " & \" (\" & FORMAT ( _s0, \"yyyy-mm-dd\" ) & \")\""}.get(zeit, "") \
        if eigene_periode else ""

    def text(L: str, kid: str) -> str:
        fmt = FORMAT.get(formate.get(kid, ""))
        if fmt is None:
            raise Fehler(f"{code}: unit_format {formate.get(kid)!r} von {kid} ohne Formatregel")
        teile = [_dax_str(f"{SEVERITY[L]} — {code} — {ac.get('name', code)}"),
                 _dax_str(f"Owner: {ac.get('owner_role', '')} | ")
                 + f" & FORMAT ( _v{idx[kid]}, {_dax_str(fmt)} ){periode}"]
        if schritte:
            teile.append(schritte)
        return (" & " + NL + " & ").join(teile)

    ausdruck = "BLANK ()"
    for L in ("L1", "L2", "L3"):              # von innen nach aussen: L3 wird zuerst geprueft
        cond = levels[L].get("condition") or {}
        kid = cond["metric_kpi_id"]
        fmt = formate.get(kid, "")
        teile = []
        for k in range(n):
            v = f"_v{idx[kid]}{suffix(k)}"
            b = f"_b{idx[kid]}{suffix(k)}" if kid in mit_basis else "BLANK ()"
            t = f"NOT ISBLANK ( {v} ) && ( {_bedingung(cond, v, b, fmt)} )"
            if guard:
                t += f" && _g{suffix(k)} {guard[1]} {guard[2]}"
            teile.append(f"( {t} )")
        ausdruck = f"IF ( {' && '.join(teile)}, {text(L, kid)}, {ausdruck} )"
    if trigger.get("gating_rules"):
        offen["gating_rules"] = "Prosa, keine auswertbare Bedingung"
    return " ".join(vars_) + " RETURN " + ausdruck, offen


def _loader():
    tooling = REPO / "products" / "fabric" / "powerbi" / "tooling"
    for p in (str(REPO), str(tooling)):
        if p not in sys.path:
            sys.path.insert(0, p)
    from page_scaffold_generator.config_loader import ConfigLoader
    return ConfigLoader(REPO)


def pruefe(schreiben: bool = False) -> list[Ergebnis]:
    loader, codes, formate = _loader(), action_codes(), _kpi_formate()
    out: list[Ergebnis] = []
    for model_dir in sorted(DIST.glob("*.SemanticModel")):
        tmdl = model_dir / "definition" / "tables" / "_Measures.tmdl"
        if not tmdl.exists():
            continue
        text = tmdl.read_text(encoding="utf-8")
        namen = loader.measure_map_for_model(model_dir)
        sym = loader._model_symbols_for_dir(model_dir)
        definiert = set(sym.measure_names)
        spalten = {f"{t}.{c}" for t, tab in sym.tables.items() for c in tab.columns}
        ersatz = {}
        for m in _MEASURE_LINE.finditer(text):
            e = Ergebnis(model_dir.name, m.group(2), m.group(3), alt=m.group(4))
            ac = codes.get(e.code)
            ausnahme = NICHT_ABLEITBAR.get(f"{model_dir.name}:{e.code}") or NICHT_ABLEITBAR.get(e.code)
            if ausnahme:
                e.nicht_ausgewertet = {"nicht_ableitbar": ausnahme[0]}
                out.append(e)
                continue
            try:
                if ac is None:
                    raise Fehler(f"kein Action-Code {e.code!r} in core/action_codes")
                e.neu, e.nicht_ausgewertet = dax_fuer(ac, namen, formate, definiert, spalten)
            except Fehler as exc:
                e.fehler = str(exc)
            out.append(e)
            if e.neu is not None and e.neu != e.alt:
                ersatz[m.group(2)] = e.neu
        if schreiben and ersatz:
            neu = _MEASURE_LINE.sub(lambda m: m.group(1) + ersatz.get(m.group(2), m.group(4)), text)
            tmdl.write_text(neu, encoding="utf-8", newline="\n")
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--write", action="store_true", help="dist/ nachziehen")
    ap.add_argument("--detail", action="store_true", help="je Code die nicht ausgewerteten Regeln mit Grund")
    args = ap.parse_args(argv)
    ergebnisse = pruefe(schreiben=args.write)
    abweichend = [e for e in ergebnisse if e.neu is not None and e.neu != e.alt]
    fehler = [e for e in ergebnisse if e.fehler]
    for e in fehler:
        print(f"FEHLER  {e.modell} {e.measure}: {e.fehler}")
    if not args.write:
        for e in abweichend:
            print(f"DRIFT   {e.modell} {e.measure}")
    offen: dict[str, list[str]] = {}
    for e in ergebnisse:
        for r in e.nicht_ausgewertet:
            offen.setdefault(r, []).append(e.code)
    for r, cs in sorted(offen.items()):
        print(f"NICHT AUSGEWERTET  {r}: {len(cs)} Codes")
    if args.detail:
        for e in ergebnisse:
            for r, grund in sorted(e.nicht_ausgewertet.items()):
                print(f"  {e.modell} {e.code} {r}: {grund}")
    print(f"{len(ergebnisse)} Action-Measures, {len(ergebnisse) - len(fehler)} erzeugbar, "
          f"{len(fehler)} Fehler, {0 if args.write else len(abweichend)} abweichend")
    return 1 if fehler or (abweichend and not args.write) else 0


if __name__ == "__main__":
    sys.exit(main())
