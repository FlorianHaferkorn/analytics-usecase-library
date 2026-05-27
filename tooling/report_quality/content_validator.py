"""Content checks for generated report text."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .models import Violation

_PLACEHOLDER_RE = re.compile(
    r"\b(TODO|FIXME|XXX)\b|Lorem\s+ipsum|\{\{[^}]+\}\}|^\s*\.{3,}\s*$|^\s*<[^>]+>\s*$",
    re.IGNORECASE,
)

_DE_WORDS = {
    "der",
    "die",
    "das",
    "und",
    "mit",
    "von",
    "ist",
    "sind",
    "wird",
    "werden",
    "empfehlung",
    "massnahme",
    "maßnahme",
    "zeitraum",
}
_EN_WORDS = {
    "the",
    "and",
    "with",
    "from",
    "is",
    "are",
    "will",
    "recommendation",
    "action",
    "period",
    "evidence",
}


def _expr_literal(node: Any) -> str | None:
    if isinstance(node, str):
        return node
    if isinstance(node, dict):
        value = node.get("expr", {}).get("Literal", {}).get("Value")
        if isinstance(value, str):
            return value.strip("'")
    return None


def _extract_rich_text(value: str) -> str:
    value = value.strip().strip("'")
    try:
        data = json.loads(value)
    except json.JSONDecodeError:
        return value
    parts: list[str] = []
    for paragraph in data.get("paragraphs", []):
        for run in paragraph.get("textRuns", []):
            text = run.get("value")
            if isinstance(text, str):
                parts.append(text)
    return "".join(parts) if parts else value


def extract_texts(visual_json: dict) -> list[tuple[str, str]]:
    """Extract known report text carriers from a visual JSON object."""

    texts: list[tuple[str, str]] = []
    visual = visual_json.get("visual", {})
    objects = visual.get("objects", {}) or {}

    for key in ("_meridian_title", "_actionready_title"):
        value = objects.get(key)
        if isinstance(value, dict):
            text = value.get("text") or value.get("value")
            if isinstance(text, str) and text.strip():
                texts.append((key, text))

    for idx, item in enumerate(objects.get("vcBody", []) or []):
        if isinstance(item, dict):
            literal = _expr_literal(item.get("properties", {}).get("content"))
            if literal:
                texts.append((f"vcBody[{idx}].content", _extract_rich_text(literal)))

    title_items = (visual.get("visualContainerObjects", {}) or {}).get("title", []) or []
    for idx, item in enumerate(title_items):
        if isinstance(item, dict):
            literal = _expr_literal(item.get("properties", {}).get("text"))
            if literal:
                texts.append((f"visualContainerObjects.title[{idx}].text", literal))

    return texts


def check_text(text: str, *, max_chars: int = 160) -> list[str]:
    findings: list[str] = []
    stripped = text.strip()
    if not stripped:
        findings.append("Empty text")
    if _PLACEHOLDER_RE.search(stripped):
        findings.append("Placeholder or unfinished text detected")
    if max_chars > 0 and len(stripped) > max_chars:
        findings.append(f"Text length {len(stripped)} exceeds {max_chars}")

    tokens = re.findall(r"\b[\wäöüÄÖÜß]+\b", stripped.lower())
    de_hits = sum(1 for token in tokens if token in _DE_WORDS)
    en_hits = sum(1 for token in tokens if token in _EN_WORDS)
    if de_hits >= 2 and en_hits >= 2:
        findings.append(f"Mixed German/English content ({de_hits} DE tokens, {en_hits} EN tokens)")
    return findings


def validate_report_content(report_dir: Path, *, max_chars: int = 160) -> list[Violation]:
    violations: list[Violation] = []
    for visual_file in report_dir.glob("definition/pages/*/visuals/*/visual.json"):
        try:
            visual = json.loads(visual_file.read_text(encoding="utf-8"))
        except Exception:
            continue
        for location, text in extract_texts(visual):
            for finding in check_text(text, max_chars=max_chars):
                violations.append(
                    Violation(
                        "content:text-quality",
                        "critical",
                        f"{report_dir.name}/{visual_file.relative_to(report_dir)}#{location}",
                        finding,
                        actual=text,
                    )
                )
    return violations
