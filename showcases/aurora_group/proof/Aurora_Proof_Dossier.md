# Aurora Proof Dossier — Domain Evidence to Core

> **Version:** 1.0  
> **Date:** 2026-06-01  
> **Scope:** Six Aurora demo use cases (COM-001, COM-002, COM-003, OPS-001, SCM-001, FIN-001)  
> **Process:** `docs/process/research-to-core-standard.md`

---

## Purpose

This dossier records the end-to-end proof that the Research-to-Core process works on Aurora's showcase scope. It shows which domain questions are answered, by which KPIs, visuals, evidence columns, and action codes — and which gaps remain open after the first pass.

---

## Process Summary

The Research-to-Core process was followed for all six Aurora use cases:

1. Deep domain evidence gathered from authoritative sources (ISO standards, academic literature, professional bodies, benchmarks, practitioner guides, anti-pattern sources)
2. Canonical domain models produced (driver trees, required dimensions, action logic)
3. Gap classification performed (content_gap, mapping_gap, schema_gap, generator_gap, model_gap)
4. Content and mapping gaps fixed directly in Core artifacts
5. Schema gaps identified and escalated via Schema Gap Reports (no unilateral schema changes)
6. Model gaps documented in data contracts (pending data engineering)

---

## OPS-001 — Deep Exemplar (OEE) ✅

**Evidence coverage:** 15 sources, portfolio score 11.8/15, all 6 categories covered.

**Domain model:** ISO 22400-2 OEE = Availability × Performance × Quality × Six Big Losses.

| Domain Question | KPI | Visual | Evidence Column |
|----------------|-----|--------|----------------|
| Is OEE on target? | ops.oee.pct | Main_1 (line chart vs target) | ops.oee.pct |
| Is Availability the dominant driver? | ops.availability.pct | Main_2 (line chart vs target) | ops.availability.pct |
| How do all three drivers compare? | A%, P%, Q% | Main_3 (grouped bar %) | ops.availability.pct, ops.performance.pct, ops.quality.pct |
| What is the root cause downtime pattern? | ops.downtime.pct | Page 2 detail matrix | cause_code, loss_type |
| Is PM compliance protecting reliability? | ops.pm_compliance.pct | Page 2 evidence columns | ops.pm_compliance.pct, ops.mtbf.hours, ops.mttr.hours |
| What are the Six Big Losses? | (dimension) | Page 2 evidence | loss_type (Six Big Losses category) |

**Gaps resolved:**
- [x] Supporting KPIs: MTBF, MTTR, PM Compliance, Scrap Rate, FPY added
- [x] Evidence columns: asset, loss_type, cause_code, maintenance_type added
- [x] Main_1 changed from Availability trend to OEE trend vs target (strategic KPI first)
- [x] Main_3 unit mixing fixed (removed throughput.units; now all % metrics)
- [x] Value driver model formula updated to explicit multiplication (ISO 22400-2)
- [x] Benchmark targets added to Factsheet Section 8 (85%/90%/95%/99.9%)
- [x] Business questions updated to include Six Big Losses and MTBF/MTTR

**Open gaps (model_gaps — require data engineering):**
- [ ] dim_loss_type dimension (Six Big Losses) missing from Operations data contract
- [ ] fact_maintenance table missing from Operations data contract

**Schema gaps:** None — all required semantics expressible in current schema.

---

## COM-001 — Sales Performance ✅ (First Pass)

**Evidence coverage:** 11 sources, portfolio score 11.4/15, all 6 categories covered.

**Domain model:** Net Sales = Volume × Price × Mix. PVM decomposition is the core analytical frame.

| Domain Question | KPI | Visual | Status |
|----------------|-----|--------|--------|
| Are we on/off plan? | sales.net_sales.delta_pct.plan | KPI card + Main_1 trend | ✅ Covered |
| What is driving the gap? | PVM effects | Main_1 PVM visual (gap pending) | ⚠️ mapping_gap open |
| Is margin protected? | margin.gm.pct | KPI card | ✅ Covered |
| Which regions are off plan? | delta_pct.plan by region | Main_3 bar chart | ✅ Covered |

**Open gaps:**
- [ ] PVM waterfall/clustered column visual not yet in 30s layer (mapping_gap)
- [ ] PVM measure validation against methodology needed (model_gap)
- [ ] Benchmark targets needed in Factsheet Section 8

---

## COM-002 — Margin & Price Performance ✅ (First Pass)

**Evidence coverage:** 11 sources, portfolio score 12.1/15, all 6 categories covered.

**Domain model:** GM% = f(Price Realization, COGS, Mix). Price realization is fastest lever.

**Open gaps:**
- [ ] Price realization trend visual missing from 30s layer
- [ ] GM% benchmark (25–45%, +0.5–1.5pp improvement target) not in Factsheet

---

## COM-003 — Customer Value ✅ (First Pass)

**Evidence coverage:** 11 sources, portfolio score 12.3/15, all 6 categories covered.

**Domain model:** CLV = f(Retention Rate, Revenue at Risk, NPS). Retention is the highest-leverage lever.

**Open gaps:**
- [ ] CLV:CAC ratio benchmark (≥ 3:1) not in Factsheet Section 8
- [ ] Revenue at risk visual to be verified in 30s layer

---

## SCM-001 — Inventory Performance ✅ (First Pass)

**Evidence coverage:** 11 sources, portfolio score 12.5/15, all 6 categories covered.

**Domain model:** DIO optimised subject to OTIF ≥ 95% constraint. Forecast Accuracy is upstream lever.

**Open gaps:**
- [ ] Forecast accuracy trend visual and DIO vs OTIF comparison missing from 30s layer
- [ ] DIO/OTIF/Stockout benchmarks not in Factsheet Section 8
- [ ] Daily inventory fact grain to be verified in data contract

---

## FIN-001 — Cash & Liquidity Performance ✅ (First Pass)

**Evidence coverage:** 11 sources, portfolio score 12.8/15, all 6 categories covered.

**Domain model:** CCC = DSO + DIO - DPO. DSO reduction is highest-leverage lever for manufacturing.

**Open gaps:**
- [ ] CCC waterfall bridge (DSO/DIO/DPO components) missing from 30s layer
- [ ] fin.overdue_ar.pct likely missing from supporting_kpi_ids
- [ ] Benchmark targets (CCC < 45 days, DSO < 40 days) not in Factsheet Section 8
- [ ] AR aging buckets needed in Finance data contract

---

## Schema Gap Reports Raised

| ID | Affected Schema | Field | Status |
|----|----------------|-------|--------|
| SGR-BRACKET-001 | `usecase_bracket.schema.json` | `documentation.evidence_pack` | Proposed — pending Framework Architect approval |

No unilateral schema changes were made. All content and mapping fixes used existing schema fields.

---

## Semantic Quality Gate — First Calibration Results

Manual audit of OPS-001 against the 33 checks defined in `docs/process/semantic-quality-gate.md`:

| Check Group | Applicable Checks | Passed | Failed | Notes |
|-------------|-----------------|--------|--------|-------|
| Evidence Coverage (SQ-E*) | 8 | 7 | 1 | SQ-E02: DEP status still `reviewed` not `approved` |
| Business Questions (SQ-Q*) | 6 | 6 | 0 | All resolved after bracket fix |
| Visual Semantic (SQ-V*) | 7 | 6 | 1 | SQ-V05: driver bridge formula updated |
| Action Codes (SQ-A*) | 5 | 4 | 1 | SQ-A01: action logic seeds need O-A2.1 wiring |
| Grain/Evidence (SQ-G*) | 4 | 3 | 1 | SQ-G02: loss_type/cause_code now added |

**OPS-001 Semantic Coverage Score:** 26/30 = **87%** (Amber — review before release)

Remaining failures are either model_gaps (data not yet available) or status pending formal DEP approval.

---

## Rollout Readiness Assessment

| Component | Status |
|-----------|--------|
| Research-to-Core Standard | ✅ Created (`docs/process/research-to-core-standard.md`) |
| Evidence Pack Spec | ✅ Created (`docs/process/domain-evidence-pack-spec.md`) |
| Gap Classification Rules | ✅ Created (`docs/process/gap-classification.md`) |
| Semantic Quality Gate Spec | ✅ Created (`docs/process/semantic-quality-gate.md`) |
| Checklist for agents/humans | ✅ Created (`docs/process/research-to-core-checklist.md`) |
| OPS-001 Deep Exemplar | ✅ Completed |
| All 6 Aurora first-pass DEPs | ✅ Completed |
| Schema Gap Reports | ✅ SGR-BRACKET-001 raised |
| add-usecase-scaffold skill update | ✅ Updated to require DEP |
| Agent workflow update | ✅ Research-to-Core referenced |
| Automated semantic-check CLI | ⏳ Pending (Phase 2) |
| CI integration (blocking) | ⏳ Pending calibration |
| Factsheet benchmark targets (all 6 UCs) | ⏳ Open gaps to close |

---

## Next Steps

1. **Framework Architect approval** required for SGR-BRACKET-001 before enforcing `documentation.evidence_pack` in CI
2. **Data engineering** required for OPS-001 model gaps (dim_loss_type, fact_maintenance)
3. **Content gap closure** for remaining 5 use cases (benchmark targets, missing visual slots)
4. **Automated CLI** implementation of semantic-check after calibration
5. **CI enforcement** after false-positive calibration confirms < 5% false-positive rate
