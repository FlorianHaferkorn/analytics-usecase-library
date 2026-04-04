# Gap-Analyse: PBI Generator vs. microsoft/skills-for-fabric

**Stand:** 2026-04-04  
**Branch:** `claude/pbi-generator-gap-analysis-MrchA`  
**Quelle:** https://github.com/microsoft/skills-for-fabric

---

## Kontext

Diese Analyse vergleicht unseren **PBI Generator** (Phase-basierter PBIP-Orchestrator in `products/fabric/powerbi/`) mit dem offiziellen Microsoft-Repository `skills-for-fabric`. Ziel ist es, konkrete Verbesserungen zu identifizieren, die unsere KI-Agenten präziser, robuster und vollständiger machen.

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

## Abgrenzung: Was wir bewusst NICHT übernehmen

| Aspekt | Begründung |
|---|---|
| `check-updates` Session-Check | Wir haben kein verteiltes Skills-Paket — Agents laufen im Repo-Kontext |
| `spark-authoring-cli`, `sqldw-authoring-cli` | Außerhalb unseres PBI-Generator-Scopes |
| `e2e-medallion-architecture` Skill | Wir haben eigenen Orchestrator mit Domain-DDM-Architektur |
| `generate_skill_catalog.py` | Wir nutzen Knowledge Graph + Registry statt statischem Katalog |
