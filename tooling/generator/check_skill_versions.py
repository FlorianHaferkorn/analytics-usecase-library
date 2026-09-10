"""
check_skill_versions.py — audit skill and rule version fields.

Reads docs/agent/skills/_index.yaml and docs/agent/rules/_index.yaml and reports:
  - Skills/rules missing a version field
  - Skills with non-semver version strings
  - Skill .md files that have changed since the version was last bumped
    (detected by comparing git blame dates of the .md and the version bump in _index.yaml)

Exit codes:
  0 — all skills versioned, no anomalies
  1 — missing versions or anomalies found

Usage:
    python tooling/generator/check_skill_versions.py [--root .] [--strict]
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import yaml
except ImportError:
    if __name__ == "__main__":
        print("ERROR: PyYAML required — pip install pyyaml", file=sys.stderr)
        sys.exit(1)
    raise

SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")


def load_index(path: Path) -> Dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8-sig")) or {}


def git_last_modified(path: Path) -> Optional[str]:
    """Return ISO date of last git commit touching this file, or None."""
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%ci", "--", str(path)],
            capture_output=True, text=True, check=True
        , encoding="utf-8", errors="replace")
        return result.stdout.strip() or None
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def check_index(
    index_path: Path,
    category: str,   # "skills" or "rules"
    source_dir: Path,
    strict: bool,
) -> List[str]:
    """Return list of violation messages."""
    violations: List[str] = []
    index = load_index(index_path)
    entries = index.get(category, {})

    for name, meta in entries.items():
        if meta is None:
            meta = {}

        version: Optional[str] = meta.get("version")

        # Check 1: version field present
        if not version:
            violations.append(f"  MISSING  {category}/{name}: no version field in _index.yaml")
            continue

        # Check 2: valid semver
        if not SEMVER_RE.match(str(version)):
            violations.append(
                f"  INVALID  {category}/{name}: version '{version}' is not semver (expected X.Y.Z)"
            )

        # Check 3 (strict): detect stale version — .md modified after _index.yaml
        if strict:
            src_file = source_dir / f"{name}.md"
            if src_file.exists():
                md_date = git_last_modified(src_file)
                idx_date = git_last_modified(index_path)
                if md_date and idx_date and md_date > idx_date:
                    violations.append(
                        f"  STALE    {category}/{name}: {src_file.name} last changed {md_date[:10]}"
                        f" but _index.yaml last updated {idx_date[:10]}"
                        f" — consider bumping version to signal breaking changes"
                    )

    return violations


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit skill and rule version fields")
    parser.add_argument("--root", type=Path, default=Path("."), help="Repository root")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Also warn when .md source is newer than _index.yaml (potential stale version)",
    )
    args = parser.parse_args()
    root = args.root.resolve()

    all_violations: List[str] = []

    # Check skills
    skills_index = root / "docs" / "agent" / "skills" / "_index.yaml"
    skills_dir = root / "docs" / "agent" / "skills"
    if skills_index.exists():
        v = check_index(skills_index, "skills", skills_dir, args.strict)
        if v:
            print("Skills:")
            print("\n".join(v))
        all_violations.extend(v)
    else:
        print(f"WARN: {skills_index} not found, skipping skills check", file=sys.stderr)

    # Check rules (rules don't require versions, but report missing ones as info)
    rules_index = root / "docs" / "agent" / "rules" / "_index.yaml"
    rules_dir = root / "docs" / "agent" / "rules"
    if rules_index.exists():
        rules_index_data = load_index(rules_index)
        rules_missing = [
            name for name, meta in rules_index_data.get("rules", {}).items()
            if not (meta or {}).get("version")
        ]
        if rules_missing:
            # Rules are optional for versioning — print as info, not violation
            print(f"INFO: {len(rules_missing)} rule(s) have no version (optional for rules):")
            for r in rules_missing:
                print(f"  - {r}")

    if all_violations:
        print(f"\n{len(all_violations)} violation(s) found.", file=sys.stderr)
        sys.exit(1)

    print(f"Skill version check passed — all skills versioned.")
    sys.exit(0)


if __name__ == "__main__":
    main()
