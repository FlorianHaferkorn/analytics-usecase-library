# AI Readiness

AI readiness ensures that analytical artifacts can be reliably consumed by assisted analytics, copilots, and agents.

While the Golden Thread defines causal logic and the Operating Model governs its operation, AI readiness ensures that this logic is interpretable, retrievable, and trustworthy for machine-assisted use.
It does not introduce new analytical meaning.
It enables reliable assistance based on existing definitions.

## 1. Role in the Framework

AI readiness is an outcome of explicit structure and governance.

- Strategy, KPIs, and Action Codes define intent and decision logic.
- Semantic models and measures express this logic explicitly.
- Data governance ensures quality, security, and traceability.

AI systems consume these artifacts.
They do not redefine them.

## 2. AI Readiness Principles

AI readiness follows a small set of binding principles.

Grounding is mandatory.
AI interactions are grounded in explicit, governed artifacts rather than generated assumptions.

Quality precedes assistance.
AI consumption is enabled only when data quality and semantic consistency are established.

Security is enforced.
Access, privacy, and compliance requirements apply equally to human and AI consumption.

Retrieval is preferred over generation.
AI systems reference existing definitions and catalogs instead of inventing meaning.

## 3. Normative AI Readiness Standards

AI readiness defines binding standards for machine-assisted analytics.

### 3.1. Grounded Semantics

KPIs, measures, and Action Codes use stable identifiers.
Identifiers link AI interactions to catalogs and semantic models.

### 3.2. Machine-Readable Artifacts

Catalogs, glossaries, and contracts are maintained in structured, machine-readable formats.
Free-text interpretation is avoided where explicit structure exists.

### 3.3. Quality and Validation

Referential integrity, completeness, and semantic consistency are validated before AI consumption.
Detected anomalies or drift are surfaced explicitly.

### 3.4. Security and Access

AI access respects existing security models.
Sensitive data is classified and handled explicitly.
Auditability is preserved.

### 3.5. Guardrails

Known ambiguities, synonyms, and anti-patterns are documented.
Guardrails reduce hallucination risk by constraining interpretation.

### 3.6. Grounding Surface and Retrieval Strategy (ADR-0015)

The OneLake AI-era blueprint makes the *grounding surface* an explicit standard:

- **Agents ground on Gold and Silver data products — never Bronze.** Bronze is the raw
  system of record; it is not a valid input for assisted analytics, copilots, or agents.
  This is a fixed constraint (`ai_grounding.grounding_surface = {gold, silver}` in the
  Architecture Blueprint IR).
- **Retrieval is built-in first, MCP for live/action.** Prefer built-in retrieval
  (governed catalog / data-agent grounding) as the default; use an MCP server only when an
  agent must take an action or read real-time data. Record the choice **per domain**
  (search vs. API/MCP, certified sources, whether auth is required).
- **Emit tool-free grounding.** The grounding manifest (`mcp_grounding.json`) points agents
  at the Gold/Silver products and travels as a plain file — no runtime dependency for the
  consumer (extends the GADW Stage 5 "Prep-for-AI" seam).
- **Adaptive Gold (forward-looking).** Frequently-requested Gold datasets may later be
  materialized from usage telemetry via the Wirkungs-Loop (ADR-0009); off by default until
  a custom telemetry agent exists.

## 4. Assisted Operation

AI assists in operating the framework.

Typical assistance includes:

- impact analysis for changes,
- consistency validation across artifacts,
- generation of derived documentation,
- and guided exploration of analytical structures.

AI does not replace ownership or decision-making.
It accelerates understanding and maintenance.

## 5. Change and Evolution

As analytical logic evolves, AI readiness evolves with it.

Changes to KPIs, Action Codes, semantic models, or contracts update the grounding context.
AI assistance remains aligned with current definitions.

This ensures that automation and assistance scale without accumulating semantic debt.

## 6. Outcome

When AI readiness is established:

- AI assistance is reliable and explainable,
- analytical meaning is preserved across interactions,
- and productivity increases without loss of control.

AI readiness enables scale by making structure consumable, not by automating decisions.

---

## 7. Sources & Grounding

The AI-readiness principles in this document — grounding over generation, quality before
assistance, enforced security and auditability, and documented guardrails — align with
recognized AI risk-management and responsible-AI frameworks, and with industry guidance on
preparing data and analytics for AI consumption. Grounded in:

- **AI risk management** (Govern–Map–Measure–Manage functions; trustworthy-AI characteristics
  including validity, security, accountability, transparency, and privacy that underpin the
  quality, security, and guardrail principles here) — NIST AI Risk Management Framework
  (AI RMF 1.0): <https://www.nist.gov/itl/ai-risk-management-framework> ·
  publication: <https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-ai-rmf-10> ·
  NIST AI Resource Center (AI RMF Core): <https://airc.nist.gov/airmf-resources/airmf/5-sec-core/>
- **Responsible AI standards** (binding goals and requirements for accountability, transparency,
  privacy, and security that mirror this document's security and guardrail principles) —
  Microsoft Responsible AI principles and Standard:
  <https://www.microsoft.com/en-us/ai/principles-and-approach>
- **AI-ready data** (data readiness as a precondition for reliable AI; quality, metadata, and
  governance underpinning the "quality precedes assistance" principle) — Gartner, *AI-Ready Data
  Essentials to Capture AI Value*: <https://www.gartner.com/en/articles/ai-ready-data> ·
  Gartner, *Lack of AI-Ready Data Puts AI Projects at Risk*:
  <https://www.gartner.com/en/newsroom/press-releases/2025-02-26-lack-of-ai-ready-data-puts-ai-projects-at-risk>

> This document does not introduce new analytical meaning; it makes existing, governed structure
> reliably consumable by assisted analytics, copilots, and agents (see §1). The cited frameworks
> motivate *why* grounding, quality, security, and guardrails are mandatory, not the framework's
> specific KPI/Action-Code definitions.
