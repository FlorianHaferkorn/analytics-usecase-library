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
- OneLake data access roles → a declarative dataAccessRoles PUT payload, **GA since May 2026**
  (`learn.microsoft.com/fabric/fundamentals/whats-new-archive`, row "May 2026 · OneLake security
  (Generally Available) and OneLake data access roles (Generally Available)", read 29.09.2026;
  was labelled Preview here until 11.08.2026).
- Endorsement (Promoted/Certified) → an audit + **manual runbook**, because Fabric exposes
  **no supported write API** for endorsement (set is portal-only).

This module **does not execute** anything — it only emits text.
"""
from __future__ import annotations

import json
import re

_NONWORD_RE = re.compile(r"[^a-z0-9]+")

# Dokumentierte Grenzen der OneLake-Sicherheit (MS Learn, `fabric/onelake/security/*`, gelesen
# 11.08.2026). Sie stehen hier als Konstanten, weil ein Schnitt je Wert genau an ihnen zerbricht:
# eine Domaene mit 300 Niederlassungen laesst sich so nicht abbilden, und das muss VOR dem Bauen
# auffallen, nicht beim PUT.
ONELAKE_MAX_ROLES_PER_ITEM = 250
ONELAKE_MAX_MEMBERS_PER_ROLE = 500
ONELAKE_MAX_PREDICATE_CHARS = 1000


def _dirslug(name: str) -> str:
    return _NONWORD_RE.sub("-", (name or "").lower()).strip("-")


def _ident(name: str) -> str:
    return _NONWORD_RE.sub("_", (name or "").lower()).strip("_")


#: Das Namensschema der Entra-Gruppen, als Muster an **einer** Stelle. Es ist die Vorgabe aus
#: `betriebskanon.BK-W04` (`fab-<domaene>-<umgebung>-<rolle>`, Quelle WAF-Security + Fabric
#: Domains-Best-Practices, geprueft 16.08.2026), und es steht hier, weil zwei Emitter es
#: brauchen: der Zeilenschnitt (eine Gruppe je Wert) und die Domaenen-Leserolle.
#:
#: **Abweichung von der Vorgabe, benannt statt geglaettet:** der `<umgebung>`-Teil fehlt.
#: `governance/onelake_data_access_roles.json` wird einmal je Lakehouse emittiert, nicht je
#: Stage, und sein Anwendungsschritt traegt keine (gemessen 17.08.2026: beide
#: `assign_roles`-Schritte in `apply/APPLY_PLAN.json` haben `stage: null`, Ziel
#: `ws-<domaene>-gold.Workspace`). Ein Stage-Teil im Namen waere an dieser Stelle geraten.
#: Wer eine stage-bezogene Konvention hat, uebersteuert sie ueber `row_security.group_pattern`.
ENTRA_GRUPPENSCHEMA = "fab-{domaene}-{rolle}"


def entra_gruppenname(domain_name: str, rolle: str, muster: str = "",
                      wert: str = "", bezeichner: str = "") -> str:
    """Der Anzeigename der Entra-Gruppe hinter einer Rolle — abgeleitet, nicht erfragt.

    Bis 17.08.2026 gab es das nur im Zeilenschnitt. Die Domaenen-Leserollen trugen den nackten
    Platzhalter ``<VERIFY: Entra group objectId>``, und zwar **denselben fuer jede Domaene**:
    gemessen an der Commercial-Fixture bekamen ``read_commercial`` und ``read_finance`` ein
    identisches Token. Der Kunde beantwortet es einmal, dieselbe GUID landet in beiden Rollen,
    und Finance-Leser sehen Commercial-Tabellen. Ein Platzhalter, der zweimal fuer zwei
    verschiedene Dinge steht, ist keine offene Frage — er ist eine falsche Antwort mit Ansage.

    ``muster`` ist die Konvention des Kunden (``row_security.group_pattern``) und gewinnt, wenn
    sie gesetzt ist; das ist das Uebersteuerungsrecht aus der Vorgabe.
    """
    if muster:
        return muster.replace("{value}", wert).replace("{label}", bezeichner)
    return ENTRA_GRUPPENSCHEMA.format(domaene=_ident(domain_name).replace("_", "-"),
                                      rolle=rolle)


def _domains(bp: dict) -> list[dict]:
    return sorted(bp.get("mesh", {}).get("domains", []), key=lambda d: d.get("name", ""))


def _rls_tmdl(domain: str, gold_products: list[str], audience: str, sensitivity: dict | None = None) -> str:
    """A TMDL RLS/OLS role scaffold for a domain (GA; deploys via Update-Definition/XMLA).

    Honest by construction: the role structure + table refs are derived from the IR, but the
    DAX row filter is domain policy (not in the IR) → TODO(contract). Column-level (OLS) hiding is
    concrete when a ``sensitivity`` map (table → [sensitive columns]) is supplied — each sensitive
    column is named in a ``metadataPermission: none`` directive to hide it from this role.

    **Der Platzhalter ist ``FALSE()``, nicht ``true`` — geaendert 14.08.2026 (A.9).** Bis dahin
    stand hier ``true``, ausdruecklich als bewusste Abweichung von ``model_roles`` begruendet: das
    Geruest werde von Hand deployt, von jemandem, der das ``TODO(contract)`` daneben liest. Diese
    Annahme traegt nicht. Gemessen im E2E-Lauf: ``governance/roles/vertrieb.tmdl`` gab **allen
    sieben** Tabellen ``true``, dieselbe Form im Kundenmandant-Lauf 1. ``true`` zeigt alle Zeilen, und
    das ist die Richtung, die niemandem auffaellt — ein zu enger Filter faellt auf, weil sich
    jemand beschwert, ein zu weiter nicht. Damit geben jetzt beide Emitter dieses Moduls dieselbe
    Antwort auf dieselbe Frage; zwei gegenlaeufige Vorgaben in einer Datei sind ein Drift-Erzeuger.
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
            f"\t\t\tFALSE() /* bis der Filter geschrieben ist bewusst restriktiv — siehe TODO oben */",
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

    Das separat emittierte Gerüst (``_rls_tmdl``) trägt seit 14.08.2026 denselben ``FALSE()``.
    Vorher stand dort ``true``, begründet damit, dass es von Hand deployt werde — von jemandem,
    der das ``TODO(contract)`` daneben liest. Befund A.9 hat die Annahme widerlegt (alle sieben
    Tabellen im E2E-Lauf, dieselbe Form im Kundenmandant-Lauf 1), und zwei gegenläufige Vorgaben in
    einer Datei sind ein Drift-Erzeuger.
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


#: Die zwei Domaenen-Rollen, in der Reihenfolge, in der sie gesetzt werden muessen. Die
#: Reihenfolge ist keine Kosmetik: Contributors darf ein Domain-Admin vergeben, Admins nur
#: ein Fabric-Administrator. Wer unten anfaengt, braucht fuer den zweiten Schritt eine
#: Identitaet, die er sich gerade selbst haette geben koennen.
#:
#: **ANNAHME, ungeprueft — die Schreibweise des Feldes `type`.** Beide MS-Learn-Seiten zu
#: `bulkAssign`/`bulkUnassign` (geprueft 20.08.2026) widersprechen sich in sich selbst: ihre
#: `DomainRole`-Aufzaehlung nennt `Admin` und `Contributor` im Singular, **alle vier**
#: Beispielaufrufe auf denselben Seiten senden `Admins` und `Contributors` im Plural. Wir
#: senden den Plural, weil ein ausgefuehrtes Beispiel schwerer wiegt als eine Tabellenzeile,
#: und schreiben die Gegenprobe daneben statt den Widerspruch zu glaetten. Gemessen ist er,
#: aufgeloest nicht — das geht nur an einem echten Mandanten.
DOMAENEN_ROLLEN = (
    ("contributor", "Contributors", "wer Workspaces in diese Domaene haengen darf"),
    ("admin", "Admins", "der fachliche Dateneigentuemer der Domaene, nicht die IT"),
)


def domaenen_gruppen(bp: dict, governance: dict | None = None) -> list[dict]:
    """Je Domaene die zwei Entra-Gruppen hinter Domain-Admin und Domain-Contributor.

    Rein und deterministisch, damit drei Stellen dieselbe Antwort bekommen: das
    Governance-Skript (setzt die Rolle), der Nachschlage-Sammler (beschafft die objectId) und
    der Test. Der Anzeigename wird ueber ``entra_gruppenname`` abgeleitet — dieselbe Quelle
    wie beim Zeilenschnitt und bei der Domaenen-Leserolle, kein zweites Namensschema.

    Uebersteuerbar ueber die lokale Governance-Karte
    (``domain_roles.<domaene>.{admin,contributor}``), weil die Vorgabe zu BK-W02 dem Kunden
    genau dieses Recht gibt: in kleinen Organisationen ist es dieselbe Gruppe fuer beides,
    aber weiterhin eine Gruppe.
    """
    eigene = ((governance or {}).get("domain_roles") or {})
    aus: list[dict] = []
    for d in _domains(bp):
        dn = d.get("name", "")
        gesetzt = eigene.get(dn.strip().lower()) or eigene.get(dn) or {}
        for rolle, feldwert, zweck in DOMAENEN_ROLLEN:
            name = gesetzt.get(rolle) or entra_gruppenname(dn, f"domain-{rolle}")
            aus.append({"domaene": dn, "rolle": rolle, "typ": feldwert, "gruppe": name,
                        "zweck": zweck,
                        "token": f"<VERIFY: Entra group objectId of {name}>"})
    return aus


def _domaenen_rollen_zeilen(bp: dict, governance: dict, dom_owner: dict) -> list[str]:
    """Abschnitt 1c des Governance-Skripts: die Domaenen-Rollen setzen (BK-W02).

    Bis 20.08.2026 legte die Lieferung Domaenen an und haengte Workspaces hinein, aber
    niemand wurde ihr Admin. Eine Domaene ohne Admin ist die Delegation, die gebaut und nicht
    genutzt wurde: Tenant-Einstellungen bleiben zentral, und der Fachbereich merkt es erst,
    wenn er etwas uebersteuern will.
    """
    gruppen = domaenen_gruppen(bp, governance)
    if not gruppen:
        return []
    zeilen = [
        "# 1c. Domaenen-Rollen (BK-W02) — Domain-Admins und Domain-Contributors je Domaene.",
        "#   POST /v1/admin/domains/{domainId}/roleAssignments/bulkAssign?preview=false",
        "#   POST /v1/admin/domains/{domainId}/roleAssignments/bulkUnassign?preview=false",
        "#   Beleg: learn.microsoft.com/rest/api/fabric/admin/domains/role-assignments-bulk-assign",
        "#   (und .../role-assignments-bulk-unassign), beide geprueft 20.08.2026. Delegierter",
        "#   Scope Tenant.ReadWrite.All, hoechstens 25 Anfragen je Minute.",
        "#",
        "#   ANNAHME, ungeprueft: der Wert von \"type\". Die DomainRole-Tabelle beider Seiten sagt",
        "#   \"Admin\"/\"Contributor\" (Singular), alle vier Beispiele derselben Seiten senden",
        "#   \"Admins\"/\"Contributors\" (Plural). Wir senden den Plural. Antwortet der Dienst mit",
        "#   einem Fehler zum Feld type, ist der Singular die Gegenprobe — ein Zeichen, kein Umbau.",
        "#",
        "#   Zwei Fallen, die von aussen wie Erfolg aussehen:",
        "#   - Domain-ADMINS kann nur ein Fabric-Administrator setzen. Ein Domain-Admin darf",
        "#     danach Contributors vergeben, aber keine weiteren Admins.",
        "#   - Ein Domain-Contributor kann einen Workspace nur dann in die Domaene haengen, wenn",
        "#     er in DIESEM Workspace zugleich Admin ist. Die Rollenzuweisung allein bewirkt",
        "#     nichts; ohne die Workspace-Rolle aus Abschnitt 2 laeuft der POST durch und der",
        "#     Fachbereich kann trotzdem nichts zuordnen.",
        "#   Bekannte Fehlercodes: PrincipalWithDomainRoleAssignmentAlreadyExists (bereits",
        "#   zugewiesen, idempotent ignorierbar), UnsupportedPrincipalTypeForDomainAdminAssignment.",
    ]
    for eintrag in gruppen:
        dn = eintrag["domaene"]
        besitzer = dom_owner.get(dn.strip().lower())
        zeilen.append(f'#   {dn} — {eintrag["typ"]}: {eintrag["zweck"]}')
        if eintrag["rolle"] == "admin" and besitzer:
            # Der Name ist eine Konvention, die Besetzung eine Festlegung des Data-Gov-Stroms.
            # Beides zusammenzufuehren ist der ganze Zweck: sonst traegt die Gruppe den
            # richtigen Namen und die falschen Leute.
            zeilen.append(f'#     Hinter der Gruppe gehoert die Rolle "{besitzer}" '
                          "(governance.json data_owners).")
        zeilen.append(f'#   fab api "admin/domains/<{_dirslug(dn)}-id>/roleAssignments/bulkAssign'
                      '?preview=false" -X POST -i - <<JSON')
        rumpf = json.dumps({"type": eintrag["typ"],
                            "principals": [{"id": eintrag["token"], "type": "Group"}]},
                           ensure_ascii=False)
        zeilen.append(f"#   {rumpf}")
        zeilen.append("#   JSON")
    zeilen.append("")
    return zeilen


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
        "#   POST /v1/admin/domains?preview=false  + .../assignWorkspacesByIds  — data-mesh domains",
        "#   POST /v1/admin/domains/{id}/roleAssignments/bulkAssign  — Domain-Admin/-Contributor",
        "# Reached via `fab api <endpoint> -X POST -i <body.json>` (confirm flags: fab api -h).",
        "# Auth: a service principal works for BOTH roleAssignments and domains. Verified against",
        "#   learn.microsoft.com/rest/api/fabric/admin/domains/create-domain on 2026-07-31: the",
        "#   supported-identities table lists service principals as supported. The caller must be a",
        "#   Fabric ADMINISTRATOR (scope Tenant.ReadWrite.All), max 25 requests/minute. An earlier",
        "#   note here said 'SP not supported' — that was true when researched, is not true now.",
        "# `preview=false` is a REQUIRED query parameter on every /v1/admin/domains call: the release",
        "#   version is reached only that way (the preview version was deprecated 2026-03-31).",
        "",
        "# 1. Domains (data mesh) — one Fabric domain per blueprint domain; assign its workspace(s).",
    ]
    for d in domains:
        dn = d["name"]
        wss = ", ".join(w["name"] for w in d.get("workspaces", [])) or workspace
        lines.append(f"# {dn}  (workspaces: {wss})")
        lines.append(f'#   fab api "admin/domains?preview=false" -X POST -i - <<JSON   # capture the returned id')
        lines.append(f'#   {{"displayName":"{dn}"}}')
        lines.append("#   JSON")
        lines.append(f'#   fab api "admin/domains/<{_dirslug(dn)}-id>/assignWorkspacesByIds?preview=false" '
                     f'-X POST -i - <<JSON')
        # Die Workspaces DIESER Domäne, am Namen qualifiziert. Vorher stand hier ein generisches
        # `<workspace-id>` je Domäne — bei vier Workspaces im Mesh sagte es nicht, welcher.
        _ids = [f'"<{w["name"]}-workspace-id>"' for w in d.get("workspaces", [])] or ['"<workspace-id>"']
        lines.append(f'#   {{"workspacesIds":[{",".join(_ids)}]}}')
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
                    lines.append(f'#   fab api "workspaces/<{w["name"]}-workspace-id>/roleAssignments" -X POST -i - <<JSON')
                    lines.append(f'#   {{"principal":{{"id":"<{_dirslug(owner)}-principal-id>","type":"Group"}},"role":"Admin"}}')
                    lines.append("#   JSON")
        lines.append("")
    lines += _domaenen_rollen_zeilen(bp, governance or {}, dom_owner)
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
                    lines.append(f'#   fab api "workspaces/<{w["name"]}-workspace-id>/roleAssignments" -X POST -i - <<JSON')
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


def emit_onelake_roles(bp: dict, lakehouse: str, sensitivity: dict | None = None,
                       catalog: dict | None = None) -> dict[str, str]:
    """Der PUT-Rumpf **und** seine Erklärung — zwei Dateien, weil das eine abgeschickt und das
    andere gelesen wird. Vorher war beides eine Datei, und die war dadurch kein gültiges JSON.

    Die CLS-Offenpunkte entstehen beim Bauen des Rumpfs; deshalb entstehen beide hier zusammen
    statt in zwei Läufen, die auseinanderdriften können.
    """
    payload, cls_todo = _onelake_security_roles(bp, lakehouse, sensitivity, catalog,
                                                _with_todo=True)
    return {"governance/onelake_data_access_roles.json": payload,
            "governance/_ONELAKE_SECURITY.md": _onelake_roles_doc(cls_todo, catalog, bp)}


def _ist_platzhalter(member: dict) -> bool:
    """Ein Mitglied, das noch niemand eingetragen hat. Das Muster stammt aus dem Emitter selbst
    (``<VERIFY: …>`` / ``<TENANT_GUID>``); wer es ersetzt, hat eine echte Gruppe benannt."""
    return any(str(member.get(k, "")).lstrip().startswith("<")
               for k in ("objectId", "tenantId"))


def check_onelake_role_guardrails(payload: dict | str) -> dict:
    """Die eine Stelle, an der der Zeilenschnitt still verschwinden kann — als Pruefpunkt.

    Entschieden 14.08.2026 (Flo): ohne erklaerten Schnitt entsteht **keine** Zeilenbedingung, die
    Tabellen der Domaene bleiben lesbar. Das traegt, solange die Rolle keine echten Mitglieder hat
    und die Domaene keine Daten — beim Emittieren ist beides der Fall. Gefaehrlich ist nicht der
    Zustand, sondern der **Uebergang**: traegt jemand spaeter die Entra-Gruppe ein, ohne dass der
    Schnitt geschrieben wurde, sieht jedes Mitglied dieser Gruppe alle Zeilen — und nichts wird rot.

    Genau diesen Uebergang meldet diese Pruefung: eine Rolle mit **echten Mitgliedern** und
    **lesbaren Tabellen**, aber **ohne** ``constraints.rows``. Die Vorgabe bleibt unveraendert; die
    Sicherung sitzt hier, nicht dort.

    Zusaetzlich geprueft, weil B12 daran haengt: kein Praedikat darf gegen die OneLake-Grammatik
    verstossen (``{Spalte} {Operator} {Wert}``, MS Learn *Row-level security syntax reference*).
    Ein einziger ungueltiger Eintrag laesst den ``PUT`` scheitern und reisst die Anlage **aller**
    Rollen des Items mit — gemessen 14.08.2026, Kundenmandant Lauf 2.

    Gibt ``{findings: [...], counts: {...}}`` zurueck — dieselbe Form wie
    ``check_metadata_completeness``, damit die Leitplanken-Pruefung sie ohne Sonderfall einsammelt.
    """
    if isinstance(payload, str):
        payload = json.loads(payload)
    rollen = payload.get("value", []) if isinstance(payload, dict) else list(payload)
    findings: list[dict] = []
    ohne_schnitt = 0

    for rolle in rollen:
        name = rolle.get("name", "<ohne Namen>")
        mitglieder = (rolle.get("members") or {}).get("microsoftEntraMembers") or []
        echte = [m for m in mitglieder if not _ist_platzhalter(m)]
        for regel in rolle.get("decisionRules") or []:
            pfade = [p for scope in regel.get("permission") or []
                     if scope.get("attributeName") == "Path"
                     for p in scope.get("attributeValueIncludedIn") or []]
            zeilen = (regel.get("constraints") or {}).get("rows") or []
            geschnitten = {r.get("tablePath") for r in zeilen}

            for r in zeilen:
                wert = str(r.get("value") or "")
                # Nur der Teil hinter WHERE zaehlt, und dort muss links vom Operator ein
                # **Spaltenname** stehen — ein Bezeichner, der mit Buchstabe oder Unterstrich
                # beginnt. Genau daran scheitert `1=0`: `1` ist kein Spaltenname, und ohne
                # diese Unterscheidung geht der Befund durch, der B12 ausgeloest hat.
                _, _, rumpf = wert.lower().partition(" where ")
                if not re.search(r"(\[[a-z_]\w*\]|\b[a-z_]\w*\b)\s*"
                                 r"(=|<>|!=|<=|>=|<|>|\bin\b|\blike\b)", rumpf):
                    findings.append({
                        "object": f"{name} → {r.get('tablePath')}", "kind": "predicate",
                        "issue": "Praedikat erfuellt die OneLake-Grammatik nicht",
                        "why": "OneLake verlangt {Spalte} {Operator} {Wert}. Ein ungueltiger "
                               "Eintrag laesst den PUT scheitern und reisst die Anlage ALLER "
                               "Rollen des Items mit — der DefaultReader bleibt dann stehen"})
                if len(wert) > ONELAKE_MAX_PREDICATE_CHARS:
                    findings.append({
                        "object": f"{name} → {r.get('tablePath')}", "kind": "predicate",
                        "issue": f"Praedikat laenger als {ONELAKE_MAX_PREDICATE_CHARS} Zeichen",
                        "why": "die Dienstgrenze; darueber wird die Regel abgelehnt"})

            # B6 (gemessen 14.08.2026, §3b): gibt die Rolle NUR das frei, was sie schneidet, dann
            # ist jede Dimension fuer ihre Mitglieder unlesbar — nicht „ungeschuetzt sichtbar",
            # sondern weg. Der Bericht ist dann leer, und das sieht nach einem Berichtsfehler aus,
            # nicht nach einer Berechtigungsentscheidung. Deshalb hier und nicht im Auge des Lesers.
            if zeilen and pfade and set(pfade) <= geschnitten:
                findings.append({
                    "object": name, "kind": "role",
                    "issue": "gibt ausschliesslich die geschnittenen Tabellen frei: "
                             + ", ".join(sorted(pfade)),
                    "why": "in OneLake-Sicherheit ist eine Tabelle, die keine Rolle freigibt, "
                           "unlesbar. Ohne ausdrueckliche Leseerlaubnis fuer die Dimensionen, die "
                           "die Berichte anfassen, sieht ein Mitglied gefilterte Faktenzeilen und "
                           "sonst nichts — der Bericht bleibt leer"})

            offen = sorted(p for p in pfade if p not in geschnitten and "/fact_" in p.lower())
            if offen and not zeilen:
                ohne_schnitt += 1
            if offen and echte:
                findings.append({
                    "object": name, "kind": "role",
                    "issue": f"echte Mitglieder ({len(echte)}) auf ungeschnittenen Faktentabellen: "
                             + ", ".join(offen),
                    "why": "die Gruppe ist eingetragen, der Zeilenschnitt aber nicht geschrieben — "
                           "jedes Mitglied sieht alle Zeilen. Entweder den Schnitt im Bauplan "
                           "erklaeren (row_security) oder die Tabelle aus der Rolle nehmen"})

        if len(mitglieder) > ONELAKE_MAX_MEMBERS_PER_ROLE:
            findings.append({"object": name, "kind": "role",
                             "issue": f"mehr als {ONELAKE_MAX_MEMBERS_PER_ROLE} Mitglieder",
                             "why": "Dienstgrenze je Rolle"})

    if len(rollen) > ONELAKE_MAX_ROLES_PER_ITEM:
        findings.append({"object": "<Item>", "kind": "item",
                         "issue": f"mehr als {ONELAKE_MAX_ROLES_PER_ITEM} Rollen",
                         "why": "Dienstgrenze je Item"})

    return {"findings": findings,
            "counts": {"roles": len(rollen), "ohne_schnitt": ohne_schnitt,
                       "findings": len(findings)}}


def _cls_columns(tables: list[str], sensitivity: dict, cols_by_table: dict) -> tuple[list, list]:
    """CLS-Einschraenkungen für eine Tabellenmenge — und die Punkte, die ohne Katalog offen bleiben.

    OneLake-CLS **erlaubt die sichtbaren** Spalten (nicht gelistete sind null). Um eine sensible
    Spalte zu verstecken, wird also das Komplement erlaubt — und das braucht die volle Spaltenliste.
    Ohne governten Katalog wird hier nichts geraten, sondern ein Offenpunkt notiert.
    """
    cols: list[dict] = []
    todo: list[str] = []
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
            todo.append(f"{t}: hide {', '.join(scols)} (needs the full column list — supply the "
                        f"governed catalog to auto-compute the Permit-complement)")
    return cols, todo


def _sql_literal(value: str) -> str:
    """T-SQL-Zeichenkette mit verdoppeltem Apostroph. Ein Wert wie ``O'Brien`` bricht das
    Praedikat sonst syntaktisch — und ein kaputtes Praedikat ist in OneLake deny-all, also ein
    Ausfall, der wie funktionierende Sicherheit aussieht."""
    return "'" + str(value).replace("'", "''") + "'"


#: Der ausdrueckliche Sammelposten fuer Zeilen, die keiner Stufe zugeordnet werden konnten.
#: **Nie NULL.** Gemessener Anlass 14.08.2026 (Kundenmandant, erster DQ-Lauf): 562 Faktenzeilen
#: fanden kein Projekt, also blieben ihre Vorfahrenspalten leer. Ein Praedikat der Form
#: ``[org_niederlassung] = 'Muenchen'`` trifft NULL nicht — die Zeilen waren fuer **jede**
#: Rolle unsichtbar, und fehlende Zeilen sehen aus wie eine fehlende Berechtigung. Der
#: Sammelposten macht daraus einen Wert, den eine Rolle sehen kann.
UNBEKANNTES_MITGLIED = "Nicht zugeordnet"


def schnittspalten(domain: dict) -> tuple[str, ...]:
    """Die Spalten, an denen dieser Domaenen-Schnitt haengt — beide Eingabeformen, eine Antwort.

    Die Wertform nennt **eine** Spalte und zaehlt ihre Werte auf; die Stufenform traegt die
    Spalte an der Stufe und liefert damit eine Spalte je Stufe. Beide muenden hier in dieselbe
    Liste, damit niemand sie ein viertes Mal ableitet: bis 16.08.2026 stand
    ``{e["name"]: e["column"] for e in rs["levels"]}`` an drei Stellen dieser Datei, und der
    DQ-Emitter kannte sie gar nicht.

    Nur Stufen, auf die tatsaechlich berechtigt wird. Eine deklarierte Stufe ohne Berechtigung
    schneidet nichts und braucht deshalb auch kein Tor.
    """
    rs = domain.get("row_security") or {}
    if rs.get("levels"):
        je_stufe = {e.get("name"): e.get("column") for e in rs["levels"]}
        benutzt = [g.get("level") for g in (rs.get("grants") or [])]
        return tuple(je_stufe[s] for s in dict.fromkeys(benutzt) if je_stufe.get(s))
    return (rs.get("column"),) if rs.get("column") else ()


def _row_security_roles(domain: dict, sensitivity: dict, cols_by_table: dict) -> tuple[list, list]:
    """Je Wert des Schnitts **eine** OneLake-Rolle — die einzige Bauform, die OneLake hergibt.

    Der Grund steht nicht in unserer Konvention, sondern im Dienst: das Praedikat einer OneLake-
    Rolle ist statisches T-SQL. Es gibt kein Gegenstueck zu ``USERPRINCIPALNAME()``, also laesst
    sich der Aufrufer nicht lesen und ein einziger Ausdruck kann den Schnitt nicht abbilden. Was
    bleibt, ist Materialisierung: eine Rolle je Wert, eine Entra-Gruppe je Wert.

    Zwei Dinge werden dabei mitgeliefert, weil sie sonst erst beim PUT auffallen: RLS und CLS
    derselben Tabelle liegen in **einer** Rolle (getrennt fuehrt die Abfrage zum Fehler), und die
    dokumentierten Grenzen werden geprueft statt vorausgesetzt.
    """
    rs = domain.get("row_security") or {}
    spalte = rs.get("column")
    werte = list(rs.get("values") or [])
    tabellen = sorted(rs.get("protected_products") or domain.get("data_products") or [])
    muster = rs.get("group_pattern")
    dident = _ident(domain.get("name", ""))
    ungeschuetzt = sorted(set(domain.get("data_products") or []) - set(tabellen))

    todo: list[str] = []
    # Beide Eingabeformen laufen auf dasselbe Tripel hinaus: Spalte, Wert, Bezeichner. Die Wertform
    # nennt eine Spalte und zaehlt ihre Werte auf, die Stufenform nennt je Berechtigung eine Stufe
    # und traegt die Spalte an der Stufe.
    #
    # Festlegung Flo, 15.08.2026: die geschuetzte Faktentabelle traegt **eine Spalte je Stufe**, nicht
    # nur die feinste. Das ist der Grund, warum hier nichts aufgeloest wird. Traegt der Fakt nur die
    # feinste Stufe, muesste eine Berechtigung auf eine groebere Stufe den Teilbaum zu einer
    # `IN`-Liste ausrechnen, und die 1000-Zeichen-Grenze je Regel begrenzte den Teilbaum auf rund 134
    # vierstellige Codes. Mit einer Spalte je Stufe ist jede Berechtigung ein einzelner Wert, und die
    # Grenze wird nie zum Thema.
    schnitte: list[tuple[str, str, str]] = []
    if rs.get("levels"):
        spalte_je_stufe = {e.get("name"): e.get("column") for e in rs["levels"]}
        for g in rs.get("grants") or []:
            sp = spalte_je_stufe.get(g.get("level"))
            if not sp:                       # in `derive_blueprint` bereits als HITL gemeldet
                continue
            knoten = str(g.get("node"))
            schnitte.append((sp, knoten, str(g.get("label") or f"{g.get('level')}_{knoten}")))
    else:
        schnitte = [(spalte, str(w), str(w)) for w in werte] if spalte else []

    # Eine Regel, die eine Spalte nennt, die es in der Tabelle nicht gibt, ist nicht folgenlos:
    # *„If a CLS or RLS rule has a mismatch with the table it's defined on, the query fails and
    # returns no data"* (MS Learn, *Table, column, and row-level security in OneLake*, gelesen
    # 15.08.2026). Wo die Spaltenliste der Tabelle bekannt ist, faellt das hier auf statt beim PUT.
    for sp in sorted({s for s, _, _ in schnitte}):
        fehlt = sorted(t for t in tabellen if cols_by_table.get(t) and sp not in cols_by_table[t])
        if fehlt:
            todo.append(f"{domain.get('name')}: Schnittspalte `{sp}` fehlt in {', '.join(fehlt)}. "
                        f"Eine RLS-Regel auf einer Spalte, die die Tabelle nicht traegt, laesst die "
                        f"Abfrage fehlschlagen und liefert KEINE Zeilen — die Tabelle ist damit "
                        f"faktisch tot, nicht nur ungeschnitten.")

    if len(schnitte) > ONELAKE_MAX_ROLES_PER_ITEM:
        todo.append(f"{domain.get('name')}: {len(schnitte)} Berechtigungen ergeben "
                    f"{len(schnitte)} Rollen — ueber der dokumentierten Grenze von "
                    f"{ONELAKE_MAX_ROLES_PER_ITEM} je Item. Der Schnitt muss vergroebert werden "
                    f"(gruebere Stufe oder Gruppierung der Werte) oder auf mehrere Items verteilt.")
    if ungeschuetzt:
        todo.append(f"{domain.get('name')}: lesbar, aber NICHT vom Schnitt erfasst: "
                    f"{', '.join(ungeschuetzt)}. Jede Rolle sieht diese Tabellen vollstaendig. "
                    f"Die Pruefrage ist nicht „ist die Liste richtig“, sondern „welche Fakten "
                    f"stehen NICHT darauf, und ist das gewollt“ — gehoeren sie in "
                    f"protected_products, oder sind sie bewusst ungeschnitten?")
    # Was die Rolle LESEN koennen muss — nicht nur, was sie schneidet. Bis 14.08.2026 waren beide
    # Mengen dieselbe: die Rolle gab genau die geschuetzten Fakten frei. Gemessen im Mandanten
    # (B6, §3b): `readvertriebeurope` trug `Path=/Tables/vertrieb/fact_umsatz | Action=Read` und
    # sonst nichts — kein `dim_territorium`, kein `dim_datum`. Ein Mitglied der Gruppe saehe
    # gefilterte Faktenzeilen und keine einzige Dimension, beide Berichte waeren leer.
    #
    # In OneLake-Sicherheit ist eine Tabelle, die keine Rolle freigibt, nicht „ungeschuetzt
    # sichtbar", sondern **unlesbar**. Der Emitter kannte dafuer keinen Begriff: er leitete die
    # Freigaben aus `protected_products` ab, und „zum Lesen noetig, aber nicht zu schneiden" kam
    # darin nicht vor. Genau diese zweite Menge steht jetzt hier.
    lesbar = sorted(set(tabellen) | set(domain.get("data_products") or []) | set(cols_by_table))

    rollen = []
    for sp, wert, bez in schnitte:
        rows = [{"tablePath": f"/Tables/{t}",
                 "value": f"select * from {t} where [{sp}] = {_sql_literal(wert)}"}
                for t in tabellen]
        zu_lang = [r["tablePath"] for r in rows if len(r["value"]) > ONELAKE_MAX_PREDICATE_CHARS]
        if zu_lang:
            todo.append(f"{domain.get('name')}/{wert}: Praedikat laenger als "
                        f"{ONELAKE_MAX_PREDICATE_CHARS} Zeichen fuer {', '.join(zu_lang)}.")
        constraints: dict = {"rows": rows} if rows else {}
        cols, cls_todo = _cls_columns(tabellen, sensitivity, cols_by_table)
        todo += cls_todo
        if cols:
            constraints["columns"] = cols
        gruppe = entra_gruppenname(domain.get("name", ""), f"reader-{_ident(bez)}",
                                   muster=muster or "", wert=wert, bezeichner=bez)
        rule = {
            "effect": "Permit",
            # GENAU ZWEI `permission`-Elemente, und mehrere Tabellen gehoeren in EIN
            # `attributeValueIncludedIn`-Array. Gemessen 14.08.2026 an der API: ein Paar je
            # Tabelle wird mit `PolicyValidationError` abgewiesen.
            "permission": [
                {"attributeName": "Path", "attributeValueIncludedIn": [f"/Tables/{t}" for t in lesbar]},
                {"attributeName": "Action", "attributeValueIncludedIn": ["Read"]},
            ],
        }
        if constraints:
            rule["constraints"] = constraints
        rollen.append({
            "name": f"read_{dident}_{_ident(bez)}",
            "kind": "Policy",
            "decisionRules": [rule],
            "members": {"microsoftEntraMembers": [{
                "objectId": f"<VERIFY: Entra group objectId of {gruppe or f'the group for {wert}'}>",
                "objectType": "Group",
                "tenantId": "<TENANT_GUID>"}]},
        })
    return rollen, todo


def _onelake_security_roles(bp: dict, lakehouse: str, sensitivity: dict | None = None,
                            catalog: dict | None = None, _with_todo: bool = False):
    """OneLake Security roles — the **primary, engine-unified** RLS/CLS/OLS layer: defined once
    on the lakehouse, enforced across Spark, notebooks, the lakehouse, the SQL analytics endpoint
    and Direct-Lake-on-OneLake semantic models (MS Learn 2026-07, OneLake security).

    Grounded in the REST reference *OneLake Data Access Security — Create Or Update Data Access
    Roles*: ``PUT /v1/workspaces/{ws}/items/{itemId}/dataAccessRoles``. OneLake security and
    OneLake data access roles are **GA since May 2026** (MS Learn what's-new, retrieved
    10.08.2026; since moved to what's-new-archive, re-read 29.09.2026); the Preview label that stood here was stale. Honest by
    construction — only the IR-derivable parts are filled, the policy parts are workshop-owned:

    - **Table access (OLS)** ← the domain's gold products. Each rule carries the two mandatory
      ``PermissionScope`` objects the API requires: ``Path`` (``/Tables/<t>``) + ``Action`` (Read).
    - **RLS** (``constraints.rows[].value``, a T-SQL predicate) → only where the blueprint
      *declares* a cut (``row_security``). Where it does not, **no row condition is emitted**
      and the gap is carried into ``_ONELAKE_SECURITY.md`` instead of into the payload.
      Measured 14.08.2026, customer tenant run 2 (B12): the former ``where 1=0`` scaffold violates the
      OneLake RLS grammar (``{column} {operator} {static value}``, MS Learn *Row-level security
      syntax reference*) → ``BadRequest: InvalidRLSPredicate``. Because the ``PUT`` replaces the
      **entire** role set, that single invalid predicate aborted the creation of *all* roles on
      the item and left ``DefaultReader``/``ReadAll`` standing. A deny-all meant to protect
      produced the opposite. Fail-closed therefore never gets expressed as a row predicate here.
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
        if d.get("row_security"):
            # Der Schnitt ist erklaert — dann ist eine Rolle je Wert die einzige Bauform, die
            # OneLake-Sicherheit hergibt (statisches Praedikat, kein Aufrufer). Sie ersetzt die
            # deny-all-Rolle dieser Domaene; beides nebeneinander waere widerspruechlich.
            wert_rollen, wert_todo = _row_security_roles(d, sensitivity, cols_by_table)
            roles += wert_rollen
            cls_todo += wert_todo
            continue
        rule: dict = {
            "effect": "Permit",
            "permission": [
                {"attributeName": "Path", "attributeValueIncludedIn": [f"/Tables/{t}" for t in tables]},
                {"attributeName": "Action", "attributeValueIncludedIn": ["Read"]},
            ],
        }
        constraints: dict = {}
        # KEIN Zeilenschnitt ohne erklaerten Zeilenschnitt (B12, gemessen 14.08.2026).
        # Hier stand `where 1=0` als fail-closed-Geruest. Das Praedikat ist grammatikalisch
        # ungueltig (OneLake verlangt {Spalte} {Operator} {Wert}), der `PUT` ersetzt die
        # gesamte Rollenmenge des Items — ein ungueltiger Eintrag riss deshalb die Anlage
        # ALLER Rollen mit, und die Vorgabe `DefaultReader`/`ReadAll` blieb stehen. Aus
        # "niemand sieht etwas" wurde "jeder sieht alles".
        # Entschieden 14.08.2026 (Flo): ohne erklaerten Schnitt entsteht keine Zeilenbedingung,
        # die Tabellen bleiben lesbar. Traegt, solange die Rolle keine Mitglieder hat und die
        # Domaene keine Daten — beim Emittieren ist beides der Fall (`<VERIFY: …>`-Platzhalter).
        # Der gefaehrliche Zustand ist der Uebergang, und den faengt die Leitplanken-Pruefung
        # (`check_onelake_role_guardrails` in diesem Modul), nicht die Vorgabe.
        # CLS: OneLake CLS *permits visible* columns (unlisted → null), so to HIDE the sensitive
        # ones we Permit the complement. This needs the full column list (governed catalog); without
        # it we can't compute the complement → record a TODO rather than guess.
        cols, todo = _cls_columns(tables, sensitivity, cols_by_table)
        cls_todo += todo
        if cols:
            constraints["columns"] = cols
        if constraints:
            rule["constraints"] = constraints
        roles.append({
            "name": f"read_{dident}",
            "kind": "Policy",
            "decisionRules": [rule],
            # Der Name der Gruppe ist ableitbar (Domaene + Rolle, Schema aus BK-W04), die GUID
            # nicht. Bis 17.08.2026 stand hier der nackte Platzhalter — fuer jede Domaene
            # derselbe. Siehe `entra_gruppenname`.
            "members": {"microsoftEntraMembers": [
                {"objectId": "<VERIFY: Entra group objectId of "
                             f"{entra_gruppenname(d.get('name', ''), 'reader')}>",
                 "objectType": "Group",
                 "tenantId": "<TENANT_GUID>"}]},
        })
    payload = {"value": sorted(roles, key=lambda r: r["name"])}
    # **Reines JSON, keine Kommentarzeilen.** Diese Datei ist der Rumpf eines PUT auf
    # `/dataAccessRoles`. Bis 31.07.2026 stand ein `//`-Kommentarblock davor — damit war sie kein
    # gültiges JSON: `json.load` scheiterte, und abgeschickt hätte der Dienst sie abgelehnt. Der
    # Kommentar war inhaltlich wertvoll und ist deshalb nicht gelöscht, sondern nach
    # `governance/_ONELAKE_SECURITY.md` gewandert (siehe `_onelake_roles_doc`).
    body = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    return (body, cls_todo) if _with_todo else body


def _row_security_doc(bp: dict) -> list[str]:
    """Der erklaerte Zeilenschnitt — was gebaut wurde und was daran Handarbeit bleibt."""
    schnitte = [(d.get("name"), d["row_security"]) for d in _domains(bp) if d.get("row_security")]
    if not schnitte:
        return []
    lines = [
        "## Zeilenschnitt: eine Rolle je Berechtigung", "",
        "Fuer diese Domaenen ist der Schnitt erklaert, deshalb steht im Rumpf je Berechtigung eine",
        "eigene Rolle mit fertigem Praedikat. Das ist keine Stilfrage: das",
        "Praedikat einer OneLake-Rolle ist statisches T-SQL ohne Zugriff auf den Aufrufer — es gibt",
        "kein Gegenstueck zu `USERPRINCIPALNAME()`. Ein Ausdruck kann den Schnitt also nicht",
        "abbilden; er muss materialisiert werden.", "",
        "Mehrere Rollen sind dabei kein Notbehelf, sondern das dokumentierte Modell: *„RLS is",
        "combined across predicates using an OR operator\"* (MS Learn, *OneLake security access",
        "control model*). Wer mehrere Knoten sehen soll, kommt in mehrere Gruppen, und die",
        "Praedikate verodern sich. Zwei Grenzen dazu: eine RLS-Rolle und eine CLS-Rolle fuer",
        "denselben Nutzer sind **nicht** kombinierbar (Abfragefehler), und viele sich vereinigende",
        "RLS-Rollen koennen den Sicherheits-Sync scheitern lassen — ein gescheiterter Sync wendet",
        "die Richtlinie gar nicht an.", "",
        "**Bei der Stufenform traegt der Fakt eine Spalte je Stufe**, nicht nur die feinste. Damit",
        "ist jede Berechtigung ein einzelner Wert auf der Spalte ihrer Stufe. Traegt der Fakt nur",
        "die feinste Stufe, muss der Teilbaum zu einer `IN`-Liste ausgerechnet werden, und die",
        f"{ONELAKE_MAX_PREDICATE_CHARS}-Zeichen-Grenze je Regel begrenzt ihn auf rund 134",
        "vierstellige Codes.", "",
        "| Domaene | Form | Spalte(n) | Rollen | Geschuetzte Tabellen | Entra-Gruppe je Rolle |",
        "|---|---|---|---|---|---|",
    ]
    for name, rs in schnitte:
        if rs.get("levels"):
            # Eine Spalte je Stufe, eine Rolle je Berechtigung. Nur die Stufen zeigen, auf die
            # tatsaechlich berechtigt wird — eine Stufe ohne Berechtigung kostet keine Rolle.
            spalte_je_stufe = {e.get("name"): e.get("column") for e in rs["levels"]}
            spalten = ", ".join(f"`{s}`" for s in schnittspalten({"row_security": rs}))
            form, anzahl = "Stufen", len([g for g in (rs.get("grants") or [])
                                          if spalte_je_stufe.get(g.get("level"))])
        else:
            spalten, form, anzahl = f"`{rs.get('column')}`", "Werte", len(rs.get("values") or [])
        lines.append(f"| {name} | {form} | {spalten} | {anzahl} | "
                     f"{len(rs.get('protected_products') or [])} | "
                     f"`{rs.get('group_pattern') or '— (Muster nicht gesetzt)'}` |")
    lines += [
        "", "**Was daran Handarbeit bleibt.** Die Gruppen werden benannt, nicht angelegt — jede",
        "`objectId` im Rumpf ist ein `<VERIFY: …>`-Platzhalter, weil das Anlegen von Entra-Gruppen",
        "ein Tenant-Vorgang mit eigenem Verantwortlichen ist. Und die Schnittspalte muss",
        "**physisch in jeder geschuetzten Tabelle** stehen: OneLake-Sicherheit kennt keine",
        "tabellenuebergreifende Zeilensicherheit, ein Praedikat auf einer Dimension erreicht ihre",
        "Fakten nicht. Wer die Spalte in der Transformation wegoptimiert, hebt den Schnitt auf,",
        "ohne dass hier etwas rot wird.", "",
        f"Grenzen, gegen die dieser Rumpf geprueft ist: {ONELAKE_MAX_ROLES_PER_ITEM} Rollen je Item, "
        f"{ONELAKE_MAX_MEMBERS_PER_ROLE} Mitglieder je Rolle, {ONELAKE_MAX_PREDICATE_CHARS} Zeichen "
        "je Praedikat.", "",
        "## Die Teile summieren sich nicht zum Ganzen", "",
        f"Zeilen ohne zuordenbare Stufe tragen den Sammelposten `{UNBEKANNTES_MITGLIED}` (nie NULL,",
        "Begruendung im DQ-Tor). Er ist auf der obersten Stufe sichtbar und auf den feineren nicht.",
        "Daraus folgt eine Eigenschaft, die jeder Leser eines Berichts frueher oder spaeter bemerkt:",
        "**die Summe der Zweige ist kleiner als die Gesamtsumme.** Wer eine oberste Stufe sieht,",
        "bekommt den Sammelposten mit; wer einen Zweig sieht, nicht.", "",
        "Das ist gewollt und muss trotzdem im Bericht stehen, sonst liest es sich als Zahlenfehler.",
        "Zwei belastbare Wege: den Sammelposten als eigene Zeile ausweisen, oder die Zahl der",
        "nicht zugeordneten Zeilen neben der Gesamtsumme nennen. Die dritte Variante — den",
        "Sammelposten auf allen Stufen sichtbar machen — hebt den Schnitt fuer diese Zeilen auf und",
        "kommt nur infrage, wenn sie unkritisch sind.", "",
        "Die Alternative waere, unzugeordnete Zeilen zu verwerfen. Dann stimmen zwar alle Summen",
        "untereinander, aber keine mit der Quelle, und der Fehler faellt niemandem mehr auf.", "",
    ]
    return lines


def _onelake_roles_doc(cls_todo: list[str], catalog: dict | None, bp: dict | None = None) -> str:
    """Die Erklärung zu ``onelake_data_access_roles.json`` — als Dokument, nicht als Kommentar
    in einem JSON-Rumpf, der abgeschickt werden soll."""
    lines = [
        "# OneLake Security roles (generiert)",
        "",
        "Rumpf für `PUT /v1/workspaces/{ws}/items/{lakehouseId}/dataAccessRoles` —",
        "`onelake_data_access_roles.json` daneben. **Status GA (seit Mai 2026)**",
        "(`OneLake.ReadWrite.All`; erst mit `dryRun=true` + ETag fahren).",
        "",
        "Das ist die **primäre** RLS/CLS/OLS-Schicht: einmal definiert, von allen Fabric-Engines",
        "durchgesetzt — auch von Direct Lake on OneLake.",
        "",
        "## Was im Rumpf steht und was du ändern musst",
        "",
        "- **RLS** — `constraints.rows[]` steht **nur dort, wo der Bauplan einen Schnitt",
        "  erklärt** (`row_security`). Wo er keinen erklärt, steht **keine Zeilenbedingung**:",
        "  die Tabellen der Domäne sind für die Rolle vollständig lesbar. Das ist eine",
        "  getroffene Entscheidung und kein Versehen — sie trägt, solange die Rolle keine",
        "  Mitglieder hat und die Domäne keine Daten. **Vor dem ersten echten Nutzer muss der",
        "  Schnitt geschrieben sein**, sonst sieht jedes Mitglied dieser Gruppe alle Zeilen.",
        "  Bis 14.08.2026 stand hier ersatzweise `where 1=0`. Das Prädikat erfüllt die",
        "  OneLake-Grammatik nicht (`{Spalte} {Operator} {Wert}`) und wurde mit",
        "  `InvalidRLSPredicate` abgelehnt — und weil der `PUT` die gesamte Rollenmenge",
        "  ersetzt, riss dieser eine Eintrag die Anlage **aller** Rollen mit. Zurück blieb der",
        "  `DefaultReader` mit `ReadAll`.",
        "- **CLS** — `constraints.columns` erlaubt die **sichtbaren** Spalten (nicht gelistete",
        "  sind null). Deklarierte sensible Spalten (`--sensitivity`) werden versteckt, indem das",
        "  Komplement erlaubt wird — berechnet aus der vollen Spaltenliste des governten Katalogs.",
        "  Ohne Deklaration kein CLS: hier wird nichts geraten.",
        "",
        "## Die Falle",
        "",
        "**Eine Rolle muss RLS und CLS derselben Tabelle zusammen halten.** RLS in Rolle A und CLS",
        "in Rolle B für denselben Benutzer lässt die Abfrage fehlschlagen. Und: privilegierte",
        "Workspace-Rollen umgehen RLS/CLS vollständig — siehe `_WORKSPACE_STRATEGIE.md`.",
        "",
    ]
    lines += _row_security_doc(bp or {})
    if cls_todo:
        # Nicht mehr nur CLS: seit dem Zeilenschnitt landen hier auch gerissene OneLake-Grenzen
        # und Produkte, die kein Schnitt erfasst. Eine Liste, weil beides dasselbe ist — etwas,
        # das vor dem PUT entschieden werden muss.
        lines += ["## Offene Punkte vor dem PUT", ""] + [f"- {t}" for t in dict.fromkeys(cls_todo)] + [""]
    vorschlag = _rls_proposal_comment(catalog).replace("// ", "").replace("//", "").strip()
    if vorschlag:
        lines += ["## RLS-Vorschlag", "", vorschlag, ""]
    return "\n".join(lines) + "\n"


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
           "| **RLS/CLS/OLS — primary (all engines)** | `onelake_data_access_roles.json` (OneLake Security) | **GA (Mai 2026)** |",
           "| **Kollision mit der Ontologie** | siehe Kasten unten | **entscheiden** |",
           "| Access-layer decision | `ACCESS_LAYER_DECISION.md` (where to enforce + why) | doc |",
           "| RLS/OLS — model-only alternative | `roles/<domain>.tmdl` (TMDL role blocks; fixed-identity case) | GA |",
           "| Workspace roles + Domains | `governance.sh` (REST/fab api) | GA |",
           "| Domain-Admins + Domain-Contributors | `governance.sh` Abschnitt 1c | GA |",
           "| Sensitivity labels | `sensitivity_labels.sh` (bulk admin API) | GA |",
           "| Endorsement | `ENDORSEMENT_RUNBOOK.md` (manual — no write API) | manual |",
           "| Which items may be created where | `fabric_policies/` (Fabric policies, target picture; "
           "not in West/North Europe) | **preview** |",
           "| Catalog tags | `tags.json` + `apply_tags.sh` (Admin List Tags → Apply Tags) | GA |"]
    doc += ["",
            "> **OneLake-Security schliesst die Fabric-IQ-Ontologie aus.** MS dokumentiert an drei",
            "> Stellen, dass ein Lakehouse mit aktivierter OneLake-Security **nicht** als",
            "> Bindungsquelle einer Ontologie taugt; die Quelle erscheint dort gar nicht erst zur",
            "> Auswahl. Beide Artefakte sind fuer sich korrekt, zusammen aber unvereinbar, und die",
            "> Lieferung emittiert sie standardmaessig beide. Zwei Wege stehen offen, und die",
            "> Entscheidung gehoert vor das Anlegen des Lakehouse, nicht danach:",
            ">",
            "> 1. **OneLake-Security behalten** (Schutz wirkt ueber alle Engines) und die Ontologie",
            ">    an ein separates Lakehouse ohne OneLake-Security binden. Kostet eine zweite Kopie",
            ">    oder einen eigenen Gold-Bereich.",
            "> 2. **Ontologie auf diesem Lakehouse** und RLS/CLS stattdessen im Semantikmodell",
            ">    erzwingen (`roles/<domain>.tmdl`). Der Schutz gilt dann nur fuer den Modellpfad,",
            ">    nicht fuer Spark, Notebooks und den SQL-Endpunkt.",
            ">",
            "> Die Konformitaetspruefung meldet den Fall als Fehler, solange beides zugleich",
            "> deklariert ist."]
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
        out.update(emit_onelake_roles(bp, lakehouse, sensitivity, governed_catalog))
        out.update(emit_fabric_policies(bp))
        out.update(emit_tags(bp))
    # P5 gehoert hierher und nicht hinter ein eigenes Flag: es IST Governance, und es erscheint genau
    # dann, wenn die IR einen Share deklariert. Ein eigenes `--emit-sharing` waere ein Schalter, den man
    # vergessen kann — bei einer Bedingung, die das Sicherheitsmodell aufhebt, ist das der falsche
    # Freiheitsgrad.
    out.update(emit_sharing(bp, stack=stack))
    return out

# --------------------------------------------------------------------------- Fabric policies (I-21 W1.12)
#
# Gelesen per Learn-MCP am 29.09.2026: `fabric/governance/fabric-policies-overview`,
# `-item-creation`, `-rest-api` (alle Preview). Die Zahlen unten sind MS-Grenzen, keine eigenen.
FABRIC_POLICIES_GEPRUEFT = "2026-09-29"
POLICY_MAX_RULES_CAPACITY = 50
POLICY_MAX_RULES_TENANT = 100
POLICY_MAX_VALUES_PER_CONDITION = 50

#: Zielbild: erlaubte Item-Typen je Workspace-Rolle, als **API-Bezeichner** (MS: „Use API item-type
#: identifiers, not UI display names", z. B. ``DataPipeline`` fuer „Pipeline"). Nur Bezeichner, die
#: auf den MS-Seiten selbst als Wert stehen — die Liste ist ein Vorschlag, den der Kunde erweitert,
#: und sie muss vor der Aktivierung gegen alles geprueft werden, was die Lieferung selbst anlegt
#: (Variable Library, Environment, Eventhouse …), sonst blockiert die Policy unser eigenes Deployment.
ITEMTYPEN_JE_ROLLE: dict[str, tuple[str, ...]] = {
    "bronze": ("Lakehouse", "Notebook", "DataPipeline"),
    "silver": ("Lakehouse", "Notebook", "DataPipeline"),
    "gold": ("Lakehouse", "Notebook", "DataPipeline", "Warehouse", "SemanticModel"),
    # D-600: der Daten-Workspace baut Bronze bis Gold; Semantikmodelle gehoeren in den
    # Consumption-Workspace (`reporting`), dort liest der Konsument.
    "data": ("Lakehouse", "Notebook", "DataPipeline", "Warehouse"),
    "reporting": ("Report", "SemanticModel"),
}
FABRIC_POLICY_PATH = "governance/fabric_policies/item_creation_policy.json"


def _policy_workspaces(bp: dict) -> list[tuple[str, str]]:
    return sorted({(str(ws.get("name")), str(ws.get("role") or ""))
                   for d in _domains(bp) for ws in (d.get("workspaces") or []) if ws.get("name")})


def _ws_platzhalter(name: str) -> str:
    """`workspace.name` weist die API mit UnsupportedPropertyValue ab — es muss die GUID sein.

    Die Form ``<{ws}-workspace-id>`` ist in ``provision_binding`` als **Laufzeit-ID** registriert
    (Erzeuger: ``create_workspace``). Ein ``<VERIFY: …>`` saehe dort aus wie eine Kundenfrage —
    gemessen 29.09.2026 am SAP-E2E-Snapshot: 8 neue „offene Punkte" fuer Werte, die der Apply-Lauf
    selbst erzeugt."""
    return f"<{name}-workspace-id>"


def fabric_policy_rules(bp: dict) -> list[dict]:
    """Die ``ItemCreation``-Regeln des Zielbilds: eine je Rolle mit Einschraenkung, ``mixed`` ohne
    Typbedingung, und die Auffangregel fuer alle **anderen** Workspaces der Kapazitaet.

    Die Auffangregel ist nicht optional: sobald eine Regel existiert, gilt die Allow-List fuer die
    ganze Kapazitaet, und jeder Workspace ausserhalb der Lieferung koennte nichts mehr anlegen
    (MS-Beispiel „Rule 2 - Allow all other item types for all users")."""
    ws = _policy_workspaces(bp)
    regeln: list[dict] = []
    for rolle in sorted({r for _, r in ws}):
        namen = [n for n, r in ws if r == rolle]
        bedingungen = [{"type": "Dynamic", "targetProperty": "workspace.id",
                        "predicate": {"operator": "AnyOf",
                                      "values": [_ws_platzhalter(n) for n in namen]}}]
        typen = ITEMTYPEN_JE_ROLLE.get(rolle)
        if typen:
            bedingungen.append({"type": "Dynamic", "targetProperty": "item.type",
                                "predicate": {"operator": "AnyOf", "values": list(typen)}})
        regeln.append({"displayName": f"Allow {rolle} item types"[:100],
                       "description": (f"Workspace role '{rolle}': "
                                       + (", ".join(typen) if typen else "no type restriction")),
                       "policy": "ItemCreation", "conditions": bedingungen})
    if ws:
        regeln.append({"displayName": "Allow all item types outside this delivery",
                       "description": "Keeps every other workspace on the capacity at allow-all.",
                       "policy": "ItemCreation",
                       "conditions": [{"type": "Dynamic", "targetProperty": "workspace.id",
                                       "predicate": {"operator": "NoneOf",
                                                     "values": [_ws_platzhalter(n) for n, _ in ws]}}]})
    return regeln


def pruefe_policy_grenzen(regeln: list[dict], scope: str = "Capacity") -> list[str]:
    """Die dokumentierten Grenzen als Befundliste (leer = innerhalb). Rein."""
    maximal = POLICY_MAX_RULES_CAPACITY if scope == "Capacity" else POLICY_MAX_RULES_TENANT
    befunde = []
    if len(regeln) > maximal:
        befunde.append(f"{len(regeln)} rules > {maximal} per {scope.lower()}-scope policy")
    for r in regeln:
        for c in r.get("conditions") or []:
            n = len((c.get("predicate") or {}).get("values") or [])
            if not 1 <= n <= POLICY_MAX_VALUES_PER_CONDITION:
                befunde.append(f"rule '{r.get('displayName')}' condition {c.get('targetProperty')}: "
                               f"{n} values (allowed 1–{POLICY_MAX_VALUES_PER_CONDITION})")
    return befunde


def emit_fabric_policies(bp: dict) -> dict[str, str]:
    """Policy-Set als Zielbild (JSON) + Runbook. Nie aktivierungsbereit ausgeliefert: Preview, und in
    West/North Europe nicht verfuegbar — der Regionsbefund steht im Runbook, aus
    ``stack_capabilities`` (eine Tabelle, nicht zwei)."""
    from core.dataarch_engine.blueprint import stack_capabilities as _sc

    regeln = fabric_policy_rules(bp)
    regionen = _sc.blueprint_regionen(bp)
    urteile = {r: _sc.feature_in_region("fabric_policies", r) for r in regionen}
    grenzen = pruefe_policy_grenzen(regeln)
    payload = {
        "_note": ("Fabric policies (preview) — Allow item creation, capacity scope. TARGET PICTURE, not "
                  "an activation: remove _note/_status, replace every workspace-id placeholder with the workspace GUID, "
                  "check the item-type lists against everything this delivery creates, then create the "
                  "policy set and activate it (Git cannot activate). Read on "
                  f"{FABRIC_POLICIES_GEPRUEFT}: learn.microsoft.com/fabric/governance/"
                  "fabric-policies-item-creation."),
        "_status": "zielbild",
        "_region_verdict": urteile or {"": "unbekannt"},
        "scopeType": "Capacity",
        "rules": regeln,
    }
    ist_eu_block = any(v == "fehlt" for v in urteile.values())
    region_zeilen = ([f"| `{r}` | **{v}** |" for r, v in sorted(urteile.items())]
                     or ["| — (no capacity region declared) | **unbekannt** |"])
    teilen = bool(bp.get("sharing"))
    doc = [
        "# Fabric policies — which items may be created where (target picture)", "",
        f"Status: **preview**, read on {FABRIC_POLICIES_GEPRUEFT}. Delivered as a target picture only "
        "— `item_creation_policy.json` carries `_status: zielbild` and is not activation-ready.", "",
        "## Region first", "",
        "MS: *Fabric policies aren't currently supported in the following capacity regions: West "
        "Europe, North Europe, and West US.* Those are the EU regions most DACH deliveries use.", "",
        "| Capacity region | Fabric policies |", "|---|---|", *region_zeilen, "",
        ("> **Not available in this delivery's region.** Keep this file as documentation; nothing "
         "can be activated until Microsoft extends the region list.") if ist_eu_block else
        ("> Region not declared or not in the MS table — confirm before planning activation."
         if not urteile or any(v != "verfuegbar" for v in urteile.values()) else
         "> The declared region supports Fabric policies (preview)."),
        "",
        "## How the policy behaves", "",
        "- A policy set is an **item** in a workspace; its scope (Tenant or Capacity) is fixed at "
        "creation. Only **one** active policy per scope. Activation needs a capacity admin (Capacity) "
        "or Fabric admin (Tenant); **Git cannot activate**.",
        "- The only effect is **Allow**. The moment one rule exists, the policy is an **allow list**: "
        "everything no rule matches is blocked — across the whole capacity. That is why the JSON "
        "ends with a catch-all rule for every workspace outside this delivery.",
        f"- Limits: {POLICY_MAX_RULES_CAPACITY} rules per capacity policy, "
        f"{POLICY_MAX_RULES_TENANT} per tenant policy, {POLICY_MAX_VALUES_PER_CONDITION} values per "
        "condition; takes effect within 15 minutes; free, no CUs.",
        "- Conditions take **GUIDs** (`workspace.id`, `principal.groups.id`); `workspace.name` is "
        "rejected with `UnsupportedPropertyValue`. Activation with `ScopeType: Workspace` is rejected.",
        "- Item types are **API identifiers** (`DataPipeline`, not *Pipeline*).",
        "",
        "## Target picture per workspace role", "",
        "| Role | Allowed item types |", "|---|---|",
        *[f"| {r} | {', '.join(f'`{t}`' for t in ITEMTYPEN_JE_ROLLE.get(r, ())) or 'no restriction'} |"
          for r in sorted({r for _, r in _policy_workspaces(bp)})],
        "",
        "Before activation: add every item type this delivery itself deploys (variable libraries, "
        "environments, eventhouses, data agents …). Missing one blocks our own deployment with a "
        "policy error, not a permission error.", "",
        "## Collision with external data sharing", "",
        "The tenant-scope policy *Allow external data sharing* defaults to **Block all**. "
        + ("This delivery declares external shares (`sharing/`). Hergeleitet, not measured: "
           "activating a tenant policy set without an Allow rule for external data sharing would "
           "block them. Add that rule in the same set — or keep the tenant scope unactivated."
           if teilen else
           "This delivery declares no external shares today; the default only matters once one is "
           "added."),
        "",
        "## Limits check", "",
        ("All rules within the documented limits." if not grenzen else
         "**Over the documented limits:**\n\n" + "\n".join(f"- {g}" for g in grenzen)),
        "",
    ]
    return {FABRIC_POLICY_PATH: json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            "governance/fabric_policies/FABRIC_POLICIES.md": "\n".join(doc) + "\n"}


# --------------------------------------------------------------------------- Tags (I-21 W5.6 d)
TAGS_GEPRUEFT = "2026-09-29"
_TAG_FRAGE = "<VERIFY: Katalog-Tag je Domäne>"


def emit_tags(bp: dict) -> dict[str, str]:
    """Tags setzen per API — bis 29.09.2026 setzte diese Lieferung keine.

    Tags sind Katalog- und Such-Metadaten (OneLake catalog). Sie werden von Admins **definiert**
    (Tenant- oder Domaenen-Ebene) und an Items **angebracht**; diese Lieferung erfindet keine
    Tag-Namen: ``tags.json`` traegt je Domaene Platzhalter, das Skript loest Namen ueber die
    Admin-API in Ids auf und bringt sie an. Gelesen per Learn-MCP am 29.09.2026:
    `rest/api/fabric/admin/tags/list-tags` (GET /v1/admin/tags, Tenant.Read.All, 25/min),
    `rest/api/fabric/core/tags/apply-tags` (POST …/items/{itemId}/applyTags, Contributor, 25/min),
    `fabric/governance/tags-overview` (max. 10 Tags je Item, 10.000 je Tenant)."""
    ziel = {
        "_note": ("Tag names per domain, applied to every item in the domain's workspaces by "
                  "apply_tags.sh. Tags must already be defined by a Fabric/domain admin; replace each "
                  "VERIFY placeholder with an existing tag display name. Max 10 tags per item."),
        "domains": {d["name"]: {"workspaces": {str(w.get("name")): _ws_platzhalter(str(w.get("name")))
                                               for w in d.get("workspaces") or [] if w.get("name")},
                                "tags": [_TAG_FRAGE]}
                    for d in _domains(bp)},
    }
    sh = "\n".join([
        "#!/usr/bin/env bash",
        f"# Apply catalog tags to the delivery's items (generated, checked {TAGS_GEPRUEFT}).",
        "# 1) GET /v1/admin/tags resolves display names to ids (Fabric admin or SPN, Tenant.Read.All).",
        "# 2) POST /v1/workspaces/{ws}/items/{item}/applyTags per item (Contributor on the workspace).",
        "# Both APIs allow 25 requests per minute per principal - the loop sleeps 2.5 s per call.",
        "# The scanner returns tags as UUIDs; the catalog scan resolves them the same way (step 1).",
        "# Token from the environment, never as an argument.",
        "set -euo pipefail",
        ': "${FABRIC_TOKEN:?set FABRIC_TOKEN}"',
        'API="https://api.fabric.microsoft.com/v1"',
        'HERE="$(cd "$(dirname "$0")" && pwd)"',
        'TAGS_JSON="$(curl -sf -H "Authorization: Bearer $FABRIC_TOKEN" "$API/admin/tags")"',
        "export TAGS_JSON",
        "# Follow continuationUri if the tenant has more tags than one page (see the API reference).",
        'python3 - "$HERE/tags.json" <<\'PY\' | while IFS=$\'\\t\' read -r WS_ID TAG_IDS; do',
        "import json, sys, os",
        "ziel = json.load(open(sys.argv[1]))['domains']",
        "tags = {t['displayName']: t['id'] for t in json.loads(os.environ['TAGS_JSON'])['value']}",
        "for dom, z in sorted(ziel.items()):",
        "    offen = [n for n in z['tags'] if n.startswith('<') or n not in tags]",
        "    if offen:",
        "        sys.exit(f'domain {dom}: unresolved tag names {offen} - nothing applied')",
        "    for ws, ws_id in sorted(z['workspaces'].items()):",
        "        print(f\"{ws_id}\\t{','.join(tags[n] for n in z['tags'])}\")",
        "PY",
        '  case "$WS_ID" in "<"*) echo "workspace id not filled in: $WS_ID"; exit 1;; esac',
        '  for ITEM in $(curl -sf -H "Authorization: Bearer $FABRIC_TOKEN" \\',
        '      "$API/workspaces/$WS_ID/items" | python3 -c \'import json,sys; [print(i["id"]) for i in json.load(sys.stdin)["value"]]\'); do',
        '    BODY="$(python3 -c \'import json,sys; print(json.dumps({"tags": sys.argv[1].split(",")}))\' "$TAG_IDS")"',
        '    curl -sf -X POST -H "Authorization: Bearer $FABRIC_TOKEN" -H "Content-Type: application/json" \\',
        '      -d "$BODY" "$API/workspaces/$WS_ID/items/$ITEM/applyTags" >/dev/null',
        '    sleep 2.5',
        '  done',
        'done',
        "",
    ])
    return {"governance/tags.json": json.dumps(ziel, indent=2, ensure_ascii=False) + "\n",
            "governance/apply_tags.sh": sh}


# --------------------------------------------------------------------------- P5 external sharing
_SHARE_GROUNDED = "2026-08-26"   # MS Learn: Fabric Core/Admin External Data Share REST v1


def _share_inventory_py() -> str:
    """Read-only audit view over the documented Fabric Admin list API via semantic-link."""
    return (
        '"""inventory_shares.py — belegt die tatsaechlich existierenden External Data Shares (generiert).\n\n'
        "Dieses Skript ist die unabhaengige Gegenprobe nach REST- oder Portal-Anlage: Admin-API\n"
        "`List External Data Shares` ueber sempy. Laeuft unter einer\n"
        "Fabric-Admin-Identitaet; liest nur.\n\n"
        "Spalten laut Doku: External Data Share Id, Paths, Creator*, Recipient UPN,\n"
        'Recipient Tenant Id, Status, Expiration Time UTC, Workspace Id, Item Id, Invitation URL."""\n'
        "import sys\n\n\n"
        "def main() -> int:\n"
        "    try:\n"
        "        from sempy.fabric.admin import list_external_data_shares\n"
        "    except ImportError as e:\n"
        "        print(f'inventory: sempy nicht verfuegbar ({e}) — in einem Fabric-Notebook ausfuehren '\n"
        "              'oder semantic-link installieren.', file=sys.stderr)\n"
        "        return 3\n"
        "    df = list_external_data_shares()\n"
        "    if df is None or len(df) == 0:\n"
        "        print('inventory: KEIN External Data Share im Tenant. Wenn die Lieferung einen '\n"
        "              'deklariert, ist er noch nicht angelegt oder noch nicht akzeptiert.')\n"
        "        return 1\n"
        "    print(df.to_string(index=False))\n"
        "    # Ein Share ohne akzeptierten Empfaenger liefert nichts — und die Einladung verfaellt.\n"
        "    pending = df[df['Status'].astype(str).str.lower() != 'active'] if 'Status' in df else None\n"
        "    if pending is not None and len(pending):\n"
        "        print(f'\\ninventory: {len(pending)} Share(s) nicht aktiv — Einladungen verfallen nach '\n"
        "              '90 Tagen.')\n"
        "    return 0\n\n\n"
        'if __name__ == "__main__":\n'
        "    sys.exit(main())\n"
    )


def _sharing_md(bp: dict) -> str:
    """Die Lieferbedingungen fuer P5 — nicht ein Feature-Kapitel, sondern die Einschraenkungen, unter
    denen die Lieferung ueberhaupt gilt.

    Der Kern: **die Governance des Anbieter-Tenants ueberschreitet die Tenant-Grenze nicht.** Damit ist
    genau der Teil unserer Sicherheitsaussage aufgehoben, den wir sonst emittieren (RLS, Labels, DLP).
    Was uebrig bleibt, ist die **Sanitisierung** — und die steht in der IR. Deshalb ist sie hier die
    einzige tragende Kontrolle, nicht eine von mehreren."""
    shares = bp.get("sharing") or []
    shortcut_sources = sorted({i.get("source", "?") for i in (bp.get("ingestion") or [])
                               if i.get("access_mode") == "shortcut"})
    lines = [
        "# P5 External Data Sharing — Lieferbedingungen (generiert)", "",
        f"Gegroundet {_SHARE_GROUNDED} gegen `fabric/governance/external-data-sharing-*`. Dieses "
        "Dokument ist **keine** Feature-Beschreibung: es nennt die Bedingungen, unter denen die "
        "Lieferung gilt. Wer P5 einschaltet, hebt einen Teil des Sicherheitsmodells auf, das der Rest "
        "dieser Lieferung aufbaut.", "",
        "## Was tatsaechlich passiert", "",
        "Der Share kopiert nichts. Im Ziel-Tenant entsteht ein **OneLake-Shortcut** zurueck auf unsere "
        "Daten — Lesezugriff, **live**: jede Aenderung an der Quelle ist dort sofort sichtbar. Es gibt "
        "kein Zeitfenster, in dem ein Fehler noch nicht drueben ist.", "",
        "## Die Bedingung, die alles andere relativiert", "",
        "MS woertlich: *governance controls from the provider tenant don't flow across tenant "
        "boundaries*. Konkret sind **nicht** durchgesetzt, sobald Daten die Organisationsgrenze "
        "verlassen:", "",
        "| Kontrolle, die wir sonst emittieren | Ueber die Tenant-Grenze |",
        "|---|---|",
        "| Semantikmodell-RLS | **greift nicht** |",
        "| Purview Information Protection (Sensitivity Labels) | **greift nicht** |",
        "| Purview DLP | **greift nicht** |", "",
        "Stattdessen gelten die Richtlinien des **Verbraucher-Tenants** — die wir nicht kennen und nicht "
        "setzen. Drei Folgen, alle dokumentiert:", "",
        "1. Der Share gewaehrt Lesezugriff fuer **jeden Nutzer** im Heimat-Tenant des Eingeladenen — "
        "nicht nur fuer die eingeladene Person.",
        "2. Wir koennen **nicht steuern**, wer im Ziel-Tenant Zugriff hat. Der Verbraucher darf ihn "
        "weitergeben, **auch an Gastnutzer ausserhalb seiner eigenen Organisation**.",
        "3. Beim Zugriff im Ziel-Tenant koennen die Daten **geografische Grenzen ueberschreiten**. Fuer "
        "eine DSGVO-Lieferung ist das aussagepflichtig — es ist dieselbe Regionsachse, die schon Direct "
        "Lake, Iceberg-Shortcuts, den OneLake-Endpunkt und die AI-Dienste bindet, hier aber ausserhalb "
        "unseres Einflussbereichs.", "",
        "**Deshalb ist die Sanitisierung nicht eine Kontrolle unter mehreren, sondern die einzige, die "
        "die Grenze ueberlebt.** Was vor dem Share entfernt oder maskiert wurde, ist drueben nicht da; "
        "alles andere ist Vertrauenssache. Ein Label ersetzt sie nicht.", "",
    ]
    if shares:
        lines += ["## Diese Lieferung deklariert", "",
                  "| Externes Produkt | Quelle (Gold) | Label | Workspace | Sanitisierung |",
                  "|---|---|---|---|---|"]
        for s in shares:
            san = s.get("sanitization") or []
            san_txt = "; ".join(str(x) for x in san) if san else "**KEINE — siehe unten**"
            lines.append(f"| `{s.get('external_product', '?')}` | `{s.get('source_gold_ref', '?')}` "
                         f"| {s.get('label', '?')} | `{s.get('workspace', '?')}` | {san_txt} |")
        unsan = [s.get("external_product", "?") for s in shares if not (s.get("sanitization") or [])]
        if unsan:
            lines += ["", "> **Ohne Sanitisierung geteilt:** " + ", ".join(f"`{u}`" for u in unsan)
                      + ". Da Labels und DLP die Grenze nicht ueberschreiten, ist bei diesen Produkten "
                      "**keine** technische Kontrolle wirksam. Das Conformance-Gate meldet es als "
                      "`unsanitized_external`; hier steht, warum es mehr als ein Schoenheitsfehler ist."]
        lines.append("")
    if shortcut_sources:
        lines += ["## Falle, die unsere eigene Ingestions-Doktrin trifft", "",
                  "Dokumentiert: **Shortcuts innerhalb eines geteilten Ordners loesen im Ziel-Tenant "
                  "nicht auf.** Diese Lieferung bindet folgende Quellen per Shortcut ein: "
                  + ", ".join(f"`{s}`" for s in shortcut_sources)
                  + ". Wird eine Ebene geteilt, die selbst auf Shortcuts steht, kommt beim Partner "
                  "**nichts** an — ohne Fehlermeldung bei uns. Nur materialisierte Tabellen teilen "
                  "(unser Gold ist materialisiert; Bronze/Silver mit `access_mode: shortcut` sind es "
                  "nicht).", ""]
    lines += [
        "## Wer was tun muss — und was wir NICHT tun koennen", "",
        "| Schritt | Wo | Wer |",
        "|---|---|---|",
        "| Tenant-Einstellung *External data sharing* einschalten + Berechtigte festlegen | unser Tenant "
        "| unser Fabric-Admin |",
        "| Tenant-Einstellung *Users can accept external data shares* einschalten | **Partner-Tenant** "
        "| Admin des Partners — **wir haben dort keinen Zugriff** |",
        "| Share anlegen (`POST .../externalDataShares`) | unser Tenant | Nutzer/SP/MI mit Read + "
        "Reshare und `Item.ExternalDataShare.All` |",
        "| Einladung pruefen und annehmen (`GET invitation`, `POST .../accept`) | Partner-Tenant | "
        "Partneridentitaet mit Schreibrecht am Ziel-Item |", "",
        "Microsoft dokumentiert inzwischen Create-, Invitation-Details-, Accept-, List- und "
        "Revoke-Endpunkte. Der Baukasten emittiert deshalb `apply_external_share.py` sowie je "
        "Provider-Workspace einen **gesperrten** Vertrag. Eine Mutation laeuft erst mit "
        "`status=approved` und `apply_authorized=true`; Tokens bleiben in "
        "`FABRIC_PROVIDER_TOKEN` bzw. `FABRIC_CONSUMER_TOKEN`. `inventory_shares.py` bleibt als "
        "zweite, read-only Admin-Gegenprobe erhalten.", "",
        "Zwei Fristen: die Einladung verfaellt nach **90 Tagen**; ein Widerruf ist jederzeit moeglich, "
        "hat aber laut MS *serious implications* fuer den Verbraucher — er verliert live Daten, auf "
        "denen dort womoeglich Berichte stehen. Widerruf ist eine Absprache, kein Klick.", "",
        "## Vor der Zusage zu klaeren", "",
        "- Welche Richtlinien gelten im Ziel-Tenant? (Unsere gelten dort nicht.)",
        "- Ist der Weiterverteilung an Dritte, einschliesslich Gastnutzer, zugestimmt?",
        "- Ist die geografische Verarbeitung im Ziel-Tenant DSGVO-seitig abgedeckt?",
        "- Ist die Sanitisierungsliste je Produkt fachlich abgenommen — als **die** Kontrolle, nicht als "
        "eine von mehreren?", "",
    ]
    return "\n".join(lines) + "\n"


def emit_sharing(bp: dict, stack: str = "fabric") -> dict[str, str]:
    """P5-Lieferbedingungen + Share-Inventar. Leer, wenn die IR keinen Share deklariert — dann ist P5
    nicht anwendbar und ein Dokument darueber waere Rauschen."""
    if stack != "fabric" or not (bp.get("sharing") or []):
        return {}
    from core.dataarch_engine.blueprint.provision_external_sharing import emit_external_share_runtime

    out = {"sharing/_SHARING.md": _sharing_md(bp),
           "sharing/inventory_shares.py": _share_inventory_py()}
    out.update(emit_external_share_runtime(bp))
    return out
