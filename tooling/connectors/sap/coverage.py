"""Welche ALUCA-Use-Cases Meridians SAP-Gold tragen kann -- abgeleitet, nicht geschaetzt.

Kette: Use Case (Bracket) -> seine KPIs -> deren Lineage-Spalten (inklusive der KPIs, von
denen sie abhaengen) -> Status jeder Spalte in meridian_gold_map.yaml.

Eine KPI ist `nutzbar`, wenn jede ihrer Spalten abgebildet oder ableitbar ist und keine
Tabelle blockiert ist. `ausser_sap` heisst: mindestens eine Spalte liegt in einer Tabelle,
die SAP in diesem Paket gar nicht betrifft (Support, Personal, Produktion ...). Alles
andere ist `luecke`, mit dem Grund aus der Karte.

CLI:  python -m tooling.connectors.sap.coverage
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[3]
KARTE = Path(__file__).with_name("meridian_gold_map.yaml")
NUTZBAR = {"abgebildet", "ableitbar"}


def karte() -> dict:
    return yaml.safe_load(KARTE.read_text(encoding="utf-8")) or {}


def _kpis() -> dict[str, dict]:
    from tooling.generator.export_governed_catalog import _load_measures

    out = {m["kpi_id"]: {"name": m["measure_name"], "lineage": m["lineage"], "deps": []}
           for m in _load_measures(REPO / "core" / "kpi_catalog" / "kpis")}
    # `depends_on_measures` fuehrt der Katalog-Export nicht; hier ergaenzt.
    for f in sorted((REPO / "core" / "kpi_catalog" / "kpis").glob("*.yaml")):
        d = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        kid = d.get("kpi_id", f.stem)
        if kid in out:
            out[kid]["deps"] = list(((d.get("technical") or {}).get("depends_on_measures")) or [])
    return out


def _spalten(kid: str, kpis: dict, name_zu_id: dict, gesehen: set | None = None) -> set[str]:
    gesehen = gesehen if gesehen is not None else set()
    if kid in gesehen or kid not in kpis:
        return set()
    gesehen.add(kid)
    out = set(kpis[kid]["lineage"])
    for dep in kpis[kid]["deps"]:
        out |= _spalten(name_zu_id.get(dep, dep), kpis, name_zu_id, gesehen)
    return out


def _use_case_kpis(bracket: dict, kpis: dict) -> set[str]:
    o = bracket.get("orchestration") or {}
    ids = {o.get("strategic_kpi_id"), *(o.get("influencing_kpi_ids") or []), *(bracket.get("primary_kpi_ids") or [])}
    p1 = (bracket.get("ux_layout_rules") or {}).get("page_1_summary") or {}
    for c in p1.get("component_30s") or []:
        if isinstance(c, dict):
            ids |= {c.get("kpi_id"), *(c.get("kpi_ids") or [])}
    c3 = p1.get("component_3s")
    if isinstance(c3, dict):
        ids.add(c3.get("kpi_id"))
    return {i for i in ids if i in kpis}


def spalten_status(spalte: str, k: dict) -> tuple[str, str]:
    tabelle = spalte.split(".", 1)[0]
    blocker = ((k.get("tabellen") or {}).get(tabelle) or {}).get("blocker")
    eintrag = (k.get("spalten") or {}).get(spalte)
    if eintrag is None:
        if tabelle in (k.get("tabellen") or {}) or any(s.startswith(tabelle + ".") for s in k.get("spalten") or {}):
            return "unbelegt", "Spalte einer SAP-Tabelle ohne Eintrag in der Karte"
        return "ausser_sap", f"{tabelle} liegt ausserhalb des SAP-Pakets"
    if blocker and eintrag.get("status") in NUTZBAR:
        return blocker["status"], blocker["grund"].split(".")[0]
    return eintrag["status"], eintrag.get("grund") or eintrag.get("regel") or eintrag.get("quelle", "")


def abdeckung() -> dict[str, dict]:
    k = karte()
    kpis = _kpis()
    name_zu_id = {v["name"]: kid for kid, v in kpis.items()}
    ergebnis: dict[str, dict] = {}
    for bf in sorted((REPO / "core" / "usecases" / "core").glob("*/UseCase_Bracket.yaml")):
        b = yaml.safe_load(bf.read_text(encoding="utf-8")) or {}
        je_kpi = {}
        for kid in sorted(_use_case_kpis(b, kpis)):
            st = {s: spalten_status(s, k) for s in sorted(_spalten(kid, kpis, name_zu_id))}
            if not st:
                urteil = "ohne_lineage"
            elif all(v[0] in NUTZBAR for v in st.values()):
                urteil = "nutzbar"
            elif any(v[0] == "ausser_sap" for v in st.values()):
                urteil = "ausser_sap"
            else:
                urteil = "luecke"
            je_kpi[kid] = {"urteil": urteil, "spalten": st}
        ergebnis[bf.parent.name] = je_kpi
    return ergebnis


def main() -> int:
    ab = abdeckung()
    print(f"{'Use Case':42} nutzbar  luecke  ausser_sap  (KPIs)")
    for uc, ks in ab.items():
        z = {u: sum(1 for v in ks.values() if v["urteil"] == u) for u in ("nutzbar", "luecke", "ausser_sap")}
        print(f"{uc:42} {z['nutzbar']:7} {z['luecke']:7} {z['ausser_sap']:10}  ({len(ks)})")
    unbelegt = sorted({s for ks in ab.values() for v in ks.values()
                       for s, (st, _) in v["spalten"].items() if st == "unbelegt"})
    if unbelegt:
        print("\nUNBELEGT (Karte unvollstaendig):", ", ".join(unbelegt))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
