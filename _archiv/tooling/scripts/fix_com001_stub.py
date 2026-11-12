"""
fix_report_page_metadata.py — Align PBIR page folder names with page.json metadata.

Fixes reports where Page_COM001_* directories contain page.json entries still
referencing another use case (e.g. Page_COM002_* / "COM-002 - Overview") after
copy/rename without updating JSON content.

Usage (from repo root):
    py -3 tooling/scripts/fix_com001_stub.py
    py -3 tooling/scripts/fix_com001_stub.py --report products/fabric/powerbi/dist/COM-001_Sales_Performance.Report
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REPORT = REPO_ROOT / "products/fabric/powerbi/dist/COM-001_Sales_Performance.Report"
PAGE_DIR_RE = re.compile(r"^Page_(?P<uc>[A-Z]{2,3}\d{3})_(?P<page>Overview|Detail)$", re.IGNORECASE)


def infer_use_case_id(report_dir: Path) -> str | None:
    m = re.match(r"^([A-Z]{2,3}-\d+)_", report_dir.name)
    return m.group(1) if m else None


def normalize_uc_token(use_case_id: str) -> str:
    return use_case_id.replace("-", "")


def fix_report_page_metadata(report_dir: Path) -> list[str]:
    """Return list of human-readable changes applied."""
    changes: list[str] = []
    pages_dir = report_dir / "definition/pages"
    pages_json_path = pages_dir / "pages.json"

    if not pages_dir.is_dir():
        raise FileNotFoundError(f"Missing pages directory: {pages_dir}")

    use_case_id = infer_use_case_id(report_dir)
    if not use_case_id:
        raise ValueError(f"Cannot infer use case ID from report folder: {report_dir.name}")

    page_dirs = sorted(p for p in pages_dir.iterdir() if p.is_dir() and p.name.startswith("Page_"))
    if not page_dirs:
        raise ValueError(f"No Page_* directories under {pages_dir}")

    page_order: list[str] = []
    for page_dir in page_dirs:
        page_json_path = page_dir / "page.json"
        if not page_json_path.is_file():
            changes.append(f"SKIP {page_dir.name}: missing page.json")
            continue

        m = PAGE_DIR_RE.match(page_dir.name)
        page_suffix = m.group("page") if m else page_dir.name.split("_")[-1]
        expected_name = page_dir.name
        expected_display = f"{use_case_id} - {page_suffix.capitalize()}"

        data = json.loads(page_json_path.read_text(encoding="utf-8"))
        old_name = data.get("name")
        old_display = data.get("displayName")

        if old_name != expected_name or old_display != expected_display:
            data["name"] = expected_name
            data["displayName"] = expected_display
            page_json_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
            changes.append(
                f"{page_dir.name}/page.json: name {old_name!r} -> {expected_name!r}, "
                f"displayName {old_display!r} -> {expected_display!r}"
            )
        else:
            changes.append(f"OK {page_dir.name}/page.json already aligned")

        page_order.append(expected_name)

    # Overview first, Detail second; preserve any extra pages at end
    overview = [n for n in page_order if n.endswith("_Overview")]
    detail = [n for n in page_order if n.endswith("_Detail")]
    other = [n for n in page_order if n not in overview + detail]
    ordered = overview + detail + other

    if not ordered:
        raise ValueError(
            f"No valid page.json files under {pages_dir} "
            f"({len(page_dirs)} Page_* folder(s) present)"
        )

    if pages_json_path.is_file():
        pages_meta = json.loads(pages_json_path.read_text(encoding="utf-8"))
        old_order = pages_meta.get("pageOrder")
        old_active = pages_meta.get("activePageName")
        active = overview[0] if overview else ordered[0]

        if old_order != ordered or old_active != active:
            pages_meta["pageOrder"] = ordered
            pages_meta["activePageName"] = active
            pages_json_path.write_text(json.dumps(pages_meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
            changes.append(f"pages.json: pageOrder/activePageName synced ({active})")
        else:
            changes.append("OK pages.json already aligned")
    else:
        changes.append("WARN pages.json missing — only page.json files updated")

    return changes


def main() -> int:
    parser = argparse.ArgumentParser(description="Align PBIR page folder names with page.json metadata.")
    parser.add_argument(
        "--report",
        type=Path,
        default=DEFAULT_REPORT,
        help="Path to *.Report directory",
    )
    args = parser.parse_args()
    report_dir = args.report.resolve()

    if not report_dir.is_dir():
        print(f"ERROR: report directory not found: {report_dir}", file=sys.stderr)
        return 1

    try:
        changes = fix_report_page_metadata(report_dir)
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    for line in changes:
        print(line)
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
