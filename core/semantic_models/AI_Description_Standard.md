# AI Description Standard

How measure / KPI descriptions are produced for AI consumption. **One governed
source, multiple rendered projections** — descriptions are never hand-written in
the semantic model or the visualization tool; they are *pulled* from the KPI
catalog, the domain measure dictionaries and the data contracts and rendered
into each surface by a single template.

Renderer: [`tooling/generator_core/ai_description.py`](../../tooling/generator_core/ai_description.py)
(`build_description(kpi_id, repo_root)`).

---

## Why structure (not free prose)

LLM agents consume different slices for different tasks: a DAX agent needs the
formula + grain; a narrative agent needs the definition + direction + drivers; a
governance agent needs owner + status. Typed, atomic fields let each task get
exactly its slice, make gaps visible (`Owner: unknown` vs. a guess), and prevent
two diverging copies of the truth. The **information** must be present, atomic and
consistent — the literal field *name* (e.g. "Purpose:") does not matter, which is
why the `validate_measure_metadata` hook accepts any `///` doc line.

---

## Field contract

| Field | Source of truth | Req. | Why it matters for AI |
|---|---|---|---|
| `name` (display) | KPI catalog `kpi_key` | ✅ | the binding key visuals reference |
| `definition` | Measure dict `documentation.description` | ✅ | disambiguates synonyms; 1 sentence |
| `formula` | Measure dict `expression.logical` | ✅ | correct DAX without re-derivation |
| `grain` | Measure dict notes / data contract `grain` | ✅ | prevents aggregation errors |
| `unit` | Measure dict notes / `calc_type` | ✅ | prevents format errors (%, EUR, days) |
| `good_is` | KPI catalog `good_is` (`higher`/`lower`) | ⭐ | variance interpretation, RAG status |
| `drivers` | KPI catalog `causal_links` (id + direction) | ⭐ | "why did it move" narratives |
| `owner` / `status` | Measure dict `governance` | ✅ | trust, routing, attribution |
| `action_codes` | KPI catalog `action_code_ref` | ⭐ | strategy-to-action linkage |
| `synonyms` | KPI catalog `synonyms` | ⭐ | natural-language → measure mapping |
| `example_question` | KPI catalog `example_question` | ⭐ | few-shot grounding |

✅ = required for the depth bar · ⭐ = high-ROI, recommended. `good_is`,
`synonyms` and `example_question` are optional catalog fields (the schema allows
additional properties); the renderer omits any field that is absent — it never
guesses.

---

## Rendered projections

### Semantic layer — TMDL `///` doc block

One line per populated facet, in priority order:

```text
/// <definition>
/// Formula: <dax>
/// Grain: <grain> · Unit: <unit> · Good: <good_is>_is_better
/// Drivers: <name> (<direction>), ...
/// Owner: <owner> · Status: <status> · Actions: <codes>
```

### Visualization tool — compact tooltip (tool-agnostic)

```text
<definition> (<unit>, <good_is> is better). Top drivers: <names>.
```

---

## Aurora worked example — `margin.gm.pct` (COM-001)

Rendered entirely from the governed catalogs (no hand-written text):

**Semantic layer:**

```text
/// Gross margin divided by net sales.
/// Formula: (Net Sales Amount - COGS Amount) / Net Sales Amount
/// Grain: month (aggregated from invoice_line) · Unit: % · Good: higher_is_better
/// Drivers: Net Sales Amount (positive), Cost of Goods Sold Amount (negative), Net Sales % vs Plan (positive)
/// Owner: Profitability Analytics · Status: active · Actions: C-M2.1, C-M2.2, C-S1.1
```

**Viz tooltip:**

```text
Gross margin divided by net sales (%, higher is better). Top drivers: Net Sales Amount, Cost of Goods Sold Amount, Net Sales % vs Plan.
```

---

## Tables & columns (data contracts)

The same principle applies to tables and columns — and for natural-language
querying (text-to-DAX, data agents) **column context is the single biggest
lever**: an agent maps "sales in the north" to a column only if it knows the
column's meaning, its allowed values and its synonyms. Source of truth: the
data contracts (`core/data_contracts/domains/*.yaml`).

### Table field contract

| Field | Source | Req. | Why for AI |
|---|---|---|---|
| `description` + `purpose` | contract table | ✅ | what the table holds and is for |
| `grain` | contract `grain` | ✅ | safe joins / aggregation |
| `kind` (fact/dimension) | inferred from name/grain | ✅ | query planning |

### Column field contract

| Field | Source | Req. | Why for AI |
|---|---|---|---|
| `description` | contract column `description` | ✅ | what the column means |
| `data_type` + `unit` | contract `type` (`currency`→EUR) / `unit` | ✅ | format & aggregation |
| `role` (key/foreign_key/measure/attribute) | inferred from `role`/`agg`/`ref` | ✅ | join vs. group vs. aggregate |
| `ref` (FK target) | contract `ref` | ⭐ | relationship grounding |
| `allowed_values` | contract `allowed_values` | ⭐ | **NL → column value mapping** |
| `synonyms` | contract `synonyms` | ⭐ | NL phrasing → column |

### Render — column TMDL `///`

```text
/// <description>. Type: <type> · Unit: <unit> · Role: <role> · FK-><ref> · Values: <a, b, ...> · Synonyms: <...>
```

### Aurora worked example — `commercial_sales`

```text
# fact_sales (table)
/// Invoice-line sales (net sales, quantity, price, COGS) with plan and prior year. Core revenue and margin reporting; PVM and variance analysis. Grain: invoice_line · Type: fact
# columns
/// Invoiced revenue net of discounts and returns. Type: currency · Unit: EUR · Role: measure · Synonyms: Revenue, Net Revenue, Umsatz
/// Sales region grouping countries. Type: text · Role: attribute · Values: DACH, Benelux, Nordics, SouthernEurope, CEE · Synonyms: Sales Region, Geo
/// Go-to-market sales channel. Type: text · Role: attribute · Values: Retail, Online, Wholesale, Marketplace, Outlet · Synonyms: Sales Channel, Route to Market
```

`allowed_values` and `synonyms` are optional contract fields the renderer omits
when absent. Enriching them for the **filter/slicer columns** (region, channel,
category, status) yields the largest NL-querying accuracy gain.

---

## Depth & quality bar

A description meets the bar when the ✅ fields render and the ⭐ fields are
populated for every **strategic** KPI. Missing facets are omitted, not faked —
so a render with gaps is a signal to enrich the *source*, not to write prose into
the model.

## Known follow-ups

- `Gross Margin %` exists in both the Commercial and Profitability measure
  dictionaries; the renderer prefers the use case's domain but the duplicate
  should be de-duplicated (one governed measure per KPI — backlog A4).
- Generators should emit the rendered `///` block instead of bespoke comments, so
  the semantic layer is a projection of this standard rather than a parallel copy.
