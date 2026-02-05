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
        help='Theme name (e.g., "Brand Blue__Monochromatic__Light__#118DFF"). Defaults to framework default.'
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
