# Urgency derivation — tooling hook (spec)

**Purpose:** Spec for a future tooling hook that derives relative urgency from the active strategy pattern and governed artifacts. Implementation is in backlog; this document defines the contract so that strategy pattern and automated-reasoning scope (Epic #6) are precise enough for tooling.

**Authority:** [core/strategy_operating_model/company/strategy_patterns.md](../../core/strategy_operating_model/company/strategy_patterns.md) §8 (Urgency rules for tooling).

---

## Contract (inputs and output)

**Inputs:**

| Input | Type | Source | Description |
|-------|------|--------|-------------|
| `pattern_primary` | string | Config or selection | One of `Margin-First`, `Cash-First`, `Growth-First`. |
| `pattern_secondary` | string (optional) | Config or selection | Second pattern when blending; same enum. |
| `kpi_deviations` | list of KPI IDs (optional) | Bracket/action logic or semantic layer | KPIs currently in deviation or triggering actions. |
| `use_case_ids` | list (optional) | Use case set | Use-case IDs to rank by urgency. |

**Output:**

- **Relative urgency** for the given inputs: e.g. an ordered list (highest urgency first) of use-case IDs, or of (KPI ID / action code ID) pairs, or a numeric tier per item. Exact format is left to the implementation.

**Rules (from strategy_patterns.md §8):**

1. KPI urgency tier = position in the pattern’s “Strategic KPIs (priority order)” (1 = highest).
2. Use-case cluster priority = “Priority” column (1–4) in the pattern’s “Use-case clusters (priority)” table.
3. When blending, primary pattern defines top tiers; secondary adds lower tiers.

---

## Implementation notes

- **Stub:** A script or module could read `strategy_patterns.md` (or an exported JSON/YAML derived from it), resolve pattern → KPI order and use-case cluster order, and return an ordered list or tier map. No stub script is provided in this repo yet; see BACKLOG_GRANULAR “[Task] Add tooling hook for urgency derivation (stub or spec)”.
- **Integration:** Potential callers include report generation (order 300s actions by urgency), recommendation layers, or PM/Assistant tooling (suggest next use case by pattern).
