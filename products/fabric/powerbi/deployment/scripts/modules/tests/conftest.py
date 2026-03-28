"""Ensure deployment modules are importable regardless of working directory."""
import sys
from pathlib import Path

# Add modules/ to sys.path so 'modules.*' imports resolve
_modules_dir = str(Path(__file__).resolve().parent.parent)
_scripts_dir = str(Path(__file__).resolve().parent.parent.parent)
if _modules_dir not in sys.path:
    sys.path.insert(0, _modules_dir)
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)
