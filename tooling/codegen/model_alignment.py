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


def dimension_tmdl(modell: str, name: str, vertrag: dict, modus: str | None = None) -> str:
    """Neue Dimension als TMDL; die Partition folgt dem Speichermodus des Mandanten (D-590).

    ``modus=None`` heisst Import — der Modus von ``dist/`` (kein Bauplan, keine Kapazitaet)."""
    from tooling.codegen.speichermodus import gold_partition, konstanten
    modus = modus or konstanten()[1]
    dim = next(d for d in vertrag["dimension"] if d["name"] == name)
    zeilen = [f"/// {' '.join(dim['description'].split())}", f"table {name}", f"\tlineageTag: {_tag(modell, name)}"]
    for c in dim["columns"]:
        zeilen += [f"\tcolumn {_col_ref(c['name'])}", f"\t\tdataType: {_TYPES[c['type']]}",
                   f"\t\tsourceColumn: {c['name']}", "\t\tsummarizeBy: none"]
        if c.get("role") == "key":
            zeilen += ["\t\tisHidden", "\t\tisAvailableInMDX: false"]
    zeilen += gold_partition(name, "dimensions", modus, einzug="\t\t\t")
    return "\n".join(zeilen) + "\n"


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
