"""provision_fabric — emit a `fab` CLI provisioning script from an ArchitectureBlueprint.

Live-provisioning helper (ADR-0015 follow-up): turns a blueprint into a deterministic
bash script of Microsoft `fab` CLI commands that a human runs against a real tenant
(e.g. a Fabric trial). This module **does not execute** anything — it emits the script.

Grounded in the repo's proven fab syntax
(`meridian/tool-layers/fabric/provisioning/blueprint1/`): `fab config set mode
command_line`, `fab mkdir "<name>.Workspace" -P capacityName=<cap>`,
`.Lakehouse` items. Steps whose exact `fab` subcommand is not established in-repo
(OneLake shortcut / mirroring creation, artifact import) are emitted as explicit,
commented VERIFY steps rather than invented commands — honest by construction.
"""
from __future__ import annotations

GOLD_LAKEHOUSE = "analytics_gold"


_MIRROR_KEYS = ("connectionId", "database", "defaultSchema", "mirrorType", "mountedTables")


def _mirror_cmd(ws: str, src: str, cfg: dict) -> str:
    """Real, idempotent Mirrored-Database creation from a connection config."""
    item = f"{ws}.Workspace/{src}.MirroredDatabase"
    params = ",".join(f"{k}={cfg[k]}" for k in _MIRROR_KEYS if cfg.get(k))
    p = f" -P {params}" if params else ""
    return f'fab ls "{item}" >/dev/null 2>&1 || fab mkdir "{item}"{p}'


def _shortcut_cmd(target_lh: str, src: str, cfg: dict) -> str:
    """Real, idempotent OneLake shortcut creation via `fab ln`."""
    item = f"{target_lh}/Files/{src}.Shortcut"
    typ = cfg.get("type", "adlsGen2")
    inp = cfg.get("input", f"<{src}_connection.json>")
    return f'fab ls "{item}" >/dev/null 2>&1 || fab ln "{item}" --type {typ} -i {inp}'


def _sap_datasphere_quellen(ingestion: list[dict]) -> dict[str, list[dict]]:
    """SAP-Quellen, die ueber Datasphere gespiegelt werden — gruppiert nach Quellsystem.

    Der Unterscheider ist der `connector`, nicht der `access_mode`: `mirroring` UND
    `sap-cdc` tragen beide `mirror`, aber nur `mirroring` bezeichnet den Weg ueber
    Datasphere (`sap_handover_gate`, Fahrplan Kap. 2).

    Gruppiert wird nach System, weil ein Mirrored-SAP-Item **alles unter seinem
    Shortcut-Pfad** abdeckt (MS Learn, `fabric/mirroring/sap-limitations`, gemessen
    08.09.2026): „Mirroring for SAP replicates all the data under the lakehouse shortcut
    path configured in the mirrored database." Ein Item je SAP-Tabelle waere dieselbe
    Kardinalitaets-Verwechslung wie ein Private Endpoint je Tabelle.
    """
    gruppen: dict[str, list[dict]] = {}
    for e in ingestion:
        if e.get("connector") != "mirroring":
            continue
        schluessel = str(e.get("source_system") or "").strip() or f"__quelle__{e.get('source', '')}"
        gruppen.setdefault(schluessel, []).append(e)
    return dict(sorted(gruppen.items()))


def _sap_mirror_block(system: str, quellen: list[dict], ws: str, lakehouse: str) -> list[str]:
    """Die dokumentierte Schrittfolge fuer ein Mirrored-SAP-Item — mit VERIFY statt Erfindung.

    Belegt gegen MS Learn `fabric/mirroring/sap-datasphere-tutorial` (gemessen 08.09.2026).
    Bis heute stand hier je Quelle ein `fab mkdir <src>.MirroredDatabase -P
    connectionId=…,database=…,defaultSchema=…`. Das ist die Form des DATENBANK-Mirrorings
    (Azure SQL und Verwandte) und fuer SAP in drei Punkten falsch: es waeren 24 Items statt
    einem, die Parameter sind andere (Lakehouse + Shortcut-Pfad), und die zwei
    Voraussetzungsschritte fehlten ganz.

    Der Item-Aufruf selbst bleibt ein VERIFY: das Portal legt „Mirrored SAP" ueber einen
    Dialog an, und ein `fab`- oder REST-Aequivalent ist uns NICHT belegt. Dasselbe Muster
    wie bei `shortcut_transform` oben — ein wohlgeformter erfundener Befehl waere schlimmer
    als ein Marker, der laut nach der Messung verlangt.
    """
    namen = [str(q.get("source", "")) for q in quellen]
    kurz = f"{len(namen)} Quellen" if len(namen) > 1 else namen[0]
    return [
        f"# --- SAP ueber Datasphere spiegeln: {system or namen[0]} ({kurz}) ---",
        "#   Belegt: learn.microsoft.com/fabric/mirroring/sap-datasphere-tutorial",
        "#   Voraussetzung SAP-Seite (Datasphere, NICHT durch dieses Skript herstellbar):",
        "#     - Datasphere-Umgebung mit Premium Outbound Integration (kostenpflichtig)",
        "#     - Replication Flow: Ziel ADLS Gen2, `Group Delta` = None, `File Type` = Parquet",
        "#     - Load Type: `Initial and Delta` oder `Initial Only`",
        f"#   Schritt 1 — Lakehouse (wird unten als '{lakehouse}' angelegt, falls noch nicht da).",
        "#   Schritt 2 — ADLS-Gen2-Shortcut auf den GANZEN Container, in den Datasphere schreibt:",
        f'#     fab ln "{ws}.Workspace/{lakehouse}.Lakehouse/Files/<datasphere>.Shortcut" '
        "--type adlsGen2 -i <datasphere_connection.json>",
        "#   Schritt 3 — VERIFY: Item 'Gespiegelte Datenbank SAP' / 'Mirrored SAP' im Portal anlegen:",
        f"#     Neues Element -> Mirrored SAP -> Lakehouse '{lakehouse}' -> Wurzelordner der",
        "#     replizierten Daten waehlen -> Namen vergeben -> Anlegen.",
        "#     EIN Item deckt alle Objekte unter diesem Pfad ab; Objekte aendert man im",
        "#     Replication Flow, nicht durch weitere Items.",
        "#     Ein `fab`-/REST-Aequivalent ist hier NICHT belegt — im Tenant messen und",
        "#     diese Zeile dann durch den gemessenen Aufruf ersetzen.",
        f"#   Betroffene Quellen: {', '.join(namen)}",
    ]


def emit_fab_commands(blueprint: dict, capacity: str = "<CAPACITY_NAME>",
                      lakehouse: str = GOLD_LAKEHOUSE,
                      connections: dict | None = None, schemas: bool = False,
                      architecture_path: str = "../../blueprint.json") -> str:
    """Return a bash `fab` provisioning script (deterministic).

    ``architecture_path`` ist die Quelle, aus der dieser Lauf entstanden ist — relativ zum Ort
    des Skripts. Vorher stand dort ``<data_architecture.json>``: ein Platzhalter für eine Datei,
    die derselbe Lauf zwei Verzeichnisse höher selbst geschrieben hatte.

    ``connections`` maps a source name → connection config, e.g.
    ``{"src": {"kind": "mirror", "connectionId": "...", "database": "...", ...}}`` or
    ``{"src": {"kind": "shortcut", "type": "adlsGen2", "input": "./conn/src.json"}}``.
    Sources present in the map emit **real** fab commands; the rest stay as templates.
    connectionIds/secrets live in the caller's map (never the repo — scope boundary).
    """
    connections = connections or {}
    domains = sorted(blueprint.get("mesh", {}).get("domains", []), key=lambda d: d.get("name", ""))
    ingestion = sorted(blueprint.get("ingestion", []), key=lambda e: e.get("source", ""))

    lines: list[str] = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        "# ArchitectureBlueprint → Fabric provisioning (ADR-0015). Generated; review before running.",
        "# Prereq: authenticated fab CLI + a capacity. See prereq/_PREREQ.md in this",
        "# delivery; the supplier's own tenant runbook is not part of it.",
        f"#   Pass your capacity via CAP (default placeholder: {capacity}).",
        'CAP="${CAP:-' + capacity + '}"',
        "",
        "# fab >= 1.6: command-line mode is the default when a command is passed",
        "# (no 'fab config set mode' step needed — that is deprecated). Authenticate first:",
        "#   fab auth login                       # interactive (browser) — simplest for a trial",
        "#   fab auth login -u <CLIENT_ID> -p <SECRET> --tenant <TENANT_GUID>   # service principal",
        "",
    ]

    # De-duplicate workspaces by name: a single-topology blueprint has all domains
    # sharing one workspace, so we must not emit the same `fab mkdir` N times.
    seen_ws: dict[str, str] = {}
    ws_domains: dict[str, list[str]] = {}
    for d in domains:
        for ws in d.get("workspaces", []):
            seen_ws.setdefault(ws["name"], ws.get("role", ""))
            ws_domains.setdefault(ws["name"], []).append(d["name"])

    single = len(seen_ws) == 1 and next(iter(seen_ws.values())) == "mixed"
    lines.append(f"# 1. Workspace(s) — {'single shared workspace' if single else 'data mesh (per domain)'}")
    lines.append("#    idempotent: skip creation if it already exists (safe to re-run / reuse)")
    for name, role in sorted(seen_ws.items()):
        who = ", ".join(sorted(set(ws_domains[name])))
        lines.append(
            f'fab ls "{name}.Workspace" >/dev/null 2>&1 || '
            f'fab mkdir "{name}.Workspace" -P capacityName="$CAP"   # {role}: {who}')
    lines.append("")

    lines.append("# 2. Gold lakehouse per gold/shared workspace (idempotent)")
    if schemas:
        lines.append("#    schema-enabled lakehouse → medallion layer = real SQL schema (gold/silver),")
        lines.append("#    not the default 'dbo' namespace. VERIFY the -P flag against your fab version.")
    sp = " -P enableSchemas=true" if schemas else ""
    for name, role in sorted(seen_ws.items()):
        if role in ("gold", "mixed"):
            lh = f'{name}.Workspace/{lakehouse}.Lakehouse'
            lines.append(f'fab ls "{lh}" >/dev/null 2>&1 || fab mkdir "{lh}"{sp}')
    lines.append("")

    gold_ws = [n for n, r in sorted(seen_ws.items()) if r in ("gold", "mixed")]
    target_lh = (f"{gold_ws[0]}.Workspace/{lakehouse}.Lakehouse" if gold_ws
                 else "<gold-workspace>.Workspace/<lakehouse>.Lakehouse")

    ws0 = gold_ws[0] if gold_ws else "<gold-workspace>"
    lines.append("# 3. Ingestion (access unification) — real fab commands where a connection is given, else templates")
    lines.append("#    connections map (--connections): {source: {kind: mirror|shortcut, connectionId/database/…}}")
    lines.append("#    --type: adlsGen2 | amazonS3 | googleCloudStorage | s3Compatible | dataverse | oneLake")

    # SAP ueber Datasphere zuerst und je SYSTEM einmal — nicht je Quelle in der Schleife unten.
    # Ein Mirrored-SAP-Item deckt alles unter seinem Shortcut-Pfad ab; die Quellen darunter
    # sind Objekte des Replication Flows, keine eigenen Fabric-Items.
    sap_gruppen = _sap_datasphere_quellen(ingestion)
    sap_quellen = {str(q.get("source", "")) for qs in sap_gruppen.values() for q in qs}
    for system, quellen in sap_gruppen.items():
        lines += _sap_mirror_block(system if not system.startswith("__quelle__") else "",
                                   quellen, ws0, lakehouse)
        lines.append("")

    for e in ingestion:
        if e.get("source") in sap_quellen:
            continue        # oben als eine Gruppe behandelt
        mode = e.get("access_mode")
        sys_ = e.get("source_system", "")
        src = e["source"]
        cfg = connections.get(src)
        kind = (cfg or {}).get("kind") or ("shortcut" if mode == "shortcut" else
                                           "mirror" if mode == "mirror" else
                                           "shortcut_transform" if mode == "shortcut_transform" else
                                           "copy")
        if kind == "shortcut_transform":
            # Bewusst KEIN erfundener fab-Befehl: die Transformationen werden am Shortcut konfiguriert,
            # und dafuer ist uns kein CLI-/REST-Aufruf dokumentiert. Also die belegten Fakten und ein
            # VERIFY statt eines Kommandos, das im Tenant scheitert.
            lines.append(f"# {src} ({sys_}): OneLake shortcut MIT Datei-Transformationen")
            lines.append(f"#   Ersetzt die Ingestions-Pipeline (CSV/Parquet/JSON/Excel -> Delta, "
                         f"Poll ~2 min).")
            lines.append(f"#   ACHTUNG: Zieltabelle ist read-optimized — weder MERGE noch DELETE. "
                         f"Ueber dieser Ebene neu aufbauen, nicht hineinschreiben.")
            lines.append(f"#   Excel-Fallen: fuehrende Nullen gehen verloren, Purview-gelabelte Mappen "
                         f"sind unverarbeitbar, Blaetter jenseits von 25 werden uebersprungen.")
            lines.append(f"# VERIFY: die Transformations-Konfiguration am Shortcut '{src}' im Portal "
                         f"setzen — ein Kommandozeilen-Aequivalent ist hier nicht belegt.")
            continue
        if cfg and kind == "mirror":
            lines.append(f"# {src} ({sys_}): Mirroring")
            lines.append(_mirror_cmd(ws0, src, cfg))
        elif cfg and kind == "shortcut":
            lines.append(f"# {src} ({sys_}): OneLake shortcut")
            lines.append(_shortcut_cmd(target_lh, src, cfg))
        elif mode == "shortcut":
            lines.append(f"# {src} ({sys_}): external OneLake shortcut — provide a connection in --connections")
            lines.append(f'#   fab ln "{target_lh}/Files/{src}.Shortcut" --type adlsGen2 -i <{src}_connection.json>')
        elif mode == "mirror":
            lines.append(f"# {src} ({sys_}): Mirroring — provide a connection in --connections, e.g.")
            lines.append(f'#   fab mkdir "{ws0}.Workspace/{src}.MirroredDatabase" -P connectionId=<id>,database=<db>,defaultSchema=<schema>')
        else:
            # Bis 01.08.2026 stand hier NUR dieser Kommentar — Shortcut und Mirror bekamen
            # echte Befehle, die physische Kopie einen Satz. Jetzt verweist die Zeile auf ein
            # echtes Copy-job-Item (`--emit-ingestion`), das importiert werden kann.
            from core.dataarch_engine.blueprint.provision_ingestion import copy_job_name
            job = copy_job_name(src)
            lines.append(f"# {src} ({sys_}): Copy — Fabric Copy job (verwaltet Watermark/CDC selbst)")
            lines.append(f'#   render: python -m core.dataarch_engine.blueprint.cli … --emit-ingestion')
            lines.append(f'fab import "{ws0}.Workspace/{job}.CopyJob" '
                         f'-i ./render/fabric/ingestion/{job}.CopyJob -f')
    if not ingestion:
        lines.append("#   (no sources declared)")
    lines.append("")

    lines.append("# 4. Artifacts — import the generated PBIP items (run the report pipeline first)")
    lines.append(f"#   python -m products.pbi_pipeline --seed-from {architecture_path} --out ./dist")
    lines.append(f'#   fab import "{ws0}.Workspace/<Name>.SemanticModel" -i ./dist/<Name>.SemanticModel -f')
    lines.append(f'#   fab import "{ws0}.Workspace/<Name>.Report" -i ./dist/<Name>.Report -f')
    lines.append("")
    lines.append('echo "Provisioning script complete."')
    return "\n".join(lines) + "\n"
