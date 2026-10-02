"""provision_purview — Microsoft Purview als Andockmodul (D-620).

OneLake catalog ist die Governance-Oberflaeche jeder Lieferung (Domaenen, Endorsement, Tags,
Scanner, Beschreibungen) und braucht kein Purview. Purview kommt nur, wenn ein Projekt es im
Umfang hat — dann soll es ohne Nacharbeit funktionieren. Der Schalter ist
``governance.purview`` im Bauplan:

* fehlt oder ``im_umfang: nein`` → kein Purview-Artefakt, nur ``_PURVIEW.md`` mit den
  Andockpunkten (was es braucht, wenn es spaeter kommt);
* ``unbekannt`` → dasselbe Dokument als offene Kundenfrage;
* ``ja`` → je Baustein in ``bausteine`` ein lauffaehiges Paket unter ``governance/purview/``.

Jeder Weg ist auf Microsoft Learn belegt (gelesen 01.10.2026, Quellen je Abschnitt). Was nur im
Portal geht, steht als Portal-Schritt da, nicht als erfundener Aufruf. Tenant-Fakten (Workspace-,
Item- und Label-IDs) kommen nicht aus dem Bauplan; wo sie fehlen, steht ein Marker, der beim
Ausfuehren laut scheitert.
"""
from __future__ import annotations

import json
from typing import Any

#: Marker fuer Tenant-Fakten, die der Bauplan nicht kennt (wie UNRESOLVED in provision_ingestion).
OFFEN = "TODO-TENANT-ID"

BAUSTEINE: tuple[str, ...] = ("labels", "dlp", "data_map", "unified_catalog", "audit", "data_quality")

_LEARN = "https://learn.microsoft.com"
QUELLEN: dict[str, tuple[str, ...]] = {
    "data_map": (f"{_LEARN}/purview/register-scan-fabric-tenant",
                 f"{_LEARN}/rest/api/purview/scanningdataplane/data-sources/create-or-replace",
                 f"{_LEARN}/rest/api/purview/scanningdataplane/scans/create-or-replace"),
    "labels": (f"{_LEARN}/rest/api/fabric/admin/labels/bulk-set-labels",
               f"{_LEARN}/fabric/governance/sensitivity-label-default-label-policy",
               f"{_LEARN}/fabric/governance/mandatory-label-policy",
               f"{_LEARN}/fabric/admin/service-admin-portal-information-protection"),
    "dlp": (f"{_LEARN}/purview/dlp-powerbi-get-started",
            f"{_LEARN}/powershell/module/exchangepowershell/new-dlpcompliancepolicy",
            f"{_LEARN}/fabric/governance/data-loss-prevention-configure"),
    "unified_catalog": (f"{_LEARN}/rest/api/purview/unified-catalog-api-overview",
                        f"{_LEARN}/rest/api/purview/purview-unified-catalog/business-domain/create",
                        f"{_LEARN}/purview/data-gov-best-practices-domains-and-gov-domains"),
    "audit": (f"{_LEARN}/fabric/governance/microsoft-purview-fabric",
              f"{_LEARN}/purview/audit-log-retention-policies",
              f"{_LEARN}/graph/api/security-auditcoreroot-post-auditlogqueries"),
    "data_quality": (f"{_LEARN}/purview/unified-catalog-data-quality-fabric-lakehouse",),
}

#: Lizenz je Baustein — nur, was Learn sagt (keine Preise).
LIZENZ: dict[str, str] = {
    "labels": "Azure Information Protection Premium P1/P2 zum Anwenden, dazu Power BI Pro oder PPU zum Labeln",
    "dlp": "Microsoft 365 E5, E5 Compliance, E5 Information Protection & Governance oder Purview capacities; "
           "Abrechnung je Asset im Geltungsbereich und Tag",
    "data_map": "Purview-Konto; nach Pay-as-you-go-Consent bzw. Enterprise-Upgrade keine Data-Map- und Scan-Kosten",
    "unified_catalog": "Pay-as-you-go je gesteuertem Asset und Tag (Azure-Subscription im selben Tenant)",
    "audit": "Standard in M365/O365 (180 Tage); Premium mit E5/Purview Suite (Aufbewahrungsrichtlinien bis 1 Jahr, "
             "Add-on 10 Jahre)",
    "data_quality": "Pay-as-you-go (Data Governance Processing Units)",
}


def status(bp: dict) -> str:
    """``ja`` · ``nein`` · ``unbekannt``. Fehlt das Feld, ist Purview nicht im Umfang."""
    pv = (bp.get("governance") or {}).get("purview") or {}
    return str(pv.get("im_umfang") or "nein")


def bausteine(bp: dict) -> tuple[str, ...]:
    """Die Bausteine, die geliefert werden — leer, solange Purview nicht im Umfang ist."""
    if status(bp) != "ja":
        return ()
    gewaehlt = ((bp.get("governance") or {}).get("purview") or {}).get("bausteine") or []
    return tuple(b for b in BAUSTEINE if b in gewaehlt)


def im_umfang(bp: dict, baustein: str) -> bool:
    return baustein in bausteine(bp)


def _pv(bp: dict) -> dict:
    return (bp.get("governance") or {}).get("purview") or {}


def _json(o: Any) -> str:
    return json.dumps(o, indent=2, ensure_ascii=False) + "\n"


def _domains(bp: dict) -> list[dict]:
    return sorted(bp.get("mesh", {}).get("domains", []), key=lambda d: d.get("name", ""))


# --------------------------------------------------------------------------- Data Map
def _data_map(bp: dict) -> dict[str, str]:
    pv = _pv(bp)
    konto = pv.get("konto") or OFFEN
    collection = pv.get("collection") or OFFEN
    quelle = {"kind": "PowerBI",
              "properties": {"tenant": OFFEN, "collection": {"type": "CollectionReference",
                                                             "referenceName": collection}}}
    scan = {"kind": "PowerBIMsi",
            "properties": {"includePersonalWorkspaces": False,
                           "collection": {"type": "CollectionReference", "referenceName": collection}}}
    sh = [
        "#!/usr/bin/env bash",
        "# Fabric-Tenant in der Purview Data Map registrieren und scannen (D-620).",
        f"# Quellen: {', '.join(QUELLEN['data_map'])} (gelesen 01.10.2026).",
        "# Voraussetzungen (Portal, einmalig — siehe _PURVIEW.md Abschnitt Data Map):",
        "#   1. Entra-Sicherheitsgruppe, Purview-Managed-Identity als Mitglied",
        "#   2. Fabric-Tenant-Einstellungen fuer diese Gruppe: read-only Admin-APIs fuer Dienstprinzipale,",
        "#      detaillierte Metadaten, DAX- und Mashup-Ausdruecke; danach ~15 Minuten warten",
        "#   3. Mit OneLake Security: Rolle mit Read fuer die Purview-Identitaet",
        "# Token kommt aus der Umgebung, nie als Argument: PURVIEW_TOKEN (Scope https://purview.azure.net/.default).",
        "set -euo pipefail",
        f'ENDPOINT="https://{konto}.purview.azure.com"',
        ': "${PURVIEW_TOKEN:?PURVIEW_TOKEN fehlt}"',
        'API="api-version=2023-09-01"',
        'auth() { printf "Authorization: Bearer %s" "$PURVIEW_TOKEN"; }',
        '# Der Fabric-Typ heisst in der API weiterhin "PowerBI" (Learn: "renamed to Fabric in all regions").',
        'curl -sSf -X PUT "$ENDPOINT/scan/datasources/fabric-tenant?$API" -H "$(auth)" \\',
        '  -H "Content-Type: application/json" --data @register_source.json',
        'curl -sSf -X PUT "$ENDPOINT/scan/datasources/fabric-tenant/scans/fabric-msi?$API" -H "$(auth)" \\',
        '  -H "Content-Type: application/json" --data @scan.json',
        'echo "Quelle und Scan angelegt. Zeitplan: Triggers - Create Or Replace (Portal oder API)."',
    ]
    return {"governance/purview/data_map/register_source.json": _json(quelle),
            "governance/purview/data_map/scan.json": _json(scan),
            "governance/purview/data_map/data_map.sh": "\n".join(sh) + "\n"}


# --------------------------------------------------------------------------- Labels
def labels_script(bp: dict, governance: dict | None = None) -> str:
    """``set_labels.sh`` — Labels auf Fabric-Items ueber ``admin/items/bulkSetLabels``.

    Ersetzt das alte ``sensitivity_labels.sh``: dort stand ``informationProtection/setLabelsAsAdmin``,
    einen Endpunkt, den es so nicht gibt (Learn 01.10.2026: Fabric ``admin/items/bulkSetLabels``,
    Power BI ``admin/informationprotection/setLabels``). Fabric deckt alle Item-Typen ab; ein
    Dienstprinzipal ist **nicht** unterstuetzt — der Aufruf laeuft unter einem Fabric-Administrator.
    """
    labels = (governance or {}).get("labels", {})
    z = [
        "#!/usr/bin/env bash",
        "# Sensitivity Labels auf Fabric-Items (D-620). Quelle: " + QUELLEN["labels"][0],
        "#   POST https://api.fabric.microsoft.com/v1/admin/items/bulkSetLabels",
        "#   bis 2.000 Items je Aufruf, 25 Aufrufe je Stunde, Scope Tenant.ReadWrite.All.",
        "#   Nur ein BENUTZER mit Fabric-Administratorrolle — Dienstprinzipal: nein (Learn).",
        "#   Das Label muss in der Label-Policy des Aufrufenden stehen.",
        "# Token aus der Umgebung: FABRIC_ADMIN_TOKEN (Benutzer-Token), nie als Argument.",
        "set -euo pipefail",
        ': "${FABRIC_ADMIN_TOKEN:?FABRIC_ADMIN_TOKEN fehlt}"',
        'URL="https://api.fabric.microsoft.com/v1/admin/items/bulkSetLabels"',
        "",
    ]
    for d in _domains(bp):
        aud = d.get("publishing", {}).get("intended_audience", "internal")
        label = labels.get(aud) or OFFEN
        body = {"items": [{"id": OFFEN, "type": "SemanticModel"}, {"id": OFFEN, "type": "Report"}],
                "labelId": label, "assignmentMethod": "Standard"}
        z += [f"# {d['name']} ({aud}) — Item-IDs nach dem Deployment eintragen",
              f"cat > /tmp/labels_{d['name'].lower().replace(' ', '_')}.json <<'JSON'",
              json.dumps(body, ensure_ascii=False),
              "JSON",
              'curl -sSf -X POST "$URL" -H "Authorization: Bearer $FABRIC_ADMIN_TOKEN" \\',
              f'  -H "Content-Type: application/json" --data @/tmp/labels_{d["name"].lower().replace(" ", "_")}.json',
              ""]
    z.append('echo "Labels gesetzt."')
    return "\n".join(z) + "\n"


def _label_policy(bp: dict) -> str:
    pv = _pv(bp)
    std = pv.get("standardlabel_id") or OFFEN
    z = [
        "# Label-Policy fuer Fabric und Power BI (D-620). Security & Compliance PowerShell.",
        f"# Quellen: {QUELLEN['labels'][1]} · {QUELLEN['labels'][2]}",
        "# Vorher (Portal): Labels in Purview Information Protection anlegen und VEROEFFENTLICHEN.",
        "# Standard- und Pflichtlabel gelten nicht fuer Dienstprinzipale und APIs (Learn).",
        "Connect-IPPSSession",
        '$Policy = "<Label-Policy-Name>"',
        f'Set-LabelPolicy -Identity $Policy -AdvancedSettings @{{powerbidefaultlabelid="{std}"}}',
    ]
    if pv.get("pflichtlabel"):
        z.append('Set-LabelPolicy -Identity $Policy -AdvancedSettings @{powerbimandatory="true"}')
    else:
        z.append('# Pflichtlabel nicht gewaehlt (governance.purview.pflichtlabel); sonst:')
        z.append('# Set-LabelPolicy -Identity $Policy -AdvancedSettings @{powerbimandatory="true"}')
    return "\n".join(z) + "\n"


# --------------------------------------------------------------------------- DLP
def _dlp(bp: dict) -> str:
    z = [
        "# DLP-Richtlinie fuer Fabric und Power BI (D-620). Security & Compliance PowerShell.",
        f"# Quellen: {', '.join(QUELLEN['dlp'])} (gelesen 01.10.2026).",
        "# Gilt nur fuer Workspaces auf Fabric- oder Premium-Kapazitaet. Unterstuetzt: Semantikmodelle,",
        "# Lakehouses, Warehouses, KQL-, gespiegelte, SQL- und Cosmos-Datenbanken.",
        "# ACHTUNG Dienstprinzipal: DLP prueft ein Semantikmodell NICHT, wenn ein Dienstprinzipal es",
        "# veroeffentlicht, aktualisiert oder besitzt. Diese Lieferung stellt per Dienstprinzipal bereit —",
        "# fuer ihre Modelle greift die Richtlinie erst, wenn ein Benutzer Eigentuemer ist.",
        "Connect-IPPSSession",
        "# Workspace-IDs der Lieferung (aus dem Deployment) statt 'All':",
    ]
    ws = [w.get("name", "") for d in _domains(bp) for w in d.get("workspaces", []) or []]
    z.append("$Workspaces = @(" + ", ".join(f'"{OFFEN}"  <# {n} #>' for n in ws or ["<workspace>"]) + ")")
    z += [
        'New-DlpCompliancePolicy -Name "Fabric-DLP" -PowerBIDlpLocation $Workspaces -Mode TestWithNotifications',
        "# Bedingung ueber Sensitivity Labels (AdvancedRule-JSON). ANNAHME, ungeprueft: welche Regel-",
        "# Parameter fuer die Power-BI-Location zulaessig sind, beschreibt Learn nicht (nur das Portal).",
        "# Erst mit -Mode TestWithNotifications laufen lassen und im Portal gegenlesen.",
        "$Regel = @'",
        '{"Version":"1.0","Condition":{"Operator":"And","SubConditions":[{"ConditionName":"ContentContainsSensitiveInformation",'
        '"Value":[{"groups":[{"Operator":"Or","labels":[{"name":"<Label-Name>","type":"Sensitivity"}]}]}]}]}}',
        "'@",
        'New-DlpComplianceRule -Name "Fabric-DLP-Label" -Policy "Fabric-DLP" -AdvancedRule $Regel -GenerateAlert $true -NotifyUser Owner',
        "# 'Restrict access' (Preview) ist auf Learn nur als Portal-Aktion beschrieben. ANNAHME, ungeprueft:",
        "# -BlockAccess $true -AccessScope NotInOrganization -BlockAccessScope PerUser",
        "# Nach der Testphase: Set-DlpCompliancePolicy -Identity \"Fabric-DLP\" -Mode Enable",
    ]
    return "\n".join(z) + "\n"


# --------------------------------------------------------------------------- Unified Catalog
def _unified_catalog(bp: dict) -> dict[str, str]:
    domaenen = [{"name": d["name"], "type": "DataDomain", "status": "DRAFT",
                 "description": (d.get("publishing", {}).get("metadata") or {}).get("description")
                 or f"Governance-Domaene {d['name']}"} for d in _domains(bp)]
    sh = [
        "#!/usr/bin/env bash",
        "# Purview Unified Catalog: Governance-Domaenen anlegen (D-620). API Public Preview.",
        f"# Quellen: {', '.join(QUELLEN['unified_catalog'])} (gelesen 01.10.2026).",
        "# Fabric-Domaenen und Governance-Domaenen sind NICHT gekoppelt (Learn: Fabric-Domaenen",
        "# uebersteigen das Limit von 5 Governance-Domaenen). Hier: eine Governance-Domaene je",
        "# Bauplan-Domaene als ENTWURF — zusammenfassen, bevor veroeffentlicht wird.",
        "# Rechte: Rolle 'Governance domain creator' fuer den aufrufenden Prinzipal.",
        "set -euo pipefail",
        ': "${PURVIEW_TOKEN:?PURVIEW_TOKEN fehlt}"',
        'URL="https://api.purview-service.microsoft.com/datagovernance/catalog/businessdomains?api-version=2026-03-20-preview"',
        'python3 - <<\'PY\'',
        "import json, os, urllib.request",
        "for d in json.load(open('business_domains.json')):",
        "    r = urllib.request.Request(os.environ['URL'], data=json.dumps(d).encode(), method='POST',",
        "        headers={'Authorization': 'Bearer ' + os.environ['PURVIEW_TOKEN'], 'Content-Type': 'application/json'})",
        "    print(d['name'], urllib.request.urlopen(r).status)",
        "PY",
    ]
    sh.insert(sh.index('python3 - <<\'PY\''), "export URL")
    return {"governance/purview/unified_catalog/business_domains.json": _json(domaenen),
            "governance/purview/unified_catalog/unified_catalog.sh": "\n".join(sh) + "\n"}


# --------------------------------------------------------------------------- Audit
def _audit() -> str:
    q = {"displayName": "Fabric-Aktivitaeten", "filterStartDateTime": "<YYYY-MM-DDT00:00:00Z>",
         "filterEndDateTime": "<YYYY-MM-DDT00:00:00Z>", "recordTypeFilters": ["powerBIAudit"]}
    return _json({"_comment": "POST https://graph.microsoft.com/v1.0/security/auditLog/queries "
                              "(Berechtigung AuditLogsQuery.Read.All). Quelle: " + QUELLEN["audit"][2],
                  "body": q})


# --------------------------------------------------------------------------- Dokument
def _doc(bp: dict) -> str:
    st, gew = status(bp), bausteine(bp)
    z = ["# Purview — Andockmodul (D-620)", "",
         "OneLake catalog ist die Governance-Oberflaeche dieser Lieferung: Domaenen, Endorsement,",
         "Tags, Beschreibungen und der Katalogscan (`governance/`, `lineage/`). Dafuer braucht es",
         "kein Purview. Purview dockt an, wenn das Projekt es im Umfang hat.", "",
         f"**Stand im Bauplan:** `governance.purview.im_umfang = {st}`"
         + (f", Bausteine: {', '.join(f'`{b}`' for b in gew)}" if gew else ""), ""]
    if st == "unbekannt":
        z += ["**Offene Kundenfrage:** Ist Microsoft Purview im Umfang, und welche Bausteine",
              "(Labels, DLP, Data Map, Unified Catalog, Audit, Data Quality)? Bis zur Antwort wird",
              "nichts davon gebaut.", ""]
    z += ["| Baustein | geliefert | Lizenz (Learn) | automatisierbar |", "|---|---|---|---|"]
    auto = {"labels": "PowerShell (Label-Policy) + REST `admin/items/bulkSetLabels` (nur Benutzer)",
            "dlp": "PowerShell `New-DlpCompliancePolicy -PowerBIDlpLocation`",
            "data_map": "REST Scanning Data Plane (Quelle + Scan); Sicherheitsgruppe und Tenant-Einstellungen Portal",
            "unified_catalog": "REST (Preview)",
            "audit": "Graph `security/auditLog/queries`",
            "data_quality": "nur Portal-Verbindung belegt; nicht gebaut"}
    for b in BAUSTEINE:
        z.append(f"| `{b}` | {'ja' if b in gew else '—'} | {LIZENZ[b]} | {auto[b]} |")
    z += ["", "## Grenzen, die jede Purview-Lieferung kennt", "",
          "- **Dienstprinzipal:** DLP prueft keine Semantikmodelle, die ein Dienstprinzipal",
          "  veroeffentlicht, aktualisiert oder besitzt; Standard- und Pflichtlabel gelten nicht fuer",
          "  Dienstprinzipale und APIs; `bulkSetLabels` nimmt keinen Dienstprinzipal. Die Bereitstellung",
          "  dieser Lieferung laeuft per Dienstprinzipal.",
          "- **Data Map:** Fabric mit Private Link auf Tenant- oder Workspace-Ebene wird nicht gescannt;",
          "  ausser Power BI nur Item-Ebene, Lakehouse-Tabellen ohne Lineage. Mit OneLake Security",
          "  braucht die Purview-Identitaet eine Rolle mit Read.",
          "- **Unified Catalog:** Fabric-Domaenen bilden sich nicht 1:1 auf Purview ab (Data Map: hoechstens",
          "  fuenf Plattform-Domaenen); Governance-Domaenen werden getrennt gepflegt und ueber",
          "  Data-Estate-Mappings an Collections gehaengt.",
          "- **Data Quality:** in A-20 verworfen (Leerzeichen in Spaltennamen, MSI braucht Contributor auf",
          "  dem Workspace, Regeln nicht in Git); Learn widerspricht sich bei SPN vs. MSI.", "",
          "## Quellen", ""]
    for b in BAUSTEINE:
        z.append(f"- `{b}`: " + " · ".join(QUELLEN[b]))
    return "\n".join(z) + "\n"


def emit_purview(bp: dict, stack: str = "fabric", governance: dict | None = None) -> dict[str, str]:
    """``governance/purview/`` — immer das Dokument, die Pakete nur fuer gewaehlte Bausteine."""
    if stack != "fabric":
        return {}
    out = {"governance/purview/_PURVIEW.md": _doc(bp)}
    gew = bausteine(bp)
    if "data_map" in gew:
        out.update(_data_map(bp))
    if "labels" in gew:
        out["governance/purview/labels/set_labels.sh"] = labels_script(bp, governance)
        out["governance/purview/labels/label_policy.ps1"] = _label_policy(bp)
    if "dlp" in gew:
        out["governance/purview/dlp/dlp_policy.ps1"] = _dlp(bp)
    if "unified_catalog" in gew:
        out.update(_unified_catalog(bp))
    if "audit" in gew:
        out["governance/purview/audit/audit_query.json"] = _audit()
    return out
