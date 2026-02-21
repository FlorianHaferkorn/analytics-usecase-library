# Granulares Backlog (feine Ziele)

**Purpose:** Fein zerlegte Issues für das GitHub Project. Jedes Item ist ein klar abgrenzbarer Task (ca. 1 PR oder wenige Stunden). Das Skript `tooling/project_mgmt/setup_project_full.py` legt diese Issues an, fügt sie dem Project hinzu und setzt die Felder.

**Language:** English.

---

## Milestones

- **Project completion** — Blocker, Review, Doku (Projektabschluss).
- **Phase 2** — 3-30-300 vollständig, Strategy Pattern / AI urgency.
- **Technical backlog** — MCP, Fabric, Aurora, Synthetic data, Page scaffold.

---

## Project completion (granular)

| Title | Area | Priority | Notes |
|-------|------|----------|--------|
| [Task] Resolve blockers from content review (company_strategy anchors, factsheet paths) | Docs | P0 | presentation_status_and_roadmap |
| [Task] Remaining review adjustments (style, link-backs, encoding) | Docs | P1 | |
| [Task] Document CI/release without Stage-1 skip | Tooling | P1 | Zero-tolerance documentation |

---

## Phase 2 – 3-30-300 (granular)

| Title | Area | Priority | Notes |
|-------|------|----------|--------|
| [Epic] 3-30-300 complete: 300s page from action-code YAML | FabricPowerBI | P1 | Parent epic |
| [Task] Define 300s page layout in page template (layout_330300) | FabricPowerBI | P1 | core/templates/page_templates |
| [Task] Generate action text from action-code YAML in report | FabricPowerBI | P1 | Action payload in 300s page |
| [Task] Generate evidence table from data contract / action payload | FabricPowerBI | P1 | Evidence for 300s |
| [Task] Wire 300s page into report scaffold (Aurora) | FabricPowerBI | P1 | Report structure |
| [Task] Integration test: 300s page end-to-end | FabricPowerBI | P2 | Verify full flow |

---

## Phase 2 – Strategy Pattern / AI (granular)

| Title | Area | Priority | Notes |
|-------|------|----------|--------|
| [Epic] Strategy Pattern / AI urgency and automated reasoning | Framework | P2 | Parent epic |
| [Task] Document urgency rules in strategy_patterns.md | Framework | P2 | core/strategy_operating_model/company |
| [Task] Add tooling hook for urgency derivation (stub or spec) | Tooling | P2 | Optional automation |
| [Task] Document automated reasoning scope and limits | Docs | P2 | internal/vision or strategy |

---

## Technical backlog – Power BI MCP / Fabric (granular)

| Title | Area | Priority | Notes |
|-------|------|----------|--------|
| [Task] Call Power BI MCP table_operations from table_ops.ps1 | Tooling | P2 | table_ops.ps1 ~line 138 |
| [Task] Call Power BI MCP relationship_operations from relationship_ops.ps1 | Tooling | P2 | relationship_ops.ps1 ~line 199 |
| [Task] Fabric: Workspace API (GET/POST) in deploy.ps1 | Tooling | P2 | deploy.ps1 |
| [Task] Fabric: Import PBIP/TMDL to semantic model API in deploy.ps1 | Tooling | P2 | deploy.ps1 |
| [Task] Fabric: Publish report and bind to dataset in deploy.ps1 | Tooling | P2 | deploy.ps1 |
| [Task] Fabric: Set refresh schedule via REST in deploy.ps1 | Tooling | P2 | deploy.ps1 |
| [Task] Fabric: Apply RLS / security_user_org mapping via API in deploy.ps1 | Tooling | P2 | deploy.ps1 |
| [Task] TMDL: default format strings and display folders (AUTOMATION_FLOW) | Tooling | P2 | tooling/powerbi_mcp/AUTOMATION_FLOW.md |
| [Task] Update relationship via MCP (AUTOMATION_FLOW) | Tooling | P2 | AUTOMATION_FLOW.md |
| [Task] Generate visuals from template (AUTOMATION_FLOW) | Tooling | P2 | AUTOMATION_FLOW.md |

---

## Technical backlog – Aurora (granular)

| Title | Area | Priority | Notes |
|-------|------|----------|--------|
| [Task] Aurora Operations model: complete relationships and measures (Operations.yaml) | Aurora | P1 | showcases/aurora_group/models |
| [Task] Aurora Operations model: DAX in KPI Catalog, Measure_Dictionary | Aurora | P1 | Operations domain |
| [Task] Aurora Finance model: complete relationships and measures (Finance.yaml) | Aurora | P1 | Finance domain |
| [Task] Aurora Finance model: DAX in KPI Catalog, Measure_Dictionary | Aurora | P1 | Finance domain |

---

## Technical backlog – Synthetic data (granular)

| Title | Area | Priority | Notes |
|-------|------|----------|--------|
| [Task] Synthetic: ensure Lakehouse exists before notebook run (create or doc) | Tooling | P2 | fabric_nb_generate_backbone_core_v1.py |
| [Task] Synthetic: implement date range with Spark (backbone notebook) | Tooling | P2 | backbone notebook |
| [Task] Synthetic: derive from sales + config.inventory (target_dio_range, coverage days) | Tooling | P2 | backbone notebook |
| [Task] Synthetic: implement join + ratio, Category join + GM% band check | Tooling | P2 | backbone notebook |
| [Task] Synthetic: RI dim_* vs facts, margin bands, DIO/CCC bands | Tooling | P2 | backbone notebook |
| [Task] Synthetic: Lakehouse and schema exist; map dims/facts to config.lakehouse.tables | Tooling | P2 | backbone notebook |
| [Task] Synthetic: optional holiday logic for is_holiday in generate_gold_layer.py | Tooling | P2 | generate_gold_layer.py line 121 |

---

## Technical backlog – Page scaffold (granular)

| Title | Area | Priority | Notes |
|-------|------|----------|--------|
| [Task] Page scaffold: BOM support in YAML scanner | Tooling | P2 | scanner.py line 187 |
| [Task] Page scaffold: tab handling rules in YAML scanner | Tooling | P2 | scanner.py line 761 |

---

## Field mapping (for script)

- **Status:** always `Backlog` for new items.
- **Risk:** `On track` for new items.
- **Milestone:** as in table (Project completion / Phase 2 / Technical backlog).
- **Area:** Framework, FabricPowerBI, Aurora, Tooling, Docs (exact spelling for Project single-select).
- **Priority:** P0, P1, P2.
