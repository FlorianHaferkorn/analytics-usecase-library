---
paths:
  - "products/fabric/powerbi/**"
  - "**/*.SemanticModel/**"
  - "**/*.pbip"
---

Learnings from Claude about connecting to semantic models via the connect-pbid skill

- PBIP models load with a **GUID database name**, not the .SemanticModel name. Match
  the target model by a **signature measure** (`$table.Measures.ContainsName(...)`),
  not `$db.Name`.
- Discover ports via `Get-NetTCPConnection -State Listen` joined to `msmdsrv` PIDs;
  the netstat-split-by-whitespace snippet in the skill parses unreliably here.
- Open a specific dist report with `Start-Process <full path>\<name>.pbip`. `pbir open`
  sometimes reports success but no-ops. After editing on-disk TMDL, the model must be
  re-opened (Desktop does not watch files) — close the stale instance first, else the
  signature-measure match may hit the old model.
- Store Power BI Desktop degrades after ~8 open/close cycles: new pbips open as blank
  "Unbenannt" windows with 0 tables. Fallback for **model** validation without Desktop:
  offline TMDL→TOM load —
  `[Microsoft.AnalysisServices.Tabular.TmdlSerializer]::DeserializeDatabaseFromFolder("<Model>.SemanticModel\definition")`,
  then enumerate tables/measures and check measure refs resolve. This catches dangling
  measure/table refs (the columnless class) without a running engine.
- Repo data note: the **Finance** model has `fact_output[Output Units]` (no `fact_ops`,
  no `Good Units`); `fact_ops`/`fact_quality` live only in the **Operations** model.
  Cross-domain proxy measures use a domain suffix — `(FIN)`, `(XD)`.
