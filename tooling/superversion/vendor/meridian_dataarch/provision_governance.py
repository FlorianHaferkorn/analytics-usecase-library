"""provision_governance — emit security & governance materialisation from a blueprint.

Fifth live-provisioning helper (ADR-0015 follow-up), sibling to provision_fabric / cicd /
transforms / orchestration. Closes the last of the five original gaps: it turns the
blueprint's mesh (domains, endorsement intent, intended audience, gold products) into the
governance layer, grounded in the researched Fabric governance surface
(meridian/docs/research/2026-07-15_fabric-automation-landscape.md §3).

Per capability, emitted at the fidelity the Fabric API actually supports (honest by
construction — never claims automation that Microsoft does not offer):

- RLS/OLS  → **TMDL role blocks** (deliverable-grade; deploys via Update-Definition/XMLA).
- Workspace roles / Domains / Sensitivity labels → idempotent REST/`fab api` templates
  (GA) with GET→diff→apply intent; tenant GUIDs/principals are VERIFY placeholders.
- OneLake data access roles → a declarative dataAccessRoles PUT payload, **Preview-gated**.
- Endorsement (Promoted/Certified) → an audit + **manual runbook**, because Fabric exposes
  **no supported write API** for endorsement (set is portal-only).

This module **does not execute** anything — it only emits text.
"""
from __future__ import annotations

import json
import re

_NONWORD_RE = re.compile(r"[^a-z0-9]+")


def _dirslug(name: str) -> str:
    return _NONWORD_RE.sub("-", (name or "").lower()).strip("-")


def _ident(name: str) -> str:
    return _NONWORD_RE.sub("_", (name or "").lower()).strip("_")


def _domains(bp: dict) -> list[dict]:
    return sorted(bp.get("mesh", {}).get("domains", []), key=lambda d: d.get("name", ""))


def _rls_tmdl(domain: str, gold_products: list[str], audience: str, sensitivity: dict | None = None) -> str:
    """A TMDL RLS/OLS role scaffold for a domain (GA; deploys via Update-Definition/XMLA).

    Honest by construction: the role structure + table refs are derived from the IR, but the
    DAX row filter is domain policy (not in the IR) → TODO(contract). Column-level (OLS) hiding is
    concrete when a ``sensitivity`` map (table → [sensitive columns]) is supplied — each sensitive
    column is named in a ``metadataPermission: none`` directive to hide it from this role.
    """
    sensitivity = sensitivity or {}
    dident = _ident(domain)
    lines = [
        f"/// RLS/OLS role for domain '{domain}' (intended audience: {audience}).",
        f"/// Deploy via Fabric Update-Definition REST or XMLA (TMSL Roles). Members set separately",
        f"/// via the Power BI security API — service principals cannot be RLS/OLS members.",
        f"createOrReplace",
        f"\trole rls_{dident}",
        f"\t\tmodelPermission: read",
        "",
    ]
    for gp in sorted(gold_products):
        lines += [
            f"\t\ttablePermission {gp} =",
            f"\t\t\t/// TODO(contract): DAX row filter for '{domain}' — e.g. [Region] = USERPRINCIPALNAME()",
            f"\t\t\ttrue",
        ]
        scols = sorted(sensitivity.get(gp, []) or [])
        if scols:
            for col in scols:
                lines += [f"\t\tcolumnPermission {gp}.{col}",
                          f"\t\t\tmetadataPermission: none   /// OLS: hide sensitive column"]
        else:
            lines.append(f"\t\t\t/// OLS: declare sensitive columns via --sensitivity to hide them (metadataPermission: none)")
        lines.append("")
    return "\n".join(lines) + "\n"


def model_roles(bp: dict, sensitivity: dict | None = None) -> list:
    """Die RLS/OLS-Rollen **für das ausgelieferte Semantikmodell** — je Domäne eine.

    Dieselbe Ableitung wie ``_rls_tmdl`` (Rollenname, Tabellen, sensible Spalten), aber als
    ``Role``-Objekte für den TMDL-Serializer, damit das Modell die Rollen wirklich trägt. Vorher
    entschied die Pipeline eine RLS-Achse und emittierte ein Rollen-Gerüst *daneben* — das Modell
    selbst ging ohne Rollen raus, was der Regelkatalog zu Recht als ``SEC001`` meldete.

    **Der Filter ist ``FALSE()``, nicht ``true``** — und das ist der Unterschied, auf den es
    ankommt. Der DAX-Zeilenfilter ist Domänen-Policy und steht nicht im IR. Ein Platzhalter, der
    ``true`` filtert, gibt jedem Mitglied dieser Rolle **alle** Zeilen und ist von funktionierender
    Sicherheit nicht zu unterscheiden. ``FALSE()`` schlägt sichtbar fehl: wer die Rolle zuweist,
    ohne die Policy zu füllen, sieht nichts und merkt es sofort. Solange niemand Mitglied ist,
    ändert die Rolle ohnehin nichts — sie kostet also nichts und schließt die Lücke.

    Das separat emittierte Gerüst (``_rls_tmdl``) behält bewusst ``true``: es wird von Hand
    deployt, von jemandem, der das ``TODO(contract)`` daneben liest.
    """
    from core.pbi_engine.parsers.tmdl_parser import Role, RoleColumnPermission, RoleTablePermission

    sensitivity = sensitivity or {}
    roles = []
    for domain in _domains(bp):
        products = sorted(domain.get("data_products", []) or [])
        if not products:
            continue
        table_perms = [
            RoleTablePermission(
                table=gp,
                # TODO(contract) im Ausdruck selbst: er wandert mit der Rolle mit, auch wenn
                # jemand nur die Rollendefinition ansieht.
                filter_expression="FALSE() /* TODO(contract): DAX-Zeilenfilter der Domäne "
                                  f"'{domain.get('name')}' — bis dahin bewusst restriktiv */",
            )
            for gp in products
        ]
        col_perms = [
            RoleColumnPermission(table=gp, column=col, metadata_permission="none")
            for gp in products for col in sorted(sensitivity.get(gp, []) or [])
        ]
        roles.append(Role(name=f"rls_{_ident(domain.get('name', ''))}",
                          model_permission="read",
                          table_permissions=table_perms,
                          column_permissions=col_perms))
    return roles


def _governance_script(bp: dict, workspace: str, governance: dict, dom_owner: dict | None = None) -> str:
    """Idempotent REST/`fab api` templates for workspace roles + domains (GA).

    ``dom_owner`` (domain-en-label → owner role, from governance.json) drives real
    owner→workspace-Admin role assignments — the Data-Gov stream's owners become RBAC.
    """
    dom_owner = dom_owner or {}
    domains = _domains(bp)
    lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        "# ArchitectureBlueprint → Fabric governance (ADR-0015). Generated; review before running.",
        "# Grounded in the GA governance REST surface (research 2026-07-15 §3):",
        "#   POST /v1/workspaces/{id}/roleAssignments        — workspace RBAC (GET→diff→POST/DELETE)",
        "#   POST /v1/admin/domains  + .../assignWorkspacesByIds  — OneLake data-mesh domains",
        "# Reached via `fab api <endpoint> -X POST -i <body.json>` (confirm flags: fab api -h).",
        "# Auth: a service principal is fine for roleAssignments; DOMAINS need a Fabric-admin USER",
        "# context (SP not supported) — see research §3.",
        "",
        "# 1. Domains (data mesh) — one Fabric domain per blueprint domain; assign its workspace(s).",
    ]
    for d in domains:
        dn = d["name"]
        wss = ", ".join(w["name"] for w in d.get("workspaces", [])) or workspace
        lines.append(f"# {dn}  (workspaces: {wss})")
        lines.append(f'#   fab api "admin/domains" -X POST -i - <<JSON   # VERIFY: capture domain id')
        lines.append(f'#   {{"displayName":"{dn}"}}')
        lines.append("#   JSON")
        lines.append(f'#   fab api "admin/domains/<{_dirslug(dn)}-id>/assignWorkspacesByIds" -X POST -i - <<JSON')
        lines.append(f'#   {{"workspacesIds":["<workspace-id>"]}}')
        lines.append("#   JSON")
    lines.append("")
    if dom_owner:
        lines.append("# 1b. Data owners → workspace Admin (from governance.json data_owners).")
        lines.append("#     The owner ROLE is the SoT; fill its actual principal id in --governance.")
        for d in domains:
            owner = dom_owner.get(d["name"].strip().lower())
            if owner:
                for w in d.get("workspaces", []):
                    lines.append(f'#   {w["name"]}: Admin for owner "{owner}"')
                    lines.append(f'#   fab api "workspaces/<{w["name"]}-id>/roleAssignments" -X POST -i - <<JSON')
                    lines.append(f'#   {{"principal":{{"id":"<{_dirslug(owner)}-principal-id>","type":"Group"}},"role":"Admin"}}')
                    lines.append("#   JSON")
        lines.append("")
    lines.append("# 2. Workspace roles (RBAC) — reconcile each workspace to the desired principals.")
    lines.append("#    audience → principals come from your local --governance map (secrets stay local).")
    roles_map = (governance or {}).get("roles", {})
    for d in domains:
        aud = d.get("publishing", {}).get("intended_audience", "internal")
        principals = roles_map.get(aud) or roles_map.get(d["name"]) or []
        for w in d.get("workspaces", []):
            if principals:
                for p in principals:
                    body = json.dumps({"principal": {"id": p.get("id", "<id>"), "type": p.get("type", "Group")},
                                       "role": p.get("role", "Viewer")}, ensure_ascii=False)
                    lines.append(f'#   fab api "workspaces/<{w["name"]}-id>/roleAssignments" -X POST -i - <<JSON')
                    lines.append(f"#   {body}")
                    lines.append("#   JSON")
            else:
                lines.append(f'#   {w["name"]} ({aud}): provide principals in --governance roles.{aud} → roleAssignments')
    lines.append("")
    lines.append('echo "Governance script complete."')
    return "\n".join(lines) + "\n"


def _sensitivity_script(bp: dict, governance: dict) -> str:
    """Bulk sensitivity-label templates via the Power BI admin API (GA)."""
    labels = (governance or {}).get("labels", {})
    lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        "# Sensitivity labels (Microsoft Purview Information Protection) — GA bulk admin API.",
        "#   POST /v1.0/myorg/admin/informationProtection/setLabelsAsAdmin",
        "#   limits: <=25 req/hr, <=2000 items/req; needs Fabric admin + Tenant.ReadWrite.All + label in policy.",
        "# labelId per audience comes from your local --governance map (labels.<audience>).",
        "",
    ]
    for d in _domains(bp):
        aud = d.get("publishing", {}).get("intended_audience", "internal")
        label = labels.get(aud, f"<{aud}-labelId>")
        lines.append(f"# {d['name']} ({aud}) → label {label}")
        lines.append(f'#   fab api "admin/informationProtection/setLabelsAsAdmin" -X POST -i - <<JSON')
        lines.append(f'#   {{"labelId":"{label}","assignmentMethod":"Standard","artifacts":[{{"artifactType":"<SemanticModel|Report>","id":"<item-id>"}}]}}')
        lines.append("#   JSON")
    lines.append("")
    lines.append('echo "Sensitivity-label script complete."')
    return "\n".join(lines) + "\n"


def _rls_proposal_comment(catalog: dict | None) -> str:
    """The pre-thought RLS predicate as a COMMENT — so whoever opens the payload sees a concrete
    proposal instead of only a deny-all. Deliberately not in the payload: the executable rule stays
    fail-closed until a human confirms (Tool-Reuse: the proposal engine owns the heuristic)."""
    if not catalog:
        return ""
    from core.dataarch_engine.blueprint.decision_proposals import propose_rls
    p = propose_rls(catalog)
    if not p.get("proposal"):
        return "// RLS-VORSCHLAG: keine Org-Spalte im Modell erkannt — Scoping-Achse im Workshop klären.\n"
    first = p["proposal"].split("\n")[0].strip()
    return ("// RLS-VORSCHLAG (zu bestätigen, ersetzt das deny-all oben — nichts läuft ungeprüft):\n"
            f"//   {first}\n"
            f"//   Konfidenz: {p['confidence']} · hergeleitet aus: {p['derived_from']}\n"
            "//   Volle Begründung + Alternativen: decisions/ENTSCHEIDUNGSVORLAGE.md (SEC-RLS)\n")


def _onelake_security_roles(bp: dict, lakehouse: str, sensitivity: dict | None = None,
                            catalog: dict | None = None) -> str:
    """OneLake Security roles — the **primary, engine-unified** RLS/CLS/OLS layer: defined once
    on the lakehouse, enforced across Spark, notebooks, the lakehouse, the SQL analytics endpoint
    and Direct-Lake-on-OneLake semantic models (MS Learn 2026-07, OneLake security).

    Grounded in the REST reference *OneLake Data Access Security — Create Or Update Data Access
    Roles* (Preview): ``PUT /v1/workspaces/{ws}/items/{itemId}/dataAccessRoles``. Honest by
    construction — only the IR-derivable parts are filled, the policy parts are workshop-owned:

    - **Table access (OLS)** ← the domain's gold products. Each rule carries the two mandatory
      ``PermissionScope`` objects the API requires: ``Path`` (``/Tables/<t>``) + ``Action`` (Read).
    - **RLS** (``constraints.rows[].value``, a T-SQL predicate) → scaffolded **fail-closed** on
      each fact (``where 1=0`` = deny-all) so an un-authored rule never leaks rows; the real
      predicate is domain policy (not in the IR) → workshop replaces ``1=0``.
    - **CLS** (``constraints.columns[]``) → **not guessed** (which columns are sensitive is domain
      policy). The exact shape to add is documented in ``ACCESS_LAYER_DECISION.md``.

    Principals (``microsoftEntraMembers``) + the item GUIDs are VERIFY placeholders (tenant-specific).
    """
    sensitivity = sensitivity or {}
    cols_by_table = {t["name"]: sorted(t.get("columns", []) or []) for t in (catalog or {}).get("tables", [])}
    cls_todo: list[str] = []
    roles = []
    for d in _domains(bp):
        dident = _ident(d["name"])
        tables = sorted(d.get("data_products", []))
        rule: dict = {
            "effect": "Permit",
            "permission": [
                {"attributeName": "Path", "attributeValueIncludedIn": [f"/Tables/{t}" for t in tables]},
                {"attributeName": "Action", "attributeValueIncludedIn": ["Read"]},
            ],
        }
        constraints: dict = {}
        # RLS on the domain's fact tables (naming-convention fact_* — the layer prefix the
        # generator enforces). Fail-closed: 1=0 denies all rows until the workshop authors the
        # predicate; an invalid/absent predicate is deny-all by OneLake anyway (safe default).
        rows = [{"tablePath": f"/Tables/{t}", "value": f"select * from {t} where 1=0"}
                for t in tables if t.startswith("fact_")]
        if rows:
            constraints["rows"] = rows
        # CLS: OneLake CLS *permits visible* columns (unlisted → null), so to HIDE the sensitive
        # ones we Permit the complement. This needs the full column list (governed catalog); without
        # it we can't compute the complement → record a TODO rather than guess.
        cols = []
        for t in tables:
            scols = sorted(sensitivity.get(t, []) or [])
            if not scols:
                continue
            full = cols_by_table.get(t)
            if full:
                visible = [c for c in full if c not in set(scols)]
                cols.append({"tablePath": f"/Tables/{t}", "columnNames": visible,
                             "columnEffect": "Permit", "columnAction": ["Read"]})
            else:
                cls_todo.append(f"{t}: hide {', '.join(scols)} (needs the full column list — supply the "
                                f"governed catalog to auto-compute the Permit-complement)")
        if cols:
            constraints["columns"] = cols
        if constraints:
            rule["constraints"] = constraints
        roles.append({
            "name": f"read_{dident}",
            "kind": "Policy",
            "decisionRules": [rule],
            "members": {"microsoftEntraMembers": [
                {"objectId": "<VERIFY: Entra group objectId>", "objectType": "Group",
                 "tenantId": "<TENANT_GUID>"}]},
        })
    payload = {"value": sorted(roles, key=lambda r: r["name"])}
    header = (
        "// OneLake Security roles — the PRIMARY RLS/CLS/OLS layer (define once, enforced across\n"
        "// ALL Fabric engines incl. Direct-Lake-on-OneLake). API: PUT /v1/workspaces/{ws}/items/\n"
        "// {lakehouseId}/dataAccessRoles  — status PREVIEW (OneLake.ReadWrite.All; dryRun=true + ETag).\n"
        "// RLS: constraints.rows[].value is FAIL-CLOSED (1=0 = deny-all) — replace with the domain\n"
        "// row predicate (T-SQL), e.g. \"select * from fact where [division] = USER_NAME()\".\n"
        "// CLS: constraints.columns Permits the VISIBLE columns (unlisted → null). Declared sensitive\n"
        "//   columns (--sensitivity) are hidden by Permitting the complement — computed from the governed\n"
        "//   catalog's full column list. No sensitivity declared → no CLS (nothing guessed).\n"
        "// Constraint: one role must hold BOTH the RLS and the CLS for a table — RLS in role A +\n"
        "// CLS in role B for the same user fails the query. Privileged workspace roles bypass RLS/CLS.\n"
        + ("".join(f"// CLS-TODO: {t}\n" for t in cls_todo) if cls_todo else "")
        + _rls_proposal_comment(catalog))
    return header + json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _access_layer_decision(bp: dict) -> str:
    """The explicit data-access-layer decision: WHERE RLS/CLS/OLS is enforced and why. Grounded in
    MS Learn (2026-07): Integrate Direct Lake security, OneLake security, SQL-endpoint security.
    Emitted because the choice is non-obvious and has correctness traps with Direct Lake."""
    n = len(_domains(bp))
    return "".join(line + "\n" for line in [
        "# Access-layer decision — where to enforce RLS / CLS / OLS",
        "",
        f"Domains in scope: **{n}**. Fabric offers three enforcement layers; they behave differently,",
        "especially under Direct Lake. Pick deliberately (grounded: MS Learn, *Integrate Direct Lake",
        "security* · *OneLake security* · *SQL-endpoint security*, 2026-07).",
        "",
        "## The three layers",
        "",
        "| Layer | Covers | Enforced for | Use when |",
        "|---|---|---|---|",
        "| **OneLake Security** (recommended) | RLS + CLS + OLS | **All engines** — Spark, notebook, "
        "lakehouse, SQL endpoint, Direct-Lake-on-OneLake — *define once* | Unified access control across "
        "every path. High in-memory performance retained. |",
        "| **Semantic-model** (TMDL roles, DAX) | RLS + OLS | That one model only | Consumers get **no** "
        "lakehouse access **and** the connection uses a **fixed identity** (not SSO). |",
        "| **SQL analytics endpoint** (T-SQL `CREATE SECURITY POLICY` / `GRANT`) | RLS + CLS + OLS | SQL/TDS "
        "context only | Classic SQL tooling / DBAs; delegated identity mode. |",
        "",
        "## Recommendation",
        "",
        "**Enforce in OneLake Security** and serve reports via **Direct Lake on OneLake** → the rules apply",
        "consistently to every engine with one definition. This repo emits that as the primary artifact",
        "(`onelake_data_access_roles.json`); the per-model TMDL roles (`roles/<domain>.tmdl`) stay as the",
        "**alternative** for the fixed-identity, model-only case.",
        "",
        "## Caveats that make the choice non-obvious (grounded)",
        "",
        "- **Direct Lake does not honor SQL-endpoint OLS/RLS in memory.** A query touching a SQL-endpoint "
        "OLS/CLS-restricted object **errors**; a table under SQL-endpoint RLS (or a view) **falls back to "
        "DirectQuery** — and *fails* if DirectQuery fallback is disabled. → for Direct Lake, enforce in "
        "OneLake or the model, **not** the SQL endpoint.",
        "- **SQL security is not translated to OneLake.** Data reached via a **shortcut** ignores SQL-defined "
        "RLS/CLS → the shortcut consumer sees everything. OneLake Security closes this.",
        "- **One role for combined RLS+CLS.** A user in role A (RLS) + role B (CLS) on the same table → the "
        "query **fails**. Put both constraints in a single role.",
        "- **Privileged roles bypass data rules.** Workspace **Admin/Member/Contributor** are not filtered by "
        "RLS/CLS (they have Write); rules apply to **Viewer** and users granted via OneLake roles. Semantic-"
        "model rules likewise don't apply to users with **Write** on the model.",
        "- **Delta-parquet only.** RLS/CLS apply to Delta tables; non-Delta objects in a secured role are "
        "**blocked**, not filtered.",
        "- **Direct Lake on OneLake combines roles** by *union* of OneLake roles, then *intersect* with any "
        "Direct Lake model roles. Sync OneLake→SQL endpoint can take up to **5 min** (roles get an `OLS_` prefix).",
    ])


def _endorsement_runbook(bp: dict) -> str:
    """Audit + manual runbook — Fabric has NO supported write API for endorsement."""
    lines = [
        "# Endorsement runbook (manual — ADR-0015)", "",
        "Fabric exposes **no supported write API** for endorsement (Promoted/Certified) — setting it is",
        "portal-only (research §3). This is the desired end-state from the blueprint; apply it by hand in the",
        "workspace item settings, or audit drift against it.", "",
        "| Domain | Gold products | Desired endorsement |", "|---|---|---|",
    ]
    for d in _domains(bp):
        gp = ", ".join(sorted(d.get("data_products", []))) or "—"
        end = d.get("publishing", {}).get("endorsement", "none")
        lines.append(f"| {d['name']} | {gp} | {end} |")
    lines.append("")
    lines.append("Certification additionally requires an admin-authorised security group (tenant setting, "
                 "delegable to domain admins).")
    return "\n".join(lines) + "\n"


def _gov_owner_index(gd: dict) -> tuple[dict, dict]:
    """Return (domain_en_label_lower → owner_role, owner_id → role) from a governance.json."""
    owners = {o["id"]: o.get("role", o["id"]) for o in gd.get("data_owners", [])}
    dom_owner = {}
    for d in gd.get("data_domains", []):
        en = (d.get("label", {}) or {}).get("en") if isinstance(d.get("label"), dict) else d.get("label")
        if en and d.get("owner_id"):
            dom_owner[en.strip().lower()] = owners.get(d["owner_id"], d["owner_id"])
    return dom_owner, owners


def _glossary_import(gd: dict) -> str:
    """Purview Unified Catalog glossary terms (bulk-import shape) from the data-gov glossary."""
    terms = []
    for t in gd.get("glossary", []):
        d = t.get("definition", {})
        terms.append({"name": t.get("term", ""),
                      "definition": d.get("en") if isinstance(d, dict) else d,
                      "domain_id": t.get("domain_id", ""),
                      "status": "Approved" if t.get("approved_by") else "Draft"})
    header = ("// Purview Unified Catalog glossary terms (from governance.json) — bulk import.\n"
              "// Register the Fabric tenant in Purview, then import via the Unified Catalog bulk API.\n")
    return header + json.dumps({"terms": sorted(terms, key=lambda x: x["name"])},
                               indent=2, ensure_ascii=False) + "\n"


def _data_quality(gd: dict) -> str:
    """Data-quality gates from governance.json (global standards + per-domain overrides)."""
    payload = {
        "standards": gd.get("data_quality_standards", {}),
        "verification_thresholds": gd.get("verification_thresholds", {}),
        "_note": ("Enforce in the silver→gold transforms / pipeline: completeness, freshness, accuracy. "
                  "Per-domain overrides (e.g. Finance stricter) take precedence over the global standards."),
    }
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def emit_governance(bp: dict, stack: str = "fabric", workspace: str = "<workspace>",
                    lakehouse: str = "analytics_gold", governance: dict | None = None,
                    governance_data: dict | None = None, sensitivity: dict | None = None,
                    governed_catalog: dict | None = None) -> dict[str, str]:
    """Return the governance artifact set (path → content), like ``emit_grounding``.

    ``_GOVERNANCE.md`` + RLS/OLS TMDL are always emitted (portable/deliverable-grade); the
    REST/`fab api` scripts + OneLake-roles payload are Fabric-specific. ``governance`` maps
    audience→principals/labels and stays in the caller's local file (secrets never in the repo).
    """
    governance = governance or {}
    gd = governance_data or {}
    sensitivity = sensitivity or governance.get("sensitivity") or {}   # {table: [sensitive columns]}
    domains = _domains(bp)
    dom_owner, _owners = _gov_owner_index(gd)

    doc = ["# Governance materialisation (generated — ADR-0015)", "",
           f"Stack: **{stack}**  ·  Domains: **{len(domains)}**  ·  "
           f"Data-gov source: **{'governance.json' if gd else 'IR only'}**", "",
           "IR-derived governance, at the fidelity Fabric actually supports (research 2026-07-15 §3):",
           "", "| Capability | Artifact | Status |", "|---|---|---|",
           "| **RLS/CLS/OLS — primary (all engines)** | `onelake_data_access_roles.json` (OneLake Security) | **Preview** |",
           "| Access-layer decision | `ACCESS_LAYER_DECISION.md` (where to enforce + why) | doc |",
           "| RLS/OLS — model-only alternative | `roles/<domain>.tmdl` (TMDL role blocks; fixed-identity case) | GA |",
           "| Workspace roles + Domains | `governance.sh` (REST/fab api) | GA |",
           "| Sensitivity labels | `sensitivity_labels.sh` (bulk admin API) | GA |",
           "| Endorsement | `ENDORSEMENT_RUNBOOK.md` (manual — no write API) | manual |"]
    if gd:
        doc += ["| **Data owners → workspace Admin** | `governance.sh` (from governance.json) | GA |",
                "| **Glossary → Purview terms** | `glossary_import.json` | GA |",
                "| **Data-quality gates** | `data_quality.json` (per-domain overrides) | policy |"]
    doc.append("")

    out: dict[str, str] = {"governance/_GOVERNANCE.md": "\n".join(doc) + "\n",
                           "governance/ACCESS_LAYER_DECISION.md": _access_layer_decision(bp),
                           "governance/ENDORSEMENT_RUNBOOK.md": _endorsement_runbook(bp)}
    for d in domains:
        aud = d.get("publishing", {}).get("intended_audience", "internal")
        out[f"governance/roles/{_dirslug(d['name'])}.tmdl"] = _rls_tmdl(
            d["name"], list(d.get("data_products", [])), aud, sensitivity)

    if gd:  # Data-Gov stream output materialised
        if gd.get("glossary"):
            out["governance/glossary_import.json"] = _glossary_import(gd)
        if gd.get("data_quality_standards") or gd.get("verification_thresholds"):
            out["governance/data_quality.json"] = _data_quality(gd)

    if stack == "fabric":
        out["governance/governance.sh"] = _governance_script(bp, workspace, governance, dom_owner)
        out["governance/sensitivity_labels.sh"] = _sensitivity_script(bp, governance)
        out["governance/onelake_data_access_roles.json"] = _onelake_security_roles(
            bp, lakehouse, sensitivity, governed_catalog)
    return out
