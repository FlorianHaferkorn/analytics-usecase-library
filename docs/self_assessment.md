# Analytics Maturity Self-Assessment

This questionnaire helps organizations determine their analytics maturity level and find the right entry point into the framework.

Inspired by TDWI Analytics Maturity Model, Gartner Data & Analytics Maturity, and the DELTA Plus framework.

---

## How to Use

1. Answer each question honestly (1-5 scale)
2. Sum your scores per dimension
3. Look up your maturity level in the scoring guide
4. Follow the recommended entry point for your level

---

## Dimension 1: Data Foundation (max 25 points)

| # | Question | 1 (Not at all) | 3 (Partially) | 5 (Fully) |
|---|----------|-----------------|----------------|-----------|
| 1.1 | Are key business data sources identified and documented? | No inventory of data sources | Some sources documented | Complete data catalog with lineage |
| 1.2 | Is data quality measured and monitored? | No quality metrics | Ad-hoc quality checks | Automated quality monitoring with SLAs |
| 1.3 | Are data definitions consistent across teams? | Every team has own definitions | Some shared definitions | Governed data dictionary / semantic model |
| 1.4 | Are data contracts in place between producers and consumers? | No contracts | Informal agreements | Formal contracts with schema validation |
| 1.5 | Is master data managed centrally? | No master data management | Partial MDM for some entities | Enterprise MDM with golden records |

**Your score: ___ / 25**

---

## Dimension 2: KPI & Metric Governance (max 25 points)

| # | Question | 1 (Not at all) | 3 (Partially) | 5 (Fully) |
|---|----------|-----------------|----------------|-----------|
| 2.1 | Are KPIs formally defined with clear ownership? | KPIs are informal, debated in meetings | Some KPIs documented, ownership unclear | KPI catalog with owner, steward, formula |
| 2.2 | Can you trace from a strategic goal to a specific KPI? | No explicit link | Some strategic KPIs exist | Full strategy-to-KPI mapping (Golden Thread) |
| 2.3 | Are KPI calculations consistent across reports? | Different reports show different numbers | Mostly consistent, some exceptions | Single source of truth (semantic model) |
| 2.4 | Do KPIs have defined thresholds and target values? | No thresholds | Some KPIs have targets | All KPIs have targets, thresholds, and alerts |
| 2.5 | Is there a review cycle for KPI relevance? | Never reviewed | Annual review | Quarterly review with business sign-off |

**Your score: ___ / 25**

---

## Dimension 3: Analytics Capability (max 25 points)

| # | Question | 1 (Not at all) | 3 (Partially) | 5 (Fully) |
|---|----------|-----------------|----------------|-----------|
| 3.1 | What type of analytics does your organization primarily use? | Manual Excel reporting | Descriptive dashboards (BI) | Diagnostic + predictive + prescriptive |
| 3.2 | Are analytics organized around business decisions (use cases)? | Reports are ad-hoc / request-driven | Some standard reports exist | Use case-driven analytics catalog |
| 3.3 | Do insights lead to documented actions? | Insights stay in reports | Some follow-up, mostly informal | Structured action codes with triggers |
| 3.4 | Is there a reusable analytics platform? | Every project builds from scratch | Some shared components | Platform with templates, reusable models |
| 3.5 | Are analytics skills distributed across the organization? | Only central IT team | Some business analysts | Embedded analytics in business teams + CoE |

**Your score: ___ / 25**

---

## Dimension 4: Organization & Governance (max 25 points)

| # | Question | 1 (Not at all) | 3 (Partially) | 5 (Fully) |
|---|----------|-----------------|----------------|-----------|
| 4.1 | Is there executive sponsorship for analytics? | No sponsorship | Departmental support | C-level sponsor with budget and mandate |
| 4.2 | Are roles and responsibilities for data/analytics defined? | Unclear ownership | Some roles defined | Clear RACI with data owners + stewards |
| 4.3 | Is there a governance process for new analytics requests? | No process, first come first served | Informal prioritization | Formal intake with RICE scoring + readiness assessment |
| 4.4 | Do business and analytics teams collaborate effectively? | Separate silos | Regular meetings | Integrated teams with shared goals |
| 4.5 | Is there a change management process for analytics adoption? | No change management | Training offered | Structured adoption program with champions |

**Your score: ___ / 25**

---

## Scoring Guide

### Calculate Your Total

| Dimension | Score |
|-----------|-------|
| 1. Data Foundation | ___ / 25 |
| 2. KPI & Metric Governance | ___ / 25 |
| 3. Analytics Capability | ___ / 25 |
| 4. Organization & Governance | ___ / 25 |
| **Total** | **___ / 100** |

### Your Maturity Level

| Score | Level | Description |
|-------|-------|-------------|
| **20-35** | **Level 1: Ad-hoc** | Analytics is reactive, no standards, limited trust in data |
| **36-55** | **Level 2: Developing** | Some standards emerging, basic BI in place, siloed efforts |
| **56-70** | **Level 3: Defined** | Standards documented, consistent KPIs, some governance |
| **71-85** | **Level 4: Managed** | Governed analytics, use case-driven, action-oriented |
| **86-100** | **Level 5: Optimizing** | Predictive/prescriptive, AI-ready, continuous improvement |

---

## Recommended Entry Point by Level

### Level 1: Ad-hoc (20-35 points)

**Start here:**
1. Read `core/strategy_operating_model/company/company_strategy.md` - understand the WHY
2. Pick ONE high-priority use case (XD-003 Executive KPI Overview recommended - lowest effort, highest reach)
3. Focus on getting 5 strategic KPIs defined and trusted

**Priority:** Build data foundation first. Don't try to implement the full framework.

### Level 2: Developing (36-55 points)

**Start here:**
1. Implement the Golden Thread for your top 3 use cases by priority_score
2. Establish a KPI catalog (`core/kpi_catalog/`) with clear ownership
3. Run `python tooling/health_scorecard.py` to measure your H1-H6 baseline

**Priority:** Standardize KPI definitions and create accountability.

### Level 3: Defined (56-70 points)

**Start here:**
1. Adopt the full UseCase_Bracket structure for all core use cases
2. Implement action codes with trigger thresholds
3. Set up Stage 1 CI validation

**Priority:** Move from "reporting" to "action-ready analytics."

### Level 4: Managed (71-85 points)

**Start here:**
1. Implement the full framework including data contracts and semantic models
2. Set up the health scorecard as a continuous governance tool
3. Extend to industry-specific and advanced use cases

**Priority:** Scale and optimize. Focus on H1-H6 metrics reaching targets.

### Level 5: Optimizing (86-100 points)

**Start here:**
1. Leverage the AI-powered Golden Thread Discovery Studio
2. Enable predictive/prescriptive analytics via the value driver model
3. Build a Community of Practice for managed self-service

**Priority:** Innovate. Use the framework as a platform for AI agents and automation.

---

## Dimension Gap Analysis

After scoring, identify your weakest dimension. This is where to focus:

| Weakest Dimension | Recommended Action |
|---|---|
| **Data Foundation** | Start with data contracts (`core/data_contracts/`) and evidence grain mapping |
| **KPI Governance** | Build your KPI catalog first, then link to use cases |
| **Analytics Capability** | Implement 3 core use cases end-to-end as templates |
| **Organization & Governance** | Establish roles (`core/organization/org_roles.yaml`) and the readiness gate |
