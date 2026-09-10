"""
Markdown Writer

Emits Evidence.dev Markdown pages from assembled sections.
Mirrors Fabric's PBIPWriter but outputs .md files instead of PBIP JSON.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional


class MarkdownWriter:
    """Assemble and write Evidence Markdown pages."""

    def __init__(self, output_dir: Optional[Path] = None) -> None:
        self.output_dir = output_dir

    def assemble_page(
        self,
        title: str,
        description: str,
        sections: List[PageSection],
        frontmatter: Optional[dict] = None,
    ) -> str:
        """Assemble a complete Evidence Markdown page."""
        lines: List[str] = []

        # Frontmatter
        if frontmatter:
            lines.append("---")
            for k, v in frontmatter.items():
                lines.append(f"{k}: {v}")
            lines.append("---")
            lines.append("")

        # Title
        lines.append(f"# {title}")
        lines.append("")
        if description:
            lines.append(f"_{description}_")
            lines.append("")

        # Sections
        for section in sections:
            lines.append(f"## {section.heading}")
            lines.append("")
            for block in section.blocks:
                lines.append(block)
                lines.append("")

        # Trailing newline
        return "\n".join(lines)

    def write_page(self, filename: str, content: str, output_dir: Optional[Path] = None) -> Path:
        """Write a page to disk."""
        out = output_dir or self.output_dir
        if out is None:
            raise ValueError("output_dir must be set")
        out.mkdir(parents=True, exist_ok=True)
        path = out / filename
        path.write_text(content, encoding="utf-8", newline="\n")
        return path


class PageSection:
    """A section of an Evidence page (heading + content blocks)."""

    def __init__(self, heading: str, blocks: Optional[List[str]] = None) -> None:
        self.heading = heading
        self.blocks = blocks or []

    def add_block(self, block: str) -> None:
        self.blocks.append(block)
