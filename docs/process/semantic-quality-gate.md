# Semantic Quality Gate — Specification

> **Version:** 1.0  
> **Status:** Design (no blocking thresholds until Aurora proof calibration)  
> **Authority:** Framework Architect  
> **Related:** `docs/process/gap-classification.md` | `docs/process/research-to-core-standard.md`

---

## Purpose

The Semantic Quality Gate checks that a use case answers the right business questions with the right data, at the right grain, before and after report generation.

Unlike structural/syntactic checks (Stage 1, PBIR JSON schema), this gate evaluates **semantic coverage** — whether domain evidence maps to visible, meaningful content in the bracket and generated report.

**No blocking thresholds are enforced until the Aurora proof run calibrates false-positive rates.**
All checks initially run as warnings only.

---

## 1. Gate Architecture

### 1.1 When It Runs

| Trigger | Mode |
|---------|------|
| Before report generation (pre-gen) | Warn only — prevents generating reports with known semantic gaps |
| After report generation (post-gen) | Warn only — confirms generated output matches bracket intent |
| During Stage 1 CI | Warn only — does not block merge until calibrated |
| Standalone CLI | `pbi-quality semantic-check --use-case <id>` |

### 1.2 What It Reads

| Input | Source |
|-------|--------|
| Domain Evidence Pack | `core/usecases/core/<ID>/Domain_Evidence_Pack.yaml` |
| UseCase Bracket | `core/usecases/core/<ID>/UseCase_Bracket.yaml` |
| Business Factsheet | `core/usecases/core/<ID>/Business_Factsheet.md` |
| KPI Catalog | `core/kpi_catalog/` |
| Action Codes | `core/action_codes/` |
| Generated Report | `products/fabric/powerbi/dist/<ID>.Report/` (optional, post-gen only) |

---

## 2. Check Catalogue

Each check has an ID, description, gap type it detects, and severity.

### 2.1 Evidence Coverage Checks

| Check ID | Description | Gap Type | Severity |
|----------|-------------|----------|----------|
| `SQ-E01` | Use case has a DEP file | N/A | `high` |
| `SQ-E02` | DEP status is not `draft` (reviewed or approved) | N/A | `medium` |
| `SQ-E03` | DEP has ≥ 10 scored sources | N/A | `high` |
| `SQ-E04` | DEP portfolio score ≥ 10/15 | N/A | `high` |
| `SQ-E05` | DEP covers at least 5 of 6 source categories | N/A | `high` |
| `SQ-E06` | DEP includes STD and BNK category sources | N/A | `critical` |
| `SQ-E07` | DEP has ≥ 1 benchmark target per outcome KPI | N/A | `medium` |
| `SQ-E08` | DEP has ≥ 3 wrong interpretations | N/A | `medium` |

---

### 2.2 Business Question Coverage Checks

| Check ID | Description | Gap Type | Severity |
|----------|-------------|----------|----------|
| `SQ-Q01` | Every core business question in Section 2 of the Factsheet maps to at least one KPI plus visual slot in the bracket | `content_gap` or `mapping_gap` | `high` |
| `SQ-Q02` | The strategic KPI ID in the bracket matches the primary outcome KPI in the DEP | `mapping_gap` | `critical` |
| `SQ-Q03` | All driver KPIs from the DEP appear in `influencing_kpi_ids` or `supporting_kpi_ids` | `content_gap` | `high` |
| `SQ-Q04` | At least one visual in `component_30s` shows a trend over time (line/area chart) for the strategic KPI | `mapping_gap` | `high` |
| `SQ-Q05` | At least one visual in `component_30s` shows a ranking or breakdown by a required dimension | `mapping_gap` | `high` |
| `SQ-Q06` | All diagnostic KPIs in the DEP appear in `evidence_columns` of `component_300s` | `content_gap` | `medium` |

---

### 2.3 Visual Semantic Checks

| Check ID | Description | Gap Type | Severity |
|----------|-------------|----------|----------|
| `SQ-V01` | Every 30s visual slot has an assigned KPI or set of KPIs that match the DEP driver tree | `mapping_gap` | `high` |
| `SQ-V02` | No 30s visual slot mixes percentage and absolute currency KPIs on the same axis | `mapping_gap` | `critical` |
| `SQ-V03` | Every trend visual (line/area) has a time axis defined (from `dim_date`) | `mapping_gap` | `high` |
| `SQ-V04` | Every trend visual includes at least one comparison context (vs plan, vs LY, or vs target) | `content_gap` | `high` |
| `SQ-V05` | Every driver bridge or waterfall visual has an explicit decomposition path matching the value driver model formula | `mapping_gap` | `medium` |
| `SQ-V06` | The `big_idea` narrative in each page references the strategic KPI or its delta | `content_gap` | `medium` |
| `SQ-V07` | The `decision_question` in each page matches a core business question from the Factsheet | `mapping_gap` | `medium` |

---

### 2.4 Action Code Coverage Checks

| Check ID | Description | Gap Type | Severity |
|----------|-------------|----------|----------|
| `SQ-A01` | Every action logic seed in the DEP has a corresponding action code ID in the bracket | `content_gap` | `high` |
| `SQ-A02` | Every action code in the bracket resolves to an existing file in `core/action_codes/` | `content_gap` | `critical` |
| `SQ-A03` | Every action code trigger KPI matches a KPI that appears in the bracket's KPI sets | `mapping_gap` | `high` |
| `SQ-A04` | Page 2 execution layer has `action_panel: true` when any action code with T4 page type is used | `mapping_gap` | `medium` |
| `SQ-A05` | T4 use cases have at least one T4-type action code with explicit trigger threshold | `content_gap` | `medium` |

---

### 2.5 Grain and Evidence Table Checks

| Check ID | Description | Gap Type | Severity |
|----------|-------------|----------|----------|
| `SQ-G01` | `evidence_grain` in `component_300s` matches the DEP `required_data_model.preferred_grain` or `minimum_grain` | `mapping_gap` | `critical` |
| `SQ-G02` | All required dimensions from the DEP appear in `evidence_columns` | `content_gap` | `high` |
| `SQ-G03` | All outcome and driver KPIs from the DEP appear in `evidence_columns` | `content_gap` | `medium` |
| `SQ-G04` | `evidence_grain` is not `transaction_line` (schema rule) | N/A | `critical` |

---

### 2.6 Post-Generation Report Checks (Optional)

These checks run after report generation and compare the generated PBIR visual bindings to the bracket configuration.
They are structural-semantic — they verify that the generator correctly translated the bracket into the report.

| Check ID | Description | Gap Type | Severity |
|----------|-------------|----------|----------|
| `SQ-P01` | Every slot in `component_30s` resolves to exactly one visual in the generated report | `generator_gap` | `critical` |
| `SQ-P02` | Every generated visual has at least one measure binding from the bracket KPI set | `generator_gap` | `high` |
| `SQ-P03` | Trend visuals use the `CalendarYearMonth` or `Date` dimension as category axis | `generator_gap` | `high` |
| `SQ-P04` | Bar/column visuals use the `category_field` from the bracket if specified | `generator_gap` | `high` |
| `SQ-P05` | KPI card visuals reference the strategic KPI measure | `generator_gap` | `high` |
| `SQ-P06` | Generated report has the correct number of pages (matches `report_structure`) | `generator_gap` | `critical` |

---

## 3. Scoring Model

### 3.1 Score Calculation

```
Semantic Coverage Score = (Checks_Passed / Total_Checks_Applicable) × 100
```

Checks that are not applicable (e.g., no DEP present → skip DEP content checks) are excluded from denominator.
Critical checks that fail automatically set the score to 0, regardless of other checks.

### 3.2 Score Interpretation (Calibration Phase — Warning Only)

| Score | Label | Action |
|-------|-------|--------|
| 90–100 | Green | No action required |
| 75–89 | Amber | Review recommended before release |
| 50–74 | Yellow | Fix high-severity gaps before release |
| < 50 | Red | Use case not ready for production generation |

> **Important:** These thresholds are calibration targets, not enforced gates.
> They will be enforced (blocking) after the Aurora proof run confirms false-positive rates below 5% across 6 use cases.

---

## 4. Implementation Path

### 4.1 Phase 1 — Manual Scoring (Now)

For each Aurora use case, the gate is run as a manual audit:
- Reviewer checks each applicable check from Section 2
- Records pass/fail per check in the DEP `mapping_readiness` section
- Computes coverage score manually

### 4.2 Phase 2 — Automated CLI (After Aurora Proof)

Implement as a Python module in `tooling/report_quality/` or `packages/pbi_quality_tools/`:

```bash
pbi-quality semantic-check --use-case OPS-001
pbi-quality semantic-check --use-case OPS-001 --post-gen --report-dir products/fabric/powerbi/dist/
pbi-quality semantic-check --all  # All use cases in core/usecases/core/
```

Output:
- Console summary with per-check results
- JSON output for CI integration
- Context pack entry for AI agent consumption

### 4.3 Phase 3 — CI Integration (After Calibration)

Add to `tooling/quality/run_quality_gate.ps1`:
```powershell
# Phase 8: Semantic Quality Gate
pbi-quality semantic-check --all --fail-on critical
```

---

## 5. Calibration Protocol

After the Aurora proof run (6 use cases):

1. Count false positives per check (check fires but finding is genuinely not applicable)
2. For each check with false-positive rate > 10%, either:
   - Refine the check logic, or
   - Downgrade severity, or
   - Add an explicit waiver mechanism in the bracket
3. Set blocking thresholds for checks with false-positive rate < 5%
4. Document calibration results in `internal/project_mgmt/KNOWN_ERRORS_AND_FIXES.md`

---

## 6. Waiver Mechanism (Pre-calibration)

A use case author may suppress a specific semantic check by adding a `semantic_waivers` section to the bracket.
This requires a written justification.

Example (non-enforced until schema gap SGR-BRACKET-001 is approved):
```yaml
# In UseCase_Bracket.yaml documentation section:
semantic_waivers:
  - check_id: SQ-Q05
    justification: "This use case has no ranking visual because all lines are equivalent. OEE is compared against target, not ranked."
    waived_by: "framework-architect"
    waived_date: "2026-06-01"
```

> **Note:** The `semantic_waivers` field requires a schema addition in the bracket schema.
> This is tracked as SGR-BRACKET-002 (to be raised after Aurora calibration if waivers are needed).
