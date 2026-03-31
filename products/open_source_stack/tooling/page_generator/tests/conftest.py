"""Pytest configuration for Evidence page generator tests."""

import sys
from pathlib import Path

# Allow imports from the page_generator package
PACKAGE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[5]

if str(PACKAGE_ROOT.parent) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT.parent))
