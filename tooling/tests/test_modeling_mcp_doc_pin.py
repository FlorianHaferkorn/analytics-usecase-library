"""Power BI Authoring (Modeling) MCP: Pin und Doku bleiben deckungsgleich (I-21 W3.5, W5.18a, W3.6).

- `.mcp.json` und `powerbi-modeling-mcp-setup.md` nennen dieselbe Paketversion.
- Die Doku unterscheidet lokal (GA) und gehostet (Preview) und verweist fuer Nutzer-Fragen auf Fabric IQ
  (Learn `power-bi/developer/mcp/power-bi-authoring-mcp`, `mcp-servers-overview`, gelesen 29.09.2026).
- Die Regel `connect-pbid.md` kennt das Desktop-Nachladen seit August 2026 und bleibt bis zum
  Desktop-Test beim Neu-Oeffnen als sicherem Standard.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DOC = REPO / "products/fabric/powerbi/docs/references/powerbi-modeling-mcp-setup.md"
MCP = REPO / ".mcp.json"
RULE = REPO / ".claude/rules/connect-pbid.md"
PKG = "@microsoft/powerbi-modeling-mcp@"


def _mcp_version() -> str:
    args = json.loads(MCP.read_text(encoding="utf-8"))["mcpServers"]["powerbi-modeling-mcp"]["args"]
    return next(a for a in args if a.startswith(PKG))[len(PKG):]


def test_doc_pin_equals_mcp_json() -> None:
    text = DOC.read_text(encoding="utf-8")
    pinned = re.search(r"\*\*Pinned version: `([^`]+)`\*\*", text)
    assert pinned is not None
    assert pinned.group(1) == _mcp_version()
    assert f"{PKG}{_mcp_version()}" in text


def test_doc_separates_local_ga_from_hosted_preview() -> None:
    text = DOC.read_text(encoding="utf-8")
    assert "https://api.fabric.microsoft.com/v1/mcp/powerbi/authoring" in text
    assert "generally available" in text and "preview" in text
    assert "Fabric IQ" in text


def test_connect_pbid_rule_knows_the_august_2026_reload() -> None:
    text = RULE.read_text(encoding="utf-8")
    assert "Apply external changes" in text
    assert "Detect and reload external PBIP changes" in text
    assert "Desktop-gated" in text
