# Slot Definitions – Page Template Governance

Slots define **what kind of analytical content** a page may contain.
They are **semantic placeholders**, not visuals.

Slots ensure that pages remain:

- decision-oriented,
- visually consistent,
- scalable across use cases and domains.

Templates (T1–T4) decide **which slots are allowed**.
The Visual Whitelist decides **how a slot may be visualized**.

---

## Core Principle

> **A slot exists to answer a specific analytical question.**
> If a question is unclear, the slot must not be used.

Slots are activated per use case via:

```yaml
mappings/UseCase_PageTemplate_Map.yaml
```

---

## Slot Overview

| Slot | Primary Question |
|-----|------------------|
| Trend | How is the KPI developing over time? |
| Variance | How far are we from target or prior period? |
| Ranking | Which entities perform best or worst? |
| Mix | How is the KPI distributed across categories? |
| Exceptions | Where are abnormal or critical cases? |
| Root Cause | What explains deviations or issues? |
| Prescriptive | What action should be taken? |
| Funnel | Where do we lose volume or value? |
| Detail Matrix | What are the underlying records or details? |

---

## Slot Definitions

### 1. Trend

**Purpose**  
Show the direction and pattern of a KPI over time.

**Typical Questions**

- Is performance improving or deteriorating?
- Are there seasonal effects?

**Allowed Templates**

- T1 – Strategic Overview  
- T2 – Tactical Variance  
- T3 – Operational Monitoring  

**Not Allowed When**

- KPI is non-temporal
- Analysis is purely structural

---

### 2. Variance

**Purpose**  
Explain deviation from target, budget, or prior period.

**Typical Questions**

- Where are we off plan?
- Is the deviation material?

**Allowed Templates**

- T1 – Strategic Overview  
- T2 – Tactical Variance  

**Not Allowed When**

- No reference value exists

---

### 3. Ranking

**Purpose**  
Compare entities by performance.

**Typical Questions**

- Who are top/bottom performers?
- Where should attention focus?

**Allowed Templates**

- T1 – Strategic Overview  
- T2 – Tactical Variance  
- T3 – Operational Monitoring  

**Not Allowed When**

- Ranking has no decision relevance

---

### 4. Mix

**Purpose**  
Show composition or share across categories.

**Typical Questions**

- What drives the total?
- How is value distributed?

**Allowed Templates**

- T1 – Strategic Overview  
- T2 – Tactical Variance  

**Not Allowed When**

- Categories are too granular
- Mix does not influence decisions

---

### 5. Exceptions

**Purpose**  
Highlight abnormal, critical, or non-compliant cases.

**Typical Questions**

- Where do we need to intervene?
- Which cases violate rules?

**Allowed Templates**

- T3 – Operational Monitoring  

**Not Allowed When**

- Thresholds or rules are undefined

---

### 6. Root Cause

**Purpose**  
Explain why deviations or issues occur.

**Typical Questions**

- What factors drive the problem?
- Which variables explain variance?

**Allowed Templates**

- T3 – Operational Monitoring  

**Not Allowed When**

- No hypothesis or driver logic exists

---

### 7. Prescriptive

**Purpose**  
Recommend concrete actions based on data.

**Typical Questions**

- What should be done next?
- Which action has highest impact?

**Allowed Templates**

- T4 – Prescriptive Recommendation  

**Not Allowed When**

- No action logic or ownership exists

---

### 8. Funnel

**Purpose**  
Analyze sequential drop-offs or conversion steps.

**Typical Questions**

- Where do we lose volume?
- Which step is critical?

**Allowed Templates**

- T2 – Tactical Variance  

**Not Allowed When**

- Process steps are not clearly defined

---

### 9. Detail Matrix

**Purpose**  
Provide detailed records for validation and drill-down.

**Typical Questions**

- Which individual records explain the KPI?
- What exactly happened?

**Allowed Templates**

- All templates (Detail pages only)

**Rules**

- Only allowed on **Detail (300)** pages
- Must not be the primary insight driver

---

## Governance Rules (Non-Negotiable)

- A page may only contain slots explicitly activated in the use case mapping.
- Slots must not be used as visual decoration.
- If a slot is activated, its purpose must be clearly visible to the user.
- Prescriptive slots require defined Action Codes.

---

## Key Principle

> **Slots enforce thinking before visualizing.**  
> If a slot cannot be justified, it must be removed.

