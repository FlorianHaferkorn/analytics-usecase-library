#!/usr/bin/env python3
"""
audit_report_versions.py — Read-only audit of all .Report and .SemanticModel
folders in the repository.

Scans every report and semantic model and reports:
  - PBIR / TMDL schema versions currently on disk
  - Deviations from schema_registry.py pinned versions
  - Binding mode (byPath vs byConnection)
  - Unsupported committed files (.pbi/localSettings.json, .pbi/cache.abf)
  - Missing required artefacts (version.json, definition.pbir)
  - Theme version mismatches

This is AUDIT ONLY — no files are written or modified. Run this before any
migration to understand the scope of changes needed.

Usage (from repository root):
    py -3 products/fabric/powerbi/tooling/migration/audit_report_versions.py
    py -3 products/fabric/powerbi/tooling/migration/audit_report_versions.py --scan-root products/fabric/powerbi/dist
    py -3 products/fabric/powerbi/tooling/migration/audit_report_versions.py --json
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

_REPO_ROOT = Path(__file__).resolve().parents[5]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from products.fabric.powerbi.tooling.schema_registry import (
    REPORT_SCHEMA,
    PAGE_SCHEMA,
    VISUAL_SCHEMA,
    PAGES_METADATA_SCHEMA,
    VERSION_METADATA_SCHEMA,
    DEFINITION_PBIR_SCHEMA,
    SEMANTIC_MODEL_SCHEMA,
    THEME_SCHEMA_PINNED_VERSION,
)

# Files that must not be committed (Desktop-local state / binary cache)
_FORBIDDEN_FILES = {
    ".pbi/localSettings.json",
    ".pbi/cache.abf",
}

# Required artefacts inside a .Report folder
_REQUIRED_REPORT_FILES = [
    "definition.pbir",
    "definition/version.json",
    "definition/report.json",
    "definition/pages/pages.json",
]


@dataclass
class ReportAudit:
    path: Path
    schema_mismatches: list[dict] = field(default_factory=list)
    missing_files: list[str] = field(default_factory=list)
    forbidden_files: list[str] = field(default_factory=list)
    binding_mode: str = "unknown"
    definition_pbir_version: str = ""
    theme_version: str = ""
    theme_version_ok: bool = True
    page_count: int = 0
    visual_count: int = 0

    @property
    def ok(self) -> bool:
        return (
            not self.schema_mismatches
            and not self.missing_files
            and not self.forbidden_files
            and self.theme_version_ok
        )


@dataclass
class ModelAudit:
    path: Path
    schema_mismatches: list[dict] = field(default_factory=list)
    tmdl_tables: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.schema_mismatches


def _read_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _schema_mismatch(file_rel: str, expected: str, actual: str | None) -> dict | None:
    if not actual or actual == expected:
        return None
    return {"file": file_rel, "expected": expected, "actual": actual}


def audit_report(report_dir: Path) -> ReportAudit:
    audit = ReportAudit(path=report_dir)

    # 1. Forbidden files
    for rel in _FORBIDDEN_FILES:
        if (report_dir / rel).exists():
            audit.forbidden_files.append(rel)

    # 2. Required files
    for rel in _REQUIRED_REPORT_FILES:
        if not (report_dir / rel).exists():
            audit.missing_files.append(rel)

    # 3. definition.pbir
    pbir_path = report_dir / "definition.pbir"
    if pbir_path.exists():
        data = _read_json(pbir_path)
        if data:
            actual_schema = data.get("$schema", "")
            m = _schema_mismatch("definition.pbir", DEFINITION_PBIR_SCHEMA, actual_schema)
            if m:
                audit.schema_mismatches.append(m)
            audit.definition_pbir_version = data.get("version", "")
            dataset_ref = data.get("datasetReference", {})
            if "byConnection" in dataset_ref:
                audit.binding_mode = "byConnection"
            elif "byPath" in dataset_ref:
                audit.binding_mode = "byPath"

    # 4. definition/report.json
    report_json = report_dir / "definition" / "report.json"
    if report_json.exists():
        data = _read_json(report_json)
        if data:
            m = _schema_mismatch(
                "definition/report.json", REPORT_SCHEMA, data.get("$schema", "")
            )
            if m:
                audit.schema_mismatches.append(m)
            # Extract theme version
            theme_collection = data.get("themeCollection") or {}
            base_theme = theme_collection.get("baseTheme") or {}
            theme_name = base_theme.get("name", "")
            audit.theme_version = theme_name

    # 5. definition/version.json
    version_json = report_dir / "definition" / "version.json"
    if version_json.exists():
        data = _read_json(version_json)
        if data:
            m = _schema_mismatch(
                "definition/version.json", VERSION_METADATA_SCHEMA, data.get("$schema", "")
            )
            if m:
                audit.schema_mismatches.append(m)

    # 6. Pages: pages.json + page.json + visual.json
    pages_dir = report_dir / "definition" / "pages"
    if pages_dir.is_dir():
        pages_meta = pages_dir / "pages.json"
        if pages_meta.exists():
            data = _read_json(pages_meta)
            if data:
                m = _schema_mismatch(
                    "definition/pages/pages.json",
                    PAGES_METADATA_SCHEMA,
                    data.get("$schema", ""),
                )
                if m:
                    audit.schema_mismatches.append(m)

        for page_dir in sorted(pages_dir.iterdir()):
            if not page_dir.is_dir():
                continue
            audit.page_count += 1
            page_json = page_dir / "page.json"
            if page_json.exists():
                data = _read_json(page_json)
                if data:
                    m = _schema_mismatch(
                        f"pages/{page_dir.name}/page.json",
                        PAGE_SCHEMA,
                        data.get("$schema", ""),
                    )
                    if m:
                        audit.schema_mismatches.append(m)

            visuals_dir = page_dir / "visuals"
            if visuals_dir.is_dir():
                for visual_dir in sorted(visuals_dir.iterdir()):
                    if not visual_dir.is_dir():
                        continue
                    vj = visual_dir / "visual.json"
                    if not vj.exists():
                        continue
                    audit.visual_count += 1
                    data = _read_json(vj)
                    if data:
                        m = _schema_mismatch(
                            f"pages/{page_dir.name}/visuals/{visual_dir.name}/visual.json",
                            VISUAL_SCHEMA,
                            data.get("$schema", ""),
                        )
                        if m:
                            audit.schema_mismatches.append(m)

    return audit


def audit_model(model_dir: Path) -> ModelAudit:
    audit = ModelAudit(path=model_dir)

    pbism = model_dir / "definition.pbism"
    if pbism.exists():
        data = _read_json(pbism)
        if data:
            m = _schema_mismatch(
                "definition.pbism", SEMANTIC_MODEL_SCHEMA, data.get("$schema", "")
            )
            if m:
                audit.schema_mismatches.append(m)

    tables_dir = model_dir / "definition" / "tables"
    if tables_dir.is_dir():
        audit.tmdl_tables = [f.stem for f in sorted(tables_dir.glob("*.tmdl"))]

    return audit


def _find_artefacts(scan_root: Path) -> tuple[list[Path], list[Path]]:
    reports = sorted(scan_root.glob("**/*.Report"))
    models  = sorted(scan_root.glob("**/*.SemanticModel"))
    return reports, models


def _print_report_audit(audit: ReportAudit) -> None:
    status = "OK" if audit.ok else "ISSUES"
    label = audit.path.name
    print(f"\n  [{status}] {label}")
    print(f"         binding={audit.binding_mode}  pages={audit.page_count}  visuals={audit.visual_count}")
    if audit.definition_pbir_version:
        print(f"         definition.pbir version={audit.definition_pbir_version}")
    if audit.theme_version:
        print(f"         theme={audit.theme_version}")
    for m in audit.schema_mismatches:
        print(f"    DRIFT  {m['file']}")
        print(f"           expected: {m['expected']}")
        print(f"           actual:   {m['actual']}")
    for f in audit.missing_files:
        print(f"    MISSING {f}")
    for f in audit.forbidden_files:
        print(f"    FORBIDDEN {f}  (must not be committed)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scan-root",
        default="products/fabric/powerbi/dist",
        help="Root directory to scan (default: products/fabric/powerbi/dist).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output findings as JSON instead of plain text.",
    )
    args = parser.parse_args()

    scan_root = (
        Path(args.scan_root)
        if Path(args.scan_root).is_absolute()
        else _REPO_ROOT / args.scan_root
    )

    if not scan_root.is_dir():
        print(f"WARN: scan root not found: {scan_root}")
        return 2

    report_dirs, model_dirs = _find_artefacts(scan_root)
    if not report_dirs and not model_dirs:
        print(f"WARN: No .Report or .SemanticModel folders found under {scan_root}")
        return 2

    report_audits = [audit_report(d) for d in report_dirs]
    model_audits  = [audit_model(d) for d in model_dirs]

    if args.json_output:
        def _to_dict(a) -> dict:
            return {
                "path": str(a.path),
                "ok": a.ok,
                **{k: v for k, v in a.__dict__.items() if k != "path"},
            }
        payload = {
            "reports": [_to_dict(a) for a in report_audits],
            "models":  [_to_dict(a) for a in model_audits],
        }
        print(json.dumps(payload, indent=2, default=str))
        issues = sum(1 for a in report_audits + model_audits if not a.ok)
        return 1 if issues else 0

    print(f"\n=== Power BI Migration Audit ===")
    print(f"Scan root: {scan_root}")
    print(f"Reports:   {len(report_audits)}")
    print(f"Models:    {len(model_audits)}")
    print(f"\nPinned schema versions (from schema_registry.py):")
    print(f"  visual={VISUAL_SCHEMA.rsplit('/', 2)[-2]}  "
          f"page={PAGE_SCHEMA.rsplit('/', 2)[-2]}  "
          f"report={REPORT_SCHEMA.rsplit('/', 2)[-2]}  "
          f"theme={THEME_SCHEMA_PINNED_VERSION}")

    if report_audits:
        print(f"\n--- Reports ---")
        for a in report_audits:
            _print_report_audit(a)

    if model_audits:
        print(f"\n--- Semantic Models ---")
        for a in model_audits:
            status = "OK" if a.ok else "ISSUES"
            print(f"\n  [{status}] {a.path.name}  tables={len(a.tmdl_tables)}")
            for m in a.schema_mismatches:
                print(f"    DRIFT  {m['file']}: {m['actual']}")

    issues = sum(1 for a in report_audits + model_audits if not a.ok)
    print(f"\n{'All artefacts are on pinned schema versions.' if not issues else f'{issues} artefact(s) need attention.'}")

    # Print migration checklist when issues are found
    if issues:
        print("""
Migration checklist (run in order):
  1. py -3 products/fabric/powerbi/tooling/update_schema_manifest.py --check-only
  2. py -3 products/fabric/powerbi/tooling/migration/audit_report_versions.py   (this script)
  3. py -3 products/fabric/powerbi/tooling/page_scaffold_generator/generate_full_report.py --all --force-full
  4. Open reports in Power BI Desktop (target version) and Save — Desktop is the authoritative migrator.
  5. .\\products\\fabric\\powerbi\\tooling\\run_fabric_checks.ps1
  6. Review git diff for unexpected changes before committing.
""")

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
