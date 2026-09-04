"""Validate capability packs against the closed capability-pack contract.

Three independent dimensions, reported separately so a failure says which rule
was broken:

* ``schema``      - the JSON Schema contract (closed, no unknown fields).
* ``reference``   - stable ids resolve and are unique inside the pack.
* ``neutrality``  - no customer identifier, address, path or organization token.

Run from the repository root::

    python tooling/validation/check_capability_packs.py
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import yaml

SCHEMA_RELATIVE_PATH = "tooling/generator/schemas/capability_pack.schema.json"
PACK_GLOB = "core/capabilities/*/capability.yaml"

CATEGORY_SCHEMA = "schema"
CATEGORY_REFERENCE = "reference"
CATEGORY_NEUTRALITY = "neutrality"

# Tokens that identify a customer or a delivering organization. A reusable pack
# carries neither.
#
# Until 2026-09-04 the customer names sat here in clear text. Two defects in one, the
# same pair found that day in the solo product's `gate_projektplan.py`: the list ages
# silently (nobody edits a validator when an engagement starts), and it puts the very
# identifiers into the repository that it exists to keep out — this file was three of
# the eleven hits its sibling checker reported.
#
# Customer names now come from `.kundendaten-sperrliste.json`, the one place they may
# live (gitignored, see `tooling/validation/check_kundendaten.py`). Whoever onboards an
# engagement maintains it anyway, so this validator follows along by itself. The
# delivering organization stays here: it is not customer data and does not change.
_DELIVERY_ORG_TOKENS = ("nagarro",)


def _blocklist_tokens(repo_root: Path) -> tuple[str, ...]:
    """Customer identifiers from the blocklist, lowercased.

    A missing blocklist is not silently tolerated — a validator that reports success
    without its rules is worse than none (same doctrine as `check_kundendaten.py`).
    """
    p = repo_root / ".kundendaten-sperrliste.json"
    if not p.exists():
        raise SystemExit(
            f"blocklist missing ({p}). The neutrality check cannot verify anything "
            "without it and therefore reports no success."
        )
    data = json.loads(p.read_text(encoding="utf-8"))
    names = [n for n in ((data.get("begriffe") or {}).get("kunde") or []) if n]
    if not names:
        raise SystemExit("blocklist carries no customer names — nothing to check against.")
    return tuple(sorted({n.lower() for n in names}, key=len, reverse=True))

LEAK_PATTERNS = (
    ("tenant or object identifier", re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.I)),
    ("mail address", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")),
    ("absolute path", re.compile(r"(?:[A-Za-z]:\\|[A-Za-z]:/|/home/|/Users/)")),
)


@dataclass(frozen=True)
class Finding:
    category: str
    path: str
    message: str

    def __str__(self) -> str:  # pragma: no cover - formatting only
        return f"[{self.category}] {self.path}: {self.message}"


def load_schema(repo_root: Path) -> dict[str, Any]:
    return json.loads((repo_root / SCHEMA_RELATIVE_PATH).read_text(encoding="utf-8"))


def _ids(items: Iterable[dict[str, Any]]) -> list[str]:
    return [str(item.get("id")) for item in items if isinstance(item, dict) and "id" in item]


def _duplicates(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    duplicated: list[str] = []
    for value in values:
        if value in seen and value not in duplicated:
            duplicated.append(value)
        seen.add(value)
    return duplicated


def check_schema(document: Any, schema: dict[str, Any]) -> list[Finding]:
    import jsonschema

    validator = jsonschema.Draft202012Validator(schema)
    findings: list[Finding] = []
    for error in sorted(validator.iter_errors(document), key=lambda e: list(e.absolute_path)):
        location = "/".join(str(part) for part in error.absolute_path) or "<root>"
        findings.append(Finding(CATEGORY_SCHEMA, location, error.message))
    return findings


def check_references(document: Any) -> list[Finding]:
    findings: list[Finding] = []
    if not isinstance(document, dict):
        return findings
    capability = document.get("capability")
    if not isinstance(capability, dict):
        return findings

    sections = {
        name: capability.get(name) or []
        for name in (
            "applicability",
            "methodology",
            "questions",
            "evidence_requirements",
            "decisions",
            "recommendation_rules",
            "architecture_rules",
            "work_packages",
            "skill_requirements",
            "estimation_rules",
            "tool_dependencies",
            "outputs",
            "readiness_gates",
            "acceptance_tests",
        )
    }
    known = {name: set(_ids(items)) for name, items in sections.items()}

    for name, items in sections.items():
        for duplicate in _duplicates(_ids(items)):
            findings.append(
                Finding(CATEGORY_REFERENCE, f"capability/{name}", f"duplicate id '{duplicate}'")
            )

    def resolve(where: str, refs: Any, target: str) -> None:
        if refs is None:
            return
        values = refs if isinstance(refs, list) else [refs]
        for value in values:
            if value is None:
                continue
            if value not in known[target]:
                findings.append(
                    Finding(CATEGORY_REFERENCE, where, f"'{value}' does not resolve in {target}")
                )

    for step in sections["methodology"]:
        resolve(f"capability/methodology/{step.get('id')}/produces", step.get("produces"), "outputs")

    for question in sections["questions"]:
        base = f"capability/questions/{question.get('id')}"
        resolve(f"{base}/applicability_refs", question.get("applicability_refs"), "applicability")
        resolve(f"{base}/evidence_requirement_refs", question.get("evidence_requirement_refs"), "evidence_requirements")
        resolve(f"{base}/decision_ref", question.get("decision_ref"), "decisions")

    option_ids_by_decision: dict[str, set[str]] = {}
    for decision in sections["decisions"]:
        decision_id = str(decision.get("id"))
        base = f"capability/decisions/{decision_id}"
        options = decision.get("options") or []
        option_ids_by_decision[decision_id] = set(_ids(options))
        for duplicate in _duplicates(_ids(options)):
            findings.append(Finding(CATEGORY_REFERENCE, f"{base}/options", f"duplicate id '{duplicate}'"))
        resolve(f"{base}/question_refs", decision.get("question_refs"), "questions")
        recommended = decision.get("recommendation_option_ref")
        if recommended is not None and recommended not in option_ids_by_decision[decision_id]:
            findings.append(
                Finding(CATEGORY_REFERENCE, f"{base}/recommendation_option_ref", f"'{recommended}' is not an option of this decision")
            )
        for option in options:
            resolve(
                f"{base}/options/{option.get('id')}/evidence_requirement_refs",
                option.get("evidence_requirement_refs"),
                "evidence_requirements",
            )

    for rule in sections["recommendation_rules"]:
        base = f"capability/recommendation_rules/{rule.get('id')}"
        decision_ref = rule.get("decision_ref")
        resolve(f"{base}/decision_ref", decision_ref, "decisions")
        option_ref = rule.get("recommend_option_ref")
        options = option_ids_by_decision.get(str(decision_ref), set())
        if decision_ref in known["decisions"] and option_ref not in options:
            findings.append(
                Finding(CATEGORY_REFERENCE, f"{base}/recommend_option_ref", f"'{option_ref}' is not an option of decision '{decision_ref}'")
            )

    for rule in sections["architecture_rules"]:
        resolve(f"capability/architecture_rules/{rule.get('id')}/decision_refs", rule.get("decision_refs"), "decisions")

    for package in sections["work_packages"]:
        package_id = str(package.get("id"))
        base = f"capability/work_packages/{package_id}"
        resolve(f"{base}/decision_refs", package.get("decision_refs"), "decisions")
        resolve(f"{base}/output_refs", package.get("output_refs"), "outputs")
        resolve(f"{base}/depends_on", package.get("depends_on"), "work_packages")
        if package_id in (package.get("depends_on") or []):
            findings.append(Finding(CATEGORY_REFERENCE, f"{base}/depends_on", "a work package cannot depend on itself"))

    for skill in sections["skill_requirements"]:
        resolve(f"capability/skill_requirements/{skill.get('id')}/work_package_refs", skill.get("work_package_refs"), "work_packages")

    for estimate in sections["estimation_rules"]:
        base = f"capability/estimation_rules/{estimate.get('id')}"
        resolve(f"{base}/work_package_ref", estimate.get("work_package_ref"), "work_packages")
        low, high = estimate.get("low"), estimate.get("high")
        if isinstance(low, (int, float)) and isinstance(high, (int, float)) and low > high:
            findings.append(Finding(CATEGORY_REFERENCE, base, "low effort is greater than high effort"))

    for dependency in sections["tool_dependencies"]:
        resolve(
            f"capability/tool_dependencies/{dependency.get('id')}/evidence_requirement_ref",
            dependency.get("evidence_requirement_ref"),
            "evidence_requirements",
        )

    for output in sections["outputs"]:
        base = f"capability/outputs/{output.get('id')}"
        resolve(f"{base}/produced_by_work_package_refs", output.get("produced_by_work_package_refs"), "work_packages")
        resolve(f"{base}/readiness_gate_refs", output.get("readiness_gate_refs"), "readiness_gates")

    for gate in sections["readiness_gates"]:
        base = f"capability/readiness_gates/{gate.get('id')}"
        resolve(f"{base}/minimum_evidence_refs", gate.get("minimum_evidence_refs"), "evidence_requirements")
        resolve(f"{base}/decision_refs", gate.get("decision_refs"), "decisions")

    for test in sections["acceptance_tests"]:
        base = f"capability/acceptance_tests/{test.get('id')}"
        resolve(f"{base}/readiness_gate_ref", test.get("readiness_gate_ref"), "readiness_gates")
        resolve(f"{base}/evidence_requirement_refs", test.get("evidence_requirement_refs"), "evidence_requirements")

    return findings


def _walk_strings(node: Any, path: str = "") -> Iterable[tuple[str, str]]:
    if isinstance(node, dict):
        for key, value in node.items():
            yield from _walk_strings(value, f"{path}/{key}" if path else str(key))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from _walk_strings(value, f"{path}[{index}]")
    elif isinstance(node, str):
        yield path or "<root>", node


def check_neutrality(document: Any, forbidden: tuple[str, ...] = ()) -> list[Finding]:
    """`forbidden` carries the customer identifiers; the caller reads them from the
    blocklist. Empty means the delivery-organization tokens are checked and customer
    names are not — that is a caller error, so `main` never passes an empty tuple."""
    findings: list[Finding] = []
    tokens = tuple(forbidden) + _DELIVERY_ORG_TOKENS
    for path, value in _walk_strings(document):
        lowered = value.lower()
        for token in tokens:
            if re.search(rf"\b{re.escape(token)}\b", lowered):
                findings.append(
                    Finding(CATEGORY_NEUTRALITY, path, f"organization or customer token '{token}'")
                )
        for label, pattern in LEAK_PATTERNS:
            if pattern.search(value):
                findings.append(Finding(CATEGORY_NEUTRALITY, path, f"{label} in a reusable pack"))
    return findings


def validate_capability_pack(document: Any, schema: dict[str, Any],
                             forbidden: tuple[str, ...] = ()) -> list[Finding]:
    """Return every finding. Schema failures do not hide reference or neutrality ones."""
    findings = check_schema(document, schema)
    findings.extend(check_references(document))
    findings.extend(check_neutrality(document, forbidden))
    return findings


def load_document(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate capability packs against the closed contract.")
    parser.add_argument("--root", default=".", help="repository root (default: current directory)")
    parser.add_argument("paths", nargs="*", help="explicit pack files; default is every core capability pack")
    args = parser.parse_args(argv)

    repo_root = Path(args.root).resolve()
    schema = load_schema(repo_root)
    forbidden = _blocklist_tokens(repo_root)
    targets = [Path(p) for p in args.paths] or sorted(repo_root.glob(PACK_GLOB))

    if not targets:
        print("No capability pack found.")
        return 0

    failed = False
    for target in targets:
        findings = validate_capability_pack(load_document(target), schema, forbidden)
        relative = target.relative_to(repo_root) if target.is_absolute() else target
        if findings:
            failed = True
            print(f"FAIL {relative} ({len(findings)} finding(s))")
            for finding in findings:
                print(f"  {finding}")
        else:
            print(f"OK   {relative}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
