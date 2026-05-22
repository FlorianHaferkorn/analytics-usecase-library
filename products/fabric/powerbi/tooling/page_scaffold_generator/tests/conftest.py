"""Ensure page_scaffold_generator is importable regardless of working directory."""
import sys
from pathlib import Path

# Add tooling/ to sys.path so 'page_scaffold_generator' resolves as a package
_tooling_dir = str(Path(__file__).resolve().parent.parent.parent)
if _tooling_dir not in sys.path:
    sys.path.insert(0, _tooling_dir)

# Add workspace root so absolute 'products.*' imports resolve
_workspace_root = str(Path(__file__).resolve().parents[6])
if _workspace_root not in sys.path:
    sys.path.insert(0, _workspace_root)
