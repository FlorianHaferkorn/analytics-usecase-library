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
- `basis: absolute | target` mit `reference: target` (Entscheidung Flo, 30.10.2026, ADR-0028
  Nachtrag) -- eine Abweichung vom Ziel: das Ziel-Measure ist die Plan-KPI des Katalogs
  (`plan_kpi_ref` der Trigger-KPI). `unit: '%' | pct` rechnet relativ (`[M] > Ziel * 1,05`),
  jede andere Einheit additiv (`[M] > Ziel + 2`). Ohne Ziel-Daten feuert die Stufe nicht.
- `basis: relative` -- eine relative Abweichung: `[M] > Basis * (1 + 10 %)`.
- `basis: band` -- ausserhalb `lower`..`upper`.
- Die Basis ist der Monatsdurchschnitt der KPI im `baseline_window` des Action-Codes
  (`impact_valuation.success_window.success_criteria.baseline_window`, etwa P90D) vor dem
  ersten Tag der Auswahl. Ohne Basis-Daten feuert die Stufe nicht.
- `unit: '%' | pp | pct` heisst: der Wert steht in Prozent (92.0 = 92 %).

Ausgewertet seit 23.09.2026 (R6.4b): `persistence` bei Monats-Granularitaet (die Bedingung
gilt auch in den n-1 Monaten vor dem letzten ausgewaehlten, per Monatsindex-Shift wie
'CCC Days PM', mit verschobener Basis) und
`volume_guardrail`, wo die Guardrail-KPI im Modell existiert. Nicht ausgewertet und im
Bericht benannt: Persistenz bei Wochen-/Tages-Granularitaet, Guardrails ohne Measure im
Modell, `gating_rules` (Prosa, keine Bedingung).

CLI:
    python -m tooling.codegen.action_trigger_dax            # Abweichungen melden (rc 1)
    python -m tooling.codegen.action_trigger_dax --write    # dist/ nachziehen

    # Opt-in Consumer-Export; schreibt niemals in das Modell:
    python -m tooling.codegen.action_trigger_dax --evidence-use-case COM-IND-R002 \\
        --evidence-model Commercial.SemanticModel --evidence-out <ordner>

Evidence exportiert ein Manifest und einen TMDL-Block für die vorhandene _Measures-Tabelle.
Das Manifest enthält repo-relative Quellpfade/-Hashes, Scope und exakte Maßnamen/-Hashes,
aber keine DAX-Ausdrücke. DAX-Hash: SHA-256 über UTF-8, CRLF/CR nach LF, außen strip().
``source.model_name`` ist der logische Name ohne ``.SemanticModel``; ``model_item_name``
behält den Verzeichnisnamen. Das beweist weder eine Veröffentlichung noch Tenant-Laufzeit.

``--evidence-bindings <json>`` nimmt explizite Proof-Measure-Bindungen je Action-Code an.
Jede Bindung enthält ``measure``, ``semantics`` (= Rollenschlüssel), ``action_code_id`` und
``use_case_id``. Rollen: observation_count, gating_met, period_start, period_end,
forecast_crossing, persistence_count_L1/L2/L3. Fehlende/ungültige Nachweise bleiben offen;
ein Prognosehorizont wird nie als Schwellenübertritt ausgegeben. Die Bindungen beschreiben
Modell-Semantik, keine stellvertretende Freigabe der Action oder ihrer Schwellen.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
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
EVIDENCE_UNITS = {
    "percent_1": ("%", .01), "percent_2": ("%", .01),
    "days_0": ("days", 1), "days_1": ("days", 1),
    "hours_0": ("hours", 1), "hours_1": ("hours", 1),
    "eur_0": ("EUR", 1), "eur_2": ("EUR", 1), "eur_per_unit_0": ("EUR/unit", 1),
    "ratio_1": ("ratio", 1), "ratio_2": ("ratio", 1), "count_0": ("count", 1),
    "units_0": ("units", 1), "index_signed_0": ("index", 1), "defects_per_1k_0": ("defects/1000", 1),
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
    nicht_ausgewertet: list[str] = field(default_factory=list)


def _kpi_formate() -> dict[str, str]:
    out = {}
    for f in sorted(KPIS.glob("*.yaml")):
        d = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        if d.get("kpi_id"):
            out[d["kpi_id"]] = (d.get("business") or {}).get("unit_format") or ""
    return out


def _kpi_plan() -> dict[str, str]:
    """Trigger-KPI -> governte Plan-KPI (Katalogfeld `plan_kpi_ref`), fuer `reference: target`."""
    out = {}
    for f in sorted(KPIS.glob("*.yaml")):
        d = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        if d.get("kpi_id") and d.get("plan_kpi_ref"):
            out[d["kpi_id"]] = d["plan_kpi_ref"]
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


def _schwellenwert(cond: dict, basis_var: str, fmt: str, ziel: str | None = None) -> str:
    """Numerische Grenze; Text-Auswerter und opt-in Evidence verwenden dieselbe Rechnung."""
    th, comp = cond.get("threshold") or {}, cond.get("comparator")
    art = th.get("basis")
    if th.get("value") is None:
        raise Fehler(f"Schwelle ohne Wert: {th}")
    if art == "relative":
        v = float(th["value"]) / 100.0
        faktor = {"gt": 1 + v, "gte": 1 + v, "lt": 1 - v, "lte": 1 - v}.get(comp)
        if faktor is None:
            raise Fehler(f"relativer Vergleich {comp!r} unbekannt")
        return f"{basis_var} * {_zahl(faktor)}"
    if art in ("absolute", "target") and th.get("reference") == "target":
        if ziel is None:
            raise Fehler(f"reference: target ohne Ziel-Measure: {th}")
        if comp not in ("gt", "gte", "lt", "lte"):
            raise Fehler(f"Vergleich {comp!r} gegen das Ziel unbekannt")
        if str(th.get("unit") or "").strip() in ("%", "pct"):
            v = float(th["value"]) / 100.0
            return f"{ziel} * {_zahl(1 + v if comp in ('gt', 'gte') else 1 - v)}"
        return f"{ziel} + {_zahl(_skaliert(th, 'value', fmt))}"
    if art in ("absolute", "target"):
        value = _zahl(_skaliert(th, "value", fmt))
        return f"{basis_var} + {value}" if th.get("reference") == "baseline" else value
    raise Fehler(f"basis {art!r} unbekannt")


def _bedingung(cond: dict, ref: str, basis_var: str, fmt: str, ziel: str | None = None) -> str:
    th = cond.get("threshold") or {}
    comp = cond.get("comparator")
    if th.get("basis") == "band":
        return f"{ref} < {_zahl(_skaliert(th, 'lower', fmt))} || {ref} > {_zahl(_skaliert(th, 'upper', fmt))}"
    grenze = _schwellenwert(cond, basis_var, fmt, ziel)
    schutz = (f"NOT ISBLANK ( {basis_var} ) && " if _braucht_basis(cond) else
              f"NOT ISBLANK ( {ziel} ) && " if th.get("reference") == "target" else "")
    if comp == "abs_gt":
        return f"{schutz}ABS ( {ref} ) > {grenze}"
    op = {"gt": ">", "gte": ">=", "lt": "<", "lte": "<="}.get(comp)
    if op is None:
        raise Fehler(f"Vergleich {comp!r} unbekannt")
    return f"{schutz}{ref} {op} {grenze}"


def _prognose_measure(code: str, trig: dict, definiert: set[str] | None) -> str:
    """Das Measure, dessen Wert die Stufen eines Forecast-Ausloesers pruefen (ADR-0028)."""
    fc = trig.get("forecast") or {}
    vergleich = fc.get("compare")
    band = fc.get("band") or {}
    name = {"point": fc.get("forecast_measure"), "band_lower": band.get("lower_measure"),
            "band_upper": band.get("upper_measure")}.get(vergleich)
    if not name:
        raise Fehler(f"{code}: Forecast ohne Measure fuer compare {vergleich!r}")
    if definiert is not None and name not in definiert:
        raise Fehler(f"{code}: Prognose-Measure {name!r} hat im Modell kein Measure")
    return name


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


def _ziel_measure(code: str, kid: str, plan_ref: dict[str, str], measure_name: dict[str, str],
                  definiert: set[str] | None) -> str:
    """Das Ziel-Measure fuer `reference: target`: die Plan-KPI des Katalogs zur Trigger-KPI."""
    pk = plan_ref.get(kid)
    if not pk:
        raise Fehler(f"{code}: reference: target, aber {kid} fuehrt keine plan_kpi_ref im Katalog")
    if pk not in measure_name or (definiert is not None and measure_name[pk] not in definiert):
        raise Fehler(f"{code}: Ziel-KPI {pk!r} hat im Modell kein Measure")
    return f"[{measure_name[pk]}]"


def _auswertung_fuer(ac: dict, measure_name: dict[str, str], formate: dict[str, str],
             definiert: set[str] | None = None,
             plan_ref: dict[str, str] | None = None) -> tuple[str, list[str], dict]:
    """Den Ausdruck fuer einen Action-Code und die Regeln, die er nicht auswertet.

    `definiert` sind die Measures, die das Zielmodell wirklich fuehrt. Die Namenskarte
    kennt jede Katalog-KPI, auch solche, die im Modell fehlen; ohne diesen Abgleich
    zeigte der Ausdruck ins Leere.
    """
    code = ac["id"]
    trig = ac.get("trigger") or {}
    prognose = _prognose_measure(code, trig, definiert) if trig.get("type") == "Forecast" else None
    levels = trig.get("levels") or {}
    if not all(isinstance(levels.get(L), dict) for L in ("L1", "L2", "L3")):
        raise Fehler(f"{code}: trigger.levels fuehrt nicht L1 bis L3")
    vars_, refs, basis, ziel, ziel_ref = [], {}, {}, {}, {}
    for L in ("L3", "L2", "L1"):
        kid = (levels[L].get("condition") or {}).get("metric_kpi_id")
        if kid not in measure_name or (definiert is not None and measure_name[kid] not in definiert):
            raise Fehler(f"{code} {L}: KPI {kid!r} hat im Modell kein Measure")
        if kid not in refs:
            refs[kid] = f"[{measure_name[kid]}]"
    fenster = ((((ac.get("impact_valuation") or {}).get("success_window") or {})
                .get("success_criteria") or {}).get("baseline_window"))
    if prognose and len(refs) > 1:
        raise Fehler(f"{code}: Forecast-Ausloeser mit mehr als einer KPI in den Stufen")
    for i, kid in enumerate(refs):
        # Forecast (ADR-0028): verglichen wird der Prognosewert zum Horizont; die Basis bleibt
        # der Ist-Verlauf der KPI.
        vars_.append(f"VAR _v{i} = {f'[{prognose}]' if prognose else refs[kid]}")
        if any(_braucht_basis(levels[L].get("condition") or {})
               and levels[L]["condition"].get("metric_kpi_id") == kid for L in levels):
            if not fenster:
                raise Fehler(f"{code}: relative Schwelle, aber kein baseline_window")
            vars_.append(f"VAR _b{i} = {_basis_ausdruck(refs[kid], _tage(fenster))}")
            basis[kid] = f"_b{i}"
        if any(((levels[L].get("condition") or {}).get("threshold") or {}).get("reference") == "target"
               and levels[L]["condition"].get("metric_kpi_id") == kid for L in levels):
            ziel_ref[kid] = _ziel_measure(code, kid, plan_ref or {}, measure_name, definiert)
            vars_.append(f"VAR _z{i} = {ziel_ref[kid]}")
            ziel[kid] = f"_z{i}"
    idx = {kid: i for i, kid in enumerate(refs)}
    steps = ((ac.get("operational_execution") or {}).get("steps")) or []
    schritte = (" & " + NL + " & ").join(_dax_str("→ " + " ".join(str(s).split())) for s in steps)

    def text(L: str, kid: str) -> str:
        fmt = FORMAT.get(formate.get(kid, ""))
        if fmt is None:
            raise Fehler(f"{code}: unit_format {formate.get(kid)!r} von {kid} ohne Formatregel")
        teile = [_dax_str(f"{SEVERITY[L]} — {code} — {ac.get('name', code)}"),
                 _dax_str(f"Owner: {ac.get('owner_role', '')} | " + ("Prognose " if prognose else ""))
                 + f" & FORMAT ( _v{idx[kid]}, {_dax_str(fmt)} )"]
        if schritte:
            teile.append(schritte)
        return (" & " + NL + " & ").join(teile)

    ev = ((ac.get("trigger") or {}).get("evaluation")) or {}
    offen = []

    # Persistenz: die Stufe gilt nur, wenn ihre Bedingung auch in den n-1 Vormonaten galt.
    # Umsetzbar nur fuer Monats-Granularitaet -- der Report filtert monatlich; eine Woche
    # um sieben Tage zu verschieben, waehrend ein Monat ausgewaehlt ist, prueft etwas anderes.
    pers = ev.get("persistence") or {}
    n = int(pers.get("min_consecutive_periods") or 1) if pers.get("required") else 1
    g = str(ev.get("grain") or "")
    monatlich = g == "month" or g.endswith("_month")
    if n > 1 and (not monatlich or prognose):
        # Fruehere Prognosestaende liegen nicht im Modell; die Vormonate des Ist-Werts zu pruefen,
        # pruefte etwas anderes als die Prognose.
        offen.append("persistence")
        n = 1

    def vormonate(cond: dict, kid: str, fmt: str) -> str:
        if n <= 1:
            return ""
        ref = refs[kid]
        b = f"( {_basis_ausdruck(ref, _tage(fenster))} )" if kid in basis else "BLANK ()"
        innen = _bedingung(cond, ref, b, fmt, ziel_ref.get(kid))
        # Monatsindex-Shift statt DATEADD, dasselbe Muster wie 'CCC Days PM' im Finance-Modell:
        # dim_date ist nicht als Datumstabelle markiert, ein Slicer auf CalendarYearMonth
        # bliebe neben DATEADD stehen und die Schnittmenge waere leer.
        return "".join(
            f" && CALCULATE ( {innen}, REMOVEFILTERS ( 'dim_date' ), FILTER ( ALL ( 'dim_date' ), "
            f"'dim_date'[Year] * 12 + 'dim_date'[MonthNumber] = _idx - {k} ) )"
            for k in range(1, n))

    # Mengen-Guardrail: unter der Mindestmenge ist die Abweichung Rauschen, keine Aktion.
    vg = (ev.get("minimum_data") or {}).get("volume_guardrail") or {}
    schutz = ""
    if vg.get("enabled"):
        gk = vg.get("metric_kpi_id")
        op = {"gte": ">=", "gt": ">", "lte": "<=", "lt": "<"}.get(vg.get("comparator"))
        if gk in measure_name and (definiert is None or measure_name[gk] in definiert) and op:
            schutz = f" && [{measure_name[gk]}] {op} {_zahl(float(vg['value']))}"
        else:
            offen.append("volume_guardrail")

    if n > 1:
        vars_.append("VAR _idx = MAX ( 'dim_date'[Year] ) * 12 + MAX ( 'dim_date'[MonthNumber] )")
    ausdruck = "BLANK ()"
    bedingungen = {}
    for L in ("L1", "L2", "L3"):              # von innen nach aussen: L3 wird zuerst geprueft
        cond = levels[L].get("condition") or {}
        kid = cond["metric_kpi_id"]
        fmt = formate.get(kid, "")
        bed = _bedingung(cond, f"_v{idx[kid]}", basis.get(kid, "BLANK ()"), fmt, ziel.get(kid))
        bed = f"( {bed} ){vormonate(cond, kid, fmt)}{schutz}"
        bedingungen[L] = bed
        ausdruck = f"IF ( {bed}, {text(L, kid)}, {ausdruck} )"
    if (ac.get("trigger") or {}).get("gating_rules"):
        offen.append("gating_rules")
    return " ".join(vars_) + " RETURN " + ausdruck, offen, {
        "vars": vars_, "refs": refs, "basis": basis, "ziel": ziel, "idx": idx,
        "bedingungen": bedingungen, "levels": levels,
    }


def dax_fuer(ac: dict, measure_name: dict[str, str], formate: dict[str, str],
             definiert: set[str] | None = None,
             plan_ref: dict[str, str] | None = None) -> tuple[str, list[str]]:
    """Bestehender Textvertrag, bytegleich; Evidence ist ausschließlich opt-in."""
    dax, offen, _ = _auswertung_fuer(ac, measure_name, formate, definiert, plan_ref)
    return dax, offen



EVIDENCE_SCHEMA_VERSION = "1.0.0"
EVIDENCE_EVALUATOR_VERSION = "1"


def _quelle(path: Path) -> tuple[dict, dict]:
    resolved = path.resolve()
    try:
        relative = resolved.relative_to(REPO.resolve()).as_posix()
    except ValueError:
        raise Fehler("Evidence-Quelle muss im ALUCA-Repository liegen") from None
    raw = resolved.read_bytes()
    return yaml.safe_load(raw.decode("utf-8")), {"path": relative, "sha256": hashlib.sha256(raw).hexdigest()}


def evidence_fuer(ac: dict, measure_name: dict[str, str], formate: dict[str, str], *,
                 action_code_path: Path, bracket_path: Path,
                 definiert: set[str] | None = None, plan_ref: dict[str, str] | None = None,
                 period_start_measure: str | None = None, period_end_measure: str | None = None,
                 forecast_period_measure: str | None = None,
                 proof_bindings: dict | None = None) -> dict:
    """Opt-in Evidence-Maßsatz und portables Manifest; kein zweiter Trigger-Auswerter.

    Quellen müssen dem Payload entsprechen, und der Bracket muss den Code explizit binden.
    Unbewiesene Bedingungen sperren Evaluated/Fired/Level; Rohwerte bleiben zur Herleitung.
    """
    original, source_code = _quelle(action_code_path)
    bracket, source_bracket = _quelle(bracket_path)
    if original != ac:
        raise Fehler("Action-Code-Payload entspricht nicht der governten Quelle")
    code = ac["id"]
    if not bracket.get("id") or code not in (bracket.get("orchestration") or {}).get("action_code_ids", []):
        raise Fehler(f"{code}: keine explizite Action-Code-Bindung im Bracket")
    _, offen, ctx = _auswertung_fuer(ac, measure_name, formate, definiert, plan_ref)
    if len(ctx["refs"]) != 1:
        raise Fehler(f"{code}: Evidence braucht genau eine Trigger-KPI")
    kid = next(iter(ctx["refs"]))
    fmt = formate[kid]
    trig = ac["trigger"]
    level_conditions = {level: data["condition"] for level, data in ctx["levels"].items()}
    thresholds = {level: cond["threshold"] for level, cond in level_conditions.items()}
    common = {tuple(th.get(k) for k in ("basis", "reference", "unit")) for th in thresholds.values()}
    if len(common) != 1 or next(iter(common))[0] == "band":
        raise Fehler(f"{code}: Evidence v1 verlangt skalare Stufen mit gleicher Basis/Referenz/Einheit")
    if any(isinstance(th.get("value"), bool) or not isinstance(th.get("value"), (int, float))
           or not math.isfinite(th["value"]) for th in thresholds.values()):
        raise Fehler(f"{code}: Evidence-Schwellen müssen endliche Zahlen sein")
    index = ctx["idx"][kid]
    value = f"_v{index}"
    actual = ctx["refs"][kid]
    baseline = ctx["basis"].get(kid, "BLANK ()")
    target = ctx["ziel"].get(kid, "BLANK ()")
    unresolved = list(dict.fromkeys(offen))
    proof_bindings = {} if proof_bindings is None else proof_bindings
    if not isinstance(proof_bindings, dict):
        raise Fehler(f"{code}: Evidence-Proof-Bindungen müssen ein Objekt sein")
    allowed = {"observation_count", "gating_met", "period_start", "period_end", "forecast_crossing",
               "persistence_count_L1", "persistence_count_L2", "persistence_count_L3"}
    if set(proof_bindings) - allowed:
        raise Fehler(f"{code}: unbekannte Evidence-Proof-Bindung")
    proofs = {}
    for role, binding in proof_bindings.items():
        if (not isinstance(binding, dict) or binding.get("action_code_id") != code
                or binding.get("use_case_id") != bracket["id"] or binding.get("semantics") != role):
            raise Fehler(f"{code}: Proof-Bindung {role} braucht passenden Code, Scope und Semantik")
        name = binding.get("measure")
        if not isinstance(name, str) or definiert is None or name not in definiert:
            raise Fehler(f"{code}: Proof-Measure {name!r} nicht im Modell belegt")
        proofs[role] = "[" + name.replace("]", "]]") + "]"
    dynamic_reasons = []
    gates = []
    ev = trig.get("evaluation") or {}
    minimum = (ev.get("minimum_data") or {}).get("min_observations") or 0
    if minimum > 0:
        if "observation_count" not in proofs:
            unresolved.append("minimum_observations")
        else:
            count = proofs["observation_count"]
            dynamic_reasons.append(
                f'IF ( ISBLANK ( {count} ) || {count} < {minimum} || INT ( {count} ) <> {count}, '
                '"minimum_observations", BLANK () )')
    if "gating_rules" in unresolved and "gating_met" in proofs:
        unresolved.remove("gating_rules")
        gate = proofs["gating_met"]
        dynamic_reasons.append(f'IF ( ISBLANK ( {gate} ) || NOT ( {gate} IN {{ 0, 1 }} ), "gating_rules", BLANK () )')
        gates.append(f"{gate} = 1")
    # Persistenz ist stufenspezifisch. Ein gemeinsamer Zähler könnte L3 aus L1 ableiten.
    level_proofs = {}
    if "persistence" in unresolved and all(f"persistence_count_{level}" in proofs for level in ("L1", "L2", "L3")):
        unresolved.remove("persistence")
        required = int((ev.get("persistence") or {}).get("min_consecutive_periods") or 1)
        for level in ("L1", "L2", "L3"):
            count = proofs[f"persistence_count_{level}"]
            dynamic_reasons.append(
                f'IF ( ISBLANK ( {count} ) || {count} < 0 || INT ( {count} ) <> {count}, '
                f'"persistence_{level}", BLANK () )')
            level_proofs[level] = f" && {count} >= {required}"
    if any(cond.get("filters") for cond in level_conditions.values()):
        unresolved.append("condition_filters")
    selected_level = "BLANK ()"
    for level in ("L1", "L2", "L3"):
        condition = ctx["bedingungen"][level] + level_proofs.get(level, "")
        selected_level = f'IF ( {condition}, "{level}", {selected_level} )'
    if gates:
        selected_level = f'IF ( {" && ".join(gates)}, {selected_level}, BLANK () )'
    fired = f"NOT ISBLANK ( {selected_level} )"

    def explicit_date(name: str | None) -> str:
        if not name:
            return "BLANK ()"
        if definiert is None or name not in definiert:
            raise Fehler(f"{code}: explizites Datums-Measure {name!r} nicht im Modell belegt")
        return "[" + name.replace("]", "]]") + "]"

    period_start = proofs.get("period_start") or explicit_date(period_start_measure)
    period_end = proofs.get("period_end") or explicit_date(period_end_measure)
    forecast_period = proofs.get("forecast_crossing") or explicit_date(forecast_period_measure)
    if period_start == "BLANK ()" or period_end == "BLANK ()":
        unresolved.append("evaluation_period_unavailable")
    if trig.get("forecast") and forecast_period == "BLANK ()":
        unresolved.append("forecast_period_unavailable")
    reasons = [_dax_str(reason) for reason in dict.fromkeys(unresolved)]
    reasons.extend(dynamic_reasons)
    guardrail = (ev.get("minimum_data") or {}).get("volume_guardrail") or {}
    guardrail_name = measure_name.get(guardrail.get("metric_kpi_id"))
    if guardrail.get("enabled") and guardrail_name and "volume_guardrail" not in unresolved:
        guardrail_ref = "[" + guardrail_name.replace("]", "]]") + "]"
        reasons.append(f'IF ( ISBLANK ( {guardrail_ref} ), "volume_guardrail_missing", BLANK () )')
    reasons.append(f"IF ( ISBLANK ( {value} ), \"value_missing\", BLANK () )")
    if kid in ctx["basis"]:
        reasons.append(f"IF ( ISBLANK ( {baseline} ), \"baseline_missing\", BLANK () )")
    if kid in ctx["ziel"]:
        reasons.append(f"IF ( ISBLANK ( {target} ), \"target_missing\", BLANK () )")
    for name, expression in (("period_start_missing", period_start), ("period_end_missing", period_end)):
        if expression != "BLANK ()":
            reasons.append(f'IF ( ISBLANK ( {expression} ), "{name}", BLANK () )')
    if forecast_period != "BLANK ()":
        reasons.append(f'IF ( {fired} && ISBLANK ( {forecast_period} ), "forecast_period_missing", BLANK () )')
    if period_start != "BLANK ()" and period_end != "BLANK ()":
        reasons.append(f'IF ( {period_start} > {period_end}, "evaluation_period_invalid", BLANK () )')
    rows = ", ".join(f'ROW ( "reason", {reason} )' for reason in reasons)
    prelude = (" ".join(ctx["vars"]) +
               f' VAR _unresolved = FILTER ( UNION ( {rows}, ROW ( "reason", BLANK () ) ), NOT ISBLANK ( [reason] ) )')
    evaluated = "COUNTROWS ( _unresolved ) = 0"
    prefix = f"Action_{code}_Evidence_"
    measures = {}

    def add(suffix: str, expression: str, kind: str, format_string: str) -> None:
        dax = prelude + " RETURN " + expression
        canonical_dax = dax.replace("\r\n", "\n").replace("\r", "\n").strip().encode("utf-8")
        measures[suffix] = {"name": prefix + suffix, "data_type": kind,
                            "format_string": format_string, "dax": dax,
                            "dax_sha256": hashlib.sha256(canonical_dax).hexdigest()}

    for suffix, expression in (("Actual", actual), ("Value", value), ("Baseline", baseline), ("Target", target)):
        add(suffix, expression, "number", FORMAT[fmt])
    for level, cond in level_conditions.items():
        expression = _schwellenwert(cond, baseline, fmt, target if kid in ctx["ziel"] else None)
        reference = (baseline if _braucht_basis(cond) else
                     target if cond["threshold"].get("reference") == "target" else None)
        if reference:
            expression = f"IF ( NOT ISBLANK ( {reference} ), {expression}, BLANK () )"
        add(f"Threshold_{level}", expression, "number", FORMAT[fmt])
    add("Evaluated", f"IF ( {evaluated}, 1, 0 )", "integer", "0")
    add("Status", f'IF ( {evaluated}, "evaluated", "not_evaluable" )', "string", "")
    add("Fired", f"IF ( {evaluated}, IF ( {fired}, 1, 0 ), BLANK () )", "integer", "0")
    add("Level", f"IF ( {evaluated}, {selected_level}, BLANK () )", "string", "")
    add("UnresolvedConditions", '"[" & CONCATENATEX ( _unresolved, """" & [reason] & """", " , " ) & "]"',
        "json_string", "")
    add("PeriodStart", period_start, "date", "yyyy-MM-dd")
    add("PeriodEnd", period_end, "date", "yyyy-MM-dd")
    forecast = trig.get("forecast")
    if forecast:
        band = forecast.get("band") or {}
        for suffix, name in (("ForecastPoint", forecast.get("forecast_measure")),
                             ("ForecastLower", band.get("lower_measure")),
                             ("ForecastUpper", band.get("upper_measure"))):
            expression = f"[{name}]" if name and (definiert is None or name in definiert) else "BLANK ()"
            add(suffix, expression, "number", FORMAT[fmt])
        # Ein Horizont ist kein erster Schwellenübertritt. Ohne expliziten Beleg bleibt der Termin leer.
        add("ForecastPeriodStart", forecast_period, "date", "yyyy-MM-dd")
    if fmt not in EVIDENCE_UNITS:
        raise Fehler(f"{code}: unit_format {fmt!r} ohne Evidence-Einheit")
    value_unit, native_per_display = EVIDENCE_UNITS[fmt]
    first = thresholds["L1"]
    return {"schema_version": EVIDENCE_SCHEMA_VERSION, "action_code_id": code, "kpi_id": kid,
            "trigger_type": trig["type"], "action_status": ac.get("status"),
            "value_unit": value_unit, "value_unit_format": fmt,
            "value_native_per_display_unit": native_per_display,
            "threshold_basis": first["basis"], "threshold_reference": first.get("reference"),
            "threshold_unit": first.get("unit"), "thresholds": thresholds,
            "forecast": forecast, "scope": {"use_case_id": bracket["id"]},
            "source": {"action_code": source_code, "bracket": source_bracket,
                       "evaluator": "tooling.codegen.action_trigger_dax",
                       "evaluator_version": EVIDENCE_EVALUATOR_VERSION},
            "unresolved_conditions": list(dict.fromkeys(unresolved)),
            "period_sources": {"start_measure": period_start_measure, "end_measure": period_end_measure,
                               "forecast_crossing_measure": forecast_period_measure},
            "proof_bindings": proof_bindings, "measures": measures}


def evidence_manifest(evidence: list[dict]) -> dict:
    """Ein expliziter Maßsatz, kein automatischer Katalog-Rollout und kein Freigabenachweis."""
    if not evidence:
        raise Fehler("Evidence-Manifest braucht mindestens eine explizite Code-Bindung")
    keys = [(e["scope"]["use_case_id"], e["action_code_id"]) for e in evidence]
    if len(keys) != len(set(keys)):
        raise Fehler("Doppelte Scope/Action-Code-Bindung im Evidence-Manifest")
    ordered = sorted(evidence, key=lambda e: (e["scope"]["use_case_id"], e["action_code_id"]))
    return {"schema_version": EVIDENCE_SCHEMA_VERSION, "evaluator_version": EVIDENCE_EVALUATOR_VERSION,
            "action_evidence": [{**packet, "measures": {key: {k: v for k, v in measure.items() if k != "dax"}
                                  for key, measure in packet["measures"].items()}}
                                for packet in ordered]}


def evidence_tmdl(evidence: list[dict]) -> str:
    """Opt-in TMDL-Block für die vorhandene _Measures-Tabelle; Quelle im Manifest."""
    evidence_manifest(evidence)
    out = []
    seen = set()
    for packet in sorted(evidence, key=lambda e: (e["scope"]["use_case_id"], e["action_code_id"])):
        for entry in packet["measures"].values():
            if entry["name"] in seen:
                raise Fehler(f"Evidence-Maß doppelt: {entry['name']}")
            seen.add(entry["name"])
            name = entry["name"].replace("'", "''")
            purpose = (f"Governed action evidence {packet['action_code_id']}; "
                       f"{entry['data_type']}. Not an action approval.")
            out += [f"\t/// Purpose: {purpose}",
                    f"\tmeasure '{name}' = {entry['dax']}",
                    f"\t\tformatString: {entry['format_string'] or chr(34) + chr(34)}",
                    "\t\tdisplayFolder: 8_Actions\\Evidence",
                    "\t\tannotation ALUCA_Generated = action_trigger_evidence", ""]
    return "\n".join(out)


def _loader():
    tooling = REPO / "products" / "fabric" / "powerbi" / "tooling"
    for p in (str(REPO), str(tooling)):
        if p not in sys.path:
            sys.path.insert(0, p)
    from page_scaffold_generator.config_loader import ConfigLoader
    return ConfigLoader(REPO)


def schreibe_evidence(use_case_id: str, model_name: str, out_dir: Path,
                     proof_bindings: dict | None = None) -> dict:
    """Expliziter CLI-Schnitt: genau die gebundenen Codes, keine Standard-Modelländerung."""
    if Path(model_name).name != model_name:
        raise Fehler("Evidence-Modell muss ein Modellname unter dist sein")
    model = DIST / model_name
    if not model.is_dir():
        raise Fehler(f"Evidence-Modell fehlt: {model_name}")
    brackets = []
    for path in (REPO / "core/usecases").rglob("UseCase_Bracket.yaml"):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if data.get("id") == use_case_id:
            brackets.append((path, data))
    if len(brackets) != 1:
        raise Fehler(f"Evidence braucht genau einen governten Bracket {use_case_id!r}")
    bracket_path, bracket = brackets[0]
    ids = (bracket.get("orchestration") or {}).get("action_code_ids") or []
    if not ids:
        raise Fehler("Evidence-Bracket hat keine expliziten Action-Code-Referenzen")
    proof_bindings = {} if proof_bindings is None else proof_bindings
    if not isinstance(proof_bindings, dict) or set(proof_bindings) - set(ids):
        raise Fehler("Evidence-Proof-Bindungen müssen explizit gebundene Action-Codes referenzieren")
    loader = _loader()
    names = loader.measure_map_for_model(model)
    defined = set(loader._model_symbols_for_dir(model).measure_names)
    paths = {}
    for path in ACTION_CODES.glob("*/*.yaml"):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if data.get("id") in ids:
            if data["id"] in paths:
                raise Fehler("Action-Code-Quelle ist nicht eindeutig")
            paths[data["id"]] = (path, data)
    packets = []
    for code in ids:
        if code not in paths:
            raise Fehler(f"Evidence-Action-Code fehlt: {code}")
        path, ac = paths[code]
        packet = evidence_fuer(ac, names, _kpi_formate(), definiert=defined, plan_ref=_kpi_plan(),
                              action_code_path=path, bracket_path=bracket_path,
                              proof_bindings=proof_bindings.get(code))
        packet["source"]["model_name"] = model_name.removesuffix(".SemanticModel")
        packet["source"]["model_item_name"] = model_name
        packets.append(packet)
    manifest = evidence_manifest(packets)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "action_evidence.manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    (out_dir / "action_evidence.tmdl").write_text(evidence_tmdl(packets), encoding="utf-8", newline="\n")
    return manifest


def pruefe(schreiben: bool = False) -> list[Ergebnis]:
    loader, codes, formate, plan = _loader(), action_codes(), _kpi_formate(), _kpi_plan()
    out: list[Ergebnis] = []
    for model_dir in sorted(DIST.glob("*.SemanticModel")):
        tmdl = model_dir / "definition" / "tables" / "_Measures.tmdl"
        if not tmdl.exists():
            continue
        text = tmdl.read_text(encoding="utf-8")
        namen = loader.measure_map_for_model(model_dir)
        definiert = set(loader._model_symbols_for_dir(model_dir).measure_names)
        ersatz = {}
        for m in _MEASURE_LINE.finditer(text):
            e = Ergebnis(model_dir.name, m.group(2), m.group(3), alt=m.group(4))
            ac = codes.get(e.code)
            if e.code in NICHT_ABLEITBAR or f"{model_dir.name}:{e.code}" in NICHT_ABLEITBAR:
                e.nicht_ausgewertet = ["nicht_ableitbar"]
                out.append(e)
                continue
            try:
                if ac is None:
                    raise Fehler(f"kein Action-Code {e.code!r} in core/action_codes")
                e.neu, e.nicht_ausgewertet = dax_fuer(ac, namen, formate, definiert, plan)
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
    ap.add_argument("--evidence-use-case", help="Opt-in: kanonische Bracket-ID, kein KPI-Mapping")
    ap.add_argument("--evidence-model", help="Opt-in: Modellname unter dist")
    ap.add_argument("--evidence-out", type=Path, help="Opt-in: Ausgabeordner für Manifest und TMDL-Block")
    ap.add_argument("--evidence-bindings", type=Path,
                    help="Optional: JSON mit expliziten Proof-Measure-Bindungen je Action-Code")
    args = ap.parse_args(argv)
    evidence_args = (args.evidence_use_case, args.evidence_model, args.evidence_out)
    if any(arg is not None for arg in evidence_args) or args.evidence_bindings is not None:
        if not all(evidence_args) or args.write:
            ap.error("Evidence verlangt --evidence-use-case, --evidence-model, --evidence-out ohne --write")
        try:
            bindings = (json.loads(args.evidence_bindings.read_text(encoding="utf-8"))
                        if args.evidence_bindings else None)
            manifest = schreibe_evidence(args.evidence_use_case, args.evidence_model, args.evidence_out, bindings)
        except (Fehler, OSError, ValueError) as exc:
            print(f"Evidence nicht erzeugt: {exc}", file=sys.stderr)
            return 2
        print(f"Evidence: {len(manifest['action_evidence'])} explizite Code-Bindungen; keine Modelländerung")
        return 0
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
    print(f"{len(ergebnisse)} Action-Measures, {len(ergebnisse) - len(fehler)} erzeugbar, "
          f"{len(fehler)} Fehler, {0 if args.write else len(abweichend)} abweichend")
    return 1 if fehler or (abweichend and not args.write) else 0


if __name__ == "__main__":
    sys.exit(main())
