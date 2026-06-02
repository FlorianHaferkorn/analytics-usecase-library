# Implementation Roadmap — Page Template Doctrine & Visual Baukasten

> **Status:** Authoritative  
> **Phase:** 5 — Umsetzungs-Roadmap  
> **Prerequisite:** All of Phase 1–4 must be complete before Phase 5 begins.  
> **Authority chain:** DOCTRINE → TAXONOMY → BAUKASTEN → ENGINE ARCHITECTURE → this roadmap

---

## 1. Overview

The implementation follows five streams in parallel once the doctrine layer is frozen. Streams A–B produce the contracts; Streams C–D consume them; Stream E validates the end-to-end integrity.

```
Freeze    ──► Stream A ──────────────────────────────────────────────────────┐
(Doctrine)                                                                   │
           ──► Stream B (Registry & Schema) ────────────────────────────────┼──► Pilot COM-002
                                                                             │         │
           ──► Stream C (Studio Preview) ──────────────────────────────────┼──►       │
                                                                             │         ▼
           ──► Stream D (Fabric Generator) ────────────────────────────────┼──► Full Scale
                                                                             │
           ──► Stream E (Validation Gates) ──────────────────────────────────┘
```

---

## 2. Gate Sequence: Freeze → Pilot → Scale

### Gate 0 — Doctrine Freeze ✅ (Complete)

**Condition:** All four doctrine documents exist, are source-backed, and cross-reference each other.

| Deliverable | Status |
|---|---|
| `studio/docs/rebuild/PAGE_TEMPLATE_DOCTRINE.md` | ✅ Done |
| `studio/docs/rebuild/PAGE_TYPE_TAXONOMY.md` | ✅ Done |
| `studio/docs/rebuild/VISUAL_BAUKASTEN.md` | ✅ Done |
| `studio/docs/rebuild/REPORT_ENGINE_TARGET_ARCHITECTURE.md` | ✅ Done |
| `core/templates/page_templates/template_manifest.yaml` | ✅ Done |
| `core/templates/page_templates/visual_registry.yaml` | ✅ Done |

**Go/No-Go:** Go — all deliverables complete. Streams B–E can begin.

---

### Gate 1 — Registry & Schema Validated

**Condition:** Machine-readable registries are syntactically valid and schema-checked. TypeScript types align with Python IR.

| Task | Stream | Owner | DoD |
|---|---|---|---|
| Write JSON Schema for `template_manifest.yaml` | B | Architecture Agent | `python -m jsonschema` validates manifest |
| Write JSON Schema for `visual_registry.yaml` | B | Architecture Agent | `python -m jsonschema` validates registry |
| Add `template_variant` field to `UseCase_Bracket.yaml` schema | B | Architecture Agent | Schema validates existing brackets |
| Add `information_block` field per slot in `layout_330300.schema.json` | B | Architecture Agent | Schema updated, no existing bracket breaks |
| Generate TypeScript types from JSON Schema | B | Architecture Agent | `studio/src/lib/schemas/template-manifest.ts` exists |
| Align `ir/specs.py VisualType` enum with `visual_registry.yaml` keys | B | Architecture Agent | Python tests pass; no enum mismatch |

**Go Condition:** All CI schema checks pass. No existing brackets break.  
**No-Go Condition:** Schema extension breaks existing bracket validation → revert field to optional.

---

### Gate 2 — Studio Preview Manifest-Driven (Pilot COM-002)

**Condition:** The Studio `PageTemplatePreview` for COM-002 renders from the manifest, not from hardcoded data.

| Task | Stream | Owner | DoD |
|---|---|---|---|
| Create `studio/src/lib/studio/template-manifest-loader.ts` | C | Implementation Agent | Reads `template_manifest.yaml` and `visual_registry.yaml`; typed output |
| Add `useManifest` flag to `ReportTemplatesGallery` (fallback to hardcoded) | C | Implementation Agent | Gallery renders both paths without error |
| Replace hardcoded `TEMPLATE_META` in `page-template-preview.tsx` | C | Implementation Agent | Preview renders from manifest for T1_Portfolio, T2_DriverBridge, T3_ExceptionQueue, T4_ActionDecision |
| Render slot placeholders with allowed visual types from registry | C | Implementation Agent | Each slot shows information_block label + allowed visual options |
| Tag sample data as `preview_sample`, distinguish from real data | C | Implementation Agent | No confusion between sample and production data |

**Go Condition:** COM-002 preview renders correctly from manifest; `npx tsc --noEmit` passes; visual inspector shows correct block labels.  
**No-Go Condition:** Manifest loader cannot parse YAML at build time → evaluate next.js server-side loading constraints and use JSON alternative.

---

### Gate 3 — Fabric Generator Registry-Validated (Pilot COM-002)

**Condition:** The PBIP generator for COM-002 validates visual selection against the registry before writing.

| Task | Stream | Owner | DoD |
|---|---|---|---|
| Add manifest reader to `config_loader.py` | D | Fabric Agent | `config_loader.get_template_manifest()` returns typed manifest |
| Extend `visual_builder.py` to check allowed visuals per slot | D | Fabric Agent | Raises `VisualNotAllowedError` for forbidden visual + slot combinations |
| Extend `visual_validator.py` with quality rules from registry | D | Fabric Agent | Waterfall reconciliation, sort order, column count rules checked |
| Add CI check: `test_visual_selection_against_registry.py` | E | Verifier Agent | Test fails when waterfall used on T1 page |
| Validate COM-002 PBIP output against registry | D+E | Fabric Agent + Verifier | `validate_page()` passes for generated COM-002 PBIP |

**Go Condition:** COM-002 generates a valid PBIP with no visual selection violations; all existing generator tests still pass.  
**No-Go Condition:** Generator path conflicts with existing scaffold logic → keep both paths and document divergence point; do not merge until pilot passes.

---

### Gate 4 — Validation Gates Live in CI

**Condition:** All validation gates run in CI on every PR that touches templates, brackets, or generated reports.

| Gate | CI Command | Failure Action |
|---|---|---|
| `template_manifest.yaml` valid | `python -m jsonschema --instance ... --schema ...` | Block PR |
| `visual_registry.yaml` valid | Same | Block PR |
| Every `UseCase_Bracket.yaml` `template_variant` resolves | `python tooling/tests/test_bracket_manifest_alignment.py` | Block PR |
| No forbidden visual in any generated PBIP slot | `visual_validator.py --registry ...` | Block PR |
| Waterfall bars reconcile | `visual_validator.py --check reconciliation` | Block PR |
| TypeScript schema types in sync | `npx tsc --noEmit` | Block PR |

**Go Condition:** All gates green on main branch.  
**No-Go Condition:** Gate false-positives on existing content → add explicit exemption flag with mandatory comment; never silently disable the gate.

---

### Gate 5 — Full Scale (Post-Pilot)

**Condition:** COM-002 pilot is complete; all gates green; team has accepted the manifest-based workflow.

| Task | Stream | Owner |
|---|---|---|
| Apply manifest-based rendering to all T1–T4 variants in Studio gallery | C | Implementation Agent |
| Migrate all use cases' `UseCase_Bracket.yaml` to include `template_variant` | B | Architecture Agent |
| Scale PBIP generator to all use cases via manifest | D | Fabric Agent |
| Update `PROGRESS.md` and close Template Doctrine epics | — | PM Agent |

---

## 3. Agent Assignments

| Agent | Streams | Primary Deliverables |
|---|---|---|
| **Research Agent** | A (completed) | Doctrine, source matrix, Meridian evaluation |
| **Product/PM Agent** | A (completed) | Taxonomy, variant definitions, use case mapping |
| **Visualization Agent** | A (completed) | Visual Baukasten, substitution matrix, encoding rules |
| **Power BI Agent** | A+D | PBIR constraints, visual builder extension, PBIP validation |
| **Architecture Agent** | B | JSON Schema, IR alignment, schema drift tracking |
| **Implementation Agent** | C | Studio manifest loader, preview renderer, TypeScript types |
| **Verifier Agent** | E | CI gates, test suite, quality rule tests |

---

## 4. Definition of Done — Gesamt

The entire doctrine and implementation initiative is **Done** when:

- [ ] Every template rule in `PAGE_TEMPLATE_DOCTRINE.md` has a source tag
- [ ] Every use case maps to exactly one `template_variant` in `template_manifest.yaml`
- [ ] Studio Preview renders from manifest (no hardcoded template data)
- [ ] PBIP generator validates visual selection against `visual_registry.yaml`
- [ ] Waterfall reconciliation validated in CI for every T2 page
- [ ] Action Panel completeness validated in CI for every T4 page
- [ ] All existing generator tests pass
- [ ] `npx tsc --noEmit` passes
- [ ] Schema drift between Python IR and TypeScript is documented and tracked

---

## 5. Rollback Strategy

- Existing Fabric generator paths remain operational until Gate 3 passes
- `useManifest` flag in Studio gallery allows instant rollback to hardcoded previews
- `template_variant` field in brackets is optional until Gate 1 completes — existing brackets without the field use the default variant for their page type
- No existing PBIP report files are deleted or overwritten until Gate 3 is validated

---

## 6. Go/No-Go Summary Table

| Gate | Go Condition | No-Go Action |
|---|---|---|
| 0 — Doctrine Freeze | All 6 doctrine + registry files exist | Block stream start |
| 1 — Schema Validated | CI schema checks pass | Make field optional; revisit extension |
| 2 — Studio Manifest-Driven | COM-002 preview from manifest; tsc passes | Keep hardcoded fallback; debug loader |
| 3 — Fabric Registry-Validated | COM-002 PBIP validated; existing tests pass | Keep parallel paths; document divergence |
| 4 — CI Gates Live | All gates green on main | Add exemption flags; never disable silently |
| 5 — Full Scale | Pilot done; team accepts workflow | Limit to pilot use cases until team buys in |

---

## 7. Self-Check: Every Template Decision Must Answer

Before finalizing any template, slot, or visual decision, answer:

1. **Which user question does this answer?** (domain task)
2. **What information does this require?** (data abstraction)
3. **What granularity is appropriate?** (3s / 30s / 300s)
4. **Which visual encoding is most accurate?** (Cleveland & McGill hierarchy)
5. **Which source justifies this choice?** (from PAGE_TEMPLATE_DOCTRINE.md source matrix)

If any of these cannot be answered, the decision is not ready.
