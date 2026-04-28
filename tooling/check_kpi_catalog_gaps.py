#!/usr/bin/env python3
"""
check_kpi_catalog_gaps.py — Find KPI IDs referenced in TMDL doc comments
but not present in core/kpi_catalog/KPI_Catalog.md.
"""
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DIST = REPO_ROOT / "products/fabric/powerbi/dist"
CATALOG = REPO_ROOT / "core/kpi_catalog/KPI_Catalog.md"

catalog_ids = set()
if CATALOG.exists():
    content = CATALOG.read_text(encoding="utf-8")
    for m in re.findall(r"kpi_id:\s*[\"']?([a-zA-Z0-9_\.]+)[\"']?", content):
        catalog_ids.add(m.strip())

missing = []
for tmdl in sorted(DIST.rglob("_Measures.tmdl")):
    model = tmdl.parent.parent.parent.name
    for line in tmdl.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\s*///\s+([a-zA-Z][a-zA-Z0-9_\.]+)\s+-", line)
        if m:
            kpi_id = m.group(1)
            if "." in kpi_id and kpi_id not in catalog_ids:
                missing.append((kpi_id, model))

unique = sorted(set(missing))
print(f"Missing KPI IDs in catalog: {len(unique)}")
for kpi_id, model in unique:
    print(f"  {kpi_id}  [{model}]")

sys.exit(1 if unique else 0)
