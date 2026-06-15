# Framework v1.0 — Open Backlog & Review Pipeline

**Purpose.** Document all items identified in the CEO readiness review that are **not covered** by PR #243 (Week 1–8 execution plan).
**Why.** PR #243 delivers the technical core of v1.0 (Lean Core, Golden-Thread drift gate, action-outcome loop, Studio forge/registry split). But a production rollout to a real mid-size customer requires more than code. This document captures what is missing so it does not get lost after the v1.0.0 tag is cut.

**Reading order.**
- **Section A — Core Blockers** must be closed **before** we market v1.0 as production-ready.
- **Section B — Go-to-Market Blockers** are non-code workstreams that must be closed before a CEO will sign.
- **Section C — Post-Launch** captures deferred scope for v1.1+.
- **Section D — Review Pipeline** lists the reviews we still owe ourselves.

Every item has: owner role, acceptance criteria, and an estimated effort band (S ≤ 3d, M ≤ 2w, L ≤ 6w).

---

## Section A — Core Blockers (must be shipped BEFORE first paying pilot)

These are substance gaps in the framework itself. Leaving them open means the product is demo-ready but not production-ready for a mid-size customer.

### A1. Source-system connector framework + one reference adapter (SAP) — L

**Why.** No mid-sized customer will sign without a credible story for getting data **out of** SAP, DATEV, Salesforce, or their ERP. The current pipeline assumes gold-layer Parquet already exists. That's a 60 %-of-budget integration problem we currently hand-wave.

**Acceptance criteria.**
- `tooling/connectors/` package with an `Adapter<Source, ParquetSink>` interface (extract → land in bronze/silver → promote to gold).
- **One working reference adapter: SAP ECC / S/4** (RFC or OData) pulling at least `VBAK/VBAP` (sales), `BKPF/BSEG` (GL), `MARA/MBEW` (materials) into the Aurora `fact_sales`, `fact_gl_journal`, `fact_inventory` contracts.
- Pluggable via Studio plugin registry (`studio/plugins/`) using the existing plugin manifest.
- CI smoke test: connector `validate()` runs against a mock SAP service on every PR.
- Docs: `products/connectors/sap/README.md` with wiring recipe.

**Owner.** BI Lead + Data Engineer.

### A2. Excel export & refresh loop — M

**Why.** 70 % of the customer org will live in Excel regardless of what we build. Without Excel we will lose adoption in weeks 3–8 of any pilot.

**Acceptance criteria.**
- Studio `(studio)/steering/` export button produces an `.xlsx` with:
  - one tab per KPI card on the current page,
  - one tab per Detail matrix,
  - one `_Actions` tab with current action-code recommendations.
- Excel file contains a refresh connection pointing back to the Fabric dataset (via Power BI analyze-in-Excel URL or direct XMLA).
- Round-trip test: refresh the xlsx, confirm values match Fabric within tolerance.

**Owner.** BI Lead.

### A3. CEO business-case template + per-KPI ROI presets — S

**Why.** The simulator exists; a CEO-grade business-case narrative does not. Without a one-pager per use case ("what is this worth to me?") we have no sales leverage and no internal justification tool.

**Acceptance criteria.**
- `core/templates/business_case/BusinessCase_Template.md` with sections: baseline, target, action-code lever, expected € impact, confidence, time-to-value.
- For each Golden-20 KPI: a preset YAML `core/templates/business_case/presets/<kpi_id>.yaml` with sensible default ranges (min / likely / max) derived from the existing simulator's value-driver model.
- Studio `(forge)/blueprint/` renders the business case preview from the preset when the user selects a KPI.
- Export: one-click PDF of the business case for the CEO pack.

**Owner.** CDAO (content) + BI Lead (template plumbing).

### A4. Multi-tenancy foundation in Studio — M

**Why.** Even on-prem pilots will need project/workspace isolation the moment a second department joins. Retrofitting multi-tenancy after the schema is populated is painful.

**Acceptance criteria.**
- `project_id` column required on all tables that currently default to `"default"` (catalog items, approvals, drafts, audit_chain).
- Every API route enforces the current user's membership of the requested `project_id` via middleware — not per-handler checks.
- `auth/config.ts` issues JWT claims that include `project_memberships[]`.
- Switcher UI in the Studio header.
- E2E test: user A in project X cannot read project Y's brackets.

**Owner.** Studio Lead.

### A5. Vendor-continuity dossier — S

**Why.** A mid-size CEO will ask "what happens if your team is hit by a bus?". No amount of code quality substitutes for a credible answer. This is table stakes for enterprise procurement.

**Acceptance criteria.**
- `internal/continuity/` folder containing:
  - **Architecture overview** (system context, data flow, dependency list with license + maintainer).
  - **Runbook** (how to deploy, how to rotate credentials, how to regenerate a showcase from scratch).
  - **Handover guide** (what a new engineer needs to read, in what order, to be productive in 2 weeks).
  - **Escrow-readiness checklist** (what belongs to the customer if we disappear: KPI catalog, action codes, brackets, generator code, schemas).
- Signed-off by a second engineer not involved in original development (rotation test).

**Owner.** BI Lead + Data Steward.

### A6. Action-outcome reconciliation — S

**Why.** Week 5 wired the `fact_action_outcome` table and the XD-004 measures. But there is no end-to-end **reconciliation** showing "Action C-M2.1 was triggered on date D, KPI `margin.gm.pct` moved from X to Y within the 14-day success window." Without that we can claim the loop is closed but cannot prove it.

**Acceptance criteria.**
- New DAX measure `[Action Effectiveness Delta]` per action code joining trigger time, outcome window, baseline KPI, realized KPI.
- New validator `tooling/generator/validation/check_action_outcome_reconciliation.py` that asserts: every executed action in `fact_action_outcome` has an observable KPI delta (non-null, within window) for the action's `outcome_kpis`.
- Validator wired as a new CI gate.
- One-page demo in Aurora proving the loop on at least 3 of the Impactful-15 action codes.

**Owner.** BI Lead.

---

## Section B — Go-to-Market Blockers (non-code workstreams)

These do not ship in a PR but must be closed before signing the first paying customer.

### B1. Reference customer — L

- Identify one mid-size customer (ideally manufacturing or supply-chain heavy) for a paid pilot with consent to be named.
- Written case study at the end of the pilot: baseline pain, which Golden-20 KPIs were instrumented, which Impactful-15 action codes fired, what € impact was measured.
- Reference call availability for future prospects.

### B2. Managed SaaS offer — L

- Hosted Studio on EU-region infrastructure (Azure West Europe or equivalent).
- SSO via Azure AD (OIDC), Google Workspace, and one generic SAML.
- Billing: Stripe metered on top-level Studio workspaces + KPI-catalog size.
- SLA tier definition (95 / 99 / 99.9 %) with price points.
- Status page.

### B3. DSGVO / compliance package — M

- Auftragsverarbeitungsvertrag (AVV) template covering Studio-hosted and on-prem deployments.
- Records of processing (Verzeichnis von Verarbeitungstätigkeiten).
- EU-only data residency guarantee with infrastructure evidence.
- Löschkonzept (retention & deletion policy) including audit-chain rows.
- ISO 27001 gap analysis (not full certification — just where we stand).

### B4. Enablement & training programme — M

- 4-hour CDAO onboarding: strategy → blueprint → Golden-20 selection.
- 8-hour BI Lead curriculum: bracket authoring, generator ops, drift debugging, MCP tools.
- 4-hour Data Steward curriculum: registry, approvals, drift triage, KPI catalog stewardship.
- Video library covering each of the above, plus the 300-second Aurora demo.
- Certification path (basic / advanced) — optional in v1.0, required if we productize training later.

---

## Section C — Post-Launch Roadmap (v1.1+)

Defer, but track here so they do not get lost.

| # | Item | Trigger to activate |
|---|---|---|
| C1 | Mobile Executive App (3-s layer only) | After first CEO-level user actually asks for it on a phone |
| C2 | Industry benchmark service (my OTIF vs. peer median) | After 3 paying customers agree to anonymized pooling |
| C3 | ML anomaly detection on Golden-20 | After we have ≥ 18 months of stable data per KPI |
| C4 | Penpot/Figma layout bridge activation | When a customer wants custom UX beyond templates |
| C5 | dbt-core adapter | When a customer asks for dbt instead of TMDL |
| C6 | Databricks adapter | When a customer is Databricks-native |
| C7 | Natural-language KPI query ("show me margin erosion last quarter") | After the MCP write surface is stable |

---

## Section D — Outstanding Reviews

Technical merges unblock go-live, but several reviews still owe us signal. Schedule them **before** the first external pilot.

### D1. Security review — priority P0

**Scope.**
- OWASP Top-10 on Studio (auth, authz, input validation, CSRF, SSRF, path traversal in YAML writer).
- Secret handling (current `.env` pattern must move to Vault/AWS SM before SaaS).
- RBAC enforcement audit: every API route has a role guard or an explicit public-route marker.
- MCP write tools: input sanitization on `create_bracket`, `publish_draft`, `run_generator`.
- Dependency audit (`npm audit`, `pip-audit`), license audit (no GPL-family in runtime path).
- Pentest (external) on hosted Studio before SaaS launch.

**Deliverable.** SEC-REVIEW-v1.md with findings + mitigations + reopen dates.

### D2. DSGVO / data-protection review — priority P0

**Scope.**
- PII flow audit: where does customer data enter the gold layer; is any of it unnecessarily persisted in the Studio DB.
- Right-to-deletion: can we guarantee a hard delete across fact_action_outcome, audit_chain, approvals.
- Anonymization posture of the Aurora showcase (names, customer IDs).
- Consent and purpose-limitation documentation for any AI calls (e.g., `/api/ai/chat`).

**Deliverable.** DSGVO-REVIEW-v1.md signed off by an external DPO.

### D3. UX review with real personas — priority P1

**Scope.**
- Three 60-min moderated sessions: one CDAO, one BI Lead, one Data Steward (ideally external, not framework authors).
- Tasks: (a) pick Golden-20 for a new company; (b) author a bracket; (c) triage a drift alert.
- 3-30-300 test: can an executive read the Aurora overview in 30 seconds and articulate one action?

**Deliverable.** UX-REVIEW-v1.md with top-10 usability issues prioritized.

### D4. Performance & scalability review — priority P1

**Scope.**
- Orchestrator regeneration time for 15 reports: current vs. target (< 3 min end-to-end).
- Studio response time for `/registry` with 500+ catalog items.
- Fabric dataset refresh duration with full Aurora gold layer.
- Parallelization of `validate_bindings` across domains (already matrix'd in CI, confirm behavior holds at 50+ reports).

**Deliverable.** PERF-REVIEW-v1.md with baselines + SLOs.

### D5. Accessibility (WCAG AA) review — priority P2

**Scope.**
- Studio routes: keyboard navigation, screen-reader landmarks, color contrast.
- Generated PBIP reports: reader-mode behavior, alt text on KPI cards.

**Deliverable.** A11Y-REVIEW-v1.md.

### D6. Documentation review — priority P2

**Scope.**
- Cold-start test: a new engineer is given only the repo and the internal/continuity/ docs. Can they regenerate Aurora in 4 hours?
- README.md / CLAUDE.md / AGENTS.md consistency audit — no divergent instructions.
- Every CLI script referenced in CLAUDE.md actually exists post-cleanup.

**Deliverable.** DOCS-REVIEW-v1.md with a fix list.

### D7. Business-case / ROI review — priority P1

**Scope.**
- For each of the Impactful-15 action codes: is the expected € impact claim defensible with evidence (case study, public benchmark, academic paper)?
- Sanity check by an independent industry analyst (not the framework authors).

**Deliverable.** ROI-REVIEW-v1.md.

### D8. Post-merge stability review (30 days after v1.0.0 tag) — priority P1

**Scope.**
- Drift-check CI gate: false-positive rate.
- Binding validator: false-positive rate.
- Action-outcome reconciliation: measurement noise vs. signal.
- Any rollback events? Why?

**Deliverable.** STABILITY-30D-REVIEW.md — decides whether v1.0.1 hotfix or v1.1 planning kicks off.

---

## Prioritization summary

| Phase | Items | Timeline |
|---|---|---|
| **Before v1.0.0 tag** | A6 (action-outcome reconciliation) | +1 week |
| **Before first paying pilot** | A1–A5 + D1 + D2 + D3 + D7 | +8 weeks |
| **Parallel to first pilot** | B1–B4 | +12 weeks |
| **Post-pilot** | D4, D5, D6, D8 | +16 weeks |
| **v1.1 planning** | C1–C7 | 2027 Q1 |

---

## Governance

- Owner of this document: **BI Lead + CDAO (dual).**
- Review cadence: monthly steering until v1.0.0 tagged, then bi-weekly during the first pilot.
- Each item moves to `DONE` only after its acceptance criteria are met **and** the relevant review (if any) has signed off.
- New items added here (not in the original 8-week plan) require a short rationale and an owner.

---

_Document created as a companion to `FRAMEWORK_V1_EXECUTION_PLAN.md`. Keep both alive until v1.1 planning._
