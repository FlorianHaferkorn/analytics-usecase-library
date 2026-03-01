# Aurora Demo & Framework Package 1 Readiness

Purpose: Short checklist for **what we validate** with the Aurora demo. For **how to run the pipeline and verify** (orchestrator, PBIP, pbi-tools), see **`products/fabric/powerbi/docs/DEMO_AND_VERIFICATION.md`**.

---

## What “customer-ready” means for Framework Package 1

- **PBIP and reports open** in Power BI Desktop without errors.
- **Pipeline is reproducible:** Single source (`core/usecases/core`), three modes (`-UseCase`, `-Domain`, `-All`). Run: `.\products\fabric/powerbi\orchestrator\orchestrate_full_model.ps1`.
- **Documentation:** Aurora README (this showcase), Fabric docs (DEMO_AND_VERIFICATION, fabric/powerbi.md).
- **No known blockers** for the defined scope (open PBIP, load report). Limits (RLS, Publish to Fabric) are documented in DEMO_AND_VERIFICATION.md.

---

## Known limits

- **RLS:** Not applied automatically; configure manually if required.
- **Publish to Fabric:** No automated publish; use Desktop or your own deployment pipeline.
- **Scope:** “Opens in Desktop and loads”; no claim for Fabric workspace deployment or embedding.
