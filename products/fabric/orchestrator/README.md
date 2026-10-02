# Fabric Enterprise Orchestrator (v2.0)

Python-basiertes CLI-Tool für vollständige Medallion-Architektur-Provisionierung in Microsoft Fabric. Implementiert Domain-Driven Design mit konfigurierbarer Strategie: **Enterprise** (9 Workspaces) oder **Compact** (3 Workspaces).

## Positionierung im Repo

**V2.0 (dieses Tool)**: Domain-Driven Medallion (Src/Trf/Anl), REST-first (`msal` + `requests`), Deployment Pipelines API.

**V1 (bestehendes System)**: Funktionale Workspace-Trennung (DE_/DM_/BI_), Fabric CLI + `fabric-cicd`, Release-Automation.  
→ Siehe `products/fabric/powerbi/deployment/` für V1-Setup/Release-Skripte.

---

## Architektur

### Architecture Strategies (--strategy)

Ein Schlagwort steuert die Workspace-Matrix; Wechsel jederzeit möglich (gleicher Befehl, anderes `--strategy`). Default kann in `config.yaml` via `default_strategy: enterprise` oder `default_strategy: compact` gesetzt werden.

| Strategy | Workspaces pro Domain | Naming (Beispiel Sales) |
|----------|------------------------|--------------------------|
| **enterprise** (Default) | 9 | `Sales_Src_Dev`, `Sales_Trf_Dev`, `Sales_Anl_Dev`, … (Layer × Dev/Test/Prod) |
| **compact** | 3 | `Sales_Dev`, `Sales_Test`, `Sales_Prod` (ein Workspace pro Environment, logische Trennung innerhalb) |

- **Enterprise:** Strikte Compute-Trennung (Spark/SQL/Semantic), OneLake Shortcuts Src→Trf, volle Governance.
- **Compact:** Pragmatisch für KMU/Mid-Size; Lakehouse (Bronze/Silver) + Warehouse-Schema (Gold) + Reports im selben Workspace.

### Workspace-Matrix (Enterprise: 9 pro Domain)

| Layer | Dev | Test | Prod |
|-------|-----|------|------|
| **Src** (Bronze/Silver) | `Sales_Src_Dev` | `Sales_Src_Test` | `Sales_Src_Prod` |
| **Trf** (Gold, Warehouse) | `Sales_Trf_Dev` | `Sales_Trf_Test` | `Sales_Trf_Prod` |
| **Anl** (Semantic Models) | `Sales_Anl_Dev` | `Sales_Anl_Test` | `Sales_Anl_Prod` |

### Layer-Definitionen

- **Src (Source/Ingest)**: Lakehouse für Bronze (Raw) & Silver (Cleaned). Spark-basiert.
- **Trf (Transform/Warehouse)**: Warehouse für Gold (Curated). dbt-fabric (T-SQL).
- **Anl (Analytics/Serving)**: Semantic Models (Direct Lake) & Power BI Reports.

### Data Linkage (Zero-Copy)

OneLake Shortcuts: `Trf` projiziert Daten von `Src` (keine Duplizierung).

---

## Prerequisites

### 1. Service Principal (SPN)

Erstellen Sie eine Azure AD App Registration:

1. Azure Portal → App registrations → New registration
2. Name: `fabric-orchestrator-spn`
3. Supported account types: Single tenant
4. Redirect URI: (leer)
5. Register → Certificates & secrets → New client secret → Copy value
6. Note: `tenant_id`, `client_id`, `client_secret`

**Notwendige API-Rechte**:
- Microsoft Graph: (keine, sofern nur Fabric-Operationen)
- Power BI Service / Fabric: Der SPN benötigt **Capacity Admin** oder **Fabric Administrator**-Rolle

### 2. Tenant Settings

Aktivieren Sie unter **OneLake catalog → Govern → Configurations → Tenant settings**
(Fallback: Settings (Zahnrad) → Admin portal → Tenant settings, solange Govern in Ihrer Region
noch nicht ausgerollt ist. Grenzen von Govern: nicht verfügbar bei aktiviertem Private Link,
keine Gastbenutzer und keine Cross-Tenant-Szenarien; dort bleibt das Admin portal der Weg — Learn
[About tenant settings](https://learn.microsoft.com/fabric/admin/about-tenant-settings),
[Govern](https://learn.microsoft.com/fabric/governance/onelake-catalog-govern), gelesen 01.10.2026):
- "Users can create Fabric items" (oder spezifisch für den SPN)
- "Users can synchronize workspace items with their Git repositories"
- "Service principals can use Fabric APIs"

### 3. Capacity

Sie benötigen eine Fabric Capacity (F2+) oder Power BI Premium Capacity (P1+). Notieren Sie die Capacity-ID(s) für `config.yaml`. Für Kostenabschätzungen (Fabric-SKUs, Pro/PPU) siehe `products/proposal_costing`.

### 4. Git Repository

GitHub oder Azure DevOps Repo. Für Git-Sync benötigt Fabric die Repo-URL und Branch-Namen.

Optional: PAT (Personal Access Token) für Branch-Creation (wenn Tool Feature-Branches automatisch erstellen soll).

---

## Installation

```bash
cd products/fabric/orchestrator
pip install -r requirements.txt
```

**Dependencies**:
- `msal` (SPN-Auth)
- `requests` (Fabric REST APIs)
- `typer` (CLI)
- `pyyaml` (Config)
- `dbt-fabric` (optional, für Template-Generierung)

---

## Konfiguration

Kopieren Sie `config.yaml.example` → `config.yaml` und passen Sie an:

```yaml
fabric:
  tenant_id: "YOUR_TENANT_ID"
  authority: "https://login.microsoftonline.com/{tenant_id}"
  api_base: "https://api.fabric.microsoft.com/v1"
  scopes:
    - "https://api.fabric.microsoft.com/.default"

capacities:
  dev:
    sku: "F2"
    capacity_id: "00000000-0000-0000-0000-000000000000"
  test:
    sku: "F4"
    capacity_id: "11111111-1111-1111-1111-111111111111"
  prod:
    sku: "F8"
    capacity_id: "22222222-2222-2222-2222-222222222222"

git_provider:
  type: "github"  # oder "azuredevops"
  repo_url: "https://github.com/your-org/your-repo"
  organization: "your-org"
  project: "your-project"  # nur Azure DevOps
  branches:
    dev: "dev"
    test: "test"
    prod: "main"

governance:
  sensitivity_labels:
    dev: "General"
    test: "General"
    prod: "Confidential"
  endorsement:
    anl_layer: "Promoted"  # für Anl-Items (Gold Semantic Models)

domains:
  - name: "Sales"
    layers: ["Src", "Trf", "Anl"]
  - name: "Finance"
    layers: ["Src", "Trf", "Anl"]
```

**Secrets (ENV, nie in config.yaml)**:

```bash
export FABRIC_CLIENT_ID="your-client-id"
export FABRIC_CLIENT_SECRET="your-client-secret"
export GIT_PAT="your-git-pat"  # optional
```

---

## CLI-Befehle

### `init-domain`

Erstellt Workspaces für eine Domain (Anzahl abhängig von `--strategy`).

```bash
# Enterprise (9 Workspaces) – Default
python orchestrator.py init-domain --name Sales --capacity-dev F2 --capacity-test F4 --capacity-prod F8

# Compact (3 Workspaces)
python orchestrator.py init-domain --name Sales --strategy compact --capacity-dev F2
```

**Was passiert**:
1. Erstellt Workspaces (enterprise: 9, compact: 3); idempotent
2. Weist Kapazitäten zu
3. Sensitivity Labels (General für Dev/Test, Confidential für Prod): Standard `purview_policy` überlässt sie der Purview-Labelrichtlinie; `admin_api` mit SPN setzt nichts, sondern meldet einen manuellen Schritt mit fertigem Aufruf (siehe *Fehler: "Sensitivity label not found"*)
4. Verknüpft mit Git (Branch/Folder je Strategy)
5. Erstellt Deployment Pipeline und weist Stages zu (Enterprise: Anl-Workspaces, Compact: ein WS pro Env)

**Default-Strategy:** In `config.yaml` kann `default_strategy: compact` gesetzt werden; dann ist `--strategy` nur beim Wechsel nötig.

**Dry-Run**:
```bash
python orchestrator.py init-domain --name Sales --strategy compact --dry-run
```

---

### `create-feature`

Erstellt isolierte Feature-Workspaces (enterprise: 3, compact: 1).

```bash
python orchestrator.py create-feature --domain Sales --feature-name jira-123 --dev-capacity F2
python orchestrator.py create-feature --domain Sales --feature-name jira-123 --strategy compact
```

**Was passiert**:
1. Enterprise: `Sales_Src_Feat_jira-123`, `Sales_Trf_Feat_jira-123`, `Sales_Anl_Feat_jira-123`; Compact: `Sales_Feat_jira-123`
2. Weist kleine Dev-Capacity zu (Kostenoptimierung)
3. Verknüpft mit Feature-Branch: `feature/jira-123`
4. Optional: Generiert Spark Notebook + dbt Skeleton lokal

---

### `deploy`

Triggert Deployment Pipeline (Promotion DEV → TEST oder TEST → PROD). Target-Workspace für Parameter-Update hängt von der Strategy ab.

```bash
python orchestrator.py deploy --domain Sales --target test
python orchestrator.py deploy --domain Sales --target prod --strategy compact
```

**Was passiert**:
1. Ermittelt Deployment Pipeline für Domain
2. Ruft Fabric Deployment Pipelines API auf: `POST /v1/deploymentPipelines/{pipelineId}/deploy`
3. Wartet auf Completion
4. Aktualisiert Parameter (Connection Strings, Workspace/Item IDs) gemäß `config.yaml`

**Kommentar im Code** markiert explizit die API-Calls für Deployment Pipelines und Parameter-Updates.

---

### `destroy-feature`

Löscht Feature-Workspaces (Clean-up). Erkennt sowohl Enterprise- (3) als auch Compact-Namen (1); kein `--strategy` nötig.

```bash
python orchestrator.py destroy-feature --domain Sales --feature-name jira-123
```

**Safety Guards**:
- Nur Workspaces mit Naming-Pattern `*_Feat_*` und passendem Domain/Feature-Namen
- Prod-Workspaces sind explizit ausgeschlossen

---

## Sandbox je Lauf (`sandbox.py`, AP-2)

Ein Workspace je Tenant-Lauf der agentischen Schleife (`UMSETZUNGSPLAN_AGENTIC_LOOP.md`),
angelegt, bespielt und wieder gelöscht. `sandbox.py` nutzt `AuthProvider`,
`FabricApiClient` und `WorkspaceManager` aus diesem Modul und `release_to_workspace` aus
`products/fabric/powerbi/deployment/scripts/fabric_release.py`; eigene Fabric-Aufrufe hat es
nicht.

```bash
python products/fabric/orchestrator/sandbox.py up     --manifest run.json --run-id run-0001 --capacity-id <id> --apply
python products/fabric/orchestrator/sandbox.py deploy --manifest run.json --pbip-dir <PBIP-Ordner> --apply
python products/fabric/orchestrator/sandbox.py down   --manifest run.json --apply
```

Ohne `--apply` ist jeder Befehl ein Trockenlauf. Der Workspace heißt `zz-aluca-sandbox-<run-id>`,
seine ID steht im Manifest. Vor jeder Schreibung wird er zurückgelesen; weichen ID oder Name ab,
bricht der Befehl ab. `down` gilt erst mit anschließendem 404 als erledigt. Ein gelöschter
Workspace bleibt für die Aufbewahrungsfrist durch Admins wiederherstellbar.

## Authentifizierung

Das Tool verwendet ausschließlich **Service Principal (SPN) Authentication** via `msal`.

```python
from msal import ConfidentialClientApplication

app = ConfidentialClientApplication(
    client_id=os.environ["FABRIC_CLIENT_ID"],
    client_credential=os.environ["FABRIC_CLIENT_SECRET"],
    authority=f"https://login.microsoftonline.com/{tenant_id}"
)
token = app.acquire_token_for_client(scopes=["https://api.fabric.microsoft.com/.default"])
```

**Validierung**: Das Tool prüft beim Start, ob der SPN Admin-Rechte auf den Ziel-Kapazitäten hat.

---

## Error Handling (429 Retry)

Quelle: Microsoft Learn `rest/api/fabric/articles/throttling` (gelesen 30.09.2026). Fabric
antwortet mit 429 aus zwei Gründen, unterschieden am `errorCode` im Antwortkörper; der
Orchestrator (`retry_delay` in `orchestrator.py`) behandelt sie getrennt:

| `errorCode` | Ursache | Verhalten |
|---|---|---|
| `RequestBlocked` | Quote der aufrufenden Identität erschöpft | genau `Retry-After` warten (Sekunden oder HTTP-Datum); liegt der Wert über `retry.max_retry_after`, bricht der Aufruf ab statt zu schlafen |
| `CapacityLimitExceeded` | Fabric-Kapazität überlastet, unabhängig von der Aufrufrate | exponentieller Backoff ab `retry.capacity_initial_delay`, gedeckelt bei `retry.capacity_max_delay`, mit Jitter (mindestens die halbe Stufe, nie sofort); ein längeres `Retry-After` gewinnt. Nach dem letzten Versuch nennt die Fehlermeldung die Ursache: Capacity Metrics App prüfen, skalieren |
| anderer 429 / 500, 502, 503, 504 | vorübergehend | `Retry-After`, falls gesendet, sonst `initial_delay * backoff_multiplier^n` |

Maximal `retry.max_retries` Wiederholungen (Standard 3). Tests mit gemockten 429 beider Arten:
`tests/test_throttling.py`.

### API-Quote je Identität: getrennte Dienstprinzipale

Die Unified Quota gilt je Identität (User, SPN, Managed Identity): 500 Aufrufe/min für
Platform-APIs, 200/min für Job-Scheduler-APIs, 500/min für Long-Running Operations, in einem
festen 60-s-Fenster ohne anteilige Erholung. API-spezifische Limits gelten zusätzlich. Teilen
sich Deploy, Monitoring und Agenten einen SPN, bremst ein Monitoring-Burst den Deploy aus.
Deshalb je Zweck eine eigene Identität:

| Zweck | Identität | Wo gesetzt |
|---|---|---|
| Provisionierung (dieser Orchestrator) | eigener SPN | `FABRIC_CLIENT_ID`/`FABRIC_CLIENT_SECRET` in der Umgebung des Orchestrator-Laufs |
| Deploy (`deployment/scripts/fabric_release.py`, fabric-cicd) | eigener SPN | `--client_id`/`--client_secret` bzw. `TENANT_ID`/`CLIENT_ID`/`CLIENT_SECRET` der Release-Pipeline |
| Monitoring, Agenten | je ein eigener SPN oder eine Managed Identity | in der jeweiligen Laufumgebung |

Die Trennung ist eine Konfigurationsfrage der Laufumgebungen; der Code liest die Identität je
Prozess aus der Umgebung. Die Rollen der Identitäten im Blueprint pflegt Meridian.

## API-Call-Übersicht (für CI/CD Transparenz)

### Git-Sync (explizit kommentiert im Code)

```python
# API CALL: Workspace Git Connect
POST /v1/workspaces/{workspaceId}/git/connect
{
  "gitProviderDetails": {
    "organizationName": "...",
    "projectName": "...",
    "repositoryName": "...",
    "branchName": "dev",
    "directoryName": "domains/Sales/Src"
  }
}
```

### Deployment Pipelines (explizit kommentiert im Code)

```python
# API CALL: Create Deployment Pipeline
POST /v1/deploymentPipelines
{
  "displayName": "Sales_Pipeline",
  "description": "Medallion pipeline for Sales domain"
}

# API CALL: Assign Workspace to Stage
POST /v1/deploymentPipelines/{pipelineId}/stages/{stageId}/assignWorkspace
{
  "workspaceId": "..."
}

# API CALL: Deploy (Promote)
POST /v1/deploymentPipelines/{pipelineId}/deploy
{
  "sourceStageOrder": 0,  # DEV
  "targetStageOrder": 1   # TEST
}
```

---

## Transformation & Templates

### Spark Notebook (PySpark) Template

Generiert für Src-Layer:

```python
# Bronze: Raw ingestion
spark.read.format("delta").load("/bronze/sales/transactions").write.mode("overwrite").save("/silver/sales/transactions_cleaned")
```

### dbt-fabric Template

Generiert für Trf-Layer:

```yaml
# profiles.yml
fabric:
  target: dev
  outputs:
    dev:
      type: fabric
      server: ...
      database: Sales_Trf_Dev
```

```sql
-- models/gold/fact_sales.sql
SELECT * FROM silver.transactions_cleaned
```

---

## Troubleshooting

### Fehler: "SPN has no access to capacity"

**Lösung**: Fügen Sie den SPN als Capacity Admin hinzu (OneLake catalog → Govern → Capacities → die Kapazität → More options → Settings → Capacity admins; Fallback: Settings (Zahnrad) → Admin portal → Capacity settings, z. B. bei Private Link — Learn [Manage your capacities in the OneLake catalog](https://learn.microsoft.com/fabric/governance/onelake-catalog-capacities), gelesen 01.10.2026).

### Fehler: "Git provider details missing"

**Lösung**: Prüfen Sie `config.yaml` → `git_provider` (repo_url, organization, branches).

### Fehler: "Sensitivity label not found"

**Lösung**: Labels müssen im Tenant existieren (Microsoft Purview). Im Modus `admin_api` Label-IDs (GUID) statt Namen in `config.yaml`. `admin_api` ruft Fabric `POST /v1/admin/items/bulkSetLabels` (alle Fabric-Item-Typen, 2.000 Items je Aufruf, 25 Aufrufe je Stunde); der Endpunkt unterstützt laut Learn (gelesen 01.10.2026) keinen Dienstprinzipal — der SPN-Orchestrator setzt dort nichts, sondern meldet einen manuellen Schritt. Default ist `purview_policy`. Eine Benutzer-Anmeldung im Orchestrator wird nicht gebaut (Entscheidung 01.10.2026: manueller Schritt plus Purview). Der manuelle Schritt enthält alles für einen Fabric-Admin: Endpunkt `POST https://api.fabric.microsoft.com/v1/admin/items/bulkSetLabels`, den fertigen JSON-Body (`items` mit `{id, type}`, `labelId`, `assignmentMethod`, optional `delegatedPrincipal` vom Typ `User`), Anmeldung nur als Benutzer mit der Rolle Fabric Administrator und Scope `Tenant.ReadWrite.All`, die Grenzen (25 Aufrufe je Stunde, 2.000 Items je Aufruf) und die Erfolgsregel: erledigt erst, wenn jedes Item in `itemsChangeLabelStatus` `Succeeded` meldet. Ein Token steht nie im Schritt.

---

## Vergleich V1 vs V2

| Feature | V1 (`products/fabric/powerbi/deployment/`) | V2 (dieses Tool) |
|---------|---------------------------------------------|-------------------|
| Workspace-Strategie | Funktional (DE_/DM_/BI_) | Domain+Medallion (Src/Trf/Anl) |
| Auth | Fabric CLI + `azure-identity` | `msal` SPN-only |
| APIs | Fabric CLI Wrapper | `requests` REST direkt |
| Deployment | Git→Workspace (`fabric-cicd`) | Deployment Pipelines API |
| Governance | Manuell | Automated (Sensitivity, Endorsement) |
| OneLake Shortcuts | Dokumentation | API-Provisionierung |
| Feature Isolation | Optional Feature-Workspace | Integriert + Auto-Cleanup |

---

## Security Notes

- **Secrets**: Nie in Git; nur ENV oder Azure Key Vault.
- **SPN Scope**: Minimale Rechte (Capacity Admin statt Tenant Admin, wenn möglich).
- **Audit**: Alle API-Calls werden strukturiert geloggt (JSON-Format für SIEM).
- **Idempotenz**: Tool ist re-runnable; keine Duplikate, keine Daten-Löschung ohne Guard.

---

## Lizenz

Dieses Tool ist Teil von ALUCA (Analytics Library of Use Cases). Siehe root README für Lizenzdetails.

---

## Referenzen

- [Microsoft Fabric REST API](https://learn.microsoft.com/en-us/rest/api/fabric/articles/using-fabric-apis)
- [Deployment Pipelines API](https://learn.microsoft.com/en-us/fabric/cicd/deployment-pipelines/pipeline-automation-fabric)
- [Git Integration API](https://learn.microsoft.com/en-us/fabric/cicd/git-integration/git-integration-process)
- [Microsoft Well-Architected Framework (Analytics)](https://learn.microsoft.com/en-us/azure/architecture/framework/)
- [FabCon Europe 2025 – Git Best Practices](https://github.com/peerinsights/FabricAutomation)
