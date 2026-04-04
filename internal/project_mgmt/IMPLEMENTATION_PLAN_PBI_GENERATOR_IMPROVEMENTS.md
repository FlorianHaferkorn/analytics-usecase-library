# Implementierungsplan: PBI Generator Improvements

**Basis:** Gap-Analyse `GAP_ANALYSIS_PBI_GENERATOR_VS_SKILLS_FOR_FABRIC.md`  
**Stand:** 2026-04-04  
**Branch-Prefix:** `claude/pbi-generator-*`

---

## Prinzipien für die Umsetzung

1. **Golden Thread bleibt erhalten**: KPI Catalog → Bracket → Generator. Nichts, was wir aus `skills-for-fabric` übernehmen, darf diese Kette aufbrechen.
2. **Additive, nicht substituierend**: Wir ergänzen bestehende Docs, ersetzen keine funktionierenden Konzepte.
3. **Referenz statt Copy-Paste**: Wo `skills-for-fabric` gutes Material hat, verlinken wir — wir pflegen keine Parallelkopien.
4. **Hooks first**: Änderungen an TMDL-Generierung → zuerst Validierungsregel definieren, dann Implementierung.

---

## Phase 1 — Kritische Korrekturen (Sprint 1-2)

### 1.1 TMDL-Referenz erweitern: Advanced Features

**Ziel:** Vollständige TMDL-Syntax-Referenz für alle Features, die unser Generator produzieren könnte.  
**Dateien:**
- `core/strategy_operating_model/operating_model/reference/TMDL_Allowed_Subset.md` — erweitern
- Neue Datei: `products/fabric/powerbi/docs/references/tmdl-advanced-features.md`

**Inhalt neu hinzufügen:**

```
A) Calculation Groups
   - Syntax: calculationGroup table mit calculationItems
   - Anwendungsfall: Zeit-Intelligenz (YTD, LY, QTD)
   - Beispiel: "Time Intelligence" Calculation Group
   - Regel: calculateOn = lastChild (oder specificColumn)

B) Direct Lake — vollständiges Muster
   - Named Expression für Lakehouse-Referenz (AzureStorage.DataLake URL)
   - Entity Partition mit expressionSource
   - Pflichtfelder: entityName, schemaName, expressionSource
   - Constraint: kein dataType:binary, keine Power Query Transforms

C) Security Roles (RLS/OLS)
   - role { modelPermission: read }
   - tablePermission mit filterExpression (DAX)
   - columnPermission mit metadataPermission (OLS)
   - Policy: RLS nur auf Dimensions, nie auf Facts (bestehende Regel mit TMDL-Syntax)

D) database.tmdl + model.tmdl Pflichtinhalt
   - compatibilityLevel: 1702 (Pflicht)
   - compatibilityMode: powerBI (Pflicht)
   - defaultPowerBIDataSourceVersion: powerBI_V3 (Pflicht für Import Mode)
   - discourageImplicitMeasures (Best Practice)

E) Annotationen (model-level + object-level)
   - Syntax: annotation { name: value }
   - Anwendungsfall: Copilot-Metadaten, Tool-Tags
```

**Aufwand:** M (4-6h)  
**Validator-Update:** `check_tmdl_syntax.ps1` um Calculation-Group-Syntax erweitern.

---

### 1.2 Direct Lake Modell-Generierung

**Ziel:** Unser Phase-2/3-Orchestrator kann Direct Lake Modelle aus Data Contracts generieren.  
**Dateien:**
- `products/fabric/powerbi/orchestrator/table_ops.ps1` — neuer Modus `--mode DirectLake`
- `products/fabric/powerbi/docs/references/direct-lake-pattern.md` — neue Referenz

**Implementierungsschritte:**

```
1. table_ops.ps1: Neuer Parameter -StorageMode (Import | DirectLake)
   - DirectLake: generiert entity partition statt M-Partition
   - Named Expression: einmalig pro Domain-Modell in model.tmdl

2. Lakehouse-ID-Resolution:
   - Aus Data Contract: Feld `lakehouse_id` (neu im data_contract.schema.json)
   - Fallback: aus connections.json (GoldDataPath)

3. SQL-Endpoint-Polling:
   - Nach Lakehouse-Create/Update: GET /workspaces/{id}/lakehouses/{id}
   - Warten bis `sqlEndpointProperties.provisioningStatus == "Success"`
   - Timeout: 5 Minuten, 30s Interval

4. Measure-Overlay bleibt unverändert (measures sind storage-mode-agnostisch)
```

**Schema-Update:** `data_contract.schema.json` um `lakehouse_id` + `storage_mode` erweitern.  
**Aufwand:** L (8-12h)

---

### 1.3 REST-API Deployment — `az rest` als Alternative zu `fab`

**Ziel:** Unsere Agents kennen den direkten REST-API-Weg für Semantic Model + Report Deployment.  
**Dateien:**
- `products/fabric/powerbi/docs/references/fabric-api-core.md` — bereits vorhanden, **erweitern**

**Inhalt ergänzen in `fabric-api-core.md`:**

```
A) Two Audiences (bereits vorhanden, validieren)
   - Fabric Items API: https://api.fabric.microsoft.com
   - Power BI Datasets API: https://analysis.windows.net/powerbi/api

B) createItemWithDefinition für Semantic Model
   - Payload-Struktur: definition.parts[] mit base64 TMDL
   - LRO-Polling: 202 → Operation-Id → GET .../operations/{id}
   - Shell-Snippet: az rest mit base64-Encoding

C) createItemWithDefinition für Report (PBIR)
   - Pflicht-Parts: definition/report.json, definition/pages/pages.json,
     definition/pages/<id>/page.json, definition/pages/<id>/visuals/<id>/visual.json
   - definition.pbir: byConnection Referenz (nicht byPath!)
   - Kritischer Hinweis: REST API unterstützt KEIN byPath

D) updateDefinition — Full-Replace Pattern
   - ALLE Parts müssen mitgeschickt werden (modified + unmodified)
   - .platform NIE mitsenden bei updateDefinition
   - Base64-Encoding Pflicht

E) Workspace + Item Discovery (JMESPath)
   - List workspaces → filter by displayName
   - List items by type → filter by displayName
```

**Aufwand:** S (2-3h)

---

### 1.4 Report `definition.pbir` — byConnection statt byPath für REST-Deploy

**Ziel:** Unser Report-Generator erzeugt wahlweise `byConnection` oder `byPath` in `definition.pbir`.  
**Hintergrund:** `byPath` funktioniert lokal (Desktop, pbi-tools) aber nicht via Fabric REST API. Für Cloud-Native Deployment brauchen wir `byConnection` mit der Workspace Connection.

**Dateien:**
- `products/fabric/powerbi/tooling/page_scaffold_generator/pbip_writer.py` — `write_definition_pbir()`

**Implementierung:**

```python
# pbip_writer.py — neuer Parameter connection_type="byPath"|"byConnection"
def write_definition_pbir(self, dataset_path, connection_type="byPath", 
                           workspace_id=None, dataset_id=None):
    if connection_type == "byConnection":
        # Fabric REST API compatible
        content = {
            "version": "4.0",
            "datasetReference": {
                "byConnection": {
                    "connectionString": None,
                    "pbiServiceModelId": None,
                    "pbiModelVirtualServerName": "sobe_wowvirtualserver",
                    "pbiModelDatabaseName": dataset_id,
                    "connectionType": "pbiServiceXmlaStyleLive",
                    "name": "EntityDataSource"
                }
            }
        }
    else:
        # Local PBIP compatible (current default)
        content = {
            "version": "4.0",
            "datasetReference": {"byPath": {"path": dataset_path}}
        }
```

**Aufwand:** S (2h)

---

## Phase 2 — Qualitätsverbesserungen (Sprint 3-4)

### 2.1 Consumption/Discovery: INFO.VIEW.* Referenz

**Ziel:** Agents können bestehende deployed Modelle erkunden und Impact-Analysen durchführen.  
**Dateien:**
- `products/fabric/powerbi/docs/references/powerbi-consumption.md` — **neue Datei**

**Inhalt:**

```
A) Must/Prefer/Avoid (Consumption)
   - Nur Lese-Operationen
   - INFO.VIEW.* vor INFO.* (Berechtigungen)
   - Scope-Estimation vor Deep Discovery

B) Empfohlene Discovery-Reihenfolge
   1. Scope schätzen (Tabellen-, Measures-Anzahl)
   2. INFO.VIEW.TABLES()
   3. INFO.VIEW.COLUMNS() + INFO.VIEW.MEASURES()
   4. INFO.VIEW.RELATIONSHIPS()
   5. INFO.DEPENDENCIES() für DAX-Abhängigkeiten

C) Häufige INFO.VIEW.* Funktionen (Top 10)
   - INFO.VIEW.TABLES, COLUMNS, MEASURES, RELATIONSHIPS
   - INFO.PARTITIONS, INFO.DEPENDENCIES
   - INFO.ROLES, INFO.CALCULATIONGROUPS

D) Narrowing Pattern
   - SELECTCOLUMNS + FILTER statt volle Rowsets
   - Scope-Estimation-Queries vor Deep Dives

E) Troubleshooting
   - ExecuteQuery nicht verfügbar → MCP Server prüfen
   - INFO.* Permission Error → auf INFO.VIEW.* zurückfallen
   - Leere ROLEMEMBERSHIPS → REST API nutzen statt DAX

F) Verwendung mit execute_dax.py
   - Verweis auf tooling/scripts/execute_dax.py
```

**Aufwand:** S (3h)

---

### 2.2 Skill-Format-Standardisierung

**Ziel:** Alle unsere Skill/Agent-Docs haben einheitliches Format für besseres AI-Routing.  
**Dateien zu aktualisieren:**

| Datei | Aktion |
|---|---|
| `.cursor/rules/agent-workflow.mdc` | YAML Frontmatter + Must/Prefer/Avoid hinzufügen |
| `.cursor/rules/assistant-agent.mdc` | YAML Frontmatter + Triggers |
| `.cursor/rules/pm-agent.mdc` | YAML Frontmatter + Delegation |
| `.cursor/rules/router-agent.mdc` | YAML Frontmatter + explizite Routing-Regeln |
| `products/fabric/powerbi/docs/references/fabric-powerbi-authoring.md` | Must/Prefer/Avoid vollständig |
| `products/fabric/powerbi/docs/references/fabric-api-core.md` | Triggers ergänzen |
| `docs/agent/rules/*.md` | Einheitliches Format |

**Standard-Template:**

```markdown
---
name: <skill-name>
description: >
  [Action-Verb]. Use when: (1) ..., (2) ...
  Triggers: "phrase1", "phrase2"
---

## Must/Prefer/Avoid

### MUST DO
- ...

### PREFER
- ...

### AVOID
- ...

## Workflow
[Agentic Workflow: Schritt-für-Schritt]

## Troubleshooting
[Bekannte Fehler mit Fix]
```

**Aufwand:** M (4-6h)

---

### 2.3 Security Roles / RLS vollständig dokumentieren

**Ziel:** Agents generieren valide TMDL für Row-Level Security.  
**Dateien:**
- `TMDL_Allowed_Subset.md` — Section hinzufügen
- `products/fabric/powerbi/docs/references/tmdl-advanced-features.md` — Detail-Beispiele

**Inhalt:**

```tmdl
// Beispiel: Region-based RLS
role 'Sales Region Manager'
    modelPermission: read

    /// Filtert Sales auf Regionen des eingeloggten Nutzers
    tablePermission Sales
        filterExpression: 'Sales'[RegionCode] = LOOKUPVALUE('User Regions'[RegionCode], 'User Regions'[Email], USERNAME())

// OLS: Kosten-Spalten nur für Finance sichtbar
role Finance
    modelPermission: read

    tablePermission Sales
        columnPermission 'Unit Cost'
            metadataPermission: read
```

Plus: REST API für Role-Membership-Assignment (Users zu RLS-Roles hinzufügen).

**Aufwand:** S (2h)

---

### 2.4 Agenten-Delegation strukturieren

**Ziel:** Cross-Cutting-Agent (`router-agent`) hat explizite Delegation zu Spezialisten.  
**Dateien:**
- `.cursor/rules/router-agent.mdc` — Delegation Rules
- `docs/agent/rules/router-agent.md`

**Struktur nach `FabricDataEngineer.agent.md`-Vorbild:**

```yaml
delegates_to:
  - fabric-powerbi-authoring  # Semantic Model Create/Update/Deploy
  - fabric-powerbi-consumption  # DAX Discovery, Impact Analysis
  - pbi-generator-orchestrator  # Phase-Orchestration (Brackets → PBIP)
  - kpi-framework-agent  # KPI Catalog, Action Codes
  - fabric-api-core  # REST API, Auth, LRO
```

**Delegations-Regeln:**
- TMDL-Generierung → `pbi-generator-orchestrator`
- Bestehende Modelle erkunden → `fabric-powerbi-consumption`
- Report via REST deployen → `fabric-powerbi-authoring`
- KPI-Definition ändern → `kpi-framework-agent` (nie in Brackets oder Factsheets)

**Aufwand:** S (2h)

---

## Phase 3 — Nice-to-Have (Sprint 5+)

### 3.1 Prompt-Security-Scan

**Ziel:** Automatisierter Check ob AI-generierte Prompt-Dateien sicher sind.  
**Vorbild:** `.github/scripts/scan_prompt_security.py` aus `skills-for-fabric`  
**Umsetzung:**
- Portieren/Adaptieren des Scripts für unsere Verzeichnisstruktur
- Zu scannende Verzeichnisse: `.cursor/rules/`, `docs/agent/`, `core/agents/`, `tooling/ai/`
- Integration in `run_stage1_checks.ps1` oder als eigener Hook

**Aufwand:** S (2-3h)

---

### 3.2 Versions-Tracking für Skills

**Ziel:** Skill-Dateien haben semantische Versionen, sodass Breaking Changes erkannt werden.  
**Umsetzung:**
- `YAML Frontmatter` um `version: "1.0.0"` erweitern
- `tooling/agent/generate_tool_configs.py` — CHANGELOG-Generierung ergänzen
- Kein `check-updates`-Skill nötig (wir sind im Repo, kein externes Package)

**Aufwand:** S (2h)

---

### 3.3 MCP-Routing-Dokumentation

**Ziel:** Klares Entscheidungsbaum wann File-Edit, wann REST API, wann MCP.  
**Umsetzung:** Abschnitt in `fabric-powerbi-authoring.md`:

```
Änderungsgröße → Tool-Empfehlung:
- Neues Semantic Model (>3 Tabellen)  → createItemWithDefinition (REST)
- Einzelne Measure ändern             → powerbi-modeling-mcp (wenn verfügbar) 
                                         oder File-Edit + TMDL-Hook
- Tabelle hinzufügen                  → Phase-3-table_ops.ps1 + REST updateDefinition
- RLS ändern                          → File-Edit roles/*.tmdl + REST updateDefinition
- Refresh triggern                    → Power BI Datasets API (az rest)
```

**Aufwand:** S (1h)

---

## Aufgaben-Reihenfolge (kompakt)

```
Sprint 1 (1-2 Wochen):
  [ ] 1.1 TMDL Advanced Features Docs (M)
  [ ] 1.3 REST-API az rest Patterns in fabric-api-core.md (S)
  [ ] 1.4 pbip_writer.py byConnection Support (S)

Sprint 2 (1-2 Wochen):
  [ ] 1.2 Direct Lake Generierung in table_ops.ps1 (L)
  [ ] 2.3 RLS/OLS TMDL Syntax (S)

Sprint 3 (1 Woche):
  [ ] 2.1 powerbi-consumption.md INFO.VIEW.* (S)
  [ ] 2.4 Router-Agent Delegation (S)
  [ ] 2.2 Skill-Format-Standardisierung (M)

Sprint 4 (optional):
  [ ] 3.1 Prompt Security Scan (S)
  [ ] 3.2 Versions-Tracking (S)
  [ ] 3.3 MCP-Routing-Doku (S)
```

---

## Erfolgs-Kriterien

| Kriterium | Messung |
|---|---|
| TMDL Calculation Groups | Generator produziert valide TMDL für Zeit-Intelligenz ohne Hook-Fehler |
| Direct Lake Deploy | `table_ops.ps1 -StorageMode DirectLake` erzeugt valide Entity Partitions |
| REST Report Deploy | `definition.pbir` mit `byConnection` wird via REST erfolgreich deployed |
| Discovery | Agent kann `INFO.VIEW.MEASURES()` auf deployed Modell ausführen |
| Skill-Routing | KI wählt korrekt zwischen `fabric-powerbi-authoring` und `pbi-generator-orchestrator` |
