"""admin_settings — the Fabric admin/tenant/capacity/workspace settings a customer delivery needs, as a
cited catalog + a capability-keyed planner. Readiness-Gate (sibling of ``capacity_recommend.py``).

The directive: *define the admin settings so one can, within a day, set what one needs how.* This module
is the machine-readable **definition**. Given the set of **capabilities** a delivery actually uses
(agnostic, feature-keyed — not source- or pattern-specific), ``required_settings`` returns exactly the
settings that gate it, each carrying: the exact portal name + section, its **scope** (tenant / capacity /
workspace), **default**, **who** can set it, the **target** value for the delivery, and — the crux of
"within a day" — whether it is **automatable** via the Fabric *Update Tenant Setting* Admin REST API
(preview) / ``sempy`` or needs a **human** admin (capacity-admin portal action, or an RBAC grant a
privileged human must perform). ``settability_summary`` splits the plan into "scriptable" vs "needs a
human" so the one-day setup is honest about what can be automated.

Honest by construction: settings MS docs do not pin (default state, or whether a specific setting
round-trips through the generic preview API) are marked ``"unverified"`` rather than guessed; the
*Update Tenant Setting* API itself is MS-flagged **preview / not for production**, surfaced as a caveat.

Tool-Reuse: this is the single source of truth for the tenant-settings knowledge that
``provision_apply._tenant_setup_md`` renders (that checklist now reads from this catalog — no second silo).

Reachability note: ``profile_from_blueprint`` currently derives only ``base``/``governance``/``sharing`` —
the blueprint IR has no field that expresses Copilot / Data Agents yet, so the ``copilot``/``data_agents``
capabilities are reachable by passing them **explicitly** to ``required_settings``/``settability_summary``
but are NOT auto-added to the rendered checklist. Wire them into ``profile_from_blueprint`` once the IR
expresses them (mirroring ``capacity_recommend``'s ``copilot``/``data_agents`` flags).

Grounding date: 2026-07-24. Sources are per-setting ``source`` URLs (learn.microsoft.com), verified then.
Cross-cutting: Update Tenant Setting API is generic over an opaque ``settingName`` but PREVIEW —
  learn.microsoft.com/rest/api/fabric/admin/tenants/update-tenant-setting
  learn.microsoft.com/rest/api/fabric/admin/tenants/list-tenant-settings (settingName ``CertifyDatasets`` shown).
"""
from __future__ import annotations

from typing import Any, Iterable

GROUNDING_DATE = "2026-07-24"

# The generic Admin REST API that makes tenant settings scriptable — but MS-flagged preview.
API_PREVIEW_CAVEAT = (
    "The Fabric *Update Tenant Setting* Admin REST API (and the sempy `update_tenant_setting` wrapper) is "
    "generic over an opaque settingName, so tenant-scope settings are in principle scriptable — but MS "
    "flags it PREVIEW / not for production, and publishes no per-setting allow-list, so smoke-test each "
    "targeted settingName before relying on it in the one-day setup."
)

# Capability keys are AGNOSTIC — a feature the delivery uses, not a source system or a mesh/medallion choice.
CAPABILITIES: dict[str, str] = {
    "base": "SPN-driven provisioning of any Fabric workspace/item + a capacity to run on (always required)",
    "admin_apis": "Admin/metadata REST APIs under the SPN (scanner, domains, restore)",
    "cicd_git": "Git-integrated CI/CD (fabric-cicd via Azure DevOps / GitHub)",
    "xmla_rw": "XMLA read/write — semantic-model TMDL / RLS deploy, external Tabular tools",
    "mcp_apply": "Power BI / Fabric MCP apply path",
    "onelake_external": "External-engine / Iceberg access to OneLake",
    "copilot": "Copilot in Fabric / Power BI",
    "data_agents": "Fabric Data Agents (preview)",
    "sharing": "Cross-tenant external data sharing (OneLake shares)",
    "governance": "Sensitivity labels + endorsement/certification",
}

# automatable: True = a documented, stable tenant switch, settable via the (preview) Update Tenant Setting
#                     API — the round-trip is still subject to the blanket smoke-test caveat below (of these,
#                     only #13 carries a settingName MS shows by name in the API docs: CertifyDatasets);
#              "unverified" = a tenant setting whose name/existence or API round-trip MS docs leave open;
#              False = needs a human (capacity-admin portal action, or an admin/RBAC grant via a different API).
_L = "https://learn.microsoft.com/"
CATALOG: list[dict[str, Any]] = [
    {
        "id": 1, "name": "Service principals can call Fabric public APIs",
        "alias": "Service principals can use Fabric APIs",   # older portal/doc name — kept for continuity
        "section": "Developer settings", "scope": "tenant", "capabilities": ["base"],
        "default": "on (new tenants)", "target": "on, scoped to the automation security group",
        "who": "Fabric tenant admin", "automatable": True,
        "how": "Update Tenant Setting REST (preview) / sempy — or portal",
        "why": "any REST / fab / MCP automation under the SPN", "required": "yes",
        "source": _L + "fabric/admin/service-admin-portal-developer",
    },
    {
        "id": 2, "name": "Service principals can create workspaces, connections, and deployment pipelines",
        "section": "Developer settings", "scope": "tenant", "capabilities": ["base"],
        "default": "off", "target": "on, scoped to the automation security group",
        "who": "Fabric tenant admin", "automatable": True,
        "how": "Update Tenant Setting REST (preview) / sempy — or portal",
        "why": "provisioning workspaces / connections / pipelines via the SPN", "required": "yes",
        "source": _L + "fabric/admin/service-admin-portal-developer",
    },
    {
        "id": 3, "name": "Service principals can access admin APIs used for updates",
        "section": "Admin API settings", "scope": "tenant", "capabilities": ["admin_apis"],
        "default": "unverified (likely off)", "target": "on if admin/metadata APIs are used",
        "who": "Fabric tenant admin", "automatable": "unverified",
        "how": "Update Tenant Setting REST (preview) / sempy — or portal",
        "why": "admin ops (domains, scanner, restore) via the SPN", "required": "if admin APIs used",
        "source": _L + "fabric/admin/enable-service-principal-admin-apis",
    },
    {
        "id": 4, "name": "Users can synchronize workspace items with their Git repositories",
        "section": "Git integration", "scope": "tenant", "capabilities": ["cicd_git"],
        "default": "Azure DevOps on / GitHub off", "target": "on for the chosen provider",
        "who": "Fabric tenant admin (delegatable to capacity/workspace)", "automatable": True,
        "how": "Update Tenant Setting REST (preview) / sempy — or portal",
        "why": "--emit-cicd Git integration + fabric-cicd", "required": "if CI/CD",
        "source": _L + "fabric/admin/git-integration-admin-settings",
    },
    {
        "id": 5, "name": "XMLA endpoint = Read Write",
        "section": "Capacity settings → Power BI workloads (NOT a tenant setting)", "scope": "capacity",
        "capabilities": ["xmla_rw"], "default": "read only", "target": "read/write",
        "who": "Capacity admin", "automatable": False,
        "how": "capacity-admin portal action (companion tenant switch 'Allow XMLA endpoints…' IS API-settable)",
        "why": "deploy semantic-model TMDL / RLS via XMLA", "required": "if XMLA/RLS/OLS",
        "source": _L + "fabric/enterprise/powerbi/service-premium-connect-tools#enable-xmla-read-write",
    },
    {
        "id": 6, "name": "Users can use the Power BI Model Context Protocol server endpoint (preview)",
        "section": "Integration settings", "scope": "tenant", "capabilities": ["mcp_apply"],
        "default": "unverified", "target": "on if the MCP apply path is used",
        "who": "Fabric tenant admin", "automatable": "unverified",
        "how": "Update Tenant Setting REST (preview) / sempy — or portal (settingName unconfirmed)",
        "why": "the Power BI / Fabric MCP apply path (+ setting #1 for the SPN)", "required": "if MCP apply",
        "source": _L + "fabric/admin/tenant-settings-index",
    },
    {
        "id": 7, "name": "Users can access data stored in OneLake with apps external to Fabric",
        "section": "OneLake settings", "scope": "tenant", "capabilities": ["onelake_external"],
        "default": "unverified", "target": "on if external engines / Iceberg interop",
        "who": "Fabric tenant admin", "automatable": "unverified",
        "how": "Update Tenant Setting REST (preview) / sempy — or portal",
        "why": "external-engine / Iceberg / OneLake-SPN access", "required": "if external/Iceberg",
        "source": _L + "fabric/admin/service-admin-portal-onelake",
    },
    {
        "id": 8, "name": "Users can use Copilot and other features powered by Azure OpenAI",
        "section": "Copilot and Azure OpenAI Service", "scope": "tenant", "capabilities": ["copilot"],
        "default": "on (auto-delegated to capacity admins)", "target": "on (default)",
        "who": "Fabric tenant admin (capacity admin retains override)", "automatable": True,
        "how": "Update Tenant Setting REST (preview) / sempy — or portal",
        "why": "Copilot in Fabric / Power BI (needs a paid F2+/P1+ capacity — not F64)", "required": "if Copilot",
        "source": _L + "fabric/admin/service-admin-portal-copilot",
    },
    {
        "id": 9, "name": ("Data sent to Azure OpenAI can be processed outside your capacity's geographic "
                          "region, compliance boundary, or national cloud instance"),   # exact portal Title
        "section": "Copilot and Azure OpenAI Service", "scope": "tenant", "capabilities": ["copilot"],
        "default": "off", "target": "on ONLY if the capacity region has no in-region Azure OpenAI",
        "who": "Fabric tenant admin", "automatable": True,
        "how": "Update Tenant Setting REST (preview) / sempy — or portal",
        "why": "cross-geo Copilot processing (does not auto-delegate to capacity admins)",
        "required": "if Copilot cross-geo",
        "source": _L + "fabric/admin/service-admin-portal-copilot",
    },
    {
        "id": 10, "name": "Capacities can be designated as Fabric Copilot capacities",
        "section": "Copilot and Azure OpenAI Service", "scope": "tenant", "capabilities": ["data_agents"],
        "default": "on", "target": "on + designate the capacity as a Copilot capacity",
        "who": "Fabric tenant admin (+ capacity admin designation)", "automatable": "unverified",
        "how": "Update Tenant Setting REST (preview) / sempy for the switch; capacity designation is portal",
        "why": "Fabric Data Agents (preview) ride on the Copilot switches + a Copilot capacity",
        "required": "if Data Agents",
        "source": _L + "fabric/data-science/data-agent-tenant-settings",
    },
    {
        "id": 11, "name": "External data sharing",
        "section": "Export and sharing settings", "scope": "tenant", "capabilities": ["sharing"],
        "default": "off (both tenants)", "target": "on in BOTH provider and consumer tenant",
        "who": "Fabric tenant admin (in each tenant separately)", "automatable": True,
        "how": "Update Tenant Setting REST (preview) / sempy — or portal, per tenant",
        "why": "P5 cross-tenant OneLake external sharing", "required": "if sharing",
        "source": _L + "fabric/governance/external-data-sharing-enable",
    },
    {
        "id": 12, "name": "Allow users to apply sensitivity labels for content",
        "section": "Information protection", "scope": "tenant", "capabilities": ["governance"],
        "default": "off", "target": "on + a label policy that includes the caller",
        "who": "Fabric tenant admin", "automatable": True,
        "how": "Update Tenant Setting REST (preview) / sempy — or portal (SPNs exempt from MANDATORY labels)",
        "why": "sensitivity-label application (--emit-governance)", "required": "if governance",
        "source": _L + "fabric/enterprise/powerbi/service-security-enable-data-sensitivity-labels",
    },
    {
        "id": 13, "name": "Certification",           # exact portal Title; the endorsement/SG detail is in why/target
        "section": "Export and sharing settings", "scope": "tenant", "capabilities": ["governance"],
        "default": "off", "target": "on + a security group of authorized certifiers (SGs only, no named users)",
        "who": "Fabric tenant admin (delegatable to domain admin)", "automatable": True,
        "how": "Update Tenant Setting REST (preview) / sempy (settingName CertifyDatasets) — or portal",
        "why": "endorsement / certification of gold products (--emit-governance)", "required": "if governance",
        "source": _L + "fabric/admin/endorsement-certification-enable",
    },
    {
        "id": 14, "name": "A Fabric capacity (or trial) assigned to the delivery workspaces",
        "section": "Capacity settings (NOT a tenant setting)", "scope": "capacity", "capabilities": ["base"],
        "default": "n/a (an assignment action)", "target": "capacity assigned to each delivery workspace",
        "who": "Capacity contributor + workspace admin (two role checks)", "automatable": False,
        "how": "Core REST 'Assign To Capacity' — needs an already-privileged human, not the tenant-settings API",
        "why": "everything runs on capacity; sizing → capacity_recommend.py", "required": "yes",
        "source": _L + "fabric/admin/capacity-settings",
    },
    {
        "id": 15, "name": "Grant the SPN a workspace role (Member / Contributor)",
        "section": "Workspace access (NOT a tenant setting)", "scope": "workspace", "capabilities": ["base"],
        "default": "n/a (a role grant)", "target": "SPN = Member or Contributor on each delivery workspace",
        "who": "Existing workspace admin", "automatable": False,
        "how": "Core REST workspace role API — an SPN CANNOT self-provision; a human grants first access",
        "why": "the SPN has no standing access until a privileged principal adds it", "required": "yes",
        "source": _L + "fabric/fundamentals/roles-workspaces",
    },
    {
        "id": 16, "name": "Domains created (+ a domain admin assigned)",
        "section": "Domain management (NOT a tenant setting)", "scope": "tenant", "capabilities": ["governance"],
        "default": "none (an admin action)", "target": "the delivery's domains created, each with a domain admin",
        "who": "Fabric admin / domain admin", "automatable": False,
        "how": "Admin REST 'Create Domain' — needs an already-privileged Fabric admin, not the tenant-settings API",
        "why": "endorsement/certification + mesh publishing are domain-scoped (--emit-governance)",
        "required": "if governance", "source": _L + "fabric/governance/domains",
    },
]

_BY_ID = {s["id"]: s for s in CATALOG}


def required_settings(capabilities: Iterable[str]) -> list[dict[str, Any]]:
    """Return the catalog settings gated by ``capabilities`` (agnostic feature keys; see ``CAPABILITIES``).
    ``base`` is always included. Unknown keys are ignored. Sorted by catalog id. Pure/deterministic."""
    wanted = set(capabilities) | {"base"}
    return [s for s in CATALOG if set(s["capabilities"]) & wanted]


def settability_summary(capabilities: Iterable[str]) -> dict[str, Any]:
    """Split the required settings into what a one-day setup can SCRIPT vs what needs a HUMAN.

    Returns ``{scriptable[], scriptable_unverified[], needs_human[], api_preview_caveat, grounding_date}``
    where each list holds ``(id, name, how)`` tuples. ``scriptable`` = tenant settings settable via the
    (preview) Update Tenant Setting API; ``scriptable_unverified`` = tenant settings whose API round-trip
    MS docs don't individually confirm (smoke-test first); ``needs_human`` = capacity-admin / RBAC actions
    that no tenant-settings script can perform."""
    req = required_settings(capabilities)
    def _t(s: dict) -> tuple[int, str, str]:
        return (s["id"], s["name"], s["how"])
    return {
        "scriptable": [_t(s) for s in req if s["automatable"] is True],
        "scriptable_unverified": [_t(s) for s in req if s["automatable"] == "unverified"],
        "needs_human": [_t(s) for s in req if s["automatable"] is False],
        "api_preview_caveat": API_PREVIEW_CAVEAT,
        "grounding_date": GROUNDING_DATE,
    }


def profile_from_blueprint(bp: dict) -> set[str]:
    """Derive the capability profile from a blueprint IR (agnostic): governance when any domain publishes,
    sharing when the blueprint declares external sharing. ``base`` is always present."""
    caps = {"base"}
    if any(d.get("publishing") for d in bp.get("mesh", {}).get("domains", []) or []):
        caps.add("governance")
    if bp.get("sharing"):
        caps.add("sharing")
    return caps
