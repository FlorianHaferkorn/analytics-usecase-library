"""Tests for the Evidence page validator."""

from pathlib import Path

import pytest
from page_generator.page_validator import ValidationResult, rubric_findings, validate_page


VALID_PAGE = """\
# Sales Performance

_Overview dashboard_

## 3-Second Layer — KPI Headlines

```sql net_sales
SELECT SUM(amount) AS value, 'Net Sales' AS label
FROM gold.fact_sales
WHERE period = '2026-01'
```

<BigValue data={net_sales} value="value" title="Net Sales" />

## 30-Second Layer — Trends

```sql sales_trend
SELECT period, SUM(amount) AS metric_value
FROM gold.fact_sales
GROUP BY period
ORDER BY period
```

<LineChart data={sales_trend} x="period" y="metric_value" title="Trend" />
"""


class TestValidatePage:
    def test_valid_page_passes(self):
        result = validate_page(VALID_PAGE, "test.md")
        assert result.passed
        assert result.errors == []

    def test_missing_title(self):
        content = "No title here\n```sql q\nSELECT 1\n```\n<BigValue data={q} />"
        result = validate_page(content)
        assert not result.passed
        assert any("title" in e.lower() for e in result.errors)

    def test_no_sql_blocks(self):
        content = "# Title\n\n<BigValue data={q} />"
        result = validate_page(content)
        assert any("SQL" in e for e in result.errors)

    def test_no_evidence_components(self):
        content = "# Title\n\n```sql q\nSELECT 1 AS v\n```\n\nJust text."
        result = validate_page(content)
        assert any("component" in e.lower() for e in result.errors)

    def test_select_star_rejected(self):
        content = (
            "# Title\n\n## 3-Second Layer\n\n"
            "```sql q\nSELECT * FROM table\n```\n"
            "<BigValue data={q} />"
        )
        result = validate_page(content)
        assert any("SELECT *" in e for e in result.errors)

    def test_placeholder_sql_rejected(self):
        content = (
            "# Title\n\n## 3-Second Layer\n\n"
            "```sql q\n-- TODO: translate DAX: CALCULATE(...)\n```\n"
            "<BigValue data={q} />"
        )
        result = validate_page(content)
        assert any("Placeholder SQL" in e for e in result.errors)

    def test_unreferenced_sql_warns(self):
        content = (
            "# Title\n\n## KPI Headlines\n\n"
            "```sql orphan_query\nSELECT 1 AS v\n```\n"
            "```sql used_query\nSELECT 1 AS v\n```\n"
            "<BigValue data={used_query} />"
        )
        result = validate_page(content)
        assert any("orphan_query" in w for w in result.warnings)

    def test_non_governed_design_token_warns(self):
        content = (
            '# Title\n\n## 3-Second Layer\n\n'
            '```sql q\nSELECT 1 AS v\n```\n'
            '<BigValue data={q} />\n'
            '<div class="fill-custom-blue">x</div>'
        )
        result = validate_page(content)
        assert any("fill-custom-blue" in w for w in result.warnings)

    def test_missing_3s_layer_warns(self):
        content = (
            "# Title\n\n## Some Section\n\n"
            "```sql q\nSELECT 1 AS v\n```\n"
            "<BigValue data={q} />"
        )
        result = validate_page(content)
        assert any("3-second" in w.lower() for w in result.warnings)

    def test_governed_tokens_do_not_warn(self):
        content = (
            '# Title\n\n## 3-Second Layer\n\n'
            '```sql q\nSELECT 1 AS v\n```\n'
            '<BigValue data={q} />\n'
            '<div class="fill-primary bg-surface text-brand-header">ok</div>'
        )
        result = validate_page(content)
        token_warnings = [w for w in result.warnings if "token" in w.lower()]
        assert token_warnings == []


class TestValidationResult:
    def test_passed_with_no_errors(self):
        r = ValidationResult(page_path="test.md")
        assert r.passed

    def test_failed_with_errors(self):
        r = ValidationResult(page_path="test.md", errors=["bad"])
        assert not r.passed


# -- Rubric 1.1 minimum for generated pages (Meridian BO-288, 22.10.2026) ----------------------------

PAGES = Path(__file__).resolve().parents[3] / "evidence_app" / "pages"
GENERATED = "---\ngenerated: true\n---\n"


def _committed_pages():
    pages = sorted(PAGES.glob("*.md"))
    assert pages, "no Evidence pages found -- the check below would pass on nothing"
    return pages


class TestRubricMinimum:
    def test_every_committed_page_meets_the_rubric_minimum(self):
        for page in _committed_pages():
            content = page.read_text(encoding="utf-8")
            assert "generated: true" in content, page.name
            assert rubric_findings(content) == [], page.name

    def test_the_valid_handwritten_page_breaches_every_rule_once_marked_generated(self):
        # Counter-check: the gate is not empty -- the plain page from above fails each rubric rule.
        found = rubric_findings(GENERATED + VALID_PAGE)
        kinds = {f.split(":")[0] for f in found}
        assert kinds == {"BC-DV-08", "BC-TRANS-04", "BC-TRANS-01/02"}
        assert not validate_page(GENERATED + VALID_PAGE).passed
        assert validate_page(VALID_PAGE).passed  # handwritten pages stay outside the rubric gate

    def _page(self):
        return next(p for p in _committed_pages() if p.name.endswith("_overview.md")).read_text(encoding="utf-8")

    def test_a_query_without_the_filter_is_found(self):
        page = self._page().replace(
            "\n  AND period BETWEEN '${inputs.period_range.start}' AND '${inputs.period_range.end}'", "", 1)
        assert any(f.startswith("BC-DV-08: query") for f in rubric_findings(page))

    def test_a_filter_below_the_first_number_is_found(self):
        page = self._page()
        tag = "<DateRange name=period_range data={period_options} dates=period />"
        assert tag in page
        page = page.replace(tag, "") + "\n" + tag + "\n"
        assert "BC-DV-08: no date-range filter above the first chart/stat/table" in rubric_findings(page)

    def test_a_missing_as_of_stamp_is_found(self):
        page = self._page().replace("_Data as of <Value", "_<Value", 1)
        assert any(f.startswith("BC-TRANS-04") for f in rubric_findings(page))

    def test_a_chart_without_table_view_is_found(self):
        page = self._page()
        assert "<LineChart" in page
        q = page.split("<LineChart data={", 1)[1].split("}", 1)[0]
        page = page.replace(f"<DataTable data={{{q}}} downloadable=true />", "")
        assert f"BC-DV-09: LineChart '{q}' has no exportable table view" in rubric_findings(page)

    def test_a_missing_catalog_reference_is_found(self):
        page = self._page().replace("- Catalog id:", "- Id:", 1)
        assert any(f.startswith("BC-TRANS-01/02") for f in rubric_findings(page))


class TestEvidencePin:
    def test_evidence_packages_are_pinned_to_an_exact_version(self):
        import json
        import re
        pkg = json.loads((PAGES.parent / "package.json").read_text(encoding="utf-8"))
        deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
        evidence = {k: v for k, v in deps.items() if k.startswith("@evidence-dev/")}
        assert "@evidence-dev/evidence" in evidence
        for name, spec in evidence.items():
            assert re.fullmatch(r"\d+\.\d+\.\d+", spec), f"{name} is not pinned: {spec}"
