"""provision_ingestion — emit Fabric **Copy job** items for physically copied sources.

Schliesst die letzte Luecke der Ingestions-Schicht. `shortcut` und `mirror` erzeugten in
`provision_fabric` seit jeher echte `fab`-Befehle; `access_mode: copy` erzeugte **einen
Prosasatz**::

    # <src> (<system>): Copy — ingest via pipeline/dataflow (physical copy)

Eine Lieferung konnte damit "vollstaendig" heissen, waehrend jede physisch kopierte Quelle
als Satz ankam. Genau die Sorte Luecke, die von aussen wie Abdeckung aussieht.

Official-First (D-156): der Copy job ist ein **erstklassiges Fabric-Item**, also emittiert
dieser Modul seine dokumentierten Definition-Parts statt eine handgeschriebene Pipeline
drumherum zu bauen::

    <cj_name>.CopyJob/copyjob-content.json   (required)
    <cj_name>.CopyJob/.platform              (optional, v2 platform file)

Schema + Beispiele (geprueft 01.08.2026):
https://learn.microsoft.com/rest/api/fabric/articles/item-management/definitions/copyjob-definition

**Kein eigener Watermark-Zustand.** Der Copy job verwaltet Inkrement-Stand, Resume und
per-Tabellen-Reset selbst. Eine private Steuerungstabelle daneben waere ein Nachbau einer
Plattform-Faehigkeit — deshalb wird keine emittiert.

**Faehigkeiten kommen aus der Matrix, nicht aus dem Namen.** `jobMode` und ob ueberhaupt
ein Item entsteht, entscheidet `_CAPABILITIES` — abgeschrieben aus „Connectors for Copy
Job". Das ist keine Formalie: der Emitter setzte anfangs `jobMode: "CDC"`, weil der
IR-Konnektor `sap-cdc` heisst. In der CDC-Tabelle steht aber kein einziger SAP-Konnektor,
und SAP ODP kommt in der Quellen-Tabelle gar nicht vor — der erzeugte Copy job war
syntaktisch gueltig und praktisch nicht ausfuehrbar.

**Honest by construction.** Verbindungs-, Workspace- und Lakehouse-GUIDs sind Tenant-Fakten,
keine Blueprint-Fakten. Sie kommen aus der `--connections`-Map, wenn eine da ist; ohne sie
schreibt der Emitter einen Marker, der beim Deployment **laut scheitert**, statt einer
wohlgeformten Null-GUID, die still auf etwas Falsches zeigt. Tabellen-Activities kommen aus
dem introspizierten Quellschema; fehlt es, bleibt die Activity-Liste leer — das ist die
dokumentierte Minimaldefinition (ContentDetails Example 1) — und `INGESTION.md` benennt
namentlich, welche Quelle unbefuellt blieb.

Typ-Paare tragen ihre Herkunft: `verified` (woertlich in einem Copy-job-Beispiel),
`derived` (beide Strings in der Konnektor-Referenz, zusammengesetzt ueber ein in 3 von 3
Beispielen geltendes Muster), `partial` (nur einer dokumentiert — der andere bleibt ein
VERIFY-Marker). Was gar keinen Eintrag hat, bekommt zwei Marker statt eines plausibel
klingenden Namens. `INGESTION.md` weist die Herkunft je Quelle aus, damit niemand eine
Ableitung fuer eine Messung haelt.

Dieses Modul fuehrt nichts aus — es emittiert nur Text.
"""
from __future__ import annotations

import json
import re
import uuid
from typing import Any

from core.dataarch_engine.blueprint.naming import DEFAULT as _NAMING

_NONWORD_RE = re.compile(r"[^a-z0-9]+")

# Der Marker fuer eine unbekannte Tenant-GUID. Bewusst KEINE Null-GUID
# ("00000000-0000-0000-0000-000000000000"): die ist wohlgeformt, kommt durch jede
# Schema-Pruefung und zeigt im Tenant auf nichts — der Fehler faellt dann erst beim
# Lauf auf, ohne Hinweis auf die Ursache. Dieser Marker ist als GUID ungueltig und
# scheitert deshalb sofort und benennbar.
UNRESOLVED = "TODO-CONNECTION-ID"

_LAKEHOUSE = {"type": "LakehouseTable", "connection_type": "Lakehouse"}
_UNVERIFIED = "VERIFY-CONNECTOR-TYPE"

# --- Was der Copy job je Konnektor KANN -------------------------------------------
# Quelle: „Connectors for Copy Job" (learn.microsoft.com/fabric/data-factory/
# copy-job-connectors), geprueft 01.08.2026. Zwei getrennte Tabellen dort, und der
# Unterschied ist genau der, an dem dieser Emitter sich zuerst geirrt hat:
#
#   * „Copy job sources and destinations" -> Full load / Incremental load (WATERMARK)
#   * „CDC Replication (Preview)"         -> jobMode CDC
#
# In der CDC-Tabelle steht **kein einziger SAP-Konnektor**. `jobMode: "CDC"` fuer eine
# SAP-Quelle erzeugt also einen Copy job, den die Plattform nicht ausfuehren kann —
# der Emitter tat das bis zu dieser Messung, weil `connector: sap-cdc` nach CDC klingt.
# Der Name einer Deklaration ist keine Faehigkeitszusage.
#
# `copy_job_source=False` heisst: die Quelle taucht in der Quellen-Tabelle GAR NICHT auf.
# Dafuer wird kein Item emittiert — ein syntaktisch gueltiger Copy job fuer einen
# nicht unterstuetzten Konnektor ist schlimmer als keiner, weil er Machbarkeit behauptet.
_CAPABILITIES: dict[str, dict[str, object]] = {
    # Kein Konnektor des IR-VOKABULARS ist CDC-faehig — die CDC-Tabelle fuehrt nur
    # SQL-Familie, Oracle, Snowflake, BigQuery, Fabric-Lakehouse und SAP Datasphere
    # Outbound. Erreichbar wird CDC deshalb nur ueber ein `source_type` in der
    # Connections-Map, die den konkreten Store benennt (z. B. `azure-sql`). Das ist
    # kein Schoenheitsfehler, sondern eine Aussage ueber das IR: es kann heute keine
    # CDC-faehige Quelle deklarieren.
    "azure-sql":   {"copy_job_source": True,  "incremental": True,  "cdc": True,
                    "doc": "Azure SQL DB"},
    "hana":        {"copy_job_source": True,  "incremental": True,  "cdc": False,
                    "doc": "SAP HANA"},
    "odata":       {"copy_job_source": True,  "incremental": False, "cdc": False,
                    "doc": "ODATA"},
    "odbc-live":   {"copy_job_source": True,  "incremental": True,  "cdc": False,
                    "doc": "ODBC"},
    "odbc-copy":   {"copy_job_source": True,  "incremental": True,  "cdc": False,
                    "doc": "ODBC"},
    # SAP ODP/CDC steht in KEINER der beiden Tabellen — weder als Quelle noch als
    # CDC-Quelle. Der Weg dorthin ist eine Pipeline mit dem SAP-CDC-Konnektor oder
    # SAP Datasphere Outbound, nicht der Copy job.
    "sap-cdc":     {"copy_job_source": False, "incremental": False, "cdc": False,
                    "doc": "SAP CDC (ODP)"},
    "bdc-connect": {"copy_job_source": False, "incremental": False, "cdc": False,
                    "doc": "BDC Connect"},
}

# --- Typ-Paare: aeusseres `type` = Dataset-Typ, `connectionSettings.type` = Linked-Service-Typ
# Das Muster haelt in 3 von 3 dokumentierten Copy-job-Beispielen (AzureSqlTable/
# AzureSqlDatabase, LakehouseTable/Lakehouse, DelimitedText/AzureBlobStorage) und ist
# damit belegt, nicht vermutet. Die Einzelstrings kommen aus den Konnektor-Referenzen.
#
# `verified` = woertlich in einem Copy-job-Beispiel gesehen.
# `derived`  = beide Strings in der ADF-Konnektor-Referenz dokumentiert, ueber das
#              obige Muster zusammengesetzt. Ein falscher Dataset-Typ scheitert beim
#              Import laut und sofort — vertretbar, solange die Herkunft dransteht.
# `partial`  = nur einer der beiden Strings dokumentiert; der andere bleibt VERIFY.
VERIFIED, DERIVED, PARTIAL = "verified", "derived", "partial"
_CONNECTOR_TYPES: dict[str, dict[str, str]] = {
    "azure-sql":  {"type": "AzureSqlTable", "connection_type": "AzureSqlDatabase",
                   "provenance": VERIFIED, "quelle": "Copy-job-Definition, Example 3"},
    "odata":      {"type": "ODataResource", "connection_type": "OData",
                   "provenance": DERIVED, "quelle": "ADF connector-odata"},
    "odbc-live":  {"type": "OdbcTable", "connection_type": "Odbc",
                   "provenance": DERIVED, "quelle": "ADF connector-odbc"},
    "odbc-copy":  {"type": "OdbcTable", "connection_type": "Odbc",
                   "provenance": DERIVED, "quelle": "ADF connector-odbc"},
    # Dataset-Typ dokumentiert (ADF connector-sap-hana), Linked-Service-Typ nicht
    # woertlich gefunden — deshalb halb, nicht ganz.
    "hana":       {"type": "SapHanaTable", "connection_type": _UNVERIFIED,
                   "provenance": PARTIAL, "quelle": "ADF connector-sap-hana"},
}


def _slug(name: str) -> str:
    """'Sales ERP' -> 'sales_erp' — Item-Namen sind SQL-/Pfad-sicher."""
    return _NONWORD_RE.sub("_", (name or "").lower()).strip("_")


def copy_job_name(source: str) -> str:
    """Item-Name eines Copy jobs: `cj_<quelle>` — ueber die Hauskonvention, nicht per
    eigener Praefix-Tabelle (die Konvention ist an EINER Stelle konfigurierbar)."""
    return _NAMING.copy_job(_slug(source))


def _activity_id(source: str, table: str) -> str:
    """Stabile Activity-GUID aus (Quelle, Tabelle).

    Deterministisch per uuid5 statt uuid4: ein Emitter, der bei jedem Lauf neue IDs
    wuerfelt, erzeugt bei jedem Deployment einen Diff und macht 'hat sich etwas
    geaendert?' unbeantwortbar.
    """
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"copyjob://{_slug(source)}/{table}"))


def _copy_entries(bp: dict[str, Any]) -> list[dict[str, Any]]:
    """Die Ingestions-Eintraege, die wirklich physisch kopieren.

    `shortcut`, `shortcut_transform` und `mirror` sind in provision_fabric abgedeckt —
    hier nichts doppelt emittieren (Tool-Reuse-Pflicht).
    """
    return [e for e in (bp.get("ingestion") or []) if e.get("access_mode") == "copy"]


def _job_mode(entry: dict[str, Any], cfg: dict[str, Any] | None = None) -> str:
    """`CDC` nur, wenn der Konnektor in der CDC-Replikations-Tabelle steht — sonst `Batch`.

    Frueher stand hier `"CDC" if connector == "sap-cdc"`. Das war aus dem NAMEN der
    Deklaration abgeleitet und gegen die Faehigkeitsmatrix falsch: die CDC-Tabelle des
    Copy job fuehrt keinen einzigen SAP-Konnektor. Der so erzeugte Copy job war
    syntaktisch gueltig und praktisch nicht ausfuehrbar.

    `Batch` ist auch die richtige Wahl fuer die watermark-basierte Inkrement-Ladung —
    die laeuft im Copy job nicht ueber `jobMode`, sondern ueber die Inkrement-Spalte.
    """
    caps = _caps_for(entry, cfg or {})
    return "CDC" if caps and caps.get("cdc") else "Batch"


def _caps_for(entry: dict[str, Any], cfg: dict[str, Any]) -> dict[str, object] | None:
    """Faehigkeiten zum Konnektor; ein `source_type` der Connections-Map schlaegt das IR."""
    return (_CAPABILITIES.get(str(cfg.get("source_type") or ""))
            or _CAPABILITIES.get(str(entry.get("connector") or "")))


def _unsupported(entry: dict[str, Any], cfg: dict[str, Any] | None = None) -> bool:
    """Wahr, wenn der Konnektor in der Copy-job-Quellen-Tabelle gar nicht vorkommt."""
    caps = _caps_for(entry, cfg or {})
    return caps is not None and not caps.get("copy_job_source")


def _types_for(entry: dict[str, Any], cfg: dict[str, Any]) -> dict[str, str] | None:
    """Typ-Paar zum Konnektor. Ein `source_type` in der Connections-Map schlaegt das IR —
    wer den Tenant kennt, weiss es besser als eine abgeleitete Tabelle."""
    return (_CONNECTOR_TYPES.get(str(cfg.get("source_type") or ""))
            or _CONNECTOR_TYPES.get(str(entry.get("connector") or "")))


def _connection_settings(entry: dict[str, Any], cfg: dict[str, Any] | None) -> dict[str, Any]:
    """Quell-Verbindung: belegtes oder abgeleitetes Typ-Paar, sonst VERIFY-Marker."""
    cfg = cfg or {}
    known = _types_for(entry, cfg)
    settings: dict[str, Any] = {
        "type": known["connection_type"] if known else _UNVERIFIED,
    }
    if cfg.get("database"):
        settings["typeProperties"] = {"database": cfg["database"]}
    settings["externalReferences"] = {"connection": cfg.get("connectionId") or UNRESOLVED}
    return {"type": known["type"] if known else _UNVERIFIED, "connectionSettings": settings}


def _destination(cfg: dict[str, Any] | None) -> dict[str, Any]:
    """Ziel ist immer die Bronze-Landezone: eine Lakehouse-Tabelle (belegtes Typ-Paar)."""
    cfg = cfg or {}
    return {
        "type": _LAKEHOUSE["type"],
        "connectionSettings": {
            "type": _LAKEHOUSE["connection_type"],
            "typeProperties": {
                "workspaceId": cfg.get("workspaceId") or UNRESOLVED,
                "artifactId": cfg.get("lakehouseId") or UNRESOLVED,
                "rootFolder": "Tables",
            },
        },
    }


def _activity(source: str, table: dict[str, Any], job_mode: str,
              schemas: bool) -> dict[str, Any]:
    """Eine Tabelle -> eine Copy-job-Activity, Batch oder CDC.

    Die CDC-Form folgt ContentDetails Example 3: `changeDataSettings.readMethod`
    `SnapshotPlusIncremental` (Vollzug + laufende Aenderungen) und ein Upsert auf
    Schluesselspalten. Ohne Schluesselvorschlag faellt die Tabelle auf `Append` zurueck —
    ein Upsert ohne `keys` ist kein konservativer, sondern ein kaputter Zustand.
    """
    from core.dataarch_engine.blueprint.source_schema import key_candidates

    name = str(table.get("name") or "")
    src_dataset: dict[str, Any] = {"table": name}
    if schemas and table.get("schema"):
        src_dataset["schema"] = table["schema"]
    # Bronze landet 1:1 unter dem Quelltabellennamen — die Umbenennung passiert in
    # bronze->silver (provision_transforms), nicht schon beim Kopieren.
    dst_dataset: dict[str, Any] = {"table": name}

    props: dict[str, Any] = {
        "source": {"datasetSettings": src_dataset},
        "destination": {"datasetSettings": dst_dataset},
        "translator": {"type": "TabularTranslator"},
        "typeConversionSettings": {
            "typeConversion": {"allowDataTruncation": True, "treatBooleanAsNumber": False},
        },
    }

    keys = key_candidates(table)[:1] if job_mode == "CDC" else []
    if job_mode == "CDC" and keys:
        props["source"]["changeDataSettings"] = {"readMethod": "SnapshotPlusIncremental"}
        props["source"]["partitionSettings"] = {"partitionOption": "None"}
        props["destination"]["writeBehavior"] = "Upsert"
        props["destination"]["upsertSettings"] = {"useTempDB": True, "keys": keys}
        props["destination"]["tableOption"] = "autoCreate"
        props["enableStaging"] = False
    else:
        props["destination"]["writeBehavior"] = "Append"

    return {"id": _activity_id(source, name), "properties": props}


def _platform(display_name: str) -> str:
    """v2 platform file — gleiche Form wie bei den Notebook-Items (provision_notebooks)."""
    return json.dumps({
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/"
                   "platformProperties/2.0.0/schema.json",
        "metadata": {"type": "CopyJob", "displayName": display_name},
        "config": {"version": "2.0", "logicalId": "00000000-0000-0000-0000-000000000000"},
    }, indent=2) + "\n"


def _tables_for(source: str, source_schema: dict[str, list[dict]] | None) -> list[dict]:
    """Introspizierte Tabellen einer Quelle, stabil sortiert (kein Dateisystem-Zufall)."""
    if not source_schema:
        return []
    return sorted(source_schema.get(source) or [], key=lambda t: str(t.get("name") or ""))


def emit_ingestion(bp: dict[str, Any], stack: str = "fabric", schemas: bool = False,
                   connections: dict[str, dict] | None = None,
                   source_schema: dict[str, list[dict]] | None = None) -> dict[str, str]:
    """Return the Copy job item set as ``path -> content`` (relativ zu ``ingestion/``).

    Nur ``stack='fabric'``: der Copy job ist ein Fabric-Item. Databricks und Snowflake
    kopieren ueber ihre eigenen Mechanismen und bekommen hier bewusst nichts — ein leeres
    Ergebnis ist ehrlicher als ein Fabric-Artefakt in einem Snowflake-Rendering.
    """
    if stack != "fabric":
        return {}
    entries = _copy_entries(bp)
    if not entries:
        return {}

    connections = connections or {}
    out: dict[str, str] = {}
    rows: list[str] = []
    unresolved: list[str] = []
    unfilled: list[str] = []
    unsupported: list[tuple[str, str]] = []
    abgeleitet: list[tuple[str, str, str]] = []

    for entry in sorted(entries, key=lambda e: str(e.get("source") or "")):
        src = str(entry["source"])
        cfg = connections.get(src) or {}
        job = copy_job_name(src)
        mode = _job_mode(entry, cfg)
        tables = _tables_for(src, source_schema)

        # Konnektor, den der Copy job gar nicht kennt -> kein Item. Ein gueltiges
        # JSON dafuer zu schreiben hiesse, Machbarkeit zu behaupten, die es nicht gibt.
        if _unsupported(entry, cfg):
            unsupported.append((src, str((_caps_for(entry, cfg) or {}).get("doc", ""))))
            continue

        typen = _types_for(entry, cfg)
        if typen and typen["provenance"] != VERIFIED:
            abgeleitet.append((src, typen["provenance"], typen["quelle"]))

        content: dict[str, Any] = {
            "properties": {
                "jobMode": mode,
                "source": _connection_settings(entry, cfg),
                "destination": _destination(cfg),
                "policy": {"timeout": "0.12:00:00", "retry": 0},
            },
            "activities": [_activity(src, t, mode, schemas) for t in tables],
        }
        out[f"{job}.CopyJob/copyjob-content.json"] = json.dumps(content, indent=2) + "\n"
        out[f"{job}.CopyJob/.platform"] = _platform(job)

        if not cfg.get("connectionId"):
            unresolved.append(src)
        if not tables:
            unfilled.append(src)
        rows.append(f"| `{src}` | `{entry.get('source_system', '')}` | {mode} | "
                    f"{len(tables)} | `{job}.CopyJob` |")

    out["INGESTION.md"] = _readme(rows, unresolved, unfilled, unsupported, abgeleitet)
    return out


def _readme(rows: list[str], unresolved: list[str], unfilled: list[str],
            unsupported: list[tuple[str, str]],
            abgeleitet: list[tuple[str, str, str]]) -> str:
    """Was der Emitter wissen konnte — und was der Tenant beisteuern muss."""
    lines = [
        "# Ingestion — Copy jobs",
        "",
        "Erzeugt aus `ingestion[]` des Blueprints: jede Quelle mit `access_mode: copy` wird",
        "ein Fabric **Copy job**-Item. Quellen mit `shortcut`, `shortcut_transform` oder",
        "`mirror` stehen nicht hier — die deckt das Provisioning-Skript ab.",
        "",
        "Der Copy job verwaltet den Inkrement-Zustand (Watermark/CDC, Resume, per-Tabellen-",
        "Reset) selbst. Es gibt bewusst **keine** eigene Steuerungstabelle daneben.",
        "",
        "| Quelle | System | jobMode | Tabellen | Item |",
        "|---|---|---|---|---|",
        *rows,
        "",
        "## Import",
        "",
        "```bash",
        'fab import "<workspace>.Workspace/<name>.CopyJob" -i ./<name>.CopyJob -f',
        "```",
        "",
    ]
    if unsupported:
        lines += [
            "## STOPP: kein Copy-job-Konnektor",
            "",
            "Fuer diese Quellen wurde **kein Item** erzeugt. Sie stehen in der",
            "Copy-job-Konnektorentabelle nicht — ein Copy job kann sie nicht lesen,",
            "egal wie das JSON aussieht:",
            "",
            *[f"- `{s}` ({doc})" for s, doc in unsupported],
            "",
            "Weg dorthin ist eine Data-Factory-**Pipeline** mit dem passenden Konnektor",
            "(bei SAP ODP/CDC: SAP-CDC-Konnektor oder SAP Datasphere Outbound), nicht",
            "der Copy job. Beleg: learn.microsoft.com/fabric/data-factory/copy-job-connectors",
            "",
        ]
    if abgeleitet:
        lines += [
            "## Typ-Paare mit Herkunft",
            "",
            "Diese `type`/`connectionSettings.type`-Werte stammen **nicht** aus einem",
            "Copy-job-Beispiel, sondern aus der Konnektor-Referenz, zusammengesetzt ueber",
            "das in 3 von 3 dokumentierten Beispielen geltende Muster (aeusseres `type` =",
            "Dataset-Typ, `connectionSettings.type` = Linked-Service-Typ). Ein falscher",
            "Wert scheitert beim Import sofort und sichtbar — aber er ist eine Ableitung:",
            "",
            "| Quelle | Herkunft | Beleg |",
            "|---|---|---|",
            *[f"| `{s}` | {p} | {q} |" for s, p, q in abgeleitet],
            "",
            "Bestaetigen laesst sich das in einem Zug: Copy job im Portal gegen die Quelle",
            "anlegen, **View -> View JSON code**, die echten Strings gegen",
            "`_CONNECTOR_TYPES` halten. `partial` heisst: einer der beiden Strings ist noch",
            f"`{_UNVERIFIED}` und MUSS vor dem Import ersetzt werden.",
            "",
        ]
    if unresolved:
        lines += [
            "## VERIFY: offene Verbindungs-IDs",
            "",
            f"Fuer diese Quellen lag keine Verbindung vor — im JSON steht `{UNRESOLVED}`,",
            "was beim Import **absichtlich scheitert** statt still ins Leere zu zeigen:",
            "",
            *[f"- `{s}`" for s in unresolved],
            "",
            "Verbindung anlegen (`POST /v1/connections`), die zurueckgegebene `id` eintragen",
            "oder als `--connections` mitgeben.",
            "",
        ]
    if unfilled:
        lines += [
            "## VERIFY: leere Activity-Liste",
            "",
            "Ohne introspiziertes Quellschema kennt der Emitter die Tabellen nicht. Diese",
            "Copy jobs sind gueltig, kopieren aber noch nichts:",
            "",
            *[f"- `{s}`" for s in unfilled],
            "",
            "Quellschema erheben (`--emit-source-schema`) und erneut rendern.",
            "",
        ]
    return "\n".join(lines)
