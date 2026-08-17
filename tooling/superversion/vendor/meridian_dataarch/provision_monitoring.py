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

#: Aufbewahrung der Workspace-Monitoring-Daten. Fest, nicht einstellbar (BK-B01).
WORKSPACE_MONITORING_RETENTION_DAYS = 30

#: Ruhezeit nach einer Kapazitaets-Benachrichtigung aus dem Admin-Portal. Danach schweigt sie,
#: auch wenn die Schwelle erneut gerissen wird — der Grund, warum sie die Activator-Regel
#: ergaenzt und nicht ersetzt.
CAPACITY_NOTIFICATION_MUTE_HOURS = 3

METRICS_APP_SETUP_PATH = "monitoring/capacity_metrics_app_setup.md"


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
        "| Compute/storage dashboards | `capacity_metrics_app_setup.md` → Fabric **Capacity Metrics "
        "App** | built-in, portal install | GA |",
        "| Audit history beyond the retention window | `activity_log_export.py` | Get Activity Events "
        "(admin REST) → Bronze, daily D-1 | runnable script |", "",
        "## Setup order", "",
        "0. **Tenant setting first, and only a Fabric administrator can set it.** Admin portal → "
        "Tenant settings → *Workspace admins can turn on monitoring for their workspaces*. Until "
        "that switch is on, step 1 is not offered in any workspace, and a workspace admin cannot "
        "turn it on for themselves. One switch for the whole tenant, once.",
        "1. Enable **Workspace monitoring** on each workspace (job logs → monitoring Eventhouse). "
        f"That is **{len(_domains(bp))} portal step(s)** for this blueprint, one per workspace that "
        "carries scheduled load, and each one is a manual step: Workspace settings → Monitoring → "
        "+Eventhouse. No REST path for it is documented (checked 2026-08-16), so this cannot be "
        "scripted with the rest of the provisioning. Two conditions decide whether the step is "
        "even offered: the workspace must already sit on a capacity, and you must hold the "
        "workspace **admin** role — contributor is not enough.",
        "1a. **Where Power BI Log Analytics is already configured, this step fails — and the fix "
        "costs hours, not minutes.** A workspace can carry workspace monitoring or Log Analytics, "
        "never both. Delete the Log Analytics configuration, then wait *a few hours* before "
        "enabling monitoring. On a brownfield tenant this is the one item in the whole setup order "
        "that cannot be done on the day it is discovered, so check it before the day is planned.",
        "1b. **Capacity notifications** (Admin portal → Capacity settings → Notifications): a "
        "percentage threshold and *capacity exceeded*, to the capacity admins. Five clicks, no "
        "infrastructure, and independent of everything below — it is the only signal in this list "
        "that survives a workspace being misconfigured. Its blind spots are in "
        "`capacity_metrics_app_setup.md`.",
        "2. Create a **KQL Queryset** from `workspace_job_failures.kql`.",
        "3. Create an **Activator** rule on that queryset → email/Teams to the on-call recipients.",
        "4. Create the **capacity** Activator rule from `capacity_throttling_alert.json`.",
        "5. Set built-in **Failure notifications** per scheduled **item** — the setting hangs off the item "
        "and covers all its schedules (`pipeline_failure_notifications.md`).",
        "6. Evidence the step in **Monitoring hub → Schedule failures** (preview): it lists every item "
        "with notifications and its recipients. There is no API field for it — the v1 `ItemSchedule` "
        "schema carries none (fetched 2026-08-14).",
        "7. Install the **Capacity Metrics App** — `capacity_metrics_app_setup.md`. It belongs "
        f"here on day 0 rather than at handover because its compute window is "
        f"**{METRICS_APP_COMPUTE_DAYS} days** and cannot be filled backwards, for the same reason "
        "steps 0 and 1 do. Only a capacity admin can install it.",
        "8. Schedule `activity_log_export.py` daily (see below). It belongs to day 0 for the same "
        "reason as steps 0 and 1: it is not retroactive beyond its window, and the window is "
        f"{ACTIVITY_LOG_DAYS} days wide.", "",
        "Steps 0 and 1 belong **before the first scheduled run**. Monitoring is not retroactive: the "
        "history starts when the switch is flipped, and runs that happened earlier leave no trace in "
        "the Eventhouse. A platform that gets monitoring on handover day has no run history for its "
        "whole build phase.", "",
        "Three properties worth planning around (MS Learn, *Workspace monitoring overview* → "
        "Considerations and limitations, read 2026-08-16): the monitoring items are billed against "
        "the capacity they consume; ingestion cannot be filtered by log type, so a workspace is "
        f"either fully monitored or not at all; retention is fixed at "
        f"{WORKSPACE_MONITORING_RETENTION_DAYS} days.", "",
        "### What survives a bad day, and what doesn't", "",
        "The layer above is not one thing under pressure, and the split is documented rather than "
        "guessed (same source):", "",
        "| Under a throttled capacity | Behaviour |", "|---|---|",
        "| Queries against the monitoring Eventhouse, and its ingestion | keep working — the "
        "capacity state does not reach them |",
        "| Power BI reports and **Activator alerts** built on the monitoring database | throttled "
        "like everything else |", "",
        "Read the second row twice. The job-failure alert from step 3 sits on the monitoring "
        "database, so a throttled capacity silences the alert at the moment it has the most to "
        "report. The capacity-side signals — the built-in notification from step 1b and the "
        "Capacity Overview Events rule from step 4 — do not come from that database, which is why "
        "this delivery emits both layers instead of the cheaper one.", "",
        "Two repair moves that are not obvious from the UI. A table missing from the monitoring "
        "Eventhouse usually means the Eventhouse predates that table: turn **Log workspace "
        "activity** off in the workspace settings and on again, and it is recreated. And the "
        "monitoring Eventhouse is **read-only** — deleting it goes through the workspace settings, "
        "and recreating it needs about 15 minutes of patience, not a second attempt.", "",
        "> **Private links and workspace monitoring do not mix at all** (documented, not a "
        "configuration problem). Where the network stance in `connectivity/_CONNECTIVITY.md` ends "
        "up on private links, this monitoring layer is not available, and the decision has to be "
        "taken with that on the table rather than after.", "",
        "> Activator must poll more frequently than the KQL time window, else failures are missed. Use",
        "> stateful operators + preview-before-activate to avoid alert spam (grounded).",
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
        out["monitoring/capacity_throttling_alert.json"] = _capacity_throttling_rule(capacity, alerts)
        out[METRICS_APP_SETUP_PATH] = _metrics_app_setup_md(capacity, alerts)
        # Der Export haengt am Power-BI-/Fabric-Aktivitaetsprotokoll. Auf einem fremden Stack gibt
        # es dieses Protokoll nicht — ein Skript dafuer waere dort eine Anweisung ins Leere.
        out[ACTIVITY_EXPORT_PATH] = _activity_log_export_py()
    globals().setdefault("_x", 0)
    return out
