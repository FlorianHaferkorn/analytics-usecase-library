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

    # Rule 6: Design tokens — only governed classes
    governed_tokens = {"fill-primary", "text-brand-header", "bg-surface"}
    custom_classes = re.findall(r'class="([^"]*)"', content)
    for cls_str in custom_classes:
        for cls in cls_str.split():
            if cls.startswith(("fill-", "text-brand-", "bg-")) and cls not in governed_tokens:
                result.warnings.append(f"Non-governed design token: {cls}")

    # Rule 7: 3-30-300 structure — should have section headings
    has_3s = bool(re.search(r"##.*3.Second|##.*KPI|##.*Headline", content, re.IGNORECASE))
    has_30s = bool(re.search(r"##.*30.Second|##.*Main|##.*Trend", content, re.IGNORECASE))
    if not has_3s:
        result.warnings.append("Missing 3-second layer section")
    if not has_30s:
        result.warnings.append("Missing 30-second layer section")

    return result


def validate_pages_directory(pages_dir: Path) -> List[ValidationResult]:
    """Validate all .md files in a directory."""
    results = []
    for md_file in sorted(pages_dir.glob("*.md")):
        content = md_file.read_text(encoding="utf-8")
        results.append(validate_page(content, str(md_file)))
    return results
