# Analytics Use Case Library

## Purpose
The **Analytics Use Case Library** defines a standardized approach for describing and maintaining business analytics scenarios across all functional domains.  
Each use case follows a uniform one-page Markdown layout to ensure consistent documentation of business goals, analytical logic, KPIs, and expected impact.

This repository acts as a shared reference point for analysts, data engineers, and business stakeholders to ensure clarity, comparability, and reusability across all analytics initiatives.

## Objectives
- Establish a common structure for documenting business analytics use cases.  
- Enable a consistent language between business and data teams.  
- Create a foundation for standardized KPIs, actions, and insights.  
- Support automation, AI interpretation, and Copilot readiness through structured metadata.  
- Ensure traceability and governance via version control and changelog discipline.

## Structure
```
/analytics-usecase-library/
│
├── /docs/
│   ├── Instructions.md
│   ├── Methodology.md
│   ├── Changelog.md
│
├── /usecases/
│   ├── /_includes/
│         ├── Glossary.md
│         ├── KPI_Catalog.md
│         └── ActionCodes.md
│   ├── UC-001_Sales_Performance.md
│   ├── UC-002_Gross_Margin.md
│   ├── UC-003_Working_Capital.md
│   └── ... (one Markdown file per use case)
│
└── README.md
```

## Use Case Layout
Each use case file follows a standardized structure:

```markdown
---
id: UC-001
title: Sales Performance vs Plan & Last Year
domain: Sales & Revenue
owner: Head of Sales
impact: High
status: Active
last_update: 07.10.2025
---

## Business Goal
Short statement explaining the purpose and business relevance.

## Business Context
Brief description of the problem, its impact, and the key decision supported.

## Key Questions
- What is being measured or compared?
- Where do deviations occur?
- What explains the change?

## Key KPIs
| KPI | Definition | Unit | Format |
|------|-------------|------|--------|
| Example KPI | Definition text | € | 0–2 decimals |

## Typical Actions
- Action 1 – description and expected effect  
- Action 2 – description and expected effect  

## Expected Business Impact
Concise summary of expected outcomes (e.g., “+3 pp Gross Margin %, −5 % Inventory Value”).

## Related Processes
List of relevant operational processes or systems.

## Insights & Learnings
Key takeaways, interpretation hints, or links to related use cases.
```

## Contribution Guidelines
1. Create a new branch named `feature/UC-###_Title`.  
2. Duplicate the template from `usecases/UC-000_Template.md`.  
3. Fill in all sections clearly and concisely using the defined layout.  
4. Submit a Pull Request with a brief description of the business rationale.  
5. Review process: one business reviewer (SME) and one data reviewer (technical).  
6. Update `docs/Changelog.md` with version, author, and change summary.

## Governance and Versioning
- Each Use Case has a unique `UC-###` ID.  
- Status values: `Draft`, `In Review`, `Active`, `Deprecated`.  
- All changes require a Pull Request and reviewer approval.  
- The Changelog records every addition or modification with author and timestamp.

## Methodology Reference
See [`/docs/Methodology.md`](./docs/Methodology.md) for:
- 3-30-300 principle  
- Semantic modeling rules  
- Naming standards (`Δ`, `Δ%`, `%`)  
- Copilot/AI readiness  
- Governance and quality criteria

## License and Use
Internal documentation only.  
Not intended for public release without prior review and approval.

*Last updated: 07.10.2025*
