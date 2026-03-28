"""
Evidence Page Generator

Main orchestrator that generates Evidence.dev Markdown pages from IR
and UseCase Bracket governance files. Mirrors the Fabric
PageScaffoldGenerator but emits Markdown + SQL instead of PBIP JSON.

Usage:
    python -m products.open_source_stack.tooling.page_generator.generator \
        --use-case COM-001 --ir-path tooling/ir/out/ir_v1.json
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config_loader import ConfigLoader
from .component_builder import ComponentBuilder
from .layout_calculator import LayoutCalculator
from .markdown_writer import MarkdownWriter, PageSection
from .page_validator import validate_page
from .sql_builder import SqlBuilder


class EvidencePageGenerator:
    """Generate Evidence.dev dashboard pages from IR and governance."""

    def __init__(
        self,
        use_case_id: str,
        ir_path: Optional[Path] = None,
        repo_root: Optional[Path] = None,
        output_dir: Optional[Path] = None,
        showcase: str = "aurora_group",
    ) -> None:
        self.use_case_id = use_case_id
        self.ir_path = ir_path
        self.showcase = showcase

        self.config_loader = ConfigLoader(repo_root)
        self.component_builder = ComponentBuilder()
        self.layout_calculator = LayoutCalculator()
        self.sql_builder = SqlBuilder()
        self.repo_root = self.config_loader.repo_root

        out = output_dir or (
            self.repo_root / "products" / "open_source_stack" / "evidence_app" / "pages"
        )
        self.markdown_writer = MarkdownWriter(output_dir=out)

        self._ir: Optional[Dict[str, Any]] = None
        self._bracket: Optional[Dict[str, Any]] = None

    def load(self) -> None:
        """Load IR and bracket configuration."""
        self._ir = self.config_loader.load_ir(self.ir_path)
        self._bracket = self.config_loader.load_bracket(self.use_case_id)

    def generate(self) -> List[Path]:
        """Generate all pages for the use case. Returns list of written file paths."""
        if self._ir is None or self._bracket is None:
            self.load()

        assert self._ir is not None
        assert self._bracket is not None

        pages_written: List[Path] = []

        # Get KPIs linked to this use case from IR
        kpi_nodes = self.config_loader.get_kpis_for_use_case(self._ir, self.use_case_id)

        # Get UX layout from bracket
        ux_layout = self._bracket.get("ux_layout", {})
        report_pages = ux_layout.get("report_pages", [])

        if not report_pages:
            # Fallback: generate a single overview page
            report_pages = [{"page_id": "overview", "page_type": "overview"}]

        for page_def in report_pages:
            page_id = page_def.get("page_id", "overview")
            content = self._build_page(page_id, page_def, kpi_nodes)

            # Validate before writing
            result = validate_page(content, page_id)

            filename = f"{self.use_case_id.lower().replace('-', '_')}_{page_id}.md"
            path = self.markdown_writer.write_page(filename, content)
            pages_written.append(path)

            if result.errors:
                print(f"  WARN: {filename} has validation errors: {result.errors}", file=sys.stderr)
            if result.warnings:
                print(f"  INFO: {filename} warnings: {result.warnings}", file=sys.stderr)

        return pages_written

    def _get_kpi_label(self, kpi: Dict[str, Any]) -> str:
        """Get a human-readable label for a KPI. IR uses various field names."""
        return kpi.get("title") or kpi.get("label") or kpi.get("id", "")

    def _build_page(
        self,
        page_id: str,
        page_def: Dict[str, Any],
        kpi_nodes: List[Dict[str, Any]],
    ) -> str:
        """Build a single Evidence page."""
        title = self.config_loader.get_use_case_title(self._ir, self.use_case_id)  # type: ignore[arg-type]
        page_type = page_def.get("page_type", "overview")
        description = f"{title} — {page_type.replace('_', ' ').title()}"

        sections: List[PageSection] = []

        # 3-Second Layer — KPI Headlines
        kpi_section = PageSection("3-Second Layer — KPI Headlines")
        for kpi in kpi_nodes:
            kpi_id = kpi.get("id", "")
            label = self._get_kpi_label(kpi)
            table = self.sql_builder.infer_table_from_kpi(kpi)
            spec = kpi.get("measure_spec", {})
            dax = spec.get("dax_expression", "")
            sql_expr = self.sql_builder.dax_to_sql_expression(dax)
            qname = self.sql_builder.kpi_to_query_name(kpi_id)

            kpi_section.add_block(
                self.sql_builder.build_kpi_headline_query(qname, table, sql_expr, label)
            )
            kpi_section.add_block(
                self.component_builder.build_kpi_card(qname, title=label)
            )
        sections.append(kpi_section)

        # 30-Second Layer — Trends
        trend_section = PageSection("30-Second Layer — Trends")
        for kpi in kpi_nodes[:3]:  # Top 3 KPIs as trends
            kpi_id = kpi.get("id", "")
            label = self._get_kpi_label(kpi)
            table = self.sql_builder.infer_table_from_kpi(kpi)
            spec = kpi.get("measure_spec", {})
            dax = spec.get("dax_expression", "")
            sql_expr = self.sql_builder.dax_to_sql_expression(dax)
            qname = f"{self.sql_builder.kpi_to_query_name(kpi_id)}_trend"

            trend_section.add_block(
                self.sql_builder.build_trend_query(qname, table, sql_expr)
            )
            trend_section.add_block(
                self.component_builder.build_chart(
                    "trend_line", qname, x="period", y="metric_value", title=label
                )
            )
        sections.append(trend_section)

        # 300-Second Layer — Detail (for detail pages)
        if page_type in ("detail", "diagnostics"):
            detail_section = PageSection("300-Second Layer — Diagnostics")
            if kpi_nodes:
                table = self.sql_builder.infer_table_from_kpi(kpi_nodes[0])
                qname = "detail_data"
                columns = ["entity", "period", "kpi_value", "driver"]
                detail_section.add_block(
                    self.sql_builder.build_detail_query(qname, table, columns)
                )
                detail_section.add_block(
                    self.component_builder.build_data_table(qname)
                )
            sections.append(detail_section)

        # Grid layout wrapper (when bracket defines ux_layout_rules with grid_blueprint)
        ux_rules = self._bracket.get("ux_layout_rules", {}) if self._bracket else {}  # type: ignore[union-attr]
        grid_blueprint = ux_rules.get("grid_blueprint")
        if grid_blueprint:
            slots = self.layout_calculator.parse_slots(grid_blueprint)
            errors = self.layout_calculator.validate_slots(slots)
            if errors:
                print(f"  WARN: Grid layout errors: {errors}", file=sys.stderr)

        frontmatter = {
            "title": title,
            "use_case": self.use_case_id,
            "generated": "true",
        }

        return self.markdown_writer.assemble_page(
            title=title,
            description=description,
            sections=sections,
            frontmatter=frontmatter,
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Evidence pages from IR")
    parser.add_argument("--use-case", required=True, help="Use case ID (e.g. COM-001)")
    parser.add_argument("--ir-path", type=Path, help="Path to ir_v1.json")
    parser.add_argument("--output-dir", type=Path, help="Output directory for pages")
    parser.add_argument("--showcase", default="aurora_group", help="Showcase name for theme")
    args = parser.parse_args()

    gen = EvidencePageGenerator(
        use_case_id=args.use_case,
        ir_path=args.ir_path,
        output_dir=args.output_dir,
        showcase=args.showcase,
    )
    gen.load()
    pages = gen.generate()
    for p in pages:
        print(f"  Generated: {p}")


if __name__ == "__main__":
    main()
