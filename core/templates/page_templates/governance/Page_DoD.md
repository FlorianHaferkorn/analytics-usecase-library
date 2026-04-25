# Page Template – Definition of Done (DoD)

A page is considered complete only if **all checks below are fulfilled**.
If one check fails, the page must not be released.

---

## 1. Page Type Compliance

- [ ] Page uses exactly one allowed page type (T1, T2, T3, or T4)
- [ ] Page purpose matches the selected page type
- [ ] Page does not mix multiple page purposes

Reference: page_templates/README.md

---

## 2. Use Case Mapping

- [ ] Use case has a `UseCase_Bracket.yaml`
- [ ] `ux_layout_rules` exists and matches the implemented report pages (overview vs execution)
- [ ] Activated content matches the bracket intent (3s/30s/300s); no extra page purposes are introduced

Reference: `core/usecases/core/<ID>_*/UseCase_Bracket.yaml`

---

## 3. Slot Compliance

For each activated slot:

- [ ] Slot purpose is clearly visible
- [ ] Slot answers a concrete analytical question
- [ ] Slot is allowed for the selected page type

Reference: governance/Slot_Definitions.md

---

## 4. Visual Governance

- [ ] Only whitelisted visuals are used
- [ ] Visuals are allowed for the activated slot
- [ ] Visuals are allowed for the selected page type
- [ ] Scatter/Funnel rules are respected
- [ ] No disallowed visuals are present

Reference: governance/Visual_Whitelist.md

---

## 5. Layer Compliance (3–30–300)

- [ ] Overview pages only contain 3/30 content
- [ ] Detail pages contain 300-level analysis only
- [ ] Detail Matrix appears only on Detail pages

---

## 6. Slicer Rules

- [ ] Maximum of 3 standard slicers used
- [ ] Optional 4th slicer (if any) is a mode switch
- [ ] No slicer is redundant or decorative

---

## 7. Action Readiness (if applicable)

If Action Panel is enabled:

- [ ] Page type is T4
- [ ] Action logic is defined
- [ ] Ownership of actions is clear

Reference: components/action_panel/ActionPanel_Spec.md

---

## 8. Decision Clarity

- [ ] The page answers the core question of its page type
- [ ] Key insight is visible within 30 seconds
- [ ] Next action or interpretation is unambiguous

---

## 9. Decision Question

Every page must have a concrete decision question that frames the reader's intent.

- [ ] `decision_question` is defined in `UseCase_Bracket.yaml` for this page
- [ ] Decision question is ≤ 80 characters (max 120 permitted; 80 is the design target)
- [ ] Decision question is phrased as a business question, not a technical label
  - Good: *"Are we on track for our Commercial targets this month?"*
  - Bad: *"Sales Performance Dashboard"*
- [ ] Decision question is displayed as a visible banner or heading on the page

Reference: `Storytelling_Principles.md §2` · `Content_Quality_Guide.md §5`

---

## 10. Big Idea

The Big Idea is the one-sentence narrative anchor that a reader should be able to state after viewing the page. It is not decorative — it is a testable quality standard.

- [ ] `big_idea` is defined in `UseCase_Bracket.yaml` for this page
- [ ] Big Idea is a single sentence (≤ 300 characters)
- [ ] Big Idea follows the template for the page type:
  - **T1 Strategic:** *"[Domain] is [on/off] track — [KPI] is [Δ] and the [direction] signals [consequence]."*
  - **T2 Tactical:** *"[KPI] is [Δ vs reference] — [primary driver] is the dominant cause."*
  - **T3 Operational:** *"[N] exceptions exceed threshold in [dimension] — [entity/team] requires attention."*
  - **T4 Prescriptive:** *"[Action] in [entity] by [date] will recover [Δ KPI] — owner: [role]."*
- [ ] **30-second test:** A reader unfamiliar with this specific filter context can construct the Big Idea sentence from the page within 30 seconds (10 seconds for T4 detail pages)

The 30-second test is the only objective measure of whether the page design has succeeded. If the test fails, the layout or content must be revised — not the timer.

Reference: `Storytelling_Principles.md §2` · `samples/page_pulse_full.md §Big Idea Verification`

---

## 11. Primary Visual Annotation

Every primary visual (the first visual in Zone 3, slot `Main_1`) must have at least one explicit annotation
marking the single most important finding in the current filter context.

> *"Direct the audience's attention to where you want them to look."*
> — Cole Nussbaumer Knaflic, *Storytelling with Data*, p. 173

- [ ] The primary visual (`Main_1`) has at least one annotation
- [ ] The annotation marks exactly one finding: an inflection point, endpoint, maximum deviation, or threshold crossing
- [ ] The annotation is text-based (callout label or reference line label) — color alone does not qualify
- [ ] The annotated finding corresponds to the Big Idea or the decision question of the page
- [ ] If the current filter context produces no notable finding, the Smart Narrative states this explicitly — the annotation requirement is waived only in this case, and the waiver must be documented in `UseCase_Bracket.yaml` (`ux_layout_rules.annotation_waiver: true`)

Reference: `Storytelling_Principles.md §8` · Knaflic, *Storytelling with Data* (2015), p. 173

---

## Final Rule

> If a page technically works but fails one DoD check,
> it is **not** considered done.

