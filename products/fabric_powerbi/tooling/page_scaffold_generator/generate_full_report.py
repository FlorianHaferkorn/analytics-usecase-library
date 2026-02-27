"""
Generate full Use Case report (overview + detail pages) from Bracket ux_layout_rules.
Writes PBIP .Report folder with datasetReference. Invoked by orchestrate_full_model.ps1.

Delta mode: if report already exists (definition/pages/pages.json and at least one page),
only add/remove/update visuals and positions (no overwrite of report.json/version.json).
Use --force-full to always do a full generate.
"""

import argparse
import sys
from pathlib import Path

# Allow running as script from repo root or from tooling dir
if __name__ == "__main__":
    _this_dir = Path(__file__).resolve().parent  # page_scaffold_generator
    _tooling = _this_dir.parent  # fabric_powerbi/tooling
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
        required=True,
        type=Path,
        help="Path to output .Report folder (e.g. products/fabric_powerbi/dist/COM-001.Report)",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repository root (auto-detected if not set)",
    )
    parser.add_argument(
        "--dataset-reference",
        default="../../../showcases/aurora_group/semantic_models/Commercial.SemanticModel",
        help="Relative path from report folder to semantic model PBIP; orchestrate sets per-domain (e.g. Commercial.SemanticModel).",
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
    output_path = Path(args.output).resolve()
    output_path.mkdir(parents=True, exist_ok=True)

    use_case_id = args.use_case.strip()
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
