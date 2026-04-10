"""
Generate full Use Case report (overview + detail pages) from Bracket ux_layout_rules.
Writes PBIP .Report folder with datasetReference. Invoked by orchestrate_full_model.ps1.

Canonical output: products/fabric/powerbi/dist/<UseCaseFolderName>.Report
(e.g. COM-001_Sales_Performance.Report). Use-case folder name is resolved from
core/usecases/core/ (first directory matching <use_case_id>*). If --output is
omitted, this default is used so manual/agent runs match the orchestrator.

Delta mode: if report already exists (definition/pages/pages.json and at least one page),
only add/remove/update visuals and positions (no overwrite of report.json/version.json).
Use --force-full to always do a full generate.
"""

import argparse
import sys
from pathlib import Path

# Canonical dist path (must match orchestrate_full_model.ps1 / generate_phase5_reports.ps1)
DIST_RELATIVE = "products/fabric/powerbi/dist"
USE_CASE_ROOT_RELATIVE = "core/usecases/core"


def get_use_case_report_folder_base_name(repo_root: Path, use_case_id: str) -> str:
    """Return use case folder name (e.g. COM-001_Sales_Performance) for report naming.
    Matches Get-UseCaseReportFolderBaseName in orchestrate_full_model.ps1.
    """
    uc_root = repo_root / USE_CASE_ROOT_RELATIVE
    if not uc_root.is_dir():
        return use_case_id
    prefix = use_case_id.strip()
    for d in uc_root.iterdir():
        if d.is_dir() and d.name.startswith(prefix):
            return d.name
    return use_case_id


def get_default_report_output_path(repo_root: Path, use_case_id: str) -> Path:
    """Canonical output path: repo_root/products/fabric/powerbi/dist/<UseCaseFolder>.Report"""
    folder_name = get_use_case_report_folder_base_name(repo_root, use_case_id)
    return repo_root / DIST_RELATIVE / f"{folder_name}.Report"


# Allow running as script from repo root or from tooling dir
if __name__ == "__main__":
    _this_dir = Path(__file__).resolve().parent  # page_scaffold_generator
    _tooling = _this_dir.parent  # fabric/powerbi/tooling
    if str(_tooling) not in sys.path:
        sys.path.insert(0, str(_tooling))

from page_scaffold_generator.scaffold_generator import PageScaffoldGenerator
from page_scaffold_generator.pbip_reader import report_exists_for_update
from page_scaffold_generator.report_sync import sync_report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate full Use Case report (overview + detail) into a single .Report PBIP folder. Uses delta update if report exists."
    )
    parser.add_argument("--use-case", required=True, help="Use case ID (e.g. COM-001)")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Path to output .Report folder. Default: products/fabric/powerbi/dist/<UseCaseFolderName>.Report (e.g. COM-001_Sales_Performance.Report), matching the orchestrator.",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repository root (auto-detected if not set)",
    )
    parser.add_argument(
        "--dataset-reference",
        default="../Commercial.SemanticModel",
        help="Relative path from report folder to semantic model PBIP. Default assumes sibling domain model in products/fabric/powerbi/dist.",
    )
    parser.add_argument(
        "--force-full",
        action="store_true",
        help="Always full generate (overwrite); do not use delta update even if report exists.",
    )
    args = parser.parse_args()

    repo_root = args.repo_root
    if repo_root is None:
        # Default: from .../page_scaffold_generator/generate_full_report.py -> repo root
        repo_root = Path(__file__).resolve().parents[4]
    repo_root = Path(repo_root)
    use_case_id = args.use_case.strip()

    if args.output is not None:
        output_path = Path(args.output).resolve()
    else:
        output_path = get_default_report_output_path(repo_root, use_case_id).resolve()
        if sys.stderr:
            print(f"Output (default): {output_path}", file=sys.stderr)
    output_path.mkdir(parents=True, exist_ok=True)
    dataset_ref = args.dataset_reference.strip()

    # Delta mode: report exists and not --force-full -> sync only (add/remove/update visuals and positions)
    if not args.force_full and report_exists_for_update(output_path):
        applied = sync_report(use_case_id, output_path, repo_root)
        if applied:
            print("mode=delta", file=sys.stdout)
            return 0
        # Fallback to full generate if sync failed (e.g. corrupt structure)
        pass

    # Full generate
    gen_overview = PageScaffoldGenerator(
        use_case_id=use_case_id,
        page_name="overview",
        repo_root=repo_root,
    )
    gen_overview.load_config()
    gen_overview.generate()
    gen_overview.write(
        output_path,
        dataset_reference_path=dataset_ref,
    )

    gen_detail = PageScaffoldGenerator(
        use_case_id=use_case_id,
        page_name="detail",
        repo_root=repo_root,
    )
    gen_detail.load_config()
    gen_detail.generate()
    gen_detail.write(output_path, append_page_only=True)

    print("mode=full", file=sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
