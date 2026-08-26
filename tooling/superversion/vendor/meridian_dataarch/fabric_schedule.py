"""fabric_schedule.py — die Form eines Fabric-Item-Zeitplans, an genau einer Stelle.

Zwei Emitter planen etwas ein: `provision_orchestration` die Medaillon-Pipeline und
`provision_monitoring` den Export des Aktivitaetsprotokolls. Beide brauchen dieselbe
Kenntnis — welche Felder eine Konfiguration traegt und wie das Pflichtsegment `jobType`
im Pfad heisst. Zwei Kopien driften, also gibt es eine.

Warum ein eigenes Modul und nicht ein Import quer zwischen den beiden: `provision_monitoring`
ist in ALUCA **vendort** (`tooling/superversion/vendor/meridian_dataarch/`), und ein
gespiegeltes Modul, das ein nicht gespiegeltes importiert, bricht dort beim ersten Aufruf.
Der gespiegelte Satz muss in sich geschlossen sein. Dieses Modul haelt sich deshalb
abhaengigkeitsarm (nur `json`) — dieselbe Ueberlegung, die `stack_capabilities.py` traegt.

Gemessen 20.08.2026 gegen MS Learn:
- `core/job-scheduler/create-item-schedule` — Pfad
  ``POST /v1/workspaces/{workspaceId}/items/{itemId}/jobs/{jobType}/schedules``, `jobType`
  ist Pflicht-URI-Parameter. `CronScheduleConfig` traegt `interval` (Minuten, 1…5270400) und
  **kein** `times`; `DailyScheduleConfig` und `WeeklyScheduleConfig` tragen `times` und
  **kein** `interval`. Beide Beispiele derselben Seite bestaetigen die Trennung.
  `WeeklyScheduleConfig` verlangt zusaetzlich `weekdays` (hoechstens sieben Eintraege),
  `MonthlyScheduleConfig` `occurrence` und `recurrence` — Letzteres ist hier nicht gebaut,
  weil es kein Aufrufer braucht; ein ungenutzter Zweig waere ungeprueft.
  Maximal 20 Zeitplaene je Item, `localTimeZoneId` ist eine Windows-Zeitzonen-Kennung.
- `data-factory/apache-airflow-jobs-run-fabric-item-job` — die Job-Typen woertlich:
  *„for notebook use \"RunNotebook\", for Spark Job Definitions use \"sparkjob\" and for
  pipelines use \"Pipeline\". This is case sensitive."*
"""
from __future__ import annotations

import json

#: Job-Typen als Pfadsegment. Gross-/Kleinschreibung ist bedeutsam — die Quelle sagt es selbst.
JOB_TYPE_NOTEBOOK = "RunNotebook"
JOB_TYPE_PIPELINE = "Pipeline"

#: Konfigurationstypen, die Uhrzeiten tragen. Alles andere rechnet in Minuten.
_MIT_UHRZEITEN = ("Daily", "Weekly", "Monthly")


def schedule_endpoint(job_type: str) -> str:
    """Der REST-Pfad zum Anlegen eines Zeitplans, mit gesetztem `jobType`.

    Ohne das Segment antwortet der Dienst nicht — es ist Pflicht und kein Standardwert.
    """
    return ("/v1/workspaces/{workspaceId}/items/{itemId}/jobs/"
            f"{job_type}/schedules")


def emit_schedule(frequency: str = "Daily", interval: int = 1,
                  time: str = "02:00", timezone: str = "UTC",
                  weekdays: tuple[str, ...] = ("Monday",)) -> str:
    """Return ``schedule.json`` — ein Fabric-Item-Zeitplan (Vorgabe: taeglich 02:00 UTC).

    **Korrigierter Defekt, benannt statt still geaendert (Belegpflicht Regel 5):** bis zum
    20.08.2026 schrieb diese Funktion `interval` in *jede* Konfiguration, also auch in die
    taegliche. Das Feld existiert dort im Schema nicht; jede erzeugte `schedule.json` trug es
    seit ihrer Einfuehrung mit.
    """
    cfg: dict = {"type": frequency, "localTimeZoneId": timezone,
                 "startDateTime": "<YYYY-MM-DDT00:00:00>"}
    if frequency in _MIT_UHRZEITEN:
        cfg["times"] = [time]
    else:
        cfg["interval"] = interval
    if frequency == "Weekly":
        # `weekdays` ist bei WeeklyScheduleConfig kein Zusatz, sondern der Teil, der die Woche
        # ueberhaupt bestimmt. Ohne ihn steht ein Zeitplan da, der nie sagt, wann er laeuft.
        cfg["weekdays"] = list(weekdays)
    return json.dumps({"enabled": True, "configuration": cfg},
                      indent=2, sort_keys=True, ensure_ascii=False) + "\n"
