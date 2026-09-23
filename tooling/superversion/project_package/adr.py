"""Render deterministic Architecture Decision Records from the decision-set SoT."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


STATUS = {
    "draft": "Draft", "proposed": "Proposed", "approved": "Accepted",
    "rejected": "Rejected", "deferred": "Deferred", "superseded": "Superseded",
}


def render_adr_register(document: dict[str, Any]) -> str:
    definitions = {item["id"]: item for item in document["definitions"]}
    lines = ["# Architecture Decision Register", "", "| ADR | Decision | Status | Decider | Date | Evidence |", "|---|---|---|---|---|---|"]
    ordered = sorted(document["instances"], key=lambda item: ((definitions.get(item["definition_ref"], {}).get("adr") or {}).get("record_id", "ZZZ-9999"), item["id"]))
    for instance in ordered:
        definition = definitions[instance["definition_ref"]]
        adr = definition.get("adr") or {}
        approval = instance["approval"]
        lines.append(
            f"| {adr.get('record_id', 'ADR missing')} | {definition['title']} | {STATUS[approval['state']]} | "
            f"{approval.get('decided_by') or '—'} | {approval.get('decided_at') or '—'} | "
            f"{', '.join(approval.get('evidence_refs', [])) or '—'} |"
        )
    for instance in ordered:
        definition = definitions[instance["definition_ref"]]
        adr = definition.get("adr") or {}
        approval = instance["approval"]
        selection = instance["selection"]
        selected = selection.get("custom_value") or selection.get("option_ref") or "Not selected"
        lines.extend([
            "", f"## {adr.get('record_id', 'ADR missing')} · {definition['title']}", "",
            f"**Status:** {STATUS[approval['state']]}  ",
            f"**Decision owner:** {definition['decider']['text']}  ",
            f"**Decision:** {selected}  ",
            f"**Decision date:** {approval.get('decided_at') or 'Not recorded'}  ",
            f"**Evidence:** {', '.join(approval.get('evidence_refs', [])) or 'Not recorded'}", "",
            "### Context", "", adr.get("context") or definition["question"]["technical_text"], "",
            "### Recommendation", "", definition["recommendation"].get("text") or "No recommendation recorded.", "",
            "### Options and consequences", "",
        ])
        detail_by_source = {item["source_value"]: item for item in definition["option_details"]}
        for option in definition["options"]:
            detail = detail_by_source.get(option["label"], {})
            lines.extend([
                f"#### {option['label']}", "",
                detail.get("text") or option["label"], "",
                f"- Advantages: {'; '.join(detail.get('advantages', [])) or 'Not recorded'}",
                f"- Disadvantages: {'; '.join(detail.get('disadvantages', [])) or 'Not recorded'}",
                f"- Implication: {detail.get('implication') or 'Not recorded'}", "",
            ])
        lines.extend(["### Approval rationale", "", approval.get("rationale") or "Not recorded.", "", "### If unresolved", "", definition["consequence_if_unresolved"]])
    return "\n".join(lines) + "\n"


def _load(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    return json.loads(text) if path.suffix.lower() == ".json" else yaml.safe_load(text)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--decision-set", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    rendered = render_adr_register(_load(args.decision_set))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8", newline="\n")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
