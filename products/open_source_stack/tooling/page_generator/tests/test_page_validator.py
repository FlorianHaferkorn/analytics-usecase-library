"""Tests for the Evidence page validator."""

import pytest
from page_generator.page_validator import validate_page, ValidationResult


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
