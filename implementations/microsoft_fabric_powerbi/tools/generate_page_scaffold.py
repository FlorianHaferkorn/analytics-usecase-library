#!/usr/bin/env python3
"""
CLI script for generating Power BI page scaffolds.

Usage:
    python generate_page_scaffold.py --use-case COM-001 --page overview --output path/to/Report --mockup path/to/mockup.html
"""

import argparse
import sys
from pathlib import Path

# Add page_scaffold_generator to path
sys.path.insert(0, str(Path(__file__).parent))

from page_scaffold_generator import PageScaffoldGenerator, MockupGenerator


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate Power BI page scaffolds from governance files"
    )
    
    parser.add_argument(
        '--use-case',
        required=True,
        help='Use case ID (e.g., COM-001)'
    )
    
    parser.add_argument(
        '--page',
        choices=['overview', 'detail'],
        required=True,
        help='Page name (overview or detail)'
    )
    
    parser.add_argument(
        '--theme',
        default=None,
        help='Theme name (e.g., "Brand Blue__Monochromatic__Light__#118DFF"). If not provided, uses showcase or framework default.'
    )
    
    parser.add_argument(
        '--no-theme',
        action='store_true',
        help='Skip theme application (opt-out). By default, themes are applied automatically.'
    )
    
    parser.add_argument(
        '--output',
        required=True,
        type=Path,
        help='Output path for .Report folder (e.g., showcases/aurora_group/reports/COM-001.Report)'
    )
    
    parser.add_argument(
        '--mockup',
        type=Path,
        default=None,
        help='Output path for HTML mockup (optional)'
    )
    
    parser.add_argument(
        '--repo-root',
        type=Path,
        default=None,
        help='Repository root path (auto-detected if not provided)'
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize generator
        generator = PageScaffoldGenerator(
            use_case_id=args.use_case,
            page_name=args.page,
            theme_name=args.theme,
            repo_root=args.repo_root
        )
        
        # Generate scaffold
        print(f"Generating scaffold for {args.use_case} - {args.page}...")
        generator.load_config()
        generator.generate()
        
        # Validate
        errors = generator.validate()
        if errors:
            print("Validation errors:")
            for error in errors:
                print(f"  - {error}")
            sys.exit(1)
        
        # Write PBIP structure
        print(f"Writing PBIP structure to {args.output}...")
        generator.write(args.output)
        print("[OK] PBIP structure written successfully")

        # Apply theme automatically unless --no-theme (opt-out, not opt-in)
        if not args.no_theme:
            try:
                from apply_report_theme import apply_theme, resolve_theme_path, get_default_theme_name
                report_path = Path(args.output).resolve()
                
                # Determine theme: explicit --theme → showcase default → framework default
                theme_name = args.theme
                if not theme_name:
                    theme_name = get_default_theme_name(report_path)
                
                if theme_name:
                    theme_path = resolve_theme_path(theme_name)
                    if theme_path is not None:
                        apply_theme(
                            report_path=report_path,
                            theme_source_path=theme_path,
                            custom_theme_name=theme_name,
                            base_theme_name="CY25SU10",
                            validate=False,
                        )
                        # Silent success for auto-applied themes
                        source = "explicit" if args.theme else ("showcase default" if "showcases" in str(report_path) else "framework default")
                        print(f"[OK] Theme applied: {theme_name} (from {source})")
                    else:
                        print(f"[WARN] Theme not found under theme_generator/themes/: {theme_name}. Report has base theme only.", file=sys.stderr)
                else:
                    # No default configured - this is OK, report has base theme only
                    pass
            except Exception as e:
                print(f"[WARN] Could not apply theme: {e}. Report has base theme only.", file=sys.stderr)

        # Generate mockup if requested
        if args.mockup:
            print(f"Generating HTML mockup to {args.mockup}...")
            mockup_gen = MockupGenerator()
            page_structure = generator.get_page_structure()
            mockup_gen.generate_mockup(
                page_structure=page_structure,
                use_case_id=args.use_case,
                page_name=args.page,
                output_path=args.mockup
            )
            print("[OK] HTML mockup generated successfully")
            print(f"  Open {args.mockup} in a browser to preview the layout")
        
        print("\n[OK] Scaffold generation complete!")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
