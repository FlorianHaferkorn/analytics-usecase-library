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
/// Example question: <example_question>
```

### Visualization tool — compact tooltip (tool-agnostic)

```text
<definition> (<unit>, <good_is> is better). Top drivers: <names>.
```

### Linguistic schema — Copilot / Q&A (`cultures/<culture>.tmdl`)

The first two projections are **description text**. Native Power BI Q&A and Copilot
do not read description prose — they read the model's **linguistic schema**
(`cultures` / `linguisticMetadata`). So a synonym that only reaches `///` is visible
to an LLM *handed the raw TMDL* but invisible to *in-product* natural language.

The third projection closes that gap. Curated column `synonyms` (governed source,
below) are projected into a TMDL `culture` object's `linguisticMetadata` — the
Power BI Q&A linguistic schema (LSDL v1.0.0) — by
[`linguistic_schema.py`](../../products/fabric/powerbi/tooling/linguistic_schema.py)
and referenced from `model.tmdl` via `ref culture <culture>`. It is deterministic
and idempotent (same contract → byte-identical output) and never LLM-generated at
build time.

```tmdl
culture en-US
	linguisticMetadata =
			{
				"Version": "1.0.0",
				"Language": "en-US",
				"Entities": {
					"<table>.<column-slug>": {
						"Definition": { "Binding": {
							"ConceptualEntity": "<table>", "ConceptualProperty": "<column>" } },
						"State": "Generated",
						"Terms": [
							{ "<column>":  { "State": "Generated" } },
							{ "<synonym>": { "Type": "Noun", "State": "Authored", "Source": "User" } }
						]
					}
				}
			}
```

The first term is the object's own name (`Generated`); each curated synonym is an
`Authored` noun. Columns without `synonyms` produce no entity; a domain with no
curated synonyms produces no culture file. Regenerate:
`python3 -m products.fabric.powerbi.tooling.linguistic_schema --domain Commercial`.

> **TMDL keyword:** the object is `culture <name>` (and `ref culture <name>` in
> `model.tmdl`), per the MS Learn TMDL reference and the SpaceParts sample. Current
> TMDL rejects `cultureInfo` as an *Unsupported object type*, so `culture` is the
> only accepted keyword — a Power BI Desktop round-trip is confirmatory only.

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
/// Example question: Why did Gross Margin % drop in Region North last quarter?
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

**Values coverage (B2).** `tooling/validation/check_values_coverage.py` reports which
*enumerable* dimension columns (low-cardinality categorical attributes — text, not a
key/identifier, not high-cardinality) carry `allowed_values`. Aurora Commercial:
`Region`, `Channel`, `Quarter` and the customer-dimension `Region`/`Channel` are
enumerated; the business-governed domains (`Category`, `Subcategory`, `Segment`,
`PromoType`, `Mechanic`) are reported as a gap to be curated — never guessed.
Run `python3 tooling/validation/check_values_coverage.py --domain Commercial`
(add `--strict` to gate).

The curated column `synonyms` are *also* the source for the **linguistic schema**
projection (above): each column with synonyms becomes a bound entity in
`cultures/<culture>.tmdl`, so the same governed source reaches the `///` block, the
viz tooltip **and** in-product Copilot/Q&A. For Aurora Commercial today:
`dim_org.Region → {Sales Region, Geo}`, `dim_org.Channel → {Sales Channel, Route to
Market}`, `fact_sales.Net Sales Amount → {Revenue, Net Revenue, Umsatz}`.

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
- Both generation paths now project the standard: the Python PBIP adapter
  (`_build_tmdl_measures`) emits the rendered block directly, and the PowerShell
  path is covered by the post-generation enricher
  (`tooling/generator/enrich_measure_docs.py`), wired into the orchestrator right
  after measure generation. The enricher rewrites the `///` of any measure that
  resolves to a catalog KPI; non-catalog measures and warning lines are preserved,
  and it is idempotent.
- Action-outcome measures still use `/// Purpose:` and have tests asserting it.
  Once a regeneration enriches them, relax those assertions to accept the rendered
  block (the standard supersedes the literal `Purpose:` keyword).
