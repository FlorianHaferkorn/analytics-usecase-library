#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
derive_brand_artifacts — CLI orchestrator for brand derivation pipeline.

Reads a showcase's brand_spec.yaml, runs both converters, writes outputs,
and patches tool_derivations back into the spec so the spec stays the
authoritative record of where all generated files live.

Usage:
    python tooling/brand/derive_brand_artifacts.py --showcase aurora_group
    python tooling/brand/derive_brand_artifacts.py --showcase aurora_group --concept NeutralAccent
    python tooling/brand/derive_brand_artifacts.py --spec path/to/brand_spec.yaml --out-dir /tmp/brand

Pipeline (single responsibility per step):
    1. loader.load_brand_spec          — I/O + validation
    2. pbi_theme.spec_to_pbi_theme     — pure derivation → PBI theme dict
    3. css_variables.spec_to_css       — pure derivation → CSS string
    4. _write_pbi_theme                — I/O: write JSON, register default
    5. _write_css                      — I/O: write CSS file
    6. _patch_tool_derivations         — I/O: update spec YAML with output paths
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional

# Resolve repo root so this script works regardless of cwd.
_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPT_DIR.parents[1]

# Adjust sys.path so the core derivations package is importable.
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from core.brand.derivations.loader import load_brand_spec
from core.brand.derivations.pbi_theme import spec_to_pbi_theme
from core.brand.derivations.css_variables import spec_to_css

try:
    import yaml  # type: ignore
    _YAML_OK = True
except ImportError:
    _YAML_OK = False

_SHOWCASES_DIR = _REPO_ROOT / "showcases"
# ALUCA-owned output (never a foreign tree): brand-spec derivations sit next to the
# on-demand engine output in themes_local/, see products/fabric/powerbi/tooling/theme_paths.py.
_THEME_OUTPUT_DIR = _REPO_ROOT / "products" / "fabric" / "powerbi" / "themes_local" / "brand"
_OSS_THEMES_DIR = _REPO_ROOT / "products" / "open_source_stack" / "themes"


# ─────────────────────────────────────────────
# Public API (importable from brand_designer.py)
# ─────────────────────────────────────────────

def derive_for_showcase(
    showcase_name: str,
    concept: str = "Monochromatic",
    canvas_profile: str = "powerbi_design_base",
    *,
    verbose: bool = True,
) -> dict[str, Path]:
    """
    Run the full derivation pipeline for a showcase.

    Args:
        showcase_name: Directory name under showcases/ (e.g. "aurora_group").
        concept: Color concept — "Monochromatic", "NeutralAccent", or "Divergent".
        canvas_profile: BrandSpec canvas profile key for font size delta.
        verbose: If True, print progress to stdout.

    Returns:
        Dict with keys "pbi_theme" and "css_variables" pointing to written files.

    Raises:
        FileNotFoundError: If the showcase or brand_spec.yaml does not exist.
        ValueError: If the spec fails validation.
    """
    spec_path = _SHOWCASES_DIR / showcase_name / "brand" / "brand_spec.yaml"
    out_dir_css = _SHOWCASES_DIR / showcase_name / "brand"
    outputs = derive_from_spec(
        spec_path=spec_path,
        out_dir_pbi=_THEME_OUTPUT_DIR,
        out_dir_css=out_dir_css,
        concept=concept,
        canvas_profile=canvas_profile,
        verbose=verbose,
    )
    # Register the generated theme as the showcase default so apply_report_theme
    # --use-default and --batch-showcase can pick it up without extra arguments.
    _register_showcase_default(showcase_name, outputs["pbi_theme"], verbose)
    # Mirror CSS variables into the OSS stack so Evidence pages pick up the brand.
    _write_oss_css(outputs["css_variables"], verbose)
    return outputs


def derive_from_spec(
    spec_path: Path,
    out_dir_pbi: Path,
    out_dir_css: Path,
    concept: str = "Monochromatic",
    canvas_profile: str = "powerbi_design_base",
    *,
    verbose: bool = True,
) -> dict[str, Path]:
    """
    Run the full derivation pipeline from an explicit spec path.

    Returns:
        Dict with keys "pbi_theme" and "css_variables" pointing to written files.
    """
    _log(f"Loading spec: {spec_path}", verbose)
    spec = load_brand_spec(spec_path)

    brand_id = spec["identity"]["brand_id"]
    primary = spec["color"]["primary"]
    theme_name = f"{spec['identity']['brand_name']}__{concept}__{canvas_profile}__{primary}"

    # ── Step 2: derive PBI theme ─────────────────────────────
    _log(f"Deriving Power BI theme ({concept}, {canvas_profile})...", verbose)
    pbi_dict = spec_to_pbi_theme(spec, concept=concept, canvas_profile=canvas_profile)

    # ── Step 3: derive CSS variables ────────────────────────
    _log("Deriving CSS custom properties...", verbose)
    try:
        source_hint = spec_path.relative_to(_REPO_ROOT).as_posix()
    except ValueError:
        source_hint = str(spec_path)
    css_str = spec_to_css(spec, source_hint=source_hint)

    # ── Step 4: write PBI theme ──────────────────────────────
    pbi_path = _write_pbi_theme(pbi_dict, theme_name, out_dir_pbi, verbose)

    # ── Step 5: write CSS ────────────────────────────────────
    css_path = _write_css(css_str, brand_id, out_dir_css, verbose)

    # ── Step 6: patch tool_derivations back into spec ────────
    _patch_tool_derivations(spec_path, pbi_path, css_path, verbose)

    outputs = {"pbi_theme": pbi_path, "css_variables": css_path}
    _log("Done.", verbose)
    return outputs


# ─────────────────────────────────────────────
# I/O helpers — one responsibility each
# ─────────────────────────────────────────────

def _write_pbi_theme(
    pbi_dict: dict[str, Any],
    theme_name: str,
    out_dir: Path,
    verbose: bool,
) -> Path:
    """Write PBI theme dict as JSON. Returns the written path."""
    out_dir.mkdir(parents=True, exist_ok=True)
    safe_name = (
        theme_name
        .replace(" ", "_")
        .replace("/", "-")
        .replace("#", "")   # hex color in name — strip leading hash for filesystem safety
    )
    out_path = out_dir / f"{safe_name}.json"
    out_path.write_text(
        json.dumps(pbi_dict, indent=2, ensure_ascii=False),
        encoding="utf-8",
        newline="\n")
    _log(f"  PBI theme → {out_path}", verbose)
    return out_path


def _write_css(css_str: str, brand_id: str, out_dir: Path, verbose: bool) -> Path:
    """Write CSS custom properties string to file. Returns the written path."""
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{brand_id}_variables.css"
    out_path.write_text(css_str, encoding="utf-8", newline="\n")
    _log(f"  CSS vars  → {out_path}", verbose)
    return out_path


def _patch_tool_derivations(
    spec_path: Path,
    pbi_path: Path,
    css_path: Path,
    verbose: bool,
) -> None:
    """
    Update tool_derivations in the brand_spec.yaml with the relative paths
    of the generated files. Writes the spec back in-place.
    """
    if not _YAML_OK:
        _log("  [skip] PyYAML not available — cannot patch tool_derivations.", verbose)
        return

    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    if not isinstance(spec, dict):
        return

    def _rel(p: Path) -> str:
        # Prefer repo-root-relative path (portable); fall back to absolute.
        for anchor in (_REPO_ROOT, spec_path.parent):
            try:
                return p.relative_to(anchor).as_posix()
            except ValueError:
                continue
        return str(p)

    td = spec.setdefault("tool_derivations", {})
    td["powerbi_theme"] = _rel(pbi_path)
    td["css_variables"] = _rel(css_path)

    spec_path.write_text(
        yaml.dump(spec, allow_unicode=True, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
        newline="\n")
    _log(f"  Patched tool_derivations in {spec_path.name}", verbose)


def _write_repo_config(showcase_name: str, verbose: bool) -> None:
    """
    Write (or update) repo_config.yaml at the repo root with the given showcase_id.
    Preserves existing keys; only updates showcase_id.
    """
    if not _YAML_OK:
        _log("  [skip] PyYAML not available — cannot update repo_config.yaml.", verbose)
        return
    config_path = _REPO_ROOT / "repo_config.yaml"
    config: dict = {}
    if config_path.exists():
        try:
            config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        except Exception:
            pass
    config.setdefault("schema_version", "1.0")
    config["showcase_id"] = showcase_name
    config_path.write_text(
        yaml.dump(config, allow_unicode=True, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
        newline="\n")
    _log(f"  repo_config.yaml → showcase_id: {showcase_name}", verbose)


def _write_oss_css(css_path: Path, verbose: bool) -> None:
    """
    Mirror the generated CSS variables file into the OSS stack themes directory
    so Evidence pages and the Tailwind config pick up the active brand without
    manual copying.  Only runs when the OSS themes directory exists.
    """
    if not _OSS_THEMES_DIR.is_dir():
        return
    dest = _OSS_THEMES_DIR / "variables.css"
    dest.write_text(css_path.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
    _log(f"  OSS CSS   → {dest.relative_to(_REPO_ROOT)}", verbose)


def _register_showcase_default(
    showcase_name: str,
    pbi_path: Path,
    verbose: bool,
) -> None:
    """
    Write/update showcases/<name>/theme_config.json with the generated theme name
    so that apply_report_theme --use-default resolves to this theme automatically.
    """
    showcase_dir = _SHOWCASES_DIR / showcase_name
    if not showcase_dir.is_dir():
        return
    config_file = showcase_dir / "theme_config.json"
    config: dict[str, Any] = {}
    if config_file.exists():
        try:
            config = json.loads(config_file.read_text(encoding="utf-8"))
        except Exception:
            pass
    # Theme name is the JSON stem (filename without .json extension).
    config["defaultThemeName"] = pbi_path.stem
    config_file.write_text(
        json.dumps(config, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n")
    _log(f"  Default theme registered in {config_file.relative_to(_REPO_ROOT)}", verbose)


def _log(msg: str, verbose: bool) -> None:
    if verbose:
        print(msg)


# ─────────────────────────────────────────────
# CLI entry point
# ─────────────────────────────────────────────

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Derive Power BI theme JSON and CSS custom properties from a BrandSpec YAML.\n"
            "Writes outputs and patches tool_derivations back into the spec."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument(
        "--showcase",
        metavar="NAME",
        help="Showcase name under showcases/ (e.g. aurora_group).",
    )
    source.add_argument(
        "--spec",
        type=Path,
        metavar="PATH",
        help="Direct path to a brand_spec.yaml file.",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        metavar="DIR",
        help=(
            "Output directory for both artifacts (overrides default locations). "
            "Only used with --spec."
        ),
    )
    parser.add_argument(
        "--concept",
        default="Monochromatic",
        choices=["Monochromatic", "NeutralAccent", "Divergent"],
        help="Color palette concept (default: Monochromatic).",
    )
    parser.add_argument(
        "--canvas-profile",
        default="powerbi_design_base",
        choices=["powerbi_design_base", "powerbi_production", "powerbi_widescreen"],
        help="Canvas profile for font size delta (default: powerbi_design_base).",
    )
    parser.add_argument(
        "--update-repo-config",
        action="store_true",
        help=(
            "After derivation, write showcase_id to repo_config.yaml at the repo root. "
            "Only applies when --showcase is used. "
            "Use this to activate a brand for all generators in one step."
        ),
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress progress output.",
    )
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    verbose = not args.quiet

    try:
        if args.showcase:
            outputs = derive_for_showcase(
                showcase_name=args.showcase,
                concept=args.concept,
                canvas_profile=args.canvas_profile,
                verbose=verbose,
            )
            if args.update_repo_config:
                _write_repo_config(args.showcase, verbose)
        else:
            spec_path = Path(args.spec).resolve()
            out_dir = Path(args.out_dir).resolve() if args.out_dir else spec_path.parent
            outputs = derive_from_spec(
                spec_path=spec_path,
                out_dir_pbi=out_dir,
                out_dir_css=out_dir,
                concept=args.concept,
                canvas_profile=args.canvas_profile,
                verbose=verbose,
            )
        if verbose:
            print("\nGenerated:")
            for key, path in outputs.items():
                print(f"  {key}: {path}")
        return 0

    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
