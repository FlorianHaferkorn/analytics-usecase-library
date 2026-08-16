"""admin_settings — the Fabric admin/tenant/capacity/workspace settings a customer delivery needs, as a
cited catalog + a capability-keyed planner. Readiness-Gate (sibling of ``capacity_recommend.py``).

The directive: *define the admin settings so one can, within a day, set what one needs how.* This module
is the machine-readable **definition**. Given the set of **capabilities** a delivery actually uses
(agnostic, feature-keyed — not source- or pattern-specific), ``required_settings`` returns exactly the
settings that gate it, each carrying: the exact portal name + section, its **scope** (``SCOPES`` —
tenant / capacity / workspace / entra), **default**, **who** can set it, the **target** value for the
delivery, and — the crux of
"within a day" — whether it is **automatable** via the Fabric *Update Tenant Setting* Admin REST API
(preview) / ``sempy`` or needs a **human** admin (capacity-admin portal action, or an RBAC grant a
privileged human must perform). ``settability_summary`` splits the plan into "scriptable" vs "needs a
human" so the one-day setup is honest about what can be automated.

Honest by construction: settings MS docs do not pin (default state, or whether a specific setting
round-trips through the generic preview API) are marked ``"unverified"`` rather than guessed; the
*Update Tenant Setting* API itself is MS-flagged **preview / not for production**, surfaced as a caveat.

Tool-Reuse: this is the single source of truth for the tenant-settings knowledge that
``provision_apply._tenant_setup_md`` renders (that checklist now reads from this catalog — no second silo).

Reachability (aufgeloest 30.07.2026): ``profile_from_blueprint`` leitet jetzt auch ``copilot``/
``data_agents``/``ontology`` ab — die IR drueckt sie ueber ``ai_grounding.data_agent`` bzw.
``ai_grounding.ontology`` aus. Die frueher hier notierte Lucke ("the blueprint IR has no field that
expresses Copilot / Data Agents yet") ist damit zu; ein Umweg ueber explizit uebergebene Capabilities
ist nicht mehr noetig, bleibt aber moeglich (die CLI nutzt ihn als Rueckfall, wenn jemand die
Emit-Flags ohne IR-Deklaration fahrt).

Grounding date: 2026-07-24. Sources are per-setting ``source`` URLs (learn.microsoft.com), verified then.
Cross-cutting: Update Tenant Setting API is generic over an opaque ``settingName`` but PREVIEW —
  learn.microsoft.com/rest/api/fabric/admin/tenants/update-tenant-setting
  learn.microsoft.com/rest/api/fabric/admin/tenants/list-tenant-settings (settingName ``CertifyDatasets`` shown).
"""
from __future__ import annotations

from typing import Any, Iterable

GROUNDING_DATE = "2026-07-24"

#: The scopes a catalog entry can sit in. ``entra`` joined the set on 2026-08-16 with #23 and it is a
#: widening, not a typo: an admin role hardened through PIM is not a Fabric setting at all — no tenant,
#: capacity or workspace surface carries it. Filing it under ``tenant`` would have been the convenient
#: lie, and it would have sent an admin to the Fabric admin portal to look for something that lives in
#: Entra. The set is a constant so the catalog and its test read the same list.
SCOPES = ("tenant", "capacity", "workspace", "entra")

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
    "ontology": "Fabric IQ Ontology item (preview)",
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
        "how": "Update Tenant Setting REST (preview) / sempy — or portal",
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
        "how": "Update Tenant Setting REST (preview) / sempy — or portal",
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
        "how": "Update Tenant Setting REST (preview) / sempy — or portal (preview item switch)",
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
        "how": "Update Tenant Setting REST (preview) / sempy — or portal",
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
        "how": "Update Tenant Setting REST (preview) / sempy — or portal",
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
        "how": ("capacity-admin portal action: Admin Portal → Capacity settings → select the capacity "
                "→ Surge protection → Background Operations On → rejection + recovery threshold → Apply"),
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
            "minutes, so the cap is soft; and raising the limit does **not** release a workspace that "
            "is already blocked, a capacity admin sets it back to *Available* by hand."),
        "grenzen": (
            "Fabric SKUs only — no other SKU type is supported.",
            "In-progress jobs are not stopped, so the rejection threshold is not an upper bound on the "
            "24-hour background percentage: running jobs keep reporting usage past it.",
            "Operations billed with Autoscale are not blocked.",
            "OneLake activities are unaffected.",
            "It does not guarantee interactive requests escape delay or rejection — at the capacity's "
            "maximum compute limit they are delayed or rejected regardless.",
            "Workspace level: Dataflows Gen1, paginated reports, scorecards, graph models, Activator "
            "and Dataflow Gen2 editing are outside its reach; Autoscale compute is excluded from the "
            "per-workspace calculation.",
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
            "named people as possible, plus a Conditional Access policy enforcing MFA on them."),
        "grenzen": (
            "PIM covers Entra roles. The Fabric capacity admin is a capacity setting and is reachable "
            "only indirectly, through a PIM-enabled security group.",
            "Entra ID P2 / ID Governance is a licence, not a toggle — check it before promising the "
            "procedure.",
            "The break-glass accounts are exempt on purpose; they are the reason the rule can be "
            "strict everywhere else.",
        ),
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
    return caps
