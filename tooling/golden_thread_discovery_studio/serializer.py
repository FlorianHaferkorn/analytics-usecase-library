"""
State <-> Bracket YAML roundtrip for Golden Thread Discovery Studio.

- draft_to_bracket_dict: UseCaseDraft -> dict suitable for YAML dump (drops status, source_refs).
- bracket_dict_to_draft: dict (from YAML) -> UseCaseDraft (adds status, optional source_refs).
- draft_to_yaml / yaml_to_draft: string roundtrip.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from models import UseCaseDraft

# Studio-only keys that must not be written to UseCase_Bracket.yaml
_STUDIO_KEYS = frozenset({"status", "source_refs"})


def draft_to_bracket_dict(draft: UseCaseDraft) -> Dict[str, Any]:
    """
    Convert UseCaseDraft to a dict that matches UseCase_Bracket.yaml (schema 2.0).
    Removes studio-only fields (status, source_refs).
    """
    out: Dict[str, Any] = {}
    for k, v in draft.items():
        if k in _STUDIO_KEYS:
            continue
        if v is None:
            continue
        out[k] = v
    return out


def bracket_dict_to_draft(data: Dict[str, Any], status: str = "draft") -> UseCaseDraft:
    """
    Convert parsed bracket dict to UseCaseDraft. Sets status; source_refs left empty.
    """
    draft: UseCaseDraft = {**data, "status": status}
    if "source_refs" not in draft:
        draft["source_refs"] = {}
    return draft


def draft_to_yaml(draft: UseCaseDraft) -> str:
    """Serialize UseCaseDraft to YAML string (bracket format, no studio-only keys)."""
    try:
        import yaml
    except ImportError:
        return ""

    d = draft_to_bracket_dict(draft)
    return yaml.dump(
        d,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
        width=120,
    )


def yaml_to_draft(yaml_text: str, status: str = "draft") -> Tuple[Optional[UseCaseDraft], Optional[str]]:
    """
    Parse YAML string into UseCaseDraft. Returns (draft, None) on success or (None, error_message).
    """
    try:
        import yaml
    except ImportError:
        return None, "pyyaml not installed"

    try:
        data = yaml.safe_load(yaml_text)
    except Exception as e:
        return None, str(e)

    if not isinstance(data, dict):
        return None, "YAML root must be a mapping"

    return bracket_dict_to_draft(data, status=status), None


def roundtrip(draft: UseCaseDraft) -> Optional[UseCaseDraft]:
    """
    Roundtrip: draft -> YAML -> draft. Returns the re-parsed draft or None on error.
    Used for tests; re-parsed draft will have no studio-only fields except status re-set.
    """
    y = draft_to_yaml(draft)
    if not y:
        return None
    out, err = yaml_to_draft(y, status=draft.get("status", "draft"))
    if err:
        return None
    if out:
        out["status"] = draft.get("status", "draft")
    return out
