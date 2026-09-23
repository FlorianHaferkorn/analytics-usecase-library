"""
Generate tool-specific agent config files from canonical docs/agent/ sources.

Reads docs/agent/rules/*.md + _index.yaml and docs/agent/skills/*.md + _index.yaml,
then produces tool-specific wrappers:
  - .cursor/rules/*.mdc        (YAML frontmatter + body)
  - .cursor/skills/*/SKILL.md  (YAML frontmatter + body)
  - skills/*/SKILL.md          (official Agent-Skills / skills-for-fabric layout, repo root)
  - .github/copilot-instructions.md  (concat of alwaysApply rules)

Version tracking:
  Skills carry a `version` field in _index.yaml (semver string, e.g. "1.2.0").
  The generator writes it into SKILL.md frontmatter so tools can detect breaking changes.
  Use check_skill_versions.py to audit missing versions or detect downgrade anomalies.

Usage:
    python tooling/generator/generate_tool_configs.py [--root .]
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]

AUTOGEN_HEADER = (
    "<!-- AUTO-GENERATED from docs/agent/ — do not edit directly. "
    "Run: python tooling/generator/generate_tool_configs.py -->\n\n"
)


def load_index(index_path: Path) -> Dict[str, Any]:
    if yaml is None:
        raise ImportError("PyYAML required: pip install pyyaml")
    return yaml.safe_load(index_path.read_text(encoding="utf-8-sig")) or {}


def generate_cursor_rules(root: Path) -> int:
    """Generate .cursor/rules/*.mdc from docs/agent/rules/."""
    rules_dir = root / "docs" / "agent" / "rules"
    index = load_index(rules_dir / "_index.yaml")
    out_dir = root / ".cursor" / "rules"
    out_dir.mkdir(parents=True, exist_ok=True)
    count = 0

    for name, meta in index.get("rules", {}).items():
        src = rules_dir / f"{name}.md"
        if not src.exists():
            print(f"  WARN: {src} not found, skipping")
            continue
        body = src.read_text(encoding="utf-8")

        # Build YAML frontmatter
        fm_lines = ["---"]
        fm_lines.append(f'description: {meta.get("description", name)}')
        if meta.get("globs"):
            fm_lines.append(f'globs: "{meta["globs"]}"')
        fm_lines.append(f'alwaysApply: {"true" if meta.get("alwaysApply") else "false"}')
        fm_lines.append("---")

        content = AUTOGEN_HEADER + "\n".join(fm_lines) + "\n\n" + body
        (out_dir / f"{name}.mdc").write_text(content, encoding="utf-8", newline="\n")
        count += 1

    return count


def generate_cursor_skills(root: Path) -> int:
    """Generate .cursor/skills/*/SKILL.md from docs/agent/skills/."""
    skills_dir = root / "docs" / "agent" / "skills"
    index = load_index(skills_dir / "_index.yaml")
    out_base = root / ".cursor" / "skills"
    count = 0

    for name, meta in index.get("skills", {}).items():
        src = skills_dir / f"{name}.md"
        if not src.exists():
            print(f"  WARN: {src} not found, skipping")
            continue
        body = src.read_text(encoding="utf-8")

        fm_lines = ["---"]
        fm_lines.append(f'name: {meta.get("name", name)}')
        fm_lines.append(f'description: {meta.get("description", name)}')
        # Write version if present — enables breaking-change detection
        version = meta.get("version")
        if version:
            fm_lines.append(f'version: "{version}"')
        fm_lines.append("---")

        out_dir = out_base / name
        out_dir.mkdir(parents=True, exist_ok=True)
        content = AUTOGEN_HEADER + "\n".join(fm_lines) + "\n\n" + body
        (out_dir / "SKILL.md").write_text(content, encoding="utf-8", newline="\n")
        count += 1

    return count


def generate_official_skills(root: Path) -> int:
    """Generate skills/<name>/SKILL.md in the official Agent-Skills / skills-for-fabric
    layout (frontmatter first, at repo root) so ALUCA overlay skills sit *alongside*
    the official vendor skills — ADR-0002 "extend, never fork"."""
    skills_dir = root / "docs" / "agent" / "skills"
    index = load_index(skills_dir / "_index.yaml")
    out_base = root / "skills"
    note = (
        "<!-- AUTO-GENERATED from docs/agent/skills/ — do not edit; "
        "run tooling/generator/generate_tool_configs.py -->\n\n"
    )
    count = 0

    for name, meta in index.get("skills", {}).items():
        src = skills_dir / f"{name}.md"
        if not src.exists():
            print(f"  WARN: {src} not found, skipping")
            continue
        body = src.read_text(encoding="utf-8")

        # Official format: YAML frontmatter MUST be first (line 1) — no header before it.
        fm_lines = ["---"]
        fm_lines.append(f'name: {meta.get("name", name)}')
        fm_lines.append(f'description: {meta.get("description", name)}')
        version = meta.get("version")
        if version:
            fm_lines.append(f'version: "{version}"')
        fm_lines.append("license: MIT")
        fm_lines.append("source: ALUCA (Analytics Library of Use Cases) — governance overlay")
        fm_lines.append("---")

        out_dir = out_base / name
        out_dir.mkdir(parents=True, exist_ok=True)
        content = "\n".join(fm_lines) + "\n\n" + note + body
        (out_dir / "SKILL.md").write_text(content, encoding="utf-8", newline="\n")
        count += 1

    return count


def generate_copilot_instructions(root: Path) -> int:
    """Generate .github/copilot-instructions.md from alwaysApply rules."""
    rules_dir = root / "docs" / "agent" / "rules"
    index = load_index(rules_dir / "_index.yaml")
    out_dir = root / ".github"
    out_dir.mkdir(parents=True, exist_ok=True)

    parts = [AUTOGEN_HEADER, "# Copilot Instructions\n\n"]
    count = 0

    for name, meta in index.get("rules", {}).items():
        if not meta.get("alwaysApply"):
            continue
        src = rules_dir / f"{name}.md"
        if not src.exists():
            continue
        parts.append(src.read_text(encoding="utf-8"))
        parts.append("\n---\n\n")
        count += 1

    (out_dir / "copilot-instructions.md").write_text("".join(parts), encoding="utf-8", newline="\n")
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate tool-specific agent configs")
    parser.add_argument("--root", type=Path, default=Path("."), help="Repository root")
    args = parser.parse_args()
    root = args.root.resolve()

    rules = generate_cursor_rules(root)
    skills = generate_cursor_skills(root)
    official = generate_official_skills(root)
    copilot = generate_copilot_instructions(root)
    print(
        f"Generated: {rules} Cursor rules, {skills} Cursor skills, "
        f"{official} official skills, {copilot} Copilot instructions"
    )


if __name__ == "__main__":
    main()
