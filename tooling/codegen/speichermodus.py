"""Speichermodus der Semantikmodelle je Mandant (Meridian D-590) fuer die dist-Codegen-Module.

Die Regel selbst steht NICHT hier. Sie ist Meridians ``storage_mode.py``, byte-identisch
gespiegelt nach ``tooling/superversion/vendor/meridian_dataarch/`` (SHARED_SUBSTANCE.md
Klasse A): Feld ``medallion.platinum.storage_mode`` im Bauplan, sonst Direct Lake on OneLake
bei Fabric-Kapazitaet, sonst Import. Dieses Modul uebersetzt den aufgeloesten Modus in die
Partitionsform, die ALUCAs Codegen (``model_alignment``, ``comparison_measures``) in ``dist/``
schreibt, und prueft vorher, ob das Zielmodell den Modus tragen kann.

**ALUCAs dist hat keinen Bauplan.** Ohne Bauplan ist keine Kapazitaet bekannt, die Vorgabe ist
Import — derselbe Modus, in dem ``dist/`` heute steht (89 von 89 Partitionen ``mode: import``,
gezaehlt 30.09.2026). Wer einen Mandanten mit Bauplan bedient, uebergibt ihn mit
``--blueprint``.

**Direct Lake on OneLake** (Learn ``fabric/fundamentals/direct-lake-develop`` → Direct Lake
model metadata / Power Query connectors, gelesen 30.09.2026): ``partition <t> = entity`` mit
``mode: directLake``, ``entityName``, ``schemaName`` und ``expressionSource`` auf eine geteilte
Expression mit ``AzureStorage.DataLake("https://onelake.dfs.fabric.microsoft.com/<ws>/<item>")``.
Die dist-Modelle sind Import-Modelle mit Gold ueber ``fn_DeltaCurrentFiles``; eine Direct-Lake-
Tabelle dort hinein waere ein stilles Mischmodell. ``pruefe_modell`` bricht deshalb ab, statt zu
mischen — ebenso bei materialisierten berechneten Spalten oder berechneten Beziehungsschluesseln
(Learn ``power-bi/transform-model/desktop-calculated-columns``, gelesen 30.09.2026).
"""
from __future__ import annotations

import importlib
import json
import re
from pathlib import Path
from types import ModuleType

#: Name der geteilten Direct-Lake-Expression. ALUCAs eigener Umsteller (``table_ops.ps1
#: -Operation WriteDirectLakeExpression/PatchPartitionSourceToDirectLake``) schreibt
#: ``DL_Lakehouse``; eine neue Tabelle muss auf dieselbe Expression zeigen, sonst findet die
#: Partition ihre Quelle nicht (Meridians Emitter nennt sie ``DatabaseQuery`` — dort ist es
#: dessen eigene Expression).
DL_EXPRESSION = "DL_Lakehouse"

_REGEL: ModuleType | None = None


def _regel() -> ModuleType:
    """Das gespiegelte Meridian-Modul ``storage_mode`` (Integritaet gegen PIN geprueft)."""
    global _REGEL
    if _REGEL is None:
        from tooling.superversion._dataarch_vendor import load_emitters
        load_emitters()                   # PIN-Pruefung + Import-Bruecke; wirft, wenn der Spiegel fehlt
        _REGEL = importlib.import_module("core.dataarch_engine.blueprint.storage_mode")
    return _REGEL


def konstanten() -> tuple[str, str]:
    """(DIRECT_LAKE_ONELAKE, IMPORT) aus der gespiegelten Regel."""
    r = _regel()
    return r.DIRECT_LAKE_ONELAKE, r.IMPORT


def lade_bauplan(pfad: Path | None) -> dict:
    """Bauplan aus JSON/YAML; ``{"blueprint": …}`` (Meridian-CLI-Ausgabe) wird ausgepackt."""
    if pfad is None:
        return {}
    text = Path(pfad).read_text(encoding="utf-8")
    if str(pfad).endswith((".yaml", ".yml")):
        import yaml
        bp = yaml.safe_load(text) or {}
    else:
        bp = json.loads(text)
    return bp.get("blueprint", bp)


def mandant_modus(bauplan: dict | None) -> str:
    """Der Speichermodus des Mandanten — einzig ueber die gespiegelte Regel."""
    return _regel().resolve_storage_mode(bauplan or {})


def gold_partition(name: str, ordner: str, modus: str, einzug: str = "\t\t\t") -> list[str]:
    """Partition einer Gold-Tabelle je Modus.

    Import: die heutige dist-Form (``fn_DeltaCurrentFiles`` + ``Parquet.Document``), Zeile fuer
    Zeile wie bisher; ``einzug`` ist der Einzug von ``let``/``in`` (die Module unterscheiden
    sich dort, und die Ausgabe muss byte-gleich bleiben). Direct Lake on OneLake: ``entity``.
    """
    dl, imp = konstanten()
    if modus == imp:
        return [f"\tpartition {name} = m", "\t\tmode: import", "\t\tsource =",
                f"{einzug}let",
                f'{einzug}\tActiveFiles = fn_DeltaCurrentFiles(GoldDataPath & "/{ordner}/{name}"),',
                f"{einzug}\tParquetData = Table.Combine(List.Transform(ActiveFiles[Content], "
                "each Parquet.Document(_)))",
                f"{einzug}in", f"{einzug}\tParquetData"]
    if modus == dl:
        return [f"\tpartition {name} = entity", "\t\tmode: directLake", "\t\tsource",
                f"\t\t\tentityName: {name}", "\t\t\tschemaName: dbo",
                f"\t\t\texpressionSource: {DL_EXPRESSION}"]
    raise _regel_fehler(f"Speichermodus {modus!r} unbekannt")


def direct_lake_expression(workspace_id: str = "<workspace-id>",
                           item_id: str = "<lakehouse-id>") -> str:
    """Die geteilte Quelle eines Direct-Lake-on-OneLake-Modells fuer ``expressions.tmdl``."""
    return (f"expression {DL_EXPRESSION} =\n\t\tlet\n\t\t\tSource = AzureStorage.DataLake("
            f'"https://onelake.dfs.fabric.microsoft.com/{workspace_id}/{item_id}")\n'
            "\t\tin\n\t\t\tSource\n")


def _regel_fehler(text: str) -> Exception:
    return _regel().StorageModeError(text)


_CALC_COL = re.compile(r"^\tcolumn\s+('(?:[^']|'')+'|[^\s=]+)\s*=\s*(.+)$")
_COL = re.compile(r"^\tcolumn\s+('(?:[^']|'')+'|[^\s=]+)\s*$")
_CTX = re.compile(r"^\t\texpressionContext:\s*(\w+)")
_REL_COL = re.compile(r"^\t(from|to)Column:\s*(.+)$")
_IMPORT_GOLD = re.compile(r"^\t\tmode:\s*import\s*$")


def _name(roh: str) -> str:
    roh = roh.strip()
    return roh[1:-1].replace("''", "'") if roh.startswith("'") else roh


def modell_struktur(definition: Path) -> tuple[list[dict], list[tuple[str, str, str, str]], list[str]]:
    """(Tabellen mit berechneten Spalten, Beziehungen, Tabellen mit Gold-Import-Partition)."""
    tabellen: list[dict] = []
    gold_import: list[str] = []
    for f in sorted((definition / "tables").glob("*.tmdl")):
        text = f.read_text(encoding="utf-8")
        name = f.stem
        spalten: list[dict] = []
        for zeile in text.splitlines():
            m = _CALC_COL.match(zeile)
            if m:
                spalten.append({"name": _name(m.group(1)), "expression": m.group(2)})
                continue
            if _COL.match(zeile):
                spalten.append({"name": _name(_COL.match(zeile).group(1))})
                continue
            c = _CTX.match(zeile)
            if c and spalten:
                spalten[-1]["expression_context"] = c.group(1)
        tabellen.append({"name": name, "columns": spalten})
        if "GoldDataPath" in text and any(_IMPORT_GOLD.match(z) for z in text.splitlines()):
            gold_import.append(name)
    rels: list[tuple[str, str, str, str]] = []
    reltexte = [p.read_text(encoding="utf-8") for p in sorted((definition / "relationships").glob("*.tmdl"))]
    single = definition / "relationships.tmdl"
    if single.exists():
        reltexte += single.read_text(encoding="utf-8").split("\nrelationship ")
    for text in reltexte:
        enden: dict[str, str] = {}
        for zeile in text.splitlines():
            m = _REL_COL.match(zeile)
            if m:
                enden[m.group(1)] = m.group(2).strip()
        if "from" in enden and "to" in enden and "." in enden["from"] and "." in enden["to"]:
            ft, fc = enden["from"].split(".", 1)
            tt, tc = enden["to"].split(".", 1)
            rels.append((_name(ft), _name(fc), _name(tt), _name(tc)))
    return tabellen, rels, gold_import


def pruefe_modell(definition: Path, modus: str) -> None:
    """Abbruch, wenn das Modell unter ``definition`` den Modus nicht tragen kann.

    Import traegt alles. Direct Lake on OneLake: keine Gold-Tabelle im Import-Modus daneben
    (sonst still gemischt) und keine materialisierten/verschluesselnden berechneten Spalten
    (gespiegelte Meridian-Regel ``check_storage_mode``).
    """
    dl, _ = konstanten()
    tabellen, rels, gold_import = modell_struktur(definition)
    if modus == dl and gold_import:
        raise _regel_fehler(
            f"{definition.parent.name}: Speichermodus {dl} verlangt, aber {len(gold_import)} "
            f"Gold-Tabelle(n) lesen im Import-Modus ({', '.join(gold_import[:5])}"
            f"{' …' if len(gold_import) > 5 else ''}). Eine Direct-Lake-Tabelle daneben waere ein "
            "stilles Mischmodell. Erst das ganze Modell umstellen (products/fabric/powerbi/"
            "orchestrator/table_ops.ps1 -Operation PatchPartitionSourceToDirectLake) oder den "
            "Mandanten auf medallion.platinum.storage_mode = import setzen.")
    if modus == dl:
        exprs = definition / "expressions.tmdl"
        text = exprs.read_text(encoding="utf-8") if exprs.exists() else ""
        if not re.search(rf"^expression\s+{DL_EXPRESSION}\s*=", text, re.M):
            raise _regel_fehler(
                f"{definition.parent.name}: Speichermodus {dl} verlangt die geteilte Expression "
                f"{DL_EXPRESSION} in expressions.tmdl (AzureStorage.DataLake auf OneLake); sie "
                "fehlt. Anlegen mit table_ops.ps1 -Operation WriteDirectLakeExpression.")
    _regel().check_storage_mode(modus, tabellen, rels)
