"""Eingefrorene Auszuege aus dem offiziellen Power-BI-Visual-Katalog.

WARUM eine Datei und kein zweiter Checker: der Katalog
`@microsoft/powerbi-core-visual-schema` (Pin 0.1.1) liegt als npm-Paket im
Nachbar-Repo Meridian, und der Zugriff darauf gehoert dort hin
(`core.pbi_engine.oracle.visual_catalog`, D-236). ALUCAs CI hat weder das
Paket noch den Nachbar-Checkout. Ein Test, der den Katalog importiert, waere
hier also ein Dauer-Soft-Skip — ein Tor, das „nichts gefunden" und „nicht
gelaufen" nicht unterscheiden kann (dieselbe Klasse wie `tabular-bpa.yml`,
18.08.2026).

Stattdessen liegt der Auszug eingecheckt daneben: `catalog_facts.json` traegt
je Visualtyp, den die Bibliothek emittiert, die Datenrollen und die
Eigenschaftsnamen der benutzten Formatierungsobjekte.

Seit AP-8 (24.09.2026) traegt er auch die **Anzeigenamen** des Format-Bereichs
(`anzeige`, `vco_anzeige`): je Visualtyp fuer die benutzten Objekte plus die
alltaeglichen (`ALLTAG_OBJEKTE`), dazu die Container-Objekte (Titel, Hintergrund,
Rahmen ...). Daraus loest `format_pfad` einen Eintrag der Synonymtabelle
`visual_library/_format_synonyme.yaml` in den Pfad auf, den ein Mensch im
Format-Bereich sieht. Der Anzeigename haengt am Visualtyp: `categoryAxis` heisst
beim `clusteredBarChart` „Y axis", beim `clusteredColumnChart` „X axis". Der Test laeuft damit
ueberall und hart. Der Auszug steigt nur ueber `write` und nur mit dem
Katalog in Reichweite — genau wie ein Pin: gemessen wird Drift, gebumpt wird
von Hand (D-238).

    python3 tooling/visual_library/catalog_facts.py check --catalog <data-dir>
    python3 tooling/visual_library/catalog_facts.py write --catalog <data-dir>

<data-dir> ist der `data/`-Ordner des npm-Pakets, z. B.
  <Meridian>/meridian/studio/node_modules/@microsoft/powerbi-core-visual-schema/data

Exit-Vokabular (drei Ausgaenge, nicht zwei):
    0  verglichen, deckungsgleich  |  1  Drift  |  2  konnte nicht vergleichen
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent
FACTS = HIER / "catalog_facts.json"
LIB = HIER.parent.parent / "core" / "templates" / "page_templates" / "visual_library"
PIN = "0.1.1"
# Objekte, nach denen Menschen fragen, auch wenn die Bibliothek sie heute nicht setzt.
ALLTAG_OBJEKTE = ("dataPoint", "categoryAxis", "valueAxis", "labels", "legend", "lineStyles")
QUELLE = "@microsoft/powerbi-core-visual-schema"


def lade() -> dict:
    """Der eingefrorene Auszug. Fehlt er, ist das ein Fehler und kein Skip."""
    return json.loads(FACTS.read_text(encoding="utf-8"))


def benutzte_typen(lib: Path | None = None) -> dict[str, set[str]]:
    """{visualType: {benutzte Formatierungsobjekte}} aus den nativen Goldens."""
    lib = lib or LIB
    aus: dict[str, set[str]] = {}
    for gp in sorted((lib / "golden").glob("*.powerbi_native*.json")):
        d = json.loads(gp.read_text(encoding="utf-8"))
        vt = d.get("visualType")
        if not vt:
            continue
        aus.setdefault(vt, set()).update(d.get("objects") or {})
    return aus


def _aus_katalog(data_dir: Path, gebraucht: dict[str, set[str]]) -> dict:
    caps = json.loads((data_dir / "capabilities.json").read_text(encoding="utf-8"))
    visuals: dict[str, dict] = {}
    for vt in sorted(gebraucht):
        c = caps.get(vt)
        if c is None:
            visuals[vt] = {"_fehlt_im_katalog": True}
            continue
        visuals[vt] = {
            "roles": sorted(r["name"] for r in c.get("dataRoles", [])),
            "objects": {
                o: sorted(c.get("objects", {}).get(o, {}).get("properties", {}))
                for o in sorted(gebraucht[vt])
            },
        }
    anzeige: dict[str, dict] = {}
    for vt in sorted(gebraucht):
        objekte = (caps.get(vt) or {}).get("objects", {})
        for o in sorted(set(gebraucht[vt]) | {x for x in ALLTAG_OBJEKTE if x in objekte}):
            od = objekte.get(o)
            if od is None:
                continue
            anzeige.setdefault(vt, {})[o] = {
                "_": od.get("displayName"),
                **{pn: pd.get("displayName") for pn, pd in sorted(od.get("properties", {}).items())},
            }
    vco = json.loads((data_dir / "vco-capabilities.json").read_text(encoding="utf-8"))
    vco_anzeige = {
        o: {"_": od.get("displayName"),
            **{pn: pd.get("displayName") for pn, pd in sorted(od.get("properties", {}).items())}}
        for o, od in sorted(vco.items()) if not o.startswith("_")
    }
    return {"quelle": QUELLE, "pin": PIN, "visuals": visuals,
            "anzeige": anzeige, "vco_anzeige": vco_anzeige}


def format_pfad(visual_type: str, objekt: str, prop: str, facts: dict | None = None) -> str:
    """Der Pfad im Format-Bereich, z. B. `Data colors › Color`. KeyError, wenn unbekannt.

    Container-Objekte (Titel, Hintergrund ...) gelten fuer jeden Visualtyp und werden
    zuerst dort gesucht, wo sie hingehoeren: in `vco_anzeige`.
    """
    facts = facts or lade()
    quelle = facts["vco_anzeige"].get(objekt) or facts["anzeige"][visual_type][objekt]
    obj_name, prop_name = quelle["_"], quelle[prop]
    return f"{obj_name or objekt} › {prop_name or prop}"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("modus", choices=["check", "write"])
    ap.add_argument("--catalog", required=True,
                    help="data/-Ordner des npm-Pakets powerbi-core-visual-schema")
    a = ap.parse_args(argv)

    data_dir = Path(a.catalog)
    if not (data_dir / "capabilities.json").exists():
        print(f"[catalog-facts] konnte nicht vergleichen: {data_dir}/capabilities.json "
              f"fehlt. Ohne den Katalog gibt es keine Messung, nur eine Vermutung.")
        return 2

    neu = _aus_katalog(data_dir, benutzte_typen())
    alt = lade() if FACTS.exists() else {}
    gleich = {k: v for k, v in alt.items() if k != "gemessen"} == neu

    if a.modus == "write":
        neu["gemessen"] = _dt.date.today().isoformat()
        FACTS.write_text(json.dumps(neu, indent=2, ensure_ascii=False,
                                    sort_keys=True) + "\n", encoding="utf-8",
                         newline="\n")
        print(f"[catalog-facts] geschrieben: {FACTS.relative_to(HIER.parent.parent)} "
              f"({len(neu['visuals'])} Visualtypen, Pin {PIN})")
        return 0

    if gleich:
        print(f"[catalog-facts] deckungsgleich: {len(neu['visuals'])} Visualtypen, "
              f"Pin {PIN}, gemessen gegen {data_dir}")
        return 0
    print("[catalog-facts] Drift gegen den Katalog — `write` haelt sie fest, "
          "nachdem geklaert ist, welche Seite recht hat:")
    for vt in sorted(set(neu["visuals"]) | set(alt.get("visuals", {}))):
        if neu["visuals"].get(vt) != alt.get("visuals", {}).get(vt):
            print(f"  {vt}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
