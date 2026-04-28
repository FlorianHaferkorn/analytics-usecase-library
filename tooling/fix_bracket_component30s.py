#!/usr/bin/env python3
"""
fix_bracket_component30s.py — Remove schema-invalid fields from component_30s items.

Fields ibcs_scenario, annotations (and their sub-items) are not in the
usecase_bracket.schema.json component_30s items definition (additionalProperties: false).
Removes them from all UseCase_Bracket.yaml files in core/usecases/core/.
"""
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BRACKETS_ROOT = REPO_ROOT / "core/usecases/core"


def fix_bracket(path: Path) -> bool:
    """Remove invalid component_30s properties. Returns True if file was modified."""
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)

    in_component_30s = False
    skip_annotation_block = False
    new_lines = []
    changed = False

    for line in lines:
        stripped = line.rstrip()

        # Track when we're inside component_30s
        if re.match(r"\s+component_30s:", stripped):
            in_component_30s = True
            skip_annotation_block = False
            new_lines.append(line)
            continue

        # End of component_30s when we hit page_2_execution at same or lesser indent
        if in_component_30s and re.match(r"\s+page_2_execution:", stripped):
            in_component_30s = False
            skip_annotation_block = False

        if in_component_30s:
            # Remove ibcs_scenario lines
            if re.match(r"\s+ibcs_scenario:", stripped):
                changed = True
                continue

            # Start of annotations block — remove the annotations: key line
            if re.match(r"\s+annotations:", stripped):
                skip_annotation_block = True
                changed = True
                continue

            # Inside annotations block: remove annotation items (- label:) and sub-items (anchor:)
            if skip_annotation_block:
                if re.match(r"\s+- label:", stripped) or re.match(r"\s+anchor:", stripped):
                    changed = True
                    continue
                else:
                    # End of annotation block when we hit something else at same or lesser indent
                    skip_annotation_block = False

        new_lines.append(line)

    if changed:
        path.write_text("".join(new_lines), encoding="utf-8")

    return changed


def main():
    brackets = sorted(BRACKETS_ROOT.rglob("UseCase_Bracket.yaml"))
    if not brackets:
        print(f"No UseCase_Bracket.yaml files found under {BRACKETS_ROOT}")
        sys.exit(0)

    fixed = 0
    for bracket in brackets:
        if fix_bracket(bracket):
            print(f"  Fixed: {bracket.relative_to(REPO_ROOT)}")
            fixed += 1
        else:
            print(f"  OK:    {bracket.relative_to(REPO_ROOT)}")

    print(f"\n{fixed}/{len(brackets)} bracket(s) fixed.")


if __name__ == "__main__":
    main()
