"""Lossless adapter from mirrored Meridian decision proposals."""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Mapping, Sequence

from ..hashes import canonical_sha256


SOURCE_FIELDS = frozenset(
    {
        "id",
        "topic",
        "gap",
        "proposal",
        "derived_from",
        "confidence",
        "status",
        "alternatives",
        "optionen",
        "decider",
        "if_undecided",
        "ermittlung",
        "kunde",
        "faelligkeit",
        "markers",
    }
)

FIELD_MAPPING = {
    "id": ("source.raw_id", "definition.id", "instance.id"),
    "topic": ("title",),
    "gap": ("question.technical_text",),
    "proposal": ("recommendation.text", "options[kind=proposal]"),
    "derived_from": ("recommendation.basis",),
    "confidence": ("recommendation.confidence_raw", "recommendation.confidence"),
    "status": ("initialization", "selection.state", "approval.state"),
    "alternatives": ("options[kind=alternative]",),
    "optionen": ("option_details",),
    "decider": ("decider.text",),
    "if_undecided": ("consequence_if_unresolved",),
    "ermittlung": ("resolution_method",),
    "kunde": ("customer_copy",),
    "faelligkeit": ("due.raw", "due.gate"),
    "markers": ("placeholder_refs",),
}

_NON_IDENTIFIER = re.compile(r"[^a-z0-9]+")
_CONFIDENCE = {
    "hoch": "high",
    "high": "high",
    "mittel": "medium",
    "medium": "medium",
    "niedrig": "low",
    "low": "low",
    "keine": "none",
    "none": "none",
}


def _identifier(value: str) -> str:
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    normalized = _NON_IDENTIFIER.sub("_", ascii_value.lower()).strip("_")
    if not normalized or not normalized[0].isalpha():
        normalized = f"id_{normalized}"
    return normalized[:64]


def _due_gate(raw: str) -> str:
    value = raw.casefold()
    if "produktiv" in value or "production" in value or "prod" in value:
        return "before_production"
    if value.strip():
        return "before_build"
    return "unscheduled"


def _domain_scope(raw_id: str, scope_ref_by_slug: Mapping[str, str]) -> tuple[str, list[str]]:
    if "·" not in raw_id:
        return raw_id, []
    base, slug = raw_id.split("·", 1)
    if slug not in scope_ref_by_slug:
        raise ValueError(f"unresolved domain scope for decision {raw_id!r}: {slug!r}")
    return f"{base}_{slug}", [scope_ref_by_slug[slug]]


def _adapt_one(
    proposal: Mapping[str, Any], scope_ref_by_slug: Mapping[str, str]
) -> tuple[dict[str, Any], dict[str, Any]]:
    actual_fields = frozenset(proposal)
    if actual_fields != SOURCE_FIELDS:
        missing = sorted(SOURCE_FIELDS - actual_fields)
        extra = sorted(actual_fields - SOURCE_FIELDS)
        raise ValueError(f"decision proposal contract drift; missing={missing}, extra={extra}")

    raw_id = str(proposal["id"])
    scoped_id, scope_refs = _domain_scope(raw_id, scope_ref_by_slug)
    slug = _identifier(scoped_id)
    definition_id = f"d_meridian_{slug}"[:64]
    instance_id = f"di_meridian_{slug}"[:64]
    recommendation = proposal["proposal"]
    options: list[dict[str, str]] = []
    if recommendation:
        options.append({"id": "proposal", "label": str(recommendation), "kind": "proposal"})
    options.extend(
        {"id": f"alternative_{index:03d}", "label": str(label), "kind": "alternative"}
        for index, label in enumerate(proposal["alternatives"], start=1)
    )
    if not options:
        options.append({"id": "custom_input", "label": "Customer-specific answer", "kind": "alternative"})

    option_details = [
        {
            "source_value": str(option.get("wert", "")),
            "text": str(option.get("text", "")),
            "recommended": bool(option.get("empfohlen", False)),
            "advantages": [str(value) for value in option.get("vorteile", [])],
            "disadvantages": [str(value) for value in option.get("nachteile", [])],
            "limitations": [
                {
                    "text": str(limitation.get("text", "")),
                    "source": str(limitation.get("quelle", "")),
                }
                for limitation in option.get("limitierungen", [])
            ],
            "implication": str(option.get("implikation", "")),
        }
        for option in proposal["optionen"]
    ]

    confidence_raw = str(proposal["confidence"])
    ermittlung = proposal["ermittlung"] or {}
    kunde = proposal["kunde"] or {}
    definition = {
        "id": definition_id,
        "source": {
            "adapter": "meridian_decision_proposals",
            "raw_id": raw_id,
            "source_ref": "tooling/superversion/vendor/meridian_dataarch/decision_proposals.py",
            "source_hash": canonical_sha256(dict(proposal)),
        },
        "title": str(proposal["topic"]),
        "question": {"technical_text": str(proposal["gap"])},
        "recommendation": {
            "text": str(recommendation) if recommendation is not None else None,
            "basis": str(proposal["derived_from"]),
            "confidence_raw": confidence_raw,
            "confidence": _CONFIDENCE.get(confidence_raw.casefold(), "none"),
        },
        "options": options,
        "option_details": option_details,
        "decider": {"text": str(proposal["decider"]), "role_ref": None},
        "consequence_if_unresolved": str(proposal["if_undecided"]),
        "resolution_method": {
            "where_to_look": str(ermittlung.get("wo", "")),
            "who_knows": str(ermittlung.get("wen", "")),
            "if_unclear": str(ermittlung.get("wenn_unklar", "")),
        },
        "customer_copy": {
            "question": str(kunde.get("frage", "")),
            "consequence": str(kunde.get("folge", "")),
            "why": str(kunde.get("warum", "")),
        },
        "due": {
            "raw": str(proposal["faelligkeit"]),
            "gate": _due_gate(str(proposal["faelligkeit"])),
        },
        "placeholder_refs": [str(marker) for marker in proposal["markers"]],
    }

    preselected = proposal["status"] == "vorbelegt" and recommendation is not None
    has_recommendation = recommendation is not None
    instance = {
        "id": instance_id,
        "definition_ref": definition_id,
        "scope_refs": scope_refs,
        "revision": 1,
        "initialization": "preselected" if proposal["status"] == "vorbelegt" else "open",
        "selection": {
            "state": "preselected" if preselected else "unselected",
            "option_ref": "proposal" if preselected else None,
            "custom_value": None,
        },
        "approval": {
            "state": "proposed" if has_recommendation else "draft",
            "proposed_by": "meridian_decision_proposals" if has_recommendation else None,
            "decided_by": None,
            "rationale": None,
        },
        "readiness": {"state": "incomplete"},
        "delivery": {"state": "not_compiled"},
    }
    return definition, instance


def adapt_decision_proposals(
    proposals: Sequence[Mapping[str, Any]],
    scope_ref_by_slug: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Map every source field once into the single Project Package decision model."""
    scope_map = scope_ref_by_slug or {}
    pairs = [_adapt_one(proposal, scope_map) for proposal in proposals]
    definitions = [pair[0] for pair in pairs]
    instances = [pair[1] for pair in pairs]
    if len({item["id"] for item in definitions}) != len(definitions):
        raise ValueError("duplicate normalized decision definition id")
    if len({item["id"] for item in instances}) != len(instances):
        raise ValueError("duplicate normalized decision instance id")
    return {"schema_version": "2.0.0", "definitions": definitions, "instances": instances}
