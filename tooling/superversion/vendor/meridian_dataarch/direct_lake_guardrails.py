"""direct_lake_guardrails — was ein Direct-Lake-Modell im Tenant zum Scheitern bringt.

Der Baukasten emittiert Direct-Lake-Modelle (`sap_tmdl` → `pbip_project`), prüfte aber nie, ob
sie im Ziel überhaupt tragen. Das ist dieselbe Signatur wie die INFORMATION_SCHEMA-Abfrage gegen
HANA und die Fabric-DDL unter `render/snowflake/`: es sieht fertig aus und fällt erst im Tenant
auf — dort vor Publikum.

**Zwei Klassen, und sie werden bewusst verschieden behandelt.**

*Statisch prüfbar* sind Spalten- und Beziehungseigenschaften, die im governten Katalog stehen:

  * **Binary- und GUID-Typen** werden von Direct Lake nicht getragen und müssen vorher in Strings
    (o. ä.) umgewandelt sein. Das ist keine Performance-Frage, das Modell lädt sonst nicht.
  * **Beziehungen brauchen typgleiche Spalten** auf beiden Seiten.
  * Die 1-Seite einer Beziehung muss **eindeutig** sein. Eindeutigkeit ist eine Dateneigenschaft,
    kein Schema — sie wird deshalb als messbare Frage emittiert, nicht als Befund behauptet.

*Nicht statisch prüfbar* sind die Kapazitäts-Guardrails (Parquet-Dateien, Row Groups, Zeilen je
Tabelle). Sie hängen am tatsächlichen Datenbestand, den diese Pipeline nie sieht. Erfunden würden
sie zur Falschaussage; deshalb dieselbe Zwei-Phasen-Form wie bei ``source_schema``: das Budget des
gewählten SKU wird ausgeschrieben, dazu eine **ausführbare Messung**, deren Ergebnis dagegen
gehalten wird.

**Warum das scharf ist.** Die Grenzen gelten **je Tabelle**, und die Folge unterscheidet sich nach
Modus — was die Wahl des Modus zu einer Betriebsentscheidung macht:

  * **Direct Lake on OneLake** (für neue Modelle empfohlen, kein Fallback): Refresh **schlägt fehl**,
    und das Modell ist **nicht mehr abfragbar**, bis die Delta-Tabellen wieder unter die Grenzen
    optimiert sind.
  * **Direct Lake on SQL**: Fallback auf DirectQuery, sofern aktiviert — Refresh gelingt mit
    Warnung, Abfragen liefern weiter Ergebnisse, nur langsamer.

Der Modellgrößen-Guardrail (Disk/OneLake) wird auf **Modell**-Ebene ausgewertet, alle anderen
**je Abfrage**.

Deterministisch; emittiert nur, führt nie aus.
"""
from __future__ import annotations

from typing import Any

# Delta-/Parquet-Typen, die Direct Lake nicht trägt (Substring-Match auf den physischen Typ).
_UNSUPPORTED_TYPES = ("binary", "varbinary", "uniqueidentifier", "guid", "uuid")

# Die dokumentierte Obergrenze für String-Spaltenwerte in Direct Lake.
MAX_STRING_LENGTH = 32764

MODE_ONELAKE = "onelake"
MODE_SQL = "sql"


def sku_budget(sku: str) -> dict[str, Any]:
    """Die Guardrails des SKU als Zahlen — aus der bestehenden Kapazitäts-Leiter, nicht neu gepflegt.

    Über ``sku_ceilings`` statt direkt über die Empfehlungs-Leiter: die endet bei F1024 (absichtlich —
    darüber ist Sizing eine gemessene Entscheidung), die **Erkennung** darf dort aber nicht enden. Vorher
    fiel ein zugewiesenes F2048 durch und dieser Emitter lieferte für die größten Kunden **gar nichts**.
    """
    from core.dataarch_engine.blueprint.capacity_recommend import sku_ceilings

    entry = sku_ceilings(str(sku))
    if entry is None:
        return {}
    return {
        "sku": entry["sku"],
        "parquet_files_per_table": entry["dl_files"],
        "row_groups_per_table": entry["dl_row_groups"],
        "rows_per_table": entry["rows_m"] * 1_000_000,
        "model_size_on_disk_gb": entry["disk_gb"],      # None = unbegrenzt (F64+)
        "max_memory_gb": entry["dl_mem_gb"],            # kein Guardrail, aber Paging-Grenze
    }


def _physical_type(col: Any) -> str:
    """Der physische Typ einer Katalogspalte — der Katalog führt Spalten als String oder als Objekt."""
    if isinstance(col, dict):
        return str(col.get("physicalType") or col.get("type") or "")
    return ""


def types_from_odcs(contracts: Any) -> dict[tuple[str, str], str]:
    """``(tabelle, spalte) → physischer Typ`` aus ODCS-Verträgen.

    Der governte Katalog führt Spalten als **Namen** (``odcs_to_catalog`` behält bewusst nur die
    Projektion). Die Typen stehen eine Ebene tiefer, in den ``properties`` des ODCS-Vertrags — und
    genau die entscheiden, ob Direct Lake die Tabelle laden kann. Deshalb wird hier dort gelesen,
    statt vom Katalog etwas zu verlangen, was er vertragsgemäß nicht trägt.
    """
    if isinstance(contracts, dict):
        contracts = [contracts]
    out: dict[tuple[str, str], str] = {}
    for contract in contracts or []:
        for obj in contract.get("schema", []) or []:
            table = str(obj.get("physicalName") or obj.get("name") or "")
            for prop in obj.get("properties") or []:
                name = str(prop.get("name") or "")
                physical = str(prop.get("physicalType") or prop.get("logicalType") or "")
                if table and name and physical:
                    out[(table, name)] = physical
    return out


def _column_entries(table: dict,
                    types: dict[tuple[str, str], str] | None = None) -> list[tuple[str, str]]:
    """``(name, physical_type)`` je Spalte; Typ leer, wo weder Katalog noch Vertrag ihn kennt."""
    types = types or {}
    tname = str(table.get("name") or "")
    out: list[tuple[str, str]] = []
    for col in table.get("columns") or []:
        if isinstance(col, dict):
            name = str(col.get("name") or "")
            physical = _physical_type(col)
        else:
            name, physical = str(col), ""
        out.append((name, physical or types.get((tname, name), "")))
    return [(n, t) for n, t in out if n]


def unsupported_column_types(governed_catalog: dict | None,
                             odcs_contracts: Any = None) -> list[dict[str, str]]:
    """Spalten, deren Typ Direct Lake nicht trägt. Ohne Typinformation wird nichts behauptet."""
    types = types_from_odcs(odcs_contracts)
    findings: list[dict[str, str]] = []
    for table in sorted((governed_catalog or {}).get("tables") or [],
                        key=lambda t: str(t.get("name", ""))):
        for name, physical in _column_entries(table, types):
            low = physical.lower()
            if any(bad in low for bad in _UNSUPPORTED_TYPES):
                findings.append({
                    "table": str(table.get("name") or ""), "column": name, "type": physical,
                    "why": "Direct Lake trägt Binary-/GUID-Typen nicht — vor dem Modell in String "
                           "(o. ä.) umwandeln, sonst lädt die Tabelle nicht",
                })
    return findings


def relationship_type_mismatches(governed_catalog: dict | None,
                                 odcs_contracts: Any = None) -> list[dict[str, str]]:
    """Beziehungen, deren beide Seiten unterschiedliche physische Typen haben.

    Nur gemeldet, wenn **beide** Typen bekannt sind — eine Beziehung ohne Typinformation ist
    keine Feststellung, sondern eine Lücke im Katalog.
    """
    gc = governed_catalog or {}
    declared = types_from_odcs(odcs_contracts)
    types: dict[tuple[str, str], str] = {}
    for table in gc.get("tables") or []:
        tname = str(table.get("name") or "")
        for name, physical in _column_entries(table, declared):
            if physical:
                types[(tname, name)] = physical

    out: list[dict[str, str]] = []
    for rel in sorted(gc.get("relationships") or [],
                      key=lambda r: (str(r.get("from_table")), str(r.get("from_column")))):
        a = types.get((str(rel.get("from_table")), str(rel.get("from_column"))))
        b = types.get((str(rel.get("to_table")), str(rel.get("to_column"))))
        if a and b and a.lower() != b.lower():
            out.append({
                "from": f"{rel.get('from_table')}[{rel.get('from_column')}] ({a})",
                "to": f"{rel.get('to_table')}[{rel.get('to_column')}] ({b})",
                "why": "Direct Lake verlangt typgleiche Spalten auf beiden Seiten einer Beziehung",
            })
    return out


def blocking_findings(governed_catalog: dict | None,
                      odcs_contracts: Any = None) -> list[dict[str, str]]:
    """Alles, was das Modell nachweislich am Laden hindert (statisch belegt, nicht vermutet)."""
    return (unsupported_column_types(governed_catalog, odcs_contracts)
            + relationship_type_mismatches(governed_catalog, odcs_contracts))


def measurement_sql(bp: dict, schemas: bool = True) -> str:
    """Die ausführbare Messung gegen die Guardrails — Spark SQL, gegen die Gold-Tabellen.

    ``DESCRIBE DETAIL`` liefert Dateizahl und Größe je Delta-Tabelle; die Zeilenzahl kommt aus einem
    `COUNT(*)`. Row Groups stehen in keiner der beiden Auskünfte — dafür wird der Parquet-Footer
    gelesen; das ist als Hinweis vermerkt statt still weggelassen, weil ein Guardrail, den niemand
    misst, genauso wirkt wie keiner.
    """
    from core.dataarch_engine.blueprint.naming import layer_ref

    products = sorted({str(p) for d in bp.get("mesh", {}).get("domains", []) or []
                       for p in d.get("data_products") or []})
    lines = [
        "-- Direct-Lake-Guardrails messen (Spark SQL, im Ziel-Workspace ausführen).",
        "-- Die Grenzen gelten JE TABELLE. Bei Direct Lake on OneLake ist eine überschrittene",
        "-- Tabelle kein Performance-Thema: der Refresh schlägt fehl und das Modell ist nicht",
        "-- mehr abfragbar, bis die Delta-Tabellen wieder darunter liegen.",
        "",
    ]
    if not products:
        lines.append("-- (keine Gold-Produkte im Blueprint — nichts zu messen)")
        return "\n".join(lines) + "\n"

    for product in products:
        t = layer_ref("gold", product, schemas)
        lines += [
            f"DESCRIBE DETAIL {t};   -- numFiles, sizeInBytes",
            f"SELECT '{t}' AS table_name, COUNT(*) AS rows FROM {t};",
            "",
        ]
    lines += [
        "-- Row Groups: weder DESCRIBE DETAIL noch COUNT(*) geben sie aus. Sie stehen im",
        "-- Parquet-Footer je Datei — z. B. über pyarrow:",
        "--   import pyarrow.parquet as pq; pq.ParquetFile(<datei>).num_row_groups",
        "-- Faustregel aus derselben Doku: für Direct Lake 8M+ Zeilen je Row Group anstreben;",
        "-- wenige große Row Groups halten die Zahl klein UND die Abfrage schnell.",
    ]
    return "\n".join(lines) + "\n"


# Rollen, in denen das Semantikmodell wohnt bzw. die Delta-Tabellen liegen — in dieser
# Reihenfolge, erster Treffer gewinnt.
_MODEL_ROLES = ("reporting", "serving", "gold")
_SOURCE_ROLES = ("gold", "silver", "lakehouse")


def _workspace_by_role(domain: dict, roles: tuple[str, ...]) -> str:
    workspaces = domain.get("workspaces") or []
    for role in roles:
        for ws in workspaces:
            if str(ws.get("role") or "").lower() == role:
                return str(ws.get("name") or "")
    return str(workspaces[0].get("name") or "") if workspaces else ""


def region_pairs(bp: dict) -> list[dict[str, str]]:
    """Workspace-Paare, die dieselbe Region haben **müssen** — je Domäne eines.

    Ein Direct-Lake-Modell darf nicht in einer anderen Region liegen als der Workspace seiner
    Quelle. Fällt bei uns beides in denselben Workspace, ist die Bedingung trivial erfüllt und
    wird als ``satisfied`` markiert statt weggelassen: „nicht geprüft" und „geprüft und in
    Ordnung" dürfen im Ergebnis nicht gleich aussehen.
    """
    out: list[dict[str, str]] = []
    for domain in sorted(bp.get("mesh", {}).get("domains", []) or [],
                         key=lambda d: str(d.get("name", ""))):
        model_ws = _workspace_by_role(domain, _MODEL_ROLES)
        source_ws = _workspace_by_role(domain, _SOURCE_ROLES)
        if not model_ws or not source_ws:
            continue
        out.append({
            "domain": str(domain.get("name") or ""),
            "model_workspace": model_ws,
            "source_workspace": source_ws,
            "status": "satisfied_same_workspace" if model_ws == source_ws else "must_match",
        })
    return out


def region_findings(pairs: list[dict[str, str]],
                    regions: dict[str, str] | None) -> list[dict[str, str]]:
    """Paare, deren Regionen auseinanderlaufen. Ohne Messung wird nichts behauptet.

    Ein unbekannter Workspace ist **kein** Befund und auch keine Entwarnung — er wird als
    ``unknown`` geführt, damit eine unvollständige Messung nicht wie ein grünes Ergebnis wirkt.
    """
    regions = {str(k): str(v) for k, v in (regions or {}).items()}
    out: list[dict[str, str]] = []
    for pair in pairs:
        if pair["status"] != "must_match":
            continue
        a, b = regions.get(pair["model_workspace"]), regions.get(pair["source_workspace"])
        if a is None or b is None:
            out.append({**pair, "verdict": "unknown",
                        "detail": "Region mindestens eines der beiden Workspaces nicht gemessen"})
        elif a.strip().lower() != b.strip().lower():
            out.append({**pair, "verdict": "mismatch",
                        "detail": f"{pair['model_workspace']}={a} vs "
                                  f"{pair['source_workspace']}={b}"})
    return out


def region_probe(pairs: list[dict[str, str]]) -> str:
    """Phase 1: die ausführbare Frage nach der Region je Workspace.

    Zwei Schritte, weil eine Region nicht am Workspace hängt: der Workspace nennt seine
    ``capacityId``, und erst die Kapazität trägt die Region. Der zweite Schritt läuft gegen die
    **Power-BI-Admin-API** — anderer Host, andere Zielgruppe, und er verlangt Fabric-/Power-BI-
    Administratorrechte. Wer die nicht hat, liest die Region im Admin-Portal ab; das ist kein
    Grund, hier einen Endpunkt zu erfinden, der ohne Adminrechte funktioniert.
    """
    names = sorted({w for p in pairs for w in (p["model_workspace"], p["source_workspace"])})
    lines = [
        "# Region je Workspace ermitteln (Phase 1)",
        "",
        "Ein Direct-Lake-Modell darf **nicht** in einer anderen Region liegen als der Workspace",
        "seiner Quelle. Die Region steht nicht am Workspace — sie kommt über seine Kapazität.",
        "",
        "## Schritt 1 — Workspace → capacityId (Fabric REST)",
        "",
        "```http",
        "GET https://api.fabric.microsoft.com/v1/workspaces/{workspaceId}",
        "Authorization: Bearer <token>",
        "```",
        "",
        "## Schritt 2 — capacityId → Region (Power BI **Admin**-API)",
        "",
        "```http",
        "GET https://api.powerbi.com/v1.0/myorg/admin/capacities",
        "Authorization: Bearer <token>",
        "```",
        "",
        "> Anderer Host **und** andere Zielgruppe als die Fabric-API, und dieser Aufruf verlangt",
        "> Administratorrechte. Ohne sie steht die Region im Admin-Portal („find your Fabric home",
        "> region\") — das ist der dokumentierte Weg, nicht ein Mangel dieser Anleitung.",
        "",
        "## Zu messen",
        "",
    ]
    lines += [f"- `{n}`" for n in names] or ["- (keine Workspaces im Blueprint)"]
    lines += [
        "",
        "## Ergebnis zurückgeben",
        "",
        "Als JSON-Objekt `{\"<workspace>\": \"<region>\"}`, z. B.:",
        "",
        "```json",
        "{",
        *[f'  "{n}": "<region>"{"," if i < len(names) - 1 else ""}' for i, n in enumerate(names)],
        "}",
        "```",
        "",
        "und mit `--direct-lake-regions <datei>` erneut emittieren. Bis dahin bleibt die",
        "Bedingung **ungeprüft** — nicht etwa erfüllt.",
    ]
    return "\n".join(lines) + "\n"


def _budget_table(budget: dict[str, Any]) -> list[str]:
    disk = budget.get("model_size_on_disk_gb")
    return [
        "| Guardrail | Grenze | Auswertung |",
        "|---|---|---|",
        f"| Parquet-Dateien je Tabelle | {budget['parquet_files_per_table']:,} | je Abfrage |",
        f"| Row Groups je Tabelle | {budget['row_groups_per_table']:,} | je Abfrage |",
        f"| Zeilen je Tabelle | {budget['rows_per_table']:,} | je Abfrage |",
        f"| Modellgröße auf Disk/OneLake | {'unbegrenzt' if disk is None else f'{disk} GB'} "
        "| **auf Modellebene** |",
        f"| Max. Arbeitsspeicher | {budget['max_memory_gb']} GB | kein Guardrail — Paging-Grenze |",
    ]


def emit_direct_lake_guardrails(bp: dict, governed_catalog: dict | None = None,
                                sku: str = "F64", mode: str = MODE_ONELAKE,
                                schemas: bool = True,
                                odcs_contracts: Any = None,
                                sku_source: str = "",
                                regions: dict[str, str] | None = None) -> dict[str, str]:
    """Artefaktsatz: Budget + Messung + die statisch belegten Blocker."""
    budget = sku_budget(sku)
    if not budget:
        return {}

    blockers = blocking_findings(governed_catalog, odcs_contracts)
    consequence = (
        "Refresh **schlägt fehl** und das Modell ist **nicht abfragbar**, bis die Delta-Tabellen "
        "wieder unter den Grenzen liegen (Direct Lake on OneLake kennt keinen Fallback)."
        if mode == MODE_ONELAKE else
        "Fallback auf DirectQuery, sofern aktiviert: Refresh gelingt mit Warnung, Abfragen "
        "liefern weiter Ergebnisse — nur langsamer (Direct Lake on SQL)."
    )

    lines = [
        f"# Direct-Lake-Guardrails — {budget['sku']}",
        "",
        f"Modus: **{'Direct Lake on OneLake' if mode == MODE_ONELAKE else 'Direct Lake on SQL'}**",
        "",
        (f"> **Woher der SKU kommt:** {sku_source}" if sku_source else
         "> **Woher der SKU kommt:** explizit übergeben."),
        ">",
        "> Die Zahlen unten gelten **für genau diesen SKU**. Ein anderer zugewiesener SKU"
        "> verschiebt sie erheblich — zwischen F32 und F64 verfünffacht sich die Dateigrenze"
        "> und die Modellgröße wird unbegrenzt. Vor der Auslegung also den *zugewiesenen* SKU"
        "> einsetzen, nicht den empfohlenen Boden.",
        "",
        "## Budget",
        "",
        *_budget_table(budget),
        "",
        "## Wenn eine Grenze reißt",
        "",
        consequence,
        "",
        "Die Grenzen gelten **je Tabelle** — eine einzige Tabelle darüber genügt.",
        "",
        "## Was hier nicht geprüft werden kann",
        "",
        "Dateizahl, Row Groups und Zeilen hängen am tatsächlichen Datenbestand, den diese Pipeline",
        "nie sieht. Sie zu schätzen wäre eine Falschaussage über den Tenant. Stattdessen liegt in",
        "`guardrail_measurement.sql` die ausführbare Messung; ihr Ergebnis wird gegen das Budget",
        "oben gehalten.",
        "",
        "## Statisch belegte Blocker",
        "",
    ]
    if blockers:
        lines.append(f"{len(blockers)} Befund(e) — diese verhindern das Laden unabhängig von der Größe:")
        lines.append("")
        for b in blockers:
            if "column" in b:
                lines.append(f"- `{b['table']}[{b['column']}]` — Typ `{b['type']}`: {b['why']}")
            else:
                lines.append(f"- {b['from']} → {b['to']}: {b['why']}")
    else:
        lines.append("Keine — soweit der governte Katalog Typen führt. Wo er nur Spaltennamen kennt,")
        lines.append("wird nichts behauptet: eine Spalte ohne Typangabe ist keine geprüfte Spalte.")

    lines += [
        "",
        "## Was nur Daten beantworten",
        "",
        "- **Eindeutigkeit der 1-Seite** jeder Beziehung: Direct Lake bricht Abfragen ab, wenn dort",
        "  Duplikate stehen. Das ist eine Dateneigenschaft — sie gehört in die Ingress-DQ",
        "  (`--emit-ingress-dq`), nicht in eine Behauptung hier.",
        f"- **String-Länge** über {MAX_STRING_LENGTH:,} Unicode-Zeichen wird nicht getragen.",
        "- **NaN** und andere nicht-numerische Fließkommawerte werden nicht getragen.",
        "",
        "## Region — gemessen, nicht angenommen",
        "",
    ]
    pairs = region_pairs(bp)
    findings = region_findings(pairs, regions)
    trivial = [p for p in pairs if p["status"] == "satisfied_same_workspace"]
    if not pairs:
        lines.append("Keine Workspaces im Blueprint — nichts zu paaren.")
    elif regions is None:
        lines += [
            f"**Ungeprüft.** {len([p for p in pairs if p['status'] == 'must_match'])} Paar(e) "
            "müssten dieselbe Region haben; die Regionen wurden nicht gemessen. Die Frage steht "
            "in `region_probe.md`, das Ergebnis kommt über `--direct-lake-regions` zurück.",
            "",
            "Ungeprüft ist **nicht** erfüllt — deshalb steht hier kein Haken.",
        ]
    elif findings:
        lines.append(f"{len(findings)} Befund(e):")
        lines.append("")
        for f in findings:
            if f["verdict"] == "mismatch":
                lines.append(f"- **{f['domain']}**: {f['detail']} — ein Direct-Lake-Modell über "
                             "diese Grenze hinweg lässt sich nicht anlegen.")
            else:
                lines.append(f"- **{f['domain']}**: {f['detail']} (ungeprüft, nicht erfüllt)")
        lines += [
            "",
            "**Dokumentierter Ausweg** (Direct Lake on SQL): ein Lakehouse im Workspace der",
            "anderen Region anlegen und die Tabellen per Shortcut hereinholen, *bevor* das",
            "Semantikmodell erzeugt wird.",
        ]
    else:
        lines.append("Alle Paare gemessen und in derselben Region.")
    if trivial:
        lines += ["",
                  f"{len(trivial)} Domäne(n) tragen Modell und Quelle im **selben** Workspace — "
                  "dort ist die Bedingung bauartbedingt erfüllt."]

    lines += [
        "",
        "## Eine Randbedingung, die erst im Tenant auffällt",
        "",
        "- Direct Lake läuft **über kein Gateway** — weder on-premises noch VNet, in beiden Modi.",
        "  Wer die Quelle nur über ein Gateway erreicht, kann Direct Lake nicht fahren.",
    ]

    out = {
        "direct_lake/_GUARDRAILS.md": "\n".join(lines) + "\n",
        "direct_lake/guardrail_measurement.sql": measurement_sql(bp, schemas),
    }
    if pairs and regions is None:
        out["direct_lake/region_probe.md"] = region_probe(pairs)
    return out
