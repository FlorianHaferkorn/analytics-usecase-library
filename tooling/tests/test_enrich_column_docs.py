"""Spalten-``///`` aus dem Datenvertrag im TMDL (W5.6, 29.09.2026).

Festgeschrieben: Vertragsbeschreibung -> ``///``; ohne Beschreibung keine; handgeschriebene
bleibt; eine früher erzeugte wird aus dem Vertrag erneuert. Dazu der Gleichstand von ``dist/``.
Der Verdrahtungstest für ``generate_semantic_model`` ging am 30.09.2026 mit dem Generator ins
Archiv (A-25); ``dist/`` hält jetzt allein ``enrich_measure_docs.py --dist ... --columns``.
"""
from __future__ import annotations

from pathlib import Path

from tooling.generator.enrich_measure_docs import enrich_columns_text, enrich_dist_columns
from tooling.generator_core.ai_description import ColumnDescription, TableDescription

_REPO = Path(__file__).resolve().parents[2]
_CONTRACTS = _REPO / "core" / "data_contracts" / "domains"
_DIST = _REPO / "products" / "fabric" / "powerbi" / "dist"

_TABLE = TableDescription(
    name="fact_x",
    columns=[
        ColumnDescription(name="Amount", data_type="currency", unit="EUR", role="measure",
                          description="Invoiced revenue."),
        ColumnDescription(name="Plain", data_type="text", role="attribute"),
        ColumnDescription(name="Manual", data_type="text", role="attribute",
                          description="Contract text."),
        ColumnDescription(name="Quantity", data_type="decimal", role="measure",
                          description="Units sold."),
    ],
)

_TMDL = (
    "/// Table doc.\n"
    "table fact_x\n"
    "\tcolumn Amount\n\t\tdataType: Decimal\n\t\tsourceColumn: Amount\n"
    "\tcolumn Plain\n\t\tdataType: String\n\t\tsourceColumn: Plain\n"
    "\t/// Hand-written note.\n"
    "\tcolumn Manual\n\t\tdataType: String\n\t\tsourceColumn: Manual\n"
    "\tcolumn 'Sales Units'\n\t\tdataType: Decimal\n\t\tsourceColumn: Quantity\n"
)


def _doc_above(text: str, column_line: str) -> str | None:
    lines = text.splitlines()
    i = lines.index(column_line)
    return lines[i - 1] if lines[i - 1].startswith("\t///") else None


def test_contract_description_becomes_doc_line():
    out = enrich_columns_text(_TMDL, _TABLE)
    assert _doc_above(out, "\tcolumn Amount") == (
        "\t/// Invoiced revenue. Type: currency · Unit: EUR · Role: measure")


def test_no_description_no_doc_line():
    out = enrich_columns_text(_TMDL, _TABLE)
    assert _doc_above(out, "\tcolumn Plain") is None


def test_hand_written_doc_wins():
    out = enrich_columns_text(_TMDL, _TABLE)
    assert _doc_above(out, "\tcolumn Manual") == "\t/// Hand-written note."
    assert "Contract text" not in out


def test_renamed_column_reads_its_source_column():
    out = enrich_columns_text(_TMDL, _TABLE)
    assert _doc_above(out, "\tcolumn 'Sales Units'").startswith("\t/// Units sold.")


def test_alias_column_does_not_inherit():
    tmdl = ("table fact_x\n\tcolumn Amount\n\t\tsourceColumn: Amount\n"
            "\tcolumn AmountAlias\n\t\tsourceColumn: Amount\n")
    out = enrich_columns_text(tmdl, _TABLE)
    assert _doc_above(out, "\tcolumn AmountAlias") is None


def test_idempotent_and_generated_doc_is_refreshed():
    once = enrich_columns_text(_TMDL, _TABLE)
    assert enrich_columns_text(once, _TABLE) == once
    stale = once.replace("Invoiced revenue.", "Old wording.")
    assert enrich_columns_text(stale, _TABLE) == once
    # description removed from the contract -> generated line goes, hand-written stays
    bare = TableDescription(name="fact_x", columns=[ColumnDescription(name="Amount", data_type="currency")])
    out = enrich_columns_text(once, bare)
    assert _doc_above(out, "\tcolumn Amount") is None
    assert _doc_above(out, "\tcolumn Manual") == "\t/// Hand-written note."


def test_table_outside_contract_untouched():
    assert enrich_columns_text(_TMDL, None) == _TMDL


def test_dist_in_sync_with_contracts():
    """dist/ trägt jede Vertragsbeschreibung; sonst ``enrich_measure_docs.py --dist ... --columns``."""
    assert enrich_dist_columns(_DIST, _CONTRACTS, write=False) == []
