"""Structural PBIR invariants and deterministic fixes."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, runtime_checkable

from .models import Severity, Violation
from .pbir import ParsedPage, ParsedReport, page_pointer, parse_report, visual_pointer, write_json

DEFAULT_PAGE_WIDTH = 1920
DEFAULT_PAGE_HEIGHT = 1080


@runtime_checkable
class Invariant(Protocol):
    name: str
    severity: Severity

    def check(self, report: ParsedReport, page: ParsedPage) -> list[Violation]: ...


@dataclass
class ReportSpec:
    """A collection of structural invariants for one or more report pages."""

    invariants: list[Invariant] = field(default_factory=list)

    def check(self, report: ParsedReport) -> list[Violation]:
        violations: list[Violation] = []
        for page in report.pages.values():
            for invariant in self.invariants:
                violations.extend(invariant.check(report, page))
        return violations


@dataclass
class PageSize:
    width: int = DEFAULT_PAGE_WIDTH
    height: int = DEFAULT_PAGE_HEIGHT
    severity: Severity = "critical"
    name: str = "page:size"

    def check(self, report: ParsedReport, page: ParsedPage) -> list[Violation]:
        violations: list[Violation] = []
        if page.page_json.get("width") != self.width:
            violations.append(
                Violation(
                    self.name,
                    self.severity,
                    page_pointer(report.report_dir, page, "width"),
                    "Unexpected page width",
                    expected=self.width,
                    actual=page.page_json.get("width"),
                )
            )
        if page.page_json.get("height") != self.height:
            violations.append(
                Violation(
                    self.name,
                    self.severity,
                    page_pointer(report.report_dir, page, "height"),
                    "Unexpected page height",
                    expected=self.height,
                    actual=page.page_json.get("height"),
                )
            )
        return violations

    def fix(self, _report: ParsedReport, page: ParsedPage, _violation: Violation) -> bool:
        changed = False
        if page.page_json.get("width") != self.width:
            page.page_json["width"] = self.width
            changed = True
        if page.page_json.get("height") != self.height:
            page.page_json["height"] = self.height
            changed = True
        if changed:
            write_json(page.page_dir / "page.json", page.page_json)
        return changed


@dataclass
class RequiredSlots:
    overview_slots: set[str] = field(default_factory=lambda: {"KPI_Cards", "Main_1", "Main_2", "Slicer_Date"})
    detail_slots: set[str] = field(default_factory=lambda: {"Detail_Matrix", "Smart_Narrative", "ActionPanel"})
    severity: Severity = "critical"
    name: str = "page:required-slots"

    def check(self, report: ParsedReport, page: ParsedPage) -> list[Violation]:
        expected: set[str] = set()
        label = f"{page.name} {page.display_name}".lower()
        if "overview" in label:
            expected = self.overview_slots
        elif "detail" in label:
            expected = self.detail_slots
        if not expected:
            return []
        missing = sorted(expected - set(page.visuals))
        if not missing:
            return []
        return [
            Violation(
                self.name,
                self.severity,
                page_pointer(report.report_dir, page),
                f"Missing required visual slots: {missing}",
                expected=sorted(expected),
                actual=sorted(page.visuals),
            )
        ]


@dataclass
class ForbiddenVisualTypes:
    forbidden: set[str] = field(default_factory=lambda: {"pieChart", "donutChart", "gauge", "treemap"})
    severity: Severity = "critical"
    name: str = "visual:forbidden-type"

    def check(self, report: ParsedReport, page: ParsedPage) -> list[Violation]:
        violations: list[Violation] = []
        for visual_name, visual in page.visuals.items():
            visual_type = visual.get("visual", {}).get("visualType")
            if visual_type in self.forbidden:
                violations.append(
                    Violation(
                        self.name,
                        self.severity,
                        visual_pointer(report.report_dir, page, visual_name, "visual/visualType"),
                        "Forbidden visual type",
                        expected=f"not in {sorted(self.forbidden)}",
                        actual=visual_type,
                    )
                )
        return violations


@dataclass
class VisualWithinPage:
    severity: Severity = "critical"
    name: str = "visual:bounds"

    def check(self, report: ParsedReport, page: ParsedPage) -> list[Violation]:
        width = page.page_json.get("width", DEFAULT_PAGE_WIDTH)
        height = page.page_json.get("height", DEFAULT_PAGE_HEIGHT)
        violations: list[Violation] = []
        for visual_name, visual in page.visuals.items():
            pos = visual.get("position") or {}
            x = pos.get("x")
            y = pos.get("y")
            w = pos.get("width")
            h = pos.get("height")
            if not all(isinstance(v, (int, float)) for v in (x, y, w, h)):
                violations.append(
                    Violation(
                        self.name,
                        self.severity,
                        visual_pointer(report.report_dir, page, visual_name, "position"),
                        "Visual position must include numeric x, y, width, height",
                        actual=pos,
                    )
                )
                continue
            if x < 0 or y < 0 or w <= 0 or h <= 0 or x + w > width or y + h > height:
                violations.append(
                    Violation(
                        self.name,
                        self.severity,
                        visual_pointer(report.report_dir, page, visual_name, "position"),
                        "Visual is outside page bounds",
                        expected={"page_width": width, "page_height": height},
                        actual=pos,
                    )
                )
        return violations


def default_spec() -> ReportSpec:
    return ReportSpec(invariants=[PageSize(), RequiredSlots(), ForbiddenVisualTypes(), VisualWithinPage()])


def check_report(report_dir: Path, spec: ReportSpec | None = None) -> list[Violation]:
    return (spec or default_spec()).check(parse_report(report_dir))
