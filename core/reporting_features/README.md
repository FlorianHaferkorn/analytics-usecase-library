# Reporting Feature Catalog

What report and cockpit users expect from **reporting, business intelligence and decision
intelligence**, one entry per feature (`catalog.yaml`, schema
`tooling/generator/schemas/reporting_feature_catalog.schema.json`). Ledger A-31 R7, Freelancing D-635.

Each feature carries, as fields:

| Field | Meaning |
|---|---|
| `area` | chart, page, navigation, time, distribution, alerting, self_service, trust, collaboration, decision, decision_loop, planning, operations, accessibility, language, performance |
| `sources` | entry ids in the research corpus `docs/architecture/research/2026-09-30_visual-stack-r1/` (Power BI baseline `pbi-`, market `market-`, users `users-`, decision intelligence `di-`, BI platform `bi-`) |
| `pbi_status` | what Power BI/Fabric offers today |
| `must_have` / `beyond_pbi` | parity requirement / better than Power BI |
| `home` | where it is built: ALUCA spec, cockpit shell, Meridian backend, Fabric platform, KPI catalog, semantic model |
| `meridian_module` | module M1–M8 of the Meridian Cockpit plan (I-22); `null` plus `gap_reason` when no module owns it |
| `status`, `tests` | done/partial/planned/gap; a built feature names the test that measures it |

Enforced by `tooling/tests/test_reporting_feature_catalog.py`: schema, unique ids, every source
exists in the corpus, every named test file exists, every must-have without a module states why.
Sources marked `zugang: search_index` in the corpus are not yet checked against the original and
carry no test authority.
