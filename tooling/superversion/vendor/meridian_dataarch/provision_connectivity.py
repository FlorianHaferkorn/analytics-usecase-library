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
        "- Enable **Outbound Access Protection (OAP)** so workloads reach only approved destinations —",
        "  the procedure, its three prerequisites and what it collides with are the section below.",
        "- Open only the source port to the Fabric subnet (1433 SQL, 1521 Oracle, …); monitor **Fabric audit logs**",
        "  for endpoint create/approve/delete; rotate credentials + review approvals periodically.",
        "",
        *_network_stance_section(bp),
        *_gateway_section(bp),
        *_oap_section(bp),
    ]
    return "\n".join(lines) + "\n"


#: Der Politik-Rumpf, den `PUT /v1/workspaces/{id}/networking/communicationPolicy` erwartet.
#: `inbound` steht ausdruecklich mit drin, obwohl nur `outbound` geaendert werden soll: MS sagt
#: dazu „Also specify the inbound value if needed so it isn't overwritten by the default value
#: (Allow)". Ein PUT, der `inbound` weglaesst, setzt es also still zurueck — die Sorte Fehler, die
#: erst auffaellt, wenn jemand den eingehenden Schutz sucht und ihn nicht mehr findet.
OAP_POLICY_PATH = "connectivity/outbound_access_protection.json"


def _oap_policy_json() -> str:
    """Der Politik-Rumpf als **gueltiges JSON** — Kommentar in `_note`, nicht in `//`-Zeilen.

    Warum das hier ausdruecklich steht: die Nachbardatei `managed_private_endpoints.json` trug
    ihren Hinweis bis 16.08.2026 als `//`-Kopf und war damit kein JSON. Aufgefallen ist es nie,
    weil sie nur bei privaten Quellen emittiert wird und die Testvorlage keine hat — der Waechter
    `test_every_emitted_json_is_parseable_json` lief also an ihr vorbei. Ein Rumpf, den jemand in
    ein `PUT` kippt, muss parsen; `_note` ist der Weg, den `capacity_throttling_alert.json` in
    dieser Lieferung schon geht.
    """
    politik = {
        "_note": (
            "PUT /v1/workspaces/{workspaceId}/networking/communicationPolicy (Workspaces - Set "
            "Network Communication Policy, checked 2026-08-16). Remove this _note before sending. "
            "`inbound` is in the body on purpose even though only `outbound` is meant: MS states "
            "that an inbound value you don't send is overwritten with the default (Allow), so "
            "shortening this body silently switches inbound protection off. Set "
            "`inbound.publicAccessRules.defaultAction` to Deny where the workspace should also be "
            "protected inbound — that is its own decision, not a side effect of this file."),
        "inbound": {"publicAccessRules": {"defaultAction": "Allow"}},
        "outbound": {"publicAccessRules": {"defaultAction": "Deny"}},
    }
    return json.dumps(politik, indent=2, ensure_ascii=False) + "\n"


def _oap_section(bp: dict) -> list[str]:
    """Outbound Access Protection: Verfahren, Vorbedingungen und die Kollisionen mit DIESER Lieferung.

    Englisch, weil `_CONNECTIVITY.md` englisch ist. Zwei Sprachen in einem Dokument, das ein Kunde
    am Stueck liest, sind schlimmer als jede der beiden.

    Bis 16.08.2026 war OAP in diesem Dokument eine Zeile („enable OAP") — eine Empfehlung ohne
    Vorbedingungen, ohne Freigabeweg und ohne die Stellen, an denen sie mit dem kollidiert, was
    dieselbe Lieferung emittiert. Genau daran ist sie teuer: OAP laesst sich auf einem Workspace
    mit nicht unterstuetzten Artefakten **gar nicht** einschalten, und Power-BI-Berichte gehoeren
    zu den nicht unterstuetzten. Ein Kunde, der der alten Zeile folgt, findet das an dem Tag
    heraus, an dem der Schalter nicht umgeht.

    Alle Angaben gegen learn.microsoft.com geprueft am 16.08.2026: `security/workspace-outbound-
    access-protection-overview` (Freigabewege je Workload, Grenzen), `-set-up` (Vorbedingungen,
    REST-Weg, Git-Schalter) und `onelake/onelake-manage-outbound-access` (die Kopier-Grenze).
    """
    shares = bool(bp.get("sharing"))
    return [
        "## Outbound Access Protection (OAP) — per workspace, with three prerequisites", "",
        "OAP blocks **every** outbound connection from the workspace, and you open it again "
        "selectively afterwards. That order is the feature, not a recommendation: there is no mode "
        "in which you allow first and block later.", "",
        "**Before flipping it — three things that otherwise surface at the switch:**",
        "1. The tenant setting **Configure workspace-level outbound network rules** is off out of the "
        "box and is set by a **Fabric tenant admin**. A workspace admin cannot set it.",
        "2. The workspace sits on an **F SKU**. No other capacity type is supported — **and F SKU "
        "trials explicitly are not either.** On a trial, OAP cannot be demonstrated at all.",
        "3. The **`Microsoft.Network`** resource provider is **re-registered** on the subscription "
        "(Azure portal → Subscriptions → Settings → Resource providers → Microsoft.Network → Re-register).",
        "",
        "The switch itself is a **workspace admin** action (Workspace settings → Network Security → "
        "*Block outbound public access*), or it is driven — the request body is in "
        f"`{OAP_POLICY_PATH.split('/')[-1]}`, sent as `PUT /v1/workspaces/{{id}}/networking/"
        "communicationPolicy`. Allow up to **15 minutes** for it to take effect.", "",
        "### Opening it again — two mechanisms, not interchangeable", "",
        "| Workload | Mechanism | Items |", "|---|---|---|",
        "| Data Engineering | managed private endpoints | Lakehouses, Notebooks, Spark Job "
        "Definitions, Environments |",
        "| OneLake | managed private endpoints | OneLake shortcuts |",
        "| Data Factory | data connection rules | Dataflows Gen2 (with CI/CD), Pipelines, Copy Jobs |",
        "| Mirrored databases · Real-Time Intelligence · Fabric IQ · Power BI | data connection "
        "rules | Eventstream, Eventhouse, Activator, semantic models, … |",
        "| Data Science · Data Warehouse | **none** | no allow-list mechanism exists for these |",
        "",
        "The last row is not a gap in the table. MS gives the mechanism for Data Science and Data "
        "Warehouse as *not applicable* — looking for an exception there means looking for something "
        "that does not exist.", "",
        "### What this collides with in this delivery", "",
        "| Collision | In the way? | Way around it |", "|---|---|---|",
        "| **Power BI reports in the workspace** | Yes, and hard: apart from semantic models no Power "
        "BI item supports OAP. A workspace holding one cannot be protected, and while OAP is on none "
        "can be created | put reports in their own unprotected workspace — the cut in "
        "`workspaces.json` decides this, not the switch |",
        "| **Git integration (`cicd/`)** | Yes: with OAP on, Git is blocked by default | turn on "
        "*Allow Git integration* in the same panel. Without that one step the delivery chain breaks "
        "and the error points at Git instead of at OAP |",
        ("| **External data sharing** | Yes — this delivery declares shares, and OAP is not compatible "
         "with Fabric external data sharing | one of the two decisions has to give; cross-tenant "
         "allow lists do not exist |") if shares else
        ("| **External data sharing** | No — this delivery declares none | it stays that way only "
         "while none is added: OAP and Fabric external data sharing are mutually exclusive |"),
        "| **OneLake Diagnostics** | Partly | only with a lakehouse in the **same** workspace |",
        "| **Warehouse paths from notebooks** | Yes, for `dbo` file paths | query it over T-SQL "
        "instead of over the path |",
        "",
        "### The limit most easily mistaken for protection", "",
        "OAP restricts **outbound calls**. Where the workspace is the **source** of a copy to the "
        "outside, no outbound call is made and OAP does not apply (MS Learn, *Copying data between "
        "Azure Storage and OneLake*: \"outbound access protection does not restrict your workspace "
        "from being the source of a copy operation\"). Only inbound protection covers that, and "
        "inbound is a separate decision.", "",
        "### Evidence", "",
        "`Workspaces - List Networking Communication Policies` (admin API) returns the inbound and "
        "outbound rules per workspace. That turns \"is OAP on everywhere it should be?\" into a query "
        "rather than a click-through. Caller: Fabric admin or service principal, permission "
        "`Tenant.Read.All`.", "",
        "> With private links enabled at workspace or tenant level, the portal cannot configure data "
        "connection rules at all — the *Outbound Gateway Rules* REST API is the only way in.",
    ]


GATEWAY_OPS_PATH = "connectivity/gateway_cluster_ops.ps1"


def _network_stance_section(bp: dict) -> list[str]:
    """Which network stance this delivery assumes, and what the other one would cost.

    Bis 16.08.2026 beschrieb dieses Dokument vier Wege nebeneinander und waehlte keinen. Eine
    Optionenliste ist keine Entscheidung, und diese hier ist die am schwersten zu drehende: Private
    Link schaltet einzelne Fabric-Faehigkeiten ab, und rueckwaerts heisst „die Anbindung aller
    Quellen neu bauen". Die Entscheidung selbst steht jetzt als `PLAT-NET` in der
    Entscheidungsvorlage — hier steht, was sie kostet.

    Die Tabelle nennt bewusst nur Kollisionen mit dem, was **diese** Lieferung emittiert. Die
    vollstaendige Grenzenliste steht bei MS; eine Abschrift davon waere eine zweite Heimat, die als
    naechstes veraltet.

    Geprueft 16.08.2026: `fabric/security/security-private-links-overview`,
    `security-trusted-workspace-access`, `security-workspace-level-firewall-overview`.
    """
    lokal = _private_sources(bp)
    return [
        "## The network stance this delivery assumes", "",
        "**Public endpoints plus Trusted Workspace Access.** Private Link is not built pre-emptively. "
        "That is a decision, not an omission — it is recorded as `PLAT-NET` in the decision template, "
        "and the customer overrides it there. Overriding is the normal case here, not the exception: "
        "a data-protection or group-IT rule decides this, we do not.", "",
        "Trusted Workspace Access lets a storage account keep its firewall closed and still be read "
        "from named workspaces, over the Microsoft backbone. Two conditions that are easy to miss:",
        "- It needs a **purchased F SKU**. **Trial capacities are not supported** — and a workspace "
        "moved to a trial or non-F capacity stops working **after about an hour**, which reads like an "
        "outage rather than a licensing effect.",
        "- It covers OneLake shortcuts, pipelines, semantic models, the T-SQL `COPY` statement and "
        "AzCopy. **It does not cover Spark.** Notebooks reaching a firewalled storage account need a "
        "managed private endpoint — which is why this delivery emits both mechanisms and not one.",
        "",
        "> Connections to firewall-enabled storage accounts show up as **Offline** in *Manage "
        "connections and gateways*. That is documented behaviour, not a fault; do not go looking for "
        "the fault.", "",
        "### What Private Link would cost this delivery", "",
        "Not the general limitation list — only the things this delivery actually emits or assumes.", "",
        "| What we deliver | Under tenant-level Private Link |", "|---|---|",
        ("| On-premises data gateway (this delivery has "
         f"**{len(lokal)} source(s)** behind a firewall) | **Fails to register.** The gateway is not "
         "supported with Private Link enabled; the VNet data gateway is the replacement, and that is a "
         "different procurement |") if lokal else
        ("| On-premises data gateway (none in this delivery today) | would fail to register — the "
         "gateway is not supported with Private Link enabled. The VNet data gateway is the "
         "replacement |"),
        "| Capacity Metrics app (`BK-B02`) | not supported — the app we point the capacity admin at "
        "stops being an option |",
        "| Copilot / Data Agent items | Copilot is not supported; Data Agents lose Kusto, semantic "
        "models and mirrored sources as data sources |",
        "| Report delivery (subscriptions, PDF/PowerPoint export, Publish to Web) | all three "
        "unsupported |",
        "| Usage metrics | partial data only — Report Open events, no page views. With **Block Public "
        "Internet Access** on, the refresh fails outright |",
        "| Cross-tenant shortcuts and OneLake data sharing | not supported over Private Link — the "
        "same collision Outbound Access Protection has |",
        "| Spark starter pools | disabled once a managed VNet exists; jobs run on custom pools created "
        "at submission time, so first-job latency rises |",
        "| Warehouse copy in pipelines | copying data from or into a warehouse is not possible |",
        "",
        "Two limits that decide the *timing* rather than the design: a newly created capacity does not "
        "support Private Link until its endpoint reaches the private DNS zone, which can take up to "
        "**24 hours**; and **trial capacity does not work over Private Link at all**. A proof of "
        "concept on a trial cannot demonstrate this stance.", "",
        "If the requirement is real but narrower than the whole tenant, the two smaller instruments "
        "are **workspace-level private links** (only the workspaces that need it) and **IP firewall "
        "rules** (up to 256 per workspace, and these do run on trial capacity).", "",
    ]


def _gateway_section(bp: dict) -> list[str]:
    """Das On-premises-Data-Gateway als Betriebsgegenstand, nicht als Installationshinweis.

    Der Punkt ist nicht „ein Gateway installieren", sondern dass ein einzelner Knoten ein
    Einzelausfallpunkt fuer jede lokale Quelle ist — und zwar einer, der beim naechsten
    Windows-Neustart zuschlaegt. Cluster, Version und Wiederherstellungsschluessel sind die drei
    Dinge, die daran haengen, und keines davon merkt man rechtzeitig.

    Geprueft 16.08.2026: `data-integration/gateway/service-gateway-high-availability-clusters`,
    `service-gateway-update`, `service-gateway-monthly-updates`, `service-gateway-migrate`,
    `service-gateway-onprem-faq`, `powershell/module/datagateway`.
    """
    if not _private_sources(bp):
        return []
    return [
        "## The gateway is a cluster, or it is a single point of failure", "",
        "One gateway node is a single point of failure for every on-premises source in this delivery. "
        "It is also the kind that arrives on a Tuesday, when the host reboots for patches.", "",
        "**Two nodes minimum, on separate hosts.** A cluster takes up to 10 members. The cloud service "
        "always uses the primary and falls back to the next available member.", "",
        "| Setting | Value | Why this one |", "|---|---|---|",
        "| Members | at least 2, separate hosts | one node reboots and every on-prem source is dark |",
        "| Version | identical across all members | mixed versions cause failures that depend on which "
        "member took the query — the hardest kind to reproduce |",
        "| Update cadence | monthly, rolling | Microsoft supports the **last six releases**, so six "
        "months is the whole runway |",
        "| Load balancing | `-LoadBalancingSelectorType Failover` | see the naming trap below |",
        "| Recovery key | in the customer's vault, not ours | Microsoft has no copy and cannot "
        "retrieve it |",
        "",
        "### The naming trap in load balancing", "",
        "`Failover` does **not** mean \"use the secondary only when the primary is down\". Microsoft's "
        "own parameter documentation reads `failover = roundrobin`. Distribution across members is what "
        "you get; the value that looks like distribution (`Random`) is the random pick. Read the "
        "parameter as a label, not as a description.", "",
        "> Disable or remove an offline member. Leaving it in the cluster means queries are tried on it "
        "first and fail over afterwards, so the cluster gets slower than a single node would be.", "",
        "### Updating without an outage", "",
        "The order matters, and `gateway_cluster_ops.ps1` follows it: disable one member, wait for its "
        "work to drain (**30 minutes** covers most workloads, longer where long-running jobs are "
        "normal), update it, enable it, then the next one. Updating both at once is how a cluster "
        "becomes a single node for the duration.", "",
        "Three preconditions that stop the script rather than the plan:",
        "- Programmatic updates need the **November 2025 baseline (3000.294.7)** or later already "
        "installed. Below that, the first update is manual.",
        "- **10 GB** free disk on the host, or the update fails partway.",
        "- Fabric pipelines need **3000.214.2** or later at all.",
        "",
        "**Dated, and close:** builds released before May 2026 lose interactive sign-in as Microsoft's "
        "identity-platform change rolls out, with enforcement completing across all tenants by "
        "**31 August 2026**. A gateway on an older build stops being manageable, not just outdated.", "",
        "### The recovery key, and the one case it does not save", "",
        "The recovery key is set by the admin at install time. Microsoft has no access to it and "
        "cannot retrieve it. It is required to migrate the gateway to another machine, to restore it, "
        "to take it over, to add a member to the cluster and to change the service account. Without "
        "it, a gateway is not recoverable after host loss — it is rebuildable, which is a different "
        "amount of work and a different amount of downtime.", "",
        "The exception is worth knowing before someone tidies up: **a gateway cluster deleted in the "
        "cloud service cannot be restored at all.** The recovery key does not help there.", "",
        "> A planned migration takes 10–15 minutes and belongs in a maintenance window. Refreshes that "
        "start during it are likely to fail.", "",
        "> Dataflow Gen2 keeps one dependency on the primary member: creating or editing connections "
        "needs it up. The cluster removes the single point of failure for queries, not for that.", "",
    ]


def _gateway_ops_ps1() -> str:
    """Der rollende Cluster-Update-Lauf als Skript.

    Warum ueberhaupt ein Skript: MS beschreibt die Reihenfolge (deaktivieren, leerlaufen lassen,
    aktualisieren, aktivieren) als Fliesstext, und genau diese Reihenfolge ist das, was in der Hektik
    abgekuerzt wird. Ein Lauf, der die Wartezeit selbst einhaelt, ist schwerer abzukuerzen als ein
    Absatz.

    Und die Grenze gleich mit: das `DataGateway`-Modul hat **kein** Cmdlet zum Deaktivieren eines
    Mitglieds (Stand 16.08.2026 — der Modulindex fuehrt Add/Get/Remove/Restore/Set/Update, kein
    Disable). Das Deaktivieren bleibt Handarbeit im Portal. Das Skript sagt das an der Stelle, an der
    es haelt, statt so zu tun, als sei der Lauf vollstaendig automatisch.
    """
    return """<#
    gateway_cluster_ops.ps1 — das On-premises-Data-Gateway-Cluster in der dokumentierten Reihenfolge
    aktualisieren, und den Lastverteilungs-Modus setzen.

    Voraussetzungen (alle 16.08.2026 gegen learn.microsoft.com geprueft):
      * PowerShell 7 oder hoeher, Modul `DataGateway` (`Install-Module -Name DataGateway`).
      * Gateway-Admin-Rechte. Ohne sie schlaegt der Update-Aufruf fehl, nicht die Anmeldung.
      * Jedes Mitglied bereits auf **3000.294.7** (Nov 2025) oder hoeher — darunter gibt es
        `Update-DataGatewayClusterMember` nicht, und das erste Update ist Handarbeit.
      * 10 GB freier Plattenplatz je Wirt.

    Was das Skript NICHT kann: ein Mitglied deaktivieren. Das `DataGateway`-Modul hat dafuer kein
    Cmdlet. Der Lauf haelt an der Stelle an und sagt, was im Portal zu tun ist — das ist ehrlicher
    als ein Lauf, der die Wartezeit ueberspringt, weil er sie nicht erzwingen kann.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][guid] $GatewayClusterId,
    # 30 Minuten deckt laut MS die meisten Lasten ab. Wo lange Jobs normal sind, hochsetzen —
    # die Zahl ist eine Aussage ueber IHRE Jobs, nicht ueber das Gateway.
    [int] $DrainMinutes = 30,
    # `Failover` heisst laut MS-Parameterdoku round-robin. Nicht der Name ist gemeint, sondern die
    # Verteilung ueber alle aktiven Mitglieder.
    [ValidateSet('Failover', 'Random')][string] $LoadBalancing = 'Failover',
    [switch] $WhatIfOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Import-Module DataGateway
Connect-DataGatewayServiceAccount | Out-Null

$cluster = Get-DataGatewayCluster -GatewayClusterId $GatewayClusterId
if (-not $cluster) { throw "Cluster $GatewayClusterId nicht gefunden oder keine Admin-Rechte darauf." }

$members = @($cluster.MemberGateways)
Write-Host ("Cluster '{0}': {1} Mitglied(er)." -f $cluster.Name, $members.Count)
if ($members.Count -lt 2) {
    # Kein Abbruch: ein Einzelknoten ist ein hingenommenes Risiko, keine Fehlbedienung. Aber er
    # gehoert benannt, sonst steht er nie im Risikoregister.
    Write-Warning ("Einzelknoten. Jede lokale Quelle haengt an diesem einen Wirt — und ein Update " +
                   "ist eine Ausfallzeit, kein rollender Lauf.")
}

$versionen = $members | Select-Object -ExpandProperty Version -Unique
if ($versionen.Count -gt 1) {
    Write-Warning ("Mitglieder laufen auf verschiedenen Versionen ({0}). Ein Fehler haengt dann " +
                   "davon ab, welches Mitglied die Abfrage bekam — die schwerste Sorte." -f
                   ($versionen -join ', '))
}

Write-Host ("Lastverteilung -> {0} (laut MS-Doku: failover = roundrobin)." -f $LoadBalancing)
if (-not $WhatIfOnly) {
    Set-DataGatewayCluster -GatewayClusterId $GatewayClusterId -LoadBalancingSelectorType $LoadBalancing
}

$verfuegbar = Get-DataGatewayAvailableUpdates -GatewayClusterId $GatewayClusterId
if (-not $verfuegbar) {
    Write-Host "Keine Aktualisierung verfuegbar. Ende."
    return
}

foreach ($m in $members) {
    Write-Host ("--- Mitglied {0} ({1}) ---" -f $m.Name, $m.Version)
    Write-Host ("1. Im Portal deaktivieren: Manage connections and gateways -> On-premises data " +
                "gateways -> {0} -> Disable." -f $m.Name)
    Write-Host ("   Dafuer gibt es kein Cmdlet. Ohne diesen Schritt schickt der Lastverteiler " +
                "waehrend des Updates weiter Abfragen auf dieses Mitglied.")
    if ($WhatIfOnly) { continue }
    Read-Host  "   Wenn deaktiviert: Eingabetaste"
    Write-Host ("2. {0} Minuten leerlaufen lassen." -f $DrainMinutes)
    Start-Sleep -Seconds ($DrainMinutes * 60)
    Write-Host "3. Aktualisieren."
    Update-DataGatewayClusterMember -GatewayClusterId $GatewayClusterId -MemberGatewayId $m.Id
    do {
        Start-Sleep -Seconds 30
        $stand = Update-DataGatewayClusterMember -GatewayClusterId $GatewayClusterId `
                                                 -MemberGatewayId $m.Id -CheckStatus
        Write-Host ("   Stand: {0}" -f $stand)
    } while ("$stand" -match 'InProgress|Running')
    Write-Host "4. Im Portal wieder aktivieren, dann Eingabetaste fuer das naechste Mitglied."
    Read-Host  "   Eingabetaste"
}

Write-Host "Fertig. Gegenprobe: Get-DataGatewayClusterStatus -GatewayClusterId $GatewayClusterId"
"""


def emit_connectivity(bp: dict, stack: str = "fabric", workspace: str = "<workspace>",
                      lakehouse: str = "analytics_gold") -> dict[str, str]:
    """Return the secure-connectivity artifact set (path → content). The plan is always emitted; the MPE
    specs + create script are Fabric-specific and only when private sources exist."""
    specs = _mpe_specs(bp)
    out: dict[str, str] = {"connectivity/_CONNECTIVITY.md": _plan(bp, specs)}
    _note = gap_doc_for(bp, "connectivity", "Sichere Konnektivität")
    if _note:                       # fremder Stack: PrivateLink/NCC statt Managed Private Endpoint
        out["connectivity/_CONNECTIVITY.md"] = _note
    if stack == "fabric" and not _note:
        # Unabhaengig von privaten Quellen: OAP schuetzt den Workspace, nicht die Quelle. Eine
        # Lieferung ganz ohne private Quelle braucht ihn genauso — sie hat nur keine MPEs.
        out[OAP_POLICY_PATH] = _oap_policy_json()
        # Anders als OAP haengt das Gateway an einer Bedingung der Lieferung: ohne Quelle
        # hinter der Firewall gibt es kein Gateway zu betreiben. Ein Betriebsskript fuer ein
        # Geraet, das niemand hat, ist eine Anweisung ins Leere.
        if _private_sources(bp):
            out[GATEWAY_OPS_PATH] = _gateway_ops_ps1()
    if stack == "fabric" and specs:
        # `_note` statt eines `//`-Kopfes: mit dem Kopf war diese Datei kein JSON, und weil sie nur
        # bei privaten Quellen entsteht, hat der Waechter sie nie zu Gesicht bekommen (gefunden
        # 16.08.2026 an der Schwesterdatei, die immer entsteht). Der Schluessel faellt beim Senden
        # weg — dieselbe Form wie in `capacity_throttling_alert.json`.
        payload = {"_note": ("Managed Private Endpoints — POST /v1/workspaces/{ws}/"
                             "managedPrivateEndpoints (grounded). Resource ids + FQDNs are "
                             "tenant-specific VERIFY placeholders; approve in Azure after create."),
                   "value": [{k: v for k, v in s.items() if not k.startswith("_")} for s in specs]}
        out["connectivity/managed_private_endpoints.json"] = (
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
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
    # Databricks-Zugriff auf OneLake gehoert auf DIESEN Pfad (Fabric ist das Ziel, OneLake der
    # Speicher) — nicht in die Fremdstack-Notiz, wo Databricks selbst die Zielplattform waere und
    # OneLake gar nicht vorkommt.
    if stack == "fabric" and _mentions_databricks(bp):
        out["connectivity/databricks_onelake_access.py"] = _databricks_onelake_notebook(lakehouse)
    return out


def _mentions_databricks(bp: dict) -> bool:
    """Databricks irgendwo in der Lieferung — als Quellsystem oder als Zielstack."""
    if str((bp.get("platform") or {}).get("stack", "")).lower() == "databricks":
        return True
    return any("databricks" in str(i.get("source_system", "")).lower()
               for i in (bp.get("ingestion") or []))


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


# ------------------------------------------------------------------------- Databricks <-> OneLake
_DBX_GROUNDED = "2026-07-30"   # MS Learn: fabric/onelake/onelake-azure-databricks


def _databricks_onelake_notebook(lakehouse: str) -> str:
    """Databricks-seitiges Notebook-Geruest fuer den OneLake-Zugriff — beide Compute-Typen.

    Warum das hier steht und nicht in der Fremdstack-Notiz: dort ist Databricks die ZIELplattform,
    OneLake kommt gar nicht vor. Hier ist Fabric das Ziel und Databricks der Bestand, der darauf
    zugreift — das ist eine Fabric-Konnektivitaetsfrage.

    Der teure Fehler, den dieses Artefakt verhindert: das Cluster-Rezept (`fs.azure.*`) auf
    Serverless zu uebertragen. Serverless erlaubt nur eine Teilmenge der Spark-Properties und
    quittiert den Rest mit `CONFIG_NOT_AVAILABLE` — dokumentiert, und nicht Azure-spezifisch
    (AWS und GCP verhalten sich identisch). Der dokumentierte Weg dort ist MSAL-Token +
    `deltalake` mit `use_fabric_endpoint`.

    Was NICHT erfunden wird: Workspace-/Lakehouse-Ids, Scope- und Key-Namen bleiben VERIFY.
    """
    c = "#"
    return "\n".join([
        f'"""Databricks -> OneLake (generiert, gegroundet {_DBX_GROUNDED}:',
        "learn.microsoft.com/fabric/onelake/onelake-azure-databricks)",
        "",
        "VORBEDINGUNGEN (dokumentiert, alle vier noetig):",
        "  1. Fabric-Workspace + Lakehouse vorhanden.",
        "  2. Databricks-Workspace im **Premium**-Tarif.",
        "  3. Dienstprinzipal mit mindestens der Workspace-Rolle **Contributor** in Fabric.",
        "  4. Databricks Secrets oder Azure Key Vault fuer die Zugangsdaten — nie im Notebook.",
        "",
        "WELCHER ZWEIG GILT: der Compute-Typ entscheidet, nicht die Vorliebe.",
        '  Standard-/Job-Cluster -> Spark-ABFS-Treiber mit `fs.azure.*`-OAuth-Konfiguration.',
        "  Serverless            -> `fs.azure.*` ist NICHT setzbar (CONFIG_NOT_AVAILABLE),",
        "                           stattdessen MSAL-Token + `deltalake`.",
        '"""',
        "",
        f"{c} --- Pfadformat (beide Zweige) ------------------------------------------------",
        f"{c} abfss://<workspace>@onelake.dfs.fabric.microsoft.com/<lakehouse>.lakehouse/Files/<pfad>",
        f"{c} abfss://<workspace>@onelake.dfs.fabric.microsoft.com/<lakehouse>.lakehouse/Tables/<pfad>",
        f"{c} Ids oder Namen sind beide erlaubt; bei Namen keine Sonderzeichen/Leerzeichen.",
        "",
        'WORKSPACE = "<VERIFY: Fabric-Workspace-Name oder -Id>"',
        f'LAKEHOUSE = "{lakehouse}"',
        'SCOPE     = "<VERIFY: Databricks-Secret-Scope>"',
        "",
        "",
        f"{c} === Zweig A: Standard- oder Job-Cluster ======================================",
        "def configure_standard_cluster(spark, dbutils):",
        '    tenant_id = dbutils.secrets.get(scope=SCOPE, key="<VERIFY: tenant-id-key>")',
        '    client_id = dbutils.secrets.get(scope=SCOPE, key="<VERIFY: client-id-key>")',
        '    client_secret = dbutils.secrets.get(scope=SCOPE, key="<VERIFY: client-secret-key>")',
        '    spark.conf.set("fs.azure.account.auth.type", "OAuth")',
        '    spark.conf.set("fs.azure.account.oauth.provider.type",',
        '                   "org.apache.hadoop.fs.azurebfs.oauth2.ClientCredsTokenProvider")',
        '    spark.conf.set("fs.azure.account.oauth2.client.id", client_id)',
        '    spark.conf.set("fs.azure.account.oauth2.client.secret", client_secret)',
        '    spark.conf.set("fs.azure.account.oauth2.client.endpoint",',
        '                   f"https://login.microsoftonline.com/{tenant_id}/oauth2/token")',
        "",
        "",
        f"{c} === Zweig B: Serverless =====================================================",
        f"{c} Hier NICHT Zweig A kopieren: jedes `fs.azure.*` scheitert mit CONFIG_NOT_AVAILABLE.",
        "def onelake_token(dbutils):",
        "    from msal import ConfidentialClientApplication",
        "",
        '    tenant_id = dbutils.secrets.get(scope=SCOPE, key="<VERIFY: tenant-id-key>")',
        '    client_id = dbutils.secrets.get(scope=SCOPE, key="<VERIFY: client-id-key>")',
        '    client_secret = dbutils.secrets.get(scope=SCOPE, key="<VERIFY: client-secret-key>")',
        "    app = ConfidentialClientApplication(",
        '        client_id, authority=f"https://login.microsoftonline.com/{tenant_id}",',
        "        client_credential=client_secret)",
        '    result = app.acquire_token_for_client(',
        '        scopes=["https://onelake.fabric.microsoft.com/.default"])',
        '    if "access_token" not in result:',
        '        raise RuntimeError(f"Token fehlgeschlagen: {result.get(\'error_description\', result)}")',
        '    return result["access_token"]',
        "",
        "",
        "def read_table_serverless(dbutils, table):",
        "    from deltalake import DeltaTable",
        "",
        '    uri = (f"abfss://{WORKSPACE}@onelake.dfs.fabric.microsoft.com/"',
        '           f"{LAKEHOUSE}.lakehouse/Tables/{table}")',
        "    dt = DeltaTable(uri, storage_options={",
        '        "bearer_token": onelake_token(dbutils), "use_fabric_endpoint": "true"})',
        "    return dt.to_pandas()",
        "",
        "",
        "def write_table_serverless(dbutils, df, table):",
        "    from deltalake import write_deltalake",
        "",
        '    uri = (f"abfss://{WORKSPACE}@onelake.dfs.fabric.microsoft.com/"',
        '           f"{LAKEHOUSE}.lakehouse/Tables/{table}")',
        '    write_deltalake(uri, df, mode="overwrite", storage_options={',
        '        "bearer_token": onelake_token(dbutils), "use_fabric_endpoint": "true"})',
        "",
        "",
        f"{c} === Entwurfsregeln (dokumentiert) ===========================================",
        f"{c} 1. EIN Schreiber pro Tabellenpfad. Mehrere Engines oder Runtime-Staende auf denselben",
        f"{c}    Pfad erzeugen Konflikte — das ist die Regel, die spaeter niemand mehr zurueckbaut.",
        f"{c} 2. Zugangsdaten ausschliesslich ueber Secret-Management.",
        f"{c} 3. Wenn nur GELESEN wird: OneLake-Shortcut statt physischer Kopie.",
        f"{c} 4. Soll der oeffentliche Netzzugang zu OneLake gesperrt werden, ist der Weg NICHT",
        f"{c}    'entweder offen oder gar nicht': die Ressourcen-Id des Databricks-Access-Connectors",
        f"{c}    in die **Resource Instance Rules** des Workspace aufnehmen (Workspace settings ->",
        f"{c}    Inbound networking -> auf ausgewaehlte Netze und freigegebene Ressourcen",
        f"{c}    beschraenken, volle ARM-Ressourcen-Id angeben). OneLake prueft dann je Anfrage die",
        f"{c}    verwaltete Identitaet.",
        "",
    ]) + "\n"
