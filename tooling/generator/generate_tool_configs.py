"""
Generate tool-specific agent config files from canonical docs/agent/ sources.

Reads docs/agent/rules/*.md + _index.yaml and docs/agent/skills/*.md + _index.yaml,
then produces tool-specific wrappers:
  - skills/*/SKILL.md          (official Agent-Skills / skills-for-fabric layout, repo root)
  - .claude/skills/*/SKILL.md  (byte-identical copy: the only place Claude Code discovers
                                project skills; a copy, not a symlink, because the maintainer
                                works on Windows, where git symlinks need core.symlinks)
  - .github/copilot-instructions.md  (concat of alwaysApply rules)

Drift check:
  ``--check`` writes nothing and exits 1 if any generated file differs from what the
  generator would write, or if skills/ or .claude/skills/ hold a skill the index no longer
  lists. tooling/tests/test_generate_tool_configs.py runs it in the pytest suite.

Version tracking:
  Skills carry a `version` field in _index.yaml (semver string, e.g. "1.2.0").
  The generator writes it into SKILL.md frontmatter so tools can detect breaking changes.
  Use check_skill_versions.py to audit missing versions or detect downgrade anomalies.

Usage:
    python tooling/generator/generate_tool_configs.py [--root .] [--check]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

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


# Every skill is emitted to each of these directories with identical bytes.
SKILL_OUTPUT_DIRS = ("skills", ".claude/skills")


def _yaml_str(value: Any) -> str:
    """Quote a frontmatter scalar. A JSON string is a valid YAML double-quoted scalar, so a
    description with ': ' in it (e.g. "capacity: SKU floor") no longer breaks the parse."""
    return json.dumps(str(value), ensure_ascii=False)


def render_official_skills(root: Path) -> Dict[str, str]:
    """Render SKILL.md in the official Agent-Skills / skills-for-fabric layout (frontmatter
    first) so ALUCA overlay skills sit *alongside* the official vendor skills — ADR-0002
    "extend, never fork". Returns {repo-relative path: content} for every output dir."""
    skills_dir = root / "docs" / "agent" / "skills"
    index = load_index(skills_dir / "_index.yaml")
    note = (
        "<!-- AUTO-GENERATED from docs/agent/skills/ — do not edit; "
        "run tooling/generator/generate_tool_configs.py -->\n\n"
    )
    out: Dict[str, str] = {}

    for name, meta in index.get("skills", {}).items():
        src = skills_dir / f"{name}.md"
        if not src.exists():
            print(f"  WARN: {src} not found, skipping")
            continue
        body = src.read_text(encoding="utf-8")

        # Official format: YAML frontmatter MUST be first (line 1) — no header before it.
        # Claude Code reads `name` and `description` (the trigger text) from it.
        fm_lines = ["---"]
        fm_lines.append(f'name: {meta.get("name", name)}')
        fm_lines.append(f'description: {_yaml_str(meta.get("description", name))}')
        version = meta.get("version")
        if version:
            fm_lines.append(f'version: "{version}"')
        fm_lines.append("license: MIT")
        fm_lines.append("source: ALUCA (Analytics Library of Use Cases) — governance overlay")
        fm_lines.append("---")

        content = "\n".join(fm_lines) + "\n\n" + note + body
        for base in SKILL_OUTPUT_DIRS:
            out[f"{base}/{name}/SKILL.md"] = content

    return out


def render_copilot_instructions(root: Path) -> Dict[str, str]:
    """Render .github/copilot-instructions.md from alwaysApply rules."""
    rules_dir = root / "docs" / "agent" / "rules"
    index = load_index(rules_dir / "_index.yaml")

    parts = [AUTOGEN_HEADER, "# Copilot Instructions\n\n"]

    for name, meta in index.get("rules", {}).items():
        if not meta.get("alwaysApply"):
            continue
        src = rules_dir / f"{name}.md"
        if not src.exists():
            continue
        parts.append(src.read_text(encoding="utf-8"))
        parts.append("\n---\n\n")

    return {".github/copilot-instructions.md": "".join(parts)}


def orphan_skills(root: Path, expected: Dict[str, str]) -> List[str]:
    """SKILL.md files in an output dir that the index no longer produces."""
    orphans = []
    for base in SKILL_OUTPUT_DIRS:
        for f in sorted((root / base).glob("*/SKILL.md")):
            rel = f.relative_to(root).as_posix()
            if rel not in expected:
                orphans.append(rel)
    return orphans


def check_drift(root: Path, expected: Dict[str, str]) -> List[str]:
    """Return one finding per generated file that is missing, differs, or is orphaned."""
    findings = []
    for rel, content in sorted(expected.items()):
        f = root / rel
        if not f.is_file():
            findings.append(f"missing: {rel}")
        elif f.read_bytes() != content.encode("utf-8"):
            findings.append(f"differs: {rel}")
    findings.extend(f"orphan:  {rel}" for rel in orphan_skills(root, expected))
    return findings


def write_outputs(root: Path, expected: Dict[str, str]) -> None:
    for rel, content in expected.items():
        f = root / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(content, encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate tool-specific agent configs")
    parser.add_argument("--root", type=Path, default=Path("."), help="Repository root")
    parser.add_argument("--check", action="store_true",
                        help="write nothing; exit 1 if generated files drifted from their sources")
    args = parser.parse_args()
    root = args.root.resolve()

    skills = render_official_skills(root)
    copilot = render_copilot_instructions(root)
    expected = {**skills, **copilot}

    if args.check:
        findings = check_drift(root, expected)
        for line in findings:
            print(f"  DRIFT {line}")
        if findings:
            print(f"FAIL: {len(findings)} generated file(s) out of date — "
                  "run python tooling/generator/generate_tool_configs.py")
            return 1
        print(f"OK: {len(expected)} generated files match their sources")
        return 0

    write_outputs(root, expected)
    for rel in orphan_skills(root, expected):
        print(f"  WARN: orphaned {rel} (skill no longer in docs/agent/skills/_index.yaml) — remove it")
    n_skills = len(skills) // len(SKILL_OUTPUT_DIRS)
    print(f"Generated: {n_skills} official skills (x{len(SKILL_OUTPUT_DIRS)}: "
          f"{', '.join(SKILL_OUTPUT_DIRS)}), {len(copilot)} Copilot instructions file")
    return 0


if __name__ == "__main__":
    sys.exit(main())
