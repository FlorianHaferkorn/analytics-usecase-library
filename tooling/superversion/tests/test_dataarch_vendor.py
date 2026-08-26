"""Der Meridian→ALUCA-Spiegel der offiziell belegten Emitter (SHARED_SUBSTANCE.md §2.1).

Zwei Dinge werden geprüft, und beide sind nötig:

1. **Der Spiegel läuft wirklich.** Ein Vendor-Ordner, der nur importierbar ist, hätte die
   Lücke nicht geschlossen. Deshalb werden die Emitter hier tatsächlich aufgerufen und ihre
   Ausgabe gegen die offiziellen Verträge geprüft (OneLake-``PermissionScope``-Form,
   Monitoring-KQL, ``VACUUM RETAIN``, Managed-Private-Endpoint-Payload).
2. **ALUCAs ``core`` bleibt unberührt.** Die gespiegelten Module importieren einander als
   ``core.dataarch_engine.blueprint.…``; ALUCA benutzt ``core`` selbst als Namespace-Paket.
   Die Import-Brücke darf ``core.brand`` niemals verschatten.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from tooling.superversion import _dataarch_vendor as vendor

VENDOR = vendor.VENDOR_DIR


# -- Integrität des committeten Spiegels ------------------------------------------


def test_pin_covers_every_vendored_module():
    pin = vendor.read_pin()
    on_disk = {p.name for p in VENDOR.glob("*.py")}
    assert {e["path"] for e in pin["files"]} == on_disk
    assert pin["source_repo"] == "Freelancing"


def test_committed_mirror_matches_its_pin():
    assert vendor.integrity_findings(VENDOR, vendor.read_pin()) == []
    assert vendor.available() is True


def test_local_edit_is_refused(tmp_path: Path):
    staged = tmp_path / "m"
    shutil.copytree(VENDOR, staged)
    (staged / "naming.py").write_text("# hand-edited\n", encoding="utf-8")
    findings = vendor.integrity_findings(staged, vendor.read_pin())
    assert any("lokal editiert" in f for f in findings)


def test_missing_file_is_refused(tmp_path: Path):
    staged = tmp_path / "m"
    shutil.copytree(VENDOR, staged)
    (staged / "capacity_recommend.py").unlink()
    findings = vendor.integrity_findings(staged, vendor.read_pin())
    assert any("fehlt im Spiegel" in f for f in findings)


def test_verify_raises_on_divergence(monkeypatch, tmp_path: Path):
    staged = tmp_path / "m"
    shutil.copytree(VENDOR, staged)
    (staged / "naming.py").write_text("# hand-edited\n", encoding="utf-8")
    monkeypatch.setattr(vendor, "VENDOR_DIR", staged)
    monkeypatch.setattr(vendor, "PIN_PATH", VENDOR / "PIN.json")
    with pytest.raises(vendor.VendorUnavailable, match="PIN"):
        vendor.verify()


# -- die Import-Brücke -------------------------------------------------------------


def test_every_promised_function_loads():
    api = vendor.load_emitters()
    expected = {fn for fns in vendor.PUBLIC_API.values() for fn in fns}
    assert set(api) == expected
    assert all(callable(v) for v in api.values())


def test_aluca_core_namespace_survives_the_bridge():
    """Der Finder darf ausschließlich core.dataarch_engine[.blueprint] beantworten."""
    vendor.load_emitters()
    import core.brand  # noqa: F401 — genau das würde ein synthetisches `core` zerstören
    import core  # noqa: F401
    assert Path(core.__path__[0]).name == "core"


def test_bridge_is_installed_only_once():
    vendor.load_emitters()
    vendor.load_emitters()
    import sys
    finders = [f for f in sys.meta_path if isinstance(f, vendor._VendorFinder)]
    assert len(finders) == 1


def test_finder_ignores_unrelated_names():
    vendor.load_emitters()
    import sys
    finder = next(f for f in sys.meta_path if isinstance(f, vendor._VendorFinder))
    for name in ("core", "core.brand", "tooling", "json", "core.dataarch_engineX"):
        assert finder.find_spec(name) is None, f"finder must not claim {name}"


# -- die Emitter laufen wirklich ---------------------------------------------------


_BP = {
    "schema_version": "0.1.0",
    "platform": {"stack": "fabric", "ownership_boundaries": []},
    "ingestion": [
        {"source": "erp_orders", "domain": "Sales", "access_mode": "shortcut",
         "rationale": "virtualize", "sensitivity": "confidential"},
        # A private source, so the Managed-Private-Endpoint path is actually exercised.
        {"source": "crm_accounts", "domain": "Sales", "access_mode": "mirror",
         "source_system": "SQL Server on-prem", "rationale": "CDC mirror",
         "sensitivity": "confidential"},
    ],
    "medallion": {
        "bronze": {"enabled": True, "immutable": True, "append_only": True},
        "silver": {"data_contract_ref": "contracts/sales.yaml"},
        "gold": {"data_products": [
            {"name": "fact_orders", "kind": "fact", "grain": "order line"},
            {"name": "dim_customer", "kind": "dimension"},
        ]},
        "no_layer_skip": True,
    },
    "mesh": {"domains": [{
        "name": "Sales",
        "workspaces": [{"name": "Sales_Gold", "role": "gold"}],
        "publishing": {"endorsement": "certified", "intended_audience": "internal"},
    }]},
    "ai_grounding": {"grounding_surface": ["gold"],
                     "retrieval": [{"domain": "Sales", "strategy": "builtin"}]},
}


@pytest.fixture(scope="module")
def api():
    return vendor.load_emitters()


def _strip_comment_header(text: str) -> str:
    """The emitted payload carries a `//` rationale header above the body.

    That is deliberate: the reasoning must travel with the artifact, but the REST body has
    to stay schema-clean (an unknown field would be rejected). Stripping it here also pins
    that separation — if the comment ever leaked into the body, this would fail.
    """
    lines = text.splitlines()
    body = [l for i, l in enumerate(lines) if not (l.lstrip().startswith("//"))]
    return "\n".join(body)


def test_governance_emits_official_onelake_shape(api):
    out = api["emit_governance"](_BP)
    raw = out["governance/onelake_data_access_roles.json"]
    roles = json.loads(_strip_comment_header(raw))
    assert roles["value"], "no roles emitted"
    for role in roles["value"]:
        # kind must be Policy, and every DecisionRule permission carries exactly the two
        # documented PermissionScope entries (Path + Action) — the shape the API rejects
        # when it is wrong.
        assert role["decisionRules"]
        for rule in role["decisionRules"]:
            scopes = rule["permission"]
            assert len(scopes) == 2
            assert {s["attributeName"] for s in scopes} == {"Path", "Action"}


def test_monitoring_emits_failure_kql(api):
    out = api["emit_monitoring"](_BP)
    blob = "\n".join(out.values())
    assert "ItemJobEventLogs" in blob
    assert "Failed" in blob


def test_lifecycle_emits_delta_maintenance(api):
    out = api["emit_lifecycle"](_BP)
    blob = "\n".join(out.values())
    assert "OPTIMIZE" in blob
    assert "VACUUM" in blob and "RETAIN" in blob


def test_connectivity_emits_managed_private_endpoint_fields(api):
    out = api["emit_connectivity"](_BP)
    blob = "\n".join(out.values())
    assert "targetPrivateLinkResourceId" in blob
    assert "targetSubresourceType" in blob


def test_operability_reports_metadata_completeness(api):
    findings = api["check_metadata_completeness"](_BP)
    assert isinstance(findings, (list, tuple, dict))


def test_decision_proposals_reach_their_lazy_dependencies(api):
    """`propose_all` lazily imports capacity_recommend and admin_settings by their Meridian
    dotted names — the case the bridge exists for."""
    proposals = api["propose_all"](_BP)
    ids = {p["id"] for p in proposals}
    # PLAT-CAP comes from capacity_recommend, PLAT-TENANT from admin_settings — both are
    # reached through a lazy `core.dataarch_engine.blueprint.…` import at call time, which
    # is exactly the case the import bridge exists for.
    assert {"PLAT-CAP", "PLAT-TENANT"} <= ids, f"lazy deps unreachable; got {sorted(ids)}"
    cap = next(p for p in proposals if p["id"] == "PLAT-CAP")
    # A real recommendation, not an empty placeholder.
    assert cap.get("vorschlag") or cap.get("proposal")


def test_decisions_markdown_renders(api):
    md = api["decisions_markdown"](api["propose_all"](_BP))
    assert md.strip()
    assert "|" in md, "expected a table"


# -- Quell-Introspektion: die Frage immer, die Antwort erst wenn sie da ist ----------


_ROWS = ("TABLE_SCHEMA,TABLE_NAME,COLUMN_NAME,DATA_TYPE,IS_NULLABLE\n"
         "dbo,Orders,OrderId,int,NO\n"
         "dbo,Orders,ChangedOn,datetime2,YES\n")


def test_phase_one_emits_a_runnable_statement(api):
    out = api["emit_source_schema"](_BP)
    sql = out["source_schema/queries/erp_orders.sql"]
    assert "INFORMATION_SCHEMA.COLUMNS" in sql
    assert "SELECT" in sql
    # Ohne Antwort bleibt die Quelle sichtbar unbekannt statt still plausibel gefüllt.
    assert not any(p.startswith("source_schema/schemas/") for p in out)
    assert "not yet answered" in out["source_schema/_SOURCE_SCHEMA.md"]


def test_phase_two_needs_the_odcs_alias(api):
    """``source_schema`` importiert ``odcs`` **lazy** — der Fehler fällt erst hier auf,
    nicht beim Import des Spiegels. Ohne die Alias-Brücke wäre Phase 2 tot."""
    out = api["emit_source_schema"](_BP, {"erp_orders": _ROWS})
    schema = json.loads(out["source_schema/schemas/erp_orders.json"])
    columns = {c["name"]: c["logicalType"] for c in schema["schema"][0]["properties"]}
    # Die logischen Typen kommen aus ALUCAs eigenem ODCS-Writer, nicht aus einer zweiten Kopie.
    assert columns == {"OrderId": "integer", "ChangedOn": "date"}


def test_the_alias_points_at_alucas_own_odcs():
    """Kein zweiter ODCS-Writer im Repo: der Spiegel bekommt den vorhandenen untergeschoben."""
    import sys

    vendor.load_emitters()
    aliased = sys.modules["core.dataarch_engine.blueprint.odcs"]
    from tooling.superversion import odcs as aluca_odcs
    assert aliased is aluca_odcs
    assert not (VENDOR / "odcs.py").exists(), "der Alias würde eine vendorte Datei verdecken"


def test_key_and_watermark_stay_candidates(api):
    """INFORMATION_SCHEMA kennt keine Schlüssel — das darf nicht als Tatsache auftauchen."""
    out = api["emit_source_schema"](_BP, {"erp_orders": _ROWS})
    proposals = json.loads(out["source_schema/proposals.json"])
    orders = proposals["sources"]["erp_orders"]["Orders"]
    assert orders["key_candidates"] == ["OrderId"]
    assert orders["watermark_candidates"] == ["ChangedOn"]


# -- Die Vollzugshälfte (26.08.2026) ---------------------------------------------------
#
# Bis hierhin spiegelte ALUCA fünf Betriebs-Belange und emittierte sonst nur die Topologie:
# gemessen 39 Artefakte gegen dieselbe Fixture. Der Rest der offiziell belegten Formen —
# `fab`-Aufrufe, fabric-cicd, Terraform, Variable Library, Copy jobs, Notebooks, Pipelines —
# lag allein in Meridian. Diese Tests halten die erweiterte Fläche fest, und vor allem die
# Zusage, die dabei am leichtesten still bricht: dass ein Emitter ohne Eingabe *gemeldet*
# wird und nicht einfach nichts schreibt.

_VOLLZUG = ("emit_apply", "emit_cicd", "emit_fabric_cicd", "emit_terraform",
            "emit_variable_library", "emit_transforms", "emit_notebooks",
            "emit_orchestration", "emit_ingestion", "emit_lineage", "emit_chargeback",
            "emit_direct_lake_guardrails", "emit_metricflow", "emit_translations",
            "emit_governance_strategy", "emit_prereq", "emit_gates", "emit_fab_commands",
            "emit_ingress_dq", "tables_by_source")


def test_the_execution_half_is_part_of_the_promised_surface(api):
    fehlt = [name for name in _VOLLZUG if name not in api]
    assert fehlt == [], f"zugesagt, aber nicht geladen: {fehlt}"


def test_the_mirror_closes_without_reaching_outside_its_package():
    """Die Hülle wurde gemessen, nicht gegriffen — hier bleibt sie messbar.

    Ein gespiegeltes Modul, das ein nicht gespiegeltes importiert, bricht erst beim ersten
    Aufruf und dann an einer Stelle, die nichts mit dem Spiegel zu tun zu haben scheint.
    """
    import ast

    from tooling.superversion._dataarch_vendor import (
        _ALIASED_CONTRACT_MODULES, _ALIASED_MODULES, VENDOR_DIR)

    pkg = "core.dataarch_engine.blueprint"
    vorhanden = {p.stem for p in VENDOR_DIR.glob("*.py")}
    # Die erlaubten Ausnahmen werden aus dem Loader gelesen, nicht hier nachgetippt: was
    # der Loader nicht unterschiebt, darf der Spiegel nicht importieren. Eine Hand-Liste
    # hier waere in dem Moment falsch, in dem jemand einen Alias entfernt.
    vorhanden |= {a.rsplit(".", 1)[-1] for a in _ALIASED_MODULES}
    erlaubt_absolut = set(_ALIASED_CONTRACT_MODULES)
    fehlend: list[str] = []
    for datei in sorted(VENDOR_DIR.glob("*.py")):
        for knoten in ast.walk(ast.parse(datei.read_text(encoding="utf-8"))):
            if not isinstance(knoten, ast.ImportFrom) or not knoten.module:
                continue
            if knoten.module == pkg:
                ziele = {a.name for a in knoten.names}
            elif knoten.module.startswith(pkg + "."):
                ziele = {knoten.module[len(pkg) + 1:].split(".")[0]}
            elif knoten.module in erlaubt_absolut:
                continue
            elif knoten.module.startswith("core."):
                fehlend.append(f"{datei.name} -> {knoten.module} (ausserhalb des Pakets)")
                continue
            else:
                continue
            fehlend += [f"{datei.name} -> {z}" for z in sorted(ziele - vorhanden)]
    assert fehlend == [], f"Spiegel unvollstaendig: {fehlend}"


def test_the_deriver_itself_is_not_mirrored():
    """ALUCA hat einen eigenen Deriver. Meridians danebenzulegen waere das Doppel-Silo."""
    from tooling.superversion._dataarch_vendor import VENDOR_DIR

    assert not (VENDOR_DIR / "blueprint.py").is_file()
    assert not (VENDOR_DIR / "named_profiles.py").is_file()


def test_the_lazily_imported_contract_classes_actually_resolve():
    """Ein Alias, der nur in einer Tabelle steht, ist eine Behauptung.

    ``provision_governance.model_roles()`` importiert ``core.pbi_engine.parsers.tmdl_parser``
    erst im Funktionsrumpf. Vor dem 26.08.2026 war das in ALUCA ein
    ``ModuleNotFoundError`` — sichtbar erst beim Aufruf, waehrend ``emit_governance`` und
    jeder Modulimport gruen blieben. Der Test ruft die Funktion deshalb wirklich auf,
    statt den Import zu pruefen.
    """
    from tooling.superversion._dataarch_vendor import load_module

    modul = load_module("provision_governance")
    bp = {"mesh": {"domains": [{"name": "Commercial", "data_products": ["fact_sales"]}]}}
    rollen = modul.model_roles(bp, {"fact_sales": ["revenue"]})

    assert [r.name for r in rollen] == ["rls_commercial"]
    rolle = rollen[0]
    assert [t.table for t in rolle.table_permissions] == ["fact_sales"]
    # Der restriktive Platzhalter ist der Kern der Regel: `true` waere von funktionierender
    # Sicherheit nicht zu unterscheiden.
    assert rolle.table_permissions[0].filter_expression.startswith("FALSE()")
    assert [(c.table, c.column, c.metadata_permission) for c in rolle.column_permissions] == [
        ("fact_sales", "revenue", "none")]


def test_the_bridge_does_not_create_a_core_pbi_engine_package():
    """Nur der Blattname wird registriert — ALUCAs ``core`` bleibt unberuehrt.

    Ein synthetisches ``core.pbi_engine`` waere derselbe Fehler, den der Finder oben
    ausdruecklich vermeidet: es verschattet einen Namespace, den ALUCA selbst fuehrt.
    """
    import sys

    from tooling.superversion._dataarch_vendor import load_module

    load_module("provision_governance")
    assert "core.pbi_engine.parsers.tmdl_parser" in sys.modules
    assert "core.pbi_engine" not in sys.modules
    assert "core.pbi_engine.parsers" not in sys.modules
    # ALUCAs eigener Namespace laedt weiter aus dem Repo, nicht aus einem Spiegel.
    import core.brand  # noqa: F401
    assert "analytics-usecase-library" in str(sys.modules["core"].__path__[0])
