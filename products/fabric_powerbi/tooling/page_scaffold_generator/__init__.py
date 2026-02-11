"""
Page Scaffold Generator

Generates standardized Power BI page structures (PBIP format) from governance files.
"""

__version__ = "1.0.0"

from .scaffold_generator import PageScaffoldGenerator
from .mockup_generator import MockupGenerator

__all__ = ["PageScaffoldGenerator", "MockupGenerator"]
