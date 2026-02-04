# Structure & Naming Recommendations (Feb 2026)

## 1. Split checks: tool-agnostic vs tool-specific

**Yes, it makes sense.** Current state already reflects it:

| Layer | Script | Scope |
|-------|--------|--------|
| **Tool-agnostic (CI gate)** | `run_stage1_checks.ps1` | Facts, KPI catalog, action codes, use case map, decision spines, IDs, SSOT, doc refs, forbidden content. No `DistRoot`, no TMDL/PBIP. |
| **Broader + Fabric** | `run_all_checks.ps1` | Stage 1–like checks plus docs↔KPI, inventory, layout, measure dictionary, **check_measures_vs_kpi**, **check_tmdl_vs_measure_dictionary**, markdownlint, YAML, etc. Uses `implementations/microsoft_fabric_powerbi/dist`. |

**Recommendations:**

1. **Document explicitly** in root README and/or AGENTS.md:  
   "Stage 1 = tool-agnostic only (CI). For Fabric/Power BI output validation, run the Fabric checks (see implementations/microsoft_fabric_powerbi/)."

2. **Add a Fabric-only check script** under `implementations/microsoft_fabric_powerbi/tools/` (e.g. `run_fabric_checks.ps1`) that runs only:
   - `check_measures_vs_kpi.ps1` (DistRoot = implementation dist)
   - `check_tmdl_vs_measure_dictionary.ps1` (same)
   So Fabric work has one entry point without running the full run_all_checks.

3. **Done:** Scripts moved to `implementations/microsoft_fabric_powerbi/validation/`; run_all_checks and run_fabric_checks invoke them there. Added `check_dax_best_practices.ps1` (DAX in TMDL vs bpa-rules-dax.json).

---

## 2. framework/implementation_guides – still needed?

**No. Move it into the Fabric implementation.**

- Content is 100% Fabric/Power BI (`fabric_powerbi.md`, `tmdl_best_practices.md`). It belongs with the implementation, not under tool-agnostic framework.
- **Recommendation:** Move `framework/implementation_guides/` → `implementations/microsoft_fabric_powerbi/guide/` (or `docs/`). Update all references (root README, framework README, implementation README, strategy/vision docs). Remove the empty `framework/implementation_guides` folder or leave a one-line README: "Implementation guides live under implementations/<platform>/guide/."

Result: One place for everything Fabric/Power BI (guide, dist, tools, theme_generator).

---

## 3. Other structure and naming

- **strategy_operating_model:** Name is clear; no change needed unless you want something shorter (e.g. `golden_thread`).
- **_internal/tools:** Fabric-specific scripts (orchestrate_full_model, fix_factsheets, etc.) still live here. Long-term you could move them under `implementations/microsoft_fabric_powerbi/tools/` and keep only shared/agnostic scripts in _internal; not required for now.
- **Root README:** Add a one-line "Structure" that shows `framework/` vs `implementations/` vs `showcases/` so the split is obvious to new readers.
- **implementations/microsoft_fabric_powerbi/README:** Already describes dist, tools, guide. After moving implementation_guides into `guide/`, point "Start with the guide" to `implementations/microsoft_fabric_powerbi/guide/fabric_powerbi.md`.

---

## 4. Summary

| Action | Priority |
|--------|----------|
| Move `framework/implementation_guides/` → `implementations/microsoft_fabric_powerbi/guide/` | High – aligns with structure |
| Document Stage 1 = tool-agnostic, run_all_checks = Stage 1 + Fabric + broader | High – clarity |
| Add `run_fabric_checks.ps1` under implementation (optional) | Medium – convenience |
| Move Fabric-specific check scripts under implementation (optional) | Low – can follow later |
