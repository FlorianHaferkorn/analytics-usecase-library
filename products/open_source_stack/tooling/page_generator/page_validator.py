"""
Page Validator

Validates generated Evidence pages against governance rules.
Mirrors Fabric's visual_validator.py but checks Markdown structure
and Evidence component usage instead of PBIP JSON.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from .component_builder import COMPONENT_MAP


PLACEHOLDER_SQL_PATTERNS = (
    re.compile(r"--\s*TODO:", re.IGNORECASE),
    re.compile(r"--\s*\[manual\]", re.IGNORECASE),
)


@dataclass
class ValidationResult:
    """Result of validating a single page."""
    page_path: str
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return len(self.errors) == 0


def validate_page(content: str, page_path: str = "<unknown>") -> ValidationResult:
    """Validate an Evidence page against framework rules."""
    result = ValidationResult(page_path=page_path)

    # Rule 1: Page must have a title (# heading)
    if not re.search(r"^# .+", content, re.MULTILINE):
        result.errors.append("Missing page title (# heading)")

    # Rule 2: Must have at least one SQL block
    sql_blocks = re.findall(r"```sql\s+(\w+)", content)
    if not sql_blocks:
        result.errors.append("No SQL query blocks found")

    # Rule 3: Must have at least one Evidence component
    valid_components = set(COMPONENT_MAP.values())
    component_pattern = r"<(\w+)\s"
    found_components = re.findall(component_pattern, content)
    evidence_components = [c for c in found_components if c in valid_components]
    if not evidence_components:
        result.errors.append("No Evidence components found (BigValue, LineChart, etc.)")

    # Rule 4: Every SQL block should be referenced by a component
    for qname in sql_blocks:
        if f"{{{qname}}}" not in content.replace(f"```sql {qname}", ""):
            result.warnings.append(f"SQL block '{qname}' may not be referenced by any component")

    # Rule 5: No SELECT * (SQL best practice)
    if re.search(r"SELECT\s+\*", content, re.IGNORECASE):
        result.errors.append("SELECT * is not allowed — use explicit column names")

    # Rule 6: Generated SQL must not contain manual placeholder markers
    for pattern in PLACEHOLDER_SQL_PATTERNS:
        if pattern.search(content):
            result.errors.append("Placeholder SQL is not allowed — replace TODO/manual translations")
            break

    # Rule 7: Design tokens — only governed classes
    governed_tokens = {"fill-primary", "text-brand-header", "bg-surface"}
    custom_classes = re.findall(r'class="([^"]*)"', content)
    for cls_str in custom_classes:
        for cls in cls_str.split():
            if cls.startswith(("fill-", "text-brand-", "bg-")) and cls not in governed_tokens:
                result.warnings.append(f"Non-governed design token: {cls}")

    # Rule 8: 3-30-300 structure — should have section headings
    has_3s = bool(re.search(r"##.*3.Second|##.*KPI|##.*Headline", content, re.IGNORECASE))
    has_30s = bool(re.search(r"##.*30.Second|##.*Main|##.*Trend", content, re.IGNORECASE))
    if not has_3s:
        result.warnings.append("Missing 3-second layer section")
    if not has_30s:
        result.warnings.append("Missing 30-second layer section")

    # Rules 9-12: boutique craft rubric 1.1 minimum (Meridian BO-288), binding for generated pages.
    if re.search(r"^generated:\s*true\s*$", content, re.MULTILINE):
        result.errors.extend(rubric_findings(content))

    return result


# A number on the page: a stat, a chart or a table outside a provenance <Details> block.
_NUMBER_COMPONENTS = ("BigValue", "LineChart", "BarChart", "AreaChart", "DataTable")
_CHART_COMPONENTS = ("LineChart", "BarChart", "AreaChart")
_DETAILS = re.compile(r"<Details\b.*?</Details>", re.DOTALL)
_COMPONENT = re.compile(r"<(" + "|".join(_NUMBER_COMPONENTS) + r")\s+data=\{(\w+)\}")


def rubric_findings(content: str) -> List[str]:
    """Rubric 1.1 minimum per page: BC-DV-08 (one filter row first, every query reads it), BC-TRANS-04 (a
    visible as-of stamp per number), BC-TRANS-01/02 (query and catalog reference one click away) and
    BC-DV-09 (table view per chart, exportable). Returns one finding per breach, empty when the page passes."""
    findings: List[str] = []
    masked = _DETAILS.sub(lambda m: " " * len(m.group(0)), content)  # same offsets, provenance blocks blanked
    numbers = list(_COMPONENT.finditer(masked))
    if not numbers:
        return findings

    date_range = re.search(r"<DateRange\s+name=(\w+)", content)
    if not date_range or date_range.start() > numbers[0].start():
        findings.append("BC-DV-08: no date-range filter above the first chart/stat/table")
    else:
        token = "${inputs." + date_range.group(1) + "."
        for m in re.finditer(r"```sql\s+(\w+)\n(.*?)```", masked, re.DOTALL):
            if m.start() > date_range.start() and token not in m.group(2):
                findings.append(f"BC-DV-08: query '{m.group(1)}' ignores the filter '{date_range.group(1)}'")

    for i, m in enumerate(numbers):
        component, query = m.group(1), m.group(2)
        end = numbers[i + 1].start() if i + 1 < len(numbers) else len(content)
        tail = content[m.end():end]
        if "_Data as of <Value" not in tail:
            findings.append(f"BC-TRANS-04: {component} '{query}' has no visible as-of stamp")
        details = _DETAILS.search(tail)
        if not details or "Catalog id:" not in details.group(0) or "```text" not in details.group(0):
            findings.append(f"BC-TRANS-01/02: {component} '{query}' has no query and catalog reference")
        elif component in _CHART_COMPONENTS and (
                f"<DataTable data={{{query}}} downloadable=true" not in details.group(0)):
            findings.append(f"BC-DV-09: {component} '{query}' has no exportable table view")
    return findings


def validate_pages_directory(pages_dir: Path) -> List[ValidationResult]:
    """Validate all .md files in a directory."""
    results = []
    for md_file in sorted(pages_dir.glob("*.md")):
        content = md_file.read_text(encoding="utf-8")
        results.append(validate_page(content, str(md_file)))
    return results
