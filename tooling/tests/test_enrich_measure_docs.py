"""Measure-``///`` aus dem KPI-Katalog im TMDL (30.09.2026).

Festgeschrieben: ``--dist`` ersetzt einen Measure-Block durch die Katalog-Projektion nur,
wenn dabei nichts verloren geht (``doc_losses``); sonst bleibt der Block und wird gemeldet.
Dazu der Gleichstand von ``dist/`` mit dem Katalog, analog zu
``test_enrich_column_docs.test_dist_in_sync_with_contracts``.
"""
from __future__ import annotations

from pathlib import Path

from tooling.generator.enrich_measure_docs import doc_losses, enrich_dist_measures, enrich_text_guarded

_REPO = Path(__file__).resolve().parents[2]
_DIST = _REPO / "products" / "fabric" / "powerbi" / "dist"

# Measures, deren dist-Block Information trägt, die der Katalog nicht hat. Sie bleiben, bis
# der Katalog sie führt (Katalogpflege, eigener Schritt); dann fällt der Eintrag hier weg,
# und der Test verlangt das (beide Richtungen werden verglichen).
MEASURE_DOC_EXCEPTIONS: dict[tuple[str, str], dict[str, str]] = {
    ("Commercial", "Volume Effect Amount"): {
        "facet": "Formula",
        "kind": "shortened",
        "grund": "dist_anmerkung_fehlt_im_katalog",
        "beleg": "dist: '— blended plan price (3-way PVM; Mix = residual)'; "
                 "Measure_Dictionary_Commercial expression.logical ohne diese Anmerkung",
        "folgeschritt": "katalogpflege_measure_dictionary_commercial",
    },
    ("Commercial", "Gross Margin %"): {
        "facet": "Grain",
        "kind": "shortened",
        "grund": "dist_aus_anderem_dictionary_eintrag",
        "beleg": "dist-Block = Eintrag Profitability ('month (aggregated from invoice_line)', "
                 "Owner Profitability Analytics); Projektion = Eintrag Commercial ('month')",
        "folgeschritt": "backlog_a4_gross_margin_pct_deduplizieren",
    },
}


def _block(*lines: str) -> list[str]:
    return [f"\t/// {line}" for line in lines]


def test_replaced_value_is_not_a_loss():
    old = _block("Old wording.", "Grain: month · Unit: EUR", "Owner: A · Status: active")
    new = _block("New wording.", "Grain: day · Unit: EUR · Good: higher_is_better",
                 "Owner: B · Status: active · Actions: X-1")
    assert doc_losses("m", old, new) == []


def test_dropped_facet_is_a_loss():
    old = _block("Def.", "Grain: sku_month · Unit: %")
    new = _block("Def.", "Good: lower_is_better")
    assert {(x.facet, x.kind) for x in doc_losses("m", old, new)} == {
        ("Grain", "dropped"), ("Unit", "dropped")}


def test_shortened_value_is_a_loss_but_trailing_period_is_not():
    old = _block("Def.", "Formula: A / B  — note on B")
    assert [(x.facet, x.kind) for x in doc_losses("m", old, _block("Def.", "Formula: A / B"))] == [
        ("Formula", "shortened")]
    assert doc_losses("m", _block("Def.", "Formula: A / B."), _block("Def.", "Formula: A / B")) == []


def test_removed_action_and_extra_line_are_losses():
    old = _block("Def.", "Second free line.", "Owner: A · Actions: X-1, X-2")
    new = _block("Def.", "Owner: A · Actions: X-1")
    assert {(x.facet, x.kind) for x in doc_losses("m", old, new)} == {
        ("Actions", "actions_removed"), ("line", "line_removed")}


def test_warning_lines_are_not_compared():
    old = _block("Def.", "[!] MISSING source")
    assert doc_losses("m", old, _block("Def.")) == []


def test_guarded_enrich_keeps_a_richer_block():
    text = ("table _Measures\n"
            "\t/// Gross margin divided by net sales.\n"
            "\t/// Grain: month (aggregated from invoice_line) · Unit: %\n"
            "\tmeasure 'Gross Margin %' = DIVIDE ( [a], [b] )\n")
    out, losses = enrich_text_guarded(text, _REPO)
    assert out == text
    assert [(x.measure, x.facet, x.kind) for x in losses] == [("Gross Margin %", "Grain", "shortened")]


def test_guarded_enrich_replaces_a_stale_block():
    text = "table _Measures\n\t/// stale\n\tmeasure 'Gross Margin %' = DIVIDE ( [a], [b] )\n"
    out, losses = enrich_text_guarded(text, _REPO)
    assert losses == []
    assert "/// stale" not in out and "/// Formula:" in out


def test_dist_measures_in_sync_with_catalog():
    """dist/ trägt die Katalog-Projektion jedes Measures; Ausnahmen nur aus der Liste oben.
    Sonst ``enrich_measure_docs.py --dist products/fabric/powerbi/dist``."""
    changed, kept = enrich_dist_measures(_DIST, _REPO, write=False)
    assert changed == []
    assert {k: {(x.facet, x.kind) for x in v} for k, v in kept.items()} == {
        k: {(e["facet"], e["kind"])} for k, e in MEASURE_DOC_EXCEPTIONS.items()}
