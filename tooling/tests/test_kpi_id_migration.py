"""KPI-ID-Migration D-594: Werkzeug (Grenzen der Umschreibung) und migrierter Stand.

Der Meridian-Pruefer (`pruefe_mapping.py`) rechnet gegen die alten IDs und ist nach der
Migration nicht mehr anwendbar. Dieser Test haelt stattdessen den Zielzustand fest: jede neue
ID der freigegebenen Tabelle ist eine Katalogdatei, keine alte ist mehr eine.
"""
from __future__ import annotations

import collections
import json
import os
import re
from pathlib import Path

import pytest
import yaml

from tooling.migration import kpi_id_migration as mig

REPO = Path(__file__).resolve().parents[2]
KPIS = REPO / "core" / "kpi_catalog" / "kpis"
MUSTER = r"^KPI-(COM|FIN|OPS|SCM|SVC|CUS|GOV|PPL|QUA|ESG)-\d{3}$"

# Stand nach der Migration (freigegebene Tabelle, D-594 Nachtrag 3): 139 Bibliotheks-KPIs
# (140 minus CCC-Proxy); die 6 Neuzugaenge aus Aurora/Branchenpaket sind blockiert
# (NEUZUGANG_BLOCKIERT), daher fehlen ESG und je einer in COM/OPS gegenueber 145.
ERWARTET_JE_KUERZEL = {"COM": 31, "CUS": 7, "FIN": 21, "GOV": 7, "OPS": 20, "PPL": 6,
                       "QUA": 6, "SCM": 27, "SVC": 14}

MAPPING = Path(os.environ.get(
    "D594_MAPPING",
    REPO.parent / "Freelancing" / "research" / "2026-09-30_d594_kpi_mapping" / "kpi_id_mapping.yaml"))


def _mini() -> mig.Mapping:
    return mig.Mapping(
        alt_neu={"margin.gm.pct": "KPI-COM-013", "sales.net_sales.amount": "KPI-COM-005",
                 "sales.units": "KPI-COM-020", "wc.ccc.days": "KPI-FIN-006",
                 "ops.working_capital.ccc.days": "KPI-FIN-006",
                 "sales.net_sales.delta_pct": "KPI-COM-021",
                 "sales.net_sales.delta_pct.ly": "KPI-COM-022"},
        entfernt={"ops.working_capital.ccc.days": "wc.ccc.days"})


# --------------------------------------------------------------------------- Grenzen

@pytest.mark.parametrize("vorher, nachher", [
    ("strategic_kpi_id: margin.gm.pct", "strategic_kpi_id: KPI-COM-013"),
    ("`margin.gm.pct`.", "`KPI-COM-013`."),
    ("Δmargin.gm.pct = 0.3 * Δsales.net_sales.amount", "ΔKPI-COM-013 = 0.3 * ΔKPI-COM-005"),
    ("Post_margin.gm.pct - Pre_margin.gm.pct", "Post_KPI-COM-013 - Pre_KPI-COM-013"),
    ("kpis/margin.gm.pct.yaml", "kpis/KPI-COM-013.yaml"),
    # laengste ID zuerst, Fortsetzung mit Punkt ist eine andere ID
    ("sales.net_sales.delta_pct.ly", "KPI-COM-022"),
    ("sales.net_sales.delta_pct.plan", "sales.net_sales.delta_pct.plan"),
    # Spalten, Tabellen und Messgroessen-Schluessel sind keine KPI-IDs
    ("fact_sales.units", "fact_sales.units"),
    ("x.margin.gm.pct", "x.margin.gm.pct"),
    ("margin.gm.pct_old", "margin.gm.pct_old"),
    ("sales_units", "sales_units"),
])
def test_grenzen(vorher, nachher):
    m = _mini()
    assert mig.umschreiben(vorher, "core/x.yaml", m, mig.Muster.aus(m)) == nachher


def test_unterstrich_nur_in_oss():
    m = _mini()
    mu = mig.Muster.aus(m)
    assert mig.umschreiben("```sql margin_gm_pct", "products/open_source_stack/p.md", m, mu) == \
        "```sql kpi_com_013"
    assert mig.umschreiben("data={margin_gm_pct_trend}", "products/open_source_stack/p.md", m, mu) == \
        "data={kpi_com_013_trend}"
    assert mig.umschreiben("- margin_gm_pct", "core/semantic_models/x.yaml", m, mu) == "- margin_gm_pct"


def test_unterstrich_name_gleich_oss_generatoren():
    from products.open_source_stack.tooling.page_generator.sql_builder import SqlBuilder
    for kid in ("KPI-COM-013", "KPI-FIN-006"):
        assert mig.unterstrich_name(kid) == SqlBuilder().kpi_to_query_name(kid) == \
            kid.lower().replace("-", "_").replace(".", "_")


def test_entfernen_liste_mit_ziel_faellt_weg_sonst_umlenken():
    m = _mini()
    mu = mig.Muster.aus(m)
    beide = "order:\n- wc.ccc.days\n- margin.gm.pct\n- ops.working_capital.ccc.days\n"
    nur = "influencing_kpi_ids:\n  - margin.gm.pct\n  - ops.working_capital.ccc.days\n"
    r1 = mig.umschreiben(mig.entferne_zeilen(beide, "a.yaml", m), "a.yaml", m, mu)
    r2 = mig.umschreiben(mig.entferne_zeilen(nur, "b.yaml", m), "b.yaml", m, mu)
    assert r1 == "order:\n- KPI-FIN-006\n- KPI-COM-013\n"
    assert r2 == "influencing_kpi_ids:\n  - KPI-COM-013\n  - KPI-FIN-006\n"


def test_entfernen_tabellenzeile_nur_in_katalog_doku():
    m = _mini()
    zeile = ("| `ops.working_capital.ccc.days` | proxy |\n"
             "| `wc.ccc.days` | exact; twin of ops.working_capital.ccc.days |\n"
             "| Cash Conversion Cycle | `wc.ccc.days` | `ops.working_capital.ccc.days` |\n")
    assert mig.entferne_zeilen(zeile, "core/kpi_catalog/standards/FIN.md", m) == \
        "| `wc.ccc.days` | exact; twin of ops.working_capital.ccc.days |\n"
    assert mig.entferne_zeilen(zeile, "core/usecases/core/X/Business_Factsheet.md", m) == zeile


def test_plan_bezuege_aus_alter_syntax():
    ids = {"sales.net_sales.amount", "sales.net_sales.plan.amount", "margin.gm.pct",
           "margin.gm.vs_plan.pct", "cost.opex.vs_plan.pct"}
    assert mig.plan_bezuege(ids) == {
        "sales.net_sales.amount": {"plan_kpi_ref": "sales.net_sales.plan.amount"},
        "margin.gm.pct": {"plan_variance_kpi_ref": "margin.gm.vs_plan.pct"},
    }


def test_varianz_aus_alter_syntax():
    ids = {"margin.gm.vs_plan.pct", "sales.net_sales.delta_pct.ly", "sales.net_sales.amount",
           "sales.price.realization_pct"}
    assert mig.varianz_ids(ids) == {"margin.gm.vs_plan.pct", "sales.net_sales.delta_pct.ly"}


def test_varianz_feld_im_katalog():
    varianz = sorted(p.stem for p in KPIS.glob("KPI-*.yaml")
                     if yaml.safe_load(p.read_text(encoding="utf-8")).get(mig.VARIANZ_FELD) is True)
    assert len(varianz) == 6, varianz   # 3x vs_plan, 3x delta_pct (alte Syntax)


# --------------------------------------------------------------------------- ein Muster

def test_ein_muster_ueberall():
    """Schema, Stage 1, Taxonomie, Studio: dasselbe ID-Muster, und die Kuerzel sind genau
    die Schluessel von kpi_domains."""
    tax = yaml.safe_load((REPO / "tooling/validation/_index.yaml").read_text(encoding="utf-8"))
    assert tax["id_patterns"]["kpi"]["regex"] == MUSTER
    kuerzel = set(re.search(r"\(([A-Z|]+)\)", MUSTER).group(1).split("|"))
    assert kuerzel == set(tax["kpi_domains"])
    schema = json.loads((REPO / "tooling/generator/schemas/kpi_definition.schema.json").read_text(encoding="utf-8"))
    assert schema["properties"]["kpi_id"]["pattern"] == MUSTER
    planned = json.loads((REPO / "tooling/generator/schemas/planned_kpi.schema.json").read_text(encoding="utf-8"))
    assert planned["items"]["properties"]["kpi_id"]["pattern"] == MUSTER
    ps1 = (REPO / "tooling/validation/validate_kpi_catalog.ps1").read_text(encoding="utf-8")
    assert f"$idRegex = '{MUSTER}'" in ps1
    ts = (REPO / "studio/src/lib/mcp/tools.ts").read_text(encoding="utf-8")
    assert f"const KPI_ID = /{MUSTER}/;" in ts
    assert mig.NEUES_MUSTER.pattern == MUSTER


def test_schwellentext_einheiten_ein_satz():
    """Zwei Formatierer des Trigger-Texts, eine Regel: die frueheren ID-Suffixe bleiben unsichtbar."""
    import sys
    sys.path.insert(0, str(REPO / "products" / "fabric" / "powerbi" / "tooling"))
    from page_scaffold_generator import config_loader
    from tooling.generator_core.ir import compiler
    assert config_loader._SUFFIX_UNITS == compiler.SUFFIX_UNITS
    assert compiler._format_threshold_value(0, "amount", "KPI-COM-010") == "0"
    assert compiler._format_threshold_value(3, "x", "KPI-COM-017") == "3 x"


# --------------------------------------------------------------------------- Zielzustand

def test_katalog_nur_neue_ids():
    dateien = sorted(p for p in KPIS.glob("*.yaml") if p.name != "_index.yaml")
    ids = []
    for p in dateien:
        kid = yaml.safe_load(p.read_text(encoding="utf-8"))["kpi_id"]
        assert re.match(MUSTER, kid), p.name
        assert p.stem == kid, p.name
        ids.append(kid)
    order = yaml.safe_load((KPIS / "_index.yaml").read_text(encoding="utf-8"))["order"]
    assert sorted(order) == sorted(ids) and len(order) == len(set(order))
    assert dict(sorted(collections.Counter(k.split("-")[1] for k in ids).items())) == ERWARTET_JE_KUERZEL


def test_plan_bezuege_zeigen_auf_katalog():
    ids = {p.stem for p in KPIS.glob("*.yaml")}
    felder = 0
    for p in KPIS.glob("KPI-*.yaml"):
        d = yaml.safe_load(p.read_text(encoding="utf-8"))
        for feld, _ in mig.PLAN_FELDER:
            if feld in d:
                felder += 1
                assert d[feld] in ids and d[feld] != d["kpi_id"], p.name
    assert felder == 2   # Net Sales -> Plan-Pegel, GM % -> Plan-Abweichung


@pytest.mark.skipif(not MAPPING.is_file(), reason=f"Mapping-Tabelle nicht erreichbar: {MAPPING} (D594_MAPPING setzen)")
def test_mapping_zielzustand():
    m = mig.lade_mapping(MAPPING)
    ids = {p.stem for p in KPIS.glob("*.yaml")}
    presets = {p.stem for p in (REPO / mig.PRESETS).glob("*.yaml")}
    fehlt = sorted({n for a, n in m.alt_neu.items()} - ids)
    alt = sorted((set(m.alt_neu) & ids) | (set(m.alt_neu) & presets))
    assert not fehlt and not alt, (fehlt, alt)
    neuzugang = sorted(z["neu_id"] for z in m.neuzugaenge)
    assert not set(neuzugang) & ids, "Neuzugaenge sind blockiert (NEUZUGANG_BLOCKIERT)"
    assert mig.check(REPO, m) == []
