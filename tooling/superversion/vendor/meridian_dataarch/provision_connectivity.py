"""provision_connectivity — emit secure/private connectivity for private data sources.

Closes the networking gap: the blueprint knew a source was on-prem/private (mirror mode, a gateway
hint) but emitted nothing to reach it privately. Grounded in MS Learn (2026-07): *Connect to
on-premises data sources using managed private endpoints*.

For each **private** source (access_mode ``mirror``, an explicit ``private: true``, or an on-prem /
gateway hint in the source system), emit:

- **Managed Private Endpoint (MPE)** spec — Fabric's outbound-over-Private-Link path for Spark /
  Data Pipelines. Real REST API: ``POST /v1/workspaces/{ws}/managedPrivateEndpoints`` with
  ``targetPrivateLinkResourceId`` + ``targetSubresourceType`` + ``targetFQDNs``. The tenant-specific
  Private-Link-Service resource id + FQDN are VERIFY placeholders (never invented); the shape is real.
- A **create script** of the same call as commented VERIFY templates (az token → POST).
- A plan naming the on-prem-gateway alternative + the hardening rails (Key Vault for secrets,
  Outbound Access Protection, open only the source port, monitor audit logs).

Honest by construction: the MPE REST body is deployable; the PLS/FQDN/subscription ids are
tenant-specific placeholders; PLS setup + approval are Azure-side steps → runbook, never a faked API.

This module **does not execute** anything — it only emits text.
"""
from __future__ import annotations

import json
import re
from core.dataarch_engine.blueprint.stack_capabilities import gap_doc_for

_NONWORD_RE = re.compile(r"[^a-z0-9]+")

# source-system hint → (MPE subresource type, default port) — grounded (1433 SQL, 1521 Oracle).
_HINTS = [
    (("sql server", "sqlserver", "mssql", "sql"), ("sql", 1433)),
    (("oracle",), ("oracle", 1521)),
    (("postgres", "postgresql"), ("postgresqlServer", 5432)),
    (("mysql", "maria"), ("mysqlServer", 3306)),
    (("blob", "adls", "storage", "lake"), ("blob", 443)),
]


def _ident(name: str) -> str:
    return _NONWORD_RE.sub("_", (name or "").lower()).strip("_")


def _slug(name: str) -> str:
    return _NONWORD_RE.sub("-", (name or "").lower()).strip("-")


def _is_private(e: dict) -> bool:
    """A source needs private connectivity if it mirrors an on-prem DB, is flagged private, or its
    system hints at on-prem / a gateway. Public REST/API copy sources don't (they reach the internet)."""
    if e.get("private") is True:
        return True
    if e.get("access_mode") == "mirror":
        return True
    sysname = (e.get("source_system") or "").lower()
    return any(h in sysname for h in ("on-prem", "on prem", "onprem", "gateway", "private", "vnet"))


def _subresource(source_system: str) -> tuple[str, int]:
    s = (source_system or "").lower()
    for needles, res in _HINTS:
        if any(n in s for n in needles):
            return res
    return ("<VERIFY: subresource type>", 0)


def _private_sources(bp: dict) -> list[dict]:
    return sorted((e for e in bp.get("ingestion", []) if _is_private(e)),
                  key=lambda e: str(e.get("source")))


def _mpe_specs(bp: dict) -> list[dict]:
    specs = []
    for e in _private_sources(bp):
        src = e.get("source", "")
        sub, port = _subresource(e.get("source_system", ""))
        specs.append({
            "name": f"mpe-{_slug(src)}"[:64],
            "targetPrivateLinkResourceId":
                "<VERIFY: /subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.Network/privateLinkServices/<pls>>",
            "targetSubresourceType": sub,
            "targetFQDNs": [f"<VERIFY: FQDN of {src} (e.g. {_ident(src)}.corp.example.com)>"],
            "requestMessage": f"Fabric private connection to {src}"[:140],
            "_port": port,
            "_source_system": e.get("source_system", ""),
        })
    return specs


def _create_script(specs: list[dict], workspace: str) -> str:
    lines = [
        "#!/usr/bin/env bash",
        "# Create Managed Private Endpoints (MPE) — outbound over Private Link (grounded MS Learn).",
        "# Prereq: an Azure Private Link Service fronts each source; approve the request afterwards in",
        "#   Azure portal → Private Link Service → Private endpoint connections.",
        "# Honest: every call is a commented VERIFY template — resource ids + FQDNs are tenant-specific.",
        "set -euo pipefail",
        'TOKEN="$(az account get-access-token --resource https://api.fabric.microsoft.com --query accessToken -o tsv)"',
        f'WORKSPACE_ID="<VERIFY: {workspace} workspace id>"',
        "",
    ]
    for s in specs:
        body = {k: v for k, v in s.items() if not k.startswith("_")}
        port = s["_port"]
        lines.append(f"# {s['name']}  (source system: {s['_source_system'] or 'n/a'}; open port {port or '<VERIFY>'} to the Fabric subnet)")
        lines.append("# curl -s -X POST \\")
        lines.append(f'#   "https://api.fabric.microsoft.com/v1/workspaces/$WORKSPACE_ID/managedPrivateEndpoints" \\')
        lines.append('#   -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \\')
        lines.append(f"#   -d '{json.dumps(body, ensure_ascii=False)}'")
        lines.append("")
    return "\n".join(lines) + "\n"


def _plan(bp: dict, specs: list[dict]) -> str:
    lines = [
        "# Secure connectivity for private sources (generated — grounded MS Learn 2026-07)", "",
        f"Private sources detected: **{len(specs)}** (mirror / on-prem / flagged private).", "",
        "| Source | System | Path | Subresource · port |", "|---|---|---|---|",
    ]
    priv = _private_sources(bp)
    for e, s in zip(priv, specs):
        lines.append(f"| {e.get('source')} | {e.get('source_system') or '—'} | Managed Private Endpoint | "
                     f"`{s['targetSubresourceType']}` · {s['_port'] or '<VERIFY>'} |")
    if not specs:
        lines.append("| — | — | (no private sources; all reach public endpoints) | — |")
    lines += [
        "",
        "## Two private paths (pick per source)",
        "- **Managed Private Endpoint (MPE)** — Fabric outbound over Private Link Service; for Spark / Data",
        "  Pipelines. The specs in `managed_private_endpoints.json` + `create_mpe.sh` follow this path.",
        "- **On-premises data gateway** — the classic path for sources that can't sit behind a Private Link",
        "  Service; install the gateway on a host that can reach the source, then bind the connection to it.",
        "",
        "## Setup order (MPE)",
        "1. Source owner: create an Azure **Private Link Service** fronting the source (or use Direct Connect",
        "   Preview for a static private IP); set auto-approval for the Fabric tenant if desired.",
        "2. Workspace admin: create the **MPE** (`create_mpe.sh` / the REST call) referencing the PLS resource id.",
        "3. Source owner: **approve** the request in Azure (Private Link Service → Private endpoint connections).",
        "4. Verify in Fabric → Settings → **Network security** that status is **Approved**; `nslookup` the FQDN",
        "   resolves to a private (10.x/172.x) IP.",
        "",
        "## Hardening rails (grounded)",
        "- Store credentials in **Azure Key Vault**, never hardcoded.",
        "- Enable **Outbound Access Protection (OAP)** so workloads reach only approved private endpoints.",
        "- Open only the source port to the Fabric subnet (1433 SQL, 1521 Oracle, …); monitor **Fabric audit logs**",
        "  for endpoint create/approve/delete; rotate credentials + review approvals periodically.",
    ]
    return "\n".join(lines) + "\n"


def emit_connectivity(bp: dict, stack: str = "fabric", workspace: str = "<workspace>",
                      lakehouse: str = "analytics_gold") -> dict[str, str]:
    """Return the secure-connectivity artifact set (path → content). The plan is always emitted; the MPE
    specs + create script are Fabric-specific and only when private sources exist."""
    specs = _mpe_specs(bp)
    out: dict[str, str] = {"connectivity/_CONNECTIVITY.md": _plan(bp, specs)}
    _note = gap_doc_for(bp, "connectivity", "Sichere Konnektivität")
    if _note:                       # fremder Stack: PrivateLink/NCC statt Managed Private Endpoint
        out["connectivity/_CONNECTIVITY.md"] = _note
    if stack == "fabric" and specs:
        payload = {"value": [{k: v for k, v in s.items() if not k.startswith("_")} for s in specs]}
        out["connectivity/managed_private_endpoints.json"] = (
            "// Managed Private Endpoints — POST /v1/workspaces/{ws}/managedPrivateEndpoints (grounded).\n"
            "// Resource ids + FQDNs are tenant-specific VERIFY placeholders; approve in Azure after create.\n"
            + json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
        out["connectivity/create_mpe.sh"] = _create_script(specs, workspace)
    # Die Snowflake-Bruecke erscheint, wenn die Lieferung Snowflake als Quelle ODER als Ziel kennt.
    # Sie gehoert in die Konnektivitaet und nicht in einen eigenen Emitter, weil ihre harten
    # Bedingungen Netz- und Regionsbedingungen sind — genau das Thema dieser Familie. Und sie
    # KOLLIDIERT mit dem Rest dieser Datei: Snowflake erreicht OneLake nur ueber das oeffentliche
    # Netz, waehrend `managed_private_endpoints.json` daneben private Pfade aufbaut.
    if stack == "fabric" and _mentions_snowflake(bp):
        gold = sorted({p.get("name") for p in
                       (((bp.get("medallion") or {}).get("gold") or {}).get("data_products") or [])
                       if p.get("name")})
        out["connectivity/snowflake_onelake_bridge.sql"] = _snowflake_bridge_sql(lakehouse, gold)
    return out


def _mentions_snowflake(bp: dict) -> bool:
    """Snowflake irgendwo in der Lieferung — als Quellsystem oder als Zielstack."""
    if str((bp.get("platform") or {}).get("stack", "")).lower() == "snowflake":
        return True
    return any("snowflake" in str(i.get("source_system", "")).lower()
               for i in (bp.get("ingestion") or []))

# --------------------------------------------------------------------------- Snowflake <-> OneLake
_SF_GROUNDED = "2026-07-30"   # MS Learn: fabric/onelake/onelake-iceberg-snowflake


def _snowflake_bridge_sql(lakehouse: str, gold_tables: list[str]) -> str:
    """Snowflake-seitiges DDL fuer die OneLake-Bruecke — beide Richtungen, gegroundet.

    Warum ueberhaupt: die haeufigste Kundenlage neben Fabric ist ein bestehender Snowflake-Bestand.
    „Iceberg fehlt" war als Luecke zu grob formuliert — der Weg ist vollstaendig dokumentiert und
    besteht aus zwei Snowflake-Objekten (`EXTERNAL VOLUME` + `CATALOG INTEGRATION`), nicht aus einem
    Fabric-Projekt.

    Was hier NICHT erfunden wird: Pfade, Tenant-ID und Metadaten-Dateinamen sind tenant-spezifisch und
    bleiben VERIFY. Der Consent-Schritt (`DESC EXTERNAL VOLUME` -> `AZURE_CONSENT_URL`) ist
    interaktiv und laesst sich nicht skripten; er steht als Schritt da, nicht als Befehl.
    """
    c = "--"
    lines = [
        f"{c} Snowflake <-> OneLake (generiert, gegroundet {_SF_GROUNDED}:",
        f"{c}   learn.microsoft.com/fabric/onelake/onelake-iceberg-snowflake)",
        f"{c}",
        f"{c} DREI BEDINGUNGEN, die vor dem ersten Statement stimmen muessen — alle dokumentiert:",
        f"{c}  1. REGION: die Fabric-Kapazitaet muss in derselben Azure-Region liegen wie das",
        f"{c}     Snowflake-Konto. Unterschiedliche Regionen => andere Kapazitaet noetig, kein Workaround.",
        f"{c}  2. NETZ: Snowflake erreicht OneLake ueber das OEFFENTLICHE Netz. Workspaces hinter",
        f"{c}     Private Link oder anderen Netzbeschraenkungen werden NICHT unterstuetzt — das",
        f"{c}     kollidiert mit unserem Konnektivitaets-Runbook, wenn dort Private Link gefordert ist.",
        f"{c}  3. TENANT-SCHALTER: Dienstprinzipale muessen Fabric-APIs UND OneLake-APIs aufrufen",
        f"{c}     duerfen (zwei getrennte Einstellungen).",
        f"{c}",
        f"{c} Schema-Hinweis: Snowflake verlangt `azure://` statt `https://` in STORAGE_BASE_URL.",
        "",
        f"{c} === Richtung 1: Snowflake SCHREIBT Iceberg nach OneLake =====================",
        "CREATE OR REPLACE EXTERNAL VOLUME onelake_write_exvol",
        "STORAGE_LOCATIONS =",
        "(",
        "    (",
        "        NAME = 'onelake_write_exvol'",
        "        STORAGE_PROVIDER = 'AZURE'",
        f"        STORAGE_BASE_URL = 'azure://<VERIFY: HTTPS-Pfad des Files-Ordners von "
        f"{lakehouse}, https:// -> azure://>/Files/icebergtables'",
        "        AZURE_TENANT_ID = '<VERIFY: Fabric-Tenant-ID>'",
        "    )",
        ");",
        "",
        f"{c} Consent — INTERAKTIV, nicht skriptbar: liefert AZURE_CONSENT_URL +",
        f"{c} AZURE_MULTI_TENANT_APP_NAME. Die URL im Browser oeffnen, zustimmen, danach der App in",
        f"{c} Fabric ueber 'Manage access' die Rolle **Contributor** im Workspace geben.",
        "DESC EXTERNAL VOLUME onelake_write_exvol;",
        "",
        f"{c} Beispiel-Tabelle (ersetzen durch die echten Spalten):",
        "CREATE OR REPLACE ICEBERG TABLE MYDATABASE.PUBLIC.<TABLE> (",
        "    <spalte> <typ>",
        ")",
        "EXTERNAL_VOLUME = 'onelake_write_exvol'",
        "CATALOG = 'SNOWFLAKE'",
        "BASE_LOCATION = '<TABLE>/';",
        "",
        f"{c} Danach in Fabric im Tables-Bereich desselben Lakehouse einen Shortcut auf die",
        f"{c} Iceberg-Tabelle anlegen — sie erscheint dann fuer alle Fabric-Workloads als Delta.",
        "",
        f"{c} === Richtung 2: Snowflake LIEST unser Gold (Delta, als Iceberg virtualisiert) =====",
        "CREATE OR REPLACE EXTERNAL VOLUME onelake_read_exvol",
        "STORAGE_LOCATIONS =",
        "(",
        "    (",
        "        NAME = 'onelake_read_exvol'",
        "        STORAGE_PROVIDER = 'AZURE'",
        f"        STORAGE_BASE_URL = 'azure://<VERIFY: Pfad des Datenelements, z. B. "
        f"onelake.dfs.fabric.microsoft.com/<workspace-guid>/<item-guid>>/Tables/'",
        "        AZURE_TENANT_ID = '<VERIFY: Fabric-Tenant-ID>'",
        "    )",
        ")",
        f"ALLOW_WRITES = false;   {c} lesend — das Gold gehoert der Fabric-Seite",
        "",
        "DESC EXTERNAL VOLUME onelake_read_exvol;",
        "",
        f"{c} Einmal je Konto: Snowflake braucht das, um bestehende Iceberg-Tabellen zu referenzieren.",
        "CREATE CATALOG INTEGRATION onelake_catalog_integration",
        "CATALOG_SOURCE = OBJECT_STORE",
        "TABLE_FORMAT = ICEBERG",
        "ENABLED = TRUE;",
        "",
    ]
    for tbl in gold_tables:
        lines += [
            f"CREATE OR REPLACE ICEBERG TABLE MYDATABASE.PUBLIC.{tbl.upper()}",
            "EXTERNAL_VOLUME = 'onelake_read_exvol'",
            "CATALOG = onelake_catalog_integration",
            f"METADATA_FILE_PATH = '<VERIFY: dbo/{tbl}/metadata/<n>.metadata.json — die JEWEILS "
            f"NEUESTE Metadatendatei>';",
            "",
        ]
    lines += [
        f"{c} Die Metadaten-Datei ist ein Zeitpunkt, keine Sicht: nach jeder Aenderung an der",
        f"{c} Delta-Tabelle zeigt ein neuer *.metadata.json den aktuellen Stand. Wer den Pfad einmal",
        f"{c} fest verdrahtet, liest still einen alten Stand weiter — das ist die Falle dieser Richtung.",
    ]
    return "\n".join(lines) + "\n"
