"""
One-time migration: Remove expression.dax and expression.formatString from core Measure Dictionaries
so core stays tool-agnostic. Fabric realisation lives in products/fabric/powerbi (overlay / TMDL).
"""
from __future__ import annotations

import re
from pathlib import Path

try:
    import yaml
except ImportError:
    raise SystemExit("pip install pyyaml")

REPO_ROOT = Path(__file__).resolve().parents[2]
DOMAINS_ROOT = REPO_ROOT / "core" / "semantic_models" / "domains"


def strip_dax_from_file(path: Path) -> bool:
    """Remove expression.dax and expression.formatString from YAML blocks. Returns True if changed."""
    text = path.read_text(encoding="utf-8-sig")
    changed = False

    def replace_block(match: re.Match) -> str:
        nonlocal changed
        block = match.group(1)
        try:
            data = yaml.safe_load(block)
        except Exception:
            return match.group(0)
        if not isinstance(data, list):
            return match.group(0)
        for item in data:
            if not isinstance(item, dict):
                continue
            expr = item.get("expression")
            if isinstance(expr, dict):
                if "dax" in expr or "formatString" in expr:
                    expr.pop("dax", None)
                    expr.pop("formatString", None)
                    if not expr:
                        item["expression"] = {"logical": "Fabric: see overlay / TMDL."}
                    changed = True
        out = yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False)
        return out.rstrip()

    new_text = re.sub(r"```yaml\s*\n(.*?)```", lambda m: "```yaml\n" + replace_block(m) + "\n```", text, flags=re.DOTALL)
    if changed:
        path.write_text(new_text, encoding="utf-8")
    return changed


def main() -> int:
    count = 0
    for path in sorted(DOMAINS_ROOT.rglob("Measure_Dictionary_*.md")):
        if "internal" in path.parts or "archive" in path.parts:
            continue
        if strip_dax_from_file(path):
            print(path.relative_to(REPO_ROOT))
            count += 1
    print(f"Stripped dax/formatString from {count} files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
