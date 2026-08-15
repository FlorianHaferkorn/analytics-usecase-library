# Page Type Taxonomy

> **Status:** Authoritative  
> **Authority:** `PAGE_TEMPLATE_DOCTRINE.md`  
> **Governs:** Page type selection for all use cases in the Analytics Use Case Library  
> **Machine-readable registry:** `core/templates/page_templates/template_manifest.yaml`

---

## 1. Decision: T1–T4 Are Retained as Page Families

After critical review, **T1–T4 remain the correct top-level page type taxonomy**.

Rationale:
- The four types map directly to the four decision question classes in management reporting (orientation → explanation → control → decision)
- They align with Munzner's nested model domain task layer (S3) — changing them would break the academic grounding
- Empirically: no established BI reporting framework uses more than 4–5 top-level archetypes.
  **Beleglage korrigiert 02.08.2026** (Recherche mit Widerlegungsauftrag): die zuvor hier
  stehende Zuschreibung „IBCS uses 4: M–Message, A–Analysis, K–KPI, T–Table" war weder auf
  ibcs.com noch in Sekundärquellen auffindbar und ist entfernt; ebenso die Jahreszahl bei Few
  (das Buch ist **2006**, 2004 war „Dashboard Confusion"). Die Aussage selbst hält — jetzt
  gestützt auf drei prüfbare Quellen statt auf eine unauffindbare:
  Few (2006) 3 Typen · Eckerson (2010) 3 Top-Level-Typen · Microsofts `powerbi-report-design`-
  Skill (2026) **5** Archetypen (Executive Summary · Operational Monitor · Analytical Canvas ·
  Narrative Story · Comparative Benchmark).

**The real gap is not the page types — it is the absence of documented *variants* beneath them.** T1–T4 felt similar because the variant layer was missing, not because the types are wrong.

### What "Almost Identical" Means in Practice

The user's perception that T2–T4 felt similar was correct at the *preview* level. The cause: the Studio gallery was rendering each template with a generic `DashboardLayout` using the same visual components regardless of page type. This is an **engine gap**, not a taxonomy gap. The types are distinct; the renderer was not distinguishing them.

---

## 2. Taxonomy: Page Families and Variants

### T1 — Strategic Overview

**Primary Decision Question:** Are we on track against strategic targets?  
**Audience:** Executives, Board, Senior Leadership  
**Time Horizon:** Monthly / quarterly  
**Primary Layer:** 3s + 30s (orientation and alignment)  

| Variant | ID | When to Use |
|---|---|---|
| Executive KPI Portfolio | T1_Portfolio | 4–6 strategic KPIs, portfolio breadth, no drill-down needed |
| Strategic Trend Monitor | T1_Trend | One primary KPI, emphasis on trajectory and momentum over time |

**T1 is complete when:** Strategic status is immediately visible; executives can align or escalate within 30 seconds.

---

### T2 — Tactical Variance

**Primary Decision Question:** Why are we off target, and which levers explain the gap?  
**Audience:** Management, Domain Leads, Function Heads  
**Time Horizon:** Monthly performance reviews  
**Primary Layer:** 30s (explanation and causal understanding)  

| Variant | ID | When to Use |
|---|---|---|
| Driver Bridge | T2_DriverBridge | Waterfall-centric; decomposes a single KPI gap into named drivers |
| Comparative Variance | T2_Comparative | Side-by-side entity comparison; which segment/region drives the gap |
| Funnel Loss | T2_Funnel | Sequential process loss; where in the funnel do we lose volume/value |

**T2 is complete when:** The dominant drivers are unambiguous; management knows where to intervene, not yet how.

**Key distinguisher from T1:** T1 shows *that* there is a gap. T2 explains *what* causes it.  
**Key distinguisher from T3:** T2 operates at aggregate/segment level. T3 operates at entity/record level.

---

### T3 — Operational Monitoring

**Primary Decision Question:** Where is execution breaking right now, and who must act?  
**Audience:** Operational Managers, Process Owners, Shift Leads  
**Time Horizon:** Daily / weekly  
**Primary Layer:** 30s + 300s (control and execution validation)  

| Variant | ID | When to Use |
|---|---|---|
| Exception Queue | T3_ExceptionQueue | Ranked list of threshold breaches; entity, severity, age, owner |
| Process Control | T3_ProcessControl | SLA / OTD / quality metrics with trend; control chart concept |
| Incident Monitor | T3_IncidentMonitor | Real-time or near-real-time exception tracking; short refresh cycle |

**T3 is complete when:** Exceptions are clearly visible and prioritized; operational owners know what needs immediate action.

**Key distinguisher from T2:** T2 explains aggregate variance. T3 identifies specific entities in breach.  
**Key distinguisher from T4:** T3 signals where action is needed. T4 specifies what the action is.

---

### T4 — Prescriptive Recommendation

**Primary Decision Question:** What is the best next action, for which entity, with what expected impact?  
**Audience:** Decision Owners, Decision Makers  
**Time Horizon:** Triggered by T2/T3 escalation  
**Primary Layer:** 3s + 30s (clear recommendation + supporting evidence)  

| Variant | ID | When to Use |
|---|---|---|
| Action Decision | T4_ActionDecision | Single primary recommendation; Impact-Owner-Deadline visible immediately |
| Option Comparison | T4_OptionComparison | Two or three explicitly compared options; ranked by impact/effort/risk |
| Sensitivity Check | T4_Sensitivity | Recommendation with scenario validation; show impact under key assumptions |

**T4 is complete when:** The recommended action is unambiguous; ownership and impact are clear; the decision maker can confidently approve or reject.

**Key distinguisher from T3:** T3 says "act here". T4 says "this is the specific action to take".

---

## 3. Decision: Is T5 (Exploratory Analysis) Needed?

**Decision: No T5 at this time.**

Rationale:
- Exploratory analysis is not management reporting. It is an analytical workflow, not a decision-presentation workflow.
- Munzner (S3) separates *analysis tools* from *presentation tools* by domain task. A T5 would require a fundamentally different template contract (free-form filtering, hypothesis navigation, no fixed slot structure).
- Evidence (S7, Few): dashboards designed for exploration degrade decision-making for monitoring and reporting audiences. Combining exploration and decision support in the same template system creates cognitive interference.
- If exploratory analysis is needed, it is done in a separate analytical environment (e.g., Q&A, ad-hoc analysis in Excel/Python) and its findings are then communicated via T1–T4.

**Condition for revisit:** If a documented use case cannot be mapped to any T1–T4 variant, this decision must be re-evaluated. The use case must be submitted with a documented decision question that T1–T4 cannot answer.

---

## 4. Page Type Selection Rules

### Decision Tree

```
Does the page primarily answer:
  "Are we on track?" → T1
  "Why are we off track?" → T2
  "Where is execution breaking?" → T3
  "What should we do?" → T4
  Something else → return to sponsor; define the decision question first
```

### Page Type Anti-Patterns (Common Misuse)

| Anti-Pattern | Wrong Type | Correct Type |
|---|---|---|
| Showing both "Are we on track?" and "Why?" on one page | T1 with T2 content leaked in | Separate T1 + T2 pages |
| Exception list as the primary content of a "variance" page | T2 used for operational control | T3 |
| Action panel on a monitoring page without decision commitment | T3 with T4 content | T4 with T3 as predecessor |
| Strategic KPIs in the exception zone | T1 content in T3 format | T1 |
| Prescriptive recommendations with no owner or impact | T4 shell without action codes | Author Action Code first |

---

## 5. Every Use Case Maps to Exactly Two Pages

Per the framework rule (one Overview page + one Detail page):

| Page | Layer(s) | Page Type | Grid Template |
|---|---|---|---|
| Overview | 3s + 30s | T1, T2, or T3 | `pulse`, `executive_kpi`, or `pulse_asymmetric` |
| Detail | 300s | T3 (extended) or T4 | `investigator`, `action_matrix`, or `investigator_focus` |

The Overview page answers the primary decision question.  
The Detail page validates the answer and (for T4) prescribes the action.

A use case is not allowed to have more than two pages (Overview + Detail). If more depth is needed, it indicates the use case scope is too broad and must be split.

---

## 6. Variant Mapping to Grid Templates

| Variant | Preferred Grid Template | Alternate |
|---|---|---|
| T1_Portfolio | `executive_kpi` | `pulse` |
| T1_Trend | `pulse` | — |
| T2_DriverBridge | `executive_kpi` | `pulse_asymmetric` |
| T2_Comparative | `pulse` | — |
| T2_Funnel | `pulse_asymmetric` | — |
| T3_ExceptionQueue | `pulse` | `investigator` |
| T3_ProcessControl | `pulse` | — |
| T3_IncidentMonitor | `pulse_asymmetric` | — |
| T4_ActionDecision | `action_matrix` | `investigator_focus` |
| T4_OptionComparison | `investigator_focus` | — |
| T4_Sensitivity | `investigator_focus` | — |

---

## 7. Definition of Done

- [ ] Every use case in `core/usecases/` maps to exactly one page type variant
- [ ] No use case uses a variant that doesn't match its primary decision question
- [ ] All T1–T4 page type specs reference this taxonomy for variant guidance
- [ ] `template_manifest.yaml` includes all variants defined here
- [ ] Any use case that cannot be mapped triggers a taxonomy review (not a silent override)
