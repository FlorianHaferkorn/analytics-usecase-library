"""Tests for the Visual-Library Layer-Tool (task I-5.1).

DoD: a standalone smoke (resolve registry → visual spec, without the ALUCA core)
AND an integrated check (the PBIR emitter only emits visuals the registry
sanctions for each visual's information block). "Visual-Typ fehlt → Katalog-Eintrag"
surfaces as a CatalogGap / non-zero resolve.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from tooling.superversion.layer_tools import visual_idioms as vi
from tooling.superversion.layer_tools import visual_library as vl
from tooling.superversion.targets import pbir


# --- Standalone (Invariant I4: runs against the bare registry) -------------- #

def test_library_loads_blocks():
    lib = vl.VisualLibrary.load()
    assert lib.registry_version
    assert {"status_signal", "time_trend", "variance_explanation",
            "entity_ranking", "detail_matrix"} <= set(lib.blocks)


def test_block_describe_and_default():
    lib = vl.VisualLibrary.load()
    b = lib.block("status_signal")
    assert b.primary_layer == "3s"
    assert "KPI_Cards" in b.slot_compatibility
    assert b.default_visual().pbip_type == "cardVisual"
    assert "cardVisual" in b.allowed_pbip_types()
    # status_signal forbids gauge/pie/radar (evidence-based)
    # `gauge`, nicht `gaugeVisual`: der offizielle Katalog fuehrt den Typ so
    # (gemessen 08.09.2026 gegen @microsoft/powerbi-core-visual-schema 0.1.1).
    # Ein Verbot auf einen Namen, den kein Visual traegt, greift nie — die
    # Registry ist am 08.09. korrigiert worden, dieser Test zog nach.
    assert {"gauge", "pieChart"} <= b.forbidden_pbip_types()


def test_resolve_slot_to_block():
    lib = vl.VisualLibrary.load()
    blocks = lib.blocks_for_slot("KPI_Cards")
    assert [b.block_id for b in blocks] == ["status_signal"]


def test_unknown_block_and_slot():
    lib = vl.VisualLibrary.load()
    with pytest.raises(vl.VisualLibraryError):
        lib.block("does_not_exist")
    assert lib.blocks_for_slot("NoSuchSlot") == []  # catalog gap → empty


def test_catalog_gap_when_block_has_no_visual():
    empty = vl.InformationBlock("x", "", "30s", [], [], allowed_visuals=[], forbidden_visuals=[])
    with pytest.raises(vl.CatalogGap):
        empty.default_visual()


def test_cli_list_and_resolve(capsys):
    assert vl.main(["list"]) == 0
    assert "blocks" in capsys.readouterr().out
    assert vl.main(["resolve", "KPI_Cards"]) == 0
    assert vl.main(["resolve", "NoSuchSlot"]) == 1   # catalog gap → non-zero


# --- Integrated with I-3.3 (PBIR emitter respects the library) -------------- #

def test_pbir_mapping_is_library_sanctioned():
    """Every official PBIR visualType the emitter maps an ALUCA visual_type to
    must be allowed by the registry for that visual's information block."""
    lib = vl.VisualLibrary.load()
    for aluca_type, plan in pbir._PLANS.items():
        block_id = lib.block_for_aluca_visual(aluca_type)
        if block_id is None:
            continue  # chrome/control (e.g. slicer) — no information block
        allowed = lib.block(block_id).allowed_pbip_types()
        assert plan.visual_type in allowed, (
            f"pbir maps {aluca_type} → {plan.visual_type}, not sanctioned by "
            f"block {block_id} (allowed: {sorted(allowed)})"
        )


def test_sanctions_helper():
    lib = vl.VisualLibrary.load()
    assert lib.sanctions("card", "cardVisual")
    assert not lib.sanctions("card", "pieChart")
    assert lib.sanctions("slicer", "anything")  # no block → exempt


def test_third_party_visual_is_rejected_at_load():
    """Doktrin: keine Fremd-Visuals. Erzwungen beim LADEN, nicht nur im Review.

    Bis 01.08.2026 fuehrte `visual_registry.yaml` zwei Eintraege mit
    `pbip_type: custom` — einer davon namentlich `"Enlighten Bullet Chart"`. Das
    Dataclass hatte dafuer ein reguläres Feld `custom_visual_name`, also war der
    Verstoss nicht nur moeglich, sondern vorgesehen.

    Fremd-Visuals kosten Lizenz, brauchen eine Org-Freigabe im Tenant, machen das
    Deliverable tool-abhaengig (Scope-Grenze: der Kunde installiert nichts) und
    aendern Export-/Print-/Mobile-Verhalten. Die Eskalation ist stattdessen
    `render_mode: svg_measure`, danach ein anderes Ziel-Tool.

    Dieser Test prueft den Waechter, nicht die Registry — eine gruene Registry
    beweist nicht, dass der Waechter feuert.
    """
    import textwrap

    import pytest

    from tooling.superversion.layer_tools.visual_library import (
        ThirdPartyVisualError, VisualLibrary)

    for verstoss in ('        custom_visual_name: "Some Marketplace Visual"\n', ""):
        yaml_text = textwrap.dedent("""\
            registry_version: "1.0.0"
            information_blocks:
              - block_id: probe
                purpose: "p"
                primary_layer: "3s"
                slot_compatibility: ["KPI_Cards"]
                page_types: ["T1"]
                allowed_visuals:
                  - visual_id: something
                    pbip_type: custom
            """) + verstoss
        path = Path(tempfile.mkdtemp()) / "visual_registry.yaml"
        path.write_text(yaml_text, encoding="utf-8")
        with pytest.raises(ThirdPartyVisualError) as exc:
            VisualLibrary.load(path)
        assert "probe" in str(exc.value) and "something" in str(exc.value)


def test_committed_registry_declares_no_third_party_visual():
    """Die eingecheckte Registry selbst ist frei von Fremd-Visuals."""
    from tooling.superversion.layer_tools.visual_library import VisualLibrary

    lib = VisualLibrary.load()
    for block in lib.blocks.values():
        for v in block.allowed_visuals:
            assert v.pbip_type != "custom", f"{block.block_id}/{v.visual_id}"
            assert v.render_mode in ("native", "svg_measure"), \
                f"{block.block_id}/{v.visual_id}: unbekannter render_mode '{v.render_mode}'"


def test_primary_connector_floor_is_complete():
    """Power BI ist Pflichtziel — jede analytische Absicht muss dort darstellbar sein.

    Das ist der Boden des Zielbilds fuer den Konnektor, der beim Kunden laeuft. Faellt
    hier ein Block heraus, kann eine Storyline im Hauptwerkzeug nicht ohne Verlust
    dargestellt werden — und zwar still, solange es niemand prueft.
    """
    from tooling.superversion.layer_tools.visual_library import VisualLibrary

    gaps = VisualLibrary.load().floor_gaps("powerbi")
    assert gaps == [], f"Bloecke ohne Power-BI-Darstellung: {gaps}"


def test_known_second_connector_gap_is_exactly_recorded():
    """Der Zweit-Konnektor hat GENAU eine bekannte Luecke — sie ist benannt, nicht geraten.

    `structural_mix` (100%-gestapelte Balken) hat in `translator_evidence.md` keine
    dokumentierte Entsprechung. Sie zu erfinden waere schlimmer als sie zu zeigen:
    eine geratene Zuordnung faellt erst beim Kunden auf.

    Wird die Luecke geschlossen, wird dieser Test rot — das ist Absicht. Dann gehoert
    die Erwartung angepasst und der Fortschritt ist sichtbar, statt in einer
    weichen Zusicherung zu verschwinden.
    """
    from tooling.superversion.layer_tools.visual_library import VisualLibrary

    assert VisualLibrary.load().floor_gaps("evidence") == ["structural_mix"]


def test_extensions_declare_their_fallback():
    """Die Decke ist frei — aber eine Extension muss ihren Boden nennen."""
    from tooling.superversion.layer_tools.visual_library import VisualLibrary

    offen = VisualLibrary.load().extensions_without_fallback()
    assert offen == [], f"Extension ohne aufloesbares `replaces`: {offen}"


def test_pbip_type_alias_stays_backward_compatible():
    """`allowed_pbip_types()` muss identisch zu `allowed_types('powerbi')` bleiben.

    Drei Konsumenten haengen daran (visual_library-CLI, generator_core/ir/specs.py,
    test_template_manifest_alignment). Der Umbau auf `targets` darf sie nicht
    beruehren.
    """
    from tooling.superversion.layer_tools.visual_library import VisualLibrary

    for block in VisualLibrary.load().blocks.values():
        assert block.allowed_pbip_types() == block.allowed_types("powerbi")
        assert block.allowed_pbip_types()


def test_check_floor_cli_fails_on_a_required_connector_gap(capsys):
    """Das Gate muss rot werden koennen — sonst ist sein Gruen wertlos.

    Stage 1 faehrt `visual_library.py check-floor`. Ein Gate, das nie faellt, ist
    von einem fehlenden Gate nicht zu unterscheiden; genau deshalb pruefen die
    folgenden drei Faelle den ROT-Pfad und nicht nur den Gruen-Pfad.
    """
    from tooling.superversion.layer_tools import visual_library as vlib

    # 1) `evidence` als Pflichtziel verlangt -> die bekannte structural_mix-Luecke blockt
    assert vlib.main(["check-floor", "--required", "evidence"]) == 1
    assert "structural_mix" in capsys.readouterr().out

    # 2) --strict macht JEDE Luecke hart, auch ohne --required
    assert vlib.main(["check-floor", "--strict"]) == 1

    # 3) Ein Pflichtziel, das nirgends deklariert ist, ist ein Konfigurationsfehler —
    #    kein "0 Luecken, alles gut". Sonst meldete das Gate Erfolg fuer ein Tool,
    #    ueber das es nichts weiss.
    assert vlib.main(["check-floor", "--required", "gibtesnicht"]) == 1
    assert "gibtesnicht" in capsys.readouterr().out


def test_check_floor_cli_is_green_for_the_mandatory_target():
    """Power BI ist Pflichtziel und vollstaendig — der Standardaufruf ist gruen."""
    from tooling.superversion.layer_tools import visual_library as vlib

    assert vlib.main(["check-floor"]) == 0

# --- Integrated with the idiom library (the tighter, point-wise authority) --- #

def test_pbir_plans_match_governed_idiom_native_type():
    """The registry test above proves the emitted type is in the ALLOWED set. This is
    stronger: for every chart visual_type, the exact PBIR visualType in _PLANS must equal
    the powerbi_native visualType of the governed idiom — so the generator and the idiom
    library can never drift apart (the reconciliation the two 'visual libraries' needed)."""
    for aluca_type, idiom in vi.ALUCA_VISUAL_IDIOM.items():
        assert aluca_type in pbir._PLANS, f"idiom bridge maps {aluca_type} but _PLANS has no such type"
        assert pbir._PLANS[aluca_type].visual_type == vi.native_visual_type(idiom), (
            f"pbir emits {pbir._PLANS[aluca_type].visual_type} for {aluca_type}, but the governed "
            f"idiom '{idiom}' produces {vi.native_visual_type(idiom)}"
        )


def test_every_plan_is_idiom_governed_or_exempt():
    """No chart type may silently escape idiom governance: every _PLANS key is either bridged
    to a governed idiom or explicitly exempt (chrome/container)."""
    for aluca_type in pbir._PLANS:
        assert aluca_type in vi.ALUCA_VISUAL_IDIOM or aluca_type in vi.EXEMPT, (
            f"_PLANS type '{aluca_type}' is neither idiom-governed nor listed EXEMPT in visual_idioms"
        )


def test_idiom_bridge_agrees_with_registry():
    """The two authorities are consistent: the idiom-governed visualType is also in the
    registry's allowed set for that visual_type's block."""
    lib = vl.VisualLibrary.load()
    for aluca_type, idiom in vi.ALUCA_VISUAL_IDIOM.items():
        block_id = lib.block_for_aluca_visual(aluca_type)
        if block_id is None:
            continue
        assert vi.native_visual_type(idiom) in lib.block(block_id).allowed_pbip_types()


def test_native_visual_type_rejects_non_native_idiom():
    with pytest.raises(vi.IdiomBridgeError):
        vi.native_visual_type("lollipop")  # lollipop has no powerbi_native realization


def test_idiom_native_types_are_derived_from_the_whole_library():
    """Coverage is index.yaml-derived, not hand-listed: every native-capable idiom appears."""
    nt = vi.idiom_native_types()
    assert nt["bar_ranking"] == "clusteredBarChart"
    assert nt["column_time"] == "clusteredColumnChart"
    assert nt["donut"] == "donutChart" and nt["scatter"] == "scatterChart"
    assert len(nt) >= 17  # 17 native-capable idioms today


def test_native_idioms_are_reachable_via_plans_or_explicitly_tracked():
    """Every native-capable idiom is either emittable via _PLANS today, or in the tracked
    PLANS_UNREACHABLE set (needs catalog-validated PBIR roles). No silent third case."""
    emitted_types = {p.visual_type for p in pbir._PLANS.values()}
    reachable, gap = set(), set()
    for iid, vt in vi.idiom_native_types().items():
        (reachable if vt in emitted_types else gap).add(iid)
    assert gap == set(vi.PLANS_UNREACHABLE), (
        f"reachability drifted — unreachable now {sorted(gap)}, tracked {sorted(vi.PLANS_UNREACHABLE)}; "
        "add catalog-validated _PLANS roles then update PLANS_UNREACHABLE"
    )
    assert {"line", "bar_ranking", "column_time", "waterfall_pvm", "matrix_evidence"} <= reachable


def test_min_slot_and_purpose_helpers():
    """The generator seam can consult the grid floor and resolve a purpose to its best idiom."""
    cols, rows = vi.min_slot("bar_ranking")
    assert cols >= 2 and rows >= 2
    assert vi.best_idiom_for_purpose("compare_categories") == "bar_ranking"
    with pytest.raises(KeyError):
        vi.best_idiom_for_purpose("nope")


def test_pbir_plans_emit_the_governed_golden_roles():
    """Stronger than the visualType check: every bridged chart's _PLANS roles (primary + dim roles
    + optional secondary measure axis) equal the DATA-ROLE projections of the governed native
    golden — so the generator emits exactly the governed reference's role shape and cannot drift.
    Non-projection queryState keys (e.g. sortDefinition) are chrome, not data roles, and excluded."""
    import json
    from pathlib import Path
    golden_dir = Path(__file__).resolve().parents[3] / "core/templates/page_templates/visual_library/golden"
    for aluca_type, idiom in vi.ALUCA_VISUAL_IDIOM.items():
        d = json.loads((golden_dir / f"{idiom}.powerbi_native.json").read_text(encoding="utf-8"))
        golden_roles = {k for k, v in d["query"]["queryState"].items()
                        if isinstance(v, dict) and v.get("projections")}
        plan = pbir._PLANS[aluca_type]
        plan_roles = {plan.primary_role, *plan.dim_roles}
        if plan.secondary_role:
            plan_roles.add(plan.secondary_role)
        assert plan_roles == golden_roles, (
            f"{aluca_type}→{idiom}: _PLANS roles {sorted(plan_roles)} != "
            f"golden data roles {sorted(golden_roles)}"
        )


def test_visual_type_for_purpose_resolves_best_native_idiom():
    """analytical_purpose seam: a purpose resolves to its best idiom's emittable visual_type, or
    None (→ card) when the best idiom is non-native (svg-dax/table/card)."""
    cases = {
        "time_comparison": "line_chart", "compare_categories": "bar_chart",
        "part_to_whole": "donut", "correlation": "scatter",
        "contribution_to_change": "waterfall", "driver_breakdown": "decomposition_tree",
    }
    for purpose, vt in cases.items():
        got = vi.visual_type_for_purpose(purpose)
        assert got == vt, f"{purpose} -> {got}, expected {vt}"
        assert got in pbir._PLANS, f"{purpose} resolved to non-emittable {got}"
    assert vi.visual_type_for_purpose("value_verdict") is None   # best = kpi_card_spark (non-native)
    assert vi.visual_type_for_purpose("does_not_exist") is None


def test_registry_und_idiom_bibliothek_widersprechen_sich_nicht_beim_nativen_typ():
    """Die fehlende Kante zwischen den zwei Registern — gemessen, nicht vermutet.

    Die Bruecke oben prueft: was der Generator emittiert, entspricht dem nativen Typ des
    Idioms. Sie prueft NICHT die andere Richtung: ob dieser native Typ auch das ist, was
    `visual_registry.yaml` fuer dieselbe `visual_id` sagt. Beide Register nennen dieselbe
    Sache, keins las das andere.

    Was das gekostet hat, gemessen 07.09.2026: die Registry fuehrt seit ADR-0018
    (Accepted 02.08.2026) `small_multiples` mit `pbip_type: lineChart` und dem Zusatz
    `small_multiples: true` — sie wusste also fuenf Wochen lang, dass es ein natives
    lineChart mit Flag ist. Die Idiom-Bibliothek fuehrte dasselbe Idiom bis heute als
    `deneb_vegalite`-only mit `powerbi_native: applicable: false`. Ein Register hatte
    recht, das andere nicht, und nichts stellte sie gegeneinander.

    Die Schnittmenge ist heute klein (2 von 25 bzw. 30), weil die beiden Register
    verschiedene Dinge benennen: die Registry eine erlaubte MENGE je Informationsblock,
    die Bibliothek einen erzeugten PUNKT je Idiom. Wo sich die Namen aber treffen, muessen
    sie dasselbe sagen — und die Schnittmenge waechst, sobald IDs angeglichen werden.
    """
    import yaml
    repo = Path(__file__).resolve().parents[3]
    reg = yaml.safe_load(
        (repo / "core/templates/page_templates/visual_registry.yaml").read_text(encoding="utf-8"))
    erlaubt: dict[str, set] = {}
    for block in reg["information_blocks"]:
        for v in (block.get("allowed_visuals") or []):
            if v.get("pbip_type"):
                erlaubt.setdefault(v["visual_id"], set()).add(v["pbip_type"])

    nativ = vi.idiom_native_types()
    gemeinsam = sorted(set(erlaubt) & set(nativ))
    assert gemeinsam, ("kein gemeinsamer Name mehr — dann prueft dieser Test nichts. "
                       "Entweder wurde eine ID umbenannt oder ein Register geleert.")
    widerspruch = {k: (sorted(erlaubt[k]), nativ[k]) for k in gemeinsam
                   if nativ[k] not in erlaubt[k]}
    assert not widerspruch, (
        "Registry und Idiom-Bibliothek nennen fuer dieselbe visual_id verschiedene native "
        f"Typen (registry, idiom): {widerspruch}")
