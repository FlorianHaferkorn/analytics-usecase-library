# Definition of Done (DoD) – Page Templates

A use case is considered "Done" when all requirements below are met.

## 1. Template & YAML
- `UseCase_PageTemplate_Map_3-30-300.yaml` contains:
  - All pages for the Use Case
  - Correct page template (T1–T4)
  - Correct slot configuration
  - Correct 3-30-300 layer assignment
- No slot conflicts (e.g., trend on detail page)

## 2. Visual Standards
- All visuals are from the official Visual Whitelist.
- Slot → Visual mapping follows `PageTemplate_SlotVisual_Map.md`.
- Max 4 visuals per overview page.
- Max 3 slicers per page.
- 3-30-300 is adhered to:
  - Overview page: KPIs + trend + variance + ranking
  - Detail page: matrix + exceptions + root cause

## 3. Factsheet Alignment
- Business Factsheet:
  - Includes `page_template`
  - Lists action codes with relevance
- Technical Factsheet:
  - Includes slot overrides (if any)
  - Action Code triggers documented

## 4. Action Codes
- `UseCase_ActionCode_Map.yaml` contains all assigned codes.
- Action Panel active if needed.
- Trigger levels and impact ranges validated.

## 5. PBIP/TMDL Implementation
- Report page layout matches the YAML specification.
- Navigation (pageNavigator) consistent.
- No local formatting overrides outside theme.

## 6. QA & Performance
- Page renders <2 seconds on Premium capacity.
- All visuals show valid data (no blanks, no errors).
- Filters and drill-down working.
- Matrix export tested.

## 7. Governance
- Changes documented in commit message.
- The template can be regenerated via automation without breaking layout.

This DoD is mandatory for all 73+ Aurora Use Cases.
