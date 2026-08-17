"""architecture_blueprint_cli — one-command standalone workflow (ADR-0015 follow-up).

Chains the four verbs into a single, deterministic run and writes all artifacts:

  derive → audit (conformance) → ground → render (per stack)

Usage:
  python -m tooling.superversion.architecture_blueprint_cli \
      --inputs inputs.json --dest out/ --stack fabric

`--inputs` is a JSON file matching the `derive_blueprint` inputs shape. Output under
`--dest`: blueprint.json, hitl.json, OPEN_QUESTIONS.md, open_questions.json,
CONFORMANCE.md, mcp_grounding.json, retrieval_decisions.md, and render/<stack>/… .
Non-zero exit if conformance is red.

`hitl.json` and `OPEN_QUESTIONS.md` are not the same list and neither replaces the other.
`hitl.json` stays what it always was — the deriver's own flat gap list, read by other
code. `OPEN_QUESTIONS.md` is the sheet a customer reads: it carries those gaps *and* the
defaults we applied without asking *and* the mirrored decisions, each with a way to the
answer (`open_questions`, SHARED_SUBSTANCE class C).
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
from tooling.superversion.open_questions import (
    collect_open_questions,
    open_questions_markdown,
    questions_without_a_way,
)
from tooling.superversion import arch_targets


_RESULT_SUFFIXES = (".csv", ".json", ".tsv")


def read_source_schema_results(directory: Path | None) -> dict[str, str]:
    """Answered source introspections, keyed by the file stem (= the source's slug).

    Reading files is I/O, so it stays on this side; interpreting them is the mirrored
    emitter's job. Anything that is not a result payload (a README, the emitted
    `.sql`/`.md` questions) is ignored rather than fed in as a broken answer.
    """
    if directory is None:
        return {}
    directory = Path(directory)
    if not directory.is_dir():
        raise FileNotFoundError(f"--source-schema-results: no such directory: {directory}")
    return {p.stem: p.read_text(encoding="utf-8")
            for p in sorted(directory.iterdir())
            if p.is_file() and p.suffix.lower() in _RESULT_SUFFIXES}


def run(inputs: dict[str, Any], dest: Path, stack: str = "fabric",
        source_schema_results: Path | None = None) -> dict[str, Any]:
    """Run the full workflow and write artifacts under ``dest``. Returns a summary."""
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)

    derived = derive_blueprint(inputs)
    bp = derived["blueprint"]
    validate_blueprint(bp)  # schema-valid or raises

    score = conformance(bp)
    grounding = emit_grounding(bp)
    results = read_source_schema_results(source_schema_results)
    rendered = arch_targets.render(stack, bp, dest=dest / "render",
                                   source_schema_results=results)

    (dest / "blueprint.json").write_text(
        json.dumps(bp, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    (dest / "hitl.json").write_text(
        json.dumps(derived["hitl"], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (dest / "CONFORMANCE.md").write_text(score.to_markdown(), encoding="utf-8")
    for rel, content in grounding.items():
        (dest / rel).write_text(content, encoding="utf-8")

    questions = collect_open_questions(inputs, derived)
    (dest / "open_questions.json").write_text(
        json.dumps(questions, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (dest / "OPEN_QUESTIONS.md").write_text(open_questions_markdown(questions), encoding="utf-8")

    return {
        "stack": stack,
        "source_schemas_answered": sorted(results),
        "hitl": derived["hitl"],
        "questions": questions["summary"],
        "questions_without_a_way": questions_without_a_way(questions),
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
    parser.add_argument("--source-schema-results", type=Path, default=None,
                        help="directory of answered source introspections "
                             "(<source>.csv/.json), as produced by render/fabric/source_schema/")
    args = parser.parse_args(argv)

    inputs = json.loads(Path(args.inputs).read_text(encoding="utf-8"))
    summary = run(inputs, args.dest, args.stack, args.source_schema_results)

    print(f"stack: {summary['stack']}")
    answered = summary["source_schemas_answered"]
    print(f"source schemas answered: {', '.join(answered) if answered else '(none yet)'}")
    print("conformance:")
    for pattern, verdict in summary["conformance"].items():
        print(f"  {pattern}: {verdict}")
    if summary["hitl"]:
        print("HITL gaps:")
        for g in summary["hitl"]:
            print(f"  - {g}")
    q = summary["questions"]
    print(f"open questions: {q['total']} ({q['open']} for the customer, "
          f"{q['preset']} decided by us, {q['proposed']} proposed)")
    # A question with no way to answer it is a blank text box. Printed, never silent —
    # the point of the sheet is that it comes back filled in.
    if summary["questions_without_a_way"]:
        print(f"  without a way to the answer: {', '.join(summary['questions_without_a_way'])}")
    if q["unreported_gaps"]:
        print(f"  gaps with no question attached: {', '.join(q['unreported_gaps'])}")
    print(f"artifacts written under: {args.dest}")
    # red conformance → non-zero exit (a gate the caller can wire into CI)
    return 0 if summary["conformance_ok"] else 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
