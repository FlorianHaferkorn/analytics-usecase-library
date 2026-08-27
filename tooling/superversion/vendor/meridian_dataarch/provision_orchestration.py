"""provision_orchestration — emit a schedulable pipeline that chains ingestion → transforms.

Fourth live-provisioning helper (ADR-0015 follow-up), sibling to provision_fabric /
provision_cicd / provision_transforms. Turns the blueprint's ingestion + transform DAG
into a runnable, scheduled orchestration:

- A stack-agnostic **activity graph** (activities + ``dependsOn`` in medallion order)
  derived from the same IR the transform layer uses — copy-mode ingestion runs first,
  bronze→silver before silver→gold, mirror/shortcut sources are passive (no activity).
- For Fabric: a real **DataPipeline definition** (``pipeline-content.json``,
  ``{properties:{activities:[…]}}`` with ``TridentNotebook``/``Copy`` activities),
  grounded in the documented Fabric definition schema
  (learn.microsoft.com/rest/api/fabric/articles/item-management/definitions/datapipeline-definition),
  plus a ``schedule.json`` and a ``deploy.sh`` that imports the pipeline and registers
  the schedule via ``fab``/``fab api``.

Honest by construction: the DAG (names, order, dependencies) is fully computed from the
IR; the per-activity Fabric IDs (notebookId/workspaceId GUIDs) that only exist on a
tenant are left as ``<…-id>`` placeholders with VERIFY notes — never invented. Sie sind
seit 31.07.2026 **am Workspace-Namen qualifiziert** (``<ws-…-workspace-id>``) und in
``deployment/BINDINGS.json`` deklariert: welcher Schritt sie erzeugt, welche Dateien sie
brauchen. Ein Name, den der Blueprint kennt, wird dagegen eingesetzt statt platzgehalten.

This module **does not execute** anything — it only emits text.
"""
from __future__ import annotations

import json
import re

# `emit_schedule` wohnt in `fabric_schedule` und wird hier re-exportiert: Aufrufer und Tests
# suchen ihn seit je an dieser Stelle.
from core.dataarch_engine.blueprint.fabric_schedule import JOB_TYPE_PIPELINE, emit_schedule
from core.dataarch_engine.blueprint.provision_apply import (
    PLACEHOLDER_WORKSPACE,
    effective_workspace as workspace_of,
)
from core.dataarch_engine.blueprint.provision_notebooks import (
    FRAMING_NOTEBOOK,
    gold_notebook_name,
)
from core.dataarch_engine.blueprint.provision_translations import model_name_of

_NONWORD_RE = re.compile(r"[^a-z0-9]+")

#: Die beiden dokumentierten Wege, ein Semantikmodell aus einer Pipeline heraus zu rahmen.
#: Vorgabe ist ``notebook`` — der Weg, der im Mandanten **angenommen** wurde. Siehe die
#: Modul-Doku und ``_framing_activity``.
REFRESH_PATHS = ("notebook", "pipeline_activity")


def _ident(name: str) -> str:
    return _NONWORD_RE.sub("_", (name or "").lower()).strip("_")


def _bronze_enabled(bp: dict) -> bool:
    return bool(bp.get("medallion", {}).get("bronze", {}).get("enabled", False))


def _gold_kinds(bp: dict) -> dict[str, str]:
    return {p["name"]: p.get("kind", "fact")
            for p in bp.get("medallion", {}).get("gold", {}).get("data_products", [])}


def _sources_for_domain(bp: dict, dident: str) -> list[dict]:
    """By the EXPLICIT ``domain`` on the ingestion entry (see provision_transforms for the full
    rationale): the previous `<slug>_` prefix match silently dropped sources that did not follow the
    naming convention, so their copy activities never made it into the pipeline."""
    ing = bp.get("ingestion", [])
    explicit = [e for e in ing if _ident(e.get("domain", "")) == dident]
    if explicit:
        return sorted(explicit, key=lambda e: e.get("source", ""))
    if any(e.get("domain") for e in ing):
        return []
    return sorted((e for e in ing                # legacy IR without `domain` → prefix fallback
                   if _ident(e.get("source", "")).startswith(dident + "_")),
                  key=lambda e: e.get("source", ""))


# Quellsystem-Text -> Fabric-Copy-Quelltyp. Die Namen sind die der Fabric-Pipeline-Aktivitaet;
# was hier NICHT drinsteht, bleibt bewusst ein Platzhalter mit VERIFY statt eines geratenen Typs.
# Ein falscher Quelltyp scheitert nicht beim Erzeugen, sondern erst beim Lauf.
_COPY_SOURCE_TYPES = (
    ("sap-cdc", "SapCdcSource"),          # zuerst der Konnektor: er ist die praezisere Aussage
    ("odata", "ODataSource"),
    ("hana", "SapHanaSource"),
    ("odbc", "OdbcSource"),
    ("rest", "RestSource"),
    ("http", "HttpSource"),
    ("api", "RestSource"),
    ("sftp", "FileSystemSource"),
    ("ftp", "FileSystemSource"),
    ("csv", "DelimitedTextSource"),
    ("excel", "ExcelSource"),
    ("kafka", "KafkaSource"),
    ("salesforce", "SalesforceSource"),
    ("servicenow", "ServiceNowSource"),
)


def _copy_source_type(e: dict) -> str:
    """Der Fabric-Quelltyp der Copy-Aktivitaet, aus Konnektor und Quellsystem gelesen.

    Bis 31.07.2026 stand hier fuer JEDE Copy-Quelle woertlich ``<SourceType>`` — ein Platzhalter,
    obwohl das IR den Konnektor und das Quellsystem bereits fuehrt. Die Pipeline liess sich damit
    erzeugen und nicht ausfuehren. Was sich nicht zuordnen laesst, bleibt weiterhin Platzhalter:
    ein GERATENER Typ waere schlimmer, weil er erst zur Laufzeit scheitert.
    """
    text = f"{e.get('connector', '')} {e.get('source_system', '')} {e.get('source', '')}".lower()
    for treffer, typ in _COPY_SOURCE_TYPES:
        if treffer in text:
            return typ
    return "<SourceType>"


def build_activity_graph(bp: dict) -> list[dict]:
    """Return the stack-agnostic activity list (name, kind, notebook/source, depends_on).

    ``kind`` is 'copy' (data-movement) or 'notebook' (a transform). ``depends_on`` lists
    activity names. Order: copy ingestion → bronze→silver (if materialised) → silver→gold.
    """
    bronze = _bronze_enabled(bp)
    kinds = _gold_kinds(bp)
    domains = sorted(bp.get("mesh", {}).get("domains", []), key=lambda d: d.get("name", ""))
    acts: list[dict] = []

    for d in domains:
        dident = _ident(d["name"])
        srcs = _sources_for_domain(bp, dident)
        # copy-mode sources become Copy activities; mirror/shortcut are passive (managed).
        copy_acts: list[str] = []
        for e in srcs:
            if e.get("access_mode") == "copy":
                nm = f"copy__{_ident(e['source'])}"
                acts.append({"name": nm, "kind": "copy", "source": e["source"], "depends_on": [],
                             "source_type": _copy_source_type(e),
                             "source_system": e.get("source_system", ""),
                             "connector": e.get("connector", ""),
                             "assumed": bool(e.get("access_mode_assumed"))})
                copy_acts.append(nm)
        # bronze→silver notebooks (only if bronze materialised); depend on copy of that source.
        silver_upstream: list[str] = list(copy_acts)
        if bronze:
            for e in srcs:
                nm = f"nb__bronze_to_silver__{_ident(e['source'])}"
                dep = [f"copy__{_ident(e['source'])}"] if e.get("access_mode") == "copy" else []
                acts.append({"name": nm, "kind": "notebook",
                             "notebook": f"nb_bronze_to_silver__{_ident(e['source'])}",
                             # Für diesen Schritt gibt es KEINEN Emitter — `provision_notebooks`
                             # schreibt nur Gold-Notebooks. Der DAG-Schritt ist trotzdem richtig
                             # (bronze→silver gehört in die Kette), aber das Item muss jemand
                             # selbst bauen. Das steht ab jetzt in der Aktivität, statt dass die
                             # Pipeline stillschweigend auf ein Item zeigt, das niemand liefert.
                             "not_emitted": True,
                             "depends_on": dep})
                silver_upstream.append(nm)
        # silver→gold notebooks; depend on this domain's bronze→silver (or copy ingestion).
        for product in sorted(d.get("data_products", [])):
            nm = f"nb__silver_to_gold__{_ident(product)}"
            acts.append({"name": nm, "kind": "notebook",
                         # Der Name kommt aus dem Emitter, der das Notebook wirklich schreibt.
                         # Hier selbst gebildet, lautete er `nb_silver_to_gold__<produkt>` und
                         # zeigte damit auf ein Item, das es nirgends gab.
                         "notebook": gold_notebook_name(product),
                         "kind_gold": kinds.get(product, "fact"),
                         "depends_on": sorted(silver_upstream)})

    # Abschluss: das Semantikmodell rahmen (framing), nachdem alle Gold-Tabellen geschrieben sind.
    modell = model_name_of(bp, fallback="")
    gold_schritte = sorted(a["name"] for a in acts if a["name"].startswith("nb__silver_to_gold__"))
    if modell and gold_schritte:
        acts.append({"name": "nb__framing", "kind": "framing", "notebook": FRAMING_NOTEBOOK,
                     "model": modell, "depends_on": gold_schritte})
    return sorted(acts, key=lambda a: a["name"])


def _framing_activity(a: dict, ws_token: str, depends: list[dict], refresh_path: str) -> dict:
    """Die Abschluss-Aktivität, die das Direct-Lake-Modell rahmt — in einem von zwei Wegen.

    **Warum es den Schritt überhaupt gibt.** Die Vorgabe „Direct Lake braucht keinen Refresh"
    stimmt für den Dauerbetrieb und nicht für die Auslieferung. Gemessen im Mandanten am
    13.08.2026: *„Ohne diesen Schritt antwortet das Modell nach jedem Gold-Lauf mit Fehlern statt
    Zahlen."* Die Doku nennt die Gründe (learn.microsoft.com/fabric/fundamentals/
    direct-lake-how-it-works, geprüft 14.08.2026):

    * Die automatische Aktualisierung ist ein **Modell-Schalter**, der standardmäßig an ist — sie
      trägt den Dauerbetrieb, aber nicht den ersten Lauf: *„After adding tables programmatically
      via TOM or TMSL, always refresh before querying."* Genau das tut jede Auslieferung.
    * Nach einem nicht behebbaren Fehler **setzt Power BI die automatische Aktualisierung aus**
      und nimmt sie erst nach einer erfolgreichen Auffrischung von Hand wieder auf.
    * Wer den Schalter absichtlich ausmacht, um erst nach dem DQ-Tor zu veröffentlichen — der von
      MS genannte ETL-Fall — hat gar keine automatische Rahmung mehr.
    * **Direct Lake on OneLake fährt ausschließlich `DirectLakeOnly`** und kennt keinen
      DirectQuery-Rückfall. Eine ungerahmte Tabelle liefert dort einen Fehler, keine langsame
      Antwort. Das erklärt „Fehler statt Zahlen" statt „veraltete Zahlen".

    **Weg B (`notebook`, Vorgabe)** — ein Notebook mit ``sempy.fabric.refresh_dataset``. Das ist
    der Weg, der im Mandanten **angenommen** wurde; er braucht kein Verbindungsobjekt und keine
    Mandanten-Einstellung.

    **Weg A (`pipeline_activity`, Opt-in)** — die dokumentierte Aktivität
    ``PBISemanticModelRefresh``. Sie bringt Warten-auf-Abschluss, Wiederholung und Zeitlimit als
    Pipeline-Eigenschaften mit, verlangt aber ``externalReferences`` auf eine Power-BI-Verbindung.
    Gemessen am 14.08.2026: die Übernahme der frei erfundenen Aktivität ``RefreshDataset`` scheitert
    mit ``BadRequest``; die Verbindung entsteht über OAuth oder über einen Dienstprinzipal, für den
    ein Mandanten-Administrator „Dienstprinzipale dürfen Fabric-APIs aufrufen" gesetzt haben muss.
    Deshalb ist dieser Weg ein Opt-in und nicht die Vorgabe: er ist der sauberere und **nicht** der
    auslieferbare. Der Handgriff steht in der ``description``, statt verschwiegen zu werden.
    """
    if refresh_path == "pipeline_activity":
        return {
            "name": a["name"], "type": "PBISemanticModelRefresh", "dependsOn": depends,
            "typeProperties": {"method": "post", "waitOnCompletion": True,
                               "operationType": "SemanticModelRefresh"},
            "externalReferences": {"connection": "<powerbi-connection-id>"},
            "description": (
                f"Rahmt das Semantikmodell '{a['model']}'. HANDGRIFF: `externalReferences."
                "connection` verlangt eine Power-BI-Verbindung — sie entsteht über OAuth im "
                "Browser oder über einen Dienstprinzipal, fuer den ein Mandanten-Administrator "
                "'Dienstprinzipale duerfen Fabric-APIs aufrufen' gesetzt hat. Ohne die Verbindung "
                "wird die Aktivität bei der Übernahme abgewiesen."),
        }
    return {
        "name": a["name"], "type": "TridentNotebook", "dependsOn": depends,
        "typeProperties": {"notebookId": f"<{a['notebook']}-id>", "workspaceId": ws_token},
        "description": (
            f"Rahmt das Semantikmodell '{a['model']}' nach dem Gold-Lauf (sempy.fabric."
            "refresh_dataset). Ohne diesen Schritt antwortet ein frisch ausgeliefertes "
            "Direct-Lake-Modell mit Fehlern statt Zahlen."),
    }


def _fabric_activity(a: dict, workspace: str = PLACEHOLDER_WORKSPACE,
                     refresh_path: str = "notebook") -> dict:
    """Map a graph node to a Fabric DataPipeline activity (schema-shaped).

    ``workspace`` qualifiziert die Workspace-GUID: ``<ws-order-to-cash-gold-workspace-id>`` statt
    des generischen ``<workspace-id>``. Der Unterschied ist praktisch: bei vier Workspaces im
    Mesh sagte der generische Platzhalter nicht, welcher gemeint ist — der Wert liess sich nicht
    ohne Nachdenken zuordnen, und genau das ist Handarbeit.
    """
    depends = [{"activity": dep, "dependencyConditions": ["Succeeded"]}
               for dep in a.get("depends_on", [])]
    if a["kind"] == "copy":
        typ = a.get("source_type") or "<SourceType>"
        return {
            "name": a["name"], "type": "Copy", "dependsOn": depends,
            # Der Quelltyp kommt aus Konnektor und Quellsystem des IR statt aus einem Platzhalter.
            # Verbindung und Datensatz bleiben eine Bereitstellungsentscheidung — sie haengen am
            # Mandanten und stehen nicht im Architekturplan.
            "typeProperties": {"source": {"type": typ}, "sink": {"type": "LakehouseTableSink"}},
            "description": (f"VERIFY: bind connection + dataset for '{a['source']}' "
                            f"({a.get('source_system') or 'source system unknown'})"
                            + (" — access mode was ASSUMED, confirm it is really a copy"
                               if a.get("assumed") else "")),
        }
    ws_token = ("<workspace-id>" if workspace == PLACEHOLDER_WORKSPACE
                else f"<{workspace}-workspace-id>")
    if a["kind"] == "framing":
        return _framing_activity(a, ws_token, depends, refresh_path)
    act = {
        "name": a["name"], "type": "TridentNotebook", "dependsOn": depends,
        # VERIFY: bind notebookId (the notebook wrapping this transform's SQL) + workspaceId.
        "typeProperties": {"notebookId": f"<{a['notebook']}-id>", "workspaceId": ws_token},
    }
    if a.get("not_emitted"):
        act["description"] = (f"ACHTUNG: '{a['notebook']}' wird von diesem Lauf NICHT emittiert — "
                              "es gibt keinen bronze→silver-Notebook-Emitter. Der Schritt gehört in "
                              "die Kette, das Item muss aber selbst gebaut werden, bevor die "
                              "Pipeline laufen kann.")
    return act


def emit_pipeline_definition(bp: dict, pipeline_name: str = "medallion_orchestration",
                             workspace: str = PLACEHOLDER_WORKSPACE,
                             refresh_path: str = "notebook") -> str:
    """Return ``pipeline-content.json`` — a real Fabric DataPipeline definition (deterministic)."""
    if refresh_path not in REFRESH_PATHS:
        raise ValueError(f"refresh_path must be one of {REFRESH_PATHS}, got {refresh_path!r}")
    ws = workspace_of(bp, workspace)
    activities = [_fabric_activity(a, ws, refresh_path) for a in build_activity_graph(bp)]
    content = {"properties": {"description": f"Medallion orchestration ({pipeline_name}) — "
                                             "ingestion → silver → gold (ADR-0015).",
                              "activities": activities}}
    return json.dumps(content, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def emit_orchestration_deploy(bp: dict, workspace: str = PLACEHOLDER_WORKSPACE,
                              pipeline_name: str = "medallion_orchestration") -> str:
    """Return a bash script importing the pipeline + registering its schedule (idempotent).

    Kennt der Aufrufer keinen Workspace-Namen, wird er **aus dem Blueprint gelesen**, nicht als
    ``<workspace>`` durchgereicht. Gemessen am 31.07.2026: derselbe Lauf legte in `provision.sh`
    `ws-order-to-cash-gold` an und schrieb hier `<workspace>` — zwei Skripte aus einem Lauf, die
    sich widersprachen, und dazwischen jemand, der das von Hand abgleicht.
    """
    workspace = workspace_of(bp, workspace)
    item = f"{workspace}.Workspace/{pipeline_name}.DataPipeline"
    return "\n".join([
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        "# ArchitectureBlueprint → Fabric orchestration (ADR-0015). Generated; review before running.",
        "# Chains ingestion → silver → gold as one scheduled DataPipeline.",
        "# Grounded in the Fabric DataPipeline definition + item/schedule REST surface.",
        "# Prereq: authenticated fab CLI; the transform notebooks must exist (bind their IDs in",
        "#   pipeline-content.json first — see the <…-id> placeholders / _ORCHESTRATION.md).",
        "",
        "# 1. Import the pipeline definition (idempotent: import overwrites in place).",
        f'fab ls "{item}" >/dev/null 2>&1 || echo "creating {pipeline_name}"',
        f'fab import "{item}" -i ./pipeline-content.json -f   # VERIFY: fab import expects the item folder',
        "",
        "# 2. Register the schedule. `jobType` is a required path segment; for a DataPipeline",
        "#    it is `Pipeline` (MS Learn, core/job-scheduler/create-item-schedule, 20.08.2026).",
        f'#   fab api "workspaces/{workspace}.Workspace/items/<{pipeline_name}-id>'
        f'/jobs/{JOB_TYPE_PIPELINE}/schedules" \\',
        "#       -X POST -i ./schedule.json",
        "",
        'echo "Orchestration deploy complete."',
    ]) + "\n"


def emit_orchestration(bp: dict, stack: str = "fabric", workspace: str = PLACEHOLDER_WORKSPACE,
                       pipeline_name: str = "medallion_orchestration",
                       frequency: str = "Daily",
                       refresh_path: str = "notebook") -> dict[str, str]:
    """Return the orchestration artifact set (path → content), like ``emit_grounding``.

    ``_ORCHESTRATION.md`` (stack-agnostic DAG) is always emitted; the Fabric
    ``pipeline-content.json`` / ``schedule.json`` / ``deploy.sh`` are emitted for fabric.

    ``refresh_path`` wählt, wie das Semantikmodell gerahmt wird — ``notebook`` (Vorgabe, der im
    Mandanten angenommene Weg) oder ``pipeline_activity`` (Opt-in, dokumentiert und sauberer,
    braucht aber eine Power-BI-Verbindung). Siehe ``_framing_activity``.
    """
    graph = build_activity_graph(bp)
    doc = ["# Orchestration DAG (generated — ADR-0015)", "",
           f"Stack: **{stack}**  ·  Schedule: **{frequency}**  ·  Activities: **{len(graph)}**",
           "",
           "Chains ingestion → silver → gold in medallion order. Copy-mode sources run first; "
           "mirror/shortcut sources are passive (managed, no activity).", "",
           "| Activity | Type | Depends on |", "|---|---|---|"]
    _typ = {"copy": "Copy",
            "framing": "PBISemanticModelRefresh" if refresh_path == "pipeline_activity"
            else "Notebook (framing)"}
    for a in graph:
        typ = _typ.get(a["kind"]) or f"Notebook ({a.get('kind_gold', 'transform')})"
        deps = ", ".join(a.get("depends_on", [])) or "—"
        doc.append(f"| `{a['name']}` | {typ} | {deps} |")
    doc.append("")
    if any(a["kind"] == "framing" for a in graph):
        doc += [
            "## Abschluss: Rahmung des Semantikmodells", "",
            "Die Kette endet mit einem Rahmungsschritt (framing). Er steht hier, weil „Direct Lake "
            "braucht keinen Refresh“ für den Dauerbetrieb gilt und nicht für die Auslieferung: ein "
            "Modell, dessen Tabellen programmatisch angelegt wurden, muss laut MS vor der ersten "
            "Abfrage gerahmt werden, und Direct Lake on OneLake antwortet ungerahmt mit einem "
            "Fehler statt mit einer langsamen Abfrage.", "",
            f"Gewählter Weg: **{refresh_path}**.", "",
            "| Weg | Bringt mit | Handgriff |", "|---|---|---|",
            "| `notebook` (Vorgabe) | kein Verbindungsobjekt, keine Mandanten-Einstellung | "
            "Wiederholung/Zeitlimit stehen im Notebook, nicht in der Pipeline |",
            "| `pipeline_activity` (Opt-in) | Warten-auf-Abschluss, Wiederholung, Zeitlimit als "
            "Pipeline-Eigenschaften | `externalReferences.connection` auf eine Power-BI-Verbindung "
            "— OAuth im Browser oder Dienstprinzipal mit Mandanten-Einstellung |", "",
        ]

    out = {"orchestration/_ORCHESTRATION.md": "\n".join(doc) + "\n"}
    if stack == "fabric":
        out["orchestration/pipeline-content.json"] = emit_pipeline_definition(bp, pipeline_name,
                                                                              workspace,
                                                                              refresh_path)
        out["orchestration/schedule.json"] = emit_schedule(frequency)
        out["orchestration/deploy.sh"] = emit_orchestration_deploy(bp, workspace, pipeline_name)
    return out
