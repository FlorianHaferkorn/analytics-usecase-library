"""Jede Vokabularquelle des Repos loest gegen die Registry auf (ADR-0018, Task L2).

Warum dieser Test existiert
---------------------------
ADR-0018 hat `visual_registry.yaml` zur alleinigen Autoritaet fuer das Visualtyp-
Vokabular erklaert. Eine Entscheidung, die niemand prueft, haelt nicht — genau das
war der Zustand VOR dem ADR: drei Listen, keine erzwungen.

Gemessen am 02.08.2026, bevor dieser Test existierte:
  * `usecase_bracket.schema.json` erlaubte **7** Typen, die die Registry nicht kennt
    (`funnel`, `funnel_chart`, `kpi_card_hero`, `kpi_card_compact`, `status_tile`,
    `stacked_bar`, `table_with_databars`)
  * `layout_330300.schema.json` erlaubte drei davon ebenfalls, dazu `detail_table`
  * `stacked_bar` ist in der Registry sogar **ausdruecklich verboten**
    (`structural_mix`: „Shows totals, not shares") — das Autoren-Schema erlaubte also,
    was die Governance untersagt

Keiner der acht war in Gebrauch (0 Deklarationen in 20 Brackets), aber jeder war
deklarierbar — und waere im Compiler auf den stillen `TREND_LINE`-Fallback gelaufen.

Was der Test NICHT tut
----------------------
Er verlangt keine Namensgleichheit. Alt-Token duerfen weiterleben, solange
`LEGACY_TO_REGISTRY` sagt, was sie bedeuten — eine Uebersetzung an genau einer Stelle
ist etwas anderes als zwei konkurrierende Wahrheiten. Und Seitenmoebel (Slicer,
Textfeld, Narrative) sind ueber `CHROME_TOKENS` ausgenommen: die Registry beschreibt
Absichten, ein Slicer beantwortet keine Frage.
"""
from __future__ import annotations

import json
import pathlib

import pytest
import yaml

from tooling.generator_core.ir.specs import VisualType
from tooling.superversion.layer_tools.visual_library import (
    CHROME_TOKENS,
    sync_schemas,
    LEGACY_TO_REGISTRY,
    VisualLibrary,
    canonical_visual_id,
    unresolved_tokens,
)

_ROOT = pathlib.Path(__file__).resolve().parents[3]
_SCHEMAS = _ROOT / "tooling" / "generator" / "schemas"
_BRACKETS = _ROOT / "core" / "usecases" / "core"


def _visual_types(obj) -> set[str]:
    """Alle `visual_type`-Werte in einer beliebig verschachtelten Struktur."""
    out: set[str] = set()
    if isinstance(obj, dict):
        if isinstance(vt := obj.get("visual_type"), str):
            out.add(vt)
        for v in obj.values():
            out |= _visual_types(v)
    elif isinstance(obj, list):
        for v in obj:
            out |= _visual_types(v)
    return out


def _schema_enums(doc) -> set[str]:
    out: set[str] = set()
    if isinstance(doc, dict):
        vt = doc.get("visual_type")
        if isinstance(vt, dict) and isinstance(vt.get("enum"), list):
            out |= {t for t in vt["enum"] if isinstance(t, str)}
        for v in doc.values():
            out |= _schema_enums(v)
    elif isinstance(doc, list):
        for v in doc:
            out |= _schema_enums(v)
    return out


def test_bracket_declarations_resolve_to_the_registry():
    """Kein Bracket deklariert ein Visual, das die Autoritaet nicht kennt."""
    tokens: set[str] = set()
    for p in _BRACKETS.rglob("UseCase_Bracket.yaml"):
        tokens |= _visual_types(yaml.safe_load(p.read_text(encoding="utf-8")) or {})
    assert tokens, "keine Bracket-Deklarationen gefunden — der Test prueft sonst nichts"
    assert unresolved_tokens(tokens) == []


@pytest.mark.parametrize("name", ["usecase_bracket.schema.json",
                                  "layout_330300.schema.json",
                                  "visual_spec.schema.json"])
def test_authoring_schemas_permit_only_sanctioned_visuals(name):
    """Ein Schema darf nicht erlauben, was die Registry nicht sanktioniert.

    Das Autoren-Schema ist das Tor: was hier steht, kann jemand schreiben. Erlaubt es
    mehr als die Registry, ist die Autoritaet aus ADR-0018 eine Behauptung.
    """
    doc = json.loads((_SCHEMAS / name).read_text(encoding="utf-8"))
    assert unresolved_tokens(_schema_enums(doc)) == []


def test_ir_enum_resolves_to_the_registry():
    """Jeder `VisualType` ist entweder ein Registry-Visual oder deklariertes Chrome.

    Der Docstring von `VisualType` behauptet genau das („Values align with … the
    visual_registry.yaml allowed_visuals entries"). Bis heute war das Prosa — und in
    vier Faellen (`kpi_card`, `waterfall`, `horizontal_bar`, `scatter`) schlicht falsch.
    """
    assert unresolved_tokens({m.value for m in VisualType}) == []


def test_legacy_map_points_only_at_real_registry_ids():
    """Die Uebersetzungstabelle darf nicht auf erfundene Ziele zeigen.

    Ohne diese Pruefung koennte ein Tippfehler in `LEGACY_TO_REGISTRY` ein Alt-Token
    „aufloesbar" machen, ohne dass es irgendwo ankommt — die Tabelle wuerde die Luecke
    verstecken, die sie schliessen soll.
    """
    echte = VisualLibrary.load().all_visual_ids()
    erfunden = sorted({z for z in LEGACY_TO_REGISTRY.values() if z not in echte})
    assert erfunden == []


def test_chrome_and_registry_do_not_overlap():
    """Ein Token ist Seitenmoebel ODER Informationsblock-Visual, nie beides.

    Ueberlappten sie, entschiede die Auswertungsreihenfolge, welche Regeln fuer das
    Visual gelten — und die Ausnahme fraesse die Regel.
    """
    doppelt = sorted(CHROME_TOKENS & VisualLibrary.load().all_visual_ids())
    assert doppelt == []


def test_forbidden_visuals_are_not_declarable():
    """Was die Registry verbietet, darf kein Schema erlauben.

    Konkreter Anlass: `stacked_bar` stand im Autoren-Schema und ist in
    `structural_mix` ausdruecklich verboten („Shows totals, not shares; does not answer
    the composition question"). Eine Governance, die das Gegenteil erlaubt, ist keine.
    """
    lib = VisualLibrary.load()
    erlaubt = lib.all_visual_ids()

    # Zwei Fallstricke, beide beim ersten Lauf aufgetreten:
    #
    # 1. Ein Name kann in einem Block verboten und in einem anderen erlaubt sein.
    #    `column_chart` ist in `time_trend` und `entity_ranking` erlaubt; `waterfall`
    #    ist in `root_cause_context` verboten, aber als `waterfall_chart` in
    #    `variance_explanation` der Default. Global verboten ist nur, was NIRGENDS
    #    erlaubt ist.
    # 2. Die Verbotslisten fuehren teils Alt-Namen (`waterfall`, `pie`, `treemap`).
    #    Ohne Kanonisierung vergleicht der Test Schreibweisen statt Visuals und meldet
    #    `waterfall` als global verboten, obwohl es der Default eines Blocks ist —
    #    genau dieser Fehlalarm ist beim ersten Lauf entstanden.
    def kanon(name: str) -> str:
        return canonical_visual_id(name) or name

    verboten = {kanon(v.visual_id) for b in lib.blocks.values()
                for v in b.forbidden_visuals if v.visual_id}
    nur_verboten = verboten - erlaubt
    assert nur_verboten, "keine global verbotenen Visuals — der Test prueft sonst nichts"

    for name in ("usecase_bracket.schema.json", "layout_330300.schema.json",
                 "visual_spec.schema.json"):
        doc = json.loads((_SCHEMAS / name).read_text(encoding="utf-8"))
        treffer = sorted({kanon(t) for t in _schema_enums(doc)} & nur_verboten)
        assert treffer == [], f"{name} erlaubt registry-verbotene Visuals: {treffer}"


def test_canonical_resolves_legacy_and_passes_through_registry_ids():
    assert canonical_visual_id("trend_line") == "line_chart"
    assert canonical_visual_id("waterfall") == "waterfall_chart"
    assert canonical_visual_id("kpi_card") == "kpi_card_with_delta"
    assert canonical_visual_id("line_chart") == "line_chart"      # schon kanonisch
    assert canonical_visual_id("slicer") is None                  # Chrome, kein Visual
    assert canonical_visual_id("gibt_es_nicht") is None


def test_authoring_schemas_are_generated_not_maintained():
    """Die drei Autoren-Schemas werden ERZEUGT, nicht gepflegt (Konsolidierung 02.08.2026).

    Vorher musste ein neuer Visualtyp an **11** Stellen eingetragen werden; drei davon
    waren diese Schema-Enums, und die tragen keine eigene Information — sie wiederholen
    die Registry. Genau daraus entstand der Zustand, dass die Schemas acht Typen
    erlaubten, die die Registry nicht kennt, darunter das ausdruecklich VERBOTENE
    `stacked_bar`.

    Wird dieser Test rot, ist die Registry geaendert und das Schema nicht nachgezogen:
        python tooling/superversion/layer_tools/visual_library.py sync-schemas --write
    """
    geaendert, meldungen = sync_schemas(schreiben=False)
    assert geaendert == 0, (
        "Autoren-Schemas weichen von der Registry ab: " + "; ".join(meldungen))


def test_narrow_fields_stay_narrow():
    """Ein Generator, der ein enges Feld aufweitet, ist kein Gate mehr.

    `component_3s` ist die KPI-Karten-Position — dort gehoert nur, was `status_signal`
    erlaubt; `diagnostics_300s` nur, was `detail_matrix` erlaubt. Beim ersten Lauf des
    Generators bekamen beide das GESAMTE Vokabular (25 statt 2), weil die
    Anwendungsreihenfolge verkehrt war. Der Kommentar beschrieb die Absicht richtig und
    der Code tat das Gegenteil — deshalb steht die Pruefung jetzt hier.
    """
    import json

    from tooling.superversion.layer_tools.visual_library import VisualLibrary

    lib = VisualLibrary.load()
    eng = {
        ("usecase_bracket.schema.json", "component_3s"): "status_signal",
        ("layout_330300.schema.json", "diagnostics_300s"): "detail_matrix",
    }
    for (datei, feld), block_id in eng.items():
        erwartet = sorted(v.visual_id for v in lib.block(block_id).allowed_visuals)
        doc = json.loads((_SCHEMAS / datei).read_text(encoding="utf-8"))
        gefunden = []

        def suche(o, pfad=""):
            if isinstance(o, dict):
                vt = o.get("visual_type")
                if isinstance(vt, dict) and "enum" in vt and feld in pfad:
                    gefunden.append(sorted(vt["enum"]))
                for k, v in o.items():
                    suche(v, f"{pfad}/{k}")
            elif isinstance(o, list):
                for v in o:
                    suche(v, pfad)

        suche(doc)
        assert gefunden, f"{datei}: Feld {feld} nicht gefunden"
        for liste in gefunden:
            assert liste == erwartet, (
                f"{datei}/{feld} erlaubt {len(liste)} Typen, {block_id} sanktioniert "
                f"{len(erwartet)}: {sorted(set(liste) - set(erwartet))}")
