# Playbook: From Strategy to First Report

## 1. Purpose

This playbook describes the **minimum steps** to go from strategic intent to a first governed, action-oriented report using the Action-Ready Analytics Framework. It is tool-agnostic in concept; the first concrete implementation path is Microsoft Fabric / Power BI (references below).

**Entry paths:**

- **Greenfield:** No existing governed analytics; start from strategy and use cases.
- **Existing BI:** You have reports and data; you want to align them to the framework (strategy → KPIs → use cases → semantic layer → reports).

This playbook focuses on the Greenfield path. Adaptation for "Existing BI migration" is noted where it differs.

---

## 2. Prerequisites

- **Business:** Executive or domain sponsor who can confirm strategic priorities and KPI ownership.
- **Analytics:** Team (or partner) that can build semantic model and reports and run validation.
- **Data:** At least one domain with accessible source data (e.g. sales, finance, or operations) and willingness to define a data contract.

---

## 3. Steps (Overview)

| Step | What you do | Output / gate |
|------|-------------|----------------|
| 1 | Define or choose strategy pattern | Selected pattern + top Strategic KPIs |
| 2 | Select use-case pack and confirm key questions | Use-case list + key questions |
| 3 | Align data: contracts and semantic requirements | Data contract(s); required facts/dims |
| 4 | Build semantic model and measures | Semantic model aligned to KPI catalog and use cases |
| 5 | Build first report (3-30-300) and link action codes | First report; optional action layer |
| 6 | Validate and iterate | Stage 1 (and Fabric) checks pass; review with business |

---

## 4. Step 1 — Define or Choose Strategy Pattern

**Goal:** Anchor analytics in strategic intent so the first report steers on the right KPIs.

**Actions:**

1. Read `framework/strategy_operating_model/company/strategy_patterns.md`.
2. Choose one primary pattern (Margin-First, Cash-First, or Growth-First) or blend two (e.g. Margin-First + Cash-First).
3. List the **top 5–7 Strategic KPIs** from the pattern(s). Confirm each exists in `framework/kpi_catalog/KPI_Catalog.md` (or add to catalog with owner).
4. Confirm **ownership** (who is accountable for each KPI) and document in your governance (see `operating_model/ownership_raci_golden_thread.md`).

**Output:** Document: "We use [pattern(s)]. Our top Strategic KPIs are: [list]. Owners: [roles]."

**Existing BI:** Map existing reports to a pattern; identify which KPIs are already in use and which are missing or inconsistent.

---

## 5. Step 2 — Select Use-Case Pack and Confirm Key Questions

**Goal:** Scope the first delivery by use cases that support the chosen strategy pattern.

**Actions:**

1. From the strategy pattern, take the **Priority 1 (and optionally 2) use-case clusters** (see `strategy_patterns.md`).
2. Open `framework/usecases/UseCase_Inventory.md` and note the use case IDs (e.g. COM-002, FIN-001).
3. For each selected use case, read the **Business Factsheet** (e.g. `framework/usecases/core/COM-002_Margin_Price_Performance/Business_Factsheet.md`) and confirm:
   - Required KPIs are in the KPI catalog.
   - Key questions (section 2) are acceptable for your context.
   - Action codes (section 4) are relevant; map is in `UseCase_ActionCode_Map.yaml`.
4. Document the **use-case pack** for Phase 1: e.g. "COM-002, FIN-002, XD-003."

**Output:** List of use cases; confirmed key questions and required KPIs per use case.

**Existing BI:** Map existing reports to use cases; identify gaps (e.g. report exists but no use case, or use case has no report).

---

## 6. Step 3 — Align Data: Silver Contracts and Semantic Requirements

**Goal:** Define or adopt **Silver** (conformed, validated domain data) so Gold and the semantic model can be built. We start from Silver, not Gold. See `framework/strategy_operating_model/operating_model/data_layers_standard.md`.

**Actions:**

1. For each use case in the pack, read the **Technical Factsheet** (section 6: Data Requirements) — required facts, dimensions, grain, time range.
2. Check if a **Silver data contract** already exists for the domain (`framework/data_contracts/domains/`, `framework/data_contracts/sources/` or customer equivalent). If not, create a minimal contract (schema, grain, key fields) for the facts and dimensions needed for **Silver**.
3. Confirm **source data** can supply these (e.g. ERP, CRM, data lake). Resolve gaps (new pipeline, staging, or scope reduction). Staging/Bronze are out of scope unless explicitly included.
4. Document **required entities** for Silver and downstream semantic model: facts, dimensions, grain. This becomes the input for Step 4 (Gold/semantic model built from Silver).

**Output:** Silver data contract(s) or contract references; list of required facts/dims; confirmation that source data exists or is planned.

**Existing BI:** Map current data to Silver contracts; identify where contracts are missing or inconsistent.

---

## 7. Step 4 — Build Semantic Model and Measures

**Goal:** Implement a semantic layer that exposes governed measures for the selected KPIs and use cases. Semantic model (and Gold, if used) consume **Silver** as defined in Step 3.

**Actions:**

1. **Design** the semantic model (tables, relationships, grain) to support the required facts and dimensions from Step 3 (Silver). Use `framework/strategy_operating_model/operating_model/reference/ActionReady_SemanticModel_Blueprint.md` and implementation guide (e.g. Fabric) for patterns.
2. **Implement measures** for every required KPI in the use-case pack. Use the KPI Catalog and measure system rules (`operating_model/measure_system.md`). For Fabric/Power BI: generate or author TMDL; use `_internal/tools/generation/generate_tmdl_measures.ps1` if applicable.
3. **Validate:** Run **Stage 1** from repo root: `.\_internal\tools\run_stage1_checks.ps1`. For Fabric: run `.\implementations\microsoft_fabric_powerbi\tools\run_fabric_checks.ps1` (measures vs KPI, TMDL vs measure dictionary). Fix any failures.

**Output:** Semantic model (e.g. TMDL dataset) with measures aligned to KPI catalog; Stage 1 and Fabric checks green.

**Existing BI:** Refactor or extend existing dataset to match KPI catalog and use-case requirements; add missing measures; run same validation.

---

## 8. Step 5 — Build First Report (3-30-300) and Link Action Codes

**Goal:** Deliver the first report that consumes the semantic model and supports decisions and actions.

**Actions:**

1. **Pick one use case** from the pack for the first report (e.g. COM-002 Margin & Price Performance).
2. **Layout:** Follow the use case's **5. 3-30-300 Page Layout** (Business Factsheet): 3-second layer (KPI cards), 30-second layer (main visuals), required slicers, 300-second layer (diagnostics).
3. **Templates:** Use `framework/templates/page_templates/` and implementation guide (e.g. Fabric report structure, theme) for consistency.
4. **Apply standardized theme:** Themes are **applied automatically** when using the page scaffold generator (unless `--no-theme` is set). The generator detects showcase default or framework default from `themes.config.json`. To override: use `--theme <name>` when generating scaffolds. To apply manually: `py implementations/microsoft_fabric_powerbi/tools/apply_report_theme.py path/to/Report --theme-name '<name>'`. Base theme remains fixed; custom theme defines the standardized look. For IBCS styling, use `--theme-name "IBCS_Light"` or set as default via `setup_theme_defaults.py`. Theme schema (optional): run `py implementations/microsoft_fabric_powerbi/tools/theme_generator/tools/theme-agent/fetch_latest_theme_schema.py --update-pin` once or in CI so validation uses the latest schema.
5. **Action codes:** Ensure the report (or an action panel) can surface which action codes apply when KPIs deviate (trigger levels L1–L3). Definitions stay in `framework/action_codes/`; report only references them.
6. **Deploy** to a dev or test workspace; validate with business that definitions and layout match expectations.

**Output:** First report (e.g. PBIR in Fabric) consuming the semantic model; optional action layer or drill-through to action code documentation.

**Existing BI:** Rebuild or restructure one report to match 3-30-300 and use-case layout; connect to governed measures only.

---

## 9. Step 6 — Validate and Iterate

**Goal:** Ensure the end-to-end chain is consistent and repeatable.

**Actions:**

1. **Run Stage 1** again after any changes to factsheets, KPI catalog, or action codes: `.\_internal\tools\run_stage1_checks.ps1`.
2. **Run Fabric checks** (if using Fabric): `.\implementations\microsoft_fabric_powerbi\tools\run_fabric_checks.ps1`.
3. **Review with business:** Confirm key questions are answered by the report; confirm action codes are understandable and owned.
4. **Iterate:** Add the next use case from the pack; repeat Steps 4–6 as needed. Extend to more domains when ready.

**Checklist for adding the next use case (Fabric/Power BI):**

- [ ] Generate **scaffold** (and optional HTML mockup) for the use case: `generate_page_scaffold.py --use-case <ID> --page overview|detail --output <Report> --mockup <path>`.
- [ ] **Bind visuals** to governed measures only (semantic model); no ad-hoc calculations in the report.
- [ ] **Apply theme** (Theme Generator or `apply_report_theme`); document theme name and path.
- [ ] Run **Report Documentation Generator** for the report: `generate_report_documentation.py --report <Report>`; store output in `showcases/<name>/reporting/Report_Documentation_<ID>.md`.
- [ ] Run **Stage 1**: `.\_internal\tools\run_stage1_checks.ps1`.
- [ ] Run **Fabric checks**: `.\implementations\microsoft_fabric_powerbi\tools\run_fabric_checks.ps1`.

**Output:** Stable first report; checklist for adding the next use case; governance (ownership, change flow) in place.

---

## 10. Reference: Framework and Implementation Links

| Need | Location |
|------|----------|
| Data layers (Silver-first) | `framework/strategy_operating_model/operating_model/data_layers_standard.md` |
| Strategy patterns | `framework/strategy_operating_model/company/strategy_patterns.md` |
| Golden Thread | `framework/strategy_operating_model/operating_model/golden_thread_strategy_to_action.md` |
| Use Case Inventory & Key Questions | `framework/usecases/UseCase_Inventory.md` |
| Use case factsheets | `framework/usecases/core/<ID>_<Name>/` |
| KPI Catalog | `framework/kpi_catalog/KPI_Catalog.md`, `KPI_Taxonomy.md` |
| Action codes & patterns | `framework/action_codes/`, `Action_Code_Patterns.md` |
| Ownership RACI | `framework/strategy_operating_model/operating_model/ownership_raci_golden_thread.md` |
| Silver data contracts | `framework/data_contracts/` (domains/, sources/) |
| Page templates | `framework/templates/page_templates/` |
| Fabric/Power BI implementation | `implementations/microsoft_fabric_powerbi/guide/fabric_powerbi.md` |
| Stage 1 (CI gate) | `_internal/tools/run_stage1_checks.ps1` |
| Fabric checks | `implementations/microsoft_fabric_powerbi/tools/run_fabric_checks.ps1` |

---

## 11. Definition of Done (First Report)

- [ ] Strategy pattern chosen; top Strategic KPIs listed and owned.
- [ ] Use-case pack selected; key questions and required KPIs confirmed.
- [ ] **Silver** data contract(s) and source data aligned with use-case requirements (Silver-first).
- [ ] Semantic model built from Silver; measures align to KPI catalog; Stage 1 and (if Fabric) Fabric checks pass.
- [ ] First report built with 3-30-300 layout and linked to action codes.
- [ ] Business review completed; next use case(s) in pack planned.
