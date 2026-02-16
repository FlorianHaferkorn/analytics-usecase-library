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

## Final Rule

> If a page technically works but fails one DoD check,
> it is **not** considered done.

