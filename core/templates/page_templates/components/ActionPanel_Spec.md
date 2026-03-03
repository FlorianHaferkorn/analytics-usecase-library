# Action Panel Spec – Page Templates

The Action Panel is an optional, standardized component used to support **prescriptive analytics**.
Its purpose is to reduce “analysis paralysis” by translating insights into **concrete, owned actions**.

**Golden rule**

- The full Action Panel is designed for **T4 – Prescriptive Recommendation** pages.
- T1–T3 pages may only use an **Action Teaser** (short, non-interactive) to avoid turning monitoring pages into task managers.

---

## Phase 1 vs Phase 2 (Implementation)

**Phase 1 (current):** Content is built **at scaffold/build time** from Action Code YAML only. The panel is rendered as a textbox (or structured text blocks) with name, owner, trigger condition, impact summary, and steps from the Bracket's `orchestration.action_code_ids`. There is **no execution** from the report: no "Execute" button, no calls to `execution_bridge` or external APIs/Webhooks. See [Recommendation_to_Execution_Research.md](../../../action_codes/Recommendation_to_Execution_Research.md) for the two-phase approach and Human-in-the-Loop for execution.

**Phase 2 (future):** The panel may be driven by a **semantic model table** (e.g. `ActionRecommendation`) with fields such as ActionCodeId, ActionTitle, OwnerRole, TriggerCondition, Recommendation, ExpectedImpact, etc., populated by a trigger-evaluation pipeline/job. The report would filter by context. **Execution** (API/Webhook, task assignment) is Phase 2 only and must go through a central layer with approval and audit; it is not implemented from Power BI in Phase 1.

---

## 1) When to Use the Action Panel

### Mandatory (T4)

Use the Action Panel when:

- `template = T4`
- `slots.needs_prescriptive = true`
- the use case defines at least one **Action Code** (owner + trigger + recommended steps)

### Optional (T1–T3 Teaser)

T1–T3 pages may show an Action Teaser only when:

- there is a clear “next step” signal (e.g., threshold breach, repeated deviation)
- the owner is known (role/team)
- the teaser links to the T4 page or a detail section that contains the recommendation

Not allowed on T1–T3:

- multi-step action workflows
- action scoring/prioritization
- assigning tasks or tracking completion (out of scope for Power BI)

---

## 2) Component Variants

### Variant A — Action Panel (Full)

**Allowed pages:** T4 only  
**Placement:** Right-side panel (fixed width, collapsible)  
**Behavior:** Updates with current filter context

### Variant B — Action Teaser (Light)

**Allowed pages:** T1, T2, T3 only  
**Placement:** Top-right callout or slim right column (non-scroll heavy)  
**Behavior:** Minimal text + link to recommendation

---

## 3) Data Contract (Inputs)

**Phase 1:** The panel does not read from a table; it displays text generated from Action Code YAML at build time.

**Phase 2 / target:** The Action Panel can read from a curated, governed structure (table, view, or semantic model table).

### Required fields (minimum viable)

- `ActionCodeId` (text, unique)
- `ActionTitle` (text)
- `ActionCategory` (text) — e.g., Pricing, Assortment, Service, Compliance
- `OwnerRole` (text) — who is accountable
- `TriggerType` (text) — e.g., threshold_breach, trend_deviation, outlier_detected
- `TriggerCondition` (text) — human-readable condition (not DAX)
- `Recommendation` (text) — what to do
- `ExpectedImpact` (text) — qualitative or quantified
- `ConfidenceLevel` (text) — low | medium | high
- `Priority` (number) — 1 (highest) .. 5 (lowest)
- `ValidFrom` (date)
- `ValidTo` (date, nullable)
- `IsActive` (boolean)

### Optional fields (recommended)

- `KpiId` (text) — link to KPI catalog
- `UseCaseId` (text)
- `EvidenceSummary` (text) — why this action is suggested
- `EvidenceMetrics` (text/json) — key numbers used
- `LastUpdatedAt` (datetime)
- `ActionLink` (text/url) — deep link to process documentation / ticket template

---

## 4) Output Requirements (What the User Sees)

### Full Action Panel (T4)

The panel must show, in this order:

1. **Top Recommendation**
   - ActionTitle
   - OwnerRole
   - Priority
   - ConfidenceLevel
2. **Why (Evidence)**
   - short EvidenceSummary
   - 1–3 supporting metrics (no long tables)
3. **How (Steps)**
   - 3–6 bullet steps (plain language)
4. **Impact**
   - ExpectedImpact (range or qualitative)
5. **Controls (optional)**
   - “Show alternatives” (expand/collapse)
   - “Open process link” (if ActionLink exists)

### Action Teaser (T1–T3)

- 1 line summary: “Recommended next step: …”
- OwnerRole
- Link/button: “View recommendation” (navigates to T4)

---

## 5) Governance Rules (Non-Negotiable)

- The Action Panel must never suggest actions without an accountable owner role.
- Recommendations must be based on governed Action Codes (no free-form “AI suggestions”).
- Trigger conditions and recommendations must be derived from Action Codes; no new decision logic is allowed here.
- If `IsActive = false` or outside ValidFrom/ValidTo, the action must not appear.
- The Action Panel must respect RLS/OLS. If data is not visible, recommendations must not leak information.
- Keep it short: the panel must fit without excessive scrolling.

---

## 6) Template Integration

### Mapping Flags

Use case mapping must declare:

- `needs_action_panel: true|false`
- `slots.needs_prescriptive: true|false`

Rules:

- If `slots.needs_prescriptive = true` ⇒ template must be `T4`
- If `needs_action_panel = true` on T1–T3 ⇒ only the **Action Teaser** is allowed

---

## 7) Design Rules

- Minimal, iOS-like clarity (no heavy borders, no dense UI)
- Emphasize the “one best next action”
- Avoid more than 3 alternatives by default
- Do not use red/green as the only signal (use labels + icons in Power BI theme)

---

## 8) Definition of Done

- Action Panel shows the correct action(s) for the current context
- Action Panel does not appear when no valid action exists
- Evidence is understandable in under 10 seconds
- Navigation to detail/recommendation works
- Works with RLS and export does not leak restricted details


