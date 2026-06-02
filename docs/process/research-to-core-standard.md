# Research-to-Core Standard

> **Version:** 1.0  
> **Status:** Active  
> **Authority:** Framework Architect / Use Case Governance  
> **Related files:** `docs/process/research-to-core-checklist.md` | `docs/process/domain-evidence-pack-spec.md`

---

## Purpose

Every standard use case must be grounded in deep domain evidence before any Core content is written or changed.
This standard defines the mandatory research process, source requirements, scoring rules, and extraction model.
It applies to humans and AI agents equally.

**Cardinal Rule:** Research outputs never mutate Core schemas directly. Any schema gap must follow the Schema Gap Decision Protocol before implementation.

---

## 1. Source Requirements

### 1.1 Quantity

| Tier | Standard Use Case | Lightweight / Sub-Use Case |
|------|------------------|---------------------------|
| Target | 15 sources | 10 sources |
| Minimum | 10 sources | 6 sources |

A use case below minimum cannot progress to Core content update.

### 1.2 Required Source Mix

Every use case must include sources from at least **5 of the 6 categories** below.
"Standards & Frameworks" and "Benchmark / Target" are mandatory for any standard use case.

| Category | ID | Description | Examples |
|----------|----|-------------|---------|
| Standards & Frameworks | `STD` | Established industry standards, process frameworks | ISO 22400 (OEE), SCOR, APQC PCF, IFRS, COGS definitions |
| Academic / Systematic Literature | `ACA` | Peer-reviewed papers, meta-analyses, systematic reviews | IEEE, IJPR, ORMSE journals; Google Scholar |
| Professional Bodies | `PRO` | Trade associations, industry bodies, certification bodies | APICS, Gartner, CSCMP, AFP, IMA |
| Benchmark / Target Sources | `BNK` | Industry benchmarks, target ranges, best-in-class data | OEE industry baseline 85%, DSO benchmarks by sector |
| Practitioner / Implementation | `IMP` | Case studies, practitioner guides, consulting playbooks | McKinsey, Deloitte, lean manufacturing guides |
| Anti-Pattern / Risk | `RSK` | Common misinterpretations, failure modes, wrong KPIs | "OEE theater" papers, gaming DSO by factoring |

### 1.3 Source Quality Requirements

Each source must be:
- Publicly identifiable (URL, DOI, ISBN, or named publication)
- No older than 10 years (exceptions allowed with written justification for classic references, e.g., ISO standards)
- Independent from the project team

---

## 2. Source Scoring

Score each source on five dimensions (1–3 per dimension, max 15):

| Dimension | 1 | 2 | 3 |
|-----------|---|---|---|
| **Authority** | Blog / opinion | Trade publication / known consultancy | ISO standard / academic journal / industry body |
| **Recency** | >10 years | 5–10 years | <5 years |
| **Domain Relevance** | Adjacent domain | Overlapping domain | Direct domain match |
| **Independence** | Vendor / product-affiliated | Practitioner without affiliation claim | Academic / standards body / independent benchmark |
| **Content Role** | Context only | Supports one of: KPI, driver, action, benchmark, risk | Directly defines or quantifies KPI / driver / action / benchmark / risk |

**Minimum source score:** 8/15 per source included in the evidence pack.  
**Portfolio score:** Sum of all source scores divided by source count ≥ 10/15 for the use case to proceed.

---

## 3. Extraction Model

The extraction model defines what must be pulled from the source inventory and structured into the Domain Evidence Pack.

### 3.1 Mandatory Extraction Fields

| Field | Description |
|-------|-------------|
| `process_scope` | Which business process does this use case govern? (e.g., "Discrete manufacturing OEE on shopfloor assets") |
| `outcome_kpis` | Top-level KPIs that define success or failure (e.g., OEE %, GM %, DSO days) |
| `driver_kpis` | Second-level KPIs that causally explain outcome KPI movement (e.g., Availability %, Gross Margin %, Receivables Turnover) |
| `diagnostic_kpis` | Third-level KPIs for root cause drill-down (e.g., MTBF, MTTR, Changeover Time, Scrap Rate) |
| `guardrails` | KPIs or conditions where the action must NOT be triggered (e.g., quality qualification runs, planned shutdowns) |
| `required_dimensions` | Dimensions needed to slice the outcome and driver KPIs meaningfully (e.g., plant, line, shift, product, cause code) |
| `required_grain` | Minimum data granularity for meaningful decisions (e.g., line-day minimum, line-shift preferred) |
| `actions_by_root_cause` | For each driver / diagnostic combination: what action, when, who (action code logic seed) |
| `wrong_interpretations` | Documented common misreadings of KPIs in this domain (feeds Risk section of factsheet) |
| `benchmark_targets` | Industry-standard benchmark ranges or targets with source citation |
| `evidence_sources` | Numbered source inventory with score, category, URL/DOI, and which extraction fields it supports |

### 3.2 Optional Extraction Fields

| Field | Description |
|-------|-------------|
| `causal_chain` | Explicit cause → driver → outcome path (for value driver model) |
| `seasonality_patterns` | Known seasonal or cyclical effects on KPIs |
| `leading_indicators` | KPIs that predict outcome movement before it appears |
| `reporting_cadence` | Domain-expected decision frequency (daily, weekly, monthly) |
| `cross_use_case_links` | Other use cases that share KPIs or actions (impact scope) |

---

## 4. Process Flow (Step by Step)

### Step 1 — Scope the Domain

Define the business process, industry segment, and any domain constraints (manufacturing vs. service, B2B vs. B2C, regulatory environment).
Select the applicable domain frameworks (SCOR, APQC PCF, ISO, etc.).

### Step 2 — Build the Source Inventory

Target 15 sources across the required mix.
Score each source. Reject any below score 8.
Document URL, date accessed, and which extraction fields the source supports.

### Step 3 — Run the Extraction

For each source, extract all applicable fields from Section 3.1.
Consolidate into a single Domain Evidence Pack per use case.
Where sources conflict, document the conflict and justify the chosen position.

### Step 4 — Produce the Canonical Domain Model

Summarise the extraction into a one-page domain model containing:
- Driver tree (outcome → driver → diagnostic KPIs with causal direction)
- Required grain and dimension set
- Top 3–5 action patterns with trigger conditions
- Top 3 wrong interpretations / guardrails

### Step 5 — Map to Existing Core Artifacts

For each piece of evidence, check whether it can be expressed in existing Core schemas:
- Does a KPI entry already exist?
- Does the Factsheet already cover the business question?
- Does the Bracket support the required visual or evidence column?
- Does the semantic model already have the required fact/dimension/grain?

Classify every mismatch (see Phase 3 — Gap Classification).

### Step 6 — Apply the Schema Gap Decision Protocol

For any `schema_gap` classification, stop and produce a Schema Gap Report before implementation (see `domain-evidence-pack-spec.md`).
For all other gap types, proceed with Core content updates.

### Step 7 — Update Core Content

Apply only changes that existing schemas support.
Reference the Domain Evidence Pack as justification in Factsheet and Bracket.
Do not add fields to Core schemas without an approved Schema Gap Report.

### Step 8 — Validate

Run Stage 1, Fabric checks, and the Semantic Quality Gate before declaring the use case evidence-complete.
Produce the Aurora Proof Dossier for any showcase-scope use case.

---

## 5. Governance

| Role | Responsibility |
|------|---------------|
| Use Case Author | Build source inventory, run extraction, produce canonical domain model |
| Framework Architect | Approve any schema gap proposal before implementation |
| AI Agent | Execute Steps 1–8 according to this standard; flag schema gaps; never silently add schema fields |
| Reviewer | Validate source scores, extraction completeness, and gap classification |

---

## 6. Tool-Agnostic Checklist Reference

See `docs/process/research-to-core-checklist.md` for the step-by-step checklist suitable for agents and human authors.

---

## 7. Related Standards

| Document | Purpose |
|----------|---------|
| `docs/process/domain-evidence-pack-spec.md` | Evidence pack artifact shape, schema gap decision protocol |
| `docs/process/gap-classification.md` | Gap types, criteria, and escalation rules |
| `docs/process/semantic-quality-gate.md` | Semantic validation checks and scoring |
| `AGENTS.md` | Cardinal rules for all agents (this standard is an extension) |
