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
IR-Konnektor `sap-cdc` heisst. SAP ODP kommt aber in keiner der beiden Tabellen vor,
weder als Quelle noch als CDC-Quelle — der erzeugte Copy job war syntaktisch gueltig und
praktisch nicht ausfuehrbar.

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
# Kein Konnektor des IR-VOKABULARS steht in der CDC-Tabelle. `jobMode: "CDC"` fuer eine
# SAP-Quelle erzeugt also einen Copy job, den die Plattform nicht ausfuehren kann —
# der Emitter tat das bis zu dieser Messung, weil `connector: sap-cdc` nach CDC klingt.
# Der Name einer Deklaration ist keine Faehigkeitszusage.
#
# KORREKTUR 09.09.2026, benannt statt geglaettet (Belegpflicht R5): hier stand „in der
# CDC-Tabelle steht kein einziger SAP-Konnektor". Das war zu breit — und der Kommentar im
# Kopf von `_CAPABILITIES`, zehn Zeilen tiefer, sagte es die ganze Zeit richtig („… und
# SAP Datasphere Outbound"). Zwei Saetze ueber dieselbe Tabelle in derselben Datei, einer
# davon falsch. Gemessen am 09.09.2026 fuehrt die CDC-Tabelle drei SAP-Zeilen, alle als
# CDC-QUELLE und keine als Ziel: `SAP Datasphere Outbound for ADLS Gen2`, `… for AWS S3`,
# `… for Google CloudStorage`. Die Aussage, auf die sich dieser Code stuetzt, ist die
# engere: keiner der Konnektoren, die unser IR deklarieren kann, steht dort.
#
# `copy_job_source=False` heisst: die Quelle taucht in der Quellen-Tabelle GAR NICHT auf.
# Dafuer wird kein Item emittiert — ein syntaktisch gueltiger Copy job fuer einen
# nicht unterstuetzten Konnektor ist schlimmer als keiner, weil er Machbarkeit behauptet.
_CAPABILITIES: dict[str, dict[str, object]] = {
    # Kein Konnektor des IR-VOKABULARS ist CDC-faehig — die CDC-Tabelle fuehrt nur
    # SQL-Familie, Oracle, Snowflake, BigQuery, Fabric-Lakehouse und SAP Datasphere
    # Outbound (dieses in drei Speicher-Varianten: ADLS Gen2, AWS S3, Google Cloud
    # Storage, alle als Quelle, keine als Ziel). Erreichbar wird CDC deshalb nur ueber
    # ein `source_type` in der Connections-Map, die den konkreten Store benennt
    # (z. B. `azure-sql`). Das ist kein Schoenheitsfehler, sondern eine Aussage ueber
    # das IR: es kann heute keine CDC-faehige Quelle deklarieren.
    #
    # Was die Quellen-Tabelle am 09.09.2026 an SAP fuehrt und wir NICHT abbilden:
    # `SAP BW Open Hub` (Full load) und neu `SAP Table (ABAP Add-On)` (Full UND
    # Incremental per Watermark) — ein Fabric-nativer Copy job direkt an SAP, ohne
    # Datasphere. Das Handover-Enum kennt beide nicht; ob es sie bekommen soll, ist
    # eine offene Entscheidung und steht als `fabric-copy-job-sap-abap-addon` im
    # feature_watch von `research/upstream_pins.yaml`. Hier nichts zu raten ist
    # Absicht: ein Konnektorname, den das IR nicht deklarieren kann, waere ein
    # Eintrag ohne Aufrufer.
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

    `shortcut`, `shortcut_transform` und `mirror` sind in provision_fabric abgedeckt,
    `file_mlv` in :func:`emit_datei_mlv` — hier nichts doppelt emittieren (Tool-Reuse-Pflicht).
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
    datei = emit_datei_mlv(bp, schemas=schemas, connections=connections)
    entries = _copy_entries(bp)
    if not entries:
        return datei

    connections = connections or {}
    out: dict[str, str] = {}
    rows: list[str] = []
    unresolved: list[str] = []
    unfilled: list[str] = []
    unsupported: list[tuple[str, str]] = []
    abgeleitet: list[tuple[str, str, str]] = []
    typ_offen: list[tuple[str, str, list[str]]] = []

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
        # R9 (30.09.2026): jede Quelle, deren JSON den Konnektor-Marker traegt, steht mit Feld
        # in INGESTION.md — vorher stand der Marker nur im JSON (gemessen 29.09.2026: 23 bzw. 1
        # Copy jobs mit Marker, 0 Nennungen in INGESTION.md).
        quelle_json = content["properties"]["source"]
        felder = [f for f, w in (("type", quelle_json["type"]),
                                 ("connectionSettings.type", quelle_json["connectionSettings"]["type"]))
                  if w == _UNVERIFIED]
        if felder:
            typ_offen.append((src, f"{job}.CopyJob", felder))
        out[f"{job}.CopyJob/copyjob-content.json"] = json.dumps(content, indent=2) + "\n"
        out[f"{job}.CopyJob/.platform"] = _platform(job)

        if not cfg.get("connectionId"):
            unresolved.append(src)
        if not tables:
            unfilled.append(src)
        rows.append(f"| `{src}` | `{entry.get('source_system', '')}` | {mode} | "
                    f"{len(tables)} | `{job}.CopyJob` |")

    out["INGESTION.md"] = _readme(rows, unresolved, unfilled, unsupported, abgeleitet, typ_offen)
    out.update(datei)
    return out


# --- Datei-MLV: Dateien aus `Files/` als Bronze-Tabelle (I-21 W5.22, D-619) -----------
#
# Quelle: MS Learn *Spark SQL reference for materialized lake views*, Abschnitt „Ingest files
# with `USING OneLake_Files`", gelesen 01.10.2026. Opt-in je Quelle (`access_mode: file_mlv`),
# Entscheidung Florian 01.10.2026: der Copy job bleibt die Vorgabe.

#: Vor der Pipeline (`fabric_schedule.emit_schedule`: 02:00 UTC), damit Silber frische Bronze
#: liest. Zeitversatz ist eine Annahme, keine Kopplung — steht im Dokument.
DATEI_MLV_REFRESH_UHRZEIT = "01:00"
DATEI_MLV_DOC = "learn.microsoft.com/fabric/data-engineering/materialized-lake-views/create-materialized-lake-view"


def _datei_mlv_entries(bp: dict[str, Any]) -> list[dict[str, Any]]:
    return sorted((e for e in (bp.get("ingestion") or []) if e.get("access_mode") == "file_mlv"),
                  key=lambda e: str(e.get("source") or ""))


def datei_mlv_sql(entry: dict[str, Any], cfg: dict[str, Any] | None = None,
                  schemas: bool = True) -> str:
    """``CREATE MATERIALIZED LAKE VIEW … USING OneLake_Files`` fuer eine Quelle.

    Der ABFSS-Pfad braucht Workspace- und Lakehouse-GUID der Bronze-Landezone. Das sind
    Tenant-Fakten wie beim Copy job: aus ``--connections`` (``workspaceId``/``lakehouseId``),
    sonst der Marker, der beim Anlegen laut scheitert statt auf etwas Falsches zu zeigen.
    """
    from core.dataarch_engine.blueprint.naming import layer_ref
    from core.dataarch_engine.blueprint.provision_transforms import _ident
    cfg = cfg or {}
    f = entry.get("file_mlv") or {}
    src = str(entry["source"])
    ws = cfg.get("workspaceId") or UNRESOLVED
    lh = cfg.get("lakehouseId") or UNRESOLVED
    pfad = f"abfss://{ws}@onelake.dfs.fabric.microsoft.com/{lh}/{f['path']}"
    optionen = [("format", f["format"]), ("path", pfad)]
    if f["format"] == "csv":
        optionen.append(("header", "true" if f.get("header", True) else "false"))
        if f.get("delimiter"):
            optionen.append(("delimiter", f["delimiter"]))
    defekt = f.get("defekte_zeilen_spalte")
    if defekt and f["format"] != "csv":
        # Das Schema sperrt das schon; hier nur, damit ein ungeprueftes Dict nicht still verliert.
        raise ValueError(f"{src}: defekte_zeilen_spalte gilt laut Learn nur fuer CSV")
    if defekt:
        optionen.append(("columnNameOfCorruptRecord", defekt))
    opt = ",\n".join(f"    '{k}' = '{v}'" for k, v in optionen)
    props = (f"    'schema_mode' = '{f.get('schema_mode', 'DYNAMIC')}',\n"
             f"    'refresh_mode' = '{f.get('refresh_mode', 'APPEND_ONLY')}'")
    # Optionale FROM-lose Projektion (Learn: `[AS SELECT select_expression ...]` als letzte
    # Klausel nach TBLPROPERTIES; `columnNameOfCorruptRecord` verlangt die Spalte im AS SELECT,
    # `__filepath__` ist eine Quell-Metadatenspalte, die man ausdruecklich projiziert).
    # ANNAHME, ungeprueft: `*` liefert die Dateispalten und schliesst beide Zusatzspalten nicht
    # ein (Learn zeigt nur benannte Spalten) — sonst doppelte Spalte beim CREATE.
    extra = [s for s in (defekt, "__filepath__" if f.get("dateipfad_spalte") else None) if s]
    ende = ");\n" if not extra else (
        ")\nAS SELECT\n" + ",\n".join(f"    {s}" for s in ["*", *extra]) + ";\n")
    return (f"-- bronze '{src}' ({entry.get('source_system', '')}): Datei-MLV aus {f['path']} "
            f"({f['format']}), D-619\n"
            f"CREATE MATERIALIZED LAKE VIEW IF NOT EXISTS {layer_ref('bronze', _ident(src), schemas)}\n"
            f"USING OneLake_Files\nOPTIONS (\n{opt}\n)\n"
            f"COMMENT 'bronze {src} (generated, file ingestion)'\n"
            f"TBLPROPERTIES (\n{props}\n{ende}")


DATEI_MLV_EREIGNIS_DOC = ("learn.microsoft.com/fabric/data-engineering/materialized-lake-views/"
                          "schedule-lineage-run")


def datei_mlv_ereignis(entry: dict[str, Any], cfg: dict[str, Any] | None = None,
                       schemas: bool = True) -> str:
    """``file_mlv/<quelle>.refresh_event.json`` — OneLake-Ereignis als Ausloeser (D-621).

    **Keine API-Nutzlast**, wie ``provision_transforms._mlv_refresh_event``: Learn
    (*Schedule a materialized lake view refresh*, gelesen 01.10.2026) beschreibt den
    ereignisgesteuerten Refresh nur im Portal (*Event-triggered (Preview)* → *OneLake events*),
    eine REST-Form steht dort nicht. Die Datei haelt fest, was einzustellen ist.
    """
    import json as _json

    from core.dataarch_engine.blueprint.naming import layer_ref
    from core.dataarch_engine.blueprint.provision_transforms import _ident
    cfg = cfg or {}
    f = entry.get("file_mlv") or {}
    src = str(entry["source"])
    return _json.dumps({
        "_comment": ("Ereignisgesteuerter Refresh der Datei-MLV (Preview, D-621). Einrichtung im "
                     "Portal (Manage schedules → New schedule → Refresh type: Event-triggered), "
                     "nicht per API. file_mlv/refresh_schedule.json bleibt der reproduzierbare "
                     "Rueckfall — vor dem Aktivieren pausieren."),
        "refreshType": "Event-triggered",
        "status": "Preview",
        "eventSourceType": "OneLake events",
        "eventSource": {"workspaceId": cfg.get("workspaceId") or UNRESOLVED,
                        "lakehouseId": cfg.get("lakehouseId") or UNRESOLVED,
                        "path": f.get("path", "")},
        "eventType": "<im Portal waehlen: Datei angelegt im Ordner oben>",
        "scope": "Refresh selected materialized lake view(s)",
        "views": [layer_ref("bronze", _ident(src), schemas)],
        "abhaengigkeiten": ["FMLV Refresh (Notebook, automatisch angelegt)",
                            "Activator (automatisch angelegt)"],
        "nicht_unterstuetzt": ["Private Link"],
        "beleg": DATEI_MLV_EREIGNIS_DOC + " (gelesen 01.10.2026)",
    }, indent=2, ensure_ascii=False) + "\n"


def emit_datei_mlv(bp: dict[str, Any], schemas: bool = True,
                   connections: dict[str, dict] | None = None) -> dict[str, str]:
    """Je ``file_mlv``-Quelle eine DDL, dazu Zeitplan und Dokument (relativ zu ``ingestion/``)."""
    entries = _datei_mlv_entries(bp)
    if not entries:
        return {}
    from core.dataarch_engine.blueprint.fabric_schedule import emit_schedule
    from core.dataarch_engine.blueprint.provision_transforms import _ident
    connections = connections or {}
    out: dict[str, str] = {}
    zeilen, offen, nicht_append, ereignis = [], [], [], []
    projektion: list[tuple[str, str]] = []
    for e in entries:
        src = str(e["source"])
        cfg = connections.get(src) or {}
        f = e.get("file_mlv") or {}
        out[f"file_mlv/{_ident(src)}.mlv.sql"] = datei_mlv_sql(e, cfg, schemas)
        if f.get("trigger") == "onelake_event":
            out[f"file_mlv/{_ident(src)}.refresh_event.json"] = datei_mlv_ereignis(e, cfg, schemas)
            ereignis.append(src)
        if not (cfg.get("workspaceId") and cfg.get("lakehouseId")):
            offen.append(src)
        modus = f.get("refresh_mode", "APPEND_ONLY")
        if modus != "APPEND_ONLY":
            nicht_append.append((src, modus))
        auswahl = [a for a, an in (("__filepath__", f.get("dateipfad_spalte")),
                                   (f"defekte Zeilen in `{f.get('defekte_zeilen_spalte')}`",
                                    f.get("defekte_zeilen_spalte"))) if an]
        if auswahl:
            projektion.append((src, ", ".join(auswahl)))
        zeilen.append(f"| `{src}` | `{f.get('path', '')}` | {f.get('format', '')} | "
                      f"{f.get('schema_mode', 'DYNAMIC')} | {modus} | "
                      f"{'OneLake-Ereignis' if f.get('trigger') == 'onelake_event' else 'Zeitplan'} |")
    out["file_mlv/refresh_schedule.json"] = emit_schedule(time=DATEI_MLV_REFRESH_UHRZEIT)
    doc = [
        "# Bronze aus Dateien — Materialized Lake Views (D-619)",
        "",
        "Quellen mit `access_mode: file_mlv` landen ohne Copy job: eine Datei-MLV",
        "(`USING OneLake_Files`) liest CSV oder Parquet aus `Files/` der Bronze-Landezone und",
        "materialisiert sie als Delta-Tabelle. Silber liest sie unter demselben Namen wie eine",
        "kopierte Quelle. MLV ist GA (Spark SQL, seit März 2026); Beleg: " + DATEI_MLV_DOC + ".",
        "",
        "| Quelle | Pfad | Format | Schema | Refresh | Auslöser |",
        "|---|---|---|---|---|---|",
        *zeilen,
        "",
        "## Anlegen und Refresh",
        "",
        "Jede `.mlv.sql` einmal im Bronze-Lakehouse ausführen (Notebook oder SQL-Editor des",
        "Lakehouse; der SQL-Analyseendpunkt kennt `CREATE MATERIALIZED LAKE VIEW` nicht). Den",
        "Refresh startet Fabric **nicht** von selbst: `refresh_schedule.json` ist der Body für",
        "`POST …/lakehouses/{bronzeLakehouseId}/jobs/refreshMaterializedLakeViews/schedules`,",
        f"täglich {DATEI_MLV_REFRESH_UHRZEIT} UTC, eine Stunde vor der Pipeline (02:00 UTC).",
        "Dauert das Laden länger, liest Silber den alten Stand — Zeitversatz, keine Kopplung.",
        "",
        "## Grenzen (Learn, gelesen 01.10.2026)",
        "",
        "- Nur CSV und Parquet; kein Leerzeichen und kein `%20` im Pfad (das Schema sperrt beides).",
        "- Ein Shortcut als Quelle: beim Anlegen werden Unterordner gelesen, beim Refresh werden",
        "  neue Dateien nur im Wurzelordner des Shortcuts entdeckt.",
        "- `FIXED` scheitert beim Anlegen, wenn Dateien im Ordner verschiedene Schemata haben.",
        "- Die Spark-CSV-Option `mode` nicht setzen; Fabric verwaltet defekte Zeilen selbst.",
        "- Der Pfad nutzt Workspace- und Lakehouse-**GUID** statt der Namen aus dem",
        "  Learn-Beispiel; beides ist OneLake-Adressierung. Am Tenant ungeprüft.",
        "",
        "## Herkunft und defekte Zeilen je Quelle (optional)",
        "",
        "Ohne Angabe hat die Sicht keine Projektion. Je Quelle wählbar, beides hängt ein",
        "FROM-loses `AS SELECT *, …` als letzte Klausel an (Learn: `[AS SELECT select_expression",
        "…]` nach `TBLPROPERTIES`, kein `FROM`):",
        "",
        "- `file_mlv.dateipfad_spalte: true` — projiziert `__filepath__`, die Quelldatei je Zeile.",
        "- `file_mlv.defekte_zeilen_spalte: <name>` (nur CSV) — setzt",
        "  `'columnNameOfCorruptRecord' = '<name>'` und projiziert die Spalte; sie hält den",
        "  Rohtext defekter Zeilen, gültige Zeilen tragen `NULL`. Prüfen mit",
        "  `SELECT <name> FROM <sicht> WHERE <name> IS NOT NULL`.",
        "- ANNAHME, ungeprüft: `*` liefert die Dateispalten ohne diese beiden Zusatzspalten",
        "  (Learn zeigt nur benannte Spalten). Am Tenant beim ersten `CREATE` prüfen.",
        "",
        "Gewählt für: " + (", ".join(f"`{s}` ({a})" for s, a in projektion) if projektion
                          else "keine Quelle") + ".",
        "",
    ]
    doc += [
        "## Auslöser je Quelle (D-621)",
        "",
        "Vorgabe ist der Zeitplan oben. Je Quelle wählbar (`file_mlv.trigger: onelake_event`):",
        "ein **ereignisgesteuerter** Refresh auf *OneLake events* des Landeordners — die Sicht",
        "läuft, wenn Dateien landen, statt zu einer geratenen Uhrzeit. Learn",
        f"({DATEI_MLV_EREIGNIS_DOC}, gelesen 01.10.2026): **Preview**, Einrichtung nur im Portal,",
        "hängt an den automatisch angelegten Items *FMLV Refresh* (Notebook) und Activator, **kein",
        "Private Link**. Unter welcher Identität diese Items laufen, ist nicht belegt (Tenant).",
        "",
    ]
    if ereignis:
        doc += [
            "Gewählt für: " + ", ".join(f"`{s}`" for s in ereignis) + ". Je Quelle beschreibt",
            "`<quelle>.refresh_event.json`, was im Portal einzustellen ist. Den Zeitplan vor dem",
            "Aktivieren des Ereignisses **pausieren** und nach der ersten Landung den Lauf in",
            "*Recent runs* lesen. Er bleibt in der Lieferung als reproduzierbarer Rückfall.",
            "",
            "Ein Ereignis startet nur die Datei-MLV. Silber entsteht per Notebook; die Pipeline",
            "danach startet weiter zu ihrer Uhrzeit — Extended lineage folgt nur MLV-Kanten und",
            "überbrückt den Notebook-Schritt nicht.",
            "",
        ]
    else:
        doc += ["In dieser Lieferung für keine Quelle gewählt.", ""]
    if nicht_append:
        doc += [
            "## Achtung: Bronze nicht append-only",
            "",
            "Bronze ist das System of Record (append-only). Diese Quellen schreiben es neu:",
            "",
            *[f"- `{s}`: `refresh_mode` {m}" for s, m in nicht_append],
            "",
        ]
    if offen:
        doc += [
            "## VERIFY: Bronze-Landezone offen",
            "",
            f"Ohne `workspaceId`/`lakehouseId` in `--connections` steht `{UNRESOLVED}` im Pfad —",
            "`CREATE` scheitert damit absichtlich:",
            "",
            *[f"- `{s}`" for s in offen],
            "",
        ]
    out["file_mlv/_DATEI_MLV.md"] = "\n".join(doc)
    return out


#: Beleg fuer die Handlung im VERIFY-Abschnitt der Konnektor-Typen (R9).
CONNECTOR_DOC = "learn.microsoft.com/fabric/data-factory/copy-job-connectors"


def _readme(rows: list[str], unresolved: list[str], unfilled: list[str],
            unsupported: list[tuple[str, str]],
            abgeleitet: list[tuple[str, str, str]],
            typ_offen: list[tuple[str, str, list[str]]] | None = None) -> str:
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
        "**Watermark-Spalte ohne NULL.** Nach der Erstladung laedt der Copy job keine Zeile, deren",
        "Watermark NULL ist — auch nicht, wenn sie spaeter eingefuegt oder geaendert wird. Die",
        "Einstellung „Null handling for incremental column\" gilt nur fuer die Erstladung (Learn",
        "`fabric/data-factory/incremental-copy-job`, gelesen 01.10.2026). Je Quelle pruefen, dass die",
        "Spalte NOT NULL ist; sonst fehlen Zeilen, ohne dass ein Lauf rot wird.",
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
    if typ_offen:
        lines += [
            "## VERIFY: Konnektor-Typ offen",
            "",
            f"Fuer diese Quellen steht im Copy job `{_UNVERIFIED}` statt eines Typs — es gibt",
            "kein belegtes Typ-Paar. Der Import scheitert daran absichtlich. **Handlung: Typ-Paar",
            "vor dem Import pruefen** und den Marker ersetzen (Quelle: Learn „Connectors for Copy",
            f"Job“, {CONNECTOR_DOC}; die echten Strings zeigt ein im Portal angelegter Copy job",
            "unter **View -> View JSON code**).",
            "",
            "| Quelle | Item | Feld mit Marker |",
            "|---|---|---|",
            *[f"| `{s}` | `{item}` | " + ", ".join(f"`{f}`" for f in felder) + " |"
              for s, item, felder in typ_offen],
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
