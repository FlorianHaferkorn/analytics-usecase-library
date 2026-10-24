"""Modell an Vertrag und Gold ausrichten (E8, Gruppen 1 und 2, entschieden 24.09.2026).

Gefunden von der DAX-Gegenprobe (AP-4): 20 ``sourceColumn`` der ausgelieferten Modelle stehen in
keiner aktiven Gold-Datei. Die Verträge unter ``core/data_contracts/domains/`` beschreiben Gold
bereits richtig; veraltet ist ``dist/``. Neu erzeugen über ``table_ops.ps1`` geht nicht, weil
dessen Partition (``FirstFile``) hinter der heutigen (``fn_DeltaCurrentFiles``, AP-3) zurückliegt.
Dieses Modul zieht deshalb genau die entschiedenen Änderungen nach, deterministisch und idempotent:

* **Gruppe 1, Umbenennen.** ``sourceColumn`` zeigt auf die Gold-Spalte; der Spaltenname im Modell
  bleibt, damit DAX und Visuals unberührt bleiben. Typen geprüft: ``Decimal`` nimmt ``int64`` und
  ``double``, ``String`` nimmt ``string``.
* **Gruppe 2, Körnung.** Gold führt Beschaffung auf ``CategoryKey``/``VendorKey`` (Vertrag
  ``supply_chain.yaml``). ``fact_procurement`` verliert ``ProductKey`` samt Beziehung zu
  ``dim_product`` und bekommt ``dim_category``/``dim_vendor`` (aus dem Vertrag, Partition wie die
  übrigen Dimensionen). ``fact_nps`` in Experience verliert ``QueueKey`` samt Beziehung zu
  ``dim_case_queue``; Gold-NPS hat keine Queue.

Vor dem Entfernen wird geprüft, dass kein DAX-Ausdruck und kein Bericht die Spalte nutzt; sonst
Abbruch statt stillem Bruch. ``diagramLayout.json`` bleibt unberührt (Desktop platziert neue
Tabellen selbst; ``check_diagram_layout.ps1`` verlangt nicht jede Tabelle).

* **COM-005, Pipeline (entschieden 24.10.2026).** Commercial bekommt ``fact_pipeline``,
  ``fact_sales_target``, ``dim_sales_stage`` und ``dim_salesrep`` ganz aus dem Vertrag
  ``commercial_sales.yaml``; die Beziehungen folgen den ``ref``-Spalten der Fakten. Ein Modell je
  Domäne, kein eigenes Pipeline-Modell. Die KPI-Measures (``NEW_KPI_MEASURES``) kommen aus dem
  Katalog: DAX über ``dax_synth`` (dieselbe Synthese wie ``build_ir``), Formatstring über
  ``format_policy`` (Profil ``model``), Doku-Block über ``enrich_measure_docs``; ein KPI mit
  ``op: hitl`` wird der dokumentierte Platzhalter (``build_ir.hitl_placeholder``) mit dem
  Katalog-Grund, nie eine erfundene Formel.

Gruppen 3 und 4 (Gold-Generator ergänzt Spalten) sind hier bewusst nicht enthalten.

    python -m tooling.codegen.model_alignment            # --check (Standard), rc 1 bei Abweichung
    python -m tooling.codegen.model_alignment --write
"""
from __future__ import annotations

import argparse
import re
import sys
import uuid
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
DIST = REPO / "products" / "fabric" / "powerbi" / "dist"
CONTRACTS = REPO / "core" / "data_contracts" / "domains"

# (Modell, Tabelle, alte sourceColumn, Gold-Spalte)
RENAMES = (
    ("SupplyChain", "fact_sales", "Sales Units", "Quantity"),
    ("SupplyChain", "fact_procurement", "Purchase Amount", "Procurement Amount"),
    ("SupplyChain", "fact_procurement", "Actual Unit Price", "Actual Unit Price Amount"),
    ("SupplyChain", "fact_procurement", "Contracted Amount", "On-Contract Amount"),
    ("SupplyChain", "fact_procurement", "Purchase Quantity", "Quantity"),
    ("Operations", "fact_inventory_snapshot", "Inventory Value", "Stock Value Amount"),
    ("Operations", "fact_inventory_snapshot", "On-Hand Units", "Stock Qty"),
    ("Experience", "fact_action_log", "Outcome Status", "Action Outcome"),
)

# (Modell, Tabelle, Spalte) und die Beziehung, die an ihr hängt
DROPS = (
    ("SupplyChain", "fact_procurement", "ProductKey", "dim_product_fact_procurement"),
    ("Experience", "fact_nps", "QueueKey", "dim_case_queue_fact_nps"),
)

# (Modell, Dimension, Vertrag, Faktentabelle, Schlüssel)
NEW_DIMENSIONS = (
    ("SupplyChain", "dim_category", "supply_chain.yaml", "fact_procurement", "CategoryKey"),
    ("SupplyChain", "dim_vendor", "supply_chain.yaml", "fact_procurement", "VendorKey"),
)

# (Modell, Tabelle, Vertrag, Vertragsabschnitt, ref-table-Anker in model.tmdl). Neue Tabellen
# ganz aus dem Vertrag; an Fakten hängen die Beziehungen aus deren ``ref``-Spalten.
NEW_TABLES = (
    ("Commercial", "dim_sales_stage", "commercial_sales.yaml", "dimension", "dim_pvm_driver"),
    ("Commercial", "dim_salesrep", "commercial_sales.yaml", "dimension", "dim_sales_stage"),
    ("Commercial", "fact_pipeline", "commercial_sales.yaml", "fact", "fact_nps"),
    ("Commercial", "fact_sales_target", "commercial_sales.yaml", "fact", "fact_sales"),
    # FIN-003: Kostenstellen-Zuordnung der OpEx (24.10.2026; Gold-FK-Treffer je 100 %)
    ("Finance", "dim_cost_center", "finance.yaml", "dimension", "dim_product"),
    ("Finance", "fact_opex_costcenter", "finance.yaml", "fact", "fact_cost"),
)

# (Modell, Tabelle, Vertrag, Spalte, Ankerspalte): Wertspalten, die der Vertrag führt und Gold
# liefert, dem Modell aber fehlen. FIN-003 (24.10.2026): KPI-FIN-021 braucht die Plan-Werte;
# Gold fact_finance trägt beide Spalten (5 aktive Dateien, pyarrow).
NEW_COLUMNS = (
    ("Finance", "fact_finance", "finance.yaml", "Plan Net Sales Amount", "Plan OpEx Amount"),
    ("Finance", "fact_finance", "finance.yaml", "Plan EBITDA Amount", "Plan Net Sales Amount"),
)

# (Modell, Anzeigeordner, KPI-IDs): Measures aus dem Katalog, ans Ende von _Measures.tmdl.
NEW_KPI_MEASURES = (
    ("Commercial", "COM-005", ("KPI-COM-026", "KPI-COM-027", "KPI-COM-028", "KPI-COM-029",
                               "KPI-COM-030", "KPI-COM-031")),
    ("Finance", "FIN-003", ("KPI-FIN-018", "KPI-FIN-020", "KPI-FIN-021")),
)

_TYPES = {"int": "Int64", "text": "String", "decimal": "Decimal", "currency": "Decimal", "bool": "Boolean"}


def _defn(modell: str) -> Path:
    return DIST / f"{modell}.SemanticModel" / "definition"


def _tag(*teile: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "aluca:model_alignment:" + ":".join(teile)))


def _col_ref(name: str) -> str:
    return f"'{name}'" if re.search(r"[^A-Za-z0-9_]", name) else name


def _column_block(text: str, name: str) -> re.Match | None:
    return re.search(rf"^\tcolumn {re.escape(_col_ref(name))}\n(?:\t\t.*\n)*", text, re.M)


def rename(text: str, alt: str, neu: str, wo: str) -> str:
    alt_zeile, neu_zeile = f"\t\tsourceColumn: {alt}\n", f"\t\tsourceColumn: {neu}\n"
    n = text.count(alt_zeile)
    if n == 0:
        if neu_zeile in text:
            return text
        raise ValueError(f"{wo}: weder sourceColumn '{alt}' noch '{neu}' gefunden")
    if n > 1:
        raise ValueError(f"{wo}: sourceColumn '{alt}' {n}-mal, nicht eindeutig")
    return text.replace(alt_zeile, neu_zeile)


def drop_column(text: str, spalte: str) -> str:
    m = _column_block(text, spalte)
    return text if m is None else text[:m.start()] + text[m.end():]


def add_key_column(text: str, spalte: str, nach: str) -> str:
    if _column_block(text, spalte):
        return text
    anker = _column_block(text, nach)
    if anker is None:
        raise ValueError(f"Ankerspalte '{nach}' fehlt")
    block = (f"\tcolumn {spalte}\n\t\tdataType: Int64\n\t\tisHidden\n"
             f"\t\tsourceColumn: {spalte}\n\t\tsummarizeBy: none\n")
    return text[:anker.end()] + block + text[anker.end():]


def add_value_column(text: str, spalte: dict, nach: str) -> str:
    """Wertspalte aus dem Vertrag hinter ``nach`` einfügen (idempotent)."""
    if _column_block(text, spalte["name"]):
        return text
    anker = _column_block(text, nach)
    if anker is None:
        raise ValueError(f"Ankerspalte '{nach}' fehlt")
    typ = _TYPES[spalte["type"]]
    block = (f"\tcolumn {_col_ref(spalte['name'])}\n\t\tdataType: {typ}\n"
             f"\t\tsourceColumn: {spalte['name']}\n\t\tsummarizeBy: none\n")
    return text[:anker.end()] + block + text[anker.end():]


def table_tmdl(modell: str, name: str, vertrag: dict, modus: str | None = None,
               abschnitt: str = "dimension") -> str:
    """Neue Tabelle als TMDL; die Partition folgt dem Speichermodus des Mandanten (D-590).

    ``modus=None`` heisst Import — der Modus von ``dist/`` (kein Bauplan, keine Kapazitaet).
    Schlüssel und Fremdschlüssel (``role: key``, ``ref``) sind verborgen; Kennzahlen aggregieren
    nur über Measures (``summarizeBy: none`` wie im übrigen dist)."""
    from tooling.codegen.speichermodus import gold_partition, konstanten
    modus = modus or konstanten()[1]
    t = next(d for d in vertrag[abschnitt] if d["name"] == name)
    zeilen = [f"/// {' '.join(t['description'].split())}", f"table {name}", f"\tlineageTag: {_tag(modell, name)}"]
    for c in t["columns"]:
        zeilen += [f"\tcolumn {_col_ref(c['name'])}", f"\t\tdataType: {_TYPES[c['type']]}",
                   f"\t\tsourceColumn: {c['name']}", "\t\tsummarizeBy: none"]
        if c.get("role") == "key" or c.get("ref"):
            zeilen += ["\t\tisHidden", "\t\tisAvailableInMDX: false"]
    ordner = "dimensions" if abschnitt == "dimension" else "facts"
    zeilen += gold_partition(name, ordner, modus, einzug="\t\t\t")
    return "\n".join(zeilen) + "\n"


def dimension_tmdl(modell: str, name: str, vertrag: dict, modus: str | None = None) -> str:
    return table_tmdl(modell, name, vertrag, modus, "dimension")


def relationship_tmdl(name: str, fakt: str, dim: str, schluessel: str) -> str:
    # Form wie die übrigen Beziehungsdateien: Standard many-to-one, ohne Zeilenende am Schluss.
    return f"relationship {name}\n\tfromColumn: {fakt}.{schluessel}\n\ttoColumn: {dim}.{schluessel}"


def add_table_ref(model_tmdl: str, tabelle: str, nach: str) -> str:
    zeile = f"ref table {tabelle}\n"
    if zeile in model_tmdl:
        return model_tmdl
    anker = f"ref table {nach}\n"
    if anker not in model_tmdl:
        raise ValueError(f"model.tmdl: Anker '{anker.strip()}' fehlt")
    return model_tmdl.replace(anker, anker + zeile, 1)


def kpi_measure_block(modell: str, kpi_id: str, ordner: str) -> str:
    """Measure einer Katalog-KPI als TMDL-Block (Doku, Ausdruck, Format, Ordner, Tag)."""
    from tooling.generator.enrich_measure_docs import _render_block
    from tooling.ir.build_ir import hitl_placeholder
    from tooling.reporting.format_policy import unit_format_string
    from tooling.superversion.from_aluca import KpiCatalog, _resolve_calculation
    from tooling.superversion.targets.dax_synth import synthesize_dax

    kpis = REPO / "core" / "kpi_catalog" / "kpis"
    kpi = yaml.safe_load((kpis / f"{kpi_id}.yaml").read_text(encoding="utf-8"))
    aufgeloest, grund = _resolve_calculation(kpi, KpiCatalog(kpis))
    dax = synthesize_dax(aufgeloest) if aufgeloest else hitl_placeholder(grund)
    name = kpi["technical"]["measure_name"]
    fmt = unit_format_string(kpi["business"].get("unit_format"), "model")
    doku = _render_block(kpi_id, REPO) or [f"\t/// {kpi['technical']['description']}"]
    zeilen = [*doku, f"\tmeasure {_col_ref(name)} = {dax}"]
    if fmt:
        zeilen.append(f"\t\tformatString: {fmt}")
    zeilen += [f"\t\tdisplayFolder: {ordner}", f"\t\tlineageTag: {_tag(modell, 'measure', name)}"]
    return "\n".join(zeilen) + "\n"


def add_measure(measures_tmdl: str, name: str, block: str) -> str:
    """Measure anhängen oder, falls vorhanden, samt Doku-Block durch den Katalogstand ersetzen.

    Die Measures aus ``NEW_KPI_MEASURES`` gehören dem Codemod: wird eine hitl-KPI im Katalog
    berechenbar, wandert der Platzhalter so ohne Handarbeit zum DAX (24.10.2026, KPI-COM-030).
    """
    m = re.search(rf"(?:^\t///.*\n)*^\tmeasure {re.escape(_col_ref(name))} =.*\n(?:^\t\t.*\n)*",
                  measures_tmdl, re.M)
    if m is None:
        return measures_tmdl.rstrip("\n") + "\n\n" + block
    return measures_tmdl[:m.start()] + block + measures_tmdl[m.end():]


def _nutzungen(modell: str, tabelle: str, spalte: str) -> list[str]:
    """DAX-Ausdrücke und Berichte, die die Spalte nutzen (Beziehungsdateien ausgenommen)."""
    treffer = []
    muster = re.compile(rf"{re.escape(tabelle)}'?\[{re.escape(spalte)}\]")
    for f in (_defn(modell) / "tables").glob("*.tmdl"):
        if muster.search(f.read_text(encoding="utf-8")):
            treffer.append(f.relative_to(REPO).as_posix())
    for f in DIST.glob("*.Report/**/*.json"):
        s = f.read_text(encoding="utf-8")
        if f'"Entity": "{tabelle}"' in s and f'"Property": "{spalte}"' in s:
            treffer.append(f.relative_to(REPO).as_posix())
    return treffer


def soll(modus: str | None = None) -> dict[Path, str | None]:
    """Zielinhalt je betroffener Datei; ``None`` heißt: Datei soll nicht existieren.

    ``modus`` ist der Speichermodus des Mandanten (D-590); ``None`` = Import. Vor jeder neuen
    Tabelle prueft ``speichermodus.pruefe_modell``, ob das Zielmodell ihn tragen kann."""
    from tooling.codegen.speichermodus import konstanten, pruefe_modell
    modus = modus or konstanten()[1]
    dateien: dict[Path, str | None] = {}

    def lesen(p: Path) -> str:
        if p not in dateien:
            dateien[p] = p.read_text(encoding="utf-8")
        return dateien[p]

    for modell, tabelle, alt, neu in RENAMES:
        p = _defn(modell) / "tables" / f"{tabelle}.tmdl"
        dateien[p] = rename(lesen(p), alt, neu, f"{modell}/{tabelle}")

    for modell, tabelle, spalte, beziehung in DROPS:
        genutzt = _nutzungen(modell, tabelle, spalte)
        if genutzt:
            raise ValueError(f"{modell}/{tabelle}[{spalte}] wird noch genutzt: {genutzt}")
        p = _defn(modell) / "tables" / f"{tabelle}.tmdl"
        dateien[p] = drop_column(lesen(p), spalte)
        dateien[_defn(modell) / "relationships" / f"{beziehung}.tmdl"] = None

    vertraege: dict[str, dict] = {}
    for modell, dim, vertrag, fakt, schluessel in NEW_DIMENSIONS:
        v = vertraege.setdefault(vertrag, yaml.safe_load((CONTRACTS / vertrag).read_text(encoding="utf-8")))
        d = _defn(modell)
        pruefe_modell(d, modus)
        dateien[d / "tables" / f"{dim}.tmdl"] = dimension_tmdl(modell, dim, v, modus)
        p = d / "tables" / f"{fakt}.tmdl"
        dateien[p] = add_key_column(lesen(p), schluessel, "OrgKey")
        name = f"{dim}_{fakt}"
        dateien[d / "relationships" / f"{name}.tmdl"] = relationship_tmdl(name, fakt, dim, schluessel)
        m = d / "model.tmdl"
        dateien[m] = add_table_ref(lesen(m), dim, "dim_lane")

    from tooling.generator.enrich_measure_docs import _domain_tables, enrich_columns_text
    for modell, tabelle, vertrag, abschnitt, anker in NEW_TABLES:
        v = vertraege.setdefault(vertrag, yaml.safe_load((CONTRACTS / vertrag).read_text(encoding="utf-8")))
        d = _defn(modell)
        pruefe_modell(d, modus)
        # Spaltenbeschreibungen wie enrich_measure_docs --columns, sonst meldet dessen --check Drift.
        spalten = _domain_tables(modell, CONTRACTS).get(tabelle)
        dateien[d / "tables" / f"{tabelle}.tmdl"] = enrich_columns_text(
            table_tmdl(modell, tabelle, v, modus, abschnitt), spalten)
        m = d / "model.tmdl"
        dateien[m] = add_table_ref(lesen(m), tabelle, anker)
        if abschnitt != "fact":
            continue
        t = next(x for x in v["fact"] if x["name"] == tabelle)
        for c in t["columns"]:
            if not c.get("ref"):
                continue
            name = f"{c['ref']}_{tabelle}"
            dateien[d / "relationships" / f"{name}.tmdl"] = relationship_tmdl(name, tabelle, c["ref"], c["name"])

    for modell, tabelle, vertrag, name, nach in NEW_COLUMNS:
        v = vertraege.setdefault(vertrag, yaml.safe_load((CONTRACTS / vertrag).read_text(encoding="utf-8")))
        t = next(x for x in v["fact"] if x["name"] == tabelle)
        spalte = next(c for c in t["columns"] if c["name"] == name)
        p = _defn(modell) / "tables" / f"{tabelle}.tmdl"
        dateien[p] = add_value_column(lesen(p), spalte, nach)

    for modell, ordner, kpi_ids in NEW_KPI_MEASURES:
        p = _defn(modell) / "tables" / "_Measures.tmdl"
        for kid in kpi_ids:
            kpi = yaml.safe_load((REPO / "core" / "kpi_catalog" / "kpis" / f"{kid}.yaml").read_text(encoding="utf-8"))
            dateien[p] = add_measure(lesen(p), kpi["technical"]["measure_name"], kpi_measure_block(modell, kid, ordner))
    return dateien


def pruefe(schreiben: bool = False, modus: str | None = None) -> list[str]:
    drift = []
    for p, inhalt in sorted(soll(modus).items()):
        ist = p.read_text(encoding="utf-8") if p.exists() else None
        if ist == inhalt:
            continue
        drift.append(p.relative_to(REPO).as_posix())
        if schreiben:
            if inhalt is None:
                p.unlink()
            else:
                p.write_text(inhalt, encoding="utf-8", newline="\n")
    return drift


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--blueprint", type=Path, default=None,
                    help="Bauplan des Mandanten; entscheidet den Speichermodus (D-590). "
                         "Ohne: keine Kapazitaet bekannt → Import (der Modus von dist/)")
    a = ap.parse_args(argv)
    from tooling.codegen.speichermodus import lade_bauplan, mandant_modus
    drift = pruefe(a.write, mandant_modus(lade_bauplan(a.blueprint)))
    if drift and not a.write:
        print(f"[model-alignment] weicht ab ({len(drift)}): {', '.join(drift)} -- --write", file=sys.stderr)
        return 1
    print(f"[model-alignment] {'geschrieben' if drift else 'aktuell'}: {len(drift)} Datei(en)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
