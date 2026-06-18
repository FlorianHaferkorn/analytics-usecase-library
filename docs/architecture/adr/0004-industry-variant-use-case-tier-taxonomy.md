# ADR 0004 — Industry-Variant Use-Case Tier Taxonomy

- **Status:** Proposed
- **Date:** 2026-06-18
- **Scope:** How use cases beyond the governed core-16 are identified, foldered, and governed (cross-industry extensions and sector-specific variants)
- **Supersedes:** —
- **Related:** [`../../../internal/project_mgmt/KNOWN_GAPS.md`](../../../internal/project_mgmt/KNOWN_GAPS.md) (§7, the deferred epic this ADR ratifies — prerequisite #4), [`0001-pluggable-validation-backends-and-capability-tiers.md`](0001-pluggable-validation-backends-and-capability-tiers.md), [`../../../core/usecases/README.md`](../../../core/usecases/README.md), [`../../../core/action_codes/decision_spines/DecisionSpine_UseCase_Map.yaml`](../../../core/action_codes/decision_spines/DecisionSpine_UseCase_Map.yaml)

---

## Context

The library ships a governed **core-16** set of use cases identified `XXX-NNN`
(`COM-001`, `FIN-002`, `XD-003`, …) under `core/usecases/core/`. They share one
Golden Thread: a use case references governed KPIs (`core/kpi_catalog/`), action
codes (`core/action_codes/`), and decision spines — it never redefines their
meaning.

Customers ask for two kinds of use case the core-16 does not cover:

- **Cross-industry extensions** — sector-agnostic analytical patterns that sit
  *beyond* the core-16 but apply broadly (e.g. Customer Segmentation / RFM, Budget
  Variance / P&L Bridge, Supplier Risk). They are not tied to one industry.
- **Industry/sector-specific variants** — use cases whose logic is meaningful only
  inside a sector (e.g. Retail Basket & Category Cross-Sell, Last-Mile Delivery,
  manufacturing OEE).

A now-closed branch (`enhance-factsheets-quality`) proposed an "industry-variant
tier" for exactly this, but bundled *net-new governance* (a new ID taxonomy, new
KPI namespaces, new action codes) with auto-generation off the branch. The
self-contained parts were salvaged; the tier itself was **deferred** in
[`KNOWN_GAPS.md`](../../../internal/project_mgmt/KNOWN_GAPS.md) §7 with four
prerequisites. Prerequisite **#4** is explicit:

> **Taxonomy decision** — the `EXT`/`IND-R/L/M` infix and `core/usecases/industry/`
> tree are an architectural choice that should be ratified (ADR or strategy index)
> before the directory convention is committed.

This ADR is that ratification. It decides **identity and foldering only**; it does
**not** loosen any Golden Thread rule.

## Decision

**Adopt a two-axis extension taxonomy on top of the governed `XXX` domain prefix.
Extension use cases are new *identifiers and folders within the existing schemas* —
they introduce no parallel governance mechanics.**

Five rules:

1. **Two ID forms alongside core `XXX-NNN`.**
   - `XXX-EXT-NNN` — **cross-industry extension** (sector-agnostic): e.g.
     `COM-EXT-001` Customer Segmentation / RFM, `FIN-EXT-001` Budget Variance.
   - `XXX-IND-<S>NNN` — **industry/sector-specific**, where `<S>` is a single
     uppercase **sector letter** (see registry below): e.g. `COM-IND-R001` Retail
     Basket & Cross-Sell, `SCM-IND-L001` Last-Mile, `OPS-IND-M001` OEE.

   `XXX` stays the governed domain (`COM`, `FIN`, `OPS`, `SCM`, `XD`); `NNN` is a
   zero-padded sequence scoped to its `(domain, tier[, sector])` namespace.

2. **One folder tree per tier**, sibling to the existing `core/` tier:
   | Tier | Folder | ID form |
   |---|---|---|
   | Core (governed-16) | `core/usecases/core/<ID>_<Title>/` | `XXX-NNN` |
   | Cross-industry extension | `core/usecases/extended/<ID>_<Title>/` | `XXX-EXT-NNN` |
   | Industry/sector-specific | `core/usecases/industry/<sector>/<ID>_<Title>/` | `XXX-IND-<S>NNN` |

   `<sector>` is the full lowercase word (`retail`, `logistics`, `manufacturing`);
   `<S>` in the ID is its first letter. Directory shape per use case (bracket +
   prose factsheet) is identical across tiers.

3. **Sector-letter registry (this ADR is its home).** A letter maps to exactly one
   sector; extend the table by adding a new ADR-amending row, never by reusing a
   letter.
   | Letter | Sector |
   |---|---|
   | `R` | Retail |
   | `L` | Logistics |
   | `M` | Manufacturing |

   (R/L/M are the sectors named by the §7 epic; future letters are added here.)

4. **The Golden Thread is unchanged.** EXT/IND use cases reference governed KPIs,
   action codes, and decision spines exactly like core use cases, through the same
   `UseCase_Bracket.yaml` schema and the same referential-integrity gate
   (`registry_builder.py`). New KPIs live in `core/kpi_catalog/` under the existing
   `domain.topic.metric` convention (new namespaces such as `retail.*`,
   `customer.rfm.*` are allowed and recorded in `KPI_Taxonomy.md`); new action
   codes live in `core/action_codes/<Domain>/` under the existing
   `<DomainLetter>-<Theme><Group>.<Seq>` scheme. **No new schema, no new validator,
   no new namespace authority** is created by this tier.

5. **Deliberate authoring, not generation — with a draft→final lifecycle.** Each
   extension use case is authored to pass the same gates as a core use case (its
   KPIs, action codes, and spine map entry must exist first). While it is still being
   worked out it carries `governance.status: draft` and its reference checks are
   advisory; it is promoted to `active` (final) only once it passes the full gate
   (see *Lifecycle gate* below). Tiers are never bulk-generated off an external branch.

## What this ratifies vs. defers

- **Ratified now:** the ID forms, the folder trees, the sector-letter registry, and
  the principle that the tier is *identity + foldering within existing schemas*.
- **Still gated by §7 prerequisites #1–#3** (per use case, not by this ADR): the
  referenced KPIs, action codes, and `DecisionSpine_UseCase_Map.yaml` entries must
  be authored before a given UC turns green. This ADR does not pre-author them.
- **First instantiation:** `COM-IND-R001` (Retail Basket & Category Cross-Sell) is
  built as the proof slice under this taxonomy; the other five §7 use cases follow
  deliberately.

## Lifecycle gate — draft vs. final

A new use case is rarely born complete: the team first works out *how to serve it
optimally*, and only then does the **data need** — and from it the **evidence
grain** — become clear. The gate therefore keys off `governance.status` in the
bracket:

| `governance.status` | Meaning | Referential / evidence-grain / org-role checks |
|---|---|---|
| absent or `active` | **final** (governed) | **ERROR** — full Golden Thread enforcement |
| `draft` | in elaboration | **advisory (WARN)** — parkable, still scanned & inventoried |
| `deprecated` | retired | advisory |

Structural/schema validity (well-formed bracket, valid ID, required fields) is
enforced in **every** state — only *reference resolution* is relaxed for drafts. A
half-formed use case can therefore live in the repo (visible in the inventory and
the reference graph) without breaking the build, while every *final* use case stays
strictly governed. `registry_builder` is the single enforcer; it scans all tiers
(no blanket `extended/industry` skip) and applies the gate by status.

**Evidence-grain workflow (draft → final).** When a use case is finalized, derive
its evidence grain from the worked-out data need:

1. If an **existing governed fact** already serves the need — directly, or via a
   non-breaking rebuild that does not change other use cases — reference it (as
   `COM-IND-R001` does with `invoice_line` from `fact_sales`).
2. Otherwise introduce a **new governed fact table** in the relevant data contract,
   so the grain is always backed by a **clean star schema** rather than an ungoverned
   ad-hoc grain. A final use case may only reference a grain a contract guarantees.

This is enforced mechanically: an ungoverned `evidence_grain` is an **ERROR** on a
final use case but only a **WARN** on a draft — the draft can name its target grain
before the supporting fact exists, then must govern it to go final.

## Consequences

**Positive**
- Industry intent is legible in the identifier itself — a reader sees `COM-IND-R001`
  is a retail-specific commercial use case without opening it.
- The extension tiers scale to customer demand without polluting or renumbering the
  governed core-16.
- Zero new governance surface: existing schemas, validators, and the Golden Thread
  gate cover the new tiers unchanged, so a reviewer audits them the same way.

**Negative / cost**
- The sector-letter registry is a small standing maintenance item (collision
  avoidance lives in this ADR).
- New KPI namespaces (`retail.*`, `customer.rfm.*`, …) risk sprawl if not curated;
  `KPI_Taxonomy.md` must stay honest as they are added.
- More IDs to govern; `UseCase_Inventory.md` and the `core/usecases/` index must
  list the new tiers.

**Neutral**
- `NNN` sequences restart per tier/sector namespace, so `COM-001` (core) and
  `COM-IND-R001` (retail) coexist without collision — the tier infix is part of the
  key.

## Alternatives considered

- **Overload core `XXX-NNN` numbering** (e.g. give Retail Cross-Sell `COM-005`).
  Rejected: hides industry intent, conflates governed-core with long-tail variants,
  and forces renumbering as sectors grow.
- **A separate repo / catalog per industry.** Rejected: breaks the shared Golden
  Thread — KPIs, action codes, and spines are deliberately one catalog; forking
  them per industry recreates the drift this library exists to prevent.
- **Tags/metadata only, no ID infix.** Rejected: the ID is the primary key across
  brackets, decision-spine maps, scorecards, and factsheets; encoding tier/sector
  in metadata alone makes cross-artifact linkage and foldering ambiguous.

## References

- Internal: [`../../../internal/project_mgmt/KNOWN_GAPS.md`](../../../internal/project_mgmt/KNOWN_GAPS.md) §7,
  [`../../../core/usecases/README.md`](../../../core/usecases/README.md),
  [`../../../core/kpi_catalog/KPI_Taxonomy.md`](../../../core/kpi_catalog/KPI_Taxonomy.md),
  [`../../../core/action_codes/README.md`](../../../core/action_codes/README.md),
  [`0001-pluggable-validation-backends-and-capability-tiers.md`](0001-pluggable-validation-backends-and-capability-tiers.md)
