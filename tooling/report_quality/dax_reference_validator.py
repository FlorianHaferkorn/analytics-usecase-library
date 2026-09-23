"""Validate report measure references against TMDL semantic model symbols."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from .models import Violation
from .pbir import iter_report_dirs


@dataclass
class TableSymbols:
    name: str
    columns: set[str] = field(default_factory=set)
    measures: dict[str, str] = field(default_factory=dict)


@dataclass
class ModelSymbols:
    tables: dict[str, TableSymbols] = field(default_factory=dict)

    @property
    def measure_names(self) -> set[str]:
        return {measure for table in self.tables.values() for measure in table.measures}

    @property
    def table_names(self) -> set[str]:
        return set(self.tables)

    def has_column(self, table: str, column: str) -> bool:
        return table in self.tables and column in self.tables[table].columns


_RE_TABLE = re.compile(r"^\s*table\s+(['\"]?)([^\s'\"]+)\1", re.MULTILINE)
_RE_COLUMN = re.compile(r"^\s+column\s+(['\"]?)([^'\"=\r\n]+)\1", re.MULTILINE)
_RE_MEASURE = re.compile(r"^\s+measure\s+(['\"])([^'\"]+)\1\s*=\s*(.*)$", re.MULTILINE)


def parse_tmdl_table(path: Path) -> TableSymbols | None:
    text = path.read_text(encoding="utf-8", errors="replace")
    table_match = _RE_TABLE.search(text)
    if not table_match:
        return None
    table = TableSymbols(name=table_match.group(2).strip())
    for col_match in _RE_COLUMN.finditer(text):
        table.columns.add(col_match.group(2).strip())
    for measure_match in _RE_MEASURE.finditer(text):
        table.measures[measure_match.group(2).strip()] = measure_match.group(3).strip()
    return table


def parse_semantic_models(dist_root: Path) -> ModelSymbols:
    """Parse all `.SemanticModel` folders and merge `_Measures` across domains."""

    symbols = ModelSymbols()
    for model_dir in sorted(dist_root.glob("*.SemanticModel")):
        tables_dir = model_dir / "definition" / "tables"
        if not tables_dir.exists():
            continue
        for tmdl in sorted(tables_dir.glob("*.tmdl")):
            table = parse_tmdl_table(tmdl)
            if not table:
                continue
            existing = symbols.tables.setdefault(table.name, TableSymbols(table.name))
            existing.columns.update(table.columns)
            existing.measures.update(table.measures)
    return symbols


def _walk(obj):
    if isinstance(obj, dict):
        yield obj
        for value in obj.values():
            yield from _walk(value)
    elif isinstance(obj, list):
        for item in obj:
            yield from _walk(item)


def visual_measure_references(visual_json: dict) -> set[str]:
    """Extract measure names from common PBIR query shapes.

    PBIR `queryRef` values are not enough to classify a reference as a measure;
    slicers and matrices often use the same shape for columns. Only explicit
    `Measure.Property` nodes are treated as measure references here.
    """

    refs: set[str] = set()
    for node in _walk(visual_json):
        measure = node.get("Measure")
        if isinstance(measure, dict):
            prop = measure.get("Property")
            if isinstance(prop, str):
                refs.add(prop)
    return refs


def validate_report_measure_references(dist_root: Path) -> list[Violation]:
    model_root = dist_root.parent if dist_root.name.endswith(".Report") and dist_root.is_dir() else dist_root
    symbols = parse_semantic_models(model_root)
    violations: list[Violation] = []
    for report_dir in iter_report_dirs(dist_root):
        for visual_file in report_dir.glob("definition/pages/*/visuals/*/visual.json"):
            try:
                import json

                visual = json.loads(visual_file.read_text(encoding="utf-8"))
            except Exception as exc:
                violations.append(
                    Violation(
                        "dax-reference:invalid-visual-json",
                        "critical",
                        visual_file.relative_to(dist_root).as_posix(),
                        f"Cannot parse visual JSON: {exc}",
                    )
                )
                continue
            missing = sorted(ref for ref in visual_measure_references(visual) if ref not in symbols.measure_names)
            for ref in missing:
                violations.append(
                    Violation(
                        "dax-reference:missing-measure",
                        "critical",
                        visual_file.relative_to(dist_root).as_posix(),
                        "Visual references a measure that is not defined in any TMDL _Measures table",
                        expected="defined TMDL measure",
                        actual=ref,
                    )
                )
    return violations
