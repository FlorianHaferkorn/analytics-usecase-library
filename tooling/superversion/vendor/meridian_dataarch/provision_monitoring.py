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
    / notebook). Grounded verbatim-shape in MS Learn (workspace-level alerts). Real, deployable."""
    return (
        "// Workspace-wide job failures — deploy as a KQL Queryset, then bind an Activator rule to it.\n"
        "// Prereq: enable Workspace monitoring (writes ItemJobEventLogs into the monitoring Eventhouse).\n"
        "// Catches pipeline, semantic-model refresh and notebook job failures in one rule.\n"
        "ItemJobEventLogs\n"
        "| extend SecondsAgo = datetime_diff('second', now(), ingestion_time())\n"
        "| where JobStatus == 'Failed'\n"
        "| where SecondsAgo <= 540   // Activator must poll more often than this window\n"
        "| order by Timestamp desc\n"
        "| project Timestamp, JobType, ItemName, WorkspaceName, JobStartTime, JobEndTime, JobStatus\n"
    )


def _capacity_throttling_rule(capacity: str, alerts: dict) -> str:
    """Activator rule spec over Capacity Overview Events — grounded thresholds (Monitor Fabric Capacity
    Health). Emitted as a declarative spec (Activator rules are authored in Real-Time Hub / Activator)."""
    spec = {
        "_note": ("Author in Real-Time Hub → Capacity Overview Events → Set alert (or an Activator rule). "
                  "This is the rule to reproduce; there is no deterministic create-API for Activator rules."),
        "source": "Capacity Overview Events",
        "capacity": capacity,
        "groupingField": "capacityId",
        "rules": [
            {"when": "backgroundRejectionThresholdPercentage", "condition": "increases to or above",
             "value": 80, "meaning": "background operations rejected under capacity pressure"},
            {"when": "interactiveRejectionThresholdPercentage", "condition": "increases to or above",
             "value": 80, "meaning": "interactive operations rejected (reports failing)"},
            {"when": "interactiveDelayThresholdPercentage", "condition": "increases to or above",
             "value": 80, "meaning": "interactive operations delayed (reports slow)"},
        ],
        "action": {"type": "email", "to": _recipients(alerts, "capacity"),
                   "subject": "Fabric Capacity Throttling Alert",
                   "note": "Capacity exceeded rejection threshold: @backgroundRejectionThresholdPercentage%"},
        "escalation": "Optionally set action=Run function (UDF) for auto-mitigation (pause/resume, scale).",
    }
    return json.dumps(spec, indent=2, ensure_ascii=False) + "\n"


def _pipeline_failure_runbook(bp: dict, alerts: dict,
                              stages: tuple[str, ...] = ("dev", "test", "prod")) -> str:
    """Runbook fuer die Fehlerbenachrichtigung — inklusive der Frage, wie man sie nachweist (Z11).

    Der HOCHTIEF-Lauf 2 hat den Schritt als einen von drei Menschenschritten je Auslieferung
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


def emit_monitoring(bp: dict, stack: str = "fabric", workspace: str = "<workspace>",
                    capacity: str = "<CAPACITY_NAME>", alerts: dict | None = None,
                    stages: tuple[str, ...] = ("dev", "test", "prod")) -> dict[str, str]:
    """Return the monitoring/alerting artifact set (path → content). Fabric-specific surfaces (KQL,
    Activator specs) are emitted for the fabric stack; the plan doc is always emitted."""
    alerts = alerts or {}
    doc = [
        "# Monitoring & alerting (generated — grounded MS Learn 2026-07)", "",
        f"Stack: **{stack}**  ·  Workspaces watched: **{len(_domains(bp))} domain(s)**  ·  "
        f"Capacity: **{capacity}**", "",
        "At the fidelity Fabric supports — real artifacts where deployable, specs + runbook where the",
        "surface is portal-authored (honest, never a faked API):", "",
        "| Signal | Artifact | Mechanism | Status |", "|---|---|---|---|",
        "| Any job failure (pipeline / refresh / notebook), workspace-wide | `workspace_job_failures.kql` | "
        "Workspace monitoring → ItemJobEventLogs KQL → Activator rule | deployable KQL + portal rule |",
        "| Scheduled pipeline failure | `pipeline_failure_notifications.md` | built-in Failure notifications | GA, per-item |",
        "| Capacity throttling | `capacity_throttling_alert.json` | Capacity Overview Events → Activator | portal rule spec |",
        "| Compute/storage dashboards | Fabric **Capacity Metrics App** (install) | built-in | GA |", "",
        "## Setup order", "",
        "1. Enable **Workspace monitoring** on each workspace (job logs → monitoring Eventhouse).",
        "2. Create a **KQL Queryset** from `workspace_job_failures.kql`.",
        "3. Create an **Activator** rule on that queryset → email/Teams to the on-call recipients.",
        "4. Create the **capacity** Activator rule from `capacity_throttling_alert.json`.",
        "5. Set built-in **Failure notifications** per scheduled **item** — the setting hangs off the item "
        "and covers all its schedules (`pipeline_failure_notifications.md`).",
        "6. Evidence the step in **Monitoring hub → Schedule failures** (preview): it lists every item "
        "with notifications and its recipients. There is no API field for it — the v1 `ItemSchedule` "
        "schema carries none (fetched 2026-08-14).",
        "7. Install the **Capacity Metrics App** for CU/storage dashboards.", "",
        "> Activator must poll more frequently than the KQL time window, else failures are missed. Use",
        "> stateful operators + preview-before-activate to avoid alert spam (grounded).",
    ]
    out: dict[str, str] = {"monitoring/_MONITORING.md": "\n".join(doc) + "\n",
                           "monitoring/pipeline_failure_notifications.md":
                               _pipeline_failure_runbook(bp, alerts, stages)}
    _note = gap_doc_for(bp, "monitoring", "Monitoring & Alerting")
    if _note:                       # fremder Stack: eigene Mechanismen, nicht die Fabric-Antwort
        out["monitoring/_MONITORING.md"] = _note
    if stack == "fabric":
        out["monitoring/workspace_job_failures.kql"] = _workspace_failures_kql()
        out["monitoring/capacity_throttling_alert.json"] = _capacity_throttling_rule(capacity, alerts)
    return out
