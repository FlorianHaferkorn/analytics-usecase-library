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
Eigenschaftsnamen der benutzten Formatierungsobjekte. Der Test laeuft damit
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
    return {"quelle": QUELLE, "pin": PIN, "visuals": visuals}


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
