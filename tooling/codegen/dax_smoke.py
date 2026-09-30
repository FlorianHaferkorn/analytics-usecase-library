"""DAX-Laufzeitprüfung, deterministisch aus den Modellen abgeleitet (AP-4, 24.09.2026).

Die Generatoren prüfen, dass jede Measure **geschrieben** ist. Ob sie im Service **rechnet**,
sagt nur ein Lauf gegen das veröffentlichte Modell. Dieses Modul trennt beides:

* `plan` (ohne Tenant, `--check`/`--write`): je Measure zwei Abfragen und eine Erwartung,
  geschrieben nach `products/fabric/powerbi/dax_smoke/<Modell>.json`.

  - `gesamt`: `EVALUATE ROW("v", [M])` -- rechnet die Measure ohne Filter?
  - `je_monat`: `EVALUATE SUMMARIZECOLUMNS('dim_date'[Year], 'dim_date'[MonthNumber], "v", [M])`.
    **Eine Measure je Abfrage**: mehrere Measures in einer `SUMMARIZECOLUMNS` liefern still
    Nullen (Freelancing CLAUDE.md, Belegpflicht Punkt 2).

  Erwartungsklassen: `zahl` (mindestens ein Monat gefüllt), `text` (Format `@`; leer erlaubt,
  wenn keine Aktion auslöst), `leer_begruendet` (hängt direkt oder über andere Measures an einer
  Tabelle, die im Demo absichtlich leer ist -- heute nur `fact_target`).

  Dazu je Beziehung aus `definition/relationships*.tmdl` eine RI-Abfrage (I-21 W5.12 b):
  `EVALUATE ROW("v", COUNTROWS(EXCEPT(DISTINCT(f[fk]), DISTINCT(d[key]))) + 0)`, erwartet 0.
  Ein verwaister Schlüssel zeigt sich im Bericht als Blank-Zeile der Dimension. `DISTINCT`, nicht
  `VALUES`: `VALUES` enthielte genau diese Blank-Zeile und verdeckte den Befund. `+ 0`, weil
  `COUNTROWS` einer leeren Tabelle BLANK liefert. Ein leerer Fremdschlüssel zählt mit (er landet
  ebenfalls auf der Blank-Zeile) -- anders als `check_data_model.py` ORPHAN-FK, das `None`
  verwirft. Diese Prüfung ist die zweite Messung zu ORPHAN-FK: dort Gold-Parquet, hier das
  veröffentlichte Modell nach dem Refresh.

* `gegenprobe` (ohne Tenant): für jede Measure der Form `SUM ( tabelle[spalte] )` rechnet pandas
  denselben Wert aus der Datenscheibe (AP-3). Das ist die zweite, unabhängige Messung.

* `run` (mit Tenant): führt den Plan über die Execute-Queries-REST-API aus. Token aus
  `POWERBI_ACCESS_TOKEN`, nie in Dateien oder Logs. Ohne Token oder Dataset: Exit 2.

* `bewerten`: stellt Laufergebnis, Erwartung und Gegenprobe nebeneinander. Exit 0/1/2.

    python -m tooling.codegen.dax_smoke plan            # --check
    python -m tooling.codegen.dax_smoke plan --write
    python -m tooling.codegen.dax_smoke gegenprobe --slice /tmp/gold_slice --out erwartet.json
    python -m tooling.codegen.dax_smoke run --model Operations.SemanticModel \\
        --workspace <id> --dataset <id> --out lauf.json
    python -m tooling.codegen.dax_smoke bewerten --lauf lauf.json --erwartet erwartet.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Callable

REPO = Path(__file__).resolve().parents[2]
DIST = REPO / "products" / "fabric" / "powerbi" / "dist"
PLAN = REPO / "products" / "fabric" / "powerbi" / "dax_smoke"

# Tabellen, die im Demo absichtlich leer sind. Begründung steht beim Eintrag, nicht im Kopf.
ABSICHTLICH_LEER = {
    "fact_target": "Zielwerte liefert der Kunde (R6.1b); im Demo leer, Schema vorhanden",
}

_MEASURE = re.compile(r"^\tmeasure (?:'((?:[^']|'')+)'|([^\s=]+)) =", re.M)
_REF = re.compile(r"(?<![\w\]'])\[([^\]]+)\]")
_SUM = re.compile(r"^SUM \( *([A-Za-z_]\w*)\[([^\]]+)\] *\)$")
_ORDNER = re.compile(r'GoldDataPath & "/((?:dimensions|facts)/\w+)"')


def _dax_name(name: str) -> str:
    return "[" + name.replace("]", "]]") + "]"


def _bloecke(text: str) -> list[str]:
    return re.split(r"\n(?=\t(?:///|measure |column |partition |hierarchy ))", text)


def measures(modell: Path) -> dict[str, dict]:
    """Name → {tabelle, ausdruck, format}. Liest alle Tabellen, nicht nur `_Measures`."""
    out: dict[str, dict] = {}
    for f in sorted((modell / "definition" / "tables").glob("*.tmdl")):
        for block in _bloecke(f.read_text(encoding="utf-8")):
            m = _MEASURE.search(block)
            if not m:
                continue
            name = (m.group(1) or m.group(2)).replace("''", "'")
            koerper = [z for z in block.split("\n")
                       if not re.match(r"^\t\t(formatString|displayFolder|lineageTag|annotation|dataCategory|isHidden)\b", z)
                       and not z.startswith("\t///")]
            fs = re.search(r"^\t\tformatString: (.*)$", block, re.M)
            ausdruck = "\n".join(koerper)
            ausdruck = ausdruck.split("=", 1)[1].strip() if "=" in ausdruck else ""
            out[name] = {"tabelle": f.stem, "ausdruck": ausdruck,
                         "format": fs.group(1).strip().strip('"') if fs else None}
    return out


def _haengt_an_leerer_tabelle(name: str, alle: dict[str, dict], gesehen: set[str] | None = None) -> str | None:
    gesehen = gesehen or set()
    if name in gesehen or name not in alle:
        return None
    gesehen.add(name)
    ausdruck = alle[name]["ausdruck"]
    for tabelle in ABSICHTLICH_LEER:
        if re.search(rf"(?<![\w']){tabelle}\b", ausdruck):
            return tabelle
    for ref in _REF.findall(ausdruck):
        treffer = _haengt_an_leerer_tabelle(ref, alle, gesehen)
        if treffer:
            return treffer
    return None


def _ordner_je_tabelle(modell: Path) -> dict[str, str]:
    out = {}
    for f in (modell / "definition" / "tables").glob("*.tmdl"):
        m = _ORDNER.search(f.read_text(encoding="utf-8"))
        if m:
            out[f.stem] = m.group(1)
    return out


def _quellspalte(modell: Path, tabelle: str, spalte: str) -> str | None:
    f = modell / "definition" / "tables" / f"{tabelle}.tmdl"
    if not f.is_file():
        return None
    for block in _bloecke(f.read_text(encoding="utf-8")):
        m = re.match(r"^\tcolumn (?:'((?:[^']|'')+)'|(\S+))", block.lstrip("\n"))
        if m and (m.group(1) or m.group(2)).replace("''", "'") == spalte:
            q = re.search(r"^\t\tsourceColumn: (.*)$", block, re.M)
            return q.group(1).strip() if q else None
    return None


_REL_SPALTE = re.compile(r"^(?:'((?:[^']|'')+)'|([^.'\s]+))\.(?:'((?:[^']|'')+)'|(\S+))$")


def _rel_spalte(wert: str) -> tuple[str, str] | None:
    m = _REL_SPALTE.match(wert.strip())
    if not m:
        return None
    return ((m.group(1) or m.group(2)).replace("''", "'"), (m.group(3) or m.group(4)).replace("''", "'"))


def _dax_spalte(tabelle: str, spalte: str) -> str:
    return "'" + tabelle.replace("'", "''") + "'" + _dax_name(spalte)


def beziehungen(modell: Path) -> list[dict]:
    """Beziehungen aus `definition/relationships.tmdl` oder `definition/relationships/*.tmdl`.

    `von` ist die n-Seite (Fakt, Fremdschlüssel), `nach` die 1-Seite (Dimension, Schlüssel).
    m:n-Beziehungen (`toCardinality: many`) haben keine Schlüsselseite und bekommen keine
    RI-Abfrage; heute kommt keine vor.
    """
    d = modell / "definition"
    dateien = sorted((d / "relationships").glob("*.tmdl")) + (
        [d / "relationships.tmdl"] if (d / "relationships.tmdl").is_file() else [])
    out = []
    for f in dateien:
        for block in re.split(r"\n(?=relationship )", f.read_text(encoding="utf-8")):
            kopf = re.match(r"^relationship (?:'((?:[^']|'')+)'|(\S+))", block.lstrip("\n"))
            von = re.search(r"^\tfromColumn: (.+)$", block, re.M)
            nach = re.search(r"^\ttoColumn: (.+)$", block, re.M)
            if not (kopf and von and nach):
                continue
            if re.search(r"^\ttoCardinality: many\s*$", block, re.M):
                continue
            v, n = _rel_spalte(von.group(1)), _rel_spalte(nach.group(1))
            if not (v and n):
                continue
            out.append({
                "name": (kopf.group(1) or kopf.group(2)).replace("''", "'"),
                "von": f"{v[0]}[{v[1]}]", "nach": f"{n[0]}[{n[1]}]",
                "aktiv": not re.search(r"^\tisActive: false\s*$", block, re.M),
                "abfrage": ('EVALUATE ROW("v", COUNTROWS(EXCEPT(DISTINCT(' + _dax_spalte(*v)
                            + "), DISTINCT(" + _dax_spalte(*n) + "))) + 0)"),
                "erwartet": 0,
            })
    return sorted(out, key=lambda b: b["name"])


def plan_fuer(modell: Path) -> dict:
    alle = measures(modell)
    rel = beziehungen(modell)
    ordner = _ordner_je_tabelle(modell)
    messungen, gegenproben = [], []
    for name in sorted(alle):
        leer = _haengt_an_leerer_tabelle(name, alle)
        if leer:
            klasse, grund = "leer_begruendet", f"{leer}: {ABSICHTLICH_LEER[leer]}"
        elif alle[name]["format"] == "@":
            klasse, grund = "text", "Textmeasure; leer erlaubt, wenn nichts auslöst"
        else:
            klasse, grund = "zahl", "mindestens ein Monat gefüllt"
        n = _dax_name(name)
        messungen.append({
            "measure": name, "tabelle": alle[name]["tabelle"], "klasse": klasse, "grund": grund,
            "abfragen": {
                "gesamt": f'EVALUATE ROW("v", {n})',
                "je_monat": f"EVALUATE SUMMARIZECOLUMNS('dim_date'[Year], 'dim_date'[MonthNumber], \"v\", {n})",
            },
        })
        s = _SUM.match(alle[name]["ausdruck"])
        if s and klasse == "zahl" and s.group(1) in ordner:
            quelle = _quellspalte(modell, s.group(1), s.group(2))
            if quelle:
                gegenproben.append({"measure": name, "ordner": ordner[s.group(1)], "spalte": quelle})
    quelle = hashlib.sha256(json.dumps({"measures": {k: alle[k] for k in sorted(alle)},
                                        "beziehungen": rel}, sort_keys=True,
                                       ensure_ascii=False).encode()).hexdigest()
    return {"modell": modell.name, "quelle_sha256": quelle, "messungen": messungen,
            "gegenproben": gegenproben, "beziehungen": rel}


def _json(wert) -> str:
    return json.dumps(wert, indent=2, ensure_ascii=False) + "\n"


def pruefe_plan(schreiben: bool = False) -> list[str]:
    drift = []
    for m in sorted(DIST.glob("*.SemanticModel")):
        ziel = PLAN / f"{m.name.removesuffix('.SemanticModel')}.json"
        neu = _json(plan_fuer(m))
        if not ziel.is_file() or ziel.read_text(encoding="utf-8") != neu:
            drift.append(ziel.name)
            if schreiben:
                ziel.parent.mkdir(parents=True, exist_ok=True)
                ziel.write_text(neu, encoding="utf-8", newline="\n")
    return drift


# ------------------------------------------------------------------ Gegenprobe (pandas)

def gegenprobe(slice_root: Path) -> dict:
    """Summen aus der Datenscheibe, je Modell und Measure. Unabhängig vom DAX-Motor.

    Fehlt die Quellspalte in den Dateien, ist das kein Wert, sondern ein Befund
    (`spalte_fehlt`): das Modell liest dann eine Spalte, die es nicht gibt. Gemessen am
    24.09.2026, als genau das `fact_sales[Sales Units]` im SupplyChain-Modell traf.
    """
    import pyarrow.parquet as pq
    werte: dict[str, float] = {}
    fehlt: list[str] = []
    for f in sorted(PLAN.glob("*.json")):
        plan = json.loads(f.read_text(encoding="utf-8"))
        for g in plan["gegenproben"]:
            dateien = sorted((slice_root / g["ordner"]).glob("*.parquet"))
            key = f'{plan["modell"]}::{g["measure"]}'
            if not dateien:
                continue
            if any(g["spalte"] not in pq.read_schema(str(d)).names for d in dateien):
                fehlt.append(f'{key} ({g["ordner"]}[{g["spalte"]}])')
                continue
            summe = sum(pq.read_table(str(d), columns=[g["spalte"]])[g["spalte"]].to_pandas().sum()
                        for d in dateien)
            werte[key] = float(summe)
    return {"werte": werte, "spalte_fehlt": fehlt}


# ------------------------------------------------------------------ Lauf (Tenant)

Transport = Callable[[str, dict, dict], dict]


def _http(url: str, kopf: dict, koerper: dict) -> dict:
    from urllib.request import Request, urlopen
    req = Request(url, data=json.dumps(koerper).encode(), headers=kopf, method="POST")
    with urlopen(req, timeout=120) as r:                                     # noqa: S310
        return json.loads(r.read().decode("utf-8"))


def lauf(plan: dict, workspace: str, dataset: str, token: str, *, budget: int = 1000,
         transport: Transport = _http) -> dict:
    url = (f"https://api.powerbi.com/v1.0/myorg/groups/{workspace}/datasets/{dataset}"
           "/executeQueries")
    kopf = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    ergebnisse, genutzt = [], 0
    for m in plan["messungen"]:
        eintrag = {"measure": m["measure"]}
        for art, abfrage in m["abfragen"].items():
            if genutzt >= budget:
                eintrag[art] = {"status": "budget"}
                continue
            genutzt += 1
            try:
                antwort = transport(url, kopf, {"queries": [{"query": abfrage}],
                                                "serializerSettings": {"includeNulls": True}})
                zeilen = antwort["results"][0]["tables"][0].get("rows", [])
                eintrag[art] = {"status": "ok", "werte": [z.get("[v]") for z in zeilen]}
            except Exception as exc:                                        # noqa: BLE001
                eintrag[art] = {"status": "fehler", "meldung": str(exc)[:300]}
        ergebnisse.append(eintrag)
    ri = []
    for b in plan.get("beziehungen", []):
        eintrag = {"name": b["name"]}
        if genutzt >= budget:
            ri.append({**eintrag, "status": "budget"})
            continue
        genutzt += 1
        try:
            antwort = transport(url, kopf, {"queries": [{"query": b["abfrage"]}],
                                            "serializerSettings": {"includeNulls": True}})
            zeilen = antwort["results"][0]["tables"][0].get("rows", [])
            ri.append({**eintrag, "status": "ok", "werte": [z.get("[v]") for z in zeilen]})
        except Exception as exc:                                            # noqa: BLE001
            ri.append({**eintrag, "status": "fehler", "meldung": str(exc)[:300]})
    return {"modell": plan["modell"], "quelle_sha256": plan["quelle_sha256"],
            "abfragen": genutzt, "ergebnisse": ergebnisse, "beziehungen": ri}


# ------------------------------------------------------------------ Bewertung

def bewerten(plan: dict, lauf_ergebnis: dict, erwartet: dict[str, float] | None = None,
             toleranz: float = 1e-6) -> list[dict]:
    """Befunde. Leere Liste heisst: jede Measure verhielt sich wie ihre Klasse verlangt."""
    if lauf_ergebnis.get("quelle_sha256") != plan["quelle_sha256"]:
        return [{"measure": "*", "befund": "Lauf passt nicht zum Plan (Modell seither geändert)"}]
    befunde = []
    je = {e["measure"]: e for e in lauf_ergebnis["ergebnisse"]}
    for m in plan["messungen"]:
        e = je.get(m["measure"], {})
        for art in ("gesamt", "je_monat"):
            r = e.get(art, {"status": "fehlt"})
            if r["status"] != "ok":
                befunde.append({"measure": m["measure"], "befund": f"{art}: {r['status']}",
                                "detail": r.get("meldung", "")})
        werte = [w for w in e.get("je_monat", {}).get("werte", []) if w not in (None, "")]
        if m["klasse"] == "zahl" and e.get("je_monat", {}).get("status") == "ok" and not werte:
            befunde.append({"measure": m["measure"], "befund": "kein Monat gefüllt"})
        if m["klasse"] == "leer_begruendet" and werte:
            befunde.append({"measure": m["measure"], "befund": "gefüllt, obwohl als leer begründet"})
    je_rel = {e["name"]: e for e in lauf_ergebnis.get("beziehungen", [])}
    for b in plan.get("beziehungen", []):
        r = je_rel.get(b["name"], {"status": "fehlt"})
        wer = f'{b["von"]} -> {b["nach"]}'
        if r["status"] != "ok":
            befunde.append({"measure": wer, "befund": f"RI: {r['status']}",
                            "detail": r.get("meldung", "")})
            continue
        ist = (r.get("werte") or [None])[0]
        if ist is None or float(ist) != b["erwartet"]:
            befunde.append({"measure": wer, "befund": "verwaiste Schlüssel",
                            "detail": f"{ist} Wert(e) ohne Gegenstück in {b['nach']} (Beziehung {b['name']})"})
    for key, soll in (erwartet or {}).items():
        modell, name = key.split("::", 1)
        if modell != plan["modell"]:
            continue
        ist = (je.get(name, {}).get("gesamt", {}).get("werte") or [None])[0]
        if ist is None or abs(float(ist) - soll) > toleranz * max(1.0, abs(soll)):
            befunde.append({"measure": name, "befund": "Gegenprobe weicht ab",
                            "detail": f"DAX {ist} gegen pandas {soll}"})
    return befunde


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan"); p.add_argument("--write", action="store_true")
    g = sub.add_parser("gegenprobe"); g.add_argument("--slice", type=Path, required=True)
    g.add_argument("--out", type=Path, required=True)
    r = sub.add_parser("run"); r.add_argument("--model", required=True)
    r.add_argument("--workspace"); r.add_argument("--dataset"); r.add_argument("--out", type=Path, required=True)
    r.add_argument("--budget", type=int, default=1000)
    b = sub.add_parser("bewerten"); b.add_argument("--lauf", type=Path, required=True)
    b.add_argument("--erwartet", type=Path)
    a = ap.parse_args(argv)

    if a.cmd == "plan":
        drift = pruefe_plan(a.write)
        if drift and not a.write:
            print(f"[dax-smoke] Plan veraltet: {', '.join(drift)} -- plan --write", file=sys.stderr)
            return 1
        plaene = [json.loads(f.read_text(encoding="utf-8")) for f in PLAN.glob("*.json")]
        n = sum(len(x["messungen"]) for x in plaene)
        r = sum(len(x.get("beziehungen", [])) for x in plaene)
        print(f"[dax-smoke] {'geschrieben' if drift else 'aktuell'}: {n} Measures und {r} "
              f"RI-Abfragen in {len(plaene)} Plänen")
        return 0
    if a.cmd == "gegenprobe":
        ergebnis = gegenprobe(a.slice)
        a.out.write_text(_json(ergebnis), encoding="utf-8", newline="\n")
        print(f"[dax-smoke] Gegenprobe: {len(ergebnis['werte'])} Summen aus {a.slice}, "
              f"{len(ergebnis['spalte_fehlt'])} mit fehlender Quellspalte")
        for x in ergebnis["spalte_fehlt"]:
            print(f"  Spalte fehlt: {x}", file=sys.stderr)
        return 0 if ergebnis["werte"] else 2
    if a.cmd == "run":
        token = os.environ.get("POWERBI_ACCESS_TOKEN")
        if not (token and a.workspace and a.dataset):
            print("[dax-smoke] nicht prüfbar: POWERBI_ACCESS_TOKEN, --workspace und --dataset nötig",
                  file=sys.stderr)
            return 2
        plan = json.loads((PLAN / f"{a.model.removesuffix('.SemanticModel')}.json").read_text(encoding="utf-8"))
        ergebnis = lauf(plan, a.workspace, a.dataset, token, budget=a.budget)
        a.out.write_text(_json(ergebnis), encoding="utf-8", newline="\n")
        print(f"[dax-smoke] {ergebnis['abfragen']} Abfragen gegen {plan['modell']}")
        return 0
    lauf_ergebnis = json.loads(a.lauf.read_text(encoding="utf-8"))
    plan = json.loads((PLAN / f"{lauf_ergebnis['modell'].removesuffix('.SemanticModel')}.json").read_text(encoding="utf-8"))
    erwartet = json.loads(a.erwartet.read_text(encoding="utf-8"))["werte"] if a.erwartet else None
    befunde = bewerten(plan, lauf_ergebnis, erwartet)
    for x in befunde:
        print(f"  {x['measure']}: {x['befund']} {x.get('detail', '')}")
    print(f"[dax-smoke] {len(befunde)} Befund(e)")
    return 1 if befunde else 0


if __name__ == "__main__":
    sys.exit(main())
