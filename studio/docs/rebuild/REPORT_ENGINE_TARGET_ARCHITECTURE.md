# Report Engine — Current Architecture and Delivery Target

> **Status:** Authoritative current-state and target picture
> **As of:** 2026-08-27
> **Scope:** Governed report delivery, Studio packaging, target adapters, and validation

## 1. Product promise

ALUCA turns governed business meaning into validated analytics delivery artifacts.
It is customer- and tool-agnostic at the core: KPI meaning, action logic, page
intent, and evidence grain are authored once. Vendor syntax is emitted only in a
target adapter and validated with the official vendor or upstream tool wherever
one exists.

The product does not replace Fabric, Power BI, Databricks, OSI, source control,
or customer deployment pipelines. It packages their inputs, exposes unresolved
human decisions, and supplies an auditable handover.

## 2. Authorities and Golden Thread

| Concern | Authority |
|---|---|
| KPI meaning and lineage | `core/kpi_catalog/` |
| Action and decision logic | `core/action_codes/` |
| Use-case orchestration | `core/usecases/**/UseCase_Bracket.yaml` |
| Data grain and fields | `core/data_contracts/` |
| Page and slot contract | `core/templates/page_templates/template_manifest.yaml` |
| Visual permission and semantics | `core/templates/page_templates/visual_registry.yaml` and `visual_library/` |
| Target-neutral delivery model | `tooling/superversion/canonical_contract.py` |
| Schema authority | `tooling/generator/schemas/` |

Factsheets, reports, and Studio screens reference these definitions. They do not
redefine KPI formulas, targets, lineage, or action triggers.

## 3. Production delivery flow

```text
Governed sources
  KPI catalog + action codes + bracket + data contracts + page/visual contracts
        |
        v
ALUCA source adapter (`tooling.superversion.from_aluca`)
        |
        v
Canonical semantic + report contract
        |
        +--> Golden Thread gate
        +--> mandatory page-slot gate
        +--> deterministic target adapter
        |
        +--> TMDL       [planned: structural checks, vendor gate pending]
        +--> PBIR       [live: official powerbi-report-author validation]
        +--> OSI        [live: official upstream schema validation]
        +--> Databricks [beta: explicit HITL plus workspace validation]
        |
        v
Studio package + gate-backed delivery manifest
        |
        v
Customer-approved deployment pipeline and official platform CLI
```

No production Studio route reimplements TMDL, PBIR, OSI, or Metric View syntax.
The Studio calls the Python core through `superversion-bridge.ts`, requests
artifact content only for an explicit package operation, and blocks a package
when the shared gate is red.

## 4. Studio responsibilities

The Studio is the governed authoring and consumption surface. Its production
responsibilities are:

1. expose source definitions, lineage, approvals, and target readiness;
2. curate a bounded use-case scope;
3. invoke the shared core without changing target semantics;
4. display gate results and unresolved HITL decisions honestly;
5. package deterministic artifacts plus a delivery manifest;
6. hand the package to the customer's approved deployment process.

The Studio must not silently repair generated PBIR bindings, infer missing
business fields, manufacture CI/CD workflows, or deploy a target whose adapter
is not classified `live`. Root causes belong in the governed source or adapter.

## 5. Current maturity

| Area | Current state | Completion condition |
|---|---|---|
| Commercial report | Content-complete; PBIR official gate green | Joint visual QA |
| Financial report | Content-complete; PBIR official gate green | Joint visual QA |
| Operations report | Content-complete; PBIR official gate green | Joint visual QA |
| Agentic governance report | Content-complete; PBIR official gate green | Joint visual QA |
| Studio Generate flow | Governed bridge and gated packaging | Joint visual and interaction QA |
| PBIR adapter | `live` | Maintain 0 errors, 0 warnings, 0 connector HITL gaps for curated reports |
| OSI adapter | `live` | Maintain upstream schema validation |
| Databricks adapter | `beta` | Validate in target workspace and resolve/accept every HITL marker |
| TMDL adapter | `geplant` | Add an official vendor validation gate before external deployment |
| CI/CD generation | Not a governed target; production route disabled | Use customer-approved pipeline and official CLI |

## 6. Non-negotiable quality gates

A delivery package is complete only when:

- every KPI and action reference resolves to its authority;
- every report contains exactly the governed overview and detail layers;
- every mandatory template slot exists and has valid geometry;
- every report field is an explicit `table.column` reference;
- no curated PBIR artifact contains `_HITL` or an unreported connector gap;
- the official PBIR validator returns 0 errors and 0 warnings;
- target status and remaining human decisions are visible in the manifest;
- Studio tests, type checking, lint, offline production build, and repository
  quality gates are green.

## 7. Visual completion target

The final phase applies one semantic visual system to both reports and Studio:

- shared hierarchy, spacing, typography, density, and status language;
- restrained semantic color with accessible contrast;
- KPI cards that express value, period, comparison, target, and freshness;
- chart selection driven by analytical meaning, not decoration;
- consistent 3–30–300 progression from signal to explanation to action;
- native visuals and official capabilities first; custom visuals only where a
  governed analytical requirement cannot be met natively;
- responsive Studio interactions and report layouts that remain readable at
  their intended consumption size.

Visual polish may not hide incomplete bindings, beta status, or HITL decisions.
Meaning and function remain the basis of every visual choice.
