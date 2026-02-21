"""
Generate full Use Case report (overview + detail pages) from Bracket ux_layout_rules.
Writes PBIP .Report folder with datasetReference. Invoked by orchestrate_full_model.ps1.
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


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate full Use Case report (overview + detail) into a single .Report PBIP folder."
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
        default="../../../showcases/aurora_group/semantic_models/CoreActionReady.SemanticModel",
        help="Relative path from report folder to semantic model PBIP (for datasetReference.byPath.path)",
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

    # Page 1: Overview
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

    # Page 2: Detail (append only)
    gen_detail = PageScaffoldGenerator(
        use_case_id=use_case_id,
        page_name="detail",
        repo_root=repo_root,
    )
    gen_detail.load_config()
    gen_detail.generate()
    gen_detail.write(output_path, append_page_only=True)

    return 0


if __name__ == "__main__":
    sys.exit(main())
