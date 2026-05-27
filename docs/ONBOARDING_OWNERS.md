# Onboarding Content Ownership

This file records which document is the canonical home for each type of onboarding content. When you want to add or update something, put it in the right place rather than in every place.

> **Audience:** Contributors who maintain onboarding and navigation docs.

---

## Ownership table

| Content type | Canonical file | Other files may… |
|---|---|---|
| Framework purpose and "what this is not" | [`README.md`](../README.md) | Quote one sentence and link |
| Two-track onboarding path (Reader / Contributor) | [`ONBOARDING.md`](../ONBOARDING.md) | Reference and link |
| Folder map and source-vs-generated rules | [`docs/architecture/README.md`](architecture/README.md) | Summarise in 2 lines and link |
| Role-based entry points | [`docs/README.md`](README.md) | May duplicate the Explorer row only, briefly |
| KPI definitions and roles | `core/kpi_catalog/` | Reference by ID only |
| Action logic and execution steps | `core/action_codes/` | Reference by ID only |
| Term and acronym definitions | [`docs/reference/GLOSSARY.md`](reference/GLOSSARY.md) | Use inline hints (2–5 words) and link |
| ID naming schemes | [`docs/reference/TAXONOMY.md`](reference/TAXONOMY.md) | Link only |
| Development workflow and setup | [`CONTRIBUTING.md`](../CONTRIBUTING.md) | Link only from Contributor track |
| Known errors and fixes | `internal/project_mgmt/KNOWN_ERRORS_AND_FIXES.md` | Link only |

---

## Rules for adding new onboarding content

1. **Prefer editing an existing file over creating a new one.** New files only if the content has its own audience, lifecycle, and a clear reason not to merge it into an existing file.
2. **Any new file must be linked from the navigation hub** ([`docs/README.md`](README.md)) before it is considered "in the system."
3. **COM-001 examples must match reality.** After changing `core/usecases/core/COM-001_Sales_Performance/UseCase_Bracket.yaml` or `core/kpi_catalog/golden_20.yaml`, check that [`ONBOARDING.md`](../ONBOARDING.md) still refers to the correct strategic KPI and action codes.
4. **No free-standing definition lists.** If a term needs a definition, it goes in GLOSSARY.md, not inline in ONBOARDING.md or architecture docs.
5. **Validation checklist after any onboarding edit:**
   - Run `py -3 tooling/validation/check_docs_links.py` — no broken links.
   - Run Stage 1 (`.\tooling\run_stage1_checks.ps1`) — no regressions.
   - Manually verify the Reader track done-checklist in ONBOARDING.md is still answerable from the docs alone.
