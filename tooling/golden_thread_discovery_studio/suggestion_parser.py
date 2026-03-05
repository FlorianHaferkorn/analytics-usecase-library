"""
Parse KPI/orchestration suggestions from assistant chat messages.
Extracts strategic_kpi_id, influencing_kpi_ids, action_code_ids from JSON or prose.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional


def parse_kpi_suggestion(message: str) -> Optional[Dict[str, Any]]:
    """
    Parse last assistant message for orchestration fields.
    Returns dict with strategic_kpi_id, influencing_kpi_ids, action_code_ids (or None).
    """
    if not message or not isinstance(message, str):
        return None
    text = message.strip()

    # 1. Try JSON block ```json ... ``` or ``` ... ```
    json_match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text)
    if json_match:
        try:
            data = json.loads(json_match.group(1))
            return _normalize_suggestion(data)
        except json.JSONDecodeError:
            pass

    # 2. Try inline JSON object
    obj_match = re.search(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", text)
    if obj_match:
        try:
            data = json.loads(obj_match.group(0))
            return _normalize_suggestion(data)
        except json.JSONDecodeError:
            pass

    # 3. Key-value lines (strategic_kpi_id: x, influencing_kpi_ids: [a,b], ...)
    out: Dict[str, Any] = {}
    sk = re.search(r"strategic_kpi_id\s*[:=]\s*[\"']?([a-zA-Z0-9_.-]+)[\"']?", text, re.IGNORECASE)
    if sk:
        out["strategic_kpi_id"] = sk.group(1).strip()
    inf = re.search(r"influencing_kpi_ids?\s*[:=]\s*\[([^\]]*)\]", text, re.IGNORECASE)
    if inf:
        ids = [x.strip().strip('"\'') for x in inf.group(1).split(",") if x.strip()]
        out["influencing_kpi_ids"] = ids
    acts = re.search(r"action_code_ids?\s*[:=]\s*\[([^\]]*)\]", text, re.IGNORECASE)
    if acts:
        ids = [x.strip().strip('"\'') for x in acts.group(1).split(",") if x.strip()]
        out["action_code_ids"] = ids
    if out:
        return _normalize_suggestion(out)

    # 4. Prose fallback (e.g. "Strategische Kennzahl: `fin.cash.ocf`", bullets with `crm.x.y`, `C-S1.1`)
    return _parse_prose_suggestion(text)


def _normalize_suggestion(data: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure keys exist and are lists where needed."""
    sk = data.get("strategic_kpi_id")
    if isinstance(sk, list):
        sk = sk[0] if sk else ""
    out: Dict[str, Any] = {
        "strategic_kpi_id": (sk or "").strip() if isinstance(sk, str) else str(sk or ""),
        "influencing_kpi_ids": _ensure_str_list(data.get("influencing_kpi_ids")),
        "action_code_ids": _ensure_str_list(data.get("action_code_ids")),
    }
    return out


def _ensure_str_list(v: Any) -> List[str]:
    if v is None:
        return []
    if isinstance(v, list):
        return [str(x).strip() for x in v if str(x).strip()]
    if isinstance(v, str):
        return [x.strip() for x in v.split(",") if x.strip()]
    return []


# KPI-like: domain.topic.metric or longer (e.g. fin.cash.ocf, cost.opex.base.amount)
_RE_KPI_BACKTICK = re.compile(r"`([a-z][a-z0-9_.]*\.[a-z0-9_.-]+)`")
# Action code: C-S1.1, F-K2.1, O-A2.1, F-C1.2
_RE_ACTION_BACKTICK = re.compile(r"`([A-Z]-[A-Z][0-9]\.[0-9]+)`")


def _parse_prose_suggestion(text: str) -> Optional[Dict[str, Any]]:
    """Extract strategic KPI, influencing KPIs, action codes from prose (e.g. Nagarro-style answer)."""
    strategic = ""
    influencing: List[str] = []
    action_codes: List[str] = []

    # Strategic: explicit line like "**Strategische Kennzahl (Strategic KPI):** `fin.cash.ocf`"
    sk_match = re.search(
        r"(?:Strategische\s+Kennzahl|Strategic\s+KPI|strategic\s+kpi)[^`]*`([a-zA-Z0-9_.-]+)`",
        text,
        re.IGNORECASE,
    )
    if sk_match:
        strategic = sk_match.group(1).strip()

    # All backtick-wrapped KPI IDs (domain.something.something)
    kpi_ids = _RE_KPI_BACKTICK.findall(text)
    kpi_ids = [x.strip() for x in kpi_ids if x.strip()]
    if strategic and strategic in kpi_ids:
        kpi_ids = [x for x in kpi_ids if x != strategic]
    if not strategic and kpi_ids:
        strategic = kpi_ids[0]
        kpi_ids = kpi_ids[1:]
    influencing = list(dict.fromkeys(kpi_ids))  # preserve order, dedupe

    # Action codes in backticks
    action_codes = list(dict.fromkeys(_RE_ACTION_BACKTICK.findall(text)))

    if strategic or influencing or action_codes:
        return _normalize_suggestion({
            "strategic_kpi_id": strategic,
            "influencing_kpi_ids": influencing,
            "action_code_ids": action_codes,
        })
    return None
