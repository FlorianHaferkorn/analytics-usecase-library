"""provision_apply — emit the live "apply" plan + Fabric MCP / skills integration.

The bridge from *emit* to *apply* (research 2026-07-15 landscape doc §4/§5). Our other
adapters emit tool-free files; this one turns the blueprint into a deterministic, **ordered,
gated** plan of Fabric operations that our own delivery pipeline can execute — via the Fabric
**Core MCP** server, `fab`, or REST — and wires in `microsoft/skills-for-fabric` for
agent-driven delivery.

Honest by construction: the plan (what, in what order, with which dependency) is fully
computed from the IR; every mutating step carries a **gate** (`human` for tenant mutations,
`human-approved` for role grants / deletes) per Microsoft's MCP security guidance — because
MCP standardises no destructive-op safeguard, we add our own. Deliverables to customers stay
tool-free; this apply path is for our delivery only (Official-First boundary).

Emits:
- `apply/APPLY_PLAN.json` — the ordered operation list (machine-readable).
- `apply/APPLY_PLAN.md`   — the same as a human runbook with gates.
- `apply/mcp.json`        — Fabric Core MCP server config (remote endpoint + auth note).
- `apply/_MCP_INTEGRATION.md` — how to wire Core MCP + skills-for-fabric, with guardrails.

This module **does not execute** anything — it only emits text.
"""
from __future__ import annotations

import json
import re

from core.dataarch_engine.blueprint import admin_settings as _admin
from core.dataarch_engine.blueprint.fabric_schedule import (
    BETRIEBSIDENTITAET_TOKEN as IDENTITAET_TOKEN,
)
from core.dataarch_engine.blueprint.fabric_schedule import (
    JOB_TYPE_NOTEBOOK,
    JOB_TYPE_PIPELINE,
)
from core.dataarch_engine.blueprint.governance_strategy import LAKEHOUSE_ROLES, LIFECYCLE_STAGES

#: Unter wem ein Zeitplan angelegt wird (D-537, O-72 eines Kundenprojekts). Der Satz steht an
#: JEDEM Zeitplan-Schritt, weil jeder einzeln im Portal angelegt werden kann — und dort legt
#: ihn an, wer gerade angemeldet ist.
#:
#: Belegt (MS Learn, abgerufen 23.09.2026): Eigentuemer (`owner`) eines Zeitplans ist *„the
#: user identity that created this schedule or last modified it“* (Job Scheduler, Create Item
#: Schedule); die API nimmt Dienstprinzipal und verwaltete Identitaet an. Und: *„Schedules
#: become expired if a user doesn't log in to Fabric for 90 consecutive days“* (Job scheduler
#: in Microsoft Fabric).
ZEITPLAN_IDENTITAET = (f" Unter der Betriebsidentitaet `{IDENTITAET_TOKEN}` anlegen, nicht unter "
                       "einem persoenlichen Konto: Eigentuemer ist, wer den Zeitplan anlegt "
                       "oder zuletzt aendert.")

_NONWORD_RE = re.compile(r"[^a-z0-9]+")

# Settings a standard SPN-driven delivery shows on the checklist regardless of blueprint flags; governance
# and sharing are added per blueprint (see admin_settings.profile_from_blueprint).
_MD_BASELINE_CAPS = {"base", "admin_apis", "cicd_git", "xmla_rw", "mcp_apply", "onelake_external"}

# Core MCP tool surface (research §4 — confirm exact names against the preview server).
CORE_MCP = "https://api.fabric.microsoft.com/v1/mcp/core"

# Der Platzhalter, den ein Aufrufer setzt, der **keinen** Workspace-Namen kennt. Kein Name, sondern
# das Eingeständnis, keinen zu haben — deshalb an einer Stelle benannt statt an dreizehn getippt.
PLACEHOLDER_WORKSPACE = "<workspace>"


def _ident(name: str) -> str:
    return _NONWORD_RE.sub("_", (name or "").lower()).strip("_")


def _dirslug(name: str) -> str:
    # hyphenated slug for filesystem paths — matches provision_transforms._dirslug (mlv/<domain>/ dir)
    return _NONWORD_RE.sub("-", (name or "").lower()).strip("-")


def _unique_workspaces(bp: dict) -> list[tuple[str, str]]:
    seen: dict[str, str] = {}
    for d in sorted(bp.get("mesh", {}).get("domains", []), key=lambda d: d.get("name", "")):
        for ws in d.get("workspaces", []):
            seen.setdefault(ws["name"], ws.get("role", ""))
    return sorted(seen.items())


def _stufenrang(ws: dict) -> int:
    """Position der Stufe in der Foerderkette ``dev < test < prod``.

    Eine unbekannte oder fehlende Stufe sortiert ans Ende: sie ist keine Aussage, und eine
    Aussage zu erfinden waere schlimmer als sie hintanzustellen.
    """
    stufe = (ws.get("stage") or "").strip().lower()
    return LIFECYCLE_STAGES.index(stufe) if stufe in LIFECYCLE_STAGES else len(LIFECYCLE_STAGES)


def gold_workspace_of(bp: dict, domain_name: str | None = None,
                      fallback: str = PLACEHOLDER_WORKSPACE,
                      stage: str | None = None) -> str:
    """Der Workspace, in den ein Gold-Artefakt gehört — aus dem IR, nicht aus einer Annahme.

    Ohne ``domain_name`` der Gold-/Mixed-Workspace des Blueprints (der Einstieg, wenn eine
    Aussage nicht domänengebunden ist). Mit ``domain_name`` der Gold-Workspace **dieser** Domäne.
    ``stage`` waehlt die Umgebung ausdruecklich; ohne Angabe die **unterste vorhandene** Stufe
    der Foerderkette (``dev`` vor ``test`` vor ``prod``).

    Warum das eine eigene Funktion ist: bis 31.07.2026 hat der Apply-Plan alle Gold-Produkte in
    ``target_ws`` importiert — den *ersten* Gold-Workspace. Solange die Konvention einen Workspace
    für alles vorsah, war das unsichtbar richtig. Seit die Governance-Ableitung je Domäne einen
    eigenen Gold-Workspace erzeugt, landeten damit `dim_customer` und `fact_sales_order_item` aus
    Order-to-Cash im Workspace von Finance-GL. Gemessen an einem Zwei-Paket-Lauf: 11 von 11
    Importen in den falschen oder zufällig richtigen Workspace.

    Zweiter Befund, gemessen 12.08.2026 am Kundenmandant-Lauf: die Auswahl nahm den ersten passenden
    Workspace in **Listenreihenfolge** und sah die Stufe gar nicht an. Welche Umgebung getroffen
    wurde, entschied damit die Reihenfolge in den Eingaben — Controlling landete in `[Dev]`, weil
    dort die dev-Kette zuerst steht, Platform in prod, weil dort prod zuerst steht. Ein Plan, der
    in einem Durchgang zwei Umgebungen anfasst, ohne es zu sagen. Jetzt entscheidet die Stufe.
    """
    doms = bp.get("mesh", {}).get("domains", []) or []
    if domain_name is not None:
        doms = [d for d in doms if d.get("name") == domain_name]
    kandidaten = [ws for d in sorted(doms, key=lambda d: d.get("name", ""))
                  for ws in d.get("workspaces", [])]
    if stage is not None:
        gewaehlt = [ws for ws in kandidaten if (ws.get("stage") or "").lower() == stage.lower()]
        kandidaten = gewaehlt or kandidaten
    # Stufe schlaegt Listenreihenfolge; innerhalb einer Stufe bleibt die Reihenfolge stabil.
    kandidaten.sort(key=_stufenrang)
    for ws in kandidaten:
        if ws.get("role") in LAKEHOUSE_ROLES:
            return ws["name"]
    # keine Gold-Rolle deklariert: der unterstufigste Workspace der Domäne, sonst der Fallback
    return kandidaten[0]["name"] if kandidaten else fallback


def _artifact_candidates(gp: str, dom_slug: str, stack: str) -> list[str]:
    """Die Pfade, unter denen ein Gold-Produkt emittiert sein *kann* — in Importreihenfolge.

    Reihenfolge = Vorrang: das Notebook trägt die Transformation, das SQL nur ihre Anweisung.
    Welcher davon existiert, entscheidet der Lauf; hier wird nichts behauptet, sondern geprüft
    (siehe ``build_apply_plan(emitted=…)``).
    """
    return [
        f"notebooks/nb_gold_{_ident(gp)}.Notebook",
        f"transforms/{dom_slug}/silver_to_gold__{_ident(gp)}.sql",
        f"mlv/{dom_slug}/{_ident(gp)}.mlv.sql",
        f"warehouse/{dom_slug}/gold_{_ident(gp)}.sql",
    ]


def _first_present(candidates: list[str], emitted: set[str] | None) -> str | None:
    """Der erste Kandidat, den der Lauf wirklich geschrieben hat — sonst ``None``.

    ``emitted=None`` heisst „der Aufrufer hat den Baum nicht mitgegeben": dann wird **kein** Pfad
    behauptet. Ein Verweis auf eine Datei, die es nicht gibt, ist schlechter als kein Verweis: er
    kostet den Lesenden die Suche und endet trotzdem im Nichts.
    """
    if emitted is None:
        return None
    for c in candidates:
        if c in emitted or any(e.startswith(c + "/") for e in emitted):
            return c
    return None


def effective_workspace(bp: dict, workspace: str | None = None) -> str:
    """Der Workspace-Name, mit dem ein Emitter arbeiten soll.

    Ein gesetzter Name gewinnt — wer ihn übergibt, hat entschieden. Sonst wird er aus dem
    Blueprint gelesen. ``<workspace>`` bleibt nur übrig, wenn das IR selbst keinen kennt.
    """
    if workspace and workspace != PLACEHOLDER_WORKSPACE:
        return workspace
    return gold_workspace_of(bp, fallback=PLACEHOLDER_WORKSPACE)


def build_apply_plan(bp: dict, workspace: str = PLACEHOLDER_WORKSPACE,
                     lakehouse: str = "analytics_gold",
                     stack: str = "fabric", sql_ddl_layers: tuple[str, ...] = (),
                     emitted: set[str] | None = None,
                     semantic_model: bool = False,
                     entscheidungen: dict | None = None) -> list[dict]:
    """Return the ordered, gated apply plan (list of operation dicts).

    Each op: {seq, action, target, tool, gate, rationale, artifact}. ``tool`` names the preferred
    execution surface (core-mcp / fab / rest); ``gate`` is auto | human | human-approved;
    ``artifact`` is the emitted file this step executes — relative to ``render/<stack>/`` — oder
    ``None``, wenn dieser Schritt keine Datei ausführt oder der Lauf sie nicht geschrieben hat.

    ``artifact`` ist die eigentliche Verkettung. Bis 31.07.2026 war der Plan eine Liste von
    **Namen**: „import_item ws-…gold.Workspace/fact_gl_line". Welche der 106 emittierten Dateien
    dieser Schritt importiert, stand nirgends — das war die Handarbeit zwischen Plan und Vollzug.
    ``emitted`` ist der tatsächlich geschriebene Baum (Pfade relativ zu ``render/<stack>/``);
    ohne ihn bleibt ``artifact`` konsequent ``None`` statt einen Pfad zu raten.

    ``sql_ddl_layers`` names the SQL-DDL emitters that were run (``"mlv"`` and/or ``"warehouse"``). Those
    emit ``CREATE`` statements that must be **executed against a SQL endpoint** — not imported as items — so
    for each such layer a ``run_sql_ddl`` step is added per gold product (closing the emit→apply gap the
    generic ``import_item`` step left open). MLV runs once and its refresh is a separate, triggered step (D-529); warehouse DDL
    is re-runnable (``CREATE OR ALTER``-shaped).

    ``entscheidungen`` ist das Profilfeld aus dem Rueckweg der Antwortdatei (C-3,
    ``entscheidungen.<ID>``). Zwei Entscheidungen erreichen den Plan (C-4): ``PLAT-NET``
    (Netzanbindung) als Schritt je Workspace oder je Mandant, und ``PLAT-LHTOPO =
    gold_warehouse`` als zusaetzliches Warehouse im Gold-Workspace. Ohne getroffene
    Entscheidung entsteht **kein** Schritt — die Vorbelegung (oeffentliche Endpunkte, ein
    Lakehouse je Domaene) ist der Plan, wie er ohnehin steht.
    """
    from core.dataarch_engine.blueprint.decision_proposals import entscheidung_fuer

    workspaces = _unique_workspaces(bp)
    gold_ws = [n for n, r in workspaces if r in LAKEHOUSE_ROLES]
    target_ws = gold_ws[0] if gold_ws else (workspaces[0][0] if workspaces else workspace)
    domains = sorted(bp.get("mesh", {}).get("domains", []), key=lambda d: d.get("name", ""))
    ingestion = sorted(bp.get("ingestion", []), key=lambda e: e.get("source", ""))
    gold = sorted(bp.get("medallion", {}).get("gold", {}).get("data_products", []),
                  key=lambda p: p["name"])
    gold_products = [p["name"] for p in gold]
    # gold product → its owning domain slug (for the deterministic emitted .sql path) und dessen
    # Gold-Workspace: das Produkt gehört in den Workspace SEINER Domäne, nicht in den ersten.
    dom_of: dict[str, str] = {}
    ws_of: dict[str, str] = {}
    for d in domains:
        for pn in d.get("data_products", []):
            dom_of.setdefault(pn, _dirslug(d["name"]))
            ws_of.setdefault(pn, gold_workspace_of(bp, d.get("name"), fallback=target_ws))
    # Quelle → Domäne (für den Artefaktverweis der Ingestion-Schritte)
    src_dom: dict[str, str] = {}
    for d in domains:
        for s in d.get("sources", []) or []:
            src_dom.setdefault(s.get("source", ""), _dirslug(d["name"]))

    plan: list[dict] = []
    seq = 0

    def add(action, target, tool, gate, rationale, artifact=None):
        nonlocal seq
        seq += 1
        plan.append({"seq": seq, "action": action, "target": target, "tool": tool,
                     "gate": gate, "rationale": rationale, "artifact": artifact})

    def present(path: str) -> str | None:
        return _first_present([path], emitted)

    for name, role in workspaces:
        add("create_workspace", f"{name}.Workspace", "core-mcp:create-workspace | fab mkdir", "human",
            f"{role} workspace (idempotent: skip if exists)",
            present("terraform/main.tf") or present("provision.sh"))
    # C-4: die Netzanbindung (PLAT-NET) ist eine Entscheidung und kein Schalter. Bis 02.09.2026
    # stand sie nur im Ledger; der Plan kannte keinen Schritt dafuer, also blieb sie beim Aufbau
    # Handarbeit. Jede Option nennt ihre Wirkung im Optionen-Katalog (`decision_proposals`),
    # hier steht der Schritt, den sie im Mandanten kostet. Die Werkzeugspalte nennt die Stelle
    # im Portal; einen REST-Pfad, den kein Lauf gemessen hat, behauptet der Plan nicht.
    # Die Vorbelegung `oeffentlich_twa` erzeugt keinen Schritt: sie ist der Plan, wie er steht.
    netz = entscheidung_fuer(entscheidungen, "PLAT-NET", "")
    if netz == "ip_firewall":
        for name, _role in workspaces:
            add("set_workspace_ip_rules", f"{name}.Workspace — IP-Firewall-Regeln",
                "portal: Workspace-Einstellungen → Netzwerksicherheit → eingehende Regeln",
                "human-approved",
                "Entschieden: PLAT-NET = ip_firewall. Nur die Regelliste kommt hinein, bis 256 "
                "Regeln je Workspace (MS Learn: fabric/security/workspace-ip-firewall); die Liste "
                "ist Teil des Apply-Plans und aendert die Erreichbarkeit — Freigabe noetig.")
    elif netz == "private_link_workspace":
        for name, _role in workspaces:
            add("enable_workspace_private_link", f"{name}.Workspace — Private Link",
                "portal: Workspace-Einstellungen → Netzwerksicherheit → Private Link | Azure: "
                "Private Endpoint",
                "human-approved",
                "Entschieden: PLAT-NET = private_link_workspace. Der private Netzpfad gilt nur "
                "fuer die dokumentierten Item-Typen (MS Learn: fabric/security/security-workspace-"
                "level-private-links-overview); je Workspace wird der Pfad im Plan gefuehrt, weil "
                "zwei Netzpfade nebeneinander betrieben werden.")
    elif netz == "private_link_tenant":
        add("enable_tenant_private_link", "Mandant — Private Link (Tenant-Ebene)",
            "Azure: Private Link Service fuer Fabric + Tenant-Einstellung 'Azure Private Link' | "
            "portal: OneLake catalog → Govern → Configurations → Tenant settings → Advanced "
            "networking (Fallback: Admin-Portal → Tenant settings; sobald Private Link aktiv ist, "
            "gibt es den Govern-Tab nicht mehr, dann bleibt nur das Admin-Portal)",
            "human-approved",
            "Entschieden: PLAT-NET = private_link_tenant. Kostet u. a. Publish-to-Web, Export, "
            "E-Mail-Abonnements, Copilot, Capacity-Metrics-App und tenantuebergreifende Shortcuts "
            "(MS Learn: fabric/security/security-private-links-overview); nachtraeglich nur mit "
            "Neuaufbau der Quellanbindung zu drehen — deshalb vor dem ersten Lakehouse.")
    for name, role in workspaces:
        if role in LAKEHOUSE_ROLES:
            add("create_lakehouse", f"{name}.Workspace/{lakehouse}.Lakehouse", "core-mcp:create-item | fab mkdir",
                "human", "gold lakehouse",
                present("terraform/main.tf") or present("provision.sh"))
    # C-4: PLAT-LHTOPO = gold_warehouse (MS-Muster 2) heisst Bronze und Silber als Lakehouse,
    # Gold als Warehouse — zwei Item-Typen, zwei Werkzeugketten. Das Lakehouse bleibt (die
    # unteren Schichten brauchen es), das Warehouse kommt dazu. Die Gold-DDL laeuft dann als
    # Warehouse-Schicht (`sql_ddl_layers`), das entscheidet der Aufrufer, nicht dieser Schritt.
    if entscheidung_fuer(entscheidungen, "PLAT-LHTOPO", "") == "gold_warehouse":
        for name, role in workspaces:
            if role in LAKEHOUSE_ROLES:
                add("create_warehouse", f"{name}.Workspace/{lakehouse}.Warehouse",
                    "core-mcp:create-item | fab mkdir", "human",
                    "Entschieden: PLAT-LHTOPO = gold_warehouse. Gold als Warehouse fuer "
                    "T-SQL-Serving mit vollem DML; kennt keine Materialized Lake Views, Direct "
                    "Lake auf Warehouse hat eigene Grenzen (MS Learn: fabric/data-warehouse/"
                    "data-warehousing). Nebenwirkung: Schreiben ueber T-SQL erzwingt den "
                    "delegierten Modus, die OneLake-Rollen werden wirkungslos.",
                    present("terraform/main.tf") or present("provision.sh"))
    for d in domains:
        # `preview=false` ist Pflichtparameter (Release-Version); Aufrufer muss Fabric-Administrator
        # sein — Dienstprinzipal wird unterstützt. Geprüft 31.07.2026 gegen
        # learn.microsoft.com/rest/api/fabric/admin/domains/create-domain.
        add("create_domain", f"domain:{d['name']}", "rest:/v1/admin/domains?preview=false", "human",
            "OneLake data-mesh domain — Fabric-Administrator nötig (SPN unterstützt)",
            present("terraform/main.tf") or present("provision.sh"))
        add("assign_domain_workspaces", f"domain:{d['name']}", "rest:.../assignWorkspacesByIds", "human",
            "assign the domain's workspace(s)", present("workspaces.json"))
        # BK-W02. Eigener Schritt und nicht als Nebensatz am Anlegen: die Rollen brauchen eine
        # ANDERE Identitaet (Domain-Admins kann nur ein Fabric-Administrator setzen) und einen
        # Wert, den es beim Anlegen noch nicht gibt — die objectId der Entra-Gruppe.
        if present("governance/governance.sh"):
            add("assign_domain_roles", f"domain:{d['name']} — Domain-Admin/-Contributor",
                "rest:/v1/admin/domains/{id}/roleAssignments/bulkAssign", "human",
                "Domain-Admin ist der fachliche Dateneigentuemer, Contributor haengt Workspaces "
                "ein — ein Contributor muss im Ziel-Workspace zugleich Admin sein",
                present("governance/governance.sh"))
    for e in ingestion:
        mode = e.get("access_mode")
        tool = ("fab mkdir *.MirroredDatabase" if mode == "mirror"
                else "fab ln *.Shortcut" if mode == "shortcut" else "pipeline/dataflow copy")
        # surface the source's authored rationale (which names the concrete connector — ODBC / OData /
        # SAP HANA / Premium Outbound / Mirroring) in the runbook; fall back to a generic note.
        rationale = e.get("rationale") or f"{mode} ingestion for {e.get('source_system', '')}"
        # Copy läuft über die emittierte Pipeline; Mirror/Shortcut über das Provisioning-Skript.
        art = (present("orchestration/pipeline-content.json") if mode == "copy"
               else present("provision.sh")) or present("ingestion_plan.json")
        add("ingest_source", f"{e['source']} ({mode})", tool, "human", rationale, art)
    for gp in gold_products:
        ws = ws_of.get(gp, target_ws)
        add("import_item", f"{ws}.Workspace/{gp}", "core-mcp:create-item | fab import", "human",
            "import generated item definition (transform notebook / pipeline / semantic model / report)",
            _first_present(_artifact_candidates(gp, dom_of.get(gp, "gold"), stack), emitted))
    # D-556: Bronze → Silber hat seit 24.09.2026 eigene Notebooks — ohne Importschritt kaemen
    # sie nie im Mandanten an, und die Pipeline riefe wieder Items auf, die es nicht gibt.
    # Ein Schritt je Domaene (ihr Gold-Workspace traegt das Lakehouse mit Bronze und Silber).
    _b2s: dict[str, list[str]] = {}
    for e in ingestion:
        # D-557: das Periodenfenster einer Quelle gehoert zu ihrer Aufnahme und kommt mit.
        for praefix in ("nb_bronze_to_silver__", "nb_periodenfenster__"):
            nb = f"notebooks/{praefix}{_ident(e.get('source', ''))}.Notebook"
            if emitted is not None and any(x.startswith(nb + "/") for x in emitted):
                _b2s.setdefault(e.get("domain") or "", []).append(nb)
    for dom, nbs in sorted(_b2s.items()):
        ws = gold_workspace_of(bp, dom or None, fallback=target_ws)
        add("import_item", f"{ws}.Workspace/{len(nbs)} Aufnahme-Notebook(s) (Bronze→Silber)",
            "core-mcp:create-item | fab import", "human",
            "import the bronze→silver transform notebooks (one per source; the pipeline calls "
            "them) and any period-window notebook of the ingestion",
            sorted(nbs)[0])
    # B3: die Notebooks tragen ihre Vorgabe-Lakehouse-Bindung als Platzhalter
    # (`<ws-…/lh_…-lakehouse-id>`), weil die GUID erst im Mandanten entsteht. Gemessen 15.08.2026
    # an einem vollen Lauf: 7 Notebooks mit unaufgeloestem Token, kein Schritt, der ihn aufloest.
    # Ungebunden bricht jedes davon mit „No default context found" ab. Das ist kein fehlendes
    # Schemafeld — das Feld ist da und richtig —, sondern ein fehlender Schritt zwischen Import
    # und erstem Lauf. Genau deshalb steht er hier und nicht im Emitter.
    # Gezaehlt werden die Notebook-**Items**, nicht die emittierten Pfade: ein Notebook besteht aus
    # mehreren Dateien, und eine Zahl, die Dateien zaehlt und Notebooks behauptet, ist beim
    # Nachzaehlen im Mandanten sofort falsch.
    notebooks = sorted({e.split(".Notebook", 1)[0] + ".Notebook"
                        for e in (emitted or set())
                        if e.startswith("notebooks/") and ".Notebook" in e})
    if notebooks:
        add("bind_default_lakehouse",
            f"{target_ws}.Workspace — {len(notebooks)} Notebook(s) an {lakehouse}.Lakehouse",
            "portal: Notebook → Lakehouse hinzufuegen | rest:/items/{id}/updateDefinition", "human",
            "Vorgabe-Lakehouse binden. Die Notebook-Definition traegt die Bindung als Platzhalter, "
            "weil die Lakehouse-GUID erst beim Anlegen entsteht; der Import loest sie nicht auf. "
            "Ohne diesen Schritt bricht jedes Notebook beim ersten Lauf mit "
            "'No default context found' ab — nach einem Aufbau, der bis hierhin gruen aussah.",
            present("notebooks"))
    # A.11: MLV und Warehouse materialisieren BEIDE `gold.<produkt>`. Wer den Plan der Reihe nach
    # abarbeitet, bekommt Gold in dem Objekttyp, der zuletzt lief — ohne Fehler und ohne Hinweis.
    # Gemessen 15.08.2026 an einem Lauf mit beiden Schichten: sechs Gold-Produkte, zwoelf DDL-
    # Schritte, dieselben sechs Ziele (`CREATE OR REPLACE MATERIALIZED LAKE VIEW gold.dim_customer`
    # gegen `CREATE TABLE gold.dim_customer`).
    #
    # Welcher Gold-Store gilt, ist eine Architekturentscheidung und wird hier nicht getroffen. Der
    # Plan darf sie aber nicht verstecken: statt zwei Materialisierungen stillschweigend
    # hintereinanderzustellen, steht die Wahl als eigener, freigabepflichtiger Schritt davor.
    doppelt = [lay for lay in ("mlv", "warehouse") if lay in sql_ddl_layers]
    if len(doppelt) > 1 and gold_products:
        add("decide_gold_store",
            f"{target_ws}.Workspace — {len(gold_products)} Gold-Produkt(e) in "
            f"{' + '.join(doppelt)}",
            "human", "human-approved",
            "BEIDE Schichten materialisieren dieselben `gold.<produkt>`-Objekte. Sequenziell "
            "abgearbeitet gewinnt der zuletzt gelaufene Objekttyp, ohne Fehlermeldung. Vor den "
            "folgenden DDL-Schritten entscheiden, welcher Gold-Store gilt, und die Schritte der "
            "anderen Schicht streichen. Nebenwirkung der Wahl: ein Warehouse-Gold macht die "
            "OneLake-Rollen wirkungslos, weil Schreiben ueber T-SQL den delegierten Modus erzwingt.")

    # execute the emitted SQL DDL (MLV / warehouse) — a CREATE statement is run, not imported
    for layer in ("mlv", "warehouse"):
        if layer not in sql_ddl_layers:
            continue
        # D-529: der Refresh einer MLV laeuft NICHT von selbst — er braucht einen Ausloeser, und
        # der ist ein eigener Schritt unten. Und das Ziel ist das **Lakehouse** (Spark SQL):
        # der SQL-Analyseendpunkt ist nur lesend und kennt `CREATE MATERIALIZED LAKE VIEW` nicht.
        once = ("once — the refresh runs only when triggered (step schedule_mlv_refresh)"
                if layer == "mlv" else "re-runnable (idempotent DDL)")
        ziel = "Lakehouse (Spark SQL)" if layer == "mlv" else "SQL endpoint"
        werkzeug = "notebook %%sql | fab" if layer == "mlv" else "fab / rest:/sql/query | notebook %%sql"
        for gp in gold_products:
            # match each emitter's on-disk filename exactly: mlv/<dom>/<p>.mlv.sql · warehouse/<dom>/gold_<p>.sql
            fname = f"{_ident(gp)}.mlv.sql" if layer == "mlv" else f"gold_{_ident(gp)}.sql"
            rel = f"{layer}/{dom_of.get(gp, 'gold')}/{fname}"
            ws = ws_of.get(gp, target_ws)
            add("run_sql_ddl", f"{ws}.Workspace {ziel} ← render/{stack}/{rel}",
                werkzeug, "human",
                f"execute the generated {layer} DDL for '{gp}' against the SQL endpoint — {once}",
                # der Pfad ist hier deklariert, nicht gesucht: die DDL-Schicht lief in diesem Lauf
                present(rel) or rel)
        if layer == "mlv":
            # Der Ausloeser (D-529). Ohne diesen Schritt steht die MLV auf dem Stand ihres
            # CREATE, und nichts wird rot.
            add("schedule_mlv_refresh", f"{target_ws}.Workspace Lakehouse — MLV-Lineage",
                "rest:/workspaces/{id}/lakehouses/{id}/jobs/refreshMaterializedLakeViews/schedules",
                "human",
                "register the MLV refresh schedule (preview API; one active schedule per lineage) "
                "— then trigger once and read the job status, not the 202."
                + ZEITPLAN_IDENTITAET,
                present("mlv/refresh_schedule.json") or "mlv/refresh_schedule.json")
    for d in domains:
        aud = d.get("publishing", {}).get("intended_audience", "internal")
        add("assign_roles", f"{d['name']} workspace roles ({aud})", "rest:/workspaces/{id}/roleAssignments",
            "human-approved", "grant workspace RBAC — permission change, requires explicit approval",
            present("governance/onelake_data_access_roles.json"))

    # A.11, zweite Haelfte: der Plan endete bei den Rollen. Gemessen 14.08.2026 am Lauf, der den
    # Tenant tatsaechlich getragen hat, fehlten darin `DefaultReader` (0 Treffer), Nutzeridentitaet
    # (0), Zeitplan (0), Framing (0) und Semantikmodell (0) — also genau die Schritte, ohne die der
    # Aufbau nicht laeuft oder der Schnitt nicht greift. Jeder Schritt haengt hier an einem
    # Artefakt, das der Lauf erzeugt hat; ohne das Artefakt entsteht der Schritt nicht.
    rollen_datei = present("governance/onelake_data_access_roles.json")
    if rollen_datei:
        # *„lakehouse items have a DefaultReader role that lets users with the ReadAll permission
        # see data in the lakehouse"* und *„To restrict the access to specific users or specific
        # folders, either modify the default role or remove it and create a new custom role"*
        # (MS Learn, OneLake security access control model, gelesen 15.08.2026). Bleibt die
        # Vorgabe-Rolle stehen, laufen die gebauten Rollen ins Leere — ohne Fehlermeldung.
        add("restrict_default_reader", f"{target_ws}.Workspace/{lakehouse}.Lakehouse — DefaultReader",
            "portal: Manage OneLake security | rest:/dataAccessRoles", "human-approved",
            "Vorgabe-Rolle `DefaultReader` einschraenken oder entfernen. Sie gibt jedem Nutzer mit "
            "ReadAll das ganze Lakehouse frei und haengt damit den gebauten Zeilenschnitt aus. "
            "Berechtigungsaenderung, deshalb freigabepflichtig.", rollen_datei)
        # Engine-Tabelle derselben Seite: der SQL-Analytics-Endpunkt setzt RLS/CLS nur im
        # *user's identity access mode* durch (GA). Im delegierten Modus greift der Schnitt dort
        # nicht, waehrend er in Spark und im Lakehouse greift — der unangenehmste Fall, weil er
        # nur an einer von mehreren Oberflaechen fehlt.
        add("set_sql_endpoint_identity_mode", f"{target_ws}.Workspace SQL analytics endpoint",
            "portal: SQL endpoint settings", "human-approved",
            "Endpunkt auf Nutzeridentitaet stellen. Nur in diesem Modus setzt der SQL-Endpunkt "
            "OneLake-RLS/CLS durch; im delegierten Modus sieht dort jeder alles, obwohl Spark und "
            "Lakehouse korrekt schneiden.", rollen_datei)

    zeitplan = present("orchestration/schedule.json")
    if zeitplan:
        add("create_schedule", f"{target_ws}.Workspace — Zeitplan der Pipeline",
            f"rest:/items/{{id}}/jobs/{JOB_TYPE_PIPELINE}/schedules", "human",
            "Zeitplan anlegen. Er steht in der Item-Definition und wird von Git getragen, aber "
            "nicht vom Import angewendet — ohne diesen Schritt laeuft die Kette nur von Hand. "
            "`jobType` ist Pflichtsegment im Pfad, fuer eine DataPipeline lautet es `Pipeline`."
            + ZEITPLAN_IDENTITAET,
            zeitplan)

    # Der Aktivitaetsprotokoll-Export hat seinen eigenen Zeitplan und sein eigenes `jobType`: er
    # laeuft als Notebook, nicht als Pipeline. Ohne diesen Schritt sammelt niemand, und was in
    # seinem Fenster nicht geholt wurde, ist fort — nachholen laesst es sich nicht (BK-B04).
    aktivitaet = present("monitoring/activity_log_export_schedule.json")
    if aktivitaet:
        add("create_schedule", f"{target_ws}.Workspace — Zeitplan des Aktivitaetsprotokoll-Exports",
            f"rest:/items/{{id}}/jobs/{JOB_TYPE_NOTEBOOK}/schedules", "human",
            "Taeglichen Lauf des Export-Notebooks anlegen. `jobType` ist Pflichtsegment und "
            "unterscheidet Gross-/Kleinschreibung; fuer ein Notebook lautet es `RunNotebook`."
            + ZEITPLAN_IDENTITAET,
            aktivitaet)

    # Dieselbe Klasse, anderer Takt: die woechentliche Leistungsmessung (BK-L03). Sie ist
    # nachholbar — anders als das Aktivitaetsprotokoll verschwinden Laufzeiten und Zeilenzahlen
    # nicht nach dreissig Tagen. Was ein ausgefallener Lauf kostet, ist ein Loch im Median, und
    # das Urteil bezieht sich auf den Median.
    leistung = present("day2/leistungsmessung_zeitplan.json")
    if leistung:
        add("create_schedule", f"{target_ws}.Workspace — Zeitplan der Leistungsmessung",
            f"rest:/items/{{id}}/jobs/{JOB_TYPE_NOTEBOOK}/schedules", "human",
            "Woechentlichen Lauf von `day2/leistungsmessung.py` anlegen. Auch hier ist `jobType` "
            "Pflichtsegment und lautet fuer ein Notebook `RunNotebook`."
            + ZEITPLAN_IDENTITAET,
            leistung)

    # Und die Pruefung gegen die drei Betriebsziele (BK-B07). Eigener Zeitplan statt eines
    # zweiten Schritts im Messjob: die Messung sammelt, die Pruefung urteilt. Wer beides in
    # einen Lauf legt, kann das Urteil nicht abschalten, ohne die Sammlung zu verlieren.
    slo = present("day2/slo_pruefung_zeitplan.json")
    if slo:
        add("create_schedule", f"{target_ws}.Workspace — Zeitplan der SLO-Pruefung",
            f"rest:/items/{{id}}/jobs/{JOB_TYPE_NOTEBOOK}/schedules", "human",
            "Woechentlichen Lauf von `day2/slo_pruefung.py` anlegen. Vorher `betriebsziele.json` "
            "mit den Kundenzahlen fuellen — bis dahin urteilt die Pruefung `kein-ziel`."
            + ZEITPLAN_IDENTITAET,
            slo)

    # D-537: die Vorgabe „Betriebsidentitaet ist ein Dienstprinzipal“ steht seit dem 16.08.2026
    # in `provision_day2.VORGABEN` — und kein Schritt des Plans hat sie durchgesetzt. Gemessen
    # in einem Kundenprojekt (23.09.2026, O-72): nach der Inbetriebnahme gehoerten ALLE sechs
    # Zeitplaene (Laden und MLV, drei Stufen) demselben benannten Nutzer. Technisch lief alles;
    # der unbeaufsichtigte Betrieb hing an einer Person. Der Pruefschritt liest den Eigentuemer
    # zurueck, statt ihn aus dem Anlegen zu folgern — eine spaetere Aenderung im Portal macht
    # den Aendernden zum Eigentuemer.
    zeitplan_schritte = [op for op in plan
                         if op["action"] in ("create_schedule", "schedule_mlv_refresh")]
    if zeitplan_schritte:
        add("verify_schedule_owner",
            f"{target_ws}.Workspace — Eigentuemer aus {len(zeitplan_schritte)} Zeitplan-Schritt(en)",
            "rest:GET /workspaces/{id}/items/{id}/jobs/{jobType}/schedules", "human",
            f"Eigentuemer jedes Zeitplans zuruecklesen: `owner.type` = ServicePrincipal und "
            f"`owner.id` = `{IDENTITAET_TOKEN}`. Ein Nutzer als Eigentuemer ist ein Befund, "
            "kein Hinweis — der Zeitplan laeuft ab, wenn dieser Nutzer 90 Tage nicht "
            "angemeldet war, und jede Aenderung im Portal macht den Aendernden zum "
            "Eigentuemer. Eine Workspace-Identitaet ersetzt den Eigentuemer nicht. Nach jeder "
            "Aenderung an einem Zeitplan erneut pruefen.",
            zeitplan_schritte[0].get("artifact"))

    # Das Semantikmodell entsteht im CLI-Ablauf NACH diesem Plan, steht beim Scannen des Baums also
    # noch nicht da. Deshalb haengen die beiden Schritte an der Ansage des Aufrufers und tragen
    # bewusst **keinen** Artefaktverweis: ein Verweis auf eine Datei, die es zur Planzeit nicht gibt,
    # kostet den Lesenden die Suche und endet im Nichts (dieselbe Regel wie in `_first_present`).
    modell = present("tmdl") or present("semantic_layer")
    if modell or semantic_model:
        add("import_item", f"{target_ws}.Workspace/Semantikmodell + Bericht",
            "core-mcp:create-item | fab import", "human",
            "Semantikmodell und Bericht einspielen. Der Plan zaehlte sie bisher nur in der "
            "Begruendung der Gold-Importe mit, ohne eigenen Schritt.", modell)
        # D-540: dieselbe Frage wie beim Zeitplan (D-537), am Modell. Im Kundenprojekt (O-72)
        # waren alle Semantikmodelle von derselben Person konfiguriert. `Default.TakeOver`
        # uebertraegt das Modell *„to the current authorized user“* und ist laut MS Learn fuer
        # Dienstprinzipal-Profile aufrufbar (Datasets - Take Over In Group, abgerufen
        # 23.09.2026). Vor dem Framing, damit schon der erste Refresh unter ihr laeuft.
        add("take_over_semantic_model", f"{target_ws}.Workspace/Semantikmodell — Eigentuemer",
            "rest:POST /groups/{id}/datasets/{id}/Default.TakeOver", "human",
            f"Modell unter der Betriebsidentitaet `{IDENTITAET_TOKEN}` uebernehmen — der Aufruf "
            "uebertraegt es an den, der ihn stellt, also als diese Identitaet aufrufen. Danach "
            "`configuredBy` zuruecklesen (`GET /groups/{id}/datasets/{id}`); eine Person dort ist "
            "ein Befund. Nach jeder Neuveroeffentlichung aus Desktop erneut: wer veroeffentlicht, "
            "wird Eigentuemer.", modell)
        add("frame_direct_lake", f"{target_ws}.Workspace/Semantikmodell — Framing",
            "rest:/datasets/{id}/refreshes | notebook sempy", "human",
            "Nach dem ersten Laden framen. Ein Direct-Lake-Modell liefert den zuletzt geframten "
            "Stand; ohne diesen Schritt zeigt ein technisch gruener Aufbau alte oder leere Daten.",
            modell)
    return plan


def _apply_md(plan: list[dict]) -> str:
    linked = sum(1 for op in plan if op.get("artifact"))
    lines = ["# Apply plan (generated — ADR-0015)", "",
             f"Ordered, gated Fabric operations ({len(plan)}). Gates per Microsoft MCP security guidance:",
             "`human` = tenant mutation (approve before run); `human-approved` = permission change / delete.",
             "",
             f"**Artefakt** nennt die emittierte Datei, die der Schritt ausführt — relativ zu diesem "
             f"Verzeichnisbaum ({linked} von {len(plan)} Schritten). Ein leeres Feld heisst: dieser Schritt "
             "führt keine Datei aus (Tenant-Mutation, Rollenvergabe) oder der Lauf hat sie nicht "
             "geschrieben. Es heisst nicht „irgendwo im Baum“.",
             "", "| # | Action | Target | Artefakt | Tool | Gate |", "|---|---|---|---|---|---|"]
    for op in plan:
        art = f"`{op['artifact']}`" if op.get("artifact") else "—"
        lines.append(f"| {op['seq']} | {op['action']} | `{op['target']}` | {art} | {op['tool']} "
                     f"| **{op['gate']}** |")
    lines.append("")
    return "\n".join(lines) + "\n"


#: Startargumente des lokalen Fabric-MCP — bewusst eng, und warum.
#:
#: Bis 02.08.2026 stand hier `--mode all`. Gegen `fabmcp 1.2.0 --help` gemessen heisst
#: das „exposes all tools individually" und ueberschreibt aktiv den **sichereren
#: Default** des Werkzeugs (`namespace` = ein Tool je Service-Namespace). Gleichzeitig
#: predigte `_MCP_INTEGRATION.md` daneben Least-Privilege. Die Prosa sagte das Richtige,
#: das Artefakt tat das Gegenteil — und dieses Artefakt geht in die Lieferung.
#:
#: Belegt in der Primaerquelle (Fabric Insider Ep. 8 mit Hasan Abo-Shally, PM fuer
#: Fabric MCP Servers & CLI, 29.07.2026): „Each MCP tool declares a risk level …
#: Be intentional about which namespaces you enable for your agent — especially in
#: production environments." Und als Einstiegsempfehlung: „Start with read-only."
#:
#: `--read-only` ist ein echtes Flag des Servers („no write operations will be
#: allowed"), kein Kommentar. Schreibpfade werden nicht hier aufgemacht, sondern
#: bewusst und benannt — siehe `_MCP_INTEGRATION.md` §3.1. Das deckt sich mit unserem
#: eigenen Modell: Lesen und Artefakt-Erzeugung automatisieren, Mandanten-Mutationen
#: und Rollenvergaben human-gated lassen.
LOCAL_MCP_ARGS: list[str] = [
    "-y", "@microsoft/fabric-mcp@latest", "server", "start",
    "--mode", "namespace",
    "--read-only",
]


def _mcp_json() -> str:
    """Both Fabric MCP servers (flexible, general-purpose).

    The supplier keeps a longer setup guide under ``meridian/tool-layers/fabric/mcp/``; it is
    deliberately not referenced from the emitted files, because the customer never receives
    that folder — a delivery that points at a path outside itself is a dead end.
    """
    cfg = {"mcpServers": {
        "fabric-core": {
            "type": "http", "url": CORE_MCP,
            "note": ("Fabric Core MCP (remote, PREVIEW). Live tenant ops: workspace/item/role CRUD. "
                     "Auth: Microsoft Entra OAuth (interactive); respects caller RBAC + audit log. "
                     "No client-side scope switch here — least privilege comes from the Entra "
                     "identity you sign in with, so use a per-environment one.")},
        "fabric-local": {
            "command": "npx",
            "args": list(LOCAL_MCP_ARGS),
            "note": ("Local Fabric MCP (PREVIEW, Node 20+). OneLake/DataFactory ops + create/run "
                     "pipeline + API-spec docs. Auth: Azure identity (az login) for live ops. "
                     "Ships READ-ONLY and namespace-scoped by design; enabling writes is a "
                     "deliberate edit, see _MCP_INTEGRATION.md §3.1.")},
    }}
    return json.dumps(cfg, indent=2, ensure_ascii=False) + "\n"


def _integration_md() -> str:
    return (
        "# Fabric MCP + Skills integration (generated — ADR-0015)\n\n"
        "Wires agent-driven delivery on top of the emitted artifacts (research §4). Deliverables to\n"
        "customers stay tool-free; this is for our own delivery pipeline only (Official-First boundary).\n\n"
        "## 1. Fabric MCP servers (both — flexible, general-purpose)\n"
        f"**fabric-core** (remote HTTP `{CORE_MCP}`) — workspace/item/role CRUD, capacity. Entra OAuth.\n"
        "**fabric-local** (`npx @microsoft/fabric-mcp`) — OneLake/DataFactory ops, create/run pipeline,\n"
        "API-spec docs; `az login` for live ops. Add the `mcp.json` next to this file to your agent\n"
        "config. Not limited to one item — covers any workspace.\n\n"
        "## 2. skills-for-fabric (Claude Code plugin)\n"
        "Adopt `microsoft/skills-for-fabric` — knowledge packs that teach the agent MS-blessed patterns\n"
        "(`@FabricDataEngineer`, `semantic-model-authoring`, `power-bi-report-authoring`). *Skills teach\n"
        "what; MCP does it.* Install via the Claude Code plugin marketplace, then invoke by name.\n\n"
        "## 3. Guardrails (enforced — MS MCP security guidance)\n"
        "- **Least-privilege Entra identity** per environment; rely on Core MCP RBAC + audit logs.\n"
        "- **Service principals do NOT enforce RLS** — keep SP-backed query agents off end-user surfaces.\n"
        "- **Destructive-op gate**: MCP standardises no safeguard for create/delete/role-grant. Run the\n"
        "  apply plan with its gates — `human` steps need approval, `human-approved` (role grants/deletes)\n"
        "  need explicit sign-off. Never auto-run a `human-approved` step.\n"
        "- **Compliance boundary**: MCP clients/models may process data outside Fabric's boundary — vet\n"
        "  per DSGVO (`compliance/`).\n"
        "- **Tenant setting** is the org kill-switch for MCP endpoints.\n\n"
        "### 3.1 Enabling writes (deliberate, never default)\n"
        "The emitted `mcp.json` starts `fabric-local` **read-only** and **namespace-scoped**. That is\n"
        "the server's own safer default (`--mode namespace`) plus its `--read-only` switch — not a\n"
        "convention of ours. Microsoft's guidance is explicit: every MCP tool carries a risk level, and\n"
        "you should be intentional about which namespaces an agent may use, especially in production.\n\n"
        "To let an agent write, change **one** of these — and record why:\n"
        "- drop `--read-only` (allows every write the identity is entitled to), **or**\n"
        "- keep `--read-only` off only for named namespaces: `--namespace NAME` (repeatable), **or**\n"
        "- expose single tools: `--tool TOOL_NAME` (repeatable; implies `--mode all` for those tools).\n\n"
        "Prefer the narrowest that works. Whatever you open stays open for every prompt in that\n"
        "session — including the ones you did not anticipate.\n\n"
        "## 4. From emit to apply\n"
        "Our adapters emit files (`provision.sh`, `terraform/`, `fabric-cicd/`, `transforms/`,\n"
        "`orchestration/`, `governance/`). `APPLY_PLAN.md` is the ordered, gated bridge to executing them\n"
        "via Core MCP / `fab` / REST. Recommended: automate reads + artifact generation; keep tenant\n"
        "mutations and role grants human-gated — exactly our generate → quality-gate → maintainer-merge model.\n")


def _tenant_setup_md(bp: dict) -> str:
    """Admin-settings prerequisites the apply plan depends on — rendered from the cited catalog
    (``admin_settings``), NOT re-listed here (single source of truth). The baseline SPN-delivery settings
    always show; governance/sharing rows are added per blueprint. Each row carries scope (tenant/capacity/
    workspace), who sets it, and how — plus a scriptable-vs-human split so the one-day setup is honest
    about what automates. These must be set BEFORE the apply plan runs.
    """
    caps = _MD_BASELINE_CAPS | _admin.profile_from_blueprint(bp)
    settings = _admin.required_settings(caps)
    lines = [
        "# Admin setup — settings the apply plan depends on (generated — ADR-0015)",
        "",
        f"Rendered from the cited `admin_settings` catalog (grounding {_admin.GROUNDING_DATE}). Set these",
        "BEFORE the apply plan. Scope service-principal settings to a dedicated Entra security group.",
        "",
        "| # | Setting (section) | Scope | Why | Set by · how | Required |",
        "|---|---|---|---|---|---|",
    ]
    for s in settings:
        name = f"**{s['name']}**"
        if s.get("alias"):
            name += f' (formerly "{s["alias"]}")'
        lines.append(f"| {s['id']} | {name} ({s['section']}) | {s['scope']} | {s['why']} | "
                     f"{s['who']} · {s['how']} | {s['required']} |")

    lines += _ki_zugang_zeilen(bp)
    summ = _admin.settability_summary(caps)
    lines += ["", "## Within a day: what scripts vs what needs a human", ""]
    if summ["scriptable"]:
        lines.append("**Scriptable** (Update Tenant Setting API — smoke-test each first): "
                     + ", ".join(f"#{i} {n}" for i, n, _ in summ["scriptable"]) + ".")
    if summ["scriptable_unverified"]:
        lines.append("**Scriptable but API round-trip unconfirmed** (verify per settingName): "
                     + ", ".join(f"#{i} {n}" for i, n, _ in summ["scriptable_unverified"]) + ".")
    if summ["needs_human"]:
        lines.append("**Needs a human** (capacity-admin portal / RBAC grant — no tenant-setting script can "
                     "do these): " + ", ".join(f"#{i} {n}" for i, n, _ in summ["needs_human"]) + ".")
    lines += ["", f"> {summ['api_caveat']}", ""]
    # I-21 W1.7: Pfade aus einer Quelle (admin_settings), Govern zuerst, Admin portal als Fallback.
    lines += _admin.navigation_md()
    lizenzen = _admin.lizenzannahmen(caps)
    if lizenzen:
        # I-21 W5.7: eine Lizenz ist keine Einstellung — sie wird vorgelegt, nicht angenommen.
        lines += ["## Licence assumptions to confirm", "",
                  "These settings only do something for users who hold the licence below. The "
                  "delivery cannot set a licence; confirm each line with the customer.", "",
                  "| # | Setting | Licence assumed |", "|---|---|---|"]
        lines += [f"| {z['id']} | {z['name']} | {z['lizenz']} |" for z in lizenzen]
        lines.append("")
    lines += _procedure_and_limits(caps, bp)
    lines.append("Also grant the SPN read on each ingestion source. See _MCP_INTEGRATION.md for "
                 "guardrails.")
    return "\n".join(lines) + "\n"


def _ki_zugang_zeilen(bp: dict) -> list[str]:
    """D-606: Ziel von #30 und die Copilot-Schalter aus ``platform.ai_zugang`` (``ki_zugang.wirkung``).

    Bis 30.09.2026 stand #30 fuer jede Lieferung als offene Entscheidung da. Jetzt entscheidet der
    Zugangsweg: ``m365_copilot`` → an fuer benannte Gruppen, sonst aus (ab Werk an). Fehlt das Feld
    oder steht ``unbekannt`` darin, ist das Ziel mit aus vorbelegt und die Kundenfrage steht in
    ``platform/SICHERHEITSBASIS.md``, Abschnitt 7."""
    from core.dataarch_engine.blueprint.ki_zugang import wirkung
    w = wirkung(bp)
    ziel = w["m365_schalter"]["ziel"]
    zeilen = ["", "## AI access paths (`platform.ai_zugang`, D-606)", "",
              "Blueprint: " + ", ".join(f"`{z}`" for z in w["zugaenge"])
              + ("" if w["angegeben"] else " (field missing — treated as `unbekannt`)") + ".", "",
              "| Effect | Result |", "|---|---|",
              f"| #30 Fabric data in Microsoft Copilot (M365 admin center) | **{ziel}**"
              + (" — pre-set until the customer answers (question in `platform/SICHERHEITSBASIS.md` §7)"
                 if w["m365_schalter"]["vorbelegt"] else "")
              + (" — named groups, Microsoft 365 Copilot Premium per user" if ziel == "an" else
                 " — recommended; on by default, so it must be switched off (data protection)")
              + " |",
              "| Copilot tenant switches (#8, #9, #31) | "
              + ("in the table above (`fabric_copilot`)" if w["tenant_faehigkeiten"] else
                 "not required — no `fabric_copilot`") + " |",
              "| Copilot preparation (Prep data for AI) | "
              + ("yes — see `platform/SICHERHEITSBASIS.md` §7" if w["copilot_vorbereitung"] else "no")
              + " |",
              "| Fabric IQ MCP setup (delegated only, no service principal) | "
              + ("yes — see `platform/SICHERHEITSBASIS.md` §7" if w["mcp_einrichtung"] else "no")
              + " |"]
    return zeilen


def _procedure_and_limits(caps: set[str], bp: dict | None = None) -> list[str]:
    """Die Settings, bei denen „an" erst der Anfang ist — Verfahren und dokumentierte Grenzen.

    Warum eigener Abschnitt und keine breitere Tabelle: Surge Protection ohne Schwellen ist
    wirkungslos, und Microsoft nennt bewusst keinen Startwert; PIM ohne den Hinweis, dass es den
    Kapazitaets-Admin gar nicht erreicht, laesst eine Luecke wie eine Haertung aussehen. Beides
    passt in keine Tabellenzelle, und beides wegzulassen waere die teurere Variante: eine
    Haertung, deren Grenzen niemand kennt, wird fuer mehr gehalten, als sie ist.
    """
    eintraege = _admin.procedural_settings(caps)
    if not eintraege:
        return []
    out = ["## Where the switch alone is not the answer", "",
           "These settings need a procedure, not a toggle. The limits are MS-documented, not our "
           "caveats — they are what the setting does not cover.", ""]
    for s in eintraege:
        out += [f"### #{s['id']} {s['name']}", ""]
        if s.get("verfahren"):
            out += [s["verfahren"], ""]
        if s.get("grenzen"):
            out += ["**Limits**", ""]
            out += [f"- {g}" for g in s["grenzen"]]
            out.append("")
        if s["id"] == 22 and bp is not None:
            out += _workspace_surge_rows(bp)
        out += [f"Source: {s['source']}", ""]
    return out


def _workspace_surge_rows(bp: dict) -> list[str]:
    """Die Workspace-Ebene von #22 je Workspace dieser Lieferung (Plan I-21 W1.3, 29.09.2026).

    Bis dahin stand die Workspace-Ebene nur als allgemeines Verfahren im Tenant-Setup; welche
    Workspaces der Lieferung betroffen sind, musste der Kapazitaets-Admin selbst zusammensuchen.
    Bewusst **kein** Blueprint-Parameter: es gibt keine Schnittstelle, die den Zustand setzt oder
    liest, und die Obergrenze entsteht erst aus dem Messfenster. Ein Feld im IR haette einen Wert
    behauptet, den kein Emitter anwenden und kein Readiness-Check nachweisen kann. Die Tabelle
    nennt deshalb nur die Workspaces, einen Vorschlag je Stufe und eine offene Spalte fuer die
    Entscheidung.
    """
    zeilen = []
    for d in (bp.get("mesh") or {}).get("domains") or []:
        for w in d.get("workspaces") or []:
            stage = w.get("stage")
            vorschlag = ("*Available* with a CU cap — keeps dev/test load off the capacity"
                         if stage in ("dev", "test") else
                         "*Mission critical* — lifts the workspace cap only (see limits above)")
            zeilen.append(f"| {w['name']} | {stage or 'single stage'} | {vorschlag} | open |")
    if not zeilen:
        return []
    return ["**Workspace level for this delivery** (preview; portal only — no API sets or reads it). "
            "Proposal per stage; the capacity admin decides, and the cap in % follows the first "
            "measurement window:", "",
            "| Workspace | Stage | Proposal | Decision · cap % |", "|---|---|---|---|",
            *zeilen, ""]


def emit_apply(bp: dict, stack: str = "fabric", workspace: str = PLACEHOLDER_WORKSPACE,
               lakehouse: str = "analytics_gold", sql_ddl_layers: tuple[str, ...] = (),
               emitted: set[str] | None = None,
               semantic_model: bool = False) -> dict[str, str]:
    """Return the apply/MCP-integration artifact set (path → content). Fabric-specific.

    ``sql_ddl_layers`` (``"mlv"``/``"warehouse"``) adds ``run_sql_ddl`` steps for the emitted SQL DDL so
    the apply runbook actually deploys it (see ``build_apply_plan``).

    ``emitted`` ist der bis hierhin geschriebene Artefaktbaum (Pfade relativ zu ``render/<stack>/``);
    er verkettet jeden Schritt mit der Datei, die er ausführt. Ohne ihn bleibt die Spalte leer.
    """
    if stack != "fabric":
        return {}
    plan = build_apply_plan(bp, workspace=workspace, lakehouse=lakehouse, stack=stack,
                            sql_ddl_layers=sql_ddl_layers, emitted=emitted,
                            semantic_model=semantic_model)
    return {
        "apply/APPLY_PLAN.json": json.dumps(plan, indent=2, ensure_ascii=False) + "\n",
        "apply/APPLY_PLAN.md": _apply_md(plan),
        "apply/TENANT_SETUP.md": _tenant_setup_md(bp),
        "apply/mcp.json": _mcp_json(),
        "apply/_MCP_INTEGRATION.md": _integration_md(),
    }
