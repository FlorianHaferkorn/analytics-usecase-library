# Action Panel – Design Specification

The Action Panel is a dedicated space on template-based report pages where recommended business actions (Action Codes) are surfaced.

## 1. Purpose
- Show recommended actions based on KPIs, thresholds, and exception patterns.
- Allow users to move from insight → decision → execution.
- Provide a consistent UX across all use cases.

## 2. Placement in Templates
- T1/T2/T3 (overview pages): right-side panel, collapsible.
- T1/T2/T3 (detail pages): bottom section below matrix.
- T4: primary visual on detail page.

## 3. Trigger Logic
Action Codes are displayed when:
- KPI crosses threshold L1/L2/L3  
- or an exception is detected  
- or a model (T4) emits a recommendation

Integration:
- Logic derived from `UseCase_ActionCode_Map.yaml`.
- UI only shows action codes relevant for the current use case.

## 4. Panel Fields (mandatory)
- Action Code ID (e.g., C-P1.1)
- Short title
- Trigger Level (L1/L2/L3)
- Impact range (min/max)
- Key steps (max 3)
- Effort (Low/Medium/High)
- Risk (Low/Medium/High)

Optional:
- Automation link
- Bookmark to jump to detail

## 5. Visual Composition
- tableEx (2 columns: field, value)
- actionButton for details
- textbox for explainer text
- Conditional formatting for L1/L2/L3 (red/orange/yellow)

## 6. Rules
- Max 3 Action Codes shown at once.
- If >3 apply, sort by severity (L3 > L2 > L1).
- Never mix more than one visual for actions.
- Minimalist layout, no icons unless necessary.

## 7. Relation to Other Files
- Action Code catalog: `ActionCodes.md`
- UseCase mapping: `UseCase_ActionCode_Map.yaml`
- Page mapping: `UseCase_PageTemplate_Map_3-30-300.yaml`

Action Panel is automatically rendered by template automation.
