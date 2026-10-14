"""admin_settings — the Fabric admin/tenant/capacity/workspace settings a customer delivery needs, as a
cited catalog + a capability-keyed planner. Readiness-Gate (sibling of ``capacity_recommend.py``).

The directive: *define the admin settings so one can, within a day, set what one needs how.* This module
is the machine-readable **definition**. Given the set of **capabilities** a delivery actually uses
(agnostic, feature-keyed — not source- or pattern-specific), ``required_settings`` returns exactly the
settings that gate it, each carrying: the exact portal name + section, its **scope** (``SCOPES`` —
tenant / capacity / workspace / entra), **default**, **who** can set it, the **target** value for the
delivery, and — the crux of
"within a day" — whether it is **automatable** via the Fabric *Update Tenant Setting* Admin REST API
/ ``sempy`` or needs a **human** admin (capacity-admin portal action, or an RBAC grant a
privileged human must perform). ``settability_summary`` splits the plan into "scriptable" vs "needs a
human" so the one-day setup is honest about what can be automated.

Honest by construction: settings MS docs do not pin (default state, or whether a specific setting
round-trips through the generic API) are marked ``"unverified"`` rather than guessed; the API publishes
no per-setting allow-list and is rate-limited, surfaced as a caveat.

Tool-Reuse: this is the single source of truth for the tenant-settings knowledge that
``provision_apply._tenant_setup_md`` renders (that checklist now reads from this catalog — no second silo).

Reachability (aufgeloest 30.07.2026): ``profile_from_blueprint`` leitet jetzt auch ``copilot``/
``data_agents``/``ontology`` ab — die IR drueckt sie ueber ``ai_grounding.data_agent`` bzw.
``ai_grounding.ontology`` aus. Die frueher hier notierte Lucke ("the blueprint IR has no field that
expresses Copilot / Data Agents yet") ist damit zu; ein Umweg ueber explizit uebergebene Capabilities
ist nicht mehr noetig, bleibt aber moeglich (die CLI nutzt ihn als Rueckfall, wenn jemand die
Emit-Flags ohne IR-Deklaration fahrt).

Grounding date: 2026-07-24. Sources are per-setting ``source`` URLs (learn.microsoft.com), verified then.
Cross-cutting: Update Tenant Setting API is generic over an opaque ``settingName`` —
  learn.microsoft.com/rest/api/fabric/admin/tenants/update-tenant-setting
  learn.microsoft.com/rest/api/fabric/admin/tenants/list-tenant-settings (settingName ``CertifyDatasets`` shown).
  Status re-measured 2026-09-29 (plan W1.4): no preview flag on either Learn page, and the official spec
  (github.com/microsoft/fabric-rest-api-specs, ``admin/swagger.json``) carries no preview marker on
  ``Tenants_ListTenantSettings`` / ``Tenants_UpdateTenantSetting`` while it marks 18 other admin operations
  preview. Until 2026-09-29 this module called the API "preview / not for production".
"""
from __future__ import annotations

from typing import Any, Iterable

GROUNDING_DATE = "2026-07-24"

#: The scopes a catalog entry can sit in. ``entra`` joined the set on 2026-08-16 with #23 and it is a
#: widening, not a typo: an admin role hardened through PIM is not a Fabric setting at all — no tenant,
#: capacity or workspace surface carries it. Filing it under ``tenant`` would have been the convenient
#: lie, and it would have sent an admin to the Fabric admin portal to look for something that lives in
#: Entra. The set is a constant so the catalog and its test read the same list.
#:
#: ``m365`` joined on 2026-09-29 (plan I-21 W5.7) for the same reason: *Fabric data in Microsoft
#: Copilot* lives in the Microsoft 365 admin center, not in Fabric. A Fabric admin looking for it under
#: Govern finds nothing, and the Fabric tenant-setting API cannot read or set it.
SCOPES = ("tenant", "capacity", "workspace", "entra", "m365")

# --- Navigation: OneLake catalog → Govern is the admin start page (plan I-21 W1.7) -------------------
#
# Learn, read 2026-09-29 via MCP: `fabric/admin/about-tenant-settings` („Select OneLake catalog, and then
# select the Govern tab … Configurations > Tenant settings"; „OneLake catalog and Govern are rolling out
# by region. If they're not available in your region, select Settings (gear) icon > Admin portal >
# Tenant settings"), `fabric/admin/tenant-settings-index` („Administrators can use Govern as their
# primary destination"), `fabric/governance/onelake-catalog-capacities` (Capacities page, same fallback
# sentence), `fabric/governance/onelake-catalog-govern` (the four limits below).
#
# Why a table and not a search-and-replace over the texts: the path is a function of the SCOPE, and the
# fallback is part of the answer, not a footnote. A text that names only Govern sends an admin in a
# region without Govern — or on a Private-Link tenant — to a tab that does not exist.
NAVIGATION_GEPRUEFT = "2026-09-29"
GOVERN_PFAD: dict[str, str] = {
    "tenant": "OneLake catalog → Govern → Configurations → Tenant settings",
    "capacity": "OneLake catalog → Govern → Capacities → the capacity → More options → Settings",
}
ADMIN_PORTAL_FALLBACK: dict[str, str] = {
    "tenant": "Settings (gear) → Admin portal → Tenant settings",
    "capacity": "Settings (gear) → Admin portal → Capacity settings",
}
#: The documented limits of the Govern tab. Each one is a case in which the fallback is not optional.
GOVERN_GRENZEN: tuple[str, ...] = (
    "Not available while Private Link is activated — the Admin portal stays the only way in.",
    "No cross-tenant scenarios and no guest users.",
    "Estate insights and recommended actions come from admin monitoring storage refreshed once a day; "
    "a change made today shows up tomorrow.",
    "Everyone viewing the admin monitoring workspace (estate report) needs a Power BI Pro licence "
    "unless that workspace is assigned to a capacity.",
)


def navigation(scope: str) -> dict[str, str] | None:
    """Where a setting of ``scope`` is set: ``{"govern": …, "fallback": …}``, or ``None``.

    ``None`` for ``workspace`` (workspace settings, not an admin surface), ``entra`` (Entra admin
    center) and ``m365`` (Microsoft 365 admin center) — Govern is the wrong place for all three, and
    answering with it would be the convenient lie again."""
    if scope not in GOVERN_PFAD:
        return None
    return {"govern": GOVERN_PFAD[scope], "fallback": ADMIN_PORTAL_FALLBACK[scope]}


def navigation_md() -> list[str]:
    """The navigation block every admin-facing runbook renders — one source, English like its readers."""
    out = [f"## Where to set it (checked {NAVIGATION_GEPRUEFT})", "",
           "The admin start page is **OneLake catalog → Govern**. The Admin portal is the fallback, "
           "not the default — and it is the only way in while Govern is not rolled out in your region.",
           "", "| Scope | Govern (primary) | Fallback |", "|---|---|---|"]
    for scope in GOVERN_PFAD:
        out.append(f"| {scope} | {GOVERN_PFAD[scope]} | {ADMIN_PORTAL_FALLBACK[scope]} |")
    out += ["", "Govern limits that force the fallback:", ""]
    out += [f"- {g}" for g in GOVERN_GRENZEN]
    out.append("")
    return out

# The generic Admin REST API that makes tenant settings scriptable. Not preview (re-measured 2026-09-29,
# see module docstring); what remains true is the opaque settingName, the missing allow-list and the limit.
API_CAVEAT = (
    "The Fabric *Update Tenant Setting* Admin REST API (and the sempy `update_tenant_setting` wrapper) is "
    "generic over an opaque settingName, so tenant-scope settings are scriptable — but MS publishes no "
    "per-setting allow-list and limits the API to 25 requests per minute (Tenant.ReadWrite.All, Fabric "
    "administrator or service principal), so read each targeted settingName via List Tenant Settings and "
    "smoke-test it before relying on it in the one-day setup."
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
    # GA seit Maerz 2026 (Learn "What's new in Fabric? archive", GA-Tabelle, Zeile "Fabric Data Agent
    # (Generally Available)"; concept-data-agent: "a generally available feature"; per MCP gelesen
    # 29.09.2026). Vorher hier als "(preview)" gefuehrt. Einzelne Konfigurationen (preview runtime,
    # Purview-Zugriffsrestriktionen) bleiben Preview; die Faehigkeit selbst nicht.
    "data_agents": "Fabric Data Agents (GA since March 2026)",
    "ontology": "Fabric IQ Ontology item (preview)",
    "sharing": "Cross-tenant external data sharing (OneLake shares)",
    "governance": "Sensitivity labels + endorsement/certification",
}

# automatable: True = a documented, stable tenant switch, settable via the Update Tenant Setting
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
        "how": "Update Tenant Setting REST / sempy — or portal",
        "why": "any REST / fab / MCP automation under the SPN", "required": "yes",
        "source": _L + "fabric/admin/service-admin-portal-developer",
    },
    {
        "id": 2, "name": "Service principals can create workspaces, connections, and deployment pipelines",
        "section": "Developer settings", "scope": "tenant", "capabilities": ["base"],
        "default": "off", "target": "on, scoped to the automation security group",
        "who": "Fabric tenant admin", "automatable": True,
        "how": "Update Tenant Setting REST / sempy — or portal",
        "why": "provisioning workspaces / connections / pipelines via the SPN", "required": "yes",
        "source": _L + "fabric/admin/service-admin-portal-developer",
    },
    {
        "id": 3, "name": "Service principals can access admin APIs used for updates",
        "section": "Admin API settings", "scope": "tenant", "capabilities": ["admin_apis"],
        "default": "unverified (likely off)", "target": "on if admin/metadata APIs are used",
        "who": "Fabric tenant admin", "automatable": "unverified",
        "how": "Update Tenant Setting REST / sempy — or portal",
        # Bis 07.08.2026 stand hier zusaetzlich „scanner". Das war falsch und teuer: der
        # Metadaten-Scanner (`scan_workspaces`) ist eine READ-ONLY-Admin-API und haengt an
        # einem ANDEREN Schalter (#20). Wer nur diesen hier setzt, bekommt beim Scan
        # weiterhin `403 InsufficientScopes` — genau der Befund vom 16.07.2026, der damals
        # faelschlich der Trial-Lizenz angelastet wurde (ADR-0050:21).
        "why": "admin write ops (domains, restore) via the SPN", "required": "if admin APIs used",
        "source": _L + "fabric/admin/enable-service-principal-admin-apis",
    },
    {
        "id": 4, "name": "Users can synchronize workspace items with their Git repositories",
        "section": "Git integration", "scope": "tenant", "capabilities": ["cicd_git"],
        "default": "Azure DevOps on / GitHub off", "target": "on for the chosen provider",
        "who": "Fabric tenant admin (delegatable to capacity/workspace)", "automatable": True,
        "how": "Update Tenant Setting REST / sempy — or portal",
        "why": "--emit-cicd Git integration + fabric-cicd", "required": "if CI/CD",
        "source": _L + "fabric/admin/git-integration-admin-settings",
    },
    {
        "id": 5, "name": "XMLA endpoint = Read Write",
        "section": "Capacity settings → Power BI workloads (NOT a tenant setting)", "scope": "capacity",
        "capabilities": ["xmla_rw"], "default": "read only", "target": "read/write",
        "who": "Capacity admin", "automatable": False,
        "how": ("capacity-admin portal action: OneLake catalog → Govern → Capacities → the capacity → "
                "Settings → Power BI workloads (fallback: Admin portal → Capacity settings); the "
                "companion tenant switch 'Allow XMLA endpoints…' IS API-settable"),
        "why": "deploy semantic-model TMDL / RLS via XMLA", "required": "if XMLA/RLS/OLS",
        "source": _L + "fabric/enterprise/powerbi/service-premium-connect-tools#enable-xmla-read-write",
    },
    {
        "id": 6, "name": "Users can use the Power BI Model Context Protocol server endpoint (preview)",
        "section": "Integration settings", "scope": "tenant", "capabilities": ["mcp_apply"],
        "default": "unverified", "target": "on if the MCP apply path is used",
        "who": "Fabric tenant admin", "automatable": "unverified",
        "how": "Update Tenant Setting REST / sempy — or portal (settingName unconfirmed)",
        "why": "the Power BI / Fabric MCP apply path (+ setting #1 for the SPN)", "required": "if MCP apply",
        "source": _L + "fabric/admin/tenant-settings-index",
    },
    {
        "id": 7, "name": "Users can access data stored in OneLake with apps external to Fabric",
        "section": "OneLake settings", "scope": "tenant", "capabilities": ["onelake_external"],
        "default": "unverified", "target": "on if external engines / Iceberg interop",
        "who": "Fabric tenant admin", "automatable": "unverified",
        "how": "Update Tenant Setting REST / sempy — or portal",
        "why": "external-engine / Iceberg / OneLake-SPN access", "required": "if external/Iceberg",
        "source": _L + "fabric/admin/service-admin-portal-onelake",
    },
    {
        "id": 8, "name": "Users can use Copilot and other features powered by Azure OpenAI",
        "section": "Copilot and Azure OpenAI Service", "scope": "tenant", "capabilities": ["copilot"],
        "default": "on (auto-delegated to capacity admins)", "target": "on (default)",
        "who": "Fabric tenant admin (capacity admin retains override)", "automatable": True,
        "how": "Update Tenant Setting REST / sempy — or portal",
        "why": "Copilot in Fabric / Power BI (needs a paid F2+/P1+ capacity — not F64)", "required": "if Copilot",
        "source": _L + "fabric/admin/service-admin-portal-copilot",
    },
    {
        "id": 9, "name": ("Data sent to Azure OpenAI can be processed outside your capacity's geographic "
                          "region, compliance boundary, or national cloud instance"),   # exact portal Title
        "section": "Copilot and Azure OpenAI Service", "scope": "tenant", "capabilities": ["copilot"],
        "default": "off", "target": "on ONLY if the capacity region has no in-region Azure OpenAI",
        "who": "Fabric tenant admin", "automatable": True,
        "how": "Update Tenant Setting REST / sempy — or portal",
        "why": "cross-geo Copilot processing (does not auto-delegate to capacity admins)",
        "required": "if Copilot cross-geo",
        "source": _L + "fabric/admin/service-admin-portal-copilot",
    },
    {
        "id": 10, "name": "Capacities can be designated as Fabric Copilot capacities",
        "section": "Copilot and Azure OpenAI Service", "scope": "tenant", "capabilities": ["data_agents"],
        "default": "on", "target": "on + designate the capacity as a Copilot capacity",
        "who": "Fabric tenant admin (+ capacity admin designation)", "automatable": "unverified",
        "how": "Update Tenant Setting REST / sempy for the switch; capacity designation is portal",
        "why": "Fabric Data Agents (GA since March 2026) ride on the Copilot switches + a Copilot capacity",
        "required": "if Data Agents",
        "source": _L + "fabric/data-science/data-agent-tenant-settings",
    },
    {
        # Korrektur 2026-07-30: dieser EINE Eintrag deckte zwei **verschieden benannte** Schalter
        # ("on in BOTH provider and consumer tenant"). Im Verbraucher-Tenant heißt die Einstellung aber
        # nicht "External data sharing", sondern **"Users can accept external data shares"** — wer im
        # Portal nach dem hier genannten Namen sucht, findet dort den falschen (oder keinen) Schalter.
        # Ein Readiness-Gate, das einen Admin auf einen nicht existierenden Namen schickt, ist genau so
        # unbrauchbar wie eines, das die Einstellung ganz vergisst. Jetzt zwei Einträge, je Seite einer.
        "id": 11, "name": "External data sharing",
        "section": "Export and sharing settings", "scope": "tenant", "capabilities": ["sharing"],
        "default": "off", "target": "on in the PROVIDING tenant + specify who may create shares",
        "who": "Fabric tenant admin (providing tenant)", "automatable": True,
        "how": "Update Tenant Setting REST / sempy — or portal",
        "why": "P5: without it nobody in our tenant can create the share at all",
        "required": "if sharing",
        "source": _L + "fabric/governance/external-data-sharing-enable",
    },
    {
        "id": 19, "name": "Users can accept external data shares",
        "section": "Export and sharing settings", "scope": "tenant", "capabilities": ["sharing"],
        "default": "off", "target": "on in the CONSUMING tenant + specify who may accept",
        "who": "Fabric tenant admin (consuming tenant — a DIFFERENT organisation)",
        "automatable": False,
        "how": "Portal in the partner's tenant. We have no access there; this is a partner "
               "prerequisite to be agreed, not a step we can run",
        "why": "P5: the invitation cannot be accepted without it, and the invite expires after 90 days",
        "required": "if sharing",
        "source": _L + "fabric/governance/external-data-sharing-enable",
    },
    {
        "id": 12, "name": "Allow users to apply sensitivity labels for content",
        "section": "Information protection", "scope": "tenant", "capabilities": ["governance"],
        "default": "off", "target": "on + a label policy that includes the caller",
        "who": "Fabric tenant admin", "automatable": True,
        "how": "Update Tenant Setting REST / sempy — or portal (SPNs exempt from MANDATORY labels)",
        "why": "sensitivity-label application (--emit-governance)", "required": "if governance",
        "source": _L + "fabric/enterprise/powerbi/service-security-enable-data-sensitivity-labels",
    },
    {
        "id": 13, "name": "Certification",           # exact portal Title; the endorsement/SG detail is in why/target
        "section": "Export and sharing settings", "scope": "tenant", "capabilities": ["governance"],
        "default": "off", "target": "on + a security group of authorized certifiers (SGs only, no named users)",
        "who": "Fabric tenant admin (delegatable to domain admin)", "automatable": True,
        "how": "Update Tenant Setting REST / sempy (settingName CertifyDatasets) — or portal",
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
    {
        # The catalog carried the cross-geo *processing* switch (id 9) but not the *storing* one, while
        # both are documented as data-agent-relevant — and we emit a Data Agent. Gate incomplete, found
        # 2026-07-30 in the ontology tutorial's prerequisite list.
        #
        # Why it is its own entry and not a footnote on id 9: this switch is about RETENTION, not routing.
        # Conversational experiences (Copilot in Notebooks, Data Agents) keep conversation history across
        # sessions; MS: it lives in the same region and Azure OpenAI resources that process the requests,
        # a user can clear it at any time, and if nobody clears it, it is kept for **28 days**. That is a
        # DPIA-relevant fact about *stored* content, which no answer about *processing* covers.
        "id": 17, "name": ("Data sent to Azure OpenAI can be stored outside your capacity's geographic "
                           "region, compliance boundary, or national cloud instance"),   # exact portal Title
        "section": "Copilot and Azure OpenAI Service", "scope": "tenant", "capabilities": ["data_agents"],
        "default": "off",
        "target": "on ONLY if the capacity region has no in-region Azure OpenAI (same condition as id 9)",
        "who": "Fabric tenant admin", "automatable": True,
        "how": "Update Tenant Setting REST / sempy — or portal",
        "why": ("Data Agents store conversation history across sessions — 28-day retention if the user "
                "never clears the chat. An EU-Data-Boundary capacity needs NEITHER this nor id 9: MS's "
                "region table maps EUDB capacity to EUDB processing. (The ontology tutorial lists both as "
                "flat prerequisites; the region-conditional table is the precise source, so the target "
                "here stays conditional rather than 'always on'.)"),
        "required": "if Data Agents cross-geo",
        "source": _L + "fabric/iq/ontology/tutorial-0-introduction",
    },
    {
        "id": 18, "name": "Enable Ontology item (preview)",
        "section": "Users can create and use new item types", "scope": "tenant", "capabilities": ["ontology"],
        "default": "off", "target": "on",
        "who": "Fabric tenant admin", "automatable": "unverified",
        "how": "Update Tenant Setting REST / sempy — or portal (preview item switch)",
        "why": "the Ontology item we emit cannot be created at all without it",
        "required": "if ontology",
        "source": _L + "fabric/iq/ontology/overview-tenant-settings",
    },
    # --- 07.08.2026: die beiden Schalter, an denen der Readiness-Collector wirklich haengt ---
    #
    # Befund beim Zusammenstellen der E2E-Voraussetzungen: der Katalog kannte nur #3 („admin APIs
    # used for UPDATES") und schrieb sich den Scanner selbst zu. Der Scanner ist aber READ-ONLY und
    # haengt an einem eigenen Schalter plus Sicherheitsgruppen-Mitgliedschaft. Die Folge war nicht
    # theoretisch: unsere eigene Vorbedingungs-Liste haette einen Kunden mit gesetztem #3 in denselben
    # `403 InsufficientScopes` laufen lassen wie uns am 16.07.2026 — und wieder haette die Lizenz
    # ausgesehen wie die Ursache.
    {
        "id": 20, "name": "Service principals can access read-only admin APIs",
        "section": "Admin API settings", "scope": "tenant", "capabilities": ["admin_apis"],
        "default": "off", "target": "on, scoped to the automation security group",
        "who": "Fabric tenant admin", "automatable": "unverified",
        "how": "Update Tenant Setting REST / sempy — or portal",
        "why": ("der Readiness-Collector fährt `sempy_labs.admin.scan_workspaces`, also eine "
                "READ-ONLY-Admin-API. MS: der SPN muss zusätzlich Mitglied der erlaubten "
                "Sicherheitsgruppe sein — die Gruppenmitgliedschaft ist der zweite, gern übersehene "
                "Teil. Ohne beides: `403 InsufficientScopes`, unabhängig von SKU und Lizenz."),
        "required": "if admin APIs used",
        "source": _L + "fabric/admin/enable-service-principal-admin-apis",
    },
    {
        "id": 21, "name": "Enhance admin APIs responses with detailed metadata",
        "section": "Admin API settings", "scope": "tenant", "capabilities": ["admin_apis"],
        "default": "off", "target": "on",
        "who": "Fabric tenant admin", "automatable": "unverified",
        "how": "Update Tenant Setting REST / sempy — or portal",
        "why": ("der Collector ruft `scan_workspaces(lineage=True, data_source_details=True)`. Ohne "
                "diesen Schalter antwortet die API, aber ohne Tabellen-/Spalten-Metadaten — der Scan "
                "wirkt erfolgreich und liefert eine leere Beobachtung. MS koppelt ihn ausdrücklich an "
                "#20: für Service Principals greift er nur, wenn #20 an ist."),
        "required": "if admin APIs used",
        "source": _L + "fabric/admin/metadata-scanning-setup",
    },
    # --- 16.08.2026: die zwei Punkte, bei denen der Schalter nicht die Antwort ist -------
    #
    # Beide standen im Betriebskanon (BK-F06, BK-Z05) mit begruendeter Vorgabe und **ohne einen
    # einzigen Beleg** — entschieden, nirgends geliefert. Beide gehoeren hierher und nicht in ein
    # neues Modul: es ist dieselbe Frage („welche Einstellung braucht die Lieferung, wer setzt
    # sie, und laesst sie sich skripten"), und ein zweiter Katalog waere ein zweites Silo.
    #
    # Sie bringen aber etwas mit, das die bisherigen 21 Eintraege nicht brauchten: bei ihnen ist
    # „an" nur der Anfang. Surge Protection ohne Schwellen ist wirkungslos, und Microsoft nennt
    # bewusst keinen Startwert. Deshalb die zwei optionalen Felder `verfahren` (was nach dem
    # Umlegen zu tun ist) und `grenzen` (was die Einstellung ausdruecklich NICHT abdeckt). Eine
    # Tabellenzeile kann das nicht tragen; sie zu quetschen hiess, die Grenzen wegzulassen, und
    # eine Haertung, deren Grenzen niemand kennt, wird fuer mehr gehalten, als sie ist.
    {
        "id": 22, "name": "Surge protection",
        # Kein `<capacity>` im Text: spitze Klammern sind in dieser Lieferung ein Platzhalter-
        # Zeichen, und der Binding-Scanner haette diesen hier als unerklaerten Platzhalter im
        # Kundenbogen gefuehrt (gemessen 16.08.2026). Ein Abschnittsname ist kein Wert.
        "section": "Capacity settings → the delivery capacity → Surge protection (NOT a tenant setting)",
        "scope": "capacity", "capabilities": ["base"],
        "default": "off — the documented enable steps switch Background Operations to On",
        "target": "on; thresholds derived from the first full measurement window, never set up front",
        "who": "Capacity admin", "automatable": False,
        "how": ("capacity-admin portal action: OneLake catalog → Govern → Capacities → select the "
                "capacity → More options → Configure surge protection (or → Settings → Surge "
                "protection) → Background Operations On → rejection + recovery threshold → Apply "
                "(fallback where Govern is not rolled out, and the path the surge-protection page "
                "itself documents: Admin portal → Capacity settings → select the capacity → Surge "
                "protection; both read 01.10.2026)"),
        "why": ("without it the capacity's 24-hour background percentage may reach 100% before background "
                "operations are rejected, and the deep throttling that follows recovers slowly"),
        "required": "yes",
        "source": _L + "fabric/enterprise/surge-protection",
        "verfahren": (
            "Switch it on at handover and leave both thresholds unset until the capacity has run one "
            "full measurement window. MS publishes no starting value: all three worked examples read "
            "the Capacity Metrics app **Compute** page — the *Background rejection*, *Interactive "
            "rejection* and *Utilization* charts — and place the rejection threshold between the "
            "average and the peak, the recovery threshold around the typical background level. The "
            "third example ends in *don't bother*: where 80–90% of usage is background, capacity-level "
            "limits don't help. So this setting has two prerequisites of its own, and neither is a "
            "switch — the Capacity Metrics app installed (`monitoring/`) and a representative load "
            "having run. Before both, any number entered here is a guess wearing a threshold's "
            "clothes.\n\n"
            "Workspace-level surge protection is the second half and a separate decision: a per-"
            "workspace CU cap over a rolling 24-hour window, plus the states *Available* / *Mission "
            "critical* / *Blocked*. Two properties decide whether it fits — the check runs every five "
            "minutes, so the cap is soft; and raising the limit or deleting the rule does **not** "
            "release a workspace that is already blocked — change the limit first, then unblock it "
            "(Admin portal → Capacity settings → the capacity → *Workspaces* table → *Unblock*, review "
            "the consumption, confirm). Unblocking can *forgive* the consumption already recorded, so "
            "it no longer counts toward the rolling 24-hour total; operations already in progress are "
            "neither cancelled nor restarted nor billed differently. Setting a blocked workspace to "
            "*Mission critical* also unblocks it.\n\n"
            "Two things to settle before switching the workspace cap on. *Blocked* is a harder stop "
            "than the capacity-level one: capacity level rejects background operations, a blocked "
            "workspace rejects **all** operations, interactive included — to its users that looks "
            "like an outage. Turn the banner on in the same visit (OneLake catalog → Govern → "
            "Capacities → the capacity → settings → *Capacity Notifications* → *Display a banner to "
            "all users of the workspace*; fallback Admin portal → Capacity settings → *Throttling "
            "notifications*) so they read a limit instead of guessing at a fault. And the rolling 24-hour window does not reset "
            "when a block expires: a workspace whose usage still sits above the cap is blocked "
            "again straight away.\n\n"
            "The capacity level has its own notifications in the same place: *Display a banner to all "
            "users of the capacity* and *Email capacity administrators contacts (preview)*; they fire "
            "when the capacity approaches or enters throttling, activates surge protection, recovers, "
            "and returns to a healthy state. Watch the effect in the Capacity Metrics app → Compute → "
            "*System events* (`SurgeProtectionActive`, `InteractiveDelayAndSurgeProtectionActive`, "
            "`InteractiveRejectedAndSurgeProtectionActive`, back to `NotOverloaded`); rejected "
            "requests carry the status *RejectedSurgeProtection* on the Timepoint page (surge-"
            "protection page read 01.10.2026)."),
        "grenzen": (
            "Fabric SKUs only — no other SKU type is supported.",
            "In-progress jobs are not stopped, so the rejection threshold is not an upper bound on the "
            "24-hour background percentage: running jobs keep reporting usage past it.",
            "Operations billed with Autoscale are not blocked.",
            "Some requests started from the Fabric UI are billed as background operations or depend "
            "on one; while surge protection is active they are rejected too, so users see it in the UI.",
            "OneLake activities are unaffected.",
            "It does not guarantee interactive requests escape delay or rejection — at the capacity's "
            "maximum compute limit they are delayed or rejected regardless.",
            "Workspace level: Dataflows Gen1, paginated reports, scorecards, graph models, Activator "
            "(no new Activators in a blocked workspace, existing ones may keep running) and Dataflow "
            "Gen2 editing (its refreshes are blocked) are outside its reach; Autoscale compute is "
            "excluded from the per-workspace calculation.",
            "*Mission critical* is worth less than it reads, and MS's own page says both things. The "
            "state table calls it \"exempt from capacity-level surge protection rules\" and answers "
            "\"subject to capacity-level surge protection? No\"; the same page's limitations say "
            "\"Mission-critical status doesn't override capacity-level surge protection\", and the "
            "unblock section narrows it to \"exempt from workspace-level surge protection\" (page read "
            "01.10.2026; still contradictory as on 20.08.2026). We deliver the conservative reading: it lifts the per-workspace cap and "
            "nothing else. Do not plan a critical workload around surviving capacity-level throttling "
            "on this flag — isolate it in its own capacity, which is what MS recommends anyway.",
            "There is no API. Every documented path for this setting is a portal step, on the surge-"
            "protection page and on `fabric/admin/capacity-settings` alike (both read 20.08.2026; "
            "surge-protection page re-read 01.10.2026, still portal only). The "
            "capacity REST surfaces that do exist reach other things: Azure `Microsoft.Fabric/"
            "capacities` creates, pauses, resumes and resizes; the Power BI `Capacities` APIs "
            "configure Premium workloads; `sempy.fabric.admin` reads the capacity state. None of them "
            "carries surge protection, so it can neither be set nor read back by script — the "
            "readiness snapshot leaves it UNKNOWN rather than claiming a state it never saw.",
        ),
    },
    {
        "id": 23, "name": "Fabric Administrator assigned Eligible via PIM (+ Conditional Access)",
        "section": "Entra ID Governance → Privileged Identity Management → Microsoft Entra roles",
        "scope": "entra", "capabilities": ["base"],
        "default": "n/a — a standing assignment is what you get if nobody decides otherwise",
        "target": "Fabric Administrator Eligible-only, activation through PIM with MFA + justification",
        "who": "Entra Privileged Role Administrator (not the Fabric admin)", "automatable": False,
        "how": ("PIM assignment in Entra ID Governance — no Fabric tenant-setting API reaches this, and "
                "no Fabric admin can grant it to themselves"),
        "why": ("Fabric Administrator is an Entra built-in role carrying "
                "`microsoft.powerApps.powerBI/allEntities/allTasks` — the widest permission in the "
                "platform. Held permanently it is the largest standing attack surface the delivery has"),
        "required": "yes",
        "source": (_L + "entra/id-governance/privileged-identity-management/pim-how-to-add-role-to-user"),
        "verfahren": (
            "Assign **Fabric Administrator** as `Eligible`, never `Active` or `Permanent`; activation "
            "runs through PIM with an MFA check and a written justification. Two cloud-only break-glass "
            "accounts stay permanently assigned, deliberately outside this rule — an outage of the "
            "activation path must not lock the tenant out of its own platform.\n\n"
            "The capacity admin needs a different answer, and this is the part that gets missed: it is "
            "**not** an Entra role but a setting on the Fabric capacity, so PIM does not reach it. "
            "Assign it to a PIM-enabled security group instead and activate the group membership "
            "just in time.\n\n"
            "Entra ID P2 or ID Governance is a licence prerequisite, not a configuration step. Without "
            "it the whole procedure is unavailable and the fallback is a standing assignment to as few "
            "named people as possible, plus a Conditional Access policy enforcing MFA on them.\n\n"
            "Whether the rule actually holds is readable, and Microsoft Graph v1.0 answers it in three "
            "calls: resolve the role by display name through `roleManagement/directory/roleDefinitions`, "
            "then read `roleEligibilitySchedules` and `roleAssignmentSchedules` for that role id. "
            "Eligible-only means the first list is non-empty while the second carries no entry with "
            "`assignmentType: Assigned` outside the break-glass accounts. `Activated` is a PIM "
            "activation in flight, so it counts as the procedure working and not as a finding — adding "
            "the two together turns a healthy PIM into a false positive. Least-privileged read: "
            "`RoleEligibilitySchedule.Read.Directory`."),
        "grenzen": (
            "PIM covers Entra roles. The Fabric capacity admin is a capacity setting and is reachable "
            "only indirectly, through a PIM-enabled security group.",
            "Entra ID P2 / ID Governance is a licence, not a toggle — check it before promising the "
            "procedure.",
            "The break-glass accounts are exempt on purpose; they are the reason the rule can be "
            "strict everywhere else.",
            "The proof is a Graph read and not a Fabric one. It needs a directory read right the "
            "Fabric admin does not carry, so a collector running under that identity alone leaves "
            "this entry UNKNOWN — which is the honest answer, not a pass.",
        ),
    },
    # --- 20.08.2026: die sechs Schalter, die nach aussen fuehren (BK-Z06) --------------------
    #
    # Alle bisherigen Eintraege beantworten dieselbe Frage: *was muss an sein, damit die Lieferung
    # laeuft*. Diese sechs beantworten die Gegenfrage — *was muss aus sein, damit sie nicht mehr
    # kann, als sie soll*. Sie stehen deshalb auf ``base`` und ``required: yes``: eine Lieferung,
    # die sie nicht anfasst, hat sie nicht offen gelassen, weil jemand das wollte, sondern weil
    # niemand hingesehen hat.
    #
    # #24 ist der einzige Eintrag des Katalogs, der **ab Werk an** ist und trotzdem **aus** gehoert
    # (#1, #8 und #10 sind ebenfalls ab Werk an — dort ist das erwuenscht). Genau deshalb faellt er
    # durch jede Pruefliste, die nur fragt „ist alles Noetige eingeschaltet".
    #
    # Die Politik dahinter ist eine Kundenentscheidung und keine Katalogzeile — sie wird ueber
    # ``decision_proposals.propose_sharing_policy`` (SEC-SHARE) erhoben. Hier steht nur, welcher
    # Schalter wie heisst, wo er sitzt und was er ausdruecklich nicht abdeckt.
    {
        "id": 24, "name": "Share Fabric data with your Microsoft 365 services",
        "section": "Tenant settings → Share Fabric data with your Microsoft 365 services",
        "scope": "tenant", "capabilities": ["base"],
        "default": 'on — MS: "The … tenant setting is on by default" (same-geo tenants)',
        "target": "off; the cross-geography sub-toggle off in every case",
        "who": "Fabric tenant admin", "automatable": "unverified",
        "how": "Update Tenant Setting REST / sempy — or portal; changes take up to 24 hours",
        "why": ("mit diesem Schalter sendet Fabric von sich aus Metadaten an Microsoft 365 — "
                "Berichtsname, Beschreibung, Adresse, ACL, Arbeitsbereich, Ersteller, Seitennamen, "
                "Diagrammtitel sowie Spalten- und Measure-Namen, dazu wer welchen Bericht "
                "angesehen hat. Kein Nutzer muss dafuer etwas tun, und der Unter-Schalter fuer "
                "geografieuebergreifende Freigabe laesst diese Daten die Region verlassen"),
        "required": "yes",
        "source": _L + "fabric/admin/admin-share-power-bi-metadata-microsoft-365-services",
        "verfahren": (
            "Turn the main toggle **off** and re-check it after 24 hours — MS states changes take up to "
            "that long to take effect. The cross-geography toggle is only **visible while the main "
            "toggle is on**, so 'I don't see it' is not evidence that it is off: to read its state you "
            "have to switch the main one on first. Where the main toggle is deliberately left on, the "
            "sub-toggle is the DSGVO-relevant one and stays off."),
        "grenzen": (
            "Turning it off does not keep Fabric content out of Microsoft 365. Everything a user does "
            "deliberately keeps working: Excel PivotTables on semantic models, link previews in Teams "
            "and Outlook, and Fabric data agents in the M365 Agent Store. The setting governs only the "
            "background flow.",
            "The default is stated for tenants whose Fabric and M365 home regions match; for a split-geo "
            "tenant MS documents only the second toggle, not a different default.",
        ),
    },
    {
        "id": 25, "name": "Guest users can access Microsoft Fabric",
        "section": "Export and sharing settings", "scope": "tenant", "capabilities": ["base"],
        "default": "unverified — the settings page does not pin it",
        "target": "off unless guest access was decided (SEC-SHARE); if decided, scoped to a named "
                  "security group, never the whole organisation",
        "who": "Fabric tenant admin", "automatable": "unverified",
        "how": "Update Tenant Setting REST / sempy — or portal",
        "why": ("der Hauptschalter fuer Entra-B2B-Gaeste. Aus heisst: ein Gast bekommt einen Fehler, "
                "auch auf Elemente, fuer die er Berechtigungen hat — und niemand kann ueber "
                "Freigabe-Dialoge neue Gaeste einladen"),
        "required": "yes",
        "source": _L + "fabric/admin/service-admin-portal-export-sharing",
    },
    {
        "id": 26, "name": "Users can invite guest users to collaborate through item sharing and permissions",
        "alias": "Share content with external users",     # MS: "This setting was previously called …"
        "section": "Export and sharing settings", "scope": "tenant", "capabilities": ["base"],
        "default": "unverified — the settings page does not pin it",
        "target": "off — an invitation is a planned act, not a side effect of a share dialog",
        "who": "Fabric tenant admin", "automatable": "unverified",
        "how": "Update Tenant Setting REST / sempy — or portal",
        "why": ("mit ihm entstehen neue Gastkonten **durch Teilen**: wer einen Bericht teilt, laedt "
                "die fremde Adresse zugleich in die Organisation ein"),
        "required": "yes",
        "source": _L + "fabric/admin/service-admin-portal-export-sharing",
        "grenzen": (
            "It only governs invitations made through Fabric. The inviting user additionally needs the "
            "Entra *Guest Inviter* role, and guests invited elsewhere in the tenant are unaffected.",
        ),
    },
    {
        "id": 27, "name": "Allow shareable links to grant access to everyone in your organization",
        "section": "Export and sharing settings", "scope": "tenant", "capabilities": ["base"],
        "default": "unverified — the settings page does not pin it",
        "target": "off — sharing then falls back to 'Specific people' / 'People with existing access'",
        "who": "Fabric tenant admin", "automatable": "unverified",
        "how": "Update Tenant Setting REST / sempy — or portal",
        "why": ("der „Jeder mit dem Link\"-Fall: ein einziger Klick macht einen Bericht fuer die "
                "ganze Organisation lesbar, an jeder Rollen- und Domaenenlogik vorbei"),
        "required": "yes",
        "source": _L + "fabric/admin/service-admin-portal-export-sharing",
    },
    {
        "id": 28, "name": "Guest users can work with shared semantic models in their own tenants",
        "section": "Export and sharing settings", "scope": "tenant", "capabilities": ["base"],
        "default": 'off — MS: "This setting is off by default for customers"',
        "target": "stays off",
        "who": "Fabric tenant admin", "automatable": "unverified",
        "how": "Update Tenant Setting REST / sempy — or portal",
        "why": ("aus heisst nicht, dass der Gast das Modell nicht sieht — er sieht es weiterhin im "
                "liefernden Tenant. An heisst, er darf es im **eigenen** Tenant weiterverwenden und "
                "darauf aufbauen"),
        "required": "yes",
        "source": _L + "fabric/admin/service-admin-portal-export-sharing",
        "grenzen": (
            "Not the same switch as *External data sharing* (#11/#19): this one rides on Entra B2B and "
            "semantic models, the other on OneLake shares. MS says so explicitly, and the two are "
            "regularly confused because both read as 'external sharing'.",
        ),
    },
    {
        "id": 29, "name": "Publish to web",
        "section": "Export and sharing settings", "scope": "tenant", "capabilities": ["base"],
        "default": "unverified — the settings page does not pin it",
        "target": "disabled for the whole organisation; where a business case exists, 'Allow only "
                  "existing embed codes' instead of a free hand",
        "who": "Fabric tenant admin", "automatable": "unverified",
        "how": "Update Tenant Setting REST / sempy — or portal",
        "why": ("die einzige Freigabe der Plattform, die **ohne Anmeldung** liest: ein "
                "veroeffentlichter Bericht ist oeffentlich im Netz"),
        "required": "yes",
        "source": _L + "fabric/admin/service-admin-portal-export-sharing",
        "verfahren": (
            "Disabling for the whole organisation also stops existing published reports from rendering. "
            "Review the existing embed codes first — Admin portal → Embed codes lists them (a Govern "
            "equivalent was not checked on 2026-09-29: ANNAHME, ungeprueft) — because that list, not "
            "the toggle, tells you what is live on the web right now."),
    },
    # --- 29.09.2026: Fabric IQ in Microsoft 365 Copilot und der neue Copilot-Einstieg (I-21 W5.7) ---
    #
    # Beide Eintraege tragen das Feld ``lizenz``: die Lizenz, die der Schalter voraussetzt, als
    # ANNAHME der Lieferung. Warum ein Feld und kein Satz im ``why``: ob der Kunde die Lizenz hat,
    # ist eine Frage an den Kunden (vorlegen, nicht schaetzen), und ein Renderer, der sie stellen
    # soll, kann sie nur aus einem Feld stellen. Gelesen per Learn-MCP am 29.09.2026:
    # `fabric/iq/connectors/microsoft-365-copilot-overview` (GA, „Microsoft 365 Copilot Premium
    # license: Required for all users", RLS/OLS respektiert, Einstellung „enabled by default"),
    # `microsoft-365/copilot/copilot-powerbi-copilot-chat` (Weg im M365 admin center),
    # `fabric/iq/connectors/copilot-power-bi-fabric` (Preview, „off by default", Copilot Premium).
    {
        "id": 30, "name": "Fabric data in Microsoft Copilot",
        "alias": "Fabric data available in M365 Copilot",   # Name auf den Fabric-IQ-Seiten
        "section": "Microsoft 365 admin center → Copilot → Settings → View all (NOT a Fabric setting)",
        "scope": "m365", "capabilities": ["governance"],
        "default": 'on — MS: "The setting is enabled by default"',
        "target": "a decision, not the default: No users / Specific groups / All users — decided with "
                  "the data-protection owner before go-live (SEC-SHARE)",
        "who": "Microsoft 365 administrator (not the Fabric admin)", "automatable": False,
        "how": ("Microsoft 365 admin center → Copilot → Settings → View all → Fabric data in Microsoft "
                "Copilot → Step 1: No users / All users / Specific groups → Save. The Fabric tenant-"
                "setting API does not reach it"),
        "why": ("Fabric IQ in Microsoft 365 Copilot Chat and Cowork is GA and answers from Power BI "
                "reports and semantic models under the user's own permissions, RLS and OLS included. "
                "Nothing is exposed beyond those permissions — but the answers leave Power BI and "
                "mix with mail, chat and files, and that is a data-protection decision the delivery "
                "must not take by default"),
        "required": "yes",
        "lizenz": "Microsoft 365 Copilot Premium for every user who is to get answers "
                  "(ANNAHME, ungeprueft — to be confirmed by the customer, not assumed)",
        "source": _L + "fabric/iq/connectors/microsoft-365-copilot-overview",
        "grenzen": (
            "Turning it off hides Fabric context from Copilot responses; it does not change who can "
            "open the report in Power BI.",
            "#24 is a different switch on the Fabric side: it governs the background metadata flow "
            "(search, attachment menu). With #24 off, users can still paste a report link or name a "
            "report in the prompt.",
            "Semantic models in workspaces on Embedded capacities (A/EM SKUs) are not supported; Pro, "
            "PPU, Premium and Fabric capacities are.",
            "Power-BI-only regions are not supported.",
        ),
    },
    {
        "id": 31, "name": "Users can access Microsoft Copilot in Power BI and Microsoft Fabric (preview)",
        "section": "Copilot and Azure OpenAI Service", "scope": "tenant", "capabilities": ["copilot"],
        "default": 'off — MS: "This setting is off by default during the preview"',
        "target": "off in production while it is preview; on only for a named pilot group",
        "who": "Fabric tenant admin", "automatable": "unverified",
        "how": "Update Tenant Setting REST / sempy — or portal (settingName unconfirmed)",
        "why": ("the new Copilot entry point in Power BI and Fabric. Preview, and MS lists three more "
                "prerequisites next to it: #8, the Microsoft 365 setting #30, and a per-user licence"),
        "required": "if Copilot",
        "lizenz": "Copilot Premium per user (ANNAHME, ungeprueft — MS announces a later rollout for "
                  "users without it, capabilities not published)",
        "source": _L + "fabric/iq/connectors/copilot-power-bi-fabric",
    },
    # --- 01.10.2026: Exportwege nach Format (D-627, Signal SIG-2610-002) ---
    #
    # Zwei Felder statt Saetzen: ``label_vererbung`` (welches Sensitivity Label die Datei bekommt:
    # ``modell``, ``bericht`` oder ``keine``) und ``max_zeilen`` (Obergrenze laut Learn). Daran haengt
    # die Empfehlung: ein Format ohne Label wird nicht fuer die ganze Organisation geoeffnet, wenn der
    # Mandant Labels nutzt. Microsoft empfiehlt sonst, Export fuer die meisten Nutzer offen zu lassen
    # (power-bi/guidance/powerbi-implementation-planning-info-protection). Gelesen per Learn-MCP am
    # 01.10.2026: `fabric/admin/service-admin-portal-export-sharing`,
    # `power-bi/visuals/power-bi-visualization-export-data` (Excel live 500.000, Excel 150.000,
    # CSV 30.000; „The first two support sensitivity labels"), `fabric/governance/information-
    # protection` (labelbasierte Zugriffskontrolle gilt nicht fuer .csv/.txt).
    {
        "id": 32, "name": "Export to Excel",
        "section": "Export and sharing settings", "scope": "tenant", "capabilities": ["base"],
        "default": "unverified — the settings page does not pin it",
        "target": "on for the organisation",
        "who": "Fabric tenant admin", "automatable": "unverified",
        "how": "Update Tenant Setting REST / sempy — or portal",
        "why": ("statischer Excel-Export aus einem Visual; die Datei erbt das Label des Berichts und "
                "dessen Verschluesselung"),
        "required": "yes",
        "label_vererbung": "bericht", "max_zeilen": 150000,
        "source": _L + "fabric/admin/service-admin-portal-export-sharing",
    },
    {
        "id": 33, "name": "Users can work with semantic models in Excel using a live connection",
        "section": "Export and sharing settings", "scope": "tenant", "capabilities": ["base"],
        "default": "unverified — the settings page does not pin it",
        "target": "on for the organisation",
        "who": "Fabric tenant admin", "automatable": "unverified",
        "how": "Update Tenant Setting REST / sempy — or portal",
        "why": ("Excel mit Live-Verbindung und Analyze in Excel ueber den XMLA-Endpunkt; bis 500.000 "
                "Zeilen, die Datei erbt das Label des Semantikmodells, RLS greift weiter"),
        "required": "yes",
        "label_vererbung": "modell", "max_zeilen": 500000,
        # UNKLAR (SIG-2610-002): die Feature Summary hebt auch „Data with current layout" auf 500.000,
        # Learn nennt am 01.10.2026 dafuer weiter 150.000 Datenschnittpunkte. Fuer die Empfehlung
        # unerheblich; kein ``grenzen``-Eintrag, weil es kein Verfahrensschritt ist.
        "source": _L + "fabric/admin/service-admin-portal-export-sharing",
    },
    {
        "id": 34, "name": "Export to .csv",
        "section": "Export and sharing settings", "scope": "tenant", "capabilities": ["base"],
        "default": "unverified — the settings page does not pin it",
        "target": "when the tenant uses sensitivity labels: only a named security group; otherwise on "
                  "for the organisation",
        "who": "Fabric tenant admin", "automatable": "unverified",
        "how": "Update Tenant Setting REST / sempy — or portal",
        "why": ("der einzige Exportweg ohne Label: eine CSV-Datei verliert Beschriftung und "
                "Verschluesselung, labelbasierte Zugriffskontrolle greift fuer .csv nicht"),
        "required": "yes",
        "label_vererbung": "keine", "max_zeilen": 30000,
        "source": _L + "fabric/admin/service-admin-portal-export-sharing",
    },
    {
        "id": 35, "name": "Download reports",
        "section": "Export and sharing settings", "scope": "tenant", "capabilities": ["base"],
        "default": "unverified — the settings page does not pin it",
        "target": "the report-creator group, not the whole organisation",
        "who": "Fabric tenant admin", "automatable": "unverified",
        "how": "Update Tenant Setting REST / sempy — or portal",
        "why": ("laedt .pbix-Dateien und paginierte Berichte herunter; bei Import-Modellen liegen die "
                "Daten damit vollstaendig auf dem Rechner"),
        "required": "yes",
        "label_vererbung": "bericht", "max_zeilen": None,
        "source": _L + "fabric/admin/service-admin-portal-export-sharing",
    },
]

_BY_ID = {s["id"]: s for s in CATALOG}


def required_settings(capabilities: Iterable[str]) -> list[dict[str, Any]]:
    """Return the catalog settings gated by ``capabilities`` (agnostic feature keys; see ``CAPABILITIES``).
    ``base`` is always included. Unknown keys are ignored. Sorted by catalog id. Pure/deterministic."""
    wanted = set(capabilities) | {"base"}
    return [s for s in CATALOG if set(s["capabilities"]) & wanted]


def procedural_settings(capabilities: Iterable[str]) -> list[dict[str, Any]]:
    """Die geforderten Settings, bei denen der Schalter allein nicht die Antwort ist.

    Also die mit ``verfahren`` (was nach dem Umlegen zu tun ist) und/oder ``grenzen`` (was die
    Einstellung ausdruecklich nicht abdeckt). Eigene Funktion statt eines ``s.get("verfahren")``
    im Renderer: sonst entscheidet der Renderer, was als Haertung gilt, und der naechste Renderer
    entscheidet es anders. Sortiert nach Katalog-Id; rein."""
    return [s for s in required_settings(capabilities) if s.get("verfahren") or s.get("grenzen")]


def lizenzannahmen(capabilities: Iterable[str]) -> list[dict[str, Any]]:
    """Die Lizenzannahmen der geforderten Settings: ``[{id, name, lizenz}]``, sortiert nach Id.

    Eine Lizenz ist keine Einstellung, und die Lieferung kann sie nicht setzen — sie kann sie nur
    **vorlegen**. Deshalb eine eigene Liste: der Renderer stellt sie als Frage an den Kunden, und ein
    Test kann zaehlen, ob jede lizenzpflichtige Einstellung ihre Annahme traegt (I-21 W5.7)."""
    return [{"id": s["id"], "name": s["name"], "lizenz": s["lizenz"]}
            for s in required_settings(capabilities) if s.get("lizenz")]


def settability_summary(capabilities: Iterable[str]) -> dict[str, Any]:
    """Split the required settings into what a one-day setup can SCRIPT vs what needs a HUMAN.

    Returns ``{scriptable[], scriptable_unverified[], needs_human[], api_caveat, grounding_date}``
    where each list holds ``(id, name, how)`` tuples. ``scriptable`` = tenant settings settable via the
    Update Tenant Setting API; ``scriptable_unverified`` = tenant settings whose API round-trip
    MS docs don't individually confirm (smoke-test first); ``needs_human`` = capacity-admin / RBAC actions
    that no tenant-settings script can perform."""
    req = required_settings(capabilities)
    def _t(s: dict) -> tuple[int, str, str]:
        return (s["id"], s["name"], s["how"])
    return {
        "scriptable": [_t(s) for s in req if s["automatable"] is True],
        "scriptable_unverified": [_t(s) for s in req if s["automatable"] == "unverified"],
        "needs_human": [_t(s) for s in req if s["automatable"] is False],
        "api_caveat": API_CAVEAT,
        "grounding_date": GROUNDING_DATE,
    }


def profile_from_blueprint(bp: dict) -> set[str]:
    """Derive the capability profile from a blueprint IR (agnostic): governance when any domain publishes,
    sharing when the blueprint declares external sharing, and the AI capabilities when
    ``ai_grounding`` declares a Data Agent / an Ontology. ``base`` is always present.

    Der letzte Teil ist neu (30.07.2026) und schliesst einen Umweg: bis dahin hingen Data Agent und
    Ontologie nur an CLI-Flags, also musste ein ``extra_capabilities`` von der Kommandozeile durch
    ``emit_platform`` bis hierher gereicht werden, damit das Gate ueberhaupt die richtigen
    Tenant-Schalter prueft. Jetzt steht es in der IR, wo es hingehoert, und diese Ableitung ist wieder
    rein blueprint-basiert. Der ``extra_capabilities``-Weg bleibt als **Rueckfall** bestehen: eine
    Lieferung, die die Flags ohne IR-Deklaration nutzt, soll weiterhin korrekt gegated werden.
    """
    caps = {"base"}
    if any(d.get("publishing") for d in bp.get("mesh", {}).get("domains", []) or []):
        caps.add("governance")
    if bp.get("sharing"):
        caps.add("sharing")
    ai = bp.get("ai_grounding") or {}
    if (ai.get("data_agent") or {}).get("enabled"):
        caps |= {"data_agents", "copilot"}      # Data Agents reiten auf den Copilot-Schaltern
    if (ai.get("ontology") or {}).get("enabled"):
        caps.add("ontology")
    # D-606: der Zugangsweg `fabric_copilot` in `platform.ai_zugang` zieht die Copilot-Schalter
    # (#8, #9, #31). `m365_copilot` braucht keine Faehigkeit: #30 steht ohnehin im Profil
    # (governance), sein ZIEL haengt am Zugangsweg (`ki_zugang.wirkung` → m365_schalter).
    # Bewusst ohne Import von `ki_zugang`: dieses Modul reist als Standard-Python in
    # `readiness/lib/` mit. Dieselbe Regel steht in `ki_zugang.wirkung["tenant_faehigkeiten"]`;
    # `test_ki_zugang.py` stellt beide gegeneinander.
    if "fabric_copilot" in ((bp.get("platform") or {}).get("ai_zugang") or []):
        caps.add("copilot")
    return caps
