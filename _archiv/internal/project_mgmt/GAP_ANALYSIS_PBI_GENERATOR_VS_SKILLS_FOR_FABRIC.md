# Gap-Analyse: PBI Generator & Fabric Architecture Generator vs. microsoft/skills-for-fabric

**Stand:** 2026-04-04  
**Branch:** `claude/pbi-generator-gap-analysis-MrchA`  
**Quelle:** <https://github.com/microsoft/skills-for-fabric>

---

## Kontext

Diese Analyse umfasst **zwei Tools**:

| Tool | Pfad | Zweck |
|---|---|---|
| **PBI Generator** | `products/fabric/powerbi/orchestrator/` | Code-Generierung: TMDL, PBIP, Reports aus UseCase Brackets |
| **Fabric Architecture Generator** | `products/fabric/orchestrator/orchestrator.py` | Infrastruktur-Provisioning: Workspaces, Deployment Pipelines, Git |

Beide werden mit dem Microsoft `skills-for-fabric`-Repository (v0.2.6) verglichen.

---

## Was wir bereits gut machen

Bevor die Lücken beschrieben werden, eine ehrliche Einschätzung unserer Stärken gegenüber `skills-for-fabric`:

| Unser Vorteil | Beschreibung |
|---|---|
| **Domain-Driven Governance** | KPI Catalog + UseCase Bracket + Business Factsheets = klare SSOT-Kette |
| **Phase-Orchestrator** | 7-Phasen-Pipeline (Registry → Measures → Tables → Relationships → Reports → Themes → Validation) |
| **Grid-basiertes Layout** | Master Grid 12×12 mit Pixel-präziser Positionierung via `grid_calculator.py` |
| **Delta-Mode** | Reports werden inkrementell aktualisiert, kein Full-Overwrite |
| **JSON-Schemas** | 13 governte Schemas in `tooling/ai/schemas/` |
| **Knowledge Graph** | `graph.json` verknüpft KPI → Measure → Column → Visual |
| **PostToolUse-Hooks** | Automatische TMDL/PBIP-Validierung nach jedem Write/Edit |
| **Visual Templates** | Fertige JSON-Templates für KPI Cards, Matrix, Slicer, Smart Narrative |
| **Action Codes** | Vollständige Governance-Kette bis zur Empfehlungslogik |

`skills-for-fabric` hat keine dieser Domain-spezifischen Konzepte — es ist eine generische Skill-Library für beliebige Fabric-Nutzer.

---

## Gap-Analyse: Wo `skills-for-fabric` besser oder anders ist

### GAP 1 — TMDL-Syntax: Fehlende fortgeschrittene Features

**Status:** Kritisch  
**Unser Stand:** `TMDL_Allowed_Subset.md` deckt Basistabellen, Measures, Columns, Relationships ab — aber in JSON-Beispiel-Format, nicht in echtem TMDL-Text-Format.  
**Skills-for-fabric:** `tmdl-authoring-guide.md` + `tmdl-advanced-features-guide.md` dokumentieren vollständig:

| Feature | In unserem TMDL Subset? | In skills-for-fabric? |
|---|---|---|
| Calculation Groups (Zeit-Intelligenz YTD, LY, etc.) | ❌ | ✅ vollständig |
| Security Roles / RLS (TMDL-Syntax) | Nur Policy-Referenz | ✅ vollständig mit OLS |
| Perspectives | ❌ | ✅ |
| Translations / Cultures (Lokalisierung) | ❌ | ✅ |
| User-defined DAX Functions | ❌ | ✅ |
| Calendar Objects (Auto Date/Time) | ❌ | ✅ |
| Direct Lake Entity Partition (vollständige Syntax) | Partial | ✅ mit `expressionSource` |
| `database.tmdl` Pflichtinhalt | ❌ | ✅ mit `compatibilityLevel: 1702` |
| `model.tmdl` mit `defaultPowerBIDataSourceVersion` | ❌ | ✅ (`powerBI_V3` kritisch für Import) |
| Multi-line DAX in Triple-Backticks | Erwähnt | ✅ mit Beispielen |
| `///` Descriptions vs. `description:` | ✅ als Rule | ✅ als Rule + Beispiele |

**Konsequenz:** Unser Measure-Generator erzeugt ggf. ungültige TMDL-Dateien bei komplexeren Features (Calculation Groups, Direct Lake mit Entity Source).

---

### GAP 2 — Direct Lake Semantic Model: Vollständiges Generierungsmuster

**Status:** Hoch  
**Unser Stand:** Unser Generator erstellt Import-Mode-Tabellen. Direct Lake wird in Kommentaren erwähnt aber das vollständige Deployment-Pattern fehlt.  
**Skills-for-fabric:** Explizites End-to-End-Muster:

```tmdl
// 1. Named Expression für Lakehouse-Referenz
expression DL_Lakehouse =
    let
        Source = AzureStorage.DataLake("https://onelake.dfs.fabric.microsoft.com/<WsId>/<LhId>", ...)
    in Source

// 2. Entity Partition pro Tabelle
partition Sales = entity
    mode: directLake
    source
        entityName: Sales
        schemaName: dbo
        expressionSource: DL_Lakehouse
```

Plus: SQL-Endpoint-Discovery-Flow (Lakehouse provisioning → `connectionString` abwarten → Semantic Model referenzieren).

**Konsequenz:** Unser Generator kann keine Direct Lake Modelle automatisch aus Data Contracts generieren.

---

### GAP 3 — REST-API-First Deployment (az rest Muster)

**Status:** Hoch  
**Unser Stand:** Wir nutzen `fab` CLI für alle Fabric-Operationen. Das ist komfortabel aber nicht portierbar (benötigt `fab` install).  
**Skills-for-fabric:** Vollständige `az rest`-Patterns direkt gegen die Fabric REST API:

| Aspekt | Unser Ansatz | skills-for-fabric |
|---|---|---|
| Tool | `fab` CLI Wrapper | `az rest` + `jq` |
| Auth | `fab auth login` | `az login` + explizite `--resource` Audience |
| API-Audience-Trennung | Implizit via `fab` | Explizit: Fabric API vs. Power BI Datasets API |
| LRO-Polling | `fab` handled intern | Explizit: `202 Accepted` → `Operation-Id` → Poll |
| JMESPath-Filtering | Nicht dokumentiert | Explizit für Workspace/Item-Discovery |
| Semantic Model Deploy | `fab import ...` | `createItemWithDefinition` mit base64 TMDL |
| Report Deploy via REST | Nicht dokumentiert | `createItemWithDefinition` mit PBIR-Parts |

**Konsequenz:** Unsere Agents wissen nicht, wie sie Semantic Models und Reports direkt via REST API deployen. Sie sind `fab`-abhängig. Fehlt `fab`, ist keine Deployment-Automation möglich.

---

### GAP 4 — Report-Deployment via REST (PBIR createItemWithDefinition)

**Status:** Hoch  
**Unser Stand:** Wir schreiben PBIP-Dateien lokal auf dem Filesystem. Deployment via `fab import`. Kein dokumentierter REST-Pfad.  
**Skills-for-fabric:** `ITEM-DEFINITIONS-CORE.md` dokumentiert vollständig:

- `definition/report.json` → Report-level settings
- `definition/pages/pages.json` → Page listing
- `definition/pages/<pageId>/page.json` → Per-page layout
- `definition/pages/<pageId>/visuals/<visualId>/visual.json` → Per-visual config
- `definition.pbir` → Semantic Model Reference (nur `byConnection`, nicht `byPath` via REST API!)

Kritischer Hinweis: **Fabric REST API unterstützt nur `byConnection`-Referenzen** in `definition.pbir`, nicht `byPath`. Unsere aktuell generierten Reports nutzen `byPath` (relativer Pfad zum `.SemanticModel`-Ordner). Das funktioniert lokal via Desktop/PBIP aber **nicht** via REST-Deploy.

---

### GAP 5 — Consumption/Discovery Pattern für bestehende Modelle

**Status:** Mittel  
**Unser Stand:** Kein dokumentiertes Pattern für das Erkunden/Abfragen bestehender deployed Semantic Models.  
**Skills-for-fabric:** `powerbi-consumption-cli` SKILL mit komplettem Discovery-Workflow:

```
Empfohlene Reihenfolge:
1. Scope Estimation (Tabellen-/Measures-Anzahl schätzen)
2. INFO.VIEW.TABLES() → schnelle Tabellen-Übersicht
3. INFO.VIEW.COLUMNS() + INFO.VIEW.MEASURES() → Details
4. INFO.VIEW.RELATIONSHIPS() → Join-Validierung
5. INFO.DEPENDENCIES() → DAX-Abhängigkeitsgraph
```

Vollständiger `INFO.VIEW.*` vs. `INFO.*` Katalog mit 30+ Funktionen. Narrowing-Pattern: `SELECTCOLUMNS` + `FILTER` statt unbegrenzte Abfragen.

**Konsequenz:** Unsere Agents können keine bestehenden deployed Modelle in Fabric erkunden. Das fehlt z.B. für Impact Analysis (welche Reports nutzen Measure X?).

---

### GAP 6 — Skill-Format-Standardisierung (YAML Frontmatter + Must/Prefer/Avoid)

**Status:** Mittel  
**Unser Stand:** Unsere Skill-Docs in `.cursor/rules/`, `docs/agent/` und `.github/copilot-instructions.md` haben kein einheitliches Format.  
**Skills-for-fabric:** Jeder Skill hat ein standardisiertes Format:

```yaml
---
name: powerbi-authoring-cli
description: >
  Action-Verb-Beschreibung. Use when: (1)..., (2)...
  Triggers: "phrase1", "phrase2"
---

## Must/Prefer/Avoid
### MUST DO
### PREFER  
### AVOID
```

Vorteile dieses Formats:
- **Routing**: KI-Agents können anhand von `description` + `Triggers` automatisch den richtigen Skill wählen
- **Guardrails**: Must/Prefer/Avoid verhindert häufige Fehler explizit
- **Tokeneffizienz**: <15.000 Token per Skill (Quality Requirement)
- **Agentic Workflow**: Expliziter Schritt-für-Schritt-Abschnitt für Automation

**Konsequenz:** Unsere Skill-Docs sind schwerer maschinenlesbar; Routing-Präzision von Agents leidet.

---

### GAP 7 — Agenten-Persona-Design mit Delegation

**Status:** Mittel  
**Unser Stand:** Unsere Agenten-Prompts (z.B. `Commercial_Sales_Agent_COM-002.system_prompt.md`) definieren Verhalten, aber keine Delegation zu spezialisierten Skills.  
**Skills-for-fabric:** `FabricDataEngineer.agent.md` zeigt:

```yaml
delegates_to:
  - powerbi-authoring-cli
  - powerbi-consumption-cli
  - spark-authoring-cli
  ...
```

Mit expliziten **Delegations-Regeln**: "Route KQL/Eventhouse queries to eventhouse-consumption-cli; route KQL schema/ingestion to eventhouse-authoring-cli."

Plus **Persönlichkeitsbeschreibung** ("methodical, detail-oriented", "uses analogies") die das Verhalten steuert ohne es zu zwingen.

**Konsequenz:** Unser `router-agent` macht implizites Routing; fehlerhafte Delegation ist schwerer zu debuggen.

---

### GAP 8 — Security Model Dokumentation

**Status:** Mittel  
**Unser Stand:** `TMDL_Allowed_Subset.md` erwähnt "RLS/OLS only on dimensions" als Policy, aber kein TMDL-Syntax-Beispiel.  
**Skills-for-fabric:** `tmdl-advanced-features-guide.md` mit vollständiger RLS/OLS-Syntax:

```tmdl
role 'Sales Region Manager'
    modelPermission: read

    tablePermission Sales
        filterExpression: 'Sales'[RegionCode] = USERNAME()

    tablePermission 'Product'[CostPrice]
        metadataPermission: none
```

Plus: **Role Membership via REST API** (nicht via DAX INFO.ROLEMEMBERSHIPS() — das ist unreliable):
```bash
POST /v1/workspaces/{wsId}/datasets/{datasetId}/users
{ "principalType": "User", "identifier": "user@org.com", "datasetUserAccessRight": "ReadRls" }
```

---

### GAP 9 — Prompt Security Scanning

**Status:** Niedrig  
**Unser Stand:** TMDL/PBIP-Validierung via Hooks, aber kein Prompt-Injection-Scanning.  
**Skills-for-fabric:** `.github/scripts/scan_prompt_security.py` scannt automatisch alle Skill-Dateien auf:
- Hartcodierte Secrets
- Prompt-Injection-Muster
- Ungültige URLs in Instructions

**Konsequenz:** AI-generierte Inhalte (Skill-Prompts, Faktenbogen) könnten unbemerkt Injection-Muster enthalten.

---

### GAP 10 — Update/Versions-Management für Skills

**Status:** Niedrig  
**Unser Stand:** Keine Versionierung unserer Skill-Dateien.  
**Skills-for-fabric:** 
- `package.json` mit semantischer Versionierung
- `check-updates` Skill prüft am Anfang jeder Session ob eine neue Version verfügbar ist
- `generate_changelog.py` erzeugt automatisch CHANGELOG.md
- Jeder Skill hat eine Update-Check-Pflichtnotiz

---

### GAP 11 — MCP-Server-Routing für Fine-Grained Modell-Änderungen

**Status:** Niedrig  
**Unser Stand:** Alle TMDL-Änderungen gehen durch File-System-Edits. Kein Unterschied zwischen großen (Full-Definition) und kleinen Änderungen.  
**Skills-for-fabric:** Explizites Routing:
- **Große Änderungen** (neues Modell, Tabellen hinzufügen) → `az rest createItemWithDefinition`
- **Kleine Änderungen** (einzelne Measure, Spalte) → `powerbi-modeling-mcp` (MCP Server)
- **Lesen/Erkunden** → `powerbi-consumption-cli` (DAX INFO.VIEW.*)

**Konsequenz:** Unser Generator macht immer Full-Definition-Roundtrips auch für kleine Änderungen (ineffizient bei großen Modellen).

---

## Zusammenfassung nach Priorität

| # | Gap | Priorität | Aufwand | Auswirkung |
|---|---|---|---|---|
| 1 | TMDL Advanced Features (Calc Groups, RLS, Direct Lake) | Kritisch | M | Korrekte TMDL-Generierung |
| 2 | Direct Lake vollständiges Generierungsmuster | Hoch | M | Fabric-native Modelle |
| 3 | REST-API-First Deployment (`az rest` Patterns) | Hoch | L | Portabilität ohne `fab` |
| 4 | Report-Deploy via REST (PBIR `byConnection`) | Hoch | M | Cloud-Native Deployment |
| 5 | Consumption/Discovery (INFO.VIEW.* Pattern) | Mittel | S | Impact-Analyse, Debugging |
| 6 | Skill-Format-Standardisierung (YAML + Must/Prefer/Avoid) | Mittel | M | Routing-Präzision |
| 7 | Agenten-Delegation & Personas | Mittel | S | Debugging, Transparenz |
| 8 | Security Roles / RLS in TMDL | Mittel | S | Governance-Vollständigkeit |
| 9 | Prompt Security Scanning | Niedrig | S | Sicherheit |
| 10 | Update/Versions-Management | Niedrig | S | Wartbarkeit |
| 11 | MCP-Routing für fine-grained Änderungen | Niedrig | L | Performance |

---

## Abgrenzung: Was wir bewusst NICHT übernehmen (PBI Generator)

| Aspekt | Begründung |
|---|---|
| `check-updates` Session-Check | Wir haben kein verteiltes Skills-Paket — Agents laufen im Repo-Kontext |
| `spark-authoring-cli`, `sqldw-authoring-cli` | Außerhalb unseres PBI-Generator-Scopes |
| `e2e-medallion-architecture` Skill | Wir haben eigenen Orchestrator mit Domain-DDM-Architektur |
| `generate_skill_catalog.py` | Wir nutzen Knowledge Graph + Registry statt statischem Katalog |

---

---

## Teil 2: Fabric Architecture Generator (`orchestrator.py`) — Gap-Analyse

### Kurzbeschreibung des Generators

`products/fabric/orchestrator/orchestrator.py` (v2.0, ~1.400 Zeilen Python) ist ein **reines Infrastruktur-Provisioning-Tool**:

- Erstellt Workspace-Matrizen (Enterprise: 9 / Compact: 3 Workspaces pro Domain)
- Konfiguriert Git-Integration (GitHub / Azure DevOps) pro Workspace
- Erstellt Deployment Pipelines (DEV→TEST→PROD) mit automatischer Stage-Zuweisung
- Wendet Governance an (Sensitivity Labels, Endorsement)
- Erstellt Feature-Workspaces für Branch-Isolation
- **Erstellt keine Items** (Lakehouse, Warehouse, Notebooks, Pipelines, Semantic Models, Reports)

**Auth:** SPN über MSAL (kein `fab`, kein `az` nötig — reines `requests` + `msal`).  
**API:** Direkt gegen `https://api.fabric.microsoft.com/v1` — kein CLI-Wrapper.

---

### Wo der Architecture Generator von skills-for-fabric profitieren würde

#### ARCH-GAP 1 — Item-Provisioning fehlt komplett

**Status:** Hoch  
**Unser Stand:** Der Generator erstellt nur Workspaces. Nach der Provisioning-Phase müssen Benutzer manuell (oder via separatem CI/CD) erstellen:
- Lakehouses im Src-Layer
- Warehouses im Trf-Layer  
- Notebooks für Bronze→Silver→Gold Transformationen
- DataPipelines für Orchestrierung
- OneLake Shortcuts zwischen Layern

**Skills-for-fabric bietet dafür:**
- `spark-authoring-cli`: Lakehouse-Erstellung, Notebook-Deployment via `createItemWithDefinition` mit `.ipynb` Base64
- `ITEM-DEFINITIONS-CORE.md`: Vollständige Item-Typen (Lakehouse, DataPipeline, SparkJobDefinition, etc.)
- `COMMON-CLI.md § OneLake Shortcuts`: Create/List/Delete Shortcut Patterns

**Konkrete Ergänzung:** `orchestrator.py` sollte nach Workspace-Provisioning optional Lakehouse + Warehouse Items erstellen können — via `POST /v1/workspaces/{id}/items` mit `{"type": "Lakehouse", "displayName": "..."}`. Das Pattern ist vollständig in `ITEM-DEFINITIONS-CORE.md` dokumentiert.

---

#### ARCH-GAP 2 — OneLake Shortcuts: Config ohne Ausführung

**Status:** Hoch  
**Unser Stand:** `config.yaml.example` zeigt `onelake_shortcuts` Konfiguration, aber `orchestrator.py` erstellt keine Shortcuts. Der Code-Kommentar sagt "configuration shown but **not explicitly created** by tool".

**Skills-for-fabric:**

```bash
# Shortcut Create via az rest
az rest --method post \
  --resource "https://api.fabric.microsoft.com" \
  --url "https://api.fabric.microsoft.com/v1/workspaces/{wsId}/items/{itemId}/shortcuts" \
  --body '{
    "name": "silver_sales",
    "path": "/Tables",
    "target": {
      "type": "OneLake",
      "oneLake": {
        "path": "Tables/sales",
        "itemId": "{srcLakehouseId}",
        "workspaceId": "{srcWorkspaceId}"
      }
    }
  }'
```

**Konsequenz:** Das "Zero-Copy" Konzept Src→Trf kann nicht automatisiert werden.

---

#### ARCH-GAP 3 — Notebook-Deployment nach Workspace-Provisioning

**Status:** Mittel  
**Unser Stand:** `TemplateGenerator` generiert PySpark-Notebook-Templates (Bronze/Silver-Ingestion + dbt-Skeleton) als **lokale Dateien**, deployt sie aber nicht in Fabric.

**Skills-for-fabric `spark-authoring-cli`:** Vollständiges Notebook-Deployment via REST:

```bash
# Notebook als base64-encoded .ipynb deployen
PAYLOAD=$(python3 -c "
import base64, json
nb = json.load(open('bronze_ingestion.ipynb'))
nb['metadata']['dependencies'] = {
  'lakehouse': {
    'default_lakehouse': '$LAKEHOUSE_ID',
    'default_lakehouse_name': 'src_lakehouse',
    'default_lakehouse_workspace_id': '$WS_ID'
  }
}
print(base64.b64encode(json.dumps(nb).encode()).decode())
")
```

Kritische `skills-for-fabric`-Erkenntnisse die uns betreffen:
- Jede Code-Cell braucht `"outputs": []` und `"execution_count": null` — sonst stilles Deployment-Versagen
- Lakehouse-Binding muss in `metadata.dependencies.lakehouse` im `.ipynb` selbst stehen
- `updateDefinition` LRO: Poll-URL ohne `/result` (anders als `getDefinition`)

---

#### ARCH-GAP 4 — Deployment Pipeline: Keine `allowCreateArtifact` Option

**Status:** Mittel  
**Unser Stand:** `PipelineManager.deploy()` sendet einen Deployment-Request, aber ohne `allowCreateArtifact`-Option.

**Skills-for-fabric:** Explizite Option für das erste Deployment:

```json
{
  "sourceStageOrder": 0,
  "isBackwardDeployment": false,
  "options": {
    "allowCreateArtifact": true,
    "allowOverwriteArtifact": true
  }
}
```

Ohne `allowCreateArtifact: true` schlägt das erste Deployment (DEV→TEST) fehl, weil TEST noch keine Items hat.

---

#### ARCH-GAP 5 — Fehlende Idempotenz für Items

**Status:** Mittel  
**Unser Stand:** Workspaces werden idempotent erstellt (find-before-create). Items werden nicht erstellt — somit auch keine Item-Idempotenz nötig. Sobald Item-Provisioning ergänzt wird (ARCH-GAP 1), muss auch Idempotenz implementiert werden.

**Skills-for-fabric Pattern:** `GET /v1/workspaces/{id}/items?type={type}` + JMESPath-Filter nach `displayName` → create nur wenn nicht vorhanden.

---

#### ARCH-GAP 6 — Governance: `workspaces/{id}/governanceLabels` ist non-standard

**Status:** Niedrig  
**Unser Stand:** `GovernanceManager.apply_sensitivity_label()` nutzt `POST /v1/workspaces/{id}/governanceLabels`. Dieser Endpoint ist nicht in `skills-for-fabric` dokumentiert — er gehört zur **Information Protection API** (Microsoft Purview), nicht zur Standard-Fabric-API.

**Risiko:** Dieser Endpoint könnte sich ändern oder Purview-Lizenz benötigen. Skills-for-fabric umgeht Governance-Labels bewusst (außerhalb ihres Scope).

---

### Was der Architecture Generator bereits besser macht als skills-for-fabric abdeckt

| Stärke | Beschreibung |
|---|---|
| **Workspace-Matrix** | 9-Workspace Enterprise-Muster; skills-for-fabric kennt kein Schema-Provisioning |
| **Git-Integration** | Workspace→Branch-Verbindung; skills-for-fabric hat kein `git connect` Pattern |
| **Feature-Isolation** | Naming-Pattern + Safe-Cleanup; skills-for-fabric nur für single-workspace |
| **Multi-Domain Config** | `config.yaml` mit N Domains; skills-for-fabric ist single-workspace-focused |
| **SPN via MSAL (kein az)** | Kein Azure CLI nötig; portabler als `az login` Flows |
| **Retry/Backoff** | Explizit implementiert mit `Retry-After`; skills-for-fabric delegiert das an az CLI |

---

### Zusammenfassung: Architecture Generator Gaps nach Priorität

| # | Gap | Priorität | Aufwand |
|---|---|---|---|
| ARCH-1 | Item-Provisioning (Lakehouse, Warehouse, Shortcut) nach Workspace | Hoch | L |
| ARCH-2 | OneLake Shortcut-Erstellung implementieren | Hoch | M |
| ARCH-3 | Notebook-Deployment in Fabric nach Template-Generierung | Mittel | M |
| ARCH-4 | `allowCreateArtifact` in Deployment-Pipeline-Deploy | Mittel | S |
| ARCH-5 | Item-Idempotenz (find-before-create für Items) | Mittel | S |
| ARCH-6 | Governance-Label-Endpoint absichern (Purview-Abhängigkeit) | Niedrig | S |

---

---

## Teil 3: Flexibilität & Zukunftssicherheit

### Was sich bei Microsoft ändern kann — und wie es uns trifft

#### A) Fabric REST API Endpunkte

| Änderungsrisiko | Betrifft | Auswirkung |
|---|---|---|
| `/v1/` → `/v2/` API-Versioning | Beide Tools | Breaking Change in allen API-Calls |
| Neue Item-Typen (z.B. `VariableLibrary`) | Architecture Generator | ARCH-GAP 1 wird größer |
| LRO-Verhalten ändert sich | Beide Tools | Polling-Logik muss angepasst werden |
| `getDefinition` `/result`-Suffix entfällt | PBI Generator (REST-Deploy) | Silent Failure beim Polling |
| `definition.pbism` Version erhöht (4.2 → 5.x) | PBI Generator | Generator erzeugt veraltete Dateien |

**Unser Risiko (Architecture Generator):** Gering — reine REST-Calls, kein CLI-Wrapper. Endpunkt-Änderungen sind an einer Stelle (FabricApiClient) zu fixen.

**Unser Risiko (PBI Generator):** Mittel — mehrere Stellen betroffen: `pbip_writer.py`, `fab import` Commands, PowerShell-Orchestrator.

**skills-for-fabric Risiko:** Gering — REST-first, modularer Aufbau. Microsoft pflegt die Skills selbst.

---

#### B) TMDL-Spezifikation

| Änderungsrisiko | Betrifft | Wahrscheinlichkeit |
|---|---|---|
| Neue TMDL-Features (z.B. Composite Models) | PBI Generator TMDL-Generierung | Hoch |
| `compatibilityLevel` erhöht (1702 → 1800+) | `database.tmdl` in Generator | Mittel |
| `defaultPowerBIDataSourceVersion` neue Werte | `model.tmdl` Template | Mittel |
| `///` Description-Syntax geändert | Alle TMDL-Generatoren | Niedrig |
| DAX-Syntax-Änderungen | Measure-Generator | Niedrig |

**Unser PBI Generator:** Spröde — TMDL-Templates sind in `measure_ops.ps1` + `table_ops.ps1` hardcodiert. Kein zentrales Template-System.  
**skills-for-fabric:** Robuster — TMDL-Syntax ist in `tmdl-authoring-guide.md` konzentriert; Skills referenzieren es. Eine Änderung → eine Datei updaten.

**Empfehlung:** TMDL-Basistemplates (database.tmdl, model.tmdl) in eine zentrale Datei auslagern, die Generator + AI-Agent gemeinsam nutzen.

---

#### C) PBIR / Report-Format

| Änderungsrisiko | Betrifft | Wahrscheinlichkeit |
|---|---|---|
| PBIR-Legacy → PBIR Migration (Microsoft erzwingt) | PBI Generator (`pbip_writer.py`) | Hoch (bereits in Gange) |
| Visual JSON-Schema Änderungen | `visual_builder.py`, `page_builder.py` | Mittel |
| `definition.pbir` `byPath` wird deprecated | PBI Generator (REST-Deploy) | Mittel |
| Report-JSON-Schema-Versionen (3.1.0+) | Alle Report-Generatoren | Mittel |

**Unser Risiko:** Hoch — `pbip_writer.py` und `page_builder.py` haben ~1.500 Zeilen hardcodierter Visual-JSON-Strukturen. Eine PBIR-Schema-Änderung erfordert umfangreiche Anpassungen.

**Mitigation:** Microsoft veröffentlicht PBIR JSON Schemas unter `developer.microsoft.com/json-schemas/fabric/item/report/` — diese könnten als Validierungsgrundlage in unsere Checks eingebunden werden.

---

#### D) `fab` CLI (nur PBI Generator)

| Änderungsrisiko | Betrifft | Wahrscheinlichkeit |
|---|---|---|
| `fab` CLI wird deprecated | `orchestrate_full_model.ps1`, Deploy-Scripts | Mittel |
| `fab import` Argumente ändern sich | Alle Deploy-Schritte | Mittel |
| `fab auth` Flow ändert sich | Auth in PowerShell | Niedrig |

**Unser Risiko:** Hoch — `fab` ist ein Community-/Microsoft-Tool ohne GA-Garantie. Skills-for-fabric hat `fab` bewusst **nicht** verwendet und setzt auf `az rest` — das ist die stabilere Wahl.  
**Empfehlung:** `az rest` als Fallback-Deploy-Pfad parallel zu `fab` implementieren (deckt GAP 3).

---

#### E) Authentication / Token Audiences

| Änderungsrisiko | Betrifft | Wahrscheinlichkeit |
|---|---|---|
| Fabric API Audience ändert sich | Beide Tools | Sehr niedrig |
| Power BI Datasets API Audience ändert sich | PBI Generator (Refresh, Permissions) | Sehr niedrig |
| SPN-Anforderungen verschärft (MFA, Conditional Access) | Architecture Generator | Mittel |
| Managed Identity als Pflicht | Architecture Generator | Niedrig |

**Architecture Generator Risiko:** SPN-only Auth ist robust, solange Microsoft Service Principals für Fabric APIs erlaubt. Langfristig empfiehlt Microsoft Managed Identity.

---

### Flexibilitätsbewertung: Gesamtübersicht

| Dimension | PBI Generator | Architecture Generator | skills-for-fabric |
|---|---|---|---|
| **REST-API Stabilität** | ⚠️ Mittel (`fab`-Abhängigkeit) | ✅ Hoch (direkte REST-Calls) | ✅ Hoch |
| **TMDL-Änderungen** | ⚠️ Spröde (hardcodiert) | — (kein TMDL) | ✅ Zentral in einer Datei |
| **Report-Format-Änderungen** | ⚠️ Hoch (viel hardcodierter Visual-JSON) | — | ✅ Referenz-Docs anpassbar |
| **Auth-Stabilität** | ⚠️ Mittel (`fab auth`) | ✅ Hoch (MSAL direkt) | ✅ Hoch (`az login`) |
| **Neue Fabric Item-Typen** | — | ⚠️ Manuell nachpflegen | ✅ Skills erweiterbar |
| **Agent-Anpassbarkeit** | ⚠️ Prompts verteilt | — | ✅ Skill-Granularität |
| **Wartungsaufwand bei Updates** | Hoch | Mittel | Niedrig (Microsoft pflegt) |

**Fazit:** Der Architecture Generator ist durch seinen REST-first Ansatz bereits robuster als der PBI Generator. Der größte gemeinsame Risikofaktor ist die TMDL-Spezifikation und das PBIR-Format — beides liegt außerhalb unserer Kontrolle. Die Empfehlung aus `skills-for-fabric`: Syntax-Regeln in zentrale, AI-lesbare Referenz-Dokumente auslagern statt in Code hardcoden — dann reicht bei einer API-Änderung ein Dokument-Update.

---

## Abgrenzung: Was wir bewusst NICHT übernehmen (beide Tools)

| Aspekt | Begründung |
|---|---|
| `check-updates` Session-Check | Wir haben kein verteiltes Skills-Paket — Agents laufen im Repo-Kontext |
| `spark-authoring-cli`, `sqldw-authoring-cli` | Außerhalb unseres Scopes (wir generieren keine Spark/SQL-Notebooks) |
| `e2e-medallion-architecture` Skill | Wir haben eigenen Orchestrator mit Domain-DDM-Architektur |
| `generate_skill_catalog.py` | Wir nutzen Knowledge Graph + Registry statt statischem Katalog |
| `FabricAppDev` Agent | Python ODBC/XMLA-App-Entwicklung ist nicht unser Anwendungsfall |
| `VariableLibrary` Item-Type | Interessant für Notebook-Config, aber kein direkter PBI-Generator-Bezug |
