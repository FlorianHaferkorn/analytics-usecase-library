# Builder Engine – Plan bis Freitag

**Ziel:** Pipeline produziert PBIP, das ohne manuelles Öffnen in Desktop als „loadable“ validiert wird; Build–Validate–Improve in einem Lauf; Fehler werden erfasst für Learning-Loop. Details siehe Plan-Datei (Cursor/Plans).

**Priorität für Freitag:**

| Priorität | Inhalt |
|-----------|--------|
| **P0** | Phase 1: Pipeline stabil, PBIP öffnet (run_fabric_checks + Struktur + optional pbi-tools compile). |
| **P1** | Phase 2: Validate im gleichen Lauf (Reihenfolge, Gate-Definition) + Projektplan verankert (dieses Doc + BACKLOG-Abschnitt). |
| **P2** | Phase 3: Inkrementell (neuer Use Case zu Domain hinzufügen) + Phase 4.1/4.2 (State-Schema, KNOWN_ERRORS_AND_FIXES). |

**Umsetzung (Referenz):**

- **Phase 1:** [products/fabric/powerbi/orchestrator/orchestrate_full_model.ps1](../../products/fabric/powerbi/orchestrator/orchestrate_full_model.ps1) – Pipeline inkl. Phase 6 „Validate Fabric output“; [showcases/aurora_group/DEMO_AND_READINESS.md](../../showcases/aurora_group/DEMO_AND_READINESS.md) – Verifikation und pbi-tools.
- **Phase 2:** Gate in [products/fabric/powerbi/orchestrator/README.md](../../products/fabric/powerbi/orchestrator/README.md); Fehler in `last_run_state.json` und `out/build_errors.json`.
- **Phase 3:** [products/fabric/powerbi/orchestrator/README.md § Adding a new use case](../../products/fabric/powerbi/orchestrator/README.md).
- **Phase 4:** [KNOWN_ERRORS_AND_FIXES.md](KNOWN_ERRORS_AND_FIXES.md); State-Schema mit `validateErrors`.

**Backlog-Anbindung:** Framework Package 1 (Demo Friday) – siehe [BACKLOG_GRANULAR.md](BACKLOG_GRANULAR.md) Abschnitt „Builder Engine (Diese Woche)“.
