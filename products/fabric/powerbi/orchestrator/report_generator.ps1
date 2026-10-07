# Retired fallback (07.10.2026, ALUCA D-686, SIG-2609-005/-008).
#
# This script used to write a report.json with "sections"/"visualContainers"/"config" into
# <UseCase>.Report\definition\ when no Python was found. That is the PBIR-Legacy shape inside a
# PBIR folder: neither format, not PBIP-compliant (docs/PBIP_REPORT_STRUCTURE.md).
#
# PBIR is GA and the default report format. Power BI Desktop converts PBIR-Legacy reports
# silently on save (backup kept 30 days in Desktop, 28 days in the service). ALUCA therefore
# emits PBIR only, through products/fabric/powerbi/tooling/page_scaffold_generator/
# generate_full_report.py (Python 3 is a prerequisite of the orchestrator, AUTOMATION_FLOW.md).
#
# The script is kept so that old calls fail with a reason instead of "file not found".

param(
	[Parameter(Mandatory = $true)]
	[string]$UseCase,
	[string]$TemplateName,
	[string]$OutputPath,
	[string]$SemanticModelRelativePath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

throw ("report_generator.ps1 is retired: it wrote the PBIR-Legacy shape (sections) and is no " +
	"longer used. Install Python 3 and run products\fabric\powerbi\tooling\page_scaffold_generator\" +
	"generate_full_report.py (PBIR, GA and default format). Use case: $UseCase")
