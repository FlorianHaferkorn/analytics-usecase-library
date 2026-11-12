#!/usr/bin/env python3
"""Generate dist/aurora_calculation.md from cost engine (no CLI deps)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cost_engine import compute_projection, fill_template

def main() -> None:
    root = Path(__file__).resolve().parent.parent
    out = compute_projection(
        "compact",
        product_root=root,
        projection_config=None,
        tco_years_list=[3, 5],
        use_reservation=False,
        storage_gb=None,
        role_allocation_path="model/role_allocation.yaml.example",
    )
    # Result for template: first horizon's full breakdown + horizons + tco_by_years
    result = out["horizons"][0]["breakdown"].copy()
    result["horizons"] = out["horizons"]
    result["tco_by_years"] = out["tco_by_years"]

    template_path = root / "templates" / "proposal_snippet.md"
    template_content = template_path.read_text(encoding="utf-8")
    filled = fill_template(result, template_content)

    out_path = root / "dist" / "aurora_calculation.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # Keep Aurora title
    out_path.write_text("# Aurora – Beispielkalkulation\n\n" + filled, encoding="utf-8")
    print(f"Written {out_path}", file=sys.stderr)

if __name__ == "__main__":
    main()
