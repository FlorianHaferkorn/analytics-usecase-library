"""Gold-Quelle als Parameter: lokaler Ordner oder OneLake (AP-3, 24.09.2026).

Die fuenf Modelle lesen ihre Gold-Tabellen ueber `fn_DeltaCurrentFiles(GoldDataPath & "/...")`,
und die Funktion listet mit `Folder.Files`. Das ist ein lokaler oder UNC-Pfad; im Power BI
Service laedt es nur mit Gateway. Fuer den Sandbox-Lauf (UMSETZUNGSPLAN_AGENTIC_LOOP.md) muss
dasselbe Modell auch aus OneLake lesen koennen.

Dieses Modul schreibt deshalb in `expressions.tmdl` jedes Modells:

* zwei Parameter neben `GoldDataPath`: `GoldSourceKind` (`folder` | `onelake`, Vorgabe `folder`)
  und `GoldContainerUrl` (der OneLake-Workspace, etwa
  `https://onelake.dfs.fabric.microsoft.com/<workspace>`);
* in `fn_DeltaCurrentFiles` die Auflistung als Weiche. Bei `onelake` listet
  `AzureStorage.DataLake` den **Container** und filtert auf den Tabellenordner. Microsoft Learn
  (Power Query, ADLS Gen2, gelesen 24.09.2026) nennt Unterordner-URLs in Desktop und Power Query
  Online als nicht unterstuetzt; darum der Container und der Filter.

Mit Vorgabe `folder` aendert sich lokal nichts: derselbe Ausdruck, dieselben Dateien.
**ANNAHME, ungeprueft:** dass `AzureStorage.DataLake` ueber OneLake dieselben Spalten liefert
(`Content`, `Name`, `Folder Path`), die die Funktion danach liest. Belegt wird das erst im
ersten Sandbox-Lauf (AP-2/AP-5).

    python -m tooling.codegen.gold_source            # --check (Standard)
    python -m tooling.codegen.gold_source --write
"""
from __future__ import annotations

import argparse
import sys
import uuid
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DIST = REPO / "products" / "fabric" / "powerbi" / "dist"

ALT = "\t\tAllFiles = Folder.Files(TableFolderPath),\n"
NEU = (
    "\t\tAllFiles =\n"
    "\t\t\tif GoldSourceKind = \"onelake\" then\n"
    "\t\t\t\tlet\n"
    "\t\t\t\t\tPrefix = Text.Replace(TableFolderPath, \"\\\", \"/\") & \"/\",\n"
    "\t\t\t\t\tListed = AzureStorage.DataLake(GoldContainerUrl)\n"
    "\t\t\t\tin\n"
    "\t\t\t\t\tTable.SelectRows(Listed, each Text.StartsWith(Text.Replace([Folder Path], \"\\\", \"/\"), Prefix))\n"
    "\t\t\telse\n"
    "\t\t\t\tFolder.Files(TableFolderPath),\n"
)


def _parameter(modell: str, name: str, wert: str, pflicht: bool) -> str:
    tag = uuid.uuid5(uuid.NAMESPACE_URL, f"aluca:{modell}:{name}")
    return (
        f'expression {name} = "{wert}" meta [IsParameterQuery=true, Type="Text", '
        f'IsParameterQueryRequired={"true" if pflicht else "false"}]\n'
        f"\tlineageTag: {tag}\n"
        f"\tannotation PBI_NavigationStepName = {name}\n"
        f"\tannotation PBI_ResultType = Text\n"
        "\n"
    )


def soll(modell: str, text: str) -> str:
    """Der Zielinhalt von `expressions.tmdl`. Idempotent: ein zweiter Lauf aendert nichts."""
    if ALT in text:
        text = text.replace(ALT, NEU, 1)
    elif NEU not in text:
        raise ValueError(f"{modell}: fn_DeltaCurrentFiles hat eine unbekannte Form")
    for name, wert, pflicht in (("GoldSourceKind", "folder", True), ("GoldContainerUrl", "", False)):
        if f"expression {name} =" not in text:
            text = text.rstrip("\n") + "\n\n" + _parameter(modell, name, wert, pflicht)
    return text.rstrip("\n") + "\n"


def pruefe(schreiben: bool = False) -> list[str]:
    drift = []
    for m in sorted(DIST.glob("*.SemanticModel")):
        pfad = m / "definition" / "expressions.tmdl"
        alt = pfad.read_text(encoding="utf-8")
        neu = soll(m.name, alt)
        if neu != alt:
            drift.append(m.name)
            if schreiben:
                pfad.write_text(neu, encoding="utf-8", newline="\n")
    return drift


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    drift = pruefe(a.write)
    if drift and not a.write:
        print(f"[gold-source] weicht ab: {', '.join(drift)} -- --write", file=sys.stderr)
        return 1
    print(f"[gold-source] {'geschrieben' if drift else 'aktuell'}: {len(list(DIST.glob('*.SemanticModel')))} Modelle")
    return 0


if __name__ == "__main__":
    sys.exit(main())
