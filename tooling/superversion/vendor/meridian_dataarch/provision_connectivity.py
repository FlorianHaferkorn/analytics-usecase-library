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


def emit_connectivity(bp: dict, stack: str = "fabric", workspace: str = "<workspace>") -> dict[str, str]:
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
    return out
