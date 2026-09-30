"""provision_monitoring — emit operational monitoring & alerting from a blueprint.

Closes the observability gap: the platform got provisioned, transformed, governed — but nothing
watched it at runtime. This turns the blueprint's workspaces + schedule into the monitoring layer,
at the fidelity Fabric actually supports (grounded in MS Learn 2026-07: *Create alerts for pipeline
runs*, *What is Fabric Activator?*, *Monitor Fabric Capacity Health*, *Well-Architected — operational
excellence*):

- **Pipeline / job failures (workspace-wide)** → enable **workspace monitoring** (job logs land in a
  monitoring Eventhouse) + one **Activator** rule over an `ItemJobEventLogs` **KQL Queryset** — a
  single rule catches every pipeline / refresh / notebook failure, instead of per-item alerts.
- **Scheduled pipeline failures (built-in)** → *Failure notifications* (email / groups), set **on the
  item** and covering all its schedules — the zero-infra first line. No API field exists for it; the
  evidence path is the Monitoring hub's *Schedule failures* page (preview). See
  ``_pipeline_failure_runbook`` for the measurement behind both statements (Z11).
- **Capacity throttling** → an Activator rule over **Capacity Overview Events** on
  `backgroundRejectionThresholdPercentage` (and the interactive delay/rejection siblings).

Honest by construction: the KQL query is a real, deployable artifact; Activator rules + workspace-
monitoring enablement are **portal/config** actions (no clean deterministic create API), so they are
emitted as structured rule **specs** + an ordered runbook, never as a faked API call. Alert
recipients come from the caller's ``alerts`` map (never invented) or stay ``<VERIFY>`` placeholders.

This module **does not execute** anything — it only emits text.
"""
from __future__ import annotations

import json
import re
from core.dataarch_engine.blueprint.fabric_schedule import (
    JOB_TYPE_NOTEBOOK,
    emit_schedule,
    schedule_endpoint,
)
from core.dataarch_engine.blueprint.stack_capabilities import gap_doc_for

_NONWORD_RE = re.compile(r"[^a-z0-9]+")


def _dirslug(name: str) -> str:
    return _NONWORD_RE.sub("-", (name or "").lower()).strip("-")


def _domains(bp: dict) -> list[dict]:
    return sorted(bp.get("mesh", {}).get("domains", []), key=lambda d: d.get("name", ""))


def _recipients(alerts: dict, key: str) -> list[str]:
    """Recipients for a severity/channel from the caller's map; a VERIFY placeholder if unset."""
    r = (alerts or {}).get(key) or (alerts or {}).get("default") or ["<VERIFY: alert recipient email/Group>"]
    return sorted(dict.fromkeys(r))                       # dedup, deterministic


def _workspace_failures_kql() -> str:
    """A KQL Queryset over ItemJobEventLogs catching ALL failed jobs workspace-wide (pipeline / refresh
    / notebook). Grounded verbatim-shape in MS Learn (workspace-level alerts). Real, deployable.

    Seit den Activator-Job-Alerts im Monitor hub (I-21 W1.6) ist die Regel fuer deren neun Jobtypen
    der **Fallback**; fuer semantische Modelle, Dataflow Gen2 und Copy job bleibt sie die einzige
    (``job_alerts.json`` → ``nicht_abgedeckt``)."""
    return (
        "// Workspace-wide job failures — deploy as a KQL Queryset, then bind an Activator rule to it.\n"
        "// Prereq: enable Workspace monitoring (writes ItemJobEventLogs into the monitoring Eventhouse).\n"
        "// Catches pipeline, semantic-model refresh and notebook job failures in one rule.\n"
        "// Since the Monitor hub job alerts (preview): fallback for the nine job types listed in\n"
        "// job_alerts.json; the only rule for semantic models, Dataflow Gen2 and Copy job.\n"
        "ItemJobEventLogs\n"
        "| extend SecondsAgo = datetime_diff('second', now(), ingestion_time())\n"
        "| where JobStatus == 'Failed'\n"
        "| where SecondsAgo <= 540   // Activator must poll more often than this window\n"
        "| order by Timestamp desc\n"
        "| project Timestamp, JobType, ItemName, WorkspaceName, JobStartTime, JobEndTime, JobStatus\n"
    )


#: Standard-Aufbewahrung der Workspace-Monitoring-Daten. **Standard, nicht fest:** die Aufbewahrung
#: ist eine Datenrichtlinie der Monitoring-KQL-Datenbank (Manage → Data policies) und aenderbar
#: (MS Learn ``fundamentals/enable-workspace-monitoring``, gelesen 29.09.2026). Bis 29.09.2026
#: stand hier „Fest, nicht einstellbar (BK-B01)" — Abweichung benannt (Plan I-21 W1.6 d).
WORKSPACE_MONITORING_RETENTION_DEFAULT_DAYS = 30

#: Grenze je Ziel-Workspace: jede Quelle bekommt dort eine eigene KQL-Datenbank, und jede zaehlt
#: auf das Item-Limit (MS Learn, gelesen 29.09.2026).
WORKSPACE_ITEM_LIMIT = 1000

TOPOLOGIEN = ("zentral", "je-workspace")

#: Die drei Kennzahlen, die Learn fuer die Kapazitaetsvorlage nennt (Tutorial
#: ``real-time-hub/tutorial-monitor-capacity-threshold``, gelesen 29.09.2026). Andere Namen
#: werden abgewiesen: ein Tippfehler waere eine Regel, die nie feuert.
CAPACITY_ALERT_METRICS: dict[str, str] = {
    "backgroundRejectionThresholdPercentage":
        "Hintergrundoperationen werden unter Kapazitaetsdruck abgewiesen",
    "interactiveDelayThresholdPercentage":
        "interaktive Operationen werden verzoegert (Berichte langsam)",
    "interactiveRejectionThresholdPercentage":
        "interaktive Operationen werden abgewiesen (Berichte scheitern)",
}

#: 80 ist im Learn-Tutorial ausdruecklich ein **Beispielwert** („Adjust this threshold based on
#: your operational policy"). Er steht hier als Vorbelegung, uebersteuerbar ueber die Politik.
CAPACITY_ALERT_DEFAULT_THRESHOLD = 80

CAPACITY_STATES = ("Any state change", "Overloaded", "Active", "Suspended", "Deleted")

#: Jobtypen der Activator-Job-Alerts (MS Learn ``admin/monitoring-hub-alerts``, gelesen
#: 29.09.2026, Abschnitt „Requirements for Activator-based alerts"). Reihenfolge wie dort.
JOB_ALERT_TYPES: tuple[str, ...] = (
    "Pipeline", "Spark job", "Notebook", "User data function", "Warehouse", "Lakehouse",
    "Mirrored database", "SQL database", "KQL database",
)

#: Was die Job-Runs-Seite zeigt, die Job-Alerts aber nicht abdecken, soweit es in dieser
#: Lieferung laeuft (Vergleich ``admin/monitoring-hub-jobs`` gegen ``admin/monitoring-hub-alerts``,
#: beide gelesen 29.09.2026). Fuer diese Typen bleibt die KQL-Queryset-Regel die einzige.
JOB_ALERT_NOT_COVERED: tuple[str, ...] = ("Semantic model", "Dataflow Gen2", "Copy job")

JOB_ALERTS_PATH = "monitoring/job_alerts.json"
MONITORING_ITEM_PATH = "monitoring/workspace_monitoring_item.json"
CAPACITY_ALERTS_RUNBOOK_PATH = "monitoring/capacity_alerts.md"
#: Item-Definition des Operations Agents (I-21 W6.4): der einzige Definitionsteil laut Learn.
#: Seit D-597 (30.09.2026) **je Stufe** eine Datei: die Datenquelle nennt den Workspace im
#: Klartext, und die Stufen-Workspaces heissen nach der Namenskonvention verschieden.
OPERATIONS_AGENT_DIR = "monitoring/operations_agent"


def operations_agent_path(stufe: str) -> str:
    """Pfad der Agent-Definition einer Stufe (D-597)."""
    return f"{OPERATIONS_AGENT_DIR}/{stufe}/Configurations.json"

# Die Bibliothek, gegen die die Datenquelle des Operations Agents aufloest (I-21 W6.4). Name und
# Variable stehen einmal hier; Definition, Runbook und emittierte Bibliothek lesen sie von hier.
MONITORING_VARLIB = "vl_monitoring"
MONITORING_KQL_VARIABLE = "monitoring_kql_database"
MONITORING_VARLIB_REFS = [
    {"name": MONITORING_KQL_VARIABLE, "cat": "items", "key": MONITORING_KQL_VARIABLE,
     "note": "KQL database of the workspace-monitoring Eventhouse (not the Eventhouse itself) - "
             "data source of the operations agent."},
]

#: Learn ``rest/api/fabric/articles/item-management/definitions/operations-agent-definition``,
#: gelesen 29.09.2026. ``validation rejects unknown values`` — daher geschlossene Mengen.
OPERATIONS_AGENT_DATASOURCE_TYPES: tuple[str, ...] = ("KustoDatabase", "Ontology")
OPERATIONS_AGENT_ACTION_KINDS: tuple[str, ...] = ("PowerAutomateAction", "FabricJobAction")
OPERATIONS_AGENT_DESTINATION_KINDS: tuple[str, ...] = ("Recipient", "TeamsChannel")
#: Sponsor-Arten, die diese Lieferung zulaesst. ``person`` ist bewusst nicht dabei.
OPERATIONS_AGENT_SPONSOR_ARTEN: tuple[str, ...] = ("gruppe", "spn")
_VARIABLE_REF_RE = re.compile(r"^\$\(/[^/()]+/[^/()]+/[^/()]+\)$")

#: Die Monitoring-Politik: alles, was vor der Anlage entschieden sein muss oder als Schwelle
#: gilt. ``None`` heisst **offen** — irreversible Optionen bekommen keine stille Vorbelegung.
MONITORING_POLITIK_VORGABE: dict = {
    "aufbewahrung_tage": WORKSPACE_MONITORING_RETENTION_DEFAULT_DAYS,
    "cache_tage": None,
    "topologie": "zentral",
    "zentral_workspace": None,
    "diagnosedaten": True,
    "ki_untersuchungen": None,
    "custom_endpoint": None,
    "kapazitaet_schwellen": {m: CAPACITY_ALERT_DEFAULT_THRESHOLD for m in CAPACITY_ALERT_METRICS},
    "kapazitaet_zustand": "Overloaded",
    "operation_events": False,
    "operations_agent_sponsor": None,
}


def monitoring_politik(politik: dict | None = None) -> dict:
    """Politik mit Vorgaben aufgefuellt und geprueft. Ein Verstoss bricht ab (``ValueError``):
    ein falsch angelegtes Monitoring-Item ist in zwei Punkten nicht mehr zu korrigieren."""
    roh = dict(politik or {})
    fehler: list[str] = []
    for k in sorted(set(roh) - set(MONITORING_POLITIK_VORGABE)):
        fehler.append(f"unbekannter Schluessel {k!r}")
    p = {**MONITORING_POLITIK_VORGABE, **roh}
    if "kapazitaet_schwellen" in roh:            # uebergeben heisst: genau diese Regeln
        p["kapazitaet_schwellen"] = dict(roh["kapazitaet_schwellen"] or {})
    tage = p["aufbewahrung_tage"]
    if not isinstance(tage, int) or isinstance(tage, bool) or tage < 1:
        fehler.append(f"aufbewahrung_tage muss eine ganze Zahl >= 1 sein, ist {tage!r}")
    cache = p["cache_tage"]
    if cache is not None and (not isinstance(cache, int) or isinstance(cache, bool) or cache < 0
                              or (isinstance(tage, int) and cache > tage)):
        fehler.append(f"cache_tage muss zwischen 0 und aufbewahrung_tage liegen "
                      f"(Learn: caching <= retention), ist {cache!r}")
    if p["topologie"] not in TOPOLOGIEN:
        fehler.append(f"topologie muss eine von {TOPOLOGIEN} sein, ist {p['topologie']!r}")
    for k in ("diagnosedaten", "ki_untersuchungen", "custom_endpoint"):
        if p[k] not in (True, False, None):
            fehler.append(f"{k} muss true, false oder null (offen) sein, ist {p[k]!r}")
    for m, wert in p["kapazitaet_schwellen"].items():
        if m not in CAPACITY_ALERT_METRICS:
            fehler.append(f"kapazitaet_schwellen: {m!r} ist keine dokumentierte Kennzahl "
                          f"({', '.join(CAPACITY_ALERT_METRICS)})")
        elif not isinstance(wert, (int, float)) or isinstance(wert, bool) or wert <= 0:
            fehler.append(f"kapazitaet_schwellen[{m!r}] muss eine Zahl > 0 sein, ist {wert!r}")
    if p["kapazitaet_zustand"] is not None and p["kapazitaet_zustand"] not in CAPACITY_STATES:
        fehler.append(f"kapazitaet_zustand muss einer von {CAPACITY_STATES} oder null sein")
    if not isinstance(p["operation_events"], bool):
        fehler.append("operation_events muss true oder false sein")
    sp = p["operations_agent_sponsor"]
    if sp is not None:
        if (not isinstance(sp, dict) or not isinstance(sp.get("alias"), str)
                or not sp.get("alias", "").strip()
                or sp.get("art") not in OPERATIONS_AGENT_SPONSOR_ARTEN):
            fehler.append("operations_agent_sponsor muss {alias: <Text>, art: "
                          f"{'|'.join(OPERATIONS_AGENT_SPONSOR_ARTEN)}}} sein — eine Person als "
                          f"Sponsor ist nicht zulaessig, ist {sp!r}")
    if fehler:
        raise ValueError("Monitoring-Politik ungueltig: " + "; ".join(fehler))
    return p


def _capacity_alert_spec(capacity: str, alerts: dict, politik: dict) -> dict:
    """Kapazitaetsalarme als Vorlagen-Spezifikation (I-21 W1.2). Eine Quelle fuer JSON und Runbook.

    Belegt (MS Learn, gelesen 29.09.2026: ``real-time-hub/set-alerts-fabric-capacity-overview-
    events``, ``tutorial-monitor-capacity-threshold``, ``set-alerts-fabric-capacity-operation-
    events``): der Dialog **Set capacity alert** hat drei Vorlagen; die Metrik-Vorlage fuellt
    Monitor und Bedingung vor, gruppiert je ``capacityId`` — ein Alarm je Ueberschreitung statt
    Dauerfeuer. Voraussetzung: keine Trial-Kapazitaet, Rolle Capacity Admin.

    Kein Emitter fuer das Activator-Item: die Reflex-Definition ist per *Create Item* anlegbar,
    aber fuer die Template-Instanzen empfiehlt Learn selbst, im Portal zu bauen und die Definition
    danach mit *Get Item Definition* zu holen. Ein erzeugtes ``ReflexEntities.json`` waere geraten.
    """
    regeln: list[dict] = [
        {"vorlage": "Alert when a capacity metric exceeds a threshold", "when": m,
         "condition": "increases to or above", "value": wert,
         "meaning": CAPACITY_ALERT_METRICS[m]}
        for m, wert in sorted(politik["kapazitaet_schwellen"].items())
    ]
    if politik["kapazitaet_zustand"]:
        regeln.append({"vorlage": "Alert when a capacity changes state", "when": "capacityState",
                       "condition": "changes to", "value": politik["kapazitaet_zustand"],
                       "meaning": "Zustandswechsel der Kapazitaet (Microsoft.Fabric.Capacity.State)"})
    op = {
        "status": "Preview", "aktiv": politik["operation_events"],
        "quelle": "Capacity operation events (Microsoft.Fabric.CapacityOperationEvents.Operation)",
        "gruppierung": ["workspaceId", "itemId", "operationName"],
        "messgroessen": ["capacityUnitMs", "durationMs", "throttlingDelayMs", "status"],
        "vorfilter": ["itemKind", "utilizationType", "status"],
        "vorfilter_pflicht": True,
        "hinweis": ("Ein Ereignis je Operation, hohes Volumen: vor der Bedingung filtern und "
                    "gruppieren, sonst Alarmsturm (Learn). Schwellen je Operation sind "
                    "Kundenangaben und stehen hier bewusst nicht vorbelegt."),
    }
    return {
        "_note": ("Author in Real-Time Hub → Fabric events → Capacity overview events → Set alert "
                  "(template dialog). Runbook: capacity_alerts.md. No create-API emitted, see "
                  "create_api."),
        "source": "Capacity Overview Events",
        "capacity": capacity,
        "groupingField": "capacityId",
        "voraussetzungen": {"kapazitaet": "keine Trial-Kapazitaet", "rolle": "Capacity Admin"},
        "rules": regeln,
        "action": {"type": "email", "to": _recipients(alerts, "capacity"),
                   "subject": "Fabric Capacity Throttling Alert",
                   "headline": "Capacity threshold exceeded",
                   "note": "Capacity exceeded rejection threshold: @backgroundRejectionThresholdPercentage%",
                   "alternativen": ["Teams message", "Run function (UDF)", "Run Fabric item"]},
        "escalation": "Optionally set action=Run function (UDF) for auto-mitigation (pause/resume, scale).",
        "oap": ("Liegt die Activator-Regel in einem Workspace mit Outbound Access Protection, "
                "braucht er die Datenverbindungsregel fuer den Connector „Real-Time Events\" — "
                "sonst ist der workspaceuebergreifende Ereignisbezug gesperrt (Learn)."),
        "historie": ("Die Ereignisse werden nicht rueckwirkend gefuellt. Wer spaeter Verlaeufe "
                     "zeigen will, leitet sie frueh per Eventstream in ein Eventhouse (Learn)."),
        "create_api": {
            "emitter": False,
            "grund": ("Reflex-Definition per Create Item dokumentiert, Template-Instanzen nicht: "
                      "Learn empfiehlt, im Portal zu bauen und Get Item Definition zu nutzen. "
                      "SPN-Eigentuemerschaft: UNKLAR, Tenant-gated."),
        },
        "operation_events": op,
    }


def _capacity_throttling_rule(capacity: str, alerts: dict, politik: dict | None = None) -> str:
    """Activator rule spec over Capacity Overview Events as JSON (see ``_capacity_alert_spec``)."""
    spec = _capacity_alert_spec(capacity, alerts, monitoring_politik(politik))
    return json.dumps(spec, indent=2, ensure_ascii=False) + "\n"


def _capacity_alerts_md(capacity: str, alerts: dict, politik: dict) -> str:
    """``capacity_alerts.md`` — das Runbook mit den exakten Vorlagenwerten, aus derselben
    Spezifikation gerendert wie das JSON (eine Quelle, zwei Formen)."""
    spec = _capacity_alert_spec(capacity, alerts, politik)
    an = ", ".join(f"`{r}`" for r in spec["action"]["to"])
    z = [
        f"# Kapazitaetsalarme fuer `{capacity}`", "",
        "Angelegt im Real-Time Hub, nicht per API: **Real-Time → Fabric events → Capacity "
        "overview events → Set alert**. Der Dialog *Set capacity alert* bietet Vorlagen; "
        "je Zeile unten eine Regel.", "",
        "Voraussetzungen: keine Trial-Kapazitaet, Rolle **Capacity Admin** auf der Kapazitaet.", "",
        "| Vorlage | Kennzahl / Feld | Bedingung | Wert | Bedeutung |", "|---|---|---|---|---|",
    ]
    for r in spec["rules"]:
        z.append(f"| {r['vorlage']} | `{r['when']}` | {r['condition']} | {r['value']} | "
                 f"{r['meaning']} |")
    z += [
        "",
        f"Bedingung vorbefuellt, gruppiert je `{spec['groupingField']}`: ein Alarm je "
        "Ueberschreitung, kein Dauerfeuer, solange der Wert oben bleibt.",
        f"Aktion: **Send email** an {an}, Betreff „{spec['action']['subject']}\", Headline "
        f"„{spec['action']['headline']}\". Im Notizfeld `@backgroundRejectionThresholdPercentage` "
        "eintippen statt einfuegen, sonst wird die Variable nicht befuellt.", "",
        f"Der Wert {CAPACITY_ALERT_DEFAULT_THRESHOLD} ist im Learn-Tutorial ein Beispielwert. "
        "Abweichende Schwellen gehoeren in die Monitoring-Politik (`kapazitaet_schwellen`), nicht "
        "in den Dialog allein — sonst weicht die Lieferung vom Mandanten ab, ohne dass es "
        "jemand sieht.", "",
        "## Ablageort und Netz", "",
        f"- {spec['oap']}",
        f"- {spec['historie']}",
        "- Speicherort: ein Activator-Item im Monitoring-Workspace, nicht auf der ueberwachten "
        "Kapazitaet, wo die Topologie das erlaubt.", "",
        "## Capacity operation events (Preview)", "",
    ]
    op = spec["operation_events"]
    if op["aktiv"]:
        z += [f"Aktiv. Gruppierung je {', '.join(f'`{g}`' for g in op['gruppierung'])}, "
              f"Messgroessen {', '.join(f'`{m}`' for m in op['messgroessen'])}. Vorher filtern "
              f"nach {', '.join(f'`{f}`' for f in op['vorfilter'])}.", "", op["hinweis"]]
    else:
        z += ["Nicht aktiv (`operation_events: false`). Einschalten erst mit Filter und "
              "Kundenschwelle je Operation: ein Ereignis je Operation, hohes Volumen."]
    z += ["", "## Warum kein Skript", "", spec["create_api"]["grund"]]
    return "\n".join(z) + "\n"


#: Entscheidungen am Monitoring-Item, die nach der Anlage nicht mehr zu aendern sind oder die
#: Anlage selbst binden (Learn ``fundamentals/enable-workspace-monitoring`` und
#: ``workspace-monitoring-overview``, beide gelesen 30.09.2026). Als Feld, damit ein Test sie
#: zaehlen kann und das Runbook sie nicht nur im Fliesstext traegt.
MONITORING_UNVERAENDERLICH: tuple[dict, ...] = (
    {"punkt": "ziel", "regel": "Ziel (this vs. another Monitoring Item) ist nach der Anlage nicht "
     "aenderbar", "beleg": "„You can't change the destination after you configure workspace "
     "monitoring.\""},
    {"punkt": "region", "regel": "Ziel in einem anderen Monitoring Item nur bei gleicher Azure-"
     "Region beider Workspaces", "beleg": "„Both workspaces must be in the same Azure region.\""},
    {"punkt": "item_limit", "regel": "je Quell-Workspace eine KQL-Datenbank im Ziel-Workspace, "
     f"zaehlt gegen dessen {WORKSPACE_ITEM_LIMIT}-Item-Grenze", "beleg": "„Each database counts "
     "toward the destination workspace's item limit.\""},
    {"punkt": "custom_endpoint", "regel": "Custom Endpoint nur bei der Anlage aktivierbar (Preview)",
     "beleg": "„Through the preview period, this setting can only be enabled at creation time.\""},
    {"punkt": "operations_agent", "regel": "Operations Agent nach Aktivierung nicht abschaltbar — "
     "erst nach Freigabe (DSGVO/Copilot) anlegen", "beleg": "„If you enable the Operations "
     "Agent, you can't disable it later.\""},
)


def region_pruefung(bp: dict, politik: dict) -> dict:
    """Gleiche Azure-Region fuer ``topologie: zentral`` — gemessen an den Kapazitaeten im Bauplan.

    Ein Workspace liegt in der Region seiner Kapazitaet (Kapazitaet je Workspace aus
    ``kapazitaet_stufen.zuordnung``, Region aus ``platform.capacities[].region``). Liegt der
    zentrale Monitoring-Workspace im Bauplan, zaehlt seine Kapazitaet mit; sonst ist seine Region
    offen. ``status``: ``gleich`` | ``abweichend`` | ``unbekannt`` | ``nicht_anwendbar``.
    """
    from core.dataarch_engine.blueprint.kapazitaet_stufen import zuordnung

    if politik["topologie"] != "zentral":
        return {"status": "nicht_anwendbar", "regionen": {}, "ohne_region": []}
    kaps = {str(k.get("name")): str(k.get("region") or "").strip()
            for k in (bp.get("platform") or {}).get("capacities") or [] if k.get("name")}
    regionen: dict[str, list[str]] = {}
    ohne: list[str] = []
    for r in zuordnung(bp):
        reg = kaps.get(r["kapazitaet"] or "", "")
        if reg:
            regionen.setdefault(re.sub(r"\s+", "", reg).lower(), []).append(r["workspace"])
        else:
            ohne.append(r["workspace"])
    zentral_ws = politik.get("zentral_workspace")
    zentral_bekannt = any(r["workspace"] == zentral_ws for r in zuordnung(bp))
    if len(regionen) > 1:
        status = "abweichend"
    elif ohne or not regionen or not zentral_bekannt:
        status = "unbekannt"
    else:
        status = "gleich"
    return {"status": status, "regionen": {k: sorted(v) for k, v in sorted(regionen.items())},
            "ohne_region": sorted(ohne),
            "zentral_workspace_im_bauplan": zentral_bekannt}


def _monitoring_item_spec(bp: dict, politik: dict) -> dict:
    """``workspace_monitoring_item.json`` — das Monitoring-Item als Spezifikation (I-21 W1.6).

    Belegt (MS Learn, gelesen 29.09.2026, ``fundamentals/enable-workspace-monitoring`` und
    ``workspace-monitoring-overview``): *Workspace settings → Monitoring* legt ein Monitoring-Item
    an (Eventhouse mit schreibgeschuetzter KQL-Datenbank, Eventstream, Activator, optional
    Operations Agent); Datensammlung ist bei der Anlage aus, kein Backfill; das Ziel ist nicht
    aenderbar; Learn empfiehlt ein zentrales Eventhouse auf eigener Kapazitaet.
    """
    quellen = [d["name"] for d in _domains(bp)]
    zentral = politik["topologie"] == "zentral"
    opt = {
        "diagnosedaten": {
            "wert": politik["diagnosedaten"], "vorgabe_microsoft": True, "reversibel": True,
            "hinweis": ("Audit-, Compliance-Logs, Telemetrie. Hoehere Ingestion-Kosten auf der "
                        "Kapazitaet; fuer Activator-Job-Alerts nicht noetig (Learn)."),
        },
        "ki_untersuchungen": {
            "wert": politik["ki_untersuchungen"], "vorgabe_microsoft": True, "reversibel": False,
            "hinweis": ("Legt den Operations Agent an — „If you enable the Operations Agent, you "
                        "can't disable it later\" (Learn). Setzt die Tenant-Settings fuer "
                        "Operations Agent, Copilot und Azure OpenAI voraus, keine Trial. "
                        "DSGVO/Copilot-Freigabe vor der Anlage klaeren."),
        },
        "custom_endpoint": {
            "wert": politik["custom_endpoint"], "vorgabe_microsoft": False, "reversibel": False,
            "hinweis": ("Export an Event Hubs/Kafka/AMQP. In der Preview nur bei der Anlage "
                        "aktivierbar (Learn)."),
        },
    }
    offen = sorted(k for k, v in opt.items() if v["wert"] is None)
    return {
        "_quelle": ("learn.microsoft.com/fabric/fundamentals/enable-workspace-monitoring + "
                    "workspace-monitoring-overview + admin/monitoring-hub-alerts, gelesen 29.09.2026"),
        "modell": "monitoring-item",
        "anlage": ("Portal: Workspace settings → Monitoring → Enable. Fuer das Monitoring-Item ist "
                   "kein dokumentierter REST-Weg vorhanden (Learn-Suche 29.09.2026); Create-API "
                   "UNKLAR, Watchlist fabric-workspace-monitoring-item."),
        "bestandteile": ["Eventhouse", "KQL Database (read-only)", "Eventstream", "Activator",
                         "Operations Agent (optional)"],
        "voraussetzungen": [
            "Workspace auf einer Fabric- oder Premium-Kapazitaet",
            "Tenant-Setting „Workspace admins can turn on monitoring for their workspaces\" "
            "(Fabric-Administrator)",
            "Tenant-Setting „Users can create Fabric items\" fuer den Ausfuehrenden — sonst ist "
            "Monitoring ausgegraut, ohne Fehlermeldung",
            "Workspace-Rolle Admin",
        ],
        "topologie": {
            "art": politik["topologie"],
            "ziel_workspace": (politik["zentral_workspace"]
                               or "<VERIFY: Monitoring-Workspace auf eigener Kapazitaet>")
            if zentral else "je Quelle der eigene Workspace",
            "eigene_kapazitaet": zentral,
            "quellen": quellen,
            "kql_datenbanken_im_ziel": len(quellen) if zentral else 1,
            "item_limit_ziel_workspace": WORKSPACE_ITEM_LIMIT,
            "gleiche_azure_region": zentral,
            "region_pruefung": region_pruefung(bp, politik),
            "begruendung": ("Learn empfiehlt ein zentrales Monitoring-Eventhouse auf eigener "
                            "Kapazitaet: schuetzt das Monitoring vor Drosselung der Last und die "
                            "Last vor dem Monitoring.") if zentral else
                           "Je Workspace ein eigenes Monitoring-Item (Abweichung von der "
                           "Learn-Empfehlung, bewusst gewaehlt).",
        },
        "ziel_aenderbar": False,
        "unveraenderlich": [dict(u) for u in MONITORING_UNVERAENDERLICH],
        "optionen": opt,
        "offene_entscheidungen": offen,
        "aufbewahrung": {
            "tage": politik["aufbewahrung_tage"],
            "cache_tage": politik["cache_tage"],
            "vorgabe_microsoft": WORKSPACE_MONITORING_RETENTION_DEFAULT_DAYS,
            "ort": "Monitoring-KQL-Datenbank → Manage → Data policies",
            "regel": "cache_tage <= tage",
        },
        "datensammlung": {"bei_anlage": "aus", "backfill": False,
                          "schritt": "Turn on data collection"},
    }


def _job_alerts_spec(alerts: dict) -> dict:
    """``job_alerts.json`` — Activator-Job-Alerts je Jobtyp (I-21 W1.6 e).

    Belegt (MS Learn ``admin/monitoring-hub-alerts``, gelesen 29.09.2026): *Job runs → … →
    Create and manage alerts → Alerts (paid)*; Voraussetzung Workspace-Monitoring (das Item nimmt
    die Alerts auf) und Owner- oder Contributor-Rolle; Ereignisse u. a. Started/Succeeded/Failed.
    Die Pruefart „On every value" stammt vom FabCon-Foto (29.09.2026) und steht auf Learn nicht:
    ANNAHME, ungeprueft.
    """
    an = _recipients(alerts, "jobs")
    return {
        "_quelle": "learn.microsoft.com/fabric/admin/monitoring-hub-alerts, gelesen 29.09.2026",
        "status": "Preview",
        "weg": "Monitor hub → Job runs → … (Item) → Create and manage alerts → Alerts (paid)",
        "voraussetzung": {"monitoring_item": True, "rollen": ["Owner", "Contributor"],
                          "eventhouse_noetig": False},
        "kosten": "Activator-Kapazitaetsverbrauch (bezahlt); Schedule failure emails sind frei",
        "regeln": [
            {"jobtyp": t, "ereignis": "Failed", "pruefung": "On every value",
             "pruefung_beleg": "ANNAHME, ungeprueft (FabCon-Foto 29.09.2026)",
             "weitere_ereignisse": ["Started", "Succeeded"],
             "aktion": {"typ": "Teams message", "an": an}}
            for t in JOB_ALERT_TYPES
        ],
        "nicht_abgedeckt": list(JOB_ALERT_NOT_COVERED),
        "fallback": "workspace_job_failures.kql (KQL Queryset + Activator)",
    }


def _operations_agent_definition(bp: dict, politik: dict, stufe: str | None = None) -> dict:
    """``Configurations.json`` des Operations Agents (I-21 W6.4) — Item-Definition statt Portal.

    Belegt (MS Learn ``rest/api/fabric/articles/item-management/definitions/
    operations-agent-definition``, gelesen 29.09.2026): ein Definitionsteil ``Configurations.json``
    mit ``configuration`` (``instructions``, ``dataSources``, ``actions`` Pflicht;
    ``messageDestination``, ``identity``), ``playbook`` (``{}``) und ``shouldRun``. ``goals`` und
    ``recipient`` sind seit Juni 2026 veraltet. ``dataSources`` darf statt GUIDs eine
    Variable-Library-Referenz ``$(/<Workspace>/<Library>/<Variable>)`` tragen — deshalb stehen hier
    keine Tenant-IDs. ``identity.sponsor`` ist laut Learn ein „Sponsor alias provided by the user";
    ob Fabric eine Gruppe oder einen SPN als Sponsor annimmt, sagt die Seite nicht (ANNAHME,
    ungeprueft; Entra Agent ID erlaubt Gruppen als Sponsor, ``entra/agent-id/
    create-delete-agent-identities``).

    D-597: der Workspace in der Referenz ist der Name **dieser Stufe** nach der
    Namenskonvention (:func:`agent_workspace`), nicht ein fester Name fuer alle Stufen.

    Bewusst leer: ``actions``. Der Agent laeuft delegiert (OBO) mit den Rechten seines Erstellers
    (Learn ``real-time-intelligence/operations-agent``) — jede Aktion wuerde unter dieser
    Identitaet laufen; vorab freigegebene Aktionen sind nur angekuendigt. ``shouldRun`` ist
    ``false``, bis die KI-/DSGVO-Freigabe vorliegt (dieselbe Frage wie ``ki_untersuchungen``).
    """
    ws = agent_workspace(politik, stufe)
    sp = politik["operations_agent_sponsor"]
    sponsor = sp["alias"] if sp else "<VERIFY: Sponsor des Operations Agents (Gruppe oder SPN)>"
    domaenen = ", ".join(d["name"] for d in _domains(bp)) or "the platform"
    return {
        "configuration": {
            "instructions": (
                "Watch the job event logs of the monitored workspaces "
                f"({domaenen}). When a pipeline, notebook, Spark job or refresh fails, report "
                "item, workspace, failure time and error message to the operations channel. When "
                "the same item fails twice in a row, say so explicitly. Do not propose or run any "
                "action; report only."),
            "dataSources": {
                "monitoringEventhouse": f"$(/{ws}/{MONITORING_VARLIB}/{MONITORING_KQL_VARIABLE})",
            },
            "actions": {},
            "messageDestination": {
                "kind": "TeamsChannel",
                "teamId": "<VERIFY: Teams-Team-ID des Betriebskanals>",
                "channelId": "<VERIFY: Teams-Kanal-ID des Betriebskanals>",
            },
            "identity": {"sponsor": sponsor},
        },
        "playbook": {},
        "shouldRun": False,
    }


def _agent_workspace(politik: dict) -> str:
    return politik["zentral_workspace"] or "<VERIFY: Monitoring-Workspace auf eigener Kapazitaet>"


def agent_workspace(politik: dict, stufe: str | None = None) -> str:
    """Der Monitoring-Workspace einer Stufe (D-597) — aus ``naming.NamingConvention``.

    Dieselbe Stelle, die in ``governance_strategy`` die Stufen-Workspaces benennt (Suffix
    ``[Dev]``/``[Test]``, Prod ohne). Keine zweite Quelle fuer den Namen; ohne Stufe der
    Basisname."""
    from core.dataarch_engine.blueprint.naming import NamingConvention
    basis = _agent_workspace(politik)
    return NamingConvention(apply_type_prefixes=False, stage=stufe).workspace(basis) \
        if stufe else basis


def pruefe_agent_variablen(out: dict[str, str], stages: tuple[str, ...],
                           monitoring: dict | None = None) -> list[str]:
    """Je Stufe (D-597): die Definition liegt vor, und jede Variablenreferenz in
    ``dataSources`` loest gegen eine in ``out`` emittierte Bibliothek samt Variable auf
    (I-21 W6.4) — **im Workspace dieser Stufe** nach der Namenskonvention. Leer heisst alles
    aufgeloest. ``monitoring`` ist dieselbe Politik wie beim Emittieren."""
    from core.dataarch_engine.blueprint.provision_varlib import (
        _REF_RE,
        library_variables,
        resolve_variable_reference,
    )
    politik = monitoring_politik(monitoring)
    libs = library_variables(out)
    befunde: list[str] = []
    for stufe in stages:
        pfad = operations_agent_path(stufe)
        if pfad not in out:
            befunde.append(f"{stufe}: {pfad} fehlt")
            continue
        defn = json.loads(out[pfad])
        soll_ws = agent_workspace(politik, stufe)
        for alias, ds in ((defn.get("configuration") or {}).get("dataSources") or {}).items():
            if not isinstance(ds, str):
                continue
            b = resolve_variable_reference(ds, libs)
            if b:
                befunde.append(f"{stufe}: dataSources.{alias}: {b}")
                continue
            ist_ws = _REF_RE.match(ds).group(1)
            if ist_ws != soll_ws:
                befunde.append(f"{stufe}: dataSources.{alias}: Workspace {ist_ws!r}, nach der "
                               f"Namenskonvention {soll_ws!r}")
    return befunde


def pruefe_operations_agent_definition(defn: dict) -> list[str]:
    """Befunde gegen die Learn-Definition (gelesen 29.09.2026); leer heisst konform.

    Prueft Pflichtfelder, geschlossene Enums (Learn: „validation rejects unknown values"), die
    Form der Variable-Library-Referenz und die beiden seit Juni 2026 veralteten Felder."""
    f: list[str] = []
    if not isinstance(defn, dict):
        return ["Definition ist kein Objekt"]
    for k in ("configuration", "playbook", "shouldRun"):
        if k not in defn:
            f.append(f"Pflichtfeld {k} fehlt")
    if not isinstance(defn.get("playbook", {}), dict):
        f.append("playbook muss ein Objekt sein")
    if "shouldRun" in defn and not isinstance(defn["shouldRun"], bool):
        f.append("shouldRun muss boolesch sein")
    c = defn.get("configuration") or {}
    for k in ("instructions", "dataSources", "actions"):
        if k not in c:
            f.append(f"configuration.{k} fehlt")
    for alt in ("goals", "recipient"):
        if alt in c:
            f.append(f"configuration.{alt} ist seit Juni 2026 veraltet")
    for alias, ds in (c.get("dataSources") or {}).items():
        if isinstance(ds, str):
            if not _VARIABLE_REF_RE.match(ds):
                f.append(f"dataSources.{alias}: Variablenreferenz nicht in der Form "
                         "$(/<Workspace>/<Library>/<Variable>)")
        elif not isinstance(ds, dict) or not {"id", "type", "workspaceId"} <= set(ds):
            f.append(f"dataSources.{alias}: id, type und workspaceId sind Pflicht")
        elif ds["type"] not in OPERATIONS_AGENT_DATASOURCE_TYPES:
            f.append(f"dataSources.{alias}: type {ds['type']!r} nicht dokumentiert")
    for alias, a in (c.get("actions") or {}).items():
        if not isinstance(a, dict) or not {"id", "displayName", "description", "kind"} <= set(a):
            f.append(f"actions.{alias}: id, displayName, description und kind sind Pflicht")
        elif a["kind"] not in OPERATIONS_AGENT_ACTION_KINDS:
            f.append(f"actions.{alias}: kind {a['kind']!r} nicht dokumentiert")
        elif a["kind"] == "FabricJobAction" and not isinstance(a.get("connection"), dict):
            f.append(f"actions.{alias}: FabricJobAction braucht connection")
    md = c.get("messageDestination")
    if md is not None:
        kind = md.get("kind") if isinstance(md, dict) else None
        if kind not in OPERATIONS_AGENT_DESTINATION_KINDS:
            f.append(f"messageDestination.kind {kind!r} nicht dokumentiert")
        elif kind == "Recipient" and "recipient" not in md:
            f.append("messageDestination Recipient braucht recipient")
        elif kind == "TeamsChannel" and not {"teamId", "channelId"} <= set(md):
            f.append("messageDestination TeamsChannel braucht teamId und channelId")
    ident = c.get("identity")
    if ident is not None and (not isinstance(ident, dict) or set(ident) - {"sponsor"}):
        f.append("identity: in GA-Definitionen ist nur sponsor zulaessig")
    return f


def _operations_agent_lines(politik: dict) -> list[str]:
    """Abschnitt in `_MONITORING.md` zur Item-Definition (I-21 W6.4)."""
    sp = politik["operations_agent_sponsor"]
    return [
        "## Operations Agent as an item definition (I-21 W6.4)", "",
        f"`{OPERATIONS_AGENT_DIR.split('/', 1)[1]}/` holds the agent's item definition, one "
        "`Configurations.json` per stage folder, deployable "
        "through the item APIs or Git instead of configured in the portal (MS Learn, *Operations "
        "Agent definition*, read 2026-09-29). It is emitted **stopped** (`shouldRun: false`) and "
        "**without actions** — on purpose:", "",
        "- The agent runs **delegated** (on-behalf-of) with the permissions of the identity that "
        "**created** it; an approved recommendation runs under that identity (MS Learn, "
        "*Operations agent identities*). Create it with the operations service account, never "
        "with a personal account — the same *consented identity* risk as the branch workspace "
        "admin profile. Whether a service principal can create the item is not documented "
        "(ASSUMPTION, unverified).",
        "- **Sponsor** (`identity.sponsor`) = a security group or a service principal, not a "
        "person: a person leaves, and the agent loses its accountable owner. "
        + (f"This delivery sets `{sp['alias']}` ({sp['art']})." if sp else
           "Still open — `operations_agent_sponsor` in the monitoring policy.")
        + " Learn documents the field only as a \"sponsor alias\"; whether Fabric accepts a group "
        "or SPN alias there is an ASSUMPTION, unverified — check at the first tenant run.",
        "- **Messages** go to a Teams channel, not to one person. Recipients need write "
        "permission on the agent item (MS Learn, *Operations agent actions*).",
        f"- **Data source** is a variable-library reference (`$(/<workspace>/{MONITORING_VARLIB}/"
        f"{MONITORING_KQL_VARIABLE})`), so the definition carries no tenant IDs. The "
        "`<workspace>` part is a plain name, and stage workspaces are named per stage by the "
        "naming convention (`[Dev]`, `[Test]`, prod without suffix) — hence one definition per "
        "stage (D-597); promote each stage's file, never copy one across stages. The variable "
        "library is not part of the agent definition (MS Learn) and is emitted next to it as "
        f"`{MONITORING_VARLIB}.VariableLibrary/` — deploy it into the same workspace **before** "
        f"the agent. `{MONITORING_KQL_VARIABLE}` is an `ItemReference` to the **KQL database** "
        "of the monitoring Eventhouse (not the Eventhouse); its IDs stay placeholders until "
        "`--varlib-config` supplies them, and Fabric rejects the library while a placeholder "
        "remains. That an operations agent accepts an `ItemReference` variable is an "
        "ASSUMPTION, unverified (Learn documents the reference form, not the variable type; "
        "Eventstreams use `ItemReference` for the same KQL database).",
        "- Start (`shouldRun: true`) only after the Copilot/Azure OpenAI tenant settings and the "
        "GDPR clearance — the same decision as *AI powered investigations* in step 1c.", "",
    ]


def _pipeline_failure_runbook(bp: dict, alerts: dict,
                              stages: tuple[str, ...] = ("dev", "test", "prod")) -> str:
    """Runbook fuer die Fehlerbenachrichtigung — inklusive der Frage, wie man sie nachweist (Z11).

    Der Kundenmandant-Lauf 2 hat den Schritt als einen von drei Menschenschritten je Auslieferung
    gezaehlt und ihn dabei „ohne jede Nachweismoeglichkeit" genannt: die Adresse tauchte weder am
    Zeitplanobjekt noch am Item auf. Die Haelfte davon ist belegt, die andere Haelfte zu scharf,
    und beides gehoert in die Lieferung statt in eine Analyse-Datei:

    - **Kein API-Weg, gemessen.** Das v1-Schema ``ItemSchedule`` (learn.microsoft.com,
      ``core/job-scheduler/create-item-schedule``, geholt 14.08.2026) traegt genau sechs Felder:
      ``configuration``, ``createdDateTime``, ``enabled``, ``executionData``, ``id``, ``owner``.
      Kein Empfaengerfeld, weder in der Anfrage noch in der Antwort. Das ist kein Versehen des
      Exports: MS beschreibt die Einstellung ausdruecklich als **Item-Einstellung**, die fuer alle
      Zeitplaene des Items gilt.
    - **Aber nicht unpruefbar.** Der Monitoring-Hub hat die Seite **Schedule failures** (Preview),
      die alle Items mit gesetzter Fehlerbenachrichtigung samt Empfaengern listet — eine Seite
      statt N Klickpfade. Zwei Grenzen, beide dokumentiert: sie ist Preview, und semantische
      Modelle fehlen dort noch. Damit ist der Nachweis fuer die Pipeline moeglich und fuer ein
      direkt eingeplantes Modell weiter nicht.

    Abweichung vom Analyse-Stand (Belegpflicht Regel 5): Z11 sagt „ohne jede Nachweismoeglichkeit".
    Das galt fuer den API-Weg und den Export, nicht fuer den Monitoring-Hub. Die Zahl der
    Handgriffe bleibt davon unberuehrt.
    """
    stufen = tuple(stages) or ("dev",)
    items = 1                                    # eine eingeplante Pipeline je Stufe
    lines = [
        "# Fehlerbenachrichtigung (eingebaut — die erste Linie ohne Infrastruktur)", "",
        f"**Handgriffe: {items * len(stufen)}** — {items} eingeplantes Item x {len(stufen)} Stufe(n) "
        f"({', '.join(stufen)}). Kein API-Weg,",
        "siehe unten; der Schritt ist damit einer der Menschenschritte je Auslieferung und gehoert in",
        "die Kalkulation, nicht in eine Checkliste.", "",
        "Je Item: oeffnen → **Home → Schedule** → Empfaenger unter **Failure notifications** eintragen.",
        "Die Einstellung haengt am **Item**, nicht am einzelnen Zeitplan: sie gilt fuer alle Zeitplaene",
        "des Items, und mehr Zeitplaene erzeugen keinen zusaetzlichen Handgriff. Nur geplante Laeufe",
        "loesen sie aus; ein von Hand gestarteter Lauf meldet sich nie. Fuer Anlegen/Aendern/Loeschen",
        "und ungeplante Laeufe bleibt die workspace-weite Activator-Regel (siehe `_MONITORING.md`).",
        "", "| Domaene | Vorgeschlagene Empfaenger |", "|---|---|",
    ]
    for d in _domains(bp):
        lines.append(f"| {d['name']} | {', '.join(_recipients(alerts, _dirslug(d['name'])))} |")
    lines += [
        "", "## Wie der Schritt nachgewiesen wird", "",
        "Nicht ueber die API. Das v1-Schema `ItemSchedule` (MS Learn, `core/job-scheduler/",
        "create-item-schedule`, geholt 14.08.2026) hat genau sechs Felder — `configuration`,",
        "`createdDateTime`, `enabled`, `executionData`, `id`, `owner` — und kein Empfaengerfeld.",
        "Wer die Adresse dort sucht, sucht an einer Stelle, an der sie nicht gespeichert wird.", "",
        "Nachweisbar ist sie im **Monitoring-Hub → Schedule failures** (Preview): eine Seite, die alle",
        "Items mit gesetzter Benachrichtigung und ihre Empfaenger auflistet, mit derselben zugrunde",
        "liegenden Konfiguration wie der Zeitplan-Bereich. Zwei dokumentierte Grenzen: Preview-Status,",
        "und semantische Modelle fehlen dort noch. Fuer die eingeplante Pipeline traegt der Nachweis,",
        "fuer ein direkt eingeplantes Modell nicht.", "",
        "Zum Abnehmen: Screenshot der Seite mit Item und Empfaengern, Datum im Uebergabeprotokoll.",
        "Bearbeiten setzt Contributor im Workspace bzw. Schreibrecht am Item voraus.", "",
        "Zwei Punkte, die man ohne Messung falsch plant: die Einstellung steht **nicht** in der",
        "Item-Definition (gemessen am Export 14.08. — weder am Zeitplanobjekt noch am Item), also",
        "traegt weder Git noch die Deployment-Pipeline sie mit und jede Stufe braucht den Handgriff",
        "erneut (hergeleitet aus dieser Messung). Und der Zeitplan schaltet sich nach rund 10",
        "aufeinanderfolgenden Fehllaeufen selbst ab (`auto-disabled`, MS Learn) — danach kommt keine",
        "Mail mehr, weil kein Lauf mehr startet. Genau dann ist Stille kein gutes Zeichen.", "",
        "Bewaehrt (belegt): Alarme muessen handlungsfaehig und eskaliert sein; mehrkanalig (E-Mail/Teams)",
        "und mit zustandsbehafteten Activator-Operatoren (BECOMES/INCREASES) statt zustandslosen, sonst",
        "wird der Alarm zum Rauschen.",
    ]
    return "\n".join(lines) + "\n"


#: Wie weit das Aktivitaetsprotokoll rueckwirkend abrufbar ist. **Abweichung, benannt statt
#: geglaettet (Belegpflicht Regel 5):** der Betriebskanon sagte bis 16.08.2026 „30 Tage". MS nennt
#: beide Zahlen an verschiedenen Stellen — die Sicherheits-Baseline schreibt „Keeps activity data
#: for 30 days", der Leitfaden zum Abruf schreibt „Activity log data is available for a maximum of
#: 28 days" und begrenzt das Rueckdatum entsprechend. Fuer einen Export zaehlt die abrufbare Zahl.
ACTIVITY_LOG_DAYS = 28

#: Aufbewahrung des Exports. 13 statt 12 Monate, damit ein Jahresvergleich moeglich bleibt: mit
#: genau 12 fehlt am Stichtag der Vergleichsmonat. Uebersteuerbar durch den Kunden.
ACTIVITY_EXPORT_RETENTION_MONTHS = 13

ACTIVITY_EXPORT_PATH = "monitoring/activity_log_export.py"

#: Das Beobachtungsfenster der Capacity Metrics App auf der **Compute**-Seite. Nicht
#: konfigurierbar und nicht rueckwirkend zu fuellen — der Grund, warum die App zum Tag 0
#: gehoert und nicht zur Uebergabe (BK-B02).
METRICS_APP_COMPUTE_DAYS = 14

#: Die **Storage**-Seite derselben App reicht weiter. Zwei verschiedene Fenster in einer App
#: sind eine haeufige Fehlerquelle beim Planen: „14 Tage" stimmt fuer Rechenlast, nicht fuer
#: Speicherwachstum.
METRICS_APP_STORAGE_DAYS = 30

#: Ruhezeit nach einer Kapazitaets-Benachrichtigung aus dem Admin-Portal. Danach schweigt sie,
#: auch wenn die Schwelle erneut gerissen wird — der Grund, warum sie die Activator-Regel
#: ergaenzt und nicht ersetzt.
CAPACITY_NOTIFICATION_MUTE_HOURS = 3

METRICS_APP_SETUP_PATH = "monitoring/capacity_metrics_app_setup.md"

#: Die Bronze-Tabelle, in der die exportierten Rohdateien abfragbar werden. Der Export allein
#: sammelt nur Dateien; wer sammelt und nicht laedt, hat die Daten und kann sie nicht befragen
#: (BK-B04).
ACTIVITY_BRONZE_TABLE = "bronze_activity_log"

ACTIVITY_BRONZE_LOAD_PATH = "monitoring/activity_log_bronze_load.py"

ACTIVITY_SCHEDULE_PATH = "monitoring/activity_log_export_schedule.json"

#: Startzeit des taeglichen Laufs, UTC. Nach Mitternacht, damit der Vortag vollstaendig ist, und
#: eine Stunde nach dem Vorgabewert der Orchestrierung (02:00 UTC, `provision_orchestration`),
#: damit die beiden geplanten Laeufe nicht gleichzeitig auf dieselbe Kapazitaet gehen.
ACTIVITY_SCHEDULE_TIME_UTC = "03:00"


def _activity_log_export_py() -> str:
    """Der taegliche D-1-Export des Aktivitaetsprotokolls nach Bronze — als lauffaehiges Skript.

    Warum ueberhaupt: das Protokoll ist 28 Tage rueckwirkend abrufbar. Jede Frage nach dem Vorjahr
    ist danach nicht schwer zu beantworten, sondern unbeantwortbar — es gibt die Daten nicht mehr.

    Warum roh und ungefiltert (ELT, nicht ETL): MS empfiehlt es ausdruecklich („avoid parsing,
    filtering, or formatting the activity log data as it's extracted"), und der Grund ist hier
    schaerfer als sonst. Was der Export wegwirft, ist nach 28 Tagen endgueltig fort; ein Filter,
    den jemand 2026 fuer sinnvoll hielt, kostet 2027 die Antwort. Dazu kommt, dass die Felder je
    Ereignisart verschieden sind und sich mit dem Dienst aendern — ein Schema an dieser Stelle
    waere eine zweite Stelle, die nachgezogen werden muesste.

    Warum D-1 und nicht heute: ein Lauf fuer den laufenden Tag holt einen halben Tag und sieht
    dabei vollstaendig aus. MS: „so you avoid retrieving partial day events".

    Warum stundenweise Fenster: die Doku sagt an zwei Stellen Verschiedenes — die API-Referenz
    schreibt, Start und Ende muessen im selben UTC-Tag liegen, der Leitfaden schreibt, ueber die
    API direkt gehe „only one hour per API request". Das ist ein Widerspruch, kein Detail, und er
    wird hier zugunsten der engeren Angabe aufgeloest: 24 Anfragen je Tag liegen weit unter der
    dokumentierten Grenze von 200 Anfragen je Stunde, ein zu grosses Fenster liefe dagegen ins
    Leere. Beide Stellen geprueft am 16.08.2026.
    """
    return f'''"""activity_log_export.py — den Vortag des Aktivitaetsprotokolls roh nach Bronze legen.

Taeglich laufen lassen. Das Protokoll ist **{ACTIVITY_LOG_DAYS} Tage** rueckwirkend abrufbar; was
hier nicht landet, ist danach fort. Deshalb wird roh geschrieben und nichts gefiltert (ELT):
die Felder unterscheiden sich je Ereignisart und aendern sich mit dem Dienst.

Identitaet: Fabric-Administrator oder ein Dienstprinzipal. Fuer den SPN gilt eine Bedingung, die
leicht uebersehen wird und den Aufruf sonst mit 401/403 beendet — die App darf **keine**
Power-BI-Berechtigungen mit Admin-Consent gesetzt haben. Der Scope `Tenant.Read.All` gehoert nur
zum delegierten Weg und darf beim SPN-Weg NICHT mitgeschickt werden.

Grenzen, alle am 16.08.2026 gegen learn.microsoft.com geprueft:
  * {ACTIVITY_LOG_DAYS} Tage Rueckschau, kein aelteres Startdatum moeglich.
  * 200 Anfragen je Stunde auf `Get Activity Events`. Dieses Skript braucht 24 fuer einen Tag.
  * Kein Aktivitaetsprotokoll fuer Microsoft Cloud Deutschland.
  * Zeitstempel sind UTC. Lokalzeit hier nicht einfuehren — sie verschiebt die Tagesgrenze.
"""
import datetime as _dt
import json
import os
import sys
import urllib.parse
import urllib.request

API = "https://api.powerbi.com/v1.0/myorg/admin/activityevents"

#: Rueckschau-Grenze des Dienstes. Ein aelteres Datum liefert keinen Fehler mit Ansage, sondern
#: eine leere Antwort — und ein leerer Tag sieht aus wie ein ruhiger Tag.
MAX_RUECKSCHAU_TAGE = {ACTIVITY_LOG_DAYS}


def _token() -> str:
    """Zugriffstoken. In einem Fabric-Notebook liefert `notebookutils` es ohne Geheimnis im Code;
    ausserhalb wird es als Umgebungsvariable erwartet."""
    tok = os.environ.get("PBI_ACCESS_TOKEN")
    if tok:
        return tok
    try:                                   # im Notebook: keine Zugangsdaten im Skript
        import notebookutils                                        # noqa: F401
        return notebookutils.credentials.getToken("pbi")            # VERIFY gegen Ihre Laufzeit
    except Exception as exc:                                        # pragma: no cover
        raise SystemExit("Kein Token: PBI_ACCESS_TOKEN setzen oder im Fabric-Notebook laufen "
                         f"lassen ({{exc}})") from exc


def _hole(url: str, token: str) -> dict:
    req = urllib.request.Request(url, headers={{"Authorization": f"Bearer {{token}}"}})
    with urllib.request.urlopen(req, timeout=120) as antwort:        # noqa: S310 (feste Host-URL)
        return json.loads(antwort.read().decode("utf-8"))


def hole_tag(tag: _dt.date, token: str) -> list[dict]:
    """Alle Ereignisse eines UTC-Tages, in 24 Stundenfenstern, Fortsetzungstoken aufgeloest.

    Stundenweise, weil der Leitfaden fuer den direkten API-Weg genau ein Stundenfenster je
    Anfrage nennt. Die API-Referenz erlaubt an derselben Stelle den ganzen UTC-Tag; wo sich zwei
    Angaben widersprechen, gilt hier die engere. 24 Anfragen bleiben weit unter 200/Stunde.
    """
    ereignisse: list[dict] = []
    for stunde in range(24):
        start = _dt.datetime.combine(tag, _dt.time(stunde, 0, 0))
        ende = start + _dt.timedelta(hours=1) - _dt.timedelta(milliseconds=1)
        frage = urllib.parse.urlencode({{
            # Die Werte gehoeren laut Referenz in einfache Anfuehrungszeichen. Ohne sie antwortet
            # die API mit 400, und die Meldung nennt das Datum, nicht die Anfuehrungszeichen.
            "startDateTime": f"'{{start.strftime('%Y-%m-%dT%H:%M:%S.000Z')}}'",
            "endDateTime": f"'{{ende.strftime('%Y-%m-%dT%H:%M:%S.999Z')}}'",
        }})
        url = f"{{API}}?{{frage}}"
        while url:
            antwort = _hole(url, token)
            ereignisse.extend(antwort.get("activityEventEntities") or [])
            url = antwort.get("continuationUri") or ""
    return ereignisse


def main(argv: list[str]) -> int:
    ziel = argv[1] if len(argv) > 1 else os.environ.get(
        "BRONZE_PFAD", "/lakehouse/default/Files/bronze/activity_log")
    # D-1: ein Lauf fuer den laufenden Tag holt einen halben Tag und sieht vollstaendig aus.
    tag = _dt.datetime.now(_dt.timezone.utc).date() - _dt.timedelta(days=1)
    if len(argv) > 2:
        tag = _dt.date.fromisoformat(argv[2])
    alter = (_dt.datetime.now(_dt.timezone.utc).date() - tag).days
    if alter > MAX_RUECKSCHAU_TAGE:
        print(f"FEHLER: {{tag}} liegt {{alter}} Tage zurueck, abrufbar sind "
              f"{{MAX_RUECKSCHAU_TAGE}}. Der Dienst antwortet dafuer leer, nicht mit Fehler — "
              "ein leerer Tag waere von einem ruhigen Tag nicht zu unterscheiden.", file=sys.stderr)
        return 2
    if alter < 1:
        print(f"FEHLER: {{tag}} ist heute oder in der Zukunft. Der Export laeuft auf D-1, sonst "
              "enthaelt die Datei einen halben Tag und sieht vollstaendig aus.", file=sys.stderr)
        return 2

    ereignisse = hole_tag(tag, _token())
    os.makedirs(ziel, exist_ok=True)
    geschrieben = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%d%H%M")
    datei = os.path.join(ziel, f"activity-{{tag:%Y%m%d}}-{{geschrieben}}.json")
    with open(datei, "w", encoding="utf-8") as f:
        json.dump(ereignisse, f, ensure_ascii=False)
    # Der Zeitstempel im Namen ist der SCHREIB-Zeitpunkt, nicht der Datentag. Wird ein Tag
    # zweimal geholt, stehen beide Dateien nebeneinander und die neuere ist erkennbar.
    print(f"{{len(ereignisse)}} Ereignis(se) fuer {{tag}} -> {{datei}}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
'''


def _activity_log_schedule_json() -> str:
    """Der taegliche Zeitplan des Export-Notebooks — als Datei, nicht als Satz im Runbook.

    Bis 20.08.2026 stand hier ein Handgriff: „Schritt 8: `activity_log_export.py` taeglich
    einplanen." Ein Handgriff, den niemand ausfuehrt, sieht in der Lieferung genauso aus wie
    einer, den jemand ausgefuehrt hat — und der Export ist der eine Teil der Ueberwachung, der
    sich nicht nachholen laesst: was in seinem Fenster nicht geholt wurde, ist fort.

    Die Form kommt aus `fabric_schedule` und wird hier **nicht** ein zweites Mal gebaut. Es
    gibt einen Fabric-Zeitplan, also gibt es eine Stelle, die weiss, wie er aussieht; zwei
    Stellen driften.
    """
    return emit_schedule(frequency="Daily", time=ACTIVITY_SCHEDULE_TIME_UTC, timezone="UTC")


def _activity_log_bronze_load_py() -> str:
    """Die exportierten Rohdateien als Bronze-Tabelle — der zweite fehlende Teil von BK-B04.

    Der Export legt JSON-Dateien in OneLake. Das ist Sammeln, nicht Verfuegbarmachen: eine Frage
    nach dem Vorjahr braucht eine Tabelle, keine 400 Dateien. Vier Entscheidungen, jede mit
    ihrem Grund:

    * **Ein Schreibvorgang je Datentag, ersetzend** (``replaceWhere``). Ein zweiter Lauf fuer
      denselben Tag ersetzt ihn, statt ihn zu verdoppeln. Ohne das waere ein Nachlauf nach einer
      Stoerung gefaehrlicher als die Stoerung.
    * **Neuester Schreibstempel je Datentag gewinnt.** Der Export schreibt den Zeitpunkt des
      Schreibens in den Dateinamen, nicht den Datentag allein — genau damit ein zweimal geholter
      Tag zwei Dateien hat und die neuere erkennbar ist. Diese Regel liest das hier aus.
    * **Schema waechst mit** (``mergeSchema``). Die Felder unterscheiden sich je Ereignisart und
      aendern sich mit dem Dienst. Ohne mitwachsendes Schema faellt ein neu auftauchendes Feld
      beim Schreiben durch — dieselbe Klasse Verlust, gegen die der ELT-Grundsatz des Exports
      sich richtet, nur eine Schicht spaeter.
    * **Kein Filter, keine Umformung.** Es kommen genau drei Spalten dazu, alle drei aus dem
      Dateinamen und keine aus dem Inhalt.
    """
    return rf'''"""activity_log_bronze_load.py — die exportierten Rohdateien abfragbar machen.

Laeuft direkt nach `activity_log_export.py`, im selben geplanten Notebook. Der Export sammelt,
dieses Skript laedt: ohne den zweiten Schritt liegen die Daten da und sind nicht zu befragen.

Was dazukommt, sind drei Spalten, und alle drei stehen im Dateinamen:
  * ``_datentag``      — der Tag, den die Datei beschreibt
  * ``_geschrieben_utc`` — wann der Export sie geschrieben hat
  * ``_quelldatei``    — welche Datei die Zeile getragen hat

Was **nicht** passiert: filtern, umbenennen, Typen festklopfen. Die Felder des
Aktivitaetsprotokolls unterscheiden sich je Ereignisart und aendern sich mit dem Dienst; das
Schema der Tabelle waechst deshalb mit (``mergeSchema``), statt neue Felder abzuweisen.

Wiederholbar: je Datentag wird ersetzt, nicht angehaengt. Ein Nachlauf nach einer Stoerung ist
damit ungefaehrlich, und ein zweimal geholter Tag verdoppelt sich nicht — es gewinnt die Datei
mit dem juengsten Schreibstempel.
"""
import datetime as _dt
import re
import sys

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

TABELLE = "{ACTIVITY_BRONZE_TABLE}"

#: Derselbe Ort wie der Standardpfad des Exports, nur ueber den anderen Zugang. Der Export
#: schreibt mit gewoehnlichem Datei-Zugriff nach `/lakehouse/default/Files/bronze/activity_log`,
#: Spark liest denselben Ordner als `Files/bronze/activity_log` relativ zum Standard-Lakehouse.
#: Wer die beiden Zeilen nebeneinander sieht und einen Fehler vermutet, sieht zwei Zugaenge.
QUELLE = "Files/bronze/activity_log"

#: Der Dateiname aus `activity_log_export.py`: das Praefix `activity-`, dann der Datentag als
#: acht Ziffern, dann der Schreibstempel als zwoelf. Gruppe 1 ist der Tag, Gruppe 2 der Stempel.
#: Benannte Gruppen stuenden hier naeher, tragen aber spitze Klammern — und die liest der
#: Platzhalter-Pruefer der Lieferung als unausgefuelltes Feld.
NAME = re.compile(r"^activity-(\d{{8}})-(\d{{12}})\.json$")


def _dateien(spark: SparkSession, quelle: str) -> dict:
    """Je Datentag die Datei mit dem juengsten Schreibstempel."""
    jvm = spark._jvm
    pfad = jvm.org.apache.hadoop.fs.Path(quelle)
    fs = pfad.getFileSystem(spark._jsc.hadoopConfiguration())
    if not fs.exists(pfad):
        return {{}}
    neueste = {{}}
    for status in fs.listStatus(pfad):
        name = status.getPath().getName()
        treffer = NAME.match(name)
        if not treffer:
            continue                      # fremde Datei im Ordner: nicht raten, nicht laden
        tag, stempel = treffer.group(1), treffer.group(2)
        if tag not in neueste or stempel > neueste[tag][0]:
            neueste[tag] = (stempel, str(status.getPath()))
    return neueste


def lade_tag(spark: SparkSession, tag: str, stempel: str, pfad: str) -> int:
    """Einen Datentag laden und dabei ersetzen, was fuer diesen Tag schon dasteht."""
    roh = spark.read.option("multiLine", True).json(pfad)
    if not roh.columns:
        print(f"{{tag}}: leere Datei, nichts zu laden")
        return 0
    datum = _dt.datetime.strptime(tag, "%Y%m%d").date()
    geschrieben = _dt.datetime.strptime(stempel, "%Y%m%d%H%M")
    angereichert = (roh
                    .withColumn("_datentag", F.lit(datum.isoformat()).cast("date"))
                    .withColumn("_geschrieben_utc", F.lit(geschrieben.isoformat()).cast("timestamp"))
                    .withColumn("_quelldatei", F.lit(pfad.rsplit("/", 1)[-1])))
    zeilen = angereichert.count()
    schreiber = (angereichert.write.format("delta")
                 .option("mergeSchema", "true")
                 .partitionBy("_datentag"))
    if spark.catalog.tableExists(TABELLE):
        # Ersetzen statt anhaengen: derselbe Tag zweimal geladen ergibt denselben Stand.
        (schreiber.mode("overwrite")
         .option("replaceWhere", f"_datentag = '{{datum.isoformat()}}'")
         .saveAsTable(TABELLE))
    else:
        schreiber.mode("overwrite").saveAsTable(TABELLE)
    print(f"{{tag}}: {{zeilen}} Zeile(n) aus {{pfad.rsplit('/', 1)[-1]}}")
    return zeilen


def main(argv: list) -> int:
    spark = SparkSession.builder.getOrCreate()
    quelle = argv[1] if len(argv) > 1 else QUELLE
    nur = argv[2] if len(argv) > 2 else None      # ein Datentag als YYYYMMDD, sonst alle offenen

    dateien = _dateien(spark, quelle)
    if not dateien:
        print(f"Keine Exportdateien unter {{quelle}} — laeuft der Export?", file=sys.stderr)
        return 1
    if nur:
        if nur not in dateien:
            print(f"Kein Export fuer {{nur}} vorhanden.", file=sys.stderr)
            return 2
        dateien = {{nur: dateien[nur]}}

    gesamt = 0
    for tag in sorted(dateien):
        stempel, pfad = dateien[tag]
        gesamt += lade_tag(spark, tag, stempel, pfad)
    print(f"{{len(dateien)}} Tag(e), {{gesamt}} Zeile(n) in {{TABELLE}}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
'''


def _metrics_app_setup_md(capacity: str, alerts: dict) -> str:
    """``monitoring/capacity_metrics_app_setup.md`` — die Installation der Capacity Metrics App
    als Ablaufschritt statt als Zeile in einer Tabelle (BK-B02).

    Der Kanon belegte BK-B02 bis 16.08.2026 mit ``capacity_throttling_alert.json``. Das ist eine
    **Warnregel**, keine Installation — und die beiden haengen nicht einmal zusammen: die App
    kann laut MS gar keine Alarme („The Microsoft Fabric Capacity Metrics app doesn't support
    alerts or notifications"), weshalb die Regel ueber Real-Time-Hub-Ereignisse laeuft und nicht
    ueber die App. Ein Beleg, der auf das falsche Artefakt zeigt, ist die leiseste Art, eine
    Luecke zu verstecken.

    Alles hier am 16.08.2026 gegen learn.microsoft.com geprueft (``fabric/enterprise/metrics-app``,
    ``fabric/enterprise/metrics-app-install``, ``fabric/admin/service-admin-premium-capacity-
    notifications``).
    """
    return "\n".join([
        f"# Capacity Metrics App — install on day 0 (generated, `{capacity}`)", "",
        f"Not because it shows anything on day 0. Because its compute window is "
        f"**{METRICS_APP_COMPUTE_DAYS} days** wide and cannot be filled backwards. Installed at "
        "handover, it has nothing to say about the build phase — and the surge-protection "
        "thresholds (`BK-F06`) then get guessed instead of read.", "",
        "| Property | Value |", "|---|---|",
        f"| Compute page window | {METRICS_APP_COMPUTE_DAYS} days |",
        f"| Storage page window | {METRICS_APP_STORAGE_DAYS} days |",
        "| Who may install | a **capacity admin** — nobody else can |",
        "| Licence to use it | Power BI Pro, PPU, or an individual trial |",
        "| Refresh | automatic at midnight; a new capacity is invisible until the next one |",
        "| Alerting | **none** — the app has no alerts or notifications |", "",

        "## Install", "",
        "1. AppSource → *Microsoft Fabric Capacity Metrics* → **Get it now** → **Install**.",
        "2. **Install it into a workspace on a Pro licence, not onto the capacity it watches.** MS "
        "says this to avoid throttling from capacity overutilization, and the consequence is the "
        "point: a monitoring app that lives on the capacity it monitors goes dark exactly when the "
        "capacity is in trouble.",
        "3. First run → **Connect** → fill three parameters and nothing else:",
        "   - `UTC_offset` — your organisation's standard time as a number (`1` for CET, `5.5` for "
        "IST). Everything the app shows is stamped with this.",
        "   - `RegionName` — `Default` for a capacity admin. A tenant admin without an admin "
        "capacity in the home region enters that region's name instead.",
        "   - `DefaultCapacityID` — the GUID from the capacity's admin-portal URL, after "
        "`/capacities/`.",
        "   The app carries further parameters. They are not user-configurable, and changing them "
        "can break the semantic model or the report.",
        "4. Authentication **OAuth2** (the only supported method), privacy level **Organizational**.",
        "5. Assign the **capacity admins** now, at install time. Everyone else gets access by "
        "sharing the report afterwards — installing is not a shared act, viewing is.", "",
        "If the app shows no data after installing, the documented fix is blunt: delete it, "
        "reinstall the current version, update the semantic model credentials. Do not go looking "
        "for a setting.", "",

        "## The alert the app cannot give you", "",
        "The app has no alerting. Two things fill that gap, and they are not alternatives:", "",
        f"- **Capacity notifications** (Admin portal → Capacity settings → *{capacity}* → "
        "Notifications). Five clicks, no infrastructure, e-mail on a percentage threshold and on "
        "*capacity exceeded*. Recipients: "
        f"{', '.join('`' + r + '`' for r in _recipients(alerts, 'capacity'))}.",
        "- **The Activator rule** in `capacity_throttling_alert.json`, over Capacity Overview "
        "Events. Slower to set up, and it distinguishes background rejection from interactive "
        "delay — which is the difference between *a pipeline is failing* and *reports are slow*.", "",
        "Four properties of the built-in notification that decide whether you believe it:", "",
        "| Property | Consequence |", "|---|---|",
        "| Capacity is checked every 15 min, over the last 15–30 min of activity | a short spike "
        "can pass unseen |",
        f"| After one mail, **{CAPACITY_NOTIFICATION_MUTE_HOURS} hours** of silence, even if the "
        "threshold is crossed again | the second, worse breach of an evening never arrives |",
        "| No timestamp in the mail, and no statement of by how much | the mail says *that*, never "
        "*when* or *how bad* |",
        "| Usage is computed over a 30-second window | the triggering event may not be findable in "
        "the app at all |", "",
        "> Pausing a capacity can set this off falsely: the accumulated smoothing is billed at "
        "pause time and can cross the threshold. A nightly pause plan (`platform/"
        "capacity_schedule.md`) therefore produces the same false mail every evening unless the "
        "threshold accounts for it.", "",

        "## Two limits worth knowing before someone else finds them", "",
        "- **Private links and this app: the two MS pages disagree.** The app's own page says it "
        "supports *tenant-level* private links and rules out only a **workspace-level** private "
        "link on the workspace it is installed in. The private-links overview says flatly that "
        "the app „doesn't support Private Link\" (both read 2026-08-16). Planned against the "
        "narrower reading in `connectivity/_CONNECTIVITY.md`; either way the workspace this app "
        "lives in is the wrong place for a workspace-level private link.",
        "- **User names are visible by default.** The tenant setting *Show user data in the "
        "Microsoft Fabric Capacity Metrics app and reports* controls whether operations are shown "
        "with the user who ran them. Left on, the app reports per-person compute usage — in "
        "Germany that is a works-council question, and it is better asked before installation "
        "than after.", "",
    ]) + "\n"


def _warehouse_monitor_lines() -> list[str]:
    """Monitor for Fabric Data Warehouse (I-21 W6.11) — Abschnitt in `_MONITORING.md`.

    Belegt (MS Learn ``fabric/data-warehouse/monitor``, gelesen 29.09.2026): Preview, frueher
    „Query Activity"; nur Workspace-Admins; bis 15 Minuten Verzug; hoechstens 10.000 Zeilen je
    Filter; dieselben Daten liegen in ``queryinsights.exec_requests_history``. Kein Alert — die
    Oberflaeche ist ein Diagnosewerkzeug, kein Signal.
    """
    return [
        "## Warehouse queries — the built-in Monitor (preview)", "",
        "Warehouse and SQL analytics endpoint have their own query monitor (formerly *Query "
        "Activity*): workspace view → **…** next to the warehouse → **Monitor**, or **Monitor** in "
        "the query editor ribbon. Pages: *Query history* (status, submitter, run source, CPU time, "
        "data scanned, result cache hit, error code; cancel a running query), *Long running "
        "queries*, *Frequently run queries* (MS Learn, `data-warehouse/monitor`, read 2026-09-29).", "",
        "| Property | Value | Consequence for operations |", "|---|---|---|",
        "| Who can open it | workspace **Admin** only — not Member, Contributor or Viewer | the "
        "on-call role needs Admin on the warehouse workspace, or works from the views below |",
        "| Latency | up to **15 minutes** | not a live signal; alerts stay with the job alerts and "
        "the KQL rule above |",
        "| Result cap | top **10,000** rows per filter | narrow the time range before concluding "
        "that a query is absent |",
        "| Same data, scriptable | `queryinsights.exec_requests_history` and the other Query "
        "insights views | use the views for evidence and trend reports; the Monitor for the "
        "incident itself |", "",
        "It raises no alerts. Failed warehouse *jobs* are covered by the job alerts (step 2, job "
        "type *Warehouse*); a slow or failing *query* is only visible here or in the views.",
        *_result_set_cache_lines(),
        *_activator_sql_lines(),
    ]


def _result_set_cache_lines() -> list[str]:
    """Result set caching (I-21 W5.8): ab Werk an, Folgen fuer Kosten, Frische und Messung.

    Belegt per Learn-MCP am 30.09.2026: `fabric/data-warehouse/result-set-caching` (ab Werk an fuer
    Warehouses und SQL-Analyseendpunkte; Abschalten je Item per ``ALTER DATABASE``, je Abfrage per
    Hint; Invalidierung bei Aenderung; Ausschluesse; 24 Stunden ohne Nutzung) und „What's new"
    September 2026 („Result set caching is enabled by default"). **GA** sagt keine der beiden Seiten
    woertlich; die Seite traegt keinen Preview-Hinweis. GA steht im Plan I-21 — hier deshalb nur
    „ab Werk an".
    """
    return [
        "", "### Result set caching is on by default", "",
        "Warehouses and SQL analytics endpoints cache the final result of eligible `SELECT` "
        "queries and answer repeats from that cache. Three consequences for operations:", "",
        "| Concern | What happens | What to do |", "|---|---|---|",
        "| **Freshness** | any change to a referenced table invalidates the cache; queries with "
        "`GETDATE()`, `CURRENT_USER`, row-level security, dynamic data masking or time travel are "
        "never cached | nothing — a cache hit is not stale data |",
        "| **Cost** | a hit skips compilation and data processing, so repeated report queries use "
        "less capacity | read capacity figures of repeated queries as cached cost, not as the "
        "cost of the query itself |",
        "| **Measurement** | a repeated query can be answered from the cache, so its runtime says "
        "nothing about the query | for timing comparisons and load tests add `OPTION ( USE HINT "
        "('DISABLE_RESULT_SET_CACHE') )`; the Monitor's *result cache hit* column shows which "
        "runs were hits |",
        "",
        "Check per item: `SELECT name, is_result_set_caching_on FROM sys.databases WHERE "
        "database_id = db_id();` — off with `ALTER DATABASE {item} SET RESULT_SET_CACHING OFF;`. "
        "A cache unused for 24 hours is dropped, and cross-database queries never use it.",
    ]


def _activator_sql_lines() -> list[str]:
    """Activator-Regel auf eine Warehouse-SQL-Abfrage als Option (I-21 W5.8, **Preview**).

    Belegt per Learn-MCP am 30.09.2026: `real-time-intelligence/data-activator/set-alerts-
    warehouse-sql-query` (nur ``SELECT``, Takt „Run query every", Alarm wenn die Abfrage Zeilen
    liefert, Bedingung „On each event") und `activator-introduction` (Preview-Kennzeichnung).
    Kein Emitter: die Regel entsteht im SQL-Editor; eine Regeldatei ohne dokumentierte Definition
    waere eine geratene.
    """
    return [
        "", "### Option: an Activator rule on a warehouse SQL query (preview)", "",
        "For checks that live in the warehouse rather than in a job log — a gold table that did "
        "not grow today, a reconciliation difference above zero — Activator can run a SQL query on "
        "a schedule and alert when it **returns rows**. In the warehouse's SQL query editor: run a "
        "`SELECT`, then **Create rule**; set *Run query every*, keep *On each event*, choose email, "
        "Teams or a Fabric item as action, and save the rule to the monitoring workspace's "
        "Activator item.", "",
        "- Write the query so that **an empty result means healthy**: every returned row is one "
        "alert, on every run.",
        "- Each run is a warehouse query on the capacity; choose the interval to match how often "
        "the data changes, not as short as possible.",
        "- Preview: keep the job alerts and the KQL rule above as the primary signal; this rule "
        "adds a data condition, it does not replace them.",
    ]


def _activity_log_lines() -> list[str]:
    """Der Abschnitt zum Protokoll-Export in `_MONITORING.md`. Englisch wie der Rest der Datei."""
    return [
        "", "## Keeping the activity log past its window", "",
        f"The Power BI activity log is retrievable for **{ACTIVITY_LOG_DAYS} days**, and capacity "
        "metrics show 14. After that, every question about last year is not hard to answer — it is "
        "unanswerable, because the data is gone. `activity_log_export.py` exports **yesterday** "
        "(D-1) once a day into Bronze.", "",
        "| Property | Value | Why |", "|---|---|---|",
        "| Window | D-1, one full UTC day | a run for the current day fetches half a day and looks "
        "complete |",
        f"| Retention of the export | {ACTIVITY_EXPORT_RETENTION_MONTHS} months | a year-on-year "
        "comparison needs one month more than a year |",
        "| Shape | raw JSON, unfiltered (ELT) | fields differ per event type and change with the "
        "service; what the export drops is gone for good |",
        "| Cost | 24 requests per day | the API allows 200 per hour |",
        "",
        "Where Microsoft Purview is in place, its default 180-day retention covers the gap between "
        "two failed exports. That is a net, not a replacement: 180 days is still not a year.", "",
        "Two conditions that end the run before it starts. The caller is a Fabric administrator or a "
        "service principal — and a service principal used here **must not** carry any admin-consent "
        "Power BI permissions on its app registration. The `Tenant.Read.All` scope belongs to the "
        "delegated path only and must not be sent on the service-principal path.", "",
        "> The export is itself a logged operation (`ExportActivityEvents`). When you analyse user",
        "> activity, separate the admin events out or you will measure your own job.",
    ]


def _region_zeilen(rp: dict) -> list[str]:
    """Schritt 1d: Ergebnis der Regionspruefung fuer die zentrale Topologie."""
    if rp["status"] == "nicht_anwendbar":
        return []
    if rp["status"] == "abweichend":
        teile = "; ".join(f"`{reg}`: " + ", ".join(f"`{w}`" for w in ws)
                          for reg, ws in rp["regionen"].items())
        return ["1d. **BLOCKER — regions differ.** *Send data to Eventhouse in another Monitoring "
                "Item* needs source and destination workspace in the **same Azure region** (Learn, "
                f"read 2026-09-30), and the blueprint's capacities span several: {teile}. One "
                "central monitoring item per region, or move the capacities — decide before step 1; "
                "the destination cannot be changed afterwards."]
    if rp["status"] == "unbekannt":
        offen = ", ".join(f"`{w}`" for w in rp["ohne_region"]) or "—"
        return ["1d. **Region check open.** The central topology needs every source workspace in "
                "the destination's Azure region. Not decidable from the blueprint: capacities "
                f"without `region` for {offen}"
                + ("" if rp.get("zentral_workspace_im_bauplan") else
                   "; the central monitoring workspace is not in the blueprint")
                + ". Check the region of each capacity (Monitor hub → Capacities, column *Region*) "
                "before step 1."]
    return ["1d. Region check: all source workspaces and the central monitoring workspace sit on "
            "capacities in `" + next(iter(rp["regionen"])) + "` — the same-region condition holds."]


def emit_monitoring(bp: dict, stack: str = "fabric", workspace: str = "<workspace>",
                    capacity: str = "<CAPACITY_NAME>", alerts: dict | None = None,
                    stages: tuple[str, ...] = ("dev", "test", "prod"),
                    monitoring: dict | None = None,
                    varlib_config: dict | None = None) -> dict[str, str]:
    """Return the monitoring/alerting artifact set (path → content). Fabric-specific surfaces (KQL,
    Activator specs) are emitted for the fabric stack; the plan doc is always emitted.

    ``monitoring`` ist die Monitoring-Politik (``MONITORING_POLITIK_VORGABE``: Aufbewahrung,
    Topologie, Optionen des Monitoring-Items, Kapazitaetsschwellen). Ungueltig → ``ValueError``."""
    alerts = alerts or {}
    politik = monitoring_politik(monitoring)
    n_ws = len(_domains(bp))
    zentral = politik["topologie"] == "zentral"
    aufbewahrung = politik["aufbewahrung_tage"]
    doc = [
        "# Monitoring & alerting (generated — grounded MS Learn 2026-07)", "",
        f"Stack: **{stack}**  ·  Workspaces watched: **{len(_domains(bp))} domain(s)**  ·  "
        f"Capacity: **{capacity}**", "",
        "At the fidelity Fabric supports — real artifacts where deployable, specs + runbook where the",
        "surface is portal-authored (honest, never a faked API):", "",
        "| Signal | Artifact | Mechanism | Status |", "|---|---|---|---|",
        "| Any job failure (pipeline / refresh / notebook), workspace-wide | `workspace_job_failures.kql` | "
        "Workspace monitoring → ItemJobEventLogs KQL → Activator rule | deployable KQL + portal rule |",
        f"| The monitoring item itself (topology, options, retention) | `{MONITORING_ITEM_PATH.split('/')[-1]}` "
        "| monitoring item, created from the workspace settings (step 1) | portal spec, decisions "
        "first |",
        f"| Job started / succeeded / failed, nine job types | `{JOB_ALERTS_PATH.split('/')[-1]}` | "
        "Monitor hub → Job runs → Alerts (paid) → Activator | portal rule spec (preview) |",
        "| Scheduled pipeline failure | `pipeline_failure_notifications.md` | built-in Failure notifications | GA, per-item |",
        "| Capacity throttling / state | `capacity_throttling_alert.json` + "
        f"`{CAPACITY_ALERTS_RUNBOOK_PATH.split('/')[-1]}` | Capacity Overview Events → Set capacity "
        "alert templates → Activator | portal rule spec + runbook |",
        "| Compute/storage dashboards | `capacity_metrics_app_setup.md` → Fabric **Capacity Metrics "
        "App** | built-in, portal install | GA |",
        "| Warehouse / SQL analytics endpoint queries: running, history, long-running, frequent "
        "(I-21 W6.11) | none — see *Warehouse queries* below | built-in **Monitor** on the "
        "warehouse | portal, preview |",
        "| Audit history beyond the retention window | `activity_log_export.py` | Get Activity Events "
        "(admin REST) → Bronze, daily D-1 | runnable script |",
        f"| …made queryable | `{ACTIVITY_BRONZE_LOAD_PATH.split('/')[-1]}` | raw files → Delta table "
        f"`{ACTIVITY_BRONZE_TABLE}`, replace-per-day | runnable script |",
        f"| …run every day | `{ACTIVITY_SCHEDULE_PATH.split('/')[-1]}` | item schedule, "
        f"{ACTIVITY_SCHEDULE_TIME_UTC} UTC daily | deployable JSON |", "",
        "## Setup order", "",
        "0. **Tenant setting first, and only a Fabric administrator can set it.** Admin portal → "
        "Tenant settings → *Workspace admins can turn on monitoring for their workspaces*. Until "
        "that switch is on, step 1 is not offered in any workspace, and a workspace admin cannot "
        "turn it on for themselves. One switch for the whole tenant, once. A second tenant "
        "setting fails silently: *Users can create Fabric items* must be on for whoever runs "
        "step 1 — without it **Monitoring** is greyed out and no error is shown (MS Learn, "
        "*Configure workspace monitoring*, read 2026-09-29).",
        "1. Enable **Workspace monitoring** on each workspace: Workspace settings → Monitoring → "
        "**Enable**. This creates a **monitoring item** (Eventhouse with a read-only KQL "
        "database, Eventstream, Activator, optionally an Operations Agent) — the legacy "
        "*+Eventhouse* path is the old model. "
        f"That is **{n_ws} portal step(s)** for this blueprint, one per workspace that carries "
        "scheduled load"
        + (", plus **1** for the central monitoring workspace, which gets its own item first; "
           "every other workspace then sends to *Eventhouse in another Monitoring Item*. "
           "Microsoft recommends this topology: one central monitoring Eventhouse on its own "
           "capacity. Same Azure region required, and each source adds one KQL database to the "
           f"central workspace's {WORKSPACE_ITEM_LIMIT}-item limit."
           if zentral else
           ". Topology *per workspace* — a deliberate deviation from Microsoft's recommendation "
           "of one central monitoring Eventhouse on its own capacity.")
        + " The destination cannot be changed later. No REST path for the monitoring item is "
        "documented (checked 2026-09-29), so this cannot be scripted with the rest of the "
        "provisioning. Two conditions decide whether the step is even offered: the workspace "
        "must already sit on a capacity, and you must hold the workspace **admin** role — "
        "contributor is not enough. Collection is **off** when the item is created: finish "
        "with *Turn on data collection*, or nothing is recorded. "
        f"The item's options and topology are in `{MONITORING_ITEM_PATH.split('/')[-1]}`.",
        "1a. **Where Power BI Log Analytics is already configured, this step fails — and the fix "
        "costs hours, not minutes.** A workspace can carry workspace monitoring or Log Analytics, "
        "never both. Delete the Log Analytics configuration, then wait *a few hours* before "
        "enabling monitoring. On a brownfield tenant this is the one item in the whole setup order "
        "that cannot be done on the day it is discovered, so check it before the day is planned. "
        "(Read 2026-08-16 for the legacy path; the monitoring-item pages read 2026-09-29 no longer "
        "state it — ASSUMPTION, unverified for the new model, so check anyway.)",
        "1c. **Decide the item's options before the item is created — two of them are one-way.** "
        "Microsoft preselects *all* options on Enable: diagnostic data (audit, compliance logs, "
        "telemetry — higher ingestion cost on the capacity) and **AI powered investigations**. "
        "The latter adds the Operations Agent, and an enabled Operations Agent cannot be switched "
        "off again. It also needs the tenant settings for Operations Agent, Copilot and Azure "
        "OpenAI, and no trial capacity — a GDPR/Copilot question for the customer, not a click. "
        "The **custom endpoint** (export via Event Hubs/Kafka/AMQP) can only be enabled at "
        "creation during the preview. Untick whatever is still open in "
        f"`{MONITORING_ITEM_PATH.split('/')[-1]}` → `offene_entscheidungen`.",
        *_region_zeilen(region_pruefung(bp, politik)),
        "1b. **Capacity notifications** (Admin portal → Capacity settings → Notifications): a "
        "percentage threshold and *capacity exceeded*, to the capacity admins. Five clicks, no "
        "infrastructure, and independent of everything below — it is the only signal in this list "
        "that survives a workspace being misconfigured. Its blind spots are in "
        "`capacity_metrics_app_setup.md`.",
        "2. **Job alerts** (Monitor hub → Job runs → … → *Create and manage alerts* → *Alerts "
        f"(paid)*, preview) per job type from `{JOB_ALERTS_PATH.split('/')[-1]}`: pipeline, Spark "
        "job, notebook, user data function, warehouse, lakehouse, mirrored database, SQL database, "
        "KQL database. Needs the monitoring item from step 1 and Owner or Contributor. Semantic "
        "models, Dataflow Gen2 and Copy job are not in that list — for them steps 3 and 4 remain "
        "the only alert.",
        "3. Create a **KQL Queryset** from `workspace_job_failures.kql` (fallback for the job "
        "types above, the only rule for the rest).",
        "4. Create an **Activator** rule on that queryset → email/Teams to the on-call recipients.",
        "4a. Create the **capacity** alerts from the *Set capacity alert* templates — exact "
        f"values in `{CAPACITY_ALERTS_RUNBOOK_PATH.split('/')[-1]}` (spec: "
        "`capacity_throttling_alert.json`). Capacity Admin on a non-trial capacity.",
        "4b. For a failed pipeline run, **Investigate** (Monitor hub → Job runs → run history) "
        "starts a read-only root-cause analysis by the Operations Agent. Only available if the "
        "agent exists (step 1c) — with its tenant prerequisites (Operations Agent, Copilot, "
        "Azure OpenAI; no trial capacity).",
        "5. Set built-in **Failure notifications** per scheduled **item** — the setting hangs off the item "
        "and covers all its schedules (`pipeline_failure_notifications.md`).",
        "6. Evidence the step in **Monitoring hub → Schedule failures** (preview): it lists every item "
        "with notifications and its recipients. There is no API field for it — the v1 `ItemSchedule` "
        "schema carries none (fetched 2026-08-14).",
        "7. Install the **Capacity Metrics App** — `capacity_metrics_app_setup.md`. It belongs "
        f"here on day 0 rather than at handover because its compute window is "
        f"**{METRICS_APP_COMPUTE_DAYS} days** and cannot be filled backwards, for the same reason "
        "steps 0 and 1 do. Only a capacity admin can install it.",
        f"8. Import `activity_log_export.py` and `{ACTIVITY_BRONZE_LOAD_PATH.split('/')[-1]}` as **one** "
        "notebook, export first and load second, then register the daily schedule from "
        f"`{ACTIVITY_SCHEDULE_PATH.split('/')[-1]}` on it: "
        f"`POST {schedule_endpoint(JOB_TYPE_NOTEBOOK)}`. `jobType` is a "
        "required path segment and it is case sensitive; for a notebook it is `RunNotebook` "
        "(MS Learn, *Create Item Schedule* + *Run a Fabric item using Apache Airflow DAGs*, read "
        "2026-08-20). It belongs to "
        "day 0 for the same reason as steps 0 and 1: it is not retroactive beyond its window, and "
        f"the window is {ACTIVITY_LOG_DAYS} days wide.", "",
        "Steps 0 and 1 belong **before the first scheduled run**. Monitoring is not retroactive: the "
        "history starts when the switch is flipped, and runs that happened earlier leave no trace in "
        "the Eventhouse. A platform that gets monitoring on handover day has no run history for its "
        "whole build phase.", "",
        "Three properties worth planning around (MS Learn, *Workspace monitoring overview* → "
        "Considerations and limitations, read 2026-08-16 and 2026-09-29): the monitoring items are "
        "billed against the capacity they consume; the legacy path cannot filter ingestion by log "
        "type, so a workspace is either fully monitored or not at all; retention is an Eventhouse "
        f"data policy, {WORKSPACE_MONITORING_RETENTION_DEFAULT_DAYS} days by default and "
        f"changeable — this delivery sets **{aufbewahrung} days** (monitoring KQL database → "
        "Manage → Data policies; caching must not exceed retention).", "",
        "### What survives a bad day, and what doesn't", "",
        "The layer above is not one thing under pressure, and the split is documented rather than "
        "guessed (same source):", "",
        "| Under a throttled capacity | Behaviour |", "|---|---|",
        "| Queries against the monitoring Eventhouse, and its ingestion | keep working — the "
        "capacity state does not reach them |",
        "| Power BI reports and **Activator alerts** built on the monitoring database | throttled "
        "like everything else |", "",
        "Read the second row twice. The job-failure alert from step 4 sits on the monitoring "
        "database, so a throttled capacity silences the alert at the moment it has the most to "
        "report. The capacity-side signals — the built-in notification from step 1b and the "
        "Capacity Overview Events rule from step 4a — do not come from that database, which is why "
        "this delivery emits both layers instead of the cheaper one. A central monitoring "
        "workspace on its own capacity (step 1) narrows the gap: throttling of the production "
        "capacity no longer reaches the monitoring database.", "",
        "Two repair moves for the **legacy** monitoring Eventhouse that are not obvious from the "
        "UI. A table missing from the monitoring Eventhouse usually means the Eventhouse predates "
        "that table: turn **Log workspace activity** off in the workspace settings and on again, "
        "and it is recreated. And the monitoring Eventhouse is **read-only** — deleting it goes "
        "through the workspace settings, and recreating it needs about 15 minutes of patience, "
        "not a second attempt. Migrating legacy to the monitoring item is manual (turn *Log "
        "workspace activity* off, then the migration banner); old data stays in the legacy "
        "Eventhouse.", "",
        "> **Private links and workspace monitoring:** the monitoring item supports private links "
        "(MS Learn, read 2026-09-29) — if enabling fails, disable the workspace's private links, "
        "enable monitoring, re-enable them. The **legacy** path (+Eventhouse) does not support "
        "private links. Until 2026-09-29 this document said they do not mix; that was the legacy "
        "statement; `connectivity/_CONNECTIVITY.md` carries the same current statement.", "",
        "> Activator must poll more frequently than the KQL time window, else failures are missed. Use",
        "> stateful operators + preview-before-activate to avoid alert spam (grounded).", "",
        *((_warehouse_monitor_lines() + [""] + _operations_agent_lines(politik))
          if stack == "fabric" else []),
        *_activity_log_lines(),
    ]
    out: dict[str, str] = {"monitoring/_MONITORING.md": "\n".join(doc) + "\n",
                           "monitoring/pipeline_failure_notifications.md":
                               _pipeline_failure_runbook(bp, alerts, stages)}
    _note = gap_doc_for(bp, "monitoring", "Monitoring & Alerting")
    if _note:                       # fremder Stack: eigene Mechanismen, nicht die Fabric-Antwort
        out["monitoring/_MONITORING.md"] = _note
    if stack == "fabric":
        out["monitoring/workspace_job_failures.kql"] = _workspace_failures_kql()
        out["monitoring/capacity_throttling_alert.json"] = _capacity_throttling_rule(
            capacity, alerts, politik)
        out[CAPACITY_ALERTS_RUNBOOK_PATH] = _capacity_alerts_md(capacity, alerts, politik)
        out[MONITORING_ITEM_PATH] = json.dumps(_monitoring_item_spec(bp, politik), indent=2,
                                               ensure_ascii=False) + "\n"
        out[JOB_ALERTS_PATH] = json.dumps(_job_alerts_spec(alerts), indent=2,
                                          ensure_ascii=False) + "\n"
        stufen = tuple(stages) or ("dev",)
        for stufe in stufen:   # D-597: je Stufe eine Definition mit dem Namen dieser Stufe
            out[operations_agent_path(stufe)] = json.dumps(
                _operations_agent_definition(bp, politik, stufe), indent=2,
                ensure_ascii=False) + "\n"
        from core.dataarch_engine.blueprint.provision_varlib import emit_item_reference_library
        out.update(emit_item_reference_library(
            MONITORING_VARLIB, MONITORING_VARLIB_REFS, _agent_workspace(politik),
            stages=stufen, env_config=varlib_config, prefix="monitoring/",
            workspaces_je_stufe={st: agent_workspace(politik, st) for st in stufen}))
        out[METRICS_APP_SETUP_PATH] = _metrics_app_setup_md(capacity, alerts)
        # Der Export haengt am Power-BI-/Fabric-Aktivitaetsprotokoll. Auf einem fremden Stack gibt
        # es dieses Protokoll nicht — ein Skript dafuer waere dort eine Anweisung ins Leere.
        out[ACTIVITY_EXPORT_PATH] = _activity_log_export_py()
        # Sammeln ist nicht dasselbe wie verfuegbar machen: ohne den Lader liegen die Dateien da
        # und sind nicht zu befragen, ohne den Zeitplan sammelt niemand (BK-B04).
        out[ACTIVITY_BRONZE_LOAD_PATH] = _activity_log_bronze_load_py()
        out[ACTIVITY_SCHEDULE_PATH] = _activity_log_schedule_json()
    globals().setdefault("_x", 0)
    return out
