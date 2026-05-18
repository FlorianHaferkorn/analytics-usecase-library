"""
Generate full Use Case report (overview + detail pages) from Bracket ux_layout_rules.
Writes PBIP .Report folder with datasetReference. Invoked by orchestrate_full_model.ps1.

IR mode (--bracket): compiles the bracket through BracketCompiler → DashboardSpec →
PBIPAdapter.render() and writes all PBIP files.  This is the Week 4 IR-first path.

Scaffold mode (default): uses PageScaffoldGenerator (legacy path, kept for compatibility).

Canonical output: products/fabric/powerbi/dist/<UseCaseFolderName>.Report
(e.g. COM-001_Sales_Performance.Report). Use-case folder name is resolved from
core/usecases/core/ (first directory matching <use_case_id>*). If --output is
omitted, this default is used so manual/agent runs match the orchestrator.

Delta mode (scaffold only): if report already exists (definition/pages/pages.json and
at least one page), only add/remove/update visuals and positions.
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


# Allow running as script from repo root or from tooling dir.
# Both tooling/ (for page_scaffold_generator.*) and the workspace root
# (for products.fabric.powerbi.tooling.* absolute imports) must be on sys.path
# before any module-level imports below are executed.
if __name__ == "__main__":
    _this_dir = Path(__file__).resolve().parent  # page_scaffold_generator
    _tooling = _this_dir.parent  # fabric/powerbi/tooling
    _repo_root = _tooling.parents[3]  # /workspace
    if str(_tooling) not in sys.path:
        sys.path.insert(0, str(_tooling))
    if str(_repo_root) not in sys.path:
        sys.path.insert(0, str(_repo_root))

from page_scaffold_generator.scaffold_generator import PageScaffoldGenerator
from page_scaffold_generator.pbip_reader import report_exists_for_update
from page_scaffold_generator.report_sync import sync_report


def _ensure_repo_root_on_path(repo_root: Path) -> None:
    root_str = str(repo_root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)


def _ir_generate(
    bracket_path: Path,
    output_path: Path,
    repo_root: Path,
    dataset_ref: str,
) -> int:
    """IR-first path: bracket → DashboardSpec → PBIPAdapter.render() → PBIP files."""
    _ensure_repo_root_on_path(repo_root)

    from tooling.generator_core.ir.compiler import BracketCompiler
    from products.fabric.powerbi.tooling.adapters.pbip import PBIPAdapter

    kpi_catalog = repo_root / "core/kpi_catalog"
    action_codes = repo_root / "core/action_codes"

    compiler = BracketCompiler(
        kpi_catalog_root=kpi_catalog,
        action_codes_root=action_codes,
    )
    spec = compiler.compile(bracket_path)

    if compiler.warnings:
        for w in compiler.warnings:
            print(f"WARNING: {w}", file=sys.stderr)

    # Override semantic_model reference if caller provided an explicit --dataset-reference
    if dataset_ref:
        # Strip leading ../ to get just the model folder name for spec
        model_name = dataset_ref.lstrip("./").lstrip("/")
        if model_name.endswith("/"):
            model_name = model_name.rstrip("/")
        spec.semantic_model = model_name

    errors = PBIPAdapter().validate_ir(spec)
    if errors:
        for e in errors:
            print(f"IR VALIDATION ERROR: {e}", file=sys.stderr)
        return 1

    result = PBIPAdapter().render(spec)
    for warning in result.warnings:
        print(f"RENDER WARNING: {warning}", file=sys.stderr)

    written = result.write_to(output_path)
    print(f"mode=ir-full files={len(written)}", file=sys.stdout)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate full Use Case report (overview + detail) into a .Report PBIP folder. "
            "Use --bracket for IR-first mode (PBIPAdapter); omit for scaffold mode (legacy)."
        )
    )
    parser.add_argument("--use-case", required=False, default=None, help="Use case ID (e.g. COM-001)")
    parser.add_argument(
        "--bracket",
        type=Path,
        default=None,
        help="Path to UseCase_Bracket.yaml — activates IR-first mode via PBIPAdapter",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Path to output .Report folder. Default: products/fabric/powerbi/dist/<UseCaseFolderName>.Report",
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
        help="Relative path from report folder to semantic model PBIP.",
    )
    parser.add_argument(
        "--force-full",
        action="store_true",
        help="Always full generate (overwrite); do not use delta update even if report exists.",
    )
    args = parser.parse_args()

    repo_root = args.repo_root
    if repo_root is None:
        repo_root = Path(__file__).resolve().parents[4]
    repo_root = Path(repo_root)

    # Resolve use_case_id from bracket path if not provided explicitly
    use_case_id = args.use_case.strip() if args.use_case else None
    if use_case_id is None and args.bracket:
        bracket_path = Path(args.bracket)
        use_case_id = bracket_path.parent.name.split("_")[0]

    if use_case_id is None:
        print("ERROR: --use-case or --bracket is required", file=sys.stderr)
        return 1

    if args.output is not None:
        output_path = Path(args.output).resolve()
    else:
        output_path = get_default_report_output_path(repo_root, use_case_id).resolve()
        print(f"Output (default): {output_path}", file=sys.stderr)
    output_path.mkdir(parents=True, exist_ok=True)
    dataset_ref = args.dataset_reference.strip()

    # ── IR-first mode ────────────────────────────────────────────────────────
    if args.bracket:
        bracket_path = Path(args.bracket)
        if not bracket_path.exists():
            print(f"ERROR: bracket not found: {bracket_path}", file=sys.stderr)
            return 1
        return _ir_generate(bracket_path, output_path, repo_root, dataset_ref)

    # ── Scaffold mode (legacy) ───────────────────────────────────────────────
    # Delta mode: report exists and not --force-full
    if not args.force_full and report_exists_for_update(output_path):
        applied = sync_report(use_case_id, output_path, repo_root)
        if applied:
            print("mode=delta", file=sys.stdout)
            return 0

    gen_overview = PageScaffoldGenerator(
        use_case_id=use_case_id,
        page_name="overview",
        repo_root=repo_root,
    )
    gen_overview.load_config()
    gen_overview.generate()
    gen_overview.write(output_path, dataset_reference_path=dataset_ref)

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
