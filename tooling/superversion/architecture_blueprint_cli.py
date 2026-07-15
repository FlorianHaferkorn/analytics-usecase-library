"""architecture_blueprint_cli — one-command standalone workflow (ADR-0015 follow-up).

Chains the four verbs into a single, deterministic run and writes all artifacts:

  derive → audit (conformance) → ground → render (per stack)

Usage:
  python -m tooling.superversion.architecture_blueprint_cli \
      --inputs inputs.json --dest out/ --stack fabric

`--inputs` is a JSON file matching the `derive_blueprint` inputs shape. Output under
`--dest`: blueprint.json, hitl.json, CONFORMANCE.md, mcp_grounding.json,
retrieval_decisions.md, and render/<stack>/… . Non-zero exit if conformance is red.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from tooling.superversion.architecture_blueprint import (
    derive_blueprint,
    emit_grounding,
    validate_blueprint,
)
from tooling.superversion.eval.blueprint_conformance import conformance
from tooling.superversion import arch_targets


def run(inputs: dict[str, Any], dest: Path, stack: str = "fabric") -> dict[str, Any]:
    """Run the full workflow and write artifacts under ``dest``. Returns a summary."""
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)

    derived = derive_blueprint(inputs)
    bp = derived["blueprint"]
    validate_blueprint(bp)  # schema-valid or raises

    score = conformance(bp)
    grounding = emit_grounding(bp)
    rendered = arch_targets.render(stack, bp, dest=dest / "render")

    (dest / "blueprint.json").write_text(
        json.dumps(bp, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    (dest / "hitl.json").write_text(
        json.dumps(derived["hitl"], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (dest / "CONFORMANCE.md").write_text(score.to_markdown(), encoding="utf-8")
    for rel, content in grounding.items():
        (dest / rel).write_text(content, encoding="utf-8")

    return {
        "stack": stack,
        "hitl": derived["hitl"],
        "conformance": score.scorecard,
        "conformance_ok": score.ok,
        "grounding_files": sorted(grounding),
        "render_files": sorted(rendered),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ArchitectureBlueprint standalone workflow")
    parser.add_argument("--inputs", type=Path, required=True, help="JSON file: derive_blueprint inputs")
    parser.add_argument("--dest", type=Path, required=True, help="output directory")
    parser.add_argument("--stack", default="fabric", choices=sorted(arch_targets.available()),
                        help="render target stack")
    args = parser.parse_args(argv)

    inputs = json.loads(Path(args.inputs).read_text(encoding="utf-8"))
    summary = run(inputs, args.dest, args.stack)

    print(f"stack: {summary['stack']}")
    print("conformance:")
    for pattern, verdict in summary["conformance"].items():
        print(f"  {pattern}: {verdict}")
    if summary["hitl"]:
        print("HITL gaps:")
        for g in summary["hitl"]:
            print(f"  - {g}")
    print(f"artifacts written under: {args.dest}")
    # red conformance → non-zero exit (a gate the caller can wire into CI)
    return 0 if summary["conformance_ok"] else 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
