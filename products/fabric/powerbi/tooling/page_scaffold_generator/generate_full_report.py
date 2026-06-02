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
from typing import Optional

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


def _ensure_repo_root_on_path(repo_root: Path) -> None:
    root_str = str(repo_root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)


def _resolve_theme_path(bracket_path: Path, repo_root: Path, explicit_theme: Optional[str]) -> Optional[Path]:
    """Resolve the Power BI theme file path.

    Resolution order:
      1. Explicit --theme argument (absolute or repo-relative path)
      2. bracket → brand.brand_id → showcases/<id>/brand/brand_spec.yaml → tool_derivations.powerbi_theme
      3. repo_config.yaml → showcase_id → brand_spec.yaml → tool_derivations.powerbi_theme
      4. None (no custom theme; falls back to CY25SU10 base theme)
    """
    if explicit_theme:
        p = Path(explicit_theme)
        if not p.is_absolute():
            p = repo_root / p
        return p if p.exists() else None

    # Try to find a brand spec via bracket or repo_config
    showcase_id = None
    if bracket_path.exists():
        import yaml as _yaml
        with open(bracket_path, encoding="utf-8") as _fh:
            bracket = _yaml.safe_load(_fh) or {}
        brand_block = bracket.get("brand") or {}
        showcase_id = brand_block.get("brand_id") if isinstance(brand_block, dict) else None

    if not showcase_id:
        rc = repo_root / "repo_config.yaml"
        if rc.exists():
            import yaml as _yaml
            with open(rc, encoding="utf-8") as _fh:
                cfg = _yaml.safe_load(_fh) or {}
            showcase_id = cfg.get("showcase_id")

    if not showcase_id:
        # Fallback: scan showcases/ directory for a single showcase
        showcases_dir = repo_root / "showcases"
        if showcases_dir.is_dir():
            candidates = [d for d in showcases_dir.iterdir() if d.is_dir()]
            if len(candidates) == 1:
                showcase_id = candidates[0].name

    if showcase_id:
        brand_spec_path = repo_root / "showcases" / showcase_id / "brand" / "brand_spec.yaml"
        if brand_spec_path.exists():
            import yaml as _yaml
            with open(brand_spec_path, encoding="utf-8") as _fh:
                brand_spec = _yaml.safe_load(_fh) or {}
            theme_rel = (brand_spec.get("tool_derivations") or {}).get("powerbi_theme")
            if theme_rel:
                theme_path = (repo_root / theme_rel).resolve()
                if theme_path.exists():
                    return theme_path

    return None


def _ir_generate(
    bracket_path: Path,
    output_path: Path,
    repo_root: Path,
    dataset_ref: str,
    theme_path: Optional[Path] = None,
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

    # Inject resolved theme path so the adapter can embed the theme file
    if theme_path:
        spec.theme_path = str(theme_path)

    errors = PBIPAdapter().validate_ir(spec)
    if errors:
        for e in errors:
            print(f"IR VALIDATION ERROR: {e}", file=sys.stderr)
        return 1

    from products.fabric.powerbi.tooling.adapters.pbip import _speaking_report_name

    result = PBIPAdapter().render(spec)
    for warning in result.warnings:
        print(f"RENDER WARNING: {warning}", file=sys.stderr)

    # PBIPAdapter.render() emits paths like '<ReportName>.Report/definition/...'.
    # Always write under the canonical dist root, not inside a nested .Report folder.
    dist_root = (repo_root / DIST_RELATIVE).resolve()
    dist_root.mkdir(parents=True, exist_ok=True)
    written = result.write_to(dist_root)

    # Clear stale AS model caches so PBI Desktop rebuilds from TMDL on next open.
    # cache.abf stores the full model state; if stale, PBI Desktop loads it first and
    # then tries to apply TMDL as an UPDATE — which triggers
    # PFE_TM_DDL_MODIFIED_CULTURE_OR_COLLATION_AFTER_CHILDREN_CREATION when culture
    # is changed on an already-populated model. Deleting the cache forces a clean rebuild.
    if spec.semantic_model:
        cache_file = dist_root / spec.semantic_model / ".pbi" / "cache.abf"
        if cache_file.exists():
            cache_file.unlink()
            print(f"cache: removed stale {cache_file.name}", file=sys.stderr)

    report_folder = f"{_speaking_report_name(spec.use_case_id, spec.title)}.Report"
    print(f"mode=ir-full report={report_folder} files={len(written)}", file=sys.stdout)
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
        default=None,
        help=(
            "Relative path from report folder to semantic model PBIP "
            "(e.g. '../Commercial.SemanticModel'). "
            "When omitted, defaults to '../<Domain>.SemanticModel' resolved from the bracket."
        ),
    )
    parser.add_argument(
        "--theme",
        default=None,
        help=(
            "Path (absolute or repo-relative) to a .json theme file to embed in the report. "
            "When omitted, auto-detected from showcases/<id>/brand/brand_spec.yaml "
            "tool_derivations.powerbi_theme."
        ),
    )
    parser.add_argument(
        "--force-full",
        action="store_true",
        help="Always full generate (overwrite); do not use delta update even if report exists.",
    )
    args = parser.parse_args()

    repo_root = args.repo_root
    if repo_root is None:
        # page_scaffold_generator → tooling → powerbi → fabric → products → repo root
        repo_root = Path(__file__).resolve().parents[5]
    repo_root = Path(repo_root).resolve()

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

    # Resolve dataset reference: explicit arg > bracket domain > generic fallback
    if args.dataset_reference:
        dataset_ref = args.dataset_reference.strip()
    else:
        # Derive from bracket domain field (e.g. "Commercial" → "../Commercial.SemanticModel")
        _domain = None
        _bracket_for_ref = args.bracket or (
            next(
                (repo_root / "core" / "usecases" / "core" / d / "UseCase_Bracket.yaml"
                 for d in (repo_root / "core" / "usecases" / "core").iterdir()
                 if d.is_dir() and d.name.startswith(use_case_id)),
                None,
            )
            if (repo_root / "core" / "usecases" / "core").exists() else None
        )
        if _bracket_for_ref and Path(_bracket_for_ref).exists():
            import yaml as _yaml
            with open(_bracket_for_ref, encoding="utf-8") as _fh:
                _b = _yaml.safe_load(_fh) or {}
            _domain = _b.get("domain")
        dataset_ref = f"../{_domain}.SemanticModel" if _domain else "../SemanticModel"

    # ── IR-first mode ────────────────────────────────────────────────────────
    if args.bracket:
        bracket_path = Path(args.bracket)
        if not bracket_path.exists():
            print(f"ERROR: bracket not found: {bracket_path}", file=sys.stderr)
            return 1
        theme_path = _resolve_theme_path(bracket_path, repo_root, getattr(args, "theme", None))
        if theme_path:
            print(f"theme: {theme_path.name}", file=sys.stderr)
        return _ir_generate(bracket_path, output_path, repo_root, dataset_ref, theme_path=theme_path)

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
