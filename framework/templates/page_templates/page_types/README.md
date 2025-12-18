# Page Templates

This directory defines the **standardized page types** used across the Analytics Use Case Library.
Page templates are not visual themes or report layouts – they are **decision templates**.

Each page type exists to answer **one specific decision question**.
Using the wrong page type leads to confusion, not better insights.

---

## Choosing the Right Page Type

Each page type answers exactly one decision question.

| Page Type | Decision Question | Typical Audience |
|---------|-------------------|------------------|
| **T1 – Strategic Overview** | Are we on track against our strategic targets? | Executives, Board |
| **T2 – Tactical Variance** | Why are we off target and which levers explain it? | Management, Domain Leads |
| **T3 – Operational Monitoring** | Where is execution currently breaking and who must react now? | Operations, Process Owners |
| **T4 – Prescriptive Recommendation** | What is the best next action and with what expected impact? | Decision Owners |

**Rule of thumb**
- If you want **alignment** → T1  
- If you want **explanation** → T2  
- If you want **control** → T3  
- If you want a **decision** → T4  

---

## Page Types and the 3–30–300 Rule

The **3–30–300 rule** describes *possible depth of understanding*, not mandatory content per page.

Each page type has a **primary decision layer**. Other layers are optional and only allowed if they support the decision.

| Page Type | Primary Layer(s) | Notes |
|---------|------------------|------|
| **T1 – Strategic Overview** | 3s, 30s | Orientation and alignment. No deep validation. |
| **T2 – Tactical Variance** | 30s | Explanation and causal understanding. |
| **T3 – Operational Monitoring** | 30s, 300s | Control and execution validation. |
| **T4 – Prescriptive Recommendation** | 3s, 30s | Clear recommendation with supporting evidence. |

**Important**
- 300s content is only used where **validation is required**
- No page must contain all three layers
- Depth serves the decision, never the other way around

---

## What Page Templates Are

Page templates define:
- the **decision question** a page must answer
- the **allowed analytical depth**
- the **permitted slot types**
- the **visual and interaction boundaries**

They ensure:
- consistent decision quality
- predictable user experience
- scalability across domains
- deterministic behavior for automation and agents

---

## What Page Templates Are NOT

Page templates are **not**:
- visual design files
- report themes
- domain-specific dashboards
- exploratory analysis canvases

They intentionally limit freedom to **increase clarity and trust**.

---

## Governance Principles

All page templates follow these rules:
- One primary decision question per page
- Strict separation between T1–T4 responsibilities
- Slot usage governed via `governance/Slot_Definitions.md`
- Visuals restricted via `governance/Visual_Whitelist.md`
- Completion criteria defined via `governance/DoD_PageTemplates.md`

If a page violates these rules, it is **not compliant**, regardless of visual quality.

---

## Relationship to Other Framework Elements

Page templates work together with:
- **KPI Catalogs** (what is measured)
- **Action Codes** (what can be done)
- **Semantic Models** (how data is structured)
- **Use Cases** (why the page exists)

Page templates do **not** define KPIs or actions themselves.
They define **how decisions are presented**.

---

## Key Principle

> Page templates exist to reduce cognitive load and increase decision confidence.  
> If a page does not clearly support a decision, it is using the wrong template.
