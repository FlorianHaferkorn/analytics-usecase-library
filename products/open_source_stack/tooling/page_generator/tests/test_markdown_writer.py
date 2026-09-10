"""Tests for the Markdown writer."""

import pytest
from pathlib import Path
from page_generator.markdown_writer import MarkdownWriter, PageSection


@pytest.fixture
def writer(tmp_path):
    return MarkdownWriter(output_dir=tmp_path)


class TestPageSection:
    def test_section_creation(self):
        s = PageSection("My Section", ["block1", "block2"])
        assert s.heading == "My Section"
        assert len(s.blocks) == 2

    def test_add_block(self):
        s = PageSection("Test")
        s.add_block("content")
        assert s.blocks == ["content"]


class TestAssemblePage:
    def test_basic_page(self, writer):
        sections = [PageSection("Section 1", ["Hello world"])]
        content = writer.assemble_page("Test Page", "A description", sections)
        assert "# Test Page" in content
        assert "_A description_" in content
        assert "## Section 1" in content
        assert "Hello world" in content

    def test_with_frontmatter(self, writer):
        content = writer.assemble_page(
            "Test", "", [],
            frontmatter={"title": "Test", "generated": "true"}
        )
        assert "---" in content
        assert "title: Test" in content
        assert "generated: true" in content

    def test_multiple_sections(self, writer):
        sections = [
            PageSection("KPIs", ["kpi block"]),
            PageSection("Trends", ["trend block"]),
        ]
        content = writer.assemble_page("Dashboard", "", sections)
        assert "## KPIs" in content
        assert "## Trends" in content
        assert content.index("## KPIs") < content.index("## Trends")


class TestWritePage:
    def test_write_creates_file(self, writer, tmp_path):
        path = writer.write_page("test.md", "# Hello")
        assert path.exists()
        assert path.read_text(encoding="utf-8") == "# Hello"
        assert path.name == "test.md"

    def test_write_creates_subdirs(self, tmp_path):
        out = tmp_path / "sub" / "dir"
        w = MarkdownWriter(output_dir=out)
        path = w.write_page("page.md", "content")
        assert path.exists()

    def test_write_raises_without_output_dir(self):
        w = MarkdownWriter()
        with pytest.raises(ValueError, match="output_dir"):
            w.write_page("test.md", "content")
