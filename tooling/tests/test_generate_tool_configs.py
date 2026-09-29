"""Tests for tooling/generator/generate_tool_configs.py.

The generated skills exist twice: skills/<name>/SKILL.md (official Agent-Skills layout) and
.claude/skills/<name>/SKILL.md (the only place Claude Code discovers project skills). Both are
copies, not symlinks, so these tests keep them honest: no drift against docs/agent/skills/,
byte-identical twins, and frontmatter that parses with `name` and a trigger `description`.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "tooling" / "generator"))

from generate_tool_configs import (  # noqa: E402
    SKILL_OUTPUT_DIRS,
    _yaml_str,
    check_drift,
    render_copilot_instructions,
    render_official_skills,
)


def _expected() -> dict:
    return {**render_official_skills(_REPO_ROOT), **render_copilot_instructions(_REPO_ROOT)}


def test_committed_outputs_match_generator():
    findings = check_drift(_REPO_ROOT, _expected())
    assert findings == [], (
        "generated agent configs drifted — run python tooling/generator/generate_tool_configs.py:\n"
        + "\n".join(findings)
    )


def test_every_skill_is_emitted_to_every_output_dir():
    skills = render_official_skills(_REPO_ROOT)
    names = {Path(rel).parent.name for rel in skills}
    assert names, "no skills rendered"
    for base in SKILL_OUTPUT_DIRS:
        assert {n for n in names if f"{base}/{n}/SKILL.md" in skills} == names
    assert ".claude/skills" in SKILL_OUTPUT_DIRS


@pytest.mark.parametrize("rel", sorted(render_official_skills(_REPO_ROOT)))
def test_skill_frontmatter_parses(rel):
    text = render_official_skills(_REPO_ROOT)[rel]
    assert text.startswith("---\n")
    meta = yaml.safe_load(text.split("---", 2)[1])
    assert meta["name"] == Path(rel).parent.name
    # Claude Code picks a skill by its description: it must say when to use it.
    assert "Use " in meta["description"], f"{rel}: description has no 'Use when/after' trigger"


def test_yaml_str_survives_colon():
    # "capacity: SKU floor" broke the unquoted frontmatter of recommend-fabric-capacity.
    value = "Recommend a Fabric capacity: SKU floor — and more"
    assert yaml.safe_load(f"d: {_yaml_str(value)}")["d"] == value


def test_check_detects_drift_and_orphans(tmp_path):
    expected = {"skills/a/SKILL.md": "x\n", ".claude/skills/a/SKILL.md": "x\n"}
    (tmp_path / "skills" / "a").mkdir(parents=True)
    (tmp_path / "skills" / "a" / "SKILL.md").write_text("y\n", encoding="utf-8")
    (tmp_path / ".claude" / "skills" / "old").mkdir(parents=True)
    (tmp_path / ".claude" / "skills" / "old" / "SKILL.md").write_text("z\n", encoding="utf-8")
    findings = check_drift(tmp_path, expected)
    assert "differs: skills/a/SKILL.md" in findings
    assert "missing: .claude/skills/a/SKILL.md" in findings
    assert "orphan:  .claude/skills/old/SKILL.md" in findings
