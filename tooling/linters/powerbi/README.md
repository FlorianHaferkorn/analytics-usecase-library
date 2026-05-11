# Power BI / Microsoft Fabric BPA Rules

## Purpose

This directory contains **tool-specific Best Practice Analyzer (BPA) rules** for Microsoft Power BI and Fabric implementations.

These rules are **implementation-specific** and only apply when:
- Generating Power BI semantic models (PBIP/TMDL format)
- Validating existing Power BI reports
- Deploying to Microsoft Fabric

## Separation of Concerns

The ActionReady Framework is **tool-agnostic** until the implementation layer:

```
Tool-Agnostic Layers:
├── core/                     # Business logic, KPIs, domains
├── data_contracts/                # Data structure definitions
├── usecases/                      # Use case specifications
└── docs/operating_model/          # Conceptual framework

Implementation Layer (Tool-Specific):
├── products/fabric/powerbi/docs/
│   └── fabric_powerbi.md          # High-level Power BI patterns
│   └── tmdl_best_practices.md     # TMDL syntax specifications
└── tooling/linters/powerbi/
    └── bpa-rules-dax.json         # DAX style rules
    └── bpa-rules-report.json      # Report layout rules
    └── bpa-rules-semanticmodel.json # Semantic model rules
    └── bpa-rules-tmdl.json        # TMDL syntax rules
```

## BPA Rule Files

### 1. bpa-rules-dax.json
**Scope**: DAX measure expressions  
**Purpose**: Enforce DAX best practices (VAR/RETURN, DIVIDE, FORMAT prohibition, error functions, BLANK handling, etc.)  
**Severity**: Error, Warning, Info  
**Auto-fixable**: Partial (DIVIDE, REMOVEFILTERS)  
**Sources**: Microsoft Learn (DAX best practices), SQLBI DAX Style (docs.sqlbi.com/dax-style), DAX.Guide.  
**v1.1 additions**: Avoid ISERROR/IFERROR; no shortened CALCULATE syntax (measure then filter in parentheses); prefer VAR over EARLIER/EARLIEST; prefer DIVIDE without alternate 0 (return BLANK).

### 2. bpa-rules-report.json
**Scope**: Power BI report visuals and pages  
**Purpose**: Enforce UX design system (max visuals per page, theme colors, alt-text, etc.)  
**Severity**: Error, Warning  
**Auto-fixable**: Limited  
**Readable overview**: [REPORT_BEST_PRACTICES.md](REPORT_BEST_PRACTICES.md) (human-readable rule list and parameters)

### 3. bpa-rules-semanticmodel.json
**Scope**: Semantic model tables, columns, relationships  
**Purpose**: Enforce performance best practices (avoid calculated columns, star schema, partitioning, etc.)  
**Severity**: Error, Warning, Info  
**Auto-fixable**: Limited

### 4. bpa-rules-tmdl.json ⭐ NEW
**Scope**: TMDL file syntax and structure  
**Purpose**: Enforce TMDL formatting rules (TAB indentation, /// comments, let...in blocks, etc.)  
**Severity**: Error, Warning, Info  
**Auto-fixable**: High (TMDL-001, TMDL-002, TMDL-003)

## Usage

### Validation Scripts

```powershell
# Validate all Power BI BPA rules
& tooling/validation/validate_powerbi.ps1 -PbipPath "products/fabric/powerbi/dist/Commercial.SemanticModel"

# Validate TMDL syntax only
& tooling/validation/validate_tmdl.ps1 -TmdlPath "products/fabric/powerbi/dist/Commercial.SemanticModel/definition" -AutoFix

# Validate DAX measures only
& tooling/validation/validate_dax.ps1 -MeasuresPath "products/fabric/powerbi/dist/Commercial.SemanticModel/definition/tables/_Measures.tmdl"
```

### Integration in Orchestrator

```powershell
# orchestrate_full_model.ps1 Phase 3
& "$PSScriptRoot\validation\validate_tmdl.ps1" -TmdlPath $tmdlFolder -AutoFix

if ($LASTEXITCODE -ne 0) {
    Write-Error "TMDL validation failed. Check bpa-rules-tmdl.json"
    exit 1
}
```

### Integration in CI/CD

```powershell
# run_all_checks.ps1 Stage 1
$bpaResults = & tooling/validation/validate_powerbi.ps1 -PbipPath $pbipPath

if ($bpaResults.Errors.Count -gt 0) {
    Write-Error "BPA validation failed: $($bpaResults.Errors | ConvertTo-Json)"
    exit 1
}
```

## Rule Severity Levels

| Level | Meaning | Action |
|-------|---------|--------|
| **error** | Blocks deployment, causes parser errors | Must fix before commit |
| **warning** | Performance/quality degradation | Should fix before production |
| **info** | Recommendations, best practices | Optional improvements |

## Auto-Fixable Rules

Rules marked `"autoFixable": true` can be corrected automatically via validation scripts:

**TMDL Rules**:
- `TMDL-001`: Convert Tab+Space to pure TAB
- `TMDL-002`: Convert `description:` property to `///` comment
- `TMDL-003`: Wrap inline M-expression in `let...in` block
- `TMDL-010`: Generate and add lineageTag GUIDs

**DAX Rules**:
- `dax.divide.preferred`: Replace `/` with `DIVIDE()`
- `dax.removefilters.preferred`: Replace `ALL()` with `REMOVEFILTERS()`

## Extending Rules

To add new Power BI BPA rules:

1. Choose appropriate file:
   - DAX expression rules → `bpa-rules-dax.json`
   - Report layout rules → `bpa-rules-report.json`
   - Semantic model rules → `bpa-rules-semanticmodel.json`
   - TMDL syntax rules → `bpa-rules-tmdl.json`

2. Add rule entry:
   ```json
   {
     "id": "TMDL-011",
     "name": "Rule Name",
     "severity": "error|warning|info",
     "category": "Syntax|Metadata|Performance",
     "description": "Detailed description",
     "pattern": "regex pattern",
     "autoFixable": true|false,
     "reference": "products/fabric/powerbi/docs/tmdl_best_practices.md#section"
   }
   ```

3. Implement auto-fix logic in `validate_tmdl.ps1` if `autoFixable: true`

4. Add test case in `tooling/validation/tests/`

5. Document in `products/fabric/powerbi/docs/tmdl_best_practices.md`

## References

- **TMDL Best Practices**: `products/fabric/powerbi/docs/tmdl_best_practices.md`
- **Fabric/Power BI Implementation**: `products/fabric/powerbi/docs/fabric_powerbi.md`
- **Validation Scripts**: `tooling/validation/`
- **MCP Operations**: `mcp_powerbi-model_*` tools

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-02-03 | Initial structure with 4 BPA rule files |
