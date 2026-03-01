# Validation Tools

## Purpose

This directory contains **validation scripts** for automated quality checks against BPA rules during model generation and CI/CD workflows.

## Scripts

### validate_tmdl.ps1
**Purpose**: Validate TMDL files against `bpa-rules-tmdl.json`  
**Auto-fix**: Yes (TMDL-001, TMDL-002, TMDL-003, TMDL-010)  
**Usage**:
```powershell
# Validate and auto-fix TMDL syntax
.\validate_tmdl.ps1 -TmdlPath "showcases\aurora_group\semantic_models\Commercial.SemanticModel\definition" -AutoFix

# Validation only (no auto-fix)
.\validate_tmdl.ps1 -TmdlPath "path\to\definition"
```

**Checks**:
- ✅ Pure TAB indentation (no Tab+Space)
- ✅ /// comments (not description: property)
- ✅ M-expression let...in blocks
- ✅ FormatString for numeric measures
- ✅ DisplayFolder for measures
- ✅ LineageTag for all objects

**Exit Codes**:
- `0`: All validations passed
- `1`: Validation failed (check errors)

---

### validate_dax.ps1
**Purpose**: Validate DAX measure expressions against `bpa-rules-dax.json`  
**Auto-fix**: Partial (DIVIDE, REMOVEFILTERS)  
**Integration**: run_all_checks.ps1 (19c) for each dist `*.SemanticModel\definition`  
**Checks**:
- VAR/RETURN usage
- DIVIDE() vs /
- FORMAT() prohibition
- IF nesting depth

---

### validate_report.ps1
**Purpose**: Validate Power BI report visuals against `bpa-rules-report.json`  
**Auto-fix**: No  
**Integration**: run_all_checks.ps1 (19f) for each dist `*.Report`  
**Checks**:
- Max visuals per page
- Theme colors usage
- Alt-text for accessibility
- Page scroll limits

---

### validate_semanticmodel.ps1
**Purpose**: Validate semantic model structure against `bpa-rules-semanticmodel.json`  
**Auto-fix**: No  
**Integration**: run_all_checks.ps1 (19d) for each dist `*.SemanticModel\definition`  
**Checks**:
- Star schema enforcement
- Calculated column avoidance
- Bi-directional relationship limits
- Partition strategies

---

## Integration

### Orchestrator (Automatic)
```powershell
# orchestrate_full_model.ps1 Phase 4
& tooling/validation/validate_tmdl.ps1 -TmdlPath $definitionPath -AutoFix

if ($LASTEXITCODE -ne 0) {
    Write-Error "TMDL validation failed"
    exit 1
}
```

### Manual Testing
```powershell
# Validate specific TMDL file
.\validate_tmdl.ps1 -TmdlPath "showcases\aurora_group\semantic_models\Commercial.SemanticModel\definition\tables\_Measures.tmdl"

# Validate entire model
.\validate_tmdl.ps1 -TmdlPath "showcases\aurora_group\semantic_models\Commercial.SemanticModel\definition" -AutoFix
```

### CI/CD (run_all_checks.ps1)
TMDL BPA validation runs in **run_all_checks.ps1** as step **19d2**: for each `*.SemanticModel\definition` under `$DistRoot` (products/fabric/powerbi/dist), `validate_tmdl.ps1` is invoked with `-TmdlPath <definitionPath>`. No auto-fix in CI; validation-only. Failed runs are recorded in the consolidated check results and contribute to the overall exit code.

---

## Auto-Fix Logic

### TMDL-001: Pure TAB Indentation
```powershell
# Before (❌)
table dim_date
  lineageTag: abc123    # Tab+Space

# After (✅)
table dim_date
 lineageTag: abc123     # Pure TAB
```

### TMDL-002: Description Property → /// Comment
```powershell
# Before (❌)
measure 'Sales' = SUM([Amount])
 description: "Total sales amount"
 formatString: #,0.00

# After (✅)
/// Total sales amount
measure 'Sales' = SUM([Amount])
 formatString: #,0.00
```

### TMDL-003: M-Expression let...in Wrap
```powershell
# Before (❌)
partition _Measures = m
 source = #table(type table [], {})

# After (✅)
partition _Measures = m
 source =
  let
   Source = #table(type table [], {})
  in
   Source
```

### TMDL-010: LineageTag Generation
```powershell
# Before (❌)
measure 'Sales' = SUM([Amount])
 formatString: #,0.00

# After (✅)
measure 'Sales' = SUM([Amount])
 formatString: #,0.00
 lineageTag: a1b2c3d4-1234-5678-9abc-def012345678
```

---

## BPA Rules Reference

All validation scripts read from `tooling/linters/powerbi/bpa-rules-*.json`:

| Rule File | Scope | Auto-Fixable | Integration |
|-----------|-------|--------------|-------------|
| bpa-rules-tmdl.json | TMDL syntax | High (4/10 rules) | ✅ validate_tmdl.ps1 (run_all_checks 19d2) |
| bpa-rules-dax.json | DAX expressions | Partial (2/10 rules) | ✅ validate_dax.ps1 (run_all_checks 19c) |
| bpa-rules-report.json | Report visuals | Low | ✅ validate_report.ps1 (run_all_checks 19f) |
| bpa-rules-semanticmodel.json | Model structure | No | ✅ validate_semanticmodel.ps1 (run_all_checks 19d) |

---

## Output Format

All validation scripts return structured results:

```json
{
  "IsValid": false,
  "Errors": [
    {
      "RuleId": "TMDL-001",
      "RuleName": "Pure TAB Indentation Required",
      "Severity": "error",
      "File": "_Measures.tmdl",
      "Description": "Mixed Tab+Space indentation detected"
    }
  ],
  "Warnings": [...],
  "Info": [...],
  "Fixed": [
    {
      "File": "_Measures.tmdl",
      "Rules": ["TMDL-001", "TMDL-002"]
    }
  ]
}
```

---

## Extending Validation

To add new validation rules:

1. **Add rule to BPA JSON**: `tooling/linters/powerbi/bpa-rules-tmdl.json`
2. **Implement auto-fix** (if applicable): Add case in `validate_tmdl.ps1` switch statement
3. **Test**: Create test TMDL file with intentional violation
4. **Document**: Update `tmdl_best_practices.md` with new rule

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-02-03 | Initial validate_tmdl.ps1 with 10 BPA rules |
